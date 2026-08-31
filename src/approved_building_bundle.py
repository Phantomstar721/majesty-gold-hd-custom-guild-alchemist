from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
from pathlib import PurePosixPath
import struct
from typing import Any, Sequence

from PIL import Image


MANIFEST_SCHEMA = "majesty-building-sprite-integration-exception/alchemist-r14-s01-v2"
LIFECYCLE_SCHEMA = "alchemist-building-sprite-lifecycle-map/accepted-as-is-v2"
RECEIVER_SCHEMA = "alchemist-repo-building-art-replacement/v2"
AUTHORITY_SCHEMA = "majesty-building-stock-authority/v1"
MANIFEST_SHA256 = "7d82d7467a7b13167d8a72cf29d0b82b38b01f39dde70eec62053801cb0d9036"
LIFECYCLE_SHA256 = "538ea01ce7579fc192468e944586b3700d6d255aae52c495e6159288783a4943"
RECEIVER_SHA256 = "76d2c511b60319e4b2a5100c4ebb94af183dbbf970d3c16cd8326ef043d96be1"
CHECKSUMS_SHA256 = "e2e18d98436fd5314b33976e766a934b807895477b31e26bf30c28aa62a6d8e3"
PAYLOAD_AGGREGATE_SHA256 = "885747972820262eaab6ddc30bafec44ca53655782381c7aa35454b116c6522a"
STOCK_AUTHORITY_SHA256 = "e9385108cc6e6682201befaded6ffbe366d0b0536301a411b40ee3df8ad02de6"
SOURCE_CAM_SHA256 = "92b1a4caa111495aebe483e5617c7cc4f291eb1d897877860cfbdbc632a0d213"
HIRES_AUTHORITY_DIRECTORY = "approved-alchemist-building-hires-v2"
HIRES_AUTHORITY_SCHEMA = "alchemist-lab-r14-registered-damage-raster-gate/v1"
HIRES_AUTHORITY_MANIFEST_SHA256 = (
    "b4649a3d04b829a9815eded14d640c0f22ba2ae45e2c213f877d6c522ffc5e78"
)
HIRES_AUTHORITY_APPROVAL_SHA256 = (
    "5371788be24e8ea9cf1073d3ab78fae4f19bbde5bdc676d5c90ee23eb3524e94"
)
HIRES_AUTHORITY_RECEIPT_SHA256 = (
    "31871813e6f2685d806ff9a54f48aaafc05161ae15c45d19edb9215de65a7893"
)
HIRES_AUTHORITY_TRANSITION_SHA256 = (
    "83f2d7198dda9774eadd6ee0d28d9a07203d962ad0f98e035703ea1ba8094d45"
)
SOURCE_PALETTE_INDEX = 68
SOURCE_PALETTE_COUNT = 854
# 854 is already the approved Alchemist hero's private palette.  The active
# Laboratory glow is the next private entry and never aliases that authority.
ACTIVE_GLOW_PALETTE_INDEX = 855
ACTIVE_GLOW_PALETTE_NAME = b"ALG1Lab Active Glow"
ACTIVE_GLOW_VIOLET_INDICES = (
    138,
    139,
    140,
    141,
    142,
    144,
    147,
    149,
    150,
    151,
    152,
    153,
)
ACTIVE_GLOW_VIOLET_COLORS = (
    (38, 27, 62),
    (46, 31, 74),
    (55, 36, 88),
    (66, 43, 104),
    (79, 51, 122),
    (94, 61, 141),
    (112, 74, 162),
    (132, 90, 184),
    (154, 109, 205),
    (178, 133, 225),
    (204, 163, 241),
    (232, 204, 255),
)
ACTIVE_GLOW_AMBER_INDICES = (93, 97, 154, 155, 156, 157, 158, 160, 164, 165)
ACTIVE_GLOW_AMBER_COLORS = (
    (56, 31, 13),
    (69, 38, 14),
    (84, 47, 17),
    (102, 57, 21),
    (123, 70, 26),
    (148, 86, 33),
    (176, 105, 43),
    (205, 131, 58),
    (232, 164, 83),
    (252, 207, 137),
)
CONTROL_INDICES = frozenset((247, 248, 249, 250))
SOURCE_IMAG_NAMES = (
    b"ABH1Marketplace1",
    b"ABH2Marketplace 2",
    b"ABH3Marketplace 3",
)
SOURCE_IMAG_SHA256 = (
    "ce576b7cf2153528ad06d3f395443cd8383e66474956efdcc36f4e5188e055be",
    "d7ab6a2708ac336e1b95924b2162ffa19d884c530a2c7749e0d5c419b49b7921",
    "46d82d6993b26766e71718cce5c989c7939e7196b2f04975be265fac3e206c4f",
)
SOURCE_IMAG_SET_COUNTS = (32, 33, 35)
SOURCE_INTERFACE_OCCURRENCES = (
    # set order, raw set ID, track order, frame order, source TILE
    (0, 1000, 0, 0, 990),
    (2, 1002, 0, 0, 991),
)
SOURCE_HOTSPOT_TILES = (989, 1006, 1023)
HOTSPOT_SET_ID = 400
INACTIVE_SET_ID = 208
READY_SOURCE_TILES = tuple(range(2349, 2365))
READY_PALETTE_INDEX = 577
READY_CANVAS = (269, 213)
READY_ANCHOR = (140, 65)
READY_HEADER = (3, 213, 269, 0, 32, 140, 65, 8)

# The accepted v2 handoff normalized r14 onto small Marketplace canvases, while
# the user-approved in-game footprint is 2x. Render the approved r14 raster
# authority directly to that final canvas so it is sampled and quantized only
# once; scale only the accepted indexed control plane with nearest-neighbor.
# The Marketplace lifecycle remains the stock-literal owner of the world
# position.  When the approved body is enlarged, preserve each exact source
# TILE's signed relationship between its hotspot and visible ground center
# (horizontal body center, bottom body row).  This removes transparent-canvas
# gutters from the calculation and seats each differently shaped Lab state on
# its own Marketplace ground plane instead of pretending its silhouette is
# oriented exactly like another guild.
RUNTIME_BUILDING_SCALE = 2.0
# The accepted r14 authority independently registers its semantic pool at this
# fixed displacement from every source hotspot.  Retain it as a body-family
# registration gate and a diagnostic cross-check, not as a replacement for the
# stock Marketplace ground owner.
LAB_OWNER_TO_POOL_DISPLACEMENT = (45, 90)
# Wizard Guild is the user's requested visual comparison.  Its complete body
# lifecycle independently proves a 138-pixel front-ground offset; the Lab's
# registered-pool placement is validated and reported against this authority,
# but the Wizard silhouette is not substituted for the Lab's own registration.
WIZARD_GUILD_GROUND_BASE_OFFSET = 138
WIZARD_GUILD_GROUND_AUTHORITY_IMAGS = (
    b"ABY1Wizard Guild1",
    b"ABY2Wizard Guild2",
    b"ABY3Wizard Guild3",
)
WIZARD_GUILD_GROUND_AUTHORITY_IMAG_SHA256 = (
    "0005d8fe35f3fae8237a6b26153ec496a897ab85435a9f4cdca8bf9659ec3e12",
    "05c43681b7a11f8850c03ee6412e1368b07d6df79d8ea82d7f9bb149144411a6",
    "7ec801021eabb743633898b67c6a329384dc486394fda65a97d7a1e3a3b67b49",
)
# These are the body-owning TILEs reached by the stock Wizard Guild lifecycle:
# construction handoff (set 80), inactive (208), damage A (98/99), damage B
# (100/101), and rubble (224).  Level 2/3 construction literally carries the
# preceding level's inactive TILE, exactly as represented below.
WIZARD_GUILD_GROUND_AUTHORITY_TILES_BY_LEVEL = {
    1: (1780, 1781, 1782, 1783, 1778),
    2: (1781, 1905, 1906, 1907, 1778),
    3: (1905, 1956, 1957, 1958, 1778),
}
# Literal eight-frame Haunt light-breathing cycle.  The authored active art is
# frame zero/four, reaches only +10% at frame two, and only -10% at frame six.
# Keeping this exact, restrained sine table is what makes its windows and
# alchemical liquids read as one stable mystical light instead of flickering
# replacement art.
ACTIVE_PULSE_FACTORS = (
    1.0,
    1.0707106781186548,
    1.1,
    1.0707106781186548,
    1.0,
    0.9292893218813453,
    0.9,
    0.9292893218813453,
)
# The Haunt brightens one stable authored light surface rather than swapping
# highlight drawings between frames.  The Lab uses the same eight-frame pulse,
# with the frozen inactive raster supplying the complete pool/vat mask.  Two
# steps of lift make the liquids read as active before the restrained +/-10%
# breathing cycle is applied.
ACTIVE_GLOW_RAMP_LIFT_STEPS = 2
LIQUID_MASK_EXPECTED_BY_LEVEL = {
    1: {
        "source_count": 1725,
        "runtime_count": 989,
        "runtime_bbox": (279, 208, 331, 233),
    },
    2: {
        "source_count": 3512,
        "runtime_count": 1667,
        "runtime_bbox": (314, 185, 388, 299),
    },
    3: {
        "source_count": 3922,
        "runtime_count": 2811,
        "runtime_bbox": (315, 148, 410, 313),
    },
}
_RUNTIME_SHADOW_METRICS_CACHE: dict[str, dict[str, Any]] = {}
_HAUNT_SHADOW_COMPOSITE_CACHE: dict[str, bytes] = {}
HAUNT_SHADOW_SOURCE_SHA256 = (
    "cf9985ecf6670886dff5970bad72b383c182ae685cb2d87ef84af34ac31bcd99"
)
_HAUNT_SHADOW_MODULE: Any | None = None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def runtime_visible_body_bbox(
    rows: Sequence[Sequence[int]],
) -> tuple[int, int, int, int]:
    """Return the exclusive bounds of ordinary visible TILE pixels."""

    width = len(rows[0]) if rows else 0
    if not width or any(len(row) != width for row in rows):
        raise ValueError("Laboratory runtime TILE rows changed shape")
    body = [
        (x, y)
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if 1 <= value <= 246
    ]
    if not body:
        raise ValueError("Laboratory runtime TILE lost its visible body")
    return (
        min(x for x, _y in body),
        min(y for _x, y in body),
        max(x for x, _y in body) + 1,
        max(y for _x, y in body) + 1,
    )


