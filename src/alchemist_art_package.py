from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from PIL import Image, ImageEnhance, ImageOps


HERO_SOURCE = b"AVC1Cultist"
HERO_CUSTOM = b"ALC1Alchemist"
BUILDING_SOURCES = (
    b"ABQ1Temple, Fervus1",
    b"ABQ2Temple, Fervus2",
    b"ABQ3Temple, Fervus3",
)
BUILDING_CUSTOM = (
    b"ALB1Alchemy Lab 1",
    b"ALB2Alchemy Lab 2",
    b"ALB3Alchemy Lab 3",
)
RAW_TEXTURE_SOURCE = b"INTIraw textures"
RAW_TEXTURE_CUSTOM = b"ALTIraw textures"
BUILDING_FRAME_SOURCE = b"INBbbuilding frame"
BUILDING_FRAME_CUSTOM = b"ALBBbuilding frame"
BUILDING_PROFILE_TILE = 1509
BUILDING_ICON_TILE = 1510
HERO_PORTRAIT_TILE = 4137
HERO_ICON_TILE = 4143
HERO_PANEL_TILE = 4144
BUILDING_PALETTE = 560
# The general palette used by the Phantom collapses the Alchemist's approved
# forest green and copper into blue-black. Fervus building palette 560 retains
# both materials and already owns the stock 247-250 sprite controls.
HERO_ART_PALETTE = 560
BREWING_BUTTON_TILES = (739, 740, 741, 742)


