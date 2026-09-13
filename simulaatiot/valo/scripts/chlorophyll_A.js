/* chlorophyll_A - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/chlorophyll_A.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['chlorophyll_A'] = {
  scene: { excitable: true, nearby: 34, place: 1 },
  _ready(self){ },                                             // molecule_name = 'chlorophyll_A'; super._ready()
  PULLING_special_actions(self, body){ },                        // Nothing here.
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return true; },
  RELEASING_special_actions(self, released_body){ },
};
})();
