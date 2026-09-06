# -*- coding: utf-8 -*-
"""Update the delivered "Johdatus biotekniikkaan" Luento 1 apkg in place: fuller linkkisanat,
genuinely broader Laaja answers, and new image cards. The user has not imported this deck yet
(their collection only holds the course's cover card), so this apkg IS the source of truth.
Editing collection.anki2x directly keeps guids, the notetype and scheduling byte-identical."""
import zipfile, sqlite3, tempfile, os, shutil, json, re, time, sys, hashlib, random
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SC)                     # tyokalut/ on repon juuressa
KURSSIT = os.path.join(REPO, "kurssit")
SRC = os.path.join(KURSSIT, "Johdatus biotekniikkaan", "Luento 1 - Mitä biotekniikka on.apkg")
KURSSI = os.path.join(KURSSIT, "Johdatus biotekniikkaan")
OUT = os.path.join(KURSSI, "Luento 1 - Mitä biotekniikka on.apkg")   # valmis pakka kurssin omaan kansioon

SEP = chr(31)
_JNRX = re.compile(r'^(?:\s|&nbsp;|<[^>]*>)*\(\s*\d+(?:[.,]\d+)?\s*\)\s*')
def _kys(v):
    """Question text for comparisons: no tags, no leading "(1.0)" order number."""
    return _JNRX.sub('', re.sub('<[^>]*>', '', v or '')).strip()
class Flds(list):
    """A note's fields, padded to 6 so f[1]/f[3]/f[5] are always safe to read.
    join() writes back the note's ORIGINAL field count — a note type with 5 or 11 fields must
    keep 5 or 11, or Anki rejects the note on import."""
    def __init__(self, flds):
        raw = flds.split(SEP)
        self.n = len(raw)
        super().__init__(raw + [''] * max(0, 6 - len(raw)))
    def join(self):
        return SEP.join(self[:self.n] if self.n <= len(self) else list(self))

work = tempfile.mkdtemp()
with zipfile.ZipFile(SRC) as z: z.extractall(work)
dbname = 'collection.anki21' if os.path.exists(os.path.join(work, 'collection.anki21')) else 'collection.anki2'
db = os.path.join(work, dbname)
con = sqlite3.connect(db); cur = con.cursor()
now = int(time.time())

models = json.loads(cur.execute("select models from col").fetchone()[0])
decks = json.loads(cur.execute("select decks from col").fetchone()[0])
target = next((d for d in decks.values() if 'Luento 1' in d.get('name', '') and 'iotekniikka' in d.get('name', '')), None)
if not target: raise SystemExit("Luento 1 -pakkaa ei loytynyt")
tid = int(target['id']); print("pakka:", target['name'])
SOLUKKO_MID = "1727391050"   # the deck's own notetype; the name varies, the id does not
solukko_mid = (next((mid for mid, m in models.items() if str(mid) == SOLUKKO_MID), None)
               or next((mid for mid, m in models.items() if m.get('name', '').startswith('Solukko')), None))
if not solukko_mid: raise SystemExit("Solukko-korttityyppia ei loytynyt (id %s)" % SOLUKKO_MID)


def apply_field(path, idx, label):
    """Apply a `front<TAB>value` file to field `idx` of the notes matched by their plain-text front."""
    if not os.path.exists(path):
        print("HUOM: %s puuttuu - %s ei paivitetty" % (os.path.basename(path), label)); return
    table = {}
    for line in open(path, encoding="utf-8"):
        if "\t" not in line: continue
        k, v = line.rstrip("\n").split("\t", 1)
        if k.strip() and v.strip(): table[k.strip()] = v.strip()
    n = 0; missed = []
    for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
        flds = cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
        f = Flds(flds)
        v = table.get(_kys(f[0]))
        if not v: continue
        f[idx] = v
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); n += 1
    print("%s: %d / %d" % (label, n, len(table)))
    if n != len(table): print("   VAROITUS: %d riviä ei osunut yhteenkään korttiin" % (len(table) - n))


