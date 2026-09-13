/* P700 - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/P700.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['P700'] = {
  scene: { BindSites: ['electron'], place: 14, excitable: true, nearby: 45 },
  _ready(self){ },   // update_label(): the level draws the aJ label while the ExcitedSprite is visible
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  async RELEASING_special_conditions(self, BindSite_name_string, acceptor){
    // CONDITION 1: I must be excited.
    if(self.ExcitedSprite.visible){
      // Stay excited for 1 second before releasing the electron, then re-check.
      if(BindSite_name_string.includes('electron')){ await V.wait(1.0); if(!self.alive || !self.ExcitedSprite.visible) return null; } }
    else { self.debug_info('RELEASING_special_conditions', 'not excited'); return null; }
    return true; },
  RELEASING_special_actions(self, released_body){
    if(released_body.is_in_group('electron')){ if(released_body.ExcitedSprite) released_body.ExcitedSprite.visible = true; released_body.EnergyLevel = self.EnergyLevel;
      // Hand the camera-follow on to the electron I just released.
      if(self.is_in_group('followed')){ self.remove_from_group('followed'); released_body.add_to_group('followed'); } } },
};
})();
