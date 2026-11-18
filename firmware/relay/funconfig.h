#ifndef _FUNCONFIG_H
#define _FUNCONFIG_H

/* 24 MHz internal oscillator, no PLL.  main() then divides it by 3: the
 * board has little to do, and a slow clock keeps its own heat away from the
 * thermistor. */
#define FUNCONF_USE_HSI 1
#define FUNCONF_USE_PLL 0
#define FUNCONF_SYSTEM_CORE_CLOCK 24000000

/* No debug printf: on the CH32V005 the SWIO pin is the I2C clock. */
#define FUNCONF_USE_DEBUGPRINTF 0
#define FUNCONF_DEBUG_HARDFAULT 0

#endif
