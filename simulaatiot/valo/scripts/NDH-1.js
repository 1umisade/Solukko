/* NDH-1 - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/NDH-1.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['NDH-1'] = {
  scene: { BindSites: [{ name: 'ferredoxin', place: 1, nearby: 320 }, { name: 'plastoquinone_B', place: 2, nearby: 90 }], nearby: 90 },
  _ready(self){ },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){
    if(body.is_in_group('ferredoxin')){ if(white(slot(body, 'electron'))){ } else { return null; } }
    if(body.is_in_group('plastoquinone_B')){ for(const pqb_BindSite of body.BindSites){ if(dark(pqb_BindSite)){ } else { return null; } } }
    return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){
    if(BindSite_name_string === 'ferredoxin'){ if(dark(slot(slot(self, 'ferredoxin'), 'electron'))){ } else { return null; } }
    if(BindSite_name_string === 'plastoquinone_B'){ for(const s of slot(self, 'plastoquinone_B').BindSites){ if(dark(s)) return null; } }
    return true; },
  RELEASING_special_actions(self, released_body){ if(released_body.is_in_group('ferredoxin')){ released_body.hard_target = self.get_node('target_2'); released_body.delivered = true; } },
};
})();
