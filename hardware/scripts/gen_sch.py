#!/usr/bin/env python3
"""Generate the KiCad schematics for the MCU temperature sensor boards.

Usage: gen_sch.py <variant> <out.kicad_sch>     variant = ch32v003 | ch32v005

The sheet is drawn in functional blocks with wires, power symbols and short
labelled stubs.  PINS holds the intended net of every pin, and the script
checks the drawn sheet against it with `kicad-cli sch export netlist`.
Symbols are copied from the stock KiCad library, except the MCUs: those are
adjusted copies, written to ../lib/minidc.kicad_sym with a sym-lib-table
beside each project (both generated; do not edit by hand).
"""
import math, os, subprocess, sys, tempfile, uuid
from sexp import loads, dumps, find, first, Sym

SYMDIR = os.environ.get('KICAD_SYMBOL_DIR', '/usr/share/kicad/symbols')
NS = uuid.UUID('6f1c2f0e-3d0a-4c58-9a70-6d6a1d0c5b11')

FP_R = 'Resistor_SMD:R_0402_1005Metric'
FP_C = 'Capacitor_SMD:C_0402_1005Metric'
FP_J = 'Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal'
FP_R0603 = 'Resistor_SMD:R_0603_1608Metric'   # wide enough to bridge over one track
FP_TP = 'TestPoint:TestPoint_Pad_D1.5mm'        # programming pads, on a 2.54 mm pitch
FP_TP_SMALL = 'TestPoint:TestPoint_Pad_D1.0mm'  # spare pins


# ref: (library, symbol, value, footprint, LCSC part, do-not-populate)
COMMON_PARTS = {
    'J1': ('Connector_Generic_MountingPin', 'Conn_01x04_MountingPin', 'Qwiic UP', FP_J, 'C7430446', False),
    'J2': ('Connector_Generic_MountingPin', 'Conn_01x04_MountingPin', 'Qwiic DOWN', FP_J, 'C7430446', False),
    'R3': ('Device', 'R', '0R', FP_R0603, 'C21189', True),
    'R4': ('Device', 'R', '0R', FP_R0603, 'C21189', True),
    'R5': ('Device', 'R', '4k7', FP_R0603, 'C23162', False),
    'R6': ('Device', 'R', '4k7', FP_R0603, 'C23162', False),
    'R1': ('Device', 'R', '100k 1%', FP_R, 'C25741', False),
    'RT1': ('Device', 'Thermistor_NTC', '100k B3950 1%', FP_R, 'C6807762', False),
    'C3': ('Device', 'C', '100n', FP_C, 'C1525', False),
    'R2': ('Device', 'R', '1k', FP_R, 'C11702', False),
    'D1': ('Device', 'LED', 'RED', 'LED_SMD:LED_0603_1608Metric', 'C2286', False),
    'C1': ('Device', 'C', '100n', FP_C, 'C1525', False),
    'C2': ('Device', 'C', '1u', FP_C, 'C52923', False),
    'TP2': ('Connector', 'TestPoint', 'VDD', FP_TP, '', False),
    'TP3': ('Connector', 'TestPoint', 'GND', FP_TP, '', False),
    'H1': ('Mechanical', 'MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', '', False),
}
COMMON_PINS = {
    'J1': {'1': 'GND', '2': 'VDD', '3': 'SDA_UP', '4': 'SCL_UP', 'MP': 'GND'},
    'J2': {'1': 'GND', '2': 'VDD', '3': 'SDA_DN', '4': 'SCL_DN', 'MP': 'GND'},
    'R3': {'1': 'SDA_UP', '2': 'SDA_DN'}, 'R4': {'1': 'SCL_UP', '2': 'SCL_DN'},
    'R5': {'1': 'VDD', '2': 'SDA_DN'}, 'R6': {'1': 'VDD', '2': 'SCL_DN'},
    'RT1': {'1': 'NTC_ADC', '2': 'GND'}, 'C3': {'1': 'NTC_ADC', '2': 'GND'},
    'R2': {'1': 'VDD', '2': 'Net-(D1-A)'}, 'D1': {'2': 'Net-(D1-A)'},
    'C1': {'1': 'VDD', '2': 'GND'}, 'C2': {'1': 'VDD', '2': 'GND'},
    'TP2': {'1': 'VDD'}, 'TP3': {'1': 'GND'},
}

