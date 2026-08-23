from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
MAGENTA = (255, 0, 255)


def chroma_crop(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            # Chroma cleanup leaves a small number of low-alpha matte pixels.
            # They are not part of the actor and must not expand the crop or
            # make one review frame appear smaller than its neighbors.
            if a < 128 or (r > 205 and b > 175 and g < 105 and r > g * 1.7 and b > g * 1.5):
                pixels[x, y] = (0, 0, 0, 0)
    bbox = image.getbbox()
    if bbox is None:
        raise ValueError(f"No actor pixels in {path}")
    return image.crop(bbox)


def fit_actor(image: Image.Image, height: int = 52) -> Image.Image:
    width = max(1, round(image.width * height / image.height))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def stage(actor: Image.Image, width: int, height: int, scale: int = 1) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (31, 34, 37, 255))
    x = (width - actor.width) // 2
    y = height - actor.height - 6
    canvas.alpha_composite(actor, (x, y))
    if scale != 1:
        canvas = canvas.resize((width * scale, height * scale), Image.Resampling.NEAREST)
    return canvas.convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("direction")
    parser.add_argument("--version", default="v3")
    parser.add_argument("--stock-dir", type=Path)
    args = parser.parse_args()
    direction = args.direction.lower()
    frame_dir = ROOT / f"assets/source/hero/walk-frames-{args.version}" / direction
    stock_dir = args.stock_dir or (
        ROOT / "artifacts/references/stock-warrior-walk-frame-targets" / direction
    )
    out_dir = ROOT / "artifacts/reviews"
    out_dir.mkdir(parents=True, exist_ok=True)

    custom = [fit_actor(chroma_crop(frame_dir / f"frame-{i}.png")) for i in range(8)]
    stock = [fit_actor(chroma_crop(stock_dir / f"frame-{i}.png")) for i in range(8)]
    cell_w, cell_h, scale = 92, 76, 5

    row_height = cell_h * scale + 52
    review = Image.new("RGB", (cell_w * scale * 8, row_height * 2), (31, 34, 37))
    draw = ImageDraw.Draw(review)
    draw.text((10, 8), f"{direction.upper()} - STOCK REFERENCE GAIT", fill=(245, 215, 95))
    draw.text((10, row_height + 8), "ALCHEMIST SOURCE FRAMES (same baseline and body height)", fill=(245, 215, 95))
    for i in range(8):
        stock_cell = stage(stock[i], cell_w, cell_h, scale)
        custom_cell = stage(custom[i], cell_w, cell_h, scale)
        x = i * cell_w * scale
        review.paste(stock_cell, (x, 52))
        review.paste(custom_cell, (x, row_height + 52))
        draw.text((x + 8, 30), f"FRAME {i + 1}", fill=(235, 235, 235))
        draw.text((x + 8, row_height + 30), f"FRAME {i + 1}", fill=(235, 235, 235))
    review_path = out_dir / f"alchemist-walk-{direction}-source-review-{args.version}.png"
    review.save(review_path)

    gif_frames = []
    for i in range(8):
        pair = Image.new("RGB", (cell_w * scale * 2, cell_h * scale + 32), (31, 34, 37))
        pair.paste(stage(stock[i], cell_w, cell_h, scale), (0, 32))
        pair.paste(stage(custom[i], cell_w, cell_h, scale), (cell_w * scale, 32))
        pair_draw = ImageDraw.Draw(pair)
        pair_draw.text((8, 8), f"STOCK FRAME {i + 1}", fill=(245, 215, 95))
        pair_draw.text((cell_w * scale + 8, 8), f"ALCHEMIST FRAME {i + 1}", fill=(245, 215, 95))
        gif_frames.append(pair)
    gif_path = out_dir / f"alchemist-walk-{direction}-source-review-{args.version}.gif"
    gif_frames[0].save(
        gif_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=110,
        loop=0,
        disposal=2,
    )
    print(review_path)
    print(gif_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
