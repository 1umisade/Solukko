/* proton - transcribed from ProjectMPB/Project/Scenes/Level_7_scenes_and_scripts/proton.gd (Godot). See valo/MoleculeBody3D.js. */
(function(){ const V = window.VALO; const white = V.white, dark = V.dark, slot = V.slot;
V.SCRIPTS['proton'] = {
  scene: { radius: 1.2 },
  _ready(self){ },                                             // molecule_name = 'proton'; super._ready()
  PULLING_special_actions(self, body){ },                        // Nothing here.
  BINDING_special_conditions(self, body, BindSite){ return true; },
  BINDING_special_actions(self, BindSite){ },
  RELEASING_special_conditions(self, BindSite_name_string, acceptor){ return true; },
  RELEASING_special_actions(self, released_body){ },
  check_soft_target(self){
    if(self.body_that_I_am_bound_to != null) return;
    const below = self.global_position[1] < V.env.membraneY(self.global_position[0], self.global_position[2]);   // (2D: y grows downward; here the lumen is BELOW the membrane)
    if(!below){ const roll = Math.floor(Math.random()*4); let t = null;
      if(roll === 0){ const c = V.pick_random(V.get_nodes_in_group('cytochrome_b6f')); t = c && V.pick_random(c.BindSites.filter(b => b.name.includes('plastoquinone_B_STROMAL'))); }
      else if(roll === 1){ const p = V.pick_random(V.get_nodes_in_group('photosystem_II')); t = p && V.pick_random(p.BindSites.filter(b => b.name.includes('plastoquinone_B'))); }
      else if(roll === 2){ const n = V.pick_random(V.get_nodes_in_group('NDH-1')); t = n && V.pick_random(n.BindSites.filter(b => b.name.includes('plastoquinone_B'))); }
      else { const f = V.pick_random(V.get_nodes_in_group('FNR')); t = f && V.pick_random(f.BindSites.filter(b => b.name.includes('NADP'))); }
      self.soft_target = t || null; }
    else { const a = V.pick_random(V.get_nodes_in_group('ATP-synthase')); self.soft_target = a ? V.pick_random(a.BindSites.filter(b => b.name.includes('proton'))) || null : null; } },
};
})();
