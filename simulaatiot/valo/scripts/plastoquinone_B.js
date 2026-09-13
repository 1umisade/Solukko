/* plastoquinone_B - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/Plastoquinone_B.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['plastoquinone_B'] = {
  scene: { BindSites: ['electron', 'electron_2', { name: 'proton', nearby: 250 }, { name: 'proton_2', nearby: 250 }], nearby: 60, nearby2: 250, radius: 14 },
  _ready(self){ this.update_proton_puller(self); },
  _physics_process(self, delta){ self.retarget_t = (self.retarget_t || 0) + delta; if(self.retarget_t > 3 && self.body_that_I_am_bound_to == null && (self.soft_target == null || white(self.soft_target))){ self.retarget_t = 0; self.check_soft_target(); } },   // (3D: check_soft_target again while the pocket it heads for is taken - the 2D level had one cytochrome and re-ran it on every nearby event)
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
    const PSII = V.pick_random(V.get_nodes_in_group('photosystem_II')), NDH_1 = V.pick_random(V.get_nodes_in_group('NDH-1')), cytb6f = V.pick_random(V.get_nodes_in_group('cytochrome_b6f'));
    if(!PSII || !cytb6f) return;
    const nearestOf = (name) => { let best = null, bd = Infinity; for(const b of V.get_nodes_in_group(name)) if(b.body_that_I_am_bound_to == null){ const d = self.distance_to(b); if(d < bd){ bd = d; best = b; } } return best; };
    const psiiN = nearestOf('photosystem_II'), ndhN = nearestOf('NDH-1');
    const ownership = (ndhN && (!psiiN || self.distance_to(ndhN) < self.distance_to(psiiN))) ? 'NDH-1' : 'PSII';
    const filled = self.BindSites.filter(item => white(item)).length;
    const heading = (target) => V.get_nodes_in_group('plastoquinone_B').filter(item => item !== self && item.soft_target === target).length;
    const freeSlot = (list) => { let best = null, bd = Infinity; for(const s of list){ if(!s || white(s)) continue; const d = self.distance_to(s); if(d < bd){ bd = d; best = s; } } return best || list.find(Boolean) || null; };
    const lumenal = freeSlot(V.get_nodes_in_group('cytochrome_b6f').flatMap(c => [c.get_node('BindSites/plastoquinone_B_LUMENAL'), c.get_node('BindSites/plastoquinone_B_LUMENAL2')]));
    const stromal = freeSlot(V.get_nodes_in_group('cytochrome_b6f').flatMap(c => [c.get_node('BindSites/plastoquinone_B_STROMAL'), c.get_node('BindSites/plastoquinone_B_STROMAL2')]));
    if(ownership === 'PSII'){
      if(filled === 4) self.soft_target = lumenal;
      else { const psiiSlot = freeSlot(V.get_nodes_in_group('photosystem_II').map(p => p.get_node('BindSites/plastoquinone_B')));
        self.soft_target = heading(stromal) > heading(psiiSlot) ? psiiSlot : stromal; } }
    else {
      if(filled === 4) self.soft_target = lumenal;
      else { const ndhSlot = freeSlot(V.get_nodes_in_group('NDH-1').map(n => n.get_node('BindSites/plastoquinone_B')));
        self.soft_target = heading(stromal) > heading(ndhSlot) ? ndhSlot : stromal; } } },
  update_proton_puller(self){ if(self.nearby_area_2) self.nearby_area_2.enabled = self.body_that_I_am_bound_to != null; },   // the proton puller works only in a pocket
};
})();
