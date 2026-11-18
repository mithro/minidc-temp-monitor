# Hardware: temperature sensor strip, v0.1

A small pass-through board for a chain of temperature sensors on a Qwiic style
(JST SH 4-pin) I2C cable. Each board carries a WCH RISC-V microcontroller that
reads a 100 k NTC thermistor and answers on I2C, so boards can assign their own
addresses instead of using strap resistors.

There are two versions of the same board, differing only in the microcontroller:

| | `sensor-ch32v003` | `sensor-ch32v005` |
|---|---|---|
| MCU | CH32V003J4M6, SOP-8 (LCSC C5346354) | CH32V005D6U6, QFN-12 2x2 mm (LCSC C49006243) |
| ADC | 10 bit | 12 bit |
| Upstream I2C (to J1) | hardware I2C on PC1/PC2 | hardware I2C on PD0/PD1 (remap 1) |
| Downstream I2C (to J2) | bit-banged on PA1/PC4 | bit-banged on PC0/PC3 |
| Thermistor divider | fed from VDD, read on PA2 | fed from PC7 while sampling, read on PC4 |
| Identify LED | shares the SWIO pin (PD1/PD4/PD5) | PA2 |
| Programming | SWIO test pad TP1 | SWIO is the SCL pin, so J1 pin 4 or TP1 |
| Spare pins | none | PA1, PC6 and reset on test pads |

## Schematic and board

| | Schematic | Board, top | Parts list | Placement |
|---|---|---|---|---|
| `sensor-ch32v003` | [PDF](sensor-ch32v003/out/schematic.pdf) | [PNG](sensor-ch32v003/out/board-top.png) | [BOM](sensor-ch32v003/out/bom-jlc.csv) | [CPL](sensor-ch32v003/out/cpl-jlc.csv) |
| `sensor-ch32v005` | [PDF](sensor-ch32v005/out/schematic.pdf) | [PNG](sensor-ch32v005/out/board-top.png) | [BOM](sensor-ch32v005/out/bom-jlc.csv) | [CPL](sensor-ch32v005/out/cpl-jlc.csv) |

![sensor-ch32v003, top](sensor-ch32v003/out/board-top.png)

![sensor-ch32v005, top](sensor-ch32v005/out/board-top.png)

- 42 x 13 mm, two layers, parts on the top only, flat back.
- J1 (UP) and J2 (DN): JST SH 1.0 mm 4-pin, pin 1 GND, 2 VDD, 3 SDA, 4 SCL.
- Mounting: one M3 hole, a zip-tie notch in each long edge, and a part-free back
  for an adhesive pad or a glued magnet.
- The thermistor sits on a finger cut free of the board on three sides, with no
  copper pour, so it follows the air rather than the board.

## Parts and cost

Both boards share every part except the microcontroller. Prices are JLCPCB
catalogue prices on 18 Nov 2026 for 200 boards; [COST.md](COST.md) has the full calculation,
including estimated fabrication and assembly fees.

| Ref | Part | LCSC | Fitted |
|---|---|---|---|
| U1 | CH32V003J4M6 or CH32V005D6U6 | C5346354 or C49006243 | yes |
| RT1 | 100k NTC, B3950, 1%, 0402 (Sunlord SDNT1005X104F3950FTF) | C6807762 | yes |
| R1 | 100k 1% 0402, divider | C25741 | yes |
| R2 | 1k 0402, LED | C11702 | yes |
| R3, R4 | 0R 0402, shared-bus links | C17168 | no |
| R5, R6 | 4k7 0402, downstream pull-ups | C25900 | yes, optional |
| C1, C3 | 100n 16 V X7R 0402 | C1525 | yes |
| C2 | 1u 25 V X5R 0402 | C52923 | yes |
| D1 | Red LED 0603 | C2286 | yes |
| J1, J2 | JST SH 4-pin, side entry, compatible clone | C7430446 | yes |

| | `sensor-ch32v003` | `sensor-ch32v005` |
|---|---|---|
| Parts per board | $0.33 | $0.30 |
| 200 boards assembled (estimate) | $118 | $113 |

## Cables

Generic double-ended JST SH 1.0 mm 4-pin leads from AliExpress, about $0.10
each, wired straight through: pin 1 at one end must reach pin 1 at the other.
[CABLES.md](CABLES.md) has the order list, the lengths, how to tell the two
wiring directions apart, and the leads for the hub end of each chain.

## Supply voltage

The boards run from 3.3 V or 5 V on VDD (J1/J2 pin 2) with no fitting change.
There is no regulator: VDD feeds the microcontroller directly and passes
straight through to the next board, so one chain runs at one voltage.

| | At 3.3 V | At 5 V | Limit |
|---|---|---|---|
| CH32V003 supply | ok | ok | 2.7 to 5.5 V, 2.8 V or more for the ADC |
| CH32V005 supply | ok | ok | 2.0 to 5.5 V, 2.4 V or more for the ADC |
| C1, C3 (100n) and C2 (1u) | ok | ok | rated 16 V and 25 V |
| Identify LED through R2 (1k) | about 1.4 mA | about 3 mA | 20 mA |
| R5, R6 pull-up current (4k7) | 0.7 mA | 1.1 mA | 3 mA for standard I2C |
| Thermistor self-heating at 25 C | about 27 uW | about 63 uW | negligible |

- The thermistor reading is ratiometric. The divider and the ADC reference both
  hang off VDD (through PC7 on the CH32V005), so the reading does not depend on
  the supply voltage. Firmware must work from the ADC ratio and never assume a
  VDD value.
- Never put more than 5.5 V on VDD. That is both the operating and the absolute
  maximum of the microcontrollers, and there is no protection on the board, so
  a 5 V supply must be a regulated one.
