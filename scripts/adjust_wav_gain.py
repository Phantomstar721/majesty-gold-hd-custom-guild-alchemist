from __future__ import annotations

import argparse
from array import array
import math
from pathlib import Path
import wave


def adjust_gain(path: Path, multiplier: float, soft_limit: bool) -> None:
    with wave.open(str(path), "rb") as source:
        params = source.getparams()
        samples = array("h", source.readframes(source.getnframes()))
    if soft_limit:
        ceiling = 10.0 ** (-1.0 / 20.0)
        boosted = array(
            "h",
            (
                round(
                    32767
                    * ceiling
                    * math.tanh((sample / 32768.0) * multiplier / ceiling)
                )
                for sample in samples
            ),
        )
    else:
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
    parser.add_argument(
        "--soft-limit",
        action="store_true",
        help="Use the Haunt-proven smooth -1 dBFS limiter instead of hard clipping",
    )
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    if args.multiplier <= 0:
        parser.error("--multiplier must be positive")
    for path in args.paths:
        adjust_gain(path, args.multiplier, args.soft_limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