def load_stock_pipeline(repo: Path):
    path = repo.parent / "majesty-gold-hd-custom-guild-phantoms-haunt" / "src" / "build_phantom_guild.py"
    spec = importlib.util.spec_from_file_location("stock_art_package_pipeline", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load the proven Haunt CAM art pipeline: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def image_rgb(path: Path, size: tuple[int, int]) -> bytes:
    return Image.open(path).convert("RGB").resize(size, Image.Resampling.LANCZOS).tobytes()


def tile_image(stock, tile: bytes, palettes) -> Image.Image:
    decoded = stock.decode_indexed_v3_tile(tile)
    colors = stock.tile_palette_colors(tile, palettes)
    if decoded is None or colors is None:
        raise ValueError("Expected an indexed v3 interface TILE")
    height, width, rows = decoded
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, index in enumerate(row):
            if index:
                r, g, b = colors[index]
                pixels[x, y] = (r, g, b, 255)
    return image


def brewing_button_frames(stock, tiles, palettes, icon_path: Path, output_dir: Path) -> list[Path]:
    icon = Image.open(icon_path).convert("RGBA")
    icon.thumbnail((16, 16), Image.Resampling.LANCZOS)
    paths: list[Path] = []
    for state, tile_index in enumerate(BREWING_BUTTON_TILES):
        frame = tile_image(stock, tiles[tile_index].data, palettes)
        state_icon = icon.copy()
        if state == 2:
            state_icon = ImageOps.grayscale(state_icon).convert("RGBA")
            state_icon = ImageEnhance.Brightness(state_icon).enhance(0.45)
        elif state == 1:
            state_icon = ImageEnhance.Brightness(state_icon).enhance(1.15)
        x = 4
        y = max(1, (frame.height - state_icon.height) // 2)
        frame.alpha_composite(state_icon, (x, y))
        path = output_dir / f"brewing-button-frame-{state}.png"
        frame.save(path)
        paths.append(path)
    return paths


def write_maindata(repo: Path, game_data: Path, art_dir: Path, output: Path) -> None:
    stock = load_stock_pipeline(repo)
    source = game_data / "maindata.cam"
    tiles = stock.read_cam_entries(source, b"TILE")
    palettes = stock.read_cam_entries(source, b"SPLT")
    hero_imag = stock.read_cam_entry(source, b"IMAG", HERO_SOURCE).data
    building_imags = [stock.read_cam_entry(source, b"IMAG", name).data for name in BUILDING_SOURCES]

    # All appended art is private. Stock TILE slots remain empty fall-through
    # placeholders in the emitted CAM, so no retail art is globally replaced.
    # Positional TILE overlays must begin after the complete retail table, not
    # after the highest source tile this mod happens to clone. Starting at
    # HERO_PANEL_TILE would silently replace later stock heroes and effects.
    base_max = len(tiles) - 1
    extra: list = []

    def append(name: bytes, data: bytes) -> int:
        index = base_max + len(extra) + 1
        extra.append(stock.CamEntry(name=stock.pad_name(name), data=data))
        return index

    hero_replacements: dict[int, int] = {}
    hero_dir = art_dir / "hero"
    for source_index in range(3934, 4137):
        path = hero_dir / f"hero_tile_{source_index:05d}.png"
        if not path.exists():
            raise FileNotFoundError(path)
        rendered = stock.tile_from_png_source(
            stock.remap_tile_palette_index(tiles[source_index].data, HERO_ART_PALETTE),
            palettes,
            path,
            horizontal_alignment="center",
            edge_margin=2,
            shadow_png_path=path,
        )
        hero_replacements[source_index] = append(
            f"ALC1Hero{source_index - 3934:04d}".encode("ascii"), rendered
        )

    hero_replacements[HERO_PORTRAIT_TILE] = append(
        b"ALC1Portrait",
        stock.tile_from_rgb(
            stock.remap_tile_palette_index(tiles[HERO_PORTRAIT_TILE].data, BUILDING_PALETTE),
            palettes,
            image_rgb(repo / "assets/source/hero/portrait.png", (100, 100)),
        ),
    )
    hero_replacements[HERO_ICON_TILE] = append(
        b"ALC1HeroIcon",
        stock.tile_from_rgb(
            stock.remap_tile_palette_index(tiles[HERO_ICON_TILE].data, BUILDING_PALETTE),
            palettes,
            image_rgb(art_dir / "interface/hero-icon-25.png", (25, 25)),
        ),
    )
    hero_replacements[HERO_PANEL_TILE] = append(
        b"ALC1HeroPanel",
        stock.tile_from_rgb(
            stock.remap_tile_palette_index(tiles[HERO_PANEL_TILE].data, HERO_ART_PALETTE),
            palettes,
            image_rgb(art_dir / "interface/building-panel-200x245.png", (200, 245)),
        ),
    )
    hero_imag = stock.remap_imag_low16_tile_indices(hero_imag, hero_replacements)

    profile_index = append(
        b"ALB1Profile",
        stock.tile_from_rgb(
            tiles[BUILDING_PROFILE_TILE].data,
            palettes,
            image_rgb(art_dir / "interface/building-portrait-100.png", (100, 100)),
        ),
    )
    icon_index = append(
        b"ALB1BuildIcon",
        stock.tile_from_rgb(
            stock.remap_tile_palette_index(tiles[BUILDING_ICON_TILE].data, BUILDING_PALETTE),
            palettes,
            image_rgb(art_dir / "interface/building-icon-25.png", (25, 25)),
        ),
    )

    for level in (1, 2, 3):
        imag = stock.remap_imag_low16_tile_indices(
            building_imags[level - 1],
            {BUILDING_PROFILE_TILE: profile_index, BUILDING_ICON_TILE: icon_index},
        )
        paths = stock.building_sprite_replacement_paths(art_dir / f"buildings/level-{level}")
        replacements: dict[int, int] = {}
        for source_index, path in sorted(paths.items()):
            replacements[source_index] = append(
                f"ALB{level}State{source_index:04d}".encode("ascii"),
                stock.tile_from_png_native_size(
                    stock.remap_tile_palette_index(tiles[source_index].data, BUILDING_PALETTE),
                    palettes,
                    path,
                ),
            )
        imag = stock.remap_imag_low16_tile_indices(imag, replacements)
        active_paths = stock.building_active_replacement_paths(art_dir / f"buildings/level-{level}")
        template_index = (1506, 1562, 1566)[level - 1]
        active_indices = [
            append(
                f"ALB{level}Active{frame:02d}".encode("ascii"),
                stock.tile_from_png_native_size(
                    stock.remap_tile_palette_index(tiles[template_index].data, BUILDING_PALETTE),
                    palettes,
                    path,
                ),
            )
            for frame, path in enumerate(active_paths)
        ]
        imag = stock.replace_building_state_animation_tiles(imag, 192, active_indices)
        building_imags[level - 1] = imag

    palette_indices = {BUILDING_PALETTE, HERO_ART_PALETTE}
    for entry in extra:
        index = stock.tile_palette_index(entry.data)
        if index is not None:
            palette_indices.add(index)
    palette_entries = tuple(
        stock.CamEntry(
            name=palettes[index].name,
            data=(
                stock.splt_with_color_replacements(
                    palettes[index].data,
                    {247: (156, 33, 24), 248: (178, 0, 178), 249: (204, 0, 204), 250: (229, 0, 229)},
                )
                if index == BUILDING_PALETTE
                else palettes[index].data
            ),
        )
        for index in range(max(palette_indices) + 1)
    )
    tile_entries = [
        stock.CamEntry(name=tiles[index].name, data=b"")
        for index in range(base_max + 1)
    ]
    tile_entries.extend(extra)
    images = (
        stock.CamEntry(stock.pad_name(HERO_CUSTOM), hero_imag),
        *(stock.CamEntry(stock.pad_name(name), imag) for name, imag in zip(BUILDING_CUSTOM, building_imags)),
    )
    stock.write_cam(
        (
            stock.CamSection(b"IMAG", b"\x00\x00\x00\x00", tuple(images)),
            stock.CamSection(b"TILE", b"\x01\x00\x00\x00", tuple(tile_entries)),
            stock.CamSection(b"SPLT", b"\x01\x00\x00\x00", palette_entries),
        ),
        output,
    )


def write_interfacedata(repo: Path, game_data: Path, art_dir: Path, output: Path) -> None:
    stock = load_stock_pipeline(repo)
    source = game_data / "interfacedata.cam"
    tiles = stock.read_cam_entries(source, b"TILE")
    raw_imag = stock.read_cam_entry(source, b"IMAG", RAW_TEXTURE_SOURCE).data
    frame_imag = stock.read_cam_entry(source, b"IMAG", BUILDING_FRAME_SOURCE).data
    base_max = len(tiles) - 1
    extra: list = []

    def append(name: bytes, data: bytes) -> int:
        index = base_max + len(extra) + 1
        extra.append(stock.CamEntry(stock.pad_name(name), data))
        return index

    panel_replacements = {
        474: append(
            b"ALTIMainPanel",
            stock.tile_v1_embedded_from_rgb(
                tiles[474].data,
                image_rgb(art_dir / "interface/building-panel-200x245.png", (200, 245)),
            ),
        ),
        495: append(
            b"ALTIBrewPanel",
            stock.tile_v1_embedded_from_rgb(
                tiles[495].data,
                image_rgb(art_dir / "interface/brewing-panel-200x245.png", (200, 245)),
            ),
        ),
    }
    raw_imag = stock.remap_imag_tile_indices(raw_imag, panel_replacements)

    button_paths = brewing_button_frames(
        stock, tiles, [], art_dir / "interface/brewing-button-icon-16.png", art_dir / "interface"
    )
    button_replacements: dict[int, int] = {}
    for tile_index, path in zip(BREWING_BUTTON_TILES, button_paths):
        button_replacements[tile_index] = append(
            f"ALBBrewButton{tile_index}".encode("ascii"),
            stock.tile_from_png_native_size(tiles[tile_index].data, [], path),
        )
    frame_imag = stock.remap_imag_low16_tile_indices(frame_imag, button_replacements)

    tile_entries = [stock.CamEntry(name=tile.name, data=b"") for tile in tiles]
    tile_entries.extend(extra)
    stock.write_cam(
        (
            stock.CamSection(
                b"IMAG",
                b"\x00\x00\x00\x00",
                (
                    stock.CamEntry(stock.pad_name(RAW_TEXTURE_CUSTOM), raw_imag),
                    stock.CamEntry(stock.pad_name(BUILDING_FRAME_CUSTOM), frame_imag),
                ),
            ),
            stock.CamSection(b"TILE", b"\x01\x00\x00\x00", tuple(tile_entries)),
        ),
        output,
    )
