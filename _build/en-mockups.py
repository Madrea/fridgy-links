#!/usr/bin/env python3
"""Construieste mockup-urile pentru engleza pornind de la screenshot-urile de App Store.

Celelalte limbi au primit din Figma mockup-uri cu alfa (_build/img-original/<lang>/);
pentru engleza nu au venit. Dar compozitia screenshot-urilor de App Store (1290x2796)
e identica in toate limbile - acelasi telefon, aceeasi pozitie, doar textul difera.

Deci, pentru fiecare mockup, dreptunghiul din JPG care corespunde exportului Figma se
masoara o data pe o limba care are ambele (potrivire prin corelatie normalizata; iese
acelasi dreptunghi pe de/ro/fr, corelatie 0.98-0.99) si se aplica identic pe JPG-ul
englezesc. Alfa se ia din exportul german - silueta e aceeasi in toate limbile.

Rezultatul intra in _build/img-original/en/, de unde trece prin acelasi tratament ca
restul limbilor:

    python3 _build/en-mockups.py
    cp _build/img-original/en/*.webp img/en/
    python3 _build/fix-notify.py                  # banner-ul de notificare
    python3 _build/fix-mockups.py en              # telefoanele drepte
    for n in scan habits waste; do                # restul, doar reincadrate la q90
      convert _build/img-original/en/$n.webp -define webp:method=6 -quality 90 img/en/$n.webp
    done
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/mnt/c/Users/User/OneDrive/Documente/fridgy finished/English/iPhone 6.9'
REF = os.path.join(ROOT, '_build', 'img-original', 'de')
OUT = os.path.join(ROOT, '_build', 'img-original', 'en')

# nume -> (numarul screenshot-ului, decupajul din JPG masurat pe de/ro/fr)
# In exportul englezesc continutul cardului de notificare (iconita, titlu, text) sta
# cu 4px mai la stanga decat in celelalte limbi, desi cardul e in acelasi loc. Cardul
# oricum se reconstruieste in fix-notify.py, deci decupajul se muta cu tot atat ca sa
# se piarda din iconita exact cat se pierde si la restul limbilor.
NOTIFY_DX = -4

SHOTS = {
    'scan':    (1, (91.55,  718.61, 1105.56, 1916.30)),
    'fridge':  (2, (198.21, 801.21,  893.33, 1830.16)),
    'recipes': (3, (198.61, 798.61,  888.89, 1833.92)),
    'notify':  (4, (286.00, 2113.83, 725.00,  251.74)),  # vezi NOTIFY_DX
    'profile': (5, (198.21, 801.21,  893.33, 1830.16)),
    'habits':  (6, (29.66,  877.63, 1116.67, 1595.59)),
    'waste':   (7, (0.00,   243.63, 1237.50, 1593.62)),
    'family':  (8, (198.21, 801.21,  893.33, 1830.16)),
}

os.makedirs(OUT, exist_ok=True)
for name, (n, (x, y, w, h)) in sorted(SHOTS.items()):
    ref = Image.open(os.path.join(REF, name + '.webp')).convert('RGBA')
    src = Image.open(os.path.join(SRC, 'iPhone 6.9_ - %d.0.jpg' % n)).convert('RGB')
    rgb = src.resize(ref.size, Image.LANCZOS, box=(x, y, x + w, y + h))
    out = rgb.convert('RGBA')
    out.putalpha(ref.getchannel('A'))
    out.save(os.path.join(OUT, name + '.webp'), 'WEBP', quality=95, method=6)
    print('  %-8s <- %d.0.jpg %.0fx%.0f+%.0f+%.0f -> %dx%d' % (name, n, w, h, x, y, *ref.size))
