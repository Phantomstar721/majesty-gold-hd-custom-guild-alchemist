from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


MAGENTA = (255, 0, 255, 255)


def load_actor(path: Path, target_height: int) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha < 128 or (
                red > 205
                and blue > 175
                and green < 105
                and red > green * 1.7
                and blue > green * 1.5
            ):
                pixels[x, y] = (0, 0, 0, 0)
    alpha = image.getchannel("A")
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError(f"Walk frame has no visible actor: {path}")
    actor = image.crop(bounds)
    width = max(1, round(actor.width * target_height / actor.height))
    return actor.resize((width, target_height), Image.Resampling.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assemble eight reviewed Alchemist walk frames into one engine strip."
    )
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--actor-height", type=int, default=520)
    parser.add_argument("--padding", type=int, default=40)
    args = parser.parse_args()

    actors = [
        load_actor(args.frames / f"frame-{index}.png", args.actor_height)
        for index in range(8)
    ]
    cell_width = max(actor.width for actor in actors) + args.padding * 2
    canvas_height = args.actor_height + args.padding * 2
    strip = Image.new("RGBA", (cell_width * 8, canvas_height), MAGENTA)
    for index, actor in enumerate(actors):
        x = index * cell_width + (cell_width - actor.width) // 2
        y = canvas_height - args.padding - actor.height
        strip.alpha_composite(actor, (x, y))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    strip.convert("RGB").save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
