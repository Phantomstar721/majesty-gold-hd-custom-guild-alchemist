from __future__ import annotations

import argparse
import array
import math
from pathlib import Path
import wave


SAMPLE_RATE = 22_050
PITCH_SEMITONES = 1.0
BRIGHTNESS = 0.04
LIMITER_CEILING_DB = -1.0
DEFAULT_ACTIVE_RMS_DB = -20.0


def read_mono_pcm16(path: Path) -> list[float]:
    with wave.open(str(path), "rb") as source:
        if source.getnchannels() != 1:
            raise ValueError(f"{path}: expected mono audio")
        if source.getsampwidth() != 2:
            raise ValueError(f"{path}: expected 16-bit PCM audio")
        if source.getframerate() != SAMPLE_RATE:
            raise ValueError(f"{path}: expected {SAMPLE_RATE} Hz audio")
        frames = source.readframes(source.getnframes())
    samples = array.array("h")
    samples.frombytes(frames)
    return [sample / 32768.0 for sample in samples]


def low_pass(samples: list[float], alpha: float) -> list[float]:
    output: list[float] = []
    state = 0.0
    for sample in samples:
        state += alpha * (sample - state)
        output.append(state)
    return output


def resample_linear(samples: list[float], factor: float) -> list[float]:
    """Resample by factor, changing pitch and duration together."""
    output_length = max(2, round(len(samples) / factor))
    output: list[float] = []
    for index in range(output_length):
        position = min(index * factor, len(samples) - 1)
        left = int(position)
        right = min(left + 1, len(samples) - 1)
        fraction = position - left
        output.append(samples[left] * (1.0 - fraction) + samples[right] * fraction)
    return output


def active_rms(samples: list[float]) -> float:
    window = round(0.020 * SAMPLE_RATE)
    active: list[float] = []
    for start in range(0, len(samples), window):
        chunk = samples[start : start + window]
        rms = math.sqrt(sum(sample * sample for sample in chunk) / len(chunk))
        if 20.0 * math.log10(max(rms, 1.0e-12)) > -40.0:
            active.extend(chunk)
    if not active:
        raise ValueError("Voice input contains no audible samples")
    return math.sqrt(sum(sample * sample for sample in active) / len(active))


def process(samples: list[float], target_active_rms_db: float) -> list[float]:
    # Match the Haunt's natural resampling treatment, but in the opposite
    # direction and at a deliberately restrained one-semitone adjustment.
    pitch_factor = 2.0 ** (PITCH_SEMITONES / 12.0)
    voice = resample_linear(samples, pitch_factor)

    # A restrained high-shelf emphasis brightens the resonance after the
    # upward shift without replacing the original consonant transients.
    low = low_pass(voice, alpha=0.18)
    voice = [sample + (sample - base) * BRIGHTNESS for sample, base in zip(voice, low)]

    # Calibrate the audible part of each performance against the matching
    # stock Rogue and Warrior WAVE records. Majesty retains ownership of all
    # distance, overlap, and cooldown behavior in the cloned DSND phases.
    target_rms = 10.0 ** (target_active_rms_db / 20.0)
    # Re-evaluate after each gain step because quiet leading/trailing windows
    # can cross the same -40 dBFS activity threshold used by the stock audit.
    # This is still one uniform gain for the whole performance, not dynamic
    # compression.
    for _ in range(4):
        gain = target_rms / active_rms(voice)
        voice = [sample * gain for sample in voice]

    # The measured stock targets leave ordinary headroom. This safety ceiling
    # is uniform attenuation only, so it does not add the compressed character
    # rejected during the first voice review.
    limiter_ceiling = 10.0 ** (LIMITER_CEILING_DB / 20.0)
    peak = max(abs(sample) for sample in voice)
    if peak > limiter_ceiling:
        voice = [sample * (limiter_ceiling / peak) for sample in voice]

    fade_samples = round(0.008 * SAMPLE_RATE)
    for index in range(fade_samples):
        voice[-1 - index] *= index / fade_samples
    return voice


def write_mono_pcm16(path: Path, samples: list[float]) -> None:
    pcm = array.array(
        "h",
        (
            round(max(-32768.0, min(32767.0, sample * 32768.0)))
            for sample in samples
        ),
    )
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(SAMPLE_RATE)
        target.writeframes(pcm.tobytes())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply the review Alchemist voice treatment."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--target-active-rms-db",
        type=float,
        default=DEFAULT_ACTIVE_RMS_DB,
        help="Target active-window RMS in dBFS (default: -20.0)",
    )
    args = parser.parse_args()

    processed = process(
        read_mono_pcm16(args.input), args.target_active_rms_db
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_mono_pcm16(args.output, processed)
    print(
        f"Wrote {args.output} "
        f"({len(processed) / SAMPLE_RATE:.3f}s, mono {SAMPLE_RATE} Hz PCM16)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
