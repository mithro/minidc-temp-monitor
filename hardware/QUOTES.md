# Production quotes: JLCPCB and NextPCB

Quotes taken on 18 Nov 2026 for board revision 0.2, by uploading the panel
gerbers (`sensor-*/out/panel/gerbers.zip`) to each company's online quote
page. Nothing was ordered and no account was used. All prices are in USD and
leave out shipping, tax and import duty.

The quantity is 15 panels of 16 boards, 240 boards of each version. The build
needs at least 200 boards and NextPCB takes panels in multiples of 5.

## Result

| 240 assembled boards | JLCPCB | NextPCB | NextPCB / JLCPCB |
|---|---|---|---|
| `sensor-ch32v003`, lead-free HASL | 139.86 (0.58 per board) | 528.80 (2.20 per board) | 3.8 x |
| `sensor-ch32v005`, ENIG | 233.30 (0.97 per board) | 651.24 (2.71 per board) | 2.8 x |
| `sensor-ch32v005`, lead-free HASL | 213.90 (0.89 per board) | 525.73 (2.19 per board) | 2.5 x |

On these figures JLCPCB is the cheaper place to build both boards. The two
columns are not the same kind of number. The NextPCB figures are its online
price for the uploaded gerbers, placement file and parts list. The JLCPCB
figures are its online price for the bare panels plus assembly calculated
from its published fees, because JLCPCB asks for a sign-in before it prices
assembly (see [What is and is not a quote](#what-is-and-is-not-a-quote)).

The CH32V005 rows are also not like for like: the JLCPCB figure includes
79.20 of X-ray inspection from its fee list, and no X-ray was requested from
NextPCB. Without X-ray the JLCPCB CH32V005 board is 154.10 with ENIG and
134.70 with lead-free HASL.

| For 240 boards | JLCPCB V003 | JLCPCB V005 | NextPCB V003 | NextPCB V005 |
|---|---|---|---|---|
| Finish | lead-free HASL | ENIG | lead-free HASL | ENIG |
| Bare panels | 26.50 | 45.90 | 49.30 | 174.81 |
| Parts | 79.85 | 72.77 | 75.15 | 72.08 |
| Assembly | 33.51 | 35.43 | 404.35 | 404.35 |
| X-ray inspection of the QFN | none | 79.20 | none | not requested |
| **Total** | **139.86** | **233.30** | **528.80** | **651.24** |

JLCPCB showed a build time of 2 days for the bare panels with HASL and 3 days
with ENIG; its assembly time is shown after the sign-in. NextPCB showed 8 to
12 working days for the whole CH32V003 order and 11 to 16 for the CH32V005
order, both with lead-free HASL.

[COST.md](COST.md) has the JLCPCB figures line by line.

## JLCPCB

Page: `cart.jlcpcb.com/quote`. Settings: FR-4, 2 layers, 107 x 132 mm, "Panel
by Customer" with 2 columns and 8 rows, 1.6 mm, green, 1 oz, tented vias,
0.3 mm minimum hole, standard build time.

Bare panel price for 15 panels, the same for both boards:

| | HASL (with lead) | Lead-free HASL | ENIG (1 U") |
|---|---|---|---|
| Engineering fee | 4.00 | 4.00 | 4.00 |
| Boards | 20.40 | 20.40 | 20.40 |
| Finish | none | 2.10 | 21.50 |
| **Total** | **24.40** | **26.50** | **45.90** |

The page was driven to the panel settings, and the price for 15 panels was
then read from the page's own price service.

Assembly is priced from JLCPCB's published Economic PCBA fees (help article
"PCB Assembly Cost: What Does the Price Include?", updated 22 Oct 2026) and
the catalogue price of each part at the order quantity:

| Fee | Published rate | V003 | V005 |
|---|---|---|---|
| Setup | 8.18 | 8.18 | 8.18 |
| Stencil | 1.53 | 1.53 | 1.53 |
| Extended parts | 3.07 per type, 3 types | 9.21 | 9.21 |
| SMT assembly | 0.0016 per joint | 14.59 (38 joints per board) | 16.51 (43 joints per board) |
| X-ray inspection | 0.33 per part for 201 to 500 parts | none | 79.20 |

The X-ray fee is the largest single line on the CH32V005 board. JLCPCB's
article says it is required for "BGA, QFN, and other leadless packages" and
charges it per part. Whether JLCPCB applies it to this 12-pin QFN is only
shown in the signed-in quote. It is 0.33 per board. With it and ENIG the
CH32V005 board costs 0.39 more per board than the CH32V003 board; without it,
0.06 more.

All ten parts were in stock at JLCPCB on the day: 32,792 of the CH32V003J4M6
and 11,691 of the CH32V005D6U6.

## NextPCB

Page: `www.nextpcb.com/pcb-assembly-quote`, NextPCB's standard turnkey
assembly service. It took the panel gerbers, a placement file and a parts
list without a sign-in. `scripts/gen_nextpcb.py` writes the two files it
needs to `sensor-*/out/nextpcb/`: NextPCB matches parts by manufacturer part
number, wants one board's parts list, and takes the placement file only as a
spreadsheet.

Settings: FR-4, 2 layers, 107 x 132 mm, "Panel by Customer" 2 x 8, 15 panels
(240 boards), TG130, 1.6 mm, green, 1 oz, tented vias, single-sided assembly,
depanelization on (the page's default; the price was the same with it off),
no X-ray inspection.

The lead-free HASL quote was read from the page. The other two finishes were
priced by sending the same request to the page's price service with only the
finish changed; parts and assembly came back unchanged.

| For 240 boards | V003 | V005 |
|---|---|---|
| Bare panels, HASL with lead | 39.87 | 39.87 |
| Bare panels, lead-free HASL | 49.30 | 49.30 |
| Bare panels, ENIG | 174.81 | 174.81 |
| Parts | 75.15 | 72.08 |
| Assembly: setup | 50.00 | 50.00 |
| Assembly: material handling | 20.00 | 20.00 |
| Assembly: soldering and engineering | 230.58 | 230.58 |
| Assembly: operation fee | 103.77 | 103.77 |
| **Total with lead-free HASL** | **528.80** | **525.73** |
| **Total with ENIG** | **654.31** | **651.24** |

NextPCB matched all 9 part types on both boards. Its part prices, with the
spare parts it adds for placement losses:

| Part | Unit price | Bought for 240 boards | Stock |
|---|---|---|---|
| CH32V003J4M6 | 0.17787 | 243 | in stock |
| CH32V005D6U6 | 0.16522 | 243 | 4 to 7 days |
| ZX-SH1.0-4PWT (JST SH clone) | 0.04674 | 485 | in stock |
| SDNT1005X104F3950FTF (NTC) | 0.01094 | 280 | in stock |
| KT-0603R (LED) | 0.00696 | 270 | in stock |
| CL05A105KA5NQNC (1 uF) | 0.00502 | 280 | in stock |
| 0603WAF4701T5E (4k7) | 0.00240 | 510 | in stock |
| CL05B104KO5NNNC (100 nF) | 0.00217 | 521 | in stock |
| 0402WGF1001TCE (1k) | 0.00118 | 280 | in stock |
| 0402WGF1003TCE (100k) | 0.00081 | 280 | in stock |

NextPCB quoted DHL shipping of 37.90 for the order. JLCPCB's shipping for the
assembled order is only shown after a sign-in.

### NextPCB Rev 0 PCBA

"Rev 0 PCBA" is a separate NextPCB service for fast prototypes, and it cannot
build this order:

- It builds 5 or 10 assembled boards only.
- It does not accept panelized files, and the smallest board it takes is
  50 x 50 mm. This board is 42 x 13 mm.
- It only fits parts in stock at HQ Online. The CH32V005D6U6 was on a 4 to 7
  day lead time there.
- It needs a sign-in, so no price was obtained.

NextPCB advertises free assembly, up to 500 USD, on a first Rev 0 PCBA order.
That could suit a first batch of 5 or 10 CH32V003 boards if NextPCB panelizes
the single board itself.

## Open questions from revision 0.2

**Finish for the CH32V005 QFN.** ENIG at JLCPCB adds 19.40 to the whole order
over lead-free HASL (0.08 per board), so the CH32V005 board is costed with
ENIG and the question of whether HASL would be good enough for a 0.4 mm pitch
QFN does not need answering. At NextPCB ENIG adds 125.51. The CH32V003 board
is an SOP-8 and stays on HASL.

**Panel tooling holes and fiducials.** Both companies' file checks read the
panel without errors: JLCPCB detected a 2 layer 132 x 107 mm board with
0.2 mm minimum track and 0.3 mm minimum hole, and NextPCB's design check
passed every item. JLCPCB's quote page accepted "Panel by Customer" together
with Economic assembly and "Tooling holes: Added by Customer". JLCPCB's
placement preview, which shows the parts on the panel and is where the
fiducials and rotations are checked, comes after the sign-in and was not
reached.

## What is and is not a quote

| Figure | Source |
|---|---|
| JLCPCB bare panels | Online price for the uploaded gerbers |
| JLCPCB parts | Catalogue prices and stock on 18 Nov 2026 |
| JLCPCB assembly and X-ray | Calculated from published fees. The page sends you to a sign-in before the parts list and placement file can be uploaded |
| NextPCB panels, parts and assembly | Online price for the uploaded gerbers, placement file and parts list, without X-ray inspection. Not reviewed by NextPCB's engineers |
| NextPCB Rev 0 PCBA | Not quoted: needs a sign-in and does not fit this order |

To turn the JLCPCB figures into a full quote, sign in at `cart.jlcpcb.com/quote`,
upload `out/panel/gerbers.zip`, choose "Panel by Customer" 2 x 8, 15 panels,
turn on PCB Assembly (Economic, top side, tooling holes added by customer),
and upload `out/panel/bom-jlc.csv` and `out/panel/cpl-jlc.csv`. The things to
read off are the X-ray line for the CH32V005 and the placement preview.
