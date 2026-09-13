/* photosystem_I - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/photosystem_I.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['photosystem_I'] = {
  scene: { BindSites: [{ name: 'plastocyanin', place: 13, nearby: 90 }, { name: 'ferredoxin', place: 20, nearby: 320 }], nearby: 90 },
  _ready(self){ self.can_overlap_membrane = false; },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){
    if(body.is_in_group('plastocyanin') === true){ if(white(slot(body, 'electron'))){ } else { return null; } }
    if(body.is_in_group('ferredoxin')){ if(dark(slot(body, 'electron'))){ } else { return null; } }   // (3D: an EMPTY ferredoxin docks on the FB face)
    return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){
    if(BindSite_name_string === 'plastocyanin'){ if(dark(slot(slot(self, 'plastocyanin'), 'electron'))){ } else { return null; } }   // (photosystem_I.gd also waited for P700 to be filled again; an excited P700 can fire first and the dock would deadlock)
    if(BindSite_name_string === 'ferredoxin'){ if(white(slot(slot(self, 'ferredoxin'), 'electron'))){ } else { return null; } }
    return true; },
  RELEASING_special_actions(self, released_body){ if(released_body.is_in_group('plastocyanin')){ released_body.hard_target = self.get_node('target_1'); } },
};
})();