VARIANTS = {
    'ch32v003': dict(
        title='Temp sensor strip, CH32V003J4M6',
        parts={'U1': ('MCU_WCH_RiscV', 'CH32V003JxMx', 'CH32V003J4M6', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'C5346354', False),
               'TP1': ('Connector', 'TestPoint', 'SWIO', FP_TP, '', False)},
        pins={'U1': {'5': 'SDA_UP', '6': 'SCL_UP', '7': 'SDA_DN', '4': 'VDD', '2': 'GND',
                     '8': 'SWIO', '1': 'NTC_ADC', '3': 'SCL_DN'},
              'R1': {'1': 'VDD', '2': 'NTC_ADC'}, 'D1': {'1': 'SWIO'}, 'TP1': {'1': 'SWIO'}},
        notes=[
            'U1 pin use: PC1/PC2 = hardware I2C to the upstream connector J1.',
            'PC4 (SDA) and PA2 (SCL) = bit-banged I2C controller to J2, used only in relay mode.',
            'PA1 = ADC channel 1 on the thermistor divider; PD6 shares the pin and stays an input.',
            'PD1 = SWIO programming pin, shared with the identify LED (drive PD4 or PD5 low to light it).',
        ],
    ),
    'ch32v005': dict(
        title='Temp sensor strip, CH32V005D6U6',
        parts={'U1': ('MCU_WCH_RiscV', 'CH32V005D6U6', 'CH32V005D6U6', 'Package_DFN_QFN:UQFN-12-1EP_2x2mm_P0.4mm_EP1.1x1.1mm', 'C49006243', False),
               'TP1': ('Connector', 'TestPoint', 'SWIO', FP_TP, '', False),
               'TP4': ('Connector', 'TestPoint', 'NRST', FP_TP_SMALL, '', False),
               'TP5': ('Connector', 'TestPoint', 'AUX_A1', FP_TP_SMALL, '', False),
               'TP6': ('Connector', 'TestPoint', 'AUX_PC7', FP_TP_SMALL, '', False)},
        pins={'U1': {'4': 'VDD', '13': 'GND', '3': 'SDA_UP', '10': 'SCL_UP', '5': 'SDA_DN', '6': 'SCL_DN',
                     '7': 'NTC_ADC', '8': 'NTC_DRV', '2': 'LED_K', '1': 'AUX_A1', '9': 'AUX_PC7',
                     '11': None, '12': 'NRST'},
              'R1': {'1': 'NTC_DRV', '2': 'NTC_ADC'}, 'D1': {'1': 'LED_K'},
              'TP1': {'1': 'SCL_UP'}, 'TP4': {'1': 'NRST'}, 'TP5': {'1': 'AUX_A1'}, 'TP6': {'1': 'AUX_PC7'}},
        notes=[
            'U1 pin use: PD0/PD1 = hardware I2C (remap 1) to the upstream connector J1.',
            'PD1 is also SWIO, so the board is programmed through J1 pin 4 (SCL).',
            'PC0 and PC3 = bit-banged I2C controller to J2, used only in relay mode.',
            'PC4 = ADC channel 2 on the thermistor divider, powered from PC6 while sampling.',
            'PA2 = identify LED (active low).  PA1 (ADC channel 1) and PC7 = spare pins on pads.',
        ],
    ),
}

GENERAL_NOTES = [
    'Chain wiring is a build option:',
    '  Relay (default): R3 and R4 unfitted.  R5 and R6 (4k7) are the pull-ups of the hop to the next board.',
    '  R5 and R6 are optional: without them firmware uses the internal pull-ups (35 to 55 k) at low speed.',
    '  Shared bus: fit R3 and R4 (0R) and remove R5 and R6.  The only pull-ups are then the ones on the hub.',
    'The hop from the hub to the first board uses the pull-ups on the hub.',
]
POWER = ('VDD', 'GND')

