// Link unic de share: fridgy.org/app → App Store pe iPhone/iPad, Google Play pe Android, landing page pe desktop.
// Boții de preview (Facebook, WhatsApp etc.) primesc app/index.html, ca să vadă tag-urile og: și să arate cardul.
// Parametrii utm_* ajung în Play Store ca "referrer", ca să vezi în Play Console din ce rețea au venit instalările.

const APP_STORE = 'https://apps.apple.com/app/id6748481042';
const PLAY_STORE = 'https://play.google.com/store/apps/details?id=com.madreamircea.fridgy';
const BOT = /bot|crawl|spider|slurp|facebookexternalhit|facebookcatalog|embedly|whatsapp|telegram|preview|lighthouse|headless|linkedin|twitter|slack|discord|pinterest/i;

function redirect(location) {
  return new Response(null, {
    status: 302,
    headers: { Location: location, 'Cache-Control': 'private, no-store', Vary: 'User-Agent' },
  });
}

export default async (request) => {
  const ua = request.headers.get('user-agent') || '';
  if (BOT.test(ua)) return;

  const url = new URL(request.url);

  if (/android/i.test(ua)) {
    const utm = [...url.searchParams].filter(([k]) => k.startsWith('utm_'));
    if (!utm.length) return redirect(PLAY_STORE);
    const referrer = new URLSearchParams(utm).toString();
    return redirect(`${PLAY_STORE}&referrer=${encodeURIComponent(referrer)}`);
  }

  // iPadOS trimite UA de Mac; pagina de fallback îl prinde pe client prin maxTouchPoints.
  if (/iphone|ipad|ipod/i.test(ua)) return redirect(APP_STORE);

  if (/macintosh/i.test(ua)) return;

  return redirect('/');
};

export const config = { path: ['/app', '/app/'] };
