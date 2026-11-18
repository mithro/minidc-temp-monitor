"""Hand layout of the two sensor boards: placement, tracks, vias and silkscreen.

All coordinates are millimetres from the board's top left corner, x to the
right and y down.  A track point is (x, y), a pad name such as 'U1.4' (the pad
centre), or ('U1.4', dx, dy) for a point offset from a pad centre.

Shared by both boards
  J1 (upstream) on the left and J2 (downstream) on the right, both facing out.
  M3 hole with a copper-free washer area, then a zip-tie waist.
  Thermistor on a finger at the top right, cut free by a slot, with no pour on it.
  Top layer carries the signals.  The back is a ground plane that only the VDD
  trunk crosses: one 0.8 mm track from J1 to J2, with the microcontroller tapped
  off it through the decoupling capacitor.
"""

W, LEN = 13.0, 42.0
EDGE = 0.5                      # copper to board edge
VIA = (0.6, 0.3)                # diameter, drill
SILK_STROKE = 0.15
SILK_REF = 0.8                  # designator height
CORNER_RADIUS = 0.5

NOTCH = (14.0, 17.0, 1.2)       # zip-tie waist: from x, to x, depth
SLOT = (24.5, 33.0, 2.6, 4.1)   # finger: opening x, root x, finger width, slot far edge
OUTLINE = [(0, 0), (NOTCH[0], 0), (NOTCH[0], NOTCH[2]), (NOTCH[1], NOTCH[2]), (NOTCH[1], 0),
           (SLOT[0], 0), (SLOT[0], SLOT[3]), (SLOT[1], SLOT[3]), (SLOT[1], SLOT[2]), (26, SLOT[2]), (26, 0),
           (LEN, 0), (LEN, W), (NOTCH[1], W), (NOTCH[1], W - NOTCH[2]), (NOTCH[0], W - NOTCH[2]),
           (NOTCH[0], W), (0, W)]
HOLE = (11.5, 6.5)
HOLE_KEEPOUT = (*HOLE, 3.6)     # 7 mm washer plus margin: no copper at all on either layer
FINGER = [(25.0, -0.5), (33.4, -0.5), (33.4, 2.9), (25.0, 2.9)]   # no pour around the thermistor

# Panel tabs: each board hangs from six break-off tabs.  Two on each long edge at these x positions.
# The pour stays TAB_CLEAR back from the edge there, so the mouse-bite holes never touch copper.
# A narrower tab at the top corner of each short edge, clear of the connector, ties the board to
# the panel's side and centre rails.
TABS, TAB_WIDTH, TAB_CLEAR = (7.0, 37.5), 5.0, 1.0
END_TAB, END_TAB_WIDTH = 1.4, 2.0          # centre from the top edge, width
def _box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
TAB_KEEPOUTS = ([_box(x - TAB_WIDTH / 2 - 0.8, y0, x + TAB_WIDTH / 2 + 0.8, y0 + TAB_CLEAR + 0.5)
                 for x in TABS for y0 in (-0.5, W - TAB_CLEAR)] +
                [_box(x0, END_TAB - END_TAB_WIDTH / 2 - 0.8, x0 + TAB_CLEAR + 0.5, END_TAB + END_TAB_WIDTH / 2 + 0.8)
                 for x0 in (-0.5, LEN - TAB_CLEAR)])

SIG, PWR, TRUNK = 0.2, 0.3, 0.8

# Upstream I2C pair: from J1 under the mounting hole, side by side, to x = 18.
UP_SDA = ['J1.3', (6.6, 7.0), (10.35, 10.75), (18.0, 10.75)]
UP_SCL = ['J1.4', (6.6, 8.0), (9.8, 11.2), (18.0, 11.2)]
# Connector power: two vias per pin.  J1's are right of the pads, J2's under the housing.
J_VIAS = [('VDD', 6.75, 6.0), ('VDD', 7.5, 6.0), ('GND', 6.75, 5.0), ('GND', 7.5, 5.0),
          ('VDD', 38.2, 7.0), ('VDD', 38.9, 7.0), ('GND', 39.3, 8.0), ('GND', 40.0, 8.0)]
