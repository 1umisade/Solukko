/* plastocyanin - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/plastocyanin.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['plastocyanin'] = {
  scene: { BindSites: ['electron'], nearby: 60, radius: 14 },
  _ready(self){ },
  _physics_process(self, delta){ self.retarget_t = (self.retarget_t || 0) + delta; if(self.retarget_t > 3 && self.body_that_I_am_bound_to == null && (self.soft_target == null || white(self.soft_target))){ self.retarget_t = 0; self.check_soft_target(); } },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return true; },
  RELEASING_special_actions(self, released_body){ },
  check_soft_target(self){
    if(self.body_that_I_am_bound_to != null) return;
    if(white(slot(self, 'electron'))){ const psi = V.pick_random(V.get_nodes_in_group('photosystem_I').filter(p => p.body_that_I_am_bound_to == null)); self.soft_target = psi ? psi.get_node('BindSites/plastocyanin') : null; }
    else { const all_slots = []; for(const cytochrome of V.get_nodes_in_group('cytochrome_b6f')){ all_slots.push(cytochrome.get_node('BindSites/plastocyanin')); all_slots.push(cytochrome.get_node('BindSites/plastocyanin2')); }
      const all_plastocyanins = V.get_nodes_in_group('plastocyanin'); let best_slot = null, fewest = Infinity;
      for(const s of all_slots){ if(!s) continue; const heading_here = all_plastocyanins.filter(item => item !== self && item.soft_target === s).length; if(heading_here < fewest){ fewest = heading_here; best_slot = s; } }
      self.soft_target = best_slot; } },
};
})();
