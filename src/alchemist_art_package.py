from __future__ import annotations

import importlib.util
from pathlib import Path
import struct
import sys

from PIL import Image, ImageDraw


HERO_SOURCE = b"AVL1Warrior"
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
BUILDING_DIALOG_SOURCE = b"INBgbuilding dialog"
BUILDING_DIALOG_CUSTOM = b"ALBGbuilding dialog"
NAVIGATION_SOURCE = b"INTN"
NAVIGATION_CUSTOM = b"ALINrecipe icons"
RESEARCH_ICON_SOURCE = b"INCrresearch icon"
RESEARCH_ICON_CUSTOM = b"ALWIweapon oil icon"
PHOENIX_RESEARCH_ICON_CUSTOM = b"ALPIphial icon"
INVENTORY_ITEM_SOURCE = b"AVk4Res Item"
INVENTORY_ITEM_CUSTOM = b"PXF1Phoenix Phial"
PROGRESS_SOURCE = b"INSrreasearch"
PROGRESS_CUSTOM = b"ALSRalchemy progress"
BUILDING_PROFILE_TILE = 1509
BUILDING_ICON_TILE = 1510
HERO_PORTRAIT_TILE = 6053
HERO_ICON_TILE = 6054
HERO_PANEL_TILE = 5411
BUILDING_PALETTE = 560
# The general palette used by the Phantom collapses the Alchemist's approved
# forest green and copper into blue-black. Fervus building palette 560 retains
# both materials and already owns the stock 247-250 sprite controls.
HERO_ART_PALETTE = 560
BREWING_BUTTON_TILES = (739, 740, 741, 742)
BREWING_DIALOG_FRAME_TILE = 594
RAGE_PROGRESS_TILES = (412, 413)
CLEAN_PROGRESS_SOURCE_TILES = (414, 415)
BREWING_PROGRESS_FRAME_SIZE = (162, 20)
VIGOR_ICON_TILES = (190, 212, 252, 293, 315, 319, 338, 342)
WEAPON_OIL_ICON_TILE = 162
PHOENIX_ITEM_TILES = tuple(range(8282, 8291))
PHOENIX_ITEM_INTERFACE_TILE = 8285
VIGOR_ICON_STYLES = {
    190: ((9, 31, 14), (184, 151, 42), 1.00),
    # Vines is AP69 interface set 1014: TILE 212 is its enabled artwork and
    # TILE 342 is the shared disabled mask. Earlier work patched set 1013,
    # which is Fervus Healing and therefore never affected the Vigor row.
    212: ((9, 31, 14), (184, 151, 42), 1.00),
    252: ((26, 27, 24), (104, 101, 83), 0.50),
    293: ((67, 68, 62), (139, 135, 111), 0.62),
    315: ((10, 45, 19), (231, 198, 62), 1.18),
    319: ((35, 29, 8), (247, 205, 58), 1.12),
    338: ((18, 58, 25), (170, 142, 37), 0.86),
    342: ((8, 12, 9), (72, 72, 65), 0.38),
}
HERO_SPRITE_RANGES = ((5919, 6053), (6055, 6119))
WARRIOR_WALK_START = 5919
WARRIOR_WALK_END = 5983


def indexed_body_geometry(stock, tile: bytes) -> tuple[int, int, int, int, int, int, int]:
    decoded = stock.decode_indexed_v3_tile(tile)
    if decoded is None:
        raise ValueError("Expected an indexed v3 sprite TILE")
    canvas_height, canvas_width, rows = decoded
    points = [
        (x, y)
        for y, row in enumerate(rows)
        for x, palette_index in enumerate(row)
        if 1 <= palette_index <= 246
    ]
    if not points:
        raise ValueError("Sprite TILE has no visible body pixels")
    left = min(x for x, _y in points)
    top = min(y for _x, y in points)
    right = max(x for x, _y in points)
    bottom = max(y for _x, y in points)
    _hotspot_x, hotspot_y = struct.unpack_from("<HH", tile, 10)
    return left, top, right, bottom, canvas_width, canvas_height, hotspot_y


