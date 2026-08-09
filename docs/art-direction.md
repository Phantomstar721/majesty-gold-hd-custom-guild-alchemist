# Alchemist Art Direction

## Approved hero sources

- `assets/source/hero/portrait.png` is the approved portrait identity.
- `assets/source/hero/sprite-actions-reference.png` is the approved full-body
  longcoat design: dark green split-tail coat, cream collar, brass goggles,
  satchel, dagger, and amber/green/blue belt potions.

The reference sheet is concept art, not final animation geometry. During the
final sprite build, reconstruct every action on the stock Cultist scaffold and
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

The bottom-row state sequence is damaged, severely damaged, advanced collapse,
and destroyed. The advanced-collapse cell must retain a recognizable partial
building with standing masonry and equipment. Only the final destroyed cell may
be reduced to a flattened footprint.

The guild panel portrait represents the inside of the building, following the
stock Majesty guild-panel convention. It must show the enclosed Alchemy
Laboratory workspace—still, brewing well, shelves, herbs, and workbench—not an
exterior building view.

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
  building portrait, main-panel backing, and Brewing-panel backing.

## Stock sprite contract

The Alchemist is a private art clone of the Cultist (`AVC1`). The generator
must retain these stock TILE counts and their ordering:

- walk `3934–3997`: 8 directions × 8 frames
- stand `3998–4005`: 8 directions × 1 frame
- special `4006–4037`: 8 directions × 4 frames
- attack `4038–4069`: 8 directions × 4 frames
- cast `4070–4101`: 8 directions × 4 frames
- death/body `4102–4136`: 16 directional collapse frames followed by the
  stock shared corpse lifecycle

Majesty's eight direction slots are populated from the six authored views with
the stock Cultist mapping `(3, 2, 2, 1, 0, 5, 4, 4)`. The duplicated oblique
slots are intentional. Preserve the stock hotspots, frame order, and timing.

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

The private records are `ALC1`, `ALB1`, `ALB2`, `ALB3`, `ALTI`, and `ALBB`.
Their TILE data must be appended after the complete retail table. All earlier
TILE slots in the mod CAM are zero-length fallthrough placeholders. Starting a
private table immediately after the Cultist/Fervus source ranges would overwrite
unrelated stock art and is forbidden.
