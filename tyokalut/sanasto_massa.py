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
# Tiedostot kasitellaan aina tassa jarjestyksessa, jotta muotojen jako on sama riippumatta siita, mika rakentaja
# (solu, biotek, kemia, muut) kutsuu - muuten 'sato' ja 'sata' saisivat saman 'satoja'-muodon eri ajoissa.
JARJESTYS = ['solu_L1', 'solu_L2', 'solu_L3', 'solu_L4a', 'biotek_L1', 'biotek_L2', 'biotek_L3',
             'kemia_1', 'kemia_21', 'kemia_22', 'kemia_31', 'kemia_32',
             'molbio_L1', 'molbio_L2', 'molbio_L3', 'kasvibiokemia', 'harjoitustyo', 'immunologia']

def _linkkisanat(lemma):
    out = []
    for w in [lemma] + MUODOT.get(lemma, []):
        if w.lower() not in KATETUT and w.lower() not in _omat: out.append(w); _omat.add(w.lower())
    try:
        for w in taiv(lemma):
            if w.lower() not in KATETUT and w.lower() not in _omat: out.append(w); _omat.add(w.lower())
    except ValueError:
        pass
    return ', '.join(out)

def _rivit(avain):
    p = os.path.join(SC, 'sanasto_massa', avain + '.txt')
    if not os.path.exists(p): return []
    out = []
    for rivi in io.open(p, encoding='utf-8'):
        rivi = rivi.rstrip('\n')
        if not rivi.strip() or rivi.startswith('#'): continue
        osat = rivi.split('\t')
        out.append((osat[0].strip(), int(osat[1]), osat[2].strip(), osat[3].strip() if len(osat) > 3 and osat[3].strip() else ''))
    return out

_KORTIT = {}
for _a in JARJESTYS:
    _KORTIT[_a] = [(lemma, tt, suppea, kys or 'Mitä %s tarkoittaa?' % lemma, _linkkisanat(lemma)) for lemma, tt, suppea, kys in _rivit(_a)]

ARKI = set(w.strip() for w in io.open(os.path.join(SC, 'sanasto_massa', 'arkisanat.txt'), encoding='utf-8') if w.strip() and not w.startswith('#'))
def kortit(avain):   # arkisanat saavat arki-lipun: rakentaja vie ne SOLUKKO::Arkisanat-pakkaan (sama guid ja numero)
    return [K(kys, suppea, '', tt, ls, arki=(lemma in ARKI)) for lemma, tt, suppea, kys, ls in _KORTIT.get(avain, [])]
