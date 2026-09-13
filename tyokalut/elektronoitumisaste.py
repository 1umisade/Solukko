# -*- coding: utf-8 -*-
"""hapetusluku / hapetusaste -> elektronoitumisaste koko kokoelmassa (kurssit/CLAUDE.md §10, omistaja 13.9.2026:
'ei saa käyttää vaan pitää puhua elektronoitumisasteesta', 'koskee myös hapetuslukua').

  1. patchaa SOLUKKO.apkg:n paikallaan (omistaja: ei erillisiä korjaus-apkg:ita - SOLUKKO.apkg tuodaan Ankiin sellaisenaan)
  2. termikortti (1.188) 'Mitä hapetusluku tarkoittaa?' -> 'Mitä elektronoitumisaste tarkoittaa?' samalla guidilla,
     vanhat sanat jäävät Kutsutaan myös -riville ja linkkisanoiksi; massakierroksen kaksoiskappale (1.518) 'Mikä on
     hapetusaste?' poistetaan, samoin rakentajan kortit joiden kysymys vaihtuu (22.012, 22.128: uusi guid, rakentaja luo ne
     uudelleen); linkkisana_korjaus.py:n POISTA_KORTIT pitää vanhat poissa uudelleenrakennuksissa
  3. päivittää korttilähteet (tyokalut/*.py, *.txt, sanasto_massa/*.txt) samalla kartalla
Idempotentti: toinen ajo ei löydä muutettavaa."""
import zipfile, sqlite3, tempfile, os, shutil, re, time, sys, io, glob
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, 'SOLUKKO.apkg')
SEP = chr(31)

KARTTA = {
    'hapetusluku': 'elektronoitumisaste', 'hapetusluvun': 'elektronoitumisasteen', 'hapetuslukua': 'elektronoitumisastetta',
    'hapetusluvussa': 'elektronoitumisasteessa', 'hapetusluvusta': 'elektronoitumisasteesta', 'hapetuslukuun': 'elektronoitumisasteeseen',
    'hapetusluvut': 'elektronoitumisasteet', 'hapetuslukujen': 'elektronoitumisasteiden', 'hapetuslukuja': 'elektronoitumisasteita',
    'hapetusluvuissa': 'elektronoitumisasteissa', 'hapetusluvulla': 'elektronoitumisasteella', 'hapetusluvuilla': 'elektronoitumisasteilla',
    'hapetusluvulle': 'elektronoitumisasteelle', 'hapetuslukuina': 'elektronoitumisasteina', 'hapetuslukuihin': 'elektronoitumisasteisiin',
    'hapetusaste': 'elektronoitumisaste', 'hapetusasteen': 'elektronoitumisasteen', 'hapetusastetta': 'elektronoitumisastetta',
    'hapetusasteessa': 'elektronoitumisasteessa', 'hapetusasteesta': 'elektronoitumisasteesta', 'hapetusasteeseen': 'elektronoitumisasteeseen',
    'hapetusasteet': 'elektronoitumisasteet', 'hapetusasteiden': 'elektronoitumisasteiden', 'hapetusasteita': 'elektronoitumisasteita',
    'hapetusasteissa': 'elektronoitumisasteissa', 'hapetusasteella': 'elektronoitumisasteella', 'hapetusasteilla': 'elektronoitumisasteilla',
}
TERMI_VANHA = 'Mitä hapetusluku tarkoittaa?'
TERMI_UUSI = 'Mitä elektronoitumisaste tarkoittaa?'
TERMI_SUPPEA = 'Atomin muodollinen varaus yhdisteessä. Kasvaa atomin hapettuessa. Kutsutaan myös: hapetusluku, hapetusaste.'
TERMI_LINKKISANAT = ('elektronoitumisaste, elektronoitumisasteen, elektronoitumisastetta, elektronoitumisasteessa, elektronoitumisasteesta, '
                     'elektronoitumisasteeseen, elektronoitumisasteet, elektronoitumisasteiden, elektronoitumisasteita, elektronoitumisasteissa, '
                     'elektronoitumisasteella, elektronoitumisasteilla, hiilen elektronoitumisaste, hiilen elektronoitumisasteen, '
                     'hiilen elektronoitumisastetta, hiilen elektronoitumisasteessa, '
                     'hapetusluku, hapetusluvun, hapetuslukua, hapetusluvussa, hapetusluvusta, hapetuslukuun, hapetusluvut, hapetuslukujen, '
                     'hapetuslukuja, hapetusluvuissa, hapetusluvulla, hapetusluvuilla, '
                     'hapetusaste, hapetusasteen, hapetusastetta, hapetusasteessa, hapetusasteesta, hapetusasteeseen, hapetusasteet, '
                     'hapetusasteiden, hapetusasteita, hapetusasteissa')
