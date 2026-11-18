#include <string.h>
#include "relay_core.h"

void relay_init(struct relay *r, void *ctx, uint8_t mcu, uint8_t page_chunks,
		uint16_t hop_ms, uint16_t base_ms)
{
	memset(r, 0, sizeof(*r));
	r->ctx = ctx;
	r->mcu = mcu;
	r->page_chunks = page_chunks;
	r->hop_ms = hop_ms;
	r->base_ms = base_ms;
}

/* Publish a reply whose payload is already in place at f[MDC_RSP_HDR]. */
static void reply(struct relay *r, uint8_t status, uint8_t hops, uint8_t len)
{
	r->f[0] = status;
	r->f[1] = r->seq;
	r->f[2] = hops;
	r->f[3] = len;
	r->waiting = 0;
	plat_reply_publish(r->ctx, r->f, mdc_seal(r->f, (uint8_t)(MDC_RSP_HDR + len)));
}

static void put_record(struct relay *r, uint8_t *p)
{
	int16_t t;
	uint16_t raw;

	plat_sensor(r->ctx, &t, &raw);
	p[0] = (uint8_t)t;
	p[1] = (uint8_t)((uint16_t)t >> 8);
	p[2] = (uint8_t)raw;
	p[3] = (uint8_t)(raw >> 8);
}

/* TEMPS reply holding only this board. */
static void temps_alone(struct relay *r, uint8_t end)
{
	uint8_t *p = r->f + MDC_RSP_HDR;

	p[0] = 1;
	p[1] = end;
	put_record(r, p + 2);
	reply(r, MDC_ST_OK, 0, 2 + MDC_TEMPS_REC);
}

/* Send the n-byte command in f downstream and start waiting for its reply.
 * hops is how many boards the command still has to travel through. */
static int forward(struct relay *r, uint8_t n, uint16_t hops)
{
	int rc = plat_dn_write(r->ctx, r->f, n);

	if (rc != DN_OK)
		return rc;
	uint32_t now = plat_millis(r->ctx);
	r->waiting = 1;
	r->dn_err = 0;
	r->deadline = now + (uint32_t)hops * r->hop_ms + r->base_ms;
	r->next_poll = now + RELAY_POLL_MS;
	return DN_OK;
}

