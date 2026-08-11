# Phoenix Phial stock-clone contract

Phoenix Phial combines only traced Majesty mechanisms. Its two custom seams are
the user-approved 70-percent lethal-event roll and the dispatch between those
stock lifecycles.

## Research

The third CGBR row is the same complete APa1 Arrows compound research control
used by Weapon Oil, privatized as command `0x2A16` and moved down one row. This
keeps both Laboratory research bars byte-for-byte identical in width, internal
hit geometry, disabled state, and native dispatch. The runtime descriptor also
starts from APa1 Arrows so the prototype remains researchable at Laboratory
level 1, then copies only APa3 Teleportation Amulets'
`ResearchPowerfulItem` completion attribute. This deliberately defers the
final Laboratory-level requirement.

Native research continues to own validation, treasury payment, timestamps,
completion, cancellation, the one-time completed state, and the green alert.
The progress display is the already-proven AP24 display pair fed with those
native timestamps. The completion alert substitutes `Phoenix Phial` only for
the private descriptor.

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
Phial. The CGBR research glyph separately clones the exact APa1 icon control
used by Weapon Oil and points it at private `ALPI` art.

## Death, resurrection, and escape

The package overrides the global `gravestone` symbol, which is therefore a CAM
merger symbol. With no Phial, or after the 30-percent failure roll, its body is
the literal stock `gravestone` lifecycle.

With a Phial, the item is deleted before the roll, so both success and failure
consume the single charge. Success performs Healer rebirth's dead-state setup
at the hero's current location and creates a private clone of Agrela's
`resurrection_effector`. `Shared_Begin_Resurrect` and
`Shared_End_Resurrect` retain ownership of death-flag clearing, dead-script
termination, hero-type restoration, action reset, and active-script restart.

The private completion callback then sets HP to 25 percent and calls stock
`Flee`. That stock function chooses the hero's home or a safe inn, uses the
normal safe-building travel path, and already contains the desired exception:
a hero near a threatened home fights instead. With nowhere safe to flee, stock
behavior makes the hero stand and fight.

No polling thread, resurrection watcher, custom destination search, custom
combat reset, or custom inventory counter is permitted.

## Siege QA fixture

The explicit Siege fixture leaves Phoenix research incomplete so its row can
be tested. Its Rogue, Warrior, and Alchemist are advanced to level 10, receive
5,000 gold and 100 Intelligence, and continue through the existing stock
`Purchase_Equipment` probe. Once research completes and earlier purchases are
satisfied, they should autonomously buy one Phial.

For repeatable lethal testing, the fixture adds 100,000 sovereign gold through
stock `$AdjustPlayerData` and spawns a completed level-3 Wizard's Guild through
stock `$SpawnUnit`. No spell, damage, death, or resurrection test controller is
added; the player uses the ordinary Wizard's Guild sovereign-spell path against
the three equipped test heroes.
