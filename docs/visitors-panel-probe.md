# Visitors panel stock-clone probe

The Laboratory Visitors button is a literal clone of the stock Blacksmith
`AP02` Visitors control. The cloned record retains command ID `0x1F55`, the
stock button class, command dispatch, and visitor-window lifecycle. Only its
CGAL position, width, string indices, and already-private `ALBB` frame resource
are changed.

The stock control reads Majesty's existing building occupant list. Weapon Oil
already uses stock `$Enter_Building`, so a hero undergoing the 17-second oil
visit should appear without a custom list, watcher, or DLL hook.

The first live test placed the button at `(7,190,93,26)`, directly beneath
Heroes and over the left half of Recruit. That proved AP10's inherited
`0x1F55` dispatch without resizing any established controls.

The accepted layout keeps every button at its stock 93-by-26 size. Visitors
now occupies Brewing's former upper-right rectangle `(103,162,93,26)`.
Brewing's complete AP10 secondary-control parent moves to the otherwise-empty
lower-left rectangle `(7,217,93,26)`, beside the stock navigation arrows.
Heroes remains at upper-left and Recruit retains its full-width row.
