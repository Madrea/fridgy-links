#!/usr/bin/env python3
"""Regula noua de plan (2026-11-19): Free = o singura bucatarie, partajata cu oricine; Premium = bucatarii
nelimitate. Pe toate cele 24 de pagini (index.html = ro):
  - sectiunea #familie: primul punct ("Cate bucatarii vrei") primeste eticheta Premium, iar nota de jos
    spune ce include planul gratuit (NOTE);
  - #planuri, Free: "Bucatarii multiple" -> FREE5, "Bucatarie partajata" -> FREE6;
  - #planuri, Premium: dupa "Tot ce include Free, plus:" se adauga PRO;
  - imaginile refacute de site-refresh.py primesc ?v=3 (cache).
Traducerile: verificate de un model separat (2026-11-19). Se poate rula de mai multe ori (nu dubleaza).
Editeaza HTML-ul direct (build.mjs e invechit, vezi memoria).
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

T = {  # NOTE, FREE5, FREE6, PRO
    'ro': ('Planul gratuit include o bucătărie, pe care o împarți cu cine vrei.', 'O bucătărie', 'Partajată cu cine vrei', 'Bucătării nelimitate'),
    'en': ('The free plan includes one kitchen, shared with anyone you want.', 'One kitchen', 'Shared with anyone you want', 'Unlimited kitchens'),
    'de': ('Der kostenlose Plan enthält eine Küche, die du teilen kannst, mit wem du willst.', 'Eine Küche', 'Teilen, mit wem du willst', 'Unbegrenzt viele Küchen'),
    'fr': ('Le plan gratuit inclut une cuisine, à partager avec qui tu veux.', 'Une cuisine', 'Partagée avec qui tu veux', 'Cuisines illimitées'),
    'hu': ('Az ingyenes csomagban egy konyha jár, amit bárkivel megoszthatsz.', 'Egy konyha', 'Bárkivel megosztható', 'Korlátlan számú konyha'),
    'nl': ('Het gratis plan bevat één keuken, die je deelt met wie je maar wilt.', 'Eén keuken', 'Te delen met wie je wilt', 'Onbeperkt keukens'),
    'da': ('Den gratis plan indeholder ét køkken, som du kan dele med hvem du vil.', 'Ét køkken', 'Del med hvem du vil', 'Ubegrænset antal køkkener'),
    'sv': ('I gratisplanen ingår ett kök som du kan dela med vem du vill.', 'Ett kök', 'Dela med vem du vill', 'Obegränsat antal kök'),
    'bg': ('Безплатният план включва една кухня, която споделяш с когото поискаш.', 'Една кухня', 'Споделена с когото поискаш', 'Неограничен брой кухни'),
    'es': ('El plan gratuito incluye una cocina, que puedes compartir con quien quieras.', 'Una cocina', 'Compartida con quien quieras', 'Cocinas ilimitadas'),
    'it': ('Il piano gratuito include una cucina, da condividere con chi vuoi.', 'Una cucina', 'Condivisa con chi vuoi', 'Cucine illimitate'),
    'pl': ('Plan darmowy obejmuje jedną kuchnię, którą możesz dzielić, z kim tylko chcesz.', 'Jedna kuchnia', 'Dziel ją, z kim tylko chcesz', 'Nieograniczona liczba kuchni'),
    'pt': ('O plano gratuito inclui uma cozinha, que podes partilhar com quem quiseres.', 'Uma cozinha', 'Partilhada com quem quiseres', 'Cozinhas ilimitadas'),
    'cs': ('Verze zdarma zahrnuje jednu kuchyni, kterou můžeš sdílet s kýmkoli.', 'Jedna kuchyně', 'Sdílená s kýmkoli', 'Neomezený počet kuchyní'),
    'el': ('Το δωρεάν πλάνο περιλαμβάνει μία κουζίνα, που τη μοιράζεσαι με όποιον θέλεις.', 'Μία κουζίνα', 'Τη μοιράζεσαι με όποιον θέλεις', 'Απεριόριστες κουζίνες'),
    'fi': ('Ilmaisversioon kuuluu yksi keittiö, jonka voit jakaa kenen kanssa haluat.', 'Yksi keittiö', 'Jaa kenen kanssa haluat', 'Rajattomasti keittiöitä'),
    'sk': ('Bezplatná verzia zahŕňa jednu kuchyňu, ktorú môžeš zdieľať s kýmkoľvek.', 'Jedna kuchyňa', 'Zdieľaná s kýmkoľvek', 'Neobmedzený počet kuchýň'),
    'hr': ('Besplatni plan uključuje jednu kuhinju koju dijeliš s kim god želiš.', 'Jedna kuhinja', 'Dijeli je s kim god želiš', 'Neograničen broj kuhinja'),
    'sl': ('Brezplačna različica vključuje eno kuhinjo, ki jo deliš s komer koli želiš.', 'Ena kuhinja', 'Deljena s komer koli', 'Neomejeno število kuhinj'),
    'lt': ('Nemokamame plane – viena virtuvė, kuria gali dalytis su kuo nori.', 'Viena virtuvė', 'Dalykis su kuo nori', 'Neribotas virtuvių skaičius'),
    'lv': ('Bezmaksas plānā ir viena virtuve, ko vari koplietot ar jebkuru.', 'Viena virtuve', 'Koplieto ar jebkuru', 'Neierobežots virtuvju skaits'),
    'et': ('Tasuta paketis on üks köök, mida saad jagada, kellega soovid.', 'Üks köök', 'Jaga, kellega soovid', 'Piiramatult kööke'),
    'ga': ('Tá cistin amháin sa phlean saor in aisce, agus is féidir í a roinnt le duine ar bith.', 'Cistin amháin', 'Roinn í le duine ar bith', 'Cistineacha gan teorainn'),
    'mt': ("Il-pjan b'xejn jinkludi kċina waħda, li tista' taqsamha ma' min trid.", 'Kċina waħda', "Aqsamha ma' min trid", 'Kċejjen bla limitu'),
}
PILL = '<span class="pill">Premium</span>'
CK = '<li><span class="ck y">&#10003;</span>'


def fix(path, code):
    s = open(path, encoding='utf-8').read()
    note, f5, f6, pro = T[code]
    a, b = s.index('id="familie"'), s.index('id="planuri"')
    fam = s[a:b]
    # 1. eticheta Premium pe primul punct
    m = re.search(r'(<ul class="fam-list">\s*<li>.*?<b>)(.*?)(</b>)', fam, re.S)
    if PILL not in m.group(2):
        fam = fam[:m.end(2)] + PILL + fam[m.end(2):]
    # 2. nota
    fam = re.sub(r'(<p class="fam-note">.*?<span>).*?(</span></p>)', lambda m: m.group(1) + note + m.group(2), fam,
                 count=1, flags=re.S)
    s = s[:a] + fam + s[b:]
    # 3-4. planuri
    p = s.index('id="planuri"')
    head, plans = s[:p], s[p:]
    uls = list(re.finditer(r'<ul>(.*?)</ul>', plans, re.S))[:2]
    free = re.findall(r'<li>.*?</li>', uls[0].group(1))
    items = [re.sub(r'<[^>]+>', '', x).replace('&#10003;', '') for x in free]
    if f5 not in items:
        free[5] = CK + f5 + '</li>'
        free[6] = CK + f6 + '</li>'
    prol = re.findall(r'<li>.*?</li>', uls[1].group(1))
    if CK + pro + '</li>' not in prol:
        prol.insert(1, CK + pro + '</li>')
    plans = (plans[:uls[0].start(1)] + ''.join(free) + plans[uls[0].end(1):uls[1].start(1)] + ''.join(prol)
             + plans[uls[1].end(1):])
    s = head + plans
    # 5. cache
    s = re.sub(r'(/img/[a-z]{2}/(?:fridge|recipes|profile|shopping|family)\.webp)(\?v=\d+)?"', r'\1?v=3"', s)
    open(path, 'w', encoding='utf-8').write(s)


for code in T:
    fix(os.path.join(ROOT, 'index.html' if code == 'ro' else f'{code}/index.html'), code)
    print(' ', code)
