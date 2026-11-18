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
POUR = [(0, 0), (LEN, 0), (LEN, W), (0, W)]

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
FINGER_TRACKS = [
    ('NTC_ADC', 'F', SIG, [(33.25, 4.75), (33.6, 4.4), (33.6, 2.2), (33.21, 1.81), 'RT1.1']),
    ('GND', 'F', SIG, ['RT1.2', (34.3, 0.79), (34.3, 1.5)]),
]

# Back silkscreen shared by both boards: name, the two chain fittings, and a white box to write
# the board's address on.
BACK_SILK = [('minidc-temp v0.2', 33.5, 5.5, 'B', 1.0, 0), ('SHARED BUS: R3 R4 = 0R', 31.5, 8.0, 'B', 0.8, 0),
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
        # thermistor node
        ('NTC_ADC', 'F', SIG, ['R1.2', 'C3.1', (21.5, 5.895), 'U1.1', (23.225, 5.4), (23.875, 4.75), (33.25, 4.75)]),
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
    vias=J_VIAS + [('VDD', *V003_TAP), ('GND', 24.7, 7.165), ('GND', 18.8, 4.87), ('GND', 34.3, 1.5)],
    stitch=[(2.0, 6.5), (3.5, 2.5), (1.5, 11.9), (8.5, 2.4), (13.0, 2.2), (15.5, 4.9), (15.5, 7.4), (12.0, 12.1),
            (22.9, 3.7), (29.7, 6.4), (24.0, 12.1), (34.5, 9.5), (36.5, 10.6), (40.8, 11.4), (37.5, 3.2), (40.6, 1.6)],
    labels={'J1': (0, 4.4, 0, 'J1 UP'), 'J2': (0, -4.3, 0, 'J2 DN'), 'U1': (0, 3.5),
            'D1': (0.6, 1.45), 'R2': (0.3, 1.25), 'R3': (0, 1.9), 'R4': (0, 1.9), 'R5': (0.1, 2.9), 'R6': (0.2, 1.9),
            'RT1': (1.7, 0), 'TP1': (-3.0, 0, 0, 'SWIO'), 'TP2': (-2.8, 0, 0, 'VDD'), 'TP3': (-2.8, 0, 0, 'GND')},
    silk=[('minidc-temp v0.2', 7.0, 1.3, 'F', 0.8, 0), ('CH32V003', 9.0, 12.1, 'F', 0.8, 0),
          ('CH32V003', 21.0, 6.0, 'B', 1.0, 0)] + BACK_SILK,
    boxes=BACK_BOXES,
)
