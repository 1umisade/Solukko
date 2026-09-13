/* xanthophyll - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/xanthophyll.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['xanthophyll'] = {
  scene: { excitable: true, nearby: 34, place: 2 },
  _ready(self){ self.add_to_group('violaxanthin'); },                                             // molecule_name = 'xanthophyll'; super._ready()
  PULLING_special_actions(self, body){ },                        // Nothing here.
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return true; },
  RELEASING_special_actions(self, released_body){ },
  try_to_transform_to_zeaxanthin(self){ self.add_to_group('zeaxanthin'); self.remove_from_group('violaxanthin'); self.wobble_once(); V.env.xanthophyllChanged(self);
    if(self.nearby_area) for(const nearby_body of self.nearby_area.get_overlapping_bodies()) if(nearby_body.has_method('try_EXCITATION_TRANSFERRING')) nearby_body.try_EXCITATION_TRANSFERRING();
    self.place_in_the_chain = 0; },
  try_to_transform_to_violaxanthin(self){ self.add_to_group('violaxanthin'); self.remove_from_group('zeaxanthin'); self.wobble_once(); V.env.xanthophyllChanged(self); self.place_in_the_chain = self.antenna_place != null ? self.antenna_place : 3; },
};
})();