def validate_packaged_walk_frame(stock, source_tile: bytes, rendered_tile: bytes, label: str) -> int:
    expected = indexed_body_geometry(stock, source_tile)
    actual = indexed_body_geometry(stock, rendered_tile)
    expected_height = expected[3] - expected[1] + 1
    actual_height = actual[3] - actual[1] + 1
    if abs(actual_height - expected_height) > 1:
        raise ValueError(
            f"{label} body height {actual_height} does not match stock Warrior "
            f"frame height {expected_height}"
        )
    expected_top = expected[1] - expected[6]
    expected_base = expected[3] - expected[6]
    actual_top = actual[1] - actual[6]
    actual_base = actual[3] - actual[6]
    if abs(actual_top - expected_top) > 1 or abs(actual_base - expected_base) > 1:
        raise ValueError(
            f"{label} hotspot geometry {(actual_top, actual_base)} does not match "
            f"stock Warrior {(expected_top, expected_base)}"
        )
    if (
        actual[0] < 1
        or actual[1] < 1
        or actual[2] >= actual[4] - 1
        or actual[3] >= actual[5] - 1
    ):
        raise ValueError(f"{label} touches its packaged TILE boundary: {actual[:6]}")
    decoded = stock.decode_indexed_v3_tile(rendered_tile)
    assert decoded is not None
    return sum(
        1
        for row in decoded[2]
        for palette_index in row
        if 1 <= palette_index <= 246
    )


def privateize_interface_imag_tiles(
    imag: bytes,
    tiles,
    append,
    name_prefix: bytes,
    overrides: dict[int, bytes] | None = None,
) -> bytes:
    """Clone every TILE reached by a stock interface IMAG into private slots.

    Interface frame IMAGs use a compact one-frame directional descriptor that
    differs from actor animation descriptors.  Trace its actual frame tables
    so unchanged stock frames remain literal byte-for-byte clones; empty TILE
    fall-through entries make disabled and alternate button states disappear.
    """
    overrides = overrides or {}
    patched = bytearray(imag)
    set_count = int.from_bytes(imag[20:24], "little")
    if set_count <= 0 or 24 + set_count * 8 > len(imag):
        raise ValueError("Interface IMAG has an invalid animation-set table")
    replacements: dict[int, int] = {}
    for set_index in range(set_count):
        table_offset = 24 + set_index * 8
        set_id = int.from_bytes(imag[table_offset : table_offset + 4], "little")
        set_offset = int.from_bytes(imag[table_offset + 4 : table_offset + 8], "little")
        if set_offset + 68 > len(imag):
            raise ValueError(f"Interface IMAG set {set_id} is truncated")
        direction_count = int.from_bytes(imag[set_offset : set_offset + 4], "little")
        if direction_count <= 0 or direction_count > 32:
            raise ValueError(f"Interface IMAG set {set_id} has invalid directions")
        for direction in range(direction_count):
            relative_offset = int.from_bytes(
                imag[set_offset + 64 + direction * 4 : set_offset + 68 + direction * 4],
                "little",
                signed=True,
            )
            direction_offset = set_offset + relative_offset + 4
            if direction_offset + 28 > len(imag):
                raise ValueError(f"Interface IMAG set {set_id} has a truncated direction")
            frame_count = int.from_bytes(
                imag[direction_offset : direction_offset + 4], "little"
            ) >> 16
            if frame_count <= 0 or frame_count > 64:
                raise ValueError(f"Interface IMAG set {set_id} has invalid frames")
            for frame in range(frame_count):
                tile_offset = direction_offset + 24 + frame * 8
                encoded = int.from_bytes(imag[tile_offset : tile_offset + 4], "little")
                source_index = encoded & 0xFFFF
                if source_index >= len(tiles):
                    raise ValueError(f"Interface IMAG references missing TILE {source_index}")
                if source_index not in replacements:
                    replacements[source_index] = append(
                        name_prefix + f"{source_index:05d}".encode("ascii"),
                        overrides.get(source_index, tiles[source_index].data),
                    )
                private_index = replacements[source_index]
                patched[tile_offset : tile_offset + 4] = (
                    ((encoded & 0xFFFF0000) | private_index).to_bytes(4, "little")
                )
    return bytes(patched)


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


