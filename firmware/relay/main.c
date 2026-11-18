/*
 * Relay firmware for the sensor strip boards (CH32V003J4M6 and CH32V005D6U6).
 *
 * Upstream (J1) the board is an I2C target on the hardware I2C peripheral.
 * Downstream (J2) it is a bit-banged I2C controller on two GPIOs, using the
 * internal pull-ups so R5/R6 are optional.  relay_core.c holds the protocol
 * logic; this file is the hardware underneath it.  See ../README.md.
 */
#include <string.h>
#include "ch32fun.h"
#include "board.h"
#include "ntc.h"
#include "relay_core.h"

/* Downstream bit rate.  10 kHz suits the internal pull-ups (about 45k); with
 * R5/R6 fitted on every board it can be raised to 100000. */
#ifndef DN_I2C_HZ
#define DN_I2C_HZ          10000u
#endif
#define DN_HALF_TICKS      (F_CPU / (2u * DN_I2C_HZ))
/* How long the downstream board may hold SCL low before we give up. */
#define DN_STRETCH_MS      250u

/* Time budget per hop: a full frame each way plus the poll gaps. */
#define HOP_MS             (2u * MDC_MAX_FRAME * 9u * 1000u / DN_I2C_HZ + 30u)
/* Time allowed at the far end: the slowest command is a bootloader COMMIT,
 * which checks the whole image (roughly 0.4 s for a full CH32V005). */
#define BASE_MS            1000u

#define SAMPLE_PERIOD_MS   1000u
#define SAMPLES            16
#define BLINK_MS           250u
#define BOOT_FALLBACK_MS   1000u    /* restart even if the reply is never read */
#define WATCHDOG_RELOAD    2000u    /* about 2 s at LSI / 128 */

static volatile uint32_t ms_ticks;

void SysTick_Handler(void) __attribute__((interrupt));
void SysTick_Handler(void)
{
	/* Catch up if the interrupt was held off for more than a tick. */
	do {
		SysTick->CMP += F_CPU / 1000u;
		ms_ticks++;
	} while ((int32_t)(SysTick->CNT - SysTick->CMP) >= 0);
	SysTick->SR = 0;
}

static uint32_t millis(void)
{
	return ms_ticks;
}

static void delay_ticks(uint32_t n)
{
	uint32_t t0 = SysTick->CNT;

	while ((uint32_t)(SysTick->CNT - t0) < n)
		;
}

/* ---- Upstream: I2C target ------------------------------------------- */

static volatile uint8_t up_rx[MDC_MAX_FRAME];
static volatile uint8_t up_rx_len;      /* length of the frame in up_rx */
static volatile uint8_t up_rx_ready;    /* a frame is waiting for the main loop */
static volatile uint8_t up_busy;        /* a command has no reply yet */
static volatile uint8_t up_reply_read;  /* the current reply has been read */
static uint8_t up_tx[MDC_MAX_FRAME];
static volatile uint8_t up_tx_len;
static uint8_t up_busy_frame[MDC_RSP_HDR + MDC_CRC_LEN];

static uint8_t isr_idx;
static uint8_t isr_rx;                  /* a write to us is in progress */
static uint8_t isr_tx_real;             /* the read in progress carries the real reply */
static const uint8_t *isr_tx;
static uint8_t isr_tx_len;

/* A write to us has ended: hand the frame to the main loop. */
static void isr_rx_done(void)
{
	if (isr_rx && isr_idx) {
		/* An over-long frame is cut short and fails its CRC. */
		up_rx_len = isr_idx > MDC_MAX_FRAME ? MDC_MAX_FRAME : isr_idx;
		up_rx_ready = 1;
		up_busy = 1;
	}
	isr_rx = 0;
}

