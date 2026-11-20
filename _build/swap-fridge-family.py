#!/usr/bin/env python3
"""Capturile noi (2026-11-19) pentru Bucatarie si Bucatariile mele, in pozele de magazin:
iPhone 2 si Android 2 (frigider, cu cardul cu paine ridicat) si iPhone 8 si Android 8 (invitatii).

Telefonul se compune ca in store-shots-lang.py (aceeasi rama, acelasi card ridicat), iar antetul
cu text se ia din poza finala existenta a limbii (topit in fundal intre FADE_Y si HEADER_H), deci
titlurile nu se schimba. Placa (rama goala) = poza 8 romaneasca din backup.

Capturile: fridgy finished/frigider/IMG_4091..4114.png si invitatii/IMG_4144..4167.png, in ordinea
din SRC (limba recunoscuta dupa textul din ecran). Originalele sunt in `_backup Frigider-Invitatii
2026-11-19/`; scriptul citeste antetul de acolo, deci se poate rula de mai multe ori.

Poza 8: titlul devine "O bucatarie pentru toata familia" (TITLES, verificat de un model separat, 2026-11-19).
Se sterge doar banda titlului (fundalul curat din clean_header, topit spre subtitlu), iar titlul se
deseneaza ca in store-shots-lang.py (Poppins Bold 104 / 88, aceleasi linii de baza; bg Montserrat,
el Commissioner). Subtitlul ramane cel original.

Utilizare: swap-fridge-family.py [Limba ...]   (implicit: toate cele 24)
"""
import importlib.util
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sl = load('store_shots_lang', 'store-shots-lang.py')
ss, sa = sl.ss, sl.sa
FINISHED = ss.FINISHED
BACKUP = os.path.join(FINISHED, '_backup Frigider-Invitatii 2026-11-19')

ORDER = ['Romanian', 'English', 'German', 'French', 'Hungarian', 'Holland', 'Danish', 'Swedish', 'Spanish',
         'Italian', 'Polish', 'Portuguese', 'Czech', 'Greek', 'Finnish', 'Slovak', 'Bulgarian', 'Croatian',
         'Slovenian', 'Lithuanian', 'Latvian', 'Estonian', 'Irish', 'Maltese']
SRC = {'fridge': ('frigider', 4091), 'family': ('invitatii', 4144)}
SHOTS = {'fridge': 2, 'family': 8}
CODES = {'Romanian': 'ro', 'English': 'en', 'German': 'de', 'French': 'fr', 'Hungarian': 'hu', 'Holland': 'nl',
         'Danish': 'da', 'Swedish': 'sv', **{v: k for k, v in sl.FOLDERS.items()}}
TITLES = {
    'ro': ('O bucătărie pentru', 'toată *familia*'), 'en': ('One kitchen for the', 'whole *family*'),
    'de': ('Eine Küche für', 'die ganze *Familie*'), 'fr': ('Une cuisine pour', 'toute la *famille*'),
    'hu': ('Egy konyha az egész', '*családnak*'), 'nl': ('Eén keuken voor', 'het hele *gezin*'),
    'da': ('Ét køkken til hele', '*familien*'), 'sv': ('Ett kök för hela', '*familjen*'),
    'bg': ('Една кухня за', 'цялото *семейство*'), 'es': ('Una cocina para', 'toda la *familia*'),
    'it': ('Una cucina per', 'tutta la *famiglia*'), 'pl': ('Jedna kuchnia', 'dla całej *rodziny*'),
    'pt': ('Uma cozinha para', 'toda a *família*'), 'cs': ('Jedna kuchyně', 'pro celou *rodinu*'),
    'el': ('Μία κουζίνα για', 'όλη την *οικογένεια*'), 'fi': ('Yksi keittiö', 'koko *perheelle*'),
    'sk': ('Jedna kuchyňa', 'pre celú *rodinu*'), 'hr': ('Jedna kuhinja', 'za cijelu *obitelj*'),
    'sl': ('Ena kuhinja', 'za vso *družino*'), 'lt': ('Viena virtuvė', 'visai *šeimai*'),
    'lv': ('Viena virtuve', 'visai *ģimenei*'), 'et': ('Üks köök', 'kogu *perele*'),
    'ga': ('Cistin amháin', 'don *teaghlach* ar fad'), 'mt': ('Kċina waħda', '*għall-familja* kollha'),
}
FONT_DIR = os.path.join(HERE, 'fonts')
# banda titlului: pana la CUT e fundal curat, apoi se topeste in poza pana la CUT + FADE (deasupra subtitlului)
TITLE_BAND = {'iphone': (398, 20), 'android': (300, 18)}
DEVICES = {
    'iphone': (sl.DEVICES['iphone'], sl.straight_iphone),
    'android': (sl.DEVICES['android'], sl.straight_android),
}


