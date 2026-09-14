# -*- coding: utf-8 -*-
"""Funktionaalisten ryhmien tunnistus (omistaja 14.9.2026: 'korosta se funktionaalinen ryhma vihrealla outlinella').
Jokaiselle ryhmakortille SMARTS-kaavat, joilla ryhman atomit loydetaan molekyylista - samat kaavat 2D-kaavaan (kaava2d.py,
RDKit-molekyyli SMILESista) ja 3D-malliin (ryhmat_3d.py, molekyyli mol2-tiedostosta, atomien jarjestys = tiedoston).
Vedyt ovat omia atomeja, joten ne kirjoitetaan kaavaan [#1]-atomeina siella, missa ne kuuluvat ryhmaan.

RYHMAT[ryhma] = lista (smarts, pidettavat kaavan atomi-indeksit tai None = kaikki, lisaa_vedyt-indeksit)."""
from rdkit import Chem

RYHMAT = {
    'metyyliryhmä':       [('[#6]([#1])([#1])([#1])[!#1]', [0, 1, 2, 3], [])],
    'etyyliryhmä':        [('[#6]([#1])([#1])([#1])[#6]([#1])([#1])[!#1]', [0, 1, 2, 3, 4, 5, 6], [])],
    'fenyyliryhmä':       [('[#6]1~[#6]~[#6]~[#6]~[#6]~[#6]1', None, [0, 1, 2, 3, 4, 5])],
    'karbonyyliryhmä':    [('[#6]=[#8]', None, [])],
    'aldehydiryhmä':      [('[#6](=[#8])([#1])[#6,#1]', [0, 1, 2], [])],
    'ketoniryhmä':        [('[#6](=[#8])([#6])[#6]', [0, 1], [])],
    'karboksyyliryhmä':   [('[#6](=[#8])[#8;!$([#8]([#6])[#6])]', None, [2])],   # O, jolla ei ole toista hiilinaapuria (ei esteri)
    'hydroksyyliryhmä':   [('[#8]([#1])[#6;!$([#6]=[#8])]', [0, 1], [])],
    'enoliryhmä':         [('[#6]=[#6][#8]([#1])', None, []), ('[#6]=[#6][#8][#15]', [0, 1, 2], [])],
    'eetteriryhmä':       [('[#6][#8;D2;!$([#8][#6]=[#8])][#6]', None, [])],
    'esteriryhmä':        [('[#6](=[#8])[#8][#6]', [0, 1, 2], [])],
    'asetyyliryhmä':      [('[#6]([#1])([#1])([#1])[#6](=[#8])[!#1]', [0, 1, 2, 3, 4, 5], [])],
    'happoanhydridi':     [('[#6](=[#8])[#8][#6](=[#8])', None, [])],
    'aminoryhmä':         [('[#7;!$([#7][#6]=[#8]);!$([#7]=[#6])]([#1])[#6]', [0], [0])],
    'amidiryhmä':         [('[#6](=[#8])[#7]', None, [2])],
    'imiiniryhmä':        [('[#6]=[#7]', None, [1])],
    'Schiffin emäs':      [('[#6]=[#7][#6]', None, [])],
    'guanidiiniryhmä':    [('[#7][#6](~[#7])~[#7]', None, [0, 2, 3])],
    'imidatsoliryhmä':    [('[#6]1~[#7]~[#6]~[#7]~[#6]~1', None, [0, 1, 2, 3, 4])],
    'sulfhydryyliryhmä':  [('[#16]([#1])[#6]', [0, 1], [])],
    'disulfidisidos':     [('[#16][#16]', None, [])],
    'tioesteri':          [('[#6](=[#8])[#16][#6]', [0, 1, 2], [])],
    'fosforyyliryhmä':    [('[#15](~[#8])(~[#8])(~[#8])~[#8]', None, [1, 2, 3, 4])],
    'fosfoanhydridisidos': [('[#15](~[#8])(~[#8])[#8][#15](~[#8])(~[#8])', [0, 3, 4], [])],
    'asyylifosfaatti':    [('[#6](=[#8])[#8][#15](~[#8])(~[#8])~[#8]', [0, 1, 2, 3], [])],
}
_KAAVAT = {}


def ryhman_atomit(m, ryhma):
    """Ryhman atomien indeksit molekyylissa m (RDKit, vedyt eksplisiittisina atomeina). Kaikki osumat yhdistetaan."""
    out = set()
    for smarts, pida, vedyt in RYHMAT[ryhma]:
        if smarts not in _KAAVAT: _KAAVAT[smarts] = Chem.MolFromSmarts(smarts)
        for osuma in m.GetSubstructMatches(_KAAVAT[smarts], uniquify=True, useChirality=False):
            idx = list(range(len(osuma))) if pida is None else pida
            for i in idx: out.add(osuma[i])
            for i in vedyt:
                for n in m.GetAtomWithIdx(osuma[i]).GetNeighbors():
                    if n.GetAtomicNum() == 1: out.add(n.GetIdx())
    return sorted(out)


def mol2_molekyyli(polku, na_haku=None, pida_n=None):
    """mol2-tiedosto RDKit-molekyyliksi ilman sanitointia (atomit tiedoston jarjestyksessa). na_haku valitsee tietueen
    atomimaaran mukaan (nadph.mol2:n ATP = 75 atomia), pida_n katkaisee (ADP = ATP:n 71 ensimmaista atomia)."""
    teksti = open(polku, encoding='utf-8', errors='replace').read()
    tietueet = teksti.split('@<TRIPOS>MOLECULE')[1:]
    valittu = None
    for t in tietueet:
        rivit = t.strip('\n').split('\n')
        na = int(rivit[1].split()[0])
        if na_haku is None or na == na_haku: valittu = t; break
    if valittu is None: raise SystemExit('mol2: tietuetta ei loydy ' + polku)
    osio = None; atomit = []; sidokset = []
    for r in valittu.split('\n'):
        s = r.strip()
        if s.startswith('@<TRIPOS>'): osio = s; continue
        if not s: continue
        if osio == '@<TRIPOS>ATOM':
            p = s.split(); tyyppi = p[5]; alk = tyyppi.split('.')[0]
            atomit.append((alk, '.ar' in tyyppi))
        elif osio == '@<TRIPOS>BOND':
            p = s.split(); sidokset.append((int(p[1]) - 1, int(p[2]) - 1, p[3]))
    n = len(atomit) if pida_n is None else pida_n
    rw = Chem.RWMol()
    for alk, ar in atomit[:n]:
        a = Chem.Atom(alk.capitalize() if len(alk) > 1 else alk); a.SetIsAromatic(ar); a.SetNoImplicit(True); rw.AddAtom(a)
    for i, j, t in sidokset:
        if i >= n or j >= n: continue
        bt = {'1': Chem.BondType.SINGLE, '2': Chem.BondType.DOUBLE, '3': Chem.BondType.TRIPLE, 'ar': Chem.BondType.AROMATIC, 'am': Chem.BondType.SINGLE}.get(t, Chem.BondType.SINGLE)
        rw.AddBond(i, j, bt)
        if t == 'ar': rw.GetAtomWithIdx(i).SetIsAromatic(True); rw.GetAtomWithIdx(j).SetIsAromatic(True)
    m = rw.GetMol(); m.UpdatePropertyCache(strict=False); Chem.FastFindRings(m)
    return m
