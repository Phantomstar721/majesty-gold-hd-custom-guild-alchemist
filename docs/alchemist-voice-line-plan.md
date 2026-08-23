# Alchemist Voice Production

The Alchemist voice set follows the proven Phantom's Haunt audio lifecycle.
Each event has one Audacity project, one automatically isolated clean take,
and one game-ready WAV.

## Processing contract

The Haunt extractor reads Audacity sample blocks directly and applies the same
take boundaries used for the Phantom:

- 20 ms activity windows at a -45 dB threshold;
- pauses up to 0.50 seconds retained inside a line;
- 0.30 seconds of lead padding and 0.20 seconds of tail padding;
- clean two-to-one downsampling from 44.1 kHz to 22.05 kHz.

`scripts/process_alchemist_voice.py` then applies the approved restrained
one-semitone upward resample and slight brightness adjustment. It applies one
uniform gain per performance so the audible windows match the corresponding
stock Rogue and Warrior events. It does not use dynamic compression. A -1 dBFS
safety ceiling prevents clipping without changing Majesty's stock distance,
overlap, phase-group, or cooldown behavior. Every final file is mono, 22,050
Hz, signed 16-bit uncompressed PCM.

## Stock level calibration

`scripts/analyze_voice_levels.py` reads the actual Rogue and Warrior WAVE
records from the installed stock `voices.cam`. It compares active 20 ms windows
above -40 dBFS. Ordinary Alchemist lines target the midpoint of the matching
Rogue and Warrior active RMS values. The cast line retains the louder stock
Wizard cast level. Recruitment uses the ordinary voice midpoint because stock
Majesty has no class-specific recruitment event.

The approved targets are:

| Event | Active RMS target |
| --- | ---: |
| Thrown-bottle cast | -14.77 dBFS |
| Recruitment | -20.00 dBFS |
| Enters combat | -20.35 dBFS |
| Flees combat | -20.89 dBFS |
| Deciding | -19.17 dBFS |
| Pursues reward | -20.98 dBFS |
| Finds item | -21.53 dBFS |
| Idle | -21.28 dBFS |
| Death | -20.00 dBFS |
| Gains level | -20.71 dBFS |
| Sees hostile | -18.40 dBFS |
| Reaches level 10 | -18.37 dBFS |
| Easter egg | -18.00 dBFS |

## Runtime routing

`AXH1` / `Alchy_Hero` is a private clone of the stock Cultist descriptor. It
retains stock event ordering, cooldown groups, hit reaction, and spatial
behavior while replacing the eleven approved personality WAVE targets. Its
Attack phase remains the Warrior and Healer blade hit `WU03`.

The Cultist descriptor has no `VFX_CAST_SPELL1` phase. This is intentional.
Stock `Cast.gpl` requests that phase for every spell, so leaving it absent keeps
Flash Flask on its stock `Drink_Potion` cue only. Stun Serum and Miasma Mist
call the separate `AXC1` / `Alchy_Cast` Begin descriptor after their stock
validation succeeds. That descriptor uses the stock Hero Cast voice cooldown
group.

Majesty has no class-specific recruitment phase. `AXR1` / `Alchy_Hired`
therefore copies Haunt's proven solution exactly: a separate stock-shaped Begin
descriptor and a one-time 20 percent birth roll after the Laboratory home is
confirmed.

## Event map

| Event | WAVE |
| --- | --- |
| Recruitment | `AHS1` |
| Deciding | `AHD1` |
| Idle | `AHI1` |
| Sees hostile | `AHH1` |
| Enters combat | `AHC1` |
| Flees combat | `AHF1` |
| Pursues reward | `AHR1` |
| Finds item | `AHN1` |
| Thrown-bottle cast | `AHC2` |
| Gains level | `AHL1` |
| Reaches level 10 | `AH10` |
| Easter egg | `AHE1` |
| Death | `AHDH` |
