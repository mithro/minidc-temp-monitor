# Qwiic and related I2C sensor ecosystems

Nov 16, 2026 · Tim 'mithro' Ansell

> Exported from the [original Claude Doc](https://claude.ai/artifact/NNGkVAbaxvyX1meoYzW1v9) on 2026-11-16. Prices, stock and recommendations are a snapshot from that date.

## Summary

The de facto standard for plug-and-play I2C sensors is a **4-pin JST SH 1.0 mm connector wired GND, V+, SDA, SCL**, shared by SparkFun Qwiic and Adafruit STEMMA QT. Building our sensor boards around that connector makes them compatible with hundreds of off-the-shelf boards, cables, hubs and extenders at no extra cost.

- **Qwiic** is 3.3 V power and logic only, with pull-ups on every board. **STEMMA QT** uses the same plug but accepts 3-5 V, with a regulator and level shifter on each board.
- The 2.0 mm systems (Grove, M5Stack, STEMMA 4-pin, DFRobot Gravity) all use different pin orders. Gravity is reversed relative to STEMMA and can damage boards if mixed.
- Plain I2C over Qwiic cables is only good for about a metre. To span an aisle, the ecosystems use a **PCA9615 differential extender over Ethernet cable** (SparkFun QwiicBus), which SparkFun reports working over 200 ft at 100 kHz.
- Address clashes are solved with address-select jumpers first, and a **TCA9548A 8-way mux** second.
- Recommendation: one small sensor board with two Qwiic connectors (pass-through), a TMP175-class sensor with 27 addresses, pull-ups off by default, and a PCA9615 + RJ45 link from a per-aisle hub. Details are in the implications section below.

## Ecosystem comparison

Only Qwiic and STEMMA QT share a plug and pinout; every 2.0 mm system needs its own adapter cable. Pin order is pin 1 first, from the [Bus Pirate adapter table](https://docs.buspirate.com/docs/overview/qwiic-stemma-breakout-garden-grove-adapter/) and [Adafruit's STEMMA guide](https://learn.adafruit.com/introducing-adafruit-stemma-qt?view=all).

| Ecosystem | Vendor | Connector | Pin order (pin 1 first) | Power / logic | Pull-ups | Buses |
| --- | --- | --- | --- | --- | --- | --- |
| [Qwiic](https://www.sparkfun.com/qwiic) | SparkFun | JST SH 4-pin, 1.0 mm | GND, 3V3, SDA, SCL | 3.3 V only, no level shifting | On every board, cut-jumper to remove (typ. 2.2 kΩ) | I2C only |
| [STEMMA QT](https://learn.adafruit.com/introducing-adafruit-stemma-qt?view=all) | Adafruit | JST SH 4-pin, 1.0 mm | GND, V+, SDA, SCL | 3-5 V, regulator + level shifter on board | On every board, to V+ (typ. 10 kΩ) | I2C only |
| [STEMMA](https://learn.adafruit.com/introducing-adafruit-stemma-qt?view=all) 4-pin | Adafruit | JST PH 4-pin, 2.0 mm | SCL, SDA, V+, GND | 3-5 V | On device | I2C (3-pin variant for analog/PWM) |
| Grove | Seeed | HY2.0 4-pin, 2.0 mm (proprietary latch) | SCL, SDA, VCC, GND | 3.3 V or 5 V, board dependent | Varies by board | I2C, UART, analog, digital |
| M5Stack Unit (Port A) | M5Stack | Grove HY2.0 4-pin | SCL, SDA, 5V, GND | 5 V power, 3.3 V logic | Usually on host | I2C on Port A (red); B and C are GPIO/UART |
| Gravity I2C | DFRobot | JST PH 4-pin, 2.0 mm | SDA, SCL, GND, V+ | 3-5 V | On device | I2C, UART |
| Breakout Garden | Pimoroni | 2x5 edge slot, 2.54 mm (mirrored) | V+, SDA, SCL, INT, GND | 3-5 V | On host slot | I2C (+INT); newer boards add Qw/ST |
| Modulino | Arduino | JST SH 4-pin, 1.0 mm | Qwiic order | 3.3 V only | On board | I2C |
| mikroBUS / Click | MikroElektronika | 2x8 0.1" header | I2C on 2 of 16 pins | 3.3 V and 5 V rails | Varies | I2C, SPI, UART, PWM, AN, INT |
| Pmod (Type 6 I2C) | Digilent | 1x6 or 2x6 0.1" header | INT, RST, SCL, SDA, GND, VCC | 3.3 V | On host | I2C (other types for SPI/UART/GPIO) |
| UEXT | Olimex | 2x5 0.1" IDC | 3V3, GND, TX, RX, SCL, SDA, MISO, MOSI, SCK, CS | 3.3 V | Varies | I2C, SPI, UART |

The Grove and Qwiic pin orders are the same sequence counted from opposite ends, so a Grove-to-Qwiic cable is a straight crimp swap. Gravity is the odd one out: Adafruit [warns](https://learn.adafruit.com/introducing-adafruit-stemma-qt/stemma-qt-comparison) its power and I2C order are reversed versus STEMMA. Pull-up values for Qwiic and STEMMA QT are typical figures from product schematics, not stated in the standards pages.

## Connectors

The 1.0 mm JST SH (genuine part SM04B-SRSS-TB, right-angle SMD) is the one worth putting on our boards. Most Qwiic and STEMMA QT boards place two of them so modules daisy-chain; SparkFun's [Qwiic page](https://www.sparkfun.com/qwiic) notes the plug is polarized and sells cables in 50, 100, 200 and 500 mm lengths.

- **JST SH 1.0 mm (Qwiic, STEMMA QT, Modulino):** smallest footprint, cheap pre-made cables everywhere, but the latch is friction-only and the crimps are fine-pitch. Generic SH clones on LCSC are much cheaper than genuine JST; check stock and pricing when we pick the BOM.
- **2.0 mm (Grove HY2.0, JST PH, Gravity):** sturdier and easier to hand-crimp, but three mutually incompatible pinouts share the same pitch, so a cable from one can plug into another and swap power.
- **0.1" headers (Breakout Garden, mikroBUS, Pmod, UEXT):** suited to stacking on a host, not to cable runs between racks.
- **RJ45 (QwiicBus, PCA9615 boards):** the long-distance option; uses standard Cat5/6 patch cables. See the long cable runs section below.

## Voltage and pull-ups

The two 1.0 mm systems made opposite choices, and that choice matters most when many boards share one bus.

- **Qwiic: 3.3 V everywhere.** No regulator or level shifter on sensor boards, so they are cheapest. Every board ships with pull-ups enabled and a cut-trace jumper to remove them, so a chain of N boards puts N pull-ups in parallel (ten 2.2 kΩ boards = 220 Ω, beyond the 3 mA I2C sink limit) unless the user cuts jumpers.
- **STEMMA QT: 3-5 V tolerant.** Each device has a regulator and a BSS138-style level shifter (Adafruit puts the shifter at about 10 cents) and is expected to pull SDA/SCL up to V+, per [Adafruit's guide](https://learn.adafruit.com/introducing-adafruit-stemma-qt?view=all). Weak 10 kΩ pull-ups make long chains safer but slow edges on long cables.
- **M5Stack Port A:** 5 V on the power pin with 3.3 V logic, so a sensor board must regulate down and must not pull up to the 5 V pin.
- **QwiicBus:** terminating 4.7 kΩ pull-ups only on the EndPoint, none on MidPoints, per the [QwiicBus hookup guide](https://learn.sparkfun.com/tutorials/sparkfun-qwiicbus-hookup-guide/hardware-overview).

For our design: 3.3 V on the connector (Qwiic-correct, and STEMMA QT boards accept it), with pull-ups on a solder jumper that is **open by default**, fitted only on the hub or the last board.

## Long cable runs

Plain I2C is limited by the 400 pF bus capacitance budget, so a Qwiic chain is practical to roughly 1 m total at 100 kHz. The ecosystems offer four ways past that, and differential PCA9615 over Ethernet cable is the one that fits an aisle.

| Option | Chip | How it works | Reach (vendor claim) | Ecosystem product |
| --- | --- | --- | --- | --- |
| Differential I2C | NXP PCA9615 | Converts SDA/SCL to two differential pairs; spare pairs carry power | "Up to 100 ft" on Ethernet cable ([SparkFun](https://learn.sparkfun.com/tutorials/qwiic-differential-i2c-bus-extender-pca9615-hookup-guide/introduction-)); rated 3 m at 1 MHz, no significant loss over 200 ft at 100 kHz ([QwiicBus guide](https://learn.sparkfun.com/tutorials/sparkfun-qwiicbus-hookup-guide/hardware-overview)) | SparkFun Differential I2C Breakout (retired), QwiicBus EndPoint + MidPoint |
| Active terminator / rise-time accelerator | ADI LTC4311 | Boosts edges so the same pull-ups drive more capacitance | A few metres of single-ended cable | Adafruit LTC4311 I2C Extender (STEMMA QT) |
| Bus buffer (current boost) | NXP P82B715 / P82B96 | Buffers the bus to drive heavy cable capacitance | Tens of metres, single-ended | Older SparkFun/third-party breakouts |
| Isolator | TI ISO1540 | Galvanically isolates two segments | No extra reach; breaks ground loops | Adafruit ISO1540 (STEMMA QT) |

QwiicBus details worth copying: RJ45 straight-through cable; 3.3 V default (5 V option) on the blue pair (pins 4/5); the green pair (pins 3/6) can carry 3.8-36 V, which the MidPoint's LMR33630 bucks to 3.3 V at up to 3 A. The controller must sit on an EndPoint; MidPoints have two RJ45 jacks and no termination.

## Addresses and multiplexers

Every ecosystem solves address clashes the same two ways: solder jumpers or pads on the board, then a mux when jumpers run out.

- **Address jumpers.** Most temperature boards expose 1-3 address pins as solder jumpers. Tri-state pins (high, low, float) are the big win: the TMP175 / PCT2075 family gets 27 addresses from three pins, versus 8 for MCP9808 and 4 for TMP117 or TMP102.
- **Fixed-address parts.** SHT4x, AHT20 and most humidity sensors have one address (some SHT4x variants are sold with an alternate address). These need a mux or one per bus.
- **I2C multiplexers.** TCA9548A (8 channels) is on SparkFun's Qwiic Mux and Adafruit's STEMMA QT breakout; Adafruit also sells a 4-channel PCA9546. M5Stack's PaHUB unit uses a PCA9548A. Muxes are themselves addressable (8 addresses), so eight muxes give 64 downstream buses.
- **Passive hubs.** Seeed's Grove I2C Hub, M5Stack Hub and SparkFun Qwiic hubs just parallel the connectors; they add no addresses and do add pull-ups and capacitance.
- **Address translators.** Adafruit sells an LTC4316 breakout that XORs the address of everything behind it, which lets duplicate fixed-address sensors share a bus.
- **Programmable addresses.** Some SparkFun boards with an onboard microcontroller (e.g. Qwiic buttons and relays) store a new address in EEPROM. Plain sensor chips cannot do this.

## Temperature and humidity breakouts

The same dozen chips recur across every ecosystem, and they overlap heavily with the parts in the [earlier LCSC sensor survey](i2c-temperature-sensors-lcsc.md). These line-ups are from vendor catalogues as I know them, not re-checked product by product today; confirm a specific board before buying.

| Ecosystem | Temperature only | Temperature + humidity | Non-contact / other |
| --- | --- | --- | --- |
| SparkFun Qwiic | TMP117, TMP102, STTS22H, AS6212 | SHTC3, AHT20, BME280, BME688 | MCP9600 thermocouple, MLX90614 IR, MLX90640 thermal camera |
| Adafruit STEMMA QT | PCT2075 (27 addr), MCP9808, TMP117, ADT7410 | SHT40/41/45, SHT31-D, AHT20, HTU31D, HDC302x, BME280, BME688, MS8607 | MCP9600/9601, MLX90614, MLX90640, AMG8833 |
| Seeed Grove | MCP9808 (High Precision Temp) | SHT31, SHT35, SHT40, DHT20 (AHT20 core), BME280, BME680 | MLX90615, MLX90640 |
| M5Stack Units | (combined units only) | ENV III (SHT30 + QMP6988), ENV IV (SHT40 + BMP280), ENV Pro (BME688) | NCIR (MLX90614), Thermal (MLX90640) |
| DFRobot Gravity | TMP117-class precision boards | SHT31, SHT40, AHT20, BME280, BME680 | MLX90614 |
| Pimoroni Breakout Garden | (combined only) | BME280, BME688 | MCP9600, MLX90640 |
| MikroE Click | Thermo Click series (TMP102, LM75, MCP9808, TMP117 and others) | Temp&Hum Click series (SHT, HDC, HTS221) | IR Thermo Click |
| Digilent Pmod | Pmod TMP2 (ADT7420), Pmod TMP3 (TCN75A) | Pmod HYGRO (HDC1080) | Pmod TC1 (thermocouple, SPI) |

Two patterns matter for us. Bulk single-point temperature boards are rare in these catalogues; they favour precision parts (TMP117, MCP9808) or combo environmental sensors. The one many-per-bus board is Adafruit's PCT2075, the same 27-address LM75/TMP175 family as our survey's top pick.

## Implications for our design

Adopt the Qwiic connector and pinout on our own boards, and borrow QwiicBus's PCA9615-over-RJ45 approach for the runs between aisles. That keeps every board cheap while letting us plug in any off-the-shelf Qwiic or STEMMA QT sensor for comparison or a reference reading.

1. **Sensor board.** Two JST SH 4-pin connectors (in/out) wired GND, 3V3, SDA, SCL; a TMP175-class sensor (UMW TMP175 clone, C5158046, from the [survey](i2c-temperature-sensors-lcsc.md)) with its three tri-state address pins on solder pads, giving 27 boards per bus. No regulator or level shifter: 3.3 V only, Qwiic style.
2. **Pull-ups.** 2.2-4.7 kΩ pull-ups behind a solder jumper that is open by default, so a 27-board chain does not stack 27 pull-ups. Fit them on the hub instead.
3. **Aisle link.** One PCA9615 board per aisle with RJ45 in/out, compatible with QwiicBus pin use (I2C pairs, 3.3 V on pins 4/5, optional higher voltage on 3/6 for a local buck). Run at 100 kHz for margin over several metres of Cat5e.
4. **Hub.** An ESP32 or RP2040 controller with a TCA9548A, one channel per aisle or rack face, so the cold and hot sides are separate buses and a fault on one cannot hang the other.
5. **Humidity and reference points.** SHT40 (fixed address) on its own mux channel per aisle, and one TMP117 as a calibration reference, both of which are available as cheap Qwiic/STEMMA QT boards for prototyping before our own PCBs exist.
6. **Prototype with off-the-shelf parts.** Adafruit PCT2075 boards plus a SparkFun QwiicBus pair can validate cable length and addressing before we order PCBs.

Open questions: total cable length per aisle and number of points per rack face, which decide whether one PCA9615 segment per aisle is enough; and whether 5 V tolerance (STEMMA QT style) is worth the extra BOM cost for M5Stack-style hosts.

## Sources

- [Adafruit: What is STEMMA?](https://learn.adafruit.com/introducing-adafruit-stemma-qt?view=all)
- [Adafruit: STEMMA QT comparison](https://learn.adafruit.com/introducing-adafruit-stemma-qt/stemma-qt-comparison)
- [SparkFun Qwiic](https://www.sparkfun.com/qwiic)
- [Bus Pirate: Qwiic, STEMMA, Breakout Garden, Grove adapter pinouts](https://docs.buspirate.com/docs/overview/qwiic-stemma-breakout-garden-grove-adapter/)
- [Cable-tester.com: DFRobot Gravity I2C pinout](https://www.cable-tester.com/i2c-pin-out-from-gravity-dfrobot/)
- [SparkFun PCA9615 Differential I2C hookup guide](https://learn.sparkfun.com/tutorials/qwiic-differential-i2c-bus-extender-pca9615-hookup-guide/introduction-)
- [SparkFun QwiicBus hookup guide](https://learn.sparkfun.com/tutorials/sparkfun-qwiicbus-hookup-guide/hardware-overview)
- [Earlier survey: Cheap I2C temperature sensors on LCSC / JLCPCB](i2c-temperature-sensors-lcsc.md)

M5Stack Port A, mikroBUS, Pmod and UEXT pinouts, typical pull-up values, and the per-ecosystem sensor line-ups are from my own knowledge, not from pages opened today.
