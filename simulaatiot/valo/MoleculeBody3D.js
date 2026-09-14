/* MoleculeBody3D - the base class every molecule of the light reactions uses.
   A port of ProjectMPB's MoleculeBody2D.gd (Godot 4.6, 2D) to the Webcyte sheet (owner 13.9.2026: 'make it resemble the
   godot logic exactly but in 3D', 'real separate files'). The functions keep the Godot names and their order, the
   per-molecule scripts (valo/scripts/<name>.js) override the same *_special_* hooks the .gd files did, and the level
   (valo/Kalvosto.js) plays the scene tree: it instantiates the bodies, moves the ones the engine moves, and runs the clock.

   What Godot gave for free and how it is played here:
     Area2D + body_entered / body_exited   -> V.Area: a sphere (radius) whose overlap set is refreshed once per frame from a
                                              spatial hash (V.Sensors), the newcomers / leavers fire the callbacks. That is what
                                              the physics server does behind the signal; nothing in JS or Babylon does it for free.
     the scene tree (BindSites children)   -> body.BindSites (array of full MoleculeBody3D with physics off), body.parent
     modulate #FFFFFF / #0000004D          -> body.modulate = 'white' | 'dark' (the level paints it)
     ExcitedSprites/ExcitedSprite.visible   -> body.ExcitedSprite.visible, body.DamagedSprite (null when the scene has none)
     groups                                 -> V.groups (add_to_group / is_in_group / get_nodes_in_group)
     collision layers 1 (free) / 2 (transit) -> body.collision_layer (Set of bits), read by the level's movers
     await timers / frames (coroutines)     -> async functions awaiting V.wait(s) / V.process_frame(), resolved by the sim clock
     queue_free / instantiate               -> V.env.dispose(body) / V.instantiate(name, ...) (the level owns sprites and models)
     move_and_collide                       -> V.env.move(body, dx, dy, dz) for the sprite bodies; the protein carriers are moved by
                                              the sheet's own movers, which read hard_target / soft_target
   Positions are [x, y, z] arrays in world units (angstrom-ish). */