static void command(struct relay *r, uint8_t n)
{
	uint8_t *f = r->f;
	uint8_t *p = f + MDC_RSP_HDR;

	r->waiting = 0;
	r->merge = 0;
	r->seq = n >= 2 ? f[1] : 0;
	if (n < MDC_CMD_HDR + MDC_CRC_LEN || !mdc_check(f, n)) {
		reply(r, MDC_ST_BAD_CRC, 0, 0);
		return;
	}

	if (f[0] != 0) {                    /* not for us: pass it on */
		uint16_t hops = f[0];

		/* A TEMPS sweep travels on past its target, so allow for that too. */
		if (f[2] == MDC_CMD_TEMPS && n == MDC_CMD_HDR + 1 + MDC_CRC_LEN && f[3] <= MDC_TEMPS_MAX)
			hops = (uint16_t)(hops + f[3]);
		f[0]--;
		mdc_seal(f, (uint8_t)(n - MDC_CRC_LEN));
		int rc = forward(r, n, hops);
		if (rc != DN_OK)
			reply(r, rc == DN_NACK ? MDC_ST_NO_DEVICE : MDC_ST_LINK, 0, 0);
		return;
	}

	uint8_t cmd = f[2];
	uint8_t plen = (uint8_t)(n - MDC_CMD_HDR - MDC_CRC_LEN);
	uint8_t a0 = f[3], a1 = f[4];

	switch (cmd) {
	case MDC_CMD_INFO:
		p[0] = MDC_MODE_APP;
		p[1] = r->mcu;
		p[2] = MDC_PROTO_VERSION;
		p[3] = RELAY_FW_MAJOR;
		p[4] = RELAY_FW_MINOR;
		p[5] = plat_flags(r->ctx);
		p[6] = r->page_chunks;
		p[7] = 0;
		reply(r, MDC_ST_OK, 0, MDC_INFO_LEN);
		break;

	case MDC_CMD_TEMPS:
		if (plen != 1 || a0 < 1 || a0 > MDC_TEMPS_MAX) {
			reply(r, MDC_ST_BAD_ARG, 0, 0);
			break;
		}
		if (a0 == 1) {
			temps_alone(r, MDC_END_MORE);
			break;
		}
		/* Ask the next board for the rest, then put our record in front. */
		f[0] = 0;
		f[2] = MDC_CMD_TEMPS;
		f[3] = (uint8_t)(a0 - 1);
		{
			int rc = forward(r, mdc_seal(f, MDC_CMD_HDR + 1), a0);
			if (rc != DN_OK)
				temps_alone(r, rc == DN_NACK ? MDC_END_CHAIN : MDC_END_ERROR);
			else
				r->merge = 1;
		}
		break;

	case MDC_CMD_LED:
		if (plen != 2 || a0 > MDC_LED_BLINK) {
			reply(r, MDC_ST_BAD_ARG, 0, 0);
			break;
		}
		plat_led(r->ctx, a0, a1);
		reply(r, MDC_ST_OK, 0, 0);
		break;

	case MDC_CMD_ENTER_BOOT:
		/* Without our bootloader there would be no way back. */
		reply(r, plat_enter_boot(r->ctx) ? MDC_ST_OK : MDC_ST_BAD_CMD, 0, 0);
		break;

	case MDC_CMD_BOOT:                  /* already running the application */
		reply(r, MDC_ST_OK, 0, 0);
		break;

	default:
		reply(r, MDC_ST_BAD_CMD, 0, 0);
		break;
	}
}

/* A complete, checked reply from downstream is in f. */
static void dn_reply(struct relay *r)
{
	uint8_t *f = r->f;
	uint8_t *p = f + MDC_RSP_HDR;

	if (!r->merge) {
		reply(r, f[0], (uint8_t)(f[2] + 1), f[3]);
		return;
	}
	uint8_t n = p[0];
	if (f[0] != MDC_ST_OK || n < 1 || n >= MDC_TEMPS_MAX || f[3] != 2 + n * MDC_TEMPS_REC) {
		temps_alone(r, MDC_END_ERROR);
		return;
	}
	memmove(p + 2 + MDC_TEMPS_REC, p + 2, (size_t)n * MDC_TEMPS_REC);
	p[0] = (uint8_t)(n + 1);
	put_record(r, p + 2);
	reply(r, MDC_ST_OK, 0, (uint8_t)(f[3] + MDC_TEMPS_REC));
}

void relay_step(struct relay *r)
{
	uint8_t n = plat_cmd_fetch(r->ctx, r->f);

	if (n) {
		command(r, n);
		return;
	}
	if (!r->waiting)
		return;

	uint32_t now = plat_millis(r->ctx);
	if ((int32_t)(now - r->next_poll) < 0)
		return;

	int len = plat_dn_read(r->ctx, r->f);
	if (len < 0)
		r->dn_err = 1;
	else if (len > 0)
		r->dn_err = !(len >= MDC_RSP_HDR + MDC_CRC_LEN && mdc_check(r->f, (uint8_t)len) &&
				r->f[3] == len - MDC_RSP_HDR - MDC_CRC_LEN);
	else
		r->dn_err = 0;

	if (len > 0 && !r->dn_err && r->f[1] == r->seq && r->f[0] != MDC_ST_BUSY) {
		dn_reply(r);
		return;
	}

	now = plat_millis(r->ctx);
	if ((int32_t)(now - r->deadline) >= 0) {
		if (r->merge)
			temps_alone(r, MDC_END_ERROR);
		else
			reply(r, r->dn_err ? MDC_ST_LINK : MDC_ST_TIMEOUT, 0, 0);
		return;
	}
	r->next_poll = now + RELAY_POLL_MS;
}
