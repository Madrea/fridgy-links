#!/usr/bin/env python3
"""Iconita noua de langa "Salut" (frigiderul alb care saluta) in ecranul de profil: iPhone 5 si 10,
Android 6 si 7 (acolo ecranul e intunecat, pm.DIM).

Iconita se ia din fridgy finished/new_profile_icon.png (captura romaneasca 1290x2796): e alba peste
gradientul header-ului; gradientul de sub ea se reface (polinom pe inelul din jur) si de aici iese
opacitatea fiecarui pixel. Pozitia: aceeasi distanta fata de capatul din dreapta al salutului ca in
captura si aceeasi inaltime, cu transformarea captura -> telefon din pill-swap.py. In alte limbi salutul
are alta latime, asa ca marginea lui dreapta se masoara in fiecare poza.

Iconita veche (albastra, cu contur) se sterge cu gradientul refacut; textul nou se pune ca alb inmultit
cu intunecarea ecranului, adica in culoarea literelor salutului din aceeasi poza.

Originalele: `_backup Hello 2026-11-19/`; scriptul se poate rula de mai multe ori.
Utilizare: hello-icon.py [Limba ...]   (implicit: Romanian)
"""
import importlib.util
import os
import shutil
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ps = load('pill_swap', 'pill-swap.py')
FINISHED = ps.FINISHED
SRC = os.path.join(FINISHED, 'new_profile_icon.png')
BACKUP = os.path.join(FINISHED, '_backup Hello 2026-11-19')
FILES = {'iphone': ['iPhone 6.9_ - 5.0.jpg', 'iPhone 6.9_ - 10.0.jpg'],
         'android': ['Android Phone - 6.0.jpg', 'Android Phone - 7.0.jpg']}

# in captura: banda salutului si a iconitei, zona de cautare a iconitei
BAND_Y = (215, 335)
ICON_BOX = (330, 215, 460, 335)


def header_px(s):
    """Pixelii de gradient (albastru, nu text alb, nu Dynamic Island / rama)."""
    lum = s.mean(2)
    return ((s[:, :, 2] - s[:, :, 0]) > 50) & (lum > 50) & (s.min(2) < 200)


def icon_layer():
    a = np.asarray(Image.open(SRC).convert('RGB')).astype(float)
    x0, y0, x1, y1 = ICON_BOX
    s = a[y0:y1, x0:x1]
    white = s.min(2) > 200
    lab, n = nd.label(nd.binary_dilation(white, iterations=4))
    k = np.argmax(nd.sum(white, lab, range(1, n + 1))) + 1
    shape = nd.binary_fill_holes(lab == k)
    ring = ~nd.binary_dilation(shape, iterations=4) & header_px(s)
    bg, err = ps.fit_bg(s, ring)
    al = np.clip(((s - bg) / (255 - bg)).mean(2), 0, 1)
    al[~nd.binary_dilation(shape, iterations=2)] = 0
    ys, xs = np.nonzero(al > 0.02)
    bx0, by0, bx1, by1 = xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3
    # capatul din dreapta al salutului, in captura
    band = a[BAND_Y[0]:BAND_Y[1], 0:x0]
    cols = np.nonzero((band.min(2) > 215).any(0))[0]
    greet_r = cols.max()
    return al[by0:by1, bx0:bx1], (x0 + bx0, y0 + by0), greet_r, bg, err


def greet_right(a, d):
    """Capatul din dreapta al salutului (text gri-alb) in poza de magazin si culoarea literelor.
    Salutul poate avea mai multe cuvinte ("Dia duit"), deci se ia ultimul text dinaintea iconitei vechi
    (prima coloana cu pixeli colorati care ies din gradient)."""
    y0 = int(d['DY'] + d['K'] * (BAND_Y[0] + 15))
    y1 = int(d['DY'] + d['K'] * (BAND_Y[1] - 25))
    x0 = int(d['DX'] + d['K'] * 40)
    x1 = int(d['DX'] + d['K'] * 760)
    s = a[y0:y1, x0:x1]
    lum = s.mean(2)
    dev = lum - np.median(lum, 1, keepdims=True)
    grey = np.abs(s[:, :, 2] - s[:, :, 0]) < 25
    text = (dev > 45) & grey
    hp = header_px(s)
    bg, _ = ps.fit_bg(s, hp & ~nd.binary_dilation(text, iterations=3))
    colored = s.mean(2) < bg.mean(2) - 20   # umplutura albastra a iconitei vechi e mai inchisa decat gradientul; textul e mai deschis
    first = np.nonzero(text.sum(0) >= 2)[0][0]
    icon_cols = np.nonzero(colored[:, first:].sum(0) >= 3)[0] + first
    icon_x = icon_cols[0]
    cols = np.nonzero(text[:, :icon_x].sum(0) >= 2)[0]
    gr = cols.max()
    t = s[:, first:gr + 1][text[:, first:gr + 1]]
    core = t[t.mean(1) >= np.percentile(t.mean(1), 80)].mean(0)   # culoarea literelor (alb x intunecare)
    return x0 + gr, core


