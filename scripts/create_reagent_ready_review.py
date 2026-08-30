from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import alchemist_art_package as package  # noqa: E402


def render_tile(stock, tile: bytes, palettes) -> Image.Image:
    decoded = stock.decode_indexed_v3_tile(tile)
    colors = stock.tile_palette_colors(tile, palettes)
    if decoded is None or colors is None:
        raise ValueError("Expected an indexed Laboratory TILE")
    height, width, rows = decoded
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            if 1 <= value <= 246:
                red, green, blue = colors[value]
                pixels[x, y] = (red, green, blue, 255)
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cam",
        type=Path,
        default=ROOT / "dist/CustomGuildAlchemist/Data/alchemist_maindata.cam",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts/review/reagent-ready-v2",
    )
    args = parser.parse_args()

    stock = package.load_stock_pipeline(ROOT)
    tiles = stock.read_cam_entries(args.cam, b"TILE")
    palettes = stock.read_cam_entries(args.cam, b"SPLT")
    base_matches = [
        entry
        for entry in tiles
        if entry.name.rstrip(b"\x00") == b"ALB3State1027"
    ]
    if len(base_matches) != 1:
        raise ValueError("Private level-3 active Laboratory TILE is missing")
    base_tile = base_matches[0].data
    source_png = (
        ROOT
        / "assets/source/effects/reagent-ready/alchemist-reagent-ready-source.png"
    )

    frames: list[Image.Image] = []
    for frame_index in range(len(package.REAGENT_READY_SOURCE_TILES)):
        overlay_tile = package.generated_reagent_ready_tile(
            stock,
            base_tile,
            palettes,
            source_png,
            frame_index,
            len(package.REAGENT_READY_SOURCE_TILES),
        )
        composed = render_tile(stock, base_tile, palettes)
        composed.alpha_composite(render_tile(stock, overlay_tile, palettes))
        frames.append(composed)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    preview_path = args.out_dir / "level3-reagent-ready-preview.png"
    gif_path = args.out_dir / "level3-reagent-ready-animation.gif"
    frames[4].save(preview_path)
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=90,
        loop=0,
        disposal=2,
    )
    print(preview_path)
    print(gif_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
