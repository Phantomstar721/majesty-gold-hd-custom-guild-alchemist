from __future__ import annotations

import argparse
import array
import io
import math
from pathlib import Path
import sys
import wave


SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from build_alchemist_probe import read_cam_entries  # noqa: E402


EVENTS = (
    ("combat", b"AHC1", b"REGT", b"WRGT"),
    ("flee", b"AHF1", b"REFT", b"WRFT"),
    ("deciding", b"AHD1", b"REDO", b"WRDO"),
    ("reward", b"AHR1", b"REDG", b"WRDG"),
    ("find-item", b"AHN1", b"REFL", b"WRFL"),
    ("idle", b"AHI1", b"RESS", b"WRSS"),
    ("death", b"AHDH", b"REDH", b"WRDH"),
    ("level-up", b"AHL1", b"REGL", b"WRGL"),
    ("see-hostile", b"AHH1", b"RESE", b"WRSE"),
    ("level-10", b"AH10", b"RETL", b"WRTL"),
    ("easter-egg", b"AHE1", b"REE1", b"WRE1"),
)


def dbfs(value: float) -> float:
    return 20.0 * math.log10(max(value, 1.0e-12))


def decode_wave(payload: bytes) -> tuple[int, list[float]]:
    with wave.open(io.BytesIO(payload), "rb") as source:
        if source.getnchannels() != 1 or source.getcomptype() != "NONE":
            raise ValueError("Expected uncompressed mono stock voice")
        rate = source.getframerate()
        width = source.getsampwidth()
        frames = source.readframes(source.getnframes())
    if width == 1:
        values = [(sample - 128) / 128.0 for sample in frames]
    elif width == 2:
        pcm = array.array("h")
        pcm.frombytes(frames)
        values = [sample / 32768.0 for sample in pcm]
    else:
        raise ValueError(f"Unsupported PCM width: {width}")
    return rate, values


def measurements(payload: bytes) -> tuple[float, float, float, float]:
    rate, samples = decode_wave(payload)
    peak = max(abs(sample) for sample in samples)
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    window = max(1, round(rate * 0.020))
    active: list[float] = []
    for start in range(0, len(samples), window):
        chunk = samples[start : start + window]
        chunk_rms = math.sqrt(sum(value * value for value in chunk) / len(chunk))
        if dbfs(chunk_rms) > -40.0:
            active.extend(chunk)
    active_rms = math.sqrt(
        sum(sample * sample for sample in active) / max(1, len(active))
    )
    return len(samples) / rate, dbfs(peak), dbfs(rms), dbfs(active_rms)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare Alchemist voice levels to stock Rogue and Warrior."
    )
    parser.add_argument("--game-path", type=Path, required=True)
    parser.add_argument("--audio-root", type=Path, required=True)
    args = parser.parse_args()

    stock_entries = read_cam_entries(args.game_path / "Data" / "voices.cam", b"WAVE")
    stock = {entry.name.rstrip(b"\x00")[:4]: entry.data for entry in stock_entries}
    print("event\tvoice\tduration\tpeak_dbfs\trms_dbfs\tactive_rms_dbfs")
    for event, _private_id, rogue_id, warrior_id in EVENTS:
        private_payload = (args.audio_root / f"alchemist-{event}-game.wav").read_bytes()
        for voice, payload in (
            ("Alchemist", private_payload),
            ("Rogue", stock[rogue_id]),
            ("Warrior", stock[warrior_id]),
        ):
            duration, peak, rms, active_rms = measurements(payload)
            print(
                f"{event}\t{voice}\t{duration:.3f}\t{peak:.2f}\t"
                f"{rms:.2f}\t{active_rms:.2f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
