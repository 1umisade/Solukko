# -*- coding: utf-8 -*-
"""Funktionaalisten ryhmien mallimolekyylit simulaattoriin ja popupiin (omistaja 12.9.2026: 'solukko-kortit jokaisesta
funktionaalisesta ryhmasta, 2D- ja 3D-mallit'). Jokaiselle Lehningerin kuvan 1-16 ryhmalle pienin luonteva molekyyli,
jossa ryhma on: etanoli hydroksyylille, asetoni ketonille, metaanitioli sulfhydryylille jne. Kortit tekee ryhmat_kortit.py.

Sama reitti kuin molekyyli_3d.py:ssa: RDKit rakentaa 3D-geometrian SMILESista (vedyt mukana), mol2 simulaatiot/-kansioon,
laji SMALL/NAME_FI/FORMULA-tauluihin, smiles.json (2D-kaava) ja molekyylit.json (popupin laukaisijat: nimen sijamuodot).
Idempotentti. Aja: python tyokalut/ryhmat_3d.py && python tyokalut/kaava2d.py && python tyokalut/kortti_build.py"""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC); SIM = os.path.join(REPO, 'simulaatiot')
sys.path.insert(0, SC)
from molekyyli_3d import rakenna_smiles, mol2
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# avain, suomenkielinen nimi, SMILES, popupin otsikkokaava, rinnakkaisnimet
LAJIT = [
    ('ETAANI',               'etaani',                 'CC',                          'C₂H₆',          []),
    ('PROPAANI',             'propaani',               'CCC',                         'C₃H₈',          []),
    ('TOLUEENI',             'tolueeni',               'Cc1ccccc1',                   'C₇H₈',          ['metyylibentseeni']),
    ('ASETALDEHYDI',         'asetaldehydi',           'CC=O',                        'CH₃CHO',        ['etanaali']),
    ('ASETONI',              'asetoni',                'CC(C)=O',                     'CH₃COCH₃',      ['propanoni']),
    ('ASETAATTI',            'asetaatti',              'CC(=O)[O-]',                  'CH₃COO⁻',       ['asetaatti-ioni']),
    ('ETANOLI',              'etanoli',                'CCO',                         'C₂H₅OH',        []),
    ('ETENOLI',              'etenoli',                'C=CO',                        'CH₂=CHOH',      ['vinyylialkoholi']),
    ('DME',                  'dimetyylieetteri',       'COC',                         'CH₃OCH₃',       []),
    ('ETYYLIASETAATTI',      'etyyliasetaatti',        'CC(=O)OCC',                   'CH₃COOC₂H₅',    []),
    ('METYYLIASETAATTI',     'metyyliasetaatti',       'CC(=O)OC',                    'CH₃COOCH₃',     []),
    ('ETIKKAHAPPOANHYDRIDI', 'etikkahappoanhydridi',   'CC(=O)OC(=O)C',               '(CH₃CO)₂O',     []),
    ('METYYLIAMMONIUM',      'metyyliammoniumioni',    'C[NH3+]',                     'CH₃NH₃⁺',       []),
    ('ASETAMIDI',            'asetamidi',              'CC(N)=O',                     'CH₃CONH₂',      []),
    ('ETAANIIMIINI',         'etaani-imiini',          'CC=N',                        'CH₃CH=NH',      []),
    ('NMETYYLIETAANIIMIINI', 'N-metyylietaani-imiini', 'CC=NC',                       'CH₃CH=NCH₃',    []),
    ('METYYLIGUANIDINIUM',   'metyyliguanidiniumioni', 'CNC(N)=[NH2+]',               'CH₃NHC(NH₂)₂⁺', []),
    ('METYYLIIMIDATSOLI',    '4-metyyli-imidatsoli',   'Cc1c[nH]cn1',                 'C₄H₆N₂',        []),
    ('METAANITIOLI',         'metaanitioli',           'CS',                          'CH₃SH',         []),
    ('DMDS',                 'dimetyylidisulfidi',     'CSSC',                        'CH₃SSCH₃',      []),
    ('METYYLITIOASETAATTI',  'S-metyylitioasetaatti',  'CC(=O)SC',                    'CH₃COSCH₃',     []),
    ('METYYLIFOSFAATTI',     'metyylifosfaatti',       'COP(=O)([O-])[O-]',           'CH₃OPO₃²⁻',     []),
    ('DIMETYYLIDIFOSFAATTI', 'dimetyylidifosfaatti',   'COP(=O)([O-])OP(=O)([O-])OC', '(CH₃O)₂P₂O₅²⁻', []),
    ('ASETYYLIFOSFAATTI',    'asetyylifosfaatti',      'CC(=O)OP(=O)([O-])[O-]',      'CH₃COOPO₃²⁻',   []),
]


