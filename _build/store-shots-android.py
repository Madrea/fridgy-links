#!/usr/bin/env python3
"""Reface pozele de Google Play "Android Phone" (1080x1920), cu telefonul Android existent.
Fisierele finale: 1 scanare, 2 frigider, 3 retete, 4 lista, 5 notificari, 6 statistici, 7 buget,
8 familie, 9 obiceiuri, 10 risipa. Play permite 8 la upload, proprietarul alege; 9 si 10 sunt
vechile 6 si 7, legate intre ele. Vechea 4 devine 5, vechea 5 devine 6.

Foloseste compunerea din store-shots.py, cu geometria Android, masurata pe poza 8:
ecranul (246,541)-(830,1819), raza ~50, camera (524,552)-(551,579). Latimea cardurilor
ridicate e cea din pozele Android vechi: 680px (paine, reteta) si 576px (statistici).

Utilizare: store-shots-android.py --fonts <dir> --out <dir> [--langs ro,en] [--shots 2,3,4,6,7]
"""
import argparse
import importlib.util
import os
import shutil

from PIL import Image, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('store_shots', os.path.join(HERE, 'store-shots.py'))
ss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ss)
sm, fm, rm, pm = ss.sm, ss.fm, ss.rm, ss.pm

BACKUP = os.path.join(ss.FINISHED, '_backup Android 2026-11-02')
# Masurat pe poza Android veche cu frigiderul: cardurile din lista sunt la x 252..828, iar
# pastila "Personal" e centrata la y=653. Pe captura, cardul e la x 22.5..921.5 si pastila la y=201.
A = 576 / 899
UNIT = A / sm.SCALE       # 1 px de mockup de site, in pixeli Android
CONTENT_X, CONTENT_Y = 252 - 22.5 * A, 653 - 201 * A  # coltul capturii, in poza Android

# store-shots.py lucreaza in "pixeli de mockup"; aici acestia sunt chiar pixelii Android
ss.W, ss.H = 1080, 1920
ss.SCREEN = (246, 541, 830, 1819)
ss.S, ss.OX, ss.OY = 1, 0, 0
ss.R_IN, ss.R_ISL = 50, 14
ss.ISLAND = (524, 552, 551, 579)
ss.SCALE, ss.DX, ss.DY = A, CONTENT_X, CONTENT_Y
ss.HEADER_H, ss.FADE_Y = 500, 470
ss.TITLE_Y, ss.SUB_Y, ss.TEXT_CX, ss.MAX_TEXT_W = (163, 267), (376, 448), 539.5, 965
TITLE_SIZE, SUB_SIZE = 88, 56  # calibrate pe poza 8
CX = 540


def src_path(folder, n):
    bak = os.path.join(BACKUP, folder, f'Android Phone - {n}.0.jpg')
    return bak if os.path.exists(bak) else os.path.join(ss.FINISHED, folder, 'Android Phone', f'Android Phone - {n}.0.jpg')


ss.src_path = src_path


def y_of(sy):
    return CONTENT_Y + A * sy


def shadow(dy, blur, op):
    return dy * UNIT, blur * UNIT, op


