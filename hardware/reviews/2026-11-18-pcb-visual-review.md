# PCB visual review, 18 Nov 2026

Review of `sensor-ch32v003` and `sensor-ch32v005` as they stood at commit
64f9dbc (auto-routed layout, board revision 0.1). A separate reviewer rendered
both boards with `kicad-cli` (3D views and per-layer plots at 1200 to 5000 dpi)
and backed what it saw with a `pcbnew` dump of pads, tracks, vias and zone
fills, plus DRC runs with stricter rules.

Coordinates are millimetres from the board's top left corner. JLCPCB limits
quoted here are from memory and were not checked against their capability page.

**Verdict:** neither board is ready to order. The CH32V005 board has one
must-fix, and both share a set of should-fix items. Nothing pushes either
board out of JLCPCB's cheapest 2-layer class.

## Must fix

**M1. CH32V005: the MCU's only ground is a single thin via chain, and C1 does not decouple it.**
The QFN-12's only ground is the exposed pad. Its via lands on a 20 mm² back
copper island cut off from the rest of the back pour (the back fill is in
three pieces of 250.7, 77.3 and 20.0 mm²). The island reaches the rest of
ground through one route: 0.3 mm track to the TP3 via, 0.2 mm track to a via
at (27.5, 10.8), then a top pour piece and a 0.2 mm track to J2 pin 1's via.
C1's ground pad sits on its own 2.8 mm² island with one via, so the C1 to
exposed pad loop is about 30 mm although the parts are 3 mm apart. One bad via
or cracked joint leaves the MCU with no ground.

## Should fix

- **S1. VDD trunk is thin and indirect.** CH32V003: J1.2, via, 0.4 mm on the
  back looping under the hole (29 mm), via, U1 pad 4, a 0.2 mm neck for 3 mm,
  C1 pad 1, 0.4 mm, via, back, via, J2.2. Four 0.3 mm vias in series and all
  downstream current through the MCU supply pad. CH32V005: 0.4 mm with two
  vias but 34 mm long, 0.5 mm from the board edge. About 55 to 60 mΩ per board.
- **S2. One via per connector ground pin.** All chain ground current goes
  through single 0.3 mm vias.
- **S3. Fragmented top pour, no stitching.** CH32V003 top: 5 pieces, 3 held by
  one via, plus a 0.2 mm wide dead-end sliver. CH32V005 top: 7 pieces, 5 held
  by one via; its back pour is cut in three by VDD and downstream I2C tracks.
- **S4. SDA_UP and SCL_UP split around the mounting hole.** One line over the
  hole and one under it, a loop of about 12 by 8 mm; on the CH32V003 each line
  also takes two vias only to cross the LED track.
- **S5. Pour 0.25 mm from the M3 hole on both layers.** A screw thread or drill
  tolerance can reach copper, and the screw head sits on mask over ground.
- **S6. Silkscreen not production-ready.** 0.12 mm stroke at 0.8 mm height, no
  designators although the back text refers to R3 to R6, no test pad labels,
  no board name or revision on the top, back text across vias.
- **S7. Copper, vias and parts too close to edges.** Ground vias 0.4 mm from
  the short edges and 0.10 mm from the connector mounting pads; pour 0.4 mm
  from every edge; on the CH32V005 tracks 0.4 to 0.5 mm from the edge. Ceramic
  parts about 1 mm from an edge that could be V-cut.
- **S8. Thermistor slot at minimum width with square inside corners.** 1.0 mm
  slot, and RT1 sits mid-finger rather than near the free end.
- **S9. Test pad pitch 2.3 mm.** Fits no pogo clip or 2.54 mm header. On the
  CH32V005, C1 is 0.15 mm from TP2 and a via 0.2 mm from TP6.
- **S10. CH32V005: open 0.3 mm via in the centre of the exposed pad under the
  paste aperture.** Solder can wick down the hole and starve the only ground
  joint.
- **S11. NTC_ADC node is 27 to 28 mm long**, running 0.2 mm from SDA_DN for
  4 mm on the CH32V003 and 0.195 mm from the VDD trunk on the CH32V005.

## Nice to have

- **N1.** CH32V003: R2 is the wrong way round, giving a 5.6 mm detour.
- **N2.** 29 and 40 vias for 12 to 13 fitted parts; the R3/R4 links cost four
  vias on the CH32V003 and chop the pours.
- **N3.** Solid pour connection on 0402 ground pads, a mild tombstoning risk.
- **N4.** Zip-tie notches exactly 2.5 mm wide with parts 0.5 mm away.
- **N5.** "UP" sits above the mounting hole, not at J1. A white write-on box
  for the address would help.
- **N6.** Router leftovers: short chamfer segments at pad exits, an acute
  junction and width steps on the CH32V005.

## Checked and fine

- Fabrication class: 0.2 mm tracks, 0.18 mm clearance, 0.6/0.3 mm vias,
  2 layers, 1.6 mm.
- Single-sided assembly, no courtyard overlaps, DRC clean.
- Connector bodies 0.73 mm inside the board edge, mouths facing out, nothing
  in front of the plug.
- JST land pattern is the stock KiCad SM04B-SRSS-TB footprint; fit of the
  clone part was not verifiable.
- Mask dams of 0.2 mm on the QFN, vias tented.
- No pour on the thermistor finger and a 1 mm air gap to the MCU side.
- Not checked: placement rotations against JLCPCB orientations.
