# Weapon Oil stock-clone contract

Weapon Oil intentionally reuses Majesty's native Guardhouse Arrows research
lifecycle. CGBR contains an exact copy of APa1's compound Arrows research row,
with only its command/control key privatized from stock `0x139C` to `0x2A13`.
The runtime calls the same native row refresh, validation, and research-command
functions used by APa1. Majesty therefore owns the cost,
timing, one-time completion attribute, disabled completed state, command
dispatch, and research-row refresh. No Alchemist timer or research state
machine is permitted.

SMNU record splicing must retain the preceding record's `0xFFFFFFFF`
terminator. AP69's second recipe begins at `0x478`, immediately after the
terminator at `0x474`; treating the terminator itself as part of the replaced
record makes `CYDialogStream` encounter a zero where it expects an opcode and
crash while opening CGBR.

The completed `#ATTRIB_ResearchArrows` flag is scoped to the Laboratory. It is
used only as the eligibility gate for the economy service; the Laboratory does
not run `Building_Guard`, so it does not acquire the Guardhouse arrow behavior.

## First hero-purchase proof: literal poison

The first Weapon Oil economy proof deliberately stops at stock poison. It does
not yet contain Paralytic Oil, Greed selection, diminishing returns, or a
private combat effector.

The Alchemist BCD overrides stock `Purchase_Equipment` with a literal stock
clone. Completed, researched `AlchemistsLaboratory` buildings are collected in
a separate `alchemyLabs` list and are never appended to `wizGuilds`; real
Wizard's Guild weapon and armor enchanting therefore remain unchanged.

The clone derives `Wants_Oil` from two existing stock hero-class properties:
`WeaponTypeIndex > 0` and `Upgrade_Weapon_Chance > 0`. The latter is used only
as a boolean marker that this hero class participates in ordinary weapon
upgrades; it is not rolled. This admits weapon-using combatants while excluding
unarmed Monks and non-weapon casters without maintaining a custom hero list.
The stock `Wants_Poison` roll remains untouched and is still used only by the
Rogues Guild `Poison_Check` branch. Oil ownership does not suppress that roll.

`Alchemy_Oil_Check` remains a private `WizGuild_Check` lifecycle clone: it
preserves the stock completed-building search radius, affordability check,
loyalty-aware closest-building selection, visiting task, and `Use_Building`
dispatch. Weapon Oil deliberately omits Wizard enchanting's additional
Intelligence roll because eligibility is generic to weapon users rather than
spellcraft aptitude. Its private purchase price is exactly 100 gold. The other
semantic changes remain the researched Laboratory candidate list, the
single-tier completion gate, and a private transaction task marker.
Once a hero owns oil, the oil check returns false and the same equipment pass
continues to the untouched stock `Poison_Check`, so a level-2 Rogues Guild
remains available under its original poison-chance and Artifice rules.

The Laboratory branch uses private intent index `309`, appended after the
complete stock/expansion AITX table in a private `GPLtext.cam` provider. Every
existing AITX record is copied unchanged; index `309` alone contains `Applying
weapon oil at the alchemy lab`. `Alchemy_Oil_Check` is the only caller of that
index. The stock Rogues Guild path continues to call index `10` and display
`Poisoning weapon`, so no hero decision tree or stock localization is changed.

All three Laboratory levels use the combined `Alchemy_Lab_Visited` dispatcher,
whose oil branch is a private clone of Wizard `Enchant_Equipment`. It retains
stock entry, the 17-second visit interval, payment to the target building, and
the complete `Done_Enhancing_Equipment` exit/reset lifecycle.
`Obtain_Alchemy_Oil` copies the level-1 `Obtain_Enchantment` transaction. Its
travel, timing, payment, revenue, exit, and decision restart remain stock; only
the private coating payload differs.

## Private oil split

The completed implementation preserves native Rogues Guild poison exactly as
`WeaponPoisoned == 1`. Oil is an independent persistent integer attribute named
`AlchemyWeaponOilType`: `1` is Paralytic Oil and `2` is Transmutation Oil. It is
created once with the same `$HasAttribute` / `$AddAttribute` agent-property
contract used by the Haunt's persistent perks, then assigned during the stock
enchantment purchase transaction. A hero may therefore own one oil, native
poison, and Wizard weapon enchantment simultaneously. The oil check rejects
only an already-owned oil; it neither reads nor writes `WeaponPoisoned` or the
stock magic-bonus attributes.