(function(){
  const V = window.VALO = window.VALO || {};
  V.SCRIPTS = V.SCRIPTS || {};

  /* ── globals.gd: one slider, three size classes ── */
  V.Globals = {
    LARGE_PARTICLE_SPEED: 0.25, MIDSIZE_PARTICLE_SPEED: 1.0, SMALL_PARTICLE_SPEED: 2,
    slider_value: 30,            // (2D: 20 px/s x class; here 30 units/s x class at 1x - the sheet is bigger than the level was)
    large: ['FNR', 'RuBisCO', 'enzyme_A'],
    mid:   ['H2O', 'CO2', 'O2', 'ADP', 'ATP', 'NADP', 'RuBP', '3PGA', 'plastocyanin', 'plastoquinone_B', 'ferredoxin', 'glucose', 'substrate_X', 'substrate_Y', 'product_P', 'O', 'VDE'],
    small: ['photon', 'proton', 'phosphate', 'electron'],
    get(key){ const name = key.replace(/_speed$/, ''); const v = this.slider_value;
      if(this.large.includes(name)) return v*this.LARGE_PARTICLE_SPEED; if(this.mid.includes(name)) return v*this.MIDSIZE_PARTICLE_SPEED; if(this.small.includes(name)) return v*this.SMALL_PARTICLE_SPEED; return null; },   // null = no physics (a complex, a cofactor)
    update_body_speeds(v){ this.slider_value = v; for(const b of V.all) b.get_speed_from_globals(); } };

  /* ── groups ── */
  V.groups = new Map();
  V.all = [];   // every live body (the "MoleculeBody2D" group)
  const grp = g => { let s = V.groups.get(g); if(!s){ s = new Set(); V.groups.set(g, s); } return s; };
  V.get_nodes_in_group = g => [...grp(g)].filter(b => b.alive);
  V.pick_random = arr => arr.length ? arr[(Math.random()*arr.length)|0] : null;
  V.is_instance_valid = b => !!(b && b.alive);

  /* ── the sim clock: timers and frames for the coroutines ── */
  V.time = 0; V.frame = 0; const timers = [], frameWaiters = [];
  V.wait = s => new Promise(res => timers.push({ t: V.time + s, res }));
  V.process_frame = () => new Promise(res => frameWaiters.push(res));
  V.physics_frame = V.process_frame;
  V.tick = dt => { V.time += dt; V.frame++;
    for(let i = timers.length-1; i >= 0; i--){ if(timers[i].t <= V.time){ const t = timers[i]; timers.splice(i, 1); t.res(); } }
    const w = frameWaiters.splice(0, frameWaiters.length); for(const r of w) r(); };

  /* ── possible_interactions (verbatim) ── */
  V.possible_interactions = {
    "OEC":                                       ["electron", "H2O"],
    "P680":                                      ["electron"],
    "P700":                                      ["electron"],
    "pheophytin":                                ["electron"],
    "plastoquinone_A":                           ["electron"],
    "plastoquinone_B":                           ["electron", "proton"],
    "photosystem_II":                            ["plastoquinone_B", "VDE"],
    "cytochrome_b6f":                            ["plastoquinone_B", "plastocyanin"],
    "heme":                                      ["electron"],
    "plastocyanin":                              ["electron"],
    "iron_sulfur_cluster_inside_cytochrome_b6f": ["electron"],
    "photosystem_I":                             ["plastocyanin", "ferredoxin"],   // (3D: the ferredoxin DOCKS on PSI's stromal face; the 2D one hovered by FB and was never bound)
    "chlorophyll_A_PSI":                         ["electron"],
    "phylloquinone":                             ["electron"],
    "iron_sulfur_cluster_inside_photosystem_I":  ["electron"],
    "RuBisCO":                                   ["CO2", "NADP", "ATP"],
    "ferredoxin":                                ["electron"],
    "FNR":                                       ["ferredoxin", "NADP", "electron"],
    "NADP":                                      ["electron", "proton"],
    "ATP-synthase":                              ["ADP", "phosphate", "proton"],
    "tyrosine":                                  ["electron", "O2"],
    "Fe3+":                                      ["electron"],
    "NDH-1":                                     ["ferredoxin", "plastoquinone_B"],
    "chlorophyll_A":                             ["electron"],   // (3D: the accessory chlorophyll ChlD1 relays P680 -> PheoD1 in the structure)
  };

  /* ── Area2D ── a sphere around a body (or a slot). monitorable = false: areas never detect areas, only bodies.
     The overlap set is kept in two halves: the STATIC bodies (recomputed only when the static hash is refreshed) and the MOVING ones
     (every frame), so a static area's per-frame work is a query against the few moving bodies. */
  class Area { constructor(owner, radius, name){ this.owner = owner; this.radius = radius; this.name = name; this._static = new Set(); this._dyn = new Set(); this.body_entered = []; this.body_exited = []; this.monitorable = false; this.enabled = true; V.areas.push(this); }
    get overlapping(){ const s = new Set(this._static); for(const b of this._dyn) s.add(b); return s; }
    get_overlapping_bodies(){ const out = []; for(const b of this._static) if(b.alive) out.push(b); for(const b of this._dyn) if(b.alive) out.push(b); return out; }
    overlaps_body(b){ return this._static.has(b) || this._dyn.has(b); }
    connect(sig, fn){ (sig === 'body_entered' ? this.body_entered : this.body_exited).push(fn); }
    _diff(set, now){ for(const b of now) if(!set.has(b)){ set.add(b); for(const f of this.body_entered) f(b); }
      for(const b of [...set]) if(!now.has(b) || !b.alive){ set.delete(b); for(const f of this.body_exited) f(b); } } }
  V.Area = Area; V.areas = [];

  /* ── the sensors: Godot's physics server, in sixty lines. Every frame the MOVING bodies go into a spatial hash and every area asks it;
     the STATIC bodies (cofactors and slots of complexes that stand still) are hashed once and a static area's static overlaps are cached,
     refreshed every couple of seconds (a dragged model) - 1600 areas against 800 bodies every frame cost 13 ms, this costs one. ── */
  V.Sensors = { cell: 64, staticT: 0, STATIC_REFRESH: 30.0, staticDirty: false, _sgrid: null, _pos: new Map(),   // the static hash is rebuilt every 30 s of sim time, or when the level says a model was dragged (staticDirty)
    _key: (i, j, k) => ((i + 4096) * 8192 + (j + 4096)) * 8192 + (k + 4096),
    _grid(bodies){ const cell = this.cell, grid = new Map(), pos = this._pos; for(const b of bodies){ const p = pos.get(b); const kk = this._key(Math.floor(p[0]/cell), Math.floor(p[1]/cell), Math.floor(p[2]/cell)); let l = grid.get(kk); if(!l){ l = []; grid.set(kk, l); } l.push(b); } grid.all = bodies; return grid; },
    _query(grid, a, c, into){ const cell = this.cell, r = a.radius, pos = this._pos; const i0 = Math.floor((c[0]-r)/cell), i1 = Math.floor((c[0]+r)/cell), j0 = Math.floor((c[1]-r)/cell), j1 = Math.floor((c[1]+r)/cell), k0 = Math.floor((c[2]-r)/cell), k1 = Math.floor((c[2]+r)/cell);
      const test = b => { if(b === a.owner) return; const p = pos.get(b); const dx = p[0]-c[0], dy = p[1]-c[1], dz = p[2]-c[2]; const rr = r + b.body_radius; if(dx*dx+dy*dy+dz*dz <= rr*rr) into.add(b); };
      if((i1-i0+1)*(j1-j0+1)*(k1-k0+1) > 64 || grid.all.length < 64){ for(const b of grid.all) test(b); return; }   // a wide area (a water pull of 400) or a short list: just walk the bodies
      for(let i=i0;i<=i1;i++) for(let j=j0;j<=j1;j++) for(let k=k0;k<=k1;k++){ const l = grid.get(this._key(i, j, k)); if(!l) continue; for(const b of l) test(b); } },
    /* perf (14.9.2026): 1650 areas each querying the moving bodies' grid was 1770 grid walks a frame (2 ms, plus a Set spread per area in
       _diff). INVERTED for the static-owner areas (nine in ten): the static areas are hashed once per refresh (their owners stand still),
       and each frame the ~90 MOVING bodies look up the areas of their own cell - a few thousand tests - and the areas with no hit and no
       previous overlap are not touched at all. Areas on moving owners keep the old per-area query. */
    _hit(a, b, p, hits){ if(!a.enabled || b === a.owner || !a.owner.alive) return; const c = this._pos.get(a.owner); if(!c) return; const dx = p[0]-c[0], dy = p[1]-c[1], dz = p[2]-c[2], rr = a.radius + b.body_radius; if(dx*dx+dy*dy+dz*dz > rr*rr) return; let s = hits.get(a); if(!s){ s = new Set(); hits.set(a, s); } s.add(b); },
    _areaGrid(){ const grid = new Map(), wide = [], cell = this.cell, M = 40; let n = 0;   // M: the largest moving body's radius - an area is entered into every cell its sphere plus M covers, so a point lookup at the body's centre is enough
      for(const a of V.areas){ if(!a.owner.is_static || !a.owner.alive) continue; n++; const c = this._pos.get(a.owner); if(!c) continue; const r = a.radius + M;
        const i0 = Math.floor((c[0]-r)/cell), i1 = Math.floor((c[0]+r)/cell), j0 = Math.floor((c[1]-r)/cell), j1 = Math.floor((c[1]+r)/cell), k0 = Math.floor((c[2]-r)/cell), k1 = Math.floor((c[2]+r)/cell);
        if((i1-i0+1)*(j1-j0+1)*(k1-k0+1) > 512){ wide.push(a); continue; }   // a wide area (a 400-unit pull) is simply tested against every moving body
        for(let i=i0;i<=i1;i++) for(let j=j0;j<=j1;j++) for(let k=k0;k<=k1;k++){ const kk = this._key(i, j, k); let l = grid.get(kk); if(!l){ l = []; grid.set(kk, l); } l.push(a); } }
      return { grid, wide, n, areas: V.areas.length }; },
    update(dt){ const pos = this._pos; pos.clear(); const dyn = [], stat = [];
      for(const b of V.all){ if(!b.alive) continue; pos.set(b, b.global_position); if(!b.has_collision) continue; (b.is_static ? stat : dyn).push(b); }
      this.staticT += dt || 0; const refresh = !this._sgrid || this.staticDirty || this.staticT >= this.STATIC_REFRESH; if(refresh){ this.staticT = 0; this.staticDirty = false; this._sgrid = this._grid(stat); this._agrid = null; }
      const dgrid = this._grid(dyn), now = new Set(), cell = this.cell;
      if(!this._agrid || this._agrid.areas !== V.areas.length) this._agrid = this._areaGrid();
      const ag = this._agrid, hits = this._hits || (this._hits = new Map()); hits.clear();
      for(const b of dyn){ const p = pos.get(b); const l = ag.grid.get(this._key(Math.floor(p[0]/cell), Math.floor(p[1]/cell), Math.floor(p[2]/cell))); if(l) for(const a of l) this._hit(a, b, p, hits); for(const a of ag.wide) this._hit(a, b, p, hits); }
      const EMPTY = this._empty || (this._empty = new Set());
      for(const a of V.areas){ if(!a.owner.alive) continue;
        if(!a.owner.is_static){ if(!a.enabled) continue; const c = pos.get(a.owner); if(!c) continue;   // a moving owner: its areas ask both grids every frame
          now.clear(); this._query(this._sgrid, a, c, now); a._diff(a._static, now);
          now.clear(); this._query(dgrid, a, c, now); a._diff(a._dyn, now); continue; }
        if(!a.enabled) continue;   // (as before: a disabled area keeps what it had until it is enabled again)
        if(refresh){ const c = pos.get(a.owner); if(c){ now.clear(); this._query(this._sgrid, a, c, now); a._diff(a._static, now); } }   // the static half: once per refresh
        const h = hits.get(a); if(h) a._diff(a._dyn, h); else if(a._dyn.size) a._diff(a._dyn, EMPTY); } } };

  /* ── MoleculeBody3D ── */
  let seq = 0;
  class MoleculeBody3D {
    constructor(molecule_name, opts){ opts = opts || {};
      this.id = seq++; this.alive = true; this.molecule_name = molecule_name; this.name = opts.name || molecule_name;   // node name (a slot can be 'electron_2', 'plastoquinone_B_LUMENAL' ...)
      this.script = V.SCRIPTS[molecule_name] || V.SCRIPTS.TEMPLATE; this.scene = this.script.scene || {};
      this.parent = opts.parent || null; this.parent_is_BindSites = !!opts.slot;   // get_parent().name == "BindSites"
      this.groups = new Set(); this.meta = {}; this.visible = true; this.modulate = opts.slot ? 'dark' : 'white';
      this.speed = 0.0; this.direction = [0, -1, 0]; this.velocity = [0, 0, 0]; this.rotation_direction = 0;
      this.hard_target = null; this.soft_target = null; this.body_that_I_am_bound_to = null;
      this.place_in_the_chain = opts.place != null ? opts.place : (this.scene.place != null ? this.scene.place : 0); this.lane = opts.lane || null;   // (lane: a 3D addition, see releasing 3G)
      this.EnergyLevel = 0.0; this._heatSeq = 0; this.namedChildren = new Map(); this.transfering_excitation = false; this.shaking = false; this.pulsating = false; this.wobble_is_running = false; this.last_failure_reason = '';
      this.pulled_bodies = []; this.list_of_bodies_that_I_am_overlapping = []; this.collision_layer = new Set([1]); this.collision_exceptions = new Set();
      this.physics_processing = true; this.has_collision = true; this.is_static = false; this.body_radius = opts.radius != null ? opts.radius : (this.scene.radius != null ? this.scene.radius : 2);
      this._pos = opts.position ? opts.position.slice() : [0, 0, 0]; this.local_offset = opts.local || [0, 0, 0]; this.frame = opts.frame || null;   // frame: { mi, p } - a point in a model's frame (follows the model)
      this.ExcitedSprites = this.scene.excitable ? [{ visible: false }] : []; this.ExcitedSprite = this.ExcitedSprites[0] || null; this.DamagedSprite = this.scene.damageable ? { visible: false } : null;
      this.touch_area = new Area(this, this.body_radius + MoleculeBody3D.touch_margin, 'Touch_area');
      this.nearby_area = (opts.nearby != null || this.scene.nearby != null) ? new Area(this, opts.nearby != null ? opts.nearby : this.scene.nearby, 'Nearby_area') : null;
      this.nearby_area_2 = (opts.nearby2 != null || this.scene.nearby2 != null) ? new Area(this, opts.nearby2 != null ? opts.nearby2 : this.scene.nearby2, 'Nearby_area_2') : null;
      this.BindSites = null; const bs = opts.BindSites || this.scene.BindSites;
      if(bs){ this.BindSites = []; for(const spec of bs){ const o = typeof spec === 'string' ? { name: spec } : spec; const type = o.type || o.name.replace(/_LUMENAL2?$|_STROMAL2?$|_\d+$|_2$/, '');
          const slot = new MoleculeBody3D(type, { name: o.name, parent: this, slot: true, local: o.local || [0, 0, 0], place: o.place, lane: o.lane || this.lane, nearby: o.nearby != null ? o.nearby : (V.SCRIPTS[type] && V.SCRIPTS[type].scene && V.SCRIPTS[type].scene.slot_nearby) || MoleculeBody3D.slot_nearby, radius: o.radius });
          this.BindSites.push(slot); } }
      V.all.push(this); this._ready(); }

    /* the scene tree */
    get_parent(){ return this.parent ? { name: this.parent_is_BindSites ? 'BindSites' : this.parent.name, node: this.parent } : null; }
    get_children(){ return this.BindSites ? this.BindSites.slice() : []; }
    is_ancestor_of(b){ let p = b && b.parent; while(p){ if(p === this) return true; p = p.parent; } return false; }
    get_node(path){ if(path === 'Nearby_area') return this.nearby_area; if(path === 'Touch_area') return this.touch_area; if(path === 'Nearby_area_2') return this.nearby_area_2;
      const m = path.match(/^(?:SimpleSprite\/)?BindSites\/([^/]+)(?:\/(.*))?$/); if(m){ const s = this.BindSites && this.BindSites.find(x => x.name === m[1]); if(!s) return null; return m[2] ? s.get_node(m[2]) : s; }
      if(path === 'ExcitedSprites/ExcitedSprite') return this.ExcitedSprite; if(path === 'ExcitedSprites/DamagedSprite') return this.DamagedSprite;
      if(this.namedChildren.has(path)) return this.namedChildren.get(path); return null; }   // (a complex's child molecules - P680, OEC, target points - by their node name)
    get_node_or_null(path){ return this.get_node(path); }
    has_node(path){ return !!this.get_node(path); }
    get global_position(){ if(this.frame){ return V.env.frameWorld(this.frame.mi, this.frame.p, [0, 0, 0]); }
      if(this.parent){ const p = this.parent.global_position; return [p[0] + this.local_offset[0], p[1] + this.local_offset[1], p[2] + this.local_offset[2]]; } return this._pos.slice(); }
    set global_position(p){ if(this.parent || this.frame){ return; } this._pos[0] = p[0]; this._pos[1] = p[1]; this._pos[2] = p[2]; }
    get position(){ return this.global_position; } set position(p){ this.global_position = p; }
    global_position_to(out){ const p = this.global_position; out[0] = p[0]; out[1] = p[1]; out[2] = p[2]; return out; }
    distance_to(b){ const a = this.global_position, c = b.global_position; return Math.hypot(a[0]-c[0], a[1]-c[1], a[2]-c[2]); }

    /* groups, meta, layers */
    add_to_group(g){ this.groups.add(g); grp(g).add(this); } remove_from_group(g){ this.groups.delete(g); grp(g).delete(this); } is_in_group(g){ return this.groups.has(g); }
    get_meta(k, d){ return k in this.meta ? this.meta[k] : d; } set_meta(k, v){ this.meta[k] = v; } has_meta(k){ return k in this.meta; } remove_meta(k){ delete this.meta[k]; }
    set_collision_layer_value(bit, on){ if(on) this.collision_layer.add(bit); else this.collision_layer.delete(bit); } set_collision_mask_value(){ }
    get_collision_layer_value(bit){ return this.collision_layer.has(bit); }
    set_physics_process(on){ this.physics_processing = on; } is_physics_processing(){ return this.physics_processing; }
    get(k){ return this[k]; } has_method(m){ return typeof this[m] === 'function'; }
    queue_free(){ if(!this.alive) return; this.alive = false; for(const g of [...this.groups]) grp(g).delete(this); if(this.BindSites) for(const s of this.BindSites) s.queue_free();
      const i = V.all.indexOf(this); if(i >= 0) V.all.splice(i, 1); for(const a of [this.touch_area, this.nearby_area, this.nearby_area_2]) if(a){ const j = V.areas.indexOf(a); if(j >= 0) V.areas.splice(j, 1); }
      for(const b of V.all){ const k = b.pulled_bodies.indexOf(this); if(k >= 0) b.pulled_bodies.splice(k, 1); }
      V.env.dispose(this); }
    add_child(){ } create_tween(){ return null; }

    /* ── _ready (the very first frame) ── */
    _ready(){
      this.add_to_group(this.molecule_name); this.add_to_group('MoleculeBody3D');
      if(this.touch_area){ this.touch_area.monitorable = false; this.touch_area.connect('body_entered', b => this.when_body_enters_touch_area(b)); this.touch_area.connect('body_exited', b => this.when_body_exits_touch_area(b)); }
      if(this.nearby_area){ this.nearby_area.monitorable = false; this.nearby_area.connect('body_entered', b => this.when_body_enters_nearby_area(b)); }
      if(this.nearby_area_2){ this.nearby_area_2.monitorable = false; this.nearby_area_2.connect('body_entered', b => this.when_body_enters_nearby_area(b)); }
      if(this.BindSites) for(const BindSite of this.BindSites){ BindSite.touch_area.connect('body_entered', b => this.when_body_enters_BindSite(b, BindSite)); BindSite.body_that_I_am_bound_to = this; }
      this.allow_overlap_with_body_and_its_descendants(this);
      if(this.script._ready) this.script._ready(this);
      this.get_speed_from_globals();
      if(this.speed == null) this.set_physics_process(false);
      if(this.parent_is_BindSites) this.set_physics_process(false);
      Promise.resolve().then(() => this._ready_call_deferred()); }
    _ready_call_deferred(){ if(!this.alive) return; this.check_soft_target(); }

    /* ── _physics_process: steering. Moving is the level's (the sprite bodies fly, the protein carriers ride the sheet's movers) ── */
    _physics_process(delta){
      /* 3D (14.9.2026): 'exiting' used to be cleared only by the sensors' exit event from the slot the body left - with the sensors running every
         other frame a fast electron was already outside when first seen, no exit ever fired, and it sat 'exiting' at its target for good
         (BINDING refuses an exiting body). Cleared here too, once the body is clear of the slot it left. */
      if(this._exitFrom){ const f = this._exitFrom, t = this.hard_target; if(!V.is_instance_valid(f) || !f.touch_area || this.distance_to(f) > f.touch_area.radius + this.body_radius + 1 || (t && t !== f && V.is_instance_valid(t) && this.distance_to(t) < 3)){ this._exitFrom = null; if(this.get_meta('exiting', false)) this.remove_meta('exiting'); } }   // (...or once it has reached the slot pulling it, even inside the old one's reach - neighbouring cofactors overlap)
      if(this.hard_target != null && V.is_instance_valid(this.hard_target)) this.direction = V.lerpDir(this.direction, V.dirTo(this.global_position, this.hard_target.global_position), 0.5);
      if(this.soft_target != null && this.hard_target == null && V.is_instance_valid(this.soft_target)) this.direction = V.lerpDir(this.direction, V.dirTo(this.global_position, this.soft_target.global_position), 0.025);
      this.velocity = [this.speed*this.direction[0], this.speed*this.direction[1], this.speed*this.direction[2]];
      let step = 1.0;   // (3D: a frame at 3x is 0.15 s - a pulled electron would jump 9 units past a slot whose touch reaches 4 and oscillate across it for ever; Godot's 60 Hz tick was 0.7 px. Never overshoot the hard target.)
      if(this.hard_target != null && V.is_instance_valid(this.hard_target)){ const d = this.distance_to(this.hard_target), l = this.speed*delta; if(l > d && d > 0) step = d/l; }
      const collision = V.env.move(this, this.velocity[0]*delta*step, this.velocity[1]*delta*step, this.velocity[2]*delta*step);
      /* (3D) Godot's bodies jostle, so a body sitting on a slot keeps re-entering its areas and the signals keep coming; here a carrier
         glides to the slot and sits dead still, so once a second a body in reach of its target is poked the way the signals would:
         pulled and touching -> try_BINDING; heading there unpulled and touching -> try_PULLING (a slot that was taken may be free now) */
      this._pokeT = (this._pokeT || 0) + delta;
      if(this._pokeT > 1.0){ this._pokeT = 0; const t = this.hard_target || this.soft_target;
        if(t instanceof MoleculeBody3D && t.parent_is_BindSites && t.body_that_I_am_bound_to && t.touch_area.overlaps_body(this) && !this.get_meta('binding_ongoing', false)){
          if(this.hard_target === t) t.body_that_I_am_bound_to.try_BINDING(this, t); else t.body_that_I_am_bound_to.try_PULLING(this); } }
      if(collision != null && (collision.collider == null || collision.collider.speed == null || collision.collider.speed <= this.speed)){
        this.direction = V.normalize(V.bounce(this.direction, collision.normal)); this.rotation_direction = -this.rotation_direction;
        if(collision.collider instanceof MoleculeBody3D) this.wobble_once(); } }

    /* ══ PULLING ══ */
    when_body_enters_nearby_area(body){
      if(body instanceof MoleculeBody3D){ this.try_PULLING(body); this.try_EXCITATION_TRANSFERRING(); body.try_RELEASING(); this.try_RELEASING();
        if(this.parent_is_BindSites && this.body_that_I_am_bound_to) this.body_that_I_am_bound_to.when_body_enters_nearby_area(body); } }
    PULLING_conditions(body){
      if(!V.is_instance_valid(body)){ this.debug_info('PULLING_conditions', 'body is not valid'); return null; }
      if(!(body instanceof MoleculeBody3D)){ return null; }
      if(body.hard_target != null){ this.debug_info('PULLING_conditions', 'body already has a hard_target', body); return null; }
      return this.BINDING_conditions(body); }
    try_PULLING(body){ const r = this.PULLING_conditions(body);
      if(r instanceof MoleculeBody3D){ const BindSite = r;
        body.set_collision_layer_value(1, false); body.set_collision_mask_value(1, false); body.set_collision_layer_value(2, true); body.set_collision_mask_value(2, true);
        if(!BindSite.pulled_bodies.includes(body)) BindSite.pulled_bodies.push(body);
        body.hard_target = BindSite; if(this.script.PULLING_special_actions) this.script.PULLING_special_actions(this, body); }
      else this.repelling(body); }
    async repelling(body){
      if(body instanceof MoleculeBody3D && body.soft_target instanceof MoleculeBody3D && body.soft_target.body_that_I_am_bound_to === this && body.soft_target.modulate === 'white' && this.modulate === 'white'){
        while(V.is_instance_valid(body) && body.soft_target && body.soft_target.nearby_area && body.soft_target.nearby_area.overlaps_body(body)){
          body.direction = V.lerpDir(body.direction, V.dirTo(this.global_position, body.global_position), 0.1); await V.physics_frame(); } } }

    /* ══ BINDING ══ */
    BINDING_conditions(body, BindSite){ if(BindSite === undefined) BindSite = null; const fn = 'BINDING_conditions';
      if(!this.BindSites){ this.debug_info(fn, 'no BindSites'); return null; }
      if(this.modulate !== 'white'){ this.debug_info(fn, 'I am not active (dark)'); return null; }
      if(this.is_ancestor_of(body)){ this.debug_info(fn, 'body is my descendant', body); return null; }
      if(!(body instanceof MoleculeBody3D)) return null;
      if(BindSite == null){
        for(const my_BindSite of this.BindSites){ const slot_nearby = my_BindSite.nearby_area; if(slot_nearby == null || !slot_nearby.overlaps_body(body)) continue;
          if(my_BindSite.pulled_bodies.some(b => V.is_instance_valid(b) && b !== body)) continue;
          const r = this.BINDING_conditions(body, my_BindSite); if(r instanceof MoleculeBody3D) return my_BindSite; }
        this.debug_info(fn, 'no BindSite of mine can take it', body); return null; }
      if(this.script.BINDING_special_conditions && this.script.BINDING_special_conditions(this, body, BindSite) !== true){ this.debug_info(fn, 'BINDING_special_conditions', body); return null; }
      if(!(body.parent == null || !body.parent_is_BindSites)){ this.debug_info(fn, 'body is a BindSite', body); return null; }
      const pi = V.possible_interactions[this.molecule_name]; if(!(pi && pi.includes(body.molecule_name))){ this.debug_info(fn, 'not in possible_interactions', body); return null; }
      if(body.get_meta('exiting', false)){ this.debug_info(fn, 'body is exiting', body); return null; }
      if(BindSite.get_meta('binding_ongoing', false)){ this.debug_info(fn, 'BindSite binding_ongoing', body); return null; }
      if(body.get_meta('binding_ongoing', false)){ this.debug_info(fn, 'body binding_ongoing', body); return null; }
      if(BindSite.molecule_name !== body.molecule_name){ this.debug_info(fn, 'wrong BindSite for this type', body); return null; }
      if(!BindSite.visible){ this.debug_info(fn, 'BindSite hidden', body); return null; }
      if(BindSite.modulate !== 'dark'){ this.debug_info(fn, 'BindSite already filled', body); return null; }
      return BindSite; }
    async try_BINDING(body, BindSite){ const r = this.BINDING_conditions(body, BindSite);
      if(r instanceof MoleculeBody3D){
        BindSite.set_meta('binding_ongoing', true); body.set_meta('binding_ongoing', true);
        body.has_collision = false; body.set_physics_process(false);
        let rate = 0.0;
        while(V.is_instance_valid(body) && BindSite.modulate === 'dark'){
          const bp = body.global_position, sp = BindSite.global_position; const distance = Math.max(Math.hypot(bp[0]-sp[0], bp[1]-sp[1], bp[2]-sp[2]), 1.0);
          rate = rate + (0.5 - rate)*(0.1/distance);
          body.global_position = [bp[0] + (sp[0]-bp[0])*rate, bp[1] + (sp[1]-bp[1])*rate, bp[2] + (sp[2]-bp[2])*rate];
          const np = body.global_position;
          if(Math.hypot(np[0]-sp[0], np[1]-sp[1], np[2]-sp[2]) < 1 || (rate > 0.45 && Math.hypot(np[0]-sp[0], np[1]-sp[1], np[2]-sp[2]) < 12)){   // (3D 14.9.2026: a slot on a MOVING host - FNR is a loose protein - runs ahead of the glide, which closes half the gap a frame: at 3x speed the gap settled at 5-10 units and the ferredoxin never bound - so once the glide is at full rate, 12 units (under a ferredoxin's radius) is close enough)
            if(body.BindSites) for(const item of body.BindSites){ const dest = BindSite.get_node('BindSites/' + item.name); if(!dest) continue;
              dest.modulate = item.modulate; if(item.ExcitedSprite && dest.ExcitedSprite) dest.ExcitedSprite.visible = item.ExcitedSprite.visible;
              if(item.is_in_group('electron')) dest.EnergyLevel = item.EnergyLevel;
              if(item.is_in_group('followed')){ item.remove_from_group('followed'); dest.add_to_group('followed'); } }
            if(body.is_in_group('electron')){ BindSite.EnergyLevel = body.EnergyLevel*0.9; if(BindSite.ExcitedSprite) BindSite.ExcitedSprite.visible = !!(body.ExcitedSprite && body.ExcitedSprite.visible); BindSite.shock_wave_animation(); }
            if(body.is_in_group('followed')){ BindSite.add_to_group('followed'); body.remove_from_group('followed'); }
            V.env.consumed(body, BindSite);   // (3D: a protein carrier is not freed but parked in the slot - the level keeps its model there until the slot releases)
            body.queue_free(); BindSite.modulate = 'white'; }
          await V.process_frame(); }
        BindSite.body_that_I_am_bound_to = this;
        for(const pulled_body of BindSite.pulled_bodies) if(V.is_instance_valid(pulled_body)) pulled_body.hard_target = null;
        BindSite.pulled_bodies.length = 0; BindSite.remove_meta('binding_ongoing');
        this.check_soft_target();
        if(this.script.BINDING_special_actions) this.script.BINDING_special_actions(this, BindSite);
        for(const ob of BindSite.touch_area.get_overlapping_bodies()) if(ob instanceof MoleculeBody3D) ob.when_body_enters_touch_area(ob);
        if(BindSite.nearby_area) for(const ob of BindSite.nearby_area.get_overlapping_bodies()) BindSite.when_body_enters_nearby_area(ob);
        for(const ob of this.touch_area.get_overlapping_bodies()){ if(!(ob instanceof MoleculeBody3D) || !ob.BindSites) continue; const s = ob.get_node('BindSites/' + this.molecule_name); if(s && s.touch_area.overlaps_body(this)) ob.try_BINDING(this, s); }
        if(this.nearby_area) for(const nb of this.nearby_area.get_overlapping_bodies()) if(nb instanceof MoleculeBody3D){ nb.try_RELEASING(); nb.try_EXCITATION_TRANSFERRING(); } } }

    /* ══ RELEASING ══ */
    RELEASING_conditions(BindSite){ const fn = 'RELEASING_conditions';
      if(!V.is_instance_valid(BindSite)) return null;
      if(BindSite.modulate !== 'white'){ this.debug_info(fn, 'BindSite empty'); return null; }
      if(String(BindSite.name).includes('electron')){
        let nb = this.nearby_area ? this.nearby_area.get_overlapping_bodies() : [];
        nb = nb.filter(item => item.is_in_group('electron'));                                   if(!nb.length){ this.debug_info(fn, '3B no electron slot nearby'); return null; }
        nb = nb.filter(item => item.is_physics_processing() === false);                          if(!nb.length){ this.debug_info(fn, '3C none is a slot'); return null; }
        nb = nb.filter(item => item.body_that_I_am_bound_to != null && item.body_that_I_am_bound_to.modulate === 'white'); if(!nb.length){ this.debug_info(fn, '3D no active parent'); return null; }
        nb = nb.filter(item => item.modulate === 'dark');                                        if(!nb.length){ this.debug_info(fn, '3E none empty'); return null; }
        nb = nb.filter(item => !item.pulled_bodies.some(b => V.is_instance_valid(b)));           if(!nb.length){ this.debug_info(fn, '3F all targeted'); return null; }
        nb = nb.filter(item => item.body_that_I_am_bound_to.place_in_the_chain === this.place_in_the_chain + 1); if(!nb.length){ this.debug_info(fn, '3G none is the next link'); return null; }
        nb = nb.filter(item => V.laneOk(this, item.body_that_I_am_bound_to));                    if(!nb.length){ this.debug_info(fn, '3G2 wrong lane (3D)'); return null; }
        nb = nb.filter(item => !(this.molecule_name === 'plastocyanin' && item.body_that_I_am_bound_to.molecule_name === 'plastocyanin')); if(!nb.length){ this.debug_info(fn, '3H plastocyanin to plastocyanin'); return null; }
        return V.pick_random(nb); }
      return true; }
    async try_RELEASING(){ if(!this.BindSites || !this.alive) return;
      for(const BindSite of this.BindSites){ if(BindSite.has_meta('releasing_ongoing')) continue;
        BindSite.set_meta('releasing_ongoing', true);
        const R = this.RELEASING_conditions(BindSite);
        const can_release = R != null && (this.script.RELEASING_special_conditions ? (await this.script.RELEASING_special_conditions(this, String(BindSite.name), R)) === true : true);
        BindSite.remove_meta('releasing_ongoing');
        if(!this.alive || !BindSite.alive) return;
        if(can_release && BindSite.modulate === 'white'){
          for(const es of this.ExcitedSprites) es.visible = false;
          BindSite.pulled_bodies.length = 0;
          const released_body = V.instantiate(BindSite.molecule_name, { position: BindSite.global_position, from_slot: BindSite });
          if(!released_body) continue;
          released_body.set_collision_layer_value(1, false); released_body.set_collision_mask_value(1, false); released_body.set_collision_layer_value(2, true); released_body.set_collision_mask_value(2, true);
          released_body.set_meta('exiting', true); released_body.body_that_I_am_bound_to = null; released_body._exitFrom = BindSite;   // (3D: the slot it leaves - see _physics_process, the 'exiting' flag is also cleared by distance)
          if(released_body.BindSites) for(const item of released_body.BindSites){ const source = BindSite.get_node('BindSites/' + item.name); if(!source) continue;
            item.modulate = source.modulate; if(item.ExcitedSprite && source.ExcitedSprite) item.ExcitedSprite.visible = source.ExcitedSprite.visible;
            if(item.is_in_group('electron')) item.EnergyLevel = source.EnergyLevel;
            if(source.is_in_group('followed')){ source.remove_from_group('followed'); item.add_to_group('followed'); } }
          if(released_body.is_in_group('electron')){ released_body.EnergyLevel = BindSite.EnergyLevel;
            if(BindSite.ExcitedSprite && BindSite.ExcitedSprite.visible){ BindSite.ExcitedSprite.visible = false; if(released_body.ExcitedSprite) released_body.ExcitedSprite.visible = true; } else if(released_body.ExcitedSprite) released_body.ExcitedSprite.visible = false; }
          if(BindSite.is_in_group('followed')){ released_body.add_to_group('followed'); BindSite.remove_from_group('followed'); }
          BindSite.modulate = 'dark'; if(BindSite.ExcitedSprite) BindSite.ExcitedSprite.visible = false;
          if(BindSite.BindSites) for(const s of BindSite.BindSites){ s.modulate = 'dark'; if(s.ExcitedSprite) s.ExcitedSprite.visible = false; }
          if(this.speed != null && this.modulate === 'white') this.wobble_once();
          if(released_body.is_in_group('electron') && R instanceof MoleculeBody3D){ released_body.hard_target = R; R.pulled_bodies.push(released_body); }
          if(this.nearby_area) for(const nb of this.nearby_area.get_overlapping_bodies()) if(nb instanceof MoleculeBody3D){ nb.try_RELEASING(); this.try_PULLING(nb); }
          released_body.check_soft_target();
          if(this.script.RELEASING_special_actions) this.script.RELEASING_special_actions(this, released_body);
          released_body.point_direction_to_target(); } } }

    /* ══ TOUCH ══ */
    when_body_enters_touch_area(body){ const fn = 'when_body_enters_touch_area';
      if(this.script.when_body_enters_touch_area_LOCAL) this.script.when_body_enters_touch_area_LOCAL(this, body);
      if(this.is_in_group('photon') && body.is_in_group && body.is_in_group('boundary')) this.queue_free();
      if(!(body instanceof MoleculeBody3D)) return;
      if(body.is_in_group('photon')) this.try_EXCITING();
      if(this.is_in_group('O') && body.is_in_group('O') && body !== this && !this.get_meta('combining', false) && !body.get_meta('combining', false)){
        this.set_meta('combining', true); body.set_meta('combining', true); const a = this.global_position, b = body.global_position;
        V.instantiate('O2', { position: [(a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2] }); body.queue_free(); this.queue_free(); return; }
      if(!this.is_ancestor_of(body) && !body.is_ancestor_of(this) && body !== this) body.list_of_bodies_that_I_am_overlapping.push(this);
      if(this.is_in_group('plastoquinone_B') && body.is_in_group('membrane')) this.allow_overlap(this, body);
      if(this.is_in_group('plastoquinone_B') && body.is_in_group('plastoquinone_B')) this.allow_overlap(this, body);
      if(this.is_in_group('photosystem_I')) return;
      if(this.is_in_group('ATP-synthase')) return;
      if(this.is_in_group('NDH-1') && body.is_in_group('ferredoxin')) return;
      if(this.is_in_group('cytochrome_b6f') && body.is_in_group('plastocyanin')) return;
      if(this.body_that_I_am_bound_to != null && this.modulate === 'white' && body.hard_target === this) body.hard_target = null;
      if(this.is_ancestor_of(body)) return;
      if(body.parent != null && body.parent_is_BindSites) return;
      if(body.is_in_group('boundary')) return;
      if(body === this) return;
      const pi = V.possible_interactions[this.molecule_name]; if(!(pi && pi.includes(body.molecule_name))) return;
      if(!this.BindSites) return;
      let BindSite = null; for(const c of this.BindSites){ if(!c.name.startsWith(body.molecule_name)) continue; if(c.modulate !== 'dark') continue; BindSite = c; break; }
      if(BindSite == null){ this.debug_info(fn, 'no free BindSite', body); return; }
      body.set_collision_layer_value(1, false); body.set_collision_mask_value(1, false); body.set_collision_layer_value(2, true); body.set_collision_mask_value(2, true);
      this.allow_overlap_with_body_and_its_descendants(body); }
    when_body_exits_touch_area(body){
      body.remove_meta('exiting');
      if(body.list_of_bodies_that_I_am_overlapping){ const i = body.list_of_bodies_that_I_am_overlapping.indexOf(this); if(i >= 0) body.list_of_bodies_that_I_am_overlapping.splice(i, 1); }
      if(!(body instanceof MoleculeBody3D)) return;
      if(body.is_in_group('boundary')) return;
      for(const item of body.list_of_bodies_that_I_am_overlapping) if(item !== this) return;
      if(body.is_in_group('photon')) return;
      if(body.hard_target != null) return;
      body.set_collision_layer_value(1, true); body.set_collision_mask_value(1, true); body.set_collision_layer_value(2, false); body.set_collision_mask_value(2, false); }

    /* ══ EXCITATION ══ */
    async try_EXCITING(){ const fn = 'try_EXCITING';
      if(!this.ExcitedSprites.length){ this.debug_info(fn, 'not excitable'); return false; }
      if(this.DamagedSprite != null && this.DamagedSprite.visible){ this.debug_info(fn, 'photodamaged'); return false; }
      if(this.transfering_excitation){ this.debug_info(fn, 'transferring'); return false; }
      if(this.shaking){ this.debug_info(fn, 'shaking'); return false; }
      if(this.script.EXCITING_special_conditions && this.script.EXCITING_special_conditions(this) !== true) return false;
      for(const body of this.touch_area.get_overlapping_bodies()){ if(body.is_in_group('photon')){
        if(body.is_in_group('followed')){ body.remove_from_group('followed'); this.add_to_group('followed'); }
        this.EnergyLevel = body.EnergyLevel; if(this.BindSites) for(const slot of this.BindSites) if(slot.is_in_group('electron')) slot.EnergyLevel = this.EnergyLevel;
        body.queue_free(); break; } }
      for(const es of this.ExcitedSprites) if(!es.visible){ es.visible = true; break; }
      this.wobble_once();
      if(this.is_in_group('zeaxanthin')) this.heat_shake_animation();
      if(this.DamagedSprite != null && this.DamagedSprite.visible){ for(const es of this.ExcitedSprites) es.visible = false; this.DamagedSprite.visible = true; await V.wait(5.0); if(this.alive) this.DamagedSprite.visible = false; }
      this.try_EXCITATION_TRANSFERRING(); this.turning_excitation_to_heat();
      if(this.script.EXCITING_special_actions) this.script.EXCITING_special_actions(this);
      return true; }
    async try_EXCITATION_TRANSFERRING(){ const fn = 'try_EXCITATION_TRANSFERRING';
      if(this.is_in_group('electron')) return;
      if(this.is_in_group('O2')) return;
      if(!this.ExcitedSprites.length) return;
      if(!this.ExcitedSprite.visible){ this.debug_info(fn, 'not excited'); return; }
      if(this.transfering_excitation) return;
      if(this.DamagedSprite != null && this.DamagedSprite.visible) return;
      if(this.shaking) return;
      let excitation_acceptor = null;
      { let f = this.nearby_area ? this.nearby_area.get_overlapping_bodies().filter(i => V.is_instance_valid(i)) : []; if(!f.length){ this.debug_info(fn, 'nobody nearby'); return; }
        f = f.filter(i => i.place_in_the_chain != null);                                          if(!f.length) return;
        f = f.filter(i => i.ExcitedSprites && i.ExcitedSprites.length);                            if(!f.length){ this.debug_info(fn, 'nobody excitable nearby'); return; }
        f = f.filter(i => !i.shaking);                                                             if(!f.length) return;
        f = f.filter(i => V.excitationStep(this, i) || (i.is_in_group('O2') && !i.parent_is_BindSites) || i.is_in_group('zeaxanthin')); if(!f.length){ this.debug_info(fn, 'no next link nearby'); return; }
        f = f.filter(i => !i.is_in_group('violaxanthin'));                                        if(!f.length) return;
        f = f.filter(i => !i.ExcitedSprite.visible);                                               if(!f.length){ this.debug_info(fn, 'all excited already'); return; }
        f = f.filter(i => i.DamagedSprite == null || !i.DamagedSprite.visible);                    if(!f.length) return;
        f = f.filter(i => !(i.is_in_group('P700') || i.is_in_group('P680')) || (i.get_node('BindSites/electron') && i.get_node('BindSites/electron').modulate === 'white')); if(!f.length){ this.debug_info(fn, 'the centre is closed'); return; }
        f = f.filter(i => !i.transfering_excitation);                                              if(!f.length) return;
        const zea = f.filter(i => i.is_in_group('zeaxanthin'));
        if(zea.length && V.zeaxanthinQuenches(this, f)) excitation_acceptor = V.pick_random(zea); else excitation_acceptor = V.pickExcitationAcceptor(f.filter(i => !i.is_in_group('zeaxanthin')).length ? f.filter(i => !i.is_in_group('zeaxanthin')) : f); }
      this.transfering_excitation = true;
      await V.wait(V.HOP);
      if(V.is_instance_valid(excitation_acceptor) && this.alive){
        const success = await excitation_acceptor.try_EXCITING();
        if(success){
          excitation_acceptor.EnergyLevel = this.EnergyLevel; if(excitation_acceptor.BindSites) for(const slot of excitation_acceptor.BindSites) if(slot.is_in_group('electron')) slot.EnergyLevel = excitation_acceptor.EnergyLevel;
          for(const es of this.ExcitedSprites) es.visible = false;
          if(this.is_in_group('followed')){ this.remove_from_group('followed'); excitation_acceptor.add_to_group('followed'); }
          excitation_acceptor.try_RELEASING();
          excitation_acceptor.check_soft_target();
          this.transfering_excitation = false;
          if(this.nearby_area) for(const nb of this.nearby_area.get_overlapping_bodies()) if(nb.has_method('try_EXCITATION_TRANSFERRING')){ nb.try_EXCITATION_TRANSFERRING(); nb.turning_excitation_to_heat(); }
          return; } }
      this.transfering_excitation = false; }
    turning_excitation_to_heat(){
      if(this.is_in_group('electron')) return;
      const my = ++this._heatSeq;
      V.wait(V.HEAT_S).then(async () => { if(!this.alive || this._heatSeq !== my) return;
        for(const es of this.ExcitedSprites){ if(es.visible && es !== this.DamagedSprite){
          await this.heat_shake_animation(); if(!this.alive) return;
          for(const es2 of this.ExcitedSprites) es2.visible = false; this.EnergyLevel = 0.0;
          if(this.BindSites) for(const slot of this.BindSites) if(slot.is_in_group('electron')) slot.EnergyLevel = 0.0;
          if(this.is_in_group('followed')) V.env.followLost(this);
          if(this.nearby_area) for(const nb of this.nearby_area.get_overlapping_bodies()) if(nb.has_method('try_EXCITATION_TRANSFERRING')){ nb.try_EXCITATION_TRANSFERRING(); nb.turning_excitation_to_heat(); } break; } } }); }
    async heat_shake_animation(){
      if(this.is_in_group('O2')) return; if(this.shaking) return;
      this.shaking = true; V.env.heat(this); let t = V.HEAT_SHAKE_S; while(t > 0.0 && this.alive){ t -= V.dt; await V.process_frame(); }
      if(!this.alive) return; this.pulsating = false; this.shaking = false;
      for(const es of this.ExcitedSprites) es.visible = false;
      if(this.nearby_area) for(const nb of this.nearby_area.get_overlapping_bodies()) if(nb.has_method('try_EXCITATION_TRANSFERRING')){ nb.try_EXCITATION_TRANSFERRING(); nb.turning_excitation_to_heat(); } }
    async shock_wave_animation(){ if(this.shaking || this.pulsating || !this.ExcitedSprite || !this.ExcitedSprite.visible) return; this.pulsating = true; V.env.shockWave(this); await V.wait(1.0); this.pulsating = false; }
    when_body_enters_BindSite(body, BindSite){ this.try_BINDING(body, BindSite); BindSite._lastEnter = { body: body.molecule_name + '#' + body.id, fail: this.last_failure_reason, t: V.time }; }   // (dev: what the last body to touch this BindSite ran into)

    /* ── helpers ── */
    allow_overlap(a, b){ a.collision_exceptions.add(b); b.collision_exceptions.add(a); }
    allow_overlap_with_body_and_its_descendants(body){ if(!V.is_instance_valid(body)) return; if(body instanceof MoleculeBody3D && body !== this) this.allow_overlap(this, body); if(body.BindSites) for(const c of body.BindSites){ this.allow_overlap(this, c); this.allow_overlap_with_body_and_its_descendants(c); } }
    point_direction_to_target(){ const t = (this.hard_target && V.is_instance_valid(this.hard_target)) ? this.hard_target : this.soft_target; if(t && V.is_instance_valid(t)) this.direction = V.dirTo(this.global_position, t.global_position); }
    get_speed_from_globals(){ if(this.molecule_name != null) this.speed = V.Globals.get(this.molecule_name + '_speed'); }
    check_soft_target(){ if(this.script.check_soft_target) this.script.check_soft_target(this); }
    debug_info(fn, reason, other){ this.last_failure_reason = String(reason); if(V.debug || V['debug_func_' + fn]) console.log(V.frame + ' | ' + this.molecule_name + ' | ' + this.id + ' | ' + fn + '(): FAILED | ' + (other && other.molecule_name ? 'body: ' + other.molecule_name + ' | ' : '') + 'Failure reason: ' + reason); }
    async wobble_once(){ await V.physics_frame(); if(this.wobble_is_running || this.modulate === 'dark' || this.is_in_group('electron') || this.is_in_group('proton')) return; this.wobble_is_running = true; V.env.wobble(this); await V.wait(1.08); this.wobble_is_running = false; }
  }
  MoleculeBody3D.touch_margin = 2.0;   // the touch sensor coats the solid body by this much (2D: 2.0 world units)
  MoleculeBody3D.slot_nearby = 45;     // a BindSite's own pulling radius when its type's scene gives none
  V.MoleculeBody3D = MoleculeBody3D;

  /* ── tuning (the 2D constants, and what the sheet's size asked for) ── */
  V.HOP = 0.15;          // s per excitation hop (2D: 0.8 s over six pigments; PSI's antenna is up to eight hops deep)
  V.HEAT_S = 5.0;        // s until an unforwarded excitation is heat (2D)
  V.HEAT_SHAKE_S = 0.6;  // s of shaking before the glow is gone (2D: 3 s of sprite jitter)
  V.dt = 0;

  /* ── the two 3D additions to the chain rules ── */
  V.laneOk = (giver, taker) => { const a = giver.lane, b = taker.lane; return !a || !b || b === a || b.startsWith(a + '.'); };   // four b6f monomers and two PSII centres share one sheet: place_in_the_chain counts within a lane
  V.excitationStep = (from, to) => to.place_in_the_chain != null && to.place_in_the_chain > from.place_in_the_chain && from.psId === to.psId;   // 2D: exactly place + 1. With 260 pigments per centre that queued every exciton through three pigments; any neighbour nearer the centre will do
  V.pickExcitationAcceptor = f => { let best = -Infinity; for(const i of f) if(i.place_in_the_chain > best) best = i.place_in_the_chain; const top = f.filter(i => i.place_in_the_chain === best); return V.pick_random(top); };   // ... and the innermost of them
  V.zeaxanthinQuenches = (from, f) => { const rc = from.rcBody; return !rc || (rc.get_node('BindSites/electron') && rc.get_node('BindSites/electron').modulate !== 'white') || !f.some(i => !i.is_in_group('zeaxanthin')); };   // zeaxanthin is preferred only while the centre is closed (2D: always - with fifty carotenoids that ate half the photons)

  /* ── vector helpers ── */
  V.normalize = v => { const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0]/l, v[1]/l, v[2]/l]; };
  V.dirTo = (a, b) => V.normalize([b[0]-a[0], b[1]-a[1], b[2]-a[2]]);
  V.lerpDir = (d, t, k) => V.normalize([d[0] + (t[0]-d[0])*k, d[1] + (t[1]-d[1])*k, d[2] + (t[2]-d[2])*k]);
  V.bounce = (d, n) => { const k = 2*(d[0]*n[0] + d[1]*n[1] + d[2]*n[2]); return [d[0] - k*n[0], d[1] - k*n[1], d[2] - k*n[2]]; };

  /* ── instantiate: the level builds the body (a sprite for an electron / oxygen, a parked model for a carrier, a free instance for water ...) ── */
  V.instantiate = (name, opts) => V.env.instantiate(name, opts || {});
  V.env = { frameWorld: (mi, p, out) => { out[0] = p[0]; out[1] = p[1]; out[2] = p[2]; return out; }, move: () => null, dispose: () => {}, consumed: () => {}, instantiate: () => null, heat: () => {}, shockWave: () => {}, wobble: () => {}, followLost: () => {} };
  V.SCRIPTS.TEMPLATE = V.SCRIPTS.TEMPLATE || { scene: {} };
  V.slot = (self, name) => self.get_node('BindSites/' + name);
  V.white = b => !!b && b.modulate === 'white'; V.dark = b => !!b && b.modulate === 'dark';
})();
