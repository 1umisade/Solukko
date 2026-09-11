# MoleculeBody2D — Complete Logic Specification

**Purpose:** This document fully describes the behaviour of `MoleculeBody2D.gd`, the single base
class shared by *every* particle/molecule in a Godot 4.6 2D photosynthesis simulation (ProjectMPB).
It is written for an AI agent that will re-implement the **same logic** in a **Babylon.js (JavaScript)
3D** version of the simulation. It is engine-agnostic: Godot-specific APIs are explained and mapped to
generic concepts, with a dedicated translation guide at the end (§18).

> Read §1–§5 first (the mental model + data model). §6–§16 are the per-subsystem algorithms. §17 is the
> event-propagation map (critical for getting the chain reactions right). §18–§19 are the porting guide.

---

## 1. What the simulation represents (conceptual model)

It is a real-time, spatial model of the **light reactions of photosynthesis** (plus bits of the Calvin
cycle). Molecules are free-floating agents on a 2D plane. They drift, collide, and interact:

- **Photons** fly in and strike light-harvesting pigments (`chlorophyll_A`, `xanthophyll`).
- **Excitation energy** hops from pigment to pigment down an ordered antenna chain to a **reaction
  center** (`P680` in Photosystem II, `P700` in Photosystem I).
- A reaction center, once excited, **ejects a high-energy electron** into an **electron transport chain**:
  `P680 → pheophytin → plastoquinone_A → plastoquinone_B → cytochrome_b6f → plastocyanin → P700 →
  chlorophyll_A_PSI → phylloquinone → iron_sulfur_cluster → ferredoxin → FNR → NADP`.
- Water is split by the **OEC** (oxygen-evolving complex) producing O₂, protons, and replacement electrons.
- Protons accumulate and **ATP-synthase** builds ATP; **RuBisCO** consumes CO₂/NADP/ATP; etc.

**The gameplay abstraction that the code actually implements** (this is what you port — not the real
chemistry):

1. A molecule roams with a velocity until it enters the **"nearby" sensing radius** of a complex that
   can accept it. The complex then **pulls** it in (sets it a strong steering target).
2. When the pulled molecule touches the correct **binding slot**, it **binds**: it glides into the slot,
   is deleted, and the slot lights up "occupied". The molecule is now *part of* the complex.
3. A complex can later **release** a bound molecule back into the world as a fresh free agent (e.g. an
   electron handed to the next carrier in the chain).
4. **Excitation** is a separate, parallel "energy" that propagates by proximity down the same ordered
   chain, independent of physical binding.

Everything below is the machinery for pull / bind / release / excite, plus movement and cosmetics.

---

## 2. Required per-molecule structure (the "node contract")

Every molecule is a small tree of nodes. In Godot these are scene nodes; in Babylon they become a mesh
with attached child objects / metadata. **A port must reproduce these logical parts** (names are the
contract the code relies on):

```
Molecule (root, "MoleculeBody2D" = a kinematic body)
├── CollisionShape            # the solid body used for movement/collision
├── SimpleSprite              # the main visible sprite (2D quad). In 3D: the main mesh.
│   └── BindSites             # container of "slots" (may be absent for simple particles)
│       ├── <slotA>           # each slot is itself a FULL Molecule instance (recursively!)
│       ├── <slotB>           #   with its own physics DISABLED. Acts as a placeholder.
│       └── ...
├── ExcitedSprites            # container of glow/state sprites
│   ├── ExcitedSprite         # shown when the molecule carries excitation energy
│   └── DamagedSprite         # shown during photodamage (blocks excitation while visible)
├── Touch_area               # TIGHT sensor hugging the CollisionShape (contact/binding trigger)
├── Nearby_area              # LARGE sensor radius (the "pull" trigger)
├── Nearby_area_2            # optional secondary large sensor
├── LabelContainer           # optional floating text label (e.g. energy readout)
└── (sibling) Camera2D       # optional; only on the currently "followed" molecule
```

Key structural facts:

- **A "slot" (BindSite) is a complete molecule instance** nested under `SimpleSprite/BindSites`. It has
  the same node structure recursively (its own `BindSites`, `ExcitedSprites`, areas…). Its physics is
  turned **off** — it never moves on its own; it is a static placeholder living at a fixed local offset.
  A slot named `"electron"` is an electron-shaped placeholder; when "filled" it represents a bound
  electron. Slots can be named with suffixes (`plastocyanin`, `plastocyanin2`) — multiple slots for the
  same molecule type on one complex.
- Each slot **also has its own `Touch_area` and `Nearby_area`**, because slots do their own pulling and
  binding of incoming bodies.
- `molecule_name` (a string) identifies the type, e.g. `"electron"`, `"P680"`, `"cytochrome_b6f"`. It is
  **also used as a group/tag** — the molecule adds itself to a group of that name.

---

## 3. Core state variables (per molecule instance)

