/* electron - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/electron.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['electron'] = {
  scene: { excitable: true, radius: 2.3 },
  ENERGY_GLOW_FACTOR: 3.0 / 0.292,
  _ready(self){ },   // pulsing(): the level scales the corona by EnergyLevel * ENERGY_GLOW_FACTOR and draws the aJ label
  _physics_process(self, delta){
    if(self.hard_target == null){ self.queue_free(); return; }
    if(V.is_instance_valid(self.body_that_I_am_bound_to) && self.body_that_I_am_bound_to.modulate !== 'white'){ self.queue_free(); } },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return true; },
  RELEASING_special_actions(self, released_body){ },
};
})();
