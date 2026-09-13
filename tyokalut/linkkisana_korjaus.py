# -*- coding: utf-8 -*-
"""Linkkisanojen paallekkaisyyksien korjaus kasin tehtyihin kortteihin (omistaja 12.9.2026: 'tottakai tumallinen ei pitaisi
linkata tumaan vaan eukaryoottiin', kromosomin pilus 'ilmiselva virhe'). Sama sana saa olla linkkisanana vain yhdella
kortilla, koska sivusto linkittaa ensimmaiseen osumaan. POISTOT: (kysymyksen alku, poistettava sanan alku).
  1. patchaa SOLUKKO.apkg:n paikallaan
  2. (korjaus-apkg:ta ei enaa kirjoiteta, omistaja 12.9.2026) - samat muutokset tehdaan Ankiin kasin
Idempotentti. Aja: python tyokalut/linkkisana_korjaus.py"""
import zipfile, sqlite3, tempfile, os, shutil, json, re, time, io

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, 'SOLUKKO.apkg')
SEP = '\x1f'
POISTOT = [('(1.020) Mikä on tuma?', 'tumallis'), ('(1.020) Mikä on tuma?', 'tumallinen'),
           ('(1.033) Mikä on kromosomi?', 'pilu')]
# LISAYKSET: (kysymyksen alku, lisattavat sanat) - kromosomi maaritellaan omistajan L1-kortilla, ei L3:n sanastossa
LISAYKSET = [('(1.033) Mikä on kromosomi?', ['kromosomi', 'kromosomin', 'kromosomia', 'kromosomissa', 'kromosomista', 'kromosomiin',
              'kromosomit', 'kromosomien', 'kromosomeja', 'kromosomeissa', 'kromosomisto', 'kromosomiston', 'kromosomistoa'])]
# POISTA_KORTIT: kaksoismaaritelmat, jotka on poistettu sanastomoduuleista mutta jaavat omistajan Ankiin (tuonti ei poista);
# poistetaan SOLUKKO.apkg:sta joka ajolla, kunnes omistaja poistaa ne Ankista kasin
POISTA_KORTIT = ['(3.107) Mikä on kromosomi?',
                 '(2.034) Mikä on lähetti-RNA-rokote?',
                 '(32.034) Mikä on valenssielektroni?',
                 '(1.997) Mikä on ulkoelektroni?',
                 '(1.514) Mikä on gram-negatiivinen bakteeri?', '(1.705) Mikä on malliorganismi?',
                 '(1.518) Mikä on hapetusaste?', '(22.128) Mikä on roomalainen numero hapetusluvun merkintänä?',
                 '(22.012) Miten nimetään metallin yhdiste, kun metallilla on useita hapetuslukuja?']   # elektronoitumisaste (omistaja 13.9.2026): 1.518 on omistajan 1.188-kortin kaksoiskappale, 22.128 nimetty uudelleen   # massakierroksen kaksoiskortit omistajan korteille   # ulkoelektroni on pintaelektroni-kortin linkkisana   # nimetty pintaelektroniksi (omistaja 13.9.2026)   # biotek L2:n kaksoiskortti omistajan L1-kortille, nimetty uudelleen nukleiinihapporokotteeksi 12.9.2026
# luentopakan oma Esittely (vain kurssipakalla saa olla, kurssit/CLAUDE.md §6): tuli takaisin vanhasta Vesikatkaisu-korjaus.apkg:sta
POISTA_ESITTELY_PAKAT = ['Luento 2 - Vesi']

