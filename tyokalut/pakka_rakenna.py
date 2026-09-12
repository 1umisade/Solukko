# -*- coding: utf-8 -*-
"""Yhteinen rakentaja luentopakoille, joiden kortit ovat Python-tiedostoissa (biotek_kortit.py, kemia1_kortit.py).

rakenna(kurssi_pdf_kansio, parent_loppu, luennot, guid_etuliite, sisar_loppu=None):
  1) SOLUKKO.apkg patchataan paikallaan: luennon pakka luodaan kurssipakan alle (mallina sisarpakka tai kurssipakka itse),
     kortit lisataan tai paivitetaan guidin mukaan (guid = sha1(etuliite + luennon numero + kysymys)), kuvat median karttaan
     -> sivusto nayttaa kortit heti.
  2) kurssin kansioon kirjoitetaan luennon oma apkg, jossa ovat VAIN sen kortit samoilla guideilla, Ankiin tuotavaksi.
Idempotentti: toinen ajo ei lisaa mitaan. Tarkistaa laajan pituuden (45-65 sanaa), suppean (<= 16), puolipisteet ja
linkkisanojen tormaykset muihin kortteihin (kurssit/CLAUDE.md §4-5, §9).
Kuvakortit: KUVAT = {tiedosto: (pdf, sivu, 'sivu' | 'kuva')} - dia renderoidaan tai sen suurin kuva poimitaan tyokalut/kuvat/.
Luento = moduuli tai dict, jossa LEHTI (pakan lehden nimi), NRO (korttinumeron etuosa), KUVAT, KORTIT (K()-dictit)."""
import zipfile, sqlite3, tempfile, os, shutil, json, re, time, sys, hashlib, io
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, 'SOLUKKO.apkg'); KUVAT = os.path.join(SC, 'kuvat')
SEP = chr(31); MID = 1727391050


def K(q, s, l, tt, links='', kuva=None):
    return {'q': q, 's': s, 'l': l, 'tt': str(tt), 'ls': links, 'kuva': kuva}


def _g(M, k): return M[k] if isinstance(M, dict) else getattr(M, k)
def _kys(v): return re.sub(r'^\(\s*\d+(?:[.,]\d+)?\s*\)\s*', '', re.sub('<[^>]*>', '', v or '')).strip()
def sanoja(html): return len(re.sub('<[^>]*>', ' ', html).split())


def guid_for(etuliite, nro, q):
    h = hashlib.sha1(('%s-L%s|' % (etuliite, nro) + _kys(q).lower()).encode('utf-8')).digest()
    abc = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(abc[b % len(abc)] for b in h[:10])


