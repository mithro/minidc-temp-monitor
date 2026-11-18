# JST SH 4-pin (Qwiic / STEMMA QT) connectors on JLCPCB, LCSC and NextPCB

Nov 17, 2026 · Tim 'mithro' Ansell

> Prices and stock are a snapshot taken on 2026-11-17 from JLCPCB's parts API (which shares stock with LCSC) and from HQ Online, the parts store behind NextPCB. Prices are USD unit prices.

## Summary

**The sensor strip boards use the Megastar ZX-SH1.0-4PWT, LCSC [C7430446](https://www.lcsc.com/product-detail/wire-to-board-connector_megastar-zx-sh1-0-4pwt_C7430446.html)**, for J1 and J2 (side entry, SMD). It is an SH-series clone at $0.058 at 100 with 187k in stock on JLC, and NextPCB stocks it too. It sits on the stock KiCad footprint for the genuine JST part; see [Land pattern of the fitted part](#land-pattern-of-the-fitted-part).

**Drop-in genuine part: JST SM04B-SRSS-TB(LF)(SN), LCSC [C160404](https://www.lcsc.com/product-detail/wire-to-board-connector_jst-sm04b-srss-tb-lf-sn_C160404.html)**. It is the part SparkFun lists for its Qwiic connector and the one the footprint was drawn for. It costs $0.17 at 100, which is about $0.23 more per two-connector board, with 67k in stock on JLC and 56k on NextPCB. It needs no board change: change the LCSC number in `hardware/scripts/gen_sch.py` and the price entry in `hardware/scripts/cost.py`, then rebuild.

Facts that hold for any choice:

- **No 4-pin 1.0 mm SH connector on JLC is Basic or Preferred.** Of about 100 candidates none is Basic or flagged Preferred, and a Basic-only query for "SH1.0" returns nothing. So the connector costs one Extended-part loading fee per order whichever part is fitted.
- **Side entry (right angle) is the Qwiic and STEMMA QT norm.** The cable runs flat along the board, which suits boards fixed to rack faces. Top entry (vertical) parts are listed below for boards where an edge is not reachable.
- **Cables are generic double-ended SH 4-pin leads at about $0.10 each from AliExpress-type sellers.** JLC/LCSC stocks only single-ended leads. The order list is in [hardware/CABLES.md](../../hardware/CABLES.md). SparkFun and Adafruit cables cost about ten times as much and are known to be wired straight. See [Cables and housings](#cables-and-housings).

## Land pattern of the fitted part

The boards place C7430446 on [`Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal`](https://gitlab.com/kicad/libraries/kicad-footprints/-/blob/master/Connector_JST.pretty/JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal.kicad_mod). The table compares that footprint with the PCB layout in Megastar's [drawing](https://www.lcsc.com/datasheet/C7430446.pdf) (version 2.0).

| | KiCad JST footprint | Megastar drawing |
| --- | --- | --- |
| Signal pads | 0.6 × 1.55 mm at 1.0 mm pitch | 0.5 × 1.7 mm at 1.0 mm pitch |
| Mounting pads | 1.2 × 1.8 mm | 1.2 × 2.5 mm |
| Mounting pad centre, measured from the end pin centre | 1.3 mm | 1.1 mm |
| Gap between signal pads and mounting pads | 2.2 mm | 1.3 mm |
| Depth over all pads | 5.55 mm | 5.5 mm |
| Body width × depth × height | 6.0 × 4.3 × 2.9 mm (JST part, from the JLC listing) | 6.35 × 4.3 × 3.15 mm |

- The signal pads agree to within 0.1 mm in width and 0.15 mm in length.
- Megastar's mounting tabs sit 1.10 ± 0.15 mm outside the end pin centres. The footprint's mounting pads cover 0.7 to 1.9 mm, so the tabs land on the pads, about 0.2 mm inboard of the pad centres.
- Megastar draws a longer mounting pad (2.5 mm against 1.8 mm) that reaches 0.7 mm closer to the signal pins. The footprint's pad covers the 1.8 mm furthest from the pins. Scaled from the drawing, which gives no dimension for it, the tab is about 1.45 mm long and about 0.2 mm of its pin-side end overhangs the footprint's pad, leaving roughly 85 % of it on copper.
- The body is 0.35 mm wider and about 0.25 mm taller than the JST part. The board has room for both.

This is a comparison of drawings. No physical part has been soldered to the footprint or mated with a Qwiic cable yet.

## Side entry (right angle), SMD: SM04B-SRSS-TB and clones

These are all sold as SM04B compatible. The SM04B land pattern in KiCad is four 0.6 × 1.55 mm signal pads at 1.0 mm pitch plus two 1.2 × 1.8 mm mounting pads. Only the Megastar part's drawing has been compared with it. "WT" or "WB" in a Chinese part number means horizontal ("卧贴"), "LT" or "LB" means vertical ("立贴").

All rows are JLC **Extended**, none Preferred. "$ @10" is the price for a quantity of 10; "$ @100" uses the price break at or below 100. "NextPCB" is HQ Online stock and its price at or below 100, where the part is listed. Each LCSC number links to its LCSC page, "JLC" links to the JLC assembly part page, and each NextPCB figure links to the HQ Online item page.

| Part | LCSC # and JLC page | Maker | Height | $ @10 | $ @100 | JLC stock | NextPCB stock ($) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SM04B-SRSS-TB(LF)(SN) | [C160404](https://www.lcsc.com/product-detail/wire-to-board-connector_jst-sm04b-srss-tb-lf-sn_C160404.html) · [JLC](https://jlcpcb.com/partdetail/JST-SM04B_SRSS_TB_LF_SN/C160404) | JST (genuine) | 2.9 mm | 0.215 | 0.174 | 67,087 | [56,425 (0.161 @50)](https://www.hqonline.com/product-detail/wire-to-board-connectors-jst-sm04b-srss-tb-lf--sn--2500326197) | Drop-in genuine part. [SparkFun PRT-14417](https://www.sparkfun.com/products/14417) part |
| ZX-SH1.0-4PWT | [C7430446](https://www.lcsc.com/product-detail/wire-to-board-connector_megastar-zx-sh1-0-4pwt_C7430446.html) · [JLC](https://jlcpcb.com/partdetail/Megastar-ZX_SH1_04PWT/C7430446) | Megastar | 3.15 mm | 0.068 | 0.058 | 187,104 | [1,677 (0.051 @50)](https://www.hqonline.com/product-detail/wire-to-board-connectors-megastar-zx-sh1-0-4pwt-2500437126) | **Fitted on the sensor strip boards** (J1, J2) |
| 1.0-4PWB | [C2905006](https://www.lcsc.com/product-detail/wire-to-board-connector_dealon-1-0-4pwb_C2905006.html) · [JLC](https://jlcpcb.com/partdetail/DEALON-1_04PWB/C2905006) | DEALON | 2.9 mm | 0.041 | 0.033 | 229,272 | not listed | Cheapest high-stock part, JLC lists it as SH series |
| HC-1.0-4PWT | [C2845363](https://www.lcsc.com/product-detail/wire-to-board-connector_hctl-hc-1-0-4pwt_C2845363.html) · [JLC](https://jlcpcb.com/partdetail/HCTL-HC_1_04PWT/C2845363) | HCTL | 3.2 mm | 0.094 | 0.074 | 88,137 | [8,033 (0.060 @50)](https://www.hqonline.com/product-detail/wire-to-board-connectors-hctl-hc-1-0-4pwt-2500353843) | Common clone, stocked by both |
| WAFER-SH1.0-4PWB | [C3029343](https://www.lcsc.com/product-detail/wire-to-board-connector_xunpu-wafer-sh1-0-4pwb_C3029343.html) · [JLC](https://jlcpcb.com/partdetail/XUNPU-WAFER_SH1_04PWB/C3029343) | XUNPU | 3.15 mm | 0.105 | 0.084 | 33,158 | [6,400 (0.074 @50)](https://www.hqonline.com/product-detail/wire-to-board-connectors-xunpu-wafer-sh1-0-4pwb-2500435391) | Stocked by both |
| BX-SH1.0-4PWT | [C18077910](https://www.lcsc.com/product-detail/wire-to-board-connector_bossie-bx-sh1-0-4pwt_C18077910.html) · [JLC](https://jlcpcb.com/partdetail/Bossie-BX_SH1_04PWT/C18077910) | Bossie | 3.15 mm | 0.065 | 0.054 | 43,046 | not listed |  |
| LAIL-PHC1.0-4P-01-SH-WT | [C54905904](https://www.lcsc.com/product-detail/C54905904.html) · [JLC](https://jlcpcb.com/partdetail/LAILAN-LAIL_PHC1_0_4P_01_SHWT/C54905904) | LAILAN | 3.1 mm | 0.133 | 0.107 | 60,852 | not listed |  |
| SH1.0mm-4P-WT | [C53055320](https://www.lcsc.com/product-detail/C53055320.html) · [JLC](https://jlcpcb.com/partdetail/LXWCONN-SH1_0mm_4PWT/C53055320) | LXWCONN | n/l | 0.055 | 0.044 | 25,833 | not listed |  |
| 1.0-4P WT | [C2906270](https://www.lcsc.com/product-detail/wire-to-board-connector_shou-han-1-0-4p-wt_C2906270.html) · [JLC](https://jlcpcb.com/partdetail/SHOUHAN-1_0_4PWT/C2906270) | SHOU HAN | n/l | 0.052 | 0.041 | 23,474 | not listed |  |
| HX SH-1.0-4PWT | [C22461259](https://www.lcsc.com/product-detail/wire-to-board-connector_hanxia-hx-sh-1-0-4pwt_C22461259.html) · [JLC](https://jlcpcb.com/partdetail/hanxia-HX_SH_1_04PWT/C22461259) | hanxia | n/l | 0.040 | 0.031 | 21,740 | [2,000 (0.025 @100)](https://www.hqonline.com/product-detail/wire-to-board-connectors-hanxia-hx-sh-1-0-4pwt-2500449387) | Cheapest at NextPCB |
| XY-SM04B-SRSS-TB | [C51940130](https://www.lcsc.com/product-detail/C51940130.html) · [JLC](https://jlcpcb.com/partdetail/XYECONN-XY_SM04B_SRSSTB/C51940130) | XYECONN | 2.9 mm | 0.039 | 0.039 | 19,242 | not listed | Named as an SM04B copy |
| HC-SH1.0-4PWT | [C53454622](https://www.lcsc.com/product-detail/C53454622.html) · [JLC](https://jlcpcb.com/partdetail/HongCheng-HC_SH1_04PWT/C53454622) | Hong Cheng | 3.1 mm | 0.038 | 0.038 | 12,241 | not listed |  |
| 1.0-4PWT | [C2763614](https://www.lcsc.com/product-detail/wire-to-board-connector_fg-1-0-4pwt_C2763614.html) · [JLC](https://jlcpcb.com/partdetail/FG-1_04PWT/C2763614) | FG | 3.05 mm | 0.058 | 0.046 | 9,412 | not listed |  |
| XY-SH1.0-4A61 | [C19271998](https://www.lcsc.com/product-detail/wire-to-board-connector_xyeconn-xy-sh1-0-4a61_C19271998.html) · [JLC](https://jlcpcb.com/partdetail/XYECONN-XY_SH1_04A61/C19271998) | XYECONN | 2.9 mm | 0.036 | 0.036 | 7,487 | not listed | $0.017 at 20,000, the lowest bulk price |
| 1.0T-4P | [C145956](https://www.lcsc.com/product-detail/wire-to-board-connector_boomele-boom-precision-elec-1-0t-4p_C145956.html) · [JLC](https://jlcpcb.com/partdetail/C145956) | BOOMELE | n/l | 0.061 | 0.061 | 1,259 | [56,707 (0.046 @100)](https://www.hqonline.com/product-detail/wire-to-board-connectors-boomele-1-0t-4pwotiebiandai-1012262449) | Low JLC stock but NextPCB's largest clone stock |
| WAFER-SH1.0-4PWB | n/a | CAX | n/l | n/a | n/a | n/a | [2,049 (0.030 @100)](https://www.hqonline.com/product-detail/wire-to-board-connectors-cax-wafer-sh1-0-4pwb-2500419395) | NextPCB only |
| SM04B-SRSS-G-TB(LF)(SN) | [C595145](https://www.lcsc.com/product-detail/wire-to-board-connector_jst-sm04b-srss-g-tb-lf-sn_C595145.html) · [JLC](https://jlcpcb.com/partdetail/JST-SM04B_SRSS_G_TB_LF_SN/C595145) | JST (gold) | 2.9 mm | 0.337 | 0.337 | 0 | not listed | Gold-plated genuine, out of stock |

"n/l" means JLC doesn't list the height. Heights differ slightly (2.9 mm genuine vs about 3.15 mm for most clones), which doesn't matter for a sensor board but would for a tight enclosure.

## Top entry (vertical), SMD: BM04B-SRSS-TB and clones

| Part | LCSC # and JLC page | Maker | Height | $ @10 | $ @100 | JLC stock | NextPCB stock ($) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BM04B-SRSS-TB(LF)(SN) | [C160390](https://www.lcsc.com/product-detail/wire-to-board-connector_jst-bm04b-srss-tb-lf-sn_C160390.html) · [JLC](https://jlcpcb.com/partdetail/JST-BM04B_SRSS_TB_LF_SN/C160390) | JST (genuine) | 4.25 mm | 0.341 | 0.273 | 10,674 | [3,490 (0.252 @50)](https://www.hqonline.com/product-detail/wire-to-board-connectors-jst-bm04b-srss-tb-lf--sn--2500310680) | [SparkFun PRT-16766](https://www.sparkfun.com/products/16766) part |
| BM04B-SRSS-TBT(LF)(SN) | [C495539](https://www.lcsc.com/product-detail/wire-to-board-connector_jst-bm04b-srss-tbt-lf-sn_C495539.html) · [JLC](https://jlcpcb.com/partdetail/JST-BM04B_SRSS_TBT_LF_SN/C495539) | JST (genuine, tape) | 4.25 mm | 0.361 | 0.282 | 664 | [1,097 (0.261 @50)](https://www.hqonline.com/product-detail/wire-to-board-connectors-jst-bm04b-srss-tbt-lf--sn--2500404026) |  |
| ZX-SH1.0-4PLT | [C7430453](https://www.lcsc.com/product-detail/wire-to-board-connector_megastar-zx-sh1-0-4plt_C7430453.html) · [JLC](https://jlcpcb.com/partdetail/Megastar-ZX_SH1_04PLT/C7430453) | Megastar | 4.4 mm | 0.077 | 0.065 | 23,207 | [984 (0.057 @50)](https://www.hqonline.com/product-detail/wire-to-board-connectors-megastar-zx-sh1-0-4plt-2500437127) | Cheap alternate |
| HC-1.0-4PLT | [C2845372](https://www.lcsc.com/product-detail/wire-to-board-connector_hctl-hc-1-0-4plt_C2845372.html) · [JLC](https://jlcpcb.com/partdetail/HCTL-HC_1_04PLT/C2845372) | HCTL | 4.4 mm | 0.106 | 0.084 | 16,321 | [1,957 (0.062 @100)](https://www.hqonline.com/product-detail/wire-to-board-connectors-hctl-hc-1-0-4plt-2500353844) |  |
| HX SH-1.0-4PLT | [C22461266](https://www.lcsc.com/product-detail/wire-to-board-connector_hanxia-hx-sh-1-0-4plt_C22461266.html) · [JLC](https://jlcpcb.com/partdetail/hanxia-HX_SH_1_04PLT/C22461266) | hanxia | n/l | 0.049 | 0.039 | 16,847 | [1,500 (0.029 @100)](https://www.hqonline.com/product-detail/wire-to-board-connectors-hanxia-hx-sh-1-0-4plt-2500449006) |  |
| 1.0-4PS | [C2904986](https://www.lcsc.com/product-detail/wire-to-board-connector_dealon-1-0-4ps_C2904986.html) · [JLC](https://jlcpcb.com/partdetail/DEALON-1_04PS/C2904986) | DEALON | 4.4 mm | 0.046 | 0.036 | 15,006 | not listed |  |
| WAFER-SH1.0-4PLB | [C3029334](https://www.lcsc.com/product-detail/wire-to-board-connector_xunpu-wafer-sh1-0-4plb_C3029334.html) · [JLC](https://jlcpcb.com/partdetail/XUNPU-WAFER_SH1_04PLB/C3029334) | XUNPU | 4.4 mm | 0.117 | 0.094 | 11,123 | [1,122 (0.082 @50)](https://www.hqonline.com/product-detail/wire-to-board-connectors-xunpu-wafer-sh1-0-4plb-2500438814) |  |
| SH-1.0-4PLT | [C42372465](https://www.lcsc.com/product-detail/C42372465.html) · [JLC](https://jlcpcb.com/partdetail/SHOUHAN-SH_1_04PLT/C42372465) | SHOU HAN | n/l | 0.059 | 0.047 | 8,007 | [1,325 (0.036 @100)](https://www.hqonline.com/product-detail/wire-to-board-connectors-shou-han-sh-1-0-4plt-2500445524) |  |
| HC-SH1.0-4PLT | [C53454629](https://www.lcsc.com/product-detail/C53454629.html) · [JLC](https://jlcpcb.com/partdetail/HongCheng-HC_SH1_04PLT/C53454629) | Hong Cheng | 4.5 mm | 0.041 | 0.033 | 6,849 | not listed |  |
| XY-BM04B-SRSS-TB | [C51940129](https://www.lcsc.com/product-detail/C51940129.html) · [JLC](https://jlcpcb.com/partdetail/XYECONN-XY_BM04B_SRSSTB/C51940129) | XYECONN | 4.9 mm | 0.045 | 0.036 | 6,664 | not listed |  |
| BX-SH1.0-4PLT | [C18077917](https://www.lcsc.com/product-detail/wire-to-board-connector_bossie-bx-sh1-0-4plt_C18077917.html) · [JLC](https://jlcpcb.com/partdetail/Bossie-BX_SH1_04PLT/C18077917) | Bossie | 4.4 mm | 0.074 | 0.062 | 5,190 | not listed |  |

## Look-alikes that are not SH compatible

The search terms "1.0 mm 4P" also return these. Don't use them for Qwiic:

- **JST NSH** (SM04B-NSHSS-TB [C5329994](https://www.lcsc.com/product-detail/wire-to-board-connector_jst-sm04b-nshss-tb-lf-sn_C5329994.html), BM04B-NSHSS-TBT [C545725](https://www.lcsc.com/product-detail/wire-to-board-connector_jst-bm04b-nshss-tbt-lf-sn_C545725.html)): also 1.0 mm, but a different, taller latching housing ([NSHR-04V-S](https://www.lcsc.com/product-detail/housings-wire-to-board-wire-to-wire_jst-nshr-04v-s_C594728.html)). It does not mate with Qwiic cables.
- **"NH1.0", "SHB1.0" and "G1.0"** parts (XUNPU [NH1.0-4PWT-MR](https://www.lcsc.com/product-detail/C53134236.html), Hong Cheng [HC-SHB1.0-4PWT](https://www.lcsc.com/product-detail/C53151885.html), HCTL [HC-G1.0-4PWT-05](https://www.lcsc.com/product-detail/wire-to-board-connector_hctl-hc-g1-0-4pwt-05_C20539073.html) and similar): JLC tags them as other series, not SH. Some are latch or "buckle" variants. Treat them as incompatible unless a datasheet proves otherwise.
- **JST GH** ([SM04B-GHS-TB](https://www.lcsc.com/product-detail/C189895.html), 1.25 mm) and **JST SUR** ([SM04B-SURS-TF](https://www.lcsc.com/product-detail/C545754.html), 0.8 mm): different pitch.
- **HR A1001WR-S-04P / A1001WV-S-04P** ([C371510](https://www.lcsc.com/product-detail/wire-to-board-connector_hr-joint-tech-elec-a1001wr-s-04p_C371510.html), [C371588](https://www.lcsc.com/product-detail/wire-to-board-connector_hr-joint-tech-elec-a1001wv-s-04p_C371588.html)): Joint Tech's 1.0 mm wafer, sometimes sold as SH compatible. They cost $0.20 to $0.28 at 100 with low stock, so no reason to choose them.
- **1.0 mm FFC cables and FPC connectors**: a different system.

## What SparkFun and Adafruit use

- **SparkFun Qwiic**: [PRT-14417](https://www.sparkfun.com/products/14417) (side entry) is listed as "SM04B-SRSS-TB(LF)(SN) (but we had it made in black)", and [PRT-16766](https://www.sparkfun.com/products/16766) (top entry) is listed as "BM04B-SRSS-TB". So SparkFun uses the genuine JST parts, in black.
- **Adafruit STEMMA QT**: boards use a side-entry part on the `JST_SH4` package from Adafruit's `microbuilder` Eagle library (value `STEMMA_I2C_QT`), for example the [TMP117 board](https://github.com/adafruit/Adafruit-TMP117-PCB). The pads are 0.6 × 1.55 mm signal pads at 1.0 mm pitch with 1.2 × 1.8 mm mounting pads 5.6 mm apart, which is the SM04B land pattern. Adafruit's loose [right-angle connector 10-pack](https://www.adafruit.com/product/4208) ($3.95) is sold as "Qwiic compatible" rather than as genuine JST.
- **KiCad footprints**: the stock library has both:
  - [`Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal`](https://gitlab.com/kicad/libraries/kicad-footprints/-/blob/master/Connector_JST.pretty/JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal.kicad_mod)
  - [`Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical`](https://gitlab.com/kicad/libraries/kicad-footprints/-/blob/master/Connector_JST.pretty/JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical.kicad_mod)

  The sensor strip boards use the horizontal footprint. Check a clone's drawing against the footprint before using it; [Land pattern of the fitted part](#land-pattern-of-the-fitted-part) does this for C7430446.

Pin order on the boards is the Qwiic order: pin 1 GND, 2 VDD, 3 SDA, 4 SCL (black, red, blue, yellow on standard cables). VDD is 3.3 V on Qwiic and 3 to 5 V on STEMMA QT; the sensor strip boards accept 3.3 V or 5 V (see [hardware/](../../hardware/README.md)).

## Cables and housings

The boards are joined with generic double-ended leads from AliExpress-type sellers; [hardware/CABLES.md](../../hardware/CABLES.md) has the order list. JLC/LCSC has no double-ended SH 4-pin lead. Its SH 4-pin leads are single-ended, with one housing and tinned wire ends (for example BXCONN SH4P-28AWG-200-A1T [C53413421](https://www.lcsc.com/product-detail/C53413421.html), 200 mm, $0.11, 200 in stock), which suit the hub end of a chain.

Branded Qwiic and STEMMA QT cables are wired straight through and make a known-good reference:

| Item | Source | Price |
| --- | --- | --- |
| Qwiic / STEMMA QT cable, 50 mm | [Adafruit 4399](https://www.adafruit.com/product/4399) / [SparkFun PRT-14426](https://www.sparkfun.com/products/14426) | $0.95 / about $0.95 |
| 100 mm | [Adafruit 4210](https://www.adafruit.com/product/4210) / [SparkFun PRT-14427](https://www.sparkfun.com/products/14427) | $0.95 / about $1.50 |
| 200 mm | [Adafruit 4401](https://www.adafruit.com/product/4401) / [SparkFun flexible PRT-14428](https://www.sparkfun.com/products/14428) | $1.25 / about $1.95 |
| 300 mm | [Adafruit 5384](https://www.adafruit.com/product/5384) | $1.25 |
| 500 mm | [SparkFun flexible PRT-14429](https://www.sparkfun.com/products/14429) | about $2.75 |

Generic "JST SH 1.0 4-pin" double-ended leads from AliExpress-type sellers come wired straight or reversed. Pin 1 at one end must reach pin 1 at the other; [hardware/CABLES.md](../../hardware/CABLES.md#wiring-direction) shows how to tell them apart.

For making cables to length:

| Item | LCSC # and JLC page | Maker | $ @100 | JLC stock | NextPCB |
| --- | --- | --- | --- | --- | --- |
| Housing SHR-04V-S | [C385125](https://www.lcsc.com/product-detail/housings-wire-to-board-wire-to-wire_jst-shr-04v-s_C385125.html) · [JLC](https://jlcpcb.com/partdetail/JST-SHR_04VS/C385125) | JST | 0.066 | 51,108 | [48,282 ($0.069)](https://www.hqonline.com/product-detail/rubber-shells-and-accessories-jst-shr-04v-s-1003355656) |
| Crimp contact SSH-003T-P0.2-H (28 to 32 AWG) | [C263995](https://www.lcsc.com/product-detail/housing-contact_jst-ssh-003t-p0-2-h_C263995.html) · [JLC](https://jlcpcb.com/partdetail/JST-SSH_003T_P0_2H/C263995) | JST | about 0.021 | 340,074 | not checked |
| Crimp contact SSH-003T-P0.2 | [C160231](https://www.lcsc.com/product-detail/housing-contact_jst-ssh-003t-p0-2_C160231.html) · [JLC](https://jlcpcb.com/partdetail/JST-SSH_003T_P02/C160231) | JST | about 0.018 | 52,228 | not checked |
| Clone housing ZX-SH1.0-4PJK | [C7462664](https://www.lcsc.com/product-detail/housings-wire-to-board-wire-to-wire_megastar-zx-sh1-0-4pjk_C7462664.html) · [JLC](https://jlcpcb.com/partdetail/Megastar-ZX_SH1_04PJK/C7462664) | Megastar | 0.013 | 43 | not checked |
| Clone housing SH1.0-4Y | [C7437096](https://www.lcsc.com/product-detail/housings-wire-to-board-wire-to-wire_shou-han-sh1-0-4y_C7437096.html) · [JLC](https://jlcpcb.com/partdetail/SHOUHAN-SH1_04Y/C7437096) | SHOU HAN | 0.013 | 7,622 | [hanxia equivalent, 2,000 ($0.009)](https://www.hqonline.com/product-detail/rubber-shells-and-accessories-hanxia-sh1-0-4y-2500448662) |
| Clone contact ZX-SH1.0-DZ | [C7462671](https://www.lcsc.com/product-detail/housing-contact_megastar-zx-sh1-0-dz_C7462671.html) · [JLC](https://jlcpcb.com/partdetail/Megastar-ZX_SH1_0DZ/C7462671) | Megastar | about 0.008 | 193,310 | not checked |

The contacts are small and need a fine crimp tool (the JST tool is expensive, and the cheap generic tools work poorly at 1.0 mm). Making cables only pays off for odd lengths, such as long runs between racks. With the default relay fitting each cable is its own short I2C bus, so the roughly 1 m limit of plain I2C applies per cable; see the [Qwiic survey](qwiic-i2c-ecosystems.md) for longer links.

## NextPCB

NextPCB's parts store is [HQ Online](https://www.hqonline.com/), and the NextPCB columns above come from its search API.

- It stocks the genuine JST parts (SM04B 56k, BM04B 3.5k, SHR-04V-S 48k). The two connectors are about 8 % under JLC's price and the housing is about 5 % over.
- Its clone range is narrower: BOOMELE 1.0T-4P (57k), HCTL, XUNPU, Megastar, hanxia and CAX. The CAX and hanxia side-entry parts are the cheapest anywhere at about $0.025 to $0.03 at 100, with about 2,000 of each in stock.
- It doesn't expose a Basic or Extended class, and its assembly loading-fee rules are not published on the site, so the per-order fees cannot be compared with JLC's.
- The search wants the full part number with suffix (for example `SM04B-SRSS-TB(LF)(SN)`). A bare `SM04B-SRSS-TB` returns nothing.

## Method and caveats

- BEIXUNZE C54308409 has no LCSC page, so it links to JLC only. The CAX WAFER-SH1.0-4PWB is not on JLC or LCSC.
- JLC data is from JLC's component search API with the terms SH1.0, SM04B, BM04B, 1.0-4P, "1x4P 1mm", "1.0mm 4P", JST SH and SHR-04V-S, filtered on the listed pitch of 1 mm and 4 pins, dropping "JLCPCB Assembly" placeholder rows, which have no stock. In the same data, Basic parts such as crystals show up as Basic, so the "no Basic SH connector" result is not a filter error.
- "SH compatible" is based on the part name and JLC's "Reference Series: SH" field, not on mating tests. For clones, check the datasheet drawing against JST's [SH datasheet](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf) and try one with a real Qwiic cable.
- JLC charges a loading fee per unique Extended part per order; [hardware/COST.md](../../hardware/COST.md) has the fee used in the cost estimate. That estimate counts the fee once for each board version.
- The SparkFun prices are shown on its site as two figures, a sale and a list price, and are given as "about".
