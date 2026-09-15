/* ferredoxin - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/ferredoxin.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['ferredoxin'] = {
  scene: { BindSites: ['electron'], place: 20, nearby: 60, radius: 16 },
  ferredoxin_goes_to_ndh: false,   // static var: FNR and NDH-1 in turn
  _ready(self){ },
  _physics_process(self, delta){ self.retarget_t = (self.retarget_t || 0) + delta; if(self.retarget_t > 3 && self.body_that_I_am_bound_to == null){ self.retarget_t = 0; self.check_soft_target(); } },   // (every 3 s while free: a carrier always has a target - full it heads for FNR / NDH-1, empty for PSI; owner 14.9.2026)
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ if(self.body_that_I_am_bound_to != null){ } else { return null; } return true; },
  RELEASING_special_actions(self, released_body){ },
  check_soft_target(self){
    if(self.body_that_I_am_bound_to != null) return;
    /* ONE ferredoxin per dock (owner 15.9.2026: 'only one carrier can target its target at a time'): a free dock no other ferredoxin heads for, else none - idle until the 3 s re-check */
    const others = V.get_nodes_in_group('ferredoxin').filter(f => f !== self); const free = list => list.filter(s => s && dark(s) && !others.some(o => o.soft_target === s || o.hard_target === s));
    const docks = grp => free(V.get_nodes_in_group(grp).filter(item => !item.parent_is_BindSites).map(item => item.get_node('BindSites/ferredoxin')));
    if(dark(slot(self, 'electron'))){ self.soft_target = V.pick_random(docks('photosystem_I')) || null; }
    else if(white(slot(self, 'electron'))){
      if(this.ferredoxin_goes_to_ndh){ self.soft_target = V.pick_random(docks('NDH-1')) || null; }
      else { self.soft_target = V.pick_random(docks('FNR')) || null; }
      if(self.soft_target == null){ self.soft_target = V.pick_random(docks('NDH-1')) || V.pick_random(docks('FNR')) || null; }
      if(self.delivered){ this.ferredoxin_goes_to_ndh = !this.ferredoxin_goes_to_ndh; self.delivered = false; } } },   // (the toggle flips per delivery, not per call: check_soft_target runs often here)
};
})();
