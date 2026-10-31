#!/usr/bin/env python3
"""Reface img/<limba>/fridge.webp din screenshot-urile cu frigiderul: ecranul intra in rama
ca la shopping-mockups.py, iar cardul cu paine se ridica peste lista, mai mare decat restul
si iesind din rama in ambele parti, ca in mockup-ul initial din Figma.

Marirea s-a masurat pe vechiul fridge.webp (ro), potrivind bara de progres, "Paine",
"7 zile" si "10,93 lei" din screenshot-ul nou peste cardul ridicat: 0.873 px de mockup per
px de screenshot 945x2048, adica 1.166x fata de restul ecranului (0.749). Pe verticala,
cardul sta intre cardul de deasupra si cel de dedesubt la fel ca in vechiul mockup
(centrul cu 3.5px sub mijlocul golului). Umbra e cea din vechiul mockup: masca cardului
coborata 16px, blur 10, opacitate 0.22, doar peste telefon (in afara lui alfa ramane 0).

Utilizare: fridge-mockups.py ["<folderul cu screenshot-uri>"] [limba=sufix ...]
"""
import importlib.util
import os
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('sm', os.path.join(ROOT, '_build', 'shopping-mockups.py'))
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)

FOLDER = '/mnt/c/Users/User/OneDrive/Documente/fridgy fridge screenshots'
SHOTS = {
    'sv': '21.00.53 (1)', 'ro': '21.00.53', 'nl': '21.00.54 (1)', 'hu': '21.00.54 (2)',
    'de': '21.00.54 (3)', 'da': '21.00.54', 'en': '21.00.55 (1)', 'fr': '21.00.55',
}
CARD, R_CARD = (22.5, 1050.5, 921.5, 1239.5), 32   # cardul cu paine, in screenshot-ul 945x2048
ABOVE, BELOW = 1024, 1273                           # marginea cardului de sus / de jos
K = 0.873                                           # scara cardului ridicat
LIFT_DY = 3.5
SH_DY, SH_BLUR, SH_OP = 16, 10, 0.22


def lift_card(shot_path, frame_path, out_path, card, r_card, k, top, shadow, cx=None, dim=1, white_from=None):
    """Ecranul in rama + cardul `card` (x0,y0,x1,y1 in screenshot-ul 945x2048) ridicat la
    scara `k`, cu marginea de sus la y=`top` in mockup si centrat pe orizontala la `cx`.
    `dim` intuneca ecranul din spate; de la randul `white_from` in jos cardul se umple cu alb
    (acolo unde in screenshot il acopera bara de navigare)."""
    tmp = out_path + '.base.webp'
    sm.build(shot_path, frame_path, tmp, dim)
    base = Image.open(tmp).convert('RGBA')
    os.remove(tmp)
    W, H = base.size

    x0, y0, x1, y1 = card
    ox = (W / 2 if cx is None else cx) - k * (x0 + x1) / 2
    oy = top - k * y0

    shot = Image.open(shot_path).convert('RGB')
    f = shot.size[0] / 945  # screenshot-urile vin si la 738x1600
    if white_from is not None:
        ImageDraw.Draw(shot).rectangle((0, white_from * f, *shot.size), fill='white')
    # mockup = k * s945 + o  ->  sursa = (mockup - o) / k * f
    lifted = shot.transform((W, H), Image.AFFINE, (f / k, 0, -ox * f / k, 0, f / k, -oy * f / k), Image.BICUBIC)
    box = (ox + k * x0, oy + k * y0, ox + k * x1, oy + k * y1)
    m = Image.new('L', (W * sm.SS, H * sm.SS), 0)
    ImageDraw.Draw(m).rounded_rectangle([v * sm.SS for v in box], k * r_card * sm.SS, fill=255)
    mask = m.resize((W, H), Image.LANCZOS)

    sh_dy, sh_blur, sh_op = shadow
    sh = Image.new('L', (W, H), 0)
    sh.paste(mask, (0, sh_dy))
    sh = sh.filter(ImageFilter.GaussianBlur(sh_blur)).point(lambda v: int(v * sh_op))
    rgb = np.asarray(base.convert('RGB')).astype(float)
    rgb *= 1 - np.asarray(sh, float)[:, :, None] / 255
    out = Image.fromarray(rgb.clip(0, 255).astype(np.uint8)).convert('RGBA')

    out.paste(lifted.convert('RGBA'), (0, 0), mask)
    out.putalpha(ImageChops.lighter(base.getchannel('A'), mask))
    out.save(out_path, 'WEBP', quality=90, method=6)
    return box


def build(shot_path, frame_path, out_path):
    mid = sm.SCALE * (ABOVE + BELOW) / 2 + sm.DY + LIFT_DY
    top = mid - K * (CARD[3] - CARD[1]) / 2
    return lift_card(shot_path, frame_path, out_path, CARD, R_CARD, K, top, (SH_DY, SH_BLUR, SH_OP))


if __name__ == '__main__':
    folder = sys.argv[1] if len(sys.argv) > 1 and '=' not in sys.argv[1] else FOLDER
    shots = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a) or SHOTS
    for lang, suf in shots.items():
        src = os.path.join(folder, f'WhatsApp Image 2026-10-30 at {suf}.jpeg')
        box = build(src, os.path.join(ROOT, 'img', lang, 'family.webp'), os.path.join(ROOT, 'img', lang, 'fridge.webp'))
        print('  ', lang, '<-', os.path.basename(src), 'card', tuple(round(v, 1) for v in box))
