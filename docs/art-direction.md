# Alchemist Art Direction

## Approved hero sources

- `assets/source/hero/portrait.png` is the approved portrait identity.
- `assets/source/hero/sprite-actions-reference.png` is the approved full-body
  longcoat design: dark green split-tail coat, cream collar, brass goggles,
  satchel, dagger, and amber/green/blue belt potions.

The reference sheet is concept art, not final animation geometry. During the
final sprite build, reconstruct every action on the stock Warrior scaffold and
fit it to the stock directional TILE metrics.

### Mandatory dagger correction

The dagger pose in the approved reference sheet holds the weapon incorrectly.
The final attack sprites must use a conventional forward grip: fingers closed
around the handle, thumb supporting the grip, and the blade projecting from the
thumb/index-finger side of the fist. Do not copy the reference sheet's reversed
or awkward wrist/blade relationship.

The dagger is always in the Alchemist's anatomical right hand in every neutral,
walk, and attack direction. In the authored six-view sheets this means the
southeast/front-three-quarter attack places the weapon on image-left, while the
northwest/rear-three-quarter neutral, walk, and attack views place it on
image-right. Never mirror a whole pose without correcting handedness afterward.
In the northwest neutral and walk views, show the back of the right glove and
its knuckles. The blade must leave the thumb/index side in a conventional
forward grip; it may not project from the pinky side as a reversed grip.
The northwest cast view must face upper-left and keep its potion in the same
anatomical right hand; it must not duplicate the northeast view.

## Approved building progression

- `assets/source/buildings/lab/level-1/profile.png` is the clean, modest brew
  house with a single-level work shed.
- `assets/source/buildings/lab/level-2/profile.png` is the structural upgrade,
  adding a full tower story and two-level distillery wing.
- `assets/source/buildings/lab/level-3/profile.png` is the prestige upgrade,
  adding the roof cupola and flask weather vane, geared octagonal brewing well,
  and one showcase copper-and-glass distiller without excessive bottle clutter.

Building production must follow the Phantoms Haunt TILE and shadow pipeline:
author each state independently, fit the native canvas, reserve palette indices
247–250 for engine shadow controls, and encode visible and shadow RLE segments
separately.

Upgrade construction is additive. Level 2 construction begins with the finished
Level 1 building still standing and erects the second story/gallery around it.
Level 3 construction begins with the finished Level 2 building still standing
and adds the cupola, showcase distiller, upgraded well, and roof refinements.
Only initial Level 1 construction starts from an empty foundation.
The inherited stone tower remains anchored at the far-left side of the footprint
in both Level 3 construction frames. It must not jump toward the center between
early construction, late construction, and completion.

The bottom-row state sequence is damaged, severely damaged, advanced collapse,
and destroyed. The advanced-collapse cell must retain a recognizable partial
building with standing masonry and equipment. Only the final destroyed cell may
be reduced to a flattened footprint.

The guild panel portrait represents the inside of the building, following the
stock Majesty guild-panel convention. It must show the enclosed Alchemy
Laboratory workspace, not an exterior building view. Focus the portrait on the
long workbench: formula book, mortar and pestle, balance, bowls, hand tools,
ingredients, and compact glass retorts. Do not reproduce the exterior's large
showcase distiller or potion well inside the portrait.

## Production source set

The approved production masters are deliberately larger than the in-game
sprites. `scripts/generate_alchemist_art.py` fits them to the stock geometry;
do not resize the masters by hand.

- `assets/source/hero/directionals.png` supplies the neutral six-view identity.
- `walk-directionals.png`, `attack-directionals.png`,
  `cast-directionals.png`, and `death-directionals.png` supply action-specific
  six-view keys. The attack sheet is the corrected forward-grip dagger pose.
- Each `assets/source/buildings/lab/level-N/states.png` is a 4-by-2 state sheet:
  inactive, active, early construction, late construction, damaged, severely
  damaged, collapsed, and destroyed.
