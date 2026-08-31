from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys

from PIL import Image, ImageOps


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


def owner_registered_frames(
    stock,
    entries: list,
    palettes: list,
    names: list[bytes],
) -> tuple[list[Image.Image], list[tuple[int, int]]]:
    by_name = {entry.name.rstrip(b"\x00"): entry.data for entry in entries}
    images: list[Image.Image] = []
    origins: list[tuple[int, int]] = []
    for name in names:
        tile = by_name.get(name)
        if tile is None:
            raise ValueError(f"Packaged review TILE is missing: {name!r}")
        hotspot = struct.unpack_from("<hh", tile, 10)
        images.append(render_tile(stock, tile, palettes))
        origins.append((-hotspot[0], -hotspot[1]))
    return images, origins


def reagent_ready_stream_layers(
    stock,
    entries: list,
    palettes: list,
    imag: bytes,
) -> list[list[tuple[Image.Image, tuple[int, int]]]]:
    """Decode both retained WRF1 streams with their stock mirror flags."""

    frames: list[list[tuple[Image.Image, tuple[int, int]]]] = [
        [] for _ in range(package.REAGENT_READY_FRAME_COUNT)
    ]
    for offsets in package.REAGENT_READY_STREAM_REFERENCE_OFFSETS:
        for frame, offset in enumerate(offsets):
            word = struct.unpack_from("<I", imag, offset)[0]
            index = word & 0xFFFF
            flags = word >> 16
            entry = entries[index]
            if not entry.name.rstrip(b"\x00").startswith(b"ALR1Ready"):
                raise ValueError("Reagents Ready IMAG escaped its private TILE family")
            image = render_tile(stock, entry.data, palettes)
            hotspot = list(struct.unpack_from("<hh", entry.data, 10))
            if flags & 0x2000:
                image = ImageOps.mirror(image)
                hotspot[0] = image.width - 1 - hotspot[0]
            if flags & 0x4000:
                image = ImageOps.flip(image)
                hotspot[1] = image.height - 1 - hotspot[1]
            if flags & ~0x6000:
                raise ValueError("Reagents Ready review found an unknown WRF1 flag")
            frames[frame].append((image, (-hotspot[0], -hotspot[1])))
    if any(len(layers) != package.REAGENT_READY_STREAM_COUNT for layers in frames):
        raise ValueError("Reagents Ready review lost a coupled stream")
    return frames


def common_canvas(
    layers: list[tuple[Image.Image, tuple[int, int]]],
    padding: int = 8,
) -> tuple[Image.Image, tuple[int, int]]:
    left = min(origin[0] for _image, origin in layers) - padding
    top = min(origin[1] for _image, origin in layers) - padding
    right = max(
        origin[0] + image.width for image, origin in layers
    ) + padding
    bottom = max(
        origin[1] + image.height for image, origin in layers
    ) + padding
    return (
        Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0)),
        (-left, -top),
    )


def composite_registered(
    canvas: Image.Image,
    owner_offset: tuple[int, int],
    layers: list[tuple[Image.Image, tuple[int, int]]],
) -> Image.Image:
    frame = canvas.copy()
    for image, origin in layers:
        frame.alpha_composite(
            image,
            (owner_offset[0] + origin[0], owner_offset[1] + origin[1]),
        )
    return frame


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cam",
        type=Path,
        default=ROOT
        / "dist/CustomGuildAlchemist/Data/alchemist_maindata.cam",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts/review/reagent-ready-supercharge",
    )
    args = parser.parse_args()

    stock = package.load_stock_pipeline(ROOT)
    tiles = stock.read_cam_entries(args.cam, b"TILE")
    palettes = stock.read_cam_entries(args.cam, b"SPLT")
    building_names = [f"ALB3Act1027F{frame:02d}".encode("ascii") for frame in range(8)]
    building_frames, building_origins = owner_registered_frames(
        stock, tiles, palettes, building_names
    )
    ready_imag = stock.read_cam_entry(
        args.cam, b"IMAG", package.REAGENT_READY_CUSTOM
    ).data
    ready_layers = reagent_ready_stream_layers(
        stock, tiles, palettes, ready_imag
    )

    all_layers = list(zip(building_frames, building_origins)) + [
        layer for frame_layers in ready_layers for layer in frame_layers
    ]
    canvas, owner_offset = common_canvas(all_layers)
    active_frames = [
        composite_registered(
            canvas,
            owner_offset,
            [(image, origin)],
        )
        for image, origin in zip(building_frames, building_origins)
    ]
    ready_composites: list[Image.Image] = []
    for frame, frame_layers in enumerate(ready_layers):
        building_frame = frame % len(building_frames)
        ready_composites.append(
            composite_registered(
                canvas,
                owner_offset,
                [
                    (
                        building_frames[building_frame],
                        building_origins[building_frame],
                    ),
                    *frame_layers,
                ],
            )
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    active_path = args.out_dir / "level3-active-pulse.gif"
    active_sheet_path = args.out_dir / "level3-active-pulse-sheet.png"
    ready_path = args.out_dir / "level3-reagents-ready.gif"
    ready_sheet_path = args.out_dir / "level3-reagents-ready-sheet.png"
    preview_path = args.out_dir / "level3-reagents-ready-preview.png"
    active_frames[0].save(
        active_path,
        save_all=True,
        append_images=active_frames[1:],
        duration=100,
        loop=0,
        disposal=2,
    )
    active_sheet = Image.new(
        "RGBA",
        (canvas.width * 4, canvas.height * 2),
        (0, 0, 0, 0),
    )
    for frame, image in enumerate(active_frames):
        active_sheet.alpha_composite(
            image,
            ((frame % 4) * canvas.width, (frame // 4) * canvas.height),
        )
    active_sheet.save(active_sheet_path)
    ready_composites[0].save(
        ready_path,
        save_all=True,
        append_images=ready_composites[1:],
        duration=100,
        loop=0,
        disposal=2,
    )
    ready_samples = ready_composites[::3]
    ready_sheet = Image.new(
        "RGBA",
        (canvas.width * 5, canvas.height * 2),
        (0, 0, 0, 0),
    )
    for frame, image in enumerate(ready_samples):
        ready_sheet.alpha_composite(
            image,
            ((frame % 5) * canvas.width, (frame // 5) * canvas.height),
        )
    ready_sheet.save(ready_sheet_path)
    ready_composites[23].save(preview_path)
    print(active_path)
    print(active_sheet_path)
    print(ready_path)
    print(ready_sheet_path)
    print(preview_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