void I2C1_EV_IRQHandler(void) __attribute__((interrupt));
void I2C1_EV_IRQHandler(void)
{
	uint32_t s1 = I2C1->STAR1;

	/* The data and stop of a finished write come before a new address. */
	if (s1 & I2C_STAR1_RXNE) {
		uint8_t d = (uint8_t)I2C1->DATAR;

		if (isr_idx < MDC_MAX_FRAME)
			up_rx[isr_idx] = d;
		if (isr_idx < 255)
			isr_idx++;
	}
	if (s1 & I2C_STAR1_STOPF) {             /* end of a write to us */
		I2C1->CTLR1 |= I2C_CTLR1_PE;        /* writing CTLR1 clears STOPF */
		isr_rx_done();
	}
	if (s1 & I2C_STAR1_ADDR) {              /* addressed: reading STAR2 clears it */
		uint32_t s2 = I2C1->STAR2;

		isr_rx_done();                      /* repeated start after a write */
		isr_idx = 0;
		if (s2 & I2C_STAR2_TRA) {
			isr_tx_real = !up_busy;
			if (up_busy) {
				isr_tx = up_busy_frame;
				isr_tx_len = sizeof(up_busy_frame);
			} else {
				isr_tx = up_tx;
				isr_tx_len = up_tx_len;
			}
		} else {
			isr_rx = 1;
		}
	}
	if (s1 & I2C_STAR1_TXE) {
		I2C1->DATAR = (isr_tx && isr_idx < isr_tx_len) ? isr_tx[isr_idx] : 0xFF;
		if (isr_idx < 255)
			isr_idx++;
	}
}

void I2C1_ER_IRQHandler(void) __attribute__((interrupt));
void I2C1_ER_IRQHandler(void)
{
	uint32_t s1 = I2C1->STAR1;

	if (s1 & I2C_STAR1_AF) {                /* end of a read from us */
		if (isr_tx_real && isr_idx > isr_tx_len)
			up_reply_read = 1;
		isr_tx_real = 0;
	}
	I2C1->STAR1 = ~(s1 & (I2C_STAR1_AF | I2C_STAR1_BERR | I2C_STAR1_ARLO | I2C_STAR1_OVR));
}

static void up_init(void)
{
	up_busy_frame[0] = MDC_ST_BUSY;
	mdc_seal(up_busy_frame, MDC_RSP_HDR);

	/* Until the first command there is no reply: answer reads with BUSY. */
	memcpy(up_tx, up_busy_frame, sizeof(up_busy_frame));
	up_tx_len = sizeof(up_busy_frame);

	RCC->APB1PCENR |= RCC_APB1Periph_I2C1;

#if SWIO_SHARED
	AFIO->PCFR1 = (AFIO->PCFR1 & ~(AFIO_PCFR1_I2C1_RM | AFIO_PCFR1_SWCFG)) |
		UP_I2C_REMAP | AFIO_PCFR1_SWCFG_2;  /* SCL takes over the SWIO pin */
#endif
	PIN_CFG(UP_PORT, UP_SDA_PIN, PIN_AF_OD);
	PIN_CFG(UP_PORT, UP_SCL_PIN, PIN_AF_OD);

	I2C1->CTLR2 = (F_CPU / 1000000u) | I2C_CTLR2_ITBUFEN | I2C_CTLR2_ITEVTEN | I2C_CTLR2_ITERREN;
	I2C1->OADDR1 = MDC_I2C_ADDR << 1;
	I2C1->CTLR1 = I2C_CTLR1_PE;
	I2C1->CTLR1 = I2C_CTLR1_PE | I2C_CTLR1_ACK;

	NVIC_EnableIRQ(I2C1_EV_IRQn);
	NVIC_EnableIRQ(I2C1_ER_IRQn);
}

uint8_t plat_cmd_fetch(void *ctx, uint8_t *frame)
{
	uint8_t n = 0;

	(void)ctx;
	if (!up_rx_ready)
		return 0;
	__disable_irq();
	if (up_rx_ready) {
		n = up_rx_len;
		memcpy(frame, (const uint8_t *)up_rx, n);
		up_rx_ready = 0;
	}
	__enable_irq();
	return n;
}

void plat_reply_publish(void *ctx, const uint8_t *frame, uint8_t n)
{
	(void)ctx;
	__disable_irq();
	if (!up_rx_ready) {                     /* else a newer command is already in */
		memcpy(up_tx, frame, n);
		up_tx_len = n;
		up_reply_read = 0;
		up_busy = 0;
	}
	__enable_irq();
}

