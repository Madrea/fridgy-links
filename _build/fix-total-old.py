#!/usr/bin/env python3
"""Rescrie eticheta "Total" (netradusa in aplicatie) din telefonul din stanga al pozei 1, la limbile
facute in Figma, direct in pozele finale. Telefonul din stanga are aceeasi geometrie ca la romana,
deci cuvantul se deseneaza in coordonatele capturii si se duce in poza cu omografia din
store-shots-lang.py (scan_H). Pozele se citesc din backup ("_backup Total 2026-11-14"), ca rularile
repetate sa plece de la original.

Utilizare: fix-total-old.py [--check]   --check doar masoara alinierea, nu scrie nimic
"""
import importlib.util
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('sl', os.path.join(HERE, 'store-shots-lang.py'))
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)

WORDS = {'Danish': 'I alt', 'German': 'Gesamt', 'Holland': 'Totaal', 'Hungarian': 'Összesen', 'Swedish': 'Totalt'}
BACKUP = os.path.join(sl.ss.FINISHED, '_backup Total 2026-11-14')
# in pozele din Figma captura e asezata putin altfel decat in scan_H: decalajul lui "Total", masurat prin
# potrivire de sablon in coordonatele capturii (identic la toate limbile vechi si la romana)
SHIFT = {'iphone': (-1, 2), 'android': (10, 6)}
T = sl.TOTAL


def word_layer(word):
    """Captura (1290x2796) cu doar eticheta: (RGB, masca zonei sterse)."""
    layer = Image.new('RGB', (1290, 2796), (255, 255, 255))
    layer = sl.retitle_total(layer, word, os.path.join(HERE, 'fonts'))
    m = Image.new('RGB', (1290, 2796), 0)
    ImageDraw.Draw(m).rectangle(T['erase'], fill=(255, 255, 255))
    return layer, m


def main():
    check = '--check' in sys.argv
    for dev_name, dev in sl.DEVICES.items():
        dx, dy = SHIFT[dev_name]
        H = dev['scan_H'] @ np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], float)
        name = dev['name'].format(n=1)
        ink_total = sl.warp(word_layer('Total')[0], H, (dev['size'])).convert('L')
        for folder, word in WORDS.items():
            src = os.path.join(BACKUP, folder, dev['dir'], name)
            img = Image.open(src).convert('RGB')
            # alinierea: cerneala "Total" prezisa vs cea din poza
            pred = np.asarray(ink_total) < 128
            real = np.asarray(img.convert('L')) < 128
            area = np.asarray(sl.warp(word_layer('Total')[1], H, dev['size']).convert('L')) > 128
            iou = (pred & real & area).sum() / max(((pred | real) & area).sum(), 1)
            print(f'  {dev_name} {folder}: potrivire "Total" {iou:.2f}', end='')
            if check:
                print()
                continue
            layer, m = word_layer(word)
            mask = sl.warp(m, H, dev['size']).convert('L').filter(ImageFilter.GaussianBlur(0.6))
            img.paste(sl.warp(layer, H, dev['size']), (0, 0), mask)
            dst = os.path.join(sl.ss.FINISHED, folder, dev['dir'], name)
            img.save(dst, 'JPEG', quality=98, subsampling=0, optimize=True)
            print(f' -> {word}')


if __name__ == '__main__':
    main()
