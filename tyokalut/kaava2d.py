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
from rdkit.Chem import AllChem, rdDepictor

SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
OUT = os.path.join(REPO, 'simulaatiot', 'kortit', '2d')

VARI = {'C': '#9d9d9d', 'H': '#c6c6c6', 'N': '#5a79d9', 'O': '#e5382d', 'P': '#f0932b', 'S': '#e3cf46', 'Mg': '#7fcf7f'}
SADE = {'H': 15}                 # muut 21 px, P/Mg 24
S = 50                           # px per RDKit-yksikko (sidos ~1.5 -> ~75 px)
HALO = 30                        # hehkun paksuus atomin/sidoksen ympari
SILTA = 2.0 * 1.5 * S            # hehkusilta, kun sitoutumattomat atomit ovat alle 2 sidospituuden paassa
ULKO = 5                         # hehkun mustan aariviivan paksuus
SIDOS = 6                        # sidosviivan paksuus
HEHKU = '#e8221c'              # (ei enaa kaytossa: hehku on alkuaineen varinen, ks. piirra)


def lighten(hexc, f=0.45):
    r, g, b = int(hexc[1:3], 16), int(hexc[3:5], 16), int(hexc[5:7], 16)
    return '#%02x%02x%02x' % tuple(int(c + (255 - c) * f) for c in (r, g, b))


def sijoita_vedyt(m, pts):
    """Vedyt eivat saa osua toisiinsa, muihin atomeihin tai sidosviivoihin (omistaja 10.9.2026: 'prevent atom overlap').
    Jokainen vety kierretaan oman atominsa ympari (sidospituus sailyy) kulmaan, jossa lahin muu atomi tai sidos on
    kauimpana; pienena lisana pysytaan lahella RDKitin ehdottamaa kulmaa. Kolme kierrosta, koska vedyt vaikuttavat toisiinsa."""
    pts = list(pts)
    hs = [a.GetIdx() for a in m.GetAtoms() if a.GetSymbol() == 'H' and a.GetDegree() == 1]
    bonds = [(b.GetBeginAtomIdx(), b.GetEndAtomIdx()) for b in m.GetBonds()]

    def seg_d(p, a, b):
        ax, ay = a; bx, by = b; px, py = p; dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

    for _ in range(3):
        for h in hs:
            par = m.GetAtomWithIdx(h).GetNeighbors()[0].GetIdx()
            px, py = pts[par]; hx, hy = pts[h]
            L = math.hypot(hx - px, hy - py) or 1.0
            a0 = math.atan2(hy - py, hx - px)
            best, best_p = -1e9, (hx, hy)
            for k in range(72):
                ang = k * math.pi / 36
                cx, cy = px + L * math.cos(ang), py + L * math.sin(ang)
                d = min((math.hypot(cx - pts[j][0], cy - pts[j][1]) for j in range(len(pts)) if j != h and j != par), default=1e9)
                for i, j in bonds:
                    if h in (i, j): continue
                    d = min(d, seg_d((cx, cy), pts[i], pts[j]) + 0.15)   # a bond line counts almost like an atom
                diff = abs((ang - a0 + math.pi) % (2 * math.pi) - math.pi)
                score = min(d, 1.6) - 0.02 * diff   # beyond 1.6 units more room buys nothing: stay near the suggested angle
                if score > best: best, best_p = score, (cx, cy)
            pts[h] = best_p
    return pts


