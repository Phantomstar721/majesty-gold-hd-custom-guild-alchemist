# Project Rule: Clone Stock Majesty Mechanisms

Follow the workspace **Majesty Gold HD: Stock-First Rule (Mandatory)** without
exception. For Alchemist behavior, find and trace the corresponding stock
spell, guild action, panel, effector, or callback and clone its full lifecycle.
Privatize only IDs, resource names, GPL symbols, art/sound references, and the
explicitly requested gameplay values.

Do not invent timers, cleanup paths, markers, watchers, controllers, or state
machines when stock code already provides the mechanism. If no exact stock
analogue exists, stop, explain that fact, and obtain user approval before
designing a custom solution.

Invigorating Elixer specifically uses Rage of Krolm's timed effector lifecycle:
create the private Rage-style effector, apply the stats in stock order, and let
the private effector callback reverse them. Do not replace this lifecycle.
