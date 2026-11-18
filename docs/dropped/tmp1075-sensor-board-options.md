# Temp sensor pass-through board: options, BOM and cost

2026-11-18 · Tim 'mithro' Ansell

## Summary and recommendation

**Chosen on 18 Nov: option B with clone SH connectors, and the address set by 0 Ω resistors placed per panel position.** That is about $0.36 of parts per board and about $119 for 200 assembled boards, before shipping, tax and cables. The table shows the three options as first proposed.

| Option | What it is | Parts per board | 200 boards assembled (estimate) |
| --- | --- | --- | --- |
| A. Lean | TMP1075, clone SH connectors, hand-set address jumpers | $0.34 | $113 |
| **B. Recommended** | TMP1075, genuine JST connectors, identify LED, addresses preset per panel position | $0.56 | $157 |
| C. Precision | TMP117 (±0.1 °C), genuine JST connectors, only 4 addresses | $1.35 | $314 |

Three findings shape this:

- **The sensor should change from the earlier draft.** The genuine TI TMP1075DGKR ([C2864807](https://jlcpcb.com/partdetail/C2864807)) is $0.236 at 100 with 14,337 in stock, against $0.385 for the UMW TMP175 clone. It has 32 addresses (0x40 to 0x5F), none of which overlap the 0x70 to 0x77 range used by TCA9548A muxes. Eight of the TMP175's 27 addresses do overlap it.
- **The sensor is no longer the main cost.** In option B the two connectors cost more than the sensor, and a branded 100 mm Qwiic cable ($0.95 retail) would cost more than the whole board. Generic cables at about $0.10 fix that.
- **The options differ by $44 across 200 boards (A to B).** That buys connectors known to mate with Qwiic cables, an LED to find a board in the rack, and no hand soldering of 200 address jumpers.

Option C is not a 200-off board. A handful of them make sense as reference points to check the cheap sensors against.

## Requirements and assumptions

These come from the request and the earlier research in the repo. The ones marked "assumed" are mine and easy to change.

- **Function:** one I2C temperature point on a small strip PCB, with a connector at each end so boards daisy-chain.
- **Address:** set per board by strapping, with no programming step.
- **Quantity:** at least 200 boards, with about 20 redriver or mux boards (designed separately) splitting the bus. That is about 10 sensor boards per bus segment.
- **Connector:** Qwiic / STEMMA QT, JST SH 4-pin, pin 1 GND, 2 V+, 3 SDA, 4 SCL, as recommended in the [Qwiic survey](https://github.com/mithro/minidc-temp-monitor/blob/main/docs/research/qwiic-i2c-ecosystems.md).
- **Supply:** 3.3 V on the chain (assumed). The recommended sensor also runs at 5 V, so nothing on the board limits this.
- **Pull-ups:** none fitted on sensor boards. They belong on the hub or redriver, so a chain does not stack them.
- **Build:** assembled by JLCPCB from LCSC stock, in KiCad, 2-layer, parts on one side (assumed).
- **Target accuracy:** about ±1 °C is enough for aisle monitoring, with a few precision points to check against (assumed).

## Block diagrams

[embedded drawing, not exported: system context · hub, redriver, chain of sensor boards]

The sensor board is the highlighted box. Every board on a segment needs its own address, and addresses can repeat on other segments if board (b) is a mux.

[embedded drawing, not exported: board block diagram · option B]

This is option B. Option A is the same without the LED, and option C swaps the sensor for a TMP117 with a single address pin. Four solder pads at each end sit in parallel with J1 and J2.

## Options and BOMs

All three options share one layout idea: a strip of about 10 × 28 mm with a connector at each end, the sensor in the middle and the four bus nets running straight through. Prices are JLCPCB unit prices in USD at the price break that 200 boards reach, read from JLC's parts API on 18 Nov 2026. Every sensor and connector is a JLC Extended part; the passives and LED are Basic.

### Option A: lean

The cheapest board that meets the brief. Addresses are set by hand with solder jumpers, and the connectors are an SH-compatible clone that has not yet been tried with real Qwiic cables.

| Ref | Part | LCSC # | Qty | Unit $ | Line $ |
| --- | --- | --- | --- | --- | --- |
| U1 | TMP1075DGKR, TI, VSSOP-8 | [C2864807](https://jlcpcb.com/partdetail/C2864807) | 1 | 0.2359 | 0.2359 |
| J1, J2 | ZX-SH1.0-4PWT, Megastar, side entry | [C7430446](https://jlcpcb.com/partdetail/C7430446) | 2 | 0.0533 | 0.1066 |
| C1 | 100 nF 0402 | [C1525](https://jlcpcb.com/partdetail/C1525) | 1 | 0.0024 | 0.0024 |
| JP1 to JP5 | Address solder jumpers (copper only) |  | 5 | 0 | 0 |
|  | **Parts per board** |  |  |  | **0.345** |

### Option B: recommended

The same circuit with genuine JST connectors, an identify LED, and the address preset in copper so most boards need no hand work.

| Ref | Part | LCSC # | Qty | Unit $ | Line $ |
| --- | --- | --- | --- | --- | --- |
| U1 | TMP1075DGKR, TI, VSSOP-8 | [C2864807](https://jlcpcb.com/partdetail/C2864807) | 1 | 0.2359 | 0.2359 |
| J1, J2 | SM04B-SRSS-TB(LF)(SN), JST, side entry | [C160404](https://jlcpcb.com/partdetail/C160404) | 2 | 0.1538 | 0.3076 |
| C1 | 100 nF 0402 | [C1525](https://jlcpcb.com/partdetail/C1525) | 1 | 0.0024 | 0.0024 |
| D1 | Red LED 0603 on the ALERT pin | [C2286](https://jlcpcb.com/partdetail/C2286) | 1 | 0.0077 | 0.0077 |
| R1 | 1 kΩ 0402, LED resistor | [C11702](https://jlcpcb.com/partdetail/C11702) | 1 | 0.0013 | 0.0013 |
| R2, R3 | 4.7 kΩ 0402 pull-up pads, not fitted | [C25900](https://jlcpcb.com/partdetail/C25900) | 0 | 0.0017 | 0 |
| JP1 to JP5 | Address jumpers, preset per panel position |  | 5 | 0 | 0 |
|  | **Parts per board** |  |  |  | **0.555** |

What the extras do:

- **Identify LED.** The sensor's ALERT output is open-drain and its polarity is a register bit. The hub can therefore light the LED on one address to show which physical board it is. It is off in normal use, so it adds no heat.
- **Preset addresses.** A 32-up panel can give each position a different address in copper, with the address printed on the silkscreen. Seven panels make 224 boards, which is seven full sets of 32 addresses. The jumpers stay, so any board can still be changed by hand.
- **Solder pads.** Four plated holes at each end, in parallel with the connectors, cost nothing and allow a soldered cable where a plug is not wanted.

### Option C: precision variant

A different sensor and footprint on the same outline, for a few reference points. It is not suitable for all 200 points, because 4 addresses per bus would need a mux channel for every 4 boards.

| Ref | Part | LCSC # | Qty | Unit $ | Line $ |
| --- | --- | --- | --- | --- | --- |
| U1 | TMP117AIDRVR, TI, WSON-6 2×2 mm, ±0.1 °C | [C699536](https://jlcpcb.com/partdetail/C699536) | 1 | 1.0384 | 1.0384 |
| J1, J2 | SM04B-SRSS-TB(LF)(SN), JST, side entry | [C160404](https://jlcpcb.com/partdetail/C160404) | 2 | 0.1538 | 0.3076 |
| C1 | 100 nF 0402 | [C1525](https://jlcpcb.com/partdetail/C1525) | 1 | 0.0024 | 0.0024 |
| JP1 | Address jumper, 4-way (GND, V+, SDA, SCL) |  | 1 | 0 | 0 |
|  | **Parts per board** |  |  |  | **1.348** |

The TMP117 has risen from $0.73 to $1.04 at 100 since the survey two days ago, and JLC stock has fallen from 10,383 to 2,916.

### Option D: MCU and thermistor, self-addressing (added 18 Nov, under discussion)

A cheap RISC-V MCU replaces the sensor chip, reads an NTC thermistor with its ADC and answers on I2C. About $0.32 of parts per board and about $113 for 200 assembled, which is $6 less than the chosen build. Every board is identical, with no strap resistors. RISC-V is Tim's stated preference over ARM or 8051; the cheapest ARM part (Puya PY32F002B, $0.109) would take the total to about $97.

| Ref | Part | LCSC # | Qty | Unit $ | Line $ |
| --- | --- | --- | --- | --- | --- |
| U1 | CH32V003J4M6, WCH, RISC-V, SOP-8 | [C5346354](https://jlcpcb.com/partdetail/C5346354) | 1 | 0.1886 | 0.1886 |
| RT1 | 10 kΩ 1% NTC 0402, Sunlord | [C95939](https://jlcpcb.com/partdetail/C95939) | 1 | 0.0100 | 0.0100 |
| R2 | 10 kΩ 1% 0402 divider resistor |  | 1 | 0.0010 | 0.0010 |
| J1, J2 | ZX-SH1.0-4PWT, Megastar, side entry | [C7430446](https://jlcpcb.com/partdetail/C7430446) | 2 | 0.0533 | 0.1066 |
| C1 | 100 nF 0402 | [C1525](https://jlcpcb.com/partdetail/C1525) | 1 | 0.0024 | 0.0024 |
| D1, R1 | Red LED 0603 and 1 kΩ 0402 | [C2286](https://jlcpcb.com/partdetail/C2286), [C11702](https://jlcpcb.com/partdetail/C11702) | 1 each | 0.0090 | 0.0090 |
| TP1 to TP3 | Programming pads: SWIO, V+, GND (copper only) |  | 3 | 0 | 0 |
|  | **Parts per board** |  |  |  | **0.318** |

RISC-V MCUs in stock at JLC on 18 Nov, at the 200-piece price:

| Part | LCSC # | Package | $ at 200 | JLC stock | Notes |
| --- | --- | --- | --- | --- | --- |
| CH32V005D6U6 | [C49006243](https://jlcpcb.com/partdetail/C49006243) | QFN-12, 2 × 2 mm | 0.159 | 11,705 | Cheapest. Newer family with a 12-bit ADC |
| **CH32V003J4M6** | [C5346354](https://jlcpcb.com/partdetail/C5346354) | SOP-8 | 0.189 | 32,797 | Most mature open tooling, 10-bit ADC |
| CH32V006F8U7 | [C55112440](https://jlcpcb.com/partdetail/C55112440) | QFN-20 | 0.194 | 1,428 | Larger sibling of the V005 |
| CH32V003F4U6 | [C5299908](https://jlcpcb.com/partdetail/C5299908) | QFN-20, 3 × 3 mm | 0.220 | 6,872 | More pins, for several thermistors |
| CH32X033F8P6 | [C19268290](https://jlcpcb.com/partdetail/C19268290) | TSSOP-20 | 0.288 | 3,837 | Adds USB, not needed here |

The 200-board estimate is $63.60 of parts, $9.60 of placement (30 joints) and $40 of fixed costs, which now include a third Extended part type. With the CH32V005 it is about $108.

Ways the boards could address themselves:

| Method | Wires | Hub learns chain order | Extra hardware |
| --- | --- | --- | --- |
| Unique-ID discovery: all boards start on one shared address and the hub assigns each a new one, using I2C arbitration on the chip's unique ID (the SMBus ARP idea) | 4, standard Qwiic | No | None |
| Token line: each board holds an enable line to the next board low until it has an address | 5, so a 5-pin connector and cable | Yes | One more pin per connector |
| Address written when the board is flashed | 4, standard Qwiic | No | None, but not automatic |

Costs and risks: firmware has to be written, all 200 boards need flashing through pogo pads, thermistor accuracy is uncalibrated (my estimate is about ±0.5 °C near 25 °C), and a hung MCU can hold the bus for the whole chain. The ADC resolutions, unique-ID and one-wire programming details for the WCH parts are from memory and need checking in their datasheets.

### Sensor choice behind the options

The TMP1075 wins on price, address count and accuracy among the parts that fit an 8-pin LM75-style footprint. Accuracy and address figures are from the TI datasheets ([TMP1075](https://www.ti.com/lit/ds/symlink/tmp1075.pdf), [TMP175 / TMP75](https://www.ti.com/lit/ds/symlink/tmp175.pdf)); the clone's accuracy is its listing claim.

| Sensor | LCSC # | $ at 200 | Addresses per bus | Max error | Supply | JLC stock |
| --- | --- | --- | --- | --- | --- | --- |
| TMP1075DGKR (TI) | [C2864807](https://jlcpcb.com/partdetail/C2864807) | 0.236 | 32 (0x40 to 0x5F) | ±1 °C, -40 to 110 °C | 1.7 to 5.5 V | 14,337 |
| TMP75AIDR (TI) | [C30389](https://jlcpcb.com/partdetail/C30389) | 0.201 | 8 (0x48 to 0x4F) | ±2 °C, -25 to 85 °C | 2.7 to 5.5 V | 4,736 |
| TMP175AIDGKR (UMW clone) | [C5158047](https://jlcpcb.com/partdetail/C5158047) | 0.398 | 27, of which 8 sit at 0x70 to 0x77 | ±0.5 °C claimed (TI original: ±1.5 °C) | 2.7 to 5.5 V | 11,386 |
| TMP117AIDRVR (TI) | [C699536](https://jlcpcb.com/partdetail/C699536) | 1.038 | 4 | ±0.1 °C, -20 to 50 °C | 1.7 to 5.5 V | 2,916 |

The TMP1075, TMP75, TMP175 and LM75 share one 8-pin pinout, and all come in the 3 × 3 mm VSSOP / MSOP package. One footprint therefore takes any of them if stock runs out.

## Cost for 200 boards

Option B costs about $157 for 200 assembled boards, or $0.78 each, before shipping, import tax and cables. Parts are live prices; the PCB, stencil and fee lines are my estimates and need a real JLC quote.

The chosen build, option B with clone connectors and three 0 Ω strap resistors ([C17168](https://jlcpcb.com/partdetail/C17168), $0.0012 each), comes to $71.50 of parts and $10.20 of placement (32 joints) plus the same $37 of fixed costs: **about $119 for 200, or $0.59 a board.**

| Cost line | A. Lean | B. Recommended | C. Precision |
| --- | --- | --- | --- |
| Parts, 200 boards | $69.00 | $111.00 | $269.70 |
| Placement, $0.0016 per joint (22 / 26 / 21 joints) | $7.00 | $8.30 | $6.70 |
| Assembly setup, Economic | $8.20 | $8.20 | $8.20 |
| Extended-part fees, 2 part types at $3 | $6.00 | $6.00 | $6.00 |
| Stencil (estimate) | $8.00 | $8.00 | $8.00 |
| PCBs, 7 to 10 panels of 100 × 100 mm, 2-layer (estimate) | $15.00 | $15.00 | $15.00 |
| **Total for 200** | **$113** | **$157** | **$314** |
| **Per board** | **$0.57** | **$0.78** | **$1.57** |

- **Fees.** The setup fee and per-joint rate are from JLC's [assembly price page](https://jlcpcb.com/help/article/pcb-assembly-price) as reported by a web search, not from a quote. The Extended-part fee may now be $1.50 per type, which would take $3 off each total.
- **Fixed costs are about $37 per order.** That is $0.19 a board at 200 and $0.09 at 400, so ordering spares in the same batch is cheap.
- **Cables are extra, roughly $20 to $30 for 200.** Each board needs one cable. Cables will come from AliExpress or JLC, not Adafruit. An AliExpress listing for double-ended SH 1.0 mm 28 AWG cables in 10, 15 or 20 cm shows about $0.10 each in lots of 10, so roughly $20 to $30 for 200 (seen in a search result on 18 Nov, not a checked cart price). JLC/LCSC lists SH 4-pin leads at $0.097 (100 mm, C54308409) and $0.105 (200 mm, C53413421), but with only about 200 of each in stock. Order a sample lot first and check with a meter that pin 1 goes to pin 1, since sellers offer both same and reverse wiring. Adafruit's $0.95 cable would have been $190.
- **Swapping the connector only** (option A's clone on option B's board) saves $40 on 200 boards. Swapping to the 8-address TMP75 saves $7.

## Trade-offs

### Address strapping

**Recommended: every PCB identical, with the address set by which 0 Ω resistors the assembly line places at each panel position.** The copper and silkscreen are the same on all boards, so the panel is one design. The address mix lives in the placement file and can change from order to order without touching the PCB.

The TMP1075 reads three pins: A2 takes GND or V+, and A1 and A0 each take GND, V+, SDA or SCL. No pin may float. Each board therefore carries ten 0402 resistor positions (four for A0, four for A1, two for A2), and exactly three are fitted.

| Method | Extra cost for 200 | Hand work | Main drawback |
| --- | --- | --- | --- |
| **0 Ω resistors per panel position** | About $2.60 (3 Basic resistors and 6 joints a board) | None | Boards look alike, so the address is read from which pads are fitted |
| Address preset in copper per panel position | None | None | The panel holds 20 different designs, which JLC may surcharge, and the address mix is frozen in the Gerbers |
| Solder jumpers set by hand | None | Up to 3 jumpers on nearly every board | Slow, and easy to set two boards the same |
| DIP switch | $30 or more | Set by hand, no soldering | Cannot select SDA or SCL, so only 8 addresses |

How it works in practice:

- **Panel.** 20 boards per panel (2 × 10, about 70 × 110 mm with rails), joined by mouse bites, because JLC's Economic assembly does not take V-cut panels. Ten panels make 200 boards; an eleventh adds 20 spares for about $12.
- **Address mix.** Each panel carries 20 different addresses, 0x40 to 0x53. Ten panels then give ten boards at each address. Any chain of up to 20 boards can be built with no clashes, and a 10-board chain uses either the low or the high half.
- **Files.** The panel is built from the single board with KiKit. A small script writes the panel BOM and placement file, fitting a different set of three resistors at each position.
- **Reading the address.** A silkscreen legend beside the resistor pads (G, V, D, C for GND, V+, SDA, SCL) shows the address from the fitted pads. The identify LED and a bus scan do the rest. A blank silkscreen box leaves room for a pen mark.
- **Rework.** A board is re-addressed by moving one 0402 resistor or bridging the other pad with solder.

To confirm with JLC before ordering: that a customer-made panel can use a panel-level placement file in which positions are populated differently.

### Connectors

The genuine JST part costs $0.15 and the Megastar clone $0.05, so the gap is $0.20 per board and $40 on the order. The two share a land pattern, so the footprint does not commit us. A sensible path is to order the first batch with genuine parts and trial a few clone connectors against real cables before any larger run. JLC stock of the genuine part has fallen from about 67,000 to 13,523 since yesterday's connector survey, which is still far more than the 400 needed.

### Bus length and loading

Each board adds little load, so cable length, not board count, sets the segment limit. The TMP1075 datasheet gives 5 pF per input pin. My estimate, not a measurement, is about 8 pF per board with pads and connector, and 50 to 100 pF per metre of 4-wire cable. Ten boards on 150 mm cables then come to about 80 pF of boards plus 75 to 150 pF of cable, inside the 400 pF limit for standard I2C. That matches the planned ratio of one redriver per 10 boards.

### Things left off on purpose

- **No regulator or level shifter.** The TMP1075 runs from 1.7 to 5.5 V, so the board works on 3.3 V Qwiic or 5 V STEMMA QT chains as it is. The one caution is that every board on a chain shares the same V+.
- **No ESD diodes.** They would add capacitance to every board on the bus. Protection is better placed once per segment, on the redriver.
- **No pull-ups fitted.** Pads only, for a chain used without a hub board.
- **ALERT is not bussed.** The Qwiic cable has no fifth wire, so the hub polls. ALERT only drives the LED.

### Mounting

The board allows for every mounting method (decided 18 Nov). The outline grows from about 10 × 28 mm to about 12 × 36 mm to make room; these sizes are estimates until layout.

- **Screw or standoff:** one 3.2 mm hole for M3 at the end away from the sensor.
- **Zip tie:** a notch in each long edge beside the hole, so a tie wraps the board without sliding. A tie can also pass through the hole.
- **Adhesive pad:** the back is flat, with no parts and no through-hole solder joints. The optional cable solder pads therefore become surface pads on the top.
- **Magnet:** a bare area of about 10 × 10 mm on the back takes a glued disc magnet, or a ring magnet goes under the M3 screw.
- **Thermal isolation:** a routed slot separates the mounting end from the sensor, so the sensor reads air and not the rack metal it is fixed to.

The extra PCB area changes the cost by well under a cent per board.

## Open questions and next steps

Once an option is picked, the next step is the KiCad schematic and layout for it. These answers would change the design:

- [ ] Which sensor: the TMP1075 with strap resistors (chosen build), or the RISC-V MCU and thermistor (option D)? Clone connectors are decided.
- [ ] Is 3.3 V on the chain confirmed, or should the hub side plan for 5 V?
- [ ] Answered: the board allows for all mounting options (see Mounting above).
- [ ] Typical spacing between boards on a rack face, which sets cable length and the cable budget.
- [ ] Is the identify LED wanted, or is any light in the aisle unwelcome?
- [ ] How many precision (option C) boards, if any?

Still to verify before ordering: a JLC quote for the panel and assembly fees, whether JLC accepts a 32-up panel with per-position addresses as one design, and that a hand-held TMP1075 board reads within tolerance of a TMP117.

## Sources

- Live prices and stock: JLCPCB parts API, read 18 Nov 2026. Each LCSC number above links to its JLC part page.
- [TI TMP1075 datasheet](https://www.ti.com/lit/ds/symlink/tmp1075.pdf): address table, accuracy, supply range, pin capacitance, ALERT output.
- [TI TMP175 / TMP75 datasheet](https://www.ti.com/lit/ds/symlink/tmp175.pdf): address table and accuracy.
- [JLCPCB assembly price page](https://jlcpcb.com/help/article/pcb-assembly-price): setup and per-joint fees, as summarised by a web search.
- Earlier project research: [sensor survey](https://github.com/mithro/minidc-temp-monitor/blob/main/docs/research/i2c-temperature-sensors-lcsc.md) and [Qwiic ecosystem survey](https://github.com/mithro/minidc-temp-monitor/blob/main/docs/research/qwiic-i2c-ecosystems.md), plus the JST SH connector survey.
- TMP117 accuracy and address count, and the cable capacitance figures, are from my own knowledge, not from pages opened today.
