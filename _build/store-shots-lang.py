#!/usr/bin/env python3
"""Pozele de magazin pentru o limba noua, pe iPhone ("iPhone 6.9", 1290x2796) si pe Android
("Android Phone", 1080x1920), pornind de la pozele romanesti si de la capturile de ecran ale
limbii noi (1290x2796, PNG de pe iPhone).

Fiecare poza arata un ecran: scan, fridge, recipes, notify, stats, habits, waste, family, list,
budget. Ordinea difera: iPhone 1..10 = scan fridge recipes notify stats habits waste family list
budget; Android 1..10 = scan fridge recipes list notify stats budget family habits waste.

Ecranele cu telefonul drept (fridge, recipes, stats, family, list, budget) se fac cu functiile din
store-shots.py, respectiv store-shots-android.py (aceeasi rama, aceleasi carduri ridicate), iar
antetul se redeseneaza peste fundalul curat.

notify: poza romaneasca (ecranul nu are text), cu mesajul si ora din notificare rescrise.

scan, habits, waste vin din Figma: se pastreaza poza romaneasca si se inlocuieste doar continutul
ecranelor si textul.
  scan    telefonul din stanga (ecranul de dupa scanare), rotit in perspectiva; silueta telefonului
          din dreapta se scade din masca, altfel ecranul nou intra in coltul ramei lui. Telefonul
          din dreapta primeste captura Previzualizare a limbii (fisierul WhatsApp din folder), dar
          fotografia bonului si miniatura raman cele romanesti, asa a cerut proprietarul.
  habits, waste  doua telefoane inclinate, cate unul in fiecare poza, iar fiecare intra cu un colt
          in poza vecina (cadrele stau la GAP unul de altul).
Omografiile: marginile ecranului masurate pe ramele romanesti (drepte potrivite pe tranzitia
rama/ecran), iar dreptunghiul din captura care cade pe ecran (RECT) e calibrat cu SIFT pe
iconitele categoriilor (eroare 0.4px pe iPhone, 0.35px pe Android).

Masca ecranului se ia din poza romaneasca: zona luminoasa marginita de rama intunecata, cu
gaurile umplute, fara Dynamic Island / camera si fara ce acopera ecranul.

Fontul: Poppins nu are chirilice, asa ca pentru bg se foloseste Montserrat (aceeasi familie
geometrica), la aceeasi marime: inaltimea majusculelor e practic aceeasi (700 vs 702/1000).

Utilizare: store-shots-lang.py --lang bg --device iphone|android --fonts <dir> [--shots 1,2,...]
  [--out <dir>]  implicit <fridgy finished>/<Limba>/<iPhone 6.9 | Android Phone>; cu --out: <dir>/<Limba>/
Textele sunt in store-texts.py; capturile limbii se iau din <fridgy finished>/<Limba>/, sortate (RAW_ORDER).
"""
import argparse
import importlib.util
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ss = load('store_shots', 'store-shots.py')          # geometria iPhone
sa = load('store_shots_android', 'store-shots-android.py')  # are propriul store-shots, cu geometria Android
sm, fm, rm, pm = ss.sm, ss.fm, ss.rm, ss.pm
SS = 2

TEXTS = load('store_texts', 'store-texts.py').TEXTS
FOLDERS = {'bg': 'Bulgarian', 'es': 'Spanish', 'it': 'Italian', 'pl': 'Polish', 'pt': 'Portuguese', 'cs': 'Czech',
           'el': 'Greek', 'fi': 'Finnish', 'sk': 'Slovak', 'hr': 'Croatian', 'sl': 'Slovenian', 'lt': 'Lithuanian',
           'lv': 'Latvian', 'et': 'Estonian', 'ga': 'Irish', 'mt': 'Maltese'}
# Poppins nu are chirilice si greaca; la malteza ii lipseste doar ħ, care se deseneaza din h + bara (SYNTH)
FONTS = {'bg': ('Montserrat-Bold.ttf', 'Montserrat-Medium.ttf', 1.0),
         'el': ('Commissioner-Bold.ttf', 'Commissioner-Medium.ttf', 1.0)}  # instante wght 756 / 538 = grosimea Poppins Bold / Medium
