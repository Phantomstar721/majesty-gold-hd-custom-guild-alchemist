# Phoenix Phial stock-clone contract

Phoenix Phial combines only traced Majesty mechanisms. Its two custom seams are
the user-approved 75-percent lethal-event success roll and the dispatch between
those stock lifecycles.

## Research

The second CGBR row is the same complete APa1 Arrows compound research control
used by Weapon Oil, privatized as command `0x2A16`. This
keeps both Laboratory research bars byte-for-byte identical in width, internal
hit geometry, disabled state, and native dispatch. The runtime descriptor also
starts from APa1 Arrows, changes its required-level field to 2, and copies only
APa3 Teleportation Amulets' `ResearchPowerfulItem` completion attribute.

Its icon and price window retain the same APa1 derived-ID contract as Weapon
Oil. The separate stock price control is cloned to `(151,90,40,17)` with ID
`0x2A16 + 1000`; this lets the unchanged native presenter render the private
descriptor price inside the normal gold-cost window.

The private Phoenix descriptor changes Arrows' `+0x08` base-price field to
750 gold. Native research
continues to own validation, displayed cost, treasury payment, timestamp and
duration creation, completion attributes, the one-time completed state, and
the green alert. The dedicated Laboratory owner documented in
`weapon-oil-stock-clone.md` holds the stock-created tuple so Phoenix research
does not occupy AP10 recruitment's activity channel. The progress display is
the already-proven AP24 display pair fed with that untouched stock timing. The
completion alert substitutes `Phoenix Phial` only for the private descriptor.

## Purchase and ownership

`Phoenix_Phial_Check` is a private Market3/Teleportation Amulet purchase clone:

- one inventory item at a time, tested through `AgentHasInventoryItem`;
- 1,000-gold affordability and purchase price;
- the stock Intelligence roll;
- researched Laboratories selected through `ResearchPowerfulItem`;
- loyalty-aware closest-building selection;
- ordinary `Use_Building` travel and occupancy;
- the stock Market3 visit duration, payment, exit, and task reset.

The item itself follows the SDK `SpecialItemsExample`: a named
`IsInventoryItem` unit description created with `CreateNewInventoryItem`. It is
non-droppable because the lethal path consumes it before ordinary item-drop
processing.

Its visual contract is also stock. `PXF1Phoenix Phial` is a private clone of
retail/SDK `AVk4Res Item`, retaining the complete Inactive, Minimap, and
Interface animation-set structure while redirecting all nine referenced TILEs
to private Phoenix bottle art. The unit's `ImageIDBase` is `PXF1`, so the
ordinary hero inventory UI—not a custom marker—shows that the hero carries a
Phial. Creation, ownership checks, and deletion all use the explicit numeric
`#PhoenixPhial` ID 113, following the proven Phantom equipment route; this is
the integer the native Items renderer uses to index QITM. Its native
inventory-text entry is therefore private QITM slot 113 and displays
`Phoenix Phial` with a short note describing its 75-percent resurrection
chance. The Alchemist and Phantom packages both preserve this slot so CAM load
order cannot blank the item text. The CGBR research glyph separately clones the exact APa1 icon control
used by Weapon Oil and points it at private `ALPI` art.

## Death, resurrection, and escape

The package overrides the global `gravestone` symbol, which is therefore a CAM
merger symbol. With no Phial, or after the 25-percent failure roll, its body is
the literal stock `gravestone` lifecycle.

With a Phial, the item is deleted before the roll, so both success and failure
consume the single charge. Success performs Healer rebirth's dead-state setup
at the hero's current location and creates a private clone of Agrela's
`resurrection_effector`. `Shared_Begin_Resurrect` and
`Shared_End_Resurrect` retain ownership of death-flag clearing, dead-script
termination, hero-type restoration, action reset, and active-script restart.

The private completion callback then sets HP to 25 percent and calls stock
`Flee` with stock `#intent_flee_lowHP`. This matters because Speed Tonic and
Invisibility Brew both use `Flee_Check`, which accepts only the stock scared
and low-HP flee intents. The former generic `#Intent_Flee` argument made both
potions unavailable immediately after revival. Stock `Flee` chooses the hero's
home or a safe inn, uses the
normal safe-building travel path, and already contains the desired exception:
a hero near a threatened home fights instead. With nowhere safe to flee, stock
behavior makes the hero stand and fight.

### Private Phoenix resurrection art

The original private descriptor changed the callback identity but accidentally
left `ImageIDBase="HRC1"`, so it could only display stock Healer/Agrela
resurrection art. No committed private Phoenix animation existed.

The first repair incorrectly composed Agrela's full 1500-ms callback owner with
a separate duration-0 Eternal Soul presenter. In game, the short Phoenix ended
while the underlying resurrection animation continued, exposing stock HRC1 art
for the rest of the revival. That two-owner composition is forbidden.

The corrected art uses one literal stock resurrection owner. Private `PXE1`
retains Agrela resurrection's set-64, 29-frame, 1500-ms table,
`Resurrection` sound, `Phoenix_Phial_Resurrection_End` callback, attachment
point 2, flags, and ordering. All 29 HRC1 frame references are redirected to 29
distinct private Phoenix TILEs. There is no second visual effector.

Every Phoenix TILE uses Eternal Soul's proven fixed 103 by 99 canvas, attachment
point 2, and stock fireball palette 505. Its private hotspot is `(56,49)`: the
PHe2 anchor raised by the six pixels confirmed in the death-site test. Eternal
Soul's initialization, smooth growth, peak pulse, reduction, and fade function
is sampled across HRC1 slots 0 through 14. Live testing established that filling
HRC1's complete 29-slot table left Phoenix art visible after stock
`Shared_End_Resurrect` restored movement, so slots 15 through 28 remain in the
literal table but point to private transparent TILEs. No callback timing,
owner, or cleanup behavior is changed.

The package validator requires PXE1 set 64 with all 29 slots mapped to distinct
private TILEs on the common canvas/hotspot and palette 505. It requires the
first 14 to carry the growing/peak/fading art, the fifteenth to complete the
fade, and the remaining fourteen to be transparent. PXE1 alone owns the art,
callback, and audio; stock HRC1, XR30, and the obsolete PXV1 channel are
rejected. The recovered detailed source master lives at
`assets/source/spells/phoenix-phial/flaming-phoenix-source.png`.

No polling thread, resurrection watcher, custom destination search, custom
combat reset, or custom inventory counter is permitted.

## Siege QA fixture

The explicit Siege fixture leaves Phoenix research incomplete so its row can
be tested. Its Rogue, Warrior, and Alchemist are advanced to level 10, receive
5,000 gold and 100 Intelligence, and continue through the existing stock
`Purchase_Equipment` probe. Once research completes and earlier purchases are
satisfied, they should autonomously buy one Phial.

Each fixture hero has the same stock home relationship as an ordinarily
recruited hero: the Rogue belongs to a completed Rogues Guild, the Warrior to a
completed Warriors Guild, and the Alchemist to the Laboratory. Parenting test
heroes to the Palace is forbidden because stock `hero_birth` deliberately
clears a Palace parent from `Home`; a subsequently resurrected homeless hero
can then reach stock `Flee`'s no-safe-building `Berserking` fallback.

For repeatable lethal testing, the fixture adds 100,000 sovereign gold through
stock `$AdjustPlayerData` and spawns a completed level-3 Wizard's Guild through
stock `$SpawnUnit`. No spell, damage, death, or resurrection test controller is
added; the player uses the ordinary Wizard's Guild sovereign-spell path against
the three equipped test heroes.
