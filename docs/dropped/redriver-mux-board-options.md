# I2C redriver / mux strip board: options and BOM

Nov 18, 2026 · @Tim 'mithro' Ansell

## Dropped on 18 Nov 2026

**This board is not being built. The document is kept as a record of the options considered.** The sensor boards now carry a RISC-V microcontroller (CH32V003 or CH32V005) that relays I2C from one board to the next, so every cable is its own short bus and no separate redriver or mux board is needed. The current design is in [hardware/ in the repository](https://github.com/mithro/minidc-temp-monitor/tree/main/hardware).

The recommendation, costs and open questions below assumed TMP175 or TMP1075 sensors with strapped addresses on a shared bus. None of them are being acted on. The part data for the I2C buffers, muxes and differential drivers may still be useful if a long hub-to-aisle link is needed later.

## Summary

I recommend **option C, a buffered mux strip**: a TCA9517A buffer plus a TCA9546A 4-channel mux, with Qwiic in, Qwiic out and four switched sensor ports. Twenty assembled boards cost about **$78 in total ($3.90 each)** from JLCPCB, before shipping.

- At 20 boards the fixed assembly fees are larger than the parts, so the gap between the cheapest option (A, $38) and option C is about $40 for the whole build.
- A plain redriver (option A) fixes capacitance but not addresses. 200 sensors at 27 addresses per bus would need all 8 hub mux channels with no spare.
- A mux on each strip gives every strip four fresh address spaces and lets the hub switch off a branch that has hung the bus.
- The differential RJ45 option (D) is only worth its cost if a single cable hop is longer than about 3 m. Its PCA9615 chip is out of stock at JLC today.
- One PCB can cover A and C: with the mux left unfitted it is a plain redriver.

## What the board has to do

The board has two separate jobs, and the options differ in which of them they solve.

| Limit | Where it comes from | What it means for 200 sensors |
| --- | --- | --- |
| Capacitance | I2C allows 400 pF per bus segment. Each sensor board adds roughly 10 pF and Qwiic cable roughly 50 to 100 pF per metre (my estimates, not measured). | A segment holds about 10 sensors plus 1 to 2 m of cable. That matches 20 boards for 200 sensors. |
| Addresses | The TMP175-class sensor has 27 addresses. Eight of them (0x70 to 0x77) are the same range the TCA9548A and TCA9546A muxes use. | 27 sensors per logical bus, or 19 if sensors stay out of the mux range. |
| Fault isolation | Any one sensor or cable holding SDA low hangs every device on the same logical bus. | Smaller switched segments mean a fault takes out one branch, not an aisle. |

All four options keep the choices already in the repo: JST SH 4-pin Qwiic connectors wired GND, 3V3, SDA, SCL, 3.3 V only, and 100 kHz. Each board fits pull-ups on the segment it creates, so sensor boards can keep theirs open. Sensor power is not a constraint: 200 TMP175-class parts draw well under 50 mA in total, so 3.3 V simply passes through.

If the sensor board uses the TMP1075 instead, as its [options doc](https://claude.ai/artifact/7VpZaSGM16YNBMafAXq71m) recommends, the address limit eases: 32 addresses from 0x40 to 0x5F, none in the mux range. Every "19 sensors" figure below then becomes 32, and the recommendation does not change.

Prices below are JLCPCB unit prices at the 10+ tier on 18 Nov 2026. Connectors are priced as genuine JST SM04B-SRSS-TB (C160404, $0.215); the XYECONN clone (C51940130, $0.039) would take about $0.18 off per connector. PCB and assembly fees are my estimates of JLC's standard charges ($8 setup, $1.50 stencil, $3 per Extended part type), not a quote.

## Option A: in-line buffer strip

The cheapest board at about $1.90 each. It repeats SDA and SCL so each strip starts a new 400 pF segment, but every sensor stays on one logical bus.

&#91;embedded content: Option A block diagram · in-line buffer\]

| Part | JLC part | Qty | Unit (USD) | Line (USD) |
| --- | --- | --- | --- | --- |
| TCA9517ADGKR buffer, TI, VSSOP-8, Extended, 17,877 in stock | C201698 | 1 | 0.385 | 0.39 |
| JST SM04B-SRSS-TB connector, Extended | C160404 | 2 | 0.215 | 0.43 |
| 2.2 kΩ 0402 pull-up, Basic. Two fitted downstream, two behind an open jumper upstream | C25879 | 4 | 0.001 | 0.01 |
| 100 nF 0402 decoupling, Basic | C1525 | 2 | 0.002 | 0.01 |
| **Parts per board** |  |  |  | **0.83** |

For 20 boards: parts $17, PCBs (about 12 x 40 mm, 2-layer) $5, assembly fees $16.50. **Total about $38.**

- **Good for:** stretching a chain past 10 sensors or 2 m at almost no cost.
- **Does not fix:** addresses. The hub must still split 200 sensors into buses of 27 or fewer, and one stuck sensor hangs its whole chain.
- **Design note:** TCA9517A strips chain A-side to B-side only, and each adds delay. I would keep to 8 or fewer in series at 100 kHz, to be checked against the datasheet.
- **Alternative chip:** TCA4311ADGKR (C130025, $0.72) adds hot-swap protection and rise-time accelerators for $0.34 more.

## Option B: mux segmenter strip

About $3.30 each. A 4-channel I2C switch hangs four sensor branches off a trunk that passes straight through, so the hub selects one branch at a time.

&#91;embedded content: Option B block diagram · mux segmenter\]

| Part | JLC part | Qty | Unit (USD) | Line (USD) |
| --- | --- | --- | --- | --- |
| TCA9546APWR 4-channel mux, TI, TSSOP-16, Extended, 15,018 in stock | C201653 | 1 | 0.844 | 0.84 |
| JST SM04B-SRSS-TB connector (in, out, four ports), Extended | C160404 | 6 | 0.215 | 1.29 |
| 2.2 kΩ 0402 pull-up, Basic. Two per port | C25879 | 8 | 0.001 | 0.01 |
| 4.7 kΩ 0402 reset pull-up, Basic | C25900 | 1 | 0.002 | 0.00 |
| 100 nF 0402 decoupling, Basic | C1525 | 1 | 0.002 | 0.00 |
| **Parts per board** |  |  |  | **2.15** |

For 20 boards: parts $43, PCBs (about 15 x 50 mm) $6, assembly fees $17.50. **Total about $67.**

- **Good for:** addresses and fault isolation. Each port is its own address space, and an unselected branch adds no capacitance and cannot hang the bus.
- **Does not fix:** reach. The switch is a pass transistor, not a driver, so the selected branch and the whole trunk still share one 400 pF budget.
- **Limit:** the mux has 8 addresses, so at most 8 strips share a trunk. Twenty strips need three or more hub channels.
- **Cheaper mux:** the UMW clone TCA9546APWR(UMW) (C42420613, $0.37) saves $0.47 a board. An 8-channel TCA9548APWR (C130026, $0.73) costs less than the 4-channel TI part but needs four more connectors.

## Option C: buffered mux strip (recommended)

About $3.90 each. Option A's buffer feeds option B's mux, so every hop between strips is redriven and every strip has four switched, separately addressed branches.

&#91;embedded content: Option C block diagram · buffered mux strip\]

| Part | JLC part | Qty | Unit (USD) | Line (USD) |
| --- | --- | --- | --- | --- |
| TCA9517ADGKR buffer, TI, VSSOP-8, Extended | C201698 | 1 | 0.385 | 0.39 |
| TCA9546APWR 4-channel mux, TI, TSSOP-16, Extended | C201653 | 1 | 0.844 | 0.84 |
| JST SM04B-SRSS-TB connector (in, out, four ports), Extended | C160404 | 6 | 0.215 | 1.29 |
| 2.2 kΩ 0402 pull-up, Basic. Two on the buffered node, two per port | C25879 | 10 | 0.001 | 0.01 |
| 4.7 kΩ 0402 reset pull-up, Basic | C25900 | 1 | 0.002 | 0.00 |
| 100 nF 0402 decoupling, Basic | C1525 | 3 | 0.002 | 0.01 |
| **Parts per board** |  |  |  | **2.55** |

For 20 boards: parts $51, PCBs (about 15 x 55 mm) $6, assembly fees $20.50. **Total about $78.**

- **Good for:** all three limits. A trunk of 8 strips carries up to 8 x 4 x 19 = 608 sensor addresses on one hub channel, far more than we need.
- **Capacity in practice:** capacitance, not addresses, sets the size of a branch. Plan on about 10 sensors per port, so one strip can serve 20 to 40 sensors and 20 strips leave plenty of spare.
- **Limit:** at most 8 strips per trunk (mux addresses), which is also about as many buffers as I would put in series.
- **One PCB, two builds:** with the mux and ports unfitted the same board is option A.
- **Design note:** sensors behind a strip must not use 0x70 to 0x77. To confirm at schematic time that the TMP175 clone really has those eight addresses, and which buffer side should face the hub.

## Option D: differential trunk node on RJ45

About $6.70 each, and the only option for long hops. It is the PCA9615-over-Cat5e link already sketched in the README, with the mux added on the local side.

&#91;embedded content: Option D block diagram · differential trunk node\]

| Part | JLC part | Qty | Unit (USD) | Line (USD) |
| --- | --- | --- | --- | --- |
| PCA9615DP differential buffer, NXP, TSSOP-10. **No JLC stock**; price is my approximate figure for Mouser or DigiKey | C2652385 | 1 | 3.00 | 3.00 |
| RJ45 SMD jack HC-RJ45-055-6, Extended, 13,796 in stock. Footprint and pinout still to check | C3000212 | 2 | 0.187 | 0.37 |
| TCA9546APWR 4-channel mux, Extended | C201653 | 1 | 0.844 | 0.84 |
| JST SM04B-SRSS-TB connector (four ports), Extended | C160404 | 4 | 0.215 | 0.86 |
| 0402 resistors, Basic: pull-ups, reset, and termination behind jumpers | C25879 and others | 17 | 0.001 | 0.02 |
| 100 nF 0402 decoupling, Basic | C1525 | 3 | 0.002 | 0.01 |
| **Parts per board** |  |  |  | **5.10** |

For 21 boards (20 nodes plus one at the hub end): parts $107, PCBs (about 20 x 70 mm) $8, assembly fees $24.50. **Total about $140.**

- **Good for:** hops of tens of metres, and noise from power cabling. SparkFun reports the same chip working over 200 ft at 100 kHz.
- **Costs:** twice option C, a much larger board because of the two RJ45 jacks, and the PCA9615 must be bought elsewhere and consigned to JLC or hand-soldered.
- **Not Qwiic on the trunk:** only the four ports take Qwiic cables. The hub needs a matching PCA9615 end.
- **In-stock alternative:** P82B96DGKR (C2652360, $2.67, 970 in stock) is a single-ended high-drive buffer that also reaches tens of metres, with less noise immunity.

## Cost trade-off

Going from the cheapest board to the recommended one costs about $40 across the whole build, because fixed fees dominate at this quantity.

|  | A: buffer | B: mux | C: buffer + mux | D: differential + mux |
| --- | --- | --- | --- | --- |
| Parts per board (USD) | 0.83 | 2.15 | 2.55 | 5.10 |
| Total for 20, assembled (USD) | 38 | 67 | 78 | 140 (21 boards) |
| Per board, assembled (USD) | 1.90 | 3.30 | 3.90 | 6.70 |
| Extends reach | Yes, per hop | No | Yes, per hop | Yes, tens of metres |
| Extends addresses | No | Yes, 4 branches | Yes, 4 branches | Yes, 4 branches |
| Isolates a stuck branch | No | Yes | Yes | Yes |
| Extended part types at JLC | 2 | 2 | 3 | 4, one not stocked |
| Rough board size (mm) | 12 x 40 | 15 x 50 | 15 x 55 | 20 x 70 |

Totals exclude shipping and tax. Switching to clone connectors and the UMW mux would bring option C down to about $2.35 a board, a saving of roughly $31 on 20 boards.

## Open questions

- [ ] How long is the longest single cable hop, hub to first strip or strip to strip? Under about 3 m, option C is enough. Longer needs option D for that hop.
- [ ] How many sensors per rack face, and how many rack faces? That sets ports per strip (four assumed) and strips per trunk.
- [ ] Genuine JST and TI parts, or clones where they exist? At 20 boards I assumed genuine.
- [ ] Should the strip match the sensor board's width and mounting so both fit the same rail or adhesive strip?

Once an option is picked, the next step is the KiCad schematic and layout in the repo.

## Sources

- Prices and stock: JLCPCB parts catalogue, queried 18 Nov 2026.
- Connector, voltage and PCA9615 link choices: [Qwiic and related I2C sensor ecosystems](https://github.com/mithro/minidc-temp-monitor/blob/main/docs/research/qwiic-i2c-ecosystems.md) in the repo.
- Sensor choice and address count: [I2C temperature sensors on LCSC](https://github.com/mithro/minidc-temp-monitor/blob/main/docs/research/i2c-temperature-sensors-lcsc.md) in the repo.
- Chip behaviour (buffer chaining, mux addresses, TMP175 address list), capacitance figures, JLC fee levels and the PCA9615 distributor price are from my own knowledge and were not checked against datasheets or quotes today.
