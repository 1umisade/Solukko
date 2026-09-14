/* ATP-synthase - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/ATP-synthase.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['ATP-synthase'] = {
  scene: { BindSites: [{ name: 'ADP', nearby: 400 }, { name: 'phosphate', nearby: 400 }], nearby: 90 },
  _ready(self){ self.channeled_protons = 0; self.proton_positions = {}; },   // (3D 14.9.2026: the ring starts empty - the fourth proton IN makes the first ATP; 2D banked three)
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){
    if(body.is_in_group('proton')){ if(white(slot(self, 'ADP')) && white(slot(self, 'phosphate'))){ } else { return null; } if((self.proton_positions[BindSite.name] || 0.0) === 0.0){ } else { return null; } }
    return true; },
  BINDING_special_actions(self, BindSite){ },   // (the rotor animation: the sheet's own proton channel turns the rotor; its passes count as channeled protons, see the level)
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){
    if(BindSite_name_string.includes('ADP') || BindSite_name_string.includes('phosphate')){ if(white(slot(self, 'ADP')) && white(slot(self, 'phosphate'))){ } else { return null; } if(self.channeled_protons >= 4){ } else { return null; } }
    if(BindSite_name_string.includes('proton')){ if((self.proton_positions[BindSite_name_string] || 0.0) >= 4.0){ } else { return null; } }
    return true; },
  RELEASING_special_actions(self, released_body){
    if(released_body.is_in_group('phosphate') || released_body.is_in_group('ADP')){ released_body.queue_free(); slot(self, 'ADP').modulate = 'dark'; slot(self, 'phosphate').modulate = 'dark'; V.env.slotEmptied(slot(self, 'ADP')); V.env.slotEmptied(slot(self, 'phosphate'));
      const ATP = V.instantiate('ATP', { position: slot(self, 'ADP').global_position }); if(ATP){ ATP.set_collision_layer_value(1, false); ATP.set_collision_mask_value(1, false); ATP.set_collision_layer_value(2, true); ATP.set_collision_mask_value(2, true); ATP.set_meta('exiting', true); }
      self.channeled_protons = 0; V.env.atpMade(self); }
    if(released_body.is_in_group('proton')){ released_body.set_collision_layer_value(2, false); released_body.set_collision_layer_value(1, true); released_body.set_meta('exiting', true); self.channeled_protons += 1; } },
  check_soft_target(self){ },
};
})();