def build(slot, lang, plate, clean, fonts):
    folder = ss.FOLDERS[lang]
    if slot == 2:
        src = ss.shot_file('fridgy fridge screenshots', fm.SHOTS[lang], '2026-10-30')
        k = 680 / (fm.CARD[2] - fm.CARD[0])
        mid = y_of((fm.ABOVE + fm.BELOW) / 2) + fm.LIFT_DY * UNIT
        out = ss.lift(ss.phone(plate, src), src, fm.CARD, fm.R_CARD, k, mid - k * (fm.CARD[3] - fm.CARD[1]) / 2,
                      shadow(fm.SH_DY, fm.SH_BLUR, fm.SH_OP), CX)
        orig = 2
    elif slot == 3:
        src = ss.shot_file('fridgy recipes screenshots', rm.SHOTS[lang], '2026-10-30')
        y0 = rm.card_top(src)
        k = 680 / (rm.X1 - rm.X0)
        out = ss.lift(ss.phone(plate, src), src, (rm.X0, y0, rm.X1, y0 + rm.HEIGHT), rm.R_CARD, k,
                      y_of(y0) - rm.RAISE * UNIT, shadow(*rm.SHADOW), CX)
        orig = 3
    elif slot == 6:
        src = os.path.join(ss.DOCS, 'fridgy profile screenshots', pm.SHOTS[lang] + '.jpeg')
        k = 576 / (pm.CARD[2] - pm.CARD[0])
        top = y_of((pm.TOP - sm.DY) / sm.SCALE)
        out = ss.lift(ss.phone(plate, src, pm.DIM), src, pm.CARD, pm.R_CARD, k, top, shadow(*pm.SHADOW), CX, pm.WHITE_FROM)
        orig = 5
    elif slot == 4:
        out = ss.phone(plate, ss.shot_file('fridgy shopping list screenshots', sm.SHOTS[lang]))
        orig = None
    elif slot == 7:
        bg = os.path.join(ss.DOCS, 'fridgy profile screenshots', pm.SHOTS[lang] + '.jpeg')
        card = ss.shot_file('fridgy budget screenshots', ss.BUDGET_SHOTS[lang])
        k = 680 / (ss.BUDGET_CARD[2] - ss.BUDGET_CARD[0])
        out = ss.lift(ss.phone(plate, bg, pm.DIM), card, ss.BUDGET_CARD, ss.BUDGET_R, k,
                      y_of((ss.BUDGET_TOP - sm.DY) / sm.SCALE), shadow(fm.SH_DY, fm.SH_BLUR, fm.SH_OP), CX)
        orig = None
    else:
        raise ValueError(slot)
    if orig:
        o = Image.open(src_path(folder, orig)).convert('RGB')
        out.paste(o.crop((0, 0, ss.W, ss.HEADER_H)), (0, 0))
    else:
        text = ss.TEXT[9 if slot == 4 else 10][lang]
        out.paste(ss.header(clean, out, text, fonts).crop((0, 0, ss.W, ss.HEADER_H)), (0, 0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--langs', default=','.join(ss.FOLDERS))
    ap.add_argument('--shots', default='2,3,4,6,7')
    a = ap.parse_args()
    shots = [int(v) for v in a.shots.split(',')]
    fonts = (ImageFont.truetype(os.path.join(a.fonts, 'Poppins-Bold.ttf'), TITLE_SIZE),
             ImageFont.truetype(os.path.join(a.fonts, 'Poppins-Medium.ttf'), SUB_SIZE))
    clean = ss.clean_header() if set(shots) & {4, 7} else None
    for lang in a.langs.split(','):
        folder = ss.FOLDERS[lang]
        plate = Image.open(src_path(folder, 8)).convert('RGB')
        dst = os.path.join(a.out, folder)
        os.makedirs(dst, exist_ok=True)
        for slot in shots:
            out = build(slot, lang, plate, clean, fonts)
            path = os.path.join(dst, f'Android Phone - {slot}.0.jpg')
            out.save(path, 'JPEG', quality=98, subsampling=0, optimize=True)
            print(' ', lang, slot, out.size, os.path.getsize(path) // 1024, 'KB')
        shutil.copy2(src_path(folder, 4), os.path.join(dst, 'Android Phone - 5.0.jpg'))
        # obiceiurile si risipa raman la alegerea proprietarului (Play permite doar 8 la upload)
        shutil.copy2(src_path(folder, 6), os.path.join(dst, 'Android Phone - 9.0.jpg'))
        shutil.copy2(src_path(folder, 7), os.path.join(dst, 'Android Phone - 10.0.jpg'))


if __name__ == '__main__':
    main()