| Variable | Type | Meaning |
|---|---|---|
| `molecule_name` | string | Type id; also the group name. Set by each molecule's local script before `super._ready()`. |
| `speed` | float | Movement speed (units/sec). Fetched from a global config keyed `"<name>_speed"`. |
| `direction` | 2D unit vector | Current heading. Default `(0,-1)` (up). |
| `hard_target` | node or null | **Strong** steering target. If set, molecule steers hard toward it and ignores `soft_target`. Used for pulling and for electrons going to an acceptor. |
| `soft_target` | node or null | **Gentle** steering target (only used when no `hard_target`). Sets the molecule's general drift destination (e.g. an electron drifts toward the next complex). |
| `body_that_I_am_bound_to` | node or null | If this molecule is a *slot*, points to the complex it belongs to. Set to `self`'s parent complex. |
| `place_in_the_chain` | int (exported) | Ordering index for BOTH the electron transport chain AND the excitation chain. Acceptor must be `place_in_the_chain + 1`. |
| `EnergyLevel` | float | Excitation energy carried, in attojoules. Photon starts at `0.292`. Drops ×0.9 per bind transfer. |
| `pulled_bodies` | array | Bodies currently being pulled toward *this* slot (used to enforce one body per slot). |
| `list_of_bodies_that_I_am_overlapping` | array | Bookkeeping of current touch-overlaps (used to decide when a body has truly left contact). |
| `transfering_excitation` | bool | Guard: excitation transfer in progress. |
| `shaking`, `pulsating` | bool | Guards for heat-shake / shockwave animations in progress. |
| `wobble_is_running` | bool | Guard for the squish animation. |
| `last_failure_reason` | string | Last debug reason recorded (for precise diagnostics). |

**Transient per-node metadata flags** (set/cleared dynamically; treat as a per-object key→bool map):

| Flag | Meaning |
|---|---|
| `binding_ongoing` | Set on a slot and on a body while a bind animation runs (prevents double-bind). |
| `releasing_ongoing` | Set on a slot while its release conditions are being evaluated (prevents re-entrant double release — this bug once spawned two ferredoxins). |
| `exiting` | Set on a freshly released body so it isn't immediately re-bound. Cleared when it leaves a touch area. |
| `combining` | Set on two `O` atoms while they merge into an `O2`. |

---

## 4. Encoding conventions (READ CAREFULLY — these drive everything)

### 4.1 `modulate` color = occupancy/active state
`modulate` in Godot is an RGBA tint multiplied over a node and all its children. The sim overloads it as
a **state flag**:

- **`#FFFFFF` (white, opaque)** = **filled / active / present / excited-capable**. A slot tinted white is
  **occupied**. A complex tinted white is **active/alive**.
- **`#0000004D`** (black, alpha `0x4D` ≈ 30%) = **empty / darkened / inactive**. A slot tinted this is an
  **empty placeholder** waiting to be filled.

Comparisons in code use approximate equality. **In Babylon:** represent this as a per-object boolean
`occupied`/`active` state, and separately drive the material (white full-opacity vs dim ~30% alpha). Do
**not** rely on reading back a rendered color; keep an explicit state field and derive the look from it.

### 4.2 Groups / tags
`add_to_group(x)` / `is_in_group(x)` / `get_nodes_in_group(x)`. Groups used as behavioural tags include:
`"MoleculeBody2D"` (all molecules), the molecule's own `molecule_name`, plus semantic tags like
`"electron"`, `"proton"`, `"photon"`, `"boundary"`, `"membrane"`, `"O"`, `"O2"`, `"zeaxanthin"`,
`"violaxanthin"`, `"P680"`, `"P700"`, `"photosystem_I"`, `"followed"` (the camera-tracked molecule),
`"upright_label"` (labels kept unrotated), etc. **In Babylon:** a `Set<string>` of tags per object plus
a global `Map<tag, Set<object>>` registry for fast "all of group" queries.

### 4.3 Collision layers/masks (bitmask, Godot uses bits 1..32)
Bodies live on **collision layers** and scan **collision masks**. The scheme:

- **Bit 1 = "free / roaming"** layer+mask. A normally drifting molecule is on layer 1 and masks 1.
- **Bit 2 = "pulled / bound / in-transit"** layer+mask. When a molecule is being pulled or is being
  bound, it is **moved off bit 1 and onto bit 2**, so it stops colliding with free molecules while it
  travels into a slot. When it is released/leaves, it goes back to bit 1.
- `Touch_area` / `Nearby_area` use their own bits so they only detect the appropriate bodies. Specific
  complexes tweak extra bits (e.g. cytochrome/PQB share a bit so they can overlap; ferredoxin/PSI use a
  dedicated bit so ferredoxin never overlaps PSI). **In Babylon:** you don't need Godot's exact bit
  numbers — replicate the *intent*: "free" vs "in-transit" collision categories, plus per-pair overlap
  allow/deny lists (see `allow_overlap`, §15).

### 4.4 z_index
2D draw order. A bound slot raises its `z_index` above the parent so it isn't clipped; released bodies
raise above their source. **In 3D this is largely irrelevant** — ignore or map to `renderingGroupId`
only if you keep a flat 2.5D look.

---

## 5. The interaction rulebook: `possible_interactions`

