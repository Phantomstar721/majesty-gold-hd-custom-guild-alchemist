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

Only after stock calculates `Wants_Poison` from the hero's
`Poison_Weapon_Chance` does the new branch call `Alchemy_Oil_Check`. That
function is a private `WizGuild_Check` clone: it preserves the stock completed-
building search radius, affordability check, Intelligence roll, loyalty-aware
closest-building selection, visiting task, and `Use_Building` dispatch. The
only semantic changes are the researched Laboratory candidate list, the
single-tier completion gate, and `Task_Number = #ATTRIB_WeaponPoisoned`.
Failure falls through to the untouched stock `Poison_Check`, so a level-2
Rogues Guild remains a valid fallback.

All three Laboratory levels use `Visited_Script
Alchemy_Oil_Enchant_Equipment`, a private clone of Wizard
`Enchant_Equipment`. It retains stock entry, the 17-second visit interval,
payment to the target building, and `Done_Enhancing_Equipment` cleanup.
`Obtain_Alchemy_Oil` copies the level-1 `Obtain_Enchantment` transaction and
sets the stock `WeaponPoisoned` attribute to exactly `1`. The explicit
single-tier clamp is required because stock combat tests `WeaponPoisoned == 1`;
letting a level-2 or level-3 Laboratory apply Wizard enchantment tiers would
produce invalid poison values `2` or `3`.

After purchase, the untouched stock `make_attack -> Poison_begin` path owns
the on-hit effect. This checkpoint exists solely to prove autonomous hero
selection, travel, payment, building revenue, persistent coating, and the
existing poison combat result before privatizing the effect as Paralytic Oil.

Live proof on 2026-08-11 used a Siege-only QA Rogue beside a pre-researched
Laboratory. Its ordinary earlier equipment upgrades were marked complete and
its stock affordability and Intelligence gates were guaranteed. The normal
`Purchase_Equipment` entry immediately selected the Laboratory; the Rogue
entered, completed the stock-timed visit, paid, exited, and received stock
poison. The forced Rogue and pre-research setup were removed immediately after
that proof and are not part of the gameplay package.

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

## Completion alert name

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

## Deferred stock-channel collision

If the Laboratory is recruiting an Alchemist when Weapon Oil research starts,
the research progress currently completes immediately when recruitment
finishes. This indicates that AP10 recruitment and APa1 research are sharing an
activity/completion channel on the combined custom building controller. Do not
paper over this with a private timer or independent research state. Before
changing it, trace both stock lifecycles through their activity ownership,
completion callback, attributes, and controller refresh, then determine the
smallest stock-compatible separation. This is deliberately deferred while the
basic Weapon Oil research path is completed.
