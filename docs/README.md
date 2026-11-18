# Documentation

The design itself is documented next to the files, in
[hardware/](../hardware/README.md), with the cost estimate in
[hardware/COST.md](../hardware/COST.md), and in
[firmware/](../firmware/README.md).

## Research

Background surveys from November 2026. Prices and stock levels go stale
quickly; re-check them before ordering.

| Document | What it covers |
| --- | --- |
| [Cheap I2C temperature sensors on LCSC / JLCPCB / NextPCB](research/i2c-temperature-sensors-lcsc.md) | Survey of in-stock I2C temperature and temperature+humidity sensors, with prices, stock, accuracy and addresses per bus. The reference for humidity and calibration sensors; the sensor strip boards use a thermistor instead. |
| [Qwiic and related I2C sensor ecosystems](research/qwiic-i2c-ecosystems.md) | Qwiic, STEMMA QT, Grove and other connector ecosystems; pinouts, voltage and pull-ups, long cable runs (PCA9615 / QwiicBus), muxes, and what the sensor strip boards take from them. |
| [JST SH 4-pin (Qwiic / STEMMA QT) connectors on JLCPCB, LCSC and NextPCB](research/jst-sh-4pin-connectors.md) | The connector on the sensor strip boards (Megastar ZX-SH1.0-4PWT, C7430446) and how its land pattern compares with the JST footprint, plus the genuine JST parts and other SH clones with price and stock at JLC and NextPCB, look-alikes that do not mate, cables and housings. |
