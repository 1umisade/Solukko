# -*- coding: utf-8 -*-
"""Funktionaalisten ryhmien mallimolekyylit simulaattoriin ja popupiin (omistaja 12.9.2026: 'solukko-kortit jokaisesta
funktionaalisesta ryhmasta, 2D- ja 3D-mallit'). Jokaiselle Lehningerin kuvan 1-16 ryhmalle pienin luonteva molekyyli,
jossa ryhma on: etanoli hydroksyylille, asetoni ketonille, metaanitioli sulfhydryylille jne. Kortit tekee ryhmat_kortit.py.
Omistaja 14.9.2026: jokaisella ryhmakortilla NELJA yhdistetta (pienin malli + kurssin biomolekyyleja, KORTIT_MALLIT), joissa
ryhman atomit korostetaan vihrealla aariviivalla: ryhmat_smarts.py tunnistaa atomit, ja niiden indeksit (mol2-tiedoston
jarjestys) kirjoitetaan molekyylit.json:iin (ryhmat: {ryhma: [i, ...]}); kaava2d.py piirtaa saman korostuksen 2D-kaavaan.

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
from ryhmat_smarts import RYHMAT, ryhman_atomit, mol2_molekyyli

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
    # 14.9.2026: kolme lisayhdistetta joka ryhmalle (KORTIT_MALLIT) - kurssin biomolekyyleja, joissa ryhma on
    ('ALANIINI',             'alaniini',               'CC(N)C(=O)O',                 'C₃H₇NO₂',       []),
    ('TYMIINI',              'tymiini',                'Cc1c[nH]c(=O)[nH]c1=O',       'C₅H₆N₂O₂',      []),
    ('ISOLEUSIINI',          'isoleusiini',            'CCC(C)C(N)C(=O)O',            'C₆H₁₃NO₂',      []),
    ('FENYYLIALANIINI',      'fenyylialaniini',        'NC(Cc1ccccc1)C(=O)O',         'C₉H₁₁NO₂',      []),
    ('TYROSIINI',            'tyrosiini',              'NC(Cc1ccc(O)cc1)C(=O)O',      'C₉H₁₁NO₃',      []),
    ('BENTSOAATTI',          'bentsoaatti',            '[O-]C(=O)c1ccccc1',           'C₇H₅O₂⁻',       []),
    ('PYRUVAATTI',           'pyruvaatti',             'CC(=O)C(=O)[O-]',             'C₃H₃O₃⁻',       []),
    ('GLYSERALDEHYDI',       'glyseraldehydi',         'OCC(O)C=O',                   'C₃H₆O₃',        []),
    ('FORMALDEHYDI',         'formaldehydi',           'C=O',                         'CH₂O',          ['metanaali']),
    ('GLUKOOSIAVO',          'glukoosi (avoketju)',    'OC[C@H](O)[C@@H](O)[C@H](O)[C@H](O)C=O', 'C₆H₁₂O₆', []),
    ('DIHYDROKSIASETONI',    'dihydroksiasetoni',      'OCC(=O)CO',                   'C₃H₆O₃',        []),
    ('FRUKTOOSIAVO',         'fruktoosi (avoketju)',   'OCC(=O)[C@@H](O)[C@H](O)[C@H](O)CO', 'C₆H₁₂O₆', []),
    ('ETIKKAHAPPO',          'etikkahappo',            'CC(=O)O',                     'CH₃COOH',       []),
    ('MAITOHAPPO',           'maitohappo',             'CC(O)C(=O)O',                 'C₃H₆O₃',        []),
    ('GLYSIINI',             'glysiini',               'NCC(=O)O',                    'C₂H₅NO₂',       []),
    ('PALMITIINIHAPPO',      'palmitiinihappo',        'CCCCCCCCCCCCCCCC(=O)O',       'C₁₆H₃₂O₂',      []),
    ('GLYSEROLI',            'glyseroli',              'OCC(O)CO',                    'C₃H₈O₃',        []),
    ('SERIINI',              'seriini',                'NC(CO)C(=O)O',                'C₃H₇NO₃',       []),
    ('GLUKOOSI',             'glukoosi',               'OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O', 'C₆H₁₂O₆', []),
    ('PEP',                  'fosfoenolipyruvaatti',   'C=C(OP(=O)([O-])[O-])C(=O)[O-]', 'C₃H₂O₆P³⁻',  []),
    ('ASKORBIINIHAPPO',      'askorbiinihappo',        'OC[C@H](O)[C@H]1OC(=O)C(O)=C1O', 'C₆H₈O₆',     ['C-vitamiini']),
    ('PROPEN2OLI',           'propen-2-oli',           'CC(O)=C',                     'C₃H₆O',         []),
    ('DIETYYLIEETTERI',      'dietyylieetteri',        'CCOCC',                       'C₄H₁₀O',        []),
    ('TETRAHYDROFURAANI',    'tetrahydrofuraani',      'C1CCOC1',                     'C₄H₈O',         []),
    ('MALTOOSI',             'maltoosi',               'OCC1OC(OC2C(O)C(O)C(O)OC2CO)C(O)C(O)C1O', 'C₁₂H₂₂O₁₁', []),
    ('ASETYYLIKOLIINI',      'asetyylikoliini',        'CC(=O)OCC[N+](C)(C)C',        'C₇H₁₆NO₂⁺',     []),
    ('TRIBUTYRIINI',         'tributyriini',           'CCCC(=O)OCC(COC(=O)CCC)OC(=O)CCC', 'C₁₅H₂₆O₆',  []),
    ('NASETYYLIKYSTEIINI',   'N-asetyylikysteiini',    'CC(=O)NC(CS)C(=O)O',          'C₅H₉NO₃S',      []),
    ('PROPIONIHAPPOANHYDRIDI', 'propionihappoanhydridi', 'CCC(=O)OC(=O)CC',           'C₆H₁₀O₃',       []),
    ('MERIPIHKAHAPPOANHYDRIDI', 'meripihkahappoanhydridi', 'O=C1CCC(=O)O1',           'C₄H₄O₃',        []),
    ('MALEIINIHAPPOANHYDRIDI', 'maleiinihappoanhydridi', 'O=C1C=CC(=O)O1',            'C₄H₂O₃',        []),
    ('LYSIINI',              'lysiini',                'NCCCCC(N)C(=O)O',             'C₆H₁₄N₂O₂',     []),
    ('ETANOLIAMIINI',        'etanoliamiini',          'NCCO',                        'C₂H₇NO',        []),
    ('GLUTAMIINI',           'glutamiini',             'NC(=O)CCC(N)C(=O)O',          'C₅H₁₀N₂O₃',     []),
    ('ASPARAGIINI',          'asparagiini',            'NC(=O)CC(N)C(=O)O',           'C₄H₈N₂O₃',      []),
    ('GLYSYYLIGLYSIINI',     'glysyyliglysiini',       'NCC(=O)NCC(=O)O',             'C₄H₈N₂O₃',      []),
    ('PROPAN2IMIINI',        'propan-2-imiini',        'CC(C)=N',                     'C₃H₇N',         []),
    ('KREATINIINI',          'kreatiniini',            'CN1CC(=O)N=C1N',              'C₄H₇N₃O',       []),
    ('P5C',                  'pyrroliini-5-karboksylaatti', 'OC(=O)C1CCC=N1',         'C₅H₇NO₂',       []),
    ('BENTSYLIDEENIMETYYLIAMIINI', 'N-bentsylideenimetyyliamiini', 'CN=Cc1ccccc1',    'C₈H₉N',         []),
    ('PLPMETYYLIIMIINI',     'PLP-metyyli-imiini',     'Cc1ncc(COP(=O)(O)O)c(C=NC)c1O', 'C₉H₁₃N₂O₅P',  []),
    ('ASETONIMETYYLIIMIINI', 'N-metyylipropan-2-imiini', 'CC(C)=NC',                  'C₄H₉N',         []),
    ('ARGINIINI',            'arginiini',              'NC(CCCNC(N)=N)C(=O)O',        'C₆H₁₄N₄O₂',     []),
    ('KREATIINI',            'kreatiini',              'CN(CC(=O)O)C(N)=N',           'C₄H₉N₃O₂',      []),
    ('GUANIDIINI',           'guanidiini',             'NC(N)=N',                     'CH₅N₃',         []),
    ('HISTIDIINI',           'histidiini',             'NC(Cc1c[nH]cn1)C(=O)O',       'C₆H₉N₃O₂',      []),
    ('HISTAMIINI',           'histamiini',             'NCCc1c[nH]cn1',               'C₅H₉N₃',        []),
    ('IMIDATSOLI',           'imidatsoli',             'c1c[nH]cn1',                  'C₃H₄N₂',        []),
    ('KYSTEIINI',            'kysteiini',              'NC(CS)C(=O)O',                'C₃H₇NO₂S',      []),
    ('GLUTATIONI',           'glutationi',             'NC(CCC(=O)NC(CS)C(=O)NCC(=O)O)C(=O)O', 'C₁₀H₁₇N₃O₆S', []),
    ('MERKAPTOETANOLI',      'merkaptoetanoli',        'OCCS',                        'C₂H₆OS',        []),
    ('KYSTIINI',             'kystiini',               'NC(CSSCC(N)C(=O)O)C(=O)O',    'C₆H₁₂N₂O₄S₂',   []),
    ('LIPOIINIHAPPO',        'lipoiinihappo',          'OC(=O)CCCCC1CCSS1',           'C₈H₁₄O₂S₂',     []),
    ('DIETYYLIDISULFIDI',    'dietyylidisulfidi',      'CCSSCC',                      'C₄H₁₀S₂',       []),
    ('SASETYYLIKYSTEAMIINI', 'S-asetyylikysteamiini',  'CC(=O)SCCN',                  'C₄H₉NOS',       []),
    ('ASETYYLIPANTETEIINI',  'asetyylipanteteiini',    'CC(=O)SCCNC(=O)CCNC(=O)C(O)C(C)(C)CO', 'C₁₃H₂₄N₂O₄S', []),
    ('ASETYYLICOA',          'asetyylikoentsyymi A',   'CC(=O)SCCNC(=O)CCNC(=O)[C@H](O)C(C)(C)COP(=O)(O)OP(=O)(O)OC[C@H]1O[C@@H](n2cnc3c(N)ncnc23)[C@H](O)[C@@H]1OP(=O)(O)O', 'C₂₃H₃₈N₇O₁₇P₃S', ['asetyyli-CoA']),
    ('FOSFOSERIINI',         'fosfoseriini',           'NC(COP(=O)([O-])[O-])C(=O)O', 'C₃H₆NO₆P²⁻',    []),
    ('PYROFOSFAATTI',        'pyrofosfaatti',          '[O-]P(=O)([O-])OP(=O)([O-])[O-]', 'P₂O₇⁴⁻',     ['difosfaatti']),
    ('BPG13',                '1,3-bisfosfoglyseraatti', 'O=C(OP(=O)([O-])[O-])C(O)COP(=O)([O-])[O-]', 'C₃H₄O₁₀P₂⁴⁻', []),
    ('KARBAMOYYLIFOSFAATTI', 'karbamoyylifosfaatti',   'NC(=O)OP(=O)([O-])[O-]',      'CH₂NO₅P²⁻',     []),
    ('PROPIONYYLIFOSFAATTI', 'propionyylifosfaatti',   'CCC(=O)OP(=O)([O-])[O-]',     'C₃H₅O₅P²⁻',     []),
    # simulaattorin oma ATP/ADP on NADP-tietueesta muokattu (atpFrom), joten sen atomijarjestysta ei voi laskea SMARTSilla:
    # ryhmakortit kayttavat omaa SMILES-mallia (ei popup-laukaisijoita, ne pysyvat vanhalla ATP/ADP-lajilla)
    ('ATPK',                 'ATP',                    'Nc1ncnc2n(cnc12)[C@@H]1O[C@H](COP(=O)([O-])OP(=O)([O-])OP(=O)([O-])[O-])[C@@H](O)[C@H]1O', 'C₁₀H₁₂N₅O₁₃P₃⁴⁻', []),
    ('ADPK',                 'ADP',                    'Nc1ncnc2n(cnc12)[C@@H]1O[C@H](COP(=O)([O-])OP(=O)([O-])[O-])[C@@H](O)[C@H]1O', 'C₁₀H₁₂N₅O₁₀P₂³⁻', []),
]
# ryhmakortin nelja yhdistetta (omistaja 14.9.2026): pienin malli ensin - se yksi nakyy, kun kortti on popup
KORTIT_MALLIT = {
    'metyyliryhmä':        ['ETAANI', 'ALANIINI', 'ASETAATTI', 'TYMIINI'],
    'etyyliryhmä':         ['PROPAANI', 'ETANOLI', 'ETYYLIASETAATTI', 'ISOLEUSIINI'],
    'fenyyliryhmä':        ['TOLUEENI', 'FENYYLIALANIINI', 'TYROSIINI', 'BENTSOAATTI'],
    'karbonyyliryhmä':     ['ASETONI', 'ASETALDEHYDI', 'PYRUVAATTI', 'GLYSERALDEHYDI'],
    'aldehydiryhmä':       ['ASETALDEHYDI', 'FORMALDEHYDI', 'GLYSERALDEHYDI', 'GLUKOOSIAVO'],
    'ketoniryhmä':         ['ASETONI', 'PYRUVAATTI', 'DIHYDROKSIASETONI', 'FRUKTOOSIAVO'],
    'karboksyyliryhmä':    ['ETIKKAHAPPO', 'MAITOHAPPO', 'GLYSIINI', 'PALMITIINIHAPPO'],
    'hydroksyyliryhmä':    ['ETANOLI', 'GLYSEROLI', 'SERIINI', 'GLUKOOSI'],
    'enoliryhmä':          ['ETENOLI', 'PROPEN2OLI', 'PEP', 'ASKORBIINIHAPPO'],
    'eetteriryhmä':        ['DME', 'DIETYYLIEETTERI', 'TETRAHYDROFURAANI', 'MALTOOSI'],
    'esteriryhmä':         ['ETYYLIASETAATTI', 'METYYLIASETAATTI', 'ASETYYLIKOLIINI', 'TRIBUTYRIINI'],
    'asetyyliryhmä':       ['METYYLIASETAATTI', 'ASETAMIDI', 'ASETYYLIKOLIINI', 'NASETYYLIKYSTEIINI'],
    'happoanhydridi':      ['ETIKKAHAPPOANHYDRIDI', 'PROPIONIHAPPOANHYDRIDI', 'MERIPIHKAHAPPOANHYDRIDI', 'MALEIINIHAPPOANHYDRIDI'],
    'aminoryhmä':          ['METYYLIAMMONIUM', 'GLYSIINI', 'LYSIINI', 'ETANOLIAMIINI'],
    'amidiryhmä':          ['ASETAMIDI', 'GLUTAMIINI', 'ASPARAGIINI', 'GLYSYYLIGLYSIINI'],
    'imiiniryhmä':         ['ETAANIIMIINI', 'PROPAN2IMIINI', 'KREATINIINI', 'P5C'],
    'Schiffin emäs':       ['NMETYYLIETAANIIMIINI', 'ASETONIMETYYLIIMIINI', 'BENTSYLIDEENIMETYYLIAMIINI', 'PLPMETYYLIIMIINI'],
    'guanidiiniryhmä':     ['METYYLIGUANIDINIUM', 'GUANIDIINI', 'ARGINIINI', 'KREATIINI'],
    'imidatsoliryhmä':     ['METYYLIIMIDATSOLI', 'IMIDATSOLI', 'HISTIDIINI', 'HISTAMIINI'],
    'sulfhydryyliryhmä':   ['METAANITIOLI', 'MERKAPTOETANOLI', 'KYSTEIINI', 'GLUTATIONI'],
    'disulfidisidos':      ['DMDS', 'DIETYYLIDISULFIDI', 'KYSTIINI', 'LIPOIINIHAPPO'],
    'tioesteri':           ['METYYLITIOASETAATTI', 'SASETYYLIKYSTEAMIINI', 'ASETYYLIPANTETEIINI', 'ASETYYLICOA'],
    'fosforyyliryhmä':     ['METYYLIFOSFAATTI', 'FOSFOSERIINI', 'G6P', 'ATPK'],
    'fosfoanhydridisidos': ['DIMETYYLIDIFOSFAATTI', 'PYROFOSFAATTI', 'ADPK', 'ATPK'],
    'asyylifosfaatti':     ['ASETYYLIFOSFAATTI', 'PROPIONYYLIFOSFAATTI', 'KARBAMOYYLIFOSFAATTI', 'BPG13'],
}


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
    if not w.endswith('i'): return [] if '(' in w else [w]   # 'etikkahappo', 'PEP': vain perusmuoto laukaisee popupin; '(avoketju)'-nimet eivat ollenkaan
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
        sanat = [] if key in ('ATPK', 'ADPK') else taivuta(nimi)   # korttimallit eivat vie ATP/ADP-sanojen popupia vanhalta lajilta
        for r in rinnakkaiset: sanat += taivuta(r)
        molj[key] = {'nimi': nimi, 'kaava': kaava, 'kaavat': [kaava], 'sanat': sanat, 'kuva2d': '2d/%s.svg' % key}
    # simulaattorin taulut: SMALL (laji, nimi, tiedosto), NAME_FI, FORMULA - rivin loppuun, vain puuttuvat
    s, a = lisaa_tauluun(s, 'const SMALL = [', small, '];', "['%s',")
    s, b = lisaa_tauluun(s, 'const NAME_FI = {', nimet, '};', " %s:'")
    s, c = lisaa_tauluun(s, 'const FORMULA = {', kaavat, '};', " %s:'")
    if a or b or c: io.open(P, 'w', encoding='utf-8', newline='').write(s); print('  simulaatiot/index.html: taulut paivitetty')
    else: print('  simulaatiot/index.html: kaikki lajit jo tauluissa')
    # ryhmakorttien yhdisteet: ryhman atomit 3D-mallissa (mol2:n jarjestys) -> molekyylit.json ryhmat, ja 2D-kaavaa varten
    # smiles.json ryhmat (kaava2d.py piirtaa korostetun kaavan 2d/AVAIN__ryhma.svg)
    for ryhma, avaimet in KORTIT_MALLIT.items():
        for key in avaimet:
            m3 = mol2_molekyyli(os.path.join(SIM, key + '.mol2'))   # LAJIT-lajit ja G6P: AVAIN.mol2
            idx = ryhman_atomit(m3, ryhma)
            if not idx: print('  HUOM ryhmaa ei loydy 3D-mallista: %s / %s' % (ryhma, key))
            molj.setdefault(key, {}).setdefault('ryhmat', {})[ryhma] = idx
            if key in smiles: smiles[key].setdefault('ryhmat', []); (smiles[key]['ryhmat'].append(ryhma) if ryhma not in smiles[key]['ryhmat'] else None)
    io.open(os.path.join(SC, 'smiles.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(smiles, ensure_ascii=False, indent=1) + '\n')
    io.open(os.path.join(SIM, 'kortit', 'molekyylit.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(molj, ensure_ascii=False, indent=1) + '\n')
    print('  smiles.json + molekyylit.json: %d lajia' % len(LAJIT))
    print('Seuraavaksi: python tyokalut/kaava2d.py && python tyokalut/kortti_build.py')


if __name__ == '__main__':
    main()
