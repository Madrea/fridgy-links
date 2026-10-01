#!/usr/bin/env python3
"""Reface img/<limba>/scan.webp (cele doua telefoane inclinate) din screenshot-ul 1.0.

Exportul din Figma era incadrat fix pe telefoane si avea un alfa zimtat si usor decalat:
muchiile de sus si de jos erau taiate drept, pe contur ramanea un fir din fundalul
deschis, iar muchia metalica din coltul din dreapta sus lipsea.

Aici conturul se masoara direct din screenshot. Silueta exportului
(_build/img-original/<limba>/scan.webp) spune doar pe unde sunt telefoanele:
  - fundalul (cu tot cu umbre) e neted, iar conturul telefonului e o muchie neta; se
    "inunda" fundalul dinspre margini prin pixelii netezi, pana la prima muchie;
  - inundarea e permisa doar intr-o banda in jurul siluetei vechi, ca sa nu intre in
    ecranele telefoanelor si sa nu ia titlul de deasupra drept telefon;
  - pe contur, transparenta fiecarui pixel se calculeaza din culoarea lui (cat e
    fundal, cat e telefon), iar urma de fundal se scoate din culoare.

Utilizare: cut-scan.py "<folderul fridgy finished>" [limbi...]   (are nevoie de scipy)
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = {'da': 'Danish', 'de': 'German', 'en': 'English', 'fr': 'French',
           'hu': 'Hungarian', 'nl': 'Holland', 'ro': 'Romanian', 'sv': 'Swedish'}
SHOT = 'iPhone 6.9/iPhone 6.9_ - 1.0.jpg'
BOX = (91.55, 718.61, 1105.56, 1916.30)   # decupajul exportului in JPG - vezi en-mockups.py

PAD = 20        # margine transparenta, in pixelii sursei
BAND = 14       # cat se poate abate conturul real de la silueta exportului
CORNER = 170    # latura zonei de colt din dreapta sus, in pixelii sursei
FADE = 90       # pe cati pixeli se stinge muchia metalica a coltului, in josul laturii
SMOOTH = 11     # sub atat, variatia locala e fundal sau umbra, nu muchie
OUTER = 4       # de la atatia pixeli in afara conturului e sigur fundal
INNER = 3       # de la atatia pixeli in interior e sigur telefon
REF_LANG = 'ro'  # screenshot fara umbra sub telefoane, pe el se masoara conturul
OUT_W = 900     # latimea telefoanelor in imaginea finala, ca in exportul vechi


def load(src):
    """Zona telefoanelor din screenshot, cu marginea de PAD pixeli."""
    x, y, w, h = BOX
    box = (round(x) - PAD, round(y) - PAD, round(x + w) + PAD, round(y + h) + PAD)
    return np.asarray(Image.open(src).convert('RGB').crop(box)).astype(float)


def outline(src, ref):
    """Conturul telefoanelor: (alfa, pixelii de recolorat, de unde isi iau culoarea).

    Se masoara o singura data, pe limba de referinta: telefoanele sunt aceeasi randare
    in toate limbile, dar in unele screenshot-uri au umbra dedesubt, iar acolo conturul
    dintre latura metalica si umbra nu se poate masura curat.
    """
    x, y, w, h = BOX
    rgb = load(src)
    H, W = rgb.shape[:2]

    # silueta din export, adusa in coordonatele sursei
    old = Image.open(ref).getchannel('A').resize((round(w), round(h)), Image.BICUBIC)
    prior = np.zeros((H, W), bool)
    prior[PAD:PAD + old.height, PAD:PAD + old.width] = np.asarray(old) > 128
    core = ndimage.binary_erosion(prior, iterations=BAND)      # sigur telefon
    reach = ndimage.binary_dilation(prior, iterations=BAND)    # dincolo de ea, sigur fundal

    # variatia locala: maximul pe canale al gradientului
    grad = np.zeros((H, W))
    for c in range(3):
        g = ndimage.gaussian_filter(rgb[..., c], 0.6)
        grad = np.maximum(grad, np.hypot(ndimage.sobel(g, 0), ndimage.sobel(g, 1)) / 4)

    # fundal = zonele netede legate de exteriorul benzii
    passable = (~core) & ((grad < SMOOTH) | ~reach)
    labels, _ = ndimage.label(passable)
    outside = np.unique(labels[~reach])
    bg = np.isin(labels, outside[outside > 0])
    phone = ndimage.binary_fill_holes(~bg)
    labels, n = ndimage.label(phone)
    phone = labels == 1 + np.argmax(ndimage.sum(phone, labels, range(1, n + 1)))

    # firul de fundal ramas lipit de rama neagra: pixeli de contur deschisi, in culoarea
    # fundalului (albastrui sau aproape albi), cu rama inchisa imediat langa ei.
    lum = rgb @ (0.299, 0.587, 0.114)
    paper = (lum > 150) & ((rgb[..., 2] - rgb[..., 0] > 12) | (lum > 228))
    # In unele limbi sub telefon e o umbra, iar firul dintre rama si umbra e gri neutru.
    # In afara coltului din dreapta sus (singurul loc cu muchie metalica subtire lipita
    # de rama neagra), orice pixel deschis de pe contur, lipit de rama, e fundal.
    loose = lum > 150
    loose[:PAD + CORNER, W - CORNER - PAD:] = False
    paper |= loose
    near_dark = ndimage.minimum_filter(lum, 11) < 75
    for _ in range(5):
        rim = phone & ~ndimage.binary_erosion(phone)
        phone &= ~(rim & paper & near_dark)

    # Muchia propriu-zisa: in banda din jurul conturului, alfa se calculeaza din culoare.
    # Fiecare pixel e un amestec intre fundalul de langa el si telefon; alfa = cat la suta
    # e telefon. Asa iese anti-aliasing-ul real al pozei, nu unul reconstruit din masca.
    d_in = ndimage.distance_transform_edt(phone)
    d_out = ndimage.distance_transform_edt(~phone)
    sure_bg, sure_fg = d_out >= OUTER, d_in >= INNER
    band = ~sure_bg & ~sure_fg

    def nearest(mask):
        """Pozitia si distanta celui mai apropiat pixel din masca."""
        dist, pos = ndimage.distance_transform_edt(~mask, return_indices=True)
        return pos, dist

    back = rgb[tuple(nearest(sure_bg)[0])]

    def matte(pos):
        """Alfa din culoare, pentru o alegere a culorii telefonului (pos) pe fiecare pixel."""
        span = rgb[tuple(pos)] - back
        norm = (span * span).sum(axis=2)
        mix = ((rgb - back) * span).sum(axis=2) / np.maximum(norm, 1)
        # unde telefonul si fundalul au aproape aceeasi culoare, decide masca
        return np.where(band, np.where(norm > 300, np.clip(mix, 0, 1), d_in >= 2), sure_fg)

    # Varianta generala. Unde conturul e rama neagra, culoarea telefonului e negrul ramei,
    # nu pixelul de la INNER px in interior: rama are la exterior un fir gri de 1-2 px, care
    # pe fundal inchis se vede ca o dunga, deci e tratat ca amestec intre negru si fundal.
    # Se cere ca negrul de langa contur sa fie o zona lata (rama), nu o dunga de antena de
    # pe laturile metalice.
    dark = phone & (lum < 75)
    density = ndimage.uniform_filter(dark.astype(float), 9)
    frame_pos, frame_dist = nearest(dark)
    on_frame = (frame_dist <= 4.5) & (density[tuple(frame_pos)] > 0.42)
    pos_main = np.where(on_frame[None], frame_pos, nearest(sure_fg)[0])

    # Varianta pentru coltul din dreapta sus: acolo firul gri se lateste intr-o muchie
    # metalica de cativa pixeli, care trebuie pastrata (altfel coltul pare ciupit). Trecerea
    # dintre variante se face treptat, in josul laturii.
    pos_corner = nearest(d_in >= 2)[0]
    yy, xx = np.mgrid[:H, :W]
    fade = np.clip((yy - (PAD + CORNER - FADE)) / FADE, 0, 1)
    fade[:, :W - CORNER - PAD] = 1

    alpha = ((1 - fade) * matte(pos_corner) + fade * matte(pos_main)).astype(np.float32)
    return alpha, band & (alpha < 1), tuple(pos_corner), tuple(pos_main), fade[..., None]


def cut(src, shape, dst):
    alpha, recolor, pos_corner, pos_main, fade = shape
    rgb = load(src)
    H, W = rgb.shape[:2]
    # pixelii partial transparenti primesc culoarea telefonului, fara urma de fundal
    front = (1 - fade) * rgb[pos_corner] + fade * rgb[pos_main]
    clean = np.where(recolor[..., None], front, rgb)
    out = Image.fromarray(np.dstack([clean, alpha * 255]).round().astype(np.uint8), 'RGBA')
    scale = OUT_W / BOX[2]
    out = out.resize((round(W * scale), round(H * scale)), Image.LANCZOS)
    out.save(dst, quality=92, method=6)
    print(f'  {os.path.relpath(dst, ROOT):20} -> {out.width}x{out.height}')


if len(sys.argv) < 2:
    sys.exit(__doc__)
shape = outline(os.path.join(sys.argv[1], FOLDERS[REF_LANG], SHOT),
                os.path.join(ROOT, '_build', 'img-original', REF_LANG, 'scan.webp'))
for lang in sys.argv[2:] or sorted(FOLDERS):
    cut(os.path.join(sys.argv[1], FOLDERS[lang], SHOT), shape,
        os.path.join(ROOT, 'img', lang, 'scan.webp'))
