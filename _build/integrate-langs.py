#!/usr/bin/env python3
"""Leaga limbile noi in site (se poate rula de mai multe ori, e idempotent).

- landing pages (index.html + <lang>/index.html): blocul hreflang, meniul de limbi (nume native,
  cu scroll cand nu incape), harta tarilor App Store;
- terms-and-conditions.html / privacy-policy.html: insereaza blocurile din
  _build/i18n-new/<lang>/{terms,privacy}.html (+ meta.json), meniul, titlurile, etichetele, codurile;
- netlify/edge-functions/lang-redirect.js: lista SUPPORTED.

    python3 _build/integrate-langs.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://fridgy.org'
ACTIVE = ' class="active"'
COOKIE = "document.cookie='fridgy-lang={l};path=/;max-age=31536000;samesite=lax;secure'"

LANGS = [
    ('ro', 'Română'), ('en', 'English'), ('es', 'Español'), ('fr', 'Français'),
    ('de', 'Deutsch'), ('it', 'Italiano'), ('pt', 'Português'), ('nl', 'Nederlands'),
    ('pl', 'Polski'), ('cs', 'Čeština'), ('sk', 'Slovenčina'), ('hu', 'Magyar'),
    ('sv', 'Svenska'), ('da', 'Dansk'), ('fi', 'Suomi'), ('et', 'Eesti'),
    ('lv', 'Latviešu'), ('lt', 'Lietuvių'), ('el', 'Ελληνικά'), ('bg', 'Български'),
    ('hr', 'Hrvatski'), ('sl', 'Slovenščina'), ('ga', 'Gaeilge'), ('mt', 'Malti'),
]
CODES = [l for l, _ in LANGS]
NAMES = dict(LANGS)
# numele limbilor in limba paginii (CLDR, generat cu babel): NAMES_IN[limba paginii][limba]
NAMES_IN = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lang-names.json'), encoding='utf-8'))
# limba -> magazinul App Store al tarii (Apple foloseste codul tarii)
STORE = {'ro': 'ro', 'de': 'de', 'fr': 'fr', 'nl': 'nl', 'da': 'dk', 'sv': 'se', 'es': 'es', 'it': 'it',
         'pt': 'pt', 'pl': 'pl', 'cs': 'cz', 'sk': 'sk', 'fi': 'fi', 'et': 'ee', 'lv': 'lv', 'lt': 'lt',
         'el': 'gr', 'bg': 'bg', 'hr': 'hr', 'sl': 'si', 'ga': 'ie', 'mt': 'mt', 'hu': 'hu'}
STORE_OK = sorted(set(STORE.values()) | {'at', 'ch', 'be', 'lu', 'cy'})


def rd(p):
    with open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return f.read()


def wr(p, s):
    with open(os.path.join(ROOT, p), 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def url(l):
    return f'{SITE}/' if l == 'ro' else f'{SITE}/{l}'


def page_path(l):
    return 'index.html' if l == 'ro' else f'{l}/index.html'


def sub1(pattern, repl, s, flags=re.S):
    out, n = re.subn(pattern, lambda m: repl, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'pattern not found: {pattern[:60]}')
    return out


# ---------------------------------------------------------------- landing pages
def landing(l):
    p = page_path(l)
    s = rd(p)
    alt = '\n'.join(f'<link rel="alternate" hreflang="{c}" href="{url(c)}" />' for c in CODES)
    alt += f'\n<link rel="alternate" hreflang="x-default" href="{SITE}/" />'
    s = sub1(r'<link rel="alternate" hreflang=.*?hreflang="x-default"[^>]*/>', alt, s)

    items = ''.join(
        f'<a href="{"/" if c == "ro" else "/" + c}" hreflang="{c}"'
        f'{ACTIVE if c == l else ""} onclick="{COOKIE.format(l=c)}">{NAMES_IN[l][c]}</a>'
        for c in CODES)
    s = sub1(r'<div class="lang-menu">.*?</div>', f'<div class="lang-menu">{items}</div>', s)

    s = re.sub(r'var ok=\{[^}]*\}, byLang=\{[^}]*\};',
               'var ok={' + ','.join(f'{c}:1' for c in STORE_OK) + '}, byLang={'
               + ','.join(f'{k}:\'{v}\'' for k, v in STORE.items()) + '};', s, count=1)
    wr(p, s)


def fix_css(p):
    """Meniul are acum 24 de limbi: scroll cand nu incape pe ecran."""
    s = rd(p)
    if '.lang-menu{max-height' in s:
        return
    m = re.search(r'\.lang-menu a\.active\{[^}]*\}', s)
    rule = m.group(0) + '\n/* meniu limbi: scroll */\n.lang-menu{max-height:min(68vh,520px);overflow-y:auto;overscroll-behavior:contain}'
    s = s[:m.start()] + rule + s[m.end():]
    wr(p, s)


# ---------------------------------------------------------------- legal pages
def block_end(s, start):
    """Indexul de dupa </div>-ul care inchide <div ...> de la `start`."""
    depth = 0
    for m in re.finditer(r'<div\b|</div>', s[start:]):
        depth += 1 if m.group(0) != '</div>' else -1
        if depth == 0:
            return start + m.end()
    raise SystemExit('unbalanced div')


def legal(p, kind, title_var):
    s = rd(p)
    metas = {}
    for c in CODES:
        mp = os.path.join(ROOT, '_build/i18n-new', c, 'meta.json')
        if os.path.exists(mp):
            metas[c] = json.load(open(mp, encoding='utf-8'))
    for c in CODES:
        if f'data-lang="{c}"' in s:
            continue
        bp = os.path.join(ROOT, '_build/i18n-new', c, f'{kind}.html')
        if not os.path.exists(bp):
            print(f'  ! {p}: lipseste {c}')
            continue
        blk = open(bp, encoding='utf-8').read().strip()
        if not blk.startswith(f'<div class="content" data-lang="{c}"'):
            raise SystemExit(f'{bp}: nu incepe cu blocul asteptat')
        blk = blk.replace('id="delete-profile-en"', f'id="delete-profile-{c}"')
        starts = [m.start() for m in re.finditer(r'<div class="content" data-lang="', s)]
        end = block_end(s, starts[-1])
        s = s[:end] + f'\n\n    <!-- {NAMES[c]} -->\n    ' + blk + s[end:]

    present = [c for c in CODES if f'data-lang="{c}"' in s]
    menu = '\n'.join(f'                <a data-l="{c}" onclick="switchLang(\'{c}\')">{NAMES[c]}</a>' for c in present)
    s = sub1(r'<div class="lang-drop-menu">.*?</div>', f'<div class="lang-drop-menu">\n{menu}\n            </div>', s)
    if '.lang-drop-menu{max-height' not in s:
        m = re.search(r'\.lang-drop-menu a\.active\{[^}]*\}', s)
        s = s[:m.end()] + '\n        .lang-drop-menu{max-height:min(68vh,520px);overflow-y:auto;overscroll-behavior:contain}' + s[m.end():]

    # titluri + "inapoi la site": pastreaza valorile existente, adauga ce vine din meta.json
    def merge_obj(var, key):
        nonlocal s
        m = re.search(r'var ' + var + r' = \{(.*?)\};', s, re.S)
        cur = dict(re.findall(r"(\w\w):\s*(\"[^\"]*\"|'[^']*')", m.group(1)))
        for c in present:
            if c not in cur and c in metas:
                cur[c] = json.dumps(metas[c][key], ensure_ascii=False)
        body = ',\n'.join(f'        {c}: {cur[c]}' for c in present if c in cur)
        s = s[:m.start()] + f'var {var} = {{\n{body}\n    }};' + s[m.end():]

    merge_obj(title_var, f'{kind}_title')
    merge_obj('backLabels', 'back_label')
    names = ',\n'.join('        ' + ui + ':{' + ','.join(f"{c}:{json.dumps(NAMES_IN[ui][c], ensure_ascii=False)}" for c in CODES) + '}'
                         for ui in CODES)
    s = sub1(r'var langNames = \{.*?\n    \};|var langNames = \{\};[^\n]*', 'var langNames = {\n' + names + '\n    };', s)
    s = sub1(r"var supportedLangs = \[[^\]]*\];", 'var supportedLangs = [' + ', '.join(f"'{c}'" for c in present) + '];', s)
    codes = '{' + ','.join(f"{c}:'{c.upper()}'" for c in present) + '}'
    s = re.sub(r'var (codes2?) = \{[^}]*\};', lambda m: f'var {m.group(1)} = {codes};', s)
    wr(p, s)
    return present


def redirect():
    p = 'netlify/edge-functions/lang-redirect.js'
    present = [c for c in CODES if os.path.exists(os.path.join(ROOT, page_path(c)))]
    s = sub1(r"const SUPPORTED = \[[^\]]*\];", 'const SUPPORTED = [' + ', '.join(f"'{c}'" for c in present) + '];', rd(p))
    wr(p, s)
    return present


if __name__ == '__main__':
    pages = [c for c in CODES if os.path.exists(os.path.join(ROOT, page_path(c)))]
    for c in pages:
        landing(c)
        fix_css(page_path(c))
    print('landing:', ' '.join(pages))
    print('terms:  ', ' '.join(legal('terms-and-conditions.html', 'terms', 'titles')))
    print('privacy:', ' '.join(legal('privacy-policy.html', 'privacy', 'pageTitles')))
    print('redirect:', ' '.join(redirect()))
