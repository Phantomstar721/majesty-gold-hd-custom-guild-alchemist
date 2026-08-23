from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import alchemist_art_package as package  # noqa: E402


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


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def walk_tile_sequences(imag: bytes) -> list[list[int]]:
    set_count = u32(imag, 20)
    sets = {
        u32(imag, 24 + index * 8): u32(imag, 28 + index * 8)
        for index in range(set_count)
    }
    set_offset = sets.get(1)
    if set_offset is None:
        raise ValueError("Alchemist IMAG has no stock Walk animation set")
    sequences: list[list[int]] = []
    for direction in range(8):
        relative = struct.unpack_from(
            "<i", imag, set_offset + 0x40 + direction * 4
        )[0]
        direction_offset = set_offset + relative
        frame_count = u32(imag, direction_offset + 4) >> 16
        if frame_count != 8:
            raise ValueError(
                f"Walk direction {direction} has {frame_count} frames; expected 8"
            )
        sequences.append(
            [
                u32(imag, direction_offset + 0x1C + frame * 8) & 0xFFFF
                for frame in range(frame_count)
            ]
        )
    return sequences


def render_tile(stock, tile: bytes, palettes) -> tuple[Image.Image, int, int]:
    decoded = stock.decode_indexed_v3_tile(tile)
    colors = stock.tile_palette_colors(tile, palettes)
    if decoded is None or colors is None:
        raise ValueError("Expected an indexed Warrior-derived TILE")
    height, width, rows = decoded
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            if 1 <= value <= 246:
                red, green, blue = colors[value]
                pixels[x, y] = (red, green, blue, 255)
    hotspot_x, hotspot_y = struct.unpack_from("<HH", tile, 10)
    return image, hotspot_x, hotspot_y


def anchored_frame(
    stock, tile: bytes, palettes, *, scale: int = 4
) -> tuple[Image.Image, Image.Image]:
    body, hotspot_x, hotspot_y = render_tile(stock, tile, palettes)
    body_canvas = Image.new("RGBA", (96, 92), (0, 0, 0, 0))
    anchor_x, anchor_y = 48, 70
    body_canvas.alpha_composite(body, (anchor_x - hotspot_x, anchor_y - hotspot_y))
    mask = body_canvas.getchannel("A").point(lambda value: 255 if value else 0)
    canvas = Image.new("RGBA", body_canvas.size, (30, 33, 34, 255))
    canvas.alpha_composite(body_canvas)
    return (
        canvas.resize((canvas.width * scale, canvas.height * scale), Image.Resampling.NEAREST),
        mask,
    )


def mask_distance(first: Image.Image, second: Image.Image) -> float:
    first_pixels = list(first.getdata())
    second_pixels = list(second.getdata())
    union = sum(1 for a, b in zip(first_pixels, second_pixels) if a or b)
    changed = sum(1 for a, b in zip(first_pixels, second_pixels) if bool(a) != bool(b))
    return changed / max(1, union)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cam",
        type=Path,
        default=ROOT / "dist/CustomGuildAlchemist/Data/alchemist_maindata.cam",
    )
    parser.add_argument(
        "--out-dir", type=Path, default=ROOT / "artifacts/reviews"
    )
    args = parser.parse_args()

    stock = package.load_stock_pipeline(ROOT)
    tiles = stock.read_cam_entries(args.cam, b"TILE")
    palettes = stock.read_cam_entries(args.cam, b"SPLT")
    imag = stock.read_cam_entry(args.cam, b"IMAG", package.HERO_CUSTOM).data
    sequences = walk_tile_sequences(imag)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    frame_width, frame_height = 96 * 4, 92 * 4
    contact = Image.new(
        "RGB", (frame_width * 8, (frame_height + 24) * 8), (25, 27, 28)
    )
    contact_draw = ImageDraw.Draw(contact)
    animation_frames = [
        Image.new("RGB", (frame_width * 4, frame_height * 2), (25, 27, 28))
        for _ in range(8)
    ]

    for direction, sequence in enumerate(sequences):
        rendered = [anchored_frame(stock, tiles[index].data, palettes) for index in sequence]
        distances = [
            mask_distance(rendered[frame][1], rendered[(frame + 1) % 8][1])
            for frame in range(8)
        ]
        print(
            f"{DIRECTIONS[direction]}: tiles={sequence} "
            f"adjacent-mask-distance={[round(value, 3) for value in distances]}"
        )
        for frame, (image, _mask) in enumerate(rendered):
            x = frame * frame_width
            y = direction * (frame_height + 24)
            contact.paste(image.convert("RGB"), (x, y))
            contact_draw.text(
                (x + 4, y + frame_height + 3),
                f"{DIRECTIONS[direction]} F{frame}",
                fill=(235, 235, 235),
            )
            preview_x = (direction % 4) * frame_width
            preview_y = (direction // 4) * frame_height
            animation_frames[frame].paste(image.convert("RGB"), (preview_x, preview_y))

    contact_path = args.out_dir / "alchemist-packaged-walk-v2.png"
    gif_path = args.out_dir / "alchemist-packaged-walk-v2.gif"
    contact.save(contact_path)
    animation_frames[0].save(
        gif_path,
        save_all=True,
        append_images=animation_frames[1:],
        duration=95,
        loop=0,
        optimize=False,
    )
    print(contact_path)
    print(gif_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
