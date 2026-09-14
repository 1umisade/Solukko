# -*- coding: utf-8 -*-
"""Kofaktorit simulaattorin korttijarjestelmaan (omistaja 14.9.2026: 'show the same kaava/muoto representation on these
molecule info cards as in solukko cards'). Webcyten kofaktorikortti (Kinoni, Hemi, Klorofylli...) nayttaa saman 2D-kaava /
elava 3D-malli -lohkon kuin Solukon kortit: kortit/2d/AVAIN.svg (kaava2d.py) ja kortti.html?tila=kortti&laji=AVAIN.

Kaksi reittia, molemmat samaan muotoon (AVAIN.mol2 + SMALL/NAME_FI/FORMULA + smiles.json + molekyylit.json):
  1) molekyylit SMILESista RDKitilla kuten ryhmat_3d.py (vedyt mukana). Porfyriinien metalli (Mg, Fe) ei ole PubChemin
     SMILESissa sidottu renkaaseen, joten se sidotaan renkaan neljaan typpeen ennen upotusta (porfyriini_metalli).
  2) metalliklusterit (Mn4CaO5, Fe4S4, Fe2S2) todellisista koordinaateista simulaattorin proteiinirakenteista
     (PSII.mol2, photosystem_I.mol2, cytochrome_b6f.mol2): niissa ei ole vetyja, joten rakenne on taydellinen sellaisenaan;
     sidokset etaisyydesta. Plastosyaniinin Cu on jo simulaattorin CU-atomilaji.
Idempotentti. Aja: python tyokalut/kofaktorit_3d.py && python tyokalut/kaava2d.py && python tyokalut/kortti_build.py"""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC); SIM = os.path.join(REPO, 'simulaatiot')
sys.path.insert(0, SC)
from molekyyli_3d import rakenna_smiles, mol2
from ryhmat_3d import lisaa_tauluun, taivuta
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, AllChem
from rdkit.Geometry import Point3D

# avain, nimi, SMILES (PubChem), otsikkokaava, rinnakkaisnimet, porfyriinin metalli. Plastokinoni (PQ) ja klorofylli a (CHL)
# ovat jo simulaattorin lajeja - kortti kayttaa niita.
MOLEKYYLIT = [
    ('FYLLOKINONI',    'fyllokinoni',    'CC1=C(C(=O)c2ccccc2C1=O)C/C=C(\\C)/CCC[C@H](C)CCC[C@H](C)CCCC(C)C', 'C₃₁H₄₆O₂', ['K-vitamiini'], None),
    ('FEOFYTIINI',     'feofytiini a',   'CCC1=C(C2=NC1=CC3=C(C4=C([C@@H](C(=C5[C@H]([C@@H](C(=CC6=NC(=C2)C(=C6C)C=C)N5)C)CCC(=O)OC/C=C(\\C)/CCC[C@H](C)CCC[C@H](C)CCCC(C)C)C4=N3)C(=O)OC)O)C)C',
     'C₅₅H₇₄N₄O₅', ['feofytiini'], None),
    ('HEMI',           'hemi b',         'CC1=C(C2=CC3=NC(=CC4=C(C(=C([N-]4)C=C5C(=C(C(=N5)C=C1[N-]2)C=C)C)C=C)C)C(=C3CCC(=O)O)C)CCC(=O)O',
     'C₃₄H₃₂FeN₄O₄', ['hemi', 'heemi'], 'Fe'),
    ('BEETAKAROTEENI', 'β-karoteeni',    'CC1=C(C(CCC1)(C)C)/C=C/C(=C/C=C/C(=C/C=C/C=C(/C=C/C=C(/C=C/C2=C(CCCC2(C)C)C)\\C)\\C)/C)/C',
     'C₄₀H₅₆', ['beetakaroteeni'], None),
]
# avain, nimi, otsikkokaava, lahderakenne, tahdenimi mol2:ssa, sidosraja (A) metalli-ligandi
KLUSTERIT = [
    ('OEC',   'Mn₄CaO₅-klusteri', 'Mn₄CaO₅', 'PSII.mol2',           'OEX', 3.0),
    ('FE4S4', 'Fe₄S₄-klusteri',   'Fe₄S₄',   'photosystem_I.mol2',  'SF',  2.7),
    ('FE2S2', 'Fe₂S₂-klusteri',   'Fe₂S₂',   'cytochrome_b6f.mol2', 'FES', 2.7),
]


