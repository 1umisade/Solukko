# -*- coding: utf-8 -*-
"""Carve the user's OWN "Luento 1" deck out of SOLUKKO.apkg, apply the term-front fixes
in place, and write it back out as a full .apkg. Notetypes, guids, scheduling and media are
copied verbatim from the user's collection, so importing UPDATES the notes in place."""
import zipfile, sqlite3, tempfile, os, shutil, json, re, time, sys
sys.stdout.reconfigure(encoding='utf-8')
SC=os.path.dirname(os.path.abspath(__file__))
REPO=os.path.dirname(SC)                       # tyokalut/ on repon juuressa
SRC=os.path.join(REPO,"SOLUKKO.apkg")
KURSSI=os.path.join(REPO,"kurssit","BKEM5030 Solu- ja biomolekyylit - teoria")
# tiedostonimi on kayttajan Ankissa antama pakannimi, ei pakan pitka sisainen nimi
OUT=os.path.join(KURSSI,"Luento 1 - Elämän perusperiaatteet.apkg")
# reuse the question map from the fix script
_src=open(os.path.join(SC,"fix_solu_L1_fronts.py"),encoding="utf-8").read()
_qsrc=_src[_src.index("Q={"):_src.index("\n}\n",_src.index("Q={"))+3]
ns={}; exec(_qsrc,ns); QMAP=ns["Q"]

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

work=tempfile.mkdtemp()
with zipfile.ZipFile(SRC) as z: z.extractall(work)
dbname='collection.anki21' if os.path.exists(os.path.join(work,'collection.anki21')) else 'collection.anki2'
db=os.path.join(work,dbname)
con=sqlite3.connect(db); cur=con.cursor()

models=json.loads(cur.execute("select models from col").fetchone()[0])
decks=json.loads(cur.execute("select decks from col").fetchone()[0])
target=None
for d in decks.values():
    n=d.get('name','')
    if 'Luento 1 - El' in n and 'Solu- ja biomolekyylit' in n: target=d
if not target: raise SystemExit("Luento 1 -pakkaa ei löytynyt")
tid=int(target['id']); print("pakka:",target['name'])

# 1) fix bare term fronts — every notetype (the user's own "Basic" cards too).
#    Only fronts we have an explicit question for are touched; cloze cards and "esittely" are left alone.
EXTRA={"solu":"Mikä on solu?","katalyytti":"Mikä on katalyytti?",
       "Elämän tarkoitus (biologisesti)":"Mikä on elämän tarkoitus (biologisesti)?"}
now=int(time.time()); fixed=0; untouched=[]
nids=[r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]
for nid in nids:
    mid,flds=cur.execute("select mid,flds from notes where id=?", (nid,)).fetchone()
    f=Flds(flds)
    front=_kys(f[0])
    if front.endswith('?') or front.lower()=='esittely' or '{{c' in f[0]: continue
    q=QMAP.get(front) or EXTRA.get(front)
    if not q: untouched.append((models[str(mid)]['name'],front[:55])); continue
    f[0]=q
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); fixed+=1
print("etupuolia korjattu:",fixed)
if untouched:
    print("jätetty ennalleen (jo kysymysmuotoisia tai omia muotoiluja):")
    for nm,fr in untouched: print("   [%s] %s"%(nm,fr))

# 1b) remove duplicate fronts. Keep the "Solukko+" note (one unified notetype); if the twin
#     is a curated card (its Suppea vastaus is filled), carry its wording over before deleting.
from collections import defaultdict
groups=defaultdict(list)
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    mid,flds=cur.execute("select mid,flds from notes where id=?", (nid,)).fetchone()
    f=Flds(flds)
    groups[_kys(f[0]).lower()].append((nid,models[str(mid)]['name'],f))
removed=[]
for front,lst in groups.items():
    if len(lst)<2: continue
    keep=next((x for x in lst if x[1]=='Solukko+'), lst[0])
    for nid,nm,f in lst:
        if nid==keep[0]: continue
        if re.sub('<[^>]*>','',f[1]).strip():          # twin is curated -> keep the user's own wording
            k=keep[2]; k[1],k[2],k[5]=f[1],f[2],(f[5] or k[5])
            cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (k.join(), now, keep[0]))
            merged=True
        else: merged=False
        cur.execute("delete from cards where nid=?", (nid,))
        cur.execute("delete from notes where id=?", (nid,))
        removed.append((lst[0][2][0][:40], nm, "sisältö siirretty" if merged else "poistettu"))
print("duplikaatteja poistettu:",len(removed))
for fr,nm,how in removed: print("   %-42s [%s] %s"%(fr,nm,how))

# 1c) expand linkkisanat with all Finnish case forms (only cards that already had linkkisanat)
lp=os.path.join(SC,"linkkisanat_uudet.txt")
if os.path.exists(lp):
    newlink={}
    for line in open(lp,encoding="utf-8"):
        if "\t" not in line: continue
        fr,lk=line.rstrip("\n").split("\t",1)
        newlink[fr.strip()]=lk.strip()
    n=0
    for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
        flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
        f=Flds(flds)
        if not f[5].strip(): continue
        lk=newlink.get(_kys(f[0]))
        if not lk: continue
        f[5]=lk
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); n+=1
    print("linkkisanat laajennettu:",n)
else:
    print("HUOM: linkkisanat_uudet.txt puuttuu — linkkisanoja ei päivitetty")

