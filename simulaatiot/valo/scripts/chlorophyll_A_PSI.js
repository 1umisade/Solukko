/* chlorophyll_A_PSI - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/chlorophyll_A_PS_I.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['chlorophyll_A_PSI'] = {
  scene: { BindSites: ['electron'], place: 15, nearby: 45 },
  _ready(self){ },                                             // molecule_name = 'chlorophyll_A_PSI'; super._ready()
  PULLING_special_actions(self, body){ },                        // Nothing here.
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return true; },
  RELEASING_special_actions(self, released_body){ },
};
})();