if __name__ == '__main__':
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(SRC) as z: z.extractall(work)
    db = os.path.join(work, 'collection.anki21'); con = sqlite3.connect(db); cur = con.cursor()
    models = json.loads(cur.execute("select models from col").fetchone()[0])
    now = int(time.time()); muutetut = []; paketti = []   # paketti: kaikki saannon kortit, myos jo korjatut (Ankiin)
    decks = json.loads(cur.execute("select decks from col").fetchone()[0])
    for nid, flds in cur.execute("select id, flds from notes").fetchall():
        q = re.sub('<[^>]*>', '', flds.split(SEP)[0]).replace('&nbsp;', ' ').strip()
        did = cur.execute("select did from cards where nid=?", (nid,)).fetchone()
        pakka = decks[str(did[0])]['name'].split('::')[-1] if did else ''
        if q in POISTA_KORTIT or (q == 'Esittely' and pakka in POISTA_ESITTELY_PAKAT):
            cur.execute("delete from cards where nid=?", (nid,)); cur.execute("delete from notes where id=?", (nid,)); muutetut.append(nid)
            print('  poistettu kortti', q, '(poista se myos Ankista kasin)')
    # Arkisanat: sanasto_massa/arkisanat.txt:n sanojen kortit kuuluvat SOLUKKO::Arkisanat-pakkaan (omistaja 13.9.2026). Ankin tuonti
    # ei siirra olemassa olevia kortteja, joten omistajan vienti voi tuoda ne takaisin luentopakkoihin - siirretaan joka ajolla.
    arki = next((d for d in decks.values() if d['name'] == 'SOLUKKO::Arkisanat'), None)
    ARKISANAT = set(w.strip() for w in io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sanasto_massa', 'arkisanat.txt'), encoding='utf-8') if w.strip() and not w.startswith('#'))
    if arki:
        siirto = []
        for cid, did, flds in cur.execute("select c.id, c.did, n.flds from cards c join notes n on n.id=c.nid").fetchall():
            q = re.sub('<[^>]*>', '', flds.split(SEP)[0]); m = re.match(r'\(\d+\.\d+\) Mitä (.+?) tarkoittaa\?$', q)
            if m and m.group(1) in ARKISANAT and did != int(arki['id']): siirto.append(cid)
        for cid in siirto: cur.execute("update cards set did=?, mod=?, usn=-1 where id=?", (int(arki['id']), now, cid)); muutetut.append(cid)
        if siirto: print('  siirretty Arkisanat-pakkaan:', len(siirto), 'korttia')
    for nid, mid, flds in cur.execute("select id, mid, flds from notes").fetchall():
        f = flds.split(SEP); q = re.sub('<[^>]*>', '', f[0]).replace('&nbsp;', ' ').strip()
        names = [x['name'].lower() for x in models[str(mid)]['flds']]
        if 'linkkisanat' not in names: continue
        li = names.index('linkkisanat'); sanat = [s.strip() for s in f[li].split(',') if s.strip()]
        if any(q.startswith(k) for k, _ in POISTOT + LISAYKSET): paketti.append(nid)
        pois = [s for s in sanat if any(q.startswith(k) and s.lower().startswith(alku) for k, alku in POISTOT)]
        lisaa = [s for k, ss in LISAYKSET if q.startswith(k) for s in ss if s not in sanat]
        if not pois and not lisaa: continue
        f[li] = ', '.join([s for s in sanat if s not in pois] + lisaa)
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (SEP.join(f), now, nid)); muutetut.append(nid)
        print('  %s: poistettu %s; lisatty %s' % (q[:40], ', '.join(pois) or '-', ', '.join(lisaa) or '-'))
    con.commit(); con.close()
    if muutetut:
        tmp = SRC + '.uusi'
        with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
            for it in zin.infolist():
                if it.filename == 'collection.anki21': zout.write(db, 'collection.anki21')
                else: zout.writestr(it, zin.read(it.filename))
        os.replace(tmp, SRC); print('SOLUKKO.apkg patchattu:', len(muutetut), 'muistiinpanoa')
    else: print('SOLUKKO.apkg: ei muutettavaa')
    # korjaus-apkg:ta ei enaa kirjoiteta (omistaja 12.9.2026: vain SOLUKKO.apkg) - Ankiin muutokset tehdaan kasin
    shutil.rmtree(work, ignore_errors=True)
