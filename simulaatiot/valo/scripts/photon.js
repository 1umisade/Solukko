/* photon - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/photon.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['photon'] = {
  scene: { excitable: true, radius: 1 },
  _ready(self){ self.EnergyLevel = 0.292; },   // (the beams themselves are the sheet's photon pool; this body exists for the frame it touches a pigment)
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return true; },
  RELEASING_special_actions(self, released_body){ },
};
})();
