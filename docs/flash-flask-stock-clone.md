# Flash Flask stock-clone contract

Flash Flask is composed only from existing stock Majesty lifecycles.

## Automatic combat use and timing

The action is a private clone of Paladin `shield_of_light` from retail
`Data/M_Actions.xml`. The Alchemist character advertises it through the same
single-entry `AllowedSpells` list used by Paladins, and retains stock
`SpellType Attack` dispatch. No decision-tree watcher, timer, marker, or custom
combat poll is involved.

Only the requested fields differ from Shield of Light:

- action/image set: `Special`
- required hero level: 3
- effector duration: 30,000 ms
- timeout/cooldown: 45,000 ms
- private action and GPL callback identities

## Buff lifecycle

The begin/end ordering is Shield of Light's duration-owned icon plus its
duration-0 activation effector. The selected attributes are the exact stock
Vigilance adjustment family:

- Dodge +10 / -10
- Parry +10 / -10
- Action Rate Modifier -400 / +400

The persistent icon owns `Alchemist_Flash_Flask_End`; expiration reverses the
three changes. There is no independent cleanup path.

## Art lifecycle

- Activation is a private XR30/PHe2 clone: six playable frames, attachment 2,
  duration 0, fixed 103x99 canvas, and no callback. XR30's original 50-ms
  frame delay made the complete effect last only about 300 ms. Its private
  set now uses delay zero, invoking Majesty's stock 100-ms fallback for an
  approximately 600-ms one-shot. The TILE hotspot X is 51 rather than the
  Phantom-centered 56, moving the effect five pixels right onto the Alchemist.
- The overhead Flash Flask icon is a private XR25/Chill clone. Its approved
  eight art phases are interpolated over XR25's complete 29-frame loop.
- Vigor's Heroic Spark uses a second private XR25/Chill clone. Its green
  accents orbit around the gold spark while the flame tip wavers.

All three use private IMAG and TILE records. Stock Shield of Light, Vigilance,
Chill, Eternal Soul, and Vigor/Rage resources remain unchanged.