POPPINS = ('Poppins-Bold.ttf', 'Poppins-Medium.ttf', 1.0)
SYNTH = {'ħ': 'h', 'Ħ': 'H'}
# capturile limbii, sortate dupa nume, sunt in aceasta ordine (asa le-a facut proprietarul pentru toate limbile)
RAW_ORDER = ['scan', 'fridge', 'list', 'stats', 'habits', 'waste', 'family', 'recipes', 'budget']


def lang_config(code):
    folder = FOLDERS[code]
    raw = os.path.join(ss.FINISHED, folder)
    files = sorted(f for f in os.listdir(raw) if f.lower().endswith(('.png', '.jpg', '.jpeg')))
    preview = [f for f in files if f.lower().startswith('whatsapp')]   # ecranul Previzualizare, pentru scan
    files = [f for f in files if f not in preview]
    if len(files) != len(RAW_ORDER):
        raise ValueError(f'{folder}: {len(files)} capturi, astept {len(RAW_ORDER)}')
    t = TEXTS[code]
    shots = dict(zip(RAW_ORDER, files))
    if len(preview) == 1:
        shots['preview'] = preview[0]
    return {'folder': folder, 'font': FONTS.get(code, POPPINS), 'shots': shots,
            'text': {k: v for k, v in t.items() if not k.startswith('notify_')},
            'notify_msg': t['notify_msg'], 'notify_now': t['notify_now'], 'notify_font': 'Inter-Regular.ttf',
            'scan_total': t.get('scan_total')}


def M(rows):
    return np.array(rows, float)


