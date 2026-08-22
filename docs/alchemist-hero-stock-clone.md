# Alchemist hero stock-clone contract

The Alchemist combines two ordinary stock hero contracts. Its decision cycle
is Rogue-derived, while its dagger is a direct Warrior-style melee attack. No
new combat dispatcher, spell filter, or theft watcher is involved.

## Decision lifecycle: Rogue

The authority is the retail SDK source
`SDK/OriginalQuests/GPL/DecisionTrees/Rogue.gpl`. `Alchemist_tree` keeps the
stock arguments, weights, intent setup, and final `Hero_Wander` fallback for
every retained branch. It keeps rewards and home-defense checks, equipment
purchase, entertainment, special-item collection, Library visits, combat,
exploration, and high-priority return home.

The deleted Rogue-specific decision branches are:

```gpl
if ($Steal_Check(thisagent,95) == False)
if ($Loot_Gravestones(ThisAgent,100) == False)
if ($Collect_Resource(thisagent,"poison_plants",90) == False)
```

No replacement scavenging controller is introduced. The Alchemist retains
ordinary special-item collection, but no longer steals, raids graves, or
harvests the Rogue's poison ingredient.

## Class spells: removed at the declaration

Stock Cultists receive `camouflage`, `change_shape`, and `charm_monster` from
the `AllowedSpells` block on the `Cultist` character description in
`SDK/OriginalQuests/Data/M_Characters.xml`. The private `ALC1` description
removes that complete block, so none of those Cultist actions enters the
Alchemist's available spell list. This removes shapeshifting at the same stock
ownership boundary that grants it; there is no runtime suppression hook.

The generic Library checks remain exactly where stock Rogue places them. They
are shared Rogue behavior, not Cultist class spells.

## Dagger combat lifecycle: Warrior basic attack

The melee path copies the stock Warrior contract across all three owners:

1. `Hero_Data.dat` supplies `attacktype 1` and
   `attack_action basic_attack`.
2. `M_Characters.xml` supplies Warrior's `AttackRange min="1" max="1"`
   geometry.
3. `M_Actions.xml` defines `basic_attack` with `ImageSet="Attack"`, its stock
   attack sound phase and rate, and the `make_attack` GPL callback.

The normal stock `attack_object` lifecycle therefore selects the hero's
maximum melee range, travels into contact, and calls `PerformAction` with
`basic_attack`. The action then enters untouched `make_attack`, where
`attacktype 1` selects H-to-H accuracy and parry before ordinary weapon damage,
experience, poison, and attack cleanup. The private ALC1 animation descriptor
already clones Warrior's action layout, so the engine action and visible
dagger animation use the same stock timing structure.

The former Cultist projectile actions (`Cultist_Dagger` and expansion
`Fire_Dagger`) are absent, and there is no Alchemist special attack action.
