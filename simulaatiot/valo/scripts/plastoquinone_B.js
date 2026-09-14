/* plastoquinone_B - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/Plastoquinone_B.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.pqSide = b => (b.kin && b.kin.pqSet) || ((b.src === 'NDH-1' || (b.src === 'cytochrome_b6f' && /2$/.test(b.srcSlot || ''))) ? 'ndh' : 'psii');   // the set is fixed per shuttle (kin.pqSet, owner 14.9.2026: 'two different sets of PQB - 10 between PSII and b6f, another between b6f and NDH-1'); the origin rule is the fallback   // which of b6f's two sides a quinone belongs to: it came from NDH-1's pocket or from b6f's second-side slots - else PSII's side (fresh ones too)
V.SCRIPTS['plastoquinone_B'] = {
  scene: { BindSites: ['electron', 'electron_2', { name: 'proton', nearby: 250 }, { name: 'proton_2', nearby: 250 }], nearby: 60, nearby2: 250, radius: 14 },
  _ready(self){ this.update_proton_puller(self); },
  _physics_process(self, delta){ self.retarget_t = (self.retarget_t || 0) + delta; if(self.retarget_t > 3 && self.body_that_I_am_bound_to == null){ self.retarget_t = 0; self.check_soft_target(); } },   // (every 3 s while free, not only when the target is taken: a quinone that chose NDH-1 before PSII existed kept that choice for ever - 14.9.2026)   // (3D: check_soft_target again while the pocket it heads for is taken - the 2D level had one cytochrome and re-ran it on every nearby event)
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){
    if(self.body_that_I_am_bound_to != null){ } else { return null; }   // only a docked quinone takes anything
    if(body.is_in_group('proton')){ if(white(slot(self, 'electron')) && white(slot(self, 'electron_2'))){ } else { return null; } }   // protons only after both electrons
    if(body.hard_target === BindSite || body.hard_target == null){ } else { return null; }
    return true; },
  BINDING_special_actions(self, BindSite){ this.update_proton_puller(self); },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){
    if(self.name === 'plastoquinone_B_LUMENAL' || self.name === 'plastoquinone_B_LUMENAL2'){ } else { return null; }   // only at the Qo site does a quinol give anything up
    if(BindSite_name_string.includes('proton')){ if(dark(slot(self, 'electron')) && dark(slot(self, 'electron_2'))){ } else { return null; } }   // protons after the electrons
    return true; },
  RELEASING_special_actions(self, released_body){
    if(released_body.is_in_group('proton')){ const cyt = V.pick_random(V.get_nodes_in_group('cytochrome_b6f')); if(cyt) released_body.hard_target = cyt.get_node('target_3'); } },
  check_soft_target(self){
    if(self.body_that_I_am_bound_to != null) return;   // (a docked one is a slot's placeholder)
    const ndh = V.pqSide(self) === 'ndh';   // the SIDE this quinone belongs to (owner 14.9.2026: 'the left side of b6f is only accessible by PQBs from PSII, the other side is reserved for the ones from NDH-1')
    /* 14.9.2026 (owner: 'the electrons dont move from PSII'): the 2D rule sent half the empty quinones to b6f's Qi sites and NDH-1, where they
       waited for electrons that only ever arrive through PSII's QB pocket - a starved loop. An EMPTY quinone now heads for a free PSII pocket
       first (the nearest one nobody is heading for), only then for b6f's Qi or NDH-1; a FULL one (two electrons, two protons) for b6f's Qo. */
    const filled = self.BindSites.filter(item => white(item)).length;
    const heading = (target) => V.get_nodes_in_group('plastoquinone_B').filter(item => item !== self && item !== target && (item.soft_target === target || item.hard_target === target)).length;
    const nearestFree = (list, spare) => { let best = null, bd = Infinity; for(const s of list){ if(!s || white(s) || (spare && heading(s) > 0)) continue; const d = self.distance_to(s); if(d < bd){ bd = d; best = s; } } return best; };
    const nearestAny = list => { let best = null, bd = Infinity; for(const s of list){ if(!s) continue; const d = self.distance_to(s); if(d < bd){ bd = d; best = s; } } return best; };   // (a carrier ALWAYS has a target - owner 14.9.2026: taken or not, it heads for the nearest site and waits there)
    const b6f = V.get_nodes_in_group('cytochrome_b6f');
    if(filled === 4){ const qo = b6f.map(c => c.get_node('BindSites/' + (ndh ? 'plastoquinone_B_LUMENAL2' : 'plastoquinone_B_LUMENAL')));   // one monomer's Qo for PSII's quinols, the other's for NDH-1's (owner 14.9.2026)
      self.soft_target = nearestFree(qo, true) || nearestFree(qo, false) || nearestAny(qo); return; }
    const qi = b6f.map(c => c.get_node('BindSites/' + (ndh ? 'plastoquinone_B_STROMAL2' : 'plastoquinone_B_STROMAL')));   // ...and the same monomer's Qi for the empty ones
    if(ndh){ const ndhSlots = V.get_nodes_in_group('NDH-1').map(n => n.get_node('BindSites/plastoquinone_B')); self.soft_target = nearestFree(ndhSlots, true) || nearestFree(qi, true) || nearestFree(ndhSlots, false) || nearestAny(ndhSlots.concat(qi)); return; }
    const psiiSlots = V.get_nodes_in_group('photosystem_II').map(p => p.get_node('BindSites/plastoquinone_B'));
    self.soft_target = nearestFree(psiiSlots, true) || nearestFree(qi, true) || nearestFree(psiiSlots, false) || nearestAny(psiiSlots.concat(qi)); },
  update_proton_puller(self){ if(self.nearby_area_2) self.nearby_area_2.enabled = self.body_that_I_am_bound_to != null; },   // the proton puller works only in a pocket
};
})();
