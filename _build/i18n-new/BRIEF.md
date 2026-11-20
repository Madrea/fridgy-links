# Rispy website — translation brief (one language per agent)

Rispy (formerly Fridgy) is a mobile app against food waste: scan grocery receipts, track what's in
the fridge and when it expires, get recipes from what's about to expire, shared fridges for families,
shopping list, monthly budget, statistics. Made in Romania. The brand name is **Rispy** (never "Fridgy").

Repo: `/home/madrea_mircea/fridgy-links` (static site, Netlify). Site domain stays `fridgy.org`
for now; contact email is `contact@rispy.app`. Do NOT change URLs, emails, `fridgy-lang` cookie,
`com.madreamircea.fridgy`, `/rispy-logo.png`.

## THE MOST IMPORTANT RULE

Do NOT translate word for word. Write like a native speaker and a good copywriter of that
language would write it for a polished consumer app: natural idioms, natural word order, natural
punctuation, typographic quotes and number formats of that language. Meaning must match exactly,
but phrasing must be native. Avoid calques from English/Romanian. Be extremely careful with
grammar, diacritics, gender/case agreement and spelling. When in doubt, choose the wording a
native would actually see in a top-quality app (Apple / Google localisation quality).

Register (formal vs informal "you") and vocabulary MUST match the app's own translation, which
already exists. Read it first to learn the tone and the product terms (fridge, receipt, scan,
Premium, shopping list, budget, expiry, members, invitation...):
- `/mnt/c/Users/User/fridgy-mobile/i18n/locales/<lang>/part1.ts`, `part2.ts`, `part3.ts`
  (Spanish `es` is not there: it is inline in `/mnt/c/Users/User/fridgy-mobile/i18n/index.ts`, block `es:`)
- the App Store screenshot headlines for your language in `/home/madrea_mircea/fridgy-links/_build/store-texts.py`

Sources: English is the working source, Romanian is the original (when EN and RO differ in
nuance, RO wins). Look at the German/French versions too if helpful to see how the copy was
adapted rather than translated.

## Deliverable 1 — landing page `/home/madrea_mircea/fridgy-links/<lang>/index.html`

Start from a copy of `en/index.html` (Romanian original: `index.html`). Translate every
user-visible string: `<title>`, meta description, og:title, og:description, all headings, paragraphs,
list items, tags, buttons, stat captions, footer, `alt`/`aria-label` texts that are words.

Mechanical changes (exact):
- `<html lang="<lang>">`
- `canonical` and `og:url` → `https://fridgy.org/<lang>`; `og:image` → `https://fridgy.org/img/og-<lang>.jpg`
- every `/img/en/` → `/img/<lang>/` (keep `?v=2` suffixes)
- brand link `href="/en"` → `href="/<lang>"`
- language button text `EN` → your code in uppercase (`ES`, `IT`, `PT`, `PL`, `CS`, `SK`, `FI`, `ET`, `LV`, `LT`, `EL`, `BG`, `HR`, `SL`, `GA`, `MT`)
- legal links `?lang=en` → `?lang=<lang>`

Leave EXACTLY as in en/index.html (the coordinator regenerates them for all languages):
the `<link rel="alternate" hreflang=...>` block, the whole `<div class="lang-menu">...</div>`,
all CSS, all `<script>`, store URLs, element ids/classes, `data-count` attributes.

Content rules:
- Money stat ("€290 lost per person per year", also in the h1) and prices, in local format:
  - euro countries (es it pt fi sk et lv lt el bg hr sl ga mt): 290 € → write it the way that
    language writes euro amounts (e.g. `290 €` in most, `€290` in Irish/Maltese if that is the
    native norm). Premium: 3,99 € / month, or 39,99 € / year · save 16% (decimal comma or point per language norm).
    Bulgaria uses the euro since 1 Jan 2026 → euro, not leva.
  - pl: stat `1 240 zł`; Premium `18,49 zł` / month, `149,99 zł` / year · save 32%
  - cs: stat `7 250 Kč`; Premium `99 Kč` / month, `999 Kč` / year · save 16%
  - In numbers with a thousands space use `&nbsp;` inside the h1, a normal space inside `data-count` elements.
- "130 kg", "53%", "10 sec" → local unit/percent format (e.g. `53 %` where the norm has a space).
- The shopping-list example (“Milk” on the list vs “WHOLE MILK 3.5% 1L” on the receipt): localise it
  to a realistic product name and receipt line in that country's language, with that language's quote marks.
- Store buttons small text ("Download from" / "Available on"): use the official Apple/Google badge
  wording for the language (e.g. ES "Descárgalo en" / "Disponible en").
- "Made with 💙 in Romania" — natural local equivalent.
- "Premium" stays "Premium" unless the app locale uses something else. "Free" plan name: as in the app.
- Brand inflection: follow the language's grammar for foreign brand names (e.g. Finnish `Rispyn`,
  `Rispyä`; Hungarian-style hyphenation rules where the language requires them). Never alter the brand spelling.

## Deliverable 2 — Open Graph card `/home/madrea_mircea/fridgy-links/_build/og/<lang>.html`

Copy `_build/og/en.html`, set `img/en/` → `img/<lang>/`, translate the h1 (same as the landing h1)
and the paragraph. Keep length similar (it must fit a 1200x630 card).

## Deliverable 3 — legal texts (staging)

Files:
- `/home/madrea_mircea/fridgy-links/terms-and-conditions.html` → block `<div class="content" data-lang="en" ...>` … its closing `</div>`
- `/home/madrea_mircea/fridgy-links/privacy-policy.html` → same for its `data-lang="en"` block
(The `data-lang="ro"` blocks are the original; read them for nuance.)

Write, under `/home/madrea_mircea/fridgy-links/_build/i18n-new/<lang>/`:
- `terms.html` — ONLY the translated block, starting with `<div class="content" data-lang="<lang>" style="display:none">`
  and ending with its matching `</div>`. Identical HTML structure: same tags, nesting, classes, ids, hrefs, order.
- `privacy.html` — same for the privacy block.
- `meta.json` — `{"terms_title": "<Terms and Conditions> - Rispy", "privacy_title": "<Privacy Policy> - Rispy", "back_label": "← <Back to site>", "native_name": "<language name in itself, e.g. Español>"}`

Legal rules: precise, complete, nothing added or removed; use the established legal terminology of
that language, and for GDPR concepts use the exact terms of the official GDPR translation in that
language (controller, processor, data subject, supervisory authority, legitimate interest, etc.).
Keep company names, addresses, registration numbers, emails, URLs exactly. Dates in local format.
Still natural, readable language — not a mechanical rendering.

## Self-check before finishing

- `grep -c` / compare tag counts of your blocks vs the EN blocks (div, p, li, ul, ol, h1-h4, a, strong) — must match.
- No English or Romanian left in visible text (except brand names, "Premium", "App Store", "Google Play", "Eurostat").
- No "Fridgy" anywhere in visible text.
- Re-read everything once more as a native proofreader.

Report back briefly: files written, register used (formal/informal), any judgement calls worth a second look.