def brewing_progress_frames(stock, tiles) -> dict[int, bytes]:
    """Build a private, single-span frame for the stock INSr renderer.

    Rage's 140x21 research-bar art contains a complete framed span.  Majesty
    tiles it when the control is widened, repeating the baked right and left
    caps.  The stock recruit bar provides the same grey/blue states as clean,
    uncrowded spans.  Resize those two stock states to the Brewing row, then
    encode them in private v1 TILEs using Rage's original TILE headers.
    """
    target_width, target_height = BREWING_PROGRESS_FRAME_SIZE
    output: dict[int, bytes] = {}
    for target_index, source_index in zip(
        RAGE_PROGRESS_TILES, CLEAN_PROGRESS_SOURCE_TILES
    ):
        source = tile_image(stock, tiles[source_index].data, []).convert("RGB")
        fitted = source.resize(
            (target_width, target_height), Image.Resampling.NEAREST
        )
        template = bytearray(tiles[target_index].data)
        if struct.unpack_from("<H", template, 0)[0] != 3:
            raise ValueError("Stock Rage progress TILE is no longer indexed-v3")
        struct.pack_into(
            "<3H", template, 2, target_height, target_width, target_width
        )
        encoded = stock.tile_v3_from_rgb(bytes(template), [], fitted.tobytes())
        if struct.unpack_from("<3H", encoded, 2) != (
            target_height,
            target_width,
            target_width,
        ):
            raise ValueError("Private Brewing progress TILE geometry changed")
        output[target_index] = encoded
    return output


def privateize_progress_imag(stock, imag: bytes, append, frames: dict[int, bytes]) -> bytes:
    """Clone the two stock INSr states without assuming button-IMAG layout."""
    replacements: dict[int, int] = {}
    for source_index in RAGE_PROGRESS_TILES:
        matches = [
            offset
            for offset in range(0, len(imag) - 3, 4)
            if struct.unpack_from("<I", imag, offset)[0] & 0xFFFF == source_index
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Stock INSr IMAG references TILE {source_index} {len(matches)} times"
            )
        replacements[source_index] = append(
            b"ALSR" + f"{source_index:05d}".encode("ascii"),
            frames[source_index],
        )
    return stock.remap_imag_low16_tile_indices(imag, replacements)


def brewing_button_frames(stock, tiles, palettes, icon_path: Path, output_dir: Path) -> list[Path]:
    # The approved large apparatus is the art-direction source, but it cannot
    # survive inside AP10's 14-pixel glyph well. Draw a deliberate pixel flask
    # while retaining the complete stock square, border, and state plate.
    _approved_icon = Image.open(icon_path).convert("RGBA")
    paths: list[Path] = []
    for state, tile_index in enumerate(BREWING_BUTTON_TILES):
        frame = tile_image(stock, tiles[tile_index].data, palettes)
        # AP10's actual icon well is x=6..19/y=6..19. Replace only that inner
        # glyph area; the surrounding 18x18 stock square must remain intact.
        well_fill = ((31, 30, 29), (160, 152, 121), (38, 38, 38), (109, 106, 97))[state]
        draw = ImageDraw.Draw(frame)
        draw.rectangle((6, 6, 19, 19), fill=(*well_fill, 255))
        if state == 2:
            outline, copper, liquid, shine = (
                (28, 28, 28, 255),
                (90, 90, 90, 255),
                (66, 66, 66, 255),
                (130, 130, 130, 255),
            )
        else:
            brightness = 1.25 if state in (1, 3) else 1.0
            color = lambda rgb: tuple(min(255, round(channel * brightness)) for channel in rgb) + (255,)
            outline, copper, liquid, shine = (
                color((48, 26, 8)),
                color((188, 113, 25)),
                color((80, 139, 34)),
                color((236, 191, 76)),
            )
        # Thirteen-pixel copper potion flask: neck, shoulders, round vessel,
        # green liquid, and one highlight. Crisp pixels read better here than
        # a downsampled illustration.
        draw.rectangle((11, 7, 14, 9), fill=outline)
        draw.rectangle((12, 7, 13, 9), fill=copper)
        draw.polygon(((10, 9), (15, 9), (17, 12), (17, 17), (15, 19), (10, 19), (8, 17), (8, 12)), fill=outline)
        draw.polygon(((11, 10), (14, 10), (16, 12), (16, 17), (14, 18), (11, 18), (9, 17), (9, 12)), fill=copper)
        draw.rectangle((10, 14, 15, 17), fill=liquid)
        draw.point((11, 11), fill=shine)
        draw.point((10, 13), fill=shine)
        path = output_dir / f"brewing-button-frame-{state}.png"
        frame.save(path)
        paths.append(path)
    return paths


