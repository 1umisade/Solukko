# -*- coding: utf-8 -*-
"""Build the NEW "Luento 2 - Vesi" deck for Solu ja biomolekyylit from the card data in
vesi_L2_kortit*.py. The user's SOLUKKO.apkg is the template: its notetypes (same id and name,
so Anki does not spawn a "Solukko+" copy), deck tree and config are kept, every other note is
dropped, and the new notes are inserted under a new child deck of the course deck.

Guids are derived from the question text, so re-running and re-importing UPDATES the notes in
place instead of duplicating them. Order numbers "(2.001)" follow the list order.

  python tyokalut/export_solu_L2_vesi.py
"""
import zipfile, sqlite3, tempfile, os, shutil, json, re, time, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, "SOLUKKO.apkg")
KURSSI = os.path.join(REPO, "kurssit", "BKEM5030 Solu- ja biomolekyylit - teoria")
OUT = os.path.join(KURSSI, "Luento 2 - Vesi.apkg")
KUVAT = os.path.join(SC, "kuvat")
LEHTI = "Luento 2 - Vesi"
SARJA = 2                       # jarjestysnumerot (2.001), (2.002), ...

sys.path.insert(0, SC)
import vesi_L2_kortit as K1, vesi_L2_kortit_2 as K2, vesi_L2_kortit_3 as K3
KORTIT = K1.KORTIT + K2.KORTIT + K3.KORTIT
ESITTELY = K1.ESITTELY

SEP = chr(31)
_JNRX = re.compile(r'^(?:\s|&nbsp;|<[^>]*>)*\(\s*\d+(?:[.,]\d+)?\s*\)\s*')
def _kys(v):
    """Question text for comparisons: no tags, no leading order number."""
    return _JNRX.sub('', re.sub('<[^>]*>', '', v or '')).strip()
def _plain(v):
    return re.sub(r'\s+', ' ', re.sub('<[^>]*>', ' ', v or '')).strip()
def _words(v):
    # sub/sup tags are glued to their base (K<sub>w</sub> is one word), other tags separate words
    return len(_plain(re.sub(r'</?su[bp]>', '', v or '')).split())

# ── 1) sanity checks on the card data before touching anything ────────────────
virheet = []
nahty = set()
for c in KORTIT:
    q = _kys(c['k'])
    if q in nahty: virheet.append("kaksi korttia samalla etupuolella: " + q)
    nahty.add(q)
    if not q.endswith('?') and not q.endswith('.'): virheet.append("etupuoli ei ole kysymys: " + q)
    if c['tt'] not in ('1', '2', '3'): virheet.append("tenttitodennakoisyys ei ole 1-3: " + q)
    if ';' in _plain(c['s']) or ';' in _plain(c['l']): virheet.append("puolipiste: " + q)
    if c['kuva'] and not os.path.exists(os.path.join(KUVAT, c['kuva'])): virheet.append("kuva puuttuu: " + c['kuva'])
    ws, wl = _words(c['s']), _words(c['l'])
    if ws > 18: virheet.append("suppea liian pitka (%d sanaa): %s" % (ws, q))
    if wl and (wl < 40 or wl > 75): virheet.append("laaja %d sanaa (tavoite 45-65): %s" % (wl, q))
if virheet:
    print("DATAVIRHEITA:"); [print("  ", v) for v in virheet]
    if any(not v.startswith("laaja") for v in virheet): raise SystemExit(1)

# ── 2) open the user's collection ─────────────────────────────────────────────
work = tempfile.mkdtemp()
with zipfile.ZipFile(SRC) as z: z.extractall(work)
dbname = 'collection.anki21' if os.path.exists(os.path.join(work, 'collection.anki21')) else 'collection.anki2'
db = os.path.join(work, dbname)
con = sqlite3.connect(db); cur = con.cursor()
now = int(time.time())

models = json.loads(cur.execute("select models from col").fetchone()[0])
decks = json.loads(cur.execute("select decks from col").fetchone()[0])
mid = next((int(k) for k, m in models.items() if m['name'] == 'Solukko'), None)
if mid != 1727391050: raise SystemExit("Solukko-korttityyppia (1727391050) ei loytynyt: %r" % mid)
flds = [f['name'] for f in models[str(mid)]['flds']]
if flds[:3] != ['Kysymys', 'Suppea vastaus', 'Laaja vastaus'] or flds[5] != 'linkkisanat':
    raise SystemExit("kenttajarjestys yllattava: %r" % flds)

parent = next((d for d in decks.values() if d['name'].endswith('::Solu- ja biomolekyylit - teoria (BKEM5030)')), None)
if not parent: raise SystemExit("kurssipakkaa ei loytynyt")
name = parent['name'] + '::' + LEHTI
target = next((d for d in decks.values() if d['name'] == name), None)
if target:
    tid = int(target['id']); print("pakka on jo kokoelmassa:", name)