# 1c1) apply the richer "Laaja vastaus" texts (rewritten to be genuinely broader than the Suppea one)
ep=os.path.join(SC,"laajat_uudet.txt")
if os.path.exists(ep):
    newlaaja={}
    for line in open(ep,encoding="utf-8"):
        if "\t" not in line: continue
        fr,tx=line.rstrip("\n").split("\t",1)
        if fr.strip() and tx.strip(): newlaaja[fr.strip()]=tx.strip()
    n=0; miss=[]
    for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
        flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
        f=Flds(flds)
        tx=newlaaja.get(_kys(f[0]))
        if not tx: continue
        f[2]=tx
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); n+=1
    print("laajoja vastauksia rikastettu:",n,"/",len(newlaaja))
else:
    print("HUOM: laajat_uudet.txt puuttuu - laajoja ei rikastettu")

# 1c1b) the slides name the cis isomer of fumaric acid "omenahappo" (malic acid) — a translation slip for
#       maleic acid. Malic acid has no C=C at all, so it cannot be a cis-trans isomer. Use the correct name,
#       and note the slide's wording on the main card so the slide-based exam still makes sense.
_CISNOTE = '<br><i>Huom. luentodioissa cis-muotoa kutsutaan omenahapoksi. Se on virhe: omenahapossa ei ole kaksoissidosta lainkaan, joten se ei voi olla cis-trans-isomeeri.</i>'
_cis=0
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
    f=Flds(flds)
    if 'omena' not in (f[0]+f[1]+f[2]).lower(): continue
    for i in (0,1,2):
        f[i]=(f[i].replace('omenahappo','maleiinihappo').replace('omenahapon','maleiinihapon')
                  .replace('omenahapossa','maleiinihapossa').replace('omenahappoa','maleiinihappoa')
                  .replace('omena- vs.','maleiini- vs.').replace('omena vs.','maleiini vs.'))
    if 'eroavat ominaisuuksiltaan' in f[0] and 'omenahapoksi' not in f[2]:
        f[2]=f[2]+_CISNOTE
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _cis+=1
print("cis-trans-nimi korjattu (omenahappo -> maleiinihappo):",_cis,"korttia")
# the explanatory note deliberately mentions the wrong name; Anki may have reformatted its HTML,
# so ignore anything inside <i>...</i> rather than matching the note text byte for byte
import re as _re2
_left=[r[0] for r in cur.execute("select n.flds from notes n join cards c on c.nid=n.id where c.did=?", (tid,))
       if 'omenaha' in _re2.sub(r'(?s)<i>.*?</i>','',r[0]).lower()]
if _left: raise SystemExit("VIRHE: 'omenahappo' jai viela %d korttiin" % len(_left))

# 1c1c) slide 70 gives the E. coli chromosome as "n. 2000 mm" - a unit slip for 2000 um = 2,0 mm.
#       State the corrected figure instead of dodging the number.
_dna=0
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
    f=Flds(flds)
    if 'joka on venytettynä monisatakertaisesti solua (n. 2 x 1 µm) pidempi' not in f[2]: continue
    f[2]=f[2].replace('joka on venytettynä monisatakertaisesti solua (n. 2 x 1 µm) pidempi', 'joka on suoraksi venytettynä noin 2,0 mm pitkä eli noin tuhat kertaa solua (n. 2 x 1 µm) pidempi')
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _dna+=1
print("E. colin DNA:n pituus korjattu (2,0 mm):",_dna,"korttia")
if _dna!=1: raise SystemExit("VIRHE: odotettiin 1 korttia, saatiin %d" % _dna)

# 1c1d) exam probability, in one pass, always as a plain number 1-3 in its OWN field.
#       A note type that has no such field gets one appended (last position, so field order and the
#       card templates stay as they were) and its notes grow one empty field to match.
#       A rating the user already set — field or tag — wins over our own guess; tags are then cleared.
# re-rated exam probabilities (KURSSI<TAB>KYSYMYS<TAB>N) - these override the card's current value
_ov={}
_ovp=os.path.join(SC,"arviot_uudet.txt")
if os.path.exists(_ovp):
    for _line in open(_ovp,encoding="utf-8"):
        _p=_line.rstrip('\n').split('\t')
        if len(_p)==3 and _p[0].strip()=='solu' and _p[2].strip() in ('1','2','3'):
            _ov[_p[1].strip()]=_p[2].strip()
    print("uudelleenarvioita luettu (solu):", len(_ov))
else:
    print("HUOM: arviot_uudet.txt puuttuu - vanhat arviot jaavat voimaan")

tp=os.path.join(SC,"solu_tahdet.txt")
pairs=[]
if os.path.exists(tp):
    for line in open(tp,encoding="utf-8"):
        if "\t" not in line: continue
        pre,st=line.rstrip("\n").split("\t",1)
        if pre.strip() and st.strip(): pairs.append((pre.strip(), st.strip()))
else:
    print("HUOM: solu_tahdet.txt puuttuu - uusia arvioita ei lisatty")

def _rate(v):
    """1-3 out of whatever form the value is in: stars, ttN, or a plain number."""
    v=re.sub('<[^>]*>','',v or '')
    k=len(re.findall('\u2605',v))
    if k: return min(k,3)
    m=re.search(r'(?:^|\s)tt([1-3])(?=\s|$)', v) or re.match(r'\s*([1-5])\b', v)
    return min(int(m.group(1)),3) if m else 0

def _staridx(m):
    for i,fl in enumerate(m['flds']):
        if 'tenttitodenn' in fl['name'].lower(): return i
    return -1

# which note types are actually used in this deck, and which of them need the field added
_used={r[0] for r in cur.execute("select distinct n.mid from notes n join cards c on c.nid=n.id where c.did=?", (tid,))}
_grown=set()
for _mid in _used:
    m=models[str(_mid)]
    if _staridx(m)>=0: continue
    _f=dict(m['flds'][-1])                       # copy an existing field so every key Anki expects is present
    _f.pop('id',None)
    _f.update(name='tenttitodennakoisyys', ord=len(m['flds']))
    m['flds'].append(_f); _grown.add(str(_mid))
    print("kentta lisatty korttityyppiin:", m['name'], "->", len(m['flds']), "kenttaa")