/* ---- Downstream: bit-banged I2C controller -------------------------- */

#define SDA_LOW()      PIN_LOW(DN_SDA_PORT, DN_SDA_PIN)
#define SDA_RELEASE()  PIN_RELEASE(DN_SDA_PORT, DN_SDA_PIN)
#define SDA_READ()     PIN_READ(DN_SDA_PORT, DN_SDA_PIN)
#define SCL_LOW()      PIN_LOW(DN_SCL_PORT, DN_SCL_PIN)
#define SCL_READ()     PIN_READ(DN_SCL_PORT, DN_SCL_PIN)

static uint8_t dn_fail;                 /* SCL stayed low: give up on this transfer */

/* Release SCL and wait for it to rise: the slow pull-up and a target that
 * stretches the clock both show up here. */
static void scl_release(void)
{
	PIN_RELEASE(DN_SCL_PORT, DN_SCL_PIN);
	if (dn_fail)
		return;
	uint32_t t0 = millis();
	while (!SCL_READ()) {
		if (millis() - t0 > DN_STRETCH_MS) {
			dn_fail = 1;
			return;
		}
	}
}

static void dn_start(void)
{
	dn_fail = 0;
	SDA_RELEASE();
	scl_release();
	delay_ticks(DN_HALF_TICKS);
	/* A target left mid-byte holds SDA low: clock it until it lets go. */
	for (int i = 0; i < 9 && !SDA_READ(); i++) {
		SCL_LOW();
		delay_ticks(DN_HALF_TICKS);
		scl_release();
		delay_ticks(DN_HALF_TICKS);
	}
	SDA_LOW();
	delay_ticks(DN_HALF_TICKS);
	SCL_LOW();
}

static void dn_stop(void)
{
	SDA_LOW();
	delay_ticks(DN_HALF_TICKS);
	scl_release();
	delay_ticks(DN_HALF_TICKS);
	SDA_RELEASE();
	delay_ticks(DN_HALF_TICKS);
}

/* Clock one bit with SCL low on entry and exit; returns the level of SDA. */
static uint8_t dn_bit(uint8_t out)
{
	if (out)
		SDA_RELEASE();
	else
		SDA_LOW();
	delay_ticks(DN_HALF_TICKS);
	scl_release();
	delay_ticks(DN_HALF_TICKS);
	uint8_t in = (uint8_t)SDA_READ();
	SCL_LOW();
	return in;
}

/* Returns 1 if the target acknowledged. */
static uint8_t dn_tx(uint8_t b)
{
	for (int i = 0; i < 8; i++, b <<= 1)
		dn_bit(b & 0x80);
	return !dn_bit(1) && !dn_fail;
}

static uint8_t dn_rx(uint8_t ack)
{
	uint8_t b = 0;

	for (int i = 0; i < 8; i++)
		b = (uint8_t)((b << 1) | dn_bit(1));
	dn_bit(!ack);
	return b;
}

int plat_dn_write(void *ctx, const uint8_t *frame, uint8_t n)
{
	int rc = DN_OK;

	(void)ctx;
	dn_start();
	if (!dn_tx(MDC_I2C_ADDR << 1)) {
		rc = dn_fail ? DN_ERR : DN_NACK;
	} else {
		for (uint8_t i = 0; i < n; i++) {
			if (!dn_tx(frame[i])) {
				rc = DN_ERR;
				break;
			}
		}
	}
	dn_stop();
	return dn_fail ? DN_ERR : rc;
}