def vigor_icon_overrides(stock, tiles, icon_path: Path, output_dir: Path) -> dict[int, bytes]:
    """Clone AP69's stock first-spell icon states with private Vigor artwork."""
    master = Image.open(icon_path).convert("RGB")
    output: dict[int, bytes] = {}
    for tile_index in VIGOR_ICON_TILES:
        tile = tiles[tile_index].data
        if len(tile) < 8:
            raise ValueError(f"Stock Vigor icon template {tile_index} is truncated")
        height, width = struct.unpack_from("<HH", tile, 2)
        background, border, brightness = VIGOR_ICON_STYLES[tile_index]
        frame = Image.new("RGB", (width, height), background)
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, 0, width - 1, height - 1), outline=border)
        if width >= 6 and height >= 6:
            draw.rectangle((1, 1, width - 2, height - 2), outline=(4, 9, 5))
        # The prepared Vigor master already includes the same one-pixel gold
        # recipe frame as the other Brewing icons.  Keep only the stock tile's
        # outer safety pixel instead of shrinking the artwork a second time.
        icon = master.resize((max(1, width - 2), max(1, height - 2)), Image.Resampling.LANCZOS)
        if brightness != 1.0:
            from PIL import ImageEnhance

            icon = ImageEnhance.Brightness(icon).enhance(brightness)
            if brightness < 0.7:
                icon = ImageEnhance.Color(icon).enhance(0.25)
        frame.paste(icon, ((width - icon.width) // 2, (height - icon.height) // 2))
        path = output_dir / f"vigor-icon-state-{tile_index}.png"
        frame.save(path)
        output[tile_index] = stock.tile_from_rgb(tile, [], frame.tobytes())
    return output


def brewing_dialog_frame(
    stock, tiles, panel_path: Path, output_path: Path
) -> Path:
    """Put the approved Brewing backing behind AP69's exact stock controls."""
    stock_frame = tile_image(stock, tiles[BREWING_DIALOG_FRAME_TILE].data, [])
    panel = Image.open(panel_path).convert("RGBA").resize(
        stock_frame.size, Image.Resampling.LANCZOS
    )
    result = panel.copy()
    source = stock_frame.load()
    target = result.load()
    for y in range(stock_frame.height):
        for x in range(stock_frame.width):
            pixel = source[x, y]
            # Preserve only AP69's functional row borders, outer frame, and
            # Back/Next controls.  Its ornamental Fervus title capsule was the
            # source of the visible curls/artifacts around BREWING.
            preserve = (
                y < 22
                or 54 <= y < 151
                or y >= 222
                or x < 6
                or x >= stock_frame.width - 6
            )
            if preserve and pixel[3]:
                target[x, y] = pixel
    # The title string is drawn by the stock dialog controller. Give it a
    # restrained Alchemist capsule with the stock dimensions, without copying
    # Fervus's purple ornamental pixels.
    draw = ImageDraw.Draw(result)
    draw.rounded_rectangle(
        (17, 24, stock_frame.width - 18, 50),
        radius=12,
        fill=(17, 39, 23, 255),
        outline=(145, 112, 47, 255),
        width=2,
    )
    # AP69 also carries several purple ornamental/control-color arcs below the
    # title and around its old Fervus medallion. They are not functional UI
    # controls; restore our approved backing anywhere one survived the stock
    # border copy.
    result_pixels = result.load()
    panel_pixels = panel.load()
    for y in range(result.height):
        for x in range(result.width):
            red, green, blue, alpha = result_pixels[x, y]
            if (
                alpha
                and red > 70
                and blue > 65
                and red + blue > green * 2.15
            ):
                result_pixels[x, y] = panel_pixels[x, y]
    result.save(output_path)
    return output_path


def write_maindata(repo: Path, game_data: Path, art_dir: Path, output: Path) -> None:
    stock = load_stock_pipeline(repo)
    source = game_data / "maindata.cam"
    tiles = stock.read_cam_entries(source, b"TILE")
    palettes = stock.read_cam_entries(source, b"SPLT")
    hero_imag = stock.read_cam_entry(source, b"IMAG", HERO_SOURCE).data
    building_imags = [stock.read_cam_entry(source, b"IMAG", name).data for name in BUILDING_SOURCES]
    phoenix_item_imag = stock.read_cam_entry(
        source, b"IMAG", INVENTORY_ITEM_SOURCE
    ).data

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
    warrior_walk_geometry = {
        source_index: indexed_body_geometry(stock, tiles[source_index].data)
        for source_index in range(WARRIOR_WALK_START, WARRIOR_WALK_END)
    }
    warrior_walk_heights = {
        source_index: geometry[3] - geometry[1] + 1
        for source_index, geometry in warrior_walk_geometry.items()
    }
    warrior_walk_base_offsets = {
        # tile_from_png_source's body_base_offset is bottom-exclusive.
        source_index: geometry[3] - geometry[6] + 1
        for source_index, geometry in warrior_walk_geometry.items()
    }
    walk_body_areas: dict[int, list[int]] = {direction: [] for direction in range(8)}
    for start, end in HERO_SPRITE_RANGES:
        for source_index in range(start, end):
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
                target_art_height=(
                    warrior_walk_heights[source_index]
                    if WARRIOR_WALK_START <= source_index < WARRIOR_WALK_END
                    else None
                ),
                body_base_offset=(
                    warrior_walk_base_offsets[source_index]
                    if WARRIOR_WALK_START <= source_index < WARRIOR_WALK_END
                    else None
                ),
            )
            if WARRIOR_WALK_START <= source_index < WARRIOR_WALK_END:
                direction = (source_index - WARRIOR_WALK_START) // 8
                walk_body_areas[direction].append(
                    validate_packaged_walk_frame(
                        stock,
                        tiles[source_index].data,
                        rendered,
                        f"Alchemist Walk TILE {source_index}",
                    )
                )
            hero_replacements[source_index] = append(
                f"ALC1Hero{source_index - 5919:04d}".encode("ascii"), rendered
            )

    for direction, areas in walk_body_areas.items():
        if len(areas) != 8 or min(areas) < max(areas) * 0.62:
            raise ValueError(
                f"Alchemist Walk direction {direction} has an incomplete packaged "
                f"frame body: {areas}"
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

    # Retail and the SDK model carried items as ordinary IsInventoryItem units
    # backed by AVk4's Inactive/Minimap/Interface animation sets. Preserve that
    # whole structure and privatize only the image identity and referenced art.
    phoenix_item_replacements: dict[int, int] = {}
    item_master = Image.open(
        art_dir / "interface/phoenix-phial-item-100.png"
    ).convert("RGB")
    for source_index in PHOENIX_ITEM_TILES:
        template = tiles[source_index].data
        height, width = struct.unpack_from("<HH", template, 2)
        rendered = stock.tile_from_rgb(
            template,
            palettes,
            item_master.resize((width, height), Image.Resampling.LANCZOS).tobytes(),
        )
        phoenix_item_replacements[source_index] = append(
            f"PXF1Item{source_index:05d}".encode("ascii"), rendered
        )
    phoenix_item_imag = stock.remap_imag_low16_tile_indices(
        phoenix_item_imag, phoenix_item_replacements
    )

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
        stock.CamEntry(stock.pad_name(INVENTORY_ITEM_CUSTOM), phoenix_item_imag),
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
    dialog_imag = stock.read_cam_entry(source, b"IMAG", BUILDING_DIALOG_SOURCE).data
    navigation_imag = stock.read_cam_entry(source, b"IMAG", NAVIGATION_SOURCE).data
    research_icon_imag = stock.read_cam_entry(source, b"IMAG", RESEARCH_ICON_SOURCE).data
    progress_imag = stock.read_cam_entry(source, b"IMAG", PROGRESS_SOURCE).data
    base_max = len(tiles) - 1
    extra: list = []

    def append(name: bytes, data: bytes) -> int:
        index = base_max + len(extra) + 1
        extra.append(stock.CamEntry(stock.pad_name(name), data))
        return index

    panel_overrides = {
        474: stock.tile_v1_embedded_from_rgb(
            tiles[474].data,
            image_rgb(art_dir / "interface/building-panel-200x245.png", (200, 245)),
        ),
        495: stock.tile_v1_embedded_from_rgb(
            tiles[495].data,
            image_rgb(art_dir / "interface/brewing-panel-200x245.png", (200, 245)),
        ),
    }
    raw_imag = privateize_interface_imag_tiles(
        raw_imag, tiles, append, b"ALTI", panel_overrides
    )

    button_paths = brewing_button_frames(
        stock, tiles, [], art_dir / "interface/brewing-button-icon-19.png", art_dir / "interface"
    )
    button_overrides: dict[int, bytes] = {}
    for tile_index, path in zip(BREWING_BUTTON_TILES, button_paths):
        button_overrides[tile_index] = stock.tile_from_png_native_size(
            tiles[tile_index].data, [], path
        )
    frame_imag = privateize_interface_imag_tiles(
        frame_imag, tiles, append, b"ALBB", button_overrides
    )
    dialog_path = brewing_dialog_frame(
        stock,
        tiles,
        art_dir / "interface/brewing-panel-200x245.png",
        art_dir / "interface/brewing-dialog-frame.png",
    )
    dialog_imag = privateize_interface_imag_tiles(
        dialog_imag,
        tiles,
        append,
        b"ALBG",
        {
            BREWING_DIALOG_FRAME_TILE: stock.tile_from_png_native_size(
                tiles[BREWING_DIALOG_FRAME_TILE].data, [], dialog_path
            )
        },
    )
    navigation_imag = privateize_interface_imag_tiles(
        navigation_imag,
        tiles,
        append,
        b"ALIN",
        vigor_icon_overrides(
            stock,
            tiles,
            art_dir / "interface/vigor-elixir-icon-24.png",
            art_dir / "interface",
        ),
    )
    research_icon_imag = privateize_interface_imag_tiles(
        research_icon_imag,
        tiles,
        append,
        b"ALWI",
        {
            WEAPON_OIL_ICON_TILE: stock.tile_v1_embedded_from_rgb(
                tiles[WEAPON_OIL_ICON_TILE].data,
                image_rgb(art_dir / "interface/weapon-oil-icon-25.png", (25, 25)),
            )
        },
    )
    phoenix_research_icon_imag = privateize_interface_imag_tiles(
        stock.read_cam_entry(source, b"IMAG", RESEARCH_ICON_SOURCE).data,
        tiles,
        append,
        b"ALPI",
        {
            WEAPON_OIL_ICON_TILE: stock.tile_v1_embedded_from_rgb(
                tiles[WEAPON_OIL_ICON_TILE].data,
                image_rgb(
                    art_dir / "interface/phoenix-phial-icon-25.png", (25, 25)
                ),
            )
        },
    )
    progress_imag = privateize_progress_imag(
        stock,
        progress_imag,
        append,
        brewing_progress_frames(stock, tiles),
    )

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
                    stock.CamEntry(stock.pad_name(BUILDING_DIALOG_CUSTOM), dialog_imag),
                    stock.CamEntry(stock.pad_name(NAVIGATION_CUSTOM), navigation_imag),
                    stock.CamEntry(stock.pad_name(RESEARCH_ICON_CUSTOM), research_icon_imag),
                    stock.CamEntry(
                        stock.pad_name(PHOENIX_RESEARCH_ICON_CUSTOM),
                        phoenix_research_icon_imag,
                    ),
                    stock.CamEntry(stock.pad_name(PROGRESS_CUSTOM), progress_imag),
                ),
            ),
            stock.CamSection(b"TILE", b"\x01\x00\x00\x00", tuple(tile_entries)),
        ),
        output,
    )