DEVICES = {
    'iphone': {
        'size': (1290, 2796), 'dir': 'iPhone 6.9', 'name': 'iPhone 6.9_ - {n}.0.jpg', 'mod': ss,
        'order': ['scan', 'fridge', 'recipes', 'notify', 'stats', 'habits', 'waste', 'family', 'list', 'budget'],
        'cx': 645, 'max_w': 1170,
        # (marime titlu, randuri), (marime subtitlu, randuri), masurate pe pozele romanesti
        'layout': {'*': ((104, (219, 348)), (66, (483, 571))),
                   'habits': ((95, (214, 342)), (66, (483, 571))),
                   'waste': ((100, (2303, 2431)), (66, (2567, 2655)))},
        'text_boxes': {'scan': [(0, 110, 1290, 620)], 'habits': [(0, 110, 1290, 620)],
                       'waste': [(150, 1950, 1290, 2345), (0, 2345, 1290, 2720)]},
        'rect': (6.0, 32.07, 1284.32, 2794.31),
        # telefonul din stanga de la scan: marginile ecranului x=107.5 / 668.7, sus (107.5,1140.5)-(668.6,1161.2),
        # jos (107.5,2543.4)-(668.7,2621.5)
        'scan_H': M([[0.418267577, -9.256e-06, 104.959323779], [-0.019611338, 0.507525987, 1124.176751921],
                     [-3.0769e-05, -9.4e-08, 1.0]]),
        'scan_seed': (330, 1640), 'scan_box': (100, 1132, 676, 2630),
        # telefonul din dreapta: marginea stanga, doua puncte pe marginea de jos, raza coltului
        'scan_back': (567, (800, 2218), (1000, 2189), 80),
        # telefonul din dreapta (Previzualizare): omografia din rama (acelasi RECT), verificata prin suprapunere
        # pe bara de sus, chenarul fotografiei, miniaturi si butoane; zonele (in coordonatele capturii) unde
        # raman pixelii romanesti: fotografia bonului si miniatura "Poza 1" (reuniunea chenarelor vechi si noi)
        'preview_H': M([[0.476358505, -4.7e-08, 618.262425362], [0.008333172, 0.528453142, 744.551331531],
                        [3.2344e-05, 0.0, 1.0]]),
        'preview_seed': (1150, 1900), 'preview_keep': [(85, 452, 1205, 1940), (339, 1979, 632, 2371)],
        'habits_H': M([[0.569925096, 0.207052218, 30.243513867], [-0.090504769, 0.426902139, 1004.116926888],
                       [2.2465e-05, -3.3813e-05, 1.0]]),
        'waste_H': M([[0.526237936, -0.242955672, 525.066280883], [0.102325302, 0.435777183, 226.119315211],
                      [-2.1605e-05, -3.2888e-05, 1.0]]),
        'habits_seed': (450, 1700), 'waste_seed': (600, 1000),
        # bucata telefonului vecin: deplasarea fata de cadrul lui si un punct din ecranul ei
        'waste_in_habits': ((1331, 0), (1285, 1500)), 'habits_in_waste': ((-1330, 0), (4, 2150)),
        # notificarea (masurata pe poza romaneasca): marimea textului (latimea randului 2 = 541px),
        # x-ul randului 1 (dupa emoji) si al celorlalte, liniile de baza, marginea dreapta ("acum"),
        # "acum": marime, linie de baza; zonele care se albesc
        'notify': {'size': 28.5, 'x1': 424, 'x': 374, 'base': (2244.5, 2281, 2317.5), 'right': 1009,
                   'now_size': 25, 'now_base': 2210.5,
                   'erase': [(940, 2190, 1015, 2217), (418, 2219, 1015, 2258), (368, 2258, 1015, 2326)],
                   # pentru un rand in plus: banda cardului (cu umbra) de la `top` la `split` urca un rand,
                   # iar iconita (271,2217)-(347,2293) urca o jumatate de rand, ca sa ramana centrata
                   'grow': {'x': (222, 1068), 'top': 2118, 'split': 2256, 'dy': 36.5, 'icon': (268, 2214, 351, 2297)}},
    },
    'android': {
        'size': (1080, 1920), 'dir': 'Android Phone', 'name': 'Android Phone - {n}.0.jpg', 'mod': sa.ss,
        'order': ['scan', 'fridge', 'recipes', 'list', 'notify', 'stats', 'budget', 'family', 'habits', 'waste'],
        'cx': 540, 'max_w': 1000,
        'layout': {'*': ((88, (163, 267)), (56, (376, 448))),
                   'habits': ((72, (157, 261)), (56, (376, 448))),
                   'waste': ((88, (1539, 1643)), (56, (1752, 1824)))},
        'text_boxes': {'scan': [(0, 70, 1080, 480)], 'habits': [(0, 70, 1080, 480)],
                       'waste': [(60, 1440, 1080, 1690), (0, 1690, 1080, 1860)]},
        'rect': (29.08, 36.04, 1262.28, 2767.04),
        # marginile ecranului: x=173.5 / 563, sus (173.5,689.6)-(563,656.6), jos (173.5,1791)-(561.6,1824)
        'scan_H': M([[0.289658938, 0.000226748, 164.840452532], [-0.056822171, 0.405145139, 675.716664512],
                     [-4.584e-05, 1.307e-06, 1.0]]),
        'scan_seed': (230, 1300), 'scan_box': (168, 650, 568, 1830),
        'scan_back': (480, (650, 1706), (800, 1693), 55),
        'preview_H': M([[0.358608906, 0.0, 508.309745807], [0.055044919, 0.427929104, 520.18757756],
                        [4.8999e-05, 0.0, 1.0]]),
        'preview_seed': (700, 1660), 'preview_keep': [(88, 452, 1201, 1942), (340, 1979, 633, 2375)],
        'habits_H': M([[0.356117487, 0.239795263, 114.048102724], [-0.19199072, 0.389695417, 778.603517052],
                       [3.017e-05, 6.186e-06, 1.0]]),
        'waste_H': M([[0.312674094, -0.224638873, 487.794821546], [0.197313411, 0.372413952, 74.681080343],
                      [-2.8996e-05, 5.889e-06, 1.0]]),
        'habits_seed': (590, 1207), 'waste_seed': (376, 805),
        'waste_in_habits': ((1121, -1), (1075, 1050)), 'habits_in_waste': ((-1121, 1), (5, 1480)),
        'notify': {'size': 20.5, 'x1': 380, 'x': 345, 'base': (1570.5, 1597, 1623.5), 'right': 802,
                   'now_size': 18, 'now_base': 1546.5,
                   'erase': [(752, 1532, 807, 1551), (377, 1552, 812, 1580), (341, 1580, 812, 1629)],
                   'grow': {'x': (232, 848), 'top': 1484, 'split': 1579, 'dy': 26.5, 'icon': (268, 1548, 329, 1609)}},
    },
}