The first presenter attempt cloned the Magic Bazaar's timed
`Speed_Tonic_Icon`, removed its callback, and changed it to an infinite
lifetime. Live testing proved that this hybrid did not appear in the native
Enchantments list; `Menu=11` alone was not a complete persistent-presenter
contract.

Live testing also disproved the Magic Ring and Petrify presenter experiments;
neither appeared. The inferred `StackPriority` explanation was wrong.

The hero Spells/Enchantments controller is AP78, not AP22. This was proven from
the live dialog-factory lifecycle and then traced against both supported
executables. AP78 setup calls the Enchantments population function at Public
`0x004A3830` / Beta2 `0x004A4110`. That function obtains the selected hero's
active-effect collection, iterates its live effect objects, reads the effect's
overlay-description pointer at `effect + 0x90`, and reads that overlay's own
FourCC at description `+4` (Public `0x004A3971` / Beta2 `0x004A4251`).

AP78 then uses a hard-coded switch over stock overlay FourCCs. Each recognized
case supplies a hard-coded stock global-text index and icon/presentation index,
builds one stock rich-text row, and appends it to Enchantments control
`0x221B`. An unrecognized FourCC jumps directly to the next effect without
creating a row. The switch does not use the overlay's XML name, description,
`Menu`, `StackPriority`, `ImageIDBase`, GPL attributes, or lifetime flags as a
fallback. Examples of recognized stock IDs include `XR01` for Speed Tonic and
the stock Magic Bazaar/Ring effect IDs; private IDs have no generic path.

The focused Beta2 live trace on 2026-08-22 captured the private Transmutation
Oil presenter reaching that exact switch as `imageId=ALo2`. AP78 omitted it
because `ALo2` is not a stock switch case. This also explains why setting the
private descriptor's `ImageIDBase` to stock `XR01` did not help: AP78 tests the
private overlay ID `ALo2`, not its rendered image channel. The trace itself was
removed after it captured this result; it was diagnostic-only and its first
implementation crashed after logging the candidate.

There is therefore no data-only stock mechanism for listing independently
private `ALo1`/`ALo2` effectors with their own names in AP78. Reusing a stock
recognized overlay ID would collide with and relabel that stock effect. The
approved runtime extension intercepts only AP78's first stock FourCC compare.
It aliases `ALo1`, `ALo2`, and `ALo3` to the already-recognized `XR01` case for
the duration of that one synchronous row build, then substitutes only the text
argument at XR01's unchanged stock string-assignment call. Every stock ID,
branch, icon/presentation index, rich-text construction call, append call,
refresh, and cleanup remains byte-for-byte on its original path. Public and
Beta2 use separately fingerprinted switch, call, and assignment addresses and
fail closed if any stock byte changes.

AP78 has one rich-text row per effect, not the Special Items panel's dedicated
description control. The private rows therefore use compact single-line text:
`Paralytic Oil - brief stun on weapon hit`, `Transmutation Oil - +5 gold on
weapon hit`, and `Poisoned Weapon - poison on weapon hit`.
A separately styled second description line would require a panel-layout
extension and is outside this scoped switch clone.

Native weapon poison is a persistent `#ATTRIB_WeaponPoisoned` value and does
not create a stock effector, so it otherwise never enters AP78's active-effect
collection. The packaged `Obtain_Poison` is a literal clone of the stock
central purchase callback with one post-attribute insertion: it creates the
private, static, invisible, duration-1/Infinite `ALo3` presenter. The stock
attribute remains the sole gameplay owner; `ALo3` has no script, stats, world
art, or cleanup. The package retains the same Magic-Ring-lifetime presenter
contract for all three rows. Oil presenters are created
by a private literal clone of `Done_Enhancing_Equipment`, immediately after
stock `Exit_Building`, rather than while the hero is hidden inside the Lab. The
overlays do not own state, combat timing, gold, poison, or paralysis cleanup.
All three descriptions use stock `XR01` art and `NotVisibleInISOView`.

