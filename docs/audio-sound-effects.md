# Alchemist sound-effect contract

The Alchemist package follows stock Majesty sound ownership and changes only
the private names or wave references needed by the guild.

## Stock-owned routes

- Flash Flask follows the healing-potion route. Its duration-zero activation
  effector uses the stock `Drink_Potion` sound, including the existing cork
  pop. The inherited Shield of Light action sound is removed so the cue plays
  exactly once from the effector.
- The Alchemist hero sound is a complete private clone of stock `Cultist`.
  Its normal personality phases point to the approved Alchemist performances,
  while `Attack` changes from `WU04` to `WU03`, the blade impact used by
  Warriors and Healers. The stock Cultist template deliberately has no cast
  phase, which keeps Flash Flask on the potion sound alone.
- Stun Serum and Miasma Mist explicitly play the private `Alchy_Cast` Begin
  phase. This uses the stock Hero Cast voice cooldown group while excluding
  Flash Flask from the line.
- Recruitment follows Phantom's Haunt exactly: a separate stock-shaped
  `Alchy_Hired` Begin descriptor is called by a one-time 20 percent roll after
  normal hero birth confirms the recruiting Laboratory.
- The Laboratory sound is a complete private clone of stock `FervisTemple`.
  Only the `Select` wave changes. Stock hit and ambient phases remain intact.
- Stun Serum and Miasma Mist share one private sound cloned from Shield of
  Light's `Begin` phase and `Spell_Group`. Only its wave is changed to the
  approved bottle break.

## Private wave assets

Both packaged files are mono, 22,050 Hz, signed 16-bit PCM WAV files.

| Wave ID | File | Purpose | Source and license |
|---|---|---|---|
| `AXBK` | `assets/audio/alchemist-bottle-break-game.wav` | Stun Serum and Miasma Mist cast cue | Freesound `Bottle Smash FF141` by martinimeniscus, CC0: https://freesound.org/people/martinimeniscus/sounds/163029/ |
| `AXLB` | `assets/audio/alchemist-laboratory-select-game.wav` | Laboratory selection cue | Composite of Freesound `burbujas_bubbles.wav` by JavierSerrat and `Glass Bottle Clink` by twohoursago, both CC0: https://freesound.org/people/JavierSerrat/sounds/464187/ and https://freesound.org/people/twohoursago/sounds/135039/ |

After the first in-game test, both private effects received the approved 2.0x
gain adjustment. The Laboratory cue now peaks at 21,000. The bottle break now
peaks at the signed 16-bit limit, with saturation affecting one sample. Stock
sounds and their original levels remain unchanged.

The two private WAV records are packaged in `Data/alchemist_audio.cam`.
The thirteen voice WAVs use the same format and live beside the two private
effects in `Data/alchemist_audio.cam`. `Data/alchemist_sounddesc.cam` supplies
the runtime DSND registrations. Loose
`Sound` XML is retained only as a readable description of the intended phase
routes because Majesty does not register new sound names from loose XML.

The DSND records follow the proven CAM audio path used by Phantom's Haunt:

- `Alchy_Vigor` clones the complete stock `Drink_Potion` DSND.
- `Alchy_Bottle` clones the complete stock `Shield_of_Light` DSND and changes
  only its `Begin` WAVE from `SL35` to `AXBK`.
- `Alchy_Lab` clones the complete stock `FervisTemple` DSND and changes only
  its `Select` WAVE from `BT01` to `AXLB`.
- `Alchy_Hero` clones the complete stock `Cultist` DSND, privatizes its eleven
  normal voice targets, and changes `Attack` from `WU04` to `WU03`.
- `Alchy_Cast` and `Alchy_Hired` clone the single-phase `Rage_of_Krolm` DSND.
  Their Begin phases use the stock Hero Cast and Voice Special cooldown groups.

Build validation rejects extra records, wrong identifiers, changed payload
bytes, missing DSND registrations, empty audio, compression, stereo audio, or
any sample format other than the stock 22,050 Hz signed 16-bit mono contract.