if _grown: cur.execute("update col set models=?", (json.dumps(models),))

_fld=0; _new=0; _tag=0; _left=[]
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    mid,flds,tags=cur.execute("select mid,flds,tags from notes where id=?", (nid,)).fetchone()
    f=Flds(flds); tags=tags or ''
    m=models[str(mid)]; si=_staridx(m)
    if str(mid) in _grown: f.n+=1                # the note type grew a field, so the note must too
    while len(f)<f.n: f.append('')
    front=_kys(f[0])
    n=_rate(_ov.get(front,''))                                  # the re-rating wins: the old values were judged wrong
    if not n: n=(_rate(f[si]) if 0<=si<len(f) else 0) or _rate(tags)
    if not n:
        hit=next((st for pre,st in pairs if front.startswith(pre)), None)
        if hit: n=_rate(hit); _new+=1
    if n and 0<=si<len(f) and f[si]!=str(n): f[si]=str(n); _fld+=1
    keep=[w for w in tags.split() if '\u2605' not in w and not re.fullmatch(r'(tt)?[1-3]', w)]   # no rating tags
    nt=(' '+' '.join(keep)+' ') if keep else ''
    if nt!=tags: _tag+=1
    if not n and front.lower()!='esittely': _left.append(front[:45])
    cur.execute("update notes set flds=?, tags=?, mod=?, usn=-1 where id=?", (f.join(), nt, now, nid))
print("tenttitodennakoisyys: %d kenttaan (%d omaa arviota), %d tagia siivottu" % (_fld,_new,_tag))
if _left: print("   ILMAN ARVIOTA:", _left)

# 1c1f) slide 63 has hapetin and pelkistin the wrong way round (it says the oxidant donates electrons).
#       The oxidant is reduced and ACCEPTS electrons; the reductant is oxidised and DONATES them.
_REDOX = {'Mikä on hapetin?': ('Aine, johon elektroni siirtyy toisesta aineesta (hapetin itse pelkistyy).', 'Hapetin hapettaa jonkin toisen aineen ja pelkistyy samalla itse, koska se vastaanottaa elektronit. Soluhengityksessä lopullinen hapetin on happi: se ottaa vastaan elektroninsiirtoketjun elektronit ja pelkistyy vedeksi. Hapetin ja pelkistin esiintyvät aina parina, sillä elektroni ei voi siirtyä ilman vastaanottajaa.<br><i>Huom. luentodialla hapetin ja pelkistin on määritelty päinvastoin. Muistisääntö: hapetin hapettaa toisen ja pelkistyy itse.</i>'), 'Mikä on pelkistin?': ('Aine, joka luovuttaa elektronin toiseen aineeseen (pelkistin itse hapettuu).', 'Pelkistin pelkistää jonkin toisen aineen ja hapettuu samalla itse, koska se luovuttaa elektronit. Solussa tyypillinen pelkistin on NADH, joka luovuttaa elektroninsa elektroninsiirtoketjuun ja hapettuu takaisin NAD+:ksi. Ravinnon orgaaniset molekyylit ovat pelkistyneitä eli elektronirikkaita, ja niiden hapettaminen vapauttaa energian.<br><i>Huom. luentodialla hapetin ja pelkistin on määritelty päinvastoin. Muistisääntö: hapetin hapettaa toisen ja pelkistyy itse.</i>')}
_rx=0
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
    f=Flds(flds)
    fix=_REDOX.get(_kys(f[0]))
    if not fix: continue
    f[1],f[2]=fix
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _rx+=1
print("hapetin/pelkistin korjattu:",_rx,"korttia")
if _rx!=len(_REDOX): raise SystemExit("VIRHE: odotettiin %d korttia, saatiin %d" % (len(_REDOX), _rx))

# 1c1g) spelling fixes. Built-in: the "emasjarjestyks-" stem and a couple of known slips.
#       On top of that, every pair listed in typot.txt (vaara<TAB>oikea<TAB>kortti).
#       Whole-word replacement, but a hyphen does NOT count as a word boundary, so the word is
#       still found inside a compound like "lahetti-RNA-ketjuhin".
_TYPORE=re.compile(r'(em[\u00e4a]sj[\u00e4a]rjest)(?:ey|ee|yy|e|y)?(ks)')
_PAIRS={"ketjuhin":"ketjuihin"}
_tp=os.path.join(SC,"typot.txt")
if os.path.exists(_tp):
    for _l in open(_tp,encoding="utf-8"):
        _c=_l.rstrip("\n").split("\t")
        if len(_c)>=2 and _c[0].strip() and _c[1].strip() and _c[0].strip()!=_c[1].strip():
            _PAIRS[_c[0].strip()]=_c[1].strip()
    print("typot.txt: %d korjausparia" % len(_PAIRS))
else:
    print("HUOM: typot.txt puuttuu - vain sisaanrakennetut korjaukset")
_B=r'(?<![\w\u00e4\u00f6\u00e5\u00c4\u00d6\u00c5])%s(?![\w\u00e4\u00f6\u00e5\u00c4\u00d6\u00c5])'
_RX=[(re.compile(_B % re.escape(k)), v) for k,v in _PAIRS.items()]
_ty=0; _hits={}
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
    f=Flds(flds); hit=False
    for i in range(len(f)):
        v=_TYPORE.sub(lambda m: m.group(1)+'y'+m.group(2), f[i])
        for rx,rep in _RX:
            v2,k=rx.subn(rep, v)
            if k: _hits[rep]=_hits.get(rep,0)+k
            v=v2
        if v!=f[i]: f[i]=v; hit=True
    if not hit: continue
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _ty+=1
print("kirjoitusvirheita korjattu:",_ty,"korttia")
for _k,_v in sorted(_hits.items()): print("   -> %-24s %d kpl"%(_k,_v))

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
    (re.compile(_WBL+r'rRNA'+_WBR), 'ribosomaalinen RNA'),
    (re.compile(_WBL+r'rRNA:n'), 'ribosomaalisen RNA:n'),
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

