#!/usr/bin/env python3
"""Hub side of the sensor chain protocol (see firmware/README.md).

Library use:

    chain = Chain(LinuxI2C(1))
    for i, (temp_c, raw) in enumerate(chain.temps()):
        print(i, temp_c)

Command line:

    minidc.py --bus 1 scan
    minidc.py --bus 1 temps
    minidc.py --bus 1 led 7 blink 30
    minidc.py --bus 1 update 7 build/relay-ch32v003.bin
    minidc.py --bus 1 update all --v003 build/relay-ch32v003.bin --v005 build/relay-ch32v005.bin
    minidc.py mkimage --mcu ch32v003 relay.bin relay-full.bin

Only the standard library is used.  The I2C transport needs Linux i2c-dev.
"""
import argparse
import binascii
import os
import struct
import sys
import time

I2C_ADDR = 0x2A
MAX_PAYLOAD = 66
MAX_FRAME = 4 + MAX_PAYLOAD + 2
CHUNK = 64
TEMPS_MAX = 16
MARKER_MAGIC = 0x3143444D
APP_TAG = b'MDC-APP:'

CMD_INFO, CMD_TEMPS, CMD_LED = 0x01, 0x02, 0x03
CMD_ENTER_BOOT, CMD_WRITE, CMD_COMMIT, CMD_BOOT = 0x10, 0x11, 0x12, 0x13

ST_OK, ST_BUSY, ST_BAD_CRC, ST_BAD_CMD, ST_BAD_ARG = 0, 1, 2, 3, 4
ST_NO_DEVICE, ST_TIMEOUT, ST_LINK, ST_FLASH, ST_IN_BOOT, ST_NO_APP = 5, 6, 7, 8, 9, 10
STATUS_NAMES = {
    ST_OK: 'ok', ST_BUSY: 'busy', ST_BAD_CRC: 'bad CRC', ST_BAD_CMD: 'bad command',
    ST_BAD_ARG: 'bad argument', ST_NO_DEVICE: 'no board there', ST_TIMEOUT: 'no reply from the next board',
    ST_LINK: 'bus error to the next board', ST_FLASH: 'image CRC mismatch',
    ST_IN_BOOT: 'board is in its bootloader', ST_NO_APP: 'no valid application',
}

MODE_APP, MODE_BOOT = 0, 1
END_MORE, END_CHAIN, END_ERROR = 0, 1, 2
LED_MODES = {'off': 0, 'on': 1, 'blink': 2}
TEMP_INVALID = -32768

# flash size and page size by MCU type, as reported by INFO
MCUS = {3: ('ch32v003', 16384, 64), 5: ('ch32v005', 32768, 256)}
MCU_BY_NAME = {name: (size, page) for name, size, page in MCUS.values()}


def crc16(data):
    """CRC-16/CCITT-FALSE."""
    return binascii.crc_hqx(bytes(data), 0xFFFF)


def seal(frame):
    return bytes(frame) + struct.pack('<H', crc16(frame))


class ChainError(Exception):
    """A command failed.  status is the reply status or None; hops is the
    position of the board that reported it."""

    def __init__(self, message, status=None, hops=None):
        super().__init__(message)
        self.status = status
        self.hops = hops


class LinuxI2C:
    """Transport over /dev/i2c-N."""
    I2C_SLAVE = 0x0703

    def __init__(self, bus, addr=I2C_ADDR):
        import fcntl
        self.fd = os.open(f'/dev/i2c-{bus}', os.O_RDWR)
        fcntl.ioctl(self.fd, self.I2C_SLAVE, addr)

    def write(self, data):
        try:
            os.write(self.fd, bytes(data))
        except OSError as e:
            raise ChainError(f'first board does not answer ({e.strerror})') from e

    def read(self, n):
        """The reply bytes, or None if the board did not acknowledge (a board
        in its bootloader does that while it is writing flash)."""
        try:
            return os.read(self.fd, n)
        except OSError:
            return None

    def sleep(self, seconds):
        time.sleep(seconds)

    def now(self):
        return time.monotonic()


