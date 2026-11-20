#!/usr/bin/env python3
"""Eticheta butonului din mijloc din bara de jos ("Fridge" -> "Kitchen" etc.), pe iPhone 3, 5, 9, 10
si Android 3, 4, 6, 7 (acolo butonul nu e activ).

Eticheta noua se ia din captura limbii din fridgy finished/frigider/ (IMG_4091.., ordinea din
swap-fridge-family.py). Acolo butonul e activ (text alb peste pastila); se reface fundalul pastilei
(polinom pe pixelii din jur) si de aici iese opacitatea fiecarui pixel al textului. Pe captura, eticheta
inactiva e alb la ~78% opacitate, iar in pozele 5/10 (Android 6/7) tot ecranul e intunecat; de aceea
culoarea textului se masoara pe eticheta veche din fiecare poza (miezul literelor), nu se presupune.

In poza de magazin: eticheta veche se sterge cu fundalul barei refacut pe banda etichetei (polinom pe
pixelii fara text), apoi stratul nou se pune la scara si pozitia ecranului (aceeasi transformare
captura -> telefon ca in pill-swap.py).

Originalele se citesc din `_backup Nav 2026-11-19/`, deci scriptul se poate rula de mai multe ori.
Utilizare: nav-label.py [Limba ...]   (implicit: toate cele 24)
"""
import importlib.util
import os
import shutil
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ps = load('pill_swap', 'pill-swap.py')
sf = load('swap_ff', 'swap-fridge-family.py')
FINISHED = ps.FINISHED
BACKUP = os.path.join(FINISHED, '_backup Nav 2026-11-19')
ORDER = sf.ORDER
FILES = {'iphone': ['iPhone 6.9_ - %d.0.jpg' % n for n in (3, 5, 9, 10)],
         'android': ['Android Phone - %d.0.jpg' % n for n in (3, 4, 6, 7)]}

# in captura (1290x2796): banda etichetei si fereastra butonului din mijloc (intre pastilele vecine)
LAB_Y = (2590, 2630)
TAB_X = (528, 762)
CX = 645


def label_layer(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    y0, y1 = LAB_Y
    s = a[y0:y1, TAB_X[0]:TAB_X[1]]
    white = s.min(2) > 200
    ring = ~nd.binary_dilation(white, iterations=4) & (s.min(2) < 190) & (s.min(2) > 120)  # pastila, fara margine
    bg, err = ps.fit_bg(s, ring)
    al = np.clip(((s - bg) / (255 - bg)).mean(2), 0, 1)
    al[~nd.binary_dilation(white, iterations=3)] = 0
    xs = np.nonzero((al > 0.02).any(0))[0]
    x0, x1 = xs.min() - 2, xs.max() + 3
    if x0 < 4 or x1 > al.shape[1] - 4:
        raise ValueError(f'{path}: eticheta atinge marginea ferestrei butonului')
    return al[:, x0:x1], (TAB_X[0] + x0, y0), err


def place_crop(A, origin, d, box):
    """Stratul A (captura) in coordonatele pozei, doar pe cutia box=(x0,y0,x1,y1); supraesantionat 4x."""
    bx0, by0, bx1, by1 = box
    W, H = bx1 - bx0, by1 - by0
    k = 4
    img = Image.fromarray(A.astype(np.float32), 'F')
    ox = d['DX'] + d['K'] * origin[0] - bx0
    oy = d['DY'] + d['K'] * origin[1] - by0
    sc = d['K'] * k
    big = img.transform((W * k, H * k), Image.AFFINE, (1 / sc, 0, -ox * k / sc, 0, 1 / sc, -oy * k / sc),
                        Image.BICUBIC)
    return np.clip(np.asarray(big, np.float32).reshape(H, k, W, k).mean((1, 3)), 0, 1)


def swap(img, A, origin, d):
    a = np.asarray(img).astype(float)
    K, DX, DY = d['K'], d['DX'], d['DY']
    bx0, bx1 = int(DX + K * TAB_X[0]), int(DX + K * TAB_X[1]) + 1
    by0, by1 = int(DY + K * (LAB_Y[0] - 2)), int(DY + K * (LAB_Y[1] + 4)) + 1
    s = a[by0:by1, bx0:bx1]
    lum = s.mean(2)
    # eticheta veche: pixelii mult mai deschisi decat fundalul barei (fundalul = mediana pe coloana, robust)
    base = np.median(lum, 0)[None, :]
    old = lum - base > 18
    lab, n = nd.label(nd.binary_dilation(old, iterations=1))
    sizes = nd.sum(old, lab, range(1, n + 1))
    keep = [i + 1 for i, v in enumerate(sizes) if v >= 3]
    old = np.isin(lab, keep) & old
    hole = nd.binary_dilation(old, iterations=3)
    ring = ~nd.binary_dilation(old, iterations=5)
    bg, err = ps.fit_bg(s, ring)
    # culoarea textului vechi: miezul literelor (cei mai deschisi pixeli), relativ la fundal
    oys, oxs = np.nonzero(old)
    core = (lum - bg.mean(2))[old]
    sel = core >= np.percentile(core, 85)
    color = s[old][sel].mean(0)
    bgc = bg[old][sel].mean(0)
    feather = np.clip(nd.gaussian_filter(hole.astype(float), 0.8) * 1.6, 0, 1)[..., None]
    out = s * (1 - feather) + bg * feather
    al = place_crop(A, origin, d, (bx0, by0, bx1, by1))[..., None]
    # textul nou: acelasi contrast fata de fundal ca miezul literelor vechi
    out = out + al * (color - bgc)[None, None, :]
    a[by0:by1, bx0:bx1] = out
    nys, nxs = np.nonzero(al[..., 0] > 0.05)
    info = {'old_x': (bx0 + oxs.min(), bx0 + oxs.max()), 'new_x': (bx0 + nxs.min(), bx0 + nxs.max()),
            'old_y': (by0 + oys.min(), by0 + oys.max()), 'new_y': (by0 + nys.min(), by0 + nys.max()),
            'color': tuple(np.round(color).astype(int)), 'bg_err': round(err, 2)}
    return Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8)), info


def main():
    langs = sys.argv[1:] or ORDER
    for lang in langs:
        cap = os.path.join(FINISHED, 'frigider', f'IMG_{4091 + ORDER.index(lang)}.png')
        A, origin, err = label_layer(cap)
        for name, d in ps.DEVICES.items():
            for f in FILES[name]:
                dst = os.path.join(FINISHED, lang, d['dir'], f)
                src = os.path.join(BACKUP, lang, d['dir'], f)
                if not os.path.exists(src):
                    os.makedirs(os.path.dirname(src), exist_ok=True)
                    shutil.copy2(dst, src)
                out, info = swap(Image.open(src).convert('RGB'), A, origin, d)
                out.save(dst, 'JPEG', quality=98, subsampling=0, optimize=True)
                print(lang.ljust(11), f.ljust(24), 'cap err', round(err, 2), info)


if __name__ == '__main__':
    main()