J_TRACKS = [('VDD', 'F', 0.4, ['J1.2', (7.5, 6.0)]), ('GND', 'F', 0.4, ['J1.1', (7.5, 5.0)]),
            ('VDD', 'F', 0.4, ['J2.2', (38.9, 7.0)]), ('GND', 'F', 0.4, ['J2.1', (40.0, 8.0)])]
# VDD trunk on the back: J1, under the hole, up to the microcontroller tap, on to J2.
def trunk(tap):
    tx, ty = tap
    return ('VDD', 'B', TRUNK, [(6.75, 6.0), (7.5, 6.0), (7.5, 8.3), (10.1, 10.9), (tx - (10.9 - ty), 10.9),
                                (tx, ty), (32.7, ty), (32.7 + ty - 7.0, 7.0), (38.9, 7.0)])

COMMON_PLACE = {'J1': (3.3, 6.5, 270), 'J2': (LEN - 3.3, 6.5, 90), 'H1': (*HOLE, 0), 'RT1': (27.3, 1.3, 90)}
# Thermistor: the sense node comes up a column at x = 33.6 past the root of the finger, and the
# ground side returns along the finger's outer edge to a via in the plane.
FINGER_ADC = [(33.6, 4.4), (33.6, 2.2), (33.21, 1.81), 'RT1.1']
FINGER_TRACKS = [('GND', 'F', SIG, ['RT1.2', (34.3, 0.79), (34.3, 1.5)])]

# Back silkscreen shared by both boards: name, the two chain fittings, and a white box to write
# the board's address on.
BACK_SILK = [('minidc-temp v0.2', 33.5, 5.5, 'B', 1.0, 0), ('SHARED BUS: R3 R4 = 0R', 30.5, 8.0, 'B', 0.8, 0),
             ('RELAY: R5 R6 = 4k7', 29.0, 11.2, 'B', 0.8, 0), ('ADDR/ID', 3.75, 8.1, 'B', 0.8, 0)]
BACK_BOXES = [(0.9, 8.9, 6.6, 11.3, 'B')]

LAYOUT = {}