int plat_dn_read(void *ctx, uint8_t *frame)
{
	int n = MDC_RSP_HDR;

	(void)ctx;
	dn_start();
	if (!dn_tx((MDC_I2C_ADDR << 1) | 1)) {
		dn_stop();
		return dn_fail ? DN_ERR : DN_NACK;
	}
	for (int i = 0; i < MDC_RSP_HDR - 1; i++)
		frame[i] = dn_rx(1);
	if (frame[0] == MDC_ST_BUSY || frame[0] == 0xFF) {
		/* Nothing to fetch yet.  0xFF is an idle bus, not a status. */
		dn_rx(0);
		n = frame[0] == MDC_ST_BUSY ? 0 : DN_ERR;
	} else {
		frame[3] = dn_rx(1);
		if (frame[3] > MDC_MAX_PAYLOAD) {
			dn_rx(0);
			n = DN_ERR;
		} else {
			uint8_t rest = (uint8_t)(frame[3] + MDC_CRC_LEN);

			for (uint8_t i = 0; i < rest; i++)
				frame[n++] = dn_rx(i + 1 < rest);
		}
	}
	dn_stop();
	return dn_fail ? DN_ERR : n;
}

/* ---- Thermistor ------------------------------------------------------ */

static uint16_t ntc_raw;
static int16_t ntc_temp = MDC_TEMP_INVALID;
static uint32_t ntc_next;
#ifdef NTC_DRV_PORT
static uint8_t ntc_powered;
#endif

static void ntc_init(void)
{
	PIN_CFG(NTC_PORT, NTC_PIN, PIN_ANALOG);
#ifdef NTC_DRV_PORT
	NTC_DRV_PORT->BCR = 1u << NTC_DRV_PIN;
	PIN_CFG(NTC_DRV_PORT, NTC_DRV_PIN, PIN_OUT_PP);
#endif
	/* ADC clock = HCLK / 2 = 4 MHz, inside the limit at any supply voltage. */
	RCC->CFGR0 &= ~RCC_ADCPRE;
	funAnalogInit();
	ADC1->SAMPTR2 = 7u << (3 * NTC_ADC_CH);     /* longest sample time */
}

static void ntc_convert(void)
{
	uint32_t sum = 0;

	for (int i = 0; i < SAMPLES; i++)
		sum += (uint32_t)funAnalogRead(NTC_ADC_CH);
	/* 16 samples add 4 bits; shift the rest of the way to 16 bits. */
	ntc_raw = (uint16_t)(sum << (16 - 4 - BOARD_ADC_BITS));
	ntc_temp = ntc_centi_c(ntc_raw);
}

static void ntc_task(uint32_t now)
{
	if ((int32_t)(now - ntc_next) < 0)
		return;
#ifdef NTC_DRV_PORT
	/* The divider is only powered while sampling, to limit self-heating. */
	if (!ntc_powered) {
		NTC_DRV_PORT->BSHR = 1u << NTC_DRV_PIN;
		ntc_powered = 1;
		ntc_next = now + NTC_SETTLE_MS;
		return;
	}
	ntc_convert();
	NTC_DRV_PORT->BCR = 1u << NTC_DRV_PIN;
	ntc_powered = 0;
	ntc_next = now + SAMPLE_PERIOD_MS - NTC_SETTLE_MS;
#else
	ntc_convert();
	ntc_next = now + SAMPLE_PERIOD_MS;
#endif
}

void plat_sensor(void *ctx, int16_t *centi_c, uint16_t *raw)
{
	(void)ctx;
	*centi_c = ntc_temp;
	*raw = ntc_raw;
}

/* ---- Identify LED ---------------------------------------------------- */

static uint8_t led_mode;
static uint8_t led_timed;
static uint32_t led_until;

static void led_drive(uint8_t on)
{
	if (on)
		PIN_LOW(LED_PORT, LED_PIN);
	else
		PIN_CFG(LED_PORT, LED_PIN, PIN_FLOAT);
}

void plat_led(void *ctx, uint8_t mode, uint8_t seconds)
{
	(void)ctx;
	led_mode = mode;
	led_timed = seconds != 0;
	led_until = millis() + seconds * 1000u;
	led_drive(mode == MDC_LED_ON);
}

static void led_task(uint32_t now)
{
	if (led_mode == MDC_LED_OFF)
		return;
	if (led_timed && (int32_t)(now - led_until) >= 0) {
		led_mode = MDC_LED_OFF;
		led_drive(0);
	} else if (led_mode == MDC_LED_BLINK) {
		led_drive((now / BLINK_MS) & 1);
	}
}

