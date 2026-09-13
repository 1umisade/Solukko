/* Kalvosto - the level (ProjectMPB's level_7.tscn + camera.gd + the spawn buttons, played on the Webcyte sheet).
   It builds every MoleculeBody3D from the real structures (the same geometry role-finder as before: P680, ChlD1, PheoD1, QA, Fe,
   the QB pocket, Rieske, hemes f/bL/bH/cn, Qo/Qi, Cu, P700, A0, FX/FA/FB, FAD ...), gives the complexes their BindSites and
   target points, wraps the sheet's own movers (the plastoquinone / plastocyanin shuttles, the loose-protein bouncers) as the
   carriers' kinematic bodies, spawns bodies for the things the sheet keeps elsewhere (a free water / NADP+ / ADP / Pi / CO2 / O2
   instance, a simulated proton, a photon beam) the moment they enter a slot's Nearby_area, and runs the clock, the sensors and
   the visuals (electron sprites, glows, aJ labels, the slot state in the cofactor overlay, the camera follow, the lantern).
   Everything the molecules DO is in valo/MoleculeBody3D.js and valo/scripts/. */
(function(){
  const V = window.VALO; const MB = V.MoleculeBody3D;
  /* a target node (target_1..5, Node, Node2): an Area2D in the 2D level whose body_entered clears the target of the body that reached it
     (target_1.gd: a plastocyanin's hard_target; target_3.gd: a proton's targets; target_4.gd: a proton's / oxygen's soft_target, a VDE is sent
     to PSII's VDE slot; target_5.gd: a ferredoxin's hard_target) */
  class Point { constructor(p, name){ this.alive = true; this._p = p; this.name = name || 'point'; this.radius = 12; this.parent_is_BindSites = false; }
    get global_position(){ return this._p.slice(); }
    when_body_enters_me(body){ const n = this.name;
      if(n === 'target_1' || n === 'target_2'){ if(body.is_in_group('plastocyanin')) body.hard_target = null; }
      else if(n === 'target_3'){ if(body.is_in_group('proton')){ body.hard_target = null; body.soft_target = null; body.reachedTarget3 = true; } }
      else if(n === 'target_4'){ if(body.is_in_group('proton') || body.is_in_group('O')) body.soft_target = null; if(body.is_in_group('VDE')){ const p = V.pick_random(V.get_nodes_in_group('photosystem_II')); body.soft_target = p ? p.get_node('BindSites/VDE') : null; } }
      else if(n === 'target_5'){ if(body.is_in_group('ferredoxin')) body.hard_target = null; } } }
  V.Point = Point;

  V.Kalvosto = { start(ctx){
    const { scene, engine, cam, mols: M, mInfo, etcGroups: G, modelOf, gModelXform, gModelOff, gHulls, gShuttles, gBouncers, insideShell, glassA, etcOverlay } = ctx;
    const get = ctx.get;   // live globals: gSpeed, gWaveT, gLantern, gBoxLo/Hi, gPsuLo/Hi, MEMBRANE_Y, gMemHalfT, gTasoZ, gProtonPasses, gValoFree, gValoProtons, gMolHold
    const labelOf = mi => (M[mi] && M[mi].cfg && M[mi].cfg.label) || '';
    const stats = { o2:0, nadph:0, atp:0, glukoosi:0, hplus:0, fotonit:0, lampo:0, vaurio:0, fnrE:0 };
    const wpt = (mi, p, out) => { const m=gModelXform, o=mi*16, x=p[0], y=p[1], z=p[2]; out[0]=m[o]*x+m[o+4]*y+m[o+8]*z+m[o+12]; out[1]=m[o+1]*x+m[o+5]*y+m[o+9]*z+m[o+13]; out[2]=m[o+2]*x+m[o+6]*y+m[o+10]*z+m[o+14]; return out; };
    const hullR = mi => { const h = gHulls.find(q => q.mi === mi); return h ? h.maxR : 30; };
    const d3 = (a, b) => Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]);
    const _a = [0,0,0], _b = [0,0,0], _c = [0,0,0];

    /* ── the roles, read off the structures ── */
    const grpModel = g => { let best = -1, bv = Infinity, bestAny = -1, bvAny = Infinity;
      for(let mi=0; mi<M.length; mi++){ const c = mInfo[mi]; if(!c || g.cx < c.x0 || g.cx > c.x1 || g.cy < c.y0 || g.cy > c.y1 || g.cz < c.z0 || g.cz > c.z1) continue;
        if(c.vol < bvAny){ bvAny = c.vol; bestAny = mi; } const m = M[mi]; if(m.shuttle || /^(chlorophyll|plastoquinone|nadph)$/i.test((m.cfg && m.cfg.match) || '')) continue; if(c.vol < bv){ bv = c.vol; best = mi; } }
      return best >= 0 ? best : (bestAny >= 0 ? bestAny : modelOf(g.cx, g.cy, g.cz)); };
    const grpMi = G.map(g => g.n ? grpModel(g) : -1);
    const cen = gi => [G[gi].cx, G[gi].cy, G[gi].cz];
    const ofType = (mi, t) => { const out = []; for(let gi=0; gi<G.length; gi++) if(G[gi].n && G[gi].type === t && grpMi[gi] === mi) out.push(gi); return out; };
    const nearest = (list, p, excl) => { let b=-1, bd=Infinity; for(const gi of list){ if(excl && excl.has(gi)) continue; const d=d3(cen(gi), p); if(d < bd){ bd=d; b=gi; } } return b; };
    const psii0 = M.findIndex(m => m.cfg && /photosystem ii/i.test(m.cfg.label || ''));
    const onSheet = mi => { if(psii0 < 0) return true; const a = mInfo[psii0], b = mInfo[mi]; if(!a || !b) return false; return Math.hypot(a.cx + gModelOff[psii0*3] - b.cx - gModelOff[mi*3], a.cy + gModelOff[psii0*3+1] - b.cy - gModelOff[mi*3+1], a.cz + gModelOff[psii0*3+2] - b.cz - gModelOff[mi*3+2]) < 2500; };   // this sheet only: the cell holds a second copy of the complexes thousands of units away
    const units = [];
    for(let mi=0; mi<M.length; mi++){ if(!/photosystem ii/i.test(labelOf(mi)) || !onSheet(mi)) continue;
      const oecG = ofType(mi, 1); if(!oecG.length) continue; const used = new Set(), mine = [];
      for(const g0 of oecG){ if(used.has(g0)) continue; const cl = [g0]; used.add(g0); for(const g of oecG){ if(!used.has(g) && d3(cen(g), cen(g0)) < 10){ cl.push(g); used.add(g); } }
        const c = [0,0,0]; for(const g of cl){ c[0] += G[g].cx/cl.length; c[1] += G[g].cy/cl.length; c[2] += G[g].cz/cl.length; } mine.push({ mi, oec: cl, oecC: c }); }
      const tyrs = ofType(mi, 9), pheos = ofType(mi, 2), quins = ofType(mi, 3), chls = ofType(mi, 7), cars = ofType(mi, 8), fes = ofType(mi, 5).filter(g => G[g].n <= 2);
      for(const u of mine){ u.tyrZ = nearest(tyrs, u.oecC); const tz = u.tyrZ >= 0 ? cen(u.tyrZ) : u.oecC; u.pheo = nearest(pheos, tz); const ph = u.pheo >= 0 ? cen(u.pheo) : tz; u.qa = nearest(quins, ph); const qa = u.qa >= 0 ? cen(u.qa) : ph;
        u.fe = nearest(fes, qa); if(u.fe >= 0 && d3(cen(u.fe), qa) > 12) u.fe = -1; const ex = new Set(); u.p680 = []; for(let k=0;k<2;k++){ const g = nearest(chls, tz, ex); if(g >= 0){ ex.add(g); u.p680.push(g); } }
        { const pts = [u.pheo, nearest(pheos, ph, new Set([u.pheo])), ...u.p680].filter(g => g >= 0).map(cen); const Mc = [0,0,0]; for(const c of pts){ Mc[0] += c[0]/pts.length; Mc[1] += c[1]/pts.length; Mc[2] += c[2]/pts.length; }
          const c2 = [2*Mc[0]-qa[0], qa[1], 2*Mc[2]-qa[2]]; let mir = c2; if(u.fe >= 0){ const fe = cen(u.fe), m2 = [2*fe[0]-qa[0], 2*fe[1]-qa[1], 2*fe[2]-qa[2]]; if(Math.abs(m2[1]-qa[1]) < 6) mir = m2; }
          const qb = nearest(quins, mir, new Set([u.qa])); u.qb = (qb >= 0 && d3(cen(qb), mir) < 10) ? qb : -1; u.qbSite = u.qb >= 0 ? cen(u.qb) : mir; }
        u.chlD1 = nearest(chls, ph, ex); if(u.chlD1 >= 0) ex.add(u.chlD1); u.rc = new Set([...u.p680, u.chlD1].filter(g => g >= 0)); u.ant = []; u.cars = []; }
      for(const g of chls){ if(mine.some(u => u.rc.has(g))) continue; let b=null, bd=Infinity; for(const u of mine){ const t = u.chlD1 >= 0 ? u.chlD1 : (u.p680[0] ?? -1); if(t < 0) continue; const d = d3(cen(g), cen(t)); if(d < bd){ bd=d; b=u; } } if(b) b.ant.push(g); }
      for(const g of cars){ let b=null, bd=Infinity; for(const u of mine){ const t = u.chlD1 >= 0 ? u.chlD1 : (u.p680[0] ?? -1); if(t < 0) continue; const d = d3(cen(g), cen(t)); if(d < bd){ bd=d; b=u; } } if(b) b.cars.push(g); }
      for(const u of mine) if(u.p680.length) units.push(u); }
    const b6fs = [];
    for(let mi=0; mi<M.length; mi++){ if(!/b6f/i.test(labelOf(mi)) || !onSheet(mi)) continue;
      const hemes = ofType(mi, 4), fes = ofType(mi, 5), quins = ofType(mi, 3); if(hemes.length < 2) continue;
      let cx=0, cz=0; for(const g of hemes){ cx += G[g].cx/hemes.length; cz += G[g].cz/hemes.length; } let sxx=0, sxz=0, szz=0; for(const g of hemes){ const dx=G[g].cx-cx, dz=G[g].cz-cz; sxx+=dx*dx; sxz+=dx*dz; szz+=dz*dz; }
      const ang = 0.5*Math.atan2(2*sxz, sxx-szz), ax = Math.cos(ang), az = Math.sin(ang); const side = g => ((G[g].cx-cx)*ax + (G[g].cz-cz)*az) >= 0 ? 1 : 0;
      const rec = { mi, monomers: [] };
      for(const sd of [0, 1]){ const hs = hemes.filter(g => side(g) === sd).sort((a, b) => G[a].cy - G[b].cy); if(hs.length < 2) continue;
        const u = { f: hs[0], bL: hs[1], bH: hs[Math.min(2, hs.length-1)], cn: hs[hs.length-1] }; u.rieske = nearest(fes, cen(u.f)); const qs = quins.filter(g => side(g) === sd);
        { const q = nearest(qs, cen(u.bL)); if(q >= 0 && d3(cen(q), cen(u.bL)) < 22) u.qoSite = cen(q); else { const a = cen(u.bL), b = u.rieske >= 0 ? cen(u.rieske) : cen(u.f); u.qoSite = [(a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2]; } }
        { const q = nearest(qs, cen(u.cn)); if(q >= 0 && d3(cen(q), cen(u.cn)) < 22 && d3(cen(q), u.qoSite) > 8) u.qiSite = cen(q); else { const a = cen(u.bH), b = cen(u.cn); u.qiSite = [b[0]+(b[0]-a[0])*0.6, b[1]+(b[1]-a[1])*0.6, b[2]+(b[2]-a[2])*0.6]; } }
        rec.monomers.push(u); }
      if(rec.monomers.length) b6fs.push(rec); }
    const psis = [];
    for(let mi=0; mi<M.length; mi++){ if(!/photosystem i$/i.test(labelOf(mi)) || !onSheet(mi)) continue;
      const quins = ofType(mi, 3), fes = ofType(mi, 5).filter(g => G[g].n >= 4), chls = ofType(mi, 7), cars = ofType(mi, 8); if(!chls.length) continue; const u = { mi, ant:[], cars };
      let qm = null; if(quins.length){ qm = [0,0,0]; for(const g of quins){ qm[0] += G[g].cx/quins.length; qm[1] += G[g].cy/quins.length; qm[2] += G[g].cz/quins.length; } }
      u.fx = qm ? nearest(fes, qm) : (fes.length ? fes.reduce((a, b) => G[a].cy < G[b].cy ? a : b) : -1); const exf = new Set([u.fx]); u.fa = u.fx >= 0 ? nearest(fes, cen(u.fx), exf) : -1; if(u.fa >= 0) exf.add(u.fa); u.fb = u.fa >= 0 ? nearest(fes, cen(u.fa), exf) : -1;
      let chlY = 0; for(const g of chls) chlY += G[g].cy/chls.length; const A = u.fx >= 0 ? cen(u.fx) : [mInfo[mi].cx, mInfo[mi].y1, mInfo[mi].cz], dirY = u.fx >= 0 ? Math.sign(chlY - A[1]) || -1 : -1;
      const B = qm || (u.fx >= 0 ? [A[0], A[1] + 45*dirY, A[2]] : [mInfo[mi].cx, mInfo[mi].y0, mInfo[mi].cz]); const ab = [B[0]-A[0], B[1]-A[1], B[2]-A[2]], L2 = ab[0]*ab[0]+ab[1]*ab[1]+ab[2]*ab[2] || 1;
      const par = chls.map(g => { const c = cen(g), t = ((c[0]-A[0])*ab[0]+(c[1]-A[1])*ab[1]+(c[2]-A[2])*ab[2])/L2; const px=A[0]+ab[0]*t, py=A[1]+ab[1]*t, pz=A[2]+ab[2]*t; return { g, t, r: Math.hypot(c[0]-px, c[1]-py, c[2]-pz) }; }).filter(o => o.r < 10 && o.t > (qm ? 0.8 : 0.25)).sort((a, b) => b.t - a.t);
      u.p700 = par.slice(0, 2).map(o => o.g); const rest = par.slice(2).sort((a, b) => a.t - b.t); u.a0 = rest.length ? rest[0].g : -1; if(!u.p700.length) u.p700 = [nearest(chls, B)];
      u.a1 = (u.a0 >= 0 && quins.length) ? nearest(quins, cen(u.a0)) : (quins.length ? quins[0] : -1); u.rc = new Set([...u.p700, u.a0].filter(g => g >= 0)); for(const g of chls) if(!u.rc.has(g)) u.ant.push(g);
      u.fdDir = [A[0]-B[0], A[1]-B[1], A[2]-B[2]]; psis.push(u); }
    const byLabel = re => { const out = []; for(let mi=0; mi<M.length; mi++) if(M[mi].cfg && !M[mi].shuttle && onSheet(mi) && re.test(labelOf(mi))) out.push(mi); return out; };
    const fdMis = byLabel(/ferredoxin/i), fnrMis = byLabel(/^FNR/i), ndhMis = byLabel(/NDH-1/i), atpMis = byLabel(/ATP synthase/i), rubMis = byLabel(/RuBisCO/i), vdeMis = byLabel(/violaxanthin de-epoxidase/i), zeMis = byLabel(/zeaxanthin epoxidase/i);
    if(!units.length && !psis.length){ console.warn('valoreaktiot: ei reaktiokeskuksia'); return null; }
    console.log('valoreaktiot (MoleculeBody3D): PSII ' + units.length + ', b6f ' + b6fs.length + ', PSI ' + psis.length + ', Fd ' + fdMis.length + ', FNR ' + fnrMis.length + ', NDH-1 ' + ndhMis.length + ', ATP-syntaasi ' + atpMis.length + ', RuBisCO ' + rubMis.length + ', VDE ' + vdeMis.length);

    /* ── the environment the base class asks for ── */
    V.env.frameWorld = wpt;
    V.env.membraneY = () => get.MEMBRANE_Y();

    /* ── building the scene: a body in a model's frame, a slot's position, a target point ── */
    const cofMols = new Map();   // etc group index -> body (the overlay paints these)
    const body = (name, mi, p, opts) => { const b = new MB(name, Object.assign({ frame: { mi, p } }, opts || {})); if(opts && opts.gi != null) cofMols.set(opts.gi, b); return b; };
    const cof = (gi, name, opts) => gi < 0 ? null : body(name, grpMi[gi], cen(gi), Object.assign({ gi }, opts || {}));
    const placeSlot = (parent, slotName, mi, p, lane) => { const s = parent.get_node('BindSites/' + slotName); if(!s) return null; s.frame = { mi, p }; if(lane !== undefined) setLane(s, lane); return s; };
    const setLane = (b, lane) => { b.lane = lane; if(b.BindSites) for(const s of b.BindSites) setLane(s, lane); };
    const point = (parent, name, mi, p) => { const pt = new Point([0,0,0], name); Object.defineProperty(pt, 'global_position', { get: () => wpt(mi, p, [0,0,0]) }); parent.namedChildren.set(name, pt); return pt; };
    const antenna = [];   // every pigment body (the excitation runs over these)
    /* PSII: OEC 2 -> Tyr Z 3 -> P680 4 -> ChlD1 5 -> PheoD1 6 -> QA 7 -> Fe 8 -> the QB pocket (lane p<k>): the 2D numbers, with the accessory chlorophyll and the non-heme iron as their own stops */
    units.forEach((u, k) => { const L = 'p' + k, mi = u.mi, c = mInfo[mi];
      u.psii = body('photosystem_II', mi, [c.cx, c.cy, c.cz], { lane: L, nearby: 90 }); u.psii.psId = L;
      placeSlot(u.psii, 'plastoquinone_B', mi, u.qbSite, L).place_in_the_chain = u.fe >= 0 ? 9 : 8;
      { const sx = u.oecC[0] >= c.cx ? 1 : -1; placeSlot(u.psii, 'VDE', mi, [c.cx + sx*(hullR(mi) + 26), u.oecC[1], c.cz], L); }   // beside the complex at the OEC's height (no room under it: PSII stands on the box floor)
      point(u.psii, 'target_4', mi, [u.oecC[0], u.oecC[1] - 45, u.oecC[2]]);   // where oxygen atoms and protons head after the OEC (the lumen)
      u.oecM = body('OEC', mi, u.oecC, { lane: L, nearby: 45 }); u.psii.namedChildren.set('OEC', u.oecM);
      u.tyrM = cof(u.tyrZ, 'tyrosine', { lane: L }); if(u.tyrM) u.psii.namedChildren.set('tyrosine', u.tyrM);
      u.p680M = cof(u.p680[0], 'P680', { lane: L }); u.p680M.psId = L; u.p680M.rcBody = u.p680M; u.psii.namedChildren.set('P680', u.p680M); antenna.push(u.p680M);
      if(u.p680[1] >= 0){ const m2 = cof(u.p680[1], 'chlorophyll_A', { lane: L }); m2.add_to_group('P680pair'); antenna.push(m2); }
      u.chlD1M = cof(u.chlD1, 'chlorophyll_A', { lane: L, BindSites: ['electron'], place: 5, nearby: 45 }); if(u.chlD1M){ u.chlD1M.ExcitedSprites = []; u.chlD1M.ExcitedSprite = null; }   // ChlD1: the accessory chlorophyll relays P680 -> PheoD1; not a pigment of the antenna here
      u.pheoM = cof(u.pheo, 'pheophytin', { lane: L, place: 6 }); u.qaM = cof(u.qa, 'plastoquinone_A', { lane: L, place: 7 }); u.feM = cof(u.fe, 'Fe3+', { lane: L, place: 8 });
      for(const g of u.ant){ const m = cof(g, 'chlorophyll_A', { lane: L }); antenna.push(m); }
      for(const g of u.cars){ const m = cof(g, 'xanthophyll', { lane: L }); antenna.push(m); }
      for(const m of antenna) if(m.lane === L){ m.psId = L; m.rcBody = u.p680M; }
      u.p680M.get_node('BindSites/electron').modulate = 'white';   // the centre starts reduced (it must hold an electron to be excited)
      orderAntenna(u.p680M, antenna.filter(m => m.psId === L && m !== u.p680M)); });
    /* b6f, per model with two monomers: the 2D scene's six BindSites (LUMENAL / STROMAL / plastocyanin x2). Qo 1 -> Rieske 2 -> f 3 -> the plastocyanin dock 4
       (arm b<m>.<k>.hi); bL 2 -> bH 3 -> cn 4 -> Qi 5 (arm b<m>.<k>.lo). A quinol docked at Qo hands one electron to each arm. */
    b6fs.forEach((rec, m) => { const mi = rec.mi, c = mInfo[mi];
      rec.b6f = body('cytochrome_b6f', mi, [c.cx, c.cy, c.cz], { nearby: 90 });
      rec.monomers.forEach((u, k) => { const L = 'b' + m + '.' + k, sfx = k ? '2' : '';
        placeSlot(rec.b6f, 'plastoquinone_B_LUMENAL' + sfx, mi, u.qoSite, L);
        placeSlot(rec.b6f, 'plastoquinone_B_STROMAL' + sfx, mi, u.qiSite, L + '.lo');
        { const f = cen(u.f); placeSlot(rec.b6f, 'plastocyanin' + sfx, mi, [f[0], f[1] - 34, f[2]], L + '.hi'); }   // the dock 34 under heme f (the shell march landed 200 units off; the mover lets a carrier into the complex it heads for)
        u.rieskeM = cof(u.rieske, 'iron_sulfur_cluster_inside_cytochrome_b6f', { lane: L + '.hi', place: 2 }); u.fM = cof(u.f, 'heme', { lane: L + '.hi', place: 3, nearby: 80 });   // heme f reaches the plastocyanin dock under the complex
        u.bLM = cof(u.bL, 'heme', { lane: L + '.lo', place: 2 }); u.bHM = cof(u.bH, 'heme', { lane: L + '.lo', place: 3 }); u.cnM = cof(u.cn, 'heme', { lane: L + '.lo', place: 4 });
        { const f = cen(u.f); point(rec.b6f, 'target_' + (k + 1), mi, [f[0], f[1] - 34 - 45, f[2]]); } });   // target_1 / target_2: where a released plastocyanin heads - under its dock, outside the hull (inside it the shell walled it off)
      point(rec.b6f, 'target_3', mi, [rec.monomers[0].qoSite[0], rec.monomers[0].qoSite[1] - 40, rec.monomers[0].qoSite[2]]); });   // target_3: protons leave the quinol into the lumen here
    /* PSI: the plastocyanin dock 13 -> P700 14 -> A0 15 -> (A1 16, none in 9E0J) -> FX -> FA -> FB -> the ferredoxin dock (lane psi<k>) */
    psis.forEach((u, k) => { const L = 'psi' + k, mi = u.mi, c = mInfo[mi];
      u.psi = body('photosystem_I', mi, [c.cx, c.cy, c.cz], { lane: L, nearby: 90 });
      placeSlot(u.psi, 'plastocyanin', mi, [c.cx, c.y0 - 14, c.cz], L).nearby_area.radius = 160;   // (the dock is under the complex, P700 well inside it)
      u.p700M = cof(u.p700[0], 'P700', { lane: L }); u.p700M.psId = L; u.p700M.rcBody = u.p700M; u.psi.namedChildren.set('P700', u.p700M); antenna.push(u.p700M);
      if(u.p700[1] >= 0){ const m2 = cof(u.p700[1], 'chlorophyll_A', { lane: L }); m2.add_to_group('P700pair'); antenna.push(m2); }
      u.a0M = cof(u.a0, 'chlorophyll_A_PSI', { lane: L, place: 15 }); u.a1M = cof(u.a1, 'phylloquinone', { lane: L, place: 16 });
      const fxP = u.a1M ? 17 : 16; u.fxM = cof(u.fx, 'iron_sulfur_cluster_inside_photosystem_I', { lane: L, place: fxP }); u.faM = cof(u.fa, 'iron_sulfur_cluster_inside_photosystem_I', { lane: L, place: fxP+1 }); u.fbM = cof(u.fb, 'iron_sulfur_cluster_inside_photosystem_I', { lane: L, place: fxP+2, nearby: 170 }); u.fdPlace = fxP + 3;   // FB's Nearby_area reaches the FNR sink on the FB face (145 measured)
      { const d = u.fdDir, l = Math.hypot(d[0], d[1], d[2]) || 1, fb = u.fb >= 0 ? cen(u.fb) : [c.cx, c.cy, c.cz]; u.fdSite = [fb[0] + d[0]/l*26, fb[1] + d[1]/l*26, fb[2] + d[2]/l*26]; const s = placeSlot(u.psi, 'ferredoxin', mi, u.fdSite, L); s.place_in_the_chain = u.fdPlace; }   // 26 past FB along the axis - inside the hull, as the 2D ferredoxin sat on FB
      point(u.psi, 'target_1', mi, [c.cx, c.y0 - 60, c.cz]);
      for(const g of u.ant){ const m = cof(g, 'chlorophyll_A', { lane: L }); antenna.push(m); } for(const g of u.cars){ const m = cof(g, 'xanthophyll', { lane: L }); antenna.push(m); }
      for(const m of antenna) if(m.lane === L){ m.psId = L; m.rcBody = u.p700M; }
      u.p700M.get_node('BindSites/electron').modulate = 'white';
      orderAntenna(u.p700M, antenna.filter(m => m.psId === L && m !== u.p700M)); });
    /* FNR: the sink (owner 13.9.2026). It stands against PSI's FB face (Node2), FB hands electrons straight to its 'electron' BindSite (one past FB, no lane - the
       ferredoxin dock is one before it), and FNR.js empties that slot the moment it fills. The NADP+ dock stays and shows the count. */
    const fnrs = fnrMis.map((mi, k) => { const c = mInfo[mi], fad = ofType(mi, 10), ps = psis[0], sinkPlace = ps ? ps.fdPlace : 21;
      const fnr = body('FNR', mi, [c.cx, c.cy, c.cz], { place: sinkPlace, nearby: 180 }); const fadC = fad.length ? cen(fad[0]) : [c.cx, c.cy, c.cz];
      placeSlot(fnr, 'electron', mi, fadC).place_in_the_chain = sinkPlace; fnr.get_node('BindSites/electron').nearby_area.radius = 45;
      placeSlot(fnr, 'ferredoxin', mi, [c.cx, c.cy + hullR(mi) + 16 + 2, c.cz]).place_in_the_chain = sinkPlace - 1;
      placeSlot(fnr, 'NADP', mi, [fadC[0] + 12, fadC[1] + 6, fadC[2]]).place_in_the_chain = sinkPlace + 1;
      const home = ps ? (() => { const d = ps.fdDir, l = Math.hypot(d[0], d[1], d[2]) || 1, R = hullR(ps.mi) + hullR(mi) - 6, cc = mInfo[ps.mi]; return wpt(ps.mi, [cc.cx + d[0]/l*R, cc.cy + d[1]/l*R, cc.cz + d[2]/l*R], [0,0,0]); })() : [c.cx + gModelOff[mi*3], c.cy + gModelOff[mi*3+1], get.gTasoZ()];
      home[2] = get.gTasoZ(); fnr.namedChildren.set('Node2', new Point(home, 'Node2')); return fnr; });
    /* NDH-1 (cyclic flow): the ferredoxin dock 1 -> its Fe-S clusters 2.. -> the plastoquinone dock last (lane ndh<k>) */
    const ndhs = ndhMis.map((mi, k) => { const L = 'ndh' + k, c = mInfo[mi], fes = ofType(mi, 5), quins = ofType(mi, 3);
      const ndh = body('NDH-1', mi, [c.cx, c.cy, c.cz], { lane: L, nearby: 90 }); const top = [c.cx, c.y1, c.cz];
      const chain = fes.slice().sort((a, b) => d3(cen(a), top) - d3(cen(b), top)).slice(0, 6); ndh.fes = chain.map((g, i) => cof(g, 'iron_sulfur_cluster_inside_photosystem_I', { lane: L, place: 2 + i }));
      const f0 = chain.length ? cen(chain[0]) : top; placeSlot(ndh, 'ferredoxin', mi, [f0[0], f0[1] + 26, f0[2]], L);
      let q = quins.length ? cen(quins[0]) : null; if(chain.length){ const l = cen(chain[chain.length-1]); if(!q || d3(q, l) > 50){ const f = cen(chain[0]), d = [l[0]-f[0], l[1]-f[1], l[2]-f[2]], n = Math.hypot(d[0], d[1], d[2]) || 1; q = [l[0] + d[0]/n*22, l[1] + d[1]/n*22, l[2] + d[2]/n*22]; } } if(!q) q = [c.cx, c.cy, c.cz];
      placeSlot(ndh, 'plastoquinone_B', mi, q, L).place_in_the_chain = 2 + chain.length;
      point(ndh, 'target_2', mi, [c.cx, c.y1 + 60, c.cz]); return ndh; });
    /* ATP synthase, RuBisCO */
    const atps = atpMis.map(mi => { const c = mInfo[mi]; const a = body('ATP-synthase', mi, [c.cx, c.cy, c.cz], { nearby: 90 }); placeSlot(a, 'ADP', mi, [c.cx - 8, c.y1 - 10, c.cz]); placeSlot(a, 'phosphate', mi, [c.cx + 8, c.y1 - 10, c.cz]); a.passes0 = null; return a; });
    const rubs = rubMis.map(mi => { const c = mInfo[mi], R = mInfo[mi].vol > 0 ? Math.cbrt(mInfo[mi].vol)*0.5 : 40; const r = body('RuBisCO', mi, [c.cx, c.cy, c.cz], { nearby: 90 });
      for(let i=0;i<3;i++){ const a = i/3*6.283; placeSlot(r, 'CO2_' + (i+1), mi, [c.cx + Math.cos(a)*R, c.cy + 6, c.cz + Math.sin(a)*R]); }
      for(let i=0;i<2;i++){ const a = (i+0.5)/2*6.283; placeSlot(r, 'NADP_' + (i+1), mi, [c.cx + Math.cos(a)*R*0.8, c.cy + 14, c.cz + Math.sin(a)*R*0.8]); }
      for(let i=0;i<3;i++){ const a = (i+0.5)/3*6.283; placeSlot(r, 'ATP_' + (i+1), mi, [c.cx + Math.cos(a)*R, c.cy - 8, c.cz + Math.sin(a)*R]); }
      r.namedChildren.set('Node', new Point([c.cx + gModelOff[mi*3], c.cy + gModelOff[mi*3+1], get.gTasoZ()], 'Node')); return r; });
    function orderAntenna(rc, list){   // the antenna's place_in_the_chain: (centre - 1 - hop depth) over the neighbour graph, so every pigment has a nearer neighbour in reach (2D: six pigments numbered by hand)
      const NB = 34, pos = new Map(); for(const m of [rc, ...list]) pos.set(m, m.global_position); for(const m of list) m.place_in_the_chain = -99;
      const q = [rc], depth = new Map([[rc, 0]]);
      while(q.length){ const a = q.shift(), pa = pos.get(a), da = depth.get(a); for(const b of list){ if(depth.has(b)) continue; const pb = pos.get(b); if(Math.hypot(pa[0]-pb[0], pa[1]-pb[1], pa[2]-pb[2]) > NB) continue; depth.set(b, da + 1); b.place_in_the_chain = rc.place_in_the_chain - (da + 1); b.antenna_place = b.place_in_the_chain; q.push(b); } } }
    { const moving = new Set([...gShuttles.map(sh => sh.mi), ...gBouncers.map(b => b.mi)]); const mark = b => { b.is_static = true; if(b.BindSites) for(const s of b.BindSites) mark(s); };
      for(const b of V.all) if(b.frame && !b.parent && !moving.has(b.frame.mi)) mark(b); }   // the sensors hash these once (a dragged model is picked up on the next refresh)
    /* ── the carriers: the shuttle models (plastoquinone_B, plastocyanin) and the loose bouncers (ferredoxin, VDE, zeaxanthin epoxidase, FNR, RuBisCO) ── */
    const kinOf = new Map();   // body -> { kind: 'sh' | 'bnc', sh | b }
    const carrierBody = (name, mi, kin) => { const b = new MB(name, { position: [0,0,0], radius: hullR(mi) }); b.kin = kin; b.mi = mi; kinOf.set(b, kin); kin.body = b; if(kin.sh) kin.sh.kin = kin; if(kin.b) kin.b.kin = kin; return b; };
    for(const sh of gShuttles){ carrierBody(sh.pq ? 'plastoquinone_B' : 'plastocyanin', sh.mi, { kind:'sh', sh }); sh.cur[2] = get.gTasoZ(); }
    for(const mi of fdMis){ const b = gBouncers.find(q => q.mi === mi); if(b) carrierBody('ferredoxin', mi, { kind:'bnc', b, side: 1 }); }
    for(const mi of vdeMis){ const b = gBouncers.find(q => q.mi === mi); if(b) carrierBody('VDE', mi, { kind:'bnc', b, side: -1 }); }
    for(const mi of zeMis){ const b = gBouncers.find(q => q.mi === mi); if(b) carrierBody('zeaxanthin_epoxidase', mi, { kind:'bnc', b, side: -1 }); }
    for(const b of gBouncers){ const f = fnrs.find(x => x.frame.mi === b.mi) || rubs.find(x => x.frame.mi === b.mi); if(f){ const kin = { kind:'bnc', b, home: true, body: f }; kinOf.set(f, kin); b.kin = kin; } }   // FNR / RuBisCO: their bouncer drifts to their soft target (a fixed node); the body itself stays a frame body (its slots turn with the model)
    /* the mover's view of a carrier (index.html's shuttle mover and bouncer loop read this): where to go, and where to be pinned */
    const carrierTarget = b => { const t = (b.hard_target && b.hard_target.alive) ? b.hard_target : b.soft_target; return (t && t.alive) ? t : null; };
    V.env.carrier = {
      target: kin => { const b = kin.body; if(!b || !b.alive) return null; const t = carrierTarget(b); return t ? t.global_position : null; },
      pinned: kin => { const b = kin.body; if(!b) return kin.dormantAt ? kin.dormantAt.global_position : null; if(!b.alive) return kin.dormantAt ? kin.dormantAt.global_position : null; if(!b.physics_processing) return b._pos; return null; },   // binding: the body glides, the model follows; dormant: parked in the slot
      hostMi: kin => { const b = kin.body; if(!b || !b.alive) return -1; const t = carrierTarget(b); return t && t.body_that_I_am_bound_to && t.body_that_I_am_bound_to.frame ? t.body_that_I_am_bound_to.frame.mi : -1; },   // the complex it heads for: its shell does not wall off its own pocket
      pulled: kin => !!(kin.body && kin.body.alive && kin.body.hard_target),
      homing: kin => !!kin.home };
    ctx.set.gValoShuttle({ target: sh => sh.kin ? V.env.carrier.target(sh.kin) : null, pinned: sh => sh.kin ? V.env.carrier.pinned(sh.kin) : null, hostMi: sh => sh.kin ? V.env.carrier.hostMi(sh.kin) : -1 });

    /* ── instantiate / dispose / consumed: what a body IS on the sheet ── */
    const eng = scene.getEngine();
    const eMat = new BABYLON.ShaderMaterial('valoElecMat', scene, 'bigelec', { attributes:['position','normal'], uniforms:['world','view','projection','uT'] });
    eMat.alphaMode = BABYLON.Constants.ALPHA_ADD; eMat.needAlphaBlending = () => true; eMat.disableDepthWrite = true; eMat.backFaceCulling = true; eMat.depthFunction = BABYLON.Engine.ALWAYS;
    eMat.onBindObservable.add(() => { const eff = eMat.getEffect(); if(eff) eff.setFloat('uT', get.gWaveT()); });
    const cMat = new BABYLON.ShaderMaterial('valoCoronaMat', scene, 'ecorona', { attributes:['position'], uniforms:['worldViewProjection','uT'] });
    cMat.alphaMode = BABYLON.Constants.ALPHA_ADD; cMat.needAlphaBlending = () => true; cMat.disableDepthWrite = true; cMat.backFaceCulling = false; cMat.depthFunction = BABYLON.Engine.ALWAYS;
    cMat.onBindObservable.add(() => { const eff = cMat.getEffect(); if(eff) eff.setFloat('uT', get.gWaveT()); });
    const onTop = m => { m.onBeforeRenderObservable.add(() => eng.setDepthFunction(BABYLON.Constants.ALWAYS)); m.onAfterRenderObservable.add(() => eng.setDepthFunction(BABYLON.Constants.LEQUAL)); };
    const sprites = []; for(let k=0;k<64;k++){ const mesh = BABYLON.MeshBuilder.CreateSphere('valoE'+k, { segments:12, diameter:4.6 }, scene); mesh.material = eMat; mesh.isPickable = false; mesh.alwaysSelectAsActiveMesh = true; mesh.renderingGroupId = 3; onTop(mesh);
      const corona = BABYLON.MeshBuilder.CreatePlane('valoEc'+k, { size:22 }, scene); corona.material = cMat; corona.isPickable = false; corona.alwaysSelectAsActiveMesh = true; corona.renderingGroupId = 3; corona.billboardMode = BABYLON.Mesh.BILLBOARDMODE_ALL; onTop(corona);
      mesh.setEnabled(false); corona.setEnabled(false); sprites.push({ mesh, corona, body: null }); }
    const oSprites = []; { const oMat = new BABYLON.StandardMaterial('valoOMat', scene); oMat.emissiveColor = new BABYLON.Color3(0.95, 0.25, 0.2); oMat.diffuseColor = new BABYLON.Color3(0.6, 0.1, 0.1); oMat.specularColor = BABYLON.Color3.Black();
      for(let k=0;k<12;k++){ const mesh = BABYLON.MeshBuilder.CreateSphere('valoO'+k, { segments:10, diameter:3.0 }, scene); mesh.material = oMat; mesh.isPickable = false; mesh.alwaysSelectAsActiveMesh = true; mesh.renderingGroupId = 1; mesh.setEnabled(false); oSprites.push({ mesh, body: null }); } }
    const FREE_KEY = { H2O:'w', O2:'o2', NADP:'nadp', ADP:'adp', ATP:'atp', phosphate:'pi', CO2:'co2' };
    const PARK = () => { const lo = get.gBoxLo(); return [lo.x - 150, lo.y - 400, lo.z - 150]; };
    const parkedP = [];   // simulated protons that ride inside a quinol / an NADPH (out of sight)
    V.env.instantiate = (name, opts) => { const at = opts.position || [0,0,0], slot = opts.from_slot;
      if(name === 'electron'){ const s = sprites.find(s => !s.body); if(!s) return null; const b = new MB('electron', { position: at }); b.kin = { kind:'sprite', s }; s.body = b; s.mesh.setEnabled(true); s.corona.setEnabled(true); return b; }
      if(name === 'O'){ const s = oSprites.find(s => !s.body); if(!s) return null; const b = new MB('O', { position: at }); b.kin = { kind:'sprite', s }; s.body = b; s.mesh.setEnabled(true); b.direction = V.normalize([Math.random()-0.5, -1, 0]); return b; }
      if(name === 'photon'){ const b = new MB('photon', { position: at }); b.kin = { kind:'static' }; b.set_physics_process(false); b.born = V.frame; return b; }
      if(name === 'proton'){ const P = get.gValoProtons(); if(!P) return null; let i = slot && slot._proton != null ? slot._proton : -1; if(slot) slot._proton = null;
        if(i < 0) i = parkedP.length ? parkedP.pop() : P.anyFree(0); if(i < 0) return null; P.grab(i); P.place(i, at[0], at[1], at[2]);
        const b = new MB('proton', { position: at }); b.kin = { kind:'proton', i }; b.born = V.time; return b; }
      if(FREE_KEY[name]){ const F = get.gValoFree(); if(!F) return null; const key = FREE_KEY[name]; let i = slot && slot._instance != null ? slot._instance : -1; if(slot) slot._instance = null;
        if(i < 0){ if(!F.count(key)) return null; i = F.nearest(key, at[0], at[1], at[2], 0); if(i < 0) return null; get.gMolHold()[F.base[key] + i] = 1; }
        F.setWorld(key, i, at[0], at[1], at[2]); const b = new MB(name, { position: at }); b.kin = { kind:'free', key, i }; return b; }
      if(['plastoquinone_B', 'plastocyanin', 'ferredoxin', 'VDE', 'zeaxanthin_epoxidase'].includes(name)){ const kin = slot && slot._dormant; if(!kin) return null; slot._dormant = null; kin.dormantAt = null;
        const b = new MB(name, { position: at, radius: hullR(kin.sh ? kin.sh.mi : kin.b.mi) }); b.kin = kin; b.mi = kin.sh ? kin.sh.mi : kin.b.mi; kin.body = b; kinOf.set(b, kin);
        if(kin.b){ const sp = V.Globals.get(name + '_speed') || 30; kin.b.vx = (Math.random()-0.5)*sp; kin.b.vy = (kin.side || 1)*sp*0.7; kin.b.vz = 0; } return b; }
      return null; };
    V.env.consumed = (b, BindSite) => { const kin = b.kin; if(!kin) return;
      if(kin.kind === 'sh' || kin.kind === 'bnc'){ BindSite._dormant = kin; kin.dormantAt = BindSite; kin.body = null; if(kin.b){ kin.b.vx = kin.b.vy = 0; kin.b.dockedAt = BindSite; } b.kin = null; }
      else if(kin.kind === 'free'){ BindSite._instance = kin.i; BindSite._key = kin.key; b.kin = null; }
      else if(kin.kind === 'proton'){ const P = get.gValoProtons(); const pk = PARK(); P.place(kin.i, pk[0] + Math.random()*40, pk[1], pk[2] + Math.random()*40); parkedP.push(kin.i); b.kin = null; } };
    V.env.dispose = b => { const kin = b.kin; if(!kin) return; b.kin = null;
      if(kin.kind === 'sprite'){ kin.s.body = null; kin.s.mesh.setEnabled(false); if(kin.s.corona) kin.s.corona.setEnabled(false); }
      else if(kin.kind === 'free'){ const F = get.gValoFree(); const p = b._pos; released.push({ key: kin.key, i: kin.i, x: p[0], y: p[1], z: p[2], vx: (Math.random()-0.5)*8, vy: 6, vz: (Math.random()-0.5)*8, t: 0, life: 20 }); }
      else if(kin.kind === 'proton'){ const P = get.gValoProtons(); const p = b._pos; const d = b.direction; P.release(kin.i, p[0], p[1], p[2], d[0]*9, d[1]*9, d[2]*9); }
      else if(kin.kind === 'sh' || kin.kind === 'bnc'){ kin.body = null; } };
    V.env.slotEmptied = BindSite => { if(BindSite._instance != null){ parkedF.push({ key: BindSite._key, i: BindSite._instance, t: 0 }); BindSite._instance = null; } if(BindSite._proton != null){ parkedP.push(BindSite._proton); BindSite._proton = null; } };
    const released = [], parkedF = [];

    /* ── the cosmetics the base class calls ── */
    const mkGlow = (name, col, alpha, cap) => { const m = BABYLON.MeshBuilder.CreateSphere(name, { diameter:1, segments:10 }, scene);
      const mat = new BABYLON.StandardMaterial(name+'Mat', scene); mat.emissiveColor = new BABYLON.Color3(col[0], col[1], col[2]); mat.disableLighting = true; mat.alpha = alpha; mat.alphaMode = BABYLON.Constants.ALPHA_ADD; mat.disableDepthWrite = true; mat.depthFunction = BABYLON.Engine.ALWAYS;
      m.material = mat; m.isPickable = false; m.alwaysSelectAsActiveMesh = true; m.renderingGroupId = 3; const buf = new Float32Array(cap*16); m.thinInstanceSetBuffer('matrix', buf, 16, false); m.thinInstanceCount = 0; m.setEnabled(false); return { m, buf, cap }; };
    const eks = mkGlow('valoEks', [0.55, 1.0, 0.30], 0.28, 64), heat = mkGlow('valoHeat', [1.0, 0.42, 0.18], 0.4, 24), flashG = mkGlow('valoFlash', [1.0, 1.0, 0.90], 0.35, 16), ringG = mkGlow('valoRing', [0.5, 0.8, 1.0], 0.25, 16);
    const putGlow = (g, n, r, x, y, z) => { const B = g.buf, m = n*16; B[m]=r; B[m+1]=0; B[m+2]=0; B[m+3]=0; B[m+4]=0; B[m+5]=r; B[m+6]=0; B[m+7]=0; B[m+8]=0; B[m+9]=0; B[m+10]=r; B[m+11]=0; B[m+12]=x; B[m+13]=y; B[m+14]=z; B[m+15]=1; };
    const showGlow = (g, n) => { if(n) g.m.thinInstancePartialBufferUpdate('matrix', g.buf.subarray(0, n*16), 0); g.m.thinInstanceCount = n; g.m.setEnabled(n > 0); };
    const heats = [], flashes = [], rings = [];
    V.env.heat = b => { const p = b.global_position; heats.push({ x:p[0], y:p[1], z:p[2], t:0 }); if(heats.length > heat.cap) heats.shift(); stats.lampo++; };
    V.env.shockWave = b => { const p = b.global_position; rings.push({ x:p[0], y:p[1], z:p[2], t:0 }); if(rings.length > ringG.cap) rings.shift(); };
    const flashAt = p => { flashes.push({ x:p[0], y:p[1], z:p[2], t:0 }); if(flashes.length > flashG.cap) flashes.shift(); };
    V.env.wobble = () => {}; V.env.xanthophyllChanged = () => {}; V.env.vdeDocked = () => {}; V.env.damaged = () => { stats.vaurio++; };
    V.env.sink = (fnr, BindSite) => { stats.fnrE++; if(stats.fnrE % 2 === 0) stats.nadph++; flashAt(BindSite.global_position); };
    V.env.nadphMade = () => {}; V.env.atpMade = a => { stats.atp++; flashAt(a.global_position); }; V.env.glucoseMade = r => { stats.glukoosi++; flashAt(r.global_position); };
    V.env.followLost = () => { if(followOn){ followArm = true; } };

    /* ── the camera follow (camera.gd: the body in the 'followed' group) ── */
    let followOn = false, followArm = false;
    window.gValoFollow = on => { followOn = !!on; if(!on) for(const b of V.get_nodes_in_group('followed')) b.remove_from_group('followed'); };
    window.gValoFollowArm = () => { followOn = true; followArm = true; };

    /* ── the aJ labels (update_label of P680.gd / chlorophyll_A.gd / electron.gd / photon.gd) ── */
    const LBL_N = 16, labels = [];
    for(let k=0;k<LBL_N;k++){ const tex = new BABYLON.DynamicTexture('valoLbl'+k, { width:160, height:44 }, scene, false); tex.hasAlpha = true;
      const mat = new BABYLON.StandardMaterial('valoLblMat'+k, scene); mat.diffuseTexture = tex; mat.emissiveColor = BABYLON.Color3.White(); mat.disableLighting = true; mat.useAlphaFromDiffuseTexture = true; mat.backFaceCulling = false; mat.disableDepthWrite = true; mat.depthFunction = BABYLON.Engine.ALWAYS;
      const pl = BABYLON.MeshBuilder.CreatePlane('valoLblP'+k, { width:18, height:5 }, scene); pl.material = mat; pl.billboardMode = BABYLON.Mesh.BILLBOARDMODE_ALL; pl.isPickable = false; pl.alwaysSelectAsActiveMesh = true; pl.renderingGroupId = 3; onTop(pl); pl.setEnabled(false); labels.push({ tex, pl, txt:'' }); }
    const fmtE = e => e.toFixed(2).replace('.', ',') + ' αJ';
    const setLabel = (L, txt, p) => { if(L.txt !== txt){ L.txt = txt; L.tex.clear(); L.tex.drawText(txt, null, null, 'bold 30px Courier New', '#f4ecd2', 'transparent', true); } L.pl.position.set(p[0], p[1] + 3.5, p[2]); L.pl.setEnabled(true); };
    const tickLabels = () => { const cp = cam.position, cand = [];
      for(const m of antenna){ if(!m.alive || !m.ExcitedSprite || !m.ExcitedSprite.visible || m.EnergyLevel <= 0) continue; const p = m.global_position; cand.push({ d: (cp.x-p[0])**2+(cp.y-p[1])**2+(cp.z-p[2])**2, e: m.EnergyLevel, p }); }
      for(const b of V.get_nodes_in_group('electron')){ if(b.parent_is_BindSites || b.EnergyLevel <= 0 || !b.kin) continue; const p = b.global_position; cand.push({ d: (cp.x-p[0])**2+(cp.y-p[1])**2+(cp.z-p[2])**2, e: b.EnergyLevel, p }); }
      cand.sort((a, b) => a.d - b.d); let n = 0; for(const c of cand){ if(n >= LBL_N || c.d > 250*250) break; setLabel(labels[n++], fmtE(c.e), c.p); } for(let k=n;k<LBL_N;k++) labels[k].pl.setEnabled(false); };

    /* ── the cofactor overlay shows the slot state (the 2D modulate): an empty electron carrier is dim, a filled one full colour, an excited pigment bright ── */
    const SLOT_W = Math.max(1, G.length), slotData = new Uint8Array(SLOT_W); slotData.fill(128); let slotDirty = true;
    const slotTex = new BABYLON.RawTexture(slotData, SLOT_W, 1, BABYLON.Constants.TEXTUREFORMAT_R, scene, false, false, BABYLON.Texture.NEAREST_SAMPLINGMODE, BABYLON.Constants.TEXTURETYPE_UNSIGNED_BYTE);
    const setSlotK = (gi, v) => { if(gi < 0 || gi >= SLOT_W) return; const b = Math.max(0, Math.min(255, Math.round(v*128))); if(slotData[gi] !== b){ slotData[gi] = b; slotDirty = true; } };
    if(etcOverlay){ const A = glassA(etcOverlay); A.setTexture('slotTex', slotTex); A.setFloat('slotN', SLOT_W); }

    /* ── the photons (photon.gd + the sheet's beam pool): a beam absorbed by pigment group gi becomes a photon body touching that pigment for a frame ── */
    ctx.set.gValoExcite((gi, x, y, z) => { const m = cofMols.get(gi); if(!m || !m.alive || !antenna.includes(m)) return false; stats.fotonit++;
      const ph = V.instantiate('photon', { position: m.global_position }); if(!ph) return false; if(followArm && followOn && !V.get_nodes_in_group('followed').length){ ph.add_to_group('followed'); followArm = false; }
      ph.touch_area._dyn.add(m); m.touch_area._dyn.add(ph); m.when_body_enters_touch_area(ph); return true; });

    /* ── the spawners: a simulated proton / a free instance inside a dark slot's Nearby_area becomes a body (the 2D level had them as bodies from the start) ── */
    const spawnT = new Map();
    const tickSpawners = dt => { const P = get.gValoProtons(), F = get.gValoFree(); if(!P || !F) return;
      for(const s of V.all){ if(!s.alive || !s.parent_is_BindSites || s.modulate !== 'dark' || !s.nearby_area || !s.nearby_area.enabled) continue;
        const nm = s.molecule_name; if(nm !== 'proton' && !FREE_KEY[nm]) continue; if(nm === 'O2') continue;   // (tyrosine takes only an EXCITED O2: those come from around P680, see below)
        const host = s.body_that_I_am_bound_to; if(!host || host.modulate !== 'white') continue; if(host.parent_is_BindSites && !host.body_that_I_am_bound_to) continue;
        if(nm === 'proton' && host.molecule_name === 'plastoquinone_B' && host.body_that_I_am_bound_to == null) continue;   // only a docked quinone takes protons
        if(s.pulled_bodies.some(b => b.alive)) continue; if(s.nearby_area.get_overlapping_bodies().some(b => b.molecule_name === nm && !b.parent_is_BindSites)) continue;   // one such body already in the area (a slot of that type does not count)
        const t = (spawnT.get(s) || 0) + dt; if(t < 0.5){ spawnT.set(s, t); continue; } spawnT.set(s, 0);
        const p = s.global_position;
        if(nm === 'proton'){ const side = p[1] > get.MEMBRANE_Y() ? 1 : -1; let i = P.nearestFree(p[0], p[1], p[2], side, s.nearby_area.radius), at;
          if(i >= 0){ const o = i*3; at = [P.pos[o], P.pos[o+1], P.pos[o+2]]; } else { i = parkedP.length ? parkedP.pop() : P.anyFree(side); if(i < 0) continue; at = [p[0] + (Math.random()-0.5)*60, p[1] + side*40, p[2]]; }   // none in reach: one from far away appears at the edge of the area (the free protons keep clear of the complexes)
          P.grab(i); P.place(i, at[0], at[1], at[2]); const b = new MB('proton', { position: at }); b.kin = { kind:'proton', i }; b.born = V.time; }
        else { const key = FREE_KEY[nm]; if(!F.count(key)) continue; const i = F.nearest(key, p[0], p[1], p[2], 0); if(i < 0) continue; F.pos(key, i, _b); if(d3(p, _b) > Math.max(s.nearby_area.radius, 700)) continue;   // (the free pools keep clear of the complexes; the nearest free water can be 300-600 away)
          if(nm === 'NADP' && host.molecule_name === 'RuBisCO'){ if(!nadphReady.includes(i)) continue; }   // RuBisCO takes only a reduced NADP (one that left FNR)
          get.gMolHold()[F.base[key] + i] = 1; const b = new MB(nm, { position: [_b[0], _b[1], _b[2]] }); b.kin = { kind:'free', key, i }; if(nm === 'NADP' && nadphReady.includes(i)){ slotOf(b, 'electron').modulate = 'white'; slotOf(b, 'electron_2').modulate = 'white'; nadphReady.splice(nadphReady.indexOf(i), 1); } } }
      // singlet oxygen: while a P680 is excited, one free O2 body drifts by it (the 2D scene had free O2 bodies around the photosystem); an O2 body that never got excited goes back to the pool after 20 s
      for(const u of units){ const rc = u.p680M; if(!rc.ExcitedSprite.visible) continue; const near = V.get_nodes_in_group('O2').filter(b => !b.parent_is_BindSites && b.kin && rc.distance_to(b) < 60); if(near.length) continue;
        const t = (spawnT.get(rc) || 0) + dt; if(t < 1.0){ spawnT.set(rc, t); continue; } spawnT.set(rc, 0); const p = rc.global_position; const i = F.nearest('o2', p[0], p[1], p[2], 0); if(i < 0) continue;
        const a = Math.random()*6.283, at = [p[0] + Math.cos(a)*16, p[1] - 6, p[2] + Math.sin(a)*16]; get.gMolHold()[F.base.o2 + i] = 1; F.setWorld('o2', i, at[0], at[1], at[2]); const b = new MB('O2', { position: at }); b.kin = { kind:'free', key:'o2', i }; b.born = V.time; }
      for(const b of V.get_nodes_in_group('O2')){ if(b.parent_is_BindSites || !b.kin || b.hard_target || b.get_meta('binding_ongoing', false)) continue; if(!(b.ExcitedSprite && b.ExcitedSprite.visible) && V.time - (b.born || 0) > 20) b.queue_free(); } };
    const slotOf = (b, n) => b.get_node('BindSites/' + n);
    const nadphReady = [];   // free NADP+ instances that left FNR reduced (the pool has one species: this list says which are NADPH)
    V.env.nadphMade = b => { if(b.kin && b.kin.kind === 'free') nadphReady.push(b.kin.i); };

    /* ── moving the sprite / instance / proton bodies (move_and_collide: the box walls and the lipid layer bounce them back) ── */
    V.env.move = (b, dx, dy, dz) => { const kin = b.kin; if(!kin) return null; if(kin.kind === 'sh' || kin.kind === 'bnc' || kin.kind === 'static') return null;
      const p = b._pos; p[0] += dx; p[1] += dy; p[2] += dz; let n = null;
      if(b.molecule_name === 'O' || b.molecule_name === 'O2' || b.molecule_name === 'proton' || kin.kind === 'free'){ const lo = get.gPsuLo() || get.gBoxLo(), hi = get.gPsuHi() || get.gBoxHi();
        if(lo){ if(p[0] < lo.x){ p[0] = lo.x; n = [1,0,0]; } if(p[0] > hi.x){ p[0] = hi.x; n = [-1,0,0]; } if(p[1] < lo.y){ p[1] = lo.y; n = [0,1,0]; } if(p[1] > hi.y){ p[1] = hi.y; n = [0,-1,0]; } }
        if(b.molecule_name === 'O' || b.molecule_name === 'O2'){ const top = get.MEMBRANE_Y() - get.gMemHalfT() - 2; if(p[1] > top){ p[1] = top; n = [0,-1,0]; } p[2] = get.gTasoZ(); } }
      if(kin.kind === 'free') get.gValoFree().setWorld(kin.key, kin.i, p[0], p[1], p[2]);
      if(kin.kind === 'proton') get.gValoProtons().place(kin.i, p[0], p[1], p[2]);
      return n ? { normal: n, collider: null } : null; };

    /* ── per frame: the clock, the sensors, physics, the bodies the sheet holds, the visuals ── */
    let valoRow = null, dev = 0, wasDragging = false; const prof = { all: 0, sens: 0 };
    scene.onBeforeRenderObservable.add(() => {
      { const ov = document.getElementById('overlay'); if(ov && !ov.classList.contains('gone')) return; }
      const dt = Math.min(engine.getDeltaTime(), 50)*0.001*get.gSpeed(); if(dt <= 0) return; V.dt = dt; const t0 = performance.now();
      // the carriers' bodies read their models' positions (the movers ran first this frame)
      for(const [b, kin] of kinOf){ if(!b.alive || !b.physics_processing) continue; if(kin.kind === 'sh'){ b._pos[0] = kin.sh.cur[0]; b._pos[1] = kin.sh.cur[1]; b._pos[2] = kin.sh.cur[2]; } else if(kin.kind === 'bnc' && !kin.home){ const mi = kin.b.mi, c = mInfo[mi]; b._pos[0] = c.cx + gModelOff[mi*3]; b._pos[1] = c.cy + gModelOff[mi*3+1]; b._pos[2] = c.cz + gModelOff[mi*3+2]; } }
      if(get.gizmoDragging && get.gizmoDragging()) wasDragging = true; else if(wasDragging){ wasDragging = false; V.Sensors.staticDirty = true; }   // a dragged model: the static hash is stale
      V.tick(dt); V.Sensors.update(dt); prof.sens = performance.now() - t0;
      tickSpawners(dt);
      for(const b of V.all){ if(!b.alive || !b.kin) continue; for(const t of [b.hard_target, b.soft_target]){ if(t instanceof Point && b.distance_to(t) <= t.radius + b.body_radius) t.when_body_enters_me(b); } }   // the target areas fire
      for(const b of V.all.slice()){ if(!b.alive) continue;
        if(b.kin && b.kin.kind === 'static' && V.frame - b.born > 2){ b.queue_free(); continue; }   // a photon nobody took (the pigment was busy): gone as heat
        if(b.kin && b.kin.kind === 'proton' && b.reachedTarget3){ b.queue_free(); stats.hplus++; continue; }   // a proton at target_3 (the lumen under b6f): back into the simulated pool
        if(b.kin && b.kin.kind === 'proton' && !b.hard_target && !b.get_meta('binding_ongoing', false)){ const age = V.time - b.born; if((age > 1.5 && (!b.soft_target || !(b.soft_target instanceof MB))) || age > 20){ b.queue_free(); continue; } }   // a proton nobody pulled goes back to the simulated pool (the OEC's after its second of drift, a wanderer after 20 s)
        if(!b.physics_processing) continue;
        if(b.script._physics_process) b.script._physics_process(b, dt); if(!b.alive) continue;
        b._physics_process(dt); }
      // the bouncers steer (ferredoxin, VDE: to their targets; FNR / RuBisCO: home)
      for(const [b, kin] of kinOf){ if(kin.kind !== 'bnc' || !kin.b) continue; const bb = kin.b; if(bb.dockedAt || (b.alive && !b.physics_processing)) continue;
        const t = b.alive ? carrierTarget(b) : null; const tp = t ? t.global_position : (kin.home && b.soft_target ? b.soft_target.global_position : null); if(!tp) continue;
        const mi = bb.mi, c = mInfo[mi], x = c.cx + gModelOff[mi*3], y = c.cy + gModelOff[mi*3+1]; let dx = tp[0]-x, dy = tp[1]-y, d = Math.hypot(dx, dy) || 1e-3; const sp = kin.home ? V.Globals.get(b.molecule_name + '_speed') || 8 : (b.speed || 30);
        if(kin.bestD == null || d < kin.bestD - 2){ kin.bestD = d; kin.stuckT = 0; } else kin.stuckT = (kin.stuckT || 0) + dt;   // no headway for 3 s (a shell in the way): detour sideways for a while
        if(kin.detour){ kin.detour.t -= dt; if(kin.detour.t <= 0){ kin.detour = null; kin.bestD = null; } else { dx = kin.detour.x; dy = kin.detour.y; d = 1; } } else if(kin.stuckT > 3 && !kin.home){ const sgn = Math.random() < 0.5 ? 1 : -1; kin.detour = { x: -dy/d*sgn, y: dx/d*sgn, t: 2.5 }; kin.stuckT = 0; }
        const k = (b.alive && b.hard_target) ? 0.5 : 0.06, f = 1 - Math.pow(1-k, dt*60); const vx = bb.vx + (dx/d*sp - bb.vx)*f, vy = bb.vy + (dy/d*sp - bb.vy)*f, l = Math.hypot(vx, vy) || 1; bb.vx = vx/l*sp; bb.vy = vy/l*sp; }
      // ATP synthase: the proton channel's passes are its channeled protons (ATP-synthase.gd counted the proton BindSites' animation)
      for(const a of atps){ const passes = get.gProtonPasses(); if(a.passes0 == null) a.passes0 = passes; if(passes > a.passes0){ if(V.white(a.get_node('BindSites/ADP')) && V.white(a.get_node('BindSites/phosphate'))){ a.channeled_protons += passes - a.passes0; a.try_RELEASING(); } a.passes0 = passes; } }   // (ATP-synthase.gd: a proton binds only while ADP and phosphate are bound)
      // the free instances sitting in slots ride the slots; the parked and released ones go back to their pools
      const F = get.gValoFree(), P = get.gValoProtons();
      if(F){ for(const s of V.all){ if(!s.alive || !s.parent_is_BindSites || s._instance == null) continue; if(s.modulate === 'dark'){ V.env.slotEmptied(s); continue; } const p = s.global_position; F.setWorld(s._key, s._instance, p[0], p[1], p[2]); }
        for(let q = parkedF.length-1; q >= 0; q--){ const pf = parkedF[q]; pf.t += dt; const pk = PARK(); F.setWorld(pf.key, pf.i, pk[0], pk[1], pk[2]); if(pf.t > 25){ parkedF.splice(q, 1); get.gMolHold()[F.base[pf.key] + pf.i] = 0; F.setOff(pf.key, pf.i, 0, 0, 0); } }
        for(let q = released.length-1; q >= 0; q--){ const r = released[q]; r.t += dt; const k = Math.min(1, r.t/r.life), k2 = k*k; const dmp = Math.max(0, 1 - dt*0.5); r.vx *= dmp; r.vy *= dmp; r.vz *= dmp; r.x += r.vx*dt; r.y += r.vy*dt; r.z += r.vz*dt;
          F.pos(r.key, r.i, _a); F.setWorld(r.key, r.i, r.x*(1-k2) + _a[0]*k2, r.y*(1-k2) + _a[1]*k2, r.z*(1-k2) + _a[2]*k2); if(k >= 1){ released.splice(q, 1); get.gMolHold()[F.base[r.key] + r.i] = 0; F.setOff(r.key, r.i, 0, 0, 0); } } }
      if(P) for(const i of parkedP){ const pk = PARK(); P.place(i, pk[0], pk[1], pk[2]); }
      // the overlay: an electron carrier dim when empty, a pigment bright when excited, a damaged tyrosine dark
      for(const [gi, m] of cofMols){ if(!m.alive) continue; let k = 1.0; const e = m.get_node('BindSites/electron'); if(e) k = e.modulate === 'white' ? 1.0 : 0.45; if(m.ExcitedSprite && m.ExcitedSprite.visible) k = 1.6; if(m.DamagedSprite && m.DamagedSprite.visible) k = 0.3; setSlotK(gi, k); }
      if(slotDirty){ slotTex.update(slotData); slotDirty = false; }
      // sprites, glows, labels
      for(const s of sprites){ if(!s.body || !s.body.alive) continue; const p = s.body._pos; s.mesh.position.set(p[0], p[1], p[2]); s.corona.position.set(p[0], p[1], p[2]); const g = 0.5 + Math.min(1.5, s.body.EnergyLevel*V.SCRIPTS.electron.ENERGY_GLOW_FACTOR); s.corona.scaling.set(g, g, g); }
      for(const s of oSprites){ if(!s.body || !s.body.alive) continue; const p = s.body._pos; s.mesh.position.set(p[0], p[1], p[2]); }
      { let n = 0; for(const m of antenna){ if(!m.alive || !m.ExcitedSprite || !m.ExcitedSprite.visible) continue; if(n >= eks.cap) break; const p = m.global_position; putGlow(eks, n++, 2.6 + 0.8*Math.sin(get.gWaveT()*9 + m.id), p[0], p[1], p[2]); } showGlow(eks, n); }
      { let hn = 0; for(let q = heats.length-1; q >= 0; q--){ const H = heats[q]; H.t += dt; if(H.t > 0.5){ heats.splice(q, 1); continue; } if(hn < heat.cap) putGlow(heat, hn++, 3 + 14*(H.t/0.5), H.x, H.y, H.z); } showGlow(heat, hn);
        let fn = 0; for(let q = flashes.length-1; q >= 0; q--){ const Fl = flashes[q]; Fl.t += dt; if(Fl.t > 0.35){ flashes.splice(q, 1); continue; } if(fn < flashG.cap) putGlow(flashG, fn++, 3 + 16*(Fl.t/0.35), Fl.x, Fl.y, Fl.z); } showGlow(flashG, fn);
        let rn = 0; for(let q = rings.length-1; q >= 0; q--){ const R = rings[q]; R.t += dt; if(R.t > 1.0){ rings.splice(q, 1); continue; } if(rn < ringG.cap) putGlow(ringG, rn++, 2 + 12*R.t, R.x, R.y, R.z); } showGlow(ringG, rn); }
      tickLabels();
      // camera.gd: follow whatever valid body is in the 'followed' group
      if(followOn){ const fb = V.get_nodes_in_group('followed')[0]; if(fb){ const p = fb.global_position, t = cam.target, f = 1 - Math.pow(0.1, dt*3); t.x += (p[0]-t.x)*f; t.y += (p[1]-t.y)*f; t.z += (p[2]-t.z)*f; } }
      // the lantern: every free electron and every filled electron slot is a spotlight
      { const L = lantern; L.length = 0; for(const b of V.get_nodes_in_group('electron')){ if(!b.alive) continue; if(b.parent_is_BindSites ? b.modulate !== 'white' : !b.kin) continue; const p = b.global_position; L.push({ on:true, x:p[0], y:p[1], z:p[2] }); if(L.length >= 64) break; }
        for(const b of V.get_nodes_in_group('proton')){ if(!b.alive || !b.kin) continue; const p = b.global_position; L.push({ on:true, x:p[0], y:p[1], z:p[2], p:1 }); if(L.length >= 64) break; } }   // ...and every free proton, an orange pool (owner 13.9.2026)
      prof.all = performance.now() - t0;
      if((++dev & 7) === 0 && (valoRow || (valoRow = document.getElementById('dev-valo-row')))) valoRow.textContent = 'valoreaktiot: O2 ' + stats.o2 + ' · e- FNR:ään ' + stats.fnrE + ' · NADPH ' + stats.nadph + ' · ATP ' + stats.atp + ' · sokeri ' + stats.glukoosi + ' · H+ lumeniin ' + stats.hplus + ' · fotoneja ' + stats.fotonit + ' · lämpönä ' + stats.lampo + ' · vaurioita ' + stats.vaurio + ' · kappaleita ' + V.all.length + ' · ' + prof.all.toFixed(1) + ' ms';
    }, -1, false);
    const lantern = []; window.gValoElecs = lantern;
    const _o2 = V.env.instantiate; V.env.instantiate = (name, opts) => { const b = _o2(name, opts); if(b && name === 'O2' && !(opts && opts.from_slot)) stats.o2++; return b; };

    /* ── dev ── */
    const J = b => b ? (b.modulate === 'white' ? 1 : 0) : '-';
    const slots = b => b && b.BindSites ? b.BindSites.map(s => J(s)).join('') : '-';
    window.__valoInt = { V, units, b6fs, psis, fnrs, ndhs, atps, rubs, antenna, cofMols, kinOf, stats, get };
    window.__valo = () => ({ stats, prof, bodies: V.all.length, areas: V.areas.length,
      units: units.map(u => ({ mi:u.mi, p680: J(u.p680M.get_node('BindSites/electron')), p680ex: !!u.p680M.ExcitedSprite.visible, tyr: u.tyrM && J(u.tyrM.get_node('BindSites/electron')), oec: J(u.oecM.get_node('BindSites/electron')), water: u.oecM.water_state + (J(u.oecM.get_node('BindSites/H2O')) === 1 ? '*' : ''), chlD1: u.chlD1M && J(u.chlD1M.get_node('BindSites/electron')), pheo: u.pheoM && J(u.pheoM.get_node('BindSites/electron')), qa: u.qaM && J(u.qaM.get_node('BindSites/electron')), qb: slots(u.psii.get_node('BindSites/plastoquinone_B')), qbW: J(u.psii.get_node('BindSites/plastoquinone_B')), vde: J(u.psii.get_node('BindSites/VDE')) })),
      b6f: b6fs.map(r => ({ mi:r.mi, qo: slots(r.b6f.get_node('BindSites/plastoquinone_B_LUMENAL')), qo2: slots(r.b6f.get_node('BindSites/plastoquinone_B_LUMENAL2')), qi: slots(r.b6f.get_node('BindSites/plastoquinone_B_STROMAL')), qi2: slots(r.b6f.get_node('BindSites/plastoquinone_B_STROMAL2')), pc: slots(r.b6f.get_node('BindSites/plastocyanin')), pc2: slots(r.b6f.get_node('BindSites/plastocyanin2')), monomers: r.monomers.map(u => ({ rieske: u.rieskeM && J(u.rieskeM.get_node('BindSites/electron')), f: J(u.fM.get_node('BindSites/electron')), bL: J(u.bLM.get_node('BindSites/electron')), bH: J(u.bHM.get_node('BindSites/electron')), cn: J(u.cnM.get_node('BindSites/electron')) })) })),
      psi: psis.map(u => ({ mi:u.mi, pc: slots(u.psi.get_node('BindSites/plastocyanin')), p700: J(u.p700M.get_node('BindSites/electron')), p700ex: !!u.p700M.ExcitedSprite.visible, a0: u.a0M && J(u.a0M.get_node('BindSites/electron')), fx: u.fxM && J(u.fxM.get_node('BindSites/electron')), fa: u.faM && J(u.faM.get_node('BindSites/electron')), fb: u.fbM && J(u.fbM.get_node('BindSites/electron')), fd: slots(u.psi.get_node('BindSites/ferredoxin')) })),
      fnr: fnrs.map(f => ({ mi:f.frame.mi, fd: slots(f.get_node('BindSites/ferredoxin')), e: J(f.get_node('BindSites/electron')), nadp: slots(f.get_node('BindSites/NADP')), nadpW: J(f.get_node('BindSites/NADP')) })),
      ndh: ndhs.map(n => ({ mi:n.frame.mi, fd: slots(n.get_node('BindSites/ferredoxin')), fes: n.fes.map(m => J(m.get_node('BindSites/electron'))).join(''), pq: slots(n.get_node('BindSites/plastoquinone_B')) })),
      atp: atps.map(a => ({ adp: J(a.get_node('BindSites/ADP')), pi: J(a.get_node('BindSites/phosphate')), protons: a.channeled_protons })), rub: rubs.map(r => r.labels),
      carriers: [...kinOf.entries()].filter(([b, k]) => !k.home).map(([b, k]) => ({ name: b.molecule_name, mi: b.mi, alive: b.alive, at: b.alive ? b._pos.map(v => v|0) : (k.dormantAt ? 'in ' + k.dormantAt.body_that_I_am_bound_to.molecule_name + '/' + k.dormantAt.name : '?'), hard: b.alive && b.hard_target ? (b.hard_target.body_that_I_am_bound_to ? b.hard_target.body_that_I_am_bound_to.molecule_name + '/' : '') + b.hard_target.name : null, soft: b.alive && b.soft_target ? (b.soft_target.body_that_I_am_bound_to ? b.soft_target.body_that_I_am_bound_to.molecule_name + '/' : '') + b.soft_target.name : null, slots: slots(b), physics: b.alive && b.physics_processing, fail: b.last_failure_reason })),
      free: V.all.filter(b => b.kin && (b.kin.kind === 'sprite' || b.kin.kind === 'free' || b.kin.kind === 'proton')).map(b => [b.molecule_name, ...b._pos.map(v => v|0), b.hard_target ? (b.hard_target.body_that_I_am_bound_to ? b.hard_target.body_that_I_am_bound_to.molecule_name : b.hard_target.name) : (b.soft_target ? 'soft' : '-')]),
      excited: antenna.filter(m => m.ExcitedSprite && m.ExcitedSprite.visible).length, antenna: antenna.length, followed: (V.get_nodes_in_group('followed')[0] || {}).molecule_name || null,
      kick: (k, n) => { const u = (k >= units.length ? psis[k - units.length] : units[k]); if(!u) return 0; let c = 0; for(let i=0;i<(n||1);i++){ const g = u.ant[(Math.random()*u.ant.length)|0]; if(ctx.get.gValoExcite()(g, 0, 0, 0)) c++; } return c; },
      sep: k => { const u = (k >= units.length ? psis[k - units.length] : units[k]); if(!u) return false; const rc = u.p680M || u.p700M; const ph = V.instantiate('photon', { position: rc.global_position }); ph.touch_area._dyn.add(rc); rc.touch_area._dyn.add(ph); rc.when_body_enters_touch_area(ph); return true; },
      follow: on => window.gValoFollow(on) });
    return { units, b6fs, psis };
  } };
})();
