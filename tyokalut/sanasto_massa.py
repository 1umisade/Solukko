# -*- coding: utf-8 -*-
"""Sanaston massakierros (omistaja 13.9.2026: 'read all the cards in solukko.apkg and make cards for each word' - sovittu
laajuus: termit ja kurssissa merkitykselliset yleiskielen sanat, ei arkisuomea eika roskaa).

Lahde: SOLUKKO.apkg:n korttitekstit lemmatisoitiin (uralicNLP, fin), ja sanat joita mikaan linkkisana ei kata jaettiin
pakoittain ensiesiintymisen mukaan. Maaritelmat ovat tekstitiedostoissa sanasto_massa/<avain>.txt, rivi per sana:
    lemma <TAB> tt <TAB> suppea [<TAB> kysymys]
Kysymys oletuksena "Mitä <lemma> tarkoittaa?". Linkkisanat = korteissa esiintyneet taivutusmuodot (sanasto_muodot.json)
+ biotek_taivutus.L:n muodot, joista suodatetaan pois muualla jo katetut. Tyhjat rivit ja #-rivit ohitetaan."""
import os, io, json
from biotek_taivutus import taiv
from pakka_rakenna import K

SC = os.path.dirname(os.path.abspath(__file__))
_M = json.load(io.open(os.path.join(SC, 'sanasto_muodot.json'), encoding='utf-8'))
MUODOT = _M['muodot']; KATETUT = set(_M['katetut'])
_omat = set()   # muodot, jotka tama kierros on jo antanut jollekin kortille (ei kahdesti)

def linkkisanat(lemma):
    out = []
    for w in [lemma] + MUODOT.get(lemma, []):
        if w.lower() not in KATETUT and w.lower() not in _omat: out.append(w); _omat.add(w.lower())
    try:
        for w in taiv(lemma):
            if w.lower() not in KATETUT and w.lower() not in _omat: out.append(w); _omat.add(w.lower())
    except ValueError:
        pass
    return ', '.join(out)

def kortit(avain):
    p = os.path.join(SC, 'sanasto_massa', avain + '.txt')
    if not os.path.exists(p): return []
    out = []
    for rivi in io.open(p, encoding='utf-8'):
        rivi = rivi.rstrip('\n')
        if not rivi.strip() or rivi.startswith('#'): continue
        osat = rivi.split('\t')
        lemma, tt, suppea = osat[0].strip(), int(osat[1]), osat[2].strip()
        kys = osat[3].strip() if len(osat) > 3 and osat[3].strip() else 'Mitä %s tarkoittaa?' % lemma
        out.append(K(kys, suppea, '', tt, linkkisanat(lemma)))
    return out
