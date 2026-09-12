# -*- coding: utf-8 -*-
"""Litran tunnus on ℓ kaikissa korteissa (kurssit/CLAUDE.md §10, omistajan linjaus 12.9.2026): mol/l -> mol/ℓ,
osmol/l -> osmol/ℓ, g/l -> g/ℓ, 10 ml -> 10 mℓ, 2 dl -> 2 dℓ, 5 l -> 5 ℓ, l/min -> ℓ/min. L/D-isomeria ja L-muoto
eivat ole litroja eika niihin kosketa (vaaditaan kauttaviiva yksikon peraan tai luku ennen yksikkoa).

Tekee saman kolmen vaiheen kierroksen kuin tyokalut/vesikatkaisu.py:
  1. patchaa SOLUKKO.apkg:n paikallaan, jotta sivusto nayttaa uuden tunnuksen heti
  2. kirjoittaa kurssit/Litra-korjaus.apkg, jossa ovat VAIN litroja sisaltavat muistiinpanot samoilla guideilla
     -> Ankiin tuonti paivittaa ne paikallaan, eika seuraava vienti palauta vanhaa tekstia
  3. paivittaa Vesi-luennon datatiedostot (tyokalut/vesi_L2_kortit*.py)
Idempotentti: toinen ajo ei loyda muutettavaa. Aja: python tyokalut/litra.py"""
import zipfile, sqlite3, tempfile, os, shutil, json, re, time, sys, io, glob
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, 'SOLUKKO.apkg')
OUT = os.path.join(REPO, 'kurssit', 'Litra-korjaus.apkg')
SEP = chr(31)

RX_PER = re.compile(r'(?<=[A-Za-zµ])/([lL])\b')                               # mol/l, osmol/L, g/l, mg/l ...
RX_NUM = re.compile(r'(?<=\d)(\s|&nbsp;| )(m|d|µ|u)?([lL])\b(?!-)|(?<=\d)(m|d|µ)([lL])\b(?!-)')      # 10 ml, 2 dl, 5 l, 10ml (ei L-muoto); luku + paljas l ilman valia ('2l + 1' kvanttiluvuissa) ei ole litra
RX_MIN = re.compile(r'\b([lL])(?=/min\b)')                                     # l/min
ETSI = re.compile(r'[A-Za-zµ]/[lL]\b|\d(\s|&nbsp;| )[mdµu]?[lL]\b(?!-)|\d[mdµ][lL]\b(?!-)|\b[lL]/min\b')


def korvaa(t):
    t = RX_PER.sub('/ℓ', t)
    t = RX_NUM.sub(lambda m: (m.group(1) or '') + (m.group(2) or m.group(4) or '').replace('u', 'µ') + 'ℓ', t)
    t = RX_MIN.sub('ℓ', t)
    return t


if __name__ == '__main__':
    # ── 1) kokoelma ───────────────────────────────────────────────────────────────
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(SRC) as z: z.extractall(work)
    db = os.path.join(work, 'collection.anki21'); con = sqlite3.connect(db); cur = con.cursor()
    now = int(time.time()); muutetut = []; paketti = []
    for nid, flds, sfld in cur.execute("select id, flds, sfld from notes").fetchall():
        if not (ETSI.search(flds) or 'ℓ' in flds): continue
        paketti.append(nid)
        uusi = SEP.join(korvaa(x) for x in flds.split(SEP))
        if uusi == flds: continue
        sfld2 = re.sub('<[^>]*>', '', uusi.split(SEP)[0]).strip()
        cur.execute("update notes set flds=?, sfld=?, mod=?, usn=-1 where id=?", (uusi, sfld2, now, nid))
        muutetut.append(nid)
        print('  muutettu:', re.sub('<[^>]*>', '', uusi.split(SEP)[0])[:70])
    con.commit(); con.close()
    if muutetut:
        tmp = SRC + '.uusi'
        with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
            for it in zin.infolist():
                if it.filename == 'collection.anki21': zout.write(db, 'collection.anki21')
                else: zout.writestr(it, zin.read(it.filename))
        os.replace(tmp, SRC)
        print('SOLUKKO.apkg patchattu:', len(muutetut), 'muistiinpanoa')
        # ── 2) korjauspaketti: litroja sisaltavat muistiinpanot samoilla guideilla ─────
        con = sqlite3.connect(db); cur = con.cursor()
        q = ','.join(str(n) for n in paketti)
        cur.execute("update notes set mod=?, usn=-1 where id in (%s)" % q, (now,))
        cur.execute("delete from cards where nid not in (%s)" % q); cur.execute("delete from notes where id not in (%s)" % q)
        cur.execute("delete from revlog"); cur.execute("delete from graves")
        cur.execute("update cards set mod=?, usn=-1", (now,)); con.commit()
        used = set()
        for (flds,) in cur.execute("select flds from notes"):
            for m in re.findall(r'src\s*=\s*["\']([^"\']+)["\']', flds): used.add(os.path.basename(m))
        con.close()
        mediamap = json.loads(open(os.path.join(work, 'media'), encoding='utf-8').read() or '{}')
        uusi_media = {}; i = 0
        if os.path.exists(OUT): os.remove(OUT)
        with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(db, 'collection.anki21')
            for num, name in mediamap.items():
                if name in used and os.path.exists(os.path.join(work, num)):
                    z.write(os.path.join(work, num), str(i)); uusi_media[str(i)] = name; i += 1
            z.writestr('media', json.dumps(uusi_media, ensure_ascii=False))
        print('kirjoitettu', os.path.relpath(OUT, REPO), '-', len(paketti), 'muistiinpanoa')
    else:
        print('kokoelmassa ei muutettavaa')
    shutil.rmtree(work, ignore_errors=True)
    # ── 3) Vesi-luennon datatiedostot ───────────────────────────────────────────────
    for fn in sorted(glob.glob(os.path.join(SC, 'vesi_L2_kortit*.py'))):
        s = io.open(fn, encoding='utf-8', newline='').read(); u = korvaa(s)
        if u != s: io.open(fn, 'w', encoding='utf-8', newline='').write(u); print('paivitetty', os.path.relpath(fn, REPO))