_OTSIKKO = '<br><i>Kutsutaan myös: '
_ALIASRX = re.compile(r'<br><i>(?:Muut nimet|Kutsutaan myös):')   # accept the old label so a rerun heals
def _leikkaa(v):
    m=_ALIASRX.search(v)
    return (v, '') if not m else (v[:m.start()], v[m.start():])
_tm=0; _al=0
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
    f=Flds(flds); hit=False
    front0=_kys(f[0])
    for i in (0,1,2):                                   # visible fields
        if i>=len(f): break
        head,tail=_leikkaa(f[i])                             # the alias line names the very words we replace
        for rx,rep in _TERMRX: head=rx.sub(rep, head)
        v=head+tail
        if v!=f[i]: f[i]=v; hit=True
    if len(f)>5 and 'mRNA' in f[5]:                     # keep the old trigger, add the new spelling
        extra=[w.strip() for w in f[5].split(',') if 'mRNA' in w]
        uudet=[w.replace('mRNA','l\u00e4hetti-RNA') for w in extra]
        puuttuvat=[w for w in uudet if w and w not in f[5]]
        if puuttuvat: f[5]=f[5].rstrip().rstrip(',')+', '+', '.join(puuttuvat); hit=True
    alias=_ALIAS.get(front0) or _ALIAS.get(_kys(f[0]))
    if alias and len(f)>2 and f[2].strip():
        rivi=_OTSIKKO+alias+'</i>'
        runko=_leikkaa(f[2])[0].rstrip()                     # rewrite, so a corrupted line heals
        if runko+rivi!=f[2]: f[2]=runko+rivi; hit=True
        _al+=1
    if not hit: continue
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _tm+=1
print("termeja yhdenmukaistettu:",_tm,"korttia,",_al,"kutsutaan-myös-riviä")

# 1c1i) a definition should not open by repeating the term it defines, and the terminology
# rename left a few "X eli X" repeats behind.
_SUPPEA={
 'Mikä on solulima?':'Solun sisältö. Soluelimet ja sytosoli.',
 'Mikä on lähetti-RNA?':'Välittää DNA:n viestin translaatioon.',
 'Mikä on tumaton?':'Eliö, jonka DNA on nukleoidissa (bakteerit ja arkeonit).',
 'Mikä on genomi?':'Solun kaikki DNA eli sen koko geneettinen tieto.',
 'Mikä on soluelin?':'Solun sisäinen rakenneosa, jolla on oma tehtävänsä. Useimmilla on oma kalvo.',
 'Mikä on solu?':'Kalvon rajaama kemiallinen järjestelmä, joka ylläpitää itseään ja lisääntyy.'}
# the alias tail is rewritten separately, so only the body is given here
_LAAJA={
 'Mikä on soluelin?':'Soluelimet ovat solulimassa sijaitsevia rakenteita, joilla kullakin on oma '
   'erikoistunut tehtävänsä: tumassa säilytetään genomia, ribosomeissa tapahtuu proteiinisynteesi ja '
   'mitokondriossa aerobinen energiantuotto. Useimmat soluelimet ovat kalvon rajaamia, mutta eivät '
   'kaikki: ribosomilla ei ole kalvoa lainkaan. Kalvorakenteiset soluelimet ovat tyypillisiä '
   'tumallisille ja puuttuvat tumattomilta pääosin, ja juuri kalvojen erottamien osastojen työnjako '
   'tekee tumallisesta solusta suuremman ja monimutkaisemman.',
 'Mikä on solu?':'Solu on elämän perusyksikkö ja pienin rakenne, joka voi toimia elävänä: solukalvon '
   'rajaama kokonaisuus, jonka sisällä kemiallinen ympäristö poikkeaa ulkopuolisesta. Kaikissa '
   'tavallisissa soluissa on genomi, joka on aina kaksinauhaista DNA:ta, sekä solukalvo ja ribosomeja. '
   'Kaikki itsenäiset eliöt koostuvat soluista. Pakollinen poikkeus ovat virukset, jotka ovat '
   'ei-solullisia ja lisääntyvät vain loisimalla solullisessa eliössä.'}
_KORJAA=[("Solulima. Solukalvon sisäpuolella oleva","Solukalvon sisäpuolella oleva"),
         ("Tumakotelo eli tumakotelo on","Tumakotelo on"),
         ("lähetti-RNA eli lähetti-RNA syntyy","Lähetti-RNA syntyy"),
         ("Tumattomilla eli tumattomilla DNA","Tumattomilla DNA")]
_sk=0
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    f=Flds(cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]); hit=False
    kysymys=_kys(f[0])
    uusi=_SUPPEA.get(kysymys)
    if uusi and len(f)>1 and f[1]!=uusi: f[1]=uusi; hit=True
    uusiL=_LAAJA.get(kysymys)
    if uusiL and len(f)>2 and f[2].strip():
        _runko,_hanta=_leikkaa(f[2])          # keep the Kutsutaan myös line the previous step wrote
        if _runko.strip()!=uusiL: f[2]=uusiL+_hanta; hit=True
    for i in (1,2):
        if i>=len(f): break
        v=f[i]
        for a,b in _KORJAA: v=v.replace(a,b)
        if v!=f[i]: f[i]=v; hit=True
    if not hit: continue
    cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid)); _sk+=1