def uid(*key):
    return str(uuid.uuid5(NS, '/'.join(str(k) for k in key)))

_libcache = {}
def lib_symbol(lib, name):
    if lib not in _libcache:
        _libcache[lib] = loads(open(f'{SYMDIR}/{lib}.kicad_sym').read())
    for s in find(_libcache[lib], 'symbol'):
        if s[1] == name:
            if first(s, 'extends'):
                raise SystemExit(f'{lib}:{name} is a derived symbol; not handled')
            return s
    raise SystemExit(f'{lib}:{name} not found')

LOCAL_LIB = 'minidc'       # project symbol library for the adjusted MCU symbols

def adjusted(sym):
    """Copy of a stock MCU symbol with the text collisions fixed: pins lengthened
    to 5.08 mm so two-digit pin numbers clear the body, and on the SOP-8 part the
    power pins moved off centre so their names clear the long PD1/PD4/PD5 name."""
    sym = loads(dumps(sym))
    for unit in find(sym, 'symbol'):
        for p in find(unit, 'pin'):
            at, length = first(p, 'at'), first(p, 'length')
            ang = int(float(at[3])) if len(at) > 3 else 0
            grow = 5.08 - float(length[1])
            at[1] = round(float(at[1]) - grow * round(math.cos(math.radians(ang))), 4)
            at[2] = round(float(at[2]) - grow * round(math.sin(math.radians(ang))), 4)
            length[1] = 5.08
            if sym[1] == 'CH32V003JxMx' and ang in (90, 270):
                at[1] = -5.08
    return sym

def pin_table(sym):
    """number -> (x, y, angle)"""
    out = {}
    for unit in find(sym, 'symbol'):
        for p in find(unit, 'pin'):
            at = first(p, 'at')
            out[first(p, 'number')[1]] = (float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0)
    return out

def effects(justify=None, hide=False):
    e = [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]]]
    if justify:
        e.append([Sym('justify')] + [Sym(j) for j in justify])
    if hide:
        e.append([Sym('hide'), Sym('yes')])
    return e

def prop(name, value, x, y, hide=False, justify=None, angle=0):
    return [Sym('property'), name, value, [Sym('at'), x, y, angle], effects(justify, hide)]

def r4(v):
    return round(v, 4)