def marketplace_ground_aligned_hotspot(
    stock: Any,
    template: bytes,
    runtime_rows: Sequence[Sequence[int]],
) -> tuple[tuple[int, int], dict[str, Any]]:
    """Preserve a Marketplace TILE's visible ground-center registration."""

    source_decoded = stock.decode_indexed_v3_tile(template)
    if source_decoded is None:
        raise ValueError("Marketplace ground-authority TILE no longer decodes")
    source_bbox = runtime_visible_body_bbox(source_decoded[2])
    runtime_bbox = runtime_visible_body_bbox(runtime_rows)
    source_hotspot = struct.unpack_from("<hh", template, 10)
    source_center_twice = source_bbox[0] + source_bbox[2]
    runtime_center_twice = runtime_bbox[0] + runtime_bbox[2]
    source_center_offset_twice = source_center_twice - 2 * source_hotspot[0]
    hotspot_x_twice = runtime_center_twice - source_center_offset_twice
    hotspot_x = (
        (hotspot_x_twice + 1) // 2
        if hotspot_x_twice >= 0
        else -((-hotspot_x_twice + 1) // 2)
    )
    source_front_ground_offset = source_bbox[3] - source_hotspot[1]
    hotspot_y = runtime_bbox[3] - source_front_ground_offset
    hotspot = (hotspot_x, hotspot_y)
    metrics = {
        "source_body_bbox": list(source_bbox),
        "runtime_body_bbox": list(runtime_bbox),
        "source_hotspot": list(source_hotspot),
        "source_body_center_offset_twice": source_center_offset_twice,
        "runtime_body_center_offset_twice": (
            runtime_center_twice - 2 * hotspot_x
        ),
        "source_front_ground_offset": source_front_ground_offset,
        "runtime_front_ground_offset": runtime_bbox[3] - hotspot_y,
    }
    if (
        abs(
            metrics["runtime_body_center_offset_twice"]
            - source_center_offset_twice
        )
        > 1
        or metrics["runtime_front_ground_offset"]
        != source_front_ground_offset
    ):
        raise AssertionError("Laboratory lost its Marketplace ground registration")
    return hotspot, metrics


def validate_stock_wizard_ground_authority(
    stock: Any,
    source_cam: Path,
    stock_tiles: Sequence[Any],
) -> dict[str, Any]:
    """Prove the stock Wizard Guild ground baseline used by private Lab TILEs."""

    lifecycle_roles = (
        "construction_handoff",
        "inactive",
        "damage_a",
        "damage_b",
        "rubble",
    )
    levels: list[dict[str, Any]] = []
    for level, (imag_name, imag_hash) in enumerate(
        zip(
            WIZARD_GUILD_GROUND_AUTHORITY_IMAGS,
            WIZARD_GUILD_GROUND_AUTHORITY_IMAG_SHA256,
        ),
        start=1,
    ):
        imag = stock.read_cam_entry(source_cam, b"IMAG", imag_name).data
        if sha256_bytes(imag) != imag_hash:
            raise ValueError("Stock Wizard Guild ground-authority IMAG changed")
        states: list[dict[str, Any]] = []
        for role, tile_index in zip(
            lifecycle_roles,
            WIZARD_GUILD_GROUND_AUTHORITY_TILES_BY_LEVEL[level],
        ):
            decoded = stock.decode_indexed_v3_tile(stock_tiles[tile_index].data)
            if decoded is None:
                raise ValueError("Stock Wizard Guild ground-authority TILE changed")
            body_bbox = runtime_visible_body_bbox(decoded[2])
            hotspot = struct.unpack_from("<hh", stock_tiles[tile_index].data, 10)
            ground_base_offset = body_bbox[3] - hotspot[1]
            if ground_base_offset != WIZARD_GUILD_GROUND_BASE_OFFSET:
                raise ValueError(
                    "Stock Wizard Guild ground baseline changed: "
                    f"level={level} role={role} offset={ground_base_offset}"
                )
            states.append(
                {
                    "role": role,
                    "tile_index": tile_index,
                    "hotspot": list(hotspot),
                    "body_bbox": list(body_bbox),
                    "ground_base_offset": ground_base_offset,
                }
            )
        levels.append(
            {
                "level": level,
                "imag": imag_name.decode("ascii"),
                "imag_sha256": imag_hash,
                "states": states,
            }
        )
    return {
        "analogue": "ABY1/2/3 Wizard Guild",
        "lifecycle_sets": {
            "construction_handoff": [80],
            "inactive": [208],
            "damage_a": [98, 99],
            "damage_b": [100, 101],
            "rubble": [224],
        },
        "ground_base_offset": WIZARD_GUILD_GROUND_BASE_OFFSET,
        "levels": levels,
    }


def _load_json(path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    if expected_sha256 is not None and sha256_file(path) != expected_sha256:
        raise ValueError(f"Approved building authority changed: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Approved building authority is not an object: {path}")
    return value


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


@dataclass(frozen=True)
class ApprovedHighResolutionState:
    state_id: str
    source_path: Path
    source_sha256: str
    source_alpha_bbox: tuple[int, int, int, int]
    source_pool_center: tuple[float, float]
    fixed_group_scale: float
    target_pool_center: tuple[int, int]
    paste_offset: tuple[int, int]


@dataclass(frozen=True)
class ApprovedBuildingState:
    concept_key: str
    level: int
    role: str
    source_tile_index: int
    indexed_object_path: Path
    indexed_object_sha256: str
    source_canvas: tuple[int, int]
    object_canvas: tuple[int, int]
    body_source_offset_in_object: tuple[int, int]
    body_bbox_in_object: tuple[int, int, int, int]
    shadow_bbox_in_object: tuple[int, int, int, int]
    control_counts: dict[int, int]
    occurrences: tuple[dict[str, int], ...]
    body_rgba_path: Path
    body_rgba_sha256: str
    high_resolution: ApprovedHighResolutionState


@dataclass(frozen=True)
class ApprovedReadyPhase:
    phase: int
    overlay_path: Path
    overlay_sha256: str


@dataclass(frozen=True)
class ApprovedBuildingBundle:
    root: Path
    source_imags: tuple[bytes, bytes, bytes]
    states_by_level: tuple[
        tuple[ApprovedBuildingState, ...],
        tuple[ApprovedBuildingState, ...],
        tuple[ApprovedBuildingState, ...],
    ]
    ready_phases: tuple[ApprovedReadyPhase, ...]
    ready_frame_to_key_phase: tuple[int, ...]


def _verify_transfer_checksums(root: Path) -> dict[str, Any]:
    checksums_path = root / "checksums.sha256"
    if sha256_file(checksums_path) != CHECKSUMS_SHA256:
        raise ValueError("Approved building transfer checksum list changed")
    rows = checksums_path.read_text(encoding="ascii").splitlines()
    if len(rows) != 76:
        raise ValueError(f"Approved building transfer expected 76 files, found {len(rows)}")
    checksum_paths: set[str] = set()
    for row in rows:
        expected, relative = row.split("  ", 1)
        checksum_paths.add(relative)
        path = root / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Approved building transfer changed: {relative}")
    manifest = _load_json(root / "manifest.json", MANIFEST_SHA256)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("Approved building manifest schema changed")
    if manifest.get("payload_aggregate_sha256") != PAYLOAD_AGGREGATE_SHA256:
        raise ValueError("Approved building payload aggregate changed")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != 75:
        raise ValueError("Approved building manifest no longer covers 75 payload files")
    manifest_paths: set[str] = set()
    for item in files:
        relative = item.get("path")
        path = root / relative if isinstance(relative, str) else root
        if (
            not isinstance(relative, str)
            or not path.is_file()
            or path.stat().st_size != item.get("bytes")
            or sha256_file(path) != item.get("sha256")
        ):
            raise ValueError(f"Approved building manifest changed: {relative}")
        manifest_paths.add(relative)
    if checksum_paths != manifest_paths | {"manifest.json"}:
        raise ValueError("Approved building checksum and manifest inventories differ")
    return manifest


def _validate_palette(stock: Any, root: Path, palettes: Sequence[Any]) -> None:
    palette_authority = _load_json(root / "authority" / "palette-68-fd9db59aaba7.json")
    expected = [tuple(color) for color in palette_authority.get("colors", [])]
    if len(expected) != 256:
        raise ValueError("Approved Marketplace palette authority is incomplete")
    if SOURCE_PALETTE_INDEX >= len(palettes):
        raise ValueError("Stock Marketplace palette 68 is missing")
    actual = stock.splt_palette_colors(palettes[SOURCE_PALETTE_INDEX].data)
    if actual != expected:
        raise ValueError("Stock Marketplace palette 68 changed")


def _state_pixel_metrics(image: Image.Image) -> tuple[
    list[list[int]], dict[int, int], tuple[int, int, int, int], tuple[int, int, int, int]
]:
    if image.mode != "P":
        raise ValueError("Approved building object is no longer indexed")
    width, height = image.size
    flat = list(image.getdata())
    rows = [flat[y * width : (y + 1) * width] for y in range(height)]
    if any(value > 250 for value in flat):
        raise ValueError("Approved building object contains forbidden palette indices")
    controls = {index: flat.count(index) for index in CONTROL_INDICES}
    body_points = [
        (x, y)
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if 1 <= value <= 246
    ]
    shadow_points = [
        (x, y)
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if value in CONTROL_INDICES
    ]
    if not body_points or not shadow_points:
        raise ValueError("Approved building object lost body or shadow-control pixels")

    def bbox(points: list[tuple[int, int]]) -> tuple[int, int, int, int]:
        return (
            min(x for x, _y in points),
            min(y for _x, y in points),
            max(x for x, _y in points) + 1,
            max(y for _x, y in points) + 1,
        )

    return rows, controls, bbox(body_points), bbox(shadow_points)


def _safe_authority_path(root: Path, relative: str) -> Path:
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or not parsed.parts or ".." in parsed.parts:
        raise ValueError(f"Unsafe high-resolution authority path: {relative}")
    return root.joinpath(*parsed.parts)


def _render_high_resolution_body(
    authority: ApprovedHighResolutionState,
    source_canvas: tuple[int, int],
    scale: float,
    *,
    registration: ApprovedHighResolutionState | None = None,
) -> Image.Image:
    """Register one approved r14 source directly at the requested game scale.

    The accepted v2 body is the 1x result of this same transform. Rendering the
    r14 source once at 2x retains its actual detail; enlarging the already
    reduced/palette-quantized v2 body cannot recover it. Active light authority
    may borrow the inactive registration so its architecture remains perfectly
    stationary across the pulse, matching the stock Haunt invariant.
    """

    registration = registration or authority
    if (
        authority.fixed_group_scale != registration.fixed_group_scale
        or authority.target_pool_center != registration.target_pool_center
    ):
        raise ValueError("High-resolution active/inactive registration family changed")
    with Image.open(authority.source_path) as opened:
        if opened.mode != "RGBA":
            raise ValueError(
                f"Approved high-resolution source is not RGBA: {authority.state_id}"
            )
        body = opened.copy()
    source_bbox = body.getchannel("A").getbbox()
    if source_bbox != authority.source_alpha_bbox:
        raise ValueError(
            f"Approved high-resolution source bounds changed: {authority.state_id}"
        )
    source_margins = (
        source_bbox[0],
        source_bbox[1],
        body.width - source_bbox[2],
        body.height - source_bbox[3],
    )
    if min(source_margins) < 8:
        raise ValueError(
            f"Approved high-resolution source lost its gutter: {authority.state_id}"
        )

    native_registered_size = (
        max(1, round(body.width * authority.fixed_group_scale)),
        max(1, round(body.height * authority.fixed_group_scale)),
    )
    resized = body.resize(
        (
            max(1, round(native_registered_size[0] * scale)),
            max(1, round(native_registered_size[1] * scale)),
        ),
        Image.Resampling.LANCZOS,
    )
    resized.putalpha(
        resized.getchannel("A").point(
            [0 if value < 8 else value for value in range(256)]
        )
    )
    target_canvas = (
        round(source_canvas[0] * scale),
        round(source_canvas[1] * scale),
    )
    offset = (
        round(registration.paste_offset[0] * scale),
        round(registration.paste_offset[1] * scale),
    )
    resized_bbox = resized.getchannel("A").getbbox()
    if resized_bbox is None:
        raise ValueError(f"Approved high-resolution source became empty: {authority.state_id}")
    placed_bbox = (
        resized_bbox[0] + offset[0],
        resized_bbox[1] + offset[1],
        resized_bbox[2] + offset[0],
        resized_bbox[3] + offset[1],
    )
    margins = (
        placed_bbox[0],
        placed_bbox[1],
        target_canvas[0] - placed_bbox[2],
        target_canvas[1] - placed_bbox[3],
    )
    if min(margins) < round(4 * scale):
        raise ValueError(
            f"High-resolution runtime body lost its fixed-canvas gutter: "
            f"{authority.state_id} {margins}"
        )
    result = Image.new("RGBA", target_canvas, (0, 0, 0, 0))
    result.alpha_composite(resized, offset)
    if result.getchannel("A").getbbox() != placed_bbox:
        raise ValueError(
            f"High-resolution runtime body was clipped: {authority.state_id}"
        )
    return result


def _load_high_resolution_authority(
    root: Path,
) -> dict[tuple[int, int], tuple[dict[str, Any], ApprovedHighResolutionState]]:
    manifest = _load_json(
        root / "review-manifest.json", HIRES_AUTHORITY_MANIFEST_SHA256
    )
    approval = _load_json(root / "approval.json", HIRES_AUTHORITY_APPROVAL_SHA256)
    _load_json(
        root / "authority-receipt.json", HIRES_AUTHORITY_RECEIPT_SHA256
    )
    _load_json(
        root / "transition-ledger.json", HIRES_AUTHORITY_TRANSITION_SHA256
    )
    if (
        manifest.get("schema") != HIRES_AUTHORITY_SCHEMA
        or manifest.get("authority_receipt_sha256")
        != HIRES_AUTHORITY_RECEIPT_SHA256
        or approval.get("revision") != "r14"
        or approval.get("decision") != "approved"
        or approval.get("scope")
        != "raster body family only; shadow-preview-s01 remains a separate review-only proposal"
    ):
        raise ValueError("Approved r14 high-resolution body authority changed")

    records: dict[
        tuple[int, int], tuple[dict[str, Any], ApprovedHighResolutionState]
    ] = {}
    for item in manifest.get("states", []):
        state_id = item.get("state_id")
        if not isinstance(state_id, str) or state_id.startswith("l3-ready-"):
            continue
        level = item.get("level")
        source_tile = item.get("stock_tile_index")
        source_record = item.get("source", {})
        registration = item.get("registration", {})
        relative = source_record.get("path")
        expected_hash = source_record.get("sha256")
        if (
            not isinstance(level, int)
            or not isinstance(source_tile, int)
            or not isinstance(relative, str)
            or not isinstance(expected_hash, str)
        ):
            raise ValueError(f"Incomplete high-resolution state authority: {state_id}")
        source_path = _safe_authority_path(root, relative)
        if not source_path.is_file() or sha256_file(source_path) != expected_hash:
            raise ValueError(f"Approved high-resolution source changed: {state_id}")
        source_bbox = tuple(registration.get("source_alpha_bbox", ()))
        source_pool = tuple(registration.get("source_pool", {}).get("center", ()))
        target_pool = tuple(registration.get("target_pool_center", ()))
        paste_offset = tuple(registration.get("paste_offset", ()))
        fixed_scale = registration.get("fixed_group_scale")
        if (
            len(source_bbox) != 4
            or len(source_pool) != 2
            or len(target_pool) != 2
            or len(paste_offset) != 2
            or not isinstance(fixed_scale, (int, float))
            or fixed_scale <= 0
        ):
            raise ValueError(f"Incomplete high-resolution registration: {state_id}")
        key = (level, source_tile)
        if key in records:
            raise ValueError(f"Duplicate high-resolution state authority: {state_id}")
        records[key] = (
            item,
            ApprovedHighResolutionState(
                state_id=state_id,
                source_path=source_path,
                source_sha256=expected_hash,
                source_alpha_bbox=tuple(int(value) for value in source_bbox),
                source_pool_center=tuple(float(value) for value in source_pool),
                fixed_group_scale=float(fixed_scale),
                target_pool_center=tuple(int(value) for value in target_pool),
                paste_offset=tuple(int(value) for value in paste_offset),
            ),
        )
    if len(records) != 25:
        raise ValueError(
            f"Approved high-resolution authority expected 25 states, found {len(records)}"
        )
    return records


def load_approved_building_bundle(
    root: Path,
    stock: Any,
    source_cam: Path,
    tiles: Sequence[Any],
    palettes: Sequence[Any],
) -> ApprovedBuildingBundle:
    manifest = _verify_transfer_checksums(root)
    lifecycle = _load_json(
        root / "integration" / "lifecycle-map.json", LIFECYCLE_SHA256
    )
    receiver = _load_json(
        root / "integration" / "receiver-contract.json", RECEIVER_SHA256
    )
    if receiver.get("schema") != RECEIVER_SCHEMA:
        raise ValueError("Approved building receiver schema changed")
    if lifecycle.get("schema") != LIFECYCLE_SCHEMA:
        raise ValueError("Approved building lifecycle schema changed")
    authority_contract = lifecycle.get("stock_authority", {})
    authority_relative = authority_contract.get("reuse_from_destination")
    if (
        authority_relative
        != "assets/source/approved-alchemist-building-set-v1/authority/stock-authority.json"
        or authority_contract.get("sha256") != STOCK_AUTHORITY_SHA256
    ):
        raise ValueError("Approved building stock-authority reuse contract changed")
    authority_path = root.parents[2] / authority_relative
    authority = _load_json(authority_path, STOCK_AUTHORITY_SHA256)
    if authority.get("schema") != AUTHORITY_SCHEMA:
        raise ValueError("Approved building stock authority schema changed")
    if (
        manifest.get("building_state_count") != 25
        or lifecycle.get("state_count") != 25
    ):
        raise ValueError("Approved building handoff no longer covers 25 states")
    if sha256_file(source_cam) != SOURCE_CAM_SHA256:
        raise ValueError("Retail maindata.cam no longer matches Marketplace authority")
    _validate_palette(stock, root, palettes)
    high_resolution_records = _load_high_resolution_authority(
        root.parent / HIRES_AUTHORITY_DIRECTORY
    )

    authority_levels = authority.get("levels")
    if not isinstance(authority_levels, list) or len(authority_levels) != 3:
        raise ValueError("Approved building authority must contain three levels")
    concepts_by_key: dict[str, dict[str, Any]] = {}
    contracts_by_level: dict[int, dict[int, dict[str, Any]]] = {}
    source_imags: list[bytes] = []
    for level, expected_name, expected_hash, expected_sets, authority_level in zip(
        (1, 2, 3),
        SOURCE_IMAG_NAMES,
        SOURCE_IMAG_SHA256,
        SOURCE_IMAG_SET_COUNTS,
        authority_levels,
    ):
        imag_authority = authority_level.get("imag", {})
        if (
            authority_level.get("level") != level
            or imag_authority.get("record_name") != expected_name.decode("ascii")
            or imag_authority.get("sha256") != expected_hash
            or imag_authority.get("set_count") != expected_sets
        ):
            raise ValueError(f"Approved Marketplace IMAG authority changed for level {level}")
        imag = stock.read_cam_entry(source_cam, b"IMAG", expected_name).data
        if sha256_bytes(imag) != expected_hash:
            raise ValueError(f"Retail Marketplace IMAG changed for level {level}")
        source_imags.append(imag)
        contracts_by_level[level] = {
            item["tile_index"]: item for item in authority_level.get("tile_contracts", [])
        }
        for concept in authority_level.get("concept_keys", []):
            concepts_by_key[concept["key"]] = concept

    states: list[list[ApprovedBuildingState]] = [[], [], []]
    seen_keys: set[str] = set()
    for item in lifecycle.get("states", []):
        key = item.get("concept_key")
        level = item.get("level")
        source_tile = int(key.rsplit("-", 1)[1]) if isinstance(key, str) else -1
        concept = concepts_by_key.get(key)
        contract = contracts_by_level.get(level, {}).get(source_tile)
        if concept is None or contract is None:
            raise ValueError(f"Approved building state has no Marketplace authority: {key}")
        if concept.get("source_tile_index") != source_tile:
            raise ValueError(f"Approved building concept changed source TILE: {key}")
        if source_tile >= len(tiles) or sha256_bytes(tiles[source_tile].data) != contract.get("sha256"):
            raise ValueError(f"Retail Marketplace TILE changed: {key}")
        if stock.tile_palette_index(tiles[source_tile].data) != SOURCE_PALETTE_INDEX:
            raise ValueError(f"Marketplace building state lost palette 68: {key}")
        decoded = stock.decode_indexed_v3_tile(tiles[source_tile].data)
        if item.get("source_tile_index") != source_tile:
            raise ValueError(f"Approved building state changed source TILE: {key}")
        expected_canvas = tuple(item.get("canvas", ()))
        if decoded is None or (decoded[1], decoded[0]) != expected_canvas:
            raise ValueError(f"Marketplace source canvas changed: {key}")
        expected_anchor = tuple(item.get("anchor", ()))
        if struct.unpack_from("<hh", tiles[source_tile].data, 10) != expected_anchor:
            raise ValueError(f"Marketplace source anchor changed: {key}")

        indexed_object = item.get("indexed_object", {})
        relative = indexed_object.get("path")
        object_path = root / relative
        expected_object_hash = indexed_object.get("sha256")
        if not object_path.is_file() or sha256_file(object_path) != expected_object_hash:
            raise ValueError(f"Approved indexed building object changed: {key}")
        with Image.open(object_path) as loaded:
            image = loaded.copy()
        rows, controls, body_bbox, shadow_bbox = _state_pixel_metrics(image)
        object_canvas = expected_canvas
        if image.size != object_canvas or (len(rows[0]), len(rows)) != object_canvas:
            raise ValueError(f"Approved indexed building canvas changed: {key}")
        expected_controls = {
            int(index): count for index, count in item.get("control_counts", {}).items()
        }
        if controls != expected_controls:
            raise ValueError(f"Approved building shadow controls changed: {key}")
        if body_bbox != tuple(item.get("body_bbox", ())):
            raise ValueError(f"Approved building body bounds changed: {key}")
        if shadow_bbox != tuple(item.get("shadow_bbox", ())):
            raise ValueError(f"Approved building shadow bounds changed: {key}")
        body_record = item.get("body_rgba", {})
        body_relative = body_record.get("path")
        body_hash = body_record.get("sha256")
        if not isinstance(body_relative, str) or not isinstance(body_hash, str):
            raise ValueError(f"Approved building body authority is incomplete: {key}")
        body_path = _safe_authority_path(root, body_relative)
        if not body_path.is_file() or sha256_file(body_path) != body_hash:
            raise ValueError(f"Approved building body authority changed: {key}")

        high_resolution_record = high_resolution_records.get((level, source_tile))
        if high_resolution_record is None:
            raise ValueError(f"Approved building state has no r14 source authority: {key}")
        high_resolution_item, high_resolution = high_resolution_record
        if (
            high_resolution.state_id != item.get("state_id")
            or tuple(high_resolution_item.get("stock_canvas", ())) != expected_canvas
            or tuple(high_resolution_item.get("stock_anchor", ())) != expected_anchor
            or high_resolution.target_pool_center
            != tuple(
                anchor + displacement
                for anchor, displacement in zip(
                    expected_anchor,
                    LAB_OWNER_TO_POOL_DISPLACEMENT,
                )
            )
            or high_resolution_item.get("output", {}).get("sha256") != body_hash
        ):
            raise ValueError(f"Approved r14 source registration changed: {key}")
        reconstructed_native = _render_high_resolution_body(
            high_resolution,
            expected_canvas,
            1.0,
        )
        with Image.open(body_path) as loaded:
            if loaded.mode != "RGBA":
                raise ValueError(f"Approved building body is not RGBA: {key}")
            approved_native = loaded.copy()
        if (
            reconstructed_native.size != approved_native.size
            or reconstructed_native.tobytes() != approved_native.tobytes()
        ):
            raise ValueError(
                f"Approved r14 source no longer reproduces the accepted v2 body: {key}"
            )
        occurrences = tuple(
            {
                "set_order": occurrence["set_order"],
                "set_id": occurrence["set_id"],
                "track_order": occurrence["track_order"],
                "frame_order": occurrence["frame_order"],
                "reference_word": occurrence["reference_word"],
            }
            for occurrence in concept.get("occurrences", [])
        )
        if not occurrences:
            raise ValueError(f"Approved building state has no IMAG occurrences: {key}")
        states[level - 1].append(
            ApprovedBuildingState(
                concept_key=key,
                level=level,
                role=item["role"],
                source_tile_index=source_tile,
                indexed_object_path=object_path,
                indexed_object_sha256=expected_object_hash,
                source_canvas=expected_canvas,
                object_canvas=object_canvas,
                body_source_offset_in_object=tuple(item["body_source_offset_in_object"]),
                body_bbox_in_object=tuple(item["body_bbox"]),
                shadow_bbox_in_object=tuple(item["shadow_bbox"]),
                control_counts=expected_controls,
                occurrences=occurrences,
                body_rgba_path=body_path,
                body_rgba_sha256=body_hash,
                high_resolution=high_resolution,
            )
        )
        seen_keys.add(key)
    if len(seen_keys) != 25 or seen_keys != set(concepts_by_key):
        raise ValueError("Approved building lifecycle does not match Marketplace concepts")
    if seen_keys != {
        f"level-{level}/tile-{source_tile}"
        for level, source_tile in high_resolution_records
    }:
        raise ValueError("Approved high-resolution authority does not match Marketplace concepts")

    ready = lifecycle.get("ready_effect", {})
    frame_mapping = tuple(ready.get("frame_to_key_phase", ()))
    if (
        tuple(ready.get("source_tiles", ())) != READY_SOURCE_TILES
        or ready.get("palette_index") != READY_PALETTE_INDEX
        or tuple(ready.get("canvas", ())) != READY_CANVAS
        or tuple(ready.get("anchor", ())) != READY_ANCHOR
        or ready.get("frame_count") != len(READY_SOURCE_TILES)
        or ready.get("key_phase_count") != 4
        or frame_mapping != (0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3)
    ):
        raise ValueError("Approved Reagents Ready lifecycle changed")
    ready_phases: list[ApprovedReadyPhase] = []
    for expected_phase, item in enumerate(ready.get("key_phases", [])):
        registered = item.get("registered_overlay_rgba", {})
        relative = registered.get("path")
        expected_hash = registered.get("sha256")
        overlay_path = root / relative
        if (
            item.get("phase") != expected_phase
            or tuple(item.get("canvas", ())) != READY_CANVAS
            or tuple(item.get("anchor", ())) != READY_ANCHOR
            or not overlay_path.is_file()
            or sha256_file(overlay_path) != expected_hash
        ):
            raise ValueError(f"Approved Reagents Ready phase changed: {expected_phase}")
        with Image.open(overlay_path) as loaded:
            overlay = loaded.copy()
        if (
            overlay.mode != "RGBA"
            or overlay.size != READY_CANVAS
            or overlay.getchannel("A").getbbox() is None
        ):
            raise ValueError(f"Approved Reagents Ready overlay changed: {expected_phase}")
        ready_phases.append(
            ApprovedReadyPhase(expected_phase, overlay_path, expected_hash)
        )
    if len(ready_phases) != 4:
        raise ValueError("Approved Reagents Ready package must contain four phases")
    return ApprovedBuildingBundle(
        root=root,
        source_imags=(source_imags[0], source_imags[1], source_imags[2]),
        states_by_level=(tuple(states[0]), tuple(states[1]), tuple(states[2])),
        ready_phases=tuple(ready_phases),
        ready_frame_to_key_phase=frame_mapping,
    )


def package_approved_building_tile(
    stock: Any,
    template: bytes,
    state: ApprovedBuildingState,
) -> bytes:
    with Image.open(state.indexed_object_path) as image:
        if image.mode != "P":
            raise ValueError(f"Approved building object is no longer indexed: {state.concept_key}")
        width, height = image.size
        flat = list(image.getdata())
    rows = [flat[y * width : (y + 1) * width] for y in range(height)]
    encoded = bytearray(
        stock.encode_indexed_v3_tile_like_original(
            template,
            rows,
            split_shadow_controls=True,
        )
    )
    if encoded[:2] != template[:2] or encoded[8:10] != template[8:10] or encoded[14:26] != template[14:26]:
        raise AssertionError(f"Approved building TILE header topology changed: {state.concept_key}")
    decoded = stock.decode_indexed_v3_tile(bytes(encoded))
    if decoded is None or decoded[2] != rows:
        raise AssertionError(f"Approved building TILE did not decode losslessly: {state.concept_key}")
    if stock.tile_palette_index(bytes(encoded)) != SOURCE_PALETTE_INDEX:
        raise AssertionError(f"Approved building TILE lost Marketplace palette: {state.concept_key}")
    if struct.unpack_from("<hh", encoded, 10) != struct.unpack_from("<hh", template, 10):
        raise AssertionError(f"Approved building TILE anchor changed: {state.concept_key}")
    return bytes(encoded)


def _palette_rgba_image(
    image: Image.Image,
    colors: Sequence[tuple[int, int, int]],
) -> Image.Image:
    """Render only visible body indices; shadow controls remain separate."""

    if image.mode != "P":
        raise ValueError("Approved building runtime source is not indexed")
    rendered_source = image.copy()
    rendered_source.putpalette(
        [channel for color in colors for channel in color]
    )
    rendered = rendered_source.convert("RGBA")
    raw_indices = Image.frombytes("L", image.size, bytes(image.getdata()))
    rendered.putalpha(
        raw_indices.point(
            [255 if 1 <= value <= 246 else 0 for value in range(256)]
        )
    )
    return rendered


def _quantize_visible_rows(
    image: Image.Image,
    colors: Sequence[tuple[int, int, int]],
    *,
    excluded_indices: frozenset[int] = frozenset(),
) -> list[list[int]]:
    """Fast no-dither quantization that reserves Majesty's control indices."""

    if excluded_indices:
        allowed_indices = [
            index for index in range(1, 247) if index not in excluded_indices
        ]
        if not allowed_indices:
            raise ValueError("Visible palette quantization has no allowed indices")
        safe_colors = [colors[index] for index in allowed_indices]
        safe_colors.extend([safe_colors[-1]] * (256 - len(safe_colors)))
        palette_image = Image.new("P", (1, 1))
        palette_image.putpalette(
            [channel for color in safe_colors for channel in color]
        )
        quantized = image.convert("RGB").quantize(
            palette=palette_image,
            dither=Image.Dither.NONE,
        )
        alpha_values = list(image.getchannel("A").getdata())
        values = list(quantized.getdata())
        width, height = image.size
        flat = [
            0
            if alpha_value < 48
            else allowed_indices[min(value, len(allowed_indices) - 1)]
            for value, alpha_value in zip(values, alpha_values)
        ]
        return [flat[y * width : (y + 1) * width] for y in range(height)]

    palette_image = Image.new("P", (1, 1))
    safe_colors = [colors[1], *colors[1:247], *([colors[246]] * 9)]
    palette_image.putpalette(
        [channel for color in safe_colors for channel in color]
    )
    quantized = image.convert("RGB").quantize(
        palette=palette_image,
        dither=Image.Dither.NONE,
    )
    alpha = image.getchannel("A")
    values = list(quantized.getdata())
    alpha_values = list(alpha.getdata())
    width, height = image.size
    flat = [
        0 if alpha_value < 48 else (1 if value == 0 else 246 if value >= 247 else value)
        for value, alpha_value in zip(values, alpha_values)
    ]
    return [flat[y * width : (y + 1) * width] for y in range(height)]


def active_glow_palette_data(stock: Any, palettes: Sequence[Any]) -> bytes:
    """Copy SPLT 68 and replace only unused visible entries with light ramps."""

    if len(palettes) != SOURCE_PALETTE_COUNT:
        raise ValueError("Stock maindata palette count changed")
    replacements = dict(
        zip(ACTIVE_GLOW_VIOLET_INDICES, ACTIVE_GLOW_VIOLET_COLORS)
    )
    replacements.update(
        zip(ACTIVE_GLOW_AMBER_INDICES, ACTIVE_GLOW_AMBER_COLORS)
    )
    return stock.splt_with_color_replacements(
        palettes[SOURCE_PALETTE_INDEX].data,
        replacements,
    )


def _registered_liquid_surface_mask(
    inactive_state: ApprovedBuildingState,
) -> Image.Image:
    """Register the frozen pool/vat surface mask on the final Lab canvas.

    This is the direct Alchemist adaptation of the Haunt's active-light rule:
    one complete, stationary authored light surface breathes over eight frames.
    The accepted active Lab rasters contain bubble drawings, not a lit master,
    so they remain provenance/control authorities but do not define the light
    mask.  Violet pixels to the right of the facade medallion are precisely the
    liquid pools, vats and small chambers in all three frozen inactive sources.
    """

    authority = inactive_state.high_resolution
    with Image.open(authority.source_path) as opened:
        if opened.mode != "RGBA":
            raise ValueError(
                "Approved high-resolution inactive Lab source is not RGBA"
            )
        source = opened.copy()
    if source.getchannel("A").getbbox() != authority.source_alpha_bbox:
        raise ValueError("Approved inactive Lab liquid authority bounds changed")

    facade_cutoff = authority.source_pool_center[0] - 50.0
    values: list[int] = []
    source_count = 0
    for y in range(source.height):
        for x in range(source.width):
            red, green, blue, alpha = source.getpixel((x, y))
            is_liquid = (
                x >= facade_cutoff
                and alpha >= 48
                and blue >= 65
                and red >= 30
                and blue * 100 > green * 118
                and red * 100 > green * 90
                and blue * 100 > red * 103
            )
            values.append(255 if is_liquid else 0)
            source_count += int(is_liquid)

    source_mask = Image.new("L", source.size, 0)
    source_mask.putdata(values)
    registered_size = (
        max(
            1,
            round(
                source.width
                * authority.fixed_group_scale
                * RUNTIME_BUILDING_SCALE
            ),
        ),
        max(
            1,
            round(
                source.height
                * authority.fixed_group_scale
                * RUNTIME_BUILDING_SCALE
            ),
        ),
    )
    registered = source_mask.resize(
        registered_size,
        Image.Resampling.LANCZOS,
    ).point([0 if value < 48 else 255 for value in range(256)])
    canvas = Image.new(
        "L",
        (
            round(inactive_state.object_canvas[0] * RUNTIME_BUILDING_SCALE),
            round(inactive_state.object_canvas[1] * RUNTIME_BUILDING_SCALE),
        ),
        0,
    )
    canvas.paste(
        registered,
        (
            round(authority.paste_offset[0] * RUNTIME_BUILDING_SCALE),
            round(authority.paste_offset[1] * RUNTIME_BUILDING_SCALE),
        ),
    )

    expected = LIQUID_MASK_EXPECTED_BY_LEVEL[inactive_state.level]
    runtime_values = list(canvas.getdata())
    runtime_count = sum(value != 0 for value in runtime_values)
    if source_count != expected["source_count"]:
        raise ValueError(
            f"Level {inactive_state.level} liquid source mask changed: "
            f"{source_count} != {expected['source_count']}"
        )
    if runtime_count != expected["runtime_count"]:
        raise ValueError(
            f"Level {inactive_state.level} runtime liquid mask changed: "
            f"{runtime_count} != {expected['runtime_count']}"
        )
    if canvas.getbbox() != expected["runtime_bbox"]:
        raise ValueError(
            f"Level {inactive_state.level} liquid mask bounds changed: "
            f"{canvas.getbbox()} != {expected['runtime_bbox']}"
        )
    return canvas


def _nearest_ramp_index(
    color: tuple[int, int, int],
    indices: Sequence[int],
    ramp: Sequence[tuple[int, int, int]],
) -> int:
    return min(
        zip(indices, ramp),
        key=lambda item: sum(
            (color[channel] - item[1][channel]) ** 2 for channel in range(3)
        ),
    )[0]


def _load_haunt_shadow_module() -> Any:
    """Load the hash-pinned Haunt building-shadow implementation verbatim."""

    global _HAUNT_SHADOW_MODULE
    if _HAUNT_SHADOW_MODULE is not None:
        return _HAUNT_SHADOW_MODULE
    source_path = (
        Path(__file__).resolve().parents[2]
        / "majesty-gold-hd-custom-guild-phantoms-haunt"
        / "scripts"
        / "generate_phantom_building_sprites.py"
    )
    if not source_path.is_file() or sha256_file(source_path) != HAUNT_SHADOW_SOURCE_SHA256:
        raise ValueError(
            "The proven Phantoms Haunt building-shadow source is missing or changed"
        )
    spec = importlib.util.spec_from_file_location(
        "alchemist_literal_haunt_building_shadow",
        source_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Haunt building-shadow source: {source_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _HAUNT_SHADOW_MODULE = module
    return module


def _haunt_shadow_parameters(
    module: Any,
    state: ApprovedBuildingState,
) -> tuple[float, float, dict[str, int]]:
    """Return the exact Haunt render-branch parameters for this lifecycle role."""

    variant = "active_0" if state.role == "active" else state.role
    shear, vertical_scale = module.shadow_profile(variant)
    kwargs: dict[str, int] = {}
    if state.role.startswith("build_"):
        stage = int(state.role.rsplit("_", 1)[1])
        kwargs = {
            "bottom_gutter": 3,
            "shadow_mask_open_size": (9, 7, 5)[stage],
            "shadow_mask_close_size": (15, 11, 7)[stage],
            "shadow_facing_depth": module.MAX_SHADOW_BODY_GAP,
            "shadow_bottom_clearance": (
                9
                if state.level in (2, 3) and stage == 0
                else (10, 0, 0)[stage]
            ),
        }
    elif state.level in (2, 3) and state.role in {
        "inactive",
        "active",
        "damaged",
        "damaged_b",
    }:
        # This is the Haunt render_variant branch for its taller upgraded art.
        shear *= 0.68
    return shear, vertical_scale, kwargs


def _literal_haunt_shadow_composite(
    visible_rows: Sequence[Sequence[int]],
    colors: Sequence[tuple[int, int, int]],
    state: ApprovedBuildingState,
) -> list[list[int]]:
    """Apply Haunt add_cast_shadow to the final quantized body literally.

    The proven Haunt function owns projection, contact repair, seam derivation,
    directional normalization, dark-edge lifting, and its internal validation.
    The validated body is requantized exactly once against the runtime palette;
    its body pixels then retain precedence over the extracted 247-250 controls.
    """

    height = len(visible_rows)
    width = len(visible_rows[0]) if visible_rows else 0
    if not width or any(len(row) != width for row in visible_rows):
        raise ValueError("Laboratory visible rows changed canvas")
    cache_key = sha256_bytes(
        struct.pack("<III", width, height, state.level)
        + state.role.encode("ascii")
        + b"\0"
        + bytes(value for row in visible_rows for value in row)
        + bytes(channel for color in colors[:247] for channel in color)
    )
    cached = _HAUNT_SHADOW_COMPOSITE_CACHE.get(cache_key)
    if cached is not None:
        return [
            list(cached[y * width : (y + 1) * width])
            for y in range(height)
        ]
    body = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = body.load()
    for y, row in enumerate(visible_rows):
        for x, value in enumerate(row):
            if 1 <= value <= 246:
                red, green, blue = colors[value]
                pixels[x, y] = (red, green, blue, 255)

    module = _load_haunt_shadow_module()
    shear, vertical_scale, kwargs = _haunt_shadow_parameters(module, state)
    projected = body.copy()
    module.add_cast_shadow(
        projected,
        shear,
        vertical_scale,
        **kwargs,
    )
    projected_pixels = projected.load()
    marker_to_index = {
        tuple(module.SHADOW_MARKERS[index]): index
        for index in sorted(CONTROL_INDICES)
    }
    flat_controls = [0] * (width * height)
    validated_rows = [list(row) for row in visible_rows]
    lit_indices = [
        index
        for index in range(1, 247)
        if (
            0.299 * colors[index][0]
            + 0.587 * colors[index][1]
            + 0.114 * colors[index][2]
        )
        >= 42
    ]
    if not lit_indices:
        raise ValueError("Laboratory runtime palette has no valid Haunt edge colors")
    for y, row in enumerate(visible_rows):
        for x, value in enumerate(row):
            if 1 <= value <= 246:
                before = colors[value]
                after = tuple(projected_pixels[x, y][:3])
                if after != before:
                    allowed_indices = lit_indices
                    if value not in ACTIVE_GLOW_VIOLET_INDICES:
                        allowed_indices = [
                            index
                            for index in lit_indices
                            if index not in ACTIVE_GLOW_VIOLET_INDICES
                            and index not in ACTIVE_GLOW_AMBER_INDICES
                        ]
                    validated_rows[y][x] = min(
                        allowed_indices,
                        key=lambda index: sum(
                            (after[channel] - colors[index][channel]) ** 2
                            for channel in range(3)
                        ),
                    )
                continue
            control = marker_to_index.get(tuple(projected_pixels[x, y]))
            if control is not None:
                flat_controls[y * width + x] = control
    control_rows = [
        flat_controls[y * width : (y + 1) * width]
        for y in range(height)
    ]
    composite = [
        [
            value if value else control_rows[y][x]
            for x, value in enumerate(row)
        ]
        for y, row in enumerate(validated_rows)
    ]
    runtime_shadow_contact_metrics(composite)
    _HAUNT_SHADOW_COMPOSITE_CACHE[cache_key] = bytes(
        value for row in composite for value in row
    )
    return composite


def runtime_shadow_contact_metrics(
    rows: Sequence[Sequence[int]],
) -> dict[str, Any]:
    """Validate the final Haunt-style shadow/body contact contract."""

    height = len(rows)
    width = len(rows[0]) if rows else 0
    if not width or any(len(row) != width for row in rows):
        raise ValueError("Laboratory runtime shadow rows changed canvas")
    classified = bytes(
        (
            value
            if value in CONTROL_INDICES
            else 1
            if 1 <= value <= 246
            else 0
        )
        for row in rows
        for value in row
    )
    cache_key = sha256_bytes(struct.pack("<II", width, height) + classified)
    cached = _RUNTIME_SHADOW_METRICS_CACHE.get(cache_key)
    if cached is not None:
        return {
            **cached,
            "control_counts": dict(cached["control_counts"]),
            "control_bbox": list(cached["control_bbox"]),
            "body_bbox": list(cached["body_bbox"]),
        }
    body = {
        (x, y)
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if 1 <= value <= 246
    }
    controls = {
        (x, y): value
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if value in CONTROL_INDICES
    }
    if not body or not controls:
        raise ValueError("Laboratory runtime TILE lost body or shadow controls")

    def neighbors8(point: tuple[int, int]):
        x, y = point
        for near_y in range(max(0, y - 1), min(height, y + 2)):
            for near_x in range(max(0, x - 1), min(width, x + 2)):
                if (near_x, near_y) != point:
                    yield near_x, near_y

    seams = {point for point, value in controls.items() if value == 247}
    bands = {
        point for point, value in controls.items() if value in (248, 249, 250)
    }
    control_component_total = 0
    connected_ground_components = 0
    detached_control_components = 0
    pending_controls = set(controls)
    while pending_controls:
        control_component_total += 1
        component: set[tuple[int, int]] = set()
        stack = [pending_controls.pop()]
        while stack:
            point = stack.pop()
            component.add(point)
            for near in neighbors8(point):
                if near in pending_controls:
                    pending_controls.remove(near)
                    stack.append(near)
        if component.intersection(seams) and component.intersection(bands):
            connected_ground_components += 1
        else:
            # Haunt's literal feather pass can leave a secondary band island.
            # Record it for provenance, but require the main grounded component
            # to contain both the body-contact seam and its 248-250 shadow band.
            detached_control_components += 1
    direct_bands = {
        point
        for point in bands
        if any(near in body for near in neighbors8(point))
    }
    edge_controls = {
        point
        for point in controls
        if point[0] in (0, width - 1) or point[1] in (0, height - 1)
    }
    control_bbox = (
        min(x for x, _y in controls),
        min(y for _x, y in controls),
        max(x for x, _y in controls) + 1,
        max(y for _x, y in controls) + 1,
    )
    transparent_sandwiches = {
        (x, y)
        for y in range(max(0, control_bbox[1] - 1), min(height, control_bbox[3] + 1))
        for x in range(max(0, control_bbox[0] - 1), min(width, control_bbox[2] + 1))
        if rows[y][x] == 0
        and any(near in body for near in neighbors8((x, y)))
        and any(near in bands for near in neighbors8((x, y)))
    }
    row_left: list[int | None] = [None] * height
    row_right: list[int | None] = [None] * height
    column_top: list[int | None] = [None] * width
    column_bottom: list[int | None] = [None] * width
    for x, y in body:
        row_left[y] = x if row_left[y] is None else min(row_left[y], x)
        row_right[y] = x if row_right[y] is None else max(row_right[y], x)
        column_top[x] = y if column_top[x] is None else min(column_top[x], y)
        column_bottom[x] = (
            y if column_bottom[x] is None else max(column_bottom[x], y)
        )
    body_envelope: set[tuple[int, int]] = set()
    envelope_notches: set[tuple[int, int]] = set()
    for y, left_edge in enumerate(row_left):
        right_edge = row_right[y]
        if left_edge is None or right_edge is None:
            continue
        for x in range(left_edge, right_edge + 1):
            top_edge = column_top[x]
            bottom_edge = column_bottom[x]
            if (
                top_edge is not None
                and bottom_edge is not None
                and top_edge <= y <= bottom_edge
            ):
                body_envelope.add((x, y))
                if rows[y][x] == 0:
                    envelope_notches.add((x, y))
    orphan_seams = {
        point
        for point in seams
        if point not in body_envelope
        and not any(near in body_envelope for near in neighbors8(point))
    }
    band_envelope_notch_violations = {
        point
        for point in bands
        if any(near in envelope_notches for near in neighbors8(point))
    }

    max_control_y = max(y for _x, y in controls)

    def hole_neighbors8(point: tuple[int, int]):
        x, y = point
        for near_y in range(max(0, y - 1), min(max_control_y + 1, y + 2)):
            for near_x in range(max(0, x - 1), min(width, x + 2)):
                if (near_x, near_y) != point:
                    yield near_x, near_y

    transparent = {
        (x, y)
        for y, row in enumerate(rows[: max_control_y + 1])
        for x, value in enumerate(row)
        if value == 0
    }
    enclosed_control_hole_count = 0
    enclosed_control_hole_pixels = 0
    enclosed_control_hole_samples: list[list[tuple[int, int]]] = []
    while transparent:
        component: set[tuple[int, int]] = set()
        stack = [transparent.pop()]
        touches_edge = False
        boundary_values: list[int] = []
        while stack:
            point = stack.pop()
            component.add(point)
            x, y = point
            if x in (0, width - 1) or y in (0, max_control_y):
                touches_edge = True
            for near in hole_neighbors8(point):
                if near in transparent:
                    transparent.remove(near)
                    stack.append(near)
                elif near not in component:
                    near_value = rows[near[1]][near[0]]
                    if near_value != 0:
                        boundary_values.append(near_value)
        if (
            not touches_edge
            and boundary_values
            and all(value in CONTROL_INDICES for value in boundary_values)
        ):
            enclosed_control_hole_count += 1
            enclosed_control_hole_pixels += len(component)
            enclosed_control_hole_samples.append(sorted(component)[:12])
    if (
        not seams
        or not bands
        or len(controls) < 100
        or orphan_seams
        or direct_bands
        or transparent_sandwiches
        or band_envelope_notch_violations
    ):
        raise ValueError(
            "Laboratory runtime shadow violates the Haunt contact contract: "
            f"seam={len(seams)} band={len(bands)} "
            f"components={control_component_total} "
            f"connected_ground={connected_ground_components} "
            f"detached={detached_control_components} "
            f"edge={len(edge_controls)} "
            f"orphan={len(orphan_seams)} "
            f"direct={len(direct_bands)} "
            f"sandwich={len(transparent_sandwiches)} "
            f"envelope_notch={len(band_envelope_notch_violations)} "
            f"enclosed_holes={enclosed_control_hole_count} "
            f"hole_points={enclosed_control_hole_samples[:2]}"
        )
    metrics = {
        "control_counts": {
            str(index): sum(value == index for value in controls.values())
            for index in sorted(CONTROL_INDICES)
        },
        "control_total": len(controls),
        "contact_seam_total": len(seams),
        "shadow_band_total": len(bands),
        "control_component_total": control_component_total,
        "connected_ground_component_total": connected_ground_components,
        "detached_control_component_total": detached_control_components,
        "control_bbox": list(control_bbox),
        "body_bbox": [
            min(x for x, _y in body),
            min(y for _x, y in body),
            max(x for x, _y in body) + 1,
            max(y for _x, y in body) + 1,
        ],
        "body_precedence": True,
        "edge_control_total": len(edge_controls),
        "direct_band_body_contact_total": len(direct_bands),
        "transparent_band_body_gap_total": len(transparent_sandwiches),
        "orphan_seam_total": len(orphan_seams),
        "band_envelope_notch_violation_total": len(
            band_envelope_notch_violations
        ),
        "enclosed_control_hole_total": enclosed_control_hole_count,
        "enclosed_control_hole_pixel_total": enclosed_control_hole_pixels,
    }
    _RUNTIME_SHADOW_METRICS_CACHE[cache_key] = metrics
    return {
        **metrics,
        "control_counts": dict(metrics["control_counts"]),
        "control_bbox": list(metrics["control_bbox"]),
        "body_bbox": list(metrics["body_bbox"]),
    }


def runtime_body_edge_metrics(
    rows: Sequence[Sequence[int]],
    colors: Sequence[tuple[int, int, int]],
) -> dict[str, Any]:
    """Enforce Haunt's opaque, luminance-42 final body-boundary rule."""

    height = len(rows)
    width = len(rows[0]) if rows else 0
    if (
        not width
        or any(len(row) != width for row in rows)
        or len(colors) < 247
    ):
        raise ValueError("Laboratory runtime body-edge inputs changed")
    body = {
        (x, y)
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if 1 <= value <= 246
    }
    if not body:
        raise ValueError("Laboratory runtime TILE lost its visible body")
    boundary: set[tuple[int, int]] = set()
    for x, y in body:
        if any(
            (near_x, near_y) not in body
            for near_y in range(max(0, y - 1), min(height, y + 2))
            for near_x in range(max(0, x - 1), min(width, x + 2))
            if (near_x, near_y) != (x, y)
        ):
            boundary.add((x, y))
    luminances = {
        point: (
            0.299 * colors[rows[point[1]][point[0]]][0]
            + 0.587 * colors[rows[point[1]][point[0]]][1]
            + 0.114 * colors[rows[point[1]][point[0]]][2]
        )
        for point in boundary
    }
    violations = {
        point: luminance
        for point, luminance in luminances.items()
        if luminance < 42
    }
    if violations:
        raise ValueError(
            "Laboratory runtime body lost Haunt's dark-edge lift: "
            f"count={len(violations)} samples={list(violations.items())[:12]}"
        )
    return {
        "boundary_pixel_total": len(boundary),
        "minimum_boundary_luminance": min(luminances.values()),
        "below_42_boundary_total": 0,
    }


def package_runtime_building_tile(
    stock: Any,
    palettes: Sequence[Any],
    template: bytes,
    state: ApprovedBuildingState,
    *,
    inactive_state: ApprovedBuildingState | None = None,
    pulse_factor: float | None = None,
) -> bytes:
    """Render approved r14 detail once at final size and preserve v2 controls."""

    with Image.open(state.indexed_object_path) as loaded:
        indexed = loaded.copy()
    if indexed.mode != "P" or indexed.size != state.object_canvas:
        raise ValueError(f"Approved building object changed: {state.concept_key}")

    colors = stock.splt_palette_colors(palettes[SOURCE_PALETTE_INDEX].data)
    target_size = (
        round(indexed.width * RUNTIME_BUILDING_SCALE),
        round(indexed.height * RUNTIME_BUILDING_SCALE),
    )
    if pulse_factor is not None:
        if inactive_state is None:
            raise ValueError("Active Lab pulse is missing its inactive authority")
        baseline = _render_high_resolution_body(
            inactive_state.high_resolution,
            inactive_state.object_canvas,
            RUNTIME_BUILDING_SCALE,
        )
        liquid_mask = _registered_liquid_surface_mask(inactive_state)
        rows = _quantize_visible_rows(
            baseline,
            colors,
            excluded_indices=frozenset(
                (*ACTIVE_GLOW_VIOLET_INDICES, *ACTIVE_GLOW_AMBER_INDICES)
            ),
        )
        baseline_pixels = baseline.load()
        liquid_pixels = liquid_mask.load()
        for y in range(target_size[1]):
            for x in range(target_size[0]):
                if not liquid_pixels[x, y]:
                    continue
                red, green, blue, alpha = baseline_pixels[x, y]
                if alpha < 48:
                    continue
                base_position = min(
                    range(len(ACTIVE_GLOW_VIOLET_COLORS)),
                    key=lambda position: sum(
                        (
                            (red, green, blue)[channel]
                            - ACTIVE_GLOW_VIOLET_COLORS[position][channel]
                        )
                        ** 2
                        for channel in range(3)
                    ),
                )
                lifted_position = min(
                    len(ACTIVE_GLOW_VIOLET_COLORS) - 1,
                    base_position + ACTIVE_GLOW_RAMP_LIFT_STEPS,
                )
                lifted = ACTIVE_GLOW_VIOLET_COLORS[lifted_position]
                desired = (
                    min(255, round(lifted[0] * pulse_factor)),
                    min(255, round(lifted[1] * pulse_factor)),
                    min(255, round(lifted[2] * pulse_factor)),
                )
                rows[y][x] = _nearest_ramp_index(
                    desired,
                    ACTIVE_GLOW_VIOLET_INDICES,
                    ACTIVE_GLOW_VIOLET_COLORS,
                )
        runtime_colors = stock.splt_palette_colors(
            active_glow_palette_data(stock, palettes)
        )
    else:
        visible = _render_high_resolution_body(
            state.high_resolution,
            state.object_canvas,
            RUNTIME_BUILDING_SCALE,
        )
        rows = _quantize_visible_rows(visible, colors)
        runtime_colors = colors

    rows = _literal_haunt_shadow_composite(rows, runtime_colors, state)
    runtime_body_edge_metrics(rows, runtime_colors)
    runtime_hotspot, _ground_alignment = marketplace_ground_aligned_hotspot(
        stock,
        template,
        rows,
    )

    encoded = (
        stock.encode_indexed_v3_tile_like_original(
            template,
            rows,
            split_shadow_controls=True,
        )
    )
    if pulse_factor is not None:
        encoded = stock.remap_tile_palette_index(
            encoded, ACTIVE_GLOW_PALETTE_INDEX
        )
    encoded = bytearray(encoded)
    struct.pack_into("<hh", encoded, 10, *runtime_hotspot)
    expected_palette = (
        ACTIVE_GLOW_PALETTE_INDEX
        if pulse_factor is not None
        else SOURCE_PALETTE_INDEX
    )
    if stock.tile_palette_index(bytes(encoded)) != expected_palette:
        raise AssertionError("Scaled Lab TILE lost its private palette contract")
    decoded = stock.decode_indexed_v3_tile(bytes(encoded))
    if decoded is None:
        raise AssertionError("Scaled Lab TILE no longer decodes")
    runtime_shadow_contact_metrics(decoded[2])
    return bytes(encoded)


def package_approved_ready_tile(
    stock: Any,
    palettes: Sequence[Any],
    phase: ApprovedReadyPhase,
) -> bytes:
    """Encode one accepted full-canvas Ready overlay without transforming it."""
    with Image.open(phase.overlay_path) as loaded:
        overlay = loaded.copy()
    if overlay.mode != "RGBA" or overlay.size != READY_CANVAS:
        raise ValueError(f"Approved Reagents Ready phase changed: {phase.phase}")
    encoded = stock.rgba_to_indexed_tile(
        overlay,
        palettes,
        READY_PALETTE_INDEX,
        READY_HEADER,
    )
    if struct.unpack_from("<hh", encoded, 10) != READY_ANCHOR:
        raise AssertionError("Approved Reagents Ready output anchor changed")
    return encoded


def package_runtime_ready_tile(
    stock: Any,
    palettes: Sequence[Any],
    phase: ApprovedReadyPhase,
) -> bytes:
    """Scale the registered ready overlay with the enlarged Lab owner."""

    with Image.open(phase.overlay_path) as loaded:
        overlay = loaded.convert("RGBA")
    target_size = (
        round(READY_CANVAS[0] * RUNTIME_BUILDING_SCALE),
        round(READY_CANVAS[1] * RUNTIME_BUILDING_SCALE),
    )
    overlay = overlay.resize(target_size, Image.Resampling.LANCZOS)
    hotspot = (
        round(READY_ANCHOR[0] * RUNTIME_BUILDING_SCALE),
        round(READY_ANCHOR[1] * RUNTIME_BUILDING_SCALE),
    )
    colors = stock.splt_palette_colors(palettes[READY_PALETTE_INDEX].data)
    rows = _quantize_visible_rows(overlay, colors)
    return stock.encode_indexed_v3_tile(
        rows,
        READY_PALETTE_INDEX,
        header_words=(
            3,
            target_size[1],
            target_size[0],
            target_size[0],
            32,
            *hotspot,
            8,
        ),
    )


def _frame_reference_offset(
    imag: bytes,
    set_order: int,
    expected_set_id: int,
    track_order: int,
    frame_order: int,
) -> int:
    set_count = _u32(imag, 20)
    if not (0 <= set_order < set_count):
        raise ValueError("Marketplace IMAG set order is out of range")
    table_offset = 24 + set_order * 8
    set_id = _u32(imag, table_offset)
    set_start = _u32(imag, table_offset + 4)
    if set_id != expected_set_id:
        raise ValueError(
            f"Marketplace IMAG set {set_order} changed: {set_id:#010x} != {expected_set_id:#010x}"
        )
    set_end = (
        _u32(imag, table_offset + 12)
        if set_order + 1 < set_count
        else len(imag)
    )
    direction_count = _u32(imag, set_start)
    direction_offsets = [
        _u32(imag, set_start + 64 + direction * 4)
        for direction in range(direction_count)
    ]
    current_track = 0
    for direction, relative in enumerate(direction_offsets):
        direction_start = set_start + relative
        direction_end = (
            set_start + direction_offsets[direction + 1]
            if direction + 1 < direction_count
            else set_end
        )
        count_word = _u32(imag, direction_start + 4)
        frame_count = count_word >> 16
        stream_count = count_word & 0xFFFF
        frame_table = direction_end - frame_count * stream_count * 8
        for stream in range(stream_count):
            if current_track == track_order:
                if not (0 <= frame_order < frame_count):
                    raise ValueError("Marketplace IMAG frame order is out of range")
                return frame_table + stream * frame_count * 8 + frame_order * 8 + 4
            current_track += 1
    raise ValueError("Marketplace IMAG track order is out of range")


def _imag_set_chunk(imag: bytes, expected_set_id: int) -> bytes:
    set_count = _u32(imag, 20)
    entries = [
        (_u32(imag, 24 + index * 8), _u32(imag, 28 + index * 8))
        for index in range(set_count)
    ]
    matches = [
        (index, start)
        for index, (set_id, start) in enumerate(entries)
        if set_id == expected_set_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Marketplace IMAG set {expected_set_id:#x} is missing or ambiguous"
        )
    order, start = matches[0]
    end = entries[order + 1][1] if order + 1 < len(entries) else len(imag)
    return imag[start:end]


def _single_frame_reference_for_set(imag: bytes, expected_set_id: int) -> int:
    set_count = _u32(imag, 20)
    orders = [
        order
        for order in range(set_count)
        if _u32(imag, 24 + order * 8) == expected_set_id
    ]
    if len(orders) != 1:
        raise ValueError(
            f"Marketplace IMAG set {expected_set_id:#x} is missing or ambiguous"
        )
    offset = _frame_reference_offset(
        imag,
        orders[0],
        expected_set_id,
        0,
        0,
    )
    return _u32(imag, offset)


def patch_approved_building_imag(
    source_imag: bytes,
    states: Sequence[ApprovedBuildingState],
    private_indices: dict[int, int],
    profile_index: int,
    icon_index: int,
) -> bytes:
    patched = bytearray(source_imag)
    changed_offsets: set[int] = set()

    def patch_occurrence(
        set_order: int,
        set_id: int,
        track_order: int,
        frame_order: int,
        source_tile: int,
        private_tile: int,
    ) -> None:
        offset = _frame_reference_offset(
            source_imag, set_order, set_id, track_order, frame_order
        )
        before = _u32(source_imag, offset)
        if before & 0xFFFF != source_tile:
            raise ValueError(
                f"Marketplace occurrence changed at {offset}: {before & 0xFFFF} != {source_tile}"
            )
        if offset in changed_offsets:
            raise ValueError(f"Marketplace occurrence was patched twice at {offset}")
        struct.pack_into("<I", patched, offset, (before & 0xFFFF0000) | private_tile)
        changed_offsets.add(offset)

    for set_order, set_id, track_order, frame_order, source_tile in SOURCE_INTERFACE_OCCURRENCES:
        patch_occurrence(
            set_order,
            set_id,
            track_order,
            frame_order,
            source_tile,
            profile_index if source_tile == 990 else icon_index,
        )
    for state in states:
        private_tile = private_indices[state.source_tile_index]
        for occurrence in state.occurrences:
            patch_occurrence(
                occurrence["set_order"],
                occurrence["set_id"],
                occurrence["track_order"],
                occurrence["frame_order"],
                occurrence["reference_word"] & 0xFFFF,
                private_tile,
            )
    expected_changes = 2 + sum(len(state.occurrences) for state in states)
    if len(changed_offsets) != expected_changes:
        raise AssertionError(
            f"Marketplace IMAG expected {expected_changes} private references, got {len(changed_offsets)}"
        )
    for offset in range(len(source_imag)):
        if offset in changed_offsets or offset - 1 in changed_offsets or offset - 2 in changed_offsets or offset - 3 in changed_offsets:
            continue
        if patched[offset] != source_imag[offset]:
            raise AssertionError(f"Marketplace IMAG changed outside authorized reference words at {offset}")
    return bytes(patched)


def expand_marketplace_active_animation(
    imag: bytes,
    set_id: int,
    tile_indices: Sequence[int],
) -> bytes:
    """Apply the Haunt's active-frame expansion to Marketplace's shorter set.

    Fervus stores eight additional bytes of state metadata before its one-frame
    table; Marketplace does not.  Locate the frame table from the stock counts
    rather than using the Fervus-specific 112-byte prefix, then preserve the
    complete Marketplace prefix and first-frame metadata verbatim.
    """

    if not tile_indices:
        raise ValueError("Marketplace active animation has no frames")
    set_count = _u32(imag, 20)
    entries = [
        (_u32(imag, 24 + index * 8), _u32(imag, 28 + index * 8))
        for index in range(set_count)
    ]
    matches = [index for index, (current, _offset) in enumerate(entries) if current == set_id]
    if len(matches) != 1:
        raise ValueError(f"Marketplace active set {set_id:#x} is missing or ambiguous")
    position = matches[0]
    set_start = entries[position][1]
    set_end = entries[position + 1][1] if position + 1 < set_count else len(imag)
    direction_count = _u32(imag, set_start)
    if direction_count != 1:
        raise ValueError("Marketplace active set lost its one-direction topology")
    direction_start = set_start + _u32(imag, set_start + 64)
    count_word = _u32(imag, direction_start + 4)
    source_frame_count = count_word >> 16
    stream_count = count_word & 0xFFFF
    if source_frame_count != 1 or stream_count != 1:
        raise ValueError("Marketplace active set lost its one-frame/one-stream topology")
    frame_table = set_end - 8
    if frame_table < direction_start or frame_table + 8 != set_end:
        raise ValueError("Marketplace active frame table is malformed")

    old_chunk = imag[set_start:set_end]
    prefix_length = frame_table - set_start + 4
    new_chunk = bytearray(old_chunk[:prefix_length])
    struct.pack_into("<H", new_chunk, direction_start - set_start + 6, len(tile_indices))
    new_chunk += struct.pack("<I", tile_indices[0])
    for tile_index in tile_indices[1:]:
        new_chunk += b"\x00\x00\x00\x00"
        new_chunk += struct.pack("<I", tile_index)

    delta = len(new_chunk) - len(old_chunk)
    patched = bytearray(imag[:set_start] + bytes(new_chunk) + imag[set_end:])
    for index, (_current, offset) in enumerate(entries):
        if offset > set_start:
            struct.pack_into("<I", patched, 28 + index * 8, offset + delta)
    return bytes(patched)


def validate_packaged_approved_building_cam(
    stock: Any,
    output_cam: Path,
    stock_tiles: Sequence[Any],
    stock_palettes: Sequence[Any],
    bundle: ApprovedBuildingBundle,
    private_indices_by_level: Sequence[dict[int, int]],
    profile_index: int,
    icon_index: int,
    output_imag_names: Sequence[bytes],
    records: Sequence[dict[str, Any]],
) -> None:
    """Fail closed on the scaled private Marketplace/Haunt-style clone."""

    from approved_sprite_bundle import validate_split_control_segments

    if (
        len(private_indices_by_level) != 3
        or len(output_imag_names) != 3
    ):
        raise ValueError("Approved building package must contain three levels")
    output_tiles = stock.read_cam_entries(output_cam, b"TILE")
    output_palettes = stock.read_cam_entries(output_cam, b"SPLT")
    if (
        len(output_palettes) <= SOURCE_PALETTE_INDEX
        or output_palettes[SOURCE_PALETTE_INDEX].data
        != stock_palettes[SOURCE_PALETTE_INDEX].data
    ):
        raise ValueError("Approved building package changed Marketplace palette 68")
    if (
        len(output_palettes) <= ACTIVE_GLOW_PALETTE_INDEX
        or output_palettes[ACTIVE_GLOW_PALETTE_INDEX].data
        != active_glow_palette_data(stock, stock_palettes)
    ):
        raise ValueError("Approved building package lost its private active palette")

    records_by_private = {record["private_tile_index"]: record for record in records}
    if len(records_by_private) != 25:
        raise ValueError("Approved building package does not contain 25 private states")
    seen_private: set[int] = set()
    for states, private_indices in zip(
        bundle.states_by_level, private_indices_by_level
    ):
        inactive_states = [state for state in states if state.role == "inactive"]
        if len(inactive_states) != 1:
            raise ValueError("Approved Lab level lost its inactive pulse authority")
        inactive_state = inactive_states[0]
        if set(private_indices) != {state.source_tile_index for state in states}:
            raise ValueError("Approved building private TILE map is incomplete")
        for state in states:
            private_index = private_indices[state.source_tile_index]
            if private_index in seen_private or private_index >= len(output_tiles):
                raise ValueError("Approved building private TILE index is invalid")
            seen_private.add(private_index)
            entry = output_tiles[private_index]
            expected_prefix = (
                f"ALB{state.level}Act" if state.role == "active"
                else f"ALB{state.level}State"
            ).encode("ascii")
            if not entry.name.rstrip(b"\x00").startswith(expected_prefix):
                raise ValueError("Approved building private TILE name changed")
            record = records_by_private.get(private_index)
            if record is None or sha256_bytes(entry.data) != record["packaged_tile_sha256"]:
                raise ValueError(f"Approved building TILE changed: {state.concept_key}")
            frame_indices = record["active_frame_private_indices"]
            expected_factors = (
                ACTIVE_PULSE_FACTORS if state.role == "active" else (None,)
            )
            if len(frame_indices) != len(expected_factors):
                raise ValueError("Approved building active-frame count changed")
            source_hotspot = struct.unpack_from(
                "<hh", stock_tiles[state.source_tile_index].data, 10
            )
            if tuple(
                pool - hotspot
                for pool, hotspot in zip(
                    state.high_resolution.target_pool_center,
                    source_hotspot,
                )
            ) != LAB_OWNER_TO_POOL_DISPLACEMENT:
                raise ValueError("Approved building owner-to-pool anchor changed")
            expected_canvas = tuple(
                round(value * RUNTIME_BUILDING_SCALE)
                for value in state.object_canvas
            )
            active_mask_points: set[tuple[int, int]] = set()
            active_outside_reference: tuple[int, ...] | None = None
            active_shadow_reference: bytes | None = None
            if state.role == "active":
                liquid_mask = _registered_liquid_surface_mask(inactive_state)
                liquid_pixels = liquid_mask.load()
                active_mask_points = {
                    (x, y)
                    for y in range(liquid_mask.height)
                    for x in range(liquid_mask.width)
                    if liquid_pixels[x, y]
                }
            for frame, (frame_index, pulse_factor) in enumerate(
                zip(frame_indices, expected_factors)
            ):
                frame_entry = output_tiles[frame_index]
                expected_payload = package_runtime_building_tile(
                    stock,
                    stock_palettes,
                    stock_tiles[state.source_tile_index].data,
                    state,
                    inactive_state=(
                        inactive_state if pulse_factor is not None else None
                    ),
                    pulse_factor=pulse_factor,
                )
                if frame_entry.data != expected_payload:
                    raise ValueError(
                        f"Approved building runtime frame changed: "
                        f"{state.concept_key}/{frame}"
                    )
                expected_palette = (
                    ACTIVE_GLOW_PALETTE_INDEX
                    if pulse_factor is not None
                    else SOURCE_PALETTE_INDEX
                )
                if stock.tile_palette_index(frame_entry.data) != expected_palette:
                    raise ValueError("Approved building private TILE lost its palette")
                decoded = stock.decode_indexed_v3_tile(frame_entry.data)
                if decoded is None or (decoded[1], decoded[0]) != expected_canvas:
                    raise ValueError("Approved building runtime canvas changed")
                frame_colors = stock.splt_palette_colors(
                    output_palettes[expected_palette].data
                )
                runtime_body_edge_metrics(decoded[2], frame_colors)
                runtime_shadow = runtime_shadow_contact_metrics(decoded[2])
                if runtime_shadow["shadow_band_total"] <= 0:
                    raise ValueError("Approved building shadow lost its grounded band")
                expected_hotspot, ground_alignment = (
                    marketplace_ground_aligned_hotspot(
                        stock,
                        stock_tiles[state.source_tile_index].data,
                        decoded[2],
                    )
                )
                if ground_alignment != record["runtime_ground_alignment"]:
                    raise ValueError("Approved building ground alignment changed")
                shadow_plane = bytes(
                    value if value in CONTROL_INDICES else 0
                    for row in decoded[2]
                    for value in row
                )
                if sha256_bytes(shadow_plane) != record[
                    "runtime_shadow_control_plane_sha256"
                ]:
                    raise ValueError("Approved building shadow plane changed across frames")
                if pulse_factor is not None:
                    violet_points = {
                        (x, y)
                        for y, row in enumerate(decoded[2])
                        for x, value in enumerate(row)
                        if value in ACTIVE_GLOW_VIOLET_INDICES
                    }
                    if not violet_points:
                        raise ValueError("Approved Lab active liquid mask is empty")
                    expected_liquid = LIQUID_MASK_EXPECTED_BY_LEVEL[state.level]
                    violet_bbox = (
                        min(x for x, _y in violet_points),
                        min(y for _x, y in violet_points),
                        max(x for x, _y in violet_points) + 1,
                        max(y for _x, y in violet_points) + 1,
                    )
                    if (
                        violet_points != active_mask_points
                        or len(violet_points) != expected_liquid["runtime_count"]
                        or violet_bbox != expected_liquid["runtime_bbox"]
                        or any(
                            value in ACTIVE_GLOW_AMBER_INDICES
                            for row in decoded[2]
                            for value in row
                        )
                    ):
                        raise ValueError(
                            "Approved Lab active frame escaped its complete liquid mask"
                        )
                    outside_mask = tuple(
                        value
                        for y, row in enumerate(decoded[2])
                        for x, value in enumerate(row)
                        if (x, y) not in active_mask_points
                    )
                    if active_outside_reference is None:
                        active_outside_reference = outside_mask
                        active_shadow_reference = shadow_plane
                    elif (
                        outside_mask != active_outside_reference
                        or shadow_plane != active_shadow_reference
                    ):
                        raise ValueError(
                            "Approved Lab active pulse moved art outside its liquid surfaces"
                        )
                if struct.unpack_from("<hh", frame_entry.data, 10) != expected_hotspot:
                    raise ValueError("Approved building runtime anchor changed")
                validate_split_control_segments(frame_entry.data)
            if state.role == "active":
                frame_payloads = [output_tiles[index].data for index in frame_indices]
                for first, second in ((0, 4), (1, 3), (5, 7)):
                    if frame_payloads[first] != frame_payloads[second]:
                        raise ValueError("Approved Lab active pulse lost Haunt cadence symmetry")

    if seen_private != set(records_by_private):
        raise ValueError("Approved building provenance contains an unbound TILE")

    output_image_names = {
        entry.name.rstrip(b"\x00") for entry in stock.read_cam_entries(output_cam, b"IMAG")
    }
    if any(name in output_image_names for name in SOURCE_IMAG_NAMES):
        raise ValueError("Approved building package emitted a retail Marketplace IMAG")
    for level, (source_imag, states, private_indices, output_name) in enumerate(
        zip(
            bundle.source_imags,
            bundle.states_by_level,
            private_indices_by_level,
            output_imag_names,
        ),
        start=1,
    ):
        expected = patch_approved_building_imag(
            source_imag,
            states,
            private_indices,
            profile_index,
            icon_index,
        )
        records_by_source = {
            record["source_tile_index"]: record
            for record in records
            if record["level"] == level
        }
        for state in states:
            if state.role != "active":
                continue
            for occurrence in state.occurrences:
                expected = expand_marketplace_active_animation(
                    expected,
                    occurrence["set_id"],
                    records_by_source[state.source_tile_index][
                        "active_frame_private_indices"
                    ],
                )
        actual = stock.read_cam_entry(output_cam, b"IMAG", output_name).data
        if actual != expected:
            raise ValueError(
                f"Approved building level {level} changed its Marketplace/Haunt topology"
            )
        if _imag_set_chunk(actual, HOTSPOT_SET_ID) != _imag_set_chunk(
            source_imag,
            HOTSPOT_SET_ID,
        ):
            raise ValueError("Approved Lab privatized Marketplace set 400")
        hotspot_tile = (
            _single_frame_reference_for_set(actual, HOTSPOT_SET_ID) & 0xFFFF
        )
        if hotspot_tile != SOURCE_HOTSPOT_TILES[level - 1]:
            raise ValueError("Approved Lab changed Marketplace Hotspot TILE ownership")
        inactive_states = [state for state in states if state.role == "inactive"]
        if len(inactive_states) != 1:
            raise ValueError("Approved Lab lost its unique inactive state")
        inactive_tile = (
            _single_frame_reference_for_set(actual, INACTIVE_SET_ID) & 0xFFFF
        )
        expected_inactive_tile = private_indices[
            inactive_states[0].source_tile_index
        ]
        if inactive_tile != expected_inactive_tile or inactive_tile == hotspot_tile:
            raise ValueError(
                "Approved Lab no longer separates stock Hotspot and private inactive TILEs"
            )