print("selityksien alkuja siistitty:",_sk)

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

# 1c2) if "Laaja vastaus" says the same thing as "Suppea vastaus", keep only the Suppea one.
#      The site then shows a single answer, greys out the toggle and tells the user there is no longer version.
import difflib
def _plain(s): return re.sub(r'\s+',' ',re.sub('<[^>]*>',' ',s or '')).strip().lower()
cleared=[]
for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
    flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
    f=Flds(flds)
    s,l=_plain(f[1]),_plain(f[2])
    if s and not l:                                              # only one answer: it belongs in Laaja
        f[2]=f[1]; f[1]=''
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid))
        cleared.append((re.sub('<[^>]*>','',f[0])[:42], 1.0)); continue
    if not s or not l: continue
    ratio=difflib.SequenceMatcher(None,s,l).ratio()
    if s==l or (ratio>=0.80 and len(l.split())<=len(s.split())+3):   # laaja adds nothing substantial
        if len(s.split())>len(l.split()): f[2]=f[1]                  # keep the richer wording...
        f[1]=''                                                      # ...and put it in Laaja, so the card shows the Laaja button
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid))
        cleared.append((re.sub('<[^>]*>','',f[0])[:42], round(ratio,2)))
print("Laaja tyhjennetty (sama kuin suppea):",len(cleared))
for fr,r in cleared: print("   %-44s samankaltaisuus %.2f"%(fr,r))

# 1d) DO NOT rename the notetype here. An import cannot rename one: Anki matches by id, sees the
#     name clash with what the collection already has, and creates a copy with "+" appended -- which
#     is how Solukko -> Solukko+ -> Solukko++ was born. The export keeps the source collection's own
#     name, so the import updates in place. Renaming is done by hand in Anki (Tools > Manage Note Types).
SOLUKKO_MID="1727391050"   # the deck's own notetype; the name varies, the id does not
print("korttityyppi:", next((m['name'] for m in models.values() if str(m.get('id'))=='1727391050'
                             or m.get('name','').startswith('Solukko')), '?'), "(ei nimetä uudelleen)")

# 2) keep only this deck's cards/notes
cur.execute("delete from cards where did<>?", (tid,))
cur.execute("delete from notes where id not in (select nid from cards)")
kept_notes=cur.execute("select count(*) from notes").fetchone()[0]
kept_cards=cur.execute("select count(*) from cards").fetchone()[0]
print("jäljellä:",kept_notes,"muistiinpanoa /",kept_cards,"korttia")

# 3) trim the deck list to Default + this deck
newdecks={k:v for k,v in decks.items() if str(v.get('id'))in(str(tid),'1')}
cur.execute("update col set decks=?", (json.dumps(newdecks),))
con.commit()

def __norm(v):
    for _rx,_rep in _TERMRX: v=_rx.sub(_rep,v)
    return v
