/* photosystem_II - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/Photosystem_II.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['photosystem_II'] = {
  scene: { BindSites: [{ name: 'plastoquinone_B', nearby: 90, place: 8 }, { name: 'VDE', nearby: 320 }], place: -1, nearby: 90 },
  _ready(self){ },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){
    if(body.is_in_group('plastoquinone_B')){ for(const pqb_BindSite of body.BindSites){ if(dark(pqb_BindSite)){ } else { return null; } } }   // an EMPTY plastoquinone docks
    return true; },
  async BINDING_special_actions(self, BindSite){
    if(BindSite.is_in_group('VDE')){ V.env.vdeDocked(self, BindSite); await V.wait(7.0); if(self.alive) self.try_RELEASING(); } },   // the VDE_animation: 7 s on the complex, then released
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){
    if(BindSite_name_string === 'plastoquinone_B'){ for(const s of slot(self, 'plastoquinone_B').BindSites){ if(dark(s)) return null; } }   // it leaves FULL (2 e-, 2 H+)
    if(BindSite_name_string === 'VDE'){ if(self.vde_done){ } else { return null; } }
    return true; },
  RELEASING_special_actions(self, released_body){ if(released_body.is_in_group('VDE')){ released_body.soft_target = self.get_node('target_4'); self.vde_done = false; } },
  when_body_exits_touch_area_SPECIAL_ACTIONS(self, body){ },
};
})();