def swap(img, layer, d):
    A, origin, greet_r_cap, cap_bg = layer
    a = np.asarray(img).astype(float)
    K, DX, DY = d['K'], d['DX'], d['DY']
    gr, white = greet_right(a, d)
    # pozitia iconitei: aceeasi distanta fata de salut ca in captura
    ox = gr + K * (origin[0] - greet_r_cap)
    oy = DY + K * origin[1]
    # zona de lucru: iconita veche + noua
    wx0 = int(gr + 4)
    wx1 = int(DX + K * 720)
    wy0 = int(DY + K * 205)
    wy1 = int(DY + K * 345)
    s = a[wy0:wy1, wx0:wx1]
    hp = header_px(s)
    bg0, _ = ps.fit_bg(s, hp & nd.binary_erosion(hp, iterations=2))
    old = (np.abs(s - bg0).max(2) > 14) | ~hp
    # doar componenta veche (cea mai mare abatere, in afara de rama/island de sus)
    lab, n = nd.label(nd.binary_closing(old, iterations=2))
    sizes = nd.sum(old, lab, range(1, n + 1))
    k = np.argmax(sizes) + 1
    oldm = nd.binary_fill_holes(lab == k)
    # nu atingem Dynamic Island / rama (intunecate)
    dark = s.mean(2) < 60
    dl, dn = nd.label(dark)   # doar ce atinge marginea de sus (insula/rama), nu pixelii intunecati ai iconitei
    dark = np.isin(dl, [v for v in np.unique(dl[0]) if v])
    oldm &= ~nd.binary_dilation(dark, iterations=2)
    hole = nd.binary_dilation(oldm, iterations=3)
    ring = ~nd.binary_dilation(oldm, iterations=5) & hp
    bg, err = ps.fit_bg(s, ring)
    feather = np.clip(nd.gaussian_filter(hole.astype(float), 1.0) * 1.6, 0, 1)[..., None]
    base = s * (1 - feather) + bg * feather
    # stratul nou, in coordonatele zonei de lucru
    al = ps.place(A, (0, 0), {'K': K, 'DX': ox - wx0, 'DY': oy - wy0}, (wx1 - wx0, wy1 - wy0))[..., None]
    out = base * (1 - al) + white * al
    a[wy0:wy1, wx0:wx1] = out
    oys, oxs = np.nonzero(oldm)
    nys, nxs = np.nonzero(al[..., 0] > 0.05)
    info = {'greet_r': gr, 'old': (wx0 + oxs.min(), wy0 + oys.min(), wx0 + oxs.max(), wy0 + oys.max()),
            'new': (wx0 + nxs.min(), wy0 + nys.min(), wx0 + nxs.max(), wy0 + nys.max()), 'bg_err': round(err, 2),
            'white': tuple(np.round(white).astype(int))}
    return Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8)), info


def main():
    langs = sys.argv[1:] or ['Romanian']
    A, origin, greet_r_cap, _, err = icon_layer()
    print('captura: iconita', origin, A.shape, 'salut pana la x', greet_r_cap, 'err', round(err, 2))
    for lang in langs:
        for name, d in ps.DEVICES.items():
            for f in FILES[name]:
                dst = os.path.join(FINISHED, lang, d['dir'], f)
                src = os.path.join(BACKUP, lang, d['dir'], f)
                if not os.path.exists(src):
                    os.makedirs(os.path.dirname(src), exist_ok=True)
                    shutil.copy2(dst, src)
                img = Image.open(src).convert('RGB')
                out, info = swap(img, (A, origin, greet_r_cap, None), d)
                out.save(dst, 'JPEG', quality=98, subsampling=0, optimize=True)
                print(lang.ljust(11), f.ljust(24), info)


if __name__ == '__main__':
    main()
