# -*- coding: utf-8 -*-
"""1000 emasparin B-DNA oikeista atomeista simulaattoriin (Webcyte, tuma).

Lahde: simulaatiot/DNA.mol2 - ChimeraX:sta viety 12 emasparin B-DNA (1D28, `addh`), vedyt ja sidoskertaluvut mukana.
1. Vesimolekyylit pois, nukleotidit ketjuittain (A 5'->3', B 5'->3'); emaspari i = (A_i, B_13-i).
2. Kierteen ruuviliike: Kabsch-sovitus emaspareista 1-2 emaspareihin 11-12 = siirto 10 emasparia (yksi kierros).
   Tarkistus: nousu noin 34 Å, kierto noin 360 astetta.
3. Yksikko = emasparit 1-10; ketju = yksikko ruuviliikkeella 100 kertaa, liitossidokset O3'-P yksikoiden valiin.
4. Ketju kaannetaan niin, etta kierteen akseli on +Z, ja pilkotaan 30 jaykkaan segmenttiin (n. 33 ep, 113 Å).
   Jokainen segmentti on oma molekyyli tiedostossa simulaatiot/DNA_1000.mol2 (nimet dna-seg-00 ... dna-seg-29);
   katselija lataa ne malleina (LoD: orbitaalit, vdW, halpa, laatta) ja asettelee ne koydeksi tumaan joka frame.
Aja: python tyokalut/dna_rakenna.py
"""
import io, os, sys, math, collections
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, 'simulaatiot', 'DNA.mol2'); OUT = os.path.join(REPO, 'simulaatiot', 'DNA_1000.mol2')
N_BP = 1000; N_SEG = 30; UNIT = 10

# ── 1. lue mol2 ─────────────────────────────────────────────────────────────────────────────────
sec = None; atoms = {}; bonds = []; subst = {}
for line in io.open(SRC, encoding='utf-8', errors='replace'):
    t = line.strip()
    if t.startswith('@<TRIPOS>'): sec = t; continue
    if not t: continue
    p = t.split()
    if sec == '@<TRIPOS>ATOM' and len(p) >= 8:
        atoms[int(p[0])] = dict(name=p[1], xyz=np.array([float(p[2]), float(p[3]), float(p[4])]), typ=p[5], sid=int(p[6]), res=p[7])
    elif sec == '@<TRIPOS>BOND' and len(p) >= 4:
        bonds.append((int(p[1]), int(p[2]), p[3]))
    elif sec == '@<TRIPOS>SUBSTRUCTURE' and len(p) >= 6:
        subst[int(p[0])] = dict(name=p[1], chain=p[5])
wet = {i for i, a in atoms.items() if a['res'].startswith('HOH')}
atoms = {i: a for i, a in atoms.items() if i not in wet}
bonds = [b for b in bonds if b[0] in atoms and b[1] in atoms]
chains = collections.defaultdict(list)
for sid, s in subst.items():
    if s['name'] == 'HOH': continue
    chains[s['chain']].append(sid)
for c in chains: chains[c].sort()
A, B = chains['A'], chains['B']
assert len(A) == len(B) == 12, (len(A), len(B))
by_sid = collections.defaultdict(dict)
for i, a in atoms.items(): by_sid[a['sid']][a['name']] = i
print('atomeja %d, sidoksia %d, ketjut A %d / B %d nukleotidia' % (len(atoms), len(bonds), len(A), len(B)))

def bp(i):          # emaspari i (1-12): (A_i, B_13-i)
    return A[i-1], B[12-i]

# ── 2. ruuviliike 10 emasparia eteenpain ───────────────────────────────────────────────────────
def kabsch(P, Q):   # R, t niin etta R P + t ~ Q
    cp, cq = P.mean(0), Q.mean(0)
    H = (P - cp).T @ (Q - cq); U, S, Vt = np.linalg.svd(H); d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d]); R = Vt.T @ D @ U.T
    return R, cq - R @ cp
# YKSI askel (bp i -> i+1) sovitetaan kaikista 11 askelparista yhtaaikaa: kahden emasparin lohkoista sovitettu 10 askeleen
# siirto oli huonosti ehdollistettu (kierto kaukaisen akselin ympari nayttaa samalta kuin siirto). Emastyypit vaihtuvat
# askeleesta toiseen, joten vain kaikille nukleotideille yhteiset selkarangan ja sokerin atomit (P, O5', C1' ...) verrataan.
src, dst = [], []
for i in range(1, 12):
    for (sa, sb) in zip(bp(i), bp(i + 1)):
        for nm, ai in by_sid[sa].items():
            if nm in by_sid[sb] and (nm[0] in 'PO' or "'" in nm): src.append(atoms[ai]['xyz']); dst.append(atoms[by_sid[sb][nm]]['xyz'])
src, dst = np.array(src), np.array(dst)
R1, t1 = kabsch(src, dst)
rms = math.sqrt(((src @ R1.T + t1 - dst) ** 2).sum(1).mean())
def cen(i):
    ids = [ai for sid in bp(i) for ai in by_sid[sid].values()]; return np.mean([atoms[ai]['xyz'] for ai in ids], 0)
