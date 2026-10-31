#!/usr/bin/env python3
"""Pune screenshot-urile cu lista de cumparaturi in rama telefoanelor drepte -> img/<limba>/shopping.webp.

Rama se ia dintr-un mockup existent (img/<limba>/family.webp, 784x1559; fridge.webp nu, are cardul ridicat peste rama): telefonul e la
x 16..767; ecranul, masurat direct pe conturul din family.webp (identic in toate limbile),
e dreptunghiul rotunjit (40,23)-(741,1534) cu raza ~90. Pe marginea ecranului (inelul de
cativa pixeli) se repun pixelii de bezel din mockup, ca anti-aliasing-ul colturilor sa fie
exact cel original. Dynamic Island (x 294..488, y 48..101) se pastreaza din mockup.

Scara si pozitia screenshot-ului (945x2048) s-au masurat pe pastila "Personal" din header,
aceeasi componenta in ambele ecrane: 209px in mockup vs 279px in screenshot -> 0.749, iar
marginile ei cad la x+40.6, y-0.6. Asa textul are exact marimea din celelalte mockup-uri.

Mockup-urile existente nu au bara de status (ora, semnal, baterie), asa ca in screenshot
zonele respective se acopera cu gradientul header-ului, refacut printr-o regresie patratica
pe pixelii curati din jur.

Utilizare: shopping-mockups.py "<folderul cu screenshot-uri>" [nume] [limba=sufix ...]
  ex. istoricul: shopping-mockups.py "<folder>" history ro="15.04.23 (1)" en=15.04.23 ...
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = {  # limba -> sufixul fisierului WhatsApp
    'ro': '14.29.46', 'en': '14.29.45', 'da': '14.29.46 (2)', 'nl': '14.29.46 (3)',
    'hu': '14.29.46 (4)', 'de': '14.29.47', 'fr': '14.29.47 (1)', 'sv': '14.29.46 (1)',
}
SCALE, DX, DY = 0.749, 40.6, -0.6
SCREEN, R_IN = (40, 23, 741, 1534), 90
ISLAND, R_ISL = (294, 48, 488, 101), 27
SS = 4


def rr_mask(size, box, r, grow=0):
    w, h = size
    m = Image.new('L', (w * SS, h * SS), 0)
    x0, y0, x1, y1 = box
    ImageDraw.Draw(m).rounded_rectangle(
        ((x0 - grow) * SS, (y0 - grow) * SS, (x1 + grow + 1) * SS - 1, (y1 + grow + 1) * SS - 1),
        (r + grow) * SS, fill=255)
    return m.resize(size, Image.LANCZOS)


def strip_status_bar(a):
    """Acopera ora / semnalul / bateria (randurile 0..120) cu gradientul header-ului."""
    a = a.astype(float)
    band = a[:150]
    bright = (band.min(axis=2) > 170) | ((band[:, :, 0] > 200) & (band[:, :, 2] < 120))  # alb + galben
    bright |= band.max(axis=2) < 90  # pastila neagra a unei activitati live (ex. Bolt Food) langa insula
    ys, xs = np.nonzero(bright[:120])
    hole = np.zeros(band.shape[:2], bool)
    for x0, x1 in ((0, 472), (472, 945)):  # ora in stanga, iconitele in dreapta
        sel = (xs >= x0) & (xs < x1)
        if sel.any():
            # +45 in dreapta: varful bateriei e albastru-deschis si nu trece pragul
            hole[max(ys[sel].min() - 10, 0):ys[sel].max() + 11,
                 max(xs[sel].min() - 12, 0):xs[sel].max() + 45] = True
    yy, xx = np.mgrid[0:150, 0:945]
    feats = lambda y, x: np.stack([np.ones_like(x), x, y, x * x, y * y, x * y], -1) / [1, 945, 150, 945**2, 150**2, 945 * 150]
    ok = ~hole
    F = feats(yy[ok].astype(float), xx[ok].astype(float))
    for c in range(3):
        coef, *_ = np.linalg.lstsq(F, band[:, :, c][ok], rcond=None)
        fit = feats(yy[hole].astype(float), xx[hole].astype(float)) @ coef
        a[:150, :, c][hole] = fit
    return np.clip(a, 0, 255).astype(np.uint8)


def build(shot_path, frame_path, out_path, dim=1):
    frame = Image.open(frame_path).convert('RGBA')
    shot = Image.open(shot_path).convert('RGB')
    # unele screenshot-uri vin recomprimate (ex. 738x1600); masuratorile sunt pe 945x2048
    if shot.size != (945, 2048):
        shot = shot.resize((945, 2048), Image.LANCZOS)
    shot = np.asarray(shot)
    # margine de 8px repetata, ca box-ul de mai jos sa nu iasa din imagine
    P = 8
    shot = Image.fromarray(np.pad(strip_status_bar(shot), ((P, P), (P, P), (0, 0)), mode='edge'))

    # doar zona ecranului, scalata cu pozitionare sub-pixel prin box-ul de la resize
    x0, y0, x1, y1 = SCREEN[0], SCREEN[1], SCREEN[2] + 1, SCREEN[3] + 1
    src_box = tuple(P + v for v in ((x0 - DX) / SCALE, (y0 - DY) / SCALE, (x1 - DX) / SCALE, (y1 - DY) / SCALE))
    part = shot.resize((x1 - x0, y1 - y0), Image.LANCZOS, box=src_box)
    if dim != 1:  # ecran intunecat in spatele unui card ridicat (profile-mockups.py)
        part = part.point(lambda v: v * dim)
    screen = Image.new('RGBA', frame.size)
    screen.paste(part, (x0, y0))

    out = frame.copy()
    out.paste(screen, (0, 0), rr_mask(frame.size, SCREEN, R_IN, grow=1))
    # pe inelul de la marginea ecranului, pixelii care in mockup sunt bezel raman bezel
    f = np.asarray(frame).astype(int)
    lum = (f[:, :, :3] * (299, 587, 114)).sum(axis=2) // 1000
    screenish = ((f[:, :, :3].max(2) - f[:, :, :3].min(2)) > 45) | (lum > 140)
    ring = (np.asarray(rr_mask(frame.size, SCREEN, R_IN, grow=2)) > 0) & \
           (np.asarray(rr_mask(frame.size, SCREEN, R_IN, grow=-6)) < 255)
    keep = Image.fromarray(np.where(ring & ~screenish, 255, 0).astype(np.uint8))
    out.paste(frame, (0, 0), keep)
    out.paste(frame, (0, 0), rr_mask(frame.size, ISLAND, R_ISL, grow=1))
    out.save(out_path, 'WEBP', quality=90, method=6)


if __name__ == '__main__':
    folder = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else 'shopping'
    shots = dict(a.split('=', 1) for a in sys.argv[3:]) or SHOTS
    for lang, suf in shots.items():
        src = os.path.join(folder, f'WhatsApp Image 2026-10-28 at {suf}.jpeg')
        build(src, os.path.join(ROOT, 'img', lang, 'family.webp'), os.path.join(ROOT, 'img', lang, name + '.webp'))
        print('  ', lang, '<-', os.path.basename(src))
