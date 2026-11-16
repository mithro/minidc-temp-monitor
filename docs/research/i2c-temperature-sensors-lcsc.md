# Cheap I2C temperature sensors on LCSC / JLCPCB / NextPCB

Nov 16, 2026 · Tim 'mithro' Ansell

> Exported from the [original Claude Doc](https://claude.ai/artifact/1k6nM7PYELgqpNiCysNJx9) on 2026-11-16. Prices, stock and recommendations are a snapshot from that date.

## Summary and top picks

The best bulk part is a TMP175-class sensor: 27 addresses on one bus, ±0.5 °C, about $0.38 each at 100. No I2C temperature sensor on JLCPCB is a Basic part, so every option costs an Extended-part fee. That makes it worth using **one sensor part number** for all points and one humidity part, which keeps the fee to two parts per order.

| Role | Pick | Why | $ @100 |
| --- | --- | --- | --- |
| Bulk temperature points | TMP175AIDR(UMW) C5158046, second source NST175H-QSPR C917444 | 27 per bus, ±0.5 °C, 9k+ stock. Two buses give 54 points for about $21 of sensors | 0.38 to 0.42 |
| Bulk, genuine TI only | TMP75AIDR C30389 | Cheapest genuine TI part, ±0.5 °C, 8 per bus (64 behind one PCA9548A mux) | 0.23 |
| Small flex or cable strips | TMP102AIDRLR C99269 | SOT-563, 36k stock, ±0.5 °C, 4 per bus | 0.26 |
| Calibration reference | TMP117AIDRVR C699536 | ±0.1 °C, one or two per aisle to check the cheap parts against | 0.73 |
| Humidity (cold aisle, inlet) | SHT40-CD1B-R3 C7461852, or SHT30-DIS-B2.5KS C77361 for 2 addresses | Genuine Sensirion, ±0.2 °C and about ±2 %RH | 1.34 to 1.99 |
| Cheapest humidity | AHT20 C2757850 | $0.53 and 33k stock, but fixed address, so one per mux channel | 0.53 |

The cheapest part overall is the TUDI LM75B clone (LM75BD-TUDI C41410989, $0.18 at 100), but its stock is under 2,000 and the maker is unknown outside LCSC.

## Comparison

Every in-stock part below is a JLCPCB **Extended** part; none of the temperature sensors found is Basic or Preferred. Prices are JLC/LCSC unit prices in USD, stock is LCSC/JLC stock, both as of 16 Nov 2026. Accuracy, range and resolution are from the JLC listing; address counts are from datasheets (marked "verify" where unsure). Clone makers (UMW, TUDI, Novosense, GXCAS, 3PEAK) are pin-compatible copies of the TI/NXP part named.

### Temperature only, sorted by sensors per bus

| Part (LCSC #) | Maker | Accuracy | Range (°C) | Res. | Package | Addr. per bus | $ @10 | $ @100 | Stock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TMP175AIDR(UMW) C5158046 | UMW (TMP175 clone) | ±0.5 °C | -40 to 125 | 12 bit | SOP-8 | 27 | 0.436 | 0.381 | 8,959 |
| TMP175AIDGKR(UMW) C5158047 | UMW (TMP175 clone) | ±0.5 °C | -40 to 125 | 12 bit | MSOP-8 | 27 | 0.517 | 0.395 | 10,386 |
| NST175H-QSPR C917444 | Novosense | ±0.5 °C | -55 to 125 | 12 bit | SOP-8 | 27 | 0.576 | 0.423 | 4,176 |
| PCT2075DP,118 C192518 | NXP | ±1 °C | -55 to 125 | 11 bit | MSOP-8 | 27 | 0.965 | 0.755 | 2,573 |
| TMP175AQDRQ1 C2859609 | TI | ±2 °C (listing) | -40 to 125 | 12 bit | SOIC-8 | 27 | 2.02 | 1.61 | 4 |
| LM75BD-TUDI C41410989 | TUDI (LM75B clone) | ±0.5 °C | -40 to 125 | 12 bit | SOP-8 | 8 | 0.209 | 0.182 | 1,875 |
| LM75AIMX-TUDI C41417240 | TUDI (LM75A clone) | ±0.5 °C | -40 to 125 | 12 bit | SOP-8 | 8 | 0.254 | 0.222 | 2,112 |
| TPTMP75-VS1R C51933410 | 3PEAK | ±1 °C | n/l | 12 bit | MSOP-8 | 8 | 0.312 | 0.223 | 1,400 |
| TMP75AIDR C30389 | TI | ±0.5 °C | -40 to 125 | 12 bit | SOIC-8 | 8 | 0.294 | 0.232 | 4,886 |
| TMP75AIDR(UMW) C5158044 | UMW (TMP75 clone) | ±0.5 °C | -40 to 125 | 12 bit | SOP-8 | 8 | 0.352 | 0.249 | 19,384 |
| LM75BDP(UMW) C2837470 | UMW (LM75B clone) | ±0.5 °C | -55 to 125 | 11 bit | MSOP-8 | 8 | 0.401 | 0.306 | 22,714 |
| LM75BD,118 C34565 | NXP | ±2 °C | -55 to 125 | 11 bit | SOIC-8 | 8 | 0.433 | 0.343 | 4,599 |
| LM75AIMX/NOPB C477979 | TI | ±2 °C | -55 to 125 | 9 bit | SOIC-8 | 8 | 0.550 | 0.425 | 26,754 |
| STDS75DS2F C283289 | ST | ±2 °C | -55 to 125 | 12 bit | MSOP-8 | 8 | 1.00 | 0.770 | 35 |
| SE95DP,118 C2803280 | NXP | ±1 °C | -55 to 125 | 13 bit | TSSOP-8 | 8 | 1.10 | 1.06 | 2 |
| MCP9808-E/MS C94847 | Microchip | ±0.5 °C max (±0.25 typ) | -40 to 125 | 13 bit | MSOP-8 | 8 | 1.65 | 1.30 | 416 |
| DS1621S+T&R C407894 | ADI (Maxim) | ±1 °C | -55 to 125 | 9 bit | SO-8 | 8 | 2.98 | 2.41 | 376 |
| P3T1755DPZ C20234292 | NXP (I2C + I3C) | ±0.5 °C | -40 to 125 | 12 bit | TSSOP-8 | verify | 0.754 | 0.564 | 32 |
| AS6221-AWLT-S C3663150 | ams OSRAM | ±0.09 °C | -40 to 125 | 16 bit | WLCSP-6 | verify | 2.38 | 1.88 | 165 |
| MAX31875R0TZS+T C3663366 | ADI (Maxim) | ±1 °C | n/l | 12 bit | WLP-4 0.8 mm | 1 per part no. (R0 to R7) | 0.560 | 0.422 | 2,482 |
| TMP102AIDRLR(UMW) C5692997 | UMW (TMP102 clone) | ±0.5 °C | -40 to 125 | 12 bit | SOT-563 | 4 | 0.255 | 0.220 | 13,045 |
| TMP102AIDRLR C99269 | TI | ±0.5 °C | -40 to 125 | 12 bit | SOT-563 | 4 | 0.321 | 0.261 | 36,192 |
| GX112S-1 C2972787 | GXCAS (TMP112 clone) | ±0.5 °C | -55 to 150 | 12 bit | SOT-563 | 4 | 0.312 | 0.270 | 1,531 |
| TMP112AQDRLRQ1 C2865764 | TI | ±0.5 °C | -40 to 125 | 12 bit | SOT-563 | 4 | 0.818 | 0.641 | 2,811 |
| TMP117AIDRVR C699536 | TI | ±0.1 °C | -55 to 150 | 16 bit | WSON-6 2x2 | 4 | 0.934 | 0.732 | 10,383 |
| TMP1075NDRLR C3663690 | TI | ±1 °C | -40 to 125 | 12 bit | SOT-563 | verify | 0.949 | 0.877 | 19,416 |
| TMP101NA/3K C388175 | TI | ±0.5 °C | -55 to 125 | 12 bit | SOT-23-6 | 3 | 1.90 | 1.45 | 4,889 |
| TMP421AIDCNR C130044 | TI (local + 1 remote diode) | ±1.5 °C | -40 to 125 | 12 bit | SOT-23-8 | verify | 0.940 | 0.739 | 949 |

### Temperature plus humidity

| Part (LCSC #) | Maker | Temp accuracy | RH accuracy | Range (°C) | Package | Addr. per bus | $ @10 | $ @100 | Stock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AHT20 C2757850 | Aosong | ±0.3 °C | ±2 %RH | -40 to 120 | 3x3 SMD | 1 (0x38) | 0.679 | 0.529 | 32,880 |
| AHT20-F C3012622 | Aosong | ±0.3 °C | ±2 %RH | -40 to 85 | 3x3 SMD | 1 (0x38) | 0.686 | 0.530 | 22,606 |
| GXHT40AD C48887140 | GXCAS (SHT40 clone) | n/l | n/l | n/l | DFN-4 1.5x1.5 | 1 | 0.740 | 0.567 | 502 |
| SHT31-P-NF C54946587 | unlisted maker | n/l | n/l | n/l | DFN-8 2.5x2.5 | verify | 1.40 | 1.09 | 500 |
| SHT40-CD1B-R3 C7461852 | Sensirion | ±0.2 °C | ±1.8 %RH | -40 to 125 | DFN-4 1.5x1.5 | 1 (0x46) | 1.69 | 1.34 | 3,816 |
| SHT30-DIS-B2.5KS C77361 | Sensirion | ±0.2 °C | ±2 %RH | -40 to 125 | DFN-8 2.5x2.5 | 2 | 2.55 | 1.99 | 14,011 |
| SHT30-DIS-B10KS C2687423 | Sensirion | ±0.2 °C | ±2 %RH | -40 to 125 | DFN-8 2.5x2.5 | 2 | 2.51 | 2.05 | 31,622 |
| SHT31-DIS-B2.5kS C80862 | Sensirion | ±0.2 °C | ±2 %RH | -40 to 125 | DFN-8 2.5x2.5 | 2 | 4.24 | 3.44 | 7,318 |
| AM2108 C3012626 | Aosong | ±0.3 °C | ±2 %RH | -40 to 80 | module | 1 | 2.27 | 1.69 | 51 |
| HDC3020DEFR C7472806 | TI | ±0.1 °C | ±0.5 %RH (listing) | -40 to 125 | WSON-8 2.5x2.5 | 4 | 4.14 | 4.10 | 6,748 |

n/l = not in the JLC listing. Bus helper: PCA9548APW,118 C21198 (NXP 8-channel I2C mux, TSSOP-24) is $0.81 at 10 and $0.61 at 100, with 22,786 in stock.

## Getting many sensors onto one bus

The address count limits how many chips share one I2C bus, so it matters more than price for a sensor-per-rack-unit layout. Address counts below are from the datasheets as I know them; confirm on the datasheet for the exact package before layout.

| Address scheme | Sensors per bus | Example parts |
| --- | --- | --- |
| 3 tri-state pins | 27 | TMP175, PCT2075, NST175 |
| 3 binary pins (A0-A2) | 8 | LM75A/B and clones, TMP75, MCP9808, DS1621, SE95, STDS75 |
| 1 pin tied to GND/VDD/SDA/SCL | 4 | TMP117, TMP112, TMP102, GX112, HDC3020 |
| 1 pin or address set by part number | 2 to 3 | SHT31 (2), SHT40 variants (1 each), TMP101 (3) |
| Fixed address | 1 | AHT20, AM2108, Si7051 |

Ways past the limit, cheapest first:

1. **Several buses from one MCU.** An RP2040 has 2 hardware I2C plus PIO; one bus per aisle side doubles capacity for free.
2. **An I2C mux** (TCA9548A / PCA9548A class, 8 channels). With 27-address parts that is 216 sensors behind one host address, and it also isolates bus capacitance per strip.
3. **A tiny MCU per sensor strip** (a CH32V003 is around $0.10) that reads its local sensors and reports over RS-485 or CAN. This is the robust answer when strips are more than about 1 m from the host, because plain I2C is a short-wire, low-capacitance bus (400 pF max).
4. **Remote-diode chips.** A TMP421-class or TMP468-class part reads cheap MMBT3904 transistors on short twisted pair, so one I2C chip covers several points. Useful for dense points along a rack face; cable length and noise need care.

Humidity matters mainly on the cold aisle (condensation and dew-point risk) and at the inlet. A sensible split is temperature-only parts for most points and a few humidity parts per aisle.

## Sourcing caveats

- **JLC class.** All parts found are Extended. JLC charges a loading fee per unique Extended part per order (about $3 when I last knew it; check the current fee). A query for Basic temperature sensors returned nothing.
- **NextPCB not checked.** nextpcb.com was not reachable from here, so its prices and its own parts library are not in this report. LCSC and JLC share stock, so the JLC numbers stand for LCSC too.
- **Clones.** UMW, TUDI, GXCAS and Novosense parts are cheap and well stocked on LCSC, but their specs above come from the listing, not a datasheet I read. Buy a few and check them against a TMP117 before a full build.
- **Not found or not checked.** The search found no in-stock match for TMP116, TMP114, HDC1080, STS30/STS40, SHTC3, Sensylink CT1075 and CHT831x, Novosense NST112 and NSHT30, and MySentech M117; some may still be on LCSC under a different part number. I did not get to TMP119, TMP100, TMP108, TMP468, STTS751, ADT7410/7420, NCT75, AT30TS75, MCP980x, AHT30 and HTU21D because of a fetch rate limit. I can run those next if any matter.
- **Volatility.** Stock and price move daily, especially for clones with a few thousand units.

Source: JLC/LCSC catalog data via [jlcsearch](https://jlcsearch.tscircuit.com/components/list.json?search=TMP175), fetched 16 Nov 2026.
