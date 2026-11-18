/*
 * Host simulation of a chain of sensor boards.
 *
 * Every board runs the real relay_core.c and boot_core.h; only the hardware
 * underneath (I2C hops, flash, clock, thermistor) is modelled here.  Run with
 * no arguments for the self-tests, or with "serve N" to act as a chain of N
 * boards for tools/minidc.py (commands on stdin, replies on stdout).
 *
 * Built twice, with -DSIM_V005 for the CH32V005 flash layout.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include "mdc_proto.h"
#include "ntc.h"
#include "relay_core.h"

#ifdef SIM_V005
#define BOOT_MCU        MDC_MCU_CH32V005
#define BOOT_PAGE       256u
#define SIM_FLASH       32768u
#else
#define BOOT_MCU        MDC_MCU_CH32V003
#define BOOT_PAGE       64u
#define SIM_FLASH       16384u
#endif
#define BOOT_APP_LIMIT  (SIM_FLASH - BOOT_PAGE)

#define MAX_BOARDS      250
#define BYTE_US         900     /* one byte on a 10 kHz hop */
#define SIM_HOP_MS      160
#define SIM_BASE_MS     500

struct board;
static struct board *cur;       /* board whose flash the fl_ functions use */

struct board {
	int index;
	int present;                /* 0: nothing answers at this position */
	int hung;                   /* takes commands, never replies */
	int no_bootloader;          /* application only, nothing in the boot area */
	int in_boot;
	uint16_t raw;               /* simulated thermistor reading */

	/* application side */
	struct relay relay;
	uint8_t rx[MDC_MAX_FRAME], rx_len, rx_ready, busy;
	uint64_t rx_at;             /* when the frame in rx has fully arrived */
	uint64_t busy_until;        /* the board is inside a downstream transfer until then */
	uint8_t tx[MDC_MAX_FRAME], tx_len;
	int boot_pending;
	uint8_t led_mode, led_secs;

	/* bootloader side */
	_Alignas(4) uint8_t flash[SIM_FLASH];
	uint8_t pagebuf[BOOT_PAGE];
	int erases, programs;
	void *boot;                 /* struct boot, defined below */
};

static const uint8_t *fl_ptr(uint32_t off) { return cur->flash + off; }

static void fl_erase(uint32_t page)
{
	if (page % BOOT_PAGE || page >= SIM_FLASH) { fprintf(stderr, "bad erase %u\n", (unsigned)page); exit(2); }
	memset(cur->flash + page, 0xFF, BOOT_PAGE);
	cur->erases++;
}

static void fl_begin(uint32_t page)
{
	fl_erase(page);
	memset(cur->pagebuf, 0xFF, BOOT_PAGE);
}

static void fl_load(uint32_t off, uint32_t w)
{
	memcpy(cur->pagebuf + off % BOOT_PAGE, &w, 4);
}

static void fl_commit(uint32_t page)
{
	if (page % BOOT_PAGE || page >= SIM_FLASH) { fprintf(stderr, "bad program %u\n", (unsigned)page); exit(2); }
	/* Flash can only clear bits, as on the real part. */
	for (uint32_t i = 0; i < BOOT_PAGE; i++)
		cur->flash[page + i] &= cur->pagebuf[i];
	cur->programs++;
}

#include "boot_core.h"

static struct board *boards;
static int n_boards;
static uint64_t now_us;         /* boards run in parallel on this clock */
#define now_ms ((uint32_t)(now_us / 1000))
static unsigned corrupt_every;      /* flip a bit in every Nth frame between boards */
static unsigned frame_count;

/* The board spends this long in a downstream transfer.  Only its own clock
 * moves: the other boards carry on meanwhile. */
static uint64_t spend(struct board *b, uint32_t us)
{
	if (b->busy_until < now_us)
		b->busy_until = now_us;
	b->busy_until += us;
	return b->busy_until;
}

static void board_reset(struct board *b, int to_boot)
{
	b->rx_ready = b->busy = 0;
	b->busy_until = 0;
	b->boot_pending = 0;
	b->led_mode = 0;
	cur = b;
	boot_init(b->boot);
	b->in_boot = to_boot || !((struct boot *)b->boot)->app_ok;
	relay_init(&b->relay, b, BOOT_MCU, BOOT_PAGE / MDC_CHUNK, SIM_HOP_MS, SIM_BASE_MS);
	uint8_t *t = b->tx;
	t[0] = MDC_ST_BUSY; t[1] = t[2] = t[3] = 0;
	b->tx_len = mdc_seal(t, MDC_RSP_HDR);
}