# ---- CH32V003J4M6, SOP-8 --------------------------------------------------------------------
# Left pads top to bottom: 1 NTC_ADC, 2 GND, 3 SCL_DN, 4 VDD.  Right: 8 SWIO, 7 SDA_DN, 6 SCL_UP,
# 5 SDA_UP.  Pin 3 and pin 8 leave inwards, under the body: SCL_DN up and over the top of the
# package to J2, SWIO down and along the bottom to the test pad and the LED.
V003_TAP = (20.48, 9.71)
LAYOUT['ch32v003'] = dict(
    place=dict(COMMON_PLACE,
               U1=(25.7, 7.8, 0),
               C1=(21.5, 9.2, 90), C2=(20.99, 7.72, 0), C3=(21.5, 6.25, 270), R1=(21.5, 4.32, 270),
               D1=(20.2, 1.5, 0), R2=(22.69, 1.5, 180),
               R3=(30.2, 8.435, 90), R4=(31.7, 7.165, 90), R5=(33.2, 7.1, 90), R6=(34.66, 6.275, 90),
               TP1=(18.8, 8.68, 0), TP2=(18.8, 6.14, 0), TP3=(18.8, 3.6, 0)),
    tracks=J_TRACKS + FINGER_TRACKS + [
        trunk(V003_TAP),
        # supply and decoupling: tap via, C1, pin 4; rail up the left to C2, R1, the VDD pad and the LED
        ('VDD', 'F', PWR, [V003_TAP, 'C1.1', 'U1.4']),
        ('VDD', 'F', PWR, [V003_TAP, (20.48, 7.72), (20.48, 6.14), (20.48, 3.81), (20.48, 2.6), (23.2, 2.6), 'R2.1']),
        ('VDD', 'F', PWR, [(20.48, 3.81), 'R1.1']),
        ('VDD', 'F', PWR, [(20.48, 6.14), 'TP2.1']),
        ('GND', 'F', PWR, ['C1.2', 'C2.2', 'C3.2', (21.5, 7.165), 'U1.2', (24.7, 7.165)]),
        ('GND', 'F', PWR, ['TP3.1', (18.8, 4.87)]),
        ('GND', 'F', PWR, ['C2.2', (22.15, 7.66)]),
        # thermistor node
        ('NTC_ADC', 'F', SIG, ['R1.2', 'C3.1', (21.5, 5.895), 'U1.1', (23.225, 5.4), (23.875, 4.75), (33.25, 4.75)] + FINGER_ADC),
        # upstream I2C, along the bottom and up the right side of the package
        ('SDA_UP', 'F', SIG, UP_SDA + [(29.65, 10.75), (30.2, 10.2), (30.2, 9.705), 'R3.1']),
        ('SDA_UP', 'F', SIG, [(30.2, 9.705), 'U1.5']),
        ('SCL_UP', 'F', SIG, UP_SCL + [(31.1, 11.2), (31.7, 10.6), (31.7, 8.435), 'R4.1']),
        ('SCL_UP', 'F', SIG, [(31.7, 8.435), 'U1.6']),
        # downstream I2C
        ('SCL_DN', 'F', SIG, ['U1.3', (25.4, 8.435), (25.4, 5.65), (25.85, 5.2), (31.7, 5.2), (33.6, 5.2),
                              (33.85, 5.45), 'R6.2', (35.3, 5.45), (35.7, 5.05), ('J2.4', 0, 0.05), 'J2.4']),
        ('SCL_DN', 'F', SIG, [(31.7, 5.2), 'R4.2']),
        ('SDA_DN', 'F', SIG, ['U1.7', (30.2, 7.165), (32.2, 7.165), (33.09, 6.275), 'R5.2', (35.2, 6.275),
                              (35.475, 6.0), 'J2.3']),
        ('SDA_DN', 'F', SIG, [(30.2, 7.165), 'R3.2']),
        ('VDD', 'F', PWR, ['J2.2', (35.5, 7.0), (35.4, 7.1), 'R6.1', (34.66, 7.6), (34.335, 7.925), 'R5.1']),
        # SWIO: under the package, test pad, then up the left edge to the LED
        ('SWIO', 'F', SIG, ['U1.8', (26.4, 5.895), (26.4, 9.9), (26.0, 10.3), (19.7, 10.3), (18.8, 9.4), 'TP1.1',
                            (17.95, 8.68), (17.65, 8.38), (17.65, 1.85), (18.0, 1.5), 'D1.1']),
        ('Net-(D1-A)', 'F', SIG, ['D1.2', 'R2.2']),
    ],
    vias=J_VIAS + [('VDD', *V003_TAP), ('GND', 24.7, 7.165), ('GND', 22.15, 7.66), ('GND', 18.8, 4.87), ('GND', 34.3, 1.5)],
    stitch=[(2.0, 6.5), (3.5, 2.5), (1.5, 11.9), (8.5, 2.4), (13.0, 2.2), (15.5, 4.9), (15.5, 7.4), (12.0, 12.1),
            (22.9, 3.7), (29.7, 6.4), (30.6, 6.1), (24.0, 12.1), (34.5, 9.5), (36.5, 10.6), (40.8, 11.4), (37.5, 3.2), (40.6, 1.6)],
    labels={'J1': (0, 4.4, 0, 'J1 UP'), 'J2': (0, -4.3, 0, 'J2 DN'), 'U1': (0, 3.5),
            'D1': (0.6, 1.45), 'R2': (0.3, 1.25), 'R3': (0, 1.9), 'R4': (0, 1.9), 'R5': (0.1, 2.9), 'R6': (0.2, 1.9),
            'RT1': (1.7, 0), 'TP1': (-3.0, 0, 0, 'SWIO'), 'TP2': (-2.8, 0, 0, 'VDD'), 'TP3': (-2.8, 0, 0, 'GND')},
    silk=[('minidc-temp v0.2', 7.0, 1.3, 'F', 0.8, 0), ('CH32V003', 8.6, 11.9, 'F', 0.8, 0),
          ('CH32V003', 21.0, 6.0, 'B', 1.0, 0)] + BACK_SILK,
    boxes=BACK_BOXES,
)