The stock `Obtain_Enchantment` transaction still owns travel, visit duration,
payment, building revenue, exit, and decision-tree restart. Its only new choice
uses the hero's existing stock `Greed` property: values greater than 20 receive
Transmutation Oil; all other eligible weapon users receive Paralytic Oil. This
puts stock Warriors, Rangers, Barbarians, and Dwarves on Paralytic Oil while
Elves, Rogues, and the greed-30 Alchemist choose Transmutation Oil.

The packaged `damage` function is generated from an exact stock clone. Its
native `WeaponPoisoned == 1 -> Poison_begin` block is unchanged; an adjacent
guarded read of `AlchemyWeaponOilType` is the only modification. The Paralytic
status uses Vines' exact effector-owned `Freeze_Unit` lifecycle. One private
Vines-derived restraint, `alchemist_paralytic_oil_restraint`, owns the duration
and `Alchemy_Paralytic_Oil_End` cleanup callback and is created with stock's
`"after"` ordering. An A/B using the default creation path did not change world
layering. Its private `ASO3` image channel contains the approved
copper-and-acid-green alchemical restraint animation. It does not create Stun
Serum's broken-bottle impact, restraint, or overhead potion debuff icon.
The private image preserves Vines' two-set topology. Following the Haunt Frost
Armor freeze implementation, every TILE uses one fixed 108-by-113 canvas: the
first five opening frames grow the complete cage upward from fixed roots, every
remaining opening and active-loop frame repeats the exact completed cage, and
stock effector cleanup releases it. A grow/shrink sequence must never be spread
across Vines' active loop, because that makes the restraint collapse and regrow
while the target is still paralyzed.
Consecutive completed applications last
3, 2, then 1 game-second, after which a stock duration-owned invisible effector
provides 10 seconds of immunity and resets the sequence. Private value 2 calls stock
`Give_Gold` for 5 gold on each confirmed physical hit, preserving the native
gold adjustment and floating-gold feedback.

`damage` is a global GPL symbol, like `Purchase_Equipment`, so CAM merger output
must merge this narrow stock-derived branch with any other mod that replaces
the same function.

Live proof on 2026-08-11 used a Siege-only QA Rogue beside a pre-researched
Laboratory. Its ordinary earlier equipment upgrades were marked complete and
its affordability was guaranteed. The normal `Purchase_Equipment` entry
immediately selected the Laboratory; the Rogue entered, completed the stock-
timed visit, paid, exited, and received stock poison. The development fixture
now supplies a Rogue, Warrior, and Alchemist for generic-eligibility testing;
it is enabled only by the explicit Siege QA build switch and is not gameplay
content.

Because `Purchase_Equipment` is a global GPL symbol, other CAMs that replace it
must be merged at that symbol. This is a known CAM-merger responsibility, not a
reason to replace the stock lifecycle with a custom watcher.

## AP10/APa1 compatibility seam

The native command sets `#ATTRIB_CurrentResearch` on the Laboratory. AP10's
Guild activity renderer (`0x004962E0`) assumes every active operation has Guild
command metadata; Guardhouse research does not. Its lookup therefore returns
null and stock AP10 dereferences it at `0x0049643D`. AP17 avoids that renderer
because it is a different building-controller class.

With explicit approval to combine those otherwise incompatible stock features,
the scoped CGAL vtable skips only AP10 activity method 13 while
`CurrentResearch == 0x2A13` (the private Weapon Oil clone). During that interval CGBR is refreshed
with APa1's native research-row iterator. The stock AP10 activity method resumes
as soon as the native attribute clears. APa1's post-submit primary-dialog
rebuild is also omitted because it would replace CGBR with the incompatible
AP10 primary. Research command construction, payment, timing, state ownership,
completion, cancellation, and cleanup remain native and unchanged.

APa1's clickable Arrows row does not own or draw the blue progress bar. It
disables itself while research is active. Stock progress is instead drawn in
the Guardhouse's AP17 *primary* panel by method `0x00496AD0`, using controls
`0x1194`, `0x1195`, and the primary Research button `0x2293`.

