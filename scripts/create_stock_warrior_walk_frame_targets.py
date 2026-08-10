from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
HAUNT_ROOT = ROOT.parent / "majesty-gold-hd-custom-guild-phantoms-haunt"
GAME_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data")
OUTPUT = ROOT / "artifacts/references/stock-warrior-walk-frame-targets"
DIRECTIONS = (
    "north",
    "northeast",
    "east",
    "southeast",
    "south",
    "southwest",
    "west",
    "northwest",
)


def load_stock_pipeline():
    path = HAUNT_ROOT / "src/build_phantom_guild.py"
    spec = importlib.util.spec_from_file_location("warrior_frame_target_pipeline", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load stock art pipeline: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def render_tile(stock, tile: bytes, palettes) -> Image.Image:
    decoded = stock.decode_indexed_v3_tile(tile)
    colors = stock.tile_palette_colors(tile, palettes)
    if decoded is None or colors is None:
        raise ValueError("Expected an indexed Warrior TILE")
    height, width, rows = decoded
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, palette_index in enumerate(row):
            if palette_index == 0 or 247 <= palette_index <= 250:
                continue
            pixels[x, y] = (*colors[palette_index], 255)
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else Image.new("RGBA", (1, 1))


def main() -> int:
    stock = load_stock_pipeline()
    tiles = stock.read_cam_entries(GAME_DATA / "maindata.cam", b"TILE")
    palettes = stock.read_cam_entries(GAME_DATA / "maindata.cam", b"SPLT")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    contact = Image.new("RGB", (8 * 220, 8 * 250), (31, 34, 37))
    draw = ImageDraw.Draw(contact)
    for direction_index, direction in enumerate(DIRECTIONS):
        direction_dir = OUTPUT / direction
        direction_dir.mkdir(parents=True, exist_ok=True)
        for frame_index in range(8):
            tile_index = 5919 + direction_index * 8 + frame_index
            actor = render_tile(stock, tiles[tile_index].data, palettes)
            scale = min(12, 390 // max(actor.width, actor.height))
            enlarged = actor.resize(
                (actor.width * scale, actor.height * scale), Image.Resampling.NEAREST
            )
            target = Image.new("RGB", (512, 512), (255, 0, 255))
            target.paste(enlarged, ((512 - enlarged.width) // 2, 470 - enlarged.height), enlarged)
            target.save(direction_dir / f"frame-{frame_index}.png")

            preview = actor.resize(
                (actor.width * 4, actor.height * 4), Image.Resampling.NEAREST
            )
            x = frame_index * 220 + (220 - preview.width) // 2
            y = direction_index * 250 + 20 + (190 - preview.height)
            contact.paste(preview, (x, y), preview)
            draw.text(
                (frame_index * 220 + 8, direction_index * 250 + 220),
                f"{direction} F{frame_index} / TILE {tile_index}",
                fill=(235, 235, 235),
            )
    contact.save(OUTPUT / "stock-warrior-64-frame-contact.png")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
