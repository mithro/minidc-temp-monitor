# Firmware: relay application and I2C bootloader

Firmware for the two [sensor strip boards](../hardware/README.md) in their
default relay fitting. It is built with the open
[ch32fun](https://github.com/cnlohr/ch32fun) SDK and GCC for RISC-V.

| Image | CH32V003J4M6 | CH32V005D6U6 | Where it lives |
|---|---|---|---|
| Relay application | 4.3 KB of 16 KB | 4.3 KB of 32 KB | user flash |
| I2C bootloader | 1500 of 1920 bytes | 1532 of 3328 bytes | boot area |

**None of this has run on a board yet.** The protocol logic of both programs
is tested on a PC in a simulated chain; the code that touches the hardware is
not. See [What has been tested](#what-has-been-tested).

## How the chain works

Every cable is its own small I2C bus. On its upstream connector (J1) a board
is an I2C target at address `0x2A`, using the hardware I2C peripheral. On its
downstream connector (J2) it is an I2C controller, bit-banged on two GPIOs.
All boards use the same address, because each one is alone on its hop.

A board's address is its position: 0 is the board plugged into the hub, 1 the
next one, and so on. Each command carries a hop count. A board that receives a
command with a hop count above zero takes one off and passes it on; the board
that sees zero carries it out. The reply comes back the same way, and each
board adds one to a counter in it, so the hub can see how far away the reply
came from. The hub therefore learns the physical order of the boards just by
counting.

Boards store and forward whole frames. Nothing holds the clock while it waits
for a board further down: the hub writes a command, then reads until the reply
stops saying "busy".

The downstream side drives its pins low or releases them to an input with the
internal pull-up (about 45 k), so the hop works with or without R5/R6. It runs
at 10 kHz by default, slow enough for the internal pull-ups alone. Build with
`make DN_I2C_HZ=100000` only for boards with R5/R6 fitted.

Speed, from the simulation at 10 kHz per hop:

| | Time |
|---|---|
| One command to board 199 of 200 and back | 2.8 s |
| All temperatures of a 200-board chain | 21 s |
| Each extra hop, for a short command | about 14 ms |

## Protocol

All multi-byte values are little-endian. Every frame ends in a CRC-16
(CCITT-FALSE: polynomial 0x1021, start 0xFFFF, no reflection), low byte first.

**Command**, written by the hub to board 0:

| Byte | Field |
|---|---|
| 0 | `hop`: position of the board the command is for |
| 1 | `seq`: any value, echoed in the reply |
| 2 | `cmd` |
| 3... | payload, up to 66 bytes |
| last 2 | CRC |

**Reply**, read from board 0. A read always starts at byte 0, and can be
repeated. Bytes past the end read as 0xFF.

| Byte | Field |
|---|---|
| 0 | `status` |
| 1 | `seq` of the command (0 in a busy reply) |
| 2 | `hops`: position of the board that produced this reply |
| 3 | `len`: payload length |
| 4... | payload |
| last 2 | CRC |

The hub writes a command, waits a few milliseconds, then reads. While `status`
is 1 (busy) it reads again. A new command replaces one that is still under
way. Allow about 0.16 s per hop plus 1.2 s before giving up, at 10 kHz. A
reply that arrives damaged can simply be read again. A board in its
bootloader does not acknowledge its address while it is writing flash, which
the hub should treat as busy. End every write with a STOP before reading; a
repeated start is not supported.

| `cmd` | Name | Payload | Reply payload |
|---|---|---|---|
| 0x01 | INFO | none | 8 bytes, below |
| 0x02 | TEMPS | `count` 1 to 16 | `n`, `end`, then `n` records |
| 0x03 | LED | `mode` (0 off, 1 on, 2 blink), `seconds` (0 = until changed) | none |
| 0x10 | ENTER_BOOT | none | none; the board restarts into its bootloader once the reply has been read. Status 3 if the boot area does not hold this bootloader |
| 0x11 | WRITE | `addr` (2 bytes), 64 data bytes | none (bootloader only) |
| 0x12 | COMMIT | `len` (2 bytes), `crc` (2 bytes) | none (bootloader only) |
| 0x13 | BOOT | none | none; the bootloader starts the application once the reply has been read |

| `status` | Meaning |
|---|---|
| 0 | ok |
| 1 | busy, read again |
| 2 | the command arrived with a bad CRC |
| 3 | unknown command, or not available in this mode |
| 4 | bad argument |
| 5 | nothing answers on the downstream connector: board `hops` is the last one |
| 6 | the board after `hops` took the command and never replied |
| 7 | bus error between board `hops` and the next |
| 8 | image CRC wrong after writing |
| 9 | board `hops` is in its bootloader and cannot pass commands on |
| 10 | no valid application to start |

**INFO** reply: `mode` (0 application, 1 bootloader), `mcu` (3 = CH32V003,
5 = CH32V005), protocol version (1), firmware version major and minor, `flags`,
flash page size in 64-byte chunks (1 or 4), one reserved byte. Flags: bit 0
valid application present (bootloader), bit 1 thermistor reading in range
(application), bit 2 identify LED active (application), bit 3 this bootloader
is in the boot area (application).

**TEMPS** reads up to 16 boards in one go, starting at board `hop`. The
target puts its own record first and asks the next board for the rest. Each
record is the temperature as a signed 16-bit number of 0.01 C (-32768 when the
thermistor reads open or shorted), then the raw divider reading scaled to
16 bits (65535 = VDD). `end` is 0 if `count` was reached, 1 if the last record
is the last board of the chain, 2 if the board after the last record did not
answer.

The application samples the thermistor once a second (16 conversions
averaged) and converts with a 129-point table for the fitted part (100 k,
B = 3950, against 100 k), interpolated; the table is within 0.02 C of the
formula from 0 to 70 C and 0.08 C from -20 to 100 C. Readings outside about
-35 to +126 C count as a fault. The raw value is there for a hub that wants to
apply its own curve or calibration. The reading is a ratio of VDD, so it is
the same at 3.3 V and 5 V.

## Bootloader

The bootloader sits in the boot area and needs the START_MODE option bit, so
it runs first after power-on. It then decides:

1. If the application asked for it (ENTER_BOOT), stay.
2. Otherwise watch upstream SDA for a short window (50 ms on the CH32V003,
   500 ms on the CH32V005). If SDA is low for 10 ms without a break, stay.
   Meanwhile SDA low is copied to the downstream connector.
3. Otherwise check the image marker and start the application if it is valid.
   If not, stay.

While it stays it answers the same protocol at the same address, with INFO,
WRITE, COMMIT and BOOT. It does not relay, so boards behind it are out of
reach (status 9) until its application runs again. That is why a chain is
updated one board at a time. It waits for BOOT with no time limit, so a hub
that stops part-way through an update has to come back and finish or send
BOOT (`minidc.py boot`).

The upstream pins never get an internal pull-up, so a chain powered up with
nothing connected to J1 of board 0 has a floating SDA there and may stop in
its bootloaders. `minidc.py boot` starts it once a hub is attached.

**Updating a board** (what `minidc.py update` does):

1. ENTER_BOOT, then INFO until `mode` is 1.
2. WRITE the image in 64-byte chunks, in address order from 0, padded with
   0xFF to a whole flash page (64 bytes on the CH32V003, 256 on the CH32V005).
   The first WRITE makes the old application invalid. The chunks of a page
   must arrive in order; after an error start that page again.
3. COMMIT with the padded length and its CRC-16. The bootloader checks flash
   against it and writes the marker.
4. BOOT, then INFO until `mode` is 0.

If power fails part-way, the board waits in its bootloader and the update can
be run again.

The application image carries the text `MDC-APP:` followed by its MCU type
byte. `minidc.py` uses it to refuse an image built for the other board, and
checks the image size, before the board leaves its application.

**Image marker:** the last page of user flash (0x3FC0 on the CH32V003, 0x7F00
on the CH32V005) holds three 32-bit words: 0x3143444D ("MDC1"), image length,
image CRC-16. The application may use everything below that page.

**Recovery.** Hold SDA low at the hub while powering the chain up, for at
least 100 ms (1 s with CH32V005 boards), then release it. Every board copies
the low level on and stays in its bootloader. `minidc.py boot --before K`
then starts boards 0 to K-1, `update K image.bin` rewrites board K, and `boot`
starts the rest. This is the way back from an application that starts but
does not work. The SWIO pad always works as a last resort.

## Programming a blank board

With a WCH-LinkE and ch32fun's `minichlink` (built from `ch32fun/minichlink`):

```
minichlink -a -U -w build/boot-ch32v003.bin bootloader -B   # bootloader
minichlink -w build/relay-ch32v003-full.bin flash -b        # application and marker
minichlink -w +a55aff00 option                              # START_MODE: boot area first
```

The first and last lines are the ones ch32fun's own bootloader example uses
for the CH32V003. The option word for the CH32V005 has not been checked: read
the option bytes of a real part and set START_MODE (bit 5 of the USER byte),
keeping the rest.

A board with only the application (no bootloader, START_MODE clear) also
works; it just cannot be updated over I2C. The application looks for the
bootloader's signature word in the boot area and refuses ENTER_BOOT without
it.

- **CH32V003:** SWIO is on TP1 and always available, except while the identify
  LED is lit, because the LED pulls that pin low.
- **CH32V005:** SWIO is the SCL pin of J1. It is a debug pin for the first
  500 ms after power-on, then the firmware turns it into SCL. To program a
  board that already has firmware, the programmer has to halt the chip inside
  that window after power-on; how best to do that with `minichlink` has to be
  worked out on a real board, and the window length (`BOOT_WINDOW_MS` in
  `common/board.h`) adjusted to suit. Keep the hub quiet on that bus for the
  first second after power-on: I2C clock pulses on SWIO in that time could be
  taken for debug traffic. The same applies to the board upstream if a
  CH32V005 restarts on its own (watchdog or reset pin) while it is being
  polled.

## Hub side

`tools/minidc.py` is a reference hub in Python (standard library only): a
`Chain` class with `scan`, `temps`, `led`, `update` and `boot_all`, and a
command line over Linux `/dev/i2c-N`:

```
tools/minidc.py --bus 1 scan
tools/minidc.py --bus 1 temps
tools/minidc.py --bus 1 led 7 blink 30
tools/minidc.py --bus 1 update 7 build/relay-ch32v003.bin
tools/minidc.py --bus 1 update all --v003 build/relay-ch32v003.bin --v005 build/relay-ch32v005.bin
```

The hub needs pull-ups on SDA and SCL for the first hop, and must tolerate
short clock stretching by board 0 (a few hundred microseconds at most).

## Building

```
sudo apt install gcc-riscv64-unknown-elf libnewlib-dev make python3
git submodule update --init firmware/ch32fun
make -C firmware          # images in firmware/build/
make -C firmware test     # host tests
```

CI ([firmware.yml](../.github/workflows/firmware.yml)) does both on every
change and keeps the images as a build artifact. The linker fails the build if
the bootloader outgrows its boot area.

| Path | Contents |
|---|---|
| `common/mdc_proto.h` | Protocol constants and CRC |
| `common/board.h` | Pin map of both boards |
| `common/ntc.h`, `ntc_table.h` | Thermistor conversion; the table is written by `tools/gen_ntc_table.py` |
| `relay/relay_core.c` | Relay logic, no hardware access |
| `relay/main.c` | I2C target, bit-banged controller, ADC, LED, watchdog |
| `bootloader/boot_core.h` | Bootloader command handling, no hardware access |
| `bootloader/boot.c` | Boot decision, I2C target, flash writes |
| `test/sim.c` | Simulated chain running the two cores; self-tests |
| `test/test_hub.py` | `minidc.py` against the simulated chain |
| `tools/minidc.py` | Hub library and command line; also makes the `-full.bin` images |
| `ch32fun/` | The SDK, as a git submodule |

Both microcontrollers run at 8 MHz from the internal oscillator and sleep
between interrupts, to keep their own heat away from the thermistor. A
watchdog restarts a board whose main loop stops for 2 s, since a hung board
would cut off everything behind it.

## What has been tested

On a PC, in CI:

- All four images build without warnings and the bootloaders fit.
- `relay_core.c` and `boot_core.h`, the same source that goes into the images,
  run in a simulated chain: addressing by position in chains of up to 200
  boards, temperature sweeps and their end-of-chain reporting, the LED
  command, bad commands and arguments, a board that hangs, a board that is
  missing, a command that overtakes another, damaged frames between boards
  (never accepted as a good answer), and firmware updates including bad CRCs,
  out-of-order chunks, an interrupted update, the largest image and a blank
  board.
- `minidc.py` drives that simulated chain through scans, sweeps, single and
  whole-chain updates with the real application binaries (the whole-chain
  one with one hub read in seven damaged), refusing oversize and wrong-MCU
  images, starting held boards, and a check that `-full.bin` images pass the
  bootloader's own test.
- The thermistor table against the formula.

Not tested, because there is no hardware yet:

- Everything in `relay/main.c` and `bootloader/boot.c` that touches registers:
  the I2C target, the bit-banged controller and its timing with internal
  pull-ups, flash erase and programming (the sequence follows ch32fun's and
  minichlink's; on the CH32V005 it loads a 256-byte page over four commands),
  the ADC, entering and leaving the boot area, the watchdog, sleep.
- The CH32V005 programming window, and its option bytes.
- Timing. The simulated bootloader answers at once, so the "not acknowledged
  while writing flash" path and the time a COMMIT takes (the image CRC is
  estimated at 0.4 s for a full CH32V005) are not exercised.
- Behaviour of a real hub.

This firmware is for the relay fitting only. With R3/R4 fitted (shared bus)
all boards would answer at the same address.