def porfyriini_metalli(smi, sym):
    """Porfyriini metalleineen: metalli datiivisidoksin renkaan neljaan typpeen (typpien varaus pois), vedyt, ETKDG-upotus ja
    UFF-optimointi metallin kanssa - Mg-N / Fe-N noin 2.0-2.1 A kuten kiderakenteissa (vapaan emaksen upotus vaantyi)."""
    rw = Chem.RWMol(Chem.MolFromSmiles(smi))
    ns = [a.GetIdx() for a in rw.GetAtoms() if a.GetSymbol() == 'N' and a.IsInRing()]
    assert len(ns) == 4, ns
    mi = rw.AddAtom(Chem.Atom(sym))
    for i in ns: rw.GetAtomWithIdx(i).SetFormalCharge(0); rw.AddBond(i, mi, Chem.BondType.DATIVE)
    m = rw.GetMol(); Chem.SanitizeMol(m); m = Chem.AddHs(m)
    ps = AllChem.ETKDGv3(); ps.randomSeed = 7
    if AllChem.EmbedMolecule(m, ps) != 0: raise SystemExit('3D-upotus epaonnistui: ' + sym)
    AllChem.UFFOptimizeMolecule(m, maxIters=2000)
    return m


def lue_klusteri(polku, tahde):
    """Ensimmainen tahde-instanssi proteiinin mol2:sta: [(symboli, x, y, z)]."""
    s = io.open(polku, encoding='utf-8', errors='replace').read()
    i = s.index('@<TRIPOS>ATOM'); j = s.index('@<TRIPOS>BOND')
    atomit, sid = [], None
    for line in s[i:j].splitlines()[1:]:
        p = line.split()
        if len(p) < 8 or not p[7].startswith(tahde): continue
        if sid is None: sid = p[6]
        if p[6] != sid: break
        sym = p[5].split('.')[0]; sym = sym[0].upper() + sym[1:].lower()
        atomit.append((sym, float(p[2]), float(p[3]), float(p[4])))
    return atomit


def klusteri_mol(atomit, raja):
    rw = Chem.RWMol(); conf = Chem.Conformer(len(atomit))
    for k, (sym, x, y, z) in enumerate(atomit):
        a = Chem.Atom(sym); a.SetNoImplicit(True); rw.AddAtom(a); conf.SetAtomPosition(k, Point3D(x, y, z))
    for a in range(len(atomit)):
        for b in range(a + 1, len(atomit)):
            sa, sb = atomit[a][0], atomit[b][0]
            if (sa in ('Mn', 'Ca', 'Fe')) == (sb in ('Mn', 'Ca', 'Fe')): continue   # vain metalli-ligandi
            d = ((atomit[a][1] - atomit[b][1]) ** 2 + (atomit[a][2] - atomit[b][2]) ** 2 + (atomit[a][3] - atomit[b][3]) ** 2) ** 0.5
            if d <= raja: rw.AddBond(a, b, Chem.BondType.SINGLE)
    m = rw.GetMol(); m.AddConformer(conf, assignId=True); m.UpdatePropertyCache(strict=False)
    return m


