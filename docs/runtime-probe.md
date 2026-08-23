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
2. `Custom Guild: Alchemist Lab`

The probe's temporary BDEP payload contains both `PHG1` and `ALB1`. This is only
for the two-mod experiment while the CAM merger is unfinished.

## Test sequence

For fast panel iteration, build with `-IncludeSiegeTestFixture` and start **The
Siege**. The probe pre-places a completed Temple to Fervus and Alchemist's
Laboratory near the player Palace. This quest override is development-only and
is absent from default builds.

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

## Result: AP10 title alias

Confirmed in game: clicking **BREWING** still crashes immediately when the
Laboratory's GPL title is temporarily aliased to `Temple_Fervus`. The title is
therefore not the missing key. Stock AP10 receives executable-side secondary
window/callback state that an unknown `CGAL` ID does not receive from the shared
constructor alone.

Windows Error Reporting records both Brewing failures as access violations at
`MajestyHD.exe+0x25984` (VA `0x00425984`). Disassembly shows this instruction
dereferences the controller returned by the common factory at `0x0050AC00`;
that return is null. This is the same failure boundary as the first unsuccessful
CGPH factory experiment, now triggered for AP10's requested secondary window.

The default probe has returned to the independent `AlchemistsLaboratory` title
and now zeroes the unsupported control's hitbox, using the same proven safeguard
as Phantoms Haunt. `-EnableUnsafeBrewingControl` exists only to reproduce this
crash during runtime-hook development. A functional Brewing window now belongs
to the DLL/controller-registry milestone, not the data-only CAM fixture.

## Result: AP69 factory mapping

Factory tracing identified the stock Fervus route as `AP10 -> AP69` and the
custom route as `CGAL -> 0x00000000`. Translating the armed CGAL zero request to
AP69 creates a stable controller in the correct sidebar layer, but its geometry,
labels, lists, and button actions are uninitialized. Activating a blank action
produces another zero child request.

This establishes that AP69 is the correct controller class but its remaining
context is not carried by the final FourCC alone. The next combined diagnostic
uses the AP69 DLL mapping with the temporary `Temple_Fervus` GPL title alias to
test whether the controller obtains its layout and spell-provider context from
the building title. The production design remains `CGAL` plus an independent
`CGBR` resource/action namespace; a global Fervus title alias is not acceptable.

## Result: AP10 context substitution

The GPL title alias did not change the malformed AP69 window. Factory argument
tracing then showed stock AP69 and the translated CGAL request use different
shared controller/resource-context pointers. The runtime captured AP10's live
context and supplied it to the translated request while preserving CGAL's
per-window pointer; the malformed window remained unchanged. Therefore the
missing initialization occurs before the common dialog factory call or through
additional AP10-owned state, rather than in the FourCC, GPL title, or the two
constructor arguments alone.
