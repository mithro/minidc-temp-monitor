/* Thermistor reading to temperature.  Shared with the host tests. */
#ifndef MDC_NTC_H
#define MDC_NTC_H

#include <stdint.h>
#include "mdc_proto.h"
#include "ntc_table.h"

/* Readings this close to either rail mean an open or shorted thermistor.
 * The limits are about +126 C and -35 C. */
#define NTC_RAW_MIN  2200u
#define NTC_RAW_MAX  63300u

/* raw is the divider reading scaled to 16 bits (65535 = supply).  Returns the
 * temperature in 0.01 C, or MDC_TEMP_INVALID. */
static inline int16_t ntc_centi_c(uint16_t raw)
{
	if (raw < NTC_RAW_MIN || raw > NTC_RAW_MAX)
		return MDC_TEMP_INVALID;
	uint32_t i = raw >> NTC_SHIFT;
	int32_t frac = raw & ((1 << NTC_SHIFT) - 1);
	int32_t a = ntc_table[i], b = ntc_table[i + 1];

	return (int16_t)(a + ((b - a) * frac) / (1 << NTC_SHIFT));
}

#endif