/* A controller writes a frame to board b, complete at time at.  Returns 0, or
 * -1 for no answer. */
static int up_write(struct board *b, const uint8_t *f, uint8_t n, uint64_t at)
{
	if (!b || !b->present)
		return -1;
	if (b->hung)
		return 0;
	if (b->in_boot) {
		struct boot *bt = b->boot;

		cur = b;
		memcpy(BOOT_FRAME(bt), f, n);
		boot_handle(bt, n);
		return 0;
	}
	memcpy(b->rx, f, n);
	b->rx_len = n;
	b->rx_at = at;
	b->rx_ready = 1;
	b->busy = 1;
	return 0;
}

/* A controller reads up to max bytes from board b.  Returns the number of
 * real bytes (the rest of out is 0xFF), or -1 for no answer. */
static int up_read(struct board *b, uint8_t *out, int max)
{
	static const uint8_t busy[] = { MDC_ST_BUSY, 0, 0, 0 };
	uint8_t tmp[MDC_RSP_HDR + MDC_CRC_LEN];
	const uint8_t *src;
	int n;

	memset(out, 0xFF, (size_t)max);
	if (!b || !b->present)
		return -1;
	if (b->in_boot) {
		struct boot *bt = b->boot;

		src = BOOT_FRAME(bt);
		n = bt->tx_len;
	} else if (b->busy || b->hung) {
		memcpy(tmp, busy, sizeof(busy));
		n = mdc_seal(tmp, MDC_RSP_HDR);
		src = tmp;
	} else {
		src = b->tx;
		n = b->tx_len;
	}
	if (n > max)
		n = max;
	memcpy(out, src, (size_t)n);

	/* Restarts happen once the whole reply has been read. */
	if (b->in_boot) {
		struct boot *bt = b->boot;

		if (bt->boot_req && max >= bt->tx_len)
			board_reset(b, 0);
	} else if (b->boot_pending && !b->busy && max >= b->tx_len) {
		board_reset(b, 1);
	}
	return n;
}

static void maybe_corrupt(uint8_t *f, int n)
{
	if (corrupt_every && n > 0 && ++frame_count % corrupt_every == 0)
		f[(frame_count / corrupt_every) % (unsigned)n] ^= 0x10;
}

/* ---- platform functions for relay_core.c ---- */

uint8_t plat_cmd_fetch(void *ctx, uint8_t *frame)
{
	struct board *b = ctx;
	uint8_t n = 0;

	if (b->rx_ready && now_us >= b->rx_at) {
		n = b->rx_len;
		memcpy(frame, b->rx, n);
		b->rx_ready = 0;
	}
	return n;
}

void plat_reply_publish(void *ctx, const uint8_t *frame, uint8_t n)
{
	struct board *b = ctx;

	if (b->rx_ready)
		return;
	memcpy(b->tx, frame, n);
	b->tx_len = n;
	b->busy = 0;
}

static struct board *next_board(struct board *b)
{
	return b->index + 1 < n_boards ? &boards[b->index + 1] : NULL;
}

int plat_dn_write(void *ctx, const uint8_t *frame, uint8_t n)
{
	uint8_t f[MDC_MAX_FRAME];

	memcpy(f, frame, n);
	maybe_corrupt(f, n);
	if (!next_board(ctx) || !next_board(ctx)->present) {
		spend(ctx, BYTE_US);
		return DN_NACK;
	}
	up_write(next_board(ctx), f, n, spend(ctx, (uint32_t)(n + 1) * BYTE_US));
	return DN_OK;
}

int plat_dn_read(void *ctx, uint8_t *frame)
{
	int n = up_read(next_board(ctx), frame, MDC_MAX_FRAME);

	if (n < 0) {
		spend(ctx, BYTE_US);
		return DN_NACK;
	}
	maybe_corrupt(frame, n);
	if (frame[0] == MDC_ST_BUSY) {
		spend(ctx, 5 * BYTE_US);
		return 0;
	}
	if (frame[3] > MDC_MAX_PAYLOAD) {
		spend(ctx, 5 * BYTE_US);
		return DN_ERR;
	}
	spend(ctx, (uint32_t)(n + 1) * BYTE_US);
	return MDC_RSP_HDR + frame[3] + MDC_CRC_LEN;
}