# ---- CH32V005D6U6, QFN-12 -------------------------------------------------------------------
# Top pads left to right: 12 NRST, 11 unused, 10 SCL_UP (also SWIO).  Right, top to bottom: 9 spare,
# 8 NTC_DRV, 7 NTC_ADC.  Bottom, left to right: 4 VDD, 5 SDA_DN, 6 SCL_DN.  Left, top to bottom:
# 1 spare, 2 LED, 3 SDA_UP.
# The two upstream pins are on opposite corners, so SCL_UP runs up the left edge and over the top of
# the package, and everything it encloses (LED, programming pads, spare pads) is fed from inside.
# SDA_UP leaves J1 under the connector housing to swap sides with SCL_UP, so the pair still runs
# together under the mounting hole.
V5_SCL = ['J1.4', (6.6, 8.0), (9.35, 10.75), (16.9, 10.75), (17.65, 10.0), (17.65, 8.68), (17.65, 1.9), (17.95, 1.6),
          (23.6, 1.6), (23.9, 1.9), (23.9, 4.4), (24.3, 4.8), (26.4, 4.8)]
V5_SDA = ['J1.3', (4.2, 7.0), (4.0, 7.2), (4.0, 8.5), (4.25, 8.75), (6.3, 8.75), (8.75, 11.2), (18.0, 11.2),
          (18.65, 11.85), (22.75, 11.85)]
