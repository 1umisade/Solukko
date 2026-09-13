/* cytochrome_b6f - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/cytochrome_b6f.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['cytochrome_b6f'] = {
  scene: { BindSites: [{ name: 'plastoquinone_B_LUMENAL', type: 'plastoquinone_B', place: 1, nearby: 90 }, { name: 'plastoquinone_B_LUMENAL2', type: 'plastoquinone_B', place: 1, nearby: 90 }, { name: 'plastoquinone_B_STROMAL', type: 'plastoquinone_B', place: 5, nearby: 90 }, { name: 'plastoquinone_B_STROMAL2', type: 'plastoquinone_B', place: 5, nearby: 90 }, { name: 'plastocyanin', place: 4, nearby: 90 }, { name: 'plastocyanin2', type: 'plastocyanin', place: 4, nearby: 90 }], nearby: 90 },
  _ready(self){ self.can_overlap_membrane = false; },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){
    if(body.is_in_group('plastoquinone_B')){
      if(BindSite.name === 'plastoquinone_B_LUMENAL'){ for(const s of body.BindSites) if(dark(s)) return null; }    // Qo takes a FULL quinol
      if(BindSite.name === 'plastoquinone_B_LUMENAL2'){ for(const s of body.BindSites) if(dark(s)) return null; }
      if(BindSite.name === 'plastoquinone_B_STROMAL'){ for(const s of body.BindSites) if(white(s)) return null; }   // Qi an EMPTY quinone
      if(BindSite.name === 'plastoquinone_B_STROMAL2'){ for(const s of body.BindSites) if(white(s)) return null; } }
    if(body.is_in_group('plastocyanin')){ if(dark(slot(body, 'electron'))){ } else { return null; } }
    return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){
    if(BindSite_name_string === 'plastocyanin'){ for(const s of slot(self, 'plastocyanin').BindSites){ if(white(s)){ } else { return null; } } }
    if(BindSite_name_string === 'plastocyanin2'){ for(const s of slot(self, 'plastocyanin2').BindSites){ if(white(s)){ } else { return null; } } }
    if(BindSite_name_string === 'plastoquinone_B_LUMENAL'){ for(const s of slot(self, 'plastoquinone_B_LUMENAL').BindSites){ if(dark(s)){ } else { return null; } } }
    if(BindSite_name_string === 'plastoquinone_B_LUMENAL2'){ for(const s of slot(self, 'plastoquinone_B_LUMENAL2').BindSites){ if(dark(s)){ } else { return null; } } }
    if(BindSite_name_string === 'plastoquinone_B_STROMAL'){ for(const s of slot(self, 'plastoquinone_B_STROMAL').BindSites){ if(white(s)){ } else { return null; } } }
    if(BindSite_name_string === 'plastoquinone_B_STROMAL2'){ for(const s of slot(self, 'plastoquinone_B_STROMAL2').BindSites){ if(white(s)){ } else { return null; } } }
    return true; },
  RELEASING_special_actions(self, released_body){
    if(released_body.is_in_group('plastocyanin')){ const t1 = self.get_node('target_1'), t2 = self.get_node('target_2'); if(t1 && t2){ const closest = released_body.distance_to(t1) <= released_body.distance_to(t2) ? t1 : t2; released_body.hard_target = closest; } } },
};
})();
