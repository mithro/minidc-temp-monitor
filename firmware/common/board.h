/*
 * Pin map of the two sensor strip boards, from hardware/README.md.
 * Used by the relay firmware and the bootloader.
 */
#ifndef MDC_BOARD_H
#define MDC_BOARD_H

#include "mdc_proto.h"

#define FLASH_BASE_ADDR    0x08000000u
#define F_CPU              8000000u   /* 24 MHz HSI divided by 3 */

#if defined(CH32V003)

#define BOARD_MCU          MDC_MCU_CH32V003
#define BOARD_FLASH_SIZE   16384u
#define BOOT_AREA_ADDR     0x1FFFF000u
#define BOARD_PAGE         64u
#define BOARD_ADC_BITS     10

#define UP_PORT            GPIOC      /* hardware I2C1, default mapping */
#define UP_SDA_PIN         1
#define UP_SCL_PIN         2
#define UP_RCC             RCC_APB2Periph_GPIOC
#define UP_I2C_REMAP       0

#define DN_SDA_PORT        GPIOC
#define DN_SDA_PIN         4
#define DN_SCL_PORT        GPIOA
#define DN_SCL_PIN         2

#define NTC_PORT           GPIOA      /* PA1 = A1, bonded with PD6 on pin 1; divider fed from VDD */
#define NTC_PIN            1
#define NTC_ADC_CH         1

#define LED_PORT           GPIOD      /* PD4, bonded with SWIO (PD1) on pin 8 */
#define LED_PIN            4

#define BOARD_RCC          (RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOC | RCC_APB2Periph_GPIOD | RCC_APB2Periph_AFIO)

/* SWIO has its own pin, so no programming window is needed. */
#define SWIO_SHARED        0
#define BOOT_WINDOW_MS     50

#elif defined(CH32V005)

#define BOARD_MCU          MDC_MCU_CH32V005
#define BOARD_FLASH_SIZE   32768u
#define BOOT_AREA_ADDR     0x1FFF0000u
#define BOARD_PAGE         256u
#define BOARD_ADC_BITS     12

#define UP_PORT            GPIOD      /* hardware I2C1, remap 1; PD1 is also SWIO */
#define UP_SDA_PIN         0
#define UP_SCL_PIN         1
#define UP_RCC             RCC_APB2Periph_GPIOD
#define UP_I2C_REMAP       AFIO_PCFR1_I2C1_RM_0

#define DN_SDA_PORT        GPIOC
#define DN_SDA_PIN         0
#define DN_SCL_PORT        GPIOC
#define DN_SCL_PIN         3

#define NTC_PORT           GPIOC      /* PC4 = A2, divider fed from PC6 */
#define NTC_PIN            4
#define NTC_ADC_CH         2
#define NTC_DRV_PORT       GPIOC
#define NTC_DRV_PIN        6
#define NTC_SETTLE_MS      30

#define LED_PORT           GPIOA
#define LED_PIN            2

#define BOARD_RCC          (RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOC | RCC_APB2Periph_GPIOD | RCC_APB2Periph_AFIO)

/* SCL to J1 is the SWIO pin.  The debug interface stays on for this long
 * after a power-on reset so a programmer can still get in. */
#define SWIO_SHARED        1
#define BOOT_WINDOW_MS     500

#else
#error "Build with -DCH32V003 or -DCH32V005"
#endif

/* The last flash page holds the image marker written by the bootloader. */
#define BOARD_APP_LIMIT    (BOARD_FLASH_SIZE - BOARD_PAGE)

/* GPIO configuration nibbles (CNF:MODE) */
#define PIN_ANALOG         0x0
#define PIN_FLOAT          0x4
#define PIN_PULL           0x8   /* pull-up when the output bit is 1 */
#define PIN_OUT_PP         0x1
#define PIN_OUT_OD         0x5
#define PIN_AF_OD          0xD

#define PIN_CFG(port, pin, mode) \
	((port)->CFGLR = ((port)->CFGLR & ~(0xFu << (4 * (pin)))) | ((uint32_t)(mode) << (4 * (pin))))

/* Open-drain style drive that also works without external pull-ups: low is an
 * open-drain output, released is an input with the internal pull-up. */
#define PIN_LOW(port, pin)     do { (port)->BCR = 1u << (pin); PIN_CFG(port, pin, PIN_OUT_OD); } while (0)
#define PIN_RELEASE(port, pin) do { PIN_CFG(port, pin, PIN_PULL); (port)->BSHR = 1u << (pin); } while (0)
#define PIN_READ(port, pin)    (((port)->INDR >> (pin)) & 1u)

#endif
