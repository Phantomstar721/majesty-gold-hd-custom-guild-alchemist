# Magic Bazaar stock lifecycle

The Alchemist uses the Northern Expansion Magic Bazaar without a private
purchase controller. `Alchemist_tree` retains Rogue's stock priority position:
`Purchase_equipment`, then `Purchase_bazaar`, then entertainment, looting,
resource collection, and hunting. The requested stronger priority changes only
the stock `bazaar_chance` argument to 101; this is one above the function's
`RandomNumber(100) + 1` ceiling and therefore makes the check deterministic
when an affordable researched item is actually available.

`Purchase_Bazaar` remains the complete stock owner. It finds completed
`Magic_Bazaar` buildings within the intelligence-scaled sight radius, filters
each of the six items through its corresponding research attribute, rejects an
item already held or unaffordable, sets the stock task and buyer intent, and
enters through `Use_Building`. `Bazaar_Visited` and `Purchasing_at_Bazaar`
preserve the stock 10-second visit, payment, inventory creation,
`QItem_Stat_Boost`, exit, and task reset. No Alchemist-only purchase watcher or
inventory path exists.

The inventory callback teaches each Bazaar item as its native one-use spell.
Combat continues to use stock `attack_object`: `getbestspell(#list_attack)`
selects the highest-ranked available spell, moves to the hero's casting range,
and calls `castspell`. Stun Serum is rank 5 and Flash Flask is rank 4; the
native combat potions then retain their own ranks (Fire Balm 3, Shapeshift 2,
Strength and Regeneration 1). This produces the requested combat-opening order
without a custom combat state machine. Speed Tonic and Invisibility Brew retain
their stock flee spell type and are used by the stock flee path, not forcibly
consumed at combat entry.

The explicit Siege QA fixture uses the same stock quest pattern found in
`Quests_3.gpl`: it spawns `MagicBazaar3` and sets
`ResearchBazaar_Item_One` through `ResearchBazaar_Item_Six`. It also spawns
`AlchemistsLaboratory3` with `ResearchArrows` and `ResearchPowerfulItem` set.
These assignments are test-only and do not change ordinary games.