apply_field(os.path.join(SC, "biotek_linkkisanat.txt"), 5, "linkkisanat laajennettu")
apply_field(os.path.join(SC, "biotek_laajat.txt"), 2, "laajoja vastauksia rikastettu")
apply_field(os.path.join(SC, "biotek_laajat2.txt"), 2, "laajoja rikastettu (2. kierros)")   # applied last: brings the rest up to the sister course's length

# 1c1e) exam probability as a plain number 1-3 (clearer to read and edit in Anki than counting stars).
#     Cards whose note type has no star field carry it as the tag tt1/tt2/tt3 instead.
_num=0; _numtag=0
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    mid,flds,tags=cur.execute("select mid,flds,tags from notes where id=?", (nid,)).fetchone()
    f=Flds(flds); tags=tags or ''
    m=models[str(mid)]
    _has=len(m['flds'])>3 and 'tenttitodenn' in m['flds'][3]['name'].lower()
    if _has:
        _v=re.sub('<[^>]*>','',f[3]).strip()
        _n=len(re.findall('\u2605',_v)) or (int(re.match(r'\d+',_v).group()) if re.match(r'\d+',_v) else 0)
        if _n and str(min(_n,3))!=f[3]:
            f[3]=str(min(_n,3))
            cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _num+=1
    # strip every rating marking from the tags (★★★, tt3, a stray number) and, when the note type has no
    # star field, put the bare number back — plain "3" reads better in Anki than "tt3".
    _old=tags.split()
    _rate=[w for w in _old if '\u2605' in w or re.fullmatch(r'tt[1-3]', w) or re.fullmatch(r'[1-3]', w)]
    if _rate:
        _n=len(re.findall('\u2605', ' '.join(_rate)))
        if not _n:
            _d=re.search(r'[1-3]', ' '.join(_rate)); _n=int(_d.group()) if _d else 0
        _keep=[w for w in _old if w not in _rate]
        if not _has and _n: _keep.append(str(min(_n,3)))
        _new=(' '+' '.join(_keep)+' ') if _keep else ''
        if _new!=tags:
            cur.execute("update notes set tags=?, mod=?, usn=-1 where id=?", (_new, now, nid)); _numtag+=1
print("tenttitodennakoisyys numeroksi: %d kenttaa, %d tagia"%(_num,_numtag))

# re-rated exam probabilities (KURSSI<TAB>KYSYMYS<TAB>N) - these override the card's current value
_ov={}
_ovp=os.path.join(SC,"arviot_uudet.txt")
if os.path.exists(_ovp):
    for _line in open(_ovp,encoding="utf-8"):
        _p=_line.rstrip('\n').split('\t')
        if len(_p)==3 and _p[0].strip()=='biotek' and _p[2].strip() in ('1','2','3'):
            _ov[_p[1].strip()]=_p[2].strip()
    print("uudelleenarvioita luettu (biotek):", len(_ov))
else:
    print("HUOM: arviot_uudet.txt puuttuu - vanhat arviot jaavat voimaan")

_ar=0
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    mid,flds=cur.execute("select mid,flds from notes where id=?", (nid,)).fetchone()
    f=Flds(flds); m=models[str(mid)]
    si=next((i for i,fl in enumerate(m['flds']) if 'tenttitodenn' in fl['name'].lower()), -1)
    if si<0: continue
    v=_ov.get(_kys(f[0]))
    if not v or f[si]==v: continue
    f[si]=v
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _ar+=1
print("tenttitodennakoisyys paivitetty:",_ar,"korttia")

