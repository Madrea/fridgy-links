# Rispy website — native review (one language per reviewer)

You are a demanding native-speaker editor and proofreader for language `<lang>`. Another agent
translated the Rispy website (food-waste app made in Romania) following
`/home/madrea_mircea/fridgy-links/_build/i18n-new/BRIEF.md` — read that brief first, it is the spec.

Review and FIX IN PLACE (edit the files directly):
1. `/home/madrea_mircea/fridgy-links/<lang>/index.html` (landing page) — compare with `en/index.html` and the Romanian original `index.html`
2. `/home/madrea_mircea/fridgy-links/_build/og/<lang>.html` (OG card)
3. `/home/madrea_mircea/fridgy-links/_build/i18n-new/<lang>/terms.html`, `privacy.html`, `meta.json` — compare with the `data-lang="en"` and `data-lang="ro"` blocks of `terms-and-conditions.html` / `privacy-policy.html`

What to look for, in order of importance:
- Meaning errors, omissions, additions vs the source (legal texts: every clause, number, deadline, right, exception must be there).
- Anything a native would find unnatural: calques, literal word-for-word phrasing, wrong collocations, stiff marketing copy, wrong idioms. Rewrite it the way a top native copywriter / legal translator would.
- Grammar, agreement, cases, diacritics, spelling, hyphenation, punctuation, quote marks, number/currency/date formats.
- Consistency with the app's own terminology and register: `/mnt/c/Users/User/fridgy-mobile/i18n/locales/<lang>/part*.ts`
  (Spanish: inline `es:` block in `/mnt/c/Users/User/fridgy-mobile/i18n/index.ts`) and `_build/store-texts.py`.
- Legal terminology: official GDPR terms in that language.
- Prices/stats exactly as in the brief. Brand is "Rispy" (correctly inflected where the grammar requires).
- HTML integrity: do not break tags/attributes; legal block tag counts must still match EN; the privacy delete
  anchor id must be `delete-profile-<lang>`. Do not touch hreflang links, the lang-menu, CSS, scripts, URLs.

Don't rewrite things that are already good just to make changes — but don't let anything mediocre through.
Do not touch other languages' files. Do not commit.

Report back briefly: number and kind of fixes made (with a few concrete before → after examples), and
anything you're unsure about that the owner should decide.
