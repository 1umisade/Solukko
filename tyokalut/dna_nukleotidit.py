# -*- coding: utf-8 -*-
"""Nukleotidit ketjun lenkkeina (Webcyte). Omistaja 11.9.2026: DNA ei saa olla jaykkia tankoja vaan jokainen
nukleotidi liikkuu omana lenkkinaan.

Lahde simulaatiot/DNA.mol2 (1D28, ChimeraX addh). Sovitetaan B-DNA:n ruuviaskel (yksi emaspari: kierto + nousu) kuten
dna_rakenna.py, ja maaritellaan emasparin i kehys: origo kierteen akselilla, z = akseli, x = suunta akselilta emasparin
1 C1'(A)-atomiin kierrettyna askelten mukana. Jokaisesta nukleotidityypista (DA, DT, DG, DC) otetaan yksi sisapuolen
nukleotidi kummastakin juosteesta ja sen atomit lausutaan OMAN emasparinsa kehyksessa -> 8 mallia
(nuk-A-DA ... nuk-B-DC), jotka simulaattori asettelee: lenkki (juoste s, emaspari i) = kehys_i * malli.
Tulos: simulaatiot/nukleotidit.mol2 (8 molekyylia) ja simulaatiot/nukleotidit.json (nousu, kierto asteina, merkki).
Aja: python tyokalut/dna_nukleotidit.py"""
import io, os, sys, math, json, collections
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
SC = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(SC)
SRC = os.path.join(REPO, 'simulaatiot', 'DNA.mol2')
OUT = os.path.join(REPO, 'simulaatiot', 'nukleotidit.mol2'); OUTJ = os.path.join(REPO, 'simulaatiot', 'nukleotidit.json')

sec = None; atoms = {}; bonds = []; subst = {}
for line in io.open(SRC, encoding='utf-8', errors='replace'):
    t = line.strip()
    if t.startswith('@<TRIPOS>'): sec = t; continue
    if not t: continue
    p = t.split()
    if sec == '@<TRIPOS>ATOM' and len(p) >= 8:
        atoms[int(p[0])] = dict(name=p[1], xyz=np.array([float(p[2]), float(p[3]), float(p[4])]), typ=p[5], sid=int(p[6]), res=p[7])
    elif sec == '@<TRIPOS>BOND' and len(p) >= 4: bonds.append((int(p[1]), int(p[2]), p[3]))
    elif sec == '@<TRIPOS>SUBSTRUCTURE' and len(p) >= 6: subst[int(p[0])] = dict(name=p[1], chain=p[5])
wet = {i for i, a in atoms.items() if a['res'].startswith('HOH')}
atoms = {i: a for i, a in atoms.items() if i not in wet}
bonds = [b for b in bonds if b[0] in atoms and b[1] in atoms]
chains = collections.defaultdict(list)
for sid, s in subst.items():
    if s['name'] != 'HOH': chains[s['chain']].append(sid)
for c in chains: chains[c].sort()
A, B = chains['A'], chains['B']; assert len(A) == len(B) == 12
by_sid = collections.defaultdict(dict)
for i, a in atoms.items(): by_sid[a['sid']][a['name']] = i
restype = {sid: subst[sid]['name'] for sid in subst}
bp = lambda i: (A[i-1], B[12-i])

def kabsch(P, Q):
    cp, cq = P.mean(0), Q.mean(0); H = (P - cp).T @ (Q - cq); U, S, Vt = np.linalg.svd(H); d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T; return R, cq - R @ cp
src, dst = [], []
for i in range(1, 12):
    for (sa, sb) in zip(bp(i), bp(i + 1)):
        for nm, ai in by_sid[sa].items():
            if nm in by_sid[sb] and (nm[0] in 'PO' or "'" in nm): src.append(atoms[ai]['xyz']); dst.append(atoms[by_sid[sb][nm]]['xyz'])