# 3b) new image cards from kuvakortit.txt: one note+card each, the figure appended to the Laaja answer.
#     The image files are added to the media map here so step 4's "keep what is referenced" filter keeps them.
import hashlib, random
_kp=os.path.join(SC,"kuvakortit.txt")
if os.path.exists(_kp):
    _solukko_mid=next((mid for mid,m in models.items() if str(mid)==SOLUKKO_MID), None) or next((mid for mid,m in models.items() if m.get('name','').startswith('Solukko')), None)
    if not _solukko_mid: raise SystemExit("Solukko-korttityyppia ei loytynyt (id %s)"%SOLUKKO_MID)
    _mp=os.path.join(work,'media'); _mm={}
    if os.path.exists(_mp):
        try: _mm=json.loads(open(_mp,encoding='utf-8').read() or '{}')
        except Exception: _mm={}
    _next=max([int(k) for k in _mm if k.isdigit()]+[-1])+1
    _due=(cur.execute("select coalesce(max(due),0) from cards where did=?", (tid,)).fetchone()[0] or 0)+1
    _seen={_kys((r[0].split(SEP)+[''])[0])
           for r in cur.execute("select flds from notes n join cards c on c.nid=n.id where c.did=?", (tid,))}
    _added=0; _missing=[]; _dup=0
    for _b in [b for b in open(_kp,encoding="utf-8").read().split("\n---") if b.strip()]:
        def _g(k,_b=_b):
            m=re.search(r'^%s:\s*(.*)$'%k,_b,re.M); return m.group(1).strip() if m else ''
        if _g('KURSSI')!='solu': continue
        _img,_q,_sup,_laa,_st=_g('TIEDOSTO'),_g('KYSYMYS'),_g('SUPPEA'),_g('LAAJA'),_g('TAHDET')
        if not (_img and _q and _sup and _laa): continue
        _q,_sup,_laa=[__norm(_z) for _z in (_q,_sup,_laa)]   # same terminology as the rest of the deck
        if _kys(_q) in _seen: _dup+=1; continue   # already imported into the collection
        _src=os.path.join(SC,'kuvat',_img)
        if not os.path.exists(_src): _missing.append(_img); continue
        _num=str(_next); _next+=1
        shutil.copyfile(_src, os.path.join(work,_num)); _mm[_num]=_img
        _fields=[_q,_sup,_laa+'<br><img src="%s">'%_img,_st,'','']
        _guid=''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(10))
        _sfld=re.sub('<[^>]*>','',_q).strip()
        _csum=int(hashlib.sha1(_sfld.encode('utf-8')).hexdigest()[:8],16)
        _nid=now*1000+_added
        cur.execute("insert into notes values (?,?,?,?,?,?,?,?,?,?,?)",
                    (_nid,_guid,int(_solukko_mid),now,-1,'','\x1f'.join(_fields),_sfld,_csum,0,''))
        cur.execute("insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (_nid+1,_nid,tid,0,now,-1,0,0,_due,0,0,0,0,0,0,0,0,''))
        _due+=1; _added+=1
    open(_mp,'w',encoding='utf-8').write(json.dumps(_mm))
    con.commit()
    print("kuvakortteja lisatty:",_added," (jo pakassa:",_dup,")")
    for _m in _missing: print("   KUVA PUUTTUU:",_m)
else:
    print("HUOM: kuvakortit.txt puuttuu - kuvakortteja ei lisatty")

# 3c) DNA and RNA had no definition card, so those words could never become word-links.
_UUDET = [('Mikä on DNA?', 'Kaksinauhainen nukleiinihappo, johon solun genomi on tallennettu.', 'DNA eli deoksiribonukleiinihappo on nukleotideista koostuva kaksinauhainen ketju, jonka nukleoemäsjärjestykseen solun genomi on kirjoitettu. Nauhat ovat toisilleen komplementaariset (A-T ja G-C), mikä tekee kahdentumisesta lähes virheetöntä ja mahdollistaa vaurioituneen nauhan korjaamisen toisen mallin mukaan. Sokerina on deoksiriboosi, joka tekee DNA:sta RNA:ta vakaamman ja siten paremman pitkäaikaisen tallennusmuodon.', '3', 'DNA, DNA:n, DNA:ta, DNA:ssa, DNA:sta, DNA:han, DNA:lla, DNA:ksi, deoksiribonukleiinihappo, deoksiribonukleiinihapon, deoksiribonukleiinihappoa, deoksiribonukleiinihapossa, deoksiribonukleiinihaposta, deoksiribonukleiinihapoksi'), ('Mikä on RNA?', 'Yksinauhainen nukleiinihappo, joka välittää ja toteuttaa genomin tietoa.', 'RNA eli ribonukleiinihappo on nukleotidiketju, joka on yleensä yksinauhainen ja jonka sokerina on riboosi. Riboosin ylimääräinen happiatomi tekee RNA:sta reaktiivisemman ja lyhytikäisemmän kuin DNA, mikä sopii väliaikaiselle työkopiolle. Emäksistä tymiinin tilalla on urasiili. RNA ei ainoastaan välitä tietoa vaan voi myös laskostua ja katalysoida reaktioita, mistä RNA-maailmahypoteesi sai alkunsa.', '3', 'RNA, RNA:n, RNA:ta, RNA:ssa, RNA:sta, RNA:han, RNA:lla, RNA:ksi, ribonukleiinihappo, ribonukleiinihapon, ribonukleiinihappoa, ribonukleiinihapossa, ribonukleiinihaposta, ribonukleiinihapoksi')]
_lisatty=0
_olemassa={_kys((r[0].split(SEP)+[''])[0])
           for r in cur.execute("select flds from notes n join cards c on c.nid=n.id where c.did=?", (tid,))}
_solukko_mid=next((mid for mid,m in models.items() if str(mid)==SOLUKKO_MID), None) or next((mid for mid,m in models.items() if m.get('name','').startswith('Solukko')), None)
if _solukko_mid:
    _due=(cur.execute("select coalesce(max(due),0) from cards where did=?", (tid,)).fetchone()[0] or 0)+1
    for _k,_sup,_laa,_st,_lk in _UUDET:
        if _k in _olemassa: continue
        _f=[_k,_sup,_laa,_st,'',_lk]
        _guid=''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(10))
        _csum=int(hashlib.sha1(_k.encode('utf-8')).hexdigest()[:8],16)
        _nid=now*1000+900+_lisatty
        cur.execute("insert into notes values (?,?,?,?,?,?,?,?,?,?,?)",
                    (_nid,_guid,int(_solukko_mid),now,-1,'',SEP.join(_f),_k,_csum,0,''))
        cur.execute("insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (_nid+1,_nid,tid,0,now,-1,0,0,_due,0,0,0,0,0,0,0,0,''))
        _due+=1; _lisatty+=1
    con.commit()
print("DNA/RNA-kortteja lisatty:",_lisatty)

# 3e) the lecture recording raises things the slides never state, plus two the slides do
#     state but no card covered.
_LISAT = [
    ('Tarvitaanko peptidin syntyyn aina ribosomi?',
     'Ei aina. Osa peptideistä syntyy entsyymien katalysoimana ilman ribosomia.',
     'Ribosomi on elämälle niin perustavanlaatuinen, että sitä pidetään pakollisena: lähes kaikki proteiinit syntyvät ribosomeissa translaatiossa. Tähänkin yleistykseen on kuitenkin pakollinen poikkeus. Osa lyhyistä peptideistä syntyy ilman ribosomia, suoraan entsyymien katalysoimina, jolloin niiden aminohappojärjestys ei tule lähetti-RNA:sta vaan on kirjoitettu itse entsyymin rakenteeseen. Tällaisia peptidejä ovat esimerkiksi monet bakteerien tuottamat antibiootit.',
     '2', ''),
    ('Missä kulkee yksisoluisen ja monisoluisen eliön raja?',
     'Raja on liukuva. Biologia ei asetu ihmisen tekemiin luokkiin.',
     'Raja ei ole terävä. Jos bakteerit muodostavat yhteisön tai yksi solu monistaa itseään niin, että solut toimivat yhdessä, luokittelu on tulkinnanvaraista. Lisäksi on obligaatteja symbiooseja, joissa eliöltä puuttuu osa elämään tarvittavasta koneistosta ja se lainaa sitä toiselta eliöltä, joten se ei pärjää yksin. Ihminen pyrkii lokeroimaan asiat, mutta biologia ei välitä lokeroista.',
     '2', ''),
    ('Ovatko bakteerit aina eläinsolua pienempiä?',
     'Eivät. Tunnetaan bakteereja, jotka ovat millimetrien kokoisia.',
     'Tyypillisesti kyllä: bakteerisolu on 1-2 µm ja eläinsolu 5-100 µm, eli bakteeri on monta kertaa pienempi. Yleistykseen on kuitenkin poikkeus, sillä tunnetaan bakteereja, jotka ovat millimetrien kokoisia eli kymmeniä kertoja suurempia kuin tavallinen eläinsolu. Koko ei siis yksin erota tumatonta tumallisesta, vaan ratkaisevaa on solun sisäinen rakenne.',
     '1', ''),
    ('Mistä kolmen domeenin malli sai alkunsa?',
     'Ribosomaalisen RNA:n geenianalyyseistä 1970-luvulla.',
     'Ennen 1970-lukua eliökunta jaettiin helposti havaittavan eron mukaan tumattomiin ja tumallisiin. Kun ribosomaalisen RNA:n geenejä alettiin analysoida, huomattiin, että tumattomien joukossa on kaksi selvästi erilaista ryhmää, bakteerit ja arkeonit. Kolmas ryhmä lisättiin aiempien rinnalle, ja niin syntyi kolmen domeenin malli. Uudempi geenidata siirsi tumalliset arkeonien sisälle.',
     '2', ''),
    ('Mikä on bioinformatiikka?',
     'Biologisia sekvenssejä ja niiden käsittelyä tutkiva laskennallinen ala.',
     'Bioinformatiikka on tieteenala, joka tutkii biologisia sekvenssejä ja niiden käsittelyä laskennallisin menetelmin. Sitä tarvitaan, koska sekä nukleiinihappojen että proteiinien toiminta perustuu rakenneosien järjestykseen ja mahdollisia järjestyksiä on käytännössä rajattomasti. Tietokoneella laskemalla saadaan uutta tietoa biologisista järjestelmistä ilman laboratoriomittauksia, ja monessa tutkimuksessa laskennallinen osuus tehdään ennen kokeellista työtä.',
     '2', 'bioinformatiikka, bioinformatiikan, bioinformatiikkaa, bioinformatiikassa, bioinformatiikasta, bioinformatiikkaan'),
    ('Mikä on HeLa-solulinja?',
     'Henrietta Lacksin kohdunkaulan syöpäsoluista peräisin oleva ihmissolulinja.',
     'HeLa on viljelty ihmissolulinja, joka on peräisin Henrietta Lacksin kohdunkaulan syövästä. Soluja on kasvatettu laboratorioissa yli viisikymmentä vuotta ympäri maailmaa, ja ne ovat yksi biokemian ja solubiologian tavallisimmista malliorganismeista. Solulinja käyttäytyy melkein kuin yksisoluinen eliö, ja syövän vuoksi sillä on muun muassa eri määrä kromosomeja kuin alkuperäisillä soluilla.',
     '1', 'HeLa, HeLa-solu, HeLa-solut, HeLa-soluja, HeLa-solulinja, HeLa-solulinjan, Henrietta Lacks, Henrietta Lacksin'),
    ('Kuka kuvasi solut ensimmäisenä ja milloin?',
     'Robert Hooke vuonna 1665, korkin soluja mikroskoopilla.',
     'Robert Hooke piirsi vuonna 1665 korkin soluja mikroskoopilla ja antoi niille nimen solu. Hän ei vielä ymmärtänyt, mitä rakenteet olivat tai mitä ne tekivät, mutta mikroskoopilla oli mahdollista nähdä, että kudos koostuu erillisistä pikkulokeroista. Havainto on solubiologian lähtökohta, sillä sen jälkeen alettiin tutkia, mitä solun sisällä on.',
     '1', ''),
    ('Kuinka suureksi yksi solu voi kasvaa?',
     'Nitella-levän solu on useita senttimetrejä pitkä.',
     'Tumallisen solun kokoa ei rajoita pelkkä aineiden kulkeutuminen, koska tukiranka tekee solunsisäisestä kuljetuksesta tehokasta. Siksi tumalliset solut voivat olla paljon suurempia kuin tumattomat, jotka luottavat pelkkään lämpöliikkeeseen. Äärimmäinen esimerkki on Nitella-levän solu, joka on useita senttimetrejä pitkä eli tuhansia kertoja pidempi kuin tavallinen 5-100 µm:n eläinsolu.',
     '1', ''),
    ('Miten metformiini liittyy mitokondrioiden bakteerialkuperään?',
     'Se vaikuttaa sekä mitokondrioihin että suolistobakteereihin, jotka ovat sukua keskenään.',
     'Metformiini on kakkostyypin diabeteksen hoitoon käytetty lääke, jonka on todettu vaikuttavan ihmisen mitokondrioihin. Samaan aikaan on huomattu, että se muuttaa suolistomikrobistoa ja toimii vähän kuin antibiootti. Havainnot sopivat yhteen, koska mitokondriot ovat syntyneet endosymbioosissa ja ovat sukua alfaproteobakteereille, joten sama vaikutus voi osua molempiin kohteisiin.',
     '1', 'metformiini, metformiinin, metformiinia, metformiinissa, metformiinista, metformiiniin'),
    ('Miksi banaanikärpänen sopii kromosomien tarkasteluun?',
     'Sen jättikromosomit näkyvät tavallisella valomikroskoopilla.',
     'Drosophila melanogaster on genetiikan työjuhta, koska sitä voi kasvattaa pienessä tilassa eikä sen käsittely vaadi erikoislaitteita. Lisäksi sen sylkirauhasissa on jättikromosomeja, jotka ovat monistuneet niin moninkertaisiksi, että ne erottuvat tavallisella valomikroskoopilla. Siksi kromosomien rakennetta voi tarkastella suoraan opiskelijatyönä ilman raskaita menetelmiä, ja lajilla on tutkittu hyvin monia perinnöllisyyden perusilmiöitä.',
     '1', ''),
]
_lisatty2=0
_olemassa2={_kys((r[0].split(SEP)+[''])[0])
            for r in cur.execute("select flds from notes n join cards c on c.nid=n.id where c.did=?", (tid,))}
if _solukko_mid:
    _due=(cur.execute("select coalesce(max(due),0) from cards where did=?", (tid,)).fetchone()[0] or 0)+1
    for _k,_sup,_laa,_st,_lk in _LISAT:
        if _k in _olemassa2: continue
        _f=[_k,_sup,_laa,_st,'',_lk]
        _guid=''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(10))
        _csum=int(hashlib.sha1(_k.encode('utf-8')).hexdigest()[:8],16)
        _nid=now*1000+940+_lisatty2
        cur.execute("insert into notes values (?,?,?,?,?,?,?,?,?,?,?)",
                    (_nid,_guid,int(_solukko_mid),now,-1,'',SEP.join(_f),_k,_csum,0,''))
        cur.execute("insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (_nid+1,_nid,tid,0,now,-1,0,0,_due,0,0,0,0,0,0,0,0,''))
        _due+=1; _lisatty2+=1
    con.commit()
print("transkriptiokortteja lisatty:",_lisatty2)

# 3d) inflected forms harvested from the deck's own text: every form that actually occurs is a
#     trigger, so no occurrence is left unlinked because a case form was not guessed in advance.
_lp=os.path.join(SC,"linkkilisat.txt")
if os.path.exists(_lp):
    _lisat={}
    for _l in open(_lp,encoding="utf-8"):
        _c=_l.rstrip("\n").split("\t")
        if len(_c)==3 and _c[0].strip()=='solu': _lisat.setdefault(_c[1].strip(),[]).append(_c[2].strip())
    _ll=0; _lm=0
    for nid in [r[0] for r in cur.execute("select distinct nid from cards where did=?", (tid,))]:
        flds=cur.execute("select flds from notes where id=?", (nid,)).fetchone()[0]
        f=Flds(flds)
        muodot=_lisat.get(_kys(f[0]))
        if not muodot or len(f)<6: continue
        olemassa={w.strip().lower() for w in re.sub('<[^>]*>','',f[5]).split(',')}
        uudet=[m for m in muodot if m.lower() not in olemassa]
        if not uudet: continue
        _pohja=f[5].rstrip().rstrip(',')
        f[5]=(_pohja+', ' if _pohja else '')+', '.join(uudet)   # the field can start out empty
        cur.execute("update notes set flds=?, mod=?, usn=-1 where id=?", (f.join(), now, nid))
        _ll+=1; _lm+=len(uudet)
    con.commit()   # step 4 closes the db without committing, so this pass must commit itself
    print("linkkisanoja lisatty:",_lm,"muotoa",_ll,"kortille")
else:
    print("HUOM: linkkilisat.txt puuttuu")

# 4) keep only the media actually referenced by the remaining notes
mediamap={}
mp=os.path.join(work,'media')
if os.path.exists(mp):
    try: mediamap=json.loads(open(mp,encoding='utf-8').read() or '{}')
    except Exception: mediamap={}
used=set()
for (flds,) in cur.execute("select flds from notes"):
    for m in re.findall(r'src\s*=\s*["\']([^"\']+)["\']', flds): used.add(os.path.basename(m))
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

# 3f) the site lists a deck in cards.id order, so the oldest cards lead. Move the redox set to the
#     end by giving those notes and cards ids above every other id in the deck.
_LOPPUUN=['Mikä on elektroninsiirtoreaktio', 'hapettuminen eli', 'pelkistyminen eli',
          'hapetus-pelkistysreaktio eli', 'redox-reaktio eli', 'Miten elektroninsiirtoreaktio']
_maxN=cur.execute("select max(id) from notes").fetchone()[0] or 0
_maxC=cur.execute("select max(id) from cards").fetchone()[0] or 0
_pohja=max(_maxN,_maxC)+1000
_siirto=[]
for _nid,_flds in cur.execute("select id, flds from notes"):
    _q=_kys((_flds.split(SEP)+[''])[0])
    if any(_q.startswith(_k) for _k in _LOPPUUN): _siirto.append((_nid,_q))
_siirto.sort()
for _i,(_vanha,_q) in enumerate(_siirto):
    _uusi=_pohja+_i*10
    cur.execute("update cards set id=? where nid=? and id=(select min(id) from cards where nid=?)",
                (_uusi+1,_vanha,_vanha))
    cur.execute("update cards set nid=? where nid=?", (_uusi,_vanha))
    cur.execute("update notes set id=? where id=?", (_uusi,_vanha))
con.commit()
print("loppuun siirretty:",len(_siirto),"korttia")

con.close()
newmedia={}; files=[]; i=0
for num,name in mediamap.items():
    if name in used and os.path.exists(os.path.join(work,num)):
        newmedia[str(i)]=name; files.append((str(i),os.path.join(work,num))); i+=1
print("mediaa mukaan:",len(newmedia),"/",len(mediamap))

# 5) rezip
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
    z.write(db, dbname)
    z.writestr('media', json.dumps(newmedia))
    for num,path in files: z.write(path, num)
shutil.rmtree(work, ignore_errors=True)

print("kirjoitettu:",OUT, os.path.getsize(OUT),"tavua")
