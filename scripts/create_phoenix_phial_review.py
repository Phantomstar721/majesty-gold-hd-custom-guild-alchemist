from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import alchemist_art_package as package  # noqa: E402


def phoenix_phase(frame_index: int, frame_count: int) -> str:
    if frame_index >= package.PHOENIX_VISIBLE_FRAMES:
        return "Private transparent tail"
    frame_count = package.PHOENIX_VISIBLE_FRAMES
    progress = frame_index / max(1, frame_count - 1)
    if frame_index == 0:
        return "Initialization"
    if progress <= 0.60:
        return "Growth"
    if progress <= 0.82:
        return "Peak"
    return "Reduction / fade"


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
        default=ROOT / "dist/CustomGuildAlchemist/Data/alchemist_maindata.cam",
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
    imag = stock.read_cam_entry(
        args.cam, b"IMAG", package.PHOENIX_LIFECYCLE_CUSTOM
    ).data
    animation_sets = stock.single_direction_imag_animation_sets(imag)
    if (
        len(animation_sets) != 1
        or animation_sets[0][0] != package.PHOENIX_LIFECYCLE_ANIMATION_SET
    ):
        raise ValueError("Private Phoenix IMAG is not the stock HRC1 set-64 lifecycle")
    tile_indices = stock.animation_tile_indices(imag, len(tiles))
    if len(tile_indices) != package.PHOENIX_LIFECYCLE_FRAMES:
        raise ValueError(
            f"Expected {package.PHOENIX_LIFECYCLE_FRAMES} Phoenix frames, "
            f"found {len(tile_indices)}"
        )

    rendered_visible: list[Image.Image] = []
    for frame_number, tile_index in enumerate(tile_indices, start=1):
        tile = tiles[tile_index].data
        header = struct.unpack_from("<8H", tile, 0)
        if header != package.PHOENIX_EFFECT_HEADER:
            raise ValueError(
                f"Phoenix frame {frame_number} has header {header}, expected "
                f"{package.PHOENIX_EFFECT_HEADER}"
            )
        if stock.tile_palette_index(tile) != package.PHOENIX_EFFECT_PALETTE:
            raise ValueError(
                f"Phoenix frame {frame_number} is not using fire palette "
                f"{package.PHOENIX_EFFECT_PALETTE}"
            )
        rendered_visible.append(render_tile(stock, tile, palettes))

    expected_size = (
        package.PHOENIX_EFFECT_HEADER[2],
        package.PHOENIX_EFFECT_HEADER[1],
    )
    rendered = rendered_visible

    args.out_dir.mkdir(parents=True, exist_ok=True)
    scale = 3
    cell_width = expected_size[0] * scale
    cell_height = expected_size[1] * scale
    label_height = 22
    columns = 6
    rows = (len(rendered) + columns - 1) // columns
    contact = Image.new(
        "RGB",
        (columns * cell_width, rows * (cell_height + label_height)),
        (20, 22, 19),
    )
    draw = ImageDraw.Draw(contact)
    animation: list[Image.Image] = []
    for frame in rendered:
        background = review_background(expected_size)
        background.paste(frame, (0, 0), frame)
        animation.append(
            background.resize(
                (cell_width, cell_height), Image.Resampling.NEAREST
            )
        )

    for frame_index in range(len(rendered)):
        column = frame_index % columns
        row = frame_index // columns
        x = column * cell_width
        y = row * (cell_height + label_height)
        contact.paste(animation[frame_index], (x, y))
        draw.text(
            (x + 5, y + cell_height + 3),
            f"{frame_index + 1}: {phoenix_phase(frame_index, len(rendered))}",
            fill=(235, 224, 190),
        )

    contact_path = args.out_dir / "phoenix-phial-animation-contact-sheet.png"
    gif_path = args.out_dir / "phoenix-phial-animation.gif"
    contact.save(contact_path)
    animation[0].save(
        gif_path,
        save_all=True,
        append_images=animation[1:],
        duration=52,
        loop=0,
        optimize=False,
    )
    print(contact_path)
    print(gif_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