def shift(Mx, d):
    return np.array([[1, 0, d[0]], [0, 1, d[1]], [0, 0, 1]], float) @ Mx


def native(img):
    """Capturile au 1290x2796; una mai mica (aceeasi proportie) se mareste."""
    return img if img.size == (1290, 2796) else img.resize((1290, 2796), Image.LANCZOS)


def strip_native(img):
    """sm.strip_status_bar pe captura nativa: se aplica la 945x2048, iar banda refacuta se mareste."""
    small = img.resize((945, 2048), Image.LANCZOS)
    a = np.asarray(small)
    b = sm.strip_status_bar(a)
    changed = (np.abs(b.astype(int) - a.astype(int)).sum(2) > 0)
    if not changed.any():
        return img
    rows = 210
    fix = Image.fromarray(b[:rows]).resize((img.width, round(rows * img.width / 945)), Image.LANCZOS)
    m = Image.fromarray((changed[:rows] * 255).astype(np.uint8)).resize(fix.size, Image.BILINEAR)
    m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
    out = img.copy()
    out.paste(fix, (0, 0), m)
    return out


def warp(src, Mx, size):
    """src (captura nativa) dusa prin omografia Mx; se micsoreaza intai cu LANCZOS, ca textul sa nu se zimtuiasca."""
    J = Mx[:2, :2] / Mx[2, 2]
    s = float(np.sqrt(abs(np.linalg.det(J - np.outer(Mx[:2, 2], Mx[2, :2])))))
    s = min(1.0, max(s, 0.2))
    pre = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
    inv = np.linalg.inv(Mx @ np.diag([1 / s, 1 / s, 1]))
    inv = inv / inv[2, 2]
    return pre.transform(size, Image.PERSPECTIVE, tuple(inv.ravel()[:8]), Image.BICUBIC)


def screen_mask(base, seed, Mx, grey=100, limit=None):
    """Ecranul vizibil din poza romaneasca: luminos (sau colorat), marginit de rama, fara insula/camera.
    `grey` ridicat opreste umplerea si la rama gri (titan) a altui telefon; `limit` = dreptunghiul
    in care poate fi ecranul."""
    a = np.asarray(base).astype(int)
    lum = (a * (299, 587, 114)).sum(2) // 1000
    sat = a.max(2) - a.min(2)
    barrier = (lum < grey) & (sat < 35)
    if limit is not None:
        x0, y0, x1, y1 = limit
        outside = np.ones_like(barrier)
        outside[y0:y1, x0:x1] = False
        barrier |= outside
    light = ~barrier
    light[[0, -1], :] = False
    light[:, [0, -1]] = False
    lab, _ = ndi.label(light)
    m = lab == lab[seed[1], seed[0]]
    m = ndi.binary_closing(m, np.ones((5, 5)))
    filled = ndi.binary_fill_holes(m)
    # insula / camera: gaura din partea de sus, la mijloc; restul gaurilor (text inchis la culoare) raman ecran
    holes = filled & ~m
    lab, n = ndi.label(holes)
    inv = np.linalg.inv(Mx)
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        if (lab[sl] == i).sum() < 120:
            continue
        cy, cx = ndi.center_of_mass(lab == i)
        p = inv @ (cx, cy, 1)
        u, v = p[0] / p[2], p[1] / p[2]
        if 300 < u < 990 and v < 260:
            filled &= ~ndi.binary_dilation(lab == i, iterations=2)
    return Image.fromarray((filled * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))


def back_mask(size, back):
    """Telefonul din dreapta de la scan: ce e la dreapta marginii lui si deasupra marginii de jos."""
    W, H = size
    xl, (ax, ay), (bx, by), r = back
    k = (by - ay) / (bx - ax)
    yb = lambda x: ay + k * (x - ax)
    cx = xl + r
    cy = yb(cx) - r * np.hypot(1, k)
    pts = [(xl, 0), (W, 0), (W, yb(W))]
    for t in np.linspace(0, 1, 40):
        ang = np.arctan2(1, -k) * (1 - t) + np.pi * t
        pts.append((cx + r * np.cos(ang), cy + r * np.sin(ang)))
    m = Image.new('L', (W * SS, H * SS), 0)
    ImageDraw.Draw(m).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    return m.resize((W, H), Image.LANCZOS)


