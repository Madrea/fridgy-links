#!/usr/bin/env python3
"""Decupeaza telefonul din screenshot-urile de store "iPhone 6.9" -> img/<limba>/<nume>.webp.

Screenshot-ul are titlu, fundal deschis si umbre; pe pagina vrem doar telefonul.
Cardul "ridicat" (painea, prima reteta) iese intentionat in afara ramei si trebuie sa ramana asa,
deci masca = silueta telefonului ∪ dreptunghiul rotunjit al cardului.

  - telefonul: pe fiecare rand, primul / ultimul pixel inchis (prinde si butoanele
    laterale); pe randurile acoperite de card se continua laturile drepte;
  - cardul: singura zona deschisa care trece peste rama; marginile si raza colturilor
    se masoara din imagine (raza pe colturile de jos, care sunt albe la toate cardurile).

Utilizare: cut-phone.py "<folderul fridgy finished>" [limbi si/sau nume de imagini...]
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = {'da': 'Danish', 'de': 'German', 'en': 'English', 'fr': 'French',
           'hu': 'Hungarian', 'nl': 'Holland', 'ro': 'Romanian', 'sv': 'Swedish'}
SHOTS = {'fridge': 'iPhone 6.9/iPhone 6.9_ - 2.0.jpg',
         'recipes': 'iPhone 6.9/iPhone 6.9_ - 3.0.jpg',
         'profile': 'iPhone 6.9/iPhone 6.9_ - 5.0.jpg',
         'family': 'iPhone 6.9/iPhone 6.9_ - 8.0.jpg'}

DARK = 90       # sub atat e rama telefonului
WHITE = 246     # cardul ridicat e alb pur; fundalul si ecranul sunt albastrui
INSET = 1.0     # masca intra putin in rama, ca sa nu ramana un fir din fundalul deschis
PHONE_W = 752   # latimea telefonului in celelalte mockup-uri de pe pagina
CORNER = 170    # inaltimea zonei de colt a telefonului, in pixelii sursei
MARGIN = 19     # margine transparenta in stanga / dreapta telefonului, in pixelii sursei
SS = 4          # supraesantionare pentru anti-aliasing


def runs(flags):
    """Cel mai lung sir continuu de True: (inceput, sfarsit)."""
    best, start = (0, -1), None
    for i, f in enumerate(list(flags) + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if i - start > best[1] - best[0] + 1:
                best = (start, i - 1)
            start = None
    return best


def smooth(v):
    pad = np.pad(v, 2, mode='edge')
    return np.median(np.stack([pad[i:i + len(v)] for i in range(5)]), axis=0)


def cut(src, dst):
    a = np.asarray(Image.open(src).convert('RGB'))
    h, w = a.shape[:2]
    lum = (a.astype(int) * (299, 587, 114)).sum(axis=2) // 1000
    dark = lum < DARK
    white = a.min(axis=2) >= WHITE

    # telefonul: laturile drepte sunt pozitia cea mai frecventa a primului / ultimului
    # pixel inchis; de la ele se urca si se coboara prin colturile rotunjite
    has = dark.sum(axis=1) > 40
    f_all = np.where(has, np.argmax(dark, axis=1), -1)
    l_all = np.where(has, w - 1 - np.argmax(dark[:, ::-1], axis=1), -1)
    px0 = int(np.bincount(f_all[has]).argmax())
    px1 = int(np.bincount(l_all[has]).argmax())
    # rand de latura dreapta = rama plina pe ambele parti; literele groase din titlu pot
    # trece testul pe cateva randuri, asa ca se pastreaza doar sirurile lungi
    # (prag mai larg decat DARK: rama are un reflex mai deschis)
    frame = lum < 130
    full = frame[:, px0 + 3:px0 + 15].all(axis=1) & frame[:, px1 - 14:px1 - 2].all(axis=1)
    side = np.nonzero(full)[0]
    breaks = np.nonzero(np.diff(side) > 1)[0]
    chunks = [c for c in np.split(side, breaks + 1) if len(c) >= 100]
    top, bot = int(chunks[0][0]), int(chunks[-1][-1])
    while has[top - 1]:
        top -= 1
    while has[bot + 1]:
        bot += 1
    first = f_all[top:bot + 1].astype(float)
    last = l_all[top:bot + 1].astype(float)

    # colturile din dreapta au un reflex deschis pe muchie, deci "ultimul pixel inchis"
    # le ciupeste; telefonul e simetric, asa ca se oglindesc colturile din stanga
    for zone in (slice(0, CORNER), slice(len(first) - CORNER, len(first))):
        last[zone] = px0 + px1 - first[zone]

    # cardul ridicat: randurile unde rama e acoperita cu deschis, pe oricare latura
    # (textul cardului poate ajunge pana in dreptul ramei, deci golurile mici se unesc)
    over = ((np.median(lum[:, px0 + 5:px0 + 19], axis=1) > 200)
            | (np.median(lum[:, px1 - 18:px1 - 4], axis=1) > 200))
    over[:top + 100] = over[bot - 100:] = False
    rows = np.nonzero(over)[0]
    has_card = len(rows) > 0          # profile / family nu au card care iese din rama
    ct = cb = cx0 = cx1 = radius = 0
    if has_card:
        groups = np.split(rows, np.nonzero(np.diff(rows) > 40)[0] + 1)
        card = max(groups, key=lambda g: g[-1] - g[0])
        ct, cb = int(card[0]), int(card[-1])
        # latimea: coloanele albe din partea de jos a cardului (sus poate fi colorat)
        low = a[cb - 90:cb - 45].min(axis=2)
        col = np.median(low, axis=0) >= WHITE
        cx0, cx1 = px0, px1
        while col[cx0 - 1]:
            cx0 -= 1
        while col[cx1 + 1]:
            cx1 += 1
        # raza: de la marginea de jos, cate randuri pana cand albul ajunge la latura cardului
        reach = np.array([white[y, cx0:cx0 + 3].any() for y in range(cb, cb - 60, -1)])
        radius = min(max(int(np.argmax(reach)) + 1, 8), 40)

    # pe randurile cardului (si ale umbrei lui) rama nu se vede: se continua laturile
    if has_card:
        covered = slice(max(0, ct - top - 8), cb - top + 40)
        first[covered], last[covered] = px0, px1
    first, last = smooth(first) + INSET, smooth(last) + 1 - INSET

    mask = np.zeros((h * SS, w * SS), bool)
    xx = (np.arange(w * SS) + 0.5) / SS
    n = len(first)
    for i in range(int(INSET * SS), n * SS - int(INSET * SS)):
        t = min(i / SS, n - 1)
        k = int(t)
        k2 = min(k + 1, n - 1)
        l = first[k] + (first[k2] - first[k]) * (t - k)
        r = last[k] + (last[k2] - last[k]) * (t - k)
        mask[top * SS + i] = (xx >= l) & (xx < r)

    if has_card:
        yy = (np.arange(h * SS) + 0.5) / SS
        dx = np.maximum(np.maximum(cx0 + radius - xx, xx - (cx1 + 1 - radius)), 0)[None, :]
        dy = np.maximum(np.maximum(ct + radius - yy, yy - (cb + 1 - radius)), 0)[:, None]
        mask |= dx * dx + dy * dy <= radius * radius

    alpha = mask.reshape(h, SS, w, SS).mean(axis=(1, 3))

    # butoanele laterale: masca pe randuri prinde si fire din fundalul deschis la capetele
    # lor; in afara laturilor drepte ramane doar ce e inchis la culoare (cardul e exceptat)
    keep = np.clip((125 - lum) / 40, 0, 1)
    keep[:, px0:px1 + 1] = 1
    if has_card:
        keep[ct - 2:cb + 3] = 1
        # colturile cardului: raza masurata e aproximativa, deci in iesituri se scoate ce are
        # culoarea fundalului (pragul e la jumatatea dintre culoarea cardului si a fundalului)
        low_ch = a.min(axis=2).astype(float)
        span = radius + 10
        for rows, y in ((slice(ct - 2, ct + span), ct + span), (slice(cb - span, cb + 3), cb - span)):
            for cols, inside, outside in ((slice(0, px0), cx0 + 8, cx0 - 14), (slice(px1 + 1, w), cx1 - 8, cx1 + 14)):
                limit = (low_ch[y, inside] + low_ch[y, outside]) / 2
                keep[rows, cols] = np.clip((low_ch[rows, cols] - limit) / 6 + 0.5, 0, 1)
    alpha *= keep

    # butoanele laterale: in sursa sunt o lamela inchisa, despartita de rama printr-un fir
    # din fundalul deschis. Decupate asa, pe pagina inchisa raman aproape invizibile, deci
    # se umplu pana la rama, intr-o singura bucata opaca, in culoarea lamelei.
    a = a.copy()
    for y in range(top + CORNER, bot - CORNER):
        if has_card and ct - 10 <= y <= cb + 45:
            continue
        for x0, x1 in ((int(f_all[y]), px0), (px1 + 1, int(l_all[y]) + 1)):
            if not has[y] or x1 - x0 < 3 or x1 - x0 > 14:
                continue
            seg = slice(x0, x1)
            tone = a[y, seg][lum[y, seg].argmin()]
            a[y, seg] = np.where((lum[y, seg] > 80)[:, None], tone, a[y, seg])
            alpha[y, seg] = 1
            # pixelul de anti-aliasing de pe muchia exterioara a butonului
            edge = x0 - 1 if x1 == px0 else x1
            a[y, edge] = tone
            alpha[y, edge] = np.clip((225 - lum[y, edge]) / 170, 0, 1)
    out = np.dstack([a, np.round(alpha * 255).astype(np.uint8)])
    ys, xs = np.nonzero(alpha > 0)
    # aceeasi margine laterala la toate imaginile (cat iese un card din rama): telefoanele
    # au aceeasi marime pe pagina, iar butoanele nu ajung lipite de marginea imaginii,
    # unde browserul le subtia la redimensionare
    left = min(xs.min(), px0 - MARGIN)
    right = max(xs.max() + 1, px1 + 1 + MARGIN)
    im = Image.fromarray(out).crop((left, ys.min(), right, ys.max() + 1))
    scale = PHONE_W / (px1 - px0 + 1)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    im.save(dst, quality=92, method=6)
    print(f'  {os.path.relpath(dst, ROOT):22} telefon x={px0}..{px1} y={top}..{bot}  '
          + (f'card x={cx0}..{cx1} y={ct}..{cb} r={radius}' if has_card else 'fara card')
          + f'  -> {im.width}x{im.height}')


if len(sys.argv) < 2:
    sys.exit(__doc__)
base = sys.argv[1]
langs = [x for x in sys.argv[2:] if x in FOLDERS] or sorted(FOLDERS)
names = [x for x in sys.argv[2:] if x in SHOTS] or sorted(SHOTS)
for lang in langs:
    for name in names:
        src = os.path.join(base, FOLDERS[lang], SHOTS[name])
        if not os.path.exists(src):
            print(f'  {lang}: lipseste {src}')
            continue
        cut(src, os.path.join(ROOT, 'img', lang, name + '.webp'))
