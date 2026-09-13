/* O2 - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/O2.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['O2'] = {
  scene: { excitable: true, radius: 2, nearby: 24 },
  _ready(self){ },                                             // molecule_name = 'O2'; super._ready()
  PULLING_special_actions(self, body){ },                        // Nothing here.
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return true; },
  RELEASING_special_actions(self, released_body){ },
  check_soft_target(self){
    if(self.body_that_I_am_bound_to != null) return;
    if(self.ExcitedSprite && self.ExcitedSprite.visible){ self.set_collision_layer_value(1, false); self.set_collision_mask_value(1, false); self.set_collision_layer_value(2, true); self.set_collision_mask_value(2, true); const t = V.pick_random(V.get_nodes_in_group('tyrosine')); self.soft_target = t ? t.get_node('BindSites/O2') : null; }
    else { self.soft_target = V.pick_random(V.get_nodes_in_group('P680')); } },
};
})();
