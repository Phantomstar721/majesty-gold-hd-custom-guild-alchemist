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

The recruit now uses a private copy of the stock Rogue decision cycle with its
stealing branch removed, while dagger combat uses Warrior's direct
`basic_attack` lifecycle. Cultist camouflage, charm, and shapeshifting are
removed at the stock `AllowedSpells` declaration. The exact ownership and call
paths are recorded in
[the Alchemist hero stock-clone notes](docs/alchemist-hero-stock-clone.md).
Stun Serum's Rogue-range engagement and native five-second freeze lifecycle
are recorded in [the Stun Serum stock-clone notes](docs/stun-serum-stock-clone.md).
The completed greed-based Paralytic/Transmutation split is recorded in
[the Weapon Oil stock-clone notes](docs/weapon-oil-stock-clone.md).

Invigorating Elixer is intentionally scoped to true recruitable heroes. Its
activation, targeting, timed effector, Palace-side count, expiry cleanup, and
repeat-use lifecycle copy the stock Rage of Krolm mechanism. Henchmen were
removed after repeated live tests showed that Majesty's available enumeration
paths select them inconsistently across casts. The complete test record is in
[the Invigorating Elixer research log](docs/invigorating-elixer-research.md).

Phoenix Phial is the third Brewing prototype: a researched, 1,000-gold,
single-charge hero inventory item with a 75-percent chance to resurrect its
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

To build the accepted hero-motion in-game gate without deploying it, use:

```powershell
.\scripts\Build-AlchemistProbe.ps1 -ApprovedSpriteTestSet
```

That explicit mode writes `dist\CustomGuildAlchemistSpriteTest`, bypasses the
regular art cache, and verifies the hash-pinned Walk V4 and Stand V5 sources
before compiling. The wrapper also enables the established two-mod BDEP
compatibility and Siege QA fixture, so The Siege starts with a completed
Laboratory and Test Alchemist ready for motion review. It appends one private
SPLT after the complete retail palette table and replaces only Warrior
Walk/Stand slots `5919–5990` in the private `ALC1` IMAG. Special/cast/death slots
`5991–6052` and attack slots `6055–6118` remain stock fallthrough references
until those actions pass their own visual gates. The generated
`ApprovedSpriteTestSet.json` records every source and packaged-frame hash. The
build command does not copy anything into the game or Majesty Mods directories.

The compiled Walk/Stand TILEs preserve every approved visible body index, add
Majesty's native `247`–`250` shadow-control bands through the pinned
grounded-shadow pipeline, and keep visible/control pixels in separate RLE runs.
Stock Warrior TILEs `5919–5990` are the contact authority: their shadow touches
the lower body in all 72 Walk/Stand frames. Palette roles, base-anchored
projection, literal seam repair, and split-run encoding follow Phantoms Haunt's
[Majesty building shadow notes](../majesty-gold-hd-custom-guild-phantoms-haunt/docs/majesty-building-shadow-encoding.md)
and
[`add_cast_shadow`](../majesty-gold-hd-custom-guild-phantoms-haunt/scripts/generate_phantom_building_sprites.py).
The complete seam contract is pinned to Phantoms commit
`1ac887f55e4c1c67dc8d90829cb099eea87b15ae`; current sibling paths are links
for convenience, not mutable authority.
The Phantom hero's `projected_floating_hero_shadow` is explicitly forbidden for
this grounded hero: its base displacement and body-clearance pass deliberately
create the transparent separation that makes the Phantom read as hovering.

The validator pins all 72 body/control planes and rejects a transparent foot
moat, direct magenta/body contact without the index-247 seam, controls on the
canvas edge, or mixed body/control RLE runs. The approved profile also
privateizes ALC1's stock Interface-00/01/02 frames, so the Alchemist portrait,
selected-unit panel, and Laboratory hero-count icon resolve to nonempty private
art instead of empty retail slots.

The compatibility switch preserves Majesty's complete Northern Expansion BDEP
table and appends the temporary `PHG1` and `ALB1` rules so this package can load
after Phantoms Haunt during the two-mod test. Approved sprite-test builds enable
it automatically. It is a deliberate stopgap for the CAM merger, not the final
distribution model.

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

For repeated Brewing development, add `-IncludeSiegeTestFixture`. Approved
sprite-test builds enable it automatically. This copies and overrides only the
stock `SIEGE()` entry point in the generated probe and spawns completed
player-owned Fervus, Krolm, level-3 Wizard, and Alchemy guilds near the Palace.
It also supplies 100,000 sovereign gold and three funded, level-10 purchase-test
heroes so Phoenix Phial death/resurrection tests can be repeated quickly. The
switch remains off for other builds unless explicitly selected.