# 1c1h) preferred terminology (see kurssit/CLAUDE.md). Visible fields only for the replacements;
#       linkkisanat gains the new spelling but keeps the old one as a trigger.
_TERMS=[(r'(?<![\w\u00e4\u00f6\u00e5])mRNA', 'l\u00e4hetti-RNA'),
        (r'(?<![\w\u00e4\u00f6\u00e5])solulimakalvosto(?![\w\u00e4\u00f6\u00e5])', 'endoplasminen kalvosto'),
        (r'(?<![\w\u00e4\u00f6\u00e5])solulimakalvoston(?![\w\u00e4\u00f6\u00e5])', 'endoplasmisen kalvoston'),
        (r'(?<![\w\u00e4\u00f6\u00e5])solulimakalvostoa(?![\w\u00e4\u00f6\u00e5])', 'endoplasmista kalvostoa'),
        (r'(?<![\w\u00e4\u00f6\u00e5])solulimakalvostossa(?![\w\u00e4\u00f6\u00e5])', 'endoplasmisessa kalvostossa'),
        (r'\s*\(nucleus\)', '')]
_TERMRX=[(re.compile(a), b) for a,b in _TERMS]
# the term's own card carries the alternative names
_ALIAS={'Mik\u00e4 on mRNA?':'mRNA, messenger RNA',
        'Mik\u00e4 on l\u00e4hetti-RNA?':'mRNA, messenger RNA',
        'Mik\u00e4 on tuma?':'nucleus'}
_WBL = "(?<![A-Za-z0-9_äöåÄÖÅ])"   # left word boundary; äöå are word characters here, \\w alone is not enough
_WBR = "(?![A-Za-z0-9_äöåÄÖÅ])"
_TERMRX.append((re.compile(_WBL+"nukleonukleo"), "nukleo"))   # undo the double prefix an earlier broken boundary produced
_TERMRX += [
    (re.compile(_WBL+r'sytoplasma'), 'solulima'),
    (re.compile(_WBL+r'Sytoplasma'), 'Solulima'),
    (re.compile(_WBL+r'tumakalvo'), 'tumakotelo'),
    (re.compile(_WBL+r'Tumakalvo'), 'Tumakotelo'),
    (re.compile(_WBL+r'nukleotidijärjest'), 'nukleoemäsjärjest'),
    (re.compile(_WBL+r'Nukleotidijärjest'), 'Nukleoemäsjärjest'),
    (re.compile(_WBL+r'emäsjärjest'), 'nukleoemäsjärjest'),
    (re.compile(_WBL+r'Emäsjärjest'), 'Nukleoemäsjärjest'),
    (re.compile(_WBL+r'perimä'+_WBR), 'genomi'),
    (re.compile(_WBL+r'perimän'+_WBR), 'genomin'),
    (re.compile(_WBL+r'perimää'+_WBR), 'genomia'),
    (re.compile(_WBL+r'perimässä'+_WBR), 'genomissa'),
    (re.compile(_WBL+r'perimästä'+_WBR), 'genomista'),
    (re.compile(_WBL+r'perimään'+_WBR), 'genomiin'),
    (re.compile(_WBL+r'perimät'+_WBR), 'genomit'),
    (re.compile(_WBL+r'perimien'+_WBR), 'genomien'),
    (re.compile(_WBL+r'perimiä'+_WBR), 'genomeja'),
    (re.compile(_WBL+r'perimältään'+_WBR), 'genomiltaan'),
    (re.compile(_WBL+r'perimäaineksen'+_WBR), 'genomin'),
    (re.compile(_WBL+r'perimäaines'+_WBR), 'genomi'),
    (re.compile(_WBL+r'Perimältään'+_WBR), 'Genomiltaan'),
    (re.compile(_WBL+r'Perimä'+_WBR), 'Genomi'),
]
_TERMRX.append((re.compile(r'\s*\(organelli\)'), ''))   # alias moves to the Muut nimet line
_ALIAS['Mik\u00e4 on soluelin?']='organelli'
_ALIAS['Mik\u00e4 on sytoplasma?']='sytoplasma'
_ALIAS['Mik\u00e4 on solulima?']='sytoplasma'
_ALIAS['Mik\u00e4 on genomi?']='perim\u00e4'
_ALIAS['Mik\u00e4 on tumakotelo?']='tumakalvo'

