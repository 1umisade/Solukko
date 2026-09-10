# -*- coding: utf-8 -*-
"""hydrolyysi -> vesikatkaisu koko kokoelmassa (kurssit/CLAUDE.md §10, 10.9.2026).

Tekee kaksi asiaa samasta muutoksesta:
  1. patchaa SOLUKKO.apkg:n paikallaan, jotta sivusto nayttaa uuden termin heti
  2. kirjoittaa kurssit/Vesikatkaisu-korjaus.apkg, jossa ovat VAIN muuttuneet muistiinpanot samoilla
     guideilla -> Ankiin tuonti paivittaa ne paikallaan, ja seuraava vienti ei palauta vanhaa tekstia.
Lisaksi paivittaa Vesi-luennon datatiedostot (tyokalut/vesi_L2_kortit*.py) samalla kartalla.
Idempotentti: toinen ajo ei loyda muutettavaa."""
import zipfile, sqlite3, tempfile, os, shutil, json, re, time, sys, io, glob
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, 'SOLUKKO.apkg')
OUT = os.path.join(REPO, 'kurssit', 'Vesikatkaisu-korjaus.apkg')
SEP = chr(31)

# sanakartta: taivutusmuoto -> vastine. Isolla alkava kasitellaan erikseen (alkukirjain sailyy).
KARTTA = {
    'hydrolyysi': 'vesikatkaisu', 'hydrolyysin': 'vesikatkaisun', 'hydrolyysiä': 'vesikatkaisua',
    'hydrolyysissä': 'vesikatkaisussa', 'hydrolyysistä': 'vesikatkaisusta', 'hydrolyysiin': 'vesikatkaisuun',
    'hydrolyysit': 'vesikatkaisut', 'hydrolyysejä': 'vesikatkaisuja', 'hydrolyysien': 'vesikatkaisujen',
    'hydrolyysillä': 'vesikatkaisulla', 'hydrolyysiksi': 'vesikatkaisuksi',
    'hydrolysoida': 'vesikatkaista', 'hydrolysoi': 'vesikatkaisee', 'hydrolysoituu': 'hajoaa vesikatkaisussa',
    'hydrolysoitua': 'hajota vesikatkaisussa', 'hydrolysoituvat': 'hajoavat vesikatkaisussa',
    'hydrolysoituminen': 'vesikatkaisu', 'hydrolysoitumisen': 'vesikatkaisun', 'hydrolysoitumista': 'vesikatkaisua',
}
# termikortin omat kentat kirjoitetaan kokonaan uusiksi
TERMI_VANHA = 'Mitä hydrolyysi tarkoittaa?'
TERMI_UUSI = 'Mitä vesikatkaisu tarkoittaa?'
TERMI_LINKKISANAT = ('vesikatkaisu, vesikatkaisun, vesikatkaisua, vesikatkaisussa, vesikatkaisusta, vesikatkaisuun, '
                     'vesikatkaisut, vesikatkaisujen, vesikatkaisuja, vesikatkaisulla, vesikatkaista, vesikatkaisee, '
                     'vesikatkaisureaktio, vesikatkaisureaktion, vesikatkaisureaktiota, vesikatkaisureaktiossa, '
                     'hydrolyysi, hydrolyysin, hydrolyysiä, hydrolyysissä, hydrolyysistä, hydrolyysiin')
RX = re.compile(r'\b([Hh])(ydroly\w*)', re.UNICODE)   # hydrolyysi- JA hydrolysoi-alkuiset


def korvaa(teksti):
    # "Kutsutaan myös: hydrolyysi" jaa rauhaan: korvataan vain se osa, joka on ennen Kutsutaan-rivia
    osat = teksti.split('Kutsutaan myös:')
    if len(osat) > 1:
        return _korvaa(osat[0]) + 'Kutsutaan myös:' + 'Kutsutaan myös:'.join(osat[1:])
    return _korvaa(teksti)


def _korvaa(teksti):
    def f(m):
        sana = 'h' + m.group(2)
        if sana.startswith('hydrolyaas'): return m.group(0)   # hydrolyaasi on entsyymiluokka, ei reaktio
        if sana not in KARTTA:
            raise SystemExit('tuntematon muoto: ' + m.group(0))
        uusi = KARTTA[sana]
        return uusi[0].upper() + uusi[1:] if m.group(1) == 'H' else uusi
    return RX.sub(f, teksti)