uint32_t plat_millis(void *ctx)
{
	struct board *b = ctx;

	return (uint32_t)((b->busy_until > now_us ? b->busy_until : now_us) / 1000);
}

void plat_sensor(void *ctx, int16_t *centi_c, uint16_t *raw)
{
	struct board *b = ctx;

	*raw = b->raw;
	*centi_c = ntc_centi_c(b->raw);
}

void plat_led(void *ctx, uint8_t mode, uint8_t seconds)
{
	struct board *b = ctx;

	b->led_mode = mode;
	b->led_secs = seconds;
}

uint8_t plat_flags(void *ctx)
{
	struct board *b = ctx;

	return (uint8_t)((ntc_centi_c(b->raw) != MDC_TEMP_INVALID ? MDC_INFO_F_SENSOR : 0) |
			(b->led_mode ? MDC_INFO_F_LED : 0) | (b->no_bootloader ? 0 : MDC_INFO_F_BOOTLDR));
}

int plat_enter_boot(void *ctx)
{
	struct board *b = ctx;

	if (b->no_bootloader)
		return 0;
	b->boot_pending = 1;
	return 1;
}

/* ---- the chain ---- */

/* Thermistor reading for a temperature, by searching the firmware's table. */
static uint16_t raw_for(int centi_c)
{
	uint16_t lo = NTC_RAW_MIN, hi = NTC_RAW_MAX;

	while (lo < hi) {
		uint16_t mid = (uint16_t)((lo + hi) / 2);

		if (ntc_centi_c(mid) > centi_c)
			lo = (uint16_t)(mid + 1);
		else
			hi = mid;
	}
	return lo;
}

static void chain_init(int n, int with_app)
{
	for (int i = 0; i < n_boards; i++)
		free(boards[i].boot);
	free(boards);
	boards = n ? calloc((size_t)n, sizeof(*boards)) : NULL;
	n_boards = n;
	now_us = 0;
	corrupt_every = frame_count = 0;
	for (int i = 0; i < n; i++) {
		struct board *b = &boards[i];

		b->index = i;
		b->present = 1;
		b->raw = raw_for(2000 + 10 * i);    /* 20.00 C plus 0.10 C per board */
		b->boot = calloc(1, sizeof(struct boot));
		memset(b->flash, 0xFF, sizeof(b->flash));
		if (with_app) {                     /* a small valid image and its marker */
			struct boot_marker m = { MDC_MARKER_MAGIC, 256, 0 };

			for (int k = 0; k < 256; k++)
				b->flash[k] = (uint8_t)(k * 7 + i);
			m.crc = mdc_crc16(0xFFFF, b->flash, 256);
			memcpy(b->flash + BOOT_APP_LIMIT, &m, sizeof(m));
		}
		board_reset(b, 0);
	}
}

static void run_ms(uint32_t ms)
{
	uint64_t end = now_us + (uint64_t)ms * 1000;

	while (now_us < end) {
		for (int i = 0; i < n_boards; i++) {
			struct board *b = &boards[i];

			if (b->present && !b->hung && !b->in_boot && now_us >= b->busy_until)
				relay_step(&b->relay);
		}
		now_us += 1000;
	}
}

/* ---- the hub, as the tests see it ---- */

static uint8_t hub_seq;

/* Send a command and wait for its reply.  Returns the status, or -1 if board 0
 * does not answer, or -2 on a timeout or a damaged reply. */
static int hub_cmd(uint8_t hop, uint8_t cmd, const uint8_t *payload, uint8_t plen,
		uint8_t *rsp, uint8_t *rlen, uint8_t *hops, uint32_t timeout_ms)
{
	uint8_t f[MDC_MAX_FRAME];
	uint32_t end = now_ms + timeout_ms;

	f[0] = hop; f[1] = ++hub_seq; f[2] = cmd;
	if (plen)
		memcpy(f + MDC_CMD_HDR, payload, plen);
	uint8_t n = mdc_seal(f, (uint8_t)(MDC_CMD_HDR + plen));
	if (up_write(&boards[0], f, n, now_us))
		return -1;
	while ((int32_t)(now_ms - end) < 0) {
		run_ms(5);
		if (up_read(&boards[0], f, MDC_MAX_FRAME) < 0)
			return -1;
		if (f[0] == MDC_ST_BUSY)
			continue;
		uint8_t total = (uint8_t)(MDC_RSP_HDR + f[3] + MDC_CRC_LEN);
		if (f[3] > MDC_MAX_PAYLOAD || !mdc_check(f, total) || f[1] != hub_seq)
			return -2;
		if (rsp)
			memcpy(rsp, f + MDC_RSP_HDR, f[3]);
		if (rlen)
			*rlen = f[3];
		if (hops)
			*hops = f[2];
		return f[0];
	}
	return -2;
}