else:
    tid = max(int(k) for k in decks) + 1
    # copy the sibling deck's record shape, only id/name/mod differ
    sibling = next(d for d in decks.values() if d['name'].startswith(parent['name'] + '::'))
    target = dict(sibling); target.update({'id': tid, 'name': name, 'mod': now, 'usn': -1})
    decks[str(tid)] = target
    cur.execute("update col set decks=?", (json.dumps(decks),))
    print("uusi pakka:", name)

# ── 3) cross-check linkkisanat against every OTHER card in the collection ─────
varatut = {}
for nid, flds_ in cur.execute("select id, flds from notes where mid=?", (mid,)):
    f = flds_.split(SEP)
    if len(f) > 5 and f[5].strip():
        for w in re.sub('<[^>]*>', '', f[5]).split(','):
            w = w.strip().lower()
            if w: varatut.setdefault(w, _kys(f[0]))
tormays = []
for c in KORTIT:
    for w in [x.strip().lower() for x in c['ls'].split(',') if x.strip()]:
        if w in varatut and varatut[w] != _kys(c['k']):
            tormays.append((w, _kys(c['k']), varatut[w]))
if tormays:
    print("LINKKISANA JO KAYTOSSA TOISELLA KORTILLA:")
    for w, uusi, vanha in tormays: print("   %-40s %s  <->  %s" % (w, uusi[:40], vanha[:40]))
    raise SystemExit(1)
# also within the new deck
kaikki = {}
for c in KORTIT:
    for w in [x.strip().lower() for x in c['ls'].split(',') if x.strip()]:
        if w in kaikki and kaikki[w] != c['k']: tormays.append((w, c['k'], kaikki[w]))
        kaikki[w] = c['k']
if tormays:
    print("SAMA LINKKISANA KAHDELLA UUDELLA KORTILLA:")
    for w, a, b in tormays: print("   %-40s %s  <->  %s" % (w, a[:40], b[:40]))
    raise SystemExit(1)

# ── 4) drop everything else, insert the new notes ─────────────────────────────
cur.execute("delete from cards"); cur.execute("delete from notes")
cur.execute("delete from revlog"); cur.execute("delete from graves")

def guid_for(q):
    h = hashlib.sha1(('solukko-vesi-L2|' + _kys(q).lower()).encode('utf-8')).digest()
    abc = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(abc[b % len(abc)] for b in h[:10])

def insert(fields, i):
    sfld = re.sub('<[^>]*>', '', fields[0]).strip()
    csum = int(hashlib.sha1(sfld.encode('utf-8')).hexdigest()[:8], 16)
    nid = now * 1000 + i * 2
    cur.execute("insert into notes values (?,?,?,?,?,?,?,?,?,?,?)",
                (nid, guid_for(fields[0]), mid, now, -1, '', SEP.join(fields), sfld, csum, 0, ''))
    cur.execute("insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (nid + 1, nid, tid, 0, now, -1, 0, 0, i + 1, 0, 0, 0, 0, 0, 0, 0, 0, ''))

mediamap = {}
def add_media(fn):
    if fn in mediamap.values(): return
    num = str(len(mediamap))
    shutil.copyfile(os.path.join(KUVAT, fn), os.path.join(work, num)); mediamap[num] = fn

insert(['Esittely', '', ESITTELY, '', '', ''], 0)
jakauma = {'1': 0, '2': 0, '3': 0}; termeja = 0; kuvia = 0
for i, c in enumerate(KORTIT, start=1):
    laaja = c['l']
    if c['kuva']:
        add_media(c['kuva']); laaja += '<br><img src="%s">' % c['kuva']; kuvia += 1
    q = '(%d.%03d) %s' % (SARJA, i, c['k'])
    insert([q, c['s'], laaja, c['tt'], '', c['ls']], i)
    jakauma[c['tt']] += 1
    if c['ls']: termeja += 1
con.commit(); con.close()

# ── 5) rezip ──────────────────────────────────────────────────────────────────
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(db, dbname)
    z.writestr('media', json.dumps(mediamap))
    for num in mediamap: z.write(os.path.join(work, num), num)
shutil.rmtree(work, ignore_errors=True)

laajat = sorted(_words(c['l']) for c in KORTIT)
print("kortteja: %d (+ Esittely), termikortteja %d, kuvakortteja %d" % (len(KORTIT), termeja, kuvia))
print("tenttitodennakoisyys: 3=%d  2=%d  1=%d" % (jakauma['3'], jakauma['2'], jakauma['1']))
print("laaja vastaus: min %d, mediaani %d, max %d sanaa" % (laajat[0], laajat[len(laajat) // 2], laajat[-1]))
print("kirjoitettu:", OUT, os.path.getsize(OUT), "tavua")
