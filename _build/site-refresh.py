#!/usr/bin/env python3
"""Pozele de pe site dupa redenumirea Frigider -> Bucatarie (2026-11-19), toate cele 24 de limbi:

  fridge.webp    refacuta din captura noua (fridgy finished/frigider/), cu fridge-mockups.build
  family.webp    refacuta din captura noua (fridgy finished/invitatii/), cu shopping-mockups.build
  recipes.webp   doar eticheta butonului din mijloc din bara de jos (nav-label.py)
  shopping.webp  eticheta + pastila noua "Personal" din header (pill-swap.py)
  profile.webp   eticheta + iconita noua de langa "Salut" (hello-icon.py)

Aceleasi functii ca la pozele de magazin, cu transformarea captura (1290px) -> mockup de site
(shopping-mockups.py: 0.749 px de mockup per px de captura 945, decalaj 40.6 / -0.6). Rama = family.webp
din backup. Canalul alfa al mockup-urilor editate ramane neschimbat.

Originalele: <fridgy finished>/_backup Site 2026-11-19/<limba>/ (nu in repo: _build se publica); scriptul citeste de acolo, deci se poate rula din nou.
Utilizare: site-refresh.py [cod ...]   (implicit: toate)
"""
import importlib.util
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NAMES = ['fridge', 'family', 'recipes', 'shopping', 'profile']


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sf = load('swap_ff', 'swap-fridge-family.py')
nl = load('nav_label', 'nav-label.py')
hi = load('hello_icon', 'hello-icon.py')
ps = nl.ps
sm, fm = sf.sl.sm, sf.sl.fm
FINISHED = sf.FINISHED
BACKUP = os.path.join(sf.FINISHED, '_backup Site 2026-11-19')
CODE_TO_LANG = {v: k for k, v in sf.CODES.items()}
SITE = {'K': sm.SCALE * 945 / 1290, 'DX': sm.DX, 'DY': sm.DY, 'screen_x1': sm.SCREEN[2]}


def edit(src, dst, fns):
    im = Image.open(src).convert('RGBA')
    alpha = im.getchannel('A')
    rgb = im.convert('RGB')
    for fn in fns:
        rgb = fn(rgb)
    out = rgb.convert('RGBA')
    out.putalpha(alpha)
    out.save(dst, 'WEBP', quality=90, method=6)


def main():
    codes = sys.argv[1:] or list(CODE_TO_LANG)
    A_hello, o_hello, gr_hello, _, _ = hi.icon_layer()
    for code in codes:
        lang = CODE_TO_LANG[code]
        i = sf.ORDER.index(lang)
        img = os.path.join(ROOT, 'img', code)
        bak = os.path.join(BACKUP, code)
        os.makedirs(bak, exist_ok=True)
        for n in NAMES:
            if not os.path.exists(os.path.join(bak, n + '.webp')):
                shutil.copy2(os.path.join(img, n + '.webp'), os.path.join(bak, n + '.webp'))
        B = lambda n: os.path.join(bak, n + '.webp')
        O = lambda n: os.path.join(img, n + '.webp')
        frame = B('family')
        fm.build(os.path.join(FINISHED, 'frigider', f'IMG_{4091 + i}.png'), frame, O('fridge'))
        sm.build(os.path.join(FINISHED, 'invitatii', f'IMG_{4144 + i}.png'), frame, O('family'))

        cap = os.path.join(FINISHED, 'frigider', f'IMG_{4091 + i}.png')
        A_nav, o_nav, _ = nl.label_layer(cap)
        A_pill, o_pill, _ = ps.pill_layer(os.path.join(ps.SRC_DIR, f'IMG_{ps.SRC[lang]}.png'))
        nav = lambda im: nl.swap(im, A_nav, o_nav, SITE)[0]
        pill = lambda im: ps.swap(im, A_pill, o_pill, SITE)[0]
        hello = lambda im: hi.swap(im, (A_hello, o_hello, gr_hello, None), SITE)[0]
        edit(B('recipes'), O('recipes'), [nav])
        edit(B('shopping'), O('shopping'), [nav, pill])
        edit(B('profile'), O('profile'), [nav, hello])
        print(' ', code, lang, 'ok')


if __name__ == '__main__':
    main()
