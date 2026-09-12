# -*- coding: utf-8 -*-
"""Linkkisanojen paallekkaisyyksien korjaus kasin tehtyihin kortteihin (omistaja 12.9.2026: 'tottakai tumallinen ei pitaisi
linkata tumaan vaan eukaryoottiin', kromosomin pilus 'ilmiselva virhe'). Sama sana saa olla linkkisanana vain yhdella
kortilla, koska sivusto linkittaa ensimmaiseen osumaan. POISTOT: (kysymyksen alku, poistettava sanan alku).
  1. patchaa SOLUKKO.apkg:n paikallaan
  2. kirjoittaa kurssit/Linkkisana-korjaus.apkg, jossa ovat VAIN muutetut muistiinpanot samoilla guideilla -> Ankiin tuotaessa
     paivittaa ne (File > Import, Update existing notes)
Idempotentti. Aja: python tyokalut/linkkisana_korjaus.py"""
import zipfile, sqlite3, tempfile, os, shutil, json, re, time, io

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, 'SOLUKKO.apkg')
OUT = os.path.join(REPO, 'kurssit', 'Linkkisana-korjaus.apkg')
SEP = '\x1f'
POISTOT = [('(1.020) Mikä on tuma?', 'tumallis'), ('(1.020) Mikä on tuma?', 'tumallinen'),
           ('(1.033) Mikä on kromosomi?', 'pilu')]
# LISAYKSET: (kysymyksen alku, lisattavat sanat) - kromosomi maaritellaan omistajan L1-kortilla, ei L3:n sanastossa
LISAYKSET = [('(1.033) Mikä on kromosomi?', ['kromosomi', 'kromosomin', 'kromosomia', 'kromosomissa', 'kromosomista', 'kromosomiin',
              'kromosomit', 'kromosomien', 'kromosomeja', 'kromosomeissa', 'kromosomisto', 'kromosomiston', 'kromosomistoa'])]
# POISTA_KORTIT: kaksoismaaritelmat, jotka on poistettu sanastomoduuleista mutta jaavat omistajan Ankiin (tuonti ei poista);
# poistetaan SOLUKKO.apkg:sta joka ajolla, kunnes omistaja poistaa ne Ankista kasin
POISTA_KORTIT = ['(3.107) Mikä on kromosomi?']
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
    con = sqlite3.connect(db); cur = con.cursor(); q = ','.join(str(n) for n in paketti)
    cur.execute("update notes set mod=?, usn=-1 where id in (%s)" % q, (now,))
    cur.execute("delete from cards where nid not in (%s)" % q); cur.execute("delete from notes where id not in (%s)" % q)
    cur.execute("delete from revlog"); cur.execute("delete from graves"); cur.execute("update cards set mod=?, usn=-1", (now,))
    con.commit()
    used = set()
    for (flds,) in cur.execute("select flds from notes"):
        for m in re.findall(r'src\s*=\s*["\']([^"\']+)["\']', flds): used.add(os.path.basename(m))
    con.close()
    mediamap = json.loads(io.open(os.path.join(work, 'media'), encoding='utf-8').read() or '{}'); uusi = {}; i = 0
    if os.path.exists(OUT): os.remove(OUT)
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(db, 'collection.anki21')
        for num, name in mediamap.items():
            if name in used and os.path.exists(os.path.join(work, num)):
                z.write(os.path.join(work, num), str(i)); uusi[str(i)] = name; i += 1
        z.writestr('media', json.dumps(uusi, ensure_ascii=False))
    print('kirjoitettu', os.path.relpath(OUT, REPO), '-', len(paketti), 'muistiinpanoa')
    shutil.rmtree(work, ignore_errors=True)