R1, t1 = kabsch(np.array(src), np.array(dst))
w, v = np.linalg.eig(R1); axis = np.real(v[:, np.argmin(abs(w - 1))]); axis /= np.linalg.norm(axis)
rise = float(t1 @ axis)
if rise < 0: axis, rise = -axis, -rise
# signed twist: rotate a perpendicular vector and see which way it turns about the axis
perp0 = np.cross(axis, [1, 0, 0]);
if np.linalg.norm(perp0) < 0.3: perp0 = np.cross(axis, [0, 1, 0])
perp0 /= np.linalg.norm(perp0); rot = R1 @ perp0
twist = math.degrees(math.atan2(np.dot(np.cross(perp0, rot), axis), np.dot(perp0, rot)))
p0 = np.linalg.lstsq(np.eye(3) - R1, t1 - rise * axis, rcond=None)[0]   # a point on the axis
print('askel: kierto %+.2f astetta, nousu %.3f Å' % (twist, rise))

# frame of base pair 1: origin = axis point nearest bp1's centroid, z = axis, x toward C1'(A1)
def cen(i): return np.mean([atoms[ai]['xyz'] for sid in bp(i) for ai in by_sid[sid].values()], 0)
c1 = cen(1); o1 = p0 + axis * float((c1 - p0) @ axis)
xref = atoms[by_sid[A[0]]["C1'"]]['xyz'] - o1; xref -= axis * float(xref @ axis); xref /= np.linalg.norm(xref)
yref = np.cross(axis, xref)
G = np.array([xref, yref, axis])   # rows: world -> frame-1 coordinates
# inverse screw i-1 times brings base pair i onto base pair 1
def to_frame(x, i):
    for _ in range(i - 1): x = R1.T @ (x - t1)
    return G @ (x - o1)

templates = {}   # (strand, type) -> list of (name, typ, local xyz, orig id)
for i in range(2, 12):          # interior base pairs only (full phosphates)
    for strand, sid in zip('AB', bp(i)):
        key = (strand, restype[sid])
        if key in templates: continue
        ids = sorted(by_sid[sid].values())
        templates[key] = [(atoms[ai]['name'], atoms[ai]['typ'], to_frame(atoms[ai]['xyz'], i), ai, atoms[ai]['res']) for ai in ids]
assert len(templates) == 8, sorted(templates)
out = []
for (strand, typ) in sorted(templates):
    T = templates[(strand, typ)]; loc = {ai: k + 1 for k, (_, _, _, ai, _) in enumerate(T)}
    sb = [(loc[a], loc[b], o) for a, b, o in bonds if a in loc and b in loc]
    out += ['@<TRIPOS>MOLECULE', 'nuk-%s-%s' % (strand, typ), '%d %d 1 0 0' % (len(T), len(sb)), 'SMALL', 'NO_CHARGES', '', '', '@<TRIPOS>ATOM']
    for k, (nm, ty, q, ai, res) in enumerate(T):
        out.append('%7d %-6s %10.4f %10.4f %10.4f %-6s %5d %-5s %8.4f' % (k + 1, nm, q[0], q[1], q[2], ty, 1, typ, 0.0))
    out.append('@<TRIPOS>BOND')
    for k, (a, b, o) in enumerate(sb): out.append('%6d %6d %6d %s' % (k + 1, a, b, o))
    r = max(np.linalg.norm(q) for _, _, q, _, _ in T)
    print('  %s-%s: %d atomia, sade akselilta enint. %.1f Å' % (strand, typ, len(T), r))
io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
json.dump({'rise': round(rise, 4), 'twistDeg': round(twist, 3), 'note': 'B-DNA 1D28: base pair i frame = frame 1 screwed i-1 times; templates nuk-<strand>-<type> live in that frame (origin on the helix axis)'}, io.open(OUTJ, 'w', encoding='utf-8', newline='\n'), indent=1)
print('kirjoitettu', os.path.relpath(OUT, REPO), 'ja', os.path.relpath(OUTJ, REPO))
