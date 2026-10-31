#!/usr/bin/env python3
"""Reface img/<limba>/profile.webp din screenshot-urile cu profilul: ecranul intra in rama
ca la shopping-mockups.py, se intuneca, iar cardul cu statisticile se ridica peste el.

Efectul e masurat pe vechiul profile.webp (ro): tot ecranul e inmultit cu 0.77 (alb -> 196,
fundalul (229,241,251) -> (178,186,192)), iar cardul ramane luminos, lat de 680px (x 51..731)
si inalt de 628px, adica 0.8115 px de mockup per px de screenshot 945x2048. Umbra e potrivita
pe acelasi mockup: masca coborata 20px, blur 8, opacitate 0.16.

In screenshot-uri cardul sta la (54,1044.5)-(892,1818), raza 41, iar bara de navigare ii
acopera ultimii 2px, asa ca randurile de sub text se umplu cu alb. Vechea pozitie (y=476) ar
lasa vizibila jumatatea de jos a cardului din lista, deci cardul sta peste locul lui: incepe
imediat sub ultimul rand de text al cardului cu cheltuieli si il acopera complet pe cel din lista.

Utilizare: profile-mockups.py ["<folderul cu screenshot-uri>"] [limba=numar ...]
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('fm', os.path.join(ROOT, '_build', 'fridge-mockups.py'))
fm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)

FOLDER = '/mnt/c/Users/User/OneDrive/Documente/fridgy profile screenshots'
SHOTS = {'sv': '1', 'da': '2', 'nl': '3', 'hu': '4', 'ro': '5', 'fr': '6', 'en': '7', 'de': '8'}
CARD, R_CARD = (54, 1044.5, 892, 1818), 41  # cardul cu statistici, in screenshot-ul 945x2048
WHITE_FROM = 1806                           # sub ultimul rand de text, deasupra barei de navigare
K, CX, TOP = 680 / 838, 391, 736
DIM = 0.77
SHADOW = (20, 8, 0.16)


if __name__ == '__main__':
    folder = sys.argv[1] if len(sys.argv) > 1 and '=' not in sys.argv[1] else FOLDER
    shots = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a) or SHOTS
    for lang, n in shots.items():
        src = os.path.join(folder, f'{n}.jpeg')
        box = fm.lift_card(src, os.path.join(ROOT, 'img', lang, 'family.webp'),
                           os.path.join(ROOT, 'img', lang, 'profile.webp'),
                           CARD, R_CARD, K, TOP, SHADOW, CX, DIM, WHITE_FROM)
        print('  ', lang, '<-', os.path.basename(src), 'card', tuple(round(v, 1) for v in box))