A dictionary "who can bind what". A complex (key) can bind the listed molecule types (values). This gates
both pulling and binding. Reproduce it verbatim:

```
OEC                                         : [electron, H2O]
P680                                        : [electron]
P700                                        : [electron]
pheophytin                                  : [electron]
plastoquinone_A                             : [electron]
plastoquinone_B                             : [electron, proton]
photosystem_II                              : [plastoquinone_B, VDE]
cytochrome_b6f                              : [plastoquinone_B, plastocyanin]
heme                                        : [electron]
plastocyanin                                : [electron]
iron_sulfur_cluster_inside_cytochrome_b6f   : [electron]
photosystem_I                               : [plastocyanin]
chlorophyll_A_PSI                           : [electron]
phylloquinone                               : [electron]
iron_sulfur_cluster_inside_photosystem_I    : [electron]
RuBisCO                                     : [CO2, NADP, ATP]
ferredoxin                                  : [electron]
FNR                                         : [ferredoxin, NADP, electron]
NADP                                        : [electron, proton]
ATP-synthase                                : [ADP, phosphate, proton]
tyrosine                                    : [electron, O2]
Fe3+                                        : [electron]
NDH-1                                       : [ferredoxin, plastoquinone_B]
```

**Chain ordering:** `place_in_the_chain` is an integer set per molecule (in each local script / scene).
An electron/excitation may only pass to an acceptor whose `place_in_the_chain == giver.place_in_the_chain + 1`
(with a couple of documented exceptions for O2 and zeaxanthin). This is what enforces the correct
biological order without hard-coding pairs.

---

## 6. Lifecycle — `_ready()` and `_ready_call_deferred()`

`_ready()` runs once when the molecule enters the scene. In two phases (Godot's `call_deferred` runs the
second phase at end-of-frame so sibling nodes exist):

**`_ready()` actions:**
1. Add self to group `molecule_name` and group `"MoleculeBody2D"`.
2. Wire up area sensors and set them **non-detectable by other areas** (perf): 
   - `Touch_area`: on body-enter → `when_body_enters_touch_area`; on body-exit → `when_body_exits_touch_area`; then build its shape (§6.1).
   - `Nearby_area` and `Nearby_area_2`: on body-enter → `when_body_enters_nearby_area`.
   - For each child slot under `BindSites`: on slot's `Touch_area` body-enter → `when_body_enters_BindSite(slot)`; and set each slot's `body_that_I_am_bound_to = self`.
3. If a `LabelContainer` exists, add it to group `"upright_label"` (a single global manager keeps all such labels unrotated — do the same in 3D: billboard labels).
4. Allow overlap between me and my own `BindSites` subtree (so I never physically collide with my own slots — §15).
5. Fetch `speed` from global config (`"<molecule_name>_speed"`).
6. If `speed` is null → disable my per-frame physics.
7. If my parent container is named `"BindSites"` (i.e. **I AM a slot**) → disable my per-frame physics (slots are static).
8. Defer phase two.

**`_ready_call_deferred()` actions:**
1. `check_soft_target()` — molecule-specific hook that assigns an initial `soft_target` (e.g. a fresh
   plastocyanin picks the least-crowded cytochrome slot; a photon aims at a photosystem). Overridden per
   molecule; base does nothing.
2. If a camera with level-of-detail exists, trigger a LOD refresh.

### 6.1 Touch_area shape generation (`_generate_touch_area_shape`)
If the `Touch_area` has no manually-set shape, it is auto-built by copying **every** collision shape of
the body and **growing each by a constant margin** (`touch_margin = 2.0` world units) — an even "coating"
so the touch sensor is slightly larger than the solid body. Growth is per-shape-type: circle/​capsule
radius += margin; rectangle size += 2·margin; convex polygon is edge-offset. **In Babylon:** give each
molecule a slightly enlarged trigger volume around its mesh (e.g. a bounding sphere/box scaled to add a
fixed margin, or a second invisible collider).

---

## 7. Per-frame movement & collision — `_physics_process(delta)`

Runs every physics tick for free (non-slot, non-null-speed) molecules:

1. **Hard steering:** if `hard_target != null`:
   `direction = normalize( lerp(direction, normalize(hard_target.pos - my.pos), 0.5) )`
   (aggressive — half-way toward the target direction each tick).
2. **Soft steering:** else if `soft_target != null`:
   `direction = normalize( lerp(direction, normalize(soft_target.pos - my.pos), 0.025) )`
   (very gentle drift).
3. `velocity = speed * direction`.
4. **Move & collide:** move by `velocity * delta`, stopping at the first collision (kinematic sweep).
5. **Bounce rule:** if a collision occurred **and** the collider either has no `speed` or `speed <= my speed`:
   - reflect: `direction = normalize( direction.bounce(collision.normal) )`
   - back off slightly: `position -= normalize(velocity) * 2`
   - flip `rotation_direction` sign
   - if the collider is a molecule, play `wobble_once()` (cosmetic squish).
   (Faster colliders are *not* bounced off of — the slower/equal one yields.)

Rotation of the sprite itself is currently disabled (commented out).