def main():
    P = os.path.join(SIM, 'index.html'); s = io.open(P, encoding='utf-8', newline='').read()
    smiles = json.load(open(os.path.join(SC, 'smiles.json'), encoding='utf-8'))
    molj = json.load(open(os.path.join(SIM, 'kortit', 'molekyylit.json'), encoding='utf-8'))
    small, nimet, kaavat = [], [], []
    def kirjaa(key, nimi, tiedosto, kaava, smi, molkaava, sanat, metalli=None):
        small.append((key, ", ['%s','%s','%s']" % (key, nimi, tiedosto))); nimet.append((key, ", %s:'%s'" % (key, nimi))); kaavat.append((key, ", %s:'%s'" % (key, kaava)))
        if key not in smiles: smiles[key] = {'nimi': nimi, 'smiles': smi, 'kaava': molkaava}
        if metalli: smiles[key]['smiles'] = smi; smiles[key]['metalli'] = metalli   # kaava2d piirtaa metallin renkaan keskelle
        molj[key] = {'nimi': nimi, 'kaava': kaava, 'kaavat': [kaava], 'sanat': sanat, 'kuva2d': '2d/%s.svg' % key}
    for key, nimi, smi, kaava, rinnakkaiset, metalli in MOLEKYYLIT:
        tiedosto = key + '.mol2'; polku = os.path.join(SIM, tiedosto)
        if not os.path.exists(polku):
            m = porfyriini_metalli(smi, metalli) if metalli else rakenna_smiles(smi)
            io.open(polku, 'w', encoding='utf-8', newline='\n').write(mol2(m, key, nimi))
            print('  %-16s %3d atomia %3d sidosta -> %s' % (nimi, m.GetNumAtoms(), m.GetNumBonds(), tiedosto))
        mh = Chem.AddHs(Chem.MolFromSmiles(smi)); molkaava = rdMolDescriptors.CalcMolFormula(mh)
        if metalli: molkaava = re.sub(r'([-+]\d*)$', '', molkaava) + metalli   # vapaan emaksen kaava + metalli
        sanat = taivuta(nimi.split(' ')[0]) if ' ' in nimi else taivuta(nimi)   # 'klorofylli a' -> klorofylli-sanat
        for r in rinnakkaiset: sanat += taivuta(r)
        kirjaa(key, nimi, tiedosto, kaava, smi, molkaava, sanat, metalli)
    for key, nimi, kaava, lahde, tahde, raja in KLUSTERIT:
        tiedosto = key + '.mol2'; polku = os.path.join(SIM, tiedosto)
        atomit = lue_klusteri(os.path.join(SIM, lahde), tahde); m = klusteri_mol(atomit, raja)
        if not os.path.exists(polku):
            io.open(polku, 'w', encoding='utf-8', newline='\n').write(mol2(m, key, nimi))
            print('  %-16s %3d atomia %3d sidosta -> %s (%s / %s)' % (nimi, m.GetNumAtoms(), m.GetNumBonds(), tiedosto, lahde, tahde))
        kirjaa(key, nimi, tiedosto, kaava, Chem.MolToSmiles(m), rdMolDescriptors.CalcMolFormula(m), []); smiles[key]['mol2'] = tiedosto   # kaava2d: kaava kiderakenteesta
    s, a = lisaa_tauluun(s, 'const SMALL = [', small, '];', "['%s',")
    s, b = lisaa_tauluun(s, 'const NAME_FI = {', nimet, '};', " %s:'")
    s, c = lisaa_tauluun(s, 'const FORMULA = {', kaavat, '};', " %s:'")
    if a or b or c: io.open(P, 'w', encoding='utf-8', newline='').write(s); print('  simulaatiot/index.html: taulut paivitetty')
    else: print('  simulaatiot/index.html: kaikki lajit jo tauluissa')
    io.open(os.path.join(SC, 'smiles.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(smiles, ensure_ascii=False, indent=1) + '\n')
    io.open(os.path.join(SIM, 'kortit', 'molekyylit.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(molj, ensure_ascii=False, indent=1) + '\n')
    print('  smiles.json + molekyylit.json: %d kofaktoria' % (len(MOLEKYYLIT) + len(KLUSTERIT)))
    print('Seuraavaksi: python tyokalut/kaava2d.py && python tyokalut/kortti_build.py')


if __name__ == '__main__':
    main()