POISTA = ['Mikä on hapetusaste?',   # massakierroksen kaksoiskappale (1.518)
          'Mikä on roomalainen numero hapetusluvun merkintänä?', 'Miten nimetään metallin yhdiste, kun metallilla on useita hapetuslukuja?']   # rakentajan kortit (22.128, 22.012): kysymys vaihtuu -> uusi guid, vanha poistetaan
RX = re.compile(r'\b([Hh])(apetus(?:lu|ast)\w*)', re.UNICODE)


def korvaa(teksti):   # "Kutsutaan myös: hapetusluku" jää rauhaan
    osat = teksti.split('Kutsutaan myös:')
    if len(osat) > 1:
        return _korvaa(osat[0]) + 'Kutsutaan myös:' + 'Kutsutaan myös:'.join(osat[1:])
    return _korvaa(teksti)


def _korvaa(teksti):
    def f(m):
        sana = 'h' + m.group(2)
        if sana not in KARTTA: raise SystemExit('tuntematon muoto: ' + m.group(0))
        uusi = KARTTA[sana]
        return uusi[0].upper() + uusi[1:] if m.group(1) == 'H' else uusi
    return RX.sub(f, teksti)


def _q(f0):
    return re.sub(r'^\(\s*[\d.,]+\s*\)\s*', '', re.sub('<[^>]*>', '', f0).strip())


def kentat(flds):
    f = flds.split(SEP)
    q = _q(f[0])
    if q in (TERMI_VANHA, TERMI_UUSI):   # termikortti: kysymys, suppea ja linkkisanat asetetaan kokonaan
        f[0] = f[0].replace(TERMI_VANHA, TERMI_UUSI)
        f[1] = TERMI_SUPPEA
        f[2] = korvaa(f[2])
        if len(f) > 5: f[5] = TERMI_LINKKISANAT
        return SEP.join(f)
    return SEP.join(korvaa(x) for x in f)


# ── 1) kokoelma ─────────────────────────────────────────────────────────────────
work = tempfile.mkdtemp()
with zipfile.ZipFile(SRC) as z: z.extractall(work)
db = os.path.join(work, 'collection.anki21'); con = sqlite3.connect(db); cur = con.cursor()
now = int(time.time()); muutetut = []; poistetut = []
for nid, flds in cur.execute("select id, flds from notes").fetchall():
    if not re.search(r'hapetus(?:lu|ast)', flds, re.I): continue
    if _q(flds.split(SEP)[0]) in POISTA:
        cur.execute("delete from cards where nid=?", (nid,)); cur.execute("delete from notes where id=?", (nid,))
        poistetut.append(nid); print('  poistettu:', _q(flds.split(SEP)[0])); continue
    uusi = kentat(flds)
    if uusi == flds: continue
    sfld2 = re.sub('<[^>]*>', '', uusi.split(SEP)[0]).strip()
    cur.execute("update notes set flds=?, sfld=?, mod=?, usn=-1 where id=?", (uusi, sfld2, now, nid))
    muutetut.append(nid)
    print('  muutettu:', re.sub('<[^>]*>', '', uusi.split(SEP)[0])[:80])
con.commit(); con.close()
if muutetut or poistetut:
    tmp = SRC + '.uusi'
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            if it.filename == 'collection.anki21': zout.write(db, 'collection.anki21')
            else: zout.writestr(it, zin.read(it.filename))
    for _ in range(20):   # OneDrive pitää tiedostoa hetken lukossa
        try: os.replace(tmp, SRC); break
        except PermissionError: time.sleep(0.5)
    print('SOLUKKO.apkg patchattu:', len(muutetut), 'muutettu,', len(poistetut), 'poistettu')
else:
    print('kokoelma: ei muutettavaa')
shutil.rmtree(work, ignore_errors=True)

# ── 2) korttilähteet ────────────────────────────────────────────────────────────
for p in sorted(glob.glob(os.path.join(SC, '*.py')) + glob.glob(os.path.join(SC, '*.txt')) + glob.glob(os.path.join(SC, 'sanasto_massa', '*.txt'))):
    if os.path.basename(p) in (os.path.basename(__file__), 'linkkisana_korjaus.py', 'linkkisanat_uudet.txt'): continue   # POISTA_KORTIT ja termikortin linkkisanat sisältävät vanhat sanat tarkoituksella
    s = io.open(p, encoding='utf-8').read()
    s2 = '\n'.join(korvaa(r) for r in s.split('\n'))   # rivi kerrallaan: 'Kutsutaan myös:' suojaa vain oman rivinsä loppuosan
    if s2 != s: io.open(p, 'w', encoding='utf-8', newline='\n').write(s2); print('  lähde päivitetty:', os.path.relpath(p, SC))
