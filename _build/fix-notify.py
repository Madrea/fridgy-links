#!/usr/bin/env python3
"""Reface mockup-ul de notificare.

Exportul original taia notificarea: iconita aplicatiei era lipita de marginea
din stanga (jumatate din patratul ei lipsea), iar cardul alb iesea in afara
panzei si in stanga si in dreapta, deci nu se vedea ca un card.

Pentru fiecare limba:
  1. citeste exportul din _build/img-original/<lang>/notify.webp;
  2. masoara cardul alb si patratul iconitei (dupa conturul lui subtire);
  3. reconstruieste cardul alb si il taie cu margini egale pe ambele capete;
  4. redeseneaza conturul iconitei in zona nou adaugata;
  5. lipeste exportul peste si rotunjeste colturile panzei.
"""
import math
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_build', 'img-original')
DST = os.path.join(ROOT, 'img')
LANGS = ['ro', 'de', 'fr', 'nl', 'sv', 'da', 'hu', 'en']
GEOM_LANG = 'de'        # exportul dupa care se masoara geometria (vezi geometry())

PAD = 140               # spatiu de lucru adaugat pe fiecare parte
MARGIN = 38             # marginea finala, egala in stanga si in dreapta
CARD_R = 26             # raza colturilor cardului de notificare
BORDER = 234            # luminanta conturului iconitei
CLEAN_X = 500           # coloana fara continut, de unde luam culoarea randului


def load(path):
    out = subprocess.run(['convert', path, '-depth', '8', 'rgba:-'],
                         capture_output=True, check=True).stdout
    w, h = subprocess.run(['identify', '-format', '%w %h', path],
                          capture_output=True, text=True).stdout.split()
    return bytearray(out), int(w), int(h)


def save(buf, w, h, path):
    subprocess.run(['convert', '-size', f'{w}x{h}', '-depth', '8', 'rgba:-',
                    '-quality', '90', path], input=bytes(buf), check=True)


def rrect_sdf(x, y, x0, y0, x1, y1, r):
    """Distanta cu semn fata de un dreptunghi rotunjit (negativ = inauntru)."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    qx = abs(x - cx) - (x1 - x0) / 2 + r
    qy = abs(y - cy) - (y1 - y0) / 2 + r
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r


def geometry(lang, band=None):
    """Cardul alb si patratul iconitei, masurate pe un export.

    band forteaza randurile cardului in loc sa le masoare: exportul englezesc e
    taiat dintr-un JPG si pragul de alb cade cu un rand-doua mai sus din cauza
    compresiei, ceea ce ar da un card mai scund decat la celelalte limbi.
    """
    raw, W, H = load(os.path.join(SRC, lang, 'notify.webp'))

    def px(x, y):
        i = (y * W + x) * 4
        return raw[i], raw[i + 1], raw[i + 2], raw[i + 3]

    if band is None:
        # cardul alb, pe o coloana fara continut
        white = [y for y in range(H) if px(CLEAN_X, y)[0] > 250]
        band = white[0], white[-1]
    top, bot = band

    # patratul iconitei: minimele de luminanta pe conturul lui
    mid_y = (top + bot) // 2
    t_right = min(range(40, 90), key=lambda x: px(x, mid_y)[0])
    inner_x = max(10, t_right - 26)
    t_top = min(range(top + 45, top + 70), key=lambda y: px(inner_x, y)[0])
    t_bot = min(range(bot - 65, bot - 40), key=lambda y: px(inner_x, y)[0])
    return top, bot, t_right, t_top, t_bot


def fix(lang, geom, anchor, width=None):
    raw, W, H = load(os.path.join(SRC, lang, 'notify.webp'))
    top, bot, t_right, t_top, t_bot = geom

    t_w = t_bot - t_top                       # iconita e patrata
    t_left = t_right - t_w + PAD
    t_right += PAD
    tile_r = round(t_w * 0.225)

    # panza noua: exact cardul de notificare, restul transparent
    NW, NH = W + 2 * PAD, bot - top + 1
    dy = -top                                 # decalajul exportului pe verticala
    t_top += dy
    t_bot += dy
    out = bytearray(b'\xff\xff\xff\x00' * (NW * NH))

    # 1. cardul alb, deocamdata dreptunghiular (se rotunjeste dupa taiere)
    for i in range(3, len(out), 4):
        out[i] = 255

    # 2. conturul iconitei (partea din dreapta e acoperita la pasul 3 de export)
    for y in range(t_top - 3, t_bot + 4):
        for x in range(t_left - 3, t_right + 4):
            d = rrect_sdf(x + .5, y + .5, t_left, t_top, t_right, t_bot, tile_r)
            a = max(0.0, min(1.0, 1.35 - abs(d)))
            if a <= 0:
                continue
            i = (y * NW + x) * 4
            for c in range(3):
                out[i + c] = round(BORDER * a + out[i + c] * (1 - a))

    # 3. continutul exportului (doar randurile cardului), peste alb
    for y in range(top, bot + 1):
        for x in range(W):
            i = (y * W + x) * 4
            a = raw[i + 3] / 255
            if a == 0:
                continue
            j = ((y + dy) * NW + x + PAD) * 4
            for c in range(3):
                out[j + c] = round(raw[i + c] * a + out[j + c] * (1 - a))

    # 4. taiem simetric: aceeasi margine langa iconita si langa ora
    def content(x, y):
        i = (y * NW + x) * 4
        return out[i + 3] == 255 and out[i] < 225

    x0 = anchor - MARGIN
    if width is None:
        right = max(x for x in range(NW) if any(content(x, y) for y in range(NH)))
        width = right + MARGIN - x0 + 1
    FW = width
    fin = bytearray(FW * NH * 4)
    for y in range(NH):
        src = (y * NW + x0) * 4
        fin[y * FW * 4:(y + 1) * FW * 4] = out[src:src + FW * 4]

    # 5. colturile rotunjite ale cardului
    for y in range(NH):
        for x in range(FW):
            a = max(0.0, min(1.0, .5 - rrect_sdf(x + .5, y + .5, 0, 0,
                                                 FW - 1, NH - 1, CARD_R)))
            fin[(y * FW + x) * 4 + 3] = round(255 * a)

    save(fin, FW, NH, os.path.join(DST, lang, 'notify.webp'))
    print(f'{lang}: {W}x{H} -> {FW}x{NH} (margini {MARGIN}px)')
    return FW


# banda cardului si marginea din stanga se iau de la un export curat, ca toate
# limbile sa iasa pe aceeasi panza; iconita se masoara pe fiecare export in parte,
# fiindca in exportul englezesc continutul cardului e mutat cu cativa pixeli.
ref = geometry(GEOM_LANG)
band, anchor = (ref[0], ref[1]), ref[2] - (ref[4] - ref[3]) + PAD
width = fix(GEOM_LANG, ref, anchor)
for lang in LANGS:
    if lang != GEOM_LANG and os.path.exists(os.path.join(SRC, lang, 'notify.webp')):
        fix(lang, geometry(lang, band), anchor, width)
