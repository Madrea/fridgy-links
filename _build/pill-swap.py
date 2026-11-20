#!/usr/bin/env python3
"""Pastila noua din header ("Personal" etc.) in pozele de magazin: iPhone 2 si 9, Android 2 si 4.

Pastila noua e un strat alb semi-transparent (umplutura ~18%, textul si iconita 100%) peste gradientul
header-ului. Pe captura noua (pilulafrigider/IMG_*.png, 1290x2796) se reface gradientul de sub ea
(polinom de gradul 3 pe inelul din jur, eroare ~0.4) si de aici iese opacitatea fiecarui pixel. In poza
de magazin, pastila veche (alba) se sterge cu gradientul refacut acolo, iar stratul nou se pune deasupra,
la scara si pozitia ecranului: aceeasi transformare captura -> telefon ca in store-shots.py /
store-shots-android.py (verificata pe titlul "Frigider": < 1px).

Originalele se citesc din `_backup Pilula 2026-11-17/`, deci scriptul se poate rula de mai multe ori.

Utilizare: pill-swap.py [Limba ...]   (implicit: toate cele 24)
"""
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

FINISHED = '/mnt/c/Users/User/OneDrive/Documente/fridgy finished'
SRC_DIR = os.path.join(FINISHED, 'pilulafrigider')
BACKUP = os.path.join(FINISHED, '_backup Pilula 2026-11-17')

SRC = {  # limba -> captura noua (limba recunoscuta dupa textul din ecran)
    'Romanian': 4064, 'English': 4065, 'German': 4066, 'French': 4067, 'Hungarian': 4068, 'Holland': 4069,
    'Danish': 4070, 'Swedish': 4071, 'Spanish': 4072, 'Italian': 4073, 'Polish': 4074, 'Portuguese': 4075,
    'Czech': 4076, 'Greek': 4077, 'Finnish': 4078, 'Slovak': 4079, 'Bulgarian': 4080, 'Croatian': 4081,
    'Slovenian': 4082, 'Lithuanian': 4083, 'Latvian': 4084, 'Estonian': 4085, 'Irish': 4086, 'Maltese': 4087,
}

# captura 1290px -> poza de magazin: x' = DX + K*x, y' = DY + K*y
_S = 1778 / 1512
_K_IP = 0.749 * _S * 945 / 1290
_A = 576 / 899
DEVICES = {
    'iphone': {'dir': 'iPhone 6.9', 'files': ['iPhone 6.9_ - 2.0.jpg', 'iPhone 6.9_ - 9.0.jpg'],
               'K': _K_IP, 'DX': 232 - 40 * _S + 40.6 * _S, 'DY': 827 - 23 * _S - 0.6 * _S,
               'screen_x1': 1050},
    'android': {'dir': 'Android Phone', 'files': ['Android Phone - 2.0.jpg', 'Android Phone - 4.0.jpg'],
                'K': _A * 945 / 1290, 'DX': 252 - 22.5 * _A, 'DY': 653 - 201 * _A,
                'screen_x1': 826},
}


def poly(y, x):
    y, x = y / 100, x / 100
    return np.stack([np.ones_like(x), x, y, x * x, y * y, x * y, x ** 3, y ** 3, x * x * y, x * y * y], -1)


def fit_bg(s, ring):
    yy, xx = np.mgrid[0:s.shape[0], 0:s.shape[1]].astype(float)
    P = poly(yy, xx)
    bg = np.empty(s.shape, float)
    res = []
    for c in range(3):
        coef, *_ = np.linalg.lstsq(P[ring], s[:, :, c][ring], rcond=None)
        bg[:, :, c] = P @ coef
        res.append((s[:, :, c][ring] - bg[:, :, c][ring]).std())
    return bg, max(res)


def gradient_px(s):
    """Pixelii de gradient albastru (nu text alb, nu insula/rama, nici marginile lor amestecate)."""
    g = (s[:, :, 2] - s[:, :, 0]) > 60
    return g & ~nd.binary_dilation(~g, iterations=4)