_TERMRX += [
    (re.compile(_WBL+r'eukaryoottisolusta'+_WBR), 'tumallisesta solusta'),
    (re.compile(_WBL+r'eukaryoottisolun'+_WBR), 'tumallisen solun'),
    (re.compile(_WBL+r'eukaryoottisolut'+_WBR), 'tumalliset solut'),
    (re.compile(_WBL+r'eukaryoottisolu'+_WBR), 'tumallinen solu'),
    (re.compile(_WBL+r'Eukaryoottisolut'+_WBR), 'Tumalliset solut'),
    (re.compile(_WBL+r'prokaryoottisolussa'+_WBR), 'tumattomassa solussa'),
    (re.compile(_WBL+r'prokaryoottisolun'+_WBR), 'tumattoman solun'),
    (re.compile(_WBL+r'prokaryoottisolut'+_WBR), 'tumattomat solut'),
    (re.compile(_WBL+r'prokaryoottisolu'+_WBR), 'tumaton solu'),
    (re.compile(_WBL+r'Prokaryoottisolussa'+_WBR), 'Tumattomassa solussa'),
    (re.compile(_WBL+r'Prokaryoottisolut'+_WBR), 'Tumattomat solut'),
    (re.compile(_WBL+r'eukaryoottinen'+_WBR), 'tumallinen'),
    (re.compile(_WBL+r'eukaryoottiset'+_WBR), 'tumalliset'),
    (re.compile(_WBL+r'prokaryoottinen'+_WBR), 'tumaton'),
    (re.compile(_WBL+r'prokaryoottiset'+_WBR), 'tumattomat'),
    (re.compile(_WBL+r'prokaryoottisten'+_WBR), 'tumattomien'),
    (re.compile(_WBL+r'prokaryoottisiin'+_WBR), 'tumattomiin'),
    (re.compile(_WBL+r'Prokaryoottinen'+_WBR), 'Tumaton'),
    (re.compile(_WBL+r'Eukaryoottinen'+_WBR), 'Tumallinen'),
    (re.compile(_WBL+r'eukaryootti'+_WBR), 'tumallinen'),
    (re.compile(_WBL+r'eukaryootin'+_WBR), 'tumallisen'),
    (re.compile(_WBL+r'eukaryoottia'+_WBR), 'tumallista'),
    (re.compile(_WBL+r'eukaryootissa'+_WBR), 'tumallisessa'),
    (re.compile(_WBL+r'eukaryootista'+_WBR), 'tumallisesta'),
    (re.compile(_WBL+r'eukaryoottiin'+_WBR), 'tumalliseen'),
    (re.compile(_WBL+r'eukaryootit'+_WBR), 'tumalliset'),
    (re.compile(_WBL+r'eukaryootteja'+_WBR), 'tumallisia'),
    (re.compile(_WBL+r'eukaryoottien'+_WBR), 'tumallisten'),
    (re.compile(_WBL+r'eukaryooteissa'+_WBR), 'tumallisissa'),
    (re.compile(_WBL+r'eukaryooteilla'+_WBR), 'tumallisilla'),
    (re.compile(_WBL+r'eukaryooteille'+_WBR), 'tumallisille'),
    (re.compile(_WBL+r'eukaryooteilta'+_WBR), 'tumallisilta'),
    (re.compile(_WBL+r'Eukaryootti'+_WBR), 'Tumallinen'),
    (re.compile(_WBL+r'Eukaryootit'+_WBR), 'Tumalliset'),
    (re.compile(_WBL+r'Eukaryootteja'+_WBR), 'Tumallisia'),
    (re.compile(_WBL+r'Eukaryoottien'+_WBR), 'Tumallisten'),
    (re.compile(_WBL+r'Eukaryooteilla'+_WBR), 'Tumallisilla'),
    (re.compile(_WBL+r'Eukaryooteille'+_WBR), 'Tumallisille'),
    (re.compile(_WBL+r'prokaryootti'+_WBR), 'tumaton'),
    (re.compile(_WBL+r'prokaryootin'+_WBR), 'tumattoman'),
    (re.compile(_WBL+r'prokaryoottia'+_WBR), 'tumatonta'),
    (re.compile(_WBL+r'prokaryootissa'+_WBR), 'tumattomassa'),
    (re.compile(_WBL+r'prokaryootista'+_WBR), 'tumattomasta'),
    (re.compile(_WBL+r'prokaryoottiin'+_WBR), 'tumattomaan'),
    (re.compile(_WBL+r'prokaryootit'+_WBR), 'tumattomat'),
    (re.compile(_WBL+r'prokaryootteja'+_WBR), 'tumattomia'),
    (re.compile(_WBL+r'prokaryoottien'+_WBR), 'tumattomien'),
    (re.compile(_WBL+r'prokaryooteissa'+_WBR), 'tumattomissa'),
    (re.compile(_WBL+r'prokaryooteilla'+_WBR), 'tumattomilla'),
    (re.compile(_WBL+r'prokaryooteille'+_WBR), 'tumattomille'),
    (re.compile(_WBL+r'prokaryooteilta'+_WBR), 'tumattomilta'),
    (re.compile(_WBL+r'prokaryootteihin'+_WBR), 'tumattomiin'),
    (re.compile(_WBL+r'Prokaryootti'+_WBR), 'Tumaton'),
    (re.compile(_WBL+r'Prokaryootit'+_WBR), 'Tumattomat'),
    (re.compile(_WBL+r'Prokaryootteja'+_WBR), 'Tumattomia'),
    (re.compile(_WBL+r'Prokaryoottien'+_WBR), 'Tumattomien'),
    (re.compile(_WBL+r'Prokaryooteilla'+_WBR), 'Tumattomilla'),
    (re.compile(_WBL+r'Prokaryootteihin'+_WBR), 'Tumattomiin'),
]
_ALIAS['Mik\u00e4 on tumallinen?']='eukaryootti'
_ALIAS['Mik\u00e4 on tumaton?']='prokaryootti'
_ALIAS['Mik\u00e4 on eukaryootti?']='eukaryootti'
_ALIAS['Mik\u00e4 on prokaryootti?']='prokaryootti'

