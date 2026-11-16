# minidc-temp-monitor

Low-cost temperature (and some humidity) monitoring for a miniature
datacenter laid out with a hot aisle and a cold aisle. The goal is many
cheap sensor points on both sides of each rack, read by custom hardware
that is cheap enough to build in quantity from LCSC / JLCPCB parts.

## Status

Research phase. No hardware design files yet; the `.gitignore` is set up
for KiCad, which is the intended PCB tool.

## Current direction (draft, not yet final)

- **Sensor board:** small PCB with a TMP175-class I2C temperature sensor
  (27 addresses per bus) and two Qwiic / STEMMA QT (JST SH 4-pin)
  connectors for daisy-chaining, 3.3 V only, pull-ups behind a
  default-open solder jumper.
- **Aisle link:** PCA9615 differential I2C over RJ45 / Cat5e, following
  SparkFun QwiicBus pin use.
- **Hub:** ESP32 or RP2040 with a TCA9548A mux, separate buses for the
  hot and cold sides.
- **Humidity and reference:** SHT40 for humidity and a TMP117 as a
  calibration reference, each on its own mux channel.

Open questions: cable length per aisle, points per rack face, and whether
5 V tolerance is worth the extra cost.

## Documentation

See [docs/](docs/README.md) for the research behind these choices.
