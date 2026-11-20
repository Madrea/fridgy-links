#!/usr/bin/env python3
"""Reface pozele de App Store "iPhone 6.9" (1290x2796): 2 frigider, 3 retete, 5 statistici
(ramane antetul original, se schimba doar telefonul) si adauga 9 lista si 10 buget.

Geometria e cea din mockup-urile de pe site (shopping/fridge/recipes/profile-mockups.py),
convertita in pixelii pozei de store. Ecranul, masurat pe poza 8 (identic in toate limbile),
e (232,827)-(1057,2604), adica 826x1778 fata de 702x1512 in family.webp -> S = 1778/1512.
Capturile se aseaza direct la rezolutia finala, nu se maresc webp-urile de pe site.

Placa curata = poza 8 din aceeasi limba: telefon drept, nimic in afara ramei. Sub randul
HEADER_H fundalul ei coincide cu al pozelor 2, 3, 5. Antetul pozelor 9 si 10 nu are o sursa
fara text, asa ca se reconstruieste ca maxim pe pixel peste pozele 2, 3, 4, 5, 8 din toate
limbile: textul difera de la o poza la alta, iar fundalul e acelasi. Se topeste in placa.

Textul nou: Poppins Bold 104 (titlu) si Medium 66 (subtitlu), potrivite pe poza 8 (latime
930 vs 930 si 1074 vs 1073), pe liniile de baza 219/348 si 483/571, centrat pe x=645.

Pe poza 10 din captura de buget se ia DOAR cardul: acele capturi contin date personale reale.
Fundalul vine din capturile de profil cu contul demo.

Utilizare: store-shots.py --fonts <dir> --out <dir> [--langs ro,en] [--shots 2,3,5,9,10]
  --out e un folder <out>/<Limba>/iPhone 6.9_ - N.0.jpg; originalele nu se modifica.
"""
import argparse
import glob
import importlib.util
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = '/mnt/c/Users/User/OneDrive/Documente'
FINISHED = os.path.join(DOCS, 'fridgy finished')
BACKUP = os.path.join(FINISHED, '_backup iPhone 6.9 2026-11-02')
FOLDERS = {'da': 'Danish', 'de': 'German', 'en': 'English', 'fr': 'French',
           'hu': 'Hungarian', 'nl': 'Holland', 'ro': 'Romanian', 'sv': 'Swedish'}


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), os.path.join(HERE, name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sm, fm, rm, pm = (load(n) for n in ('shopping-mockups', 'fridge-mockups', 'recipes-mockups', 'profile-mockups'))

W, H = 1290, 2796
SCREEN = (232, 827, 1057, 2604)
S = 1778 / 1512                        # px de store per px de mockup
OX, OY = SCREEN[0] - 40 * S, SCREEN[1] - 23 * S  # coltul mockup-ului de site, in poza de store
R_IN, R_ISL = 90 * S, 27 * S
ISLAND = tuple(round(v) for v in (OX + 294 * S, OY + 48 * S, OX + 488 * S, OY + 101 * S))
SCALE = sm.SCALE * S
DX, DY = OX + sm.DX * S, OY + sm.DY * S
HEADER_H = 780
FADE_Y = 620
SS = 2                                 # supraesantionare pentru masti, la 1290x2796

BUDGET_SHOTS = {'en': '14.07.16', 'de': '14.07.17 (1)', 'hu': '14.07.17 (2)', 'nl': '14.07.17 (3)',
                'da': '14.07.17 (4)', 'sv': '14.07.17 (5)', 'ro': '14.07.17 (6)', 'fr': '14.07.17'}
BUDGET_CARD, BUDGET_R = (53, 650, 892, 1089), 41  # in captura 945x2048
BUDGET_K, BUDGET_TOP = 784 / 839, 478   # la fel de lat ca painea, peste locul lui din profil

# *cuvant* = albastru; fiecare element e un rand
TEXT = {
    9: {
        'ro': (('Lista de cumpărături', '*inteligentă*'), ('Se completează din obiceiurile', 'tale și îți sugerează ce ți-ar trebui')),
        'en': (('*Smart*', 'shopping list'), ('Builds itself from your habits and', 'suggests what you might need')),
        'de': (('*Smarte*', 'Einkaufsliste'), ('Lernt, was du oft kaufst, und', 'schlägt vor, was du brauchst')),
        'fr': (('Liste de courses', '*intelligente*'), ('Se remplit selon tes habitudes', 'et te suggère ce qu’il te faut')),
        'nl': (('*Slimme*', 'boodschappenlijst'), ('Leert wat je vaak koopt en', 'stelt voor wat je nodig hebt')),
        'hu': (('*Okos*', 'bevásárlólista'), ('A szokásaid alapján bővül, és', 'javasolja, amire szükséged lehet')),
        'da': (('*Smart*', 'indkøbsliste'), ('Udfylder sig selv ud fra dine vaner', 'og foreslår, hvad du mangler')),
        'sv': (('*Smart*', 'inköpslista'), ('Fylls på efter dina vanor och', 'föreslår vad du kan behöva')),
    },
    10: {
        'ro': (('Bugetul tău,', 'sub *control*'), ('Setezi limita lunară, iar noi', 'te ajutăm să n-o depășești')),
        'en': (('Your budget,', 'under *control*'), ('Set a monthly limit and we’ll', 'help you stick to it')),
        'de': (('Dein Budget', 'im *Griff*'), ('Leg dein Monatsbudget fest,', 'wir helfen dir, es einzuhalten')),
        'fr': (('Ton budget,', 'sous *contrôle*'), ('Fixe ta limite du mois, on t’aide', 'à ne pas la dépasser')),
        'nl': (('Je budget', 'onder *controle*'), ('Stel je maandbudget in, wij', 'helpen je eronder te blijven')),
        'hu': (('Tartsd *kézben*', 'a kiadásaidat'), ('Megadod a havi keretet, mi pedig', 'segítünk, hogy ne lépd túl')),
        'da': (('Dit budget', 'under *kontrol*'), ('Sæt et månedligt budget, så', 'hjælper vi dig med at holde det')),
        'sv': (('Din budget', 'under *kontroll*'), ('Sätt en månadsbudget, så', 'hjälper vi dig att hålla den')),
    },
}
BLUE, INK = (74, 126, 244), (0, 0, 0)
TITLE_Y, SUB_Y, TEXT_CX, MAX_TEXT_W = (219, 348), (483, 571), 645, 1140


def x_(v):
    return OX + S * v


def y_(v):
    return OY + S * v


def rr(box, r, grow=0):
    x0, y0, x1, y1 = box
    m = Image.new('L', (W * SS, H * SS), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        ((x0 - grow) * SS, (y0 - grow) * SS, (x1 + grow + 1) * SS - 1, (y1 + grow + 1) * SS - 1),
        (r + grow) * SS, fill=255)
    return m.resize((W, H), Image.LANCZOS)


def phone(plate, shot_path, dim=1):
    """Captura in rama placii, ca sm.build, in coordonatele pozei de store."""
    shot = Image.open(shot_path).convert('RGB')
    if shot.size != (945, 2048):
        shot = shot.resize((945, 2048), Image.LANCZOS)
    P = 8
    shot = Image.fromarray(np.pad(sm.strip_status_bar(np.asarray(shot)), ((P, P), (P, P), (0, 0)), mode='edge'))
    x0, y0, x1, y1 = SCREEN[0], SCREEN[1], SCREEN[2] + 1, SCREEN[3] + 1
    box = tuple(P + v for v in ((x0 - DX) / SCALE, (y0 - DY) / SCALE, (x1 - DX) / SCALE, (y1 - DY) / SCALE))
    part = shot.resize((x1 - x0, y1 - y0), Image.LANCZOS, box=box)
    if dim != 1:
        part = part.point(lambda v: v * dim)
    layer = Image.new('RGB', (W, H))
    layer.paste(part, (x0, y0))
    out = plate.copy()
    out.paste(layer, (0, 0), rr(SCREEN, R_IN, grow=1))
    # pe inelul de la marginea ecranului, pixelii care pe placa sunt bezel raman bezel
    f = np.asarray(plate).astype(int)
    lum = (f * (299, 587, 114)).sum(axis=2) // 1000
    screenish = ((f.max(2) - f.min(2)) > 45) | (lum > 140)
    ring = (np.asarray(rr(SCREEN, R_IN, grow=2)) > 0) & (np.asarray(rr(SCREEN, R_IN, grow=-7)) < 255)
    out.paste(plate, (0, 0), Image.fromarray(np.where(ring & ~screenish, 255, 0).astype(np.uint8)))
    out.paste(plate, (0, 0), rr(ISLAND, R_ISL, grow=1))
    return out


def lift(base, shot_path, card, r_card, k_site, top_site, shadow, cx_site=392, white_from=None):
    """Cardul `card` (x0,y0,x1,y1 in captura 945x2048) ridicat peste telefon, ca fm.lift_card."""
    k = k_site * S
    x0, y0, x1, y1 = card
    ox, oy = x_(cx_site) - k * (x0 + x1) / 2, y_(top_site) - k * y0
    shot = Image.open(shot_path).convert('RGB')
    f = shot.size[0] / 945
    if white_from is not None:
        ImageDraw.Draw(shot).rectangle((0, white_from * f, *shot.size), fill='white')
    lifted = shot.transform((W, H), Image.AFFINE, (f / k, 0, -ox * f / k, 0, f / k, -oy * f / k), Image.BICUBIC)
    box = (ox + k * x0, oy + k * y0, ox + k * x1, oy + k * y1)
    m = Image.new('L', (W * SS, H * SS), 0)
    ImageDraw.Draw(m).rounded_rectangle([v * SS for v in box], k * r_card * SS, fill=255)
    mask = m.resize((W, H), Image.LANCZOS)
    dy, blur, op = shadow
    sh = ImageChops.offset(mask, 0, round(dy * S)).filter(ImageFilter.GaussianBlur(blur * S)).point(lambda v: int(v * op))
    rgb = np.asarray(base).astype(float) * (1 - np.asarray(sh, float)[:, :, None] / 255)
    out = Image.fromarray(rgb.clip(0, 255).astype(np.uint8))
    out.paste(lifted, (0, 0), mask)
    return out


def clean_header():
    """Fundalul fara text: maximul pe pixel (textul e mai inchis decat fundalul in toate pozele,
    iar pozitiile lui difera), netezit, fiindca fundalul e un gradient lin."""
    bg = None
    for lang in FOLDERS.values():
        for n in (2, 3, 4, 5, 8):
            a = np.asarray(Image.open(src_path(lang, n)).convert('RGB').crop((0, 0, W, HEADER_H)))
            bg = a if bg is None else np.maximum(bg, a)
    return Image.fromarray(bg).filter(ImageFilter.GaussianBlur(14))


def src_path(folder, n):
    """Originalul: din backup pentru pozele rescrise, ca rularile repetate sa plece de la el."""
    if n in (2, 3, 5):
        return os.path.join(BACKUP, folder, f'iPhone 6.9_ - {n}.0.jpg')
    return os.path.join(FINISHED, folder, 'iPhone 6.9', f'iPhone 6.9_ - {n}.0.jpg')


def draw_line(canvas, line, font, baseline):
    """Un rand centrat, cu *cuvantul* albastru; kerning-ul se pastreaza intre segmente."""
    plain = line.replace('*', '')
    width = font.getlength(plain)
    if width > MAX_TEXT_W:
        raise ValueError(f'rand prea lat ({width:.0f}px): {plain}')
    k = 4
    big = font.font_variant(size=font.size * k)
    mask_ink, mask_blue = (Image.new('L', (W * k, 200 * k), 0) for _ in range(2))
    x0 = (TEXT_CX + 0.5) * k - big.getlength(plain) / 2
    pos = 0
    for i, seg in enumerate(line.split('*')):
        if seg:
            x = x0 + big.getlength(plain[:pos + len(seg)]) - big.getlength(seg)
            ImageDraw.Draw(mask_blue if i % 2 else mask_ink).text((x, 150 * k), seg, font=big, fill=255, anchor='ls')
            pos += len(seg)
    for mask, color in ((mask_ink, INK), (mask_blue, BLUE)):
        canvas.paste(color, (0, baseline - 150), mask.resize((W, 200), Image.LANCZOS))
    return width


def header(clean, plate, text, fonts):
    out = plate.copy()
    # sub text (randurile FADE_Y..HEADER_H) fundalul reconstruit trece treptat in cel al placii
    fade = np.ones((HEADER_H, W), np.float32) * 255
    fade[FADE_Y:] = np.linspace(255, 0, HEADER_H - FADE_Y)[:, None]
    out.paste(clean, (0, 0), Image.fromarray(fade.astype(np.uint8)))
    title, sub = text
    for line, y in zip(title, TITLE_Y):
        draw_line(out, line, fonts[0], y)
    for line, y in zip(sub, SUB_Y):
        draw_line(out, line, fonts[1], y)
    return out


def shot_file(folder, suffix, date='2026-10-28'):
    return os.path.join(DOCS, folder, f'WhatsApp Image {date} at {suffix}.jpeg')


def build(n, lang, plate, clean, fonts):
    folder = FOLDERS[lang]
    if n == 2:
        src = shot_file('fridgy fridge screenshots', fm.SHOTS[lang], '2026-10-30')
        mid = sm.SCALE * (fm.ABOVE + fm.BELOW) / 2 + sm.DY + fm.LIFT_DY
        top = mid - fm.K * (fm.CARD[3] - fm.CARD[1]) / 2
        out = lift(phone(plate, src), src, fm.CARD, fm.R_CARD, fm.K, top, (fm.SH_DY, fm.SH_BLUR, fm.SH_OP))
    elif n == 3:
        src = shot_file('fridgy recipes screenshots', rm.SHOTS[lang], '2026-10-30')
        y0 = rm.card_top(src)
        top = sm.SCALE * y0 + sm.DY - rm.RAISE
        card = (rm.X0, y0, rm.X1, y0 + rm.HEIGHT)
        out = lift(phone(plate, src), src, card, rm.R_CARD, rm.K, top, rm.SHADOW, rm.CX)
    elif n == 5:
        src = os.path.join(DOCS, 'fridgy profile screenshots', pm.SHOTS[lang] + '.jpeg')
        out = lift(phone(plate, src, pm.DIM), src, pm.CARD, pm.R_CARD, pm.K, pm.TOP, pm.SHADOW, pm.CX, pm.WHITE_FROM)
    elif n == 9:
        out = phone(plate, shot_file('fridgy shopping list screenshots', sm.SHOTS[lang]))
    elif n == 10:
        bg = os.path.join(DOCS, 'fridgy profile screenshots', pm.SHOTS[lang] + '.jpeg')
        card = shot_file('fridgy budget screenshots', BUDGET_SHOTS[lang])
        out = lift(phone(plate, bg, pm.DIM), card, BUDGET_CARD, BUDGET_R, BUDGET_K, BUDGET_TOP,
                   (fm.SH_DY, fm.SH_BLUR, fm.SH_OP))
    else:
        raise ValueError(n)
    if n in (2, 3, 5):
        orig = Image.open(src_path(folder, n)).convert('RGB')
        out.paste(orig.crop((0, 0, W, HEADER_H)), (0, 0))
    else:
        h = header(clean, out, TEXT[n][lang], fonts)
        out.paste(h.crop((0, 0, W, HEADER_H)), (0, 0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--langs', default=','.join(FOLDERS))
    ap.add_argument('--shots', default='2,3,5,9,10')
    a = ap.parse_args()
    shots = [int(v) for v in a.shots.split(',')]
    fonts = (ImageFont.truetype(os.path.join(a.fonts, 'Poppins-Bold.ttf'), 104),
             ImageFont.truetype(os.path.join(a.fonts, 'Poppins-Medium.ttf'), 66))
    clean = clean_header() if any(n > 8 for n in shots) else None
    for lang in a.langs.split(','):
        folder = FOLDERS[lang]
        plate = Image.open(src_path(folder, 8)).convert('RGB')
        dst = os.path.join(a.out, folder)
        os.makedirs(dst, exist_ok=True)
        for n in shots:
            out = build(n, lang, plate, clean, fonts)
            path = os.path.join(dst, f'iPhone 6.9_ - {n}.0.jpg')
            out.save(path, 'JPEG', quality=98, subsampling=0, optimize=True)
            print(' ', lang, n, out.size, os.path.getsize(path) // 1024, 'KB')


if __name__ == '__main__':
    main()
