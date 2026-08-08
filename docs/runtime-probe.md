# CGAL Runtime Probe

This fixture isolates the AP10-derived custom-panel path before custom hero GPL,
art, inventory, or Brewing effects are introduced.

The first placement build exposed a prerequisite already solved by Phantoms
Haunt: an XML building `Name` also needs a matching GPL building-data record.
Without it, peasants can receive the construction job but cannot initialize the
site. The probe now registers all three Laboratory levels as ordinary guilds,
using `basic_birth`, `Guild_Birth`, `basic_upgrade`, and the stock
`cultist_tree`. It intentionally does not inherit Fervus birth/death scripts,
which would add temple allegiance and animal-spawning side effects.

## Active-mod order

Enable both entries and place the Alchemist probe after Phantoms Haunt:

1. `Custom Guild: Phantoms Haunt`
2. `Custom Guild: Alchemist (CGAL Probe)`

The probe's temporary BDEP payload contains both `PHG1` and `ALB1`. This is only
for the two-mod experiment while the CAM merger is unfinished.

## Test sequence

1. Start a Palace-level-2 freestyle game with enough gold for construction.
2. Confirm both **Phantoms Haunt** and **Alchemist's Laboratory** are separately
   available in the build list.
3. Build one of each and alternate between their panels several times.
4. Recruit from each. The Laboratory intentionally recruits a stock Cultist,
   labeled **Test Alchemist** in its building panel.
5. Upgrade the Laboratory through levels 2 and 3, reopening its panel after
   each upgrade.
6. Click **BREWING** last.
7. Confirm the stock Elf Guild and Temple to Fervus still open and recruit
   normally.
8. Save, reload, and reopen both custom buildings.

## What to report

- Whether both custom build entries appear simultaneously.
- Whether `CGPH` and `CGAL` retain their own titles, buttons, hero lists, and
  selected-building state while alternating between them.
- What happens when **BREWING** is clicked: a spell window, no action, wrong
  building data, or a crash.
- Whether Laboratory upgrades preserve `CGAL` and the Brewing button.
- Whether the temporary Cultist recruit succeeds and behaves normally.

The most valuable failure report is the last successful step plus the exact
click that failed. A screenshot of any wrong-but-noncrashing panel is useful.

## Result: custom title

Confirmed in game: construction, all three Laboratory levels, and upgrades are
functional with the independent `AlchemistsLaboratory` GPL title. Clicking the
visible **BREWING** control crashes immediately. This reproduces the exact AP10
control that the Haunt fixture had to remove.

The next diagnostic build keeps `ALB1`-`ALB3`, `CGAL`, the generic guild
callbacks, and the custom CAM resources unchanged, but temporarily aliases the
GPL runtime title to `Temple_Fervus`. This tests whether the stock spell callback
looks up AP10 state by building title. It does not adopt `fervus_Birth`,
`fervus_destroyed`, or Fervus animal spawning.

- If **BREWING** opens the stock Fervus spell window, title-based state is the
  missing link and can be intercepted by the future registry/DLL.
- If it still crashes, the missing state is tied to the custom DialogID or
  another executable-only mapping, not the GPL title.
