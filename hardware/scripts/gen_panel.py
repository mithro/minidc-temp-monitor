#!/usr/bin/env python3
"""Build the JLCPCB assembly panel for one board.

  gen_panel.py PROJECT_DIR      e.g. gen_panel.py sensor-ch32v003

Reads PROJECT_DIR/<name>.kicad_pcb and writes <name>-panel.kicad_pcb next to it,
plus PROJECT_DIR/out/panel/bom-jlc.csv from the single-board BOM.

The panel is a grid of boards inside a frame of 5 mm rails.  Boards are held by
break-off tabs with mouse-bite holes on their long edges, at the positions set
in layout.py, and are free on the short edges where the connectors are.  The
rails carry three fiducials and four tooling holes.  Every part keeps its
designator with the board number added, for example R5_07.

Copper is copied as it is on the single board, pours included, so the panel is
only as good as the board it was built from: rebuild the board first.
"""
import csv
import os
import shutil
import sys
import tempfile

import pcbnew
from pcbnew import FromMM, VECTOR2I

import layout as L

COLS, ROWS = 2, 8
RAIL = 5.0                  # frame width
GAP = 2.0                   # routed slot between boards, and between boards and frame
BITE_DRILL = 0.6            # mouse-bite hole
BITE_PITCH = 1.0            # 0.4 mm of board left between holes
BITE_INSET = 0.25           # hole centres this far inside the board edge, so the stubs sit below it
TOOLING_DRILL = 1.152
TOOLING_AT = 2.5            # tooling hole centre from both panel edges
FIDUCIAL_AT = (10.0, 3.85)  # fiducial centre from the short and the long panel edge
ORIGIN = (50.0, 30.0)       # panel's top left corner on the sheet
BOARD_ORIGIN = (100.0, 100.0)

PANEL_W = 2 * RAIL + GAP + COLS * (L.LEN + GAP)
PANEL_H = 2 * RAIL + GAP + ROWS * (L.W + GAP)


def P(x, y):
    """Panel millimetres, from the panel's top left corner, to board units."""
    return VECTOR2I(FromMM(ORIGIN[0] + x), FromMM(ORIGIN[1] + y))


def rect(x0, y0, x1, y1):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        s.Append(P(x, y))
    return s


def board_at(col, row):
    """Top left corner of a board on the panel."""
    return RAIL + GAP + col * (L.LEN + GAP), RAIL + GAP + row * (L.W + GAP)


def hole(board, x, y, drill, mask_margin=0.0):
    """A non-plated hole as a one-pad footprint that stays out of the BOM and placement file."""
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference('')
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_BOARD_ONLY)
    pad = pcbnew.PAD(fp)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pad.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.F_Cu, VECTOR2I(FromMM(drill), FromMM(drill)))
    pad.SetDrillSize(VECTOR2I(FromMM(drill), FromMM(drill)))
    pad.SetLayerSet(pcbnew.PAD.UnplatedHoleMask())
    pad.SetLocalSolderMaskMargin(FromMM(mask_margin))
    fp.Add(pad)
    fp.SetPosition(P(x, y))
    board.Add(fp)


def fiducial(board, x, y):
    """1 mm bare copper dot in a 2 mm mask opening, top side."""
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference('')
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_BOARD_ONLY)
    pad = pcbnew.PAD(fp)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.F_Cu, VECTOR2I(FromMM(1.0), FromMM(1.0)))
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask)
    pad.SetLayerSet(ls)
    pad.SetLocalSolderMaskMargin(FromMM(0.5))
    fp.Add(pad)
    fp.SetPosition(P(x, y))
    board.Add(fp)


