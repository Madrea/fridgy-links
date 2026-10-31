#!/usr/bin/env python3
"""Reface img/<limba>/recipes.webp din screenshot-urile cu retetele: ecranul intra in rama
ca la shopping-mockups.py, iar prima reteta se ridica peste lista, ca in mockup-ul initial.

Marimea s-a masurat pe vechiul recipes.webp (ro), potrivind titlul, etichetele, descrierea
si "Vezi reteta" din screenshot-ul nou peste cardul ridicat: toate cad exact cu 0.904 px de
mockup per px de screenshot 945x2048 (1.207x fata de restul ecranului), centrat la x=391.
Cardul nou are poza in loc de emoji si e mai inalt, asa ca nu mai incape la aceeasi
inaltime (ar acoperi titlul ecranului): sta cu 30px mai sus decat locul lui din lista,
sub filtrele Usor / Mediu / Dificil, si creste in jos. Umbra e masurata tot pe vechiul
mockup: masca coborata 8px, blur 10, opacitate 0.14.

Utilizare: recipes-mockups.py ["<folderul cu screenshot-uri>"] [limba=sufix ...]
"""
import importlib.util
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('fm', os.path.join(ROOT, '_build', 'fridge-mockups.py'))
fm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)

FOLDER = '/mnt/c/Users/User/OneDrive/Documente/fridgy recipes screenshots'
SHOTS = {
    'sv': '22.22.03 (1)', 'ro': '22.22.03', 'nl': '22.22.04 (1)', 'hu': '22.22.04 (2)',
    'de': '22.22.04 (3)', 'fr': '22.22.04 (4)', 'en': '22.22.04 (5)', 'da': '22.22.04',
}
X0, X1, HEIGHT, R_CARD = 35, 909.5, 807.5, 33  # prima reteta, in screenshot-ul 945x2048
K, CX, RAISE = 0.904, 391, 30
SHADOW = (8, 10, 0.14)


def card_top(path):
    """Unde incepe poza primei retete (in germana header-ul are un rand in plus)."""
    a = np.asarray(Image.open(path).convert('L').resize((945, 2048), Image.LANCZOS)).astype(int)
    y = next(y for y in range(530, 900) if a[y, 472] < 230)
    return y - 0.5


if __name__ == '__main__':
    folder = sys.argv[1] if len(sys.argv) > 1 and '=' not in sys.argv[1] else FOLDER
    shots = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a) or SHOTS
    for lang, suf in shots.items():
        src = os.path.join(folder, f'WhatsApp Image 2026-10-30 at {suf}.jpeg')
        y0 = card_top(src)
        top = fm.sm.SCALE * y0 + fm.sm.DY - RAISE
        box = fm.lift_card(src, os.path.join(ROOT, 'img', lang, 'family.webp'),
                           os.path.join(ROOT, 'img', lang, 'recipes.webp'),
                           (X0, y0, X1, y0 + HEIGHT), R_CARD, K, top, SHADOW, CX)
        print('  ', lang, '<-', os.path.basename(src), 'card', tuple(round(v, 1) for v in box))