- 5 V leaves far more room for voltage drop along a long chain than 3.3 V does
  (2.2 V against 0.5 V before the CH32V003 ADC limit).
- The hub must suit the chain voltage. The simple case is hub pull-ups to the
  same rail as VDD. A 3.3 V hub can also drive a 5 V chain if its pull-ups go
  to 3.3 V, because both microcontrollers read 3.3 V as high at VDD = 5 V
  (input high threshold about 2.1 V on the CH32V003 and 2.2 V on the
  CH32V005). That relies on the boards never driving SDA or SCL high, so
  firmware must only ever pull the upstream I2C pins low or release them. Do not pull the bus up to 5 V on
  a 3.3 V chain.
- No signal may go above VDD. The CH32V005 has no 5 V tolerant pins, and on the
  CH32V003 only the upstream I2C pins are. Set the debug probe to the chain
  voltage or lower: a 3.3 V probe works on a 5 V board, a 5 V probe on a 3.3 V
  board does not.
- Qwiic and STEMMA QT cables and the JST SH connectors carry either voltage,
  but standard Qwiic boards are 3.3 V only. Do not plug one into a 5 V chain.

## Chain wiring option

| Mode | R3, R4 (0R) | R5, R6 (4k7) | Behaviour |
|---|---|---|---|
| Relay (default) | not fitted | fitted (optional) | Each board is an I2C target upstream and a bit-banged controller downstream, and forwards traffic. Every hop is a fresh, short bus. |
| Shared bus | fitted | not fitted | SDA/SCL pass straight through. All boards share one bus. |

R5 and R6 are optional. The microcontrollers have internal pull-ups of 35 to
55 k, which carry a short hop at roughly 10 to 20 kHz, so a relay board also
works with R5 and R6 left off. With them fitted a hop runs at 100 kHz and holds
the bus better against noise. They are in the BOM and placement files; delete
their rows from both to build without them.

The BOM and placement files are for the relay fitting. R5 and R6 are the pull-ups
of the hop to the next board; the hop from the hub to the first board uses the
pull-ups on the hub. In shared-bus mode no pull-ups are fitted on the boards.

A relay-fitted board with no firmware does not pass the bus on, so the chain
stops at the first unprogrammed board.

## Files

Everything is generated by the scripts, so change the scripts and rebuild rather
than editing the KiCad files by hand (hand edits are lost on the next build).

- `scripts/gen_sch.py` draws the schematic and checks it against its pin table.
  It also writes `lib/minidc.kicad_sym` (the MCU symbols, adjusted so pin text
  does not collide) and the `sym-lib-table` in each project directory.
- `scripts/gen_pcb.py` places the parts, routes the board and pours ground.
- `scripts/route.py` is the small grid router `gen_pcb.py` uses.
- `scripts/cost.py` prices both boards from their parts lists and writes
  [COST.md](COST.md).
- `build.sh` runs the schematic and board scripts for both versions, then
  ERC, DRC, the exports and `cost.py`.
- `sensor-*/out/` holds the schematic PDF, board renders, the BOM and placement
  files in JLCPCB column layout, and the ERC and DRC reports. Gerbers are written
  to `out/gerbers/` by the build and are not committed.

Needs KiCad 9 (`kicad-cli` and the `pcbnew` Python module) and numpy.

## Notes for firmware

- CH32V005: SCL to J1 is also SWIO, and the debug interface is on after reset.
  Firmware must wait a moment at boot before turning it off and enabling I2C,
  or the board cannot be reflashed. In shared-bus mode R4 joins every board's
  SWIO, so flash a board on its own.
- CH32V005: the divider is powered from PC7. Wait about 25 ms after driving PC7
  high before sampling, so C3 has settled.
- CH32V003: the LED sits on the SWIO pin. Light it by driving PD4 or PD5 low and
  leave PD1 as SWIO. Pin 1 is PD6 and PA1 bonded together, so keep PD6 an input.
- R5 and R6 are optional, so in relay mode firmware must work the downstream
  SDA and SCL pins without them: release a line by making the pin an input with
  its pull-up on, and drive it by making the pin an output held low. The
  internal pull-up only exists in input mode. Pick the downstream bit rate to
  suit: 10 to 20 kHz on internal pull-ups alone, up to 100 kHz with R5 and R6.
  Keep the pull-ups off on the upstream pins, and on every bus pin in
  shared-bus mode, so the only pull-ups there are the ones on the hub.
- CH32V003: the ADC and flash writes want VDD of 2.8 V or more, and ADC accuracy
  is only specified above 2.9 V. Watch the drop on long chains, mainly at 3.3 V.
- The allowed ADC speed depends on VDD. Keep the CH32V003 ADC clock at 6 MHz or
  less and the CH32V005 sample rate at 1 MHz or less, so one firmware covers
  both voltages.

## Known gaps in v0.1

- No firmware yet. The default fitting depends on relay firmware. Self-addressing,
  the relay mode and the CH32V005 programming window on the shared SCL/SWIO pin
  are untested ideas until there is some.
- Running without R5 and R6 is untested. Try a few boards with them removed
  before leaving them off a whole build.
- The routing is machine-made and passes DRC, but has not been tidied by hand.
- No reference designators on the silkscreen.
- The placement file rotations have not been checked against JLCPCB's part
  orientations. Check the preview when ordering.
- No panel drawing yet.
- The JST SH connector part is a compatible clone (LCSC C7430446). Its drawing
  shows the leads and mounting tabs landing on the JST footprint used here (see the
  [connector survey](../docs/research/jst-sh-4pin-connectors.md#land-pattern-of-the-fitted-part)),
  but no part has been soldered to the footprint or mated with a cable yet.
- With a metal M3 screw or standoff, only solder mask separates it from the
  ground pour around the hole.
