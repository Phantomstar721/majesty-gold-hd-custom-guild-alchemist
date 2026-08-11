# Custom Guild: Alchemist

Planned Majesty Gold HD custom guild and recruitable Alchemist hero.

## Status

Runnable AP10-derived panel fixture. The Laboratory uses the development
DialogID `CGAL` and is the second substantial fixture for the Majesty Gold HD
CAM Merger alongside Phantoms Haunt.

The hero's core identity is field preparation: brew limited mixtures while
resting, then choose the right thrown flask for armor, crowds, fast enemies, or
an emergency recovery. This should feel distinct from a Wizard's reusable spell
rotation and the Marketplace's player-purchased consumables.

See [the initial design brief](docs/design-brief.md).

Invigorating Elixer is intentionally scoped to true recruitable heroes. Its
activation, targeting, timed effector, Palace-side count, expiry cleanup, and
repeat-use lifecycle copy the stock Rage of Krolm mechanism. Henchmen were
removed after repeated live tests showed that Majesty's available enumeration
paths select them inconsistently across casts. The complete test record is in
[the Invigorating Elixer research log](docs/invigorating-elixer-research.md).

Phoenix Phial is the third Brewing prototype: a researched, 1,000-gold,
single-charge hero inventory item with a 70-percent chance to resurrect its
owner in place and dispatch the revived hero through stock fleeing. Its exact
research, purchase, inventory, Healer/Agrela resurrection, and escape contract
is recorded in [the Phoenix Phial stock-clone notes](docs/phoenix-phial-stock-clone.md).

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

## Build the panel probe

The current package intentionally borrows the three stock Temple to Fervus
building images, the Cultist recruit, and their sounds. It adds independent
`ALB1`-`ALB3` Laboratory descriptions and clones AP10's panel as `CGAL`, with
the final `SPELLS` label changed to `BREWING`. Matching GPL building-data
records use ordinary guild construction and upgrade callbacks; Fervus-specific
temple and animal-spawning callbacks are not inherited.

```powershell
.\scripts\Build-AlchemistProbe.ps1 -IncludePhantomsHauntProbe
.\scripts\Deploy-AlchemistProbe.ps1
```

The compatibility switch emits both temporary `PHG1` and `ALB1` BDEP rules so
this package can load after Phantoms Haunt during the two-mod test. It is a
deliberate stopgap for the CAM merger, not the final distribution model.

In game, enable **Custom Guild: Phantoms Haunt** and **Custom Guild: Alchemist
(CGAL Probe)**, with the Alchemist probe later in the active list. The first
test is panel safety: build and upgrade both guilds, recruit the temporary stock
Cultist from the Laboratory, and click `BREWING`. The Brewing click may still
expose an AP10 callback assumption; that is the behavior this fixture exists to
measure.

Follow the complete [CGAL runtime probe](docs/runtime-probe.md) so panel,
upgrade, coexistence, stock-regression, and save/reload behavior are checked in
a useful order.

The default build disables the cloned AP10 secondary-control hitbox. Live tests
proved that it crashes under `CGAL` even when the Laboratory aliases the stock
`Temple_Fervus` GPL title. Use `-EnableUnsafeBrewingControl` only when developing
the future DLL callback mapping; it intentionally restores the known-crashing
control.

For repeated Brewing development, add `-IncludeSiegeTestFixture`. This copies
and overrides only the stock `SIEGE()` entry point in the generated probe and
spawns completed player-owned Fervus, Krolm, level-3 Wizard, and Alchemy guilds
near the Palace. It also supplies 100,000 sovereign gold and three funded,
level-10 purchase-test heroes so Phoenix Phial death/resurrection tests can be
repeated quickly. The switch is deliberately off by default.