def pill_layer(path):
    """Opacitatea pastilei noi (float 0..1) si cutia ei in captura."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    x0, y0, x1, y1 = 640, 150, 1290, 420
    s = a[y0:y1, x0:x1]
    # pastila: zona mai deschisa decat gradientul din dreapta titlului; o gasim relativ la randul de sus
    guess = np.zeros(s.shape[:2], bool)
    rough = s.mean(2) - s[5].mean(1)[None, :]
    lab, n = nd.label(nd.binary_opening(rough > 12, iterations=2))
    k = np.argmax(nd.sum(np.ones_like(rough), lab, range(1, n + 1))) + 1
    guess = nd.binary_fill_holes(lab == k)
    ring = ~nd.binary_dilation(guess, iterations=6) & gradient_px(s)
    ring[:, -12:] = False
    bg, res = fit_bg(s, ring)
    al = np.clip(((s - bg) / (255 - bg)).mean(2), 0, 1)
    al[~nd.binary_dilation(guess, iterations=4)] = 0
    ys, xs = np.nonzero(al > 0.02)
    box = (xs.min() - 3, ys.min() - 3, xs.max() + 4, ys.max() + 4)
    A = al[box[1]:box[3], box[0]:box[2]]
    return A, (box[0] + x0, box[1] + y0), res


def place(A, origin, d, size):
    """Stratul de opacitate dus in poza de magazin (supraesantionat 4x, apoi micsorat)."""
    W, H = size
    k = 4
    img = Image.fromarray(np.round(A * 65535).astype(np.uint16).astype(np.int32), 'I').convert('F')
    ox = d['DX'] + d['K'] * origin[0]
    oy = d['DY'] + d['K'] * origin[1]
    sc = d['K'] * k
    big = img.transform((W * k, H * k), Image.AFFINE, (1 / sc, 0, -ox * k / sc, 0, 1 / sc, -oy * k / sc),
                        Image.BICUBIC)
    small = np.asarray(big, dtype=np.float32).reshape(H, k, W, k).mean((1, 3)) / 65535
    return np.clip(small, 0, 1)


def swap(img, A, origin, d):
    a = np.asarray(img).astype(float)
    H, W = a.shape[:2]
    al = place(A, origin, d, (W, H))
    ys, xs = np.nonzero(al > 0.003)
    new_box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)

    # pastila veche: componenta alba din zona pastilei noi
    cx0, cy0, cx1, cy1 = new_box[0] - 40, new_box[1] - 30, new_box[2] + 10, new_box[3] + 30
    s = a[cy0:cy1, cx0:cx1]
    white = s.min(2) > 225
    lab, n = nd.label(white)
    k = np.argmax(nd.sum(white, lab, range(1, n + 1))) + 1
    old_full = np.zeros((H, W), bool)
    old_full[cy0:cy1, cx0:cx1] = nd.binary_fill_holes(lab == k)
    oys, oxs = np.nonzero(old_full)
    old_box = (oxs.min(), oys.min(), oxs.max() + 1, oys.max() + 1)

    # zona de lucru: ambele pastile + margine; gradientul se potriveste pe inelul din jur
    m = 45
    x0 = min(old_box[0], new_box[0]) - m
    y0 = min(old_box[1], new_box[1]) - m
    x1 = min(max(old_box[2], new_box[2]) + m, d['screen_x1'])
    y1 = max(old_box[3], new_box[3]) + m
    s = a[y0:y1, x0:x1]
    oldm = old_full[y0:y1, x0:x1]
    hole = nd.binary_dilation(oldm, iterations=5)  # pastila veche + umbra/anti-aliasing
    ring = ~nd.binary_dilation(oldm, iterations=10) & gradient_px(s)
    bg, res = fit_bg(s, ring)

    feather = np.clip(nd.gaussian_filter(hole.astype(float), 1.2) * 1.6, 0, 1)[..., None]
    base = s * (1 - feather) + bg * feather
    A2 = al[y0:y1, x0:x1][..., None]
    out = base * (1 - A2) + 255 * A2
    a[y0:y1, x0:x1] = out
    return Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8)), {
        'old': old_box, 'new': new_box, 'bg_err': round(res, 2)}


def main():
    langs = sys.argv[1:] or list(SRC)
    for lang in langs:
        A, origin, res = pill_layer(os.path.join(SRC_DIR, f'IMG_{SRC[lang]}.png'))
        for name, d in DEVICES.items():
            for f in d['files']:
                dst = os.path.join(FINISHED, lang, d['dir'], f)
                src = os.path.join(BACKUP, lang, d['dir'], f)
                if not os.path.exists(src):
                    os.makedirs(os.path.dirname(src), exist_ok=True)
                    shutil.copy2(dst, src)
                out, info = swap(Image.open(src).convert('RGB'), A, origin, d)
                out.save(dst, 'JPEG', quality=98, subsampling=0, optimize=True)
                print(lang.ljust(11), f.ljust(24), 'src bg err', round(res, 2), info)


if __name__ == '__main__':
    main()
