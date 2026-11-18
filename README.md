# minidc-temp-monitor

Low-cost temperature (and some humidity) monitoring for a miniature
datacenter laid out with a hot aisle and a cold aisle. The goal is many
cheap sensor points on both sides of each rack, read by custom hardware
that is cheap enough to build in quantity from LCSC / JLCPCB parts.

## Status

First hardware revision drawn, not yet built. [hardware/](hardware/README.md)
holds KiCad 9 files for the sensor strip board (v0.1) in two versions, one
per microcontroller. Both pass ERC and DRC. [firmware/](firmware/README.md)
holds the relay firmware and an I2C bootloader for both; they build and pass
tests in a simulated chain, and have not run on a board.

## Design

- **Sensor board:** a 42 x 13 mm pass-through strip with a WCH RISC-V
  microcontroller (CH32V003 or CH32V005) reading a 100 k NTC thermistor,
  and a Qwiic / STEMMA QT style connector (JST SH 4-pin) at each end for
  daisy-chaining. A board's address is its position in the chain, so there
  are no address straps and the hub sees the physical order.
- **Chain:** by default each board relays the bus to the next one (I2C
  target upstream, bit-banged controller downstream), so every cable is its
  own short bus. A shared pass-through bus is a build option.
- **Firmware:** commands hop from board to board with a hop count. One
  command reads up to 16 temperatures, another blinks a board's identify
  LED, and boards are updated over the same cable, one at a time.
- **Supply:** 3.3 V or 5 V, passed straight through the chain.
- **Cost:** about $0.30 to $0.33 of parts per board, and an estimated $113
  to $118 for 200 assembled boards. See [hardware/COST.md](hardware/COST.md).

Not designed yet: the hub that powers and reads the chains, the link from
the hub to the first board of each chain, and humidity sensing. A reference
hub library in Python is in [firmware/tools/](firmware/tools/minidc.py).

Open questions: cable length per aisle and points per rack face.

## Documentation

See [hardware/](hardware/README.md) for the boards,
[firmware/](firmware/README.md) for the firmware and its protocol, and
[docs/](docs/README.md) for the background research.
