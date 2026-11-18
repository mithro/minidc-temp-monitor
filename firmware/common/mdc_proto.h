/*
 * Chain protocol shared by the relay firmware, the bootloader, the host
 * tests and (mirrored in Python) tools/minidc.py.  See ../README.md.
 */
#ifndef MDC_PROTO_H
#define MDC_PROTO_H

#include <stdint.h>

#define MDC_I2C_ADDR       0x2A   /* every board, on its own upstream hop */
#define MDC_PROTO_VERSION  1

/* Command frame, controller to target: hop, seq, cmd, payload, crc16 (LE). */
#define MDC_CMD_HDR        3
/* Reply frame, read back from the target: status, seq, hops, len, payload, crc16 (LE). */
#define MDC_RSP_HDR        4
#define MDC_CRC_LEN        2
#define MDC_MAX_PAYLOAD    66
#define MDC_MAX_FRAME      (MDC_RSP_HDR + MDC_MAX_PAYLOAD + MDC_CRC_LEN)

/* Commands */
#define MDC_CMD_INFO       0x01
#define MDC_CMD_TEMPS      0x02   /* payload: count (1..MDC_TEMPS_MAX) */
#define MDC_CMD_LED        0x03   /* payload: mode, seconds (0 = until changed) */
#define MDC_CMD_ENTER_BOOT 0x10   /* application: restart into the bootloader */
#define MDC_CMD_WRITE      0x11   /* bootloader: addr16 LE, 64 data bytes */
#define MDC_CMD_COMMIT     0x12   /* bootloader: len16 LE, crc16 LE */
#define MDC_CMD_BOOT       0x13   /* bootloader: start the application */

/* Reply status */
#define MDC_ST_OK          0
#define MDC_ST_BUSY        1      /* no reply yet, read again */
#define MDC_ST_BAD_CRC     2
#define MDC_ST_BAD_CMD     3      /* unknown, or not available in this mode */
#define MDC_ST_BAD_ARG     4
#define MDC_ST_NO_DEVICE   5      /* nothing answers on the downstream connector */
#define MDC_ST_TIMEOUT     6      /* downstream board took the command but never replied */
#define MDC_ST_LINK        7      /* downstream bus error */
#define MDC_ST_FLASH       8      /* image CRC does not match after writing */
#define MDC_ST_IN_BOOT     9      /* board is in its bootloader and cannot relay */
#define MDC_ST_NO_APP      10     /* no valid application to start */

/* INFO reply payload */
#define MDC_INFO_LEN       8
#define MDC_MODE_APP       0
#define MDC_MODE_BOOT      1
#define MDC_MCU_CH32V003   3
#define MDC_MCU_CH32V005   5
#define MDC_INFO_F_APP_OK  0x01   /* bootloader: a valid application is present */
#define MDC_INFO_F_SENSOR  0x02   /* application: thermistor reading is in range */
#define MDC_INFO_F_LED     0x04   /* application: identify LED is active */

/* TEMPS reply payload: n, end, then n records of temp (int16 LE, 0.01 C) and
 * raw (uint16 LE, ADC reading scaled to 16 bits, 65535 = VDD). */
#define MDC_TEMPS_MAX      16
#define MDC_TEMPS_REC      4
#define MDC_END_MORE       0      /* count reached, more boards may follow */
#define MDC_END_CHAIN      1      /* the last record is the last board of the chain */
#define MDC_END_ERROR      2      /* the board after the last record failed to answer */
#define MDC_TEMP_INVALID   ((int16_t)-32768)

/* LED modes */
#define MDC_LED_OFF        0
#define MDC_LED_ON         1
#define MDC_LED_BLINK      2

/* Firmware update */
#define MDC_CHUNK          64
#define MDC_MARKER_MAGIC   0x3143444Du   /* "MDC1" */

/* CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, MSB first, no final xor. */
static inline uint16_t mdc_crc16(uint16_t crc, const uint8_t *p, uint32_t n)
{
	while (n--) {
		crc ^= (uint16_t)(*p++) << 8;
		for (int i = 0; i < 8; i++)
			crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
	}
	return crc;
}

/* Append the CRC to a frame of n bytes; returns the new length. */
static inline uint8_t mdc_seal(uint8_t *f, uint8_t n)
{
	uint16_t c = mdc_crc16(0xFFFF, f, n);
	f[n] = (uint8_t)c;
	f[n + 1] = (uint8_t)(c >> 8);
	return (uint8_t)(n + 2);
}

/* True if the n-byte frame ends in a matching CRC. */
static inline int mdc_check(const uint8_t *f, uint8_t n)
{
	if (n < MDC_CRC_LEN)
		return 0;
	uint16_t c = mdc_crc16(0xFFFF, f, (uint32_t)n - 2);
	return f[n - 2] == (uint8_t)c && f[n - 1] == (uint8_t)(c >> 8);
}

#endif
