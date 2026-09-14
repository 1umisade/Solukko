# -*- coding: utf-8 -*-
"""Kurssipakan Esittely-kortti (kurssit/CLAUDE.md §6): yksi kortti kurssia kohti, Kysymys 'Esittely', Laaja vastaus =
kansiteksti. Sivusto nayttaa sen pakan kantena (index.html _deckIntro), ei ruudukossa.

omistaja 14.9.2026: 'miksei kemia I:ssa nay esittelytekstia' -> kurssipakassa oli vain tyhja '(1) empty' -paikanvaraaja,
joka poistettiin. Tama patchaa SOLUKKO.apkg:n paikallaan: lisaa kortin kurssipakkaan (ei luentoon) tai paivittaa
tekstin guidin mukaan. Idempotentti. Ankin tuonti (SOLUKKO.apkg) tuo sen omistajan kokoelmaan.
"""
import zipfile, sqlite3, tempfile, os, json, re, time, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, 'SOLUKKO.apkg')
SEP = chr(31); MID = 1727391050   # Solukko-korttityyppi

ESITTELYT = {   # kurssipakan nimen loppu -> kansiteksti (yksi kappale, kokonaisia lauseita)
    '::Kemian peruskurssi I':
        'Kemia yhdistää atomien ja molekyylien rakenteen aineen havaittaviin ominaisuuksiin: mistä aine koostuu, '
        'miksi se käyttäytyy niin kuin käyttäytyy ja miten se muuttuu. Kurssilla opitaan kemian työtapa havainnosta '
        'hypoteesin kautta testattavaan malliin, tutustutaan kemian historian käännekohtiin ja yhdisteiden nimeämisen '
        'sääntöihin sekä perehdytään atomin rakenteeseen, jaksolliseen järjestelmään ja kvanttimekaaniseen atomimalliin.',
}


def guid_for(deck_loppu):
    h = hashlib.sha1(('solukko-esittely|' + deck_loppu).encode('utf-8')).digest()
    abc = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(abc[b % len(abc)] for b in h[:10])


if __name__ == '__main__':
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(SRC) as z: z.extractall(work)
    db = os.path.join(work, 'collection.anki21'); con = sqlite3.connect(db); cur = con.cursor()
    decks = json.loads(cur.execute("select decks from col").fetchone()[0])
    now = int(time.time()); uudet = paivitetyt = 0
    for i, (loppu, teksti) in enumerate(ESITTELYT.items()):
        kurssi = next(d for d in decks.values() if d['name'].endswith(loppu)); did = int(kurssi['id'])
        # kurssilla saa olla vain yksi Esittely: toisen (esim. kasin tehdyn) loydyttya ei tehda toista
        vieras = cur.execute("select n.id from notes n join cards c on c.nid=n.id where c.did=? and lower(n.sfld)='esittely' and n.guid!=?",
                             (did, guid_for(loppu))).fetchone()
        if vieras: print('HUOM: kurssilla on jo Esittely-kortti (nid %d), ei lisata toista:' % vieras[0], kurssi['name']); continue
        fields = ['Esittely', '', teksti, '', '', '']
        sfld = 'Esittely'; csum = int(hashlib.sha1(sfld.encode('utf-8')).hexdigest()[:8], 16)
        row = cur.execute("select id, flds from notes where guid=?", (guid_for(loppu),)).fetchone()
        if row:
            if row[1] != SEP.join(fields):
                cur.execute("update notes set flds=?, sfld=?, csum=?, mod=?, usn=-1 where id=?", (SEP.join(fields), sfld, csum, now, row[0])); paivitetyt += 1
        else:
            nid = now * 1000 + i * 2
            cur.execute("insert into notes values (?,?,?,?,?,?,?,?,?,?,?)", (nid, guid_for(loppu), MID, now, -1, '', SEP.join(fields), sfld, csum, 0, ''))
            cur.execute("insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (nid + 1, nid, did, 0, now, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ''))
            uudet += 1; print('uusi Esittely:', kurssi['name'])
    con.commit(); con.close()
    print('SOLUKKO.apkg: %d uutta, %d paivitettya' % (uudet, paivitetyt))
    if uudet or paivitetyt:
        tmp = SRC + '.uusi'
        with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
            for it in zin.infolist():
                if it.filename == 'collection.anki21': zout.write(db, 'collection.anki21')
                else: zout.writestr(it, zin.read(it.filename))
        for _ in range(20):   # OneDrive pitaa tiedostoa hetken auki
            try: os.replace(tmp, SRC); break
            except PermissionError: time.sleep(0.5)
