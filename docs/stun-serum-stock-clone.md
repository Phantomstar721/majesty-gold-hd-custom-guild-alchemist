# Stun Serum stock-clone contract

Stun Serum is a private clone of the stock `Paralytic Gaze` attack-spell
lifecycle. The stock action supplies the `Cast` animation, Attack spell type,
rank-5 combat priority, 45-second cooldown, and duration-owned cleanup. Only
the private name/IDs, level-5 gate, requested 5-second duration, GPL symbols,
and art channels differ.

The GPL begin/end pair copies stock `Paralytic_Gaze_Begin/End` and therefore
uses the same `Freeze_Unit` / `UnFreeze_Unit` functions as Vines. Begin rejects
dead targets and buildings/lairs, creates the private impact, restraint, and
duration-owned icon, sets `#ATTRIB_HasEffectParalyticGaze`, stops movement,
suspends the target's active script, and marks the paralyzed intent. The icon's
native timeout invokes the sole cleanup callback, which clears the stock freeze
lock and calls `UnFreeze_Unit`. There is no watcher, polling loop, or private
timer.

The three art roles remain independent:

- `ASS1` uses XR30's proven duration-0 attachment-point-2 impact scaffold for
  the broken flask and splash.
- `ASS2` retains CRB1 Vines' complete 30-TILE presentation table but removes
  its callback; it is a visual-only alchemical restraint lasting the same
  five seconds as the owner.
- `ASS3` retains QRc1 Poison's animated overhead-status table and owns the
  private end callback.

The hero keeps Warrior's literal `AttackRange 1..1` and `basic_attack`, so the
dagger remains melee. Its GPL `castingrange` is 130, equal to stock Rogue's
maximum basic-attack range. Stock `attack_object` uses casting range while an
Attack spell is available and engine attack range otherwise; the Alchemist
therefore begins combat by throwing Stun Serum at Rogue range, then closes to
melee once its combat spells are on cooldown.