class Info:
    def __init__(self, payload):
        (self.mode, self.mcu, self.proto, self.major, self.minor, self.flags,
         self.page_chunks, _) = struct.unpack('<8B', payload[:8])
        self.in_bootloader = self.mode == MODE_BOOT
        self.app_ok = bool(self.flags & 0x01) if self.in_bootloader else True
        self.sensor_ok = bool(self.flags & 0x02) if not self.in_bootloader else None
        self.led_on = bool(self.flags & 0x04) if not self.in_bootloader else None
        self.has_bootloader = True if self.in_bootloader else bool(self.flags & 0x08)
        self.page = self.page_chunks * CHUNK
        self.mcu_name = MCUS.get(self.mcu, (f'type {self.mcu}',))[0]

    def __str__(self):
        where = 'bootloader' if self.in_bootloader else 'application'
        extra = ('' if self.app_ok else ', no valid application') if self.in_bootloader else \
            ('' if self.sensor_ok else ', thermistor fault') + ('' if self.has_bootloader else ', no bootloader')
        return f'{self.mcu_name} {where} v{self.major}.{self.minor}{extra}'


class Chain:
    """One chain of boards behind a transport.

    dn_hz is the bit rate the boards use between each other (the firmware's
    DN_I2C_HZ); it only sets how long to wait for replies.
    """

    def __init__(self, transport, dn_hz=10000, retries=2):
        self.t = transport
        self.seq = 0
        self.retries = retries
        self.hop_s = 2 * MAX_FRAME * 9 / dn_hz + 0.03
        self.base_s = 1.0

    def _once(self, hop, cmd, payload, depth):
        self.seq = (self.seq + 1) & 0xFF
        self.t.write(seal(bytes([hop, self.seq, cmd]) + bytes(payload)))
        deadline = self.t.now() + depth * self.hop_s + self.base_s + 0.2
        poll = 0.002
        while True:
            self.t.sleep(poll)
            poll = min(poll * 2, 0.05)
            f = self.t.read(MAX_FRAME)
            damaged = False
            if f and len(f) >= 6 and f[0] != ST_BUSY:
                total = 4 + f[3] + 2
                if f[3] <= MAX_PAYLOAD and seal(f[:total - 2]) == f[:total] and f[1] == self.seq:
                    return f[0], f[2], bytes(f[4:4 + f[3]])
                damaged = True      # the board keeps its reply: read it again
            if self.t.now() > deadline:
                raise ChainError('damaged reply' if damaged else 'no reply in time')

    def request(self, hop, cmd, payload=b'', depth=None, retry=True):
        """Send one command to the board at position hop (0 = nearest).
        Returns the reply payload; raises ChainError on any failure."""
        if not 0 <= hop <= 255:
            raise ChainError('position out of range')
        depth = hop + 1 if depth is None else depth
        last = None
        for _ in range(1 + (self.retries if retry else 0)):
            try:
                status, hops, data = self._once(hop, cmd, payload, depth)
            except ChainError as e:
                last = e
                continue
            if status == ST_OK:
                return data
            last = ChainError(f'board {hops}: {STATUS_NAMES.get(status, status)}', status, hops)
            # These can be the result of a damaged frame on the way: try again.
            if status not in (ST_BAD_CRC, ST_TIMEOUT, ST_LINK):
                break
        raise last

    def info(self, hop):
        return Info(self.request(hop, CMD_INFO))

    def scan(self):
        """Info of every board, in physical order, up to the end of the chain
        or the first board that cannot be reached past."""
        boards = []
        for hop in range(256):
            try:
                boards.append(self.info(hop))
            except ChainError as e:
                if e.status in (ST_NO_DEVICE, ST_IN_BOOT):
                    break
                raise
        return boards

    def temps(self, first=0, count=None):
        """Temperatures from position first on, as (degrees C or None, raw
        16-bit reading).  Reads to the end of the chain unless count is given.
        Stops early at a board that does not answer."""
        out = []
        while count is None or len(out) < count:
            want = TEMPS_MAX if count is None else min(TEMPS_MAX, count - len(out))
            hop = first + len(out)
            if hop > 255:
                break
            try:
                p = self.request(hop, CMD_TEMPS, bytes([want]), depth=hop + want + 1)
            except ChainError as e:
                if e.status in (ST_NO_DEVICE, ST_IN_BOOT):
                    break
                raise
            n, end = p[0], p[1]
            for i in range(n):
                centi, raw = struct.unpack_from('<hH', p, 2 + 4 * i)
                out.append((None if centi == TEMP_INVALID else centi / 100, raw))
            if end != END_MORE:
                break
        return out

    def led(self, hop, mode, seconds=0):
        """Identify LED: mode 'off', 'on' or 'blink'; seconds 0 = until changed."""
        if not 0 <= seconds <= 255:
            raise ChainError('seconds must be 0 to 255')
        self.request(hop, CMD_LED, bytes([LED_MODES[mode], seconds]))

    def enter_bootloader(self, hop):
        info = self.info(hop)
        if info.in_bootloader:
            return info
        if not info.has_bootloader:
            raise ChainError(f'board {hop} has no I2C bootloader')
        return self._switch(hop, CMD_ENTER_BOOT, MODE_BOOT)

    def start_application(self, hop):
        info = self.info(hop)
        if not info.in_bootloader:
            return info
        return self._switch(hop, CMD_BOOT, MODE_APP)

    def _switch(self, hop, cmd, mode):
        """Send a mode change and wait for it.  The board restarts once it
        has seen its reply read, so a lost reply does not mean it failed:
        look at the mode, and ask again if it has not changed."""
        last = None
        for _ in range(4):
            try:
                self.request(hop, cmd, retry=False)
            except ChainError as e:
                if e.status not in (None, ST_BAD_CRC, ST_TIMEOUT, ST_LINK):
                    raise
                last = e
            for _ in range(10):
                self.t.sleep(0.1)
                try:
                    info = self.info(hop)
                except ChainError as e:
                    last = e
                    continue
                if info.mode == mode:
                    return info
                last = ChainError(f'board {hop} did not change mode')
        raise last

    def update(self, hop, image, progress=None):
        """Write a new application to the board at hop and start it.  The
        boards behind it are out of reach until it is running again."""
        info = self.info(hop)
        if info.mcu not in MCUS:
            raise ChainError(f'board {hop}: unknown MCU type {info.mcu}')
        name, size, page = MCUS[info.mcu]
        tag = image_mcu(image)
        if tag is not None and tag != info.mcu:
            raise ChainError(f'board {hop} is a {name}, the image is for {MCUS.get(tag, (tag,))[0]}')
        image = pad_image(image, page)
        if len(image) > size - page:
            raise ChainError('image too large for this board')
        self.enter_bootloader(hop)
        for base in range(0, len(image), page):
            for attempt in range(4):
                try:
                    for a in range(base, base + page, CHUNK):
                        self.request(hop, CMD_WRITE, struct.pack('<H', a) + image[a:a + CHUNK])
                    break
                except ChainError:
                    # Start the page again: its chunks must arrive in order.
                    if attempt == 3:
                        raise
            if progress:
                progress(base + page, len(image))
        self.request(hop, CMD_COMMIT, struct.pack('<HH', len(image), crc16(image)))
        return self.start_application(hop)

    def boot_all(self, before=256):
        """Start the application on every board that is waiting in its
        bootloader, nearest first, stopping at position before.  Returns the
        position of a board with no valid application, in a list, if one
        stops the walk."""
        stuck = []
        for hop in range(before):
            try:
                info = self.info(hop)
            except ChainError as e:
                if e.status in (ST_NO_DEVICE, ST_IN_BOOT):
                    break
                raise
            if info.in_bootloader:
                if not info.app_ok:
                    stuck.append(hop)
                    break
                self.start_application(hop)
        return stuck


