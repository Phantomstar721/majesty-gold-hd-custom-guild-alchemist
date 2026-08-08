# Alchemist Design Brief

## Pillar

The Alchemist prepares a finite field kit at home and spends it intelligently.
Power comes from choosing the right mixture, not repeatedly casting conventional
magic.

## First playable scope

- A three-level Alchemists Laboratory available at Palace level 2.
- One recruitable Alchemist archetype and a four-member guild cap.
- A basic thrown flask attack plus three situational mixtures.
- A dedicated decision tree that values ingredients, equipment, lairs, enemy
  buildings, clustered targets, and returning home to restock.
- Unique guild, hero, projectile, overlay, interface, text, and sound resources.

## Candidate mixtures

- **Volatile Flask** - reliable splash damage and the default expendable.
- **Vitriol** - physical-armor reduction against durable units and buildings.
- **Binding Resin** - movement and action slowdown against fast threats.
- **Flash Powder** - short disruption against ranged or spellcasting enemies.
- **Panacea** - later self-rescue or targeted ally cleanse, if support behavior
  remains readable and balanced.

Each mixture should use a visible charge attribute. Resting at the Laboratory
refills charges; guild upgrades unlock recipes or increase carrying capacity.

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

## Decisions deliberately deferred

- exact stats, recruitment cost, and unlock levels;
- whether mixtures are spells, inventory markers, or a hybrid;
- final guild name and faction exclusions;
- final art and voice direction.
