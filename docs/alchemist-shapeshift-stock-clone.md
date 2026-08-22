# Alchemist Shapeshift Potion stock clone

The Alchemist still buys and consumes the native Magic Bazaar Shapeshift
Potion. Its action descriptor, inventory deletion, learned-spell cleanup,
30-second icon effector, `ChangeUnitType`/`RevertUnitType` ownership, callback,
and final HP clamp remain the stock Northern Expansion lifecycle.

The package compiles a fail-closed clone of stock `Shapeshift_Potion_Effect`
and `Shapeshift_Potion_End`. The clone inserts one title-specific branch before
the unchanged Dryad, Medusa, and Minotaur dispatch. Only an `Alchemist` becomes
the stock `Giant_Spider`; every other hero follows its original stock branch.

The Spider branch retains the melee form's stock `+5` basic-damage armor and
`+10` hand-to-hand bonuses, reduces the Minotaur durability package to `+18`
Strength, `+15` Vitality, and `+30` current/maximum HP, and adds `-50` to
`ActionRateModifier`. That action-rate value is copied exactly from stock Speed
Tonic. The native Shapeshift callback restores the Alchemist's type and applies
the exact inverse adjustments in the same order before stock HP clamping.

The builder refuses to generate this clone if either stock form-dispatch anchor
changes. Package validation also requires both native Shapeshift function
symbols in the compiled BCD. No timer, watcher, replacement inventory item, or
custom transformation controller exists.
