#!/usr/bin/env python3
"""Repara mockup-urile exportate gresit (fridge / recipes / profile / family).

In exporturile originale cardul "ridicat" din ecran era desenat mai lat decat
telefonul: iesea peste bezel pana la marginea panzei, iar in jurul ramei ramanea
un halou alb-albastrui. Pe fundalul inchis al paginii se vedea ca o banda alba
lipita de telefon.

Pentru fiecare imagine:
  1. detecteaza rama (banda de pixeli inchisi de pe margini);
  2. gaseste benzile de randuri unde continutul acopera bezelul si le comprima
     pe latimea ecranului, ca sa nu se piarda text la taiere;
  3. repicteaza bezelul acolo unde fusese acoperit;
  4. taie alfa la silueta rounded-rect a telefonului.

Se ruleaza pe exporturile proaspat copiate din _build/img-original/; cu un argument
(ex. "en") se limiteaza la limbile date, ca sa nu retrateze imaginile deja reparate.
"""
import os
import sys
import statistics
import subprocess
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = '/tmp/fixmock'
TARGETS = ['fridge', 'recipes', 'profile', 'family']

DARK = 110              # prag de luminanta sub care consideram ca e bezel
BEZEL = 24              # grosimea ramei, masurata pe exporturi
RADIUS = 78             # raza colturilor exterioare, masurata pe exporturi
BEZEL_COLOR = '#2b2b30'
MIN_BAND = 8            # benzi mai scurte de atat sunt zgomot
ONLY = set(sys.argv[1:])


def run(*args):
    subprocess.run(list(args), check=True)


def size(path):
    w, h = subprocess.run(['identify', '-format', '%w %h', path],
                          capture_output=True, text=True).stdout.split()
    return int(w), int(h)


def gray(path):
    return subprocess.run(['convert', path, '-alpha', 'off', '-colorspace', 'Gray',
                           '-depth', '8', 'gray:-'], capture_output=True).stdout


def frame_edges(g, w, h):
    """Marginile stanga/dreapta ale ramei: cel mai frecvent prim pixel inchis pe rand."""
    left, right = Counter(), Counter()
    for y in range(120, h - 120):
        row = g[y * w:(y + 1) * w]
        li = next((x for x in range(w) if row[x] < DARK), None)
        if li is None:
            continue
        right[next(x for x in range(w - 1, -1, -1) if row[x] < DARK)] += 1
        left[li] += 1
    return left.most_common(1)[0][0], right.most_common(1)[0][0]


def overflow_bands(g, w, h, x0, x1, bez, r_out):
    """Randurile unde bezelul e acoperit de continut, grupate in benzi.

    Un rand e "spart" daca mijlocul bandei de bezel e deschis la culoare, pe oricare
    dintre laturi. Se ia mediana pe cateva coloane ca sa nu declanseze un pixel izolat.
    """
    left = range(x0 + 4, x0 + bez - 4)
    right = range(max(0, x1 - bez + 4), min(w, x1 - 4))
    hit = []
    for y in range(h):
        row = g[y * w:(y + 1) * w]
        if (statistics.median(row[c] for c in left) > DARK
                or statistics.median(row[c] for c in right) > DARK):
            hit.append(y)
    bands = []
    for y in hit:
        # unifica benzile despartite de cateva randuri (un rand de text inchis la culoare)
        if bands and y - bands[-1][1] <= 30:
            bands[-1][1] = y
        else:
            bands.append([y, y])
    # colturile rotunjite nu sunt suprapuneri, ci curbura ramei
    return [(a, b) for a, b in bands
            if b - a + 1 >= MIN_BAND and a > r_out and b < h - 1 - r_out]


def fix(path):
    w, h = size(path)
    g = gray(path)
    x0, x1 = frame_edges(g, w, h)
    x0, x1 = max(0, x0 - 1), min(w - 1, x1 + 1)
    scale = (x1 - x0) / 752
    r_out = round(RADIUS * scale)
    bez = round(BEZEL * scale)
    r_in = r_out - bez
    sx0, sx1 = x0 + bez, x1 - bez        # aria ecranului
    sw = sx1 - sx0

    work = f'{TMP}/work.png'
    run('convert', path, work)

    # 1. comprima benzile care ies din ecran
    bands = overflow_bands(g, w, h, x0, x1, bez, r_out)
    for (a, b) in bands:
        bh = b - a + 1
        band = f'{TMP}/band.png'
        run('convert', work, '-crop', f'{w}x{bh}+0+{a}', '+repage',
            '-resize', f'{sw}x{bh}!', band)
        run('convert', work, band, '-geometry', f'+{sx0}+{a}', '-composite', work)

    # 2. masti: silueta telefonului si banda bezelului
    silhouette, ring = f'{TMP}/silhouette.png', f'{TMP}/ring.png'
    run('convert', '-size', f'{w}x{h}', 'xc:black', '-fill', 'white',
        '-draw', f'roundrectangle {x0},0 {x1},{h - 1} {r_out},{r_out}', silhouette)
    run('convert', '-size', f'{w}x{h}', 'xc:black',
        '-fill', 'white', '-draw', f'roundrectangle {x0},0 {x1},{h - 1} {r_out},{r_out}',
        '-fill', 'black', '-draw',
        f'roundrectangle {sx0},{bez} {sx1},{h - 1 - bez} {r_in},{r_in}', ring)

    # 3. repicteaza bezelul unde a ramas acoperit
    patch = f'{TMP}/patch.png'
    run('convert', work, '-alpha', 'off', '-colorspace', 'Gray',
        '-threshold', f'{DARK * 100 // 255}%', ring,
        '-compose', 'multiply', '-composite', '-blur', '0x0.6', patch)
    run('convert', work, '(', '-size', f'{w}x{h}', f'xc:{BEZEL_COLOR}', ')', patch,
        '-compose', 'over', '-composite', work)

    # 4. alfa final = alfa original ∩ silueta
    alpha = f'{TMP}/alpha.png'
    run('convert', path, '-alpha', 'extract', silhouette,
        '-compose', 'multiply', '-composite', alpha)
    run('convert', work, alpha, '-alpha', 'off',
        '-compose', 'copy_opacity', '-composite',
        '-define', 'webp:method=6', '-quality', '90', path)
    print(f'  {os.path.relpath(path, ROOT):24} rama x={x0}..{x1} bezel={bez} '
          f'benzi comprimate: {bands or "-"}')


os.makedirs(TMP, exist_ok=True)
for lang in sorted(os.listdir(os.path.join(ROOT, 'img'))):
    d = os.path.join(ROOT, 'img', lang)
    if not os.path.isdir(d) or (ONLY and lang not in ONLY):
        continue
    todo = [os.path.join(d, n + '.webp') for n in TARGETS
            if os.path.exists(os.path.join(d, n + '.webp'))]
    if not todo:
        continue
    print(lang)
    for p in todo:
        fix(p)
