/* FNR - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/FNR.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['FNR'] = {
  scene: { BindSites: [{ name: 'ferredoxin', place: 19, nearby: 320 }, { name: 'NADP', place: 21, nearby: 400 }, { name: 'electron', place: 21, nearby: 45 }], place: 20, nearby: 180 },
  _ready(self){ },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){
    if(body.is_in_group('NADP')){ if(dark(slot(body, 'electron')) || dark(slot(body, 'electron_2'))){ } else { return null; } }
    if(body.is_in_group('ferredoxin')){ if(white(slot(body, 'electron'))){ } else { return null; } }
    return true; },
  BINDING_special_actions(self, BindSite){
    /* 3D (owner 13.9.2026: 'a stream of electrons going to FNR where they disappear as a placeholder'): FNR is the SINK - an electron
       that lands on its 'electron' BindSite is gone at once, counted (two per NADPH); the docked NADP+ shows the count filling up */
    if(BindSite.name === 'electron'){ BindSite.modulate = 'dark'; BindSite.EnergyLevel = 0; V.env.sink(self, BindSite);
      const nd = slot(self, 'NADP'); if(nd && white(nd)){ const e1 = slot(nd, 'electron'), e2 = slot(nd, 'electron_2'); if(e1 && dark(e1)) e1.modulate = 'white'; else if(e2 && dark(e2)) e2.modulate = 'white'; } } },
  async RELEASING_special_conditions(self, BindSite_name_string, acceptor){
    if(BindSite_name_string === 'ferredoxin'){
      if(white(slot(slot(self, 'ferredoxin'), 'electron'))) return null;
      await V.physics_frame(); await V.physics_frame(); if(!self.alive) return null;
      for(const body of slot(self, 'ferredoxin').touch_area.get_overlapping_bodies()) if(body.is_in_group('electron') && !body.parent_is_BindSites) return null; }
    if(BindSite_name_string === 'NADP'){ const nd = slot(self, 'NADP'); if(white(slot(nd, 'electron')) && white(slot(nd, 'electron_2')) && white(slot(nd, 'proton'))){ } else { return null; } }
    return true; },
  RELEASING_special_actions(self, released_body){ if(released_body.is_in_group('NADP')) V.env.nadphMade(released_body); if(released_body.is_in_group('ferredoxin')) released_body.delivered = true; },
  check_soft_target(self){ self.soft_target = self.get_node('Node2'); },   // a fixed node: it stays where it is (3D: against PSI's FB face, see the level)
};
})();
