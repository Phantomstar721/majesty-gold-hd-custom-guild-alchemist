# CGAL Runtime Probe

This fixture isolates the AP10-derived custom-panel path before custom hero GPL,
art, inventory, or Brewing effects are introduced.

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
