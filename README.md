# minidc-temp-monitor

Low-cost temperature (and some humidity) monitoring for a miniature
datacenter laid out with a hot aisle and a cold aisle. The goal is many
cheap sensor points on both sides of each rack, read by custom hardware
that is cheap enough to build in quantity from LCSC / JLCPCB parts.

## Status

First hardware revision drawn, not yet built. [hardware/](hardware/README.md)
holds KiCad 9 files for the sensor strip board (v0.1) in two versions, one
per microcontroller. Both pass ERC and DRC. There is no firmware yet.

## Current direction (draft, not yet final)

- **Sensor board (drawn):** a 42 x 13 mm pass-through strip with a WCH
  RISC-V microcontroller (CH32V003 or CH32V005) reading a 100 k NTC
  thermistor, and a Qwiic / STEMMA QT (JST SH 4-pin) connector at each end
  for daisy-chaining. Boards are meant to assign their own I2C addresses,
  so there are no address straps.
- **Chain:** by default each board relays the bus to the next one (I2C
  target upstream, bit-banged controller downstream), so every cable is its
  own short bus and no separate redriver board is needed. A shared
  pass-through bus is a build option.
- **Aisle link:** PCA9615 differential I2C over RJ45 / Cat5e, following
  SparkFun QwiicBus pin use.
- **Hub:** ESP32 or RP2040 with a TCA9548A mux, separate buses for the
  hot and cold sides.
- **Humidity and reference:** SHT40 for humidity on its own mux
  channel, plus a TMP117 as a calibration reference.

The aisle link, hub and humidity items are still the research-phase draft
and have not been revisited since the sensor board changed to a
microcontroller.

Open questions: whether the chain runs at 3.3 V (Qwiic style, as the
research assumed) or 5 V, cable length per aisle, points per rack face, and
how firmware does self-addressing and the relay.

## Documentation

See [docs/](docs/README.md) for the earlier research (it predates the
microcontroller sensor board) and [hardware/](hardware/README.md) for the
boards.
