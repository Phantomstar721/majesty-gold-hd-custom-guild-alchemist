# Miasma Mist stock-clone contract

Miasma Mist is the Alchemist's level-8 area-control spell. Its implementation
is a private composition of stock Meteor Storm and Phantoms Haunt's Endless
Winter/Empowered Chill paths; it does not introduce a second scheduler or a
new area-controller mechanism.

## Action and target gate

- Action image set: stock `Cast`.
- Character level: `8`.
- Cooldown: `60000` game milliseconds.
- Cast range: the Alchemist's existing `castingrange` (`130`), exactly the same
  range used by Stun Serum.
- Buildings and lairs are rejected both before casting and again on impact.
- The expensive cast reuses the Alchemist combat-consumable threat boundary:
  the private literal clone of stock `list_eval` must score the current fight
  below `1`. This is the same established test that prevents combat flasks
  from being spent on trivial incidental enemies.

Stun Serum remains the higher-ranked combat-opening spell, so it resolves
before Miasma Mist when both are available.

## Area lifecycle

The private cloud unit copies the Endless Winter/Meteor Storm contract:

- lifetime: `21000` game milliseconds;
- radius: `175` world units;
- immediate pulse on creation;
- subsequent pulses: the spell unit's engine-owned `ActiveScript` every
  `1600` game milliseconds;
- target-following sample: every `25` game milliseconds;
- tracking detaches under the same Endless Winter conditions (dead or housed
  target, native speed trail, or a single movement jump beyond the full
  radius), after which the cloud remains at its last valid location.

Every pulse compiles enemies in the stock radius and launches a private,
invisible Meteor Storm-shaped missile at each eligible non-structure target.

## Damage and debuff

Each missile deals fixed `1` spell damage. Stock poison uses a ten-count poison
counter and removes one hit point per native poison interval, so this is one
native poison tick per Miasma pulse—not ten poison damage on every pulse.

Surviving targets receive one non-stacking, refreshable ten-second debuff:

- Dodge `-10`;
- Parry `-10`;
- `MovementRateModifier +100`;
- `ActionRateModifier +1000`.

The rate penalties are the exact Empowered Chill values. Repeated cloud pulses
reset the remaining duration to `10000` without applying the four adjustments
again. Expiry reverses those exact deltas and removes the private overhead
icon. The refresh/cleanup ownership is the established Phantom Chill lifecycle
named by the design, rather than a second Alchemist-specific timing scheme.

## Private presentation

The package preserves the complete stock topology and changes only private IDs
and art references:

- `AMm1`: orange/copper translucent cloud on the Meteor Storm/Endless Winter
  rotating fixed-footprint scaffold;
- `AMm2`: invisible Meteor Storm-shaped pulse missile;
- `AMm4`: private orange vapor attachment;
- `AMm5`: animated orange liquid-drop overhead debuff icon, cloned on the stock
  poison-icon topology;
- `AMm6`: transparent spell-unit anchor.

Source masters live under
`assets/source/spells/miasma-mist/`. The generated cloud rotates its internal
vapor bands while preserving a fixed outer footprint, avoiding the pulse and
size-jump failures seen in earlier effect experiments.

