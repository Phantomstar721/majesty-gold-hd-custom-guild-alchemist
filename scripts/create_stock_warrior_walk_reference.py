from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
HAUNT_ROOT = ROOT.parent / "majesty-gold-hd-custom-guild-phantoms-haunt"
GAME_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data")
OUTPUT = ROOT / "artifacts/references/stock-warrior-walk-directions"
DIRECTION_NAMES = ("north", "northwest", "west", "southwest", "south", "southeast", "east", "northeast")


def load_stock_pipeline():
    path = HAUNT_ROOT / "src/build_phantom_guild.py"
    spec = importlib.util.spec_from_file_location("stock_warrior_reference_pipeline", path)
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
            if palette_index == 0:
                continue
            if 247 <= palette_index <= 250:
                pixels[x, y] = (255, 0, 255, 255)
            else:
                pixels[x, y] = (*colors[palette_index], 255)
    return image


def main() -> int:
    stock = load_stock_pipeline()
    cam = GAME_DATA / "maindata.cam"
    tiles = stock.read_cam_entries(cam, b"TILE")
    palettes = stock.read_cam_entries(cam, b"SPLT")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for direction, name in enumerate(DIRECTION_NAMES):
        frames = [render_tile(stock, tiles[5919 + direction * 8 + frame].data, palettes) for frame in range(8)]
        scale = 8
        cell_width = max(frame.width for frame in frames) * scale + 24
        cell_height = max(frame.height for frame in frames) * scale + 52
        strip = Image.new("RGB", (cell_width * 8, cell_height), (35, 39, 43))
        draw = ImageDraw.Draw(strip)
        for frame_index, frame in enumerate(frames):
            enlarged = frame.resize((frame.width * scale, frame.height * scale), Image.Resampling.NEAREST)
            x = frame_index * cell_width + (cell_width - enlarged.width) // 2
            y = 8 + (cell_height - 44 - enlarged.height) // 2
            strip.paste(enlarged, (x, y), enlarged)
            draw.text((frame_index * cell_width + 8, cell_height - 30), f"{name.upper()} F{frame_index}", fill=(240, 240, 240))
        strip.save(OUTPUT / f"{direction}-{name}.png")

    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
