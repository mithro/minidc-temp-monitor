#!/usr/bin/env python3
"""Place the MCU temperature sensor board and write an unrouted or routed PCB.

Usage: gen_pcb.py <variant> <project dir> [--route]

Reads the schematic next to the PCB (via `kicad-cli sch export netlist`),
loads stock KiCad footprints, places them from the tables below, draws the
outline, optionally routes it with scripts/route.py, then pours the ground zones.
"""
import math, os, subprocess, sys, tempfile
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I
from sexp import loads, find, first

FPDIR = os.environ.get('KICAD_FOOTPRINT_DIR', '/usr/share/kicad/footprints')
W, L = 13.0, 42.0          # board height and length, mm
X0, Y0 = 100.0, 100.0      # board origin on the sheet

# Outline, clockwise from the top-left corner.  Zip-tie notches at x 15..17.5,
# thermistor finger at top right (free end at x 26, joined to the board at x 33).
OUTLINE = [(0, 0), (15, 0), (15, 1.2), (17.5, 1.2), (17.5, 0), (25, 0), (25, 3.6), (33, 3.6),
           (33, 2.6), (26, 2.6), (26, 0), (L, 0), (L, W), (17.5, W), (17.5, W - 1.2),
           (15, W - 1.2), (15, W), (0, W)]

HOLE_KEEPOUT = (10.5, 6.5, 3.0)   # M3 screw head, kept clear of tracks and vias

EP_VIA = {'ch32v005': (24.3, 7.4)}  # ground via in the QFN exposed pad

# Ground pour, both layers.  Kept off the thermistor finger.
POUR = [(0.4, 0.4), (24.6, 0.4), (24.6, 4.0), (33.4, 4.0), (33.4, 0.4), (L - 0.4, 0.4), (L - 0.4, W - 0.4), (0.4, W - 0.4)]

COMMON_PLACE = {
    'J1': (3.3, 6.5, 270), 'J2': (L - 3.3, 6.5, 90), 'H1': (10.5, 6.5, 0),
    'RT1': (29.5, 1.3, 0), 'C3': (35.2, 1.3, 0), 'R1': (37.6, 1.3, 0),
    'D1': (20.2, 1.5, 0), 'R2': (23.1, 1.5, 0),
    'R3': (19.0, 4.4, 0), 'R4': (19.0, 5.6, 0),
    'R5': (32.6, 5.4, 0), 'R6': (32.6, 6.6, 0),
    'C1': (29.6, 7.6, 90), 'C2': (30.9, 7.6, 90),
}
PLACE = {
    'ch32v003': dict(COMMON_PLACE, U1=(24.3, 7.4, 180), TP1=(19.6, 11.6, 0), TP2=(21.9, 11.6, 0), TP3=(24.2, 11.6, 0)),
    'ch32v005': dict(COMMON_PLACE, U1=(24.3, 7.4, 0), TP1=(19.6, 11.6, 0), TP2=(21.9, 11.6, 0), TP3=(24.2, 11.6, 0),
                     TP4=(26.5, 11.6, 0), TP5=(28.8, 11.6, 0), TP6=(31.1, 11.6, 0)),
}
SILK_NAME = {'ch32v003': 'CH32V003', 'ch32v005': 'CH32V005'}

def P(x, y):
    return VECTOR2I(FromMM(X0 + x), FromMM(Y0 + y))

def netlist(sch):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'n.net')
        subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', out, sch],
                       check=True, stdout=subprocess.DEVNULL)
        t = loads(open(out).read())
    comps = {}
    for c in find(first(t, 'components'), 'comp'):
        props = {first(p, 'name')[1]: (first(p, 'value') or [0, ''])[1] for p in find(c, 'property')}
        comps[first(c, 'ref')[1]] = dict(value=first(c, 'value')[1], footprint=first(c, 'footprint')[1],
                                         props=props, path=first(c, 'tstamps')[1])
    nets = {}
    for n in find(first(t, 'nets'), 'net'):
        name = first(n, 'name')[1]
        for node in find(n, 'node'):
            nets[(first(node, 'ref')[1], first(node, 'pin')[1])] = name
    return comps, nets