U5 = (26.0, 7.6)
LAYOUT['ch32v005'] = dict(
    place=dict(COMMON_PLACE,
               U1=(*U5, 0),
               C1=(24.6, 9.85, 180), C2=(20.81, 4.87, 0), C3=(30.1, 8.11, 90), R1=(28.9, 8.11, 270),
               D1=(21.8, 7.75, 180), R2=(21.01, 9.52, 90),
               R3=(27.9, 11.85, 0), R4=(33.6, 5.1, 0), R5=(32.9, 11.05, 90), R6=(31.4, 10.225, 90),
               TP1=(18.8, 8.68, 0), TP2=(18.8, 6.14, 0), TP3=(18.8, 3.6, 0),
               TP4=(22.9, 3.6, 0), TP5=(22.9, 5.9, 0), TP6=(28.8, 6.0, 0)),
    tracks=J_TRACKS + FINGER_TRACKS + [
        ('VDD', 'B', TRUNK, [(6.75, 6.0), (7.5, 6.0), (7.5, 8.3), (10.1, 10.9), (17.3, 10.9), (17.9, 10.3),
                             (32.9, 10.3), (36.2, 7.0), (38.9, 7.0)]),
        # supply: tap via, C1, pin 4
        ('VDD', 'F', PWR, [(25.11, 10.6), 'C1.1']),
        ('VDD', 'F', PWR, ['C1.1', (25.6, 9.33)]),
        ('VDD', 'F', SIG, [(25.6, 9.33), 'U1.4']),
        ('GND', 'F', PWR, ['C1.2', (24.12, 11.2)]),
        # second tap inside the SCL_UP loop: rail to the LED, C2 and the VDD pad
        ('VDD', 'F', PWR, [(20.2, 10.5), (20.2, 10.03), (20.2, 6.14), (20.2, 5.0), 'C2.1']),
        ('VDD', 'F', PWR, [(20.2, 10.03), 'R2.1']),
        ('VDD', 'F', PWR, [(20.2, 6.14), 'TP2.1']),
        ('GND', 'F', PWR, ['C2.2', (22.05, 4.87)]),
        ('GND', 'F', PWR, ['TP3.1', (18.8, 4.87)]),
        ('LED_K', 'F', SIG, ['U1.2', (23.7, 7.6), (23.55, 7.75), 'D1.1']),
        ('Net-(D1-A)', 'F', SIG, ['D1.2', 'R2.2']),
        ('NRST', 'F', SIG, ['U1.12', (25.6, 5.9), (25.3, 5.6), (24.3, 5.6), (23.2, 4.5), (22.9, 4.2), 'TP4.1']),
        ('AUX_A1', 'F', SIG, ['U1.1', (24.2, 7.2), 'TP5.1']),
        ('AUX_PC7', 'F', SIG, ['U1.9', (27.8, 7.2), (28.8, 6.2), 'TP6.1']),
        # upstream I2C
        ('SCL_UP', 'F', SIG, V5_SCL + ['U1.10']),
        ('SCL_UP', 'F', SIG, [(17.65, 8.68), 'TP1.1']),
        ('SCL_UP', 'F', SIG, [(26.4, 4.8), (32.475, 4.8), (32.775, 5.1), 'R4.1']),
        ('SDA_UP', 'F', SIG, V5_SDA + [(23.4, 11.2), (23.4, 8.8), (24.2, 8.0), 'U1.3']),
        ('SDA_UP', 'F', SIG, [(22.75, 11.85), 'R3.1']),
        # thermistor node: R1 across pins 8 and 7, C3 next to it, then out to the finger
        ('NTC_DRV', 'F', SIG, ['U1.8', 'R1.1']),
        ('NTC_ADC', 'F', SIG, ['U1.7', (27.9, 8.0), (28.4, 8.5), (28.78, 8.62), 'R1.2', 'C3.1', (33.3, 8.62), (33.6, 8.32)] + FINGER_ADC),
        ('GND', 'F', PWR, ['C3.2', (30.1, 6.75)]),
        # downstream I2C
        ('SCL_DN', 'F', SIG, ['U1.6', (26.4, 9.1), (26.7, 9.4), 'R6.2', (34.0, 9.4), (34.4, 9.0), (34.4, 5.1), 'R4.2',
                              (35.4, 5.1), 'J2.4']),
        ('SDA_DN', 'F', SIG, ['U1.5', (26.0, 9.5), (26.4, 9.9), (28.725, 9.9), (30.2, 9.9), (30.525, 10.225), 'R5.2',
                              (34.4, 10.225), (34.9, 9.725), (34.9, 6.4), (35.3, 6.0), 'J2.3']),
        ('SDA_DN', 'F', SIG, [(28.725, 9.9), 'R3.2']),
        ('VDD', 'F', PWR, ['R6.1', (31.4, 11.55), (31.725, 11.875), 'R5.1', (35.1, 11.875), (35.5, 11.475), (35.5, 7.0),
                           'J2.2']),
    ],
    vias=J_VIAS + [('VDD', 25.11, 10.6), ('VDD', 20.2, 10.5),
                   ('GND', U5[0] + 0.3, U5[1] - 0.3, (0.5, 0.3)),
                   ('GND', 24.12, 11.2), ('GND', 22.05, 4.87), ('GND', 18.8, 4.87), ('GND', 30.1, 6.75), ('GND', 34.3, 1.5)],
    # one via in a corner of the exposed pad; paste covers the rest, 60 % of the pad
    paste_windows={'U1': ([], [(-0.25, 0, 0.5, 1.0), (0.25, 0.275, 0.5, 0.45)])},
    stitch=[(2.0, 6.5), (3.5, 2.5), (1.5, 11.9), (8.5, 2.4), (13.0, 2.2), (15.5, 4.9), (15.5, 7.4), (12.0, 12.1),
            (30.3, 12.2), (26.0, 11.2), (36.3, 10.2), (40.8, 11.4), (37.5, 3.2), (40.6, 1.6),
            (32.4, 6.6)],
    labels={'J1': (0, 4.4, 0, 'J1 UP'), 'J2': (0, -4.3, 0, 'J2 DN'),
            'U1': (0, -2.3), 'C1': (-0.45, 1.45), 'C2': (0.1, -0.97), 'D1': (0.4, 1.4), 'R2': (1.3, 0.9),
            'R1': (-0.5, 1.55), 'C3': (-0.15, 1.55), 'R3': (-0.6, -1.15), 'R4': (0, 1.2), 'R5': (1.35, 0.45), 'R6': (-1.7, 0.4),
            'TP4': (0, -1.3, 0, 'RST'), 'TP5': (-1.95, 0, 0, 'PA1'), 'TP6': (2.0, 0, 0, 'PC7'),
            'RT1': (1.7, 0), 'TP1': (-3.0, 0, 0, 'SWIO'), 'TP2': (-2.8, 0, 0, 'VDD'), 'TP3': (-2.8, 0, 0, 'GND')},
    silk=[('minidc-temp v0.2', 7.0, 1.3, 'F', 0.8, 0), ('CH32V005', 8.6, 11.9, 'F', 0.8, 0),
          ('CH32V005', 21.0, 6.0, 'B', 1.0, 0)] + BACK_SILK,
    boxes=BACK_BOXES,
)