class Sheet:
    """Collects symbols, wires, labels and text, then writes one schematic page."""

    def __init__(self, variant, project):
        self.variant, self.project = variant, project
        v = VARIANTS[variant]
        self.parts = dict(COMMON_PARTS, **v['parts'])
        self.expect = {ref: dict(COMMON_PINS.get(ref, {}), **v['pins'].get(ref, {})) for ref in self.parts}
        self.root = uid(variant, 'root')
        self.libsyms, self.items, self.wires, self.pin_points, self.n = {}, [], [], [], 0
        self.placed = set()

    def _uid(self, kind):
        self.n += 1
        return uid(self.variant, kind, self.n)

    def _lib(self, lib, name):
        lid = f'{lib}:{name}'
        src = lib_symbol(lib, name)
        if lib == 'MCU_WCH_RiscV':
            lid, src = f'{LOCAL_LIB}:{name}', adjusted(src)
        if lid not in self.libsyms:
            copy = loads(dumps(src))
            copy[1] = lid
            self.libsyms[lid] = copy
        return lid, pin_table(src)

    def _symbol(self, lid, table, ref, value, x, y, rot, mirror, fp, lcsc, dnp, in_bom, texts, key):
        s = [Sym('symbol'), [Sym('lib_id'), lid], [Sym('at'), x, y, rot]]
        if mirror:
            s.append([Sym('mirror'), Sym(mirror)])
        (rx, ry, rj), (vx, vy, vj) = texts
        hidden_ref = ref.startswith('#')
        ta = 90 if rot in (90, 270) else 0     # KiCad turns field text with the symbol; this keeps it level
        s += [[Sym('unit'), 1], [Sym('exclude_from_sim'), Sym('no')], [Sym('in_bom'), Sym('yes' if in_bom else 'no')],
              [Sym('on_board'), Sym('yes')], [Sym('dnp'), Sym('yes' if dnp else 'no')], [Sym('uuid'), uid(self.variant, key)],
              prop('Reference', ref, r4(x + rx), r4(y + ry), hide=hidden_ref, justify=rj, angle=ta),
              prop('Value', value, r4(x + vx), r4(y + vy), hide=vj == 'hide', justify=None if vj == 'hide' else vj, angle=ta),
              prop('Footprint', fp, x, y, hide=True), prop('Datasheet', '', x, y, hide=True),
              prop('Description', '', x, y, hide=True)]
        if lcsc:
            s.append(prop('LCSC', lcsc, x, y, hide=True))
        for num in table:
            s.append([Sym('pin'), num, [Sym('uuid'), uid(self.variant, key, 'pin', num)]])
        s.append([Sym('instances'), [Sym('project'), self.project,
                  [Sym('path'), '/' + self.root, [Sym('reference'), ref], [Sym('unit'), 1]]]])
        self.items.append(s)

    def place(self, ref, x, y, rot=0, mirror=None, ref_at=(2.54, -1.27, ['left']), val_at=(2.54, 1.27, ['left'])):
        """Place a part.  Returns {pin: (x, y, (dx, dy))} with the direction pointing away from the body."""
        assert not (mirror and rot), 'mirror is only handled for unrotated symbols'
        lib, name, value, fp, lcsc, dnp = self.parts[ref]
        lid, table = self._lib(lib, name)
        self._symbol(lid, table, ref, value, x, y, rot, mirror, fp, lcsc, dnp, bool(fp) and ref[0] not in 'HT',
                     (ref_at, val_at), ref)
        self.placed.add(ref)
        c, s = round(math.cos(math.radians(rot))), round(math.sin(math.radians(rot)))
        out = {}
        for num, (px, py, ang) in table.items():
            ox, oy = -round(math.cos(math.radians(ang))), -round(math.sin(math.radians(ang)))
            if mirror == 'y':
                px, ox = -px, -ox
            if mirror == 'x':
                py, oy = -py, -oy
            p = (r4(x + px * c - py * s), r4(y - (px * s + py * c)))
            out[num] = (p[0], p[1], (ox * c - oy * s, -(ox * s + oy * c)))
            self.pin_points.append(p)
            if self.expect[ref].get(num, '') is None:
                self.items.append([Sym('no_connect'), [Sym('at'), p[0], p[1]], [Sym('uuid'), self._uid('nc')]])
        return out

    def wire(self, *pts):
        for a, b in zip(pts, pts[1:]):
            a, b = (r4(a[0]), r4(a[1])), (r4(b[0]), r4(b[1]))
            if a != b:
                assert a[0] == b[0] or a[1] == b[1], f'diagonal wire {a} {b}'
                self.wires.append((a, b))

    def label(self, net, x, y, toward):
        """Net label at the end of a wire; `toward` is the direction the text runs."""
        rot, just = {(1, 0): (0, ['left', 'bottom']), (-1, 0): (180, ['right', 'bottom'])}[toward]
        self.items.append([Sym('label'), net, [Sym('at'), r4(x), r4(y), rot], effects(just), [Sym('uuid'), self._uid('label')]])

    def power(self, net, x, y):
        lid, table = self._lib('power', net)
        self.n += 1
        ref = f'#PWR{self.n:03d}'
        texts = ((0, 0, None), (0, -3.81 if net == 'VDD' else 3.81, None))
        self._symbol(lid, table, ref, net, r4(x), r4(y), 0, None, '', '', False, False, texts, ref)
        self.pin_points.append((r4(x), r4(y)))

    def flag(self, x, y):
        lid, table = self._lib('power', 'PWR_FLAG')
        self.n += 1
        ref = f'#FLG{self.n:03d}'
        self._symbol(lid, table, ref, 'PWR_FLAG', x, y, 0, None, '', '', False, False, ((0, 0, None), (0, -5.08, None)), ref)
        self.pin_points.append((r4(x), r4(y)))

    def stub(self, pin, length, net):
        """Wire straight out of a pin, ending in a power symbol or a net label."""
        x, y, (dx, dy) = pin
        ex, ey = x + dx * length, y + dy * length
        self.wire((x, y), (ex, ey))
        if net in POWER:
            self.power(net, ex, ey)
        else:
            self.label(net, ex, ey, (dx, dy))

    def text(self, s, x, y, size=1.27, bold=False):
        font = [Sym('font'), [Sym('size'), size, size]] + ([[Sym('bold'), Sym('yes')]] if bold else [])
        self.items.append([Sym('text'), s, [Sym('exclude_from_sim'), Sym('no')], [Sym('at'), x, y, 0],
                           [Sym('effects'), font, [Sym('justify'), Sym('left'), Sym('bottom')]], [Sym('uuid'), self._uid('text')]])

    def frame(self, title, x1, y1, x2, y2):
        self.items.append([Sym('rectangle'), [Sym('start'), x1, y1], [Sym('end'), x2, y2],
                           [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('dash')]],
                           [Sym('fill'), [Sym('type'), Sym('none')]], [Sym('uuid'), self._uid('frame')]])
        self.text(title, x1 + 1.27, y1 + 3.81, size=1.524, bold=True)

    def _finish_wires(self):
        """Split wires where another wire or a pin ends on them, and add junction dots."""
        ends = {p for w in self.wires for p in w} | set(self.pin_points)
        segs = []
        for a, b in self.wires:
            inner = sorted(p for p in ends if p != a and p != b and
                           min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))
            chain = sorted([a, b] + inner)
            segs += list(zip(chain, chain[1:]))
        count = {}
        for a, b in segs:
            for p in (a, b):
                count[p] = count.get(p, 0) + 1
            self.items.append([Sym('wire'), [Sym('pts'), [Sym('xy'), a[0], a[1]], [Sym('xy'), b[0], b[1]]],
                               [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('default')]], [Sym('uuid'), self._uid('wire')]])
        for p in self.pin_points:
            count[p] = count.get(p, 0) + 1
        for p, c in sorted(count.items()):
            if c >= 3:
                self.items.append([Sym('junction'), [Sym('at'), p[0], p[1]], [Sym('diameter'), 0],
                                   [Sym('color'), 0, 0, 0, 0], [Sym('uuid'), self._uid('junction')]])

    def dumps(self):
        missing = set(self.parts) - self.placed
        if missing:
            raise SystemExit(f'not placed: {sorted(missing)}')
        self._finish_wires()
        v = VARIANTS[self.variant]
        sch = [Sym('kicad_sch'), [Sym('version'), 20250114], [Sym('generator'), 'eeschema'],
               [Sym('generator_version'), '9.0'], [Sym('uuid'), self.root], [Sym('paper'), 'A4'],
               [Sym('title_block'), [Sym('title'), v['title']], [Sym('date'), '2026-11-18'], [Sym('rev'), '0.2'],
                [Sym('company'), 'minidc-temp-monitor']],
               [Sym('lib_symbols')] + list(self.libsyms.values())] + self.items + [
               [Sym('sheet_instances'), [Sym('path'), '/', [Sym('page'), '1']]],
               [Sym('embedded_fonts'), Sym('no')]]
        return dumps(sch) + '\n'