def mol2d(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None:   # esim. koordinoitunut Mg: osittainen sanitointi
        m = Chem.MolFromSmiles(smiles, sanitize=False); m.UpdatePropertyCache(strict=False)
        Chem.SanitizeMol(m, sanitizeOps=Chem.SanitizeFlags.SANITIZE_ALL ^ Chem.SanitizeFlags.SANITIZE_PROPERTIES ^ Chem.SanitizeFlags.SANITIZE_KEKULIZE, catchErrors=True)
    try: Chem.Kekulize(m, clearAromaticFlags=True)
    except Exception: pass
    # Runko ensin ilman vetyja (oppikirjan tikkukaavan asettelu, RDKitin oma - CoordGen vaanti renkaat), vedyt
    # lisataan valmiisiin koordinaatteihin. Kun vedyt olivat mukana asettelussa, ne veivat kulmatilaa ja runko
    # vaantyi (omistaja 10.9.2026: 'atoms too crowded').
    rdDepictor.SetPreferCoordGen(False)
    rdDepictor.Compute2DCoords(m)
    m = Chem.AddHs(m, addCoords=True)
    conf = m.GetConformer()
    pts = [(conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y) for i in range(m.GetNumAtoms())]
    pts = sijoita_vedyt(m, pts)
    # pitka akseli vaakaan (paakomponentti), fosfaatit vasemmalle kuten oppikirjassa (peilaus ei muuta tasokaavaa)
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - cx) ** 2 for p in pts); syy = sum((p[1] - cy) ** 2 for p in pts); sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts)
    th = 0.5 * math.atan2(2 * sxy, sxx - syy); c, s_ = math.cos(-th), math.sin(-th)
    pts = [((x - cx) * c - (y - cy) * s_, (x - cx) * s_ + (y - cy) * c) for x, y in pts]
    px = [pts[a.GetIdx()][0] for a in m.GetAtoms() if a.GetSymbol() == 'P']
    if px and sum(px) / len(px) > 0: pts = [(-x, y) for x, y in pts]
    atoms = []
    for a in m.GetAtoms():
        x, y = pts[a.GetIdx()]
        atoms.append({'sym': a.GetSymbol(), 'x': x * S, 'y': -y * S, 'q': a.GetFormalCharge()})
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
    # 1) hehku: ensin musta (aariviiva) yhtena mollukkana, sitten vdW-hehku paalle ATOMIN ALKUAINEEN VARISSA (omistaja
    #    12.9.2026: 'color the vdw in 2d as the color of the element'): jokaisen sidoksen ja sillan hehku on kaksi
    #    puolikasta, kumpikin oman paan atomin varissa, ja atomin oma ympyra sen varissa - vedyt vaaleanharmaita,
    #    happi punainen, typpi sininen. Vari on hehkusavy (vaalennettu), jotta mustat sidokset ja kirjaimet erottuvat.
    hehku = lambda a: lighten(VARI.get(a['sym'], '#b0b0b0'), 0.30)
    liukut = []   # sidoksen/sillan hehku liukuu a:n varista b:n variin (kaksi puolikasta jatti teravat saumat)
    def puolikkaat(a, b, extra):
        gid = 'l%d' % len(liukut)
        L = math.hypot(b['x'] - a['x'], b['y'] - a['y']) or 1.0   # a:n vari a:n oman hehkuympyran reunaan asti, siita liukuen b:n variin b:n reunalla
        oa = min(0.45, (r_of(a) + HALO) / L); ob = max(0.55, 1 - (r_of(b) + HALO) / L)
        liukut.append('<linearGradient id="%s" gradientUnits="userSpaceOnUse" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"><stop offset="%.2f" stop-color="%s"/><stop offset="%.2f" stop-color="%s"/></linearGradient>' % (gid, a['x'], a['y'], b['x'], b['y'], oa, hehku(a), ob, hehku(b)))
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="url(#%s)" stroke-width="%.1f" stroke-linecap="round"/>' % (a['x'], a['y'], b['x'], b['y'], gid, 2 * (HALO + extra)))
    o.append('<g fill="#111" stroke="#111" stroke-linecap="round" stroke-linejoin="round">')
    for i, j, k in bonds:
        a, b = atoms[i], atoms[j]
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke-width="%.1f"/>' % (a['x'], a['y'], b['x'], b['y'], 2 * (HALO + ULKO)))
    sillat = [(i, j) for i in range(len(atoms)) for j in range(i + 1, len(atoms)) if math.hypot(atoms[i]['x'] - atoms[j]['x'], atoms[i]['y'] - atoms[j]['y']) < SILTA]   # hehkusilta lahekkaisten sitoutumattomien atomien valiin: molekyylin sisaan ei jaa pikkureikia
    for i, j in sillat:
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke-width="%.1f"/>' % (atoms[i]['x'], atoms[i]['y'], atoms[j]['x'], atoms[j]['y'], 2 * (HALO + ULKO)))
    for a in atoms:
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" stroke="none"/>' % (a['x'], a['y'], r_of(a) + HALO + ULKO))
    for ring in rings:
        o.append('<polygon points="%s" stroke-width="%.1f"/>' % (' '.join('%.1f,%.1f' % (atoms[i]['x'], atoms[i]['y']) for i in ring), 2 * (HALO + ULKO)))
    o.append('</g>')
    o.append('<g stroke-linejoin="round">')
    for ring in rings:   # renkaan sisus: renkaan atomien keskivari
        cs = [VARI.get(atoms[i]['sym'], '#b0b0b0') for i in ring]
        r_, g_, b_ = (sum(int(c[k:k + 2], 16) for c in cs) // len(cs) for k in (1, 3, 5))
        o.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%.1f"/>' % (' '.join('%.1f,%.1f' % (atoms[i]['x'], atoms[i]['y']) for i in ring), lighten('#%02x%02x%02x' % (r_, g_, b_), 0.30), lighten('#%02x%02x%02x' % (r_, g_, b_), 0.30), 2 * HALO))
    for i, j in sillat: puolikkaat(atoms[i], atoms[j], 0)   # sillat alimmaksi: ne vain tayttavat reiat, sidosten hehku ja atomit paalle
    for i, j, k in bonds: puolikkaat(atoms[i], atoms[j], 0)
    for a in atoms:   # atomin oma hehku paallimmaiseksi, jotta sen vari voittaa naapurin sidospuolikkaan
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="none"/>' % (a['x'], a['y'], r_of(a) + HALO, hehku(a)))
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
    if liukut: o.insert(o.index('</defs>'), chr(10).join(liukut))   # sidoshehkujen liukuvarit defs-lohkoon
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
