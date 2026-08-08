# Alchemist Design Brief

## Pillar

The Alchemist prepares a finite field kit at home and spends it intelligently.
Power comes from choosing the right mixture, not repeatedly casting conventional
magic.

## First playable scope

- A three-level Alchemists Laboratory available at Palace level 2.
- One recruitable Alchemist archetype and a four-member guild cap.
- An AP10-derived panel whose stock `SPELLS` surface is relabeled `BREWING`.
- A basic thrown-flask attack, one situational field mixture, and one sovereign
  Brewing recipe for the first proof.
- A small decision tree that values clustered targets and returns home to
  restock when its field mixture is empty.
- Unique guild, hero, projectile, overlay, interface, text, and sound resources.

This intentionally cuts the first build below the full fantasy. Additional
mixtures, shopping behavior, and economic interactions come after the second
CAM can coexist with Phantoms Haunt.

## Controller and panel

- Development DialogID: `CGAL`.
- Declared controller base: stock `AP10`, Temple to Fervus.
- Stock shape retained: three building levels, one recruit action, Heroes, and
  the secondary spell-menu surface.
- `SPELLS` becomes `BREWING`; temple-specific copy and controls are replaced,
  not merely hidden behind Alchemist labels.

AP07 and AP10 enter the same stock constructor, which is why the current
Expanded Building Slots proof patch can host both `CGPH` and `CGAL` without a
second executable hook. The custom IDs keep their CAM resources independent.
This proves the factory route and panel construction path only. Activating the
AP10 secondary surface and binding Alchemist-specific Brewing callbacks under
`CGAL` remain the next runtime experiment.

## First Brewing experiment

The first recipe should test something ordinary hero spells do not: a timed
kingdom-support concoction. Current lead:

- **Civic Tonic** — temporarily improves the mobility and survivability of
  non-hero kingdom workers such as Peasants, Tax Collectors, and City Guards.

This is deliberately one recipe. It proves the renamed AP10 menu, purchase and
cooldown flow, multi-agent targeting, visible effectors, and expiry behavior.
If kingdom-wide iteration proves unsafe or unreadable, narrow it to a selected
friendly non-hero unit before adding more recipes.

Weapon oils remain an excellent second phase. Having autonomous heroes visit
the Laboratory and buy an oil requires merchant inventory, AI shopping, item
ownership, and timed combat modifiers, so it should not block the first merge
fixture.

## Candidate mixtures

- **Volatile Flask** - reliable splash damage and the default expendable.
- **Vitriol** - physical-armor reduction against durable units and buildings.
- **Binding Resin** - movement and action slowdown against fast threats.
- **Flash Powder** - short disruption against ranged or spellcasting enemies.
- **Panacea** - later self-rescue or targeted ally cleanse, if support behavior
  remains readable and balanced.

Each field mixture should eventually use a visible charge attribute. Resting at
the Laboratory refills charges; guild upgrades unlock recipes or increase
carrying capacity. The first build needs only one charge-consuming situational
mixture before expanding this system.

## Majesty interactions to explore

- visits to the Marketplace, Bazaar, Library, and Magic Bazaar;
- potion and elixir recognition without duplicating their effects;
- bonus effectiveness against regenerating monsters;
- Vitriol assistance for Dwarves or Warriors attacking buildings;
- Healer or Agrela interaction with Panacea;
- reluctance or rivalry around Wizards if the guild needs a faction identity.

## Technical purpose

Build this as an independent CAM provider with `CGAL` dialog resources and a
separate ID namespace. It should modify the same global tables and art registries
as Phantoms Haunt so the CAM merger is tested against real BDEP, text-table,
TILE, SPLT, SMNU, audio, and GPL conflicts.

The first coexistence milestone is two enabled custom buildings at once:
`CGPH` using the Phantom package and `CGAL` using this package. Alternating
between their panels must never leak strings, controls, portraits, or state.

## Decisions deliberately deferred

- exact stats, recruitment cost, and unlock levels;
- whether mixtures are spells, inventory markers, or a hybrid;
- final guild name and faction exclusions;
- final art and voice direction.