static uint32_t t_for(int hops) { return (uint32_t)hops * SIM_HOP_MS + SIM_BASE_MS + 100; }

/* ---- self-tests ---- */

static int failures, checks;
#define CHECK(c) do { checks++; if (!(c)) { failures++; \
	printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); } } while (0)

static void test_crc(void)
{
	/* CRC-16/CCITT-FALSE check value */
	CHECK(mdc_crc16(0xFFFF, (const uint8_t *)"123456789", 9) == 0x29B1);
}

static void test_ntc(void)
{
	CHECK(ntc_centi_c(32768) >= 2495 && ntc_centi_c(32768) <= 2505);   /* R = R1: 25 C */
	CHECK(ntc_centi_c(0) == MDC_TEMP_INVALID);                         /* shorted */
	CHECK(ntc_centi_c(65535) == MDC_TEMP_INVALID);                     /* open */
	for (uint32_t r = NTC_RAW_MIN; r < NTC_RAW_MAX; r++)               /* falls as the reading rises */
		CHECK(ntc_centi_c((uint16_t)r) >= ntc_centi_c((uint16_t)(r + 1)));
}

static void test_info_and_order(void)
{
	uint8_t p[MDC_MAX_PAYLOAD], len, hops;

	chain_init(12, 1);
	for (int h = 0; h < 12; h++) {
		CHECK(hub_cmd((uint8_t)h, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(h)) == MDC_ST_OK);
		CHECK(len == MDC_INFO_LEN && hops == h);
		CHECK(p[0] == MDC_MODE_APP && p[1] == BOOT_MCU && p[2] == MDC_PROTO_VERSION);
		CHECK(p[6] == BOOT_PAGE / MDC_CHUNK);
	}
	/* One past the end: board 11 reports that nothing is plugged into it. */
	CHECK(hub_cmd(12, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(12)) == MDC_ST_NO_DEVICE);
	CHECK(hops == 11);
	CHECK(hub_cmd(40, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(40)) == MDC_ST_NO_DEVICE);
	CHECK(hops == 11);
}

static void test_temps(void)
{
	uint8_t p[MDC_MAX_PAYLOAD], len, hops, arg;

	chain_init(40, 1);
	/* Sweep the chain in windows of 16 and check order and values. */
	int seen = 0, end = MDC_END_MORE;
	while (end == MDC_END_MORE) {
		arg = MDC_TEMPS_MAX;
		int st = hub_cmd((uint8_t)seen, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(seen + 16));

		CHECK(st == MDC_ST_OK);
		if (st != MDC_ST_OK)
			break;
		CHECK(hops == seen && len == 2 + p[0] * MDC_TEMPS_REC);
		if (seen + p[0] > 40)
			break;
		for (int i = 0; i < p[0]; i++) {
			int16_t t = (int16_t)(p[2 + 4 * i] | (p[3 + 4 * i] << 8));
			uint16_t raw = (uint16_t)(p[4 + 4 * i] | (p[5 + 4 * i] << 8));

			CHECK(raw == boards[seen + i].raw);
			CHECK(t >= 2000 + 10 * (seen + i) - 2 && t <= 2000 + 10 * (seen + i) + 2);
		}
		seen += p[0];
		end = p[1];
		if (seen > 40)
			break;
	}
	CHECK(seen == 40 && end == MDC_END_CHAIN);

	/* A window that ends exactly on the last board cannot know it is the end. */
	arg = 8;
	CHECK(hub_cmd(32, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(40)) == MDC_ST_OK);
	CHECK(p[0] == 8 && p[1] == MDC_END_MORE);
	arg = 9;
	CHECK(hub_cmd(32, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(41)) == MDC_ST_OK);
	CHECK(p[0] == 8 && p[1] == MDC_END_CHAIN);

	arg = 0;
	CHECK(hub_cmd(0, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(1)) == MDC_ST_BAD_ARG);
	arg = MDC_TEMPS_MAX + 1;
	CHECK(hub_cmd(3, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(4)) == MDC_ST_BAD_ARG);
	CHECK(hops == 3);

	/* A broken thermistor is reported, not hidden. */
	boards[5].raw = 65535;
	arg = 1;
	CHECK(hub_cmd(5, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(6)) == MDC_ST_OK);
	CHECK((int16_t)(p[2] | (p[3] << 8)) == MDC_TEMP_INVALID);
}

