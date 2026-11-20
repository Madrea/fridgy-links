#!/usr/bin/env python3
"""Reface un mockup din screenshot-urile de App Store, pentru toate limbile.

De folosit cand se schimba un screenshot in "fridgy finished" (ex. poza 1.0, cea cu
bonul). Decupajul e cel masurat in en-mockups.py; alfa se pastreaza din exportul
existent, silueta telefonului fiind aceeasi in toate limbile.

    python3 _build/refresh-shot.py scan            # toate limbile
    python3 _build/refresh-shot.py scan --lang ro de

Scrie si in _build/img-original/<lang>/ (q95, sursa) si in img/<lang>/ (q90, live).
Atentie: notify are nevoie dupa aceea de fix-notify.py, iar fridge/recipes/profile/
family de fix-mockups.py <lang>.
"""
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/mnt/c/Users/User/OneDrive/Documente/fridgy finished'

LANGS = {'da': 'Danish', 'de': 'German', 'en': 'English', 'fr': 'French',
         'hu': 'Hungarian', 'nl': 'Holland', 'ro': 'Romanian', 'sv': 'Swedish'}
# limbile noi (pozele de store facute cu store-shots-lang.py, pe compozitia romaneasca)
NEW = {'bg': 'Bulgarian', 'es': 'Spanish', 'it': 'Italian', 'pl': 'Polish', 'pt': 'Portuguese',
       'cs': 'Czech', 'el': 'Greek', 'fi': 'Finnish', 'sk': 'Slovak', 'hr': 'Croatian', 'sl': 'Slovenian',
       'lt': 'Lithuanian', 'lv': 'Latvian', 'et': 'Estonian', 'ga': 'Irish', 'mt': 'Maltese'}
LANGS.update(NEW)
REF_LANG = 'de'   # o limba noua nu are export propriu: alfa (aceeasi silueta) se ia de aici

# notificarea are un rand in plus cand mesajul nu incape in 3 (store-shots-lang.py, grow_card):
# cardul creste in sus cu atatia pixeli de store; decupajul urca la fel, iar alfa se lungeste
NOTIFY_GROW = {'el': 36.5}

# nume -> (numarul screenshot-ului, decupajul din JPG) - vezi en-mockups.py
SHOTS = {
    'scan':    (1, (91.55,  718.61, 1105.56, 1916.30)),
    'fridge':  (2, (198.21, 801.21,  893.33, 1830.16)),
    'recipes': (3, (198.61, 798.61,  888.89, 1833.92)),
    'notify':  (4, (286.00, 2113.83, 725.00,  251.74)),
    'profile': (5, (198.21, 801.21,  893.33, 1830.16)),
    'habits':  (6, (29.66,  877.63, 1116.67, 1595.59)),
    'waste':   (7, (0.00,   243.63, 1237.50, 1593.62)),
    'family':  (8, (198.21, 801.21,  893.33, 1830.16)),
}

args = sys.argv[1:]
if '--lang' in args:
    i = args.index('--lang')
    names, langs = args[:i], args[i + 1:]
else:
    names, langs = args, sorted(LANGS)
if not names:
    sys.exit(__doc__)

for name in names:
    n, (x, y, w, h) = SHOTS[name]
    print(name)
    for lang in langs:
        orig = os.path.join(ROOT, '_build', 'img-original', lang, name + '.webp')
        live = os.path.join(ROOT, 'img', lang, name + '.webp')
        jpg = os.path.join(SRC, LANGS[lang], 'iPhone 6.9', 'iPhone 6.9_ - %d.0.jpg' % n)
        if lang in NEW:  # mereu din REF_LANG, ca o rulare repetata sa nu lungeasca iar notificarea
            orig_ref = os.path.join(ROOT, '_build', 'img-original', REF_LANG, name + '.webp')
            ref = Image.open(orig_ref).convert('RGBA')
        else:
            ref = Image.open(orig if os.path.exists(orig) else live).convert('RGBA')
        alpha = ref.getchannel('A')
        size, box = ref.size, (x, y, x + w, y + h)
        grow = NOTIFY_GROW.get(lang, 0) if name == 'notify' else 0
        if grow:
            # cardul mai inalt: randurile din mijlocul alfei (opace) se repeta
            extra = round(ref.size[1] * (h + grow) / h) - ref.size[1]
            size = (ref.size[0], ref.size[1] + extra)
            box = (x, y - grow, x + w, y + h)
            mid = ref.size[1] // 2
            a = Image.new('L', size)
            a.paste(alpha.crop((0, 0, size[0], mid)), (0, 0))
            a.paste(alpha.crop((0, mid, size[0], mid + 1)).resize((size[0], extra)), (0, mid))
            a.paste(alpha.crop((0, mid, size[0], ref.size[1])), (0, mid + extra))
            alpha = a
        src = Image.open(jpg).convert('RGB')
        out = src.resize(size, Image.LANCZOS, box=box).convert('RGBA')
        out.putalpha(alpha)
        out.save(orig, 'WEBP', quality=95, method=6)
        out.save(live, 'WEBP', quality=90, method=6)
        print('  %-3s <- %s  %dx%d' % (lang, os.path.basename(jpg), *size))
