/* RuBisCO - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/RuBisCo.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['RuBisCO'] = {
  scene: { BindSites: [{ name: 'CO2_1', nearby: 400 }, { name: 'CO2_2', nearby: 400 }, { name: 'CO2_3', nearby: 400 }, { name: 'NADP_1', nearby: 400 }, { name: 'NADP_2', nearby: 400 }, { name: 'ATP_1', nearby: 400 }, { name: 'ATP_2', nearby: 400 }, { name: 'ATP_3', nearby: 400 }], nearby: 90 },
  _ready(self){ this.update_substrate_labels(self); },
  update_substrate_labels(self){ let co2_bound = 0, co2_total = 0, nadp_bound = 0, nadp_total = 0, atp_bound = 0, atp_total = 0;
    for(const s of self.BindSites){ const filled = white(s); if(s.name.startsWith('CO2')){ co2_total++; if(filled) co2_bound++; } else if(s.name.startsWith('NADP')){ nadp_total++; if(filled) nadp_bound++; } else if(s.name.startsWith('ATP')){ atp_total++; if(filled) atp_bound++; } }
    self.labels = { CO2: co2_bound + '/' + co2_total, NADP: nadp_bound + '/' + nadp_total, ATP: atp_bound + '/' + atp_total }; },
  PULLING_special_actions(self, body){ },
  BINDING_special_conditions(self, body, BindSite){ if(body.is_in_group('NADP')){ if(white(slot(body, 'electron'))){ } else { return null; } } return true; },   // only NADPH counts
  BINDING_special_actions(self, BindSite){ this.update_substrate_labels(self); },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ for(const BindSite of self.BindSites){ if(dark(BindSite)) return null; } return true; },
  RELEASING_special_actions(self, released_body){
    for(const _BindSite_ of self.BindSites){ _BindSite_.modulate = 'dark'; V.env.slotEmptied(_BindSite_); } released_body.queue_free();
    V.env.glucoseMade(self);   // (no glucose model in the sheet: counted; the 2D pressed the spawn buttons for the next round)
    this.update_substrate_labels(self); },
  check_soft_target(self){ self.soft_target = self.get_node('Node'); },
};
})();