def draw(variant, project):
    v = VARIANTS[variant]
    s = Sheet(variant, project)
    net = lambda ref, pin: s.expect[ref][pin]
    s.text(v['title'], 20.32, 22.86, size=2.54, bold=True)

    # --- I2C pass-through: J1, 0R links (shared bus), downstream pull-ups, J2 -------------------
    s.frame('I2C pass-through and chain option links', 20.32, 27.94, 200.66, 73.66)
    j1 = s.place('J1', 38.1, 53.34, mirror='y', ref_at=(-3.81, -1.27, ['left']), val_at=(-3.81, 1.27, ['left']))
    j2 = s.place('J2', 182.88, 53.34, ref_at=(3.81, -1.27, ['left']), val_at=(3.81, 1.27, ['left']))
    r3 = s.place('R3', 96.52, 55.88, rot=90, ref_at=(0, -5.08, None), val_at=(0, -2.54, None))
    r4_ = s.place('R4', 111.76, 58.42, rot=90, ref_at=(0, 2.54, None), val_at=(0, 5.08, None))
    r5 = s.place('R5', 132.08, 43.18)
    r6 = s.place('R6', 144.78, 43.18)
    for j, side, xg, xv in ((j1, 1, 50.8, 45.72), (j2, -1, 170.18, 175.26)):
        s.wire(j['1'][:2], (xg, j['1'][1]), (xg, 66.04)); s.power('GND', xg, 66.04)
        s.wire(j['2'][:2], (xv, j['2'][1]), (xv, 45.72)); s.power('VDD', xv, 45.72)
        s.stub(j['MP'], 2.54, 'GND')
    s.wire(j1['3'][:2], r3['1'][:2]); s.wire(r3['2'][:2], j2['3'][:2])
    s.wire(j1['4'][:2], r4_['1'][:2]); s.wire(r4_['2'][:2], j2['4'][:2])
    s.label('SDA_UP', 60.96, 55.88, (1, 0)); s.label('SCL_UP', 60.96, 58.42, (1, 0))
    s.label('SDA_DN', 152.4, 55.88, (1, 0)); s.label('SCL_DN', 152.4, 58.42, (1, 0))
    s.stub(r5['1'], 2.54, 'VDD'); s.stub(r6['1'], 2.54, 'VDD')
    s.wire(r5['2'][:2], (132.08, 55.88)); s.wire(r6['2'][:2], (144.78, 58.42))
    s.text('Shared bus: fit R3 and R4 instead', 86.36, 69.85)
    s.text('Relay (default): R5 and R6 fitted (optional)', 152.4, 35.56)

    # --- Microcontroller ------------------------------------------------------------------------
    s.frame('Microcontroller', 20.32, 83.82, 109.22, 147.32)
    u1 = s.place('U1', 66.04, 116.84, ref_at=(-25.4, -16.51, ['left']), val_at=(-25.4, -13.97, ['left']))
    for num, pin in u1.items():
        name = net('U1', num)
        if name:
            s.stub(pin, 2.54 if name in POWER else 5.08, name)

    # --- Decoupling -----------------------------------------------------------------------------
    s.frame('Supply decoupling', 114.3, 83.82, 160.02, 147.32)
    c1 = s.place('C1', 129.54, 114.3)
    c2 = s.place('C2', 142.24, 114.3)
    top, bot = 106.68, 121.92
    s.wire((121.92, top), (142.24, top)); s.wire((121.92, bot), (142.24, bot))
    for c in (c1, c2):
        s.wire(c['1'][:2], (c['1'][0], top)); s.wire(c['2'][:2], (c['2'][0], bot))
    s.power('VDD', 135.89, top); s.power('GND', 135.89, bot)
    s.flag(121.92, top); s.flag(121.92, bot)

    # --- Identify LED ---------------------------------------------------------------------------
    s.frame('Identify LED', 165.1, 83.82, 190.5, 147.32)
    r2 = s.place('R2', 172.72, 104.14)
    d1 = s.place('D1', 172.72, 115.57, rot=90, ref_at=(3.81, -1.27, ['right']), val_at=(3.81, 1.27, ['right']))
    s.stub(r2['1'], 2.54, 'VDD')
    s.wire(r2['2'][:2], d1['2'][:2])
    s.wire(d1['1'][:2], (172.72, 124.46), (176.53, 124.46)); s.label(net('D1', '1'), 176.53, 124.46, (1, 0))

    # --- Thermistor divider ---------------------------------------------------------------------
    s.frame('Thermistor divider', 195.58, 83.82, 248.92, 147.32)
    r1 = s.place('R1', 217.17, 104.14)
    rt = s.place('RT1', 217.17, 119.38, ref_at=(3.81, -1.27, ['left']), val_at=(3.81, 1.27, ['left']))
    c3 = s.place('C3', 240.03, 119.38)
    if net('R1', '1') == 'VDD':
        s.stub(r1['1'], 2.54, 'VDD')
    else:
        s.wire(r1['1'][:2], (217.17, 97.79), (209.55, 97.79)); s.label(net('R1', '1'), 209.55, 97.79, (-1, 0))
    mid, low = 111.76, 127.0
    s.wire(r1['2'][:2], (217.17, mid), rt['1'][:2])
    s.wire(c3['1'][:2], (240.03, mid), (209.55, mid)); s.label('NTC_ADC', 209.55, mid, (-1, 0))
    s.wire(rt['2'][:2], (217.17, low)); s.wire(c3['2'][:2], (240.03, low), (217.17, low)); s.power('GND', 217.17, low)

    # --- Test pads and mounting -----------------------------------------------------------------
    tps = sorted((r for r in s.parts if r.startswith('TP')), key=lambda r: int(r[2:]))
    s.frame('Test pads', 252.73, 83.82, 280.67, 147.32)
    y = 93.98
    for ref in tps:
        tp = s.place(ref, 269.24, y, rot=270, ref_at=(5.08, 0, ['left']), val_at=(0, 0, 'hide'))
        s.stub(tp['1'], 5.08, net(ref, '1'))
        y += 10.16 if net(ref, '1') == 'GND' else 7.62
    s.place('H1', 266.7, 141.605, ref_at=(3.81, -1.27, ['left']), val_at=(3.81, 1.27, ['left']))

    y = 160.02
    for line in v['notes'] + [''] + GENERAL_NOTES:
        if line:
            s.text(line, 20.32, y)
        y += 2.54
    return s