Do not call all of `0x00496AD0` against CGBR. That method is a complete AP17
primary-panel renderer, not an after-click renderer for APa1's row. Invoking it
in the AP69-derived CGBR controller crashed at `MajestyHD.exe+0xAE4E8` because
it assumes the rest of AP17's primary-panel control graph.

AP17's `0x1194/0x1195` control records are also not compatible with AP69's
post-construction lifecycle. They resolve through the streamed-control lookup,
but AP69 subsequently crashes at `MajestyHD.exe+0xAE4E8` even when no custom
visibility or progress operation is issued. They must not be included in CGBR.

CGBR instead uses a second private clone of AP24's display pair—the same
control class already proven stable for Vigor—positioned over Weapon Oil with
private IDs `0x2A11/0x2A12`. The first clone omits only AP24's final end-of-
stream word so the existing Vigor clone remains the owner of the final double
`0xFFFFFFFF` marker. Its label terminator and every control opcode remain
stock. The runtime feeds this compatible display AP17's native research
timestamps and exact `[7, elapsed, 0, duration]` progress message; APa1 remains
the owner of command submission, completion, and disabled row state.

APa1 renders the Arrows glyph with a separate 25-by-25 control at `(3,60)`,
not as part of the clickable research row. CGBR clones that complete control
in the first brew row and changes only its control ID to command-plus-500
(`0x2C07`), and redirects
`INCr` set `1007` to the private `ALWI` image record. `ALWI` retains the stock
one-frame research-icon animation and replaces only its TILE with the Weapon
Oil artwork. Do not bake the icon into the button background or add a custom
draw hook.

APa1 likewise renders the gold research cost through a separate `0x98`-byte
control at `(154,64,40,17)`. It is not embedded in the clickable Arrows row.
CGBR clones that complete control at `(151,63,40,17)` and preserves
APa1's derived-ID contract: the icon is `command + 500` and the price field is
`command + 1000`. The native row presenter at `0x004A8870` targets those exact
children when it applies state and formats the descriptor's live cost. Merely
cloning the clickable row leaves the price window absent.

## Completion alert name

The private descriptor preserves Arrows' duration, level-1 gate, name plumbing,
and completion attribute, with descriptor field `+0x08` set to the final
250-gold research price. Stock `0x004A65A0` consumes that same field for
the affordability check, row price text, treasury deduction, and research
submission, so the displayed and charged values cannot diverge. Real
Guardhouse Arrows retains its stock 250-gold descriptor.

The stock completion callback begins at `0x004DFE20`. It reads
`#ATTRIB_CurrentResearch`, resolves the native research descriptor through
`0x004A86E0`, applies the descriptor's completion attribute, formats GMTX
`0xBC` (`Research Complete`) with the descriptor name, posts the green alert,
and only then clears `#ATTRIB_CurrentResearch` and the duration attribute.

Stock constructs the Arrows descriptor at `0x004A7F40` with the exact tuple:
level `1`, completion attribute `#ATTRIB_ResearchArrows` (`0x2A425041`), GMTX
name `Arrows` (`0xCA`), and command key `0x139C`. The runtime asks the stock
resolver for that descriptor, copies all five descriptor dwords literally,
and registers the copy under private key `0x2A13`. Thus row validation,
payment, duration, attribute application, completion, and cleanup all traverse
the same native code, while the private descriptor has an identity distinct
from real Guardhouse Arrows.

Globally changing GMTX `0xCA` would also rename Guardhouse research. The
runtime instead preserves the complete stock completion callback and, at its
existing name push at `0x004DFFC7`, substitutes `Weapon Oil` only when `EBX`
is the private cloned descriptor. The stock prefix, formatter, green-alert
dispatch, color, timing, completion attribute, and cleanup are untouched.
Real Guardhouse descriptors continue through the original `EDI` name pointer
and still post `Research Complete: Arrows`.

## Completed-row lockout

APa1's setup iterator at `0x004A8AE0` only discovers streamed controls whose
IDs are in its hard-coded stock range `[0x1388, 0x13EC)`. A private `0x2A13`
row is therefore invisible to the iterator even though the stock descriptor
resolver understands it. Do not recreate the enabled/disabled logic. Call the
iterator's exact per-row worker at `0x004A8870` directly with the CGBR panel,
Laboratory context, and `0x2A13`. That stock worker reads descriptor field
`+0x10` (`#ATTRIB_ResearchArrows`) and owns the completed lockout, current-
research state, level gate, price, control art, and tooltip refresh.

