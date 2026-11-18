#!/usr/bin/env python3
"""Build a sensor board PCB from the schematic and the hand layout in layout.py.

Usage: gen_pcb.py <variant> <project dir>

Reads the schematic next to the PCB (via `kicad-cli sch export netlist`), loads
stock KiCad footprints, and places parts, tracks, vias and silkscreen exactly as
layout.py says.  Nothing is auto-routed: the only computed copper is the ground
pour.  build.sh runs DRC afterwards, which is what proves every net is joined.
"""
import json, math, os, subprocess, sys, tempfile
import pcbnew
from pcbnew import FromMM, VECTOR2I
from sexp import loads, find, first
import layout as L

FPDIR = os.environ.get('KICAD_FOOTPRINT_DIR', '/usr/share/kicad/footprints')
MODELDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '3dmodels')
X0, Y0 = 100.0, 100.0      # board origin on the sheet
LAYER = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}


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


def text(board, s, x, y, layer, size=1.0, rot=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size)))
    t.SetTextThickness(FromMM(L.SILK_STROKE))
    t.SetTextAngleDegrees(rot)
    t.SetMirrored(layer == pcbnew.B_SilkS)
    board.Add(t)


def local_models(fp):
    """Point the footprint's 3D models at hardware/3dmodels, which holds the
    few models these boards need, so renders do not need KiCad's model library."""
    models = list(fp.Models())
    fp.Models().clear()
    for m in models:
        stem = os.path.splitext(os.path.basename(m.m_Filename))[0]
        for ext in ('.step', '.wrl'):
            if os.path.exists(os.path.join(MODELDIR, stem + ext)):
                m.m_Filename = '${KIPRJMOD}/../3dmodels/' + stem + ext
                fp.Models().push_back(m)
                break


def window_paste(board, fp, vias, apertures):
    """Exposed pad with vias in it: drop the stock paste opening and paste only
    the area away from the vias, so solder is not drawn down the holes."""
    for pad in list(fp.Pads()):
        if not pad.GetNumber() and pad.IsOnLayer(pcbnew.F_Paste):
            fp.Remove(pad)
    centre = fp.GetPosition()
    for dx, dy, w, h in apertures:
        pad = pcbnew.PAD(fp)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_RECT)
        pad.SetSize(pcbnew.F_Cu, VECTOR2I(FromMM(w), FromMM(h)))
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Paste)
        pad.SetLayerSet(ls)
        pad.SetPosition(VECTOR2I(centre.x + FromMM(dx), centre.y + FromMM(dy)))
        fp.Add(pad)


def outline(board, pts, radius):
    """Closed outline.  Inside (concave) corners get an arc of the given radius,
    which is what the router bit leaves anyway and avoids a stress point."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    cut = []                                   # per corner: (point where the edge arrives, where it leaves, arc mid)
    for i, b in enumerate(pts):
        a, c = pts[i - 1], pts[(i + 1) % n]
        ua = ((a[0] - b[0]) / math.dist(a, b), (a[1] - b[1]) / math.dist(a, b))
        uc = ((c[0] - b[0]) / math.dist(c, b), (c[1] - b[1]) / math.dist(c, b))
        turn = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if turn * area < 0 and radius:         # concave
            p1 = (b[0] + ua[0] * radius, b[1] + ua[1] * radius)
            p2 = (b[0] + uc[0] * radius, b[1] + uc[1] * radius)
            centre = (b[0] + (ua[0] + uc[0]) * radius, b[1] + (ua[1] + uc[1]) * radius)
            d = math.dist(b, centre)
            mid = (centre[0] + (b[0] - centre[0]) * radius / d, centre[1] + (b[1] - centre[1]) * radius / d)
            cut.append((p1, p2, mid))
        else:
            cut.append((b, b, None))
    for i in range(n):
        p1, p2, mid = cut[i]
        if mid:
            arc = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
            arc.SetArcGeometry(P(*p1), P(*mid), P(*p2))
            arc.SetLayer(pcbnew.Edge_Cuts); arc.SetWidth(FromMM(0.1))
            board.Add(arc)
        seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(P(*p2)); seg.SetEnd(P(*cut[(i + 1) % n][0]))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(FromMM(0.1))
        board.Add(seg)


def rule_area(board, pts, pour_only):
    """Copper keep-out on both layers: no pour, and unless pour_only, no tracks or vias."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowTracks(not pour_only); z.SetDoNotAllowVias(not pour_only)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    o = z.Outline(); o.NewOutline()
    for x, y in pts:
        o.Append(FromMM(X0 + x), FromMM(Y0 + y))
    board.Add(z)


