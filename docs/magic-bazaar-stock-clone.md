# Magic Bazaar stock lifecycle

The Alchemist uses the Northern Expansion Magic Bazaar with a private clone of
only the stock item selector. `Alchemist_tree` retains Rogue's stock priority
position: `Purchase_equipment`, then `Alchemist_Purchase_Bazaar`, then
entertainment, looting, resource collection, and hunting. Keeping the complete
stock `Purchase_equipment` gate first preserves ordinary Marketplace,
Blacksmith, Library, and Wizard Guild shopping opportunities. The Bazaar chance
is 101, one above the function's `RandomNumber(100) + 1` ceiling, so the check
is deterministic only when a researched, affordable, not-already-held flask is
available.

Stock `Purchase_Bazaar` checks the whole item list and the last successful
candidate owns `TaskName`. The private clone therefore iterates candidates from
lowest to highest priority: Invisibility, Shapeshift, Fire, Regeneration,
Strength, Speed. The resulting purchase priority is exactly Speed > Strength >
Regeneration > Fire > Shapeshift > Invisibility. `Alchemist_Bazaar_Item_Check`
changes only the Fire Balm title gate to include `alchemist`; all research,
cost, inventory, building-completion, and affordability checks remain stock.

The cloned selector retains the complete stock transaction. It finds completed
`Magic_Bazaar` buildings within the intelligence-scaled sight radius, filters
each of the six items through its corresponding research attribute, rejects an
item already held or unaffordable, sets the stock task and buyer intent, and
enters through `Use_Building`. `Bazaar_Visited` and `Purchasing_at_Bazaar`
preserve the stock 10-second visit, payment, inventory creation,
`QItem_Stat_Boost`, exit, and task reset. No Alchemist-only purchase watcher,
payment path, inventory path, or visit lifecycle exists.

The private GPL intent-text CAM clones Northern Expansion's final
`DataMX/mx_gpltext.cam`, not Original Majesty's shorter `Data/gpltext.cam`.
All 309 stock intent strings—including the Magic Bazaar purchase statuses—are
preserved, and the two Laboratory-only intents append at indices 309 and 310.
This prevents the package from blanking Bazaar status text for every hero.

The inventory callback teaches each Bazaar item as its native one-use spell.
Combat continues to use stock `attack_object`: `getbestspell(#list_attack)`
selects the highest-ranked available spell, moves to the hero's casting range,
and calls `castspell`. Stun Serum is rank 5 and Flash Flask is rank 4; the
native combat potions then retain their own ranks (Fire Balm 3, Shapeshift 2,
Strength and Regeneration 1). This produces the requested combat-opening order
without a custom combat state machine. Speed Tonic and Invisibility Brew retain
their stock flee spell type and are used by the stock flee path, not forcibly
consumed at combat entry.

Stock Fire Balm temporarily swaps `attack_action` and
`special_attack_action`, then swaps them back in its native effector callback.
Because the Alchemist intentionally has no Cultist `Fire_Dagger`, both action
slots point to the stock melee `basic_attack`; Fire Balm's native
`fire_balm_hit` splat still supplies the fiery hit while the dagger action and
stock cleanup lifecycle remain valid.

The explicit Siege QA fixture uses the same stock quest pattern found in
`Quests_3.gpl`: it spawns `MagicBazaar3` and sets
`ResearchBazaar_Item_One` through `ResearchBazaar_Item_Six`. It also spawns
`AlchemistsLaboratory3` with `ResearchArrows` and `ResearchPowerfulItem` set.
These assignments are test-only and do not change ordinary games.
