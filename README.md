# Custom Guild: Alchemist Lab

Custom Guild: Alchemist Lab adds a complete three-level guild and a new
Alchemist hero class to Majesty Gold HD. Alchemists are lightly armored field
researchers who turn monster remains into Reagents, prepare themselves through
careful shopping, and bring experimental oils, phials, thrown mixtures, and
kingdom-scale alchemy into battle.

The mod includes original building and hero art, animation, interface panels,
icons, spell effects, voice work, sound design, names, help text, progression,
AI behavior, and support for Original Majesty and Northern Expansion content.

## Installation and launching

This mod **requires the
[Majesty Mod Manager](https://steamcommunity.com/sharedfiles/filedetails/?id=3793024054)**.
The Lab uses private building slots, interface controllers, name generation,
and CAM resources that the ordinary Majesty executable cannot initialize.

1. Subscribe to Custom Guild: Alchemist Lab and Majesty Mod Manager on Steam
   Workshop.
2. Open the Mod Manager's Workshop folder and run `Majesty Mod Manager.exe`.
3. Complete its one-time Majesty installation setup.
4. Select Custom Guild: Alchemist Lab and choose **Prepare Selected Mods**.
5. Start the game with **Launch Majesty** inside the manager.

Do not enable the Alchemist package directly in Majesty's mod selector, and do
not start a prepared Alchemist game with the ordinary Steam executable.

To use this mod with Custom Guild: Phantoms Haunt, select both mods in the Mod
Manager. It builds one compatible local profile containing both guilds. Do not
enable the two raw Workshop packages together without the manager.

## Alchemy Lab

The Alchemy Lab requires a level-2 Palace, houses up to four Alchemists, and has
its own stock-shaped recruitment, Visitors, and Brewing panels.

| Level | Cost | Progression |
| --- | ---: | --- |
| 1 | 1,400 gold | Recruit Alchemists; research Weapon Oil for 250 gold |
| 2 | 1,800 gold | Research Phoenix Phial for 750 gold |
| 3 | 2,200 gold | Use Vigor Elixir, Arcane Infusion, and Philosopher's Stone |

Each level's research must be completed before the next building upgrade. Rows
remain hidden until their relevant building level is reached, while Reagents
can be collected and stored from level 1 onward. The level-3 recipes are
revealed only when the Lab can use them.

At 10 or more stored Reagents, a persistent purple enchantment spiral appears
over the Lab's brewing pool. It is removed as soon as that Lab falls below the
threshold. The building has unique construction, inactive, active, damaged,
destroyed, and collapsed states; active liquid sources use a gentle animated
glow. Its placement and blocking footprint is a private clone of the larger
stock Temple to Krypta footprint.

## Alchemist hero

Alchemists cost 600 gold and fight in melee with daggers. They begin with a
100-gold research grant in addition to Majesty's normal starting purse. Their
base identity includes:

- 11 Vitality, 11 Strength, 18 Intelligence, and 20 Artifice;
- 45 Attack, 35 Parry, 40 Dodge, 6 weapon damage, and 3 armor;
- 22 Greed, 18 Luck, poison immunity, and a 30-percent retreat threshold;
- light leather armor and movement between a Warrior and a Rogue.

Their decision tree begins with Majesty's Rogue behavior, removes stealing,
gravestone looting, and poison-plant scavenging, and uses the Warrior's basic
melee attack lifecycle. Alchemists are eager bounty hunters, but preparation
has priority while they are still near town. A suitable shop within 500 units
can precede a new reward flag, while a field Alchemist with at least 2,000 gold
can make a deliberate full-range resupply trip only when a real researched
purchase is available. A full load of three Reagents receives a 95-percent
stock Go Home check before another reward is accepted.

Alchemists retain normal Marketplace, Blacksmith, Library, and Wizard Guild
shopping. At a researched Magic Bazaar they prioritize Speed, Strength,
Regeneration, Fire Balm, Shapeshift, and Invisibility according to combat need;
their private Shapeshift form is a Giant Spider.

### Flash Flask — level 3

A 30-second self-buff granting +10 Dodge, +10 Parry, and a 400-point action-rate
improvement. It has a 45-second cooldown.

### Stun Serum — level 5

A thrown flask that freezes a non-building target for five seconds through the
stock Vines and Paralytic Gaze control lifecycle. It has a 45-second cooldown.

### Miasma Mist — level 8

A stationary 175-radius cloud lasting 21 seconds and pulsing every 1.6 seconds.
Each pulse deals one damage and refreshes a ten-second debuff with -10 Dodge,
-10 Parry, a 100-point movement slowdown, and a 1,000-point action slowdown.
It has a 60-second cooldown and cannot target buildings or lairs.

## Monster Reagents

When an ordinary monster dies, its stock `LevelXP` value determines the chance
that the closest eligible Alchemist within 300 units collects one Reagent.
Quest-protected bosses do not provide renewable Reagents.

| Threat rank | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Drop chance | 10% | 20% | 30% | 45% | 60% | 75% | 90% | 100% |

An Alchemist carries at most three Reagents. They use Majesty's native carried
guild-resource count rather than a quest item, so they do not appear as entries
in the hero Items panel. Resting at the Alchemist's home Lab deposits the load
into that building and resets the carried count. The Brewing panel displays the
Lab's live stored total.

## Brewing discoveries

### Weapon Oil

Weapon Oil research costs 250 gold, and a researched oil costs a visiting hero
100 gold. It is independent from stock poison and Wizard weapon enchantments.

- Paralytic Oil freezes a struck enemy for two seconds. The same target cannot
  trigger any hero's Paralytic Oil again for ten seconds. This private cooldown
  does not block Vines, Stun Serum, Frost Armor, or other control effects.
- Transmutation Oil grants its owner five gold on a successful weapon hit.

Heroes with Greed above 20 choose Transmutation Oil; others choose Paralytic
Oil. The current Alchemist oil appears in the hero Enchantments panel. Stock
poison remains fully functional but has no Enchantments entry, matching its
native lifecycle.

### Phoenix Phial

Phoenix Phial research costs 750 gold, and a hero can buy one for 750 gold. It
appears in the Items panel and is consumed on death. The phial has a 75-percent
chance to resurrect its owner at the death location with 25 percent health,
after which the hero enters Majesty's normal absolute-flee behavior.

### Vigor Elixir

Vigor costs the sovereign 1,500 gold and one stored Reagent. Every living hero
receives +20 current and maximum hit points, a 200-point movement improvement,
and +1 self estimation for 30 seconds. Its progress, cleanup, and mutual
exclusion with Rage of Krolm clone the complete stock Rage lifecycle; Vigor and
Rage cannot stack. A green-and-gold ritual plays over the exact Lab that brewed
the elixir.

### Arcane Infusion

Arcane Infusion costs ten stored Reagents and can be completed once per kingdom.
It permanently grants +25 Magic Resistance to every current Alchemist from any
Lab, and all Alchemists recruited or restored afterward receive the same
benefit. A long purple enchanting ritual plays over the selected Lab.

### Philosopher's Stone

Philosopher's Stone costs ten stored Reagents. It can transmute the closest
ordinary hostile monster or enemy hero within 45 units of the chosen point,
excluding quest-protected agents. The kingdom receives 3,000 gold, the target
shows Majesty's Gold Gain presentation and a long transmutation effect, and the
target then follows its normal death callbacks.

## Guild and quest integration

- The Lab's Visitors panel lets heroes buy researched Weapon Oil and Phoenix
  Phials.
- Stock Embassies discover completed Alchemy Labs and recruit Alchemists.
- Outpost and Embassy random recruitment appends Alchemist to Northern
  Expansion's complete selector without removing Paladins.
- Reanimated Alchemists can return to and reattach to an eligible active Lab.
- The package uses dataset `Any` for Original Majesty and Northern Expansion
  quests.

## Technical architecture

The package follows Majesty's stock systems and privatizes only the identifiers
and assets required for the new guild.

| Area | Implementation |
| --- | --- |
| Package | One `.mmxml` manifest loading private CAM archives, XML descriptions, and compiled GPL |
| Runtime | Manager v3 typed features declaring the private building, Brewing controller, oil rows, name generator, and stock-derived actions |
| Building | Marketplace lifecycle topology, original high-resolution indexed art, native TILE-v3 encoding, stock shadow controls, and the Krypta blocking footprint |
| Interface | Private `CGAL` guild dialog and `CGBR` Brewing dialog cloned from stock controller families |
| Rules | Stock-derived GPL compiled with Majesty's SDK compiler |
| Text | Private names, actions, help, interface strings, and live resource count |
| Audio | Mono PCM game WAVs routed through stock-shaped sound descriptors |
| Compatibility | Full stock building-dependency table plus one Palace-level Lab rule; private CAM and resource identifiers |

World art is stored in private IMAG records and appended TILE/SPLT slots rather
than overwriting retail building art. The building family preserves native
direction, stream, timing, palette-control, anchor, and active/inactive
ownership. Interface controls, sovereign commands, timed effectors, research,
resurrection, shopping, and resource transfers are private stock clones with
their original dispatch and cleanup shapes intact.

## Repository layout

```text
docs/        Public technical documentation
release/     Player-facing Workshop safety instructions
scripts/     Build, validation, review, deployment, and Workshop staging tools
src/         CAM/package builder and GPL source
tests/       Automated stock-contract and package tests
```

Generated packages and review output live under `dist/` and `artifacts/` and
are not source-controlled. Original art, recording projects, processed audio,
and Workshop masters live under the private `assets/` tree and are also not
published in the source repository. The public repository contains the build
logic, behavior source, documentation, and tests; building the complete package
requires the original assets.

## Building and testing

Requirements:

- Majesty Gold HD with the Majesty SDK and `Gplbcc.exe`;
- the shared workspace Python launcher at `..\.tools\python.cmd`;
- the private original assets used by the package builder.

Build and validate the production package:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Build-CustomGuildAlchemist.ps1
```

The result is written to `dist\CustomGuildAlchemist`. Run the automated tests
with:

```powershell
..\.tools\python.cmd -m unittest discover -s tests
```

Prepare a repository-owned RGSeditor upload without touching Majesty's test mod
directories:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Stage-Workshop.ps1
```

The staged content, preview, checksum manifest, and `.mswproj` are written to
`dist\workshop-upload`.

## License

Repository source code is available under the [MIT License](LICENSE). Majesty
Gold HD and its original assets remain the property of their respective rights
holders. The license does not grant rights to redistribute Majesty's retail
game assets.