def check(sch, sheet):
    """Compare the netlist KiCad extracts from the drawn sheet with the intended one."""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'n.net')
        subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', out, sch],
                       check=True, stdout=subprocess.DEVNULL)
        t = loads(open(out).read())
    got = {}
    for n in find(first(t, 'nets'), 'net'):
        name = first(n, 'name')[1].lstrip('/')
        for node in find(n, 'node'):
            got[(first(node, 'ref')[1], first(node, 'pin')[1])] = name
    bad = []
    for ref, pins in sheet.expect.items():
        for pin, want in pins.items():
            have = got.get((ref, pin), '')
            if (want is None and not have.startswith('unconnected')) or (want is not None and have != want):
                bad.append(f'{ref}.{pin}: drawn as {have!r}, should be {want!r}')
    if bad:
        raise SystemExit('schematic does not match the pin table:\n  ' + '\n  '.join(bad))

def write_library(pdir):
    """Write the project symbol library and the table that points the project at it."""
    syms = []
    for name in sorted(p[1] for v in VARIANTS.values() for p in v['parts'].values() if p[0] == 'MCU_WCH_RiscV'):
        syms.append(adjusted(lib_symbol('MCU_WCH_RiscV', name)))
    libdir = os.path.join(pdir, '..', 'lib')
    os.makedirs(libdir, exist_ok=True)
    lib = [Sym('kicad_symbol_lib'), [Sym('version'), 20241209], [Sym('generator'), 'gen_sch'],
           [Sym('generator_version'), '9.0']] + syms
    open(os.path.join(libdir, LOCAL_LIB + '.kicad_sym'), 'w').write(dumps(lib) + '\n')
    open(os.path.join(pdir, 'sym-lib-table'), 'w').write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/../lib/%s.kicad_sym")'
        '(options "")(descr "Adjusted MCU symbols for the sensor boards"))\n)\n' % (LOCAL_LIB, LOCAL_LIB))

if __name__ == '__main__':
    variant, out = sys.argv[1], sys.argv[2]
    sheet = draw(variant, os.path.splitext(os.path.basename(out))[0])
    open(out, 'w').write(sheet.dumps())
    write_library(os.path.dirname(os.path.abspath(out)))
    check(out, sheet)
