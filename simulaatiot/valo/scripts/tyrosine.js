/* tyrosine - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/tyrosine.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['tyrosine'] = {
  scene: { BindSites: ['electron', { name: 'O2', nearby: 60 }], place: 3, damageable: true, nearby: 45 },
  _ready(self){ self.original_place = self.place_in_the_chain; },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){
    if(body.is_in_group('O2')){ if(body.ExcitedSprite && body.ExcitedSprite.visible === true){ } else { return null; } }   // only EXCITED oxygen binds (photodamage)
    return true; },
  async BINDING_special_actions(self, BindSite){
    if(BindSite.is_in_group('O2') || BindSite.name === 'O2'){ const o2 = slot(self, 'O2'); if(o2.ExcitedSprite) o2.ExcitedSprite.visible = true; self.DamagedSprite.visible = true; self.place_in_the_chain = 0; V.env.damaged(self);
      await V.wait(5.0); if(!self.alive) return; if(o2.ExcitedSprite) o2.ExcitedSprite.visible = false; self.DamagedSprite.visible = false; self.place_in_the_chain = self.original_place; self.try_RELEASING(); } },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){
    if(BindSite_name_string === 'O2'){ const o2 = slot(self, 'O2'); if(o2.ExcitedSprite && o2.ExcitedSprite.visible === false){ } else { return null; } }
    if(self.DamagedSprite.visible === false){ } else { return null; }
    return true; },
  RELEASING_special_actions(self, released_body){ self.place_in_the_chain = self.original_place; if(released_body.is_in_group('O2')){ self.try_RELEASING(); } for(const body of V.get_nodes_in_group('O2')) body.hard_target = null; },
};
})();
