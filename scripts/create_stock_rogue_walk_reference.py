from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
HAUNT_ROOT = ROOT.parent / "majesty-gold-hd-custom-guild-phantoms-haunt"
GAME_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data")
OUTPUT = ROOT / "artifacts/references/stock-rogue-walk"
SLOTS = (2, 3, 4, 5, 6, 7)
TILE_STARTS = (4794, 4802, 4810, 4818, 4826, 4834)


def load_stock_pipeline():
    path = HAUNT_ROOT / "src/build_phantom_guild.py"
    spec = importlib.util.spec_from_file_location("rogue_walk_reference_pipeline", path)
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
        raise ValueError("Expected an indexed Rogue TILE")
    height, width, rows = decoded
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, palette_index in enumerate(row):
            if palette_index == 0 or 247 <= palette_index <= 250:
                continue
            pixels[x, y] = (*colors[palette_index], 255)
    return image


def main() -> int:
    stock = load_stock_pipeline()
    tiles = stock.read_cam_entries(GAME_DATA / "maindata.cam", b"TILE")
    palettes = stock.read_cam_entries(GAME_DATA / "maindata.cam", b"SPLT")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    scale, cell_w, cell_h = 8, 180, 210
    sheet = Image.new("RGB", (cell_w * 8, cell_h * len(SLOTS)), (31, 34, 37))
    draw = ImageDraw.Draw(sheet)
    for row, (slot, start) in enumerate(zip(SLOTS, TILE_STARTS)):
        slot_dir = OUTPUT / f"slot-{slot}"
        slot_dir.mkdir(parents=True, exist_ok=True)
        for frame in range(8):
            image = render_tile(stock, tiles[start + frame].data, palettes)
            bbox = image.getbbox()
            if bbox:
                image = image.crop(bbox)
            target_scale = min(12, 390 // max(image.width, image.height))
            target_actor = image.resize(
                (image.width * target_scale, image.height * target_scale),
                Image.Resampling.NEAREST,
            )
            target = Image.new("RGB", (512, 512), (255, 0, 255))
            target.paste(
                target_actor,
                ((512 - target_actor.width) // 2, 470 - target_actor.height),
                target_actor,
            )
            target.save(slot_dir / f"frame-{frame}.png")
            enlarged = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
            x = frame * cell_w + (cell_w - enlarged.width) // 2
            y = row * cell_h + 10 + (165 - enlarged.height)
            sheet.paste(enlarged, (x, y), enlarged)
            draw.text((frame * cell_w + 8, row * cell_h + 182), f"slot {slot} F{frame} / {start + frame}", fill=(235, 235, 235))
    path = OUTPUT / "stock-rogue-walk-contact.png"
    sheet.save(path)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
