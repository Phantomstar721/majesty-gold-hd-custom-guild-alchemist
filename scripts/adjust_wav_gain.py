from __future__ import annotations

import argparse
from array import array
from pathlib import Path
import wave


def adjust_gain(path: Path, multiplier: float) -> None:
    with wave.open(str(path), "rb") as source:
        params = source.getparams()
        samples = array("h", source.readframes(source.getnframes()))
    boosted = array(
        "h",
        (
            max(-32768, min(32767, round(sample * multiplier)))
            for sample in samples
        ),
    )
    with wave.open(str(path), "wb") as target:
        target.setparams(params)
        target.writeframes(boosted.tobytes())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply a saturating gain multiplier to signed 16-bit PCM WAVs"
    )
    parser.add_argument("--multiplier", type=float, required=True)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    if args.multiplier <= 0:
        parser.error("--multiplier must be positive")
    for path in args.paths:
        adjust_gain(path, args.multiplier)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
