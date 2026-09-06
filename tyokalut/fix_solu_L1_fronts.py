# -*- coding: utf-8 -*-
"""Reads the user's OWN edited Luento 1 cards from SOLUKKO.apkg and rewrites only the
bare term fronts into questions. Guids are preserved -> importing UPDATES in place
(no duplicates, review history kept). One note type: "Solukko", no ä/ö in field names."""
import genanki, zipfile, sqlite3, tempfile, os, shutil, json, sys
sys.stdout.reconfigure(encoding='utf-8')
SC=os.path.dirname(os.path.abspath(__file__))
REPO=os.path.dirname(SC)                       # tyokalut/ on repon juuressa
DECK="SOLUKKO::1. LUKUVUOSI::1.1 SYKSY::1. Periodi::Solu- ja biomolekyylit - teoria (BKEM5030)::Luento 1 - Elämä, perusteet ja periaatteet"

Q={  # bare term -> natural Finnish question
"polymeeri":"Mikä on polymeeri?","ribosomi":"Mikä on ribosomi?","solukalvo":"Mikä on solukalvo?",
"sytoplasma":"Mikä on sytoplasma?","sytosoli":"Mikä on sytosoli?","soluelin":"Mikä on soluelin?",
"genomi":"Mikä on genomi?","tuma":"Mikä on tuma?","tumakotelo":"Mikä on tumakotelo?","nukleoidi":"Mikä on nukleoidi?",
"makromolekyyli":"Mikä on makromolekyyli?","monomeeri":"Mikä on monomeeri?","nukleotidi":"Mikä on nukleotidi?",
"nukleiinihappo":"Mikä on nukleiinihappo?","aminohappo":"Mikä on aminohappo?","proteiini":"Mikä on proteiini?",
"sekvenssi":"Mitä sekvenssi tarkoittaa?","selenokysteiini":"Mikä on selenokysteiini?","iminohappo":"Mikä on iminohappo?",
"prokaryootti":"Mikä on prokaryootti?","eukaryootti":"Mikä on eukaryootti?","domeeni":"Mitä domeeni tarkoittaa taksonomiassa?",
"bakteeri":"Mikä on bakteeri?","arkeoni":"Mikä on arkeoni?","syanobakteeri":"Mikä on syanobakteeri?",
"protisti":"Mikä on protisti?","hiiva":"Mikä on hiiva?","LUCA":"Mitä LUCA tarkoittaa?","LECA":"Mitä LECA tarkoittaa?",
"endosymbioosi":"Mitä endosymbioosi tarkoittaa?","mitokondrio":"Mikä on mitokondrio?","kloroplasti":"Mikä on kloroplasti?",
"asgardarkeoni":"Mikä on asgardarkeoni?","virus":"Mikä on virus?","malliorganismi":"Mikä on malliorganismi?",
"Escherichia coli":"Mikä on Escherichia coli?","Saccharomyces cerevisiae":"Mikä on Saccharomyces cerevisiae?",
"Caenorhabditis elegans":"Mikä on Caenorhabditis elegans?","Drosophila melanogaster":"Mikä on Drosophila melanogaster?",
"Arabidopsis thaliana":"Mikä on Arabidopsis thaliana?","Danio rerio":"Mikä on Danio rerio?","Mus musculus":"Mikä on Mus musculus?",
"stromatoliitti":"Mikä on stromatoliitti?","RNA-maailmahypoteesi":"Mitä RNA-maailmahypoteesi tarkoittaa?",
"Miller-Urey-koe":"Mikä oli Miller-Urey-koe?","soluseinä":"Mikä on soluseinä?","peptidoglykaani":"Mikä on peptidoglykaani?",
"Gram-negatiivinen bakteeri":"Mikä on Gram-negatiivinen bakteeri?","pilus":"Mikä on pilus?","flagella":"Mikä on flagella?",
"plasmidi":"Mikä on plasmidi?","entsyymi":"Mikä on entsyymi?","hapetus-pelkistysreaktio":"Mikä on hapetus-pelkistysreaktio?",
"hapetin":"Mikä on hapetin?","pelkistin":"Mikä on pelkistin?","aerobinen":"Mitä aerobinen tarkoittaa?",
"anaerobinen":"Mitä anaerobinen tarkoittaa?","fototrofi":"Mikä on fototrofi?","kemotrofi":"Mikä on kemotrofi?",
"litotrofi":"Mikä on litotrofi?","organotrofi":"Mikä on organotrofi?","autotrofi":"Mikä on autotrofi?",
"heterotrofi":"Mikä on heterotrofi?","alkuaine":"Mikä on alkuaine?","kovalenttinen sidos":"Mikä on kovalenttinen sidos?",
"biomolekyyli":"Mikä on biomolekyyli?","hiilihydraatti":"Mikä on hiilihydraatti?","lipidi":"Mikä on lipidi?",
"keratiini":"Mikä on keratiini?","kollageeni":"Mikä on kollageeni?","vasta-aine":"Mikä on vasta-aine?",
"antigeeni":"Mikä on antigeeni?","selluloosa":"Mikä on selluloosa?","tärkkelys":"Mikä on tärkkelys?",
"geneettinen koodi":"Mikä on geneettinen koodi?","konfiguraatio":"Mitä konfiguraatio tarkoittaa?",
"konformaatio":"Mitä konformaatio tarkoittaa?","cis-trans-isomeria":"Mitä cis-trans-isomeria tarkoittaa?",
"stereoisomeria":"Mitä stereoisomeria tarkoittaa?","kiraalinen keskus":"Mikä on kiraalinen keskus?",
"enantiomeeri":"Mikä on enantiomeeri?","diastereomeeri":"Mikä on diastereomeeri?",
"R/S-isomeria":"Mitä R/S-isomeria tarkoittaa?","L/D-isomeria":"Mitä L/D-isomeria tarkoittaa?",
"konformeeri":"Mikä on konformeeri?","kondensaatioreaktio":"Mikä on kondensaatioreaktio?",
"informationaalinen makromolekyyli":"Mikä on informationaalinen makromolekyyli?",
"molekyylibiologian keskusdogma":"Mitä molekyylibiologian keskusdogma tarkoittaa?",
"transkriptio":"Mitä transkriptio tarkoittaa?","translaatio":"Mitä translaatio tarkoittaa?","mRNA":"Mikä on mRNA?",
"laskostuminen":"Mitä laskostuminen tarkoittaa?","supramolekulaarinen rakenne":"Mikä on supramolekulaarinen rakenne?",
"kromatiini":"Mikä on kromatiini?","histoni":"Mikä on histoni?",
"termodynamiikan ensimmäinen pääsääntö":"Mitä sanoo termodynamiikan ensimmäinen pääsääntö?",
"termodynamiikan toinen pääsääntö":"Mitä sanoo termodynamiikan toinen pääsääntö?",
"entropia":"Mitä entropia tarkoittaa?","eksergoninen reaktio":"Mikä on eksergoninen reaktio?",
"endergoninen reaktio":"Mikä on endergoninen reaktio?","kytketty reaktio":"Mikä on kytketty reaktio?",
"korkeaenerginen yhdiste":"Mikä on korkeaenerginen yhdiste?","ATP":"Mikä on ATP?","ADP":"Mikä on ADP?","NADH":"Mikä on NADH?",
"katabolia":"Mitä katabolia tarkoittaa?","anabolia":"Mitä anabolia tarkoittaa?","metabolia":"Mitä metabolia tarkoittaa?",
"reaktiotie":"Mikä on reaktiotie?","laktaatti":"Mikä on laktaatti?","pyruvaatti":"Mikä on pyruvaatti?",
"laktaattidehydrogenaasi":"Mikä on laktaattidehydrogenaasi?","hapetusluku":"Mitä hapetusluku tarkoittaa?",
"komplementaarisuus":"Mitä komplementaarisuus tarkoittaa?","mutaatio":"Mikä on mutaatio?",
"duplikaatio":"Mitä duplikaatio tarkoittaa?","luonnonvalinta":"Mitä luonnonvalinta tarkoittaa?",
"evoluutio":"Mitä on evoluutio?","erilaistuminen":"Mitä erilaistuminen tarkoittaa?",
}

