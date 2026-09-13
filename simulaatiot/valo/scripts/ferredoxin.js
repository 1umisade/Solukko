/* ferredoxin - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/ferredoxin.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['ferredoxin'] = {
  scene: { BindSites: ['electron'], place: 20, nearby: 60, radius: 16 },
  ferredoxin_goes_to_ndh: false,   // static var: FNR and NDH-1 in turn
  _ready(self){ },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ if(self.body_that_I_am_bound_to != null){ } else { return null; } return true; },
  RELEASING_special_actions(self, released_body){ },
  check_soft_target(self){
    if(self.body_that_I_am_bound_to != null) return;
    if(dark(slot(self, 'electron'))){ const psi = V.pick_random(V.get_nodes_in_group('photosystem_I').filter(item => !item.parent_is_BindSites)); self.soft_target = psi ? psi.get_node('BindSites/ferredoxin') : null; }
    else if(white(slot(self, 'electron'))){
      if(this.ferredoxin_goes_to_ndh){ const n = V.pick_random(V.get_nodes_in_group('NDH-1').filter(item => !item.parent_is_BindSites)); self.soft_target = n ? n.get_node('BindSites/ferredoxin') : null; }
      else { const f = V.pick_random(V.get_nodes_in_group('FNR').filter(item => !item.parent_is_BindSites)); self.soft_target = f ? f.get_node('BindSites/ferredoxin') : null; }
      if(self.soft_target == null){ const n = V.pick_random(V.get_nodes_in_group('NDH-1').filter(item => !item.parent_is_BindSites)); self.soft_target = n ? n.get_node('BindSites/ferredoxin') : null; }
      if(self.delivered){ this.ferredoxin_goes_to_ndh = !this.ferredoxin_goes_to_ndh; self.delivered = false; } } },   // (the toggle flips per delivery, not per call: check_soft_target runs often here)
};
})();
