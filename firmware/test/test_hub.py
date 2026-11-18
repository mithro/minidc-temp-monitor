#!/usr/bin/env python3
"""Tests of tools/minidc.py against the simulated chain (build/sim-*), which
runs the firmware's own protocol code.  Usage: test_hub.py BUILD_DIR"""
import os
import random
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
import minidc  # noqa: E402

BUILD = sys.argv[1] if len(sys.argv) > 1 else 'build'


class SimTransport:
    """Talks to "sim serve N"; time is the simulation's, not the wall clock."""

    def __init__(self, mcu, n):
        self.p = subprocess.Popen([os.path.join(BUILD, f'sim-{mcu}'), 'serve', str(n)],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.clock = 0.0

    def cmd(self, line):
        self.p.stdin.write(line + '\n')
        self.p.stdin.flush()
        return self.p.stdout.readline().strip()

    def write(self, data):
        if self.cmd('w ' + bytes(data).hex()) != 'ok':
            raise minidc.ChainError('first board does not answer')

    def read(self, n):
        r = self.cmd(f'r {n}')
        return None if r == 'nack' else bytes.fromhex(r)

    def sleep(self, seconds):
        ms = max(1, round(seconds * 1000))
        self.cmd(f't {ms}')
        self.clock += ms / 1000

    def now(self):
        return self.clock

    def state(self, i):
        mode, erases, programs = self.cmd(f'state {i}').split()
        return mode, int(erases), int(programs)

    def close(self):
        self.p.stdin.close()
        self.p.wait()


class LossyTransport(SimTransport):
    """Flips a bit in some of the replies the hub reads."""

    def __init__(self, mcu, n):
        super().__init__(mcu, n)
        self.rng = random.Random(1)
        self.damaged = 0

    def read(self, n):
        data = super().read(n)
        if data and data[0] != minidc.ST_BUSY and self.rng.random() < 1 / 7:
            self.damaged += 1
            data = bytearray(data)
            data[self.rng.randrange(6 + data[3] if data[3] <= 66 else 6)] ^= 1 << self.rng.randrange(8)
            data = bytes(data)
        return data


def app_image(mcu):
    """The real relay binary if it has been built, else stand-in bytes."""
    path = os.path.join(BUILD, f'relay-{mcu}.bin')
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return f.read()
    return bytes((i * 37 + (i >> 8)) & 0xFF for i in range(4000))


def run(mcu):
    mcu_id = {'ch32v003': 3, 'ch32v005': 5}[mcu]
    image = app_image(mcu)

    t = SimTransport(mcu, 20)
    chain = minidc.Chain(t)

    boards = chain.scan()
    assert len(boards) == 20, len(boards)
    assert all(b.mcu == mcu_id and not b.in_bootloader and b.sensor_ok for b in boards)
    assert str(boards[0]).startswith(mcu + ' application')

    temps = chain.temps()
    assert len(temps) == 20
    for i, (temp, raw) in enumerate(temps):
        assert abs(temp - (20.0 + 0.1 * i)) < 0.03, (i, temp)
    assert [x[1] for x in chain.temps(first=5, count=3)] == [x[1] for x in temps[5:8]]
    assert len(chain.temps(first=18, count=10)) == 2
    assert chain.temps(first=25) == []

    chain.led(7, 'blink', 30)
    assert chain.info(7).led_on and not chain.info(6).led_on
    chain.led(7, 'off')
    assert not chain.info(7).led_on

    # Update one board in the middle; nothing else is written.
    seen = []
    info = chain.update(7, image, lambda done, total: seen.append((done, total)))
    assert not info.in_bootloader
    assert seen and seen[-1][0] == seen[-1][1] >= len(image)
    for i in range(20):
        mode, erases, programs = t.state(i)
        assert mode == 'app'
        assert (programs > 0) == (i == 7), (i, programs)
    assert len(chain.scan()) == 20

    # Too large an image, or one for the other MCU, is refused before the
    # board leaves its application.
    size, page = minidc.MCU_BY_NAME[mcu]
    other = bytes(100) + minidc.APP_TAG + bytes([8 - mcu_id]) + bytes(100)
    for bad in (bytes(size - page + 1), other):
        try:
            chain.update(3, bad)
            raise AssertionError('bad image accepted')
        except minidc.ChainError:
            pass
        assert t.state(3) == ('app', 0, 0)
    if os.path.exists(os.path.join(BUILD, f'relay-{mcu}.bin')):
        assert minidc.image_mcu(image) == mcu_id

    # A blank board stops the chain there until it is given an application.
    assert t.cmd('blank 4') == 'ok'
    boards = chain.scan()
    assert len(boards) == 5 and boards[4].in_bootloader and not boards[4].app_ok
    assert len(chain.temps()) == 4
    assert chain.boot_all() == [4]
    chain.update(4, image)
    assert len(chain.scan()) == 20

    # Boards held in their bootloader are started one by one.
    for i in (0, 1, 2, 9):
        assert t.cmd(f'boot {i}') == 'ok'
    assert len(chain.scan()) == 1
    assert chain.boot_all(before=2) == []
    assert len(chain.scan()) == 3 and chain.info(2).in_bootloader
    assert chain.boot_all() == []
    assert len(chain.scan()) == 20 and not any(b.in_bootloader for b in chain.scan())

    # mkimage output is accepted by the bootloader's own check.
    full = minidc.mkimage(image, mcu)
    assert len(full) == size
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        f.write(full)
    try:
        assert t.cmd(f'image 2 {f.name}') == 'ok'
        assert t.state(2)[0] == 'app'
        broken = bytearray(full)
        broken[10] ^= 1
        with open(f.name, 'wb') as g:
            g.write(broken)
        assert t.cmd(f'image 2 {f.name}') == 'ok'
        assert t.state(2)[0] == 'boot'
        chain.update(2, image)
    finally:
        os.unlink(f.name)
    t.close()

    # Update every board of a short chain, nearest first, with one hub read
    # in seven damaged.
    t = LossyTransport(mcu, 5)
    chain = minidc.Chain(t)
    for hop in range(5):
        chain.update(hop, image)
    assert t.damaged > 20
    assert all(t.state(i)[2] > 0 and t.state(i)[0] == 'app' for i in range(5))
    assert len(chain.temps()) == 5
    t.close()


def main():
    assert minidc.crc16(b'123456789') == 0x29B1
    for mcu in ('ch32v003', 'ch32v005'):
        run(mcu)
        print(f'ok   hub library against {mcu} chain')


if __name__ == '__main__':
    main()