def build(variant, pdir):
    lay = L.LAYOUT[variant]
    name = os.path.basename(os.path.normpath(pdir))
    sch, pcb = (os.path.join(pdir, name + ext) for ext in ('.kicad_sch', '.kicad_pcb'))
    comps, nets = netlist(sch)
    if os.path.exists(pcb):
        os.remove(pcb)
    board = pcbnew.NewBoard(pcb)
    ds = board.GetDesignSettings()
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(FromMM(0.15)); nc.SetTrackWidth(FromMM(0.2))
    nc.SetViaDiameter(FromMM(L.VIA[0])); nc.SetViaDrill(FromMM(L.VIA[1]))
    ds.m_TrackMinWidth = FromMM(0.15); ds.m_MinClearance = FromMM(0.15)
    ds.m_ViasMinSize = FromMM(0.5); ds.m_MinThroughDrill = FromMM(0.3)
    ds.m_ViasMinAnnularWidth = FromMM(0.1)
    ds.m_CopperEdgeClearance = FromMM(L.EDGE); ds.m_HoleToHoleMin = FromMM(0.25)
    ds.m_HoleClearance = FromMM(0.2)
    ds.SetCustomTrackWidth(FromMM(0.2))
    ds.m_TentViasFront = ds.m_TentViasBack = True

    netobjs = {}
    for nname in sorted(set(nets.values())):
        ni = pcbnew.NETINFO_ITEM(board, nname)
        board.Add(ni)
        netobjs[nname] = ni
    net = lambda n: netobjs[n] if n in netobjs else netobjs['/' + n]

    pads = {}                                   # 'R1.2' -> pad centre in board mm
    for ref, c in sorted(comps.items()):
        lib, fpname = c['footprint'].split(':')
        fp = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + '.pretty'), fpname)
        fp.SetReference(ref); fp.SetValue(c['value'])
        fp.SetFPID(pcbnew.LIB_ID(lib, fpname))
        local_models(fp)
        x, y, rot = lay['place'][ref]
        fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(rot)
        fp.Value().SetVisible(False)
        label = lay['labels'].get(ref)          # (dx, dy[, rotation[, text]]) from the part centre
        r = fp.Reference()
        r.SetVisible(False)
        if label:
            text(board, label[3] if len(label) > 3 else ref, x + label[0], y + label[1], pcbnew.F_SilkS,
                 L.SILK_REF, label[2] if len(label) > 2 else 0)
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
            if ref[0] in 'JT':                  # connector and test pads sit solid in the pour
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        if ref in lay.get('paste_windows', {}):
            window_paste(board, fp, *lay['paste_windows'][ref])
        board.Add(fp)
        for pad in fp.Pads():
            if pad.GetNumber():
                pos = pad.GetPosition()
                pads.setdefault(f'{ref}.{pad.GetNumber()}', (pcbnew.ToMM(pos.x) - X0, pcbnew.ToMM(pos.y) - Y0))
    missing = set(lay['place']) ^ set(comps)
    if missing:
        raise SystemExit(f'placement and schematic disagree on: {sorted(missing)}')

    def pt(p):
        """A track point: (x, y), 'REF.PAD', or ('REF.PAD', dx, dy)."""
        if isinstance(p, str):
            return pads[p]
        if isinstance(p[0], str):
            return (pads[p[0]][0] + p[1], pads[p[0]][1] + p[2])
        return p

    outline(board, L.OUTLINE, L.CORNER_RADIUS)
    hx, hy, hr = L.HOLE_KEEPOUT
    rule_area(board, [(hx + hr * math.cos(math.radians(a)), hy + hr * math.sin(math.radians(a)))
                      for a in range(0, 360, 10)], pour_only=False)
    rule_area(board, L.FINGER, pour_only=True)
    for pts in L.TAB_KEEPOUTS:
        rule_area(board, pts, pour_only=True)

    for n, layer, width, pts in lay['tracks']:
        pts = [pt(p) for p in pts]
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(P(*a)); t.SetEnd(P(*b))
            t.SetWidth(FromMM(width)); t.SetLayer(LAYER[layer]); t.SetNet(net(n))
            board.Add(t)
    for n, *where in lay['vias'] + [('GND', x, y) for x, y in lay['stitch']]:
        size = where[2] if len(where) > 2 else L.VIA
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(P(*pt(tuple(where[:2]) if not isinstance(where[0], str) else where[0])))
        v.SetWidth(pcbnew.F_Cu, FromMM(size[0])); v.SetDrill(FromMM(size[1]))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net(n))
        board.Add(v)

    for s, x, y, side, size, rot in lay['silk']:
        text(board, s, x, y, pcbnew.F_SilkS if side == 'F' else pcbnew.B_SilkS, size, rot)

    for x1, y1, x2, y2, side in lay['boxes']:   # filled silkscreen box to write on
        box = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
        box.SetStart(P(x1, y1)); box.SetEnd(P(x2, y2))
        box.SetLayer(pcbnew.F_SilkS if side == 'F' else pcbnew.B_SilkS)
        box.SetWidth(FromMM(L.SILK_STROKE)); box.SetFilled(True)
        board.Add(box)

    def inset(by):
        """The board outline moved in by a distance, as one polygon."""
        s = pcbnew.SHAPE_POLY_SET(); s.NewOutline()
        for x, y in L.OUTLINE:
            s.Append(P(x, y))
        s.Deflate(FromMM(by), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FromMM(0.005))
        return s
    # The pour is drawn as the outline moved in by the edge clearance, so it cannot reach an edge.
    pour_area = inset(L.EDGE)               # kept in a name: the outline below points into it
    edge = pour_area.Outline(0)
    pour = [edge.CPoint(i) for i in range(edge.PointCount())]
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(net('GND'))
        z.SetLocalClearance(FromMM(0.25)); z.SetMinThickness(FromMM(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(FromMM(0.2)); z.SetThermalReliefSpokeWidth(FromMM(0.3))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline(); o.NewOutline()
        for pt in pour:
            o.Append(pt)
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    # The filler run from a script does not apply the board-edge rule and DRC does not test fills
    # against the edge, so check here that no copper pour comes closer to the edge than it should.
    limit = inset(L.EDGE - 0.01)
    for z in board.Zones():
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not z.GetIsRuleArea() and z.IsOnLayer(layer):
                over = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(layer))
                over.BooleanSubtract(limit)
                if over.Area() > 0:
                    sys.exit('pour closer than %.1f mm to the board edge' % L.EDGE)
    pcbnew.SaveBoard(pcb, board)
    if lay.get('paste_windows'):
        # A windowed paste layer makes the footprint differ from its library copy on purpose.
        pro = pcb[:-len('kicad_pcb')] + 'kicad_pro'
        with open(pro) as f:
            settings = json.load(f)
        settings['board']['design_settings']['rule_severities']['lib_footprint_mismatch'] = 'ignore'
        with open(pro, 'w') as f:
            json.dump(settings, f, indent=2)
            f.write('\n')
    return pcb


if __name__ == '__main__':
    print('wrote', build(sys.argv[1], sys.argv[2]))
