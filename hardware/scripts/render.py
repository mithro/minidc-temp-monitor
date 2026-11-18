#!/usr/bin/env python3
"""Render one board in 3D and mark its sizes.

  render.py PROJECT_DIR      e.g. render.py sensor-ch32v003

Writes PROJECT_DIR/out/board-3d.png: an angled 3D view, then top, bottom and
side views to one scale with dimension lines and a scale bar.  The millimetre
values come from the board file (outline, mounting hole, connectors) and the
overall height from the side render, so the picture cannot drift from the
design.  Needs kicad-cli, the pcbnew Python module and Pillow.
"""
import os
import subprocess
import sys
import tempfile

import pcbnew
from PIL import Image, ImageDraw, ImageFont

BG = (247, 247, 244)
INK = (30, 30, 30)
DIM = (176, 38, 38)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
W, H, ZOOM = 2600, 1000, 2.0          # camera for the flat views
PAD = 70                              # canvas margin, pixels


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def render(pcb, out, *args, quality='basic'):
    """Basic quality has no floor or shadows, so the image's alpha channel is
    exactly the board and its parts.  That is what the scale is measured from."""
    subprocess.run(['kicad-cli', 'pcb', 'render', '--background', 'transparent',
                    '--quality', quality, '-o', out, *args, pcb],
                   check=True, stdout=subprocess.DEVNULL)
    return Image.open(out).convert('RGBA')