def build(pdir):
    name = os.path.basename(os.path.normpath(pdir))
    src_path = os.path.join(pdir, name + '.kicad_pcb')
    out_path = os.path.join(pdir, name + '-panel.kicad_pcb')
    # Two boards from one project folder cannot be open together, so the source is read from a copy.
    tmp = tempfile.mkdtemp()
    src = pcbnew.LoadBoard(shutil.copy(src_path, tmp))
    # The panel takes the board's project file, so it is checked against the same rules.
    shutil.copy(src_path[:-3] + 'pro', out_path[:-3] + 'pro')
    if os.path.exists(out_path):
        os.remove(out_path)
    panel = pcbnew.NewBoard(out_path)
    panel.GetDesignSettings().SetBoardThickness(src.GetDesignSettings().GetBoardThickness())

    outline = pcbnew.SHAPE_POLY_SET()
    src.GetBoardPolygonOutlines(outline)
    substrate = rect(0, 0, PANEL_W, PANEL_H)
    substrate.BooleanSubtract(rect(RAIL, RAIL, PANEL_W - RAIL, PANEL_H - RAIL))

    nets = {}
    def net(old, n):
        if not old:
            return panel.FindNet(0)
        key = 'B%02d%s%s' % (n, '' if old.startswith('/') else '/', old)
        if key not in nets:
            nets[key] = pcbnew.NETINFO_ITEM(panel, key)
            panel.Add(nets[key])
        return nets[key]

    n = 0
    for col in range(COLS):
        for row in range(ROWS):
            n += 1
            bx, by = board_at(col, row)
            shift = VECTOR2I(FromMM(ORIGIN[0] + bx - BOARD_ORIGIN[0]), FromMM(ORIGIN[1] + by - BOARD_ORIGIN[1]))
            piece = pcbnew.SHAPE_POLY_SET(outline)
            piece.Move(shift)
            substrate.BooleanAdd(piece)
            for fp in src.GetFootprints():
                c = fp.Duplicate().Cast()
                c.Move(shift)
                if c.GetReference():
                    c.SetReference('%s_%02d' % (c.GetReference(), n))
                for pad in c.Pads():
                    pad.SetNet(net(pad.GetNetname(), n))
                panel.Add(c)
            for t in src.GetTracks():
                c = t.Duplicate().Cast()
                c.Move(shift)
                c.SetNet(net(t.GetNetname(), n))
                panel.Add(c)
            for z in src.Zones():
                c = z.Duplicate().Cast()
                c.Move(shift)
                if not z.GetIsRuleArea():
                    c.SetNet(net(z.GetNetname(), n))
                panel.Add(c)
            for d in src.GetDrawings():
                if d.GetLayer() != pcbnew.Edge_Cuts:
                    c = d.Duplicate().Cast()
                    c.Move(shift)
                    panel.Add(c)
            # Tabs above and below this board, with a row of holes just inside the board edge.
            for tx in L.TABS:
                x0, x1 = bx + tx - L.TAB_WIDTH / 2, bx + tx + L.TAB_WIDTH / 2
                substrate.BooleanAdd(rect(x0, by - GAP - 0.01, x1, by + 0.01))
                if row == ROWS - 1:
                    substrate.BooleanAdd(rect(x0, by + L.W - 0.01, x1, by + L.W + GAP + 0.01))
                for i in range(int(round(L.TAB_WIDTH / BITE_PITCH)) + 1):
                    for y in (by + BITE_INSET, by + L.W - BITE_INSET):
                        hole(panel, x0 + i * BITE_PITCH, y, BITE_DRILL)

    substrate.Simplify()
    for i in range(substrate.OutlineCount()):
        chains = [substrate.Outline(i)] + [substrate.Hole(i, h) for h in range(substrate.HoleCount(i))]
        for chain in chains:
            pts = [chain.CPoint(k) for k in range(chain.PointCount())]
            for a, b in zip(pts, pts[1:] + pts[:1]):
                seg = pcbnew.PCB_SHAPE(panel, pcbnew.SHAPE_T_SEGMENT)
                seg.SetStart(VECTOR2I(a.x, a.y)); seg.SetEnd(VECTOR2I(b.x, b.y))
                seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(FromMM(0.05))
                panel.Add(seg)

    for x in (TOOLING_AT, PANEL_W - TOOLING_AT):
        for y in (TOOLING_AT, PANEL_H - TOOLING_AT):
            hole(panel, x, y, TOOLING_DRILL, mask_margin=0.148)
    fx, fy = FIDUCIAL_AT
    for x, y in ((fx, fy), (PANEL_W - fx, fy), (fx, PANEL_H - fy)):      # three, so the panel has one way up
        fiducial(panel, x, y)
    label = pcbnew.PCB_TEXT(panel)
    label.SetText('%s panel, %d x %d boards, %.0f x %.0f mm' % (name, COLS, ROWS, PANEL_W, PANEL_H))
    label.SetPosition(P(PANEL_W / 2, RAIL / 2)); label.SetLayer(pcbnew.F_SilkS)
    label.SetTextSize(VECTOR2I(FromMM(1.5), FromMM(1.5))); label.SetTextThickness(FromMM(0.2))
    panel.Add(label)
    pcbnew.SaveBoard(out_path, panel)
    shutil.rmtree(tmp)

    # Panel BOM: the single-board BOM with every designator repeated for each board.
    out = os.path.join(pdir, 'out', 'panel')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(pdir, 'out', 'bom-jlc.csv')) as f:
        rows = list(csv.DictReader(f))
    with open(os.path.join(out, 'bom-jlc.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_ALL)
        w.writeheader()
        for r in rows:
            refs = ['%s_%02d' % (ref, k) for k in range(1, n + 1) for ref in r['Designator'].split(',')]
            w.writerow(dict(r, Designator=','.join(refs), Qty=len(refs)))
    return out_path, n


if __name__ == '__main__':
    print('wrote %s, %d boards, %.0f x %.0f mm' % (*build(sys.argv[1]), PANEL_W, PANEL_H))
