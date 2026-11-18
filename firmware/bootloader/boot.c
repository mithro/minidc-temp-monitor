/*
 * I2C bootloader for the sensor strip boards, living in the boot area
 * (1920 bytes on the CH32V003, 3328 bytes on the CH32V005).
 *
 * It runs first after power-on (START_MODE option bit).  It starts the
 * application unless the application asked for the bootloader, the image
 * marker is missing or wrong, or upstream SDA is held low during the boot
 * window.  A low SDA is copied to the downstream connector, so holding SDA low
 * while powering a chain up stops every board in its bootloader.
 *
 * No interrupts, no static data.  See ../README.md for the protocol.
 */
#include "ch32fun.h"
#include "board.h"

#define BOOT_MCU        BOARD_MCU
#define BOOT_PAGE       BOARD_PAGE
#define BOOT_APP_LIMIT  BOARD_APP_LIMIT

#define HOLD_US         10000u      /* SDA low this long means "stay" */
#define RESET_FLAGS     (RCC_PINRSTF | RCC_PORRSTF | RCC_SFTRSTF | RCC_IWDGRSTF)

static inline const uint8_t *fl_ptr(uint32_t off)
{
	return (const uint8_t *)(FLASH_BASE_ADDR + off);
}

static void fl_op(uint32_t ctlr)
{
	FLASH->CTLR = ctlr;
	while (FLASH->STATR & FLASH_STATR_BSY)
		;
}

static void fl_erase(uint32_t page)
{
	FLASH->CTLR = CR_PAGE_ER;
	FLASH->ADDR = FLASH_BASE_ADDR + page;
	fl_op(CR_PAGE_ER | CR_STRT_Set);
}

static void fl_begin(uint32_t page)
{
	fl_erase(page);
	FLASH->CTLR = CR_PAGE_PG;
	FLASH->ADDR = FLASH_BASE_ADDR + page;
	fl_op(CR_PAGE_PG | CR_BUF_RST);
}

static void fl_load(uint32_t off, uint32_t w)
{
	*(volatile uint32_t *)(FLASH_BASE_ADDR + off) = w;
	fl_op(CR_PAGE_PG | CR_BUF_LOAD);
}

static void fl_commit(uint32_t page)
{
	FLASH->ADDR = FLASH_BASE_ADDR + page;
	fl_op(CR_PAGE_PG | CR_STRT_Set);
}

#include "boot_core.h"

/* Leave the boot area: clear the boot mode bit and reset into user flash. */
static void __attribute__((noreturn)) start_app(void)
{
	FLASH->BOOT_MODEKEYR = FLASH_KEY1;
	FLASH->BOOT_MODEKEYR = FLASH_KEY2;
	FLASH->STATR = 0;
	FLASH->CTLR = CR_LOCK_Set;
	PFIC->SCTLR = 1u << 31;
	for (;;)
		;
}