def text(board, s, x, y, layer, size=0.8, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size)))
    t.SetTextThickness(FromMM(size * 0.15))
    t.SetMirrored(mirror)
    board.Add(t)

def build(variant, pdir):
    name = os.path.basename(os.path.normpath(pdir))
    sch, pcb = (os.path.join(pdir, name + ext) for ext in ('.kicad_sch', '.kicad_pcb'))
    comps, nets = netlist(sch)
    if os.path.exists(pcb):
        os.remove(pcb)
    board = pcbnew.NewBoard(pcb)
    ds = board.GetDesignSettings()
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(FromMM(0.15)); nc.SetTrackWidth(FromMM(0.2))
    nc.SetViaDiameter(FromMM(0.6)); nc.SetViaDrill(FromMM(0.3))
    ds.m_TrackMinWidth = FromMM(0.127); ds.m_MinClearance = FromMM(0.127)
    ds.m_ViasMinSize = FromMM(0.5); ds.m_MinThroughDrill = FromMM(0.3)
    ds.m_CopperEdgeClearance = FromMM(0.3); ds.m_HoleToHoleMin = FromMM(0.5)
    ds.SetCustomTrackWidth(FromMM(0.2))
    ds.m_TentViasFront = ds.m_TentViasBack = True

    netobjs = {}
    for nname in sorted(set(nets.values())):
        ni = pcbnew.NETINFO_ITEM(board, nname)
        board.Add(ni)
        netobjs[nname] = ni

    place = PLACE[variant]
    for ref, c in sorted(comps.items()):
        lib, fpname = c['footprint'].split(':')
        fp = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + '.pretty'), fpname)
        fp.SetReference(ref); fp.SetValue(c['value'])
        fp.SetFPID(pcbnew.LIB_ID(lib, fpname))
        x, y, rot = place[ref]
        fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(rot)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH('/' + c['path'].strip('/')))
        if 'dnp' in c['props']:
            fp.SetDNP(True)
        if c['props'].get('LCSC'):
            fp.SetField('LCSC', c['props']['LCSC'])
            fp.GetFieldByName('LCSC').SetVisible(False)
        for pad in fp.Pads():
            n = nets.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netobjs[n])
        board.Add(fp)
    missing = set(place) - set(comps)
    if missing:
        raise SystemExit(f'placed but not in schematic: {missing}')

    for a, b in zip(OUTLINE, OUTLINE[1:] + OUTLINE[:1]):
        seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(P(*a)); seg.SetEnd(P(*b)); seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(FromMM(0.1))
        board.Add(seg)

    text(board, 'UP', 7.4, 1.5, pcbnew.F_SilkS)
    text(board, 'DN', L - 4.0, 12.0, pcbnew.F_SilkS)
    text(board, f'minidc temp {SILK_NAME[variant]} v0.1', 24, 5.0, pcbnew.B_SilkS, size=0.9, mirror=True)
    text(board, 'SHARED BUS: R3 R4 = 0R', 21, 7.0, pcbnew.B_SilkS, size=0.8, mirror=True)
    text(board, 'RELAY: R5 R6 = 4k7', 21, 8.6, pcbnew.B_SilkS, size=0.8, mirror=True)
    text(board, 'ADDR/ID:', 6.5, 11.0, pcbnew.B_SilkS, size=0.8, mirror=True)
    pcbnew.SaveBoard(pcb, board)
    return pcb