def swap_screen(base, ref, shot, Mx, seed, occluder=None, **kw):
    """Continutul ecranului din `ref` (poza romaneasca) inlocuit cu captura `shot`, peste `base`."""
    mask = screen_mask(ref, seed, Mx, **kw)
    if occluder is not None:
        mask = Image.fromarray((np.asarray(mask, float) * (1 - np.asarray(occluder, float) / 255)).astype(np.uint8))
    out = base.copy()
    out.paste(warp(shot, Mx, base.size), (0, 0), mask)
    return out


def clean_text(img, boxes):
    """Sterge textul din `boxes`: pixelii de text se refac din fundalul din jur (un gradient lin)."""
    a = np.asarray(img).astype(np.float32)
    text = np.zeros(a.shape[:2], bool)
    ink = (a.max(2) < 170) | ((a[..., 2] - a[..., 0] > 50) & (a[..., 2] > 160))
    for x0, y0, x1, y1 in boxes:
        text[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
    text = ndi.binary_dilation(text, iterations=7)
    w = (~text).astype(np.float32)
    num = np.stack([ndi.gaussian_filter(a[..., c] * w, 28) for c in range(3)], 2)
    den = ndi.gaussian_filter(w, 28)[..., None]
    bg = num / np.maximum(den, 1e-3)
    soft = np.clip(ndi.gaussian_filter(text.astype(np.float32), 2)[..., None] * 1.6, 0, 1)
    return Image.fromarray((a * (1 - soft) + bg * soft).clip(0, 255).round().astype(np.uint8))


def synth_bar(font, ch):
    """Bara lui ħ peste h (fata de originea literei, la marimea `font`), proportionala cu tulpina."""
    m = font.getmask(ch)
    a = np.array(m).reshape(m.size[1], m.size[0])
    stem = np.nonzero((a[:int(a.shape[0] * 0.35)] > 128).all(0))[0]
    x0 = font.getbbox(ch, anchor='ls')[0]
    top = font.getbbox(ch, anchor='ls')[1]
    E = font.size
    t = 0.7 * (stem.max() - stem.min() + 1)
    return x0 + stem.min() - 0.03 * E, top + 0.08 * E, x0 + stem.max() + 0.16 * E, top + 0.08 * E + t


def draw_line(canvas, line, font, baseline, cx, max_w):
    W = canvas.width
    marked = line
    for c, base in SYNTH.items():
        line = line.replace(c, base) if font.getmask(c).size == font.getmask('\uffff').size else line
    plain = line.replace('*', '')
    width = font.getlength(plain)
    if width > max_w:
        raise ValueError(f'rand prea lat ({width:.0f}px): {plain}')
    k = 4
    big = font.font_variant(size=font.size * k)
    mask_ink, mask_blue = (Image.new('L', (W * k, 220 * k), 0) for _ in range(2))
    x0 = (cx + 0.5) * k - big.getlength(plain) / 2
    pos = 0
    orig = marked.replace('*', '')
    for i, seg in enumerate(line.split('*')):
        if seg:
            x = x0 + big.getlength(plain[:pos + len(seg)]) - big.getlength(seg)
            d = ImageDraw.Draw(mask_blue if i % 2 else mask_ink)
            d.text((x, 160 * k), seg, font=big, fill=255, anchor='ls')
            for j in range(len(seg)):
                if orig[pos + j] != plain[pos + j]:      # litera sintetizata: h + bara
                    hx = x0 + big.getlength(plain[:pos + j])
                    bx0, by0, bx1, by1 = synth_bar(big, plain[pos + j])
                    d.rectangle((hx + bx0, 160 * k + by0, hx + bx1, 160 * k + by1), fill=255)
            pos += len(seg)
    for mask, color in ((mask_ink, ss.INK), (mask_blue, ss.BLUE)):
        canvas.paste(color, (0, baseline - 160), mask.resize((W, 220), Image.LANCZOS))


def draw_text(canvas, dev, key, text, fonts):
    (ts, ty), (us, uy) = dev['layout'].get(key, dev['layout']['*'])
    bold, medium, scale = fonts[:3]
    title, sub = text
    for line, y in zip(title, ty):
        draw_line(canvas, line, bold.font_variant(size=round(ts * scale)), y, dev['cx'], dev['max_w'])
    for line, y in zip(sub, uy):
        draw_line(canvas, line, medium.font_variant(size=round(us * scale)), y, dev['cx'], dev['max_w'])


def header(clean, out, mod):
    """Antetul fara text, ca store-shots.header: fundalul reconstruit, topit spre cel al pozei sub FADE_Y."""
    fade = np.ones((mod.HEADER_H, out.width), np.float32) * 255
    fade[mod.FADE_Y:] = np.linspace(255, 0, mod.HEADER_H - mod.FADE_Y)[:, None]
    out = out.copy()
    out.paste(clean, (0, 0), Image.fromarray(fade.astype(np.uint8)))
    return out


def straight_iphone(key, plate, src, path):
    if key == 'fridge':
        mid = sm.SCALE * (fm.ABOVE + fm.BELOW) / 2 + sm.DY + fm.LIFT_DY
        top = mid - fm.K * (fm.CARD[3] - fm.CARD[1]) / 2
        return ss.lift(ss.phone(plate, src), src, fm.CARD, fm.R_CARD, fm.K, top, (fm.SH_DY, fm.SH_BLUR, fm.SH_OP))
    if key == 'recipes':
        y0 = rm.card_top(src)
        top = sm.SCALE * y0 + sm.DY - rm.RAISE
        return ss.lift(ss.phone(plate, src), src, (rm.X0, y0, rm.X1, y0 + rm.HEIGHT), rm.R_CARD, rm.K, top,
                       rm.SHADOW, rm.CX)
    if key == 'stats':
        return ss.lift(ss.phone(plate, src, pm.DIM), src, pm.CARD, pm.R_CARD, pm.K, pm.TOP, pm.SHADOW, pm.CX,
                       pm.WHITE_FROM)
    if key in ('family', 'list'):
        return ss.phone(plate, src)
    if key == 'budget':
        return ss.lift(ss.phone(plate, path('stats'), pm.DIM), src, ss.BUDGET_CARD, ss.BUDGET_R, ss.BUDGET_K,
                       ss.BUDGET_TOP, (fm.SH_DY, fm.SH_BLUR, fm.SH_OP))
    raise ValueError(key)


def straight_android(key, plate, src, path):
    a = sa.ss
    if key == 'fridge':
        k = 680 / (fm.CARD[2] - fm.CARD[0])
        mid = sa.y_of((fm.ABOVE + fm.BELOW) / 2) + fm.LIFT_DY * sa.UNIT
        return a.lift(a.phone(plate, src), src, fm.CARD, fm.R_CARD, k, mid - k * (fm.CARD[3] - fm.CARD[1]) / 2,
                      sa.shadow(fm.SH_DY, fm.SH_BLUR, fm.SH_OP), sa.CX)
    if key == 'recipes':
        y0 = rm.card_top(src)
        k = 680 / (rm.X1 - rm.X0)
        return a.lift(a.phone(plate, src), src, (rm.X0, y0, rm.X1, y0 + rm.HEIGHT), rm.R_CARD, k,
                      sa.y_of(y0) - rm.RAISE * sa.UNIT, sa.shadow(*rm.SHADOW), sa.CX)
    if key == 'stats':
        k = 576 / (pm.CARD[2] - pm.CARD[0])
        top = sa.y_of((pm.TOP - sm.DY) / sm.SCALE)
        return a.lift(a.phone(plate, src, pm.DIM), src, pm.CARD, pm.R_CARD, k, top, sa.shadow(*pm.SHADOW), sa.CX,
                      pm.WHITE_FROM)
    if key in ('family', 'list'):
        return a.phone(plate, src)
    if key == 'budget':
        k = 680 / (a.BUDGET_CARD[2] - a.BUDGET_CARD[0])
        return a.lift(a.phone(plate, path('stats'), pm.DIM), src, a.BUDGET_CARD, a.BUDGET_R, k,
                      sa.y_of((a.BUDGET_TOP - sm.DY) / sm.SCALE), sa.shadow(fm.SH_DY, fm.SH_BLUR, fm.SH_OP), sa.CX)
    raise ValueError(key)


def wrap(msg, f, n):
    lines, cur = [], ''
    for w in msg.split():
        start = n['x1'] if not lines else n['x']
        c = (cur + ' ' + w).strip()
        if f.getlength(c) <= n['right'] - start or not cur:
            cur = c
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def grow_card(img, g, rows):
    """Cardul notificarii, mai inalt cu `rows` randuri: partea de sus urca, iconita ramane centrata."""
    out = img.copy()
    dy = round(g['dy'] * rows)
    x0, x1 = g['x']
    icon = out.crop(g['icon'])
    ImageDraw.Draw(out).rectangle(g['icon'], fill=(255, 255, 255))
    band = out.crop((x0, g['top'], x1, g['split']))
    out.paste(band, (x0, g['top'] - dy))
    filler = out.crop((x0, g['split'], x1, g['split'] + 1)).resize((x1 - x0, dy))  # un rand alb al cardului, cu marginile
    out.paste(filler, (x0, g['split'] - dy))
    out.paste(icon, (g['icon'][0], g['icon'][1] - round(dy / 2)))
    return out, dy


def notification(img, n, msg, now, font_path):
    """Rescrie mesajul si ora din notificare, cu aceleasi pozitii; emoji-ul de la inceput ramane.
    Daca mesajul nu incape in 3 randuri, cardul creste in sus (ca bannerul din iOS)."""
    f = ImageFont.truetype(font_path, n['size'])
    lines = wrap(msg, f, n)
    extra = max(0, len(lines) - len(n['base']))
    if extra > 1:
        raise ValueError(f'mesajul are {len(lines)} randuri')
    out, dy = grow_card(img, n['grow'], extra) if extra else (img.copy(), 0)
    shift = lambda box, i: (box[0], box[1] - dy, box[2], box[3] - dy) if i < 2 else box
    d = ImageDraw.Draw(out)
    for i, box in enumerate(n['erase']):
        d.rectangle(shift(box, i), fill=(255, 255, 255))
    base = list(n['base'])
    if extra:
        base = [base[0] - n['grow']['dy']] + base
    k = 4
    W, H = out.size

    def text(x, b, s, size, color, right=False):
        big = ImageFont.truetype(font_path, size * k)
        if right:
            x = x - big.getlength(s) / k
        top = int(b) - 60
        m = Image.new('L', (W * k, 80 * k), 0)
        ImageDraw.Draw(m).text((x * k, (b - top) * k), s, font=big, fill=255, anchor='ls')
        out.paste(color, (0, top), m.resize((W, 80), Image.LANCZOS))

    for i, line in enumerate(lines):
        text(n['x1'] if i == 0 else n['x'], base[i], line, n['size'], (0, 0, 0))
    text(n['right'], n['now_base'] - dy, now, n['now_size'], (118, 118, 118), right=True)
    return out


# eticheta "Total" din captura de scanare (1290x2796): incepe la x=62, linia de baza y=2486, SF semibold
# ~14pt; Inter wght 650 / opsz 14 la 41.5px are aceeasi latime, inaltime si grosime
TOTAL = {'x': 62, 'base': 2486, 'size': 41.5, 'erase': (55, 2445, 600, 2495), 'font': 'Inter-SemiBold.ttf'}


def retitle_total(img, word, fonts_dir):
    out = img.copy()
    ImageDraw.Draw(out).rectangle(TOTAL['erase'], fill=(255, 255, 255))
    k = 4
    big = ImageFont.truetype(os.path.join(fonts_dir, TOTAL['font']), TOTAL['size'] * k)
    m = Image.new('L', (600 * k, 80 * k), 0)
    ImageDraw.Draw(m).text(((TOTAL['x'] - 50) * k - big.getbbox(word, anchor='ls')[0], 60 * k), word, font=big,
                           fill=255, anchor='ls')
    out.paste((0, 0, 0), (50, TOTAL['base'] - 60), m.resize((600, 80), Image.LANCZOS))
    return out


def build(key, dev, cfg, plate, clean, fonts, raw):
    path = lambda k: os.path.join(raw, cfg['shots'][k])
    ro = lambda k: Image.open(os.path.join(ss.FINISHED, 'Romanian', dev['dir'],
                                           dev['name'].format(n=dev['order'].index(k) + 1))).convert('RGB')
    shot = lambda k: strip_native(native(Image.open(path(k)).convert('RGB')))
    if key == 'notify':
        dev_name = 'iphone' if dev['mod'] is ss else 'android'
        out = notification(ro('notify'), dev['notify'], cfg['notify_msg'], cfg['notify_now'],
                           os.path.join(fonts[3], cfg['notify_font']))
        out = header(clean, out, dev['mod'])
        draw_text(out, dev, key, cfg['text'][key][dev_name], fonts)
        return out
    if key == 'scan':
        base = ro('scan')
        scan = shot('scan')
        if cfg.get('scan_total'):
            scan = retitle_total(scan, cfg['scan_total'], fonts[3])
        out = swap_screen(base, base, scan, dev['scan_H'], dev['scan_seed'], grey=175,
                          limit=dev['scan_box'], occluder=back_mask(base.size, dev['scan_back']))
        if 'preview' in cfg['shots']:
            # telefonul din dreapta: ecranul nou, dar fotografia bonului si miniatura raman cele romanesti
            out = swap_screen(out, base, shot('preview'), dev['preview_H'], dev['preview_seed'])
            m = Image.new('RGB', (1290, 2796), 0)
            for box in dev['preview_keep']:
                ImageDraw.Draw(m).rectangle(box, fill=(255, 255, 255))
            keep = warp(m, dev['preview_H'], base.size).convert('L')
            out.paste(base, (0, 0), keep.filter(ImageFilter.GaussianBlur(0.6)))
    elif key in ('habits', 'waste'):
        other = 'waste' if key == 'habits' else 'habits'
        base = ro(key)
        out = swap_screen(base, base, shot(key), dev[key + '_H'], dev[key + '_seed'])
        d, seed = dev[f'{other}_in_{key}']
        out = swap_screen(out, base, shot(other), shift(dev[other + '_H'], d), seed)
    else:
        straight = straight_iphone if dev['mod'] is ss else straight_android
        out = straight(key, plate, path(key), path)
        out = header(clean, out, dev['mod'])
        draw_text(out, dev, key, cfg['text'][key], fonts)
        return out
    out = clean_text(out, dev['text_boxes'][key])
    draw_text(out, dev, key, cfg['text'][key], fonts)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', required=True, help='un cod sau mai multe separate prin virgula, ex. bg,es')
    ap.add_argument('--device', default='iphone', choices=DEVICES)
    ap.add_argument('--fonts', required=True)
    ap.add_argument('--out')
    ap.add_argument('--shots', help='numerele pozelor in ordinea dispozitivului, ex. 1,2,3')
    a = ap.parse_args()
    dev = DEVICES[a.device]
    mod = dev['mod']
    plate = Image.open(mod.src_path('Romanian', 8)).convert('RGB')
    clean = mod.clean_header()
    for code in a.lang.split(','):
        cfg = lang_config(code)
        bold, medium, scale = cfg['font']
        fonts = (ImageFont.truetype(os.path.join(a.fonts, bold), 100),
                 ImageFont.truetype(os.path.join(a.fonts, medium), 66), scale, a.fonts)
        raw = os.path.join(ss.FINISHED, cfg['folder'])
        dst = os.path.join(a.out, cfg['folder']) if a.out else os.path.join(raw, dev['dir'])
        os.makedirs(dst, exist_ok=True)
        nums = [int(v) for v in a.shots.split(',')] if a.shots else range(1, 11)
        for n in nums:
            key = dev['order'][n - 1]
            out = build(key, dev, cfg, plate, clean, fonts, raw)
            p = os.path.join(dst, dev['name'].format(n=n))
            out.save(p, 'JPEG', quality=98, subsampling=0, optimize=True)
            print(' ', code, a.device, n, key, os.path.getsize(p) // 1024, 'KB')


if __name__ == '__main__':
    main()