void __attribute__((noreturn, used)) boot_main(void)
{
	struct boot b;
	uint8_t *f = BOOT_FRAME(&b);
	uint8_t idx = 0, rx = 0;

	RCC->CFGR0 = RCC_HPRE_DIV3;                 /* 24 MHz HSI / 3 = 8 MHz */
	RCC->APB2PCENR = BOARD_RCC;
	RCC->APB1PCENR = RCC_APB1Periph_I2C1;
	SysTick->CTLR = SYSTICK_CTLR_STE;           /* HCLK / 8 = 1 MHz */

	FLASH->KEYR = FLASH_KEY1;
	FLASH->KEYR = FLASH_KEY2;
	FLASH->MODEKEYR = FLASH_KEY1;
	FLASH->MODEKEYR = FLASH_KEY2;

	/* Idle the downstream hop, in case it has no pull-up resistors. */
	PIN_RELEASE(DN_SCL_PORT, DN_SCL_PIN);
	PIN_RELEASE(DN_SDA_PORT, DN_SDA_PIN);

	/* Only a software reset on its own means the application sent us here. */
	int stay = (RCC->RSTSCKR & RESET_FLAGS) == RCC_SFTRSTF;

	if (!stay) {
		uint32_t high_at = 0;

		/* Plain input: the only pull-ups on the upstream hop are the ones on
		 * the board or hub before us. */
		PIN_CFG(UP_PORT, UP_SDA_PIN, PIN_FLOAT);
		for (;;) {
			uint32_t t = SysTick->CNT;

			if (PIN_READ(UP_PORT, UP_SDA_PIN)) {
				PIN_RELEASE(DN_SDA_PORT, DN_SDA_PIN);
				high_at = t;
				if (t >= BOOT_WINDOW_MS * 1000u)
					break;
			} else {
				PIN_LOW(DN_SDA_PORT, DN_SDA_PIN);
				if (t - high_at >= HOLD_US)
					stay = 1;
			}
		}
	}

	boot_init(&b);
	if (!stay && b.app_ok)
		start_app();

#if SWIO_SHARED
	AFIO->PCFR1 = UP_I2C_REMAP | AFIO_PCFR1_SWCFG_2;    /* SCL takes over the SWIO pin */
#endif
	PIN_CFG(UP_PORT, UP_SDA_PIN, PIN_AF_OD);
	PIN_CFG(UP_PORT, UP_SCL_PIN, PIN_AF_OD);
	I2C1->CTLR2 = F_CPU / 1000000u;
	I2C1->OADDR1 = MDC_I2C_ADDR << 1;
	I2C1->CTLR1 = I2C_CTLR1_PE;
	I2C1->CTLR1 = I2C_CTLR1_PE | I2C_CTLR1_ACK;

	for (;;) {
		uint32_t s1 = I2C1->STAR1;

		IWDG->CTLR = 0xAAAA;                    /* in case a watchdog is running */

		/* The data and stop of a finished write come before a new address. */
		if (s1 & I2C_STAR1_RXNE) {
			uint8_t d = (uint8_t)I2C1->DATAR;

			if (idx < MDC_MAX_FRAME)
				f[idx] = d;
			if (idx < 255)
				idx++;
		}
		if (s1 & I2C_STAR1_STOPF) {             /* end of a write to us */
			I2C1->CTLR1 = I2C_CTLR1_PE | I2C_CTLR1_ACK;
			if (rx) {
				/* Flash work takes a while.  Do not acknowledge our address
				 * meanwhile, rather than hold the clock for that long. */
				I2C1->CTLR1 = I2C_CTLR1_PE;
				/* An over-long frame is cut short and fails its CRC. */
				boot_handle(&b, idx > MDC_MAX_FRAME ? MDC_MAX_FRAME : idx);
				I2C1->CTLR1 = I2C_CTLR1_PE | I2C_CTLR1_ACK;
				rx = 0;
			}
		}
		if (s1 & I2C_STAR1_ADDR) {              /* addressed: reading STAR2 clears it */
			if (!(I2C1->STAR2 & I2C_STAR2_TRA))
				rx = 1;
			idx = 0;
		}
		if (s1 & I2C_STAR1_TXE) {
			I2C1->DATAR = idx < b.tx_len ? f[idx] : 0xFF;
			idx++;
		}
		if (s1 & I2C_STAR1_AF) {                /* end of a read from us */
			I2C1->STAR1 = ~I2C_STAR1_AF;
			if (b.boot_req)
				start_app();
		}
		if (s1 & (I2C_STAR1_BERR | I2C_STAR1_ARLO | I2C_STAR1_OVR))
			I2C1->STAR1 = ~(I2C_STAR1_BERR | I2C_STAR1_ARLO | I2C_STAR1_OVR);
	}
}

void __attribute__((naked, used, section(".init"))) _start(void)
{
	__asm__ volatile(
		".option push\n"
		".option norelax\n"
		".option norvc\n"
		"la sp, _eusrstack\n"
		"j boot_main\n"
		".word 0x3142444d\n"            /* MDC_BOOT_SIG at MDC_BOOT_SIG_OFF */
		".option pop\n");
}
