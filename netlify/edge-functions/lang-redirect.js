// Redirecționează vizitatorii de pe "/" către limba lor, pe server (înainte să se încarce pagina).
// Ordine: cookie "fridgy-lang" (alegerea manuală din meniu) > Accept-Language > română.
// Boții (Googlebot etc.) primesc mereu pagina română, ca să fie indexată corect.

const SUPPORTED = ['ro', 'en', 'de', 'hu', 'fr', 'nl', 'da', 'sv'];
const BOT = /bot|crawl|spider|slurp|facebookexternalhit|embedly|whatsapp|telegram|preview|lighthouse|headless/i;

function pickLang(header) {
  if (!header) return null;
  const langs = header.split(',')
    .map((part) => {
      const [tag, ...params] = part.trim().toLowerCase().split(';');
      const q = params.find((p) => p.trim().startsWith('q='));
      return { code: tag.trim().slice(0, 2), q: q ? parseFloat(q.split('=')[1]) || 0 : 1 };
    })
    .filter((l) => l.code && l.q > 0)
    .sort((a, b) => b.q - a.q);
  const match = langs.find((l) => SUPPORTED.includes(l.code));
  return match ? match.code : 'en';
}

export default async (request, context) => {
  const ua = request.headers.get('user-agent') || '';
  if (BOT.test(ua)) return;

  const saved = context.cookies.get('fridgy-lang');
  const lang = SUPPORTED.includes(saved) ? saved : pickLang(request.headers.get('accept-language'));

  if (!lang || lang === 'ro') {
    const res = await context.next();
    res.headers.set('Vary', 'Accept-Language, Cookie');
    return res;
  }

  const url = new URL(request.url);
  return new Response(null, {
    status: 302,
    headers: {
      Location: `/${lang}${url.search}`,
      'Cache-Control': 'private, no-store',
      Vary: 'Accept-Language, Cookie',
    },
  });
};

export const config = { path: '/' };