print('|bp1->bp11| = %.1f Å, |bp1->bp2| = %.1f Å (%d verrattua atomia)' % (np.linalg.norm(cen(11) - cen(1)), np.linalg.norm(cen(2) - cen(1)), len(src)))
ang1 = math.degrees(math.acos(max(-1, min(1, (np.trace(R1) - 1) / 2))))
w, v = np.linalg.eig(R1); axis = np.real(v[:, np.argmin(abs(w - 1))]); axis /= np.linalg.norm(axis)
rise1 = float(t1 @ axis)
if rise1 < 0: axis = -axis; rise1 = -rise1
print('askel: kierto %.1f astetta/ep (B-DNA ~34-36), nousu %.2f Å/ep (~3.4), sovituksen rms %.2f Å' % (ang1, rise1, rms))
# 10 askelta = yksi yksikko
R, t = np.eye(3), np.zeros(3)
for _ in range(UNIT): R, t = R1 @ R, R1 @ t + t1
rise = float(t @ axis)
print('yksikko (10 ep): nousu %.1f Å' % rise)
# akselin piste: ratkaise (I - R) p = t - (t.axis) axis pienimman nelion mielessa
p0 = np.linalg.lstsq(np.eye(3) - R, t - rise * axis, rcond=None)[0]

# ── 3. yksikko (ep 1-10) ja ketju ──────────────────────────────────────────────────────────────
unit_sids = [A[r + 1] for r in range(UNIT)] + [B[10 - r] for r in range(UNIT)]   # A2..A11, B11..B2 (bp 2..11 - the 5' ends have no phosphate, so bp 1 and 12 are left out)
unit_atoms = [i for i in sorted(atoms) if atoms[i]['sid'] in set(unit_sids)]
uidx = {ai: k for k, ai in enumerate(unit_atoms)}
bp_of_sid = {}
for r in range(UNIT): bp_of_sid[A[r + 1]] = r; bp_of_sid[B[10 - r]] = r
unit_bonds = [(uidx[a], uidx[b], o) for a, b, o in bonds if a in uidx and b in uidx]
# liitokset seuraavaan yksikkoon: O3'(A10) -> P(A1'), P(B3) -> O3'(B12')
def find(sid, nm): return uidx[by_sid[sid][nm]]
junction = [(find(A[10], "O3'"), find(A[1], 'P'), 'A'), (find(B[1], 'P'), find(B[10], "O3'"), 'B')]   # (tama yksikko, seuraava yksikko): O3'(A11)->P(A2'), P(B2)->O3'(B11')
UX = np.array([atoms[i]['xyz'] for i in unit_atoms])
n_units = N_BP // UNIT
# kaanto: akseli -> +Z, akselipiste -> origo
def frame_to_z(ax):
    z = ax / np.linalg.norm(ax); h = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 1.0, 0])
    x = np.cross(h, z); x /= np.linalg.norm(x); y = np.cross(z, x); return np.array([x, y, z])   # rivit = uudet akselit
M = frame_to_z(axis)
X_all = []; bp_all = []
Rk = np.eye(3); tk = np.zeros(3)
for u in range(n_units):
    Xu = UX @ Rk.T + tk
    X_all.append((Xu - p0) @ M.T)
    bp_all.extend([u * UNIT + bp_of_sid[atoms[i]['sid']] for i in unit_atoms])
    Rk, tk = R @ Rk, R @ tk + t
X_all = np.vstack(X_all); bp_all = np.array(bp_all); nU = len(unit_atoms)
print('ketju: %d atomia, pituus z %.0f Å' % (len(X_all), X_all[:, 2].max() - X_all[:, 2].min()))
# kaikki sidokset globaalein indeksein
all_bonds = []
for u in range(n_units):
    o = u * nU
    for a, b, k in unit_bonds: all_bonds.append((o + a, o + b, k))
    if u + 1 < n_units:
        for a, b, ch in junction: all_bonds.append((o + a, o + nU + b, '1'))

# ── 4. segmentit ja tiedosto ───────────────────────────────────────────────────────────────────
seg_of_bp = lambda j: min(N_SEG - 1, j * N_SEG // N_BP)
seg_atoms = collections.defaultdict(list)
for g in range(len(X_all)): seg_atoms[seg_of_bp(bp_all[g])].append(g)
out = []
for s in range(N_SEG):
    ids = seg_atoms[s]; loc = {g: k + 1 for k, g in enumerate(ids)}
    sb = [(loc[a], loc[b], k) for a, b, k in all_bonds if a in loc and b in loc]
    nbp = len({bp_all[g] for g in ids})   # emasparien maara nimeen: katselija lukee sen (dna-seg-00-bp33) ja asettelee segmentin sen mukaan
    out.append('@<TRIPOS>MOLECULE'); out.append('dna-seg-%02d-bp%d' % (s, nbp)); out.append('%d %d 1 0 0' % (len(ids), len(sb)))
    out.append('BIOPOLYMER'); out.append('NO_CHARGES'); out.append(''); out.append(''); out.append('@<TRIPOS>ATOM')
    for k, g in enumerate(ids):
        a = atoms[unit_atoms[g % nU]]; x, y, z = X_all[g]
        out.append('%7d %-6s %10.4f %10.4f %10.4f %-6s %5d %-5s %8.4f' % (k + 1, a['name'], x, y, z, a['typ'], bp_all[g] + 1, a['res'][:2], 0.0))
    out.append('@<TRIPOS>BOND')
    for k, (a, b, o) in enumerate(sb): out.append('%6d %6d %6d %s' % (k + 1, a, b, o))
io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
sizes = [len(seg_atoms[s]) for s in range(N_SEG)]
print('kirjoitettu %s: %d segmenttia, %d-%d atomia kussakin, %.1f MB' % (os.path.relpath(OUT, REPO), N_SEG, min(sizes), max(sizes), os.path.getsize(OUT) / 1e6))
