# -*- coding: utf-8 -*-
"""Molekyylien 2D-kaavat popupin 2D-asentoon, sarjakuvatyylilla (omistajan mallikuva 10.9.2026):
punainen vdW-hehku mustalla aariviivalla koko molekyylin ympari, mustat sidokset, atomit varillisina
palloina (C harmaa, N sininen, O punainen, P oranssi, H vaaleanharmaa) kirjaimineen, kaikki vedyt nakyvissa.

Lahde: tyokalut/smiles.json (PubChem, IsomericSMILES). 2D-koordinaatit ja eksplisiittiset vedyt RDKitilla.
Tulos: simulaatiot/kortit/2d/<laji>.svg, lapinakyva tausta (popupin kortti on kermanvarinen).
Vaatii: pip install rdkit"""
import json, os, sys, math, io
sys.stdout.reconfigure(encoding='utf-8')
from rdkit import Chem
from rdkit.Chem import AllChem

SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
OUT = os.path.join(REPO, 'simulaatiot', 'kortit', '2d')

VARI = {'C': '#9d9d9d', 'H': '#c6c6c6', 'N': '#5a79d9', 'O': '#e5382d', 'P': '#f0932b', 'S': '#e3cf46', 'Mg': '#7fcf7f'}
SADE = {'H': 15}                 # muut 21 px, P/Mg 24
S = 42                           # px per RDKit-yksikko (sidos ~1.5 -> ~63 px)
HALO = 30                        # hehkun paksuus atomin/sidoksen ympari
ULKO = 5                         # hehkun mustan aariviivan paksuus
SIDOS = 6                        # sidosviivan paksuus
HEHKU = '#e8221c'


def lighten(hexc, f=0.45):
    r, g, b = int(hexc[1:3], 16), int(hexc[3:5], 16), int(hexc[5:7], 16)
    return '#%02x%02x%02x' % tuple(int(c + (255 - c) * f) for c in (r, g, b))


