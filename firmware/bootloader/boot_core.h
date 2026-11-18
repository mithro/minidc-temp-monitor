/*
 * Bootloader command handling, kept free of hardware access so the same code
 * runs in the boot area and in the host tests (../test).
 *
 * The file that includes this must first define BOOT_MCU, BOOT_PAGE (flash
 * page size in bytes) and BOOT_APP_LIMIT (size of the application area, the
 * image marker page starts there), and these functions, all taking offsets
 * from the start of user flash:
 *
 *   const uint8_t *fl_ptr(uint32_t off)      read access
 *   void fl_erase(uint32_t page)             erase one page
 *   void fl_begin(uint32_t page)             erase one page and clear the page buffer
 *   void fl_load(uint32_t off, uint32_t w)   put one word in the page buffer
 *   void fl_commit(uint32_t page)            program the page buffer
 */
#ifndef BOOT_CORE_H
#define BOOT_CORE_H

#include "mdc_proto.h"

#define BOOT_FW_MAJOR  0
#define BOOT_FW_MINOR  1

struct boot {
	/* The frame starts 3 bytes into the store, which puts the 64 data bytes
	 * of a WRITE (frame offset 5) on a word boundary. */
	uint32_t store[(3 + MDC_MAX_FRAME + 3) / 4];
	uint16_t next;       /* offset the next WRITE must carry */
	uint8_t tx_len;      /* length of the reply now held in the frame */
	uint8_t app_ok;      /* a valid image marker is present */
	uint8_t boot_req;    /* start the application once the reply is read */
};

#define BOOT_FRAME(b)  ((uint8_t *)(b)->store + 3)

struct boot_marker {
	uint32_t magic;
	uint32_t len;
	uint32_t crc;
};

static int boot_app_valid(void)
{
	const struct boot_marker *m = (const struct boot_marker *)(const void *)fl_ptr(BOOT_APP_LIMIT);

	return m->magic == MDC_MARKER_MAGIC && m->len != 0 && m->len <= BOOT_APP_LIMIT &&
		mdc_crc16(0xFFFF, fl_ptr(0), m->len) == m->crc;
}

static void boot_init(struct boot *b)
{
	b->next = 0xFFFF;
	b->tx_len = 0;
	b->boot_req = 0;
	b->app_ok = (uint8_t)boot_app_valid();
}

/* Handle the n-byte command in the frame and leave the reply there. */
static void boot_handle(struct boot *b, uint8_t n)
{
	uint8_t *f = BOOT_FRAME(b);
	uint8_t *p = f + MDC_RSP_HDR;
	uint8_t st = MDC_ST_OK, len = 0;
	uint8_t seq = n >= 2 ? f[1] : 0;

	if (n < MDC_CMD_HDR + MDC_CRC_LEN || !mdc_check(f, n)) {
		st = MDC_ST_BAD_CRC;
	} else if (f[0] != 0) {
		st = MDC_ST_IN_BOOT;
	} else {
		uint8_t plen = (uint8_t)(n - MDC_CMD_HDR - MDC_CRC_LEN);
		uint32_t w0 = f[3] | ((uint32_t)f[4] << 8);
		uint32_t w1 = f[5] | ((uint32_t)f[6] << 8);

		switch (f[2]) {
		case MDC_CMD_INFO:
			p[0] = MDC_MODE_BOOT;
			p[1] = BOOT_MCU;
			p[2] = MDC_PROTO_VERSION;
			p[3] = BOOT_FW_MAJOR;
			p[4] = BOOT_FW_MINOR;
			p[5] = b->app_ok ? MDC_INFO_F_APP_OK : 0;
			p[6] = BOOT_PAGE / MDC_CHUNK;
			p[7] = 0;
			len = MDC_INFO_LEN;
			break;

		case MDC_CMD_ENTER_BOOT:        /* already here */
			break;

		case MDC_CMD_WRITE:
			if (plen != 2 + MDC_CHUNK || (w0 & (MDC_CHUNK - 1)) || w0 >= BOOT_APP_LIMIT) {
				st = MDC_ST_BAD_ARG;
				break;
			}
			if ((w0 & (BOOT_PAGE - 1)) != 0 && w0 != b->next) {
				st = MDC_ST_BAD_ARG;    /* chunks of a page must come in order */
				break;
			}
			if (b->app_ok) {            /* the old image stops being valid here */
				fl_erase(BOOT_APP_LIMIT);
				b->app_ok = 0;
			}
			if ((w0 & (BOOT_PAGE - 1)) == 0)
				fl_begin(w0);
			{
				const uint32_t *d = (const uint32_t *)(const void *)(f + MDC_CMD_HDR + 2);

				for (uint32_t i = 0; i < MDC_CHUNK / 4; i++)
					fl_load(w0 + 4 * i, d[i]);
			}
			b->next = (uint16_t)(w0 + MDC_CHUNK);
			if ((b->next & (BOOT_PAGE - 1)) == 0) {
				fl_commit(b->next - BOOT_PAGE);
				b->next = 0xFFFF;
			}
			break;

		case MDC_CMD_COMMIT:
			if (plen != 4 || w0 == 0 || w0 > BOOT_APP_LIMIT) {
				st = MDC_ST_BAD_ARG;
				break;
			}
			b->next = 0xFFFF;
			if (mdc_crc16(0xFFFF, fl_ptr(0), w0) != w1) {
				st = MDC_ST_FLASH;
				break;
			}
			fl_begin(BOOT_APP_LIMIT);
			for (uint32_t i = 0; i < BOOT_PAGE; i += 4)
				fl_load(BOOT_APP_LIMIT + i,
					i == 0 ? MDC_MARKER_MAGIC : i == 4 ? w0 : i == 8 ? w1 : 0xFFFFFFFFu);
			fl_commit(BOOT_APP_LIMIT);
			{
				/* The image was checked just above; read the marker back. */
				const struct boot_marker *m =
					(const struct boot_marker *)(const void *)fl_ptr(BOOT_APP_LIMIT);

				b->app_ok = m->magic == MDC_MARKER_MAGIC && m->len == w0 && m->crc == w1;
			}
			if (!b->app_ok)
				st = MDC_ST_FLASH;
			break;

		case MDC_CMD_BOOT:
			if (b->app_ok)
				b->boot_req = 1;
			else
				st = MDC_ST_NO_APP;
			break;

		default:
			st = MDC_ST_BAD_CMD;
			break;
		}
	}

	f[0] = st;
	f[1] = seq;
	f[2] = 0;
	f[3] = len;
	b->tx_len = mdc_seal(f, (uint8_t)(MDC_RSP_HDR + len));
}

#endif