static void test_led_and_bad_commands(void)
{
	uint8_t p[MDC_MAX_PAYLOAD], len, hops;
	uint8_t led[2] = { MDC_LED_BLINK, 30 };

	chain_init(6, 1);
	CHECK(hub_cmd(4, MDC_CMD_LED, led, 2, p, &len, &hops, t_for(4)) == MDC_ST_OK);
	for (int i = 0; i < 6; i++)
		CHECK(boards[i].led_mode == (i == 4 ? MDC_LED_BLINK : 0));
	CHECK(boards[4].led_secs == 30);
	led[0] = 9;
	CHECK(hub_cmd(4, MDC_CMD_LED, led, 2, p, &len, &hops, t_for(4)) == MDC_ST_BAD_ARG);
	CHECK(hub_cmd(2, 0x7E, 0, 0, p, &len, &hops, t_for(2)) == MDC_ST_BAD_CMD);
	CHECK(hops == 2);
	/* Update commands are refused by a running application. */
	CHECK(hub_cmd(2, MDC_CMD_COMMIT, p, 4, p, &len, &hops, t_for(2)) == MDC_ST_BAD_CMD);

	/* A frame with a bad CRC is answered by the first board, whoever it was for. */
	uint8_t f[8] = { 3, 0x55, MDC_CMD_INFO, 0, 0 };
	up_write(&boards[0], f, 5, now_us);
	run_ms(20);
	up_read(&boards[0], f, 8);
	CHECK(f[0] == MDC_ST_BAD_CRC && f[1] == 0x55 && f[2] == 0);
}

static void test_faults(void)
{
	uint8_t p[MDC_MAX_PAYLOAD], len, hops, arg;

	chain_init(10, 1);

	/* Board 6 takes commands but never answers: board 5 reports a timeout. */
	boards[6].hung = 1;
	CHECK(hub_cmd(8, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(8)) == MDC_ST_TIMEOUT);
	CHECK(hops == 5);
	arg = MDC_TEMPS_MAX;
	CHECK(hub_cmd(0, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(16)) == MDC_ST_OK);
	CHECK(p[0] == 6 && p[1] == MDC_END_ERROR);
	/* Boards before it still work. */
	CHECK(hub_cmd(5, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(5)) == MDC_ST_OK);
	boards[6].hung = 0;

	/* Board 3 unplugged: the chain now ends at board 2. */
	boards[3].present = 0;
	CHECK(hub_cmd(7, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(7)) == MDC_ST_NO_DEVICE);
	CHECK(hops == 2);
	CHECK(hub_cmd(0, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(16)) == MDC_ST_OK);
	CHECK(p[0] == 3 && p[1] == MDC_END_CHAIN);
	boards[3].present = 1;

	/* A new command replaces one still in flight. */
	uint8_t f[MDC_MAX_FRAME] = { 9, 0x11, MDC_CMD_INFO };
	up_write(&boards[0], f, mdc_seal(f, 3), now_us);
	run_ms(30);                 /* part of the way down */
	CHECK(hub_cmd(1, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(1)) == MDC_ST_OK);
	CHECK(hops == 1);
	run_ms(3000);               /* the abandoned reply must not surface later */
	up_read(&boards[0], f, MDC_MAX_FRAME);
	CHECK(f[1] == hub_seq && f[2] == 1);

	/* Damaged frames between boards never produce a wrong answer. */
	chain_init(10, 1);
	corrupt_every = 3;
	int ok = 0, bad = 0;
	for (int i = 0; i < 200; i++) {
		int h = i % 10;
		int st = hub_cmd((uint8_t)h, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(h) + 2000);

		if (st == MDC_ST_OK) {
			ok++;
			CHECK(hops == h && len == MDC_INFO_LEN && p[1] == BOOT_MCU);
		} else {
			bad++;
			CHECK(st == MDC_ST_BAD_CRC || st == MDC_ST_TIMEOUT || st == MDC_ST_LINK);
		}
	}
	CHECK(ok > 20 && bad > 20);
}

