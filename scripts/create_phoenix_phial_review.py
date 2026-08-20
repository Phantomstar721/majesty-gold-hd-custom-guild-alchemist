from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import alchemist_art_package as package  # noqa: E402


def render_tile(stock, tile: bytes, palettes) -> Image.Image:
    decoded = stock.decode_indexed_v3_tile(tile)
    colors = stock.tile_palette_colors(tile, palettes)
    if decoded is None or colors is None:
        raise ValueError("Expected an indexed Phoenix TILE")
    height, width, rows = decoded
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            if 1 <= value <= 246:
                red, green, blue = colors[value]
                pixels[x, y] = (red, green, blue, 255)
    return image


def review_background(size: tuple[int, int]) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, (27, 31, 25))
    draw = ImageDraw.Draw(image)
    step = 8
    for y in range(0, height, step):
        for x in range(0, width, step):
            if (x // step + y // step) % 2:
                draw.rectangle(
                    (x, y, min(width - 1, x + step - 1), min(height - 1, y + step - 1)),
                    fill=(38, 43, 35),
                )
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cam",
        type=Path,
        default=ROOT / "dist/CustomGuildAlchemistProbe/Data/alchemist_maindata.cam",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts/generated-art/reviews/phoenix-phial",
    )
    args = parser.parse_args()

    stock = package.load_stock_pipeline(ROOT)
    tiles = stock.read_cam_entries(args.cam, b"TILE")
    palettes = stock.read_cam_entries(args.cam, b"SPLT")
    imag = stock.read_cam_entry(args.cam, b"IMAG", package.PHOENIX_EFFECT_CUSTOM).data
    animation_sets = dict(stock.single_direction_imag_animation_sets(imag))
    frames = animation_sets.get(64)
    if frames is None:
        raise ValueError("Private Phoenix IMAG has no stock Resurrection animation set 64")
    tile_indices = [value & 0xFFFF for _offset, value in frames if (value & 0xFFFF)]
    if len(tile_indices) != 28:
        raise ValueError(f"Expected 28 visible Phoenix frames, found {len(tile_indices)}")

    rendered = [render_tile(stock, tiles[index].data, palettes) for index in tile_indices]
    expected_size = (package.PHOENIX_EFFECT_HEADER[2], package.PHOENIX_EFFECT_HEADER[1])
    if any(frame.size != expected_size for frame in rendered):
        raise ValueError("Phoenix frames do not share the fixed self-cast canvas")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    scale = 3
    cell_width = expected_size[0] * scale
    cell_height = expected_size[1] * scale
    label_height = 22
    columns = 7
    rows = 4
    contact = Image.new(
        "RGB",
        (columns * cell_width, rows * (cell_height + label_height)),
        (20, 22, 19),
    )
    draw = ImageDraw.Draw(contact)
    animation: list[Image.Image] = []
    for index, frame in enumerate(rendered):
        background = review_background(expected_size)
        background.paste(frame, (0, 0), frame)
        scaled = background.resize(
            (cell_width, cell_height), Image.Resampling.NEAREST
        )
        x = (index % columns) * cell_width
        y = (index // columns) * (cell_height + label_height)
        contact.paste(scaled, (x, y))
        draw.text((x + 5, y + cell_height + 3), f"Frame {index + 1}", fill=(235, 224, 190))
        animation.append(scaled)

    contact_path = args.out_dir / "phoenix-phial-animation-contact-sheet.png"
    gif_path = args.out_dir / "phoenix-phial-animation.gif"
    contact.save(contact_path)
    animation[0].save(
        gif_path,
        save_all=True,
        append_images=animation[1:],
        duration=54,
        loop=0,
        optimize=False,
    )
    print(contact_path)
    print(gif_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