def tee_kuvat(kansio, kuvat):
    import pymupdf
    os.makedirs(KUVAT, exist_ok=True)
    for fn, (pdf, sivu, tapa) in kuvat.items():
        out = os.path.join(KUVAT, fn)
        if os.path.exists(out): continue
        doc = pymupdf.open(os.path.join(kansio, pdf)); p = doc[sivu - 1]
        if tapa == 'sivu': p.get_pixmap(dpi=110).save(out)
        else:
            best = None
            for im in p.get_images(full=True):
                pix = pymupdf.Pixmap(doc, im[0])
                if pix.n > 4 or pix.alpha: pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                if best is None or pix.width * pix.height > best.width * best.height: best = pix
            best.save(out, jpg_quality=88) if out.endswith('.jpg') else best.save(out)
        print('  kuva:', fn, os.path.getsize(out) // 1024, 'kB')


def rakenna(kansio, parent_loppu, luennot, guid_etuliite, sisar_loppu=None):
    for M in luennot: tee_kuvat(kansio, _g(M, 'KUVAT'))
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(SRC) as z: z.extractall(work)
    db = os.path.join(work, 'collection.anki21'); con = sqlite3.connect(db); cur = con.cursor()
    decks = json.loads(cur.execute("select decks from col").fetchone()[0])
    parent = next(d for d in decks.values() if d['name'].endswith(parent_loppu))
    sisar = next(d for d in decks.values() if d['name'].endswith(sisar_loppu)) if sisar_loppu else parent
    now = int(time.time())
    # uuden noten id: juokseva luku nykyhetken ms-leimasta tai tietokannan suurimmasta id:sta ylospain (kaksi rakentajaa
    # perakkain samalla sekunnilla tormasi ennen: now*1000 + luento*1000 osui edellisen ajon ideihin)
    seuraava = [max(now * 1000, (cur.execute("select max(id) from notes").fetchone()[0] or 0) + 1, (cur.execute("select max(id) from cards").fetchone()[0] or 0) + 1)]
    muut = {}
    for nid, guid, flds in cur.execute("select id, guid, flds from notes").fetchall():
        f = flds.split(SEP)
        if len(f) > 5 and f[5].strip():
            for w in f[5].split(','):
                w = w.strip().lower()
                if w: muut.setdefault(w, (guid, _kys(f[0])))
    mediamap = json.loads(open(os.path.join(work, 'media'), encoding='utf-8').read() or '{}')
    def lisaa_media(fn):
        if fn in mediamap.values(): return
        num = str(max([int(k) for k in mediamap] + [-1]) + 1)
        shutil.copyfile(os.path.join(KUVAT, fn), os.path.join(work, num)); mediamap[num] = fn
    kaikki_nid = {}
    for li, M in enumerate(luennot):
        LEHTI, NRO, KORTIT = _g(M, 'LEHTI'), str(_g(M, 'NRO')), _g(M, 'KORTIT')
        ALKU = (M.get('ALKU', 0) if isinstance(M, dict) else getattr(M, 'ALKU', 0))   # numeroinnin alku: lisays olemassa olevaan pakkaan jatkaa sen numeroita (esim. 300 -> 1.301...)
        name = parent['name'] + '::' + LEHTI
        target = next((d for d in decks.values() if d['name'] == name), None)
        if target: did = int(target['id'])
        else:
            did = max(int(k) for k in decks) + 1
            target = dict(sisar); target.update({'id': did, 'name': name, 'mod': now, 'usn': -1}); decks[str(did)] = target
            cur.execute("update col set decks=?", (json.dumps(decks),)); print('uusi pakka:', name)
        uudet = paivitetyt = 0; nids = []; omat = {}; jak = {'1': 0, '2': 0, '3': 0}; termit = 0
        for i, k in enumerate(KORTIT):
            n = sanoja(k['l']); s = sanoja(k['s'])
            if (k['l'] and not 45 <= n <= 65) or s > 16: print('  HUOM pituus (%s): %s laaja %d suppea %d' % (NRO, k['q'], n, s))
            if ';' in re.sub('<[^>]*>', '', k['s'] + k['l']): print('  HUOM puolipiste:', k['q'])
            guid = guid_for(guid_etuliite, NRO, k['q'])
            for w in [x.strip().lower() for x in k['ls'].split(',') if x.strip()]:
                if w in omat and omat[w] != guid: print('  HUOM linkkisana kahdella kortilla (%s): %s' % (NRO, w))
                omat[w] = guid
                if w in muut and muut[w][0] != guid: print('  HUOM linkkisana on jo kortilla "%s": %s' % (muut[w][1], w))
            laaja = k['l']
            if k['kuva']: lisaa_media(k['kuva']); laaja += '<br><img src="%s">' % k['kuva']
            fields = ['(%s.%03d) %s' % (NRO, ALKU + i + 1, k['q']), k['s'], laaja, k['tt'], '', k['ls']]
            jak[k['tt']] += 1; termit += bool(k['ls'])
            sfld = re.sub('<[^>]*>', '', fields[0]).strip(); csum = int(hashlib.sha1(sfld.encode('utf-8')).hexdigest()[:8], 16)
            row = cur.execute("select id, flds from notes where guid=?", (guid,)).fetchone()
            if row:
                nid = row[0]
                if row[1] != SEP.join(fields):
                    cur.execute("update notes set flds=?, sfld=?, csum=?, mod=?, usn=-1 where id=?", (SEP.join(fields), sfld, csum, now, nid)); paivitetyt += 1
            else:
                nid = seuraava[0]; seuraava[0] += 2
                cur.execute("insert into notes values (?,?,?,?,?,?,?,?,?,?,?)", (nid, guid, MID, now, -1, '', SEP.join(fields), sfld, csum, 0, ''))
                cur.execute("insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (nid + 1, nid, did, 0, now, -1, 0, 0, ALKU + i + 1, 0, 0, 0, 0, 0, 0, 0, 0, ''))
                uudet += 1
            nids.append(nid)
        # muiden korttien linkkisanat tunnetaan nyt myos taman luennon osalta (seuraavat luennot eivat saa toistaa niita)
        for w, g in omat.items(): muut.setdefault(w, (g, LEHTI))
        kaikki_nid[li] = nids   # avain moduulin jarjestysnumero, ei LEHTI: sanastomoduuli jakaa luennon LEHTI:n
        print('%s %s: %d korttia (%d termi-), tt3/2/1 = %d/%d/%d, %d uutta, %d paivitettya' % (NRO, LEHTI, len(nids), termit, jak['3'], jak['2'], jak['1'], uudet, paivitetyt))
    con.commit(); con.close()
    io.open(os.path.join(work, 'media'), 'w', encoding='utf-8').write(json.dumps(mediamap, ensure_ascii=False))
    tmp = SRC + '.uusi'
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        vanhat = set()
        for it in zin.infolist():
            if it.filename in ('collection.anki21', 'media'): continue
            zout.writestr(it, zin.read(it.filename)); vanhat.add(it.filename)
        zout.write(db, 'collection.anki21'); zout.write(os.path.join(work, 'media'), 'media')
        for num in mediamap:
            if num not in vanhat: zout.write(os.path.join(work, num), num)
    os.replace(tmp, SRC); print('SOLUKKO.apkg patchattu')
    for li, M in enumerate(luennot):
        # Lisaysmoduulit (TIEDOSTO) eivat saa omaa apkg:ta: omistaja 12.9.2026 'poista kaikki korjaus-apkg:t ja sanastolisaykset,
        # jata VAIN SOLUKKO.apkg' - sanastokortit ovat SOLUKKO.apkg:ssa luentopakkansa alla
        if (M.get('TIEDOSTO') if isinstance(M, dict) else getattr(M, 'TIEDOSTO', None)): continue
        LEHTI = _g(M, 'LEHTI'); nids = kaikki_nid[li]; q = ','.join(str(n) for n in nids)
        w2 = tempfile.mkdtemp(); db2 = os.path.join(w2, 'collection.anki21'); shutil.copyfile(db, db2)
        con = sqlite3.connect(db2); cur = con.cursor()
        cur.execute("update notes set mod=?, usn=-1 where id in (%s)" % q, (now,))
        cur.execute("delete from cards where nid not in (%s)" % q); cur.execute("delete from notes where id not in (%s)" % q)
        cur.execute("delete from revlog"); cur.execute("delete from graves"); cur.execute("update cards set mod=?, usn=-1", (now,)); con.commit()
        used = set()
        for (flds,) in cur.execute("select flds from notes"):
            for m in re.findall(r'src\s*=\s*["\']([^"\']+)["\']', flds): used.add(os.path.basename(m))
        con.close()
        out = os.path.join(kansio, LEHTI.replace(':', ',') + '.apkg')
        if os.path.exists(out): os.remove(out)
        mm = {}; i = 0
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(db2, 'collection.anki21')
            for num, name in mediamap.items():
                if name in used: z.write(os.path.join(work, num), str(i)); mm[str(i)] = name; i += 1
            z.writestr('media', json.dumps(mm, ensure_ascii=False))
        print('kirjoitettu', os.path.relpath(out, REPO), '-', len(nids), 'korttia,', len(mm), 'kuvaa')
        shutil.rmtree(w2, ignore_errors=True)
    shutil.rmtree(work, ignore_errors=True)
