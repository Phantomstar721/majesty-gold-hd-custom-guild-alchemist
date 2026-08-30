from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import struct
import sys

from PIL import Image, ImageChops, ImageDraw

from approved_sprite_bundle import (
    load_approved_sprite_bundle,
    package_provenance,
    patch_completed_warrior_imag,
    remap_approved_warrior_imag,
    sha256_bytes,
    sha256_file,
    validate_packaged_approved_sprite_cam,
)
from approved_building_bundle import (
    PAYLOAD_AGGREGATE_SHA256 as APPROVED_BUILDING_PAYLOAD_SHA256,
    SOURCE_IMAG_NAMES as APPROVED_BUILDING_SOURCE_IMAGS,
    load_approved_building_bundle,
    package_approved_building_tile,
    patch_approved_building_imag,
    stable_state_geometry,
    validate_packaged_approved_building_cam,
)


HERO_SOURCE = b"AVL1Warrior"
HERO_CUSTOM = b"ALC1Alchemist"
BUILDING_SOURCES = (
    *APPROVED_BUILDING_SOURCE_IMAGS,
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
TACTICAL_CURSOR_SOURCE = b"CUR1Tactical Cursor"
TACTICAL_CURSOR_CUSTOM = TACTICAL_CURSOR_SOURCE
TACTICAL_CURSOR_TEMPLATE_SET_ID = 1014
PHILOSOPHERS_STONE_CURSOR_SET_ID = 1039
TACTICAL_CURSOR_TEMPLATE_TILE = 38
TACTICAL_CURSOR_SOURCE_SHA256 = (
    "093fe7e069f74be730685e6ed123f83396316de866196daeccfdc97d430ff212"
)
TACTICAL_CURSOR_TEMPLATE_TILE_SHA256 = (
    "51612f68948df25bb2760c443f2b2c9e8c5f3c36850cfb6a0702178b584b750f"
)
RESEARCH_ICON_SOURCE = b"INCrresearch icon"
RESEARCH_ICON_CUSTOM = b"ALWIweapon oil icon"
PHOENIX_RESEARCH_ICON_CUSTOM = b"ALPIphial icon"
INVENTORY_ITEM_SOURCE = b"AVk4Res Item"
INVENTORY_ITEM_CUSTOM = b"PXF1Phoenix Phial"
PHOENIX_LIFECYCLE_SOURCE = b"HRC1resurrect_e"
PHOENIX_LIFECYCLE_CUSTOM = b"PXE1Phoenix Life"
PHOENIX_EFFECT_TEMPLATE_SOURCE = b"XR30frost_fld_hit"
PHOENIX_EFFECT_PALETTE = 505
# Agrela's 29-frame/1500-ms table remains the sole resurrection owner. Its
# complete visual table is privatized with Eternal Soul's phased artwork so
# the Phoenix and callback share the exact same stock lifetime.
PHOENIX_LIFECYCLE_ANIMATION_SET = 64
PHOENIX_LIFECYCLE_FRAMES = 29
# Keep HRC1's complete 29-slot owner/table literal. Live testing established
# that painting every slot leaves custom art visible after stock
# Shared_End_Resurrect restores movement, so the approved presentation occupies
# its first 15 slots and the remaining private slots are transparent. No timer,
# callback, or second effector is introduced.
PHOENIX_VISIBLE_FRAMES = 15
PHOENIX_EFFECT_TEMPLATE_ANIMATION_SET = 96
PHOENIX_EFFECT_TEMPLATE_FRAMES = 6
PHOENIX_EFFECT_HEADER = (3, 99, 103, 0, 32, 51, 49, 8)
BUFF_ICON_TEMPLATE_SOURCE = b"XR25plague_icon"
VIGOR_EFFECT_CUSTOM = b"ALV1Vigor Spark"
FLASH_FLASK_BUFF_CUSTOM = b"AFF1Flash Flask Icon"
FLASH_FLASK_ACTIVATION_CUSTOM = b"AFF2Flash Flask Cast"
STUN_SERUM_IMPACT_CUSTOM = b"ASS1Stun Serum Hit"
STUN_SERUM_RESTRAINT_CUSTOM = b"ASS2Stun Serum Bind"
STUN_SERUM_DEBUFF_CUSTOM = b"ASS3Stun Serum Icon"
PARALYTIC_OIL_RESTRAINT_CUSTOM = b"ASO3Oil Restraint"
PHILOSOPHERS_STONE_HIT_CUSTOM = b"AST1Stone Hit"
ARCANE_INFUSION_EFFECT_CUSTOM = b"AIF1Arcane Infuse"
VIGOR_ACTIVATION_EFFECT_CUSTOM = b"AIV1Vigor Ritual"
# Agrela resurrection supplies a stock 29-frame, default-100-ms one-shot
# lifecycle. Stone keeps that complete table and expands only its private art
# canvas so the transmutation reads as a major sovereign event.
PHILOSOPHERS_STONE_ANIMATION_SET = 64
PHILOSOPHERS_STONE_FRAMES = 29
PHILOSOPHERS_STONE_DELAY_MS = 0
PHILOSOPHERS_STONE_HEADER = (3, 184, 192, 0, 32, 96, 92, 8)
# Arcane Infusion uses the same stock HRC1 29-frame one-shot as Stone. Its
# private TILE canvas instead matches the proven level-3 Laboratory object
# canvas/hotspot so an effector created on the selected building remains
# centered over that exact Laboratory rather than over a generic unit box.
ARCANE_INFUSION_ANIMATION_SET = PHILOSOPHERS_STONE_ANIMATION_SET
ARCANE_INFUSION_FRAMES = PHILOSOPHERS_STONE_FRAMES
ARCANE_INFUSION_DELAY_MS = PHILOSOPHERS_STONE_DELAY_MS
ARCANE_INFUSION_PALETTE = 560
ARCANE_INFUSION_HEADER = (3, 269, 213, 0, 32, 140, 65, 8)
# The generated source cells do not share a common crop origin. These are the
# centers of the persistent alchemical ring/cardinal motif in each authored
# phase, measured in the original 362x724 cells. Registering that landmark—
# rather than each phase's changing visible bounds—keeps the ritual fixed to
# one world-space pixel while flames, sparks, and fragments grow around it.
ARCANE_INFUSION_SOURCE_ANCHORS = (
    (168, 439),
    (160, 427),
    (177, 427),
    (188, 427),
    (183, 427),
    (193, 446),
)
VIGOR_ACTIVATION_ANIMATION_SET = PHILOSOPHERS_STONE_ANIMATION_SET
VIGOR_ACTIVATION_FRAMES = PHILOSOPHERS_STONE_FRAMES
VIGOR_ACTIVATION_DELAY_MS = PHILOSOPHERS_STONE_DELAY_MS
VIGOR_ACTIVATION_PALETTE = ARCANE_INFUSION_PALETTE
VIGOR_ACTIVATION_HEADER = ARCANE_INFUSION_HEADER
VIGOR_ACTIVATION_SOURCE_ANCHORS = (
    (168, 441),
    (158, 439),
    (173, 438),
    (194, 437),
    (201, 439),
    (193, 441),
)
MIASMA_STORM_SOURCE = b"WRg1meteor_swarm_E1"
MIASMA_MISSILE_SOURCE = b"WPg3meteor_missile"
MIASMA_PARTICLE_SOURCE = b"XL20MeteorStrmEffct"
MIASMA_STORM_CUSTOM = b"AMm1Miasma Cloud"
MIASMA_MISSILE_CUSTOM = b"AMm2Miasma Missile"
MIASMA_PARTICLE_CUSTOM = b"AMm4Miasma Vapor"
MIASMA_DEBUFF_CUSTOM = b"AMm5Miasma Icon"
MIASMA_ANCHOR_CUSTOM = b"AMm6Miasma Anchor"
# Keep each private effect on the closest literal stock palette for its art.
# Giant Spider palette 577 preserves the approved Miasma raster's yellow-green
# vapor range.  The previously shared fire palette 505 collapsed that range to
# dark orange.  Tempest and the approved overhead drop remain on 505.
MIASMA_CLOUD_PALETTE = 577
MIASMA_DEBUFF_PALETTE = 505
MIASMA_CLOUD_BRIGHTNESS = 1.15
MIASMA_CLOUD_SATURATION = 1.40
MIASMA_PARTICLE_BRIGHTNESS = 0.95
MIASMA_PARTICLE_SATURATION = 1.40
MIASMA_PARTICLE_ALPHA_SCALE = 0.72
REAGENT_READY_SOURCE = b"ARM1WizardTower"
REAGENT_READY_CUSTOM = b"ALR1Reagent Ready"
REAGENT_READY_SOURCE_SHA256 = (
    "eafcd91a5f8f63da85bc7f692e4dc75737ed71cc2d388dd9341f912815f1bb7c"
)
REAGENT_READY_SOURCE_TILES = tuple(range(2349, 2365))
REAGENT_READY_PALETTE = 577
REAGENT_READY_CANVAS = (269, 213)
REAGENT_READY_HOTSPOT = (140, 65)
# The accepted level-3 sprite's round green potion pool occupies the lower
# center of the object canvas. The first live build fitted the full portrait
# effect into a narrow box, leaving only a tiny off-center wisp. Use the broad
# bubbling lower half of that art and cover the actual pool surface instead.
REAGENT_READY_ART_BOX = (121, 133, 201, 178)
REAGENT_READY_SOURCE_CROP_TOP = 0.62
METEOR_STORM_RADIUS = 175
# Keep Tempest's private Meteor field on the complete stock field footprint.
# The previous second scale-down made its visible boundary too small to
# communicate which units were inside the 150-unit gameplay radius.
BUFF_ICON_PALETTE = 560
OVERHEAD_EFFECT_FIT_RATIO = 0.80
FLASH_FLASK_ACTIVATION_PALETTE = 505
FLASH_FLASK_ACTIVATION_HEADER = (3, 99, 103, 0, 32, 51, 43, 8)
FLASH_FLASK_ACTIVATION_SOURCE_DELAY_MS = 50
FLASH_FLASK_ACTIVATION_DELAY_MS = 0
VINES_FIXED_HEADER = (3, 113, 108, 108, 32, 54, 54, 8)
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
APPROVED_BUILDING_ROOT = Path("assets/source/approved-alchemist-building-set-v1")
APPROVED_INTERFACE_ART_SHA256 = {
    HERO_PORTRAIT_TILE: "f78a44a14bff09a378e4392a2bbaa7c25d4ed7405a48b0cddd7428843113c944",
    HERO_ICON_TILE: "3131dd204cc42d6c8ac2a5cb865e65ae1a5eeb942c7c8fb160feda61c9fc81a0",
    HERO_PANEL_TILE: "7c3d2a2ba50bed0e313ee90c8c67976961886c3ee5d6e2e7b9644f1c47234986",
}
BREWING_BUTTON_TILES = (739, 740, 741, 742)
BREWING_DIALOG_FRAME_TILE = 594
RAGE_PROGRESS_TILES = (412, 413)
CLEAN_PROGRESS_SOURCE_TILES = (414, 415)
BREWING_PROGRESS_FRAME_SIZE = (162, 20)
RECIPE_GOLD_PLATE_SOURCE_TILES = (655, 656, 657, 658)
RECIPE_PRIVATE_PLATE_TILE_GROUPS = (
    (683, 684, 685, 686),
    (687, 688, 689, 690),
    (691, 692, 693, 694),
)
RECIPE_PRIVATE_PLATE_SIZE = (162, 20)
VIGOR_ICON_TILES = (177, 199, 252, 280, 302, 319, 325, 342)
WEAPON_OIL_ICON_TILE = 162
PHOENIX_ITEM_TILES = tuple(range(8282, 8291))
PHOENIX_ITEM_INTERFACE_TILE = 8285
VIGOR_ICON_STYLES = {
    177: ((9, 31, 14), (184, 151, 42), 1.00),
    # CGBR privatizes AP69's complete first spell row. That row is image set
    # 1013 (0x3F5), whose enabled TILE is 199 and whose disabled mask is 342.
    # Keep the entire 0x3F5 state family private; patching AP69's second slot
    # (0x3F6) leaves Healing's green-plus art on Vigor.
    199: ((9, 31, 14), (184, 151, 42), 1.00),
    252: ((26, 27, 24), (104, 101, 83), 0.50),
    280: ((67, 68, 62), (139, 135, 111), 0.62),
    302: ((10, 45, 19), (231, 198, 62), 1.18),
    319: ((35, 29, 8), (247, 205, 58), 1.12),
    325: ((18, 58, 25), (170, 142, 37), 0.86),
    342: ((8, 12, 9), (72, 72, 65), 0.38),
}
HERO_SPRITE_RANGES = ((5919, 6053), (6055, 6119))
WARRIOR_WALK_START = 5919
WARRIOR_WALK_END = 5983


def keyed_strip_frames(source_png: Path, frame_count: int) -> list[Image.Image]:
    """Split an approved black-backed strip and recover transparent frames."""
    with Image.open(source_png) as loaded:
        strip = loaded.convert("RGB")
    frames: list[Image.Image] = []
    for frame_index in range(frame_count):
        left = round(strip.width * frame_index / frame_count)
        right = round(strip.width * (frame_index + 1) / frame_count)
        rgb = strip.crop((left, 0, right, strip.height))
        red, green, blue = rgb.split()
        alpha = ImageChops.lighter(ImageChops.lighter(red, green), blue).point(
            lambda value: 0 if value <= 4 else min(255, round((value - 4) * 1.45))
        )
        rgba = rgb.convert("RGBA")
        rgba.putalpha(alpha)
        bbox = alpha.getbbox()
        if bbox is None:
            raise ValueError(f"Approved strip frame {frame_index} has no visible art")
        frames.append(rgba.crop(bbox))
    max_width = max(frame.width for frame in frames)
    max_height = max(frame.height for frame in frames)
    normalized: list[Image.Image] = []
    for frame in frames:
        canvas = Image.new("RGBA", (max_width, max_height), (0, 0, 0, 0))
        canvas.alpha_composite(
            frame,
            (
                (max_width - frame.width) // 2,
                (max_height - frame.height) // 2,
            ),
        )
        normalized.append(canvas)
    return normalized


def keyed_strip_cells(source_png: Path, frame_count: int) -> list[Image.Image]:
    """Split a black-backed strip while preserving each authored cell origin."""
    with Image.open(source_png) as loaded:
        strip = loaded.convert("RGB")
    frames: list[Image.Image] = []
    for frame_index in range(frame_count):
        left = round(strip.width * frame_index / frame_count)
        right = round(strip.width * (frame_index + 1) / frame_count)
        rgb = strip.crop((left, 0, right, strip.height))
        red, green, blue = rgb.split()
        alpha = ImageChops.lighter(ImageChops.lighter(red, green), blue).point(
            lambda value: 0 if value <= 4 else min(255, round((value - 4) * 1.45))
        )
        if alpha.getbbox() is None:
            raise ValueError(f"Approved strip frame {frame_index} has no visible art")
        rgba = rgb.convert("RGBA")
        rgba.putalpha(alpha)
        frames.append(rgba)
    return frames


def black_key_grid_frames(
    source_png: Path, columns: int, rows: int
) -> list[Image.Image]:
    """Split a pure-black phase sheet and recover soft translucent alpha."""
    with Image.open(source_png) as loaded:
        sheet = loaded.convert("RGB")
    frames: list[Image.Image] = []
    for row in range(rows):
        for column in range(columns):
            left = round(sheet.width * column / columns)
            right = round(sheet.width * (column + 1) / columns)
            top = round(sheet.height * row / rows)
            bottom = round(sheet.height * (row + 1) / rows)
            rgb = sheet.crop((left, top, right, bottom))
            red, green, blue = rgb.split()
            alpha = ImageChops.lighter(ImageChops.lighter(red, green), blue).point(
                lambda value: 0 if value <= 7 else min(255, round((value - 7) * 1.35))
            )
            rgba = rgb.convert("RGBA")
            rgba.putalpha(alpha)
            bbox = alpha.getbbox()
            if bbox is None:
                raise ValueError(
                    f"Miasma source cell {column},{row} has no visible art"
                )
            frames.append(rgba.crop(bbox))
    return frames


def generated_area_effect_tile(
    stock,
    template_tile: bytes,
    palettes,
    source_png: Path,
    frame_index: int,
    frame_count: int,
    fit_ratio: float,
    brightness: float,
    saturation: float,
    palette_index: int,
) -> bytes:
    """Render a stable-footprint stock Meteor field with moving interior art."""
    from PIL import ImageEnhance

    height = struct.unpack_from("<H", template_tile, 2)[0]
    width = struct.unpack_from("<H", template_tile, 4)[0]
    source_frames = black_key_grid_frames(source_png, 4, 2)
    normalized_frames: list[Image.Image] = []
    for source in source_frames:
        fit = min(
            width * fit_ratio / max(1, source.width),
            height * fit_ratio / max(1, source.height),
        )
        source = source.resize(
            (
                max(2, round(source.width * fit)),
                max(2, round(source.height * fit)),
            ),
            Image.Resampling.LANCZOS,
        )
        normalized = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        normalized.alpha_composite(
            source,
            ((width - source.width) // 2, (height - source.height) // 2),
        )
        normalized_frames.append(normalized)

    phase = frame_index / max(1, frame_count)
    source_position = phase * len(normalized_frames)
    source_index = math.floor(source_position) % len(normalized_frames)
    next_index = (source_index + 1) % len(normalized_frames)
    blend = source_position - math.floor(source_position)
    moving = Image.blend(
        normalized_frames[source_index],
        normalized_frames[next_index],
        blend,
    )
    # Keep the field footprint still while its source phases undulate. This is
    # the visual motion of Troll spawn fog inside Meteor Storm's fixed owner,
    # not Endless Winter's rotating ground plane.
    mask = Image.new("L", (width, height), 0)
    pixels = mask.load()
    center_x = (width - 1) / 2.0
    center_y = (height - 1) / 2.0
    radius_x = max(1.0, width * 0.47)
    radius_y = max(1.0, height * 0.47)
    for y in range(height):
        for x in range(width):
            radius = math.sqrt(
                ((x - center_x) / radius_x) ** 2
                + ((y - center_y) / radius_y) ** 2
            )
            if radius <= 0.76:
                alpha = 255
            elif radius >= 0.98:
                alpha = 0
            else:
                transition = (radius - 0.76) / 0.22
                smooth = transition * transition * (3.0 - 2.0 * transition)
                alpha = round(255 * (1.0 - smooth))
            pixels[x, y] = alpha
    canvas = Image.composite(moving, normalized_frames[0], mask)
    canvas = ImageEnhance.Color(canvas).enhance(saturation)
    canvas = ImageEnhance.Brightness(canvas).enhance(brightness)
    header = list(struct.unpack_from("<8H", template_tile, 0))
    header[4] = 32
    return stock.rgba_to_indexed_tile(
        canvas,
        palettes,
        palette_index,
        tuple(header),
    )


def generated_miasma_particle_tile(
    stock,
    template_tile: bytes,
    palettes,
    source_png: Path,
    frame_index: int,
    frame_count: int,
    palette_index: int,
    brightness: float = 0.60,
    saturation: float = 1.0,
    alpha_scale: float = 0.62,
) -> bytes:
    """Render a small translucent vapor curl for the stock Meteor emitter."""
    from PIL import ImageEnhance

    height = struct.unpack_from("<H", template_tile, 2)[0]
    width = struct.unpack_from("<H", template_tile, 4)[0]
    frames = black_key_grid_frames(source_png, 4, 2)
    source = frames[frame_index % len(frames)]
    source.thumbnail(
        (
            max(3, round(width * 0.78)),
            max(3, round(height * 0.78)),
        ),
        Image.Resampling.LANCZOS,
    )
    source = source.rotate(
        frame_index * 360.0 / max(1, frame_count),
        resample=Image.Resampling.BICUBIC,
        expand=True,
    )
    source = ImageEnhance.Color(source).enhance(saturation)
    source = ImageEnhance.Brightness(source).enhance(brightness)
    alpha = source.getchannel("A").point(lambda value: round(value * alpha_scale))
    source.putalpha(alpha)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(
        source,
        ((width - source.width) // 2, (height - source.height) // 2),
    )
    header = list(struct.unpack_from("<8H", template_tile, 0))
    header[4] = 32
    return stock.rgba_to_indexed_tile(
        canvas,
        palettes,
        palette_index,
        tuple(header),
    )


def generated_reagent_ready_tile(
    stock,
    template_tile: bytes,
    palettes,
    source_png: Path,
    frame_index: int,
    frame_count: int,
) -> bytes:
    """Paint a clear bubbling pulse over the level-3 Lab's potion pool."""
    from PIL import ImageEnhance

    header = list(struct.unpack_from("<8H", template_tile, 0))
    height, width = header[1], header[2]
    if (width, height) != REAGENT_READY_CANVAS:
        raise ValueError(
            f"Level-3 Reagent overlay canvas changed: {(width, height)}"
        )
    if tuple(header[5:7]) != REAGENT_READY_HOTSPOT:
        raise ValueError(
            f"Level-3 Reagent overlay hotspot changed: {tuple(header[5:7])}"
        )

    with Image.open(source_png) as loaded:
        source = loaded.convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("Reagent-ready source has no visible alpha")
    source = source.crop(bbox)
    crop_top = round(source.height * REAGENT_READY_SOURCE_CROP_TOP)
    source = source.crop((0, crop_top, source.width, source.height))

    left, top, right, bottom = REAGENT_READY_ART_BOX
    target_width = right - left
    target_height = bottom - top
    fit = min(
        target_width / max(1, source.width),
        target_height / max(1, source.height),
    )
    source = source.resize(
        (
            max(2, round(source.width * fit)),
            max(2, round(source.height * fit)),
        ),
        Image.Resampling.LANCZOS,
    )
    phase = 2.0 * math.pi * frame_index / max(1, frame_count)
    pulse = 0.95 + 0.25 * (0.5 + 0.5 * math.sin(phase))
    source = ImageEnhance.Brightness(source).enhance(pulse)
    alpha = source.getchannel("A").point(lambda value: round(value * 0.92))
    source.putalpha(alpha)

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(
        source,
        (
            left + (target_width - source.width) // 2,
            bottom - source.height + round(math.sin(phase)),
        ),
    )
    # The source contributes the bubbling plume. A broad, crisp pool ring makes
    # the readiness state legible at Majesty's native zoom and fixes the live
    # presentation's previous resemblance to a stray yellow particle.
    ring = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ring)
    ring_brightness = 0.82 + 0.18 * (0.5 + 0.5 * math.sin(phase))
    outer_color = (
        round(205 * ring_brightness),
        round(242 * ring_brightness),
        round(72 * ring_brightness),
        235,
    )
    inner_color = (
        250,
        round(218 * ring_brightness),
        round(70 * ring_brightness),
        245,
    )
    draw.ellipse((129, 150, 194, 180), outline=outer_color, width=2)
    arc_start = round(frame_index * 360 / max(1, frame_count))
    draw.arc(
        (135, 154, 188, 176),
        start=arc_start,
        end=arc_start + 150,
        fill=inner_color,
        width=2,
    )
    draw.arc(
        (135, 154, 188, 176),
        start=arc_start + 180,
        end=arc_start + 270,
        fill=inner_color,
        width=1,
    )
    canvas.alpha_composite(ring)
    header[4] = 32
    return stock.rgba_to_indexed_tile(
        canvas,
        palettes,
        REAGENT_READY_PALETTE,
        tuple(header),
    )


def generated_approved_strip_tile(
    stock,
    template_tile: bytes,
    palettes,
    source_png: Path,
    source_frame_count: int,
    frame_index: int,
    output_frame_count: int,
    palette_index: int,
    fixed_header: tuple[int, int, int, int, int, int, int, int] | None = None,
    fit_ratio: float = 0.94,
) -> bytes:
    """Fit one approved strip phase into a stock overlay's fixed attachment."""
    source_frames = keyed_strip_frames(source_png, source_frame_count)
    position = frame_index * source_frame_count / max(1, output_frame_count)
    source_index = math.floor(position) % source_frame_count
    next_index = (source_index + 1) % source_frame_count
    blend = position - math.floor(position)
    source = Image.blend(source_frames[source_index], source_frames[next_index], blend)
    bbox = source.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"Approved strip phase {frame_index} became transparent")
    source = source.crop(bbox)

    if fixed_header is None:
        header = list(struct.unpack_from("<8H", template_tile, 0))
        width = header[2]
        height = header[1]
    else:
        header = list(fixed_header)
        width = fixed_header[2]
        height = fixed_header[1]
    fit = min(
        width * fit_ratio / max(1, source.width),
        height * fit_ratio / max(1, source.height),
    )
    source = source.resize(
        (
            max(2, round(source.width * fit)),
            max(2, round(source.height * fit)),
        ),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(
        source,
        (
            (width - source.width) // 2,
            (height - source.height) // 2,
        ),
    )
    header[4] = 32
    return stock.rgba_to_indexed_tile(
        canvas,
        palettes,
        palette_index,
        tuple(header),
    )


def generated_registered_strip_tile(
    stock,
    palettes,
    source_png: Path,
    source_frame_count: int,
    frame_index: int,
    output_frame_count: int,
    palette_index: int,
    fixed_header: tuple[int, int, int, int, int, int, int, int],
    source_anchors: tuple[tuple[int, int], ...],
    fit_ratio: float = 0.94,
) -> bytes:
    """Interpolate phases around one fixed authored landmark and no wrap.

    The source art's changing flames and fragments make alpha-bound centering
    drift. Each phase is therefore registered on the center of its persistent
    alchemical ring before interpolation. The shared landmark is then placed
    at the exact center of every output TILE.
    """
    source_frames = keyed_strip_cells(source_png, source_frame_count)
    if len(source_anchors) != source_frame_count:
        raise ValueError("Registered strip must provide one anchor per source phase")
    boxes = [frame.getchannel("A").getbbox() for frame in source_frames]
    if any(box is None for box in boxes):
        raise ValueError("Registered strip contains a transparent source phase")
    left_extent = max(
        anchor[0] - box[0]
        for anchor, box in zip(source_anchors, boxes)
        if box is not None
    )
    top_extent = max(
        anchor[1] - box[1]
        for anchor, box in zip(source_anchors, boxes)
        if box is not None
    )
    right_extent = max(
        box[2] - anchor[0]
        for anchor, box in zip(source_anchors, boxes)
        if box is not None
    )
    bottom_extent = max(
        box[3] - anchor[1]
        for anchor, box in zip(source_anchors, boxes)
        if box is not None
    )
    registered_width = left_extent + right_extent
    registered_height = top_extent + bottom_extent
    registered: list[Image.Image] = []
    for frame, box, anchor in zip(source_frames, boxes, source_anchors):
        assert box is not None
        content = frame.crop(box)
        registered_frame = Image.new(
            "RGBA", (registered_width, registered_height), (0, 0, 0, 0)
        )
        registered_frame.alpha_composite(
            content,
            (
                left_extent + box[0] - anchor[0],
                top_extent + box[1] - anchor[1],
            ),
        )
        registered.append(registered_frame)

    progress = frame_index / max(1, output_frame_count - 1)
    position = progress * (source_frame_count - 1)
    source_index = min(source_frame_count - 1, math.floor(position))
    next_index = min(source_frame_count - 1, source_index + 1)
    blend = position - source_index
    source = Image.blend(registered[source_index], registered[next_index], blend)

    width = fixed_header[2]
    height = fixed_header[1]
    fit = min(
        width * fit_ratio / max(1, 2 * max(left_extent, right_extent)),
        height * fit_ratio / max(1, 2 * max(top_extent, bottom_extent)),
    )
    resized_width = max(2, round(source.width * fit))
    resized_height = max(2, round(source.height * fit))
    source = source.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
    scaled_anchor_x = left_extent * resized_width / registered_width
    scaled_anchor_y = top_extent * resized_height / registered_height
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(
        source,
        (
            round(width / 2 - scaled_anchor_x),
            round(height / 2 - scaled_anchor_y),
        ),
    )
    return stock.rgba_to_indexed_tile(
        canvas,
        palettes,
        palette_index,
        fixed_header,
    )


def generated_discrete_strip_tile(
    stock,
    palettes,
    source_png: Path,
    source_frame_count: int,
    source_frame_index: int,
    palette_index: int,
    fixed_header: tuple[int, int, int, int, int, int, int, int],
) -> bytes:
    """Render one exact approved strip cell without cross-frame ghosting."""
    source = keyed_strip_frames(source_png, source_frame_count)[source_frame_index]
    bbox = source.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"Approved strip frame {source_frame_index} is transparent")
    source = source.crop(bbox)
    width = fixed_header[2]
    height = fixed_header[1]
    fit = min(
        width * 0.94 / max(1, source.width),
        height * 0.94 / max(1, source.height),
    )
    source = source.resize(
        (
            max(2, round(source.width * fit)),
            max(2, round(source.height * fit)),
        ),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(
        source,
        ((width - source.width) // 2, (height - source.height) // 2),
    )
    return stock.rgba_to_indexed_tile(
        canvas,
        palettes,
        palette_index,
        fixed_header,
    )


def set_single_overlay_animation_delay(
    imag: bytes,
    expected_set_id: int,
    allowed_source_delays: tuple[int, ...],
    target_delay: int,
) -> bytes:
    """Change only one stock overlay set's native frame-delay field.

    XR30 stores its 50-ms delay at set+0x1c. A value of zero invokes Majesty's
    stock 100-ms default, slowing the same six-frame one-shot without a timer,
    duplicated frames, or a second effector.
    """
    if len(imag) < 64 or struct.unpack_from("<I", imag, 20)[0] != 1:
        raise ValueError("Expected one stock overlay animation set")
    set_id, set_offset = struct.unpack_from("<II", imag, 24)
    if set_id != expected_set_id or set_offset + 32 > len(imag):
        raise ValueError("Stock overlay animation-set layout changed")
    delay_offset = set_offset + 28
    source_delay = struct.unpack_from("<I", imag, delay_offset)[0]
    if source_delay not in allowed_source_delays:
        raise ValueError(
            f"Stock overlay delay {source_delay} is outside {allowed_source_delays}"
        )
    patched = bytearray(imag)
    struct.pack_into("<I", patched, delay_offset, target_delay)
    return bytes(patched)


def generated_frost_armor_hold_tile(
    stock,
    palettes,
    source_png: Path,
    palette_index: int,
    fixed_header: tuple[int, int, int, int, int, int, int, int],
    opening_frame_index: int | None,
    source_frame_count: int = 1,
    peak_frame_index: int = 0,
) -> bytes:
    """Clone Haunt Frost Armor: fixed roots, five-frame growth, then hold."""
    if source_frame_count == 1:
        with Image.open(source_png) as loaded:
            source = loaded.convert("RGBA")
        bbox = source.getchannel("A").getbbox()
        if bbox is None:
            raise ValueError(f"Frost Armor-style source has no visible art: {source_png}")
        source = source.crop(bbox)
    else:
        source = keyed_strip_frames(source_png, source_frame_count)[peak_frame_index]
        bbox = source.getchannel("A").getbbox()
        if bbox is None:
            raise ValueError(f"Frost Armor-style peak frame is transparent: {source_png}")
        source = source.crop(bbox)

    width = fixed_header[2]
    height = fixed_header[1]
    fit = min(
        width * 0.96 / max(1, source.width),
        height * 0.96 / max(1, source.height),
    )
    source = source.resize(
        (
            max(2, round(source.width * fit)),
            max(2, round(source.height * fit)),
        ),
        Image.Resampling.LANCZOS,
    )
    growth_scales = (0.22, 0.42, 0.68, 0.86, 1.0)
    if opening_frame_index is not None:
        scale = growth_scales[min(opening_frame_index, len(growth_scales) - 1)]
        if scale < 1.0:
            source = source.resize(
                (source.width, max(1, round(source.height * scale))),
                Image.Resampling.BICUBIC,
            )

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(
        source,
        ((width - source.width) // 2, height - source.height - 1),
    )
    return stock.rgba_to_indexed_tile(
        canvas,
        palettes,
        palette_index,
        fixed_header,
    )


def generated_phoenix_resurrection_tile(
    stock,
    template_tile: bytes,
    palettes,
    source_png: Path,
    frame_index: int,
    frame_count: int,
) -> bytes:
    """Render the approved Phoenix phases, then HRC1's private transparent tail."""
    from PIL import ImageEnhance

    height = struct.unpack_from("<H", template_tile, 2)[0]
    width = struct.unpack_from("<H", template_tile, 4)[0]
    with Image.open(source_png) as loaded:
        source = loaded.convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("Phoenix resurrection source has no visible alpha")
    source = source.crop(bbox)

    if frame_count != PHOENIX_LIFECYCLE_FRAMES:
        raise ValueError(
            f"Phoenix resurrection expected {PHOENIX_LIFECYCLE_FRAMES} visible "
            f"frames, found {frame_count}"
        )

    header = PHOENIX_EFFECT_HEADER
    if frame_index >= PHOENIX_VISIBLE_FRAMES:
        return stock.rgba_to_indexed_tile(
            Image.new("RGBA", (width, height), (0, 0, 0, 0)),
            palettes,
            PHOENIX_EFFECT_PALETTE,
            header,
        )

    # Literal copy of Phantoms Haunt's live-proven Eternal Soul cast phases.
    # It is sampled across the 15 live-approved visible slots; the source
    # master, private IDs, fiery palette, and phase sampling are the only art
    # substitutions.
    progress = frame_index / max(1, PHOENIX_VISIBLE_FRAMES - 1)
    if progress <= 0.60:
        growth = progress / 0.60
        smooth_growth = growth * growth * (3.0 - 2.0 * growth)
        scale = 0.18 + 0.82 * smooth_growth
        visible_alpha = 0.32 + 0.68 * growth
    elif progress <= 0.82:
        pulse = (progress - 0.60) / 0.22
        scale = 1.0 + 0.08 * math.sin(math.pi * pulse)
        visible_alpha = 1.0
    else:
        fade = (progress - 0.82) / 0.18
        scale = 1.03 - 0.15 * fade
        visible_alpha = max(0.06, 1.0 - 0.94 * fade)

    target_height = max(4, round(height * 0.74 * scale))
    target_width = max(
        3,
        round(source.width * target_height / max(1, source.height)),
    )
    if target_width > round(width * 0.94):
        target_width = max(3, round(width * 0.94))
        target_height = max(
            4,
            round(source.height * target_width / max(1, source.width)),
        )
    source = source.resize((target_width, target_height), Image.Resampling.LANCZOS)
    source = ImageEnhance.Brightness(source).enhance(0.48 + 0.50 * visible_alpha)
    alpha = source.getchannel("A").point(
        lambda value: round(value * visible_alpha)
    )
    source.putalpha(alpha)

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    left = (width - source.width) // 2
    top = height - source.height - 1
    canvas.alpha_composite(source, (left, top))
    return stock.rgba_to_indexed_tile(
        canvas,
        palettes,
        PHOENIX_EFFECT_PALETTE,
        header,
    )


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


def recipe_button_plate_frames(stock, tiles) -> dict[int, bytes]:
    """Fit APa1's complete gold plate into AP69's three 162x20 states.

    APa1's stock plate is 172x23, while AP69's three stacked spell plates are
    162x20. Pointing an AP69 control directly at APa1 tiles clips and repeats
    the state frame. Preserve each AP69 image-set and TILE header, but replace
    its four distinct state images with dimension-matched copies of APa1's
    corresponding stock states.
    """
    target_width, target_height = RECIPE_PRIVATE_PLATE_SIZE
    output: dict[int, bytes] = {}
    stock_plate_images = {
        source_index: tile_image(stock, tiles[source_index].data, [])
        for source_index in RECIPE_GOLD_PLATE_SOURCE_TILES
    }
    common_transparent_pixels = {
        (x, y)
        for y in range(stock_plate_images[RECIPE_GOLD_PLATE_SOURCE_TILES[0]].height)
        for x in range(stock_plate_images[RECIPE_GOLD_PLATE_SOURCE_TILES[0]].width)
        if all(
            stock_plate_images[source_index].getpixel((x, y))[3] == 0
            for source_index in RECIPE_GOLD_PLATE_SOURCE_TILES
        )
    }
    expected_common_transparency = {(0, 0), (0, 22), (171, 22)}
    disabled_transparency = {
        (x, y)
        for y in range(stock_plate_images[RECIPE_GOLD_PLATE_SOURCE_TILES[2]].height)
        for x in range(stock_plate_images[RECIPE_GOLD_PLATE_SOURCE_TILES[2]].width)
        if stock_plate_images[RECIPE_GOLD_PLATE_SOURCE_TILES[2]].getpixel((x, y))[3]
        == 0
    }
    if common_transparent_pixels != expected_common_transparency:
        raise ValueError("Stock recipe plate common transparency changed")
    if len(disabled_transparency - common_transparent_pixels) != 15:
        raise ValueError("Stock disabled recipe plate cutout count changed")
    for target_group in RECIPE_PRIVATE_PLATE_TILE_GROUPS:
        for target_index, source_index in zip(
            target_group, RECIPE_GOLD_PLATE_SOURCE_TILES
        ):
            source_tile = tiles[source_index].data
            source = stock_plate_images[source_index].copy()
            if source_index == RECIPE_GOLD_PLATE_SOURCE_TILES[2]:
                # APa1's disabled plate deliberately punches fifteen holes
                # through to a backing plate owned by that dialog. CGBR has no
                # such backing at these rows, so clone the stock composite as
                # well as the foreground state. Keep only the three pixels
                # that are transparent in every stock state. Embedded palette
                # index 1 is APa1's own neutral disabled fill and matches the
                # pixels surrounding each stock-only opening.
                source_colors = stock.tile_palette_colors(source_tile, [])
                if source_colors is None or len(source_colors) < 2:
                    raise ValueError("Stock disabled recipe plate palette changed")
                if source_colors[1] != (114, 114, 114):
                    raise ValueError("Stock disabled recipe plate fill color changed")
                disabled_fill = (*source_colors[1], 255)
                for y in range(source.height):
                    for x in range(source.width):
                        if (
                            source.getpixel((x, y))[3] == 0
                            and (x, y) not in common_transparent_pixels
                        ):
                            source.putpixel((x, y), disabled_fill)
            source = source.convert("RGB")
            fitted = source.resize(
                (target_width, target_height), Image.Resampling.NEAREST
            )
            template = bytearray(tiles[target_index].data)
            if struct.unpack_from("<H", template, 0)[0] != 3:
                raise ValueError("Stock AP69 recipe TILE is no longer indexed-v3")
            if (
                struct.unpack_from("<H", source_tile, 20)[0] != 1
                or struct.unpack_from("<H", template, 20)[0] != 1
            ):
                raise ValueError("Stock recipe plates no longer use embedded palettes")
            source_palette_offset = struct.unpack_from("<I", source_tile, 22)[0]
            target_palette_offset = struct.unpack_from("<I", template, 22)[0]
            if (
                source_palette_offset >= len(source_tile)
                or target_palette_offset >= len(template)
            ):
                raise ValueError("Stock recipe plate palette offset changed")
            # Preserve AP69's exact target TILE header and 162x20 geometry,
            # but use APa1's own embedded palette with APa1's gold frame art.
            # Quantizing through AP69's gray spell palette erased the border.
            template = bytearray(
                bytes(template[:target_palette_offset])
                + source_tile[source_palette_offset:]
            )
            encoded = stock.tile_v3_from_rgb(
                bytes(template), [], fitted.tobytes()
            )
            if struct.unpack_from("<3H", encoded, 2) != (
                target_height,
                target_width,
                target_width,
            ):
                raise ValueError("Private AP69 gold-plate TILE geometry changed")
            if source_index == RECIPE_GOLD_PLATE_SOURCE_TILES[2]:
                decoded = stock.decode_indexed_v3_tile(encoded)
                if decoded is None:
                    raise ValueError("Private disabled recipe plate is not valid V3")
                _height, _width, rows = decoded
                if any(
                    rows[y][x] == 0
                    for y in range(1, len(rows) - 1)
                    for x in range(1, len(rows[y]) - 1)
                ):
                    raise ValueError("Private disabled recipe plate retained stock holes")
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


def private_tactical_cursor_tile(
    stock,
    template_tile: bytes,
    icon_path: Path,
) -> bytes:
    """Center one approved 25x25 recipe icon on stock CUR1's 40x40 canvas."""
    header = struct.unpack_from("<8H", template_tile, 0)
    if header[0] != 3 or (header[2], header[1]) != (40, 40):
        raise ValueError("Expansion tactical cursor TILE 38 geometry changed")
    if sha256_bytes(template_tile) != TACTICAL_CURSOR_TEMPLATE_TILE_SHA256:
        raise ValueError("Expansion tactical cursor TILE 38 changed")
    with Image.open(icon_path) as loaded:
        icon = loaded.convert("RGBA")
    if icon.size != (25, 25):
        raise ValueError(f"Approved cursor icon is not 25x25: {icon_path}")
    left = (40 - 25) // 2
    top = (40 - 25) // 2

    # DataMX TILE 38 owns an embedded V3 cursor palette. A straight RGB remap
    # into Lightning Storm's embedded palette forces the approved copper and
    # green recipe colors into Lightning's limited blue/control entries. Keep
    # CUR1's exact V3/RLE/palette topology, but give the private cursor a
    # private embedded visible palette derived from its already-approved icon.
    # Indices 247..255 remain completely unused so Majesty never interprets an
    # ordinary icon pixel as a dynamic cursor/control color.
    quantized = icon.convert("RGB").quantize(
        colors=192,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    quantized_palette = quantized.getpalette()
    if quantized_palette is None:
        raise ValueError("Approved tactical cursor icon has no quantized palette")
    rows = [[0 for _x in range(40)] for _y in range(40)]
    for y in range(25):
        for x in range(25):
            rows[top + y][left + x] = int(quantized.getpixel((x, y))) + 1

    encoded = bytearray(
        stock.encode_indexed_v3_tile_like_original(template_tile, rows)
    )
    if struct.unpack_from("<H", encoded, 20)[0] != 1:
        raise ValueError("Private tactical cursor lost its embedded V3 palette")
    palette_offset = struct.unpack_from("<I", encoded, 22)[0]
    if encoded[palette_offset : palette_offset + 8] == b"\x00\x00\x00\x01\x00\x00\x00\x00":
        palette_offset += 8
    if palette_offset + 256 * 4 > len(encoded):
        raise ValueError("Private tactical cursor embedded palette is truncated")
    for palette_index in range(1, 193):
        source_offset = (palette_index - 1) * 3
        target_offset = palette_offset + palette_index * 4
        encoded[target_offset : target_offset + 3] = bytes(
            quantized_palette[source_offset : source_offset + 3]
        )
    return bytes(encoded)


def append_private_tactical_cursor_sets(
    imag: bytes,
    stone_cursor_tile: int,
) -> bytes:
    """Append Stone's private cursor presenter to the complete expansion CUR1."""
    if sha256_bytes(imag) != TACTICAL_CURSOR_SOURCE_SHA256:
        raise ValueError("Expansion CUR1 tactical cursor record changed")
    if stone_cursor_tile > 0xFFFF:
        raise ValueError("Private cursor TILE exceeds CUR1's low16 reference field")
    original_count = struct.unpack_from("<I", imag, 20)[0]
    original_table_start = 24
    original_table_end = original_table_start + original_count * 8
    if original_count != 34 or original_table_end != 0x128 or len(imag) != 8024:
        raise ValueError("Expansion CUR1 animation-set table changed")
    original_entries = [
        struct.unpack_from("<II", imag, original_table_start + index * 8)
        for index in range(original_count)
    ]
    source_offset = next(
        offset
        for set_id, offset in original_entries
        if set_id == TACTICAL_CURSOR_TEMPLATE_SET_ID
    )
    next_offset = min(
        offset for _set_id, offset in original_entries if offset > source_offset
    )
    source_body = imag[source_offset:next_offset]
    if source_offset != 0x5C0 or len(source_body) != 280:
        raise ValueError("Expansion CUR1 Lightning cursor body changed")
    # CUR1 set 1014 is a multi-stream presenter. The visible Lightning glyph
    # is repeated in all four directional/state streams while TILEs 41, 42,
    # and 47 remain separate cursor-state controls. Privatize every visible
    # glyph occurrence and nothing else.
    lightning_glyph_offsets = (0x7C, 0xAC, 0xE4, 0x10C)
    if any(
        (struct.unpack_from("<I", source_body, offset)[0] & 0xFFFF) != 38
        for offset in lightning_glyph_offsets
    ):
        raise ValueError("Expansion CUR1 Lightning cursor TILE references changed")

    table_growth = 8
    private_offset = len(imag) + table_growth
    output = bytearray(imag[:20])
    output += struct.pack("<I", original_count + 1)
    for set_id, offset in original_entries:
        output += struct.pack("<II", set_id, offset + table_growth)
    output += struct.pack(
        "<II",
        PHILOSOPHERS_STONE_CURSOR_SET_ID,
        private_offset,
    )
    output += imag[original_table_end:]
    clone = bytearray(source_body)
    for offset in lightning_glyph_offsets:
        original_ref = struct.unpack_from("<I", clone, offset)[0]
        struct.pack_into(
            "<I", clone, offset, (original_ref & 0xFFFF0000) | stone_cursor_tile
        )
    output += clone
    if len(output) != 8312:
        raise ValueError("Private CUR1 output length changed")
    return bytes(output)


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


def interface_imag_set_tiles(imag: bytes, wanted_set: int) -> list[int]:
    """Return the literal TILE order owned by one stock interface image-set."""
    set_count = int.from_bytes(imag[20:24], "little")
    matches: list[int] = []
    for set_index in range(set_count):
        table_offset = 24 + set_index * 8
        set_id = int.from_bytes(imag[table_offset : table_offset + 4], "little")
        if set_id != wanted_set:
            continue
        set_offset = int.from_bytes(
            imag[table_offset + 4 : table_offset + 8], "little"
        )
        direction_count = int.from_bytes(imag[set_offset : set_offset + 4], "little")
        for direction in range(direction_count):
            relative_offset = int.from_bytes(
                imag[
                    set_offset + 64 + direction * 4 :
                    set_offset + 68 + direction * 4
                ],
                "little",
                signed=True,
            )
            direction_offset = set_offset + relative_offset + 4
            frame_count = int.from_bytes(
                imag[direction_offset : direction_offset + 4], "little"
            ) >> 16
            for frame in range(frame_count):
                tile_offset = direction_offset + 24 + frame * 8
                tile_index = int.from_bytes(
                    imag[tile_offset : tile_offset + 4], "little"
                ) & 0xFFFF
                if tile_index not in matches:
                    matches.append(tile_index)
    if not matches:
        raise ValueError(f"Stock INTN image-set {wanted_set:#x} has no TILEs")
    return matches


def brewing_recipe_icon_overrides(
    stock,
    tiles,
    navigation_imag: bytes,
    icon_specs: tuple[tuple[int, Path, str], ...],
    output_dir: Path,
) -> dict[int, bytes]:
    """Privatize two literal AP69 icon-state families with approved art."""
    from PIL import ImageEnhance, ImageOps

    output: dict[int, bytes] = {}
    # Weapon Oil and Phoenix Phial keep their colored icons while unavailable.
    # Apply that same proven Brewing presentation to all eight literal AP69
    # icon states; availability remains communicated by the stock row plate.
    state_styles = ((1.00, 1.00),) * 8
    for image_set, icon_path, slug in icon_specs:
        source = Image.open(icon_path).convert("RGB")
        set_tiles = interface_imag_set_tiles(navigation_imag, image_set)
        for state_index, tile_index in enumerate(set_tiles):
            template = tiles[tile_index].data
            dimensions = stock.tile_dimensions(template)
            if dimensions is None:
                raise ValueError(
                    f"Stock INTN {image_set:#x} TILE {tile_index} has no dimensions"
                )
            height, width = dimensions
            frame = source.resize((width, height), Image.Resampling.LANCZOS)
            if len(set_tiles) != len(state_styles):
                raise ValueError(
                    f"Stock INTN {image_set:#x} state count changed: "
                    f"{len(set_tiles)}"
                )
            brightness, saturation = state_styles[state_index]
            if saturation < 1.0:
                grey = ImageOps.grayscale(frame).convert("RGB")
                frame = Image.blend(grey, frame, saturation)
            if brightness != 1.0:
                frame = ImageEnhance.Brightness(frame).enhance(brightness)
            path = output_dir / f"{slug}-icon-state-{tile_index}.png"
            frame.save(path)
            if struct.unpack_from("<H", template, 0)[0] == 1:
                output[tile_index] = stock.tile_v1_embedded_from_rgb(
                    template, frame.tobytes()
                )
            else:
                output[tile_index] = stock.tile_from_rgb(
                    template, [], frame.tobytes()
                )
    return output


def brewing_dialog_frame(
    stock, tiles, panel_path: Path, output_path: Path
) -> Path:
    """Put the approved Brewing backing behind AP69's exact stock controls.

    AP69's dialog TILE already paints three complete spell-row frames.  CGBR
    supplies five real compound controls of its own, so retaining those baked
    rows draws a second border beneath Oil, Phoenix, and Vigor.  Keep only the
    outer frame and stock navigation area here; the literal indexed title is
    restored after RGB composition by ``brewing_dialog_tile``.
    """
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
            # The five live row controls own their complete button frames.
            # Preserve only AP69's outer edge and Back/Next area in this RGB
            # composition pass.
            preserve = (
                y >= 222
                or x < 6
                or x >= stock_frame.width - 6
            )
            if preserve and pixel[3]:
                target[x, y] = pixel
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
                y >= 54
                and
                alpha
                and red > 70
                and blue > 65
                and red + blue > green * 2.15
            ):
                result_pixels[x, y] = panel_pixels[x, y]
    result.save(output_path)
    return output_path


def brewing_dialog_tile(stock, template: bytes, dialog_path: Path) -> bytes:
    """Restore AP69's visible title ornament over the private Brewing backing.

    The stock title capsule in TILE 594 uses indexed UI/control colors
    248..254.  Passing those pixels through RGBA and quantizing them back into
    the TILE collapses their distinct control roles. Copying them into CGBR
    literally exposes their magenta key colors, while converting them to
    ordinary colors paints an opaque brown capsule. Compose the private
    backing normally, then copy AP69's ordinary visible pixels through its
    complete 57-row header literally and
    let its reserved control pixels fall through to the approved private
    backing. This retains the exact stock gold ornament without importing
    AP69's palette-control background.
    """
    composed = stock.tile_from_png_native_size(template, [], dialog_path)
    stock_decoded = stock.decode_indexed_v3_tile(template)
    private_decoded = stock.decode_indexed_v3_tile(composed)
    if stock_decoded is None or private_decoded is None:
        raise ValueError("Brewing dialog TILE is no longer indexed-v3")
    stock_height, stock_width, stock_rows = stock_decoded
    private_height, private_width, private_rows = private_decoded
    if (
        (stock_height, stock_width) != (private_height, private_width)
        or stock_height < 57
    ):
        raise ValueError("Brewing dialog TILE geometry changed")
    combined_rows = [list(row) for row in private_rows]
    for y in range(57):
        for x, stock_index in enumerate(stock_rows[y]):
            if stock_index < 247:
                combined_rows[y][x] = stock_index
    return stock.encode_indexed_v3_tile_like_original(template, combined_rows)


def write_maindata(
    repo: Path,
    game_data: Path,
    art_dir: Path,
    output: Path,
    approved_sprite_test_root: Path | None = None,
) -> dict | None:
    stock = load_stock_pipeline(repo)
    source = game_data / "maindata.cam"
    tiles = stock.read_cam_entries(source, b"TILE")
    palettes = stock.read_cam_entries(source, b"SPLT")
    hero_imag = stock.read_cam_entry(source, b"IMAG", HERO_SOURCE).data
    approved_building_bundle = load_approved_building_bundle(
        repo / APPROVED_BUILDING_ROOT,
        stock,
        source,
        tiles,
        palettes,
    )
    building_imags = list(approved_building_bundle.source_imags)
    phoenix_item_imag = stock.read_cam_entry(
        source, b"IMAG", INVENTORY_ITEM_SOURCE
    ).data
    phoenix_lifecycle_imag = stock.read_cam_entry(
        source, b"IMAG", PHOENIX_LIFECYCLE_SOURCE
    ).data
    # Eternal Soul and Chill established XR25 as the stock animated overhead
    # buff-icon scaffold and XR30 as the duration-0 self-cast scaffold. Keep
    # both stock tables literal and privatize only their image IDs and TILE art.
    mx_source = game_data.parent / "DataMX" / "mx_maindata.cam"
    if not mx_source.is_file():
        raise FileNotFoundError(f"Stock Northern Expansion maindata is missing: {mx_source}")
    mx_tiles = stock.read_cam_entries(mx_source, b"TILE")
    mx_palettes = stock.read_cam_entries(mx_source, b"SPLT")
    phoenix_effect_template_imag = stock.read_cam_entry(
        mx_source, b"IMAG", PHOENIX_EFFECT_TEMPLATE_SOURCE
    ).data
    buff_icon_template_imag = stock.read_cam_entry(
        mx_source, b"IMAG", BUFF_ICON_TEMPLATE_SOURCE
    ).data
    vigor_effect_imag = buff_icon_template_imag
    flash_flask_buff_imag = buff_icon_template_imag
    flash_flask_activation_imag = phoenix_effect_template_imag
    stun_serum_impact_imag = phoenix_effect_template_imag
    philosophers_stone_hit_imag = stock.read_cam_entry(
        source, b"IMAG", PHOENIX_LIFECYCLE_SOURCE
    ).data
    arcane_infusion_effect_imag = stock.read_cam_entry(
        source, b"IMAG", PHOENIX_LIFECYCLE_SOURCE
    ).data
    vigor_activation_effect_imag = stock.read_cam_entry(
        source, b"IMAG", PHOENIX_LIFECYCLE_SOURCE
    ).data
    stun_serum_restraint_imag = stock.read_cam_entry(
        source, b"IMAG", b"CRB1vines_e"
    ).data
    stun_serum_debuff_imag = stock.read_cam_entry(
        source, b"IMAG", b"QRc1poison_IC"
    ).data
    paralytic_oil_restraint_imag = stock.read_cam_entry(
        source, b"IMAG", b"CRB1vines_e"
    ).data
    miasma_storm_source_imag = stock.read_cam_entry(
        source, b"IMAG", MIASMA_STORM_SOURCE
    ).data
    miasma_anchor_imag = stock.replace_embedded_attachment_id(
        miasma_storm_source_imag,
        b"XL20",
        b"\x00\x00\x00\x00",
    )
    miasma_storm_imag = stock.replace_embedded_attachment_id(
        miasma_storm_source_imag,
        b"XL20",
        b"AMM4",
    )
    miasma_missile_imag = stock.read_cam_entry(
        source, b"IMAG", MIASMA_MISSILE_SOURCE
    ).data
    miasma_missile_imag = stock.replace_embedded_attachment_id(
        miasma_missile_imag,
        b"XL21",
        b"\x00\x00\x00\x00",
    )
    miasma_particle_imag = stock.read_cam_entry(
        source, b"IMAG", MIASMA_PARTICLE_SOURCE
    ).data
    miasma_debuff_imag = buff_icon_template_imag
    reagent_ready_imag = stock.read_cam_entry(
        source, b"IMAG", REAGENT_READY_SOURCE
    ).data
    if sha256_bytes(reagent_ready_imag) != REAGENT_READY_SOURCE_SHA256:
        raise ValueError("Stock Wizard Tower enchantment IMAG changed")

    approved_bundle = (
        load_approved_sprite_bundle(
            approved_sprite_test_root,
            stock,
            source,
            tiles,
            palettes,
            hero_imag,
        )
        if approved_sprite_test_root is not None
        else None
    )

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

    hero_dir = art_dir / "hero"
    approved_private_tile_indices: dict[int, int] = {}
    approved_interface_tile_indices: dict[int, int] = {}
    approved_interface_records: list[dict] = []
    if approved_bundle is not None:
        if approved_bundle.handoff_manifest_sha256 is not None:
            # Clone the complete Warrior action topology. Each approved art
            # record is appended privately, then only its manifest-authorized
            # low16 occurrence words are changed. Cast/Special occurrences are
            # intentionally disjoint even where retail Warrior aliases TILEs.
            for record in approved_bundle.records:
                record_index = record["record_index"]
                approved_private_tile_indices[record_index] = append(
                    (
                        f"ALC1{record['kind'][:3].title()}"
                        f"{record_index:03d}"
                    ).encode("ascii"),
                    record["packaged_tile"],
                )
            hero_imag = patch_completed_warrior_imag(
                hero_imag,
                approved_bundle,
                list(approved_private_tile_indices.values()),
            )
        else:
            for source_index, rendered in sorted(
                approved_bundle.tiles_by_stock_slot.items()
            ):
                approved_private_tile_indices[source_index] = append(
                    f"ALC1Test{source_index:05d}".encode("ascii"), rendered
                )
            hero_imag = remap_approved_warrior_imag(
                stock, hero_imag, approved_private_tile_indices
            )
    else:
        hero_replacements: dict[int, int] = {}
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
        walk_body_areas: dict[int, list[int]] = {
            direction: [] for direction in range(8)
        }
        for start, end in HERO_SPRITE_RANGES:
            for source_index in range(start, end):
                path = hero_dir / f"hero_tile_{source_index:05d}.png"
                if not path.exists():
                    raise FileNotFoundError(path)
                rendered = stock.tile_from_png_source(
                    stock.remap_tile_palette_index(
                        tiles[source_index].data, HERO_ART_PALETTE
                    ),
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
                stock.remap_tile_palette_index(
                    tiles[HERO_PORTRAIT_TILE].data, BUILDING_PALETTE
                ),
                palettes,
                image_rgb(repo / "assets/source/hero/portrait.png", (100, 100)),
            ),
        )
        hero_replacements[HERO_ICON_TILE] = append(
            b"ALC1HeroIcon",
            stock.tile_from_rgb(
                stock.remap_tile_palette_index(
                    tiles[HERO_ICON_TILE].data, BUILDING_PALETTE
                ),
                palettes,
                image_rgb(art_dir / "interface/hero-icon-25.png", (25, 25)),
            ),
        )
        hero_replacements[HERO_PANEL_TILE] = append(
            b"ALC1HeroPanel",
            stock.tile_from_rgb(
                stock.remap_tile_palette_index(
                    tiles[HERO_PANEL_TILE].data, HERO_ART_PALETTE
                ),
                palettes,
                image_rgb(
                    art_dir / "interface/building-panel-200x245.png", (200, 245)
                ),
            ),
        )
        hero_imag = stock.remap_imag_low16_tile_indices(
            hero_imag, hero_replacements
        )

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

    # Agrela's private 1500-ms callback owner keeps the complete HRC1 table.
    # Every playable slot receives a private Phoenix TILE so the phased art,
    # Resurrection sound, and callback all share one stock-owned lifetime.
    phoenix_lifecycle_sets = stock.single_direction_imag_animation_sets(
        phoenix_lifecycle_imag
    )
    if (
        len(phoenix_lifecycle_sets) != 1
        or phoenix_lifecycle_sets[0][0] != PHOENIX_LIFECYCLE_ANIMATION_SET
    ):
        raise ValueError("Stock HRC1 resurrection animation set changed")
    phoenix_lifecycle_indices = stock.animation_tile_indices(
        phoenix_lifecycle_imag,
        len(tiles),
    )
    if len(phoenix_lifecycle_indices) != PHOENIX_LIFECYCLE_FRAMES:
        raise ValueError("Stock HRC1 resurrection frame contract changed")

    # Eternal Soul's XR30/PHe2 scaffold supplies its proven fixed canvas and
    # hotspot. The apparent zero at offset 120 is attachment data; the six
    # template TILEs occupy offsets 128 through 168.
    phoenix_template_sets = stock.single_direction_imag_animation_sets(
        phoenix_effect_template_imag
    )
    if (
        len(phoenix_template_sets) != 1
        or phoenix_template_sets[0][0] != PHOENIX_EFFECT_TEMPLATE_ANIMATION_SET
    ):
        raise ValueError("Stock XR30 Eternal Soul visual set changed")
    phoenix_template_indices = stock.animation_tile_indices(
        phoenix_effect_template_imag,
        len(mx_tiles),
    )
    if len(phoenix_template_indices) != PHOENIX_EFFECT_TEMPLATE_FRAMES:
        raise ValueError("Stock XR30 Eternal Soul visual frames changed")
    if PHOENIX_EFFECT_PALETTE >= len(palettes):
        raise ValueError("Stock fireball palette 505 is missing")
    phoenix_effect_source_png = (
        repo
        / "assets"
        / "source"
        / "spells"
        / "phoenix-phial"
        / "flaming-phoenix-source.png"
    )
    if not phoenix_effect_source_png.is_file():
        raise FileNotFoundError(phoenix_effect_source_png)
    phoenix_effect_template_tile = mx_tiles[phoenix_template_indices[-1]].data
    phoenix_lifecycle_replacements: dict[int, int] = {}
    for frame_index, source_index in enumerate(phoenix_lifecycle_indices):
        phoenix_lifecycle_replacements[source_index] = append(
            f"PXE1Phoenix{frame_index:02d}".encode("ascii"),
            generated_phoenix_resurrection_tile(
                stock,
                phoenix_effect_template_tile,
                palettes,
                phoenix_effect_source_png,
                frame_index,
                len(phoenix_lifecycle_indices),
            ),
        )
    phoenix_lifecycle_imag = stock.remap_imag_animation_tiles(
        phoenix_lifecycle_imag,
        phoenix_lifecycle_replacements,
    )

    buff_template_indices = stock.animation_tile_indices(
        buff_icon_template_imag, len(mx_tiles)
    )
    if len(buff_template_indices) != 29:
        raise ValueError("Stock XR25 animated buff-icon contract changed")
    vigor_source_png = repo / "assets/source/effects/vigor/heroic-spark-strip.png"
    flash_buff_source_png = repo / "assets/source/spells/flash-flask/buff-strip.png"
    flash_activation_source_png = (
        repo / "assets/source/spells/flash-flask/activation-strip.png"
    )
    stun_impact_source_png = repo / "assets/source/spells/stun-serum/impact-strip.png"
    stun_restraint_source_png = (
        repo / "assets/source/spells/stun-serum/restraint-strip.png"
    )
    stun_debuff_source_png = repo / "assets/source/spells/stun-serum/debuff-strip.png"
    paralytic_oil_restraint_source_png = (
        repo / "assets/source/effects/paralytic-oil/approved-restraint-master.png"
    )
    miasma_cloud_source_png = (
        repo / "assets/source/spells/miasma-mist/cloud-mist-sheet.png"
    )
    miasma_debuff_source_png = (
        repo / "assets/source/spells/miasma-mist/debuff-strip.png"
    )
    philosophers_stone_hit_source_png = (
        repo
        / "assets/source/spells/philosophers-stone/transmutation-impact-sheet.png"
    )
    arcane_infusion_effect_source_png = (
        repo
        / "assets/source/spells/arcane-infusion/laboratory-enchantment-sheet.png"
    )
    vigor_activation_effect_source_png = (
        repo / "assets/source/spells/vigor-elixir/laboratory-vigor-sheet.png"
    )
    reagent_ready_source_png = (
        repo
        / "assets/source/effects/reagent-ready/alchemist-reagent-ready-source.png"
    )
    for source_png in (
        vigor_source_png,
        flash_buff_source_png,
        flash_activation_source_png,
        stun_impact_source_png,
        stun_restraint_source_png,
        stun_debuff_source_png,
        paralytic_oil_restraint_source_png,
        miasma_cloud_source_png,
        miasma_debuff_source_png,
        philosophers_stone_hit_source_png,
        arcane_infusion_effect_source_png,
        vigor_activation_effect_source_png,
        reagent_ready_source_png,
    ):
        if not source_png.is_file():
            raise FileNotFoundError(source_png)

    vigor_effect_replacements: dict[int, int] = {}
    flash_buff_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(buff_template_indices):
        template_tile = mx_tiles[source_index].data
        vigor_effect_replacements[source_index] = append(
            f"ALV1Spark{frame:02d}".encode("ascii"),
            generated_approved_strip_tile(
                stock,
                template_tile,
                palettes,
                vigor_source_png,
                8,
                frame,
                len(buff_template_indices),
                BUFF_ICON_PALETTE,
                fit_ratio=OVERHEAD_EFFECT_FIT_RATIO,
            ),
        )
        flash_buff_replacements[source_index] = append(
            f"AFF1Flask{frame:02d}".encode("ascii"),
            generated_approved_strip_tile(
                stock,
                template_tile,
                palettes,
                flash_buff_source_png,
                8,
                frame,
                len(buff_template_indices),
                BUFF_ICON_PALETTE,
                fit_ratio=OVERHEAD_EFFECT_FIT_RATIO,
            ),
        )
    vigor_effect_imag = stock.remap_imag_animation_tiles(
        vigor_effect_imag, vigor_effect_replacements
    )
    flash_flask_buff_imag = stock.remap_imag_animation_tiles(
        flash_flask_buff_imag, flash_buff_replacements
    )

    flash_activation_indices = stock.animation_tile_indices(
        flash_flask_activation_imag, len(mx_tiles)
    )
    if len(flash_activation_indices) != 6:
        raise ValueError("Stock XR30 self-cast activation contract changed")
    flash_activation_template = mx_tiles[flash_activation_indices[-1]].data
    flash_activation_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(flash_activation_indices):
        flash_activation_replacements[source_index] = append(
            f"AFF2Flash{frame:02d}".encode("ascii"),
            generated_approved_strip_tile(
                stock,
                flash_activation_template,
                palettes,
                flash_activation_source_png,
                6,
                frame,
                len(flash_activation_indices),
                FLASH_FLASK_ACTIVATION_PALETTE,
                FLASH_FLASK_ACTIVATION_HEADER,
            ),
        )
    flash_flask_activation_imag = stock.remap_imag_animation_tiles(
        flash_flask_activation_imag,
        flash_activation_replacements,
    )
    flash_flask_activation_imag = set_single_overlay_animation_delay(
        flash_flask_activation_imag,
        PHOENIX_EFFECT_TEMPLATE_ANIMATION_SET,
        (FLASH_FLASK_ACTIVATION_SOURCE_DELAY_MS,),
        FLASH_FLASK_ACTIVATION_DELAY_MS,
    )

    # Stun Serum's instantaneous bottle impact uses the same six-frame,
    # attachment-point-2 stock scaffold proven by Eternal Soul and Flash Flask.
    stun_impact_indices = stock.animation_tile_indices(
        stun_serum_impact_imag, len(mx_tiles)
    )
    if len(stun_impact_indices) != 6:
        raise ValueError("Stock XR30 Stun Serum impact scaffold changed")
    stun_impact_replacements: dict[int, int] = {}
    stun_impact_phase_indices = (0, 1, 2, 3, 5, 7)
    for frame, source_index in enumerate(stun_impact_indices):
        stun_impact_replacements[source_index] = append(
            f"ASS1Impact{frame:02d}".encode("ascii"),
            generated_discrete_strip_tile(
                stock,
                palettes,
                stun_impact_source_png,
                8,
                stun_impact_phase_indices[frame],
                FLASH_FLASK_ACTIVATION_PALETTE,
                FLASH_FLASK_ACTIVATION_HEADER,
            ),
        )
    stun_serum_impact_imag = stock.remap_imag_animation_tiles(
        stun_serum_impact_imag, stun_impact_replacements
    )

    # Philosopher's Stone uses Agrela resurrection's complete 29-frame
    # one-shot topology. Its stock default 100-ms cadence gives the approved
    # six-phase transmutation enough time to read, while one fixed, centered
    # private canvas makes the result roughly twice the old XR30 footprint.
    philosophers_stone_hit_indices = stock.animation_tile_indices(
        philosophers_stone_hit_imag, len(tiles)
    )
    if len(philosophers_stone_hit_indices) != PHILOSOPHERS_STONE_FRAMES:
        raise ValueError("Stock HRC1 Philosopher's Stone scaffold changed")
    philosophers_stone_hit_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(philosophers_stone_hit_indices):
        template_tile = tiles[source_index].data
        philosophers_stone_hit_replacements[source_index] = append(
            f"AST1StoneHit{frame:02d}".encode("ascii"),
            generated_approved_strip_tile(
                stock,
                template_tile,
                palettes,
                philosophers_stone_hit_source_png,
                6,
                frame,
                len(philosophers_stone_hit_indices),
                PHOENIX_EFFECT_PALETTE,
                fixed_header=PHILOSOPHERS_STONE_HEADER,
                fit_ratio=0.94,
            ),
        )
    philosophers_stone_hit_imag = stock.remap_imag_animation_tiles(
        philosophers_stone_hit_imag,
        philosophers_stone_hit_replacements,
    )
    philosophers_stone_hit_imag = set_single_overlay_animation_delay(
        philosophers_stone_hit_imag,
        PHILOSOPHERS_STONE_ANIMATION_SET,
        (0,),
        PHILOSOPHERS_STONE_DELAY_MS,
    )

    # Arcane Infusion clones Stone's proven HRC1 one-shot topology and default
    # 100-ms cadence. Only the private purple ritual artwork and Laboratory-
    # sized canvas differ; no timer, callback, or persistent effect is added.
    arcane_infusion_effect_indices = stock.animation_tile_indices(
        arcane_infusion_effect_imag, len(tiles)
    )
    if len(arcane_infusion_effect_indices) != ARCANE_INFUSION_FRAMES:
        raise ValueError("Stock HRC1 Arcane Infusion scaffold changed")
    arcane_infusion_effect_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(arcane_infusion_effect_indices):
        arcane_infusion_effect_replacements[source_index] = append(
            f"AIF1Infuse{frame:02d}".encode("ascii"),
            generated_registered_strip_tile(
                stock,
                palettes,
                arcane_infusion_effect_source_png,
                6,
                frame,
                len(arcane_infusion_effect_indices),
                ARCANE_INFUSION_PALETTE,
                fixed_header=ARCANE_INFUSION_HEADER,
                source_anchors=ARCANE_INFUSION_SOURCE_ANCHORS,
                fit_ratio=0.96,
            ),
        )
    arcane_infusion_effect_imag = stock.remap_imag_animation_tiles(
        arcane_infusion_effect_imag,
        arcane_infusion_effect_replacements,
    )
    arcane_infusion_effect_imag = set_single_overlay_animation_delay(
        arcane_infusion_effect_imag,
        ARCANE_INFUSION_ANIMATION_SET,
        (0,),
        ARCANE_INFUSION_DELAY_MS,
    )

    # Vigor uses the same stock building-owned one-shot topology and the same
    # fixed registration path as Arcane Infusion. Its distinct green/gold
    # ritual communicates the successful brew before Rage's hero effects run.
    vigor_activation_effect_indices = stock.animation_tile_indices(
        vigor_activation_effect_imag, len(tiles)
    )
    if len(vigor_activation_effect_indices) != VIGOR_ACTIVATION_FRAMES:
        raise ValueError("Stock HRC1 Vigor activation scaffold changed")
    vigor_activation_effect_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(vigor_activation_effect_indices):
        vigor_activation_effect_replacements[source_index] = append(
            f"AIV1Vigor{frame:02d}".encode("ascii"),
            generated_registered_strip_tile(
                stock,
                palettes,
                vigor_activation_effect_source_png,
                6,
                frame,
                len(vigor_activation_effect_indices),
                VIGOR_ACTIVATION_PALETTE,
                fixed_header=VIGOR_ACTIVATION_HEADER,
                source_anchors=VIGOR_ACTIVATION_SOURCE_ANCHORS,
                fit_ratio=0.96,
            ),
        )
    vigor_activation_effect_imag = stock.remap_imag_animation_tiles(
        vigor_activation_effect_imag,
        vigor_activation_effect_replacements,
    )
    vigor_activation_effect_imag = set_single_overlay_animation_delay(
        vigor_activation_effect_imag,
        VIGOR_ACTIVATION_ANIMATION_SET,
        (0,),
        VIGOR_ACTIVATION_DELAY_MS,
    )

    # CRB1 is Vines' literal 30-TILE restraint presentation. Preserve its
    # table/ordering and privatize only those named Vines TILEs.
    stun_restraint_source_indices = tuple(range(2578, 2608))
    stun_restraint_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(stun_restraint_source_indices):
        opening_frame = frame if source_index <= 2594 else None
        stun_restraint_replacements[source_index] = append(
            f"ASS2Bind{frame:02d}".encode("ascii"),
            generated_frost_armor_hold_tile(
                stock,
                palettes,
                stun_restraint_source_png,
                FLASH_FLASK_ACTIVATION_PALETTE,
                VINES_FIXED_HEADER,
                opening_frame,
                source_frame_count=8,
                peak_frame_index=4,
            ),
        )
    stun_serum_restraint_imag = stock.remap_imag_low16_tile_indices(
        stun_serum_restraint_imag, stun_restraint_replacements
    )

    # Paralytic Oil uses Vines' exact callback-owned 30-frame restraint
    # presentation, but owns a completely private alchemical cage channel.
    # It deliberately does not borrow Stun Serum's bottle impact or overhead
    # debuff icon.
    paralytic_oil_restraint_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(stun_restraint_source_indices):
        opening_frame = frame if source_index <= 2594 else None
        paralytic_oil_restraint_replacements[source_index] = append(
            f"ASO3Bind{frame:02d}".encode("ascii"),
            generated_frost_armor_hold_tile(
                stock,
                palettes,
                paralytic_oil_restraint_source_png,
                FLASH_FLASK_ACTIVATION_PALETTE,
                VINES_FIXED_HEADER,
                opening_frame,
            ),
        )
    paralytic_oil_restraint_imag = stock.remap_imag_low16_tile_indices(
        paralytic_oil_restraint_imag,
        paralytic_oil_restraint_replacements,
    )

    # QRc1 is stock Poison's animated overhead-status scaffold (eight TILE
    # records). It supplies the requested debuff-icon placement and cadence.
    stun_debuff_source_indices = tuple(range(17020, 17028))
    stun_debuff_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(stun_debuff_source_indices):
        stun_debuff_replacements[source_index] = append(
            f"ASS3Icon{frame:02d}".encode("ascii"),
            generated_approved_strip_tile(
                stock,
                tiles[source_index].data,
                palettes,
                stun_debuff_source_png,
                8,
                frame,
                len(stun_debuff_source_indices),
                BUFF_ICON_PALETTE,
            ),
        )
    stun_serum_debuff_imag = stock.remap_imag_low16_tile_indices(
        stun_serum_debuff_imag, stun_debuff_replacements
    )

    # Miasma Mist is a literal private Meteor Storm/Endless Winter art
    # composition: a visible storm IMAG with its private stock particle
    # attachment, a transparent tracking anchor, an invisible fast missile,
    # and a private XR25/Poison-style animated debuff icon.
    # Meteor Storm is a three-direction IMAG, not the single-direction XR30
    # topology. Endless Winter reads every real high-index reference and
    # remaps all occurrences; preserve that exact proven path here.
    miasma_storm_indices = sorted(
        index
        for index in stock.referenced_tile_indices(
            miasma_storm_source_imag, len(tiles)
        )
        if index >= 8000
    )
    if not miasma_storm_indices:
        raise ValueError("Stock Meteor Storm image has no playable TILEs")
    miasma_storm_template = max(
        (tiles[index].data for index in miasma_storm_indices),
        key=lambda tile: (
            struct.unpack_from("<H", tile, 2)[0]
            * struct.unpack_from("<H", tile, 4)[0]
        ),
    )
    miasma_storm_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(miasma_storm_indices):
        miasma_storm_replacements[source_index] = append(
            f"AMm1Cloud{frame:02d}".encode("ascii"),
            generated_area_effect_tile(
                stock,
                miasma_storm_template,
                palettes,
                miasma_cloud_source_png,
                frame,
                len(miasma_storm_indices),
                0.96,
                MIASMA_CLOUD_BRIGHTNESS,
                MIASMA_CLOUD_SATURATION,
                MIASMA_CLOUD_PALETTE,
            ),
        )
    miasma_storm_imag = stock.remap_imag_tile_indices(
        miasma_storm_imag,
        miasma_storm_replacements,
    )

    miasma_anchor_blank = append(
        b"AMm6Anchor00",
        stock.blank_indexed_v3_tile(miasma_storm_template),
    )
    miasma_anchor_imag = stock.remap_imag_tile_indices(
        miasma_anchor_imag,
        {index: miasma_anchor_blank for index in miasma_storm_indices},
    )

    miasma_missile_indices = stock.animation_tile_indices(
        miasma_missile_imag, len(tiles)
    )
    if not miasma_missile_indices:
        raise ValueError("Stock Meteor Storm missile has no playable TILEs")
    miasma_missile_template = max(
        (tiles[index].data for index in miasma_missile_indices),
        key=lambda tile: (
            struct.unpack_from("<H", tile, 2)[0]
            * struct.unpack_from("<H", tile, 4)[0]
        ),
    )
    miasma_missile_blank = append(
        b"AMm2Missile00",
        stock.blank_indexed_v3_tile(miasma_missile_template),
    )
    miasma_missile_imag = stock.remap_imag_tile_indices(
        miasma_missile_imag,
        {index: miasma_missile_blank for index in miasma_missile_indices},
    )

    miasma_particle_indices = stock.animation_tile_indices(
        miasma_particle_imag, len(tiles)
    )
    if not miasma_particle_indices:
        raise ValueError("Stock Meteor Storm particle image has no playable TILEs")
    miasma_particle_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(miasma_particle_indices):
        miasma_particle_replacements[source_index] = append(
            f"AMm4Vapor{frame:02d}".encode("ascii"),
            generated_miasma_particle_tile(
                stock,
                tiles[source_index].data,
                palettes,
                miasma_cloud_source_png,
                frame,
                len(miasma_particle_indices),
                MIASMA_CLOUD_PALETTE,
                MIASMA_PARTICLE_BRIGHTNESS,
                MIASMA_PARTICLE_SATURATION,
                MIASMA_PARTICLE_ALPHA_SCALE,
            ),
        )
    miasma_particle_imag = stock.remap_imag_animation_tiles(
        miasma_particle_imag,
        miasma_particle_replacements,
    )

    miasma_debuff_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(buff_template_indices):
        miasma_debuff_replacements[source_index] = append(
            f"AMm5Drop{frame:02d}".encode("ascii"),
            generated_approved_strip_tile(
                stock,
                mx_tiles[source_index].data,
                palettes,
                miasma_debuff_source_png,
                8,
                frame,
                len(buff_template_indices),
                MIASMA_DEBUFF_PALETTE,
                fit_ratio=OVERHEAD_EFFECT_FIT_RATIO,
            ),
        )
    miasma_debuff_imag = stock.remap_imag_animation_tiles(
        miasma_debuff_imag,
        miasma_debuff_replacements,
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

    approved_building_records: list[dict] = []
    approved_building_private_indices: list[dict[int, int]] = []
    reagent_ready_template: bytes | None = None
    for level in (1, 2, 3):
        states = approved_building_bundle.states_by_level[level - 1]
        private_indices: dict[int, int] = {}
        for state in states:
            geometry_state = stable_state_geometry(states, state)
            payload = package_approved_building_tile(
                stock,
                tiles[state.source_tile_index].data,
                state,
                tiles[geometry_state.source_tile_index].data,
                geometry_state,
            )
            private_index = append(
                f"ALB{level}State{state.source_tile_index:04d}".encode("ascii"),
                payload,
            )
            private_indices[state.source_tile_index] = private_index
            if level == 3 and state.source_tile_index == 1027:
                reagent_ready_template = payload
            source_hotspot = struct.unpack_from(
                "<hh", tiles[state.source_tile_index].data, 10
            )
            packaged_hotspot = struct.unpack_from("<hh", payload, 10)
            approved_building_records.append(
                {
                    "concept_key": state.concept_key,
                    "level": level,
                    "role": state.role,
                    "source_tile_index": state.source_tile_index,
                    "private_tile_index": private_index,
                    "source_canvas": list(state.source_canvas),
                    "object_canvas": list(state.object_canvas),
                    "body_source_offset_in_object": list(
                        state.body_source_offset_in_object
                    ),
                    "source_hotspot": list(source_hotspot),
                    "packaged_hotspot": list(packaged_hotspot),
                    "source_art_sha256": state.indexed_object_sha256,
                    "geometry_source_tile_index": geometry_state.source_tile_index,
                    "packaged_canvas": list(geometry_state.object_canvas),
                    "packaged_body_bbox": list(geometry_state.body_bbox_in_object),
                    "packaged_tile_sha256": sha256_bytes(payload),
                    "occurrence_count": len(state.occurrences),
                }
            )
        building_imags[level - 1] = patch_approved_building_imag(
            building_imags[level - 1],
            states,
            private_indices,
            profile_index,
            icon_index,
        )
        approved_building_private_indices.append(private_indices)

    if reagent_ready_template is None:
        raise ValueError("Approved level-3 active Lab state is missing")
    reagent_ready_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(REAGENT_READY_SOURCE_TILES):
        if source_index >= len(tiles):
            raise ValueError(f"Wizard Tower enchantment TILE {source_index} is missing")
        reagent_ready_replacements[source_index] = append(
            f"ALR1Ready{frame:02d}".encode("ascii"),
            generated_reagent_ready_tile(
                stock,
                reagent_ready_template,
                palettes,
                reagent_ready_source_png,
                frame,
                len(REAGENT_READY_SOURCE_TILES),
            ),
        )
    reagent_ready_imag = stock.remap_imag_tile_indices(
        reagent_ready_imag,
        reagent_ready_replacements,
    )

    if approved_bundle is not None:
        # ALC1's cloned Interface-00/01/02 records still point at retail TILE
        # numbers. Those positions are intentionally empty in this private CAM,
        # so copy the already-established Alchemist interface art at the end of
        # the private table and remap all three records together. Appending here
        # preserves every approved motion and previously generated private TILE
        # index while restoring portrait, selected-unit panel, and hero-count
        # icon as one stock interface contract.
        interface_specs = (
            (
                HERO_PORTRAIT_TILE,
                b"ALC1Portrait",
                repo / "assets/source/hero/portrait.png",
                (100, 100),
                BUILDING_PALETTE,
            ),
            (
                HERO_ICON_TILE,
                b"ALC1HeroIcon",
                art_dir / "interface/hero-icon-25.png",
                (25, 25),
                BUILDING_PALETTE,
            ),
            (
                HERO_PANEL_TILE,
                b"ALC1HeroPanel",
                art_dir / "interface/building-panel-200x245.png",
                (200, 245),
                HERO_ART_PALETTE,
            ),
        )
        for source_index, name, image_path, image_size, palette_index in interface_specs:
            source_art_sha256 = sha256_file(image_path)
            if source_art_sha256 != APPROVED_INTERFACE_ART_SHA256[source_index]:
                raise ValueError(
                    f"Approved Alchemist interface art changed for TILE {source_index}: "
                    f"{source_art_sha256}"
                )
            template = stock.remap_tile_palette_index(
                tiles[source_index].data,
                palette_index,
            )
            payload = stock.tile_from_rgb(
                template,
                palettes,
                image_rgb(image_path, image_size),
            )
            private_index = append(name, payload)
            approved_interface_tile_indices[source_index] = private_index
            approved_interface_records.append(
                {
                    "source_stock_slot": source_index,
                    "private_tile_index": private_index,
                    "name": name.decode("ascii"),
                    "source_art": image_path.relative_to(repo).as_posix(),
                    "source_art_sha256": source_art_sha256,
                    "packaged_tile_sha256": sha256_bytes(payload),
                    "canvas": list(image_size),
                    "palette_index": palette_index,
                }
            )
        hero_imag = stock.remap_imag_low16_tile_indices(
            hero_imag,
            approved_interface_tile_indices,
        )

    palette_indices = {BUILDING_PALETTE, HERO_ART_PALETTE}
    for entry in extra:
        index = stock.tile_palette_index(entry.data)
        if index is not None:
            palette_indices.add(index)
    palette_entries_list = []
    for index in range(max(palette_indices) + 1):
        if approved_bundle is not None and index == approved_bundle.private_palette_index:
            palette_entries_list.append(
                stock.CamEntry(
                    name=stock.pad_name(b"ALC1WalkStandV4"),
                    data=approved_bundle.private_palette_data,
                )
            )
            continue
        palette_entries_list.append(
            stock.CamEntry(
                name=palettes[index].name,
                data=(
                    stock.splt_with_color_replacements(
                        palettes[index].data,
                        {
                            247: (156, 33, 24),
                            248: (178, 0, 178),
                            249: (204, 0, 204),
                            250: (229, 0, 229),
                        },
                    )
                    if index == BUILDING_PALETTE
                    else palettes[index].data
                ),
            )
        )
    palette_entries = tuple(palette_entries_list)
    tile_entries = [
        stock.CamEntry(name=tiles[index].name, data=b"")
        for index in range(base_max + 1)
    ]
    tile_entries.extend(extra)
    images = (
        stock.CamEntry(stock.pad_name(HERO_CUSTOM), hero_imag),
        *(stock.CamEntry(stock.pad_name(name), imag) for name, imag in zip(BUILDING_CUSTOM, building_imags)),
        stock.CamEntry(stock.pad_name(INVENTORY_ITEM_CUSTOM), phoenix_item_imag),
        stock.CamEntry(stock.pad_name(PHOENIX_LIFECYCLE_CUSTOM), phoenix_lifecycle_imag),
        stock.CamEntry(stock.pad_name(VIGOR_EFFECT_CUSTOM), vigor_effect_imag),
        stock.CamEntry(stock.pad_name(FLASH_FLASK_BUFF_CUSTOM), flash_flask_buff_imag),
        stock.CamEntry(
            stock.pad_name(FLASH_FLASK_ACTIVATION_CUSTOM),
            flash_flask_activation_imag,
        ),
        stock.CamEntry(stock.pad_name(STUN_SERUM_IMPACT_CUSTOM), stun_serum_impact_imag),
        stock.CamEntry(
            stock.pad_name(STUN_SERUM_RESTRAINT_CUSTOM), stun_serum_restraint_imag
        ),
        stock.CamEntry(stock.pad_name(STUN_SERUM_DEBUFF_CUSTOM), stun_serum_debuff_imag),
        stock.CamEntry(
            stock.pad_name(PARALYTIC_OIL_RESTRAINT_CUSTOM),
            paralytic_oil_restraint_imag,
        ),
        stock.CamEntry(
            stock.pad_name(PHILOSOPHERS_STONE_HIT_CUSTOM),
            philosophers_stone_hit_imag,
        ),
        stock.CamEntry(
            stock.pad_name(ARCANE_INFUSION_EFFECT_CUSTOM),
            arcane_infusion_effect_imag,
        ),
        stock.CamEntry(
            stock.pad_name(VIGOR_ACTIVATION_EFFECT_CUSTOM),
            vigor_activation_effect_imag,
        ),
        stock.CamEntry(stock.pad_name(MIASMA_STORM_CUSTOM), miasma_storm_imag),
        stock.CamEntry(stock.pad_name(MIASMA_MISSILE_CUSTOM), miasma_missile_imag),
        stock.CamEntry(stock.pad_name(MIASMA_PARTICLE_CUSTOM), miasma_particle_imag),
        stock.CamEntry(stock.pad_name(MIASMA_DEBUFF_CUSTOM), miasma_debuff_imag),
        stock.CamEntry(stock.pad_name(MIASMA_ANCHOR_CUSTOM), miasma_anchor_imag),
        stock.CamEntry(stock.pad_name(REAGENT_READY_CUSTOM), reagent_ready_imag),
    )
    stock.write_cam(
        (
            stock.CamSection(b"IMAG", b"\x00\x00\x00\x00", tuple(images)),
            stock.CamSection(b"TILE", b"\x01\x00\x00\x00", tuple(tile_entries)),
            stock.CamSection(b"SPLT", b"\x01\x00\x00\x00", palette_entries),
        ),
        output,
    )
    validate_packaged_approved_building_cam(
        stock,
        output,
        tiles,
        palettes,
        approved_building_bundle,
        approved_building_private_indices,
        profile_index,
        icon_index,
        BUILDING_CUSTOM,
        approved_building_records,
    )
    if approved_bundle is not None:
        validate_packaged_approved_sprite_cam(
            stock,
            output,
            tiles,
            palettes,
            stock.read_cam_entry(source, b"IMAG", HERO_SOURCE).data,
            approved_bundle,
            approved_private_tile_indices,
            approved_interface_tile_indices,
            approved_interface_records,
        )
        provenance = package_provenance(
            approved_bundle,
            approved_private_tile_indices,
            approved_interface_tile_indices,
            approved_interface_records,
            output,
        )
        provenance["building_art"] = {
            "authority": "accepted-as-is-r9",
            "payload_aggregate_sha256": APPROVED_BUILDING_PAYLOAD_SHA256,
            "source_topology": [
                {
                    "level": level,
                    "imag": name.decode("ascii"),
                    "imag_sha256": sha256_bytes(imag),
                }
                for level, (name, imag) in enumerate(
                    zip(APPROVED_BUILDING_SOURCE_IMAGS, approved_building_bundle.source_imags),
                    start=1,
                )
            ],
            "states": approved_building_records,
        }
        return provenance
    return None


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
    expansion_source = game_data.parent / "DataMX" / "mx_interfacedata.cam"
    expansion_tiles = stock.read_cam_entries(expansion_source, b"TILE")
    tactical_cursor_imag = stock.read_cam_entry(
        expansion_source, b"IMAG", TACTICAL_CURSOR_SOURCE
    ).data
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
    button_overrides.update(recipe_button_plate_frames(stock, tiles))
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
            BREWING_DIALOG_FRAME_TILE: brewing_dialog_tile(
                stock, tiles[BREWING_DIALOG_FRAME_TILE].data, dialog_path
            )
        },
    )
    navigation_overrides = vigor_icon_overrides(
        stock,
        tiles,
        art_dir / "interface/vigor-elixir-icon-24.png",
        art_dir / "interface",
    )
    navigation_overrides.update(
        brewing_recipe_icon_overrides(
            stock,
            tiles,
            navigation_imag,
            (
                (
                    0x3F6,
                    art_dir / "interface/arcane-infusion-icon-25.png",
                    "arcane-infusion",
                ),
                (
                    0x3F7,
                    art_dir / "interface/philosophers-stone-icon-25.png",
                    "philosophers-stone",
                ),
            ),
            art_dir / "interface",
        )
    )
    navigation_imag = privateize_interface_imag_tiles(
        navigation_imag,
        tiles,
        append,
        b"ALIN",
        navigation_overrides,
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
    stone_cursor_tile = append(
        b"ALCSStoneCursor",
        private_tactical_cursor_tile(
            stock,
            expansion_tiles[TACTICAL_CURSOR_TEMPLATE_TILE].data,
            art_dir / "interface/philosophers-stone-icon-25.png",
        ),
    )
    tactical_cursor_imag = append_private_tactical_cursor_sets(
        tactical_cursor_imag,
        stone_cursor_tile,
    )

    tile_entries = [stock.CamEntry(name=tile.name, data=b"") for tile in tiles]
    # The complete expansion CUR1 record reads its stock cursor payloads from
    # the continuous DataMX TILE range 17..53. Carry those records literally
    # at their native indices so this private CUR1 override is self-contained;
    # every other stock TILE slot remains an empty fall-through entry.
    if len(tile_entries) <= 53 or len(expansion_tiles) <= 53:
        raise ValueError("Expansion tactical cursor TILE range changed")
    for tile_index in range(17, 54):
        tile_entries[tile_index] = stock.CamEntry(
            expansion_tiles[tile_index].name,
            expansion_tiles[tile_index].data,
        )
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
                    stock.CamEntry(
                        stock.pad_name(TACTICAL_CURSOR_CUSTOM),
                        tactical_cursor_imag,
                    ),
                ),
            ),
            stock.CamSection(b"TILE", b"\x01\x00\x00\x00", tuple(tile_entries)),
        ),
        output,
    )