/* Write an image to the board at hop through its bootloader. */
static int hub_update(uint8_t hop, const uint8_t *img, uint32_t len)
{
	uint8_t p[MDC_MAX_PAYLOAD], w[2 + MDC_CHUNK], rl, hops;

	for (uint32_t a = 0; a < len; a += MDC_CHUNK) {
		w[0] = (uint8_t)a; w[1] = (uint8_t)(a >> 8);
		memcpy(w + 2, img + a, MDC_CHUNK);
		int st = hub_cmd(hop, MDC_CMD_WRITE, w, sizeof(w), p, &rl, &hops, t_for(hop));
		if (st != MDC_ST_OK)
			return st;
	}
	uint16_t crc = mdc_crc16(0xFFFF, img, len);
	uint8_t c[4] = { (uint8_t)len, (uint8_t)(len >> 8), (uint8_t)crc, (uint8_t)(crc >> 8) };
	return hub_cmd(hop, MDC_CMD_COMMIT, c, 4, p, &rl, &hops, t_for(hop));
}

static void test_update(void)
{
	uint8_t p[MDC_MAX_PAYLOAD], len, hops;
	static uint8_t img[4096];

	for (unsigned i = 0; i < sizeof(img); i++)
		img[i] = (uint8_t)(i * 31 + (i >> 8));

	chain_init(8, 1);
	const int h = 5;

	/* A board in its bootloader still answers, and says it cannot relay. */
	CHECK(hub_cmd(h, MDC_CMD_ENTER_BOOT, 0, 0, p, &len, &hops, t_for(h)) == MDC_ST_OK);
	CHECK(boards[h].in_boot);
	CHECK(hub_cmd(h, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(h)) == MDC_ST_OK);
	CHECK(p[0] == MDC_MODE_BOOT && (p[5] & MDC_INFO_F_APP_OK));
	CHECK(hub_cmd(h + 1, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(h + 1)) == MDC_ST_IN_BOOT);
	CHECK(hops == h);
	uint8_t arg = MDC_TEMPS_MAX;
	CHECK(hub_cmd(0, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(16)) == MDC_ST_OK);
	CHECK(p[0] == h && p[1] == MDC_END_ERROR);

	/* The first write makes the old image invalid, so an interrupted update
	 * leaves the board in its bootloader. */
	uint8_t w[2 + MDC_CHUNK] = { 0, 0 };
	memcpy(w + 2, img, MDC_CHUNK);
	CHECK(hub_cmd(h, MDC_CMD_WRITE, w, sizeof(w), p, &len, &hops, t_for(h)) == MDC_ST_OK);
	CHECK(hub_cmd(h, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(h)) == MDC_ST_OK);
	CHECK(!(p[5] & MDC_INFO_F_APP_OK));
	CHECK(hub_cmd(h, MDC_CMD_BOOT, 0, 0, p, &len, &hops, t_for(h)) == MDC_ST_NO_APP);
	board_reset(&boards[h], 0);                 /* power cycle */
	CHECK(boards[h].in_boot);

	/* Bad arguments */
	w[0] = 4;                                   /* not on a chunk boundary */
	CHECK(hub_cmd(h, MDC_CMD_WRITE, w, sizeof(w), p, &len, &hops, t_for(h)) == MDC_ST_BAD_ARG);
	w[0] = (uint8_t)BOOT_APP_LIMIT; w[1] = (uint8_t)(BOOT_APP_LIMIT >> 8);   /* the marker page */
	CHECK(hub_cmd(h, MDC_CMD_WRITE, w, sizeof(w), p, &len, &hops, t_for(h)) == MDC_ST_BAD_ARG);
	w[0] = 0; w[1] = 0;
	CHECK(hub_cmd(h, MDC_CMD_WRITE, w, 10, p, &len, &hops, t_for(h)) == MDC_ST_BAD_ARG);
	if (BOOT_PAGE > MDC_CHUNK) {                /* a chunk out of order within a page */
		w[0] = 2 * MDC_CHUNK;
		CHECK(hub_cmd(h, MDC_CMD_WRITE, w, sizeof(w), p, &len, &hops, t_for(h)) == MDC_ST_BAD_ARG);
	}

	/* A wrong CRC at the end is refused and the board stays put. */
	CHECK(hub_update(h, img, sizeof(img)) == MDC_ST_OK);
	board_reset(&boards[h], 0);
	CHECK(!boards[h].in_boot);
	board_reset(&boards[h], 1);
	/* A refused WRITE leaves the valid image alone. */
	w[0] = 4;
	CHECK(hub_cmd(h, MDC_CMD_WRITE, w, sizeof(w), p, &len, &hops, t_for(h)) == MDC_ST_BAD_ARG);
	w[0] = 0;
	CHECK(hub_cmd(h, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(h)) == MDC_ST_OK);
	CHECK(p[0] == MDC_MODE_BOOT && (p[5] & MDC_INFO_F_APP_OK));
	uint8_t c[4] = { 0, 0x10, 0x34, 0x12 };
	CHECK(hub_cmd(h, MDC_CMD_COMMIT, c, 4, p, &len, &hops, t_for(h)) == MDC_ST_FLASH);

	/* The full update, then start it and see the chain whole again. */
	CHECK(hub_update(h, img, sizeof(img)) == MDC_ST_OK);
	CHECK(memcmp(boards[h].flash, img, sizeof(img)) == 0);
	CHECK(boards[h].flash[sizeof(img)] == 0xFF);
	CHECK(hub_cmd(h, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(h)) == MDC_ST_OK);
	CHECK(p[0] == MDC_MODE_BOOT && (p[5] & MDC_INFO_F_APP_OK));
	CHECK(hub_cmd(h, MDC_CMD_BOOT, 0, 0, p, &len, &hops, t_for(h)) == MDC_ST_OK);
	CHECK(!boards[h].in_boot);
	CHECK(hub_cmd(7, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(7)) == MDC_ST_OK);
	CHECK(p[0] == MDC_MODE_APP && hops == 7);
	/* Other boards were not touched. */
	for (int i = 0; i < 8; i++)
		if (i != h)
			CHECK(boards[i].erases == 0 && boards[i].programs == 0);

	/* The largest image that fits, on the first board. */
	static uint8_t big[BOOT_APP_LIMIT];
	for (unsigned i = 0; i < sizeof(big); i++)
		big[i] = (uint8_t)(i ^ (i >> 7));
	CHECK(hub_cmd(0, MDC_CMD_ENTER_BOOT, 0, 0, p, &len, &hops, t_for(0)) == MDC_ST_OK);
	CHECK(hub_update(0, big, sizeof(big)) == MDC_ST_OK);
	CHECK(memcmp(boards[0].flash, big, sizeof(big)) == 0);
	CHECK(hub_cmd(0, MDC_CMD_BOOT, 0, 0, p, &len, &hops, t_for(0)) == MDC_ST_OK);
	CHECK(hub_cmd(7, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(7)) == MDC_ST_OK);

	/* A board without our bootloader refuses to leave its application. */
	boards[2].no_bootloader = 1;
	CHECK(hub_cmd(2, MDC_CMD_ENTER_BOOT, 0, 0, p, &len, &hops, t_for(2)) == MDC_ST_BAD_CMD);
	CHECK(!boards[2].in_boot);
	CHECK(hub_cmd(2, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(2)) == MDC_ST_OK);
	CHECK(p[0] == MDC_MODE_APP && !(p[5] & MDC_INFO_F_BOOTLDR));
	CHECK(hub_cmd(3, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(3)) == MDC_ST_OK);
	CHECK(p[5] & MDC_INFO_F_BOOTLDR);

	/* A blank board (no image) waits in its bootloader. */
	chain_init(3, 0);
	CHECK(boards[0].in_boot);
	CHECK(hub_cmd(0, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(0)) == MDC_ST_OK);
	CHECK(p[0] == MDC_MODE_BOOT && !(p[5] & MDC_INFO_F_APP_OK));
	CHECK(hub_cmd(1, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(1)) == MDC_ST_IN_BOOT);
}

