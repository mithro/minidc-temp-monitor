"""Small two-layer grid router for the sensor boards.

A* search on a 0.1 mm grid with 45 degree moves.  Each net is grown as a
tree from its first pad.  Clearances are kept by ownership grids: a cell is
either free, owned by one net (only that net may use it) or blocked.

This is not a general autorouter.  It is enough for ~20 short nets on an
open board, and KiCad's DRC is the check on its output.
"""
import heapq, math
import numpy as np
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I

G = 0.1                        # grid pitch, mm
CLR = 0.15                     # copper clearance, mm
EDGE = 0.3                     # copper to board edge, mm
VIA_D, VIA_DRILL = 0.6, 0.3
BASE = 0.1                     # half width of the narrowest track; keep-outs are stored for it
SLOP = 0.03                    # margin on pad and edge keep-outs, mm
TSLOP = 0.02                   # margin on track keep-outs, mm
VIA_PAD = 0.4                  # via centre to any pad edge, mm (hole edge 0.25 mm clear)
VSLOP = 0.06                   # margin on via keep-outs, mm
VIA_COST, BACK_COST = 60.0, 1.6
CROWD_R, CROWD_COST = 1.2, 2.0  # keep tracks from hugging other nets' small pads
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)


class Router:
    def __init__(self, board, origin, size, outline, keepouts=()):
        """outline: board polygon in mm relative to origin.
        keepouts: (x, y, r) circles closed to tracks and vias on both layers."""
        self.board, self.origin = board, origin
        self.nx, self.ny = int(round(size[0] / G)) + 1, int(round(size[1] / G)) + 1
        self.X, self.Y = np.meshgrid(np.arange(self.nx) * G, np.arange(self.ny) * G, indexing='ij')
        self.trk = np.zeros((2, self.nx, self.ny), np.int32)   # track-centre ownership per layer
        self.via = np.zeros((self.nx, self.ny), np.int32)      # via-centre ownership
        self.netid = {}
        edge = self._edge_distance(outline)
        self.trk[:, edge < EDGE + BASE + SLOP] = -1
        self.via[edge < EDGE + VIA_D / 2 + SLOP] = -1
        for x, y, r in keepouts:
            d = np.hypot(self.X - x, self.Y - y)
            self.trk[:, d < r + BASE] = -1
            self.via[d < r + VIA_D / 2] = -1
        self.trees, self.islands, self.done, self.via_ends, self.pad_via = {}, {}, set(), {}, {}
        self.vias_at = set()
        self.crowd = np.zeros(self.trk.shape, np.float32)     # extra cost near pads still to be reached
        self.crowd_own = {}
        self.pads = {}                                          # net -> [(ref, pad, layers, bbox mm)]
        for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):   # fixed order: repeatable routing
            for pad in fp.Pads():
                on = [i for i, l in enumerate(LAYERS) if pad.IsOnLayer(l)]
                if not on:
                    continue
                bb = pad.GetBoundingBox()
                box = (ToMM(bb.GetLeft()) - origin[0], ToMM(bb.GetTop()) - origin[1],
                       ToMM(bb.GetRight()) - origin[0], ToMM(bb.GetBottom()) - origin[1])
                net = pad.GetNetname()
                n = self._id(net) if net else -1
                for l in on:
                    self._mark(self.trk[l], self._box(box, CLR + BASE + 0.02), n)
                self._mark(self.via, self._box(box, CLR + VIA_D / 2 + SLOP), n)
                self.via[self._box(box, VIA_PAD)] = -1          # keep via holes out of and away from pads
                if net and min(box[2] - box[0], box[3] - box[1]) < 0.7:
                    m = self._box(box, CROWD_R)
                    for l in on:
                        self.crowd[l] += m
                        self.crowd_own.setdefault(net, np.zeros(self.trk.shape, np.float32))[l] += m
                if net:
                    if pad.GetShape(LAYERS[on[0]]) == pcbnew.PAD_SHAPE_CIRCLE:   # connect inside the circle
                        c, h = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), (box[2] - box[0]) * 0.35
                        box = (c[0] - h, c[1] - h, c[0] + h, c[1] + h)
                    self.pads.setdefault(net, []).append((fp.GetReference(), pad, on, box))

    def _id(self, net):
        return self.netid.setdefault(net, len(self.netid) + 1)

    def _edge_distance(self, poly):
        """Distance from each grid point to the outline; 0 outside the board."""
        inside = np.zeros(self.X.shape, bool)
        dist = np.full(self.X.shape, 1e9)
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            if y1 != y2:
                cond = ((y1 > self.Y) != (y2 > self.Y)) & (self.X < (x2 - x1) * (self.Y - y1) / (y2 - y1) + x1)
                inside ^= cond
            dx, dy = x2 - x1, y2 - y1
            t = np.clip(((self.X - x1) * dx + (self.Y - y1) * dy) / (dx * dx + dy * dy), 0, 1)
            dist = np.minimum(dist, np.hypot(self.X - x1 - t * dx, self.Y - y1 - t * dy))
        return np.where(inside, dist, 0.0)

    def _box(self, b, grow):
        return (self.X > b[0] - grow) & (self.X < b[2] + grow) & (self.Y > b[1] - grow) & (self.Y < b[3] + grow)

    @staticmethod
    def _mark(grid, mask, n):
        if n < 0:
            grid[mask] = -1
        else:
            grid[mask & (grid != 0) & (grid != n)] = -1
            grid[mask & (grid == 0)] = n

    def _disc(self, grid, i, j, r, n):
        k = int(math.ceil(r / G))
        i0, i1, j0, j1 = max(i - k, 0), min(i + k + 1, self.nx), max(j - k, 0), min(j + k + 1, self.ny)
        ii, jj = np.ogrid[i0:i1, j0:j1]
        self._mark(grid[i0:i1, j0:j1], (ii - i) ** 2 + (jj - j) ** 2 < (r / G) ** 2, n)

    def _ok(self, n, width):
        """Cells a track centre of this net and width may occupy, per layer."""
        ok = (self.trk == 0) | (self.trk == n)
        k = int(math.ceil((width / 2 - BASE) / G - 1e-9))
        bad = ~ok
        grown = bad.copy()
        for di in range(-k, k + 1):
            for dj in range(-k, k + 1):
                if (di or dj) and di * di + dj * dj <= k * k:
                    grown |= np.roll(bad, (di, dj), axis=(1, 2))
        return ~grown, ok

    def _pad_cells(self, box, layers):
        m = self._box(box, -0.04)
        if not m.any():                                        # very thin pad: use its centreline
            m = self._box(box, 0.0)
        ii, jj = np.nonzero(m)
        return {(l, int(i), int(j)) for l in layers for i, j in zip(ii, jj)}

    def escape(self, ref, length=0.5):
        """Give each fine-pitch pad of a footprint a straight stub outward, so
        that later tracks cannot wall the pad in."""
        fp = self.board.FindFootprintByReference(ref)
        cx, cy = ToMM(fp.GetPosition().x) - self.origin[0], ToMM(fp.GetPosition().y) - self.origin[1]
        for net, pads in self.pads.items():
            for r, pad, layers, box in pads:
                w, h = box[2] - box[0], box[3] - box[1]
                if r != ref or min(w, h) > 0.3 or len(pads) < 2:
                    continue
                px, py = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                d = ((1 if px > cx else -1), 0) if w > h else (0, (1 if py > cy else -1))
                i, j = int(round(px / G)), int(round(py / G))
                steps = int(round((max(w, h) / 2 + length) / G))
                path = [(layers[0], i + d[0] * k, j + d[1] * k) for k in range(steps + 1)]
                self._commit(net, self._id(net), 0.2, path)
                self.islands.setdefault(net, []).append({path[-1]})   # later tracks start at the tip
                self.done.add(id(pad))

    def seed_via(self, net, x, y):
        """Place a via by hand (for example in an exposed pad) and start the net's tree there."""
        i, j = int(round(x / G)), int(round(y / G))
        self._add_via(self.board.FindNet(net), self._id(net), i, j)
        self.trees.setdefault(net, set()).update({(0, i, j), (1, i, j)})
        for _, pad, _, box in self.pads[net]:
            if box[0] < x < box[2] and box[1] < y < box[3]:
                self.done.add(id(pad))
        return (1, i, j)

    def drop_vias(self, net, skip=(), redo=()):
        """Take every pad of a net to the back layer through its own via (for a net
        that is a copper pour on the back).  Returns the refs that failed."""
        n, failed = self._id(net), []
        for ref, pad, layers, box in self.pads.get(net, []):
            if (id(pad) in self.done and ref not in redo) or ref in skip or 1 in layers:
                continue
            path = self._search(net, n, 0.2, self._pad_cells(box, layers), None, box)
            if path is None:
                failed.append(ref)
                continue
            self._commit(net, n, 0.2, path)
            self.done.add(id(pad))
            self.via_ends.setdefault(net, set()).add(path[-1])
            self.pad_via[(ref, pad.GetNumber())] = path[-1]
        return failed

    def tie(self, net, sources, targets, width=0.2, vias=True):
        """Join two sets of cells of one net with a track.  True on success."""
        xs, ys = [c[1] * G for c in targets], [c[2] * G for c in targets]
        path = self._search(net, self._id(net), width, sources, set(targets), (min(xs), min(ys), max(xs), max(ys)), vias)
        if path:
            self._commit(net, self._id(net), width, path)
        return bool(path)

    def route_net(self, net, width=0.2, refs=None, stubs=None):
        """Connect the pads of a net (only those on `refs` if given, in that order),
        then the stubs made by escape() (by default only when `refs` is not given).  Returns the refs that could not be reached."""
        n = self._id(net)
        pads = [p for p in self.pads.get(net, []) if id(p[1]) not in self.done]
        if refs:
            pads = sorted((p for p in pads if p[0] in refs), key=lambda p: refs.index(p[0]))
        if net not in self.trees:
            if pads:
                first = pads.pop(0)
                self.trees[net] = self._pad_cells(first[3], first[2])
                self.done.add(id(first[1]))
            elif self.islands.get(net):
                self.trees[net] = self.islands[net].pop()
            else:
                return []
        tree, failed = self.trees[net], []
        centre = lambda p: ((p[3][0] + p[3][2]) / 2 / G, (p[3][1] + p[3][3]) / 2 / G)
        while pads:
            if not refs:                                       # nearest pad to the tree next
                pads.sort(key=lambda p: min(abs(centre(p)[0] - c[1]) + abs(centre(p)[1] - c[2]) for c in tree))
            ref, pad, layers, box = pads.pop(0)
            path = self._search(net, n, width, tree, self._pad_cells(box, layers), box)
            if path is None:
                failed.append(ref)
                continue
            self._commit(net, n, width, path)
            self.done.add(id(pad))
            tree |= set(path) | self._pad_cells(box, layers)
        while (stubs if stubs is not None else not refs) and self.islands.get(net):
            isl = self.islands[net].pop()
            xs, ys = [c[1] * G for c in tree], [c[2] * G for c in tree]
            path = self._search(net, n, 0.2, isl, tree, (min(xs), min(ys), max(xs), max(ys)))
            if path is None:
                failed.append('stub')
                continue
            self._commit(net, n, 0.2, path)
            tree |= set(path) | isl
        return failed

    def _search(self, net, n, width, sources, targets, tbox, vias=True):
        wide, plain = self._ok(n, width)
        own = np.zeros(self.trk.shape, bool)
        for _, _, layers, box in self.pads.get(net, []):
            for l in layers:
                own[l] |= self._box(box, 0.0)
        ok = wide | (plain & own)                              # a track may always leave its own pad
        via_ok = ((self.via == 0) | (self.via == n)) & wide[0] & wide[1]
        crowd = (self.crowd - self.crowd_own.get(net, 0)) * CROWD_COST
        tx, ty = (tbox[0] + tbox[2]) / 2 / G, (tbox[1] + tbox[3]) / 2 / G
        slack = math.hypot(tbox[2] - tbox[0], tbox[3] - tbox[1]) / 2 / G

        def h(i, j):
            if targets is None:
                return 0.0
            dx, dy = abs(i - tx), abs(j - ty)
            return max(0.0, max(dx, dy) + 0.414 * min(dx, dy) - slack)

        best, prev, heap = {}, {}, []
        for l, i, j in sources:
            if not ok[l, i, j]:
                continue
            s = (l, i, j, 8)
            best[s] = 0.0
            heapq.heappush(heap, (h(i, j), 0.0, s))
        while heap:
            _, c, s = heapq.heappop(heap)
            if c > best.get(s, 1e18):
                continue
            l, i, j, d = s
            if (l == 1 and d == 8) if targets is None else (l, i, j) in targets:
                path = [(l, i, j)]
                while s in prev:
                    s = prev[s]
                    path.append(s[:3])
                return path[::-1]
            for nd, (di, dj) in enumerate(DIRS):
                turn = 0 if d == 8 else min((nd - d) % 8, (d - nd) % 8)
                if turn > 2:
                    continue
                a, b = i + di, j + dj
                if not (0 <= a < self.nx and 0 <= b < self.ny) or not ok[l, a, b]:
                    continue
                step = (1.4142 if di and dj else 1.0) * (BACK_COST if l else 1.0)
                self._push(heap, best, prev, s, (l, a, b, nd), c + step + (0, 1.5, 6)[turn] + crowd[l, a, b], h(a, b))
            if vias and via_ok[i, j] and ok[1 - l, i, j]:
                self._push(heap, best, prev, s, (1 - l, i, j, 8), c + VIA_COST, h(i, j))
        return None

    @staticmethod
    def _push(heap, best, prev, s, t, c, h):
        if c < best.get(t, 1e18):
            best[t] = c
            prev[t] = s
            heapq.heappush(heap, (c + h, c, t))

    def _pt(self, i, j):
        return VECTOR2I(FromMM(self.origin[0] + i * G), FromMM(self.origin[1] + j * G))

    def _commit(self, net, n, width, path):
        ni = self.board.FindNet(net)
        r_trk = width / 2 + CLR + BASE + TSLOP                 # _ok widens this for wider tracks
        r_via = width / 2 + CLR + VIA_D / 2 + VSLOP
        for l, i, j in path:
            self._disc(self.trk[l], i, j, r_trk, n)
            self._disc(self.via, i, j, r_via, n)
        runs, cur = [], [path[0]]
        for p in path[1:]:
            if p[0] != cur[-1][0]:                             # layer change: via
                runs.append(cur)
                cur = [p]
                self._add_via(ni, n, p[1], p[2])
            else:
                cur.append(p)
        runs.append(cur)
        for run in runs:
            a = run[0]
            for k in range(1, len(run)):
                step = (run[k][1] - run[k - 1][1], run[k][2] - run[k - 1][2])
                if k == len(run) - 1 or step != (run[k + 1][1] - run[k][1], run[k + 1][2] - run[k][2]):
                    t = pcbnew.PCB_TRACK(self.board)
                    t.SetStart(self._pt(a[1], a[2])); t.SetEnd(self._pt(run[k][1], run[k][2]))
                    t.SetWidth(FromMM(width)); t.SetLayer(LAYERS[a[0]]); t.SetNet(ni)
                    self.board.Add(t)
                    a = run[k]

    def _add_via(self, ni, n, i, j):
        if (i, j) in self.vias_at:                             # a layer change at a via that is already there
            return
        self.vias_at.add((i, j))
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(self._pt(i, j)); v.SetWidth(pcbnew.F_Cu, FromMM(VIA_D)); v.SetDrill(FromMM(VIA_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni)
        self.board.Add(v)
        for l in (0, 1):
            self._disc(self.trk[l], i, j, VIA_D / 2 + CLR + BASE + TSLOP, n)
        self._disc(self.via, i, j, VIA_D + CLR + VSLOP, n)