def backup(lang, dev, n):
    dst = os.path.join(FINISHED, lang, dev['dir'], dev['name'].format(n=n))
    bak = os.path.join(BACKUP, lang, dev['dir'], dev['name'].format(n=n))
    if not os.path.exists(bak):
        os.makedirs(os.path.dirname(bak), exist_ok=True)
        shutil.copy2(dst, bak)
    return dst, bak


def keep_header(out, old, mod):
    fade = np.zeros((out.height, out.width), np.float32)
    fade[:mod.FADE_Y] = 255
    fade[mod.FADE_Y:mod.HEADER_H] = np.linspace(255, 0, mod.HEADER_H - mod.FADE_Y)[:, None]
    out = out.copy()
    out.paste(old, (0, 0), Image.fromarray(fade.astype(np.uint8)))
    return out


def retitle(out, lang, name, dev, clean):
    cut, fade = TITLE_BAND[name]
    m = np.zeros((out.height, out.width), np.float32)
    m[:cut] = 255
    m[cut:cut + fade] = np.linspace(255, 0, fade)[:, None]
    out = out.copy()
    out.paste(clean, (0, 0), Image.fromarray(m.astype(np.uint8)).crop((0, 0) + clean.size))
    code = CODES[lang]
    bold_file, _, scale = sl.FONTS.get(code, sl.POPPINS)
    size, baselines = dev['layout']['*'][0]
    font = ImageFont.truetype(os.path.join(FONT_DIR, bold_file), round(size * scale))
    for line, y in zip(TITLES[code], baselines):
        sl.draw_line(out, line, font, y, dev['cx'], dev['max_w'])
    return out


def main():
    langs = sys.argv[1:] or ORDER
    for lang in ORDER:  # backup-ul intai, pentru toate limbile (placa vine din backup-ul romanesc)
        for dev, _ in DEVICES.values():
            for n in SHOTS.values():
                backup(lang, dev, n)
    for name, (dev, straight) in DEVICES.items():
        mod = dev['mod']
        plate = Image.open(backup('Romanian', dev, 8)[1]).convert('RGB')
        orig_src = mod.src_path   # fundalul curat din originale (2 si 8 se rescriu aici)
        mod.src_path = lambda f, n, o=orig_src, dev=dev: (
            backup(f, dev, n)[1] if n in SHOTS.values() else o(f, n))
        clean = mod.clean_header()
        mod.src_path = orig_src
        for lang in langs:
            i = ORDER.index(lang)
            for key, n in SHOTS.items():
                folder, first = SRC[key]
                src = os.path.join(FINISHED, folder, f'IMG_{first + i}.png')
                dst, bak = backup(lang, dev, n)
                out = straight(key, plate, src, None)
                out = keep_header(out, Image.open(bak).convert('RGB'), mod)
                if key == 'family':
                    out = retitle(out, lang, name, dev, clean)
                out.save(dst, 'JPEG', quality=98, subsampling=0, optimize=True)
                print(lang.ljust(11), name.ljust(8), n, key, os.path.basename(src))


if __name__ == '__main__':
    main()
