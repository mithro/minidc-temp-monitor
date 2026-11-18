# Cables to order

What to buy to join about 200 sensor boards into chains and to connect each
chain to a hub. Checked on 2026-11-18. Prices and stock move, so confirm them
at checkout.

## Order list

| # | Item | Source | Lots | Pieces | About |
|---|---|---|---|---|---|
| 1 | Double-ended SH 1.0 mm 4-pin lead, 28 AWG, 15 cm, "reverse" | [AliExpress 3256804098040339](https://www.aliexpress.us/item/3256804098040339.html) | 20 x 10 | 200 | $20 |
| 2 | Same lead, 10 cm, "reverse" | same listing | 10 x 10 | 100 | $10 |
| 3 | Same lead, 20 cm, "reverse" | same listing | 5 x 10 | 50 | $5 |
| 4 | Same lead, 15 cm, "same" (for the wiring check only) | same listing | 1 x 10 | 10 | $1 |
| 5 | Double-ended SH 1.0 mm 4-pin lead, 28 AWG, 30 cm, "reverse" | [AliExpress 3256801109294283](https://www.aliexpress.us/item/3256801109294283.html) | 4 x 5 | 20 | $3 |
| 6 | Single-ended SH 1.0 mm 4-pin lead, 28 AWG, 20 cm, tinned ends: BXCONN SH4P-28AWG-200-A1T | [LCSC C53413421](https://www.lcsc.com/product-detail/C53413421.html) | | 20 | $2.19 |
| | **Total** | | | **400** | **about $41 plus shipping** |

Pick the 4-pin (4P) option in each AliExpress listing. Lines 1 to 5 are the
board-to-board cables. Line 6 is for the hub end of each chain.

How sure each line is:

- Lines 1 to 4: the listing offers 2 to 10 pins, 10, 15 and 20 cm, and "same"
  or "reverse" ends, at $0.10 a piece in lots of 10. This comes from the
  listing's search result. AliExpress would not serve the listing page itself
  to the build environment, so the 4-pin price at each length is not confirmed.
- Line 5: the listing is for double-ended SH 1.0 leads in lots of 5 with "Same
  Side" and "Reverse Side" options. That it has a 4-pin 30 cm option, and its
  price, are not confirmed. Any double-ended SH 1.0 4-pin 30 cm lead will do.
- Line 6: read from LCSC. $0.1093 each at 5 or more, 200 in stock, sold in
  multiples of 5.

JLCPCB and LCSC do not stock a double-ended SH 1.0 mm 4-pin lead. Their four SH
4-pin leads are all single-ended, with one housing and bare tinned wire ends,
and each has 60 to 200 in stock:

| Part | Length | Price | Stock |
|---|---|---|---|
| BXCONN SH4P-28AWG-200-A1T, [C53413421](https://www.lcsc.com/product-detail/C53413421.html) | 200 mm | $0.109 | 200 |
| XYECONN XY-SH1.0-28B-200-DD3-4A, [C22459247](https://jlcpcb.com/partdetail/C22459247) | 200 mm | $0.105 | 85 |
| BEIXUNZE SH1.00--4P-100-30A, [C54308409](https://jlcpcb.com/partdetail/C54308409) | 100 mm | $0.102 | 195 |
| HanElectricity SH1.0-4P-1-100(3)-28A-UL1571, [C54529089](https://jlcpcb.com/partdetail/C54529089) | 100 mm | $0.083 | 60 |

So the board-to-board cables come from AliExpress, and JLC/LCSC is only useful
for the hub leads.

## Wiring direction

The cable must be straight through: pin 1 at one end reaches pin 1 at the
other. Pin order on J1 and J2 is 1 GND, 2 VDD, 3 SDA, 4 SCL.

Sellers offer two versions. Lay a lead flat with its wires parallel and not
twisted, then look at the two housings:

- One housing shows its top and the other shows its underside: pin 1 goes to
  pin 1. **This is the one to buy.** Most sellers call it "reverse" (反向).
- Both housings show the same face: pin 1 goes to pin 4. Sellers usually call
  this "same" (同向). It swaps GND with SCL and VDD with SDA, so it puts the
  supply across the wrong pins. Do not use it.

The seller names are not standardised, and the listing picture could not be
checked, so "reverse" is the expected answer, not a confirmed one. Line 4 buys
one lot of the other type so both are on the bench. Before plugging anything
in, check one lead of each type with a meter, pin 1 to pin 1, and use the type
that passes. If the bulk lot turns out to be the wrong type, re-order in the
other direction; the cost of that is about $35 and the delivery time.

A straight-through lead between two boards mounted in line, both face up, sits
with a half twist in it. That is normal and is how Qwiic cables sit.

Wire colours on generic leads follow no standard. Go by pin position.

## Lengths and quantities

Assumptions, because the rack layout is not fixed yet:

- 200 boards, so at most 200 cables between boards and to chain heads.
- Boards sit in line along a rack face. The connectors are on the two short
  ends of the 42 mm board, so the gap a cable spans is the board pitch minus
  42 mm. A cable should be 10 to 20 mm longer than the gap.
- The pitch is somewhere between 2U and 5U (1U is 44.45 mm).

| Board pitch | Gap | Cable |
|---|---|---|
| up to 125 mm (2U is 89 mm) | up to 83 mm | 10 cm |
| up to 175 mm (3U is 133 mm) | up to 133 mm | 15 cm |
| up to 225 mm (4U is 178 mm, 5U is 222 mm) | up to 183 mm | 20 cm |
| up to 325 mm (6U is 267 mm, 7U is 311 mm) | up to 283 mm | 30 cm |

The 15 cm lead works at any pitch up to 3U, with a loop of spare cable at
closer spacing, so 200 of them could build the whole chain alone. The 10 cm and
20 cm lots are for tidier close spacing and for 4U to 5U spacing. The 30 cm
lot is for jumps between rack faces or racks and for hub connections. The 400
pieces are twice what a 200-board build uses; the surplus is what covers not
knowing the mix. Once the pitch is fixed, 220 leads of the right length are
enough.

With the default relay fitting each cable is its own I2C bus, so cable length
does not add up along a chain. Keep any single cable under about 1 m. For runs
longer than 30 cm, make a cable from the housings and crimp contacts listed in
the [connector survey](../docs/research/jst-sh-4pin-connectors.md#cables-and-housings).

## Chain head and hub

The hub is not designed yet. Either hub style is covered by this order:

- Hub with a JST SH 4-pin socket (or any Qwiic or STEMMA QT controller board):
  use one of the double-ended leads, usually a 30 cm one.
- Hub with solder pads, a pin header or screw terminals: use a single-ended
  lead (line 6). Its housing goes into J1 of the first board and the tinned
  ends go to the hub. Buy these only when there is an LCSC order to add them
  to, because shipping costs more than the leads. The AliExpress sellers also
  list single-ended SH 1.0 4-pin leads.

Plan for at least 8 chains, and so at least 8 head leads. Power is passed down
the chain through 28 AWG wire and two contacts per hop, roughly 0.15 to 0.2
ohm per hop for VDD and GND together. At an estimated 5 mA per board that
drops about 0.2 V over 20 boards and about 0.4 V over 30. A 3.3 V chain has
0.5 V to spare (see [Supply voltage](README.md#supply-voltage)), so keep 3.3 V
chains to about 25 boards. A 5 V chain has 2.2 V to spare and can be longer.
The per-board current is an estimate until firmware runs on real boards.
