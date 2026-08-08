# Custom Guild: Alchemist

Planned Majesty Gold HD custom guild and recruitable Alchemist hero.

## Status

AP10-derived design fixture. The Laboratory reserves the development DialogID
`CGAL` and is the intended second substantial fixture for the Majesty Gold HD
CAM Merger alongside Phantoms Haunt.

The hero's core identity is field preparation: brew limited mixtures while
resting, then choose the right thrown flask for armor, crowds, fast enemies, or
an emergency recovery. This should feel distinct from a Wizard's reusable spell
rotation and the Marketplace's player-purchased consumables.

See [the initial design brief](docs/design-brief.md).

## Planned dependencies

- **Majesty Gold HD - Expanded Building Slots** for a unique `CGAL` recruitment
  dialog routed through the shared AP07/AP10 guild constructor without an
  Alchemist-specific EXE patch.
- **Majesty Gold HD CAM Merger** when combining this package with Phantoms Haunt
  or another CAM mod.

No game files belong in this repository.

See the [resource namespace](docs/resource-namespace.md) for the stable fixture
IDs and [`mod-definition.json`](mod-definition.json) for the future manager-facing
building/controller declaration.