def sointu(w):
    """Vokaalisointu: yhdyssanassa viimeinen osa (tavuviivan jalkeen) ratkaisee, muuten koko sana; viimeinen a/o/u/ä/ö/y
    paattaa. Palauttaa [aä-vaihtoehdot]: y:n ratkaisemaan etuvokaalisuuteen otetaan mukaan myos takavokaalinen muoto,
    koska molemmat elavat kielessa (asetaldehydiä ~ asetaldehydia)."""
    osa = w.split('-')[-1] if '-' in w else w
    v = [c for c in osa.lower() if c in 'aouäöy']
    if not v: return ['ä']
    if v[-1] in 'aou': return ['a']
    return ['ä', 'a'] if v[-1] == 'y' else ['ä']


def taivuta(w):
    """i-loppuisen sanan sijamuodot popupin laukaisijoiksi: yksikon nom, gen, part, iness, elat, illat, transl, adess, allat
    + monikon nom, gen, part, iness. Astevaihtelu tti/kki/ppi -> t/k/p heikoissa muodoissa."""
    assert w.endswith('i'), w
    S = w[:-1]                                           # vahva vartalo: asetaatt-
    W = re.sub(r'(tt|kk|pp)$', lambda m: m.group(1)[0], S)   # heikko vartalo: asetaat-
    out = [w]
    for A in sointu(w):
        out += [W+'in', S+'i'+A, W+'iss'+A, W+'ist'+A, S+'iin', W+'iksi', W+'ill'+A, W+'ille',
                W+'it', S+'ien', S+'ej'+A, W+'eiss'+A]
    seen = set(); return [x for x in out if not (x in seen or seen.add(x))]


def lisaa_tauluun(s, alku, uudet, loppu, tunnus):
    """Lisaa alkiot (avain, teksti) rivin `const X = ...` loppuun ennen sulkevaa merkkia - vain ne, joiden avainta
    (tunnus % avain, esim. "'ETAANI'" tai " ETAANI:") rivilla ei viela ole."""
    i = s.index(alku); j = s.index('\n', i); rivi = s[i:j]
    k = rivi.rstrip().rfind(loppu); assert k > 0, alku
    lisa = ''.join(t for key, t in uudet if (tunnus % key) not in rivi)
    return s[:i] + rivi[:k].rstrip() + lisa + ' ' + rivi[k:] + s[j:], bool(lisa)


def main():
    P = os.path.join(SIM, 'index.html'); s = io.open(P, encoding='utf-8', newline='').read()
    smiles = json.load(open(os.path.join(SC, 'smiles.json'), encoding='utf-8'))
    molj = json.load(open(os.path.join(SIM, 'kortit', 'molekyylit.json'), encoding='utf-8'))
    small, nimet, kaavat = [], [], []
    for key, nimi, smi, kaava, rinnakkaiset in LAJIT:
        tiedosto = key + '.mol2'; polku = os.path.join(SIM, tiedosto)
        if not os.path.exists(polku):
            m = rakenna_smiles(smi)
            io.open(polku, 'w', encoding='utf-8', newline='\n').write(mol2(m, key, nimi))
            print('  %-22s %2d atomia %2d sidosta -> %s' % (nimi, m.GetNumAtoms(), m.GetNumBonds(), tiedosto))
        m = Chem.AddHs(Chem.MolFromSmiles(smi))
        small.append((key, ", ['%s','%s','%s']" % (key, nimi, tiedosto))); nimet.append((key, ", %s:'%s'" % (key, nimi))); kaavat.append((key, ", %s:'%s'" % (key, kaava)))
        if key not in smiles: smiles[key] = {'nimi': nimi, 'smiles': smi, 'kaava': rdMolDescriptors.CalcMolFormula(m)}
        sanat = taivuta(nimi)
        for r in rinnakkaiset: sanat += taivuta(r)
        molj[key] = {'nimi': nimi, 'kaava': kaava, 'kaavat': [kaava], 'sanat': sanat, 'kuva2d': '2d/%s.svg' % key}
    # simulaattorin taulut: SMALL (laji, nimi, tiedosto), NAME_FI, FORMULA - rivin loppuun, vain puuttuvat
    s, a = lisaa_tauluun(s, 'const SMALL = [', small, '];', "['%s',")
    s, b = lisaa_tauluun(s, 'const NAME_FI = {', nimet, '};', " %s:'")
    s, c = lisaa_tauluun(s, 'const FORMULA = {', kaavat, '};', " %s:'")
    if a or b or c: io.open(P, 'w', encoding='utf-8', newline='').write(s); print('  simulaatiot/index.html: taulut paivitetty')
    else: print('  simulaatiot/index.html: kaikki lajit jo tauluissa')
    io.open(os.path.join(SC, 'smiles.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(smiles, ensure_ascii=False, indent=1) + '\n')
    io.open(os.path.join(SIM, 'kortit', 'molekyylit.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(molj, ensure_ascii=False, indent=1) + '\n')
    print('  smiles.json + molekyylit.json: %d lajia' % len(LAJIT))
    print('Seuraavaksi: python tyokalut/kaava2d.py && python tyokalut/kortti_build.py')


if __name__ == '__main__':
    main()
