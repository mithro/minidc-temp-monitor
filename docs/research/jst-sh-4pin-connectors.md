# JST SH 4-pin (Qwiic / STEMMA QT) connectors on JLCPCB, LCSC and NextPCB

Nov 17, 2026 · Tim 'mithro' Ansell

> Prices and stock are a snapshot taken on 2026-11-17 from JLCPCB's parts API (which shares stock with LCSC) and from HQ Online, the parts store behind NextPCB. Prices are USD unit prices.

## Summary and default pick

**Default: genuine JST SM04B-SRSS-TB(LF)(SN), LCSC C160404** (side entry, SMD). It is the exact part SparkFun lists for its Qwiic connector, the footprint is in the stock KiCad library, JLC has about 67k in stock and NextPCB about 56k, and it costs $0.17 at 100. Two per sensor board is about $0.35.

**Cheap alternate: Megastar ZX-SH1.0-4PWT, LCSC C7430446** (side entry, SMD). An SH-series clone at $0.058 at 100 with 187k on JLC, and also stocked at NextPCB. It saves about $0.23 per two-connector board ($23 per 100 boards). Order a few and check the latch feel against real Qwiic cables before switching the whole BOM to it.

The deciding facts:

- **No 4-pin 1.0 mm SH connector on JLC is Basic or Preferred.** I checked about 100 candidates and none is Basic or flagged Preferred. A Basic-only query for "SH1.0" returns nothing. So any choice costs one Extended-part loading fee per order, and the genuine part costs no more in fees than a clone.
- **Side entry (right angle) is the Qwiic and STEMMA QT norm.** The cable runs flat along the board, which suits boards stuck to rack faces. Use top entry (vertical) only where a board edge isn't reachable.
- **Pre-made cables are cheaper and better from SparkFun, Adafruit or generic Qwiic cable sellers** than from LCSC, which has only a few hundred SH 4-pin leads in stock. See [Cables and housings](#cables-and-housings).

## Side entry (right angle), SMD: SM04B-SRSS-TB and clones

These all use the SM04B land pattern: four 0.6 × 1.55 mm signal pads at 1.0 mm pitch plus two 1.2 × 1.8 mm mounting pads. "WT" or "WB" in a Chinese part number means horizontal ("卧贴"), "LT" or "LB" means vertical ("立贴").

All rows are JLC **Extended**, none Preferred. "$ @10" is the price for a quantity of 10; "$ @100" uses the price break at or below 100. "NextPCB" is HQ Online stock and its price at or below 100, where the part is listed.

| Part | LCSC # | Maker | Height | $ @10 | $ @100 | JLC stock | NextPCB stock ($) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SM04B-SRSS-TB(LF)(SN) | C160404 | JST (genuine) | 2.9 mm | 0.215 | 0.174 | 67,087 | 56,425 (0.161 @50) | **Default.** SparkFun PRT-14417 part |
| ZX-SH1.0-4PWT | C7430446 | Megastar | 3.15 mm | 0.068 | 0.058 | 187,104 | 1,677 (0.051 @50) | **Cheap alternate**, biggest SH-named stock |
| 1.0-4PWB | C2905006 | DEALON | 2.9 mm | 0.041 | 0.033 | 229,272 | not listed | Cheapest high-stock part, JLC lists it as SH series |
| HC-1.0-4PWT | C2845363 | HCTL | 3.2 mm | 0.094 | 0.074 | 88,137 | 8,033 (0.060 @50) | Common clone, stocked by both |
| WAFER-SH1.0-4PWB | C3029343 | XUNPU | 3.15 mm | 0.105 | 0.084 | 33,158 | 6,400 (0.074 @50) | Stocked by both |
| BX-SH1.0-4PWT | C18077910 | Bossie | 3.15 mm | 0.065 | 0.054 | 43,046 | not listed | |
| LAIL-PHC1.0-4P-01-SH-WT | C54905904 | LAILAN | 3.1 mm | 0.133 | 0.107 | 60,852 | not listed | |
| SH1.0mm-4P-WT | C53055320 | LXWCONN | n/l | 0.055 | 0.044 | 25,833 | not listed | |
| 1.0-4P WT | C2906270 | SHOU HAN | n/l | 0.052 | 0.041 | 23,474 | not listed | |
| HX SH-1.0-4PWT | C22461259 | hanxia | n/l | 0.040 | 0.031 | 21,740 | 2,000 (0.025 @100) | Cheapest at NextPCB |
| XY-SM04B-SRSS-TB | C51940130 | XYECONN | 2.9 mm | 0.039 | 0.039 | 19,242 | not listed | Named as an SM04B copy |
| HC-SH1.0-4PWT | C53454622 | Hong Cheng | 3.1 mm | 0.038 | 0.038 | 12,241 | not listed | |
| 1.0-4PWT | C2763614 | FG | 3.05 mm | 0.058 | 0.046 | 9,412 | not listed | |
| XY-SH1.0-4A61 | C19271998 | XYECONN | 2.9 mm | 0.036 | 0.036 | 7,487 | not listed | Cheapest per unit in bulk |
| 1.0T-4P | C145956 | BOOMELE | n/l | 0.061 | 0.061 | 1,259 | 56,707 (0.046 @100) | Low JLC stock but NextPCB's largest clone stock |
| WAFER-SH1.0-4PWB | n/a | CAX | n/l | n/a | n/a | n/a | 2,049 (0.030 @100) | NextPCB only |
| SM04B-SRSS-G-TB(LF)(SN) | C595145 | JST (gold) | 2.9 mm | 0.337 | 0.337 | 0 | not listed | Gold-plated genuine, out of stock |

"n/l" means JLC doesn't list the height. Heights differ slightly (2.9 mm genuine vs about 3.15 mm for most clones), which doesn't matter for a sensor board but would for a tight enclosure.

## Top entry (vertical), SMD: BM04B-SRSS-TB and clones

| Part | LCSC # | Maker | Height | $ @10 | $ @100 | JLC stock | NextPCB stock ($) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BM04B-SRSS-TB(LF)(SN) | C160390 | JST (genuine) | 4.25 mm | 0.341 | 0.273 | 10,674 | 3,490 (0.252 @50) | SparkFun PRT-16766 part |
| BM04B-SRSS-TBT(LF)(SN) | C495539 | JST (genuine, tape) | 4.25 mm | 0.361 | 0.282 | 664 | 1,097 (0.261 @50) | |
| ZX-SH1.0-4PLT | C7430453 | Megastar | 4.4 mm | 0.077 | 0.065 | 23,207 | 984 (0.057 @50) | Cheap alternate |
| HC-1.0-4PLT | C2845372 | HCTL | 4.4 mm | 0.106 | 0.084 | 16,321 | 1,957 (0.062 @100) | |
| HX SH-1.0-4PLT | C22461266 | hanxia | n/l | 0.049 | 0.039 | 16,847 | 1,500 (0.029 @100) | |
| 1.0-4PS | C2904986 | DEALON | 4.4 mm | 0.046 | 0.036 | 15,006 | not listed | |
| WAFER-SH1.0-4PLB | C3029334 | XUNPU | 4.4 mm | 0.117 | 0.094 | 11,123 | 1,122 (0.082 @50) | |
| SH-1.0-4PLT | C42372465 | SHOU HAN | n/l | 0.059 | 0.047 | 8,007 | 1,325 (0.036 @100) | |
| HC-SH1.0-4PLT | C53454629 | Hong Cheng | 4.5 mm | 0.041 | 0.033 | 6,849 | not listed | |
| XY-BM04B-SRSS-TB | C51940129 | XYECONN | 4.9 mm | 0.045 | 0.036 | 6,664 | not listed | |
| BX-SH1.0-4PLT | C18077917 | Bossie | 4.4 mm | 0.074 | 0.062 | 5,190 | not listed | |

## Look-alikes that are not SH compatible

The search terms "1.0 mm 4P" also return these. Don't use them for Qwiic:

- **JST NSH** (SM04B-NSHSS-TB C5329994, BM04B-NSHSS-TBT C545725): also 1.0 mm, but a different, taller latching housing (NSHR-04V-S). It does not mate with Qwiic cables.
- **"NH1.0", "SHB1.0" and "G1.0"** parts (XUNPU NH1.0-4PWT-MR, Hong Cheng HC-SHB1.0-4PWT, HCTL HC-G1.0-4PWT-05 and similar): JLC tags them as other series, not SH. Some are latch or "buckle" variants. Treat them as incompatible unless a datasheet proves otherwise.
- **JST GH** (SM04B-GHS-TB, 1.25 mm) and **JST SUR** (SM04B-SURS-TF, 0.8 mm): different pitch.
- **HR A1001WR-S-04P / A1001WV-S-04P** (C371510, C371588): Joint Tech's 1.0 mm wafer, sometimes sold as SH compatible. They cost $0.20 to $0.28 at 100 with low stock, so no reason to choose them.
- **1.0 mm FFC cables and FPC connectors**: a different system.

## What SparkFun and Adafruit use

- **SparkFun Qwiic**: [PRT-14417](https://www.sparkfun.com/products/14417) (side entry) is listed as "SM04B-SRSS-TB(LF)(SN) (but we had it made in black)", and [PRT-16766](https://www.sparkfun.com/products/16766) (top entry) is listed as "BM04B-SRSS-TB". So SparkFun uses the genuine JST parts, in black.
- **Adafruit STEMMA QT**: boards use a side-entry part on the `JST_SH4` package from Adafruit's `microbuilder` Eagle library (value `STEMMA_I2C_QT`), for example the [TMP117 board](https://github.com/adafruit/Adafruit-TMP117-PCB). The pads are 0.6 × 1.55 mm signal pads at 1.0 mm pitch with 1.2 × 1.8 mm mounting pads 5.6 mm apart, which is the SM04B land pattern. Adafruit's loose [right-angle connector 10-pack](https://www.adafruit.com/product/4208) ($3.95) is sold as "Qwiic compatible" rather than as genuine JST.
- **KiCad footprints**: the stock library has both:
  - `Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal`
  - `Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical`

  The SH clones above are made to the same land pattern, so one footprint covers the genuine part and its clones. Check the clone's datasheet for the mounting-pad size before a large run.

Pin order on the board is the Qwiic order: pin 1 GND, 2 3V3, 3 SDA, 4 SCL (black, red, blue, yellow on standard cables).

## Cables and housings

Ready-made cables are the cheap option. LCSC has only a few hundred pre-crimped SH 4-pin leads in stock, at about $0.08 to $0.11 each (for example BEIXUNZE SH1.00--4P-100-30A C54308409, 195 in stock, and BXCONN SH4P-28AWG-200-A1T C53413421, 200 in stock). These are single-ended or unclear, so check before buying.

| Item | Source | Price |
| --- | --- | --- |
| Qwiic / STEMMA QT cable, 50 mm | [Adafruit 4399](https://www.adafruit.com/product/4399) / [SparkFun PRT-14426](https://www.sparkfun.com/products/14426) | $0.95 / about $0.95 |
| 100 mm | [Adafruit 4210](https://www.adafruit.com/product/4210) / [SparkFun PRT-14427](https://www.sparkfun.com/products/14427) | $0.95 / about $1.50 |
| 200 mm | [Adafruit 4401](https://www.adafruit.com/product/4401) / [SparkFun flexible PRT-14428](https://www.sparkfun.com/products/14428) | $1.25 / about $1.95 |
| 300 mm | [Adafruit 5384](https://www.adafruit.com/product/5384) | $1.25 |
| 500 mm | [SparkFun flexible PRT-14429](https://www.sparkfun.com/products/14429) | about $2.75 |

Generic "JST SH 1.0 4-pin" double-ended cables from AliExpress-type sellers are usually cheaper again in bulk, but check that they are wired straight through (pin 1 to pin 1). Some are made reversed.

For making our own cables to length:

| Item | LCSC # | Maker | $ @100 | JLC stock | NextPCB |
| --- | --- | --- | --- | --- | --- |
| Housing SHR-04V-S | C385125 | JST | 0.066 | 51,108 | 48,282 ($0.069) |
| Crimp contact SSH-003T-P0.2-H (28 to 32 AWG) | C263995 | JST | about 0.021 | 340,074 | not checked |
| Crimp contact SSH-003T-P0.2 | C160231 | JST | about 0.018 | 52,228 | not checked |
| Clone housing ZX-SH1.0-4PJK | C7462664 | Megastar | 0.013 | 43 | not checked |
| Clone housing SH1.0-4Y | C7437096 | SHOU HAN | 0.013 | 7,622 | hanxia equivalent, 2,000 ($0.009) |
| Clone contact ZX-SH1.0-DZ | C7462671 | Megastar | about 0.008 | 193,310 | not checked |

The contacts are small and need a fine crimp tool (the JST tool is expensive, and the cheap generic tools work poorly at 1.0 mm). Making cables only pays off for odd lengths, such as long runs between racks. Even then, the [Qwiic survey](qwiic-i2c-ecosystems.md) suggests a differential link (PCA9615 over RJ45) for anything longer than about 0.5 m.

## NextPCB

NextPCB was reachable this time. Its parts store is [HQ Online](https://www.hqonline.com/), and the NextPCB columns above come from its search API. What I found:

- It stocks the genuine JST parts (SM04B 56k, BM04B 3.5k, SHR-04V-S 48k) at prices 5 to 10 % under JLC's.
- Its clone range is narrower: BOOMELE 1.0T-4P (57k), HCTL, XUNPU, Megastar, hanxia and CAX. The CAX and hanxia side-entry parts are the cheapest anywhere at about $0.025 to $0.03 at 100, with only 2,000 in stock.
- It doesn't expose a Basic or Extended class, and I could not find its assembly loading-fee rules on the site. So I can't compare the per-order fees with JLC's from here.
- The search wants the full part number with suffix (for example `SM04B-SRSS-TB(LF)(SN)`). A bare `SM04B-SRSS-TB` returns nothing.

## Method and caveats

- JLC data is from JLC's component search API with the terms SH1.0, SM04B, BM04B, 1.0-4P, "1x4P 1mm", "1.0mm 4P", JST SH and SHR-04V-S. I filtered on the listed pitch of 1 mm and 4 pins, and dropped "JLCPCB Assembly" placeholder rows, which have no stock. In the same data, Basic parts such as crystals show up as Basic, so the "no Basic SH connector" result is not a filter error.
- "SH compatible" is based on the part name and JLC's "Reference Series: SH" field, not on mating tests. For clones, check the datasheet drawing against JST's [SH datasheet](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf) and try one with a real Qwiic cable.
- JLC charges a loading fee per unique Extended part per order (about $3 when last known; check the current fee). Use one connector part number across all boards to pay it once.
- The SparkFun prices are shown on its site as two figures, a sale and a list price, and are given as "about".
