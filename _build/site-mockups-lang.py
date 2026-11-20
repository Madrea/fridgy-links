#!/usr/bin/env python3
"""Mockup-urile de pe site cu telefonul drept, pentru limbile noi (cele din store-shots-lang.py).

Aceleasi functii ca la limbile vechi, doar ca sursele sunt capturile limbii din
<fridgy finished>/<Limba>/ (1290x2796, ordinea RAW_ORDER din store-shots-lang.py), nu folderele
cu fisiere WhatsApp:
  shopping  shopping-mockups.build  (captura 'list')
  fridge    fridge-mockups.build    (captura 'fridge')
  recipes   ca in recipes-mockups.py (captura 'recipes')
  profile   ca in profile-mockups.py (captura 'stats')
  budget    cardul de buget decupat 1:1 din captura adusa la 945x2048, la (51,647)-(893,1091)
            (potrivit pe img/en/budget.webp, eroare medie ~1/255), cu alfa (colturile rotunjite)
            din img/en/budget.webp - e identica in toate limbile
  history   nu exista captura pentru limbile noi -> se copiaza img/en/history.webp
Rama e img/<limba>/family.webp, deci intai: cut-phone.py "<fridgy finished>" <limbi> family

Utilizare: site-mockups-lang.py <limbi...>   (ex. es it el)
"""
import importlib.util
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sl = load('store_shots_lang', 'store-shots-lang.py')
sm, fm, rm, pm = sl.sm, sl.fm, sl.rm, sl.pm
BUDGET_BOX = (51, 647, 893, 1091)

langs = sys.argv[1:]
if not langs:
    sys.exit(__doc__)
for lang in langs:
    cfg = sl.lang_config(lang)
    raw = os.path.join(sl.ss.FINISHED, cfg['folder'])
    path = lambda k: os.path.join(raw, cfg['shots'][k])
    img = lambda n: os.path.join(ROOT, 'img', lang, n + '.webp')
    frame = img('family')

    sm.build(path('list'), frame, img('shopping'))
    fm.build(path('fridge'), frame, img('fridge'))

    src = path('recipes')
    y0 = rm.card_top(src)
    top = sm.SCALE * y0 + sm.DY - rm.RAISE
    fm.lift_card(src, frame, img('recipes'), (rm.X0, y0, rm.X1, y0 + rm.HEIGHT), rm.R_CARD, rm.K, top,
                 rm.SHADOW, rm.CX)

    fm.lift_card(path('stats'), frame, img('profile'), pm.CARD, pm.R_CARD, pm.K, pm.TOP, pm.SHADOW, pm.CX,
                 pm.DIM, pm.WHITE_FROM)

    shot = Image.open(path('budget')).convert('RGB').resize((945, 2048), Image.LANCZOS)
    card = shot.crop(BUDGET_BOX).convert('RGBA')
    card.putalpha(Image.open(os.path.join(ROOT, 'img', 'en', 'budget.webp')).getchannel('A'))
    card.save(img('budget'), 'WEBP', quality=90, method=6)

    shutil.copyfile(os.path.join(ROOT, 'img', 'en', 'history.webp'), img('history'))
    print(' ', lang, 'shopping fridge recipes profile budget  (history = en)')
