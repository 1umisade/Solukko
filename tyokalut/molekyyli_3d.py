# -*- coding: utf-8 -*-
"""Uusi pieni molekyyli simulaattoriin ja popupiin - tasmalleen samaa reittia kuin nykyiset (mol2-tiedosto,
SMALL-lista, molekyylit.json, 2D-kaava).

    python tyokalut/molekyyli_3d.py G6P "glukoosi-6-fosfaatti" 5958 --kaava G6P --sanat glukoosi-6-fosfaatti glukoosi-6-fosfaatin ...

1. Hakee PubChemista 3D-konformeerin vetyineen (CID) - tai --smiles annettuna rakentaa geometrian RDKitilla (ETKDG + MMFF).
2. Kirjoittaa simulaatiot/<AVAIN>.mol2 (Sybyl-atomityypit, sidoskertaluvut 1/2/3/ar) - parseMol2 lukee taman.
3. Lisaa lajin simulaatiot/index.html:n SMALL-, FORMULA- ja NAME_FI-tauluihin (ensureSpecies rakentaa sen mol2:sta).
4. Lisaa merkinnan tyokalut/smiles.json:iin (2D-kaava: aja sitten kaava2d.py) ja simulaatiot/kortit/molekyylit.json:iin.
Aja lopuksi: python tyokalut/kaava2d.py && python tyokalut/kortti_build.py
"""
import argparse, io, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors

SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SIM = os.path.join(REPO, 'simulaatiot')


def hae_pubchem_3d(cid):
    url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%d/SDF?record_type=3d' % cid
    with urllib.request.urlopen(url, timeout=60) as r: sdf = r.read().decode('utf-8')
    m = Chem.MolFromMolBlock(sdf, removeHs=False)
    if m is None: raise SystemExit('PubChem SDF ei jasentynyt')
    return m


def rakenna_smiles(smiles):
    m = Chem.AddHs(Chem.MolFromSmiles(smiles))
    if AllChem.EmbedMolecule(m, AllChem.ETKDGv3()) != 0: raise SystemExit('3D-upotus epaonnistui')
    AllChem.MMFFOptimizeMolecule(m)
    return m


SYBYL_HYB = {Chem.HybridizationType.SP: '1', Chem.HybridizationType.SP2: '2', Chem.HybridizationType.SP3: '3'}


def sybyl(a):
    s = a.GetSymbol()
    if s == 'H': return 'H'
    if a.GetIsAromatic(): return s + '.ar'
    if s in ('C', 'N', 'O', 'S', 'P'):
        return s + '.' + SYBYL_HYB.get(a.GetHybridization(), '3')
    return s


def mol2(m, key, nimi):
    conf = m.GetConformer()
    counts = {}
    o = ['@<TRIPOS>MOLECULE', '%s (%s)' % (nimi, key), '%d %d 1 0 0' % (m.GetNumAtoms(), m.GetNumBonds()), 'SMALL', 'NO_CHARGES', '', '', '@<TRIPOS>ATOM']
    for a in m.GetAtoms():
        p = conf.GetAtomPosition(a.GetIdx()); s = a.GetSymbol(); counts[s] = counts.get(s, 0) + 1
        o.append('%7d %-8s %10.4f %10.4f %10.4f %-6s %5d %-6s %9.4f' % (a.GetIdx() + 1, s + str(counts[s]), p.x, p.y, p.z, sybyl(a), 1, key[:4], float(a.GetFormalCharge())))
    o.append('@<TRIPOS>BOND')
    for b in m.GetBonds():
        t = 'ar' if b.GetIsAromatic() else {1.0: '1', 2.0: '2', 3.0: '3'}.get(b.GetBondTypeAsDouble(), '1')
        o.append('%6d %5d %5d %s' % (b.GetIdx() + 1, b.GetBeginAtomIdx() + 1, b.GetEndAtomIdx() + 1, t))
    return '\n'.join(o) + '\n'


def lisaa_simulaattoriin(key, nimi, tiedosto, kaava):
    P = os.path.join(SIM, 'index.html'); s = io.open(P, encoding='utf-8', newline='').read()
    if "['%s'," % key in s: print('  SMALL: %s on jo listassa' % key); return
    n = 0
    def sub(old, new):
        nonlocal s, n
        assert s.count(old) == 1, (s.count(old), old[:60]); s = s.replace(old, new); n += 1
    # rivin loppuun ennen sulkevaa merkkia, mika tahansa viimeinen alkio (ryhmat_3d.lisaa_tauluun; G6P:n jalkeen vanha ankkuri ei enaa osunut)
    from ryhmat_3d import lisaa_tauluun
    for alku, alkio, loppu, tunnus in (('const SMALL = [', ", ['%s','%s','%s']" % (key, nimi, tiedosto), '];', "['%s',"),
                                       ('const NAME_FI = {', ", %s:'%s'" % (key, nimi), '};', " %s:'"),
                                       ('const FORMULA = {', ", %s:'%s'" % (key, kaava), '};', " %s:'")):
        s, ok = lisaa_tauluun(s, alku, [(key, alkio)], loppu, tunnus); n += ok
    io.open(P, 'w', encoding='utf-8', newline='').write(s); print('  simulaatiot/index.html: %d taulua paivitetty' % n)


def lisaa_json(key, nimi, kaava, kaavat, sanat, smiles, molkaava):
    p = os.path.join(SC, 'smiles.json'); d = json.load(open(p, encoding='utf-8'))
    d[key] = {'nimi': nimi, 'smiles': smiles, 'kaava': molkaava}
    io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(d, ensure_ascii=False, indent=1) + '\n')
    p = os.path.join(SIM, 'kortit', 'molekyylit.json'); d = json.load(open(p, encoding='utf-8'))
    d[key] = {'nimi': nimi, 'kaava': kaava, 'kaavat': kaavat, 'sanat': sanat, 'kuva2d': '2d/%s.svg' % key}
    io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(d, ensure_ascii=False, indent=1) + '\n')
    print('  smiles.json + molekyylit.json: %s' % key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('key'); ap.add_argument('nimi'); ap.add_argument('cid', type=int, nargs='?')
    ap.add_argument('--smiles'); ap.add_argument('--kaava', help='lyhenne popupin otsikkoon, esim. G6P')
    ap.add_argument('--kaavat', nargs='*', default=[], help='tekstissa tunnistettavat kaavamuodot'); ap.add_argument('--sanat', nargs='*', default=[])
    a = ap.parse_args()
    m = rakenna_smiles(a.smiles) if a.smiles else hae_pubchem_3d(a.cid)
    tiedosto = a.key + '.mol2'
    io.open(os.path.join(SIM, tiedosto), 'w', encoding='utf-8', newline='\n').write(mol2(m, a.key, a.nimi))
    print('  %s: %d atomia (%d H), %d sidosta' % (tiedosto, m.GetNumAtoms(), sum(1 for x in m.GetAtoms() if x.GetSymbol() == 'H'), m.GetNumBonds()))
    kaava = a.kaava or a.key
    lisaa_simulaattoriin(a.key, a.nimi, tiedosto, kaava)
    smiles = Chem.MolToSmiles(Chem.RemoveHs(m)); molkaava = rdMolDescriptors.CalcMolFormula(m)
    lisaa_json(a.key, a.nimi, kaava, a.kaavat or [kaava], a.sanat or [a.nimi], smiles, molkaava)
    print('Seuraavaksi: python tyokalut/kaava2d.py && python tyokalut/kortti_build.py')


if __name__ == '__main__':
    main()
