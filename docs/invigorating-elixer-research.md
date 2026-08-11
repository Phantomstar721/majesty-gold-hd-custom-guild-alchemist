# Invigorating Elixer Research Log

The complete reusable UI method for a labeled timed-effect bar in a custom
subpanel is documented in the expanded-building-slots repository under
`docs/rage-of-krolm-reference.md`, section **Reusable recipe: timed effect bar
inside a custom subpanel**. It records the proven `INSr` clone, private IMAG and
single-span frame, positional STRT index 28, AP24 display messages, simulation
clock refresh, Palace mutual exclusion, GPL cleanup, and regression checklist.

## Final prototype scope

Invigorating Elixer affects true player heroes only. This is deliberate. The
hero path was repeatedly confirmed in game to apply, expire, clean up, and
re-arm correctly when implemented as a private clone of Rage of Krolm.

The final brew costs 1 gold for testing and lasts 30 seconds of simulation
time. Each affected hero receives:

- 20 current and maximum hit points;
- 1 Self_Estimation;
- -200 MovementRateModifier;
- the stock speed-trail behavior.

The implementation copies Rage's exact target query:

```gpl
$ListObjects(ThisAgent, "hero", -1, Heroes, #MyPlayer,
    #InsideOtherUnits, #NoHiddenMap, #CheckSubtypes, "Hero");
```

It also preserves Rage's ordering: create the timed effector, apply the stat
changes, count affected heroes on the Palace, and let the effector's expiry
callback reverse the changes and decrement that count. Only private Alchemist
resource names, values, duration, and sound are substituted.

## Henchman experiments removed from the build

Majesty classifies peasants, female peasants, tax collectors, city guards,
veteran city guards, Palace guards, and caravans as the `Henchman` subtype.
The requested realm-wide version was tested through every relevant stock
enumeration pattern found during this work:

1. Broad `hero` and `monster` queries produced partial selections.
2. `#CheckSubtypes, "Henchman"` sometimes selected all visible henchmen on the
   first cast, then omitted guards or all henchmen on later casts.
3. The stock visible/invisible/camouflaged/hidden union used by
   `List_Heroes_near_flag` improved outdoor selection but omitted contained
   units and still failed inconsistently on repeats.
4. Rage's raw `hero` query followed by `$ListSubtypes(..., "Henchman")`
   included contained henchmen on the first cast, but later casts remained
   selective or empty.
5. Adding stock building `Occupants`, `Guards`, and `$GetBuildingContents`
   lists, with `$AgentInList` deduplication, reached units inside buildings but
   did not make repeat selection reliable.
6. Alternating effectors was considered and rejected. It would conceal the
   enumeration problem and diverge from Rage's single-effector lifecycle.
7. A temporary `OutputDebugStringA` import hook for filtered `$DebugOut`
   diagnostics caused the Elixer click to crash. The hook and all GPL
   diagnostics were removed.

For henchmen that were selected, the private Rage-style effector correctly
removed the icon, trail, movement change, hit points, and self-estimation at
expiry. Runtime logs also confirmed that repeat clicks reached the private GPL
function. The Palace count is a binary re-arm gate for the UI; it cannot
explain why a subset of henchmen was selected inside one invocation.

## Conclusion and restart point

The unresolved problem is Majesty's state-dependent henchman discovery, not
Rage's proven application or cleanup lifecycle. No more query combinations,
watchers, alternating clones, or custom cleanup controllers should be added by
guessing.

If realm-wide henchmen support is revisited, first identify and reproduce an
exact stock mechanism that reliably revisits every henchman across repeated
casts. If none exists, stop and obtain explicit approval before pursuing a
different architecture such as a birth/death-maintained unit registry or
deeper engine reverse engineering.