_tm=0; _al=0
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
    f=Flds(flds); hit=False
    front0=_kys(f[0])
    for i in (0,1,2):                                   # visible fields
        if i>=len(f): break
        head,sep,tail=f[i].partition('<br><i>Muut nimet:')   # the alias line names the very words we replace
        for rx,rep in _TERMRX: head=rx.sub(rep, head)
        v=head+sep+tail
        if v!=f[i]: f[i]=v; hit=True
    if len(f)>5 and 'mRNA' in f[5]:                     # keep the old trigger, add the new spelling
        extra=[w.strip() for w in f[5].split(',') if 'mRNA' in w]
        uudet=[w.replace('mRNA','l\u00e4hetti-RNA') for w in extra]
        puuttuvat=[w for w in uudet if w and w not in f[5]]
        if puuttuvat: f[5]=f[5].rstrip().rstrip(',')+', '+', '.join(puuttuvat); hit=True
    alias=_ALIAS.get(front0) or _ALIAS.get(_kys(f[0]))
    if alias and len(f)>2 and f[2].strip():
        rivi='<br><i>Muut nimet: '+alias+'</i>'
        runko=f[2].partition('<br><i>Muut nimet:')[0].rstrip()   # rewrite, so a corrupted line heals
        if runko+rivi!=f[2]: f[2]=runko+rivi; hit=True
        _al+=1
    if not hit: continue
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _tm+=1
print("termeja yhdenmukaistettu:",_tm,"korttia,",_al,"muut-nimet-riviä")

def __norm(v):
    for _rx,_rep in _TERMRX: v=_rx.sub(_rep,v)
    return v
# 1c3) no semicolons in card text: use a period and capitalise what follows.
def _semi(v):
    out=''; last=0
    for m in re.finditer(';', v):
        if re.search(r'&[a-zA-Z#0-9]+;$', v[:m.start()+1]): continue   # HTML entity, not punctuation
        out+=v[last:m.start()]+'.'
        k=m.end()
        while k<len(v) and v[k].isspace(): k+=1
        out+=v[m.end():k]
        if k<len(v) and v[k].islower(): out+=v[k].upper(); last=k+1
        else: last=k
    return out+v[last:]