- `assets/source/interface/` contains the building icon, Brewing button icon,
  Weapon Oil research icon, Vigor icon, building portrait, main-panel backing,
  and Brewing-panel backing. The Lab and Weapon Oil icons use a medium green
  field so their copper silhouettes survive the final 25-pixel reduction.

## Stock sprite contract

The Alchemist is a private art clone of the Warrior (`AVL1`). The generator
must retain these stock TILE counts and their ordering:

- walk `5919–5982`: 8 directions × 8 frames
- stand `5983–5990`: 8 directions × 1 frame
- special/cast `5991–6019`: the Warrior's shared, direction-specific frame
  pool with its original repeated-frame sequencing
- death/body `6020–6051`, then dead tile `6052`: the Warrior's directional
  collapse-and-hold lifecycle
- attack `6055–6118`: 8 directions × 8 frames

Stock Warrior movement slots are ordered north, northeast, east, southeast,
south, southwest, west, northwest. This is verified from live movement; do not
rename the slots from the apparent facing of decoded frames in isolation.
Neutral and single-pose action slots are populated from the six authored views
with mapping `(3, 4, 4, 5, 0, 1, 2, 2)`. Walking is the exception: stock Warrior Walk has
eight distinct headings, so `assets/source/hero/walk-cycles-engine/` owns one
literal strip for each heading. Each strip has exactly eight poses and is
packaged in that stock engine order without mirroring. Frames are extracted as
complete alpha components rather than equal-width cells; several approved
sheets cross their nominal eighths. Every Walk frame is scaled and anchored to
the matching stock Warrior Walk TILE's per-frame body height and hotspot
geometry. This preserves the stock gait's stable head line and footfall instead
of applying the Phantom's hovering Stand-height normalization to a grounded
hero.
Preserve stock hotspots, frame order, timing, opposing arm swing, and the
anatomical right-hand dagger.

## Lighting, shadows, seams, and CAM isolation

Majesty lights objects from the viewer's upper-right. Texture highlights belong
on upper/right-facing materials, with ordinary self-shadow toward the lower
left. Do not paint a ground shadow into the visible texture. The generator
creates the projected upper-left shadow as a separate engine shadow segment.

For indexed TILE v3 art, indices 1–246 are visible colors, 247 is the seam
control color `(156, 33, 24)`, and 248–250 are the three projected-shadow
controls. Every building state and hero frame is encoded with independent
visible and shadow RLE streams. Keep the validated transparent top and side
gutters; seam pixels may only occupy the validated footprint.

Grounded hero shadows use stock Warrior Walk/Stand TILEs `5919–5990` as the
contact reference and the sibling Phantoms Haunt
[shadow contract](../../majesty-gold-hd-custom-guild-phantoms-haunt/docs/majesty-building-shadow-encoding.md)
and
[`add_cast_shadow`](../../majesty-gold-hd-custom-guild-phantoms-haunt/scripts/generate_phantom_building_sprites.py)
for the base anchor, index-247 contact seam, 248–250 bands, and literal gap
repair. The full contact contract is pinned to Phantoms commit
`1ac887f55e4c1c67dc8d90829cb099eea87b15ae`. Never reuse Phantoms'
`projected_floating_hero_shadow` as a complete algorithm for a grounded
unit: its `-3/-3` displacement and body-clearance pass intentionally detach the
shadow to communicate hovering. Every Alchemist frame must have an index-247
seam touching its lowest six body rows, with no transparent or magenta-only
contact between the body and projected bands.

The private records are `ALC1`, `ALB1`, `ALB2`, `ALB3`, `ALTI`, and `ALBB`.
Their TILE data must be appended after the complete retail table. All earlier
TILE slots in the mod CAM are zero-length fallthrough placeholders. Starting a
private table immediately after the Warrior/Fervus source ranges would overwrite
unrelated stock art and is forbidden.
