#!/usr/bin/env python3
"""Rebranding Fridgy -> Rispy in poza cu notificarea din magazine (iPhone 4, Android 5), toate limbile.

1. Logo-ul mare de pe ecranul intunecat devine rispy-logo.png: aceeasi inaltime si acelasi centru ca
   logo-ul vechi. Ecranul are un filtru care inmulteste culorile (fundalul alb -> gri 177..195, iar
   albastrul logo-ului = fundal x (0.09, 0.51, 1.0)); factorii se masoara pe logo-ul vechi din fiecare
   poza si se aplica la fel pe cel nou, deci iese exact la fel de intunecat. Fundalul de sub logo-ul vechi
   se reface dintr-un polinom de gradul 3 potrivit pe inelul din jur (eroare < 1 nivel de gri).
2. In notificare, titlul "Fridgy" devine "Rispy" (Inter SemiBold, aceeasi inaltime a majusculei si
   aceeasi linie de baza) si iconita devine Rispy-frigider-lapte-portocala.svg.

Pozitiile se detecteaza pe fiecare poza (engleza e putin deplasata, la greaca cardul e mai inalt).
Originalele se citesc din `_backup Notif 2026-11-17/`, deci scriptul se poate rula de mai multe ori.

Utilizare: rebrand-notify.py <icon.png randat din svg, 1024x1024 RGBA> [Limba ...]
  (svg-ul se randeaza cu Chrome headless; ImageMagick deseneaza contururi negre false)
"""
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as nd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINISHED = '/mnt/c/Users/User/OneDrive/Documente/fridgy finished'
BACKUP = os.path.join(FINISHED, '_backup Notif 2026-11-17')
FONT = os.path.join(ROOT, '_build', 'fonts', 'Inter-SemiBold.ttf')

DEVICES = {
    'iphone': {
        'dir': 'iPhone 6.9', 'file': 'iPhone 6.9_ - 4.0.jpg',
        'screen': (260, 1000, 1030, 2060),  # zona ecranului cu logo-ul, deasupra notificarii
        'blur': 1.1,
        'notif': (250, 2000, 380, 2400),    # unde se cauta iconita mica
        'tile_off': (-18, -15, 18, 18),     # cadrul iconitei fata de desenul albastru din ea (masurat pe ro)
        'title_x': (366, 520),
    },
    'android': {
        'dir': 'Android Phone', 'file': 'Android Phone - 5.0.jpg',
        'screen': (262, 720, 815, 1440),
        'blur': 0.7,
        'notif': (250, 1400, 345, 1700),
        'tile_off': (-14, -11, 13, 12),
        'title_x': (338, 470),
    },
}

LOGO = Image.open(os.path.join(ROOT, 'rispy-logo.png')).convert('RGBA')
LOGO_A = LOGO.getchannel('A').crop(LOGO.getchannel('A').getbbox())


def poly(y, x):
    y, x = y / 1000, x / 1000
    return np.stack([np.ones_like(x), x, y, x * x, y * y, x * y, y ** 3, x ** 3, x * x * y, x * y * y], -1)


def swap_logo(a, d):
    x0, y0, x1, y1 = d['screen']
    s = a[y0:y1, x0:x1].astype(float)
    m = (s[:, :, 2] - s[:, :, 0]) > 25
    ys, xs = np.nonzero(m)
    top, bot, left, right = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1

    ring = nd.binary_dilation(m, iterations=70) & ~nd.binary_dilation(m, iterations=10)
    yy, xx = np.mgrid[0:s.shape[0], 0:s.shape[1]].astype(float)
    P = poly(yy, xx)
    bg = np.empty_like(s)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(P[ring], s[:, :, c][ring], rcond=None)
        bg[:, :, c] = P @ coef

    core = nd.binary_erosion((s[:, :, 2] - s[:, :, 0]) > 100, iterations=3)
    k = np.median(s[core] / bg[core], axis=0)

    # logo-ul vechi dispare: zona lui (plus 6px) se umple cu fundalul refacut, cu tranzitie de 2px
    hole = nd.binary_dilation(m, iterations=6).astype(float)
    hole = np.clip(nd.gaussian_filter(hole, 1.0) * 1.5, 0, 1)[..., None]
    base = s * (1 - hole) + bg * hole

    # logo-ul nou: aceeasi inaltime, acelasi centru
    H = bot - top
    sc = H / LOGO_A.height
    W = LOGO_A.width * sc
    cx, cy = (left + right) / 2, (top + bot) / 2
    ox, oy = cx - W / 2, cy - H / 2
    # bicubic pe micsorare face aliere; randam la 4x si micsoram
    big = LOGO_A.transform(
        (s.shape[1] * 4, s.shape[0] * 4), Image.AFFINE,
        (1 / (sc * 4), 0, -ox / sc, 0, 1 / (sc * 4), -oy / sc), Image.BICUBIC)
    alpha = big.resize((s.shape[1], s.shape[0]), Image.LANCZOS).filter(ImageFilter.GaussianBlur(d['blur']))
    al = (np.asarray(alpha).astype(float) / 255)[..., None]

    out = base * (1 - al) + bg * k * al
    a[y0:y1, x0:x1] = np.clip(np.round(out), 0, 255).astype(np.uint8)
    return {'old': (left + x0, top + y0, right + x0, bot + y0), 'new_w': round(W, 1), 'k': np.round(k, 3)}