_sp=0
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
    f=Flds(flds); hit=False
    for i in (0,1,2):
        if i>=len(f): break
        v=_semi(f[i])
        if v!=f[i]: f[i]=v; hit=True
    if hit:
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _sp+=1
print("puolipisteita korvattu pisteella:",_sp,"korttia")

# ── new image cards ────────────────────────────────────────────────────────────
def add_image_cards(course_tag, media_dir, mediamap, workdir):
    """Read kuvakortit.txt, add one note+card per block for this course, copy the image in."""
    kp = os.path.join(SC, "kuvakortit.txt")
    if not os.path.exists(kp):
        print("HUOM: kuvakortit.txt puuttuu - kuvakortteja ei lisätty"); return 0
    blocks = [b for b in open(kp, encoding="utf-8").read().split("\n---") if b.strip()]
    due = (cur.execute("select coalesce(max(due),0) from cards where did=?", (tid,)).fetchone()[0] or 0) + 1
    # this script's source IS its own previous output, so re-running must not duplicate cards
    seen = {_kys((r[0].split(SEP) + [''])[0])
            for r in cur.execute("select flds from notes n join cards c on c.nid=n.id where c.did=?", (tid,))}
    added = 0; skipped = 0
    for b in blocks:
        g = lambda k: (re.search(r'^%s:\s*(.*)$' % k, b, re.M).group(1).strip() if re.search(r'^%s:\s*(.*)$' % k, b, re.M) else '')
        if g('KURSSI') != course_tag: continue
        img, q, sup, laa, st = g('TIEDOSTO'), g('KYSYMYS'), g('SUPPEA'), g('LAAJA'), g('TAHDET')
        if not (img and q and sup and laa): continue
        q,sup,laa=[__norm(z) for z in (q,sup,laa)]   # same terminology as the rest of the deck
        if _kys(q) in seen: skipped += 1; continue   # already in the deck
        srcimg = os.path.join(media_dir, img)
        if not os.path.exists(srcimg): print("   PUUTTUU:", img); continue
        num = str(len(mediamap))
        shutil.copyfile(srcimg, os.path.join(workdir, num)); mediamap[num] = img
        fields = [q, sup, laa + '<br><img src="%s">' % img, st, '', '']
        guid = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(10))
        sfld = re.sub('<[^>]*>', '', q).strip()
        csum = int(hashlib.sha1(sfld.encode('utf-8')).hexdigest()[:8], 16)
        nid = now * 1000 + added
        cur.execute("insert into notes values (?,?,?,?,?,?,?,?,?,?,?)",
                    (nid, guid, int(solukko_mid), now, -1, '', SEP.join(fields), sfld, csum, 0, ''))
        cur.execute("insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (nid + 1, nid, tid, 0, now, -1, 0, 0, due, 0, 0, 0, 0, 0, 0, 0, 0, ''))
        due += 1; added += 1
    print("kuvakortteja lisätty (%s): %d  (jo pakassa: %d)" % (course_tag, added, skipped))
    return added


mediamap = {}
mp = os.path.join(work, 'media')
if os.path.exists(mp):
    try: mediamap = json.loads(open(mp, encoding='utf-8').read() or '{}')
    except Exception: mediamap = {}
add_image_cards('biotek', os.path.join(SC, 'kuvat'), mediamap, work)

# 3d) inflected forms harvested from the deck's own text: every form that actually occurs is a
#     trigger, so no occurrence is left unlinked because a case form was not guessed in advance.
_lp=os.path.join(SC,"linkkilisat.txt")
if os.path.exists(_lp):
    _lisat={}
    for _l in open(_lp,encoding="utf-8"):
        _c=_l.rstrip("\n").split("\t")
        if len(_c)==3 and _c[0].strip()=='biotek': _lisat.setdefault(_c[1].strip(),[]).append(_c[2].strip())
    _ll=0; _lm=0
    for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
        flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
        f=Flds(flds)
        muodot=_lisat.get(_kys(f[0]))
        if not muodot or len(f)<6: continue
        olemassa={w.strip().lower() for w in re.sub('<[^>]*>','',f[5]).split(',')}
        uudet=[m for m in muodot if m.lower() not in olemassa]
        if not uudet: continue
        f[5]=f[5].rstrip().rstrip(',')+', '+', '.join(uudet)
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid))
        _ll+=1; _lm+=len(uudet)
    print("linkkisanoja lisatty:",_lm,"muotoa",_ll,"kortille")
