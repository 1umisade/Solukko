/* plastocyanin - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/plastocyanin.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['plastocyanin'] = {
  scene: { BindSites: ['electron'], nearby: 60, radius: 14 },
  _ready(self){ },
  _physics_process(self, delta){ self.retarget_t = (self.retarget_t || 0) + delta; if(self.retarget_t > 3 && self.body_that_I_am_bound_to == null && (self.soft_target == null || white(self.soft_target))){ self.retarget_t = 0; self.check_soft_target(); } },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return self.body_that_I_am_bound_to != null ? true : null; },   // (3D 14.9.2026: a FREE plastocyanin sits at place 0 and b6f's quinol at place 1 - a full one passing b6f handed its electron back to the quinol, and it cycled quinol -> Rieske -> heme f -> plastocyanin -> quinol for good. It gives up its electron only where it is docked: at PSI, place 13 -> P700)
  RELEASING_special_actions(self, released_body){ },
  check_soft_target(self){
    if(self.body_that_I_am_bound_to != null) return;
    /* ONE plastocyanin per dock (owner 15.9.2026: 'only one carrier can target its target at a time'): a free dock no other plastocyanin heads for, else none - idle until the 3 s re-check */
    const others = V.get_nodes_in_group('plastocyanin').filter(p => p !== self); const free = list => list.filter(s => s && dark(s) && !others.some(o => o.soft_target === s || o.hard_target === s));
    if(white(slot(self, 'electron'))){ self.soft_target = V.pick_random(free(V.get_nodes_in_group('photosystem_I').map(p => p.get_node('BindSites/plastocyanin')))) || null; }
    else { const all_slots = []; for(const cytochrome of V.get_nodes_in_group('cytochrome_b6f')){ all_slots.push(cytochrome.get_node('BindSites/plastocyanin')); all_slots.push(cytochrome.get_node('BindSites/plastocyanin2')); }
      let best = null, bd = Infinity; for(const s of free(all_slots)){ const d = self.distance_to(s); if(d < bd){ bd = d; best = s; } } self.soft_target = best; } },
};
})();