def route(pcb, variant, tries=15):
    """Route with the grid router in route.py.

    Ground is a pour on both layers, so each ground pad only gets a via to the
    back; the thermistor's ground runs as a track along the finger, which has no
    pour.  The router has no rip-up: when nets fail, they go to the front of the
    order and the board is routed again from scratch."""
    from route import Router
    order, seen = None, None
    for attempt in range(tries):
        board = pcbnew.LoadBoard(pcb)
        r = Router(board, (X0, Y0), (L, W), OUTLINE, keepouts=[HOLE_KEEPOUT])
        r.escape('U1')
        ep = r.seed_via('GND', *EP_VIA[variant]) if variant in EP_VIA else None
        r.trees.pop('GND', None)
        failed = {'GND': r.route_net('GND', refs=['C3', 'RT1'])}
        r.trees.pop('GND', None)
        failed['GND'] += r.drop_vias('GND', redo=['C3'])
        if ep:      # tracks ring the QFN, so tie its ground via by track to a ground via well outside
            far = {c for c in r.via_ends['GND'] if math.hypot(c[1] * 0.1 - ep[1] * 0.1, c[2] * 0.1 - ep[2] * 0.1) > 4}
            if not r.tie('GND', {ep}, far, 0.3):
                failed['GND'].append('U1')
        if order is None:
            span = lambda net: max(abs(a[3][0] - b[3][0]) + abs(a[3][1] - b[3][1]) for a in r.pads[net] for b in r.pads[net])
            order = sorted((n for n in r.pads if n != 'GND' and len(r.pads[n]) > 1), key=span)
        for net in order:
            failed[net] = []
            if net == 'VDD':                                  # wide trunk from connector to connector
                failed[net] = r.route_net(net, 0.4, refs=['J1', 'J2'])
            failed[net] += r.route_net(net)
        failed = {k: v for k, v in failed.items() if v}
        print(f'attempt {attempt}: not routed {failed}' if failed else f'attempt {attempt}: all routed', flush=True)
        if not failed or set(failed) == seen:
            break
        seen = set(failed)
        order = [n for n in order if n in failed] + [n for n in order if n not in failed]
    pcbnew.SaveBoard(pcb, board)
    return r

def ground_groups(board, net):
    """Groups of ground vias that the filled pours, pads and tracks join together."""
    vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net]
    parent = {}
    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def at(pos, layer):
        """Everything on the net that has copper at this point of this layer."""
        hits = [('via', v.GetPosition().x, v.GetPosition().y) for v in vias
                if (v.GetPosition() - pos).EuclideanNorm() < v.GetWidth(layer) // 2]
        for z in board.Zones():
            if z.GetFirstLayer() == layer:
                polys = z.GetFilledPolysList(layer)
                hits += [('zone', layer, k) for k in range(polys.OutlineCount()) if polys.Contains(pos, k)]
        hits += [('pad', p.GetPosition().x, p.GetPosition().y) for fp in board.GetFootprints() for p in fp.Pads()
                 if p.GetNetname() == net and p.IsOnLayer(layer) and p.HitTest(pos)]
        return hits
    def join(items):
        for other in items[1:]:
            parent[find(other)] = find(items[0])
    for v in vias:
        me = ('via', v.GetPosition().x, v.GetPosition().y)
        join([me] + at(v.GetPosition(), pcbnew.F_Cu) + at(v.GetPosition(), pcbnew.B_Cu))
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == net:
            join(at(t.GetStart(), t.GetLayer()) + at(t.GetEnd(), t.GetLayer()))
    groups = {}
    for v in vias:
        groups.setdefault(find(('via', v.GetPosition().x, v.GetPosition().y)), []).append(v)
    return sorted(groups.values(), key=len, reverse=True)

def pour(pcb, router=None):
    """Add the ground zones and fill them.  Signal tracks can cut a piece of pour
    off from the rest; such a piece is tied back with a track and the fill redone."""
    board = router.board if router else pcbnew.LoadBoard(pcb)
    gnd = board.FindNet('GND')
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(gnd)
        z.SetLocalClearance(FromMM(0.25)); z.SetMinThickness(FromMM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline(); o.NewOutline()
        for x, y in POUR:
            o.Append(FromMM(X0 + x), FromMM(Y0 + y))
        board.Add(z)
    for _ in range(4):
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        groups = ground_groups(board, 'GND')
        if len(groups) < 2 or not router:
            break
        cells = lambda vs: {(l, int(round((ToMM(v.GetPosition().x) - X0) / 0.1)), int(round((ToMM(v.GetPosition().y) - Y0) / 0.1)))
                            for v in vs for l in (0, 1)}
        for g in groups[1:]:
            print('tying cut-off ground piece:', 'ok' if router.tie('GND', cells(g), cells(groups[0])) else 'FAILED')
    pcbnew.SaveBoard(pcb, board)

if __name__ == '__main__':
    variant, pdir = sys.argv[1], sys.argv[2]
    pcb = build(variant, pdir)
    if '--route' in sys.argv:
        router = route(pcb, variant)
        if '--no-pour' not in sys.argv:
            pour(pcb, router)
    print('wrote', pcb)
