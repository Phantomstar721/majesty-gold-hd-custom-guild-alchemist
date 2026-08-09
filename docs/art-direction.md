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
