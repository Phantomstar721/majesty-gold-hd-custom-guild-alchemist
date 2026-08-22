# Alchemist movement and spell confidence

This implementation copies the two distinct mechanisms proven by Phantom's
Haunt. Majesty's XML `Speed` value is an AI-facing chase and escape rating; it
does not determine the unit's actual walking rate. The Alchemist retains the
stock Warrior `Class 1` movement profile, receives a one-time
`MovementRateModifier -50`, matching stock Vigilance's proven movement bonus,
and uses AI Speed rating 2. The AI rating remains between stock Warrior rating
1 and stock Rogue rating 3, while the real movement modifier makes the
Alchemist visibly faster than a Warrior without replacing the walk animation
or creating a movement watcher. The same boolean-guarded sync runs
from both `Alchemist_birth` and `Alchemist_tree`, exactly like the Haunt path,
so it neither misses existing heroes nor stacks on repeated decisions.

Majesty's stock `list_eval` calls `spell_extra_value`; `SpellRank` affects cast
order only. The Alchemist private BCD therefore carries the complete stock
function and appends title-guarded weights using the Haunt's exact pattern:

| Spell | Confidence |
| --- | ---: |
| Flash Flask | 60 |
| Stun Serum | 100 |

Stun Serum receives the larger weight because its five-second disable removes
both movement and action from the target. Spell confidence applies only while
the native spell is currently available; its cooldown removes that
contribution. The stable baseline therefore copies the stock Warrior of
Discord combat estimates (`enemy_estimation .5`, `self_estimation 2.0`) and
the stock Paladin/Warrior-of-Discord 15-percent HP retreat threshold. This is
still Majesty's stock time-to-kill versus time-to-die evaluator; it does not
replace fleeing with a custom bravery rule.

The stock spell clauses remain byte-for-text equivalent. The Phantom branch is
also retained so loading the Alchemist after Phantom's Haunt does not erase its
confidence weights. No custom flee controller, polling loop, or watcher exists.