def kentat(flds):
    f = flds.split(SEP)
    q = re.sub('<[^>]*>', '', f[0]).strip()
    q = re.sub(r'^\(\s*[\d.,]+\s*\)\s*', '', q)
    if q in (TERMI_VANHA, TERMI_UUSI):   # termikortti: linkkisanat asetetaan kokonaan, Kutsutaan-rivi saa pitaa hydrolyysin
        f[0] = f[0].replace('hydrolyysi', 'vesikatkaisu')
        f[1] = korvaa(f[1])
        f[2] = korvaa(f[2]).replace('Kutsutaan myös: vedellä hajottaminen.', 'Kutsutaan myös: hydrolyysi, vedellä hajottaminen.')
        if len(f) > 5: f[5] = TERMI_LINKKISANAT
        return SEP.join(f)
    return SEP.join(korvaa(x) for x in f)


# ── 1) kokoelma ─────────────────────────────────────────────────────────────────
work = tempfile.mkdtemp()
with zipfile.ZipFile(SRC) as z: z.extractall(work)
db = os.path.join(work, 'collection.anki21'); con = sqlite3.connect(db); cur = con.cursor()
now = int(time.time()); muutetut = []
paketti = []   # kaikki vesikatkaisua koskevat muistiinpanot korjauspakettiin, muuttuivat tai eivat (uusintatuonti on turvallinen)
for nid, flds, sfld in cur.execute("select id, flds, sfld from notes").fetchall():
    if not re.search(r'hydroly|vesikatkais', flds, re.I): continue
    paketti.append(nid)
    uusi = kentat(flds)
    if uusi == flds: continue
    sfld2 = re.sub('<[^>]*>', '', uusi.split(SEP)[0]).strip()
    cur.execute("update notes set flds=?, sfld=?, mod=?, usn=-1 where id=?", (uusi, sfld2, now, nid))
    muutetut.append(nid)
    print('  muutettu:', re.sub('<[^>]*>', '', uusi.split(SEP)[0])[:70])
con.commit()
if not muutetut:
    print('ei muutettavaa'); con.close(); shutil.rmtree(work, ignore_errors=True); sys.exit()

# patchattu kokoelma takaisin SOLUKKO.apkg:ksi (kaikki muut tiedostot zipista sellaisinaan)
con.close()
tmp = SRC + '.uusi'
with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    for it in zin.infolist():
        if it.filename == 'collection.anki21': zout.write(db, 'collection.anki21')
        else: zout.writestr(it, zin.read(it.filename))
os.replace(tmp, SRC)
print('SOLUKKO.apkg patchattu:', len(muutetut), 'muistiinpanoa')

# ── 2) korjauspaketti: vain muuttuneet muistiinpanot ────────────────────────────
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
    z.writestr('media', json.dumps(uusi_media))
shutil.rmtree(work, ignore_errors=True)
print('korjauspaketti:', OUT, '|', len(paketti), 'muistiinpanoa | mediaa', len(uusi_media))

# ── 3) Vesi-luennon datatiedostot ───────────────────────────────────────────────
for p in sorted(glob.glob(os.path.join(SC, 'vesi_L2_kortit*.py'))):
    s = io.open(p, encoding='utf-8').read()
    s2 = korvaa(s).replace('Kutsutaan myös: vedellä hajottaminen.', 'Kutsutaan myös: hydrolyysi, vedellä hajottaminen.')
    s2 = re.sub(r'"vesikatkaisu, vesikatkaisun, vesikatkaisua, vesikatkaisussa, vesikatkaisusta, vesikatkaisuun, vesikatkaisut, vesikatkaisuja, vesikatkaista, vesikatkaisee, hajoaa vesikatkaisussa, hajota vesikatkaisussa, vesikatkaisu, vesikatkaisun, vesikatkaisua, hajoavat vesikatkaisussa"',
                '"' + TERMI_LINKKISANAT + '"', s2)
    if s2 != s: io.open(p, 'w', encoding='utf-8', newline='\n').write(s2); print('  datatiedosto paivitetty:', os.path.basename(p))
