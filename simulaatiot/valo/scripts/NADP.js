/* NADP - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/NADP.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['NADP'] = {
  scene: { BindSites: ['electron', 'electron_2', { name: 'proton', nearby: 250 }], nearby: 45 },
  _ready(self){ },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){
    if(body.is_in_group('electron')){ if(self.body_that_I_am_bound_to != null && self.body_that_I_am_bound_to.is_in_group('FNR')){ } else { return null; } }
    if(body.is_in_group('proton')){ if(white(slot(self, 'electron')) || white(slot(self, 'electron_2'))){ } else { return null; } }
    return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return null; },   // NADP never releases on its own
  RELEASING_special_actions(self, released_body){ },
  check_soft_target(self){
    if(self.body_that_I_am_bound_to != null) return;
    if(white(slot(self, 'electron'))){ const r = V.pick_random(V.get_nodes_in_group('RuBisCO').filter(item => !item.parent_is_BindSites)); self.soft_target = r ? r.get_node('BindSites/NADP_1') : null; }
    else if(dark(slot(self, 'electron'))){ const f = V.pick_random(V.get_nodes_in_group('FNR').filter(item => !item.parent_is_BindSites)); self.soft_target = f ? f.get_node('BindSites/NADP') : null; } },
};
})();