APa1's click path also calls its native eligibility function at `0x004A8B40`
before submitting the research command. The custom controller must preserve
that call before `0x004C2C60`; this makes completion a hard one-time gate even
if a stale click event reaches the row before its disabled presentation has
repainted.

## Dedicated Laboratory research owner

Live testing proved that AP10 recruitment and APa1/APa3 research share the
same three-field building activity tuple:

- `#ATTRIB_CurrentResearch` (`APB,`);
- the activity start tick (`APB8`);
- the activity duration (`APB\r`).

That stock tuple cannot represent recruitment and research simultaneously.
Recruit completion could therefore complete research early, while active
research could make the Recruit button inert. There is no stock building that
runs those two activities concurrently, so the user explicitly approved one
custom owner for this combined Laboratory surface.

The runtime keeps the customization as narrow as possible:

1. Snapshot the Laboratory's complete native activity tuple, including an
   active Alchemist recruitment.
2. Clear the tuple only across the synchronous stock APa1/APa3 eligibility and
   command-queue submission calls, then restore it immediately.
3. Let stock validate level, gold, completed flags, charge the player, select
   duration, and construct the recipe activity.
4. On the stock game update that applies the queued command, snapshot AP10's
   live tuple before the update, capture the exact recipe/start/duration values
   stock produces, then restore the pre-update AP10 tuple byte-for-byte.
5. Advance the captured recipe with Majesty's simulation clock on the existing
   state-3 update dispatch. No OS timer, worker, watcher, or GPL polling thread
   is introduced.
6. Stock submission has already scheduled native event `0x2009`, whose handler
   is the complete research callback at `0x004DFE20`. During the final
   simulation second, snapshot the then-current AP10 activity and stage the
   captured recipe tuple only around each stock game update. This lets the
   already-scheduled event invoke its handler through Majesty's native event
   dispatcher; the DLL must never call the handler directly.
7. Stock applies the cloned completion attribute, formats and posts the green
   completion alert, and clears its tuple. After the stock update returns, the
   runtime observes that cleanup and restores the AP10 activity byte-for-byte.
   AP17 never invokes AP10's guild-activity renderer during this lifecycle, so
   the Laboratory clone preserves that class boundary for the entire staged
   stock update. Guarding only while `CurrentResearch` contains the private
   recipe is insufficient because stock clears that attribute partway through
   the same update; allowing a later AP10 activity pass dereferences incomplete
   guild state at `MajestyHD.exe+0x9643D`. An upgrade can replace the live CGAL
   panel context before research completes, so this one-update boundary is
   scoped by the private CGAL vtable itself rather than the context pointer
   captured when research began.
8. CGBR inherits AP69 only as its streamed-panel controller. During that same
   staged completion update, it suppresses AP69's Fervus spell-event renderer;
   stock AP17 research never enters that renderer. The normal post-update APa1
   refresh then restores the completed private row. The completion guard begins
   only after the research tuple has been staged; moving it ahead of those
   writes perturbs ordinary AP10 recruitment-completion ordering and crashes at
   `MajestyHD.exe+0x9643D`. A brief underlying Fervus-icon flash remains a
   cosmetic issue and must not be fixed by changing this proven lifecycle.
   The AP10 guard remains active through restoration of the saved Laboratory
   activity tuple and is cleared only afterward. Those restoration setters also
   synchronously dispatch activity; clearing sooner exposes half-restored
   recruitment state to AP10 at `MajestyHD.exe+0x9643D` when both operations
   complete together.

Stock also rejects starting research after an upgrade has claimed the building
activity tuple. This native eligibility rule remains intact. Allowing that
additional combination has no stock analogue and would require a separately
approved custom ownership exception.

The owner is shared by Weapon Oil and Phoenix Phial, so those recipes are
mutually exclusive. It does not own or inspect Vigor's Palace/Rage state and it
does not retain the Laboratory activity tuple, so one research, Vigor, and one
Alchemist recruitment can run concurrently.