static int have_bootloader(void)
{
	return *(const uint32_t *)(BOOT_AREA_ADDR + MDC_BOOT_SIG_OFF) == MDC_BOOT_SIG;
}

uint8_t plat_flags(void *ctx)
{
	(void)ctx;
	return (uint8_t)((ntc_temp != MDC_TEMP_INVALID ? MDC_INFO_F_SENSOR : 0) |
			(led_mode != MDC_LED_OFF ? MDC_INFO_F_LED : 0) |
			(have_bootloader() ? MDC_INFO_F_BOOTLDR : 0));
}

/* ---- Restart into the bootloader ------------------------------------ */

static uint8_t boot_pending;
static uint32_t boot_at;

int plat_enter_boot(void *ctx)
{
	(void)ctx;
	if (!have_bootloader())
		return 0;
	up_reply_read = 0;
	boot_pending = 1;
	boot_at = millis() + BOOT_FALLBACK_MS;
	return 1;
}

uint32_t plat_millis(void *ctx)
{
	(void)ctx;
	return millis();
}

/* ---- Main ------------------------------------------------------------ */

static struct relay relay;

/* Lets the hub tool tell which board an application image is for. */
static const char app_tag[] = { 'M', 'D', 'C', '-', 'A', 'P', 'P', ':', BOARD_MCU };

int main(void)
{
	SystemInit();
	RCC->CFGR0 = (RCC->CFGR0 & ~RCC_HPRE) | RCC_HPRE_DIV3;     /* 8 MHz */

	uint32_t reset_flags = RCC->RSTSCKR;
	RCC->RSTSCKR |= RCC_RMVF;

	RCC->APB2PCENR |= BOARD_RCC;

	SysTick->CTLR = 0;
	SysTick->CMP = F_CPU / 1000u - 1;
	SysTick->CNT = 0;
	SysTick->CTLR = SYSTICK_CTLR_STE | SYSTICK_CTLR_STIE | SYSTICK_CTLR_STCLK;
	NVIC_EnableIRQ(SysTick_IRQn);
	__enable_irq();

	/* Idle the downstream hop before anything else. */
	PIN_RELEASE(DN_SCL_PORT, DN_SCL_PIN);
	PIN_RELEASE(DN_SDA_PORT, DN_SDA_PIN);
	led_drive(0);

#if SWIO_SHARED
	/* After power-on, leave SWIO alone for a while so the board can still be
	 * programmed.  The bootloader has already waited if it ran first, which
	 * shows as a software reset on top of the power-on one. */
	if ((reset_flags & (RCC_PORRSTF | RCC_PINRSTF)) && !(reset_flags & RCC_SFTRSTF)) {
		uint32_t t0 = millis();

		while (millis() - t0 < BOOT_WINDOW_MS)
			;
	}
#else
	(void)reset_flags;
#endif

	ntc_init();
	(void)*(volatile const char *)app_tag;      /* keep the tag in the image */
	relay_init(&relay, 0, BOARD_MCU, BOARD_PAGE / MDC_CHUNK, HOP_MS, BASE_MS);
	up_init();

	/* Watchdog: a hung board would cut off everything behind it. */
	IWDG->CTLR = 0x5555;
	IWDG->PSCR = IWDG_Prescaler_128;
	IWDG->CTLR = 0x5555;
	IWDG->RLDR = WATCHDOG_RELOAD;
	IWDG->CTLR = 0xAAAA;
	IWDG->CTLR = 0xCCCC;

	for (;;) {
		uint32_t now = millis();

		IWDG->CTLR = 0xAAAA;
		relay_step(&relay);
		ntc_task(now);
		led_task(now);

		if (boot_pending && (up_reply_read || (int32_t)(now - boot_at) >= 0)) {
			__disable_irq();
			funRebootToBootloader();
		}

		/* Sleep until the next interrupt (the 1 ms tick at the latest). */
		if (!up_rx_ready)
			__WFI();
	}
}