static void test_long_chain(void)
{
	uint8_t p[MDC_MAX_PAYLOAD], len, hops;

	chain_init(200, 1);
	uint32_t t0 = now_ms;
	CHECK(hub_cmd(199, MDC_CMD_INFO, 0, 0, p, &len, &hops, t_for(199)) == MDC_ST_OK);
	CHECK(hops == 199);
	printf("  200 boards, INFO to the last one: %u ms at 10 kHz per hop\n", (unsigned)(now_ms - t0));
	t0 = now_ms;
	int seen = 0;
	for (;;) {
		uint8_t arg = MDC_TEMPS_MAX;

		CHECK(hub_cmd((uint8_t)seen, MDC_CMD_TEMPS, &arg, 1, p, &len, &hops, t_for(seen + 16)) == MDC_ST_OK);
		seen += p[0];
		if (p[1] != MDC_END_MORE || seen > 200)
			break;
	}
	CHECK(seen == 200);
	printf("  200 boards, all temperatures: %u ms\n", (unsigned)(now_ms - t0));
}

static int self_test(void)
{
	static const struct { const char *name; void (*fn)(void); } tests[] = {
		{ "crc", test_crc }, { "ntc", test_ntc }, { "info and order", test_info_and_order },
		{ "temps", test_temps }, { "led and bad commands", test_led_and_bad_commands },
		{ "faults", test_faults }, { "update", test_update }, { "long chain", test_long_chain },
	};

	for (unsigned i = 0; i < sizeof(tests) / sizeof(tests[0]); i++) {
		int before = failures;

		tests[i].fn();
		printf("%s %s\n", failures == before ? "ok  " : "FAIL", tests[i].name);
	}
	chain_init(0, 0);
	printf("%d checks, %d failed (MCU type %d)\n", checks, failures, BOOT_MCU);
	return failures ? 1 : 0;
}