**Babylon note:** `move_and_collide` is a *kinematic swept move that returns the first contact + normal*.
You either (a) use a physics engine in kinematic mode and read contacts, or (b) implement a simple manual
mover: predict next position, test overlap against nearby colliders, and on hit reflect the direction
about the contact normal. The behaviour is deliberately simple/arcadey (bounce like billiard balls), not
rigid-body physics.

---

## 8. The PULL system (attract free molecules to a complex)

**Trigger:** `when_body_enters_nearby_area(body)` fires when any body enters my (or a slot's) large
`Nearby_area`. It calls, in order:
`self.try_PULLING(body)`, `self.try_EXCITATION_TRANSFERRING()`, `body.try_RELEASING()`, `self.try_RELEASING()`.
If I am a slot, it also forwards the event to my parent complex.

### 8.1 `PULLING_conditions(body)` → returns a slot or null
- Body must be valid and a molecule.
- Body must **not already have a `hard_target`** (not already committed elsewhere).
- Then defer to `BINDING_conditions(body)` **with no slot argument** (see §9.1) — pulling and binding
  share the same rulebook; pulling asks "is there *any* slot on me this body could bind?".

### 8.2 `try_PULLING(body)`
- If `PULLING_conditions` returned a slot:
  1. Move the body onto the **"in-transit" collision category** (off bit 1, onto bit 2) so it stops
     colliding with free molecules while flying in.
  2. Register the body in that slot's `pulled_bodies` (no duplicates).
  3. Set `body.hard_target = slot` (strong steering pulls it in).
- Else → `repelling(body)` (§8.3).

### 8.3 `repelling(body)` (coroutine)
Pushes a body *away* if it is drifting toward a slot that is **already occupied by me**. Condition to
repel: body has a `soft_target` that is one of my (white/filled) slots and I am white/active. While the
body still overlaps that slot's nearby area, each physics frame nudge its `direction` away from me
(`lerp(dir, (body.pos - my.pos).normalized(), 0.1)`). This keeps latecomers from clustering on a full slot.

---

## 9. The BIND system (consume a molecule into a slot)

**Trigger:** `when_body_enters_BindSite(body, slot)` (a body entered a slot's tight `Touch_area`) →
`try_BINDING(body, slot)`.

### 9.1 `BINDING_conditions(body, slot = null)` → returns the slot or null
Safety checks: my `BindSites` exists; I am white/active; I am not the body's ancestor; body is a molecule.

**If `slot == null` (called by the pull path):** iterate my child slots and find the first that can pull
this body:
- The slot's own `Nearby_area` must actually overlap the body (only the slot whose sensor triggered).
- The slot must not already be pulling a *different* body (one body per slot).
- Recursively call `BINDING_conditions(body, thatSlot)`; if it passes, **return that slot**.
- If none qualify, return null (and record the precise last-failure reason).

**If `slot` is given, all of these must hold (else null):**
1. `BINDING_special_conditions(body, slot)` (per-molecule hook) returns true.
2. The body is not itself a slot (its parent isn't a `BindSites` container).
3. Both are listed in `possible_interactions` (`self` type can bind `body` type).
4. Body is not flagged `exiting`.
5. The slot is not already `binding_ongoing`.
6. The body is not already `binding_ongoing`.
7. `slot.molecule_name == body.molecule_name` (right slot for this type).
8. The slot is visible.
9. The slot is **darkened/empty** (`#0000004D`).

### 9.2 `try_BINDING(body, slot)` (coroutine — the actual bind animation)
If `BINDING_conditions` passes:
1. Set `binding_ongoing` on slot and body.
2. Disable the body's `CollisionShape` (deferred) and stop its physics.
3. **Glide loop** (each frame until close enough, while the slot is still empty):
   - Increase a `rate` toward 0.5, scaled by inverse distance, and
     `body.pos = lerp(body.pos, slot.pos, rate)`, `body.rot = lerp_angle(body.rot, slot.rot, rate)`.
   - **When** within 1 unit and <0.1 rad of the slot pose, do the "consume":
     a. For each of the body's own child slots, copy its `modulate`, its `ExcitedSprite` visibility, its
        `EnergyLevel` (electrons only), and transfer the `"followed"` tag, onto the corresponding slot
        inside *this* slot (state is copied inward — the bound molecule's internal structure is mirrored).
     b. If the body is an electron: `slot.EnergyLevel = body.EnergyLevel * 0.9` (energy drops a tenth per
        transfer); mirror its `ExcitedSprite` visibility onto the slot; play a shock-wave pulse.
     c. If the body carried the `"followed"` tag (camera), move it to the slot.
     d. **Delete the body**, set `slot.modulate = white` (now occupied), raise slot `z_index`.
   - Yield a frame.
4. After the loop: re-enable the slot's own collision shapes; set `slot.body_that_I_am_bound_to = self`.
5. **Free the slot for others:** null the `hard_target` of every other body that was pulling to this slot,
   and clear `pulled_bodies` (the slot is full now).
6. Clear `binding_ongoing` on the slot.
7. `check_soft_target()` (I may now want a new destination).
8. `BINDING_special_actions(slot)` (per-molecule hook).
9. **Cascade:** re-trigger contact/pull/release/excitation on nearby & overlapping bodies (so newly
   possible reactions fire immediately) — see §17.

---

## 10. The RELEASE system (emit a bound molecule back into the world)

**Trigger:** `try_RELEASING()` is called liberally (on nearby-area enter, after any bind, after any
release nearby, after excitation). It scans **all** of my slots and releases each one that qualifies.

### 10.1 `RELEASING_conditions(slot)` → true / an acceptor / null
- The slot must be valid and **occupied (white)**.
- **General case:** return `true`.
- **Electron slot special case** (slot name contains `"electron"`): it must find a valid **acceptor** to
  hand the electron to. Starting from all bodies overlapping my `Nearby_area`, filter down by ALL of:
  - **3B** is in group `electron`;
  - **3C** is a *slot* (its physics is disabled);
  - **3D** its parent complex exists and is white/active;
  - **3E** the acceptor slot itself is darkened/empty;
  - **3F** it isn't already being targeted (no valid entries in its `pulled_bodies`);
  - **3G** its parent's `place_in_the_chain == my place_in_the_chain + 1` (next link in the chain);
  - **3H** NOT (I am a `plastocyanin` handing to another `plastocyanin`) — plastocyanin never gives to
    plastocyanin.
  - Pick a random survivor and **return it as the acceptor**. If any filter empties the set → return null
    (with the precise reason).

### 10.2 `try_RELEASING()` (coroutine)
For each slot:
- Skip if `releasing_ongoing`; else set it (re-entrancy guard). Evaluate `RELEASING_conditions(slot)` AND
  `RELEASING_special_conditions(slotName)` (per-molecule hook, may `await`, e.g. a reaction center stays
  excited 1 s before releasing). Clear `releasing_ongoing`.
- If releasable:
  1. De-excite me (hide my `ExcitedSprite`s).
  2. Clear the slot's `pulled_bodies`; reset slot `z_index`.
  3. **Instantiate a brand-new molecule** of type `slot.molecule_name` (load its scene/prefab).
  4. Put it on the in-transit collision category.
  5. Position/rotate it at the slot's world pose; flag it `exiting`; `body_that_I_am_bound_to = null`;
     add it to the scene.
  6. **Copy state outward:** mirror each child slot's `modulate`, `ExcitedSprite` visibility, `EnergyLevel`
     (electrons), and `"followed"` tag from the slot's internal structure onto the new body's structure.
     For an electron body: `body.EnergyLevel = slot.EnergyLevel`, and move the excitation glow from slot
     to the freed electron.
  7. Transfer `"followed"` (camera) if the slot had it.
  8. **Darken the slot** (now empty) and hide its (and its sub-slots') `ExcitedSprite`s.
  9. Raise the new body's `z_index` above me; play my wobble.
  10. **Electron special:** set `body.hard_target = acceptor` and register the body in the acceptor's
      `pulled_bodies` (the freed electron flies straight to the next carrier).
  11. **Cascade:** prompt nearby bodies to `try_RELEASING` and `try_PULLING`.
  12. `body.check_soft_target()`, `RELEASING_special_actions(body)`, `body.point_direction_to_target()`.

---

## 11. Touch-area contact events

### 11.1 `when_body_enters_touch_area(body)`
Fires on tight contact. Handles many special contact behaviours **before** the generic path:
- Calls `when_body_enters_touch_area_LOCAL(body)` (per-molecule hook).
- **Photon vs boundary:** if I am a photon and I hit a `boundary`, delete me.
- If body isn't a molecule → stop.
- **Photon excites:** if the body is a `photon`, call `try_EXCITING()`.
- **O + O → O₂:** if I am `O` and the body is `O` (and neither is already `combining`), flag both
  `combining`, spawn an `O2` at their midpoint, delete both `O`s.
- Track overlap bookkeeping (`list_of_bodies_that_I_am_overlapping`).
- **Overlap exceptions:** plastoquinone_B is allowed to overlap `membrane` and other plastoquinone_B.
- **Early-out complexes:** `photosystem_I`, `ATP-synthase`, `NDH-1`+ferredoxin, `cytochrome_b6f`+plastocyanin
  return here (their binding is driven purely by slot sensors, not the complex body's touch area).
- **Release a stale hard_target:** if I'm bound/active and the incoming body's `hard_target == self`, null
  it (it has arrived).
- **Generic bind-by-contact path:** safety (not my child, not a slot, not a boundary, not myself) →
  interaction allowed (`possible_interactions`) → find one of my **darkened** slots whose name begins with
  the body's `molecule_name`; if found, move the body onto the in-transit category, raise its z, and allow
  overlap with the body's whole subtree. (The actual bind then proceeds via the slot's own sensor →
  `try_BINDING`.)

### 11.2 `when_body_exits_touch_area(body)`
- Clear the body's `exiting` flag; remove me from its overlap list.
- If the body is a boundary / still overlapping another molecule / a photon / has a `hard_target` → stop
  (don't reset it).
- Otherwise **return the body to the free collision category** (back on bit 1, off bit 2) and reset its
  `z_index` (unless it's a slot).

---

## 12. The EXCITATION system (energy propagation, independent of binding)

### 12.1 `try_EXCITING()` — become excited
Runs when a photon touches me (or when a neighbour hands me excitation). Guards: I have `ExcitedSprites`;
I am not photodamaged; I am not currently transferring; I am not shaking (losing heat). Then:
1. **Consume the photon:** for a photon overlapping my touch area — transfer its `"followed"` tag to me,
   set `my.EnergyLevel = photon.EnergyLevel`, copy that energy onto my electron sub-slots, delete the photon.
2. Reveal my next hidden `ExcitedSprite` (show the glow).
3. Cosmetics: wobble; if I'm `zeaxanthin`, also heat-shake.
4. If I was photodamaged, hide everything but `DamagedSprite` for 5 s.
5. `try_EXCITATION_TRANSFERRING()` (try to pass it on).
6. `turning_excitation_to_heat()` (start the 5 s decay timer).
7. `EXCITING_special_actions()` (per-molecule hook). Return true on success.

### 12.2 `try_EXCITATION_TRANSFERRING()` — pass energy to the next pigment
Electrons never transfer (early return). Guards: I'm not `O2`; I have `ExcitedSprites`; my `ExcitedSprite`
is visible (I *am* excited); I'm not already transferring; not photodamaged; not shaking.
**Find an acceptor** among bodies in my `Nearby_area`, filtering by ALL of:
- valid; has `place_in_the_chain`; has an `ExcitedSprites` node with at least one child (excitable); not
  shaking;
- **chain order:** `place_in_the_chain == mine + 1` **OR** it's an `O2` not in a slot **OR** it's `zeaxanthin`;
- not `violaxanthin`; its `ExcitedSprite` currently hidden (not already excited); not photodamaged;
- if it's a reaction center (`P700`/`P680`), it must **already hold an electron** in its electron slot;
- it isn't already transferring.
- **Prefer `zeaxanthin`** if any qualifies, else pick random.

Then: set `transfering_excitation = true`; wait **0.8 s** (the visible hop); if the acceptor still exists,
`await acceptor.try_EXCITING()`. On success: `acceptor.EnergyLevel = my.EnergyLevel` (energy carries over,
propagated onto the acceptor's electron sub-slots); hide my glow; transfer `"followed"` to the acceptor
**first**, then `acceptor.try_RELEASING()` (so a reaction center that just got excited immediately ejects
its electron); refresh `acceptor.check_soft_target()`; clear my transferring flag; and prompt neighbours to
transfer/heat. 

### 12.3 `turning_excitation_to_heat()` — energy decays if not passed on
Electrons early-return. Creates a **one-shot 5 s timer**; on timeout, if I still have a visible non-damage
`ExcitedSprite`: play `heat_shake_animation()`, then de-excite (hide all `ExcitedSprite`s), **reset my
`EnergyLevel` to 0** (and my electron sub-slots' to 0), and prompt neighbours to transfer/heat. This is the
"use it or lose it" rule: excitation not forwarded within 5 s is dissipated as heat.

---

## 13. `EnergyLevel` propagation summary
- A **photon** carries `EnergyLevel = 0.292` (aJ).
- On excitation, the receiver copies the giver's `EnergyLevel` (photon→antenna→…→reaction center), and
  mirrors it onto its electron sub-slots.
- On **binding** an electron into a slot, the slot's `EnergyLevel = incoming.EnergyLevel * 0.9`
  (a 10% drop per transfer down the chain).
- On **releasing** an electron, the freed electron inherits the slot's `EnergyLevel`.
- On **heat loss**, `EnergyLevel` resets to 0.
- Labels display it (e.g. `"2,92αJ"` — value ×… formatted with a comma decimal + "α" + "J"); the label is
  visible only while the `ExcitedSprite` is visible. (Label rotation is kept upright by a single global
  manager; in 3D, billboard them.)

---

## 14. Cosmetic animations (port as visual polish; not required for logic correctness)
- **`wobble_once()`** — brief elastic squish of the sprite scale (skips electrons/protons and darkened
  molecules). Guarded by `wobble_is_running`.
- **`heat_shake_animation()`** — 3 s random position jitter + fade of the excitation glow to zero, then
  hide glows; prompts neighbours afterward. Guarded by `shaking`.
- **`shock_wave_animation()`** — spawns a one-shot expanding ring effect at my position (1 s). Guarded by
  `pulsating`.
- **`_spawn_heat_wave_to(target)` / `_track_heat_wave`** — an optional screen-space heat-haze band spanning
  giver→receiver during excitation transfer (currently disabled in code).

---

## 15. Helper functions
- **`allow_overlap(a, b)`** — mutually add a collision exception so two bodies pass through each other.
  In Babylon: maintain per-pair ignore sets in your collision test.
- **`allow_overlap_with_body_and_its_descendants(body)`** — recursively exclude collisions between me and
  every molecule in `body`'s subtree (used so a complex never collides with a molecule it has accepted, or
  with its own slots).
- **`point_direction_to_target()`** — set `direction` straight at `hard_target` (else `soft_target`).
- **`get_speed_from_globals()`** — `speed = Globals["<molecule_name>_speed"]` (a central, slider-adjustable
  speed table). In Babylon: a config object keyed by type.
- **`check_soft_target()`** — **base does nothing**; overridden per molecule to choose a drift destination
  (this is where a released electron picks the next complex, a plastocyanin picks the least-crowded
  cytochrome slot, etc.).
- **`debug_info(func, reason, otherBody)`** — records `last_failure_reason` and optionally prints a precise
  failure line when a debug flag is on.

---

## 16. Per-molecule override hooks (the "special" functions)
The base class defines these as no-ops / pass-through; **each concrete molecule's own script overrides the
ones it needs**. Your port needs the same extension points (e.g. a subclass or a per-type strategy object):

| Hook | Base return | Purpose |
|---|---|---|
| `check_soft_target()` | — | Choose/refresh `soft_target` (routing). Called in `_ready` (deferred), after binding, after releasing, and after excitation transfer. |
| `BINDING_special_conditions(body, slot)` | true | Extra per-type gate before a bind is allowed. |
| `BINDING_special_actions(slot)` | — | Extra per-type effects after a successful bind. |
| `PULLING_special_actions(body)` | — | Extra per-type effects during pulling. |
| `EXCITING_special_conditions()` | true | Extra gate before excitation. |
| `EXCITING_special_actions()` | — | Extra effects after excitation. |
| `RELEASING_special_conditions(slotName)` | true | Extra gate before release; may `await` (e.g. RC stays excited 1 s). |
| `RELEASING_special_actions(body)` | — | Extra effects after release (e.g. hand the camera to the freed electron; force its glow on). |
| `when_body_enters_touch_area_LOCAL(body)` | — | Per-type contact behaviour. |

> Examples of what subclasses do with these: reaction centers (`P680`/`P700`) use
> `RELEASING_special_conditions` to wait 1 s excited before ejecting the electron, and
> `RELEASING_special_actions` to pass the camera-follow to that electron and force its glow on;
> `plastocyanin.check_soft_target()` distributes evenly across cytochrome slots; `O2.check_soft_target()`
> targets tyrosine when excited else P680; `ferredoxin` alternates between FNR and NDH-1.

---

## 17. Event-propagation map (why chain reactions work — implement this carefully)
The simulation has no central scheduler; instead, **each state change re-pokes its neighbours**, producing
cascades. The important fan-outs:

- **Body enters a Nearby_area** → `try_PULLING(body)` + `self.try_EXCITATION_TRANSFERRING()` +
  `body.try_RELEASING()` + `self.try_RELEASING()` (+ forward to parent complex if I'm a slot).
- **After a successful bind** (`try_BINDING` tail) → for overlapping bodies: re-run `when_body_enters_touch_area`,
  `when_body_enters_nearby_area`, `try_BINDING`; for nearby bodies: `try_RELEASING` + `try_EXCITATION_TRANSFERRING`.
- **After a successful release** (`try_RELEASING` tail) → nearby bodies: `try_RELEASING` + `try_PULLING`;
  and the freed body runs `check_soft_target` + `point_direction_to_target`.
- **After excitation transfer succeeds** → acceptor runs `try_RELEASING` (RC ejects electron) + neighbours
  run `try_EXCITATION_TRANSFERRING` + `turning_excitation_to_heat`.
- **On heat loss / heat-shake end** → neighbours run `try_EXCITATION_TRANSFERRING` + `turning_excitation_to_heat`.

**Re-entrancy guards are essential** (they prevent double-processing during the multi-frame coroutines):
`binding_ongoing`, `releasing_ongoing`, `combining`, `transfering_excitation`, `shaking`, `pulsating`,
`wobble_is_running`. Replicate every one.

---

## 18. Godot → Babylon.js translation guide

| Godot concept | Babylon.js equivalent / approach |
|---|---|
| `CharacterBody2D` + `move_and_collide` | A kinematic mesh you move manually each frame; detect first contact via your own overlap/raycast test (or Havok kinematic bodies reading contacts). Reflect `direction` about the contact normal for the bounce. |
| `Vector2`, `rotation` (2D) | `Vector3` on a chosen plane (e.g. XY or XZ). If you keep it planar, lock one axis. Rotation → a single Euler angle about the plane normal, or a quaternion. Consider whether "3D" means true volumetric motion or a 2.5D plane — most logic is orientation-agnostic and works in either. |
| `Area2D` (`Nearby_area`, `Touch_area`) + `body_entered`/`body_exited`/`get_overlapping_bodies`/`overlaps_body` | Trigger volumes: a large sphere (nearby) and a tight enlarged collider (touch) per molecule. Each frame compute overlaps (sphere/AABB tests or physics triggers) and diff against last frame to synthesize enter/exit events. Keep an explicit overlap set per volume. |
| `monitorable=false` (areas don't detect each other) | Simply don't test area-vs-area overlaps; only test area-vs-body. |
| Collision **layers/masks** (bit 1 free, bit 2 in-transit) | A `category` enum per body: `FREE` vs `IN_TRANSIT` (plus per-pair ignore sets). Only `FREE`↔`FREE` collide for movement; `IN_TRANSIT` bodies are steering to a slot and ignore free traffic. |
| `add_collision_exception_with` | Per-pair "ignore collision" set consulted in your mover. |
| `modulate` white vs `#0000004D` | An explicit `occupied`/`active` boolean per object; drive material `albedoColor`(white) + `alpha`(1.0) vs a dim color + `alpha≈0.3`. **Never read color back for logic — use the boolean.** |
| Groups (`add_to_group`/`is_in_group`/`get_nodes_in_group`) | Per-object `Set<string> tags` + a global `Map<string, Set<Molecule>>` registry updated on add/remove. |
| `await get_tree().process_frame` / `physics_frame` | `await nextFrame()` where `nextFrame` resolves a promise on the next `scene.onBeforeRenderObservable`. Rewrite coroutines as `async` functions, or convert them to per-object state machines advanced in the render loop. The multi-frame ones are: bind glide, repelling, heat-shake, heat-wave tracking. |
| `await create_timer(t).timeout` | `await delay(t*1000)` (a promise around `setTimeout`) — but respect pause/speed scaling if you have it. |
| `Timer` node (one-shot) | `setTimeout` or a scene-driven countdown you tick each frame (preferred, so it scales with sim speed/pause). |
| `queue_free()` | `mesh.dispose()` + remove from all registries/overlap sets. Guard every deferred access with an "is this still alive?" check (equivalent to `is_instance_valid`). |
| `load(...).instantiate()` + `add_child` to current scene | Instantiate your molecule prefab/factory by `molecule_name` and add to the scene. |
| `z_index` | Ignore in true 3D (real depth handles it); or `renderingGroupId` if 2.5D. |
| `set_deferred("disabled", …)` | Just set a boolean; Babylon has no physics-flush timing issue if you run your own mover. |
| `lerp` / `lerp_angle` / `bounce` / `.normalized()` | `Vector3.Lerp`, angle lerp (shortest-path), reflect vector about normal, `.normalize()`. |
| `Globals["<name>_speed"]` | A config map of per-type speeds. |
| Labels + `upright_label` group | Billboarded GUI/text that faces the camera; one manager updates all. |

### Coroutine rewrite pattern (important)
Several functions `await` across frames while holding a guard flag. The safe port pattern:

```js
async function tryBinding(body, slot) {
  if (!bindingConditions(body, slot)) return;
  slot.flags.binding_ongoing = true; body.flags.binding_ongoing = true;
  body.collisionEnabled = false; body.physicsActive = false;
  let rate = 0;
  while (alive(body) && slot.empty) {
    const d = Math.max(distance(body.pos, slot.pos), 1);
    rate = lerp(rate, 0.5, 0.1 / d);
    body.pos = Vector3.Lerp(body.pos, slot.pos, rate);
    body.rot = lerpAngle(body.rot, slot.rot, rate);
    if (distance(body.pos, slot.pos) < 1 && Math.abs(angleDiff(body.rot, slot.rot)) < 0.1) {
      consumeIntoSlot(body, slot);   // copy state inward, delete body, mark slot occupied
    }
    await nextFrame();
  }
  // …post-bind bookkeeping + cascade…
}
```
Because `nextFrame()`/`delay()` can outlive the objects, **re-check `alive(...)` after every await**.

---

## 19. Suggested implementation order for the port
1. **Data model & registries:** molecule object with `type/molecule_name`, `pos/rot/direction/speed`,
   `tags:Set`, `flags:{}`, `occupied/active`, `energyLevel`, `placeInChain`, `hardTarget/softTarget`,
   `bindSites:[]` (recursive), `pulledBodies:Set`; global group registry; the `possibleInteractions` map.
2. **Movement + bounce** (`_physics_process`) and steering (hard/soft).
3. **Overlap sensing** (nearby/touch volumes) with synthesized enter/exit events.
4. **Pull** (`nearby enter → try_PULLING/PULLING_conditions/repelling`).
5. **Bind** (`slot touch → try_BINDING/BINDING_conditions`) with the glide coroutine and inward state copy.
6. **Release** (`try_RELEASING/RELEASING_conditions`) incl. the electron-acceptor filter chain and outward
   state copy.
7. **Excitation** (`try_EXCITING/try_EXCITATION_TRANSFERRING/turning_excitation_to_heat`) + EnergyLevel rules.
8. **Contact specials** (photon-kill, O+O→O2, overlap exceptions, early-out complexes).
9. **The cascade re-pokes** in §17 (get these exactly right or chains stall or double-fire).
10. **Per-type override hooks** (§16) — port each concrete molecule's overrides on top of the base.
11. **Cosmetics** (wobble/heat-shake/shockwave/labels) last.

> Correctness hinges on three things: the **white/dark occupancy state**, the **place_in_the_chain + 1
> ordering rule**, and the **re-entrancy guards + neighbour re-poke cascades**. Get those right and the
> photosynthetic chain self-assembles the same way it does in the 2D version.
```
```
