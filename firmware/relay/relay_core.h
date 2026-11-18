/*
 * Relay logic of the sensor board, kept free of hardware access so the same
 * code runs on the microcontroller and in the host tests (../test).
 */
#ifndef RELAY_CORE_H
#define RELAY_CORE_H

#include <stdint.h>
#include "mdc_proto.h"

#define RELAY_FW_MAJOR   0
#define RELAY_FW_MINOR   1

#define RELAY_POLL_MS    10     /* gap between reads of a pending downstream reply */

/* Results of plat_dn_write() and plat_dn_read() */
#define DN_OK            0
#define DN_NACK          (-1)   /* address not acknowledged: no board there */
#define DN_ERR           (-2)   /* bus stuck, or data not acknowledged */

struct relay {
	void *ctx;                  /* passed back to every plat_ function */
	uint8_t mcu;                /* MDC_MCU_... */
	uint8_t page_chunks;        /* flash page size / MDC_CHUNK */
	uint16_t hop_ms;            /* time allowed per downstream hop */
	uint16_t base_ms;           /* time allowed at the far end */

	uint8_t waiting;            /* a command is out downstream */
	uint8_t merge;              /* it is our own TEMPS, to be merged */
	uint8_t seq;
	uint8_t dn_err;
	uint32_t deadline;
	uint32_t next_poll;
	uint8_t f[MDC_MAX_FRAME];
};

/* Provided by the platform */
uint8_t  plat_cmd_fetch(void *ctx, uint8_t *frame);             /* length, 0 if none */
void     plat_reply_publish(void *ctx, const uint8_t *frame, uint8_t n);
int      plat_dn_write(void *ctx, const uint8_t *frame, uint8_t n);
int      plat_dn_read(void *ctx, uint8_t *frame);               /* length, 0 if busy, or DN_... */
uint32_t plat_millis(void *ctx);
void     plat_sensor(void *ctx, int16_t *centi_c, uint16_t *raw);
void     plat_led(void *ctx, uint8_t mode, uint8_t seconds);
uint8_t  plat_flags(void *ctx);                                 /* MDC_INFO_F_... */
int      plat_enter_boot(void *ctx);                            /* 0 if there is no bootloader; else
                                                                   restarts once the reply is read */

void relay_init(struct relay *r, void *ctx, uint8_t mcu, uint8_t page_chunks,
		uint16_t hop_ms, uint16_t base_ms);
void relay_step(struct relay *r);

#endif
