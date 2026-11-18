# minidc-temp-monitor

Low-cost temperature (and some humidity) monitoring for a miniature
datacenter laid out with a hot aisle and a cold aisle. The goal is many
cheap sensor points on both sides of each rack, read by custom hardware
that is cheap enough to build in quantity from LCSC / JLCPCB parts.

## Status

First hardware revision drawn, not yet built. [hardware/](hardware/README.md)
holds KiCad 9 files for the sensor strip board (v0.1) in two versions, one
per microcontroller. Both pass ERC and DRC. There is no firmware yet.

## Design

- **Sensor board:** a 42 x 13 mm pass-through strip with a WCH RISC-V
  microcontroller (CH32V003 or CH32V005) reading a 100 k NTC thermistor,
  and a Qwiic / STEMMA QT style connector (JST SH 4-pin) at each end for
  daisy-chaining. Boards assign their own I2C addresses, so there are no
  address straps.
- **Chain:** by default each board relays the bus to the next one (I2C
  target upstream, bit-banged controller downstream), so every cable is its
  own short bus. A shared pass-through bus is a build option.
- **Supply:** 3.3 V or 5 V, passed straight through the chain.
- **Cost:** about $0.30 to $0.33 of parts per board, and an estimated $113
  to $118 for 200 assembled boards. See [hardware/COST.md](hardware/COST.md).
- **Cables:** generic double-ended JST SH 4-pin leads from AliExpress, an
  estimated $41 plus shipping for a 200-board build, hub leads included.
  See [hardware/CABLES.md](hardware/CABLES.md).

Not designed yet: the hub that powers and reads the chains, humidity
sensing, and the firmware (self-addressing and the relay).

Open questions: cable length per aisle and points per rack face.

## Documentation

See [hardware/](hardware/README.md) for the boards and
[docs/](docs/README.md) for the background research.