def image_mcu(image):
    """MCU type an application image was built for, from its tag, or None."""
    i = bytes(image).find(APP_TAG)
    return image[i + len(APP_TAG)] if 0 <= i < len(image) - len(APP_TAG) else None


def pad_image(image, page):
    image = bytes(image)
    return image + b'\xff' * (-len(image) % page)


def mkimage(image, mcu):
    """Whole-flash image: the application, padding, and the marker page the
    bootloader checks before it starts the application."""
    size, page = MCU_BY_NAME[mcu]
    image = pad_image(image, page)
    if len(image) > size - page:
        raise ValueError('application too large')
    marker = struct.pack('<III', MARKER_MAGIC, len(image), crc16(image))
    return image + b'\xff' * (size - page - len(image)) + marker + b'\xff' * (page - len(marker))


def main(argv=None):
    ap = argparse.ArgumentParser(description='Sensor chain hub tool')
    ap.add_argument('--bus', type=int, default=1, help='Linux I2C bus number')
    ap.add_argument('--dn-hz', type=int, default=10000, help='bit rate between boards')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('scan', help='list the boards in order')
    sub.add_parser('temps', help='read every temperature')
    p = sub.add_parser('led', help='identify LED')
    p.add_argument('board', type=int)
    p.add_argument('mode', choices=LED_MODES)
    p.add_argument('seconds', type=int, nargs='?', default=0)
    p = sub.add_parser('update', help='write a new application')
    p.add_argument('board', help='position, or "all"')
    p.add_argument('image', nargs='?', help='application .bin for one board')
    p.add_argument('--v003', help='application .bin for CH32V003 boards')
    p.add_argument('--v005', help='application .bin for CH32V005 boards')
    p = sub.add_parser('boot', help='start boards that wait in their bootloader')
    p.add_argument('--before', type=int, default=256, help='stop at this position')
    p = sub.add_parser('mkimage', help='application + marker for SWIO programming')
    p.add_argument('--mcu', required=True, choices=sorted(MCU_BY_NAME))
    p.add_argument('input')
    p.add_argument('output')
    args = ap.parse_args(argv)

    if args.cmd == 'mkimage':
        with open(args.input, 'rb') as f:
            out = mkimage(f.read(), args.mcu)
        with open(args.output, 'wb') as f:
            f.write(out)
        return 0

    chain = Chain(LinuxI2C(args.bus), dn_hz=args.dn_hz)
    try:
        if args.cmd == 'scan':
            for i, info in enumerate(chain.scan()):
                print(f'{i:3d}  {info}')
        elif args.cmd == 'temps':
            for i, (t, raw) in enumerate(chain.temps()):
                print(f'{i:3d}  ' + ('fault' if t is None else f'{t:7.2f} C') + f'  raw {raw}')
        elif args.cmd == 'led':
            chain.led(args.board, args.mode, args.seconds)
        elif args.cmd == 'boot':
            stuck = chain.boot_all(args.before)
            if stuck:
                print(f'board {stuck[0]} has no valid application')
                return 1
        elif args.cmd == 'update':
            images = {}
            for mcu, path in ((3, args.v003), (5, args.v005)):
                if path:
                    with open(path, 'rb') as f:
                        images[mcu] = f.read()
            if args.board == 'all':
                targets = range(len(chain.scan()))
            else:
                targets = [int(args.board)]
                if args.image:
                    with open(args.image, 'rb') as f:
                        images[chain.info(targets[0]).mcu] = f.read()
            for hop in targets:
                mcu = chain.info(hop).mcu
                if mcu not in images:
                    print(f'board {hop}: no image given for {MCUS[mcu][0]}')
                    return 1
                chain.update(hop, images[mcu],
                             lambda done, total, hop=hop: print(f'\rboard {hop}: {done}/{total}', end=''))
                print(' done')
    except ChainError as e:
        print(f'error: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