def swap_notification(img, a, d, icon):
    x0, y0, x1, y1 = d['notif']
    s = a[y0:y1, x0:x1].astype(int)
    ys, xs = np.nonzero((s[:, :, 2] - s[:, :, 0]) > 60)
    g = (xs.min() + x0, ys.min() + y0, xs.max() + x0, ys.max() + y0)
    o = d['tile_off']
    tile = (g[0] + o[0], g[1] + o[1], g[2] + o[2], g[3] + o[3])

    # titlul: primul grup de randuri cu text inchis deasupra iconitei
    tx0, tx1 = d['title_x']
    gray = a[:, :, :3].min(2).astype(int)
    win = gray[tile[1] - 75:tile[1] + 4, tx0:tx1] < 150
    rows = np.nonzero(win.any(1))[0]
    run = [rows[0]]
    for r in rows[1:]:
        if r - run[-1] > 1:
            break
        run.append(r)
    t_top, t_bot = run[0] + tile[1] - 75, run[-1] + tile[1] - 75
    cols = np.nonzero((gray[t_top:t_bot + 1, tx0:tx1] < 150).any(0))[0]
    t_left, t_right = cols.min() + tx0, cols.max() + tx0
    # majuscula F: coloanele tulpinii dau inaltimea si linia de baza
    stem = np.nonzero((gray[t_top:t_bot + 1, t_left:t_left + 3] < 120).any(1))[0]
    cap_top, base_y = stem.min() + t_top, stem.max() + t_top + 1

    out = img
    dr = ImageDraw.Draw(out)
    dr.rectangle((t_left - 3, t_top - 3, t_right + 3, t_bot + 1), fill=(255, 255, 255))
    dr.rectangle((tile[0] - 2, tile[1] - 2, tile[2] + 2, tile[3] + 2), fill=(255, 255, 255))

    # iconita: cat cadrul vechi pe latime, proportiile svg-ului pastrate, centrata
    ib = icon.crop(icon.getbbox())
    tw = tile[2] - tile[0] + 1
    th = tile[3] - tile[1] + 1
    sc = min(tw / ib.width, th / ib.height)
    iw, ih = round(ib.width * sc), round(ib.height * sc)
    small = ib.resize((iw, ih), Image.LANCZOS)
    out.paste(small, (tile[0] + (tw - iw) // 2, tile[1] + (th - ih) // 2), small)

    # titlul "Rispy": aceeasi inaltime a majusculei si aceeasi linie de baza
    cap = base_y - cap_top
    size = cap / 0.727
    k = 4
    f = ImageFont.truetype(FONT, round(size * k))
    word = 'Rispy'
    bbox = f.getbbox(word, anchor='ls')
    Wc, Hc = 400, 100
    mk = Image.new('L', (Wc * k, Hc * k), 0)
    ImageDraw.Draw(mk).text((-bbox[0], 70 * k), word, font=f, fill=255, anchor='ls')
    # titlul original e gri foarte inchis (~16..34) si putin moale, nu negru curat
    mk = mk.resize((Wc, Hc), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.4))
    out.paste((20, 20, 20), (t_left, base_y - 70), mk)
    return {'tile': tile, 'title': (t_left, cap_top, base_y), 'size': round(size, 1)}


def main():
    icon = Image.open(sys.argv[1]).convert('RGBA')
    langs = sys.argv[2:] or sorted(
        l for l in os.listdir(FINISHED)
        if os.path.isdir(os.path.join(FINISHED, l, 'iPhone 6.9')) and not l.startswith('_'))
    for lang in langs:
        for name, d in DEVICES.items():
            dst = os.path.join(FINISHED, lang, d['dir'], d['file'])
            src = os.path.join(BACKUP, lang, d['dir'], d['file'])
            if not os.path.exists(src):
                os.makedirs(os.path.dirname(src), exist_ok=True)
                shutil.copy2(dst, src)
            img = Image.open(src).convert('RGB')
            a = np.array(img)
            info = swap_logo(a, d)
            img = Image.fromarray(a)
            info.update(swap_notification(img, np.asarray(img), d, icon))
            img.save(dst, 'JPEG', quality=98, subsampling=0, optimize=True)
            print(lang.ljust(11), name.ljust(7), info)


if __name__ == '__main__':
    main()
