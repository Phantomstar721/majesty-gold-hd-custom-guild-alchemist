# Alchemist help text and name-pool proposal

Status: **help text and name copy approved and integrated**. The help strings are wired under private IDs
`hAL0` for the hero and `hAL1` through `hAL3` for the three Laboratory levels.
The revised name pool is packaged under private tables `HN69` through `HN72`,
and the dual-profile runtime registers private generator `NM18` through the
stock name-registry lifecycle.

The structure follows stock Majesty help pages: concise mechanical bullets,
gold upgrade-preview text, and one lore paragraph.

## Alchemist hero (`hAL0`)

```text
- Fights in melee with a dagger, but prepares for combat from a distance

- Seeks out Magic Bazaar potions, Weapon Oil and Phoenix Phials

- Immune to poison

- Learns Flash Flask at level 3, Stun Serum at level 5 and Miasma Mist at level 8


Alchemists are restless scholars who carry their experiments out of the workshop
and into the wilds of Ardania. They lack a Warrior's discipline and a Wizard's
raw command of magic, but careful preparation makes them elusive and dangerous
opponents. Every battle is another field trial, and every monster is a promising
source of ingredients, provided the formula survives its inventor.
```

## Alchemy Lab, level 1 (`hAL1`)

```text
- Requires a level 2 Palace

- Recruits Alchemists

- Houses up to four guild members

- Can research Weapon Oil for 250 gold

- Researched Weapon Oil may be purchased by visiting weapon-wielding heroes for 100 gold

Upgrading the Laboratory adds
+ Phoenix Phial research
+ Increased building hit points


Behind the stained windows of an Alchemy Lab, copper vessels simmer beside ranks
of carefully labeled bottles. Its practitioners promise that every scorch mark,
shattered flask and alarming odor is simply another step toward a reliable result.
```

## Alchemy Lab, level 2 (`hAL2`)

```text
- Allows Phoenix Phials to be researched for 750 gold

- Researched Phoenix Phials may be purchased by visiting heroes for 1,000 gold

- A carried Phoenix Phial is consumed at death and has a 75% chance to revive its owner

Upgrading the Laboratory adds
+ Vigor Elixir
+ Increased building hit points


With a larger still and a better-stocked workbench, the Laboratory's experiments
turn from useful preparations to improbable feats. The Phoenix Phial is its proudest
achievement, although the alchemists remain evasive when asked about the other
twenty-five percent.
```

## Alchemy Lab, level 3 (`hAL3`)

```text
- Allows the sovereign to brew Vigor Elixir for 1,500 gold

- Vigor Elixir invigorates every hero in the realm for 30 seconds

- Invigorated heroes move faster, gain 20 maximum and current hit points, and fight with greater confidence

- Vigor Elixir and Rage of Krolm cannot be active at the same time


Crowned by an elaborate distiller, a master Laboratory turns the wealth and
curiosities of an entire realm into bottled possibility. Its furnaces never cool,
its glassworks never empty and its alchemists insist that the occasional explosion
is a sign of vigorous scholarship.
```

## Proposed Alchemist name pool

Stock and Northern Expansion heroes build names by combining a class-specific
given-name table with a surname or epithet table. This proposal uses 43 entries
in each table, matching the usual Expansion-sized pools and yielding 1,849
possible combinations.

### Given names (43)

```text
Adalia
Aeris
Alys
Ameline
Anora
Beatrix
Brinna
Bryony
Calista
Celandra
Cerys
Corvina
Delphine
Delyra
Elara
Elspeth
Eudora
Evania
Fenella
Hester
Ilyra
Isolde
Jessamine
Katell
Lavinia
Lenora
Maelis
Melisande
Mirabel
Mirelda
Nerissa
Odette
Petra
Rosamund
Rowena
Sabine
Selene
Sybilla
Tamsin
Verena
Vespera
Olyra
Zora
```

### Surnames and epithets (43)

The leading space shown by stock data is omitted here for readability.

```text
Alembic
Amberglass
Ashvial
Blackflask
Brasscoil
Brightbottle
Cinderbrew
Fireglass
Emberglass
Flamebrew
Flaskwise
Fullflask
Glassweaver
Giltglass
Brightvial
Mortarwise
Quickmeasure
Quicksilver
Silverstill
Singedbrow
Smokesleeve
Sootsleeve
Stonepestle
Vitriol
of the Brass Crucible
of the Copper Coil
of the Emerald Flask
of the Golden Measure
of the Scarlet Flask
of the Viridian Flame
of the Silver Still
the Apothecary
the Artificer
the Bottlemaker
the Brewmistress
the Catalyst
the Distiller
the Experimenter
the Formula Keeper
the Crucible Keeper
the Singed
the Meticulous
the Transmuter
```

Representative generated names include `Beatrix Amberglass`, `Hester
Singedbrow`, `Lavinia Vitriol`, `Vespera of the Emerald Flask`, and `Eudora the
Meticulous`.

## Implementation boundary

The approved help pages use private records rather than replacing the Cultist's
stock pages. Name packaging likewise uses private resources and does not replace
the Cultist's `HN09` and `HN10` pools. The runtime extension is required because
stock Majesty registers only `NM01` through `NM17`; `NM17` already belongs to
Inns. The injected `NM18` entry uses Majesty's existing allocator, generator
constructor, registry map, random selection, fragment concatenation, ownership,
and destruction paths.