def flat(pcb, out, side):
    """A flat view at twice the size, scaled down to smooth the edges."""
    im = render(pcb, out, '--side', side, '--width', str(2 * W), '--height', str(2 * H),
                '--zoom', str(ZOOM))
    return im.resize((im.width // 2, im.height // 2), Image.LANCZOS)


def solid(im):
    """Bounding box of the opaque part of an image."""
    return im.getchannel('A').point(lambda a: 255 if a > 127 else 0).getbbox()


def strip_models(text):
    """The board file without its (model ...) blocks."""
    out, i = [], 0
    while True:
        j = text.find('(model', i)
        if j < 0:
            return ''.join(out) + text[i:]
        out.append(text[i:j])
        depth, k = 0, j
        while True:
            depth += {'(': 1, ')': -1}.get(text[k], 0)
            if depth == 0:
                break
            k += 1
        i = k + 1


def geometry(pcb):
    """Sizes in mm, measured from the top left corner of the outline."""
    board = pcbnew.LoadBoard(pcb)
    xs, ys = [], []
    for d in board.GetDrawings():
        if d.GetLayerName() == 'Edge.Cuts':
            for p in (d.GetStart(), d.GetEnd()):
                xs.append(pcbnew.ToMM(p.x)); ys.append(pcbnew.ToMM(p.y))
    x0, y0 = min(xs), min(ys)
    g = {'w': max(xs) - x0, 'h': max(ys) - y0, 'thickness':
         pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())}
    for fp in board.GetFootprints():
        pos = fp.GetPosition()
        at = (pcbnew.ToMM(pos.x) - x0, pcbnew.ToMM(pos.y) - y0)
        if fp.GetReference() == 'H1':
            drill = max(pcbnew.ToMM(p.GetDrillSize().x) for p in fp.Pads())
            g['hole'] = (*at, drill)
        elif fp.GetReference() in ('J1', 'J2'):
            g[fp.GetReference()] = at
    return g


class Sheet:
    """A canvas that grows downwards as views are added."""

    def __init__(self, width):
        self.im = Image.new('RGB', (width, 12000), BG)
        self.d = ImageDraw.Draw(self.im)
        self.y = PAD

    def title(self, text, size=44, bold=True):
        self.d.text((PAD, self.y), text, font=font(size, bold), fill=INK)
        self.y += int(size * 1.6)

    def paste(self, im, x, y):
        self.im.paste(im, (int(x), int(y)), im)

    def arrow(self, tip, direction, size=16):
        (x, y), (dx, dy) = tip, direction
        self.d.polygon([(x, y), (x - dx * size - dy * size / 3, y - dy * size - dx * size / 3),
                        (x - dx * size + dy * size / 3, y - dy * size + dx * size / 3)], fill=DIM)

    def dim_h(self, x0, x1, y, text, ext_from):
        """Horizontal dimension from x0 to x1 at height y, with extension lines."""
        for x in (x0, x1):
            self.d.line([(x, ext_from), (x, y + (10 if y > ext_from else -10))], fill=DIM, width=2)
        self.d.line([(x0, y), (x1, y)], fill=DIM, width=3)
        self.arrow((x0, y), (-1, 0)); self.arrow((x1, y), (1, 0))
        f = font(30)
        tw = self.d.textlength(text, font=f)
        tx = (x0 + x1 - tw) / 2
        ty = y - 42 if y < ext_from else y + 8
        self.d.rectangle([tx - 6, ty, tx + tw + 6, ty + 36], fill=BG)
        self.d.text((tx, ty), text, font=f, fill=DIM)

    def dim_v(self, y0, y1, x, text, ext_from):
        """Vertical dimension from y0 to y1 at position x, text beside it."""
        for y in (y0, y1):
            self.d.line([(ext_from, y), (x + (10 if x > ext_from else -10), y)], fill=DIM, width=2)
        self.d.line([(x, y0), (x, y1)], fill=DIM, width=3)
        self.arrow((x, y0), (0, -1)); self.arrow((x, y1), (0, 1))
        f = font(30)
        tw = self.d.textlength(text, font=f)
        tx = x - tw - 14 if x < ext_from else x + 14
        self.d.text((tx, (y0 + y1) / 2 - 18), text, font=f, fill=DIM)

    def scale_bar(self, x, y, px_per_mm, mm=10):
        for i in range(mm):
            self.d.rectangle([x + i * px_per_mm, y, x + (i + 1) * px_per_mm, y + 14],
                             fill=INK if i % 2 == 0 else BG, outline=INK)
        self.d.text((x + mm * px_per_mm + 14, y - 12), '%d mm' % mm, font=font(30), fill=INK)

    def save(self, path):
        self.im.crop((0, 0, self.im.width, self.y + PAD // 2)).save(path, optimize=True)


def main(pdir):
    name = os.path.basename(os.path.normpath(pdir))
    pcb = os.path.join(pdir, name + '.kicad_pcb')
    g = geometry(pcb)
    with tempfile.TemporaryDirectory() as tmp:
        bare = os.path.join(tmp, 'bare.kicad_pcb')
        with open(pcb) as f, open(bare, 'w') as o:
            o.write(strip_models(f.read()))
        views, boxes = {}, {}
        for side in ('top', 'bottom', 'front'):
            views[side] = flat(pcb, os.path.join(tmp, side + '.png'), side)
            # The bare board, same camera, gives the outline's place in the image.
            boxes[side] = solid(flat(bare, os.path.join(tmp, side + '-bare.png'), side))
        iso = render(pcb, os.path.join(tmp, 'iso.png'), '--perspective', '--rotate', '-50,0,25',
                     '--width', '2600', '--height', '1600', '--zoom', '1.1', quality='high')
    iso = iso.crop(iso.getchannel('A').getbbox())

    sheet = Sheet(W)
    sheet.title('%s   %.1f x %.1f mm' % (name, g['w'], g['h']))
    sheet.paste(iso, (W - iso.width) / 2, sheet.y)
    sheet.y += iso.height + 50

    for side in ('top', 'bottom'):
        l, t, r, b = boxes[side]
        s = (r - l) / g['w']                      # pixels per mm
        full = solid(views[side])
        view = views[side].crop(full)
        sheet.title('%s view' % side.capitalize(), 34)
        top_room = 150 if side == 'top' else 30
        ox = (W - (r - l)) / 2                    # outline's left edge on the sheet
        oy = sheet.y + top_room
        sheet.paste(view, ox - (l - full[0]), oy - (t - full[1]))
        ex, ey = ox + g['w'] * s, oy + g['h'] * s
        if side == 'top':
            sheet.dim_h(ox, ex, oy - 110, '%.1f mm' % g['w'], oy)
            sheet.dim_v(oy, ey, ox - 60, '%.1f mm' % g['h'], ox)
            hx, hy, hd = g['hole']
            sheet.dim_h(ox, ox + hx * s, oy - 45, '%.1f mm' % hx, oy)
            f = font(30)
            sheet.d.line([(ox + hx * s, oy + hy * s + hd * s / 2), (ox + hx * s, ey + 40)], fill=DIM, width=2)
            sheet.d.text((ox + hx * s - 90, ey + 44), 'hole %.1f mm (M3), %.1f mm from the top edge'
                         % (hd, hy), font=f, fill=DIM)
            sheet.scale_bar(ex - 10 * s - 130, ey + 50, s)
            sheet.y = int(ey + 130)
        else:
            sheet.y = int(ey + 50)

    l, t, r, b = boxes['front']
    s = (r - l) / g['w']
    full = solid(views['front'])
    view = views['front'].crop(full)
    height = (full[3] - full[1]) / s
    sheet.title('Side view', 34)
    ox, oy = (W - (r - l)) / 2, sheet.y + 30
    sheet.paste(view, ox - (l - full[0]), oy)
    ex = ox + g['w'] * s
    sheet.dim_v(oy, oy + view.height, ex + 60, '%.1f mm overall' % height, ex)
    sheet.dim_v(oy + view.height - g['thickness'] * s, oy + view.height, ox - 60,
                '%.1f mm board' % g['thickness'], ox)
    sheet.y = int(oy + view.height + 30)
    sheet.save(os.path.join(pdir, 'out', 'board-3d.png'))
    print('%s: %.1f x %.1f mm, %.1f mm overall height' % (name, g['w'], g['h'], height))


if __name__ == '__main__':
    main(sys.argv[1])
