/* zeaxanthin_epoxidase - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/zeaxanthin_epoxidase.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['zeaxanthin_epoxidase'] = {
  scene: { nearby: 60, radius: 26 },
  _ready(self){ },                                             // molecule_name = 'zeaxanthin_epoxidase'; super._ready()
  PULLING_special_actions(self, body){ },                        // Nothing here.
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return true; },
  RELEASING_special_actions(self, released_body){ },
  when_body_enters_touch_area_LOCAL(self, body){ /* if(body.is_in_group('violaxanthin')) body.script.try_to_transform_to_zeaxanthin(body); else if(body.is_in_group('zeaxanthin')) body.script.try_to_transform_to_violaxanthin(body); */ },
};
})();