else:
    print("HUOM: linkkilisat.txt puuttuu")

con.commit()
kept = cur.execute("select count(*) from notes").fetchone()[0]
print("kortteja pakassa:", kept)
# 3i) only a short answer written -> it belongs in Laaja, which is the field the site renders.
_siirto = 0
for nid, flds in list(cur.execute("select n.id, n.flds from notes n join cards c on c.nid=n.id where c.did=? group by n.id", (tid,))):
    f = Flds(flds)
    if len(f) < 3: continue
    _pl = lambda v: re.sub(r'\s+', ' ', re.sub('<[^>]*>', ' ', v or '')).strip()
    if _pl(f[1]) and not _pl(f[2]):
        f[2] = f[1]; f[1] = ''
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid))
        _siirto += 1
con.commit()
print("suppea siirretty laajaan:", _siirto)

# 3g) the leading "(1.0)" is the card's place in the deck: the site sorts by it and hides it.
#     Image Occlusion notetypes are skipped -- their first field is occlusion data, not a question.
_JN = re.compile(r'^(?:\s|&nbsp;|<[^>]*>)*\(\s*\d+(?:[.,]\d+)?\s*\)')
_numeroitavat = {str(mid) for mid, m in models.items()
                 if m.get('flds') and m['flds'][0]['name'] in ('Kysymys', 'Content')}
_num = 0
for nid, mid, flds in list(cur.execute("select n.id, n.mid, n.flds from notes n join cards c on c.nid=n.id where c.did=? group by n.id", (tid,))):
    if str(mid) not in _numeroitavat: continue
    f = Flds(flds)
    if not f[0].strip() or _JN.match(f[0]): continue
    if _kys(f[0]).lower() == 'esittely': continue   # pakan kansi, ei ruudukossa
    f[0] = '(1) ' + f[0]
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid))
    _num += 1
con.commit()
print("jarjestysnumero lisatty:", _num, "kortille")

# 3h) name the notetype exactly as the user's collection does, or Anki keeps both under "<name>+".
_KOKOELMA = os.path.join(REPO, "SOLUKKO.apkg")
if os.path.exists(_KOKOELMA):
    _tt = tempfile.mkdtemp()
    with zipfile.ZipFile(_KOKOELMA) as _z:
        _z.extract('collection.anki21' if 'collection.anki21' in _z.namelist() else 'collection.anki2', _tt)
    _tdb = os.path.join(_tt, 'collection.anki21')
    if not os.path.exists(_tdb): _tdb = os.path.join(_tt, 'collection.anki2')
    _tcon = sqlite3.connect(_tdb)
    _tmodels = json.loads(_tcon.execute("select models from col").fetchone()[0])
    _tcon.close(); shutil.rmtree(_tt, ignore_errors=True)
    for _mid, _m in models.items():
        _oikea = _tmodels.get(str(_mid), {}).get('name')
        if _oikea and _oikea != _m.get('name'):
            print("korttityypin nimi kokoelmasta: %s -> %s" % (_m['name'], _oikea))
            _m['name'] = _oikea
    cur.execute("update col set models=?", (json.dumps(models),))
    con.commit()

con.close()

if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(db, dbname)
    z.writestr('media', json.dumps(mediamap))
    for num in mediamap:
        p = os.path.join(work, num)
        if os.path.exists(p): z.write(p, num)
shutil.rmtree(work, ignore_errors=True)
print("kirjoitettu:", OUT, os.path.getsize(OUT), "tavua")
