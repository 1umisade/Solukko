/* OEC - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/OEC.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['OEC'] = {
  scene: { BindSites: ['electron', { name: 'H2O', nearby: 400 }], place: 2 },
  _ready(self){ self.water_state = 'H2O'; },   // the H2O BindSite's sprite: H2O -> OH -> released as O (the 2D swapped textures; here a state)
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ this.try_to_remove_electron_from_water(self); },   // Runs after binding
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ if(BindSite_name_string !== 'H2O'){ } else { return null; } return true; },   // water is never released as water
  RELEASING_special_actions(self, released_body){ this.try_to_remove_electron_from_water(self); },   // Runs after releasing a body
  try_to_remove_electron_from_water(self){
    // SAFETY 1: the required BindSites exist
    if(!(slot(self, 'H2O') && slot(self, 'electron'))){ self.debug_info('try_to_remove_electron_from_water', 'Required BindSites missing'); return null; }
    // CONDITION 1: I must have bound water
    if(!white(slot(self, 'H2O'))){ self.debug_info('try_to_remove_electron_from_water', 'No bound water'); return null; }
    // CONDITION 2: I must not have an electron
    if(!dark(slot(self, 'electron'))){ self.debug_info('try_to_remove_electron_from_water', 'Already have an electron'); return null; }
    const H2O_BindSite = slot(self, 'H2O'), at = H2O_BindSite.global_position;
    // ACTION 1: change the sprite of H2O_BindSite - H2O -> OH, OH -> O and release it
    if(self.water_state === 'H2O'){ self.water_state = 'OH'; }
    else if(self.water_state === 'OH'){
      const scene = V.instantiate('O', { position: at, from_slot: H2O_BindSite });
      if(scene){ scene.set_collision_layer_value(1, false); scene.set_collision_mask_value(1, false); scene.set_collision_layer_value(2, true); scene.set_collision_mask_value(2, true);
        const psii = V.pick_random(V.get_nodes_in_group('photosystem_II')); if(psii){ scene.soft_target = psii.get_node('target_4'); scene.direction = V.dirTo(scene.global_position, psii.get_node('target_4').global_position); }
        scene.set_meta('exiting', true); }
      // reset the sprite back to H2O
      self.water_state = 'H2O'; H2O_BindSite.modulate = 'dark'; V.env.slotEmptied(H2O_BindSite); }
    // ACTION 2: spawn electron
    { const scene = V.instantiate('electron', { position: at });
      if(scene){ scene.hard_target = slot(self, 'electron'); scene.set_collision_layer_value(1, false); scene.set_collision_mask_value(1, false); scene.set_collision_layer_value(2, true); scene.set_collision_mask_value(2, true); } }
    // ACTION 3: spawn proton
    { const scene = V.instantiate('proton', { position: at });
      if(scene){ scene.set_collision_layer_value(1, false); scene.set_collision_mask_value(1, false); scene.set_collision_layer_value(2, true); scene.set_collision_mask_value(2, true);
        const psii = V.pick_random(V.get_nodes_in_group('photosystem_II')); if(psii) scene.soft_target = psii.get_node('target_4');
        (async () => { let timer = 1.0; while(timer > 0 && scene.alive){ scene.direction = V.normalize([Math.random()*2-1, -1.0, 0]); timer -= V.dt; await V.process_frame(); } })(); } } },
};
})();