def mol2d(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None:   # esim. koordinoitunut Mg: osittainen sanitointi
        m = Chem.MolFromSmiles(smiles, sanitize=False); m.UpdatePropertyCache(strict=False)
        Chem.SanitizeMol(m, sanitizeOps=Chem.SanitizeFlags.SANITIZE_ALL ^ Chem.SanitizeFlags.SANITIZE_PROPERTIES ^ Chem.SanitizeFlags.SANITIZE_KEKULIZE, catchErrors=True)
    m = Chem.AddHs(m)
    try: Chem.Kekulize(m, clearAromaticFlags=True)
    except Exception: pass
    AllChem.Compute2DCoords(m)
    conf = m.GetConformer()
    atoms = []
    for a in m.GetAtoms():
        p = conf.GetAtomPosition(a.GetIdx())
        atoms.append({'sym': a.GetSymbol(), 'x': p.x * S, 'y': -p.y * S, 'q': a.GetFormalCharge()})
    bonds = [(b.GetBeginAtomIdx(), b.GetEndAtomIdx(), int(round(b.GetBondTypeAsDouble()))) for b in m.GetBonds()]
    rings = [list(r) for r in m.GetRingInfo().AtomRings()]   # renkaan sisus taytetaan hehkulla, muuten keskelle jaa reika
    return atoms, bonds, rings


def piirra(atoms, bonds, rings=(), lisa_merkki=None):
    r_of = lambda a: SADE.get(a['sym'], 24 if a['sym'] in ('P', 'Mg', 'S') else 21)
    xs = [a['x'] for a in atoms]; ys = [a['y'] for a in atoms]
    pad = HALO + max(r_of(a) for a in atoms) + ULKO + 8
    x0, y0 = min(xs) - pad, min(ys) - pad; W, H = max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.0f %.0f %.0f %.0f" width="%.0f" height="%.0f">' % (x0, y0, W, H, W, H), '<defs>']
    for sym, c in VARI.items():
        o.append('<radialGradient id="g%s" cx="40%%" cy="35%%" r="70%%"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient>' % (sym, lighten(c), c))
    o.append('<radialGradient id="gX" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#e0e0e0"/><stop offset="1" stop-color="#b0b0b0"/></radialGradient>')
    o.append('</defs>')
    # 1) hehku: ensin musta (aariviiva), sitten punainen paalle -> yhtenainen mollukka mustalla reunalla
    for vari, extra in ((('#111', ULKO)), (HEHKU, 0)):
        o.append('<g fill="%s" stroke="%s" stroke-linecap="round" stroke-linejoin="round">' % (vari, vari))
        for i, j, k in bonds:
            a, b = atoms[i], atoms[j]
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke-width="%.1f"/>' % (a['x'], a['y'], b['x'], b['y'], 2 * (HALO + extra)))
        for a in atoms:
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" stroke="none"/>' % (a['x'], a['y'], r_of(a) + HALO + extra))
        for ring in rings:
            o.append('<polygon points="%s" stroke-width="%.1f"/>' % (' '.join('%.1f,%.1f' % (atoms[i]['x'], atoms[i]['y']) for i in ring), 2 * (HALO + extra)))
        o.append('</g>')
    # 2) sidokset
    o.append('<g stroke="#111" stroke-width="%d" stroke-linecap="round">' % SIDOS)
    for i, j, k in bonds:
        a, b = atoms[i], atoms[j]
        dx, dy = b['x'] - a['x'], b['y'] - a['y']; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L * 7, dx / L * 7
        offs = {1: [0], 2: [-1, 1], 3: [-1, 0, 1]}.get(k, [0])
        for f in offs:
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (a['x'] + nx * f, a['y'] + ny * f, b['x'] + nx * f, b['y'] + ny * f))
    o.append('</g>')
    # 3) atomit
    for a in atoms:
        r = r_of(a); g = 'g' + a['sym'] if a['sym'] in VARI else 'gX'
        o.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="url(#%s)" stroke="#111" stroke-width="3"/>' % (a['x'], a['y'], r, g))
        fs = r * (1.15 if len(a['sym']) == 1 else 0.9)
        o.append('<text x="%.1f" y="%.1f" text-anchor="middle" dominant-baseline="central" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="%.0f" fill="#111">%s</text>' % (a['x'], a['y'] + fs * 0.04, fs, a['sym']))
        q = a.get('q', 0)
        if q:
            merkki = ('+' if q > 0 else '−') * min(abs(q), 1) if abs(q) == 1 else ('%d%s' % (abs(q), '+' if q > 0 else '−'))
            o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="%d" fill="#111">%s</text>' % (a['x'] + r * 0.95, a['y'] - r * 0.75, int(r * 0.9), merkki))
    if lisa_merkki: o.append(lisa_merkki)
    o.append('</svg>')
    return '\n'.join(o)


def main():
    lajit = json.load(open(os.path.join(SC, 'smiles.json'), encoding='utf-8'))
    os.makedirs(OUT, exist_ok=True)
    for key, d in lajit.items():
        atoms, bonds, rings = mol2d(d['smiles'])
        svg = piirra(atoms, bonds, rings)
        io.open(os.path.join(OUT, key + '.svg'), 'w', encoding='utf-8', newline='\n').write(svg)
        print('%-5s %3d atomia %3d sidosta -> %s.svg (%d kB)' % (key, len(atoms), len(bonds), key, len(svg) // 1024))
    # protoni: yksi vety plussalla
    a = [{'sym': 'H', 'x': 0, 'y': 0, 'q': 1}]
    io.open(os.path.join(OUT, 'Hplus.svg'), 'w', encoding='utf-8', newline='\n').write(piirra(a, []))
    print('Hplus -> Hplus.svg')
    # vanhat PubChem-PNG:t pois
    for f in os.listdir(OUT):
        if f.endswith('.png'): os.remove(os.path.join(OUT, f)); print('poistettu', f)


if __name__ == '__main__':
    main()