# ── read the user's own cards ──
tmp=tempfile.mkdtemp(); notes=[]; allfronts=[]
try:
    with zipfile.ZipFile(os.path.join(REPO,"SOLUKKO.apkg")) as z: z.extractall(tmp)
    db=os.path.join(tmp,'collection.anki21') if os.path.exists(os.path.join(tmp,'collection.anki21')) else os.path.join(tmp,'collection.anki2')
    con=sqlite3.connect(db)
    models=json.loads(con.execute("select models from col").fetchone()[0])
    decks=json.loads(con.execute("select decks from col").fetchone()[0])
    dn={str(d['id']):d['name'] for d in decks.values()}
    for nid,guid,mid,flds in con.execute("select id,guid,mid,flds from notes"):
        did=con.execute("select did from cards where nid=? limit 1",(nid,)).fetchone()
        deck=dn.get(str(did[0]),'') if did else ''
        if not('Luento 1 - El' in deck and 'Solu- ja biomolekyylit' in deck): continue
        f=(flds.split('\x1f')+['']*6)[:6]; nm=models[str(mid)]['name']
        allfronts.append(f[0].strip())
        notes.append((guid,nm,f))
    con.close()
finally: shutil.rmtree(tmp,ignore_errors=True)

# ── notetype replicated EXACTLY as it exists in the user's collection, so Anki updates
#    the guid-matched notes instead of skipping them on a schema mismatch ──
model=genanki.Model(1727391050,"Solukko+",
  fields=[{"name":"Kysymys"},{"name":"Suppea vastaus"},{"name":"Laaja vastaus"},
          {"name":"tenttitodennäköisyys"},{"name":"3D-malli"},{"name":"linkkisanat"}],
  templates=[{"name":"Kortti","qfmt":"{{Kysymys}}",
              "afmt":'{{FrontSide}}<hr id="answer">{{Laaja vastaus}}<hr>{{Suppea vastaus}}'}],
  css="")
deck=genanki.Deck(2028010101,DECK)

changed=0; missing=[]; skipped_other=[]
newfronts=[]
for guid,nm,f in notes:
    front=f[0].strip()
    if not (f[5].strip() and not front.endswith('?')): continue     # only bare-term term cards
    if nm!='Solukko+':                                              # other note types: leave alone
        skipped_other.append((nm,front)); continue
    q=Q.get(front)
    if not q: missing.append(front); continue
    deck.add_note(genanki.Note(model=model,guid=guid,fields=[q,f[1],f[2],f[3],f[4],f[5]]))
    changed+=1; newfronts.append(q)

# collision check against every other front already in the deck
others=[x for x in allfronts]
coll=sorted({q for q in newfronts if others.count(q)>0})
print("Luento 1 -kortteja yhteensä:",len(notes))
print("muutettu (etupuoli -> kysymys):",changed)
if missing: print("EI KARTTAA (jäi muuttamatta):",missing)
if skipped_other: print("ohitettu (muu korttityyppi):",skipped_other)
print("törmäyksiä olemassa oleviin etupuoliin:", coll if coll else "ei yhtään")
genanki.Package(deck).write_to_file(os.path.join(SC,"Luento 1 - kysymysmuotoiset etupuolet (paivitys).apkg"))
print("kirjoitettu apkg")