/* ---- server for tools/minidc.py ----
 *   w HEX      hub writes a frame to board 0      -> "ok" or "nack"
 *   r N        hub reads N bytes from board 0     -> HEX or "nack"
 *   t MS       let MS milliseconds pass           -> "ok"
 *   boot I     put board I in its bootloader      -> "ok"
 *   blank I    erase board I and reset it         -> "ok"
 *   image I F  load file F as the whole flash of board I and reset it -> "ok"
 *   state I    -> "app" or "boot", erase and program counts
 */
static int serve(int n)
{
	char line[512];

	chain_init(n, 1);
	setvbuf(stdout, NULL, _IOLBF, 0);
	while (fgets(line, sizeof(line), stdin)) {
		char arg[400] = "";
		char cmd[16] = "";

		char arg2[400] = "";

		sscanf(line, "%15s %399s %399s", cmd, arg, arg2);
		if (!strcmp(cmd, "w")) {
			uint8_t f[200];
			size_t len = strlen(arg) / 2;

			for (size_t i = 0; i < len; i++) {
				unsigned v;

				sscanf(arg + 2 * i, "%2x", &v);
				f[i] = (uint8_t)v;
			}
			if (len > MDC_MAX_FRAME)
				len = MDC_MAX_FRAME;
			puts(up_write(&boards[0], f, (uint8_t)len, now_us) ? "nack" : "ok");
		} else if (!strcmp(cmd, "r")) {
			uint8_t f[256];
			int want = atoi(arg);

			if (want < 1 || want > 255)
				want = MDC_MAX_FRAME;
			if (up_read(&boards[0], f, want) < 0) {
				puts("nack");
			} else {
				for (int i = 0; i < want; i++)
					printf("%02x", f[i]);
				putchar('\n');
			}
		} else if (!strcmp(cmd, "t")) {
			run_ms((uint32_t)atoi(arg));
			puts("ok");
		} else if (!strcmp(cmd, "boot") || !strcmp(cmd, "blank") || !strcmp(cmd, "state") ||
				!strcmp(cmd, "image")) {
			int i = atoi(arg);

			if (i < 0 || i >= n_boards) {
				puts("error");
				continue;
			}
			if (!strcmp(cmd, "blank"))
				memset(boards[i].flash, 0xFF, sizeof(boards[i].flash));
			if (!strcmp(cmd, "image")) {
				FILE *fp = fopen(arg2, "rb");

				if (!fp || fread(boards[i].flash, 1, SIM_FLASH, fp) != SIM_FLASH) {
					puts("error");
					continue;
				}
				fclose(fp);
				board_reset(&boards[i], 0);
			} else if (strcmp(cmd, "state")) {
				board_reset(&boards[i], 1);
			}
			if (!strcmp(cmd, "state"))
				printf("%s %d %d\n", boards[i].in_boot ? "boot" : "app", boards[i].erases, boards[i].programs);
			else
				puts("ok");
		} else {
			puts("error");
		}
	}
	return 0;
}

int main(int argc, char **argv)
{
	if (argc >= 3 && !strcmp(argv[1], "serve")) {
		int n = atoi(argv[2]);

		return serve(n < 1 ? 1 : n > MAX_BOARDS ? MAX_BOARDS : n);
	}
	return self_test();
}
