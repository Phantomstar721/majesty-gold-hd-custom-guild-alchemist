from __future__ import annotations

from dataclasses import dataclass
import hashlib
import inspect
import json
from pathlib import Path
import struct
from typing import Any, Sequence

from PIL import Image


DIRECTION_ORDER = (
    "north",
    "northeast",
    "east",
    "southeast",
    "south",
    "southwest",
    "west",
    "northwest",
)
WALK_START = 5919
WALK_END = 5983
STAND_START = 5983
STAND_END = 5991
APPROVED_SLOT_START = WALK_START
APPROVED_SLOT_END = STAND_END
UNTOUCHED_WARRIOR_SLOT_RANGES = ((5991, 6053), (6055, 6119))
EXPECTED_REMAPPED_IMAG_OFFSETS = (
    0x1C8,
    *(
        0x630 + direction * 0x58 + frame * 8
        for direction in range(8)
        for frame in range(8)
    ),
    *(0x960 + direction * 0x30 for direction in range(8)),
)
INTERFACE_SOURCE_SLOTS = (6053, 6054, 5411)
EXPECTED_INTERFACE_IMAG_OFFSETS = {
    6053: 0x14C,
    6054: 0x22C,
    5411: 0x290,
}

NATIVE_CANVAS = (96, 92)
NATIVE_ROOT = (48, 70)
ALPHA_THRESHOLD = 128
LOCAL_UNRESOLVED_PALETTE_REF = 0xFFFFFFFF
EXPECTED_RETAIL_SPLT_COUNT = 854

RETAIL_MAINDATA_SHA256 = (
    "92b1a4caa111495aebe483e5617c7cc4f291eb1d897877860cfbdbc632a0d213"
)
WARRIOR_IMAG_SHA256 = (
    "2aec8bc57ebbb385daf46a4d4fa0abbf6563e0be4adb232003a7a6418ed829ba"
)
WALK_CHECKPOINT_SHA256 = (
    "1d7340a4e3588fed7e0ce5c30b398b27d224122cbb94720db3e92988082c34f9"
)
STAND_CHECKPOINT_SHA256 = (
    "9ee4d85617cb63d4a5a775b4dafc605c7808c039ab372c1f44437d1742b39783"
)
WALK_PROVENANCE_SHA256 = (
    "f3c70bf14d593580065bdfb4ec1139592d12d1e14d413f678b91f2151482d76e"
)
STAND_PROVENANCE_SHA256 = (
    "257446bee7a248848b06fd67757ebe79c0096cd1f92460f974dcd8407e6adf3e"
)
PALETTE_MANIFEST_SHA256 = (
    "0b5d73b0e17aea6f82fd278c09ca966f280d689c0a1907ade93d9f34cdb58d60"
)
PALETTE_CONTENT_SHA256 = (
    "cd5b84c48cb6531d4610037e9509928cd048b5db036d1f4c61221f4b23061647"
)

CONTROL_RGB = {
    247: (156, 33, 24),
    248: (178, 0, 178),
    249: (204, 0, 204),
    250: (229, 0, 229),
}
CONTROL_INDICES = frozenset(CONTROL_RGB)
STRONG_CORE_NAMES = ("red", "green", "blue", "steel")
PROJECTED_SHADOW_FUNCTION_SHA256 = (
    "57477d9ec6c6a35ef2607facc780bd110a4322137183726a722d34c86cc97eb4"
)
EXPECTED_SHADOW_TOTALS = {
    "projected": 15073,
    "body_conflicts": 15,
    "retained": 15058,
}
EXPECTED_RETAINED_SHADOW_BANDS = {
    247: 8247,
    248: 1830,
    249: 3631,
    250: 1350,
}
EXPECTED_CONFLICT_SHADOW_BANDS = {
    247: 3,
    248: 5,
    249: 6,
    250: 1,
}


@dataclass(frozen=True)
class ApprovedSpriteBundle:
    private_palette_index: int
    private_palette_data: bytes
    tiles_by_stock_slot: dict[int, bytes]
    records: tuple[dict[str, Any], ...]
    source_hashes: dict[str, str]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_sha256(path: Path, expected: str, label: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{label} is missing: {path}")
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(
            f"{label} SHA-256 changed: expected {expected}, found {actual}: {path}"
        )
    return actual


def palette_content_sha256(colours: Sequence[tuple[int, int, int]]) -> str:
    payload = json.dumps([list(colour) for colour in colours], separators=(",", ":"))
    return sha256_bytes(payload.encode("ascii"))


def _load_json(path: Path, expected_sha256: str, label: str) -> dict[str, Any]:
    require_sha256(path, expected_sha256, label)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return value


def _validate_rgb(value: object, label: str) -> tuple[int, int, int]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label} must be a three-channel RGB list")
    channels = tuple(value)
    if any(not isinstance(channel, int) or not 0 <= channel <= 255 for channel in channels):
        raise ValueError(f"{label} contains an invalid RGB channel: {value!r}")
    return channels  # type: ignore[return-value]


def _load_visible_palette(manifest: dict[str, Any]) -> tuple[tuple[int, int, int], ...]:
    if manifest.get("schema") != "majesty-alchemist-candidate-palette-v3":
        raise ValueError("Approved palette manifest schema changed")
    if manifest.get("game_loadable") is not False:
        raise ValueError("Approved local palette manifest unexpectedly claims to be loadable")
    if manifest.get("tile_palette_reference") != "0xFFFFFFFF unresolved local sentinel":
        raise ValueError("Approved palette sentinel contract changed")

    raw_entries = manifest.get("visible_entries")
    if not isinstance(raw_entries, list) or len(raw_entries) != 246:
        raise ValueError("Approved palette must contain exactly 246 visible entries")
    visible: list[tuple[int, int, int]] = []
    for expected_index, entry in enumerate(raw_entries, 1):
        if not isinstance(entry, dict) or entry.get("index") != expected_index:
            raise ValueError("Approved palette visible indices are not contiguous 1..246")
        visible.append(_validate_rgb(entry.get("rgb"), f"palette index {expected_index}"))

    if palette_content_sha256(visible) != PALETTE_CONTENT_SHA256:
        raise ValueError("Approved visible palette content hash changed")
    raw_controls = manifest.get("reserved_controls")
    expected_controls = [
        {"index": index, "rgb": list(CONTROL_RGB[index])}
        for index in sorted(CONTROL_RGB)
    ]
    if raw_controls != expected_controls:
        raise ValueError("Approved palette control colours changed")
    return tuple(visible)


def build_private_splt(
    stock_palette_template: bytes,
    visible_colours: Sequence[tuple[int, int, int]],
) -> bytes:
    """Clone the stock SPLT record shape and replace only its 256 RGB values."""

    if len(stock_palette_template) < 8 + 256 * 4:
        raise ValueError("Stock SPLT template is truncated")
    entries = [(0, 0, 0)] * 256
    for index, colour in enumerate(visible_colours, 1):
        entries[index] = colour
    for index, colour in CONTROL_RGB.items():
        entries[index] = colour

    output = bytearray(stock_palette_template)
    for index, colour in enumerate(entries):
        offset = 8 + index * 4
        output[offset : offset + 3] = bytes(colour)
    return bytes(output)


def strong_core(pixel: tuple[int, int, int], name: str) -> bool:
    """Literal approved indexed-pilot strong-core classifier."""

    red, green, blue = pixel
    if name == "red":
        return red > 100 and red > 2.0 * green and red > 1.5 * blue
    if name == "green":
        return green > 100 and green > 1.8 * red and green > 1.5 * blue
    if name == "blue":
        return blue > 100 and blue > 1.8 * red and blue > 1.5 * green
    if name == "steel":
        return min(pixel) > 160 and max(pixel) - min(pixel) < 45
    raise ValueError(name)


def nearest_visible_index(
    rgb: tuple[int, int, int],
    visible_colours: Sequence[tuple[int, int, int]],
    cache: dict[tuple[int, int, int], int],
) -> int:
    cached = cache.get(rgb)
    if cached is not None:
        return cached
    source_core = next(
        (name for name in STRONG_CORE_NAMES if strong_core(rgb, name)),
        None,
    )
    eligible = [
        index
        for index in range(1, len(visible_colours) + 1)
        if source_core is None or strong_core(visible_colours[index - 1], source_core)
    ]
    if not eligible:
        raise ValueError(f"Approved palette has no {source_core} strong-core entry")
    red, green, blue = rgb
    best_index = min(
        eligible,
        key=lambda index: (
            (red - visible_colours[index - 1][0]) ** 2
            + (green - visible_colours[index - 1][1]) ** 2
            + (blue - visible_colours[index - 1][2]) ** 2,
            index,
        ),
    )
    cache[rgb] = best_index
    return best_index


def rgba_to_indices(
    image: Image.Image,
    visible_colours: Sequence[tuple[int, int, int]],
    alpha_threshold: int = ALPHA_THRESHOLD,
) -> bytes:
    cache: dict[tuple[int, int, int], int] = {}
    indices = bytearray()
    for red, green, blue, alpha in image.convert("RGBA").getdata():
        if alpha < alpha_threshold:
            indices.append(0)
        else:
            indices.append(
                nearest_visible_index((red, green, blue), visible_colours, cache)
            )
    if any(index in CONTROL_INDICES or index > 246 for index in indices):
        raise ValueError("Ordinary Stand conversion emitted a reserved palette index")
    return bytes(indices)


def _tile_indices(stock: Any, tile: bytes) -> bytes:
    decoded = stock.decode_indexed_v3_tile(tile)
    if decoded is None:
        raise ValueError("Approved payload is not an indexed TILE-v3 record")
    height, width, rows = decoded
    if (width, height) != NATIVE_CANVAS:
        raise ValueError(f"Approved TILE canvas changed: {(width, height)}")
    return bytes(index for row in rows for index in row)


def _tile_rows(stock: Any, tile: bytes) -> list[list[int]]:
    decoded = stock.decode_indexed_v3_tile(tile)
    if decoded is None:
        raise ValueError("Approved payload is not an indexed TILE-v3 record")
    height, width, rows = decoded
    if (width, height) != NATIVE_CANVAS:
        raise ValueError(f"Approved TILE canvas changed: {(width, height)}")
    return [list(row) for row in rows]


def _control_plane(rows: Sequence[Sequence[int]]) -> bytes:
    return bytes(
        value if value in CONTROL_INDICES else 0
        for row in rows
        for value in row
    )


def _visible_body_plane(rows: Sequence[Sequence[int]]) -> bytes:
    return bytes(
        0 if value in CONTROL_INDICES else value
        for row in rows
        for value in row
    )


def validate_split_control_segments(tile: bytes) -> None:
    """Reject mixed body/control RLE runs in a generated TILE-v3 payload."""

    if len(tile) < 26 or struct.unpack_from("<H", tile, 0)[0] != 3:
        raise ValueError("Shadow-bearing payload is not TILE v3")
    height = struct.unpack_from("<H", tile, 2)[0]
    offset_base = 26
    if offset_base + height * 4 > len(tile):
        raise ValueError("Shadow-bearing TILE row table is truncated")
    offsets = [
        struct.unpack_from("<I", tile, offset_base + row * 4)[0]
        for row in range(height)
    ]
    for row_index, row_offset in enumerate(offsets):
        start = offset_base + row_offset
        end = (
            offset_base + offsets[row_index + 1]
            if row_index + 1 < height
            else len(tile)
        )
        if not offset_base <= start <= end <= len(tile):
            raise ValueError("Shadow-bearing TILE has an invalid row offset")
        position = start
        saw_final = False
        while position + 4 <= end:
            count = tile[position + 2]
            flags = tile[position + 3]
            position += 4
            values = tile[position : position + count]
            if len(values) != count:
                raise ValueError("Shadow-bearing TILE row segment is truncated")
            position += count
            if any(value > 250 for value in values):
                raise ValueError("Shadow-bearing TILE uses forbidden indices 251..255")
            has_body = any(1 <= value <= 246 for value in values)
            has_control = any(value in CONTROL_INDICES for value in values)
            if has_body and has_control:
                raise ValueError("TILE RLE segment mixes visible and shadow-control pixels")
            if flags & 0x80:
                saw_final = True
                break
        if not saw_final:
            raise ValueError("Shadow-bearing TILE row has no final segment")
        if position != end:
            raise ValueError("Shadow-bearing TILE row has trailing bytes")


def project_approved_shadow_controls(
    stock: Any,
    approved_tile: bytes,
    palette_colours: Sequence[tuple[int, int, int]],
) -> tuple[bytes, dict[str, Any]]:
    """Derive Majesty control bands from the approved Alchemist silhouette.

    This is the exact body-derived hero-shadow path already used by the proven
    Phantoms/regular-Alchemist packer.  It authors Majesty's real 247..250 TILE
    controls while avoiding the Warrior shield/sword shapes that a literal mask
    transplant would retain.  Body indices, registration, and canvas are fixed.
    """

    algorithm_sha256 = sha256_bytes(
        inspect.getsource(stock.projected_floating_hero_shadow).encode("utf-8")
    )
    if algorithm_sha256 != PROJECTED_SHADOW_FUNCTION_SHA256:
        raise ValueError("Proven body-derived hero-shadow algorithm changed")
    approved_decoded = stock.decode_indexed_v3_tile(approved_tile)
    if approved_decoded is None:
        raise ValueError("Approved shadow projection requires an indexed TILE-v3 record")
    approved_height, approved_width, approved_rows = approved_decoded
    if (approved_width, approved_height) != NATIVE_CANVAS:
        raise ValueError("Shadow projection changed the approved native canvas")
    if len(palette_colours) < 251:
        raise ValueError("Shadow projection palette is incomplete")
    if any(
        value in CONTROL_INDICES or value > 246
        for row in approved_rows
        for value in row
    ):
        raise ValueError("Shadow projection target must contain body indices 0..246 only")
    if struct.unpack_from("<HH", approved_tile, 10) != NATIVE_ROOT:
        raise ValueError("Shadow projection target hotspot changed")

    caster = Image.new("RGBA", NATIVE_CANVAS, (0, 0, 0, 0))
    caster.putdata(
        [
            (*palette_colours[value], 255) if value else (0, 0, 0, 0)
            for row in approved_rows
            for value in row
        ]
    )
    projected_rows = stock.projected_floating_hero_shadow(caster, 1.0)
    if len(projected_rows) != approved_height or any(
        len(row) != approved_width for row in projected_rows
    ):
        raise ValueError("Body-derived shadow projection changed the canvas")
    if any(
        value != 0 and value not in CONTROL_INDICES
        for row in projected_rows
        for value in row
    ):
        raise ValueError("Body-derived shadow emitted a non-control palette index")

    target_rows = [list(row) for row in approved_rows]
    projected_counts = {index: 0 for index in sorted(CONTROL_INDICES)}
    retained_counts = {index: 0 for index in sorted(CONTROL_INDICES)}
    conflict_counts = {index: 0 for index in sorted(CONTROL_INDICES)}
    for y, row in enumerate(projected_rows):
        for x, value in enumerate(row):
            if value == 0:
                continue
            projected_counts[value] += 1
            if target_rows[y][x] != 0:
                conflict_counts[value] += 1
                continue
            target_rows[y][x] = value
            retained_counts[value] += 1

    projected_total = sum(projected_counts.values())
    conflict_total = sum(conflict_counts.values())
    retained_total = sum(retained_counts.values())
    if not projected_total or not retained_total:
        raise ValueError("Approved frame has no retained body-derived shadow")
    if projected_total != conflict_total + retained_total:
        raise AssertionError("Body-derived shadow pixel accounting is incomplete")

    encoded = stock.encode_indexed_v3_tile_like_original(
        approved_tile,
        target_rows,
        split_shadow_controls=True,
    )
    # The proven helper normalizes header word 3 to the canvas width. These
    # approved fixtures deliberately retain word 3 == 0, so restore that
    # non-row header field after the split-run encoding.
    output_bytes = bytearray(encoded)
    output_bytes[6:8] = approved_tile[6:8]
    output = bytes(output_bytes)
    if output[:26] != approved_tile[:26]:
        raise AssertionError("Shadow projection changed TILE geometry/hotspot/palette")
    if _tile_rows(stock, output) != target_rows:
        raise AssertionError("Shadow projection TILE does not decode exactly")
    validate_split_control_segments(output)
    stats: dict[str, Any] = {
        "algorithm": "projected_floating_hero_shadow",
        "algorithm_source_sha256": algorithm_sha256,
        "caster_body_sha256": sha256_bytes(_visible_body_plane(approved_rows)),
        "projected_control_counts": {str(k): v for k, v in projected_counts.items()},
        "projected_control_total": projected_total,
        "body_conflict_counts": {str(k): v for k, v in conflict_counts.items()},
        "body_conflict_total": conflict_total,
        "retained_control_counts": {str(k): v for k, v in retained_counts.items()},
        "retained_control_total": retained_total,
        "projected_control_sha256": sha256_bytes(_control_plane(projected_rows)),
        "retained_control_sha256": sha256_bytes(_control_plane(target_rows)),
    }
    return output, stats


def _patch_walk_palette(tile: bytes, private_palette_index: int) -> bytes:
    if len(tile) < 26 or struct.unpack_from("<H", tile, 0)[0] != 3:
        raise ValueError("Approved Walk payload is not TILE v3")
    if struct.unpack_from("<H", tile, 20)[0] != 0:
        raise ValueError("Approved Walk TILE no longer uses an external SPLT")
    if struct.unpack_from("<I", tile, 22)[0] != LOCAL_UNRESOLVED_PALETTE_REF:
        raise ValueError("Approved Walk TILE no longer has the local palette sentinel")
    output = bytearray(tile)
    struct.pack_into("<I", output, 22, private_palette_index)
    if output[:22] != tile[:22] or output[26:] != tile[26:]:
        raise AssertionError("Walk palette patch changed bytes outside the palette reference")
    return bytes(output)


def _encode_stand_tile(
    stock: Any,
    image: Image.Image,
    visible_colours: Sequence[tuple[int, int, int]],
    private_palette_index: int,
) -> tuple[bytes, bytes]:
    if image.size != NATIVE_CANVAS:
        raise ValueError(f"Approved Stand canvas changed: {image.size}")
    indices = rgba_to_indices(image, visible_colours)
    width, height = NATIVE_CANVAS
    rows = [list(indices[y * width : (y + 1) * width]) for y in range(height)]
    tile = stock.encode_indexed_v3_tile(
        rows,
        private_palette_index,
        (3, height, width, 0, 32, NATIVE_ROOT[0], NATIVE_ROOT[1], 1),
    )
    if _tile_indices(stock, tile) != indices:
        raise AssertionError("Encoded Stand TILE does not decode to the quantized pixels")
    return tile, indices


def _expected_walk_records(report: dict[str, Any]) -> list[dict[str, Any]]:
    indexed = report.get("indexed")
    if not isinstance(indexed, dict):
        raise ValueError("Walk provenance has no indexed contract")
    if indexed.get("coverage_threshold") != ALPHA_THRESHOLD:
        raise ValueError("Walk alpha threshold changed")
    if indexed.get("palette_content_sha256") != PALETTE_CONTENT_SHA256:
        raise ValueError("Walk provenance palette hash changed")
    records = indexed.get("records")
    if not isinstance(records, list) or len(records) != 64:
        raise ValueError("Walk provenance must contain exactly 64 indexed records")
    return records


def load_approved_sprite_bundle(
    sprite_pipeline_root: Path,
    stock: Any,
    stock_cam: Path,
    stock_tiles: Sequence[Any],
    stock_palettes: Sequence[Any],
    warrior_imag: bytes,
) -> ApprovedSpriteBundle:
    """Load and gate the accepted Walk V4 and Stand V5 test assets.

    The local Walk TILEs are already the approved canonical indexed payloads;
    making them loadable changes only the four-byte palette reference. Stand
    follows that same accepted alpha128 mapping and palette, then uses the
    proven stock TILE-v3 encoder on the shared 96x92/48,70 registration.
    """

    sprite_pipeline_root = sprite_pipeline_root.resolve()
    walk_checkpoint_path = (
        sprite_pipeline_root / "references" / "alchemist-walk-full-v4-checkpoint.json"
    )
    stand_checkpoint_path = (
        sprite_pipeline_root / "references" / "alchemist-stand-v5-checkpoint.json"
    )
    walk_report_path = (
        sprite_pipeline_root
        / "output"
        / "mixamo-walk-full-gate-v4-review"
        / "full-walk-gate-provenance.json"
    )
    stand_report_path = (
        sprite_pipeline_root
        / "output"
        / "mixamo-stand-gate-v5-review-v3"
        / "stand-gate-provenance.json"
    )
    palette_path = walk_report_path.parent / "indexed" / "candidate-palette.json"

    if sha256_file(stock_cam) != RETAIL_MAINDATA_SHA256:
        raise ValueError("Installed maindata.cam does not match the approved retail authority")
    if sha256_bytes(warrior_imag) != WARRIOR_IMAG_SHA256:
        raise ValueError("Stock AVL1Warrior IMAG changed from the approved authority")
    if len(stock_palettes) != EXPECTED_RETAIL_SPLT_COUNT:
        raise ValueError(
            f"Retail SPLT table changed: expected {EXPECTED_RETAIL_SPLT_COUNT}, "
            f"found {len(stock_palettes)}"
        )

    walk_checkpoint = _load_json(
        walk_checkpoint_path, WALK_CHECKPOINT_SHA256, "Walk V4 checkpoint"
    )
    stand_checkpoint = _load_json(
        stand_checkpoint_path, STAND_CHECKPOINT_SHA256, "Stand V5 checkpoint"
    )
    walk_report = _load_json(
        walk_report_path, WALK_PROVENANCE_SHA256, "Walk V4 provenance"
    )
    stand_report = _load_json(
        stand_report_path, STAND_PROVENANCE_SHA256, "Stand V5 provenance"
    )
    palette_manifest = _load_json(
        palette_path, PALETTE_MANIFEST_SHA256, "Walk V4 candidate palette"
    )
    visible_colours = _load_visible_palette(palette_manifest)

    if walk_checkpoint.get("checkpoint_id") != "alchemist-walk-full-v4":
        raise ValueError("Walk checkpoint identity changed")
    if walk_checkpoint.get("approval_status") != "accepted_for_ingame_test":
        raise ValueError("Walk checkpoint is not approved for an in-game test")
    stock_contract = walk_checkpoint.get("stock_contract", {})
    if stock_contract.get("direction_order") != list(DIRECTION_ORDER):
        raise ValueError("Walk checkpoint direction order changed")
    if stock_contract.get("tile_range") != [WALK_START, WALK_END - 1]:
        raise ValueError("Walk checkpoint TILE range changed")
    motion_contract = walk_checkpoint.get("motion_contract", {})
    if motion_contract.get("native_canvas") != list(NATIVE_CANVAS):
        raise ValueError("Walk checkpoint native canvas changed")
    if motion_contract.get("root_hotspot") != list(NATIVE_ROOT):
        raise ValueError("Walk checkpoint root hotspot changed")
    indexed_contract = walk_checkpoint.get("indexed_contract", {})
    if indexed_contract.get("palette_content_sha256") != PALETTE_CONTENT_SHA256:
        raise ValueError("Walk checkpoint palette content changed")

    if stand_checkpoint.get("checkpoint_id") != "alchemist-stand-v5":
        raise ValueError("Stand checkpoint identity changed")
    stand_contract = stand_checkpoint.get("stock_contract", {})
    if stand_contract.get("direction_order") != list(DIRECTION_ORDER):
        raise ValueError("Stand checkpoint direction order changed")
    if stand_contract.get("warrior_stand_tiles") != list(range(STAND_START, STAND_END)):
        raise ValueError("Stand checkpoint TILE order changed")

    private_palette_index = len(stock_palettes)
    private_palette_data = build_private_splt(
        stock_palettes[427].data, visible_colours
    )
    if stock.splt_palette_colors(private_palette_data)[1:247] != list(visible_colours):
        raise AssertionError("Private SPLT does not contain the approved visible palette")
    private_colours = stock.splt_palette_colors(private_palette_data)
    if any(private_colours[index] != CONTROL_RGB[index] for index in CONTROL_RGB):
        raise AssertionError("Private SPLT lost its reserved control colours")

    tiles_by_stock_slot: dict[int, bytes] = {}
    output_records: list[dict[str, Any]] = []
    shadow_totals = {
        "projected": 0,
        "body_conflicts": 0,
        "retained": 0,
    }
    retained_shadow_bands = {index: 0 for index in sorted(CONTROL_INDICES)}
    conflict_shadow_bands = {index: 0 for index in sorted(CONTROL_INDICES)}

    def record_shadow_stats(stats: dict[str, Any]) -> None:
        shadow_totals["projected"] += stats["projected_control_total"]
        shadow_totals["body_conflicts"] += stats["body_conflict_total"]
        shadow_totals["retained"] += stats["retained_control_total"]
        for index in sorted(CONTROL_INDICES):
            retained_shadow_bands[index] += stats["retained_control_counts"][str(index)]
            conflict_shadow_bands[index] += stats["body_conflict_counts"][str(index)]

    walk_records = _expected_walk_records(walk_report)
    expected_artifacts = {
        record["path"]: record
        for record in walk_report.get("artifacts", [])
        if isinstance(record, dict) and isinstance(record.get("path"), str)
    }
    for ordinal, record in enumerate(walk_records):
        direction_index, frame = divmod(ordinal, 8)
        direction = DIRECTION_ORDER[direction_index]
        stock_slot = WALK_START + ordinal
        expected_path = (
            f"output/mixamo-walk-full-gate-v4-review/indexed/frames/{direction}/"
            f"frame-{frame:02d}-a128.tile"
        )
        if (
            record.get("direction") != direction
            or record.get("slot") != direction_index
            or record.get("frame") != frame
            or record.get("tile_path") != expected_path
        ):
            raise ValueError(f"Walk indexed record order changed at ordinal {ordinal}")
        tile_path = sprite_pipeline_root / Path(expected_path)
        expected_hash = record.get("tile_sha256")
        if not isinstance(expected_hash, str):
            raise ValueError(f"Walk record {ordinal} has no TILE hash")
        require_sha256(tile_path, expected_hash, f"Walk {direction} frame {frame}")
        artifact = expected_artifacts.get(expected_path)
        if artifact is None or artifact.get("sha256") != expected_hash:
            raise ValueError(f"Walk artifact table disagrees for {expected_path}")
        source_tile = tile_path.read_bytes()
        source_indices = _tile_indices(stock, source_tile)
        if any(index > 246 for index in source_indices):
            raise ValueError(f"Walk {direction} frame {frame} uses a reserved index")
        patched_tile = _patch_walk_palette(source_tile, private_palette_index)
        if _tile_indices(stock, patched_tile) != source_indices:
            raise AssertionError("Walk palette patch changed decoded pixels")
        shadowed_tile, shadow_stats = project_approved_shadow_controls(
            stock,
            patched_tile,
            private_colours,
        )
        record_shadow_stats(shadow_stats)
        tiles_by_stock_slot[stock_slot] = shadowed_tile
        output_records.append(
            {
                "kind": "walk",
                "stock_slot": stock_slot,
                "direction": direction,
                "frame": frame,
                "source": expected_path,
                "source_sha256": expected_hash,
                "indexed_pixel_sha256": sha256_bytes(source_indices),
                "full_indexed_pixel_sha256": sha256_bytes(
                    _tile_indices(stock, shadowed_tile)
                ),
                "shadow": shadow_stats,
                "packaged_tile_sha256": sha256_bytes(shadowed_tile),
            }
        )

    stand_frames = stand_report.get("frames")
    stand_hashes = stand_report.get("output_sha256")
    if not isinstance(stand_frames, list) or len(stand_frames) != 8:
        raise ValueError("Stand provenance must contain exactly eight frames")
    if not isinstance(stand_hashes, dict):
        raise ValueError("Stand provenance has no output hash table")
    for slot, direction in enumerate(DIRECTION_ORDER):
        stock_slot = STAND_START + slot
        record = stand_frames[slot]
        expected_path = f"native/{direction}/alchemist-soft-b.png"
        if (
            record.get("direction") != direction
            or record.get("slot") != slot
            or record.get("warrior_tile") != stock_slot
            or record.get("native", {}).get("alchemist_soft_b") != expected_path
        ):
            raise ValueError(f"Stand record order changed at slot {slot}")
        expected_hash = stand_hashes.get(expected_path)
        if not isinstance(expected_hash, str):
            raise ValueError(f"Stand provenance has no hash for {expected_path}")
        image_path = stand_report_path.parent / Path(expected_path)
        require_sha256(image_path, expected_hash, f"Stand {direction}")
        with Image.open(image_path) as loaded:
            image = loaded.convert("RGBA")
        tile, indices = _encode_stand_tile(
            stock, image, visible_colours, private_palette_index
        )
        shadowed_tile, shadow_stats = project_approved_shadow_controls(
            stock,
            tile,
            private_colours,
        )
        record_shadow_stats(shadow_stats)
        tiles_by_stock_slot[stock_slot] = shadowed_tile
        output_records.append(
            {
                "kind": "stand",
                "stock_slot": stock_slot,
                "direction": direction,
                "frame": 0,
                "source": (
                    "output/mixamo-stand-gate-v5-review-v3/" + expected_path
                ),
                "source_sha256": expected_hash,
                "indexed_pixel_sha256": sha256_bytes(indices),
                "full_indexed_pixel_sha256": sha256_bytes(
                    _tile_indices(stock, shadowed_tile)
                ),
                "shadow": shadow_stats,
                "packaged_tile_sha256": sha256_bytes(shadowed_tile),
            }
        )

    if sorted(tiles_by_stock_slot) != list(range(APPROVED_SLOT_START, APPROVED_SLOT_END)):
        raise AssertionError("Approved sprite bundle does not cover exactly 5919..5990")
    if shadow_totals != EXPECTED_SHADOW_TOTALS:
        raise ValueError(
            f"Approved body-derived shadow totals changed: {shadow_totals!r}"
        )
    if retained_shadow_bands != EXPECTED_RETAINED_SHADOW_BANDS:
        raise ValueError(
            "Approved retained body-derived shadow bands changed: "
            f"{retained_shadow_bands!r}"
        )
    if conflict_shadow_bands != EXPECTED_CONFLICT_SHADOW_BANDS:
        raise ValueError(
            "Approved body-conflict shadow bands changed: "
            f"{conflict_shadow_bands!r}"
        )

    # The exact retail CAM hash already protects every source TILE, but check
    # the Stand per-TILE hashes carried by the approval report as a local
    # direction/order guard as well.
    warrior_records = stand_report.get("stock", {}).get("warrior_records", [])
    if len(warrior_records) != 8:
        raise ValueError("Stand stock authority record count changed")
    for slot, record in enumerate(warrior_records):
        stock_slot = STAND_START + slot
        if record.get("tile") != stock_slot:
            raise ValueError("Stand stock authority TILE order changed")
        if sha256_bytes(stock_tiles[stock_slot].data) != record.get("tile_sha256"):
            raise ValueError(f"Stock Stand TILE {stock_slot} changed")

    source_hashes = {
        "retail_maindata.cam": RETAIL_MAINDATA_SHA256,
        "AVL1Warrior IMAG": WARRIOR_IMAG_SHA256,
        "references/alchemist-walk-full-v4-checkpoint.json": WALK_CHECKPOINT_SHA256,
        "references/alchemist-stand-v5-checkpoint.json": STAND_CHECKPOINT_SHA256,
        "output/mixamo-walk-full-gate-v4-review/full-walk-gate-provenance.json": WALK_PROVENANCE_SHA256,
        "output/mixamo-walk-full-gate-v4-review/indexed/candidate-palette.json": PALETTE_MANIFEST_SHA256,
        "output/mixamo-stand-gate-v5-review-v3/stand-gate-provenance.json": STAND_PROVENANCE_SHA256,
    }
    return ApprovedSpriteBundle(
        private_palette_index=private_palette_index,
        private_palette_data=private_palette_data,
        tiles_by_stock_slot=tiles_by_stock_slot,
        records=tuple(output_records),
        source_hashes=source_hashes,
    )


def remap_approved_warrior_imag(
    stock: Any,
    warrior_imag: bytes,
    replacements: dict[int, int],
) -> bytes:
    if sorted(replacements) != list(range(APPROVED_SLOT_START, APPROVED_SLOT_END)):
        raise ValueError("Warrior replacement map must contain exactly 5919..5990")
    patched = stock.remap_imag_low16_tile_indices(warrior_imag, replacements)
    changed_offsets: list[int] = []
    expected_offsets: list[int] = []
    for offset in range(0, len(warrior_imag) - 3, 4):
        before = struct.unpack_from("<I", warrior_imag, offset)[0]
        after = struct.unpack_from("<I", patched, offset)[0]
        source_slot = before & 0xFFFF
        if APPROVED_SLOT_START <= source_slot < APPROVED_SLOT_END:
            expected_offsets.append(offset)
            expected = (before & 0xFFFF0000) | replacements[source_slot]
            if after != expected:
                raise AssertionError(f"Warrior IMAG target at {offset} was not remapped exactly")
        elif before != after:
            changed_offsets.append(offset)
    if changed_offsets:
        raise AssertionError(
            f"Warrior IMAG changed outside approved slots: {changed_offsets[:8]}"
        )
    if not expected_offsets:
        raise ValueError("Warrior IMAG contains no approved Walk/Stand references")
    if tuple(expected_offsets) != EXPECTED_REMAPPED_IMAG_OFFSETS:
        raise ValueError(
            "Warrior Walk/Stand IMAG offsets changed from the audited 73-reference layout"
        )

    for start, end in UNTOUCHED_WARRIOR_SLOT_RANGES:
        for offset in range(0, len(warrior_imag) - 3, 4):
            before = struct.unpack_from("<I", warrior_imag, offset)[0]
            if start <= (before & 0xFFFF) < end:
                after = struct.unpack_from("<I", patched, offset)[0]
                if after != before:
                    raise AssertionError(
                        f"Warrior stock action reference changed at IMAG offset {offset}"
                    )
    return patched


def validate_packaged_approved_sprite_cam(
    stock: Any,
    output_cam: Path,
    stock_tiles: Sequence[Any],
    stock_palettes: Sequence[Any],
    warrior_imag: bytes,
    bundle: ApprovedSpriteBundle,
    private_tile_indices: dict[int, int],
    interface_tile_indices: dict[int, int],
    interface_records: Sequence[dict[str, Any]],
) -> None:
    """Re-read the emitted CAM and prove the narrow stock clone survived I/O."""

    output_palettes = stock.read_cam_entries(output_cam, b"SPLT")
    if len(output_palettes) != bundle.private_palette_index + 1:
        raise ValueError("Packaged SPLT table does not end at the private palette")
    if output_palettes[bundle.private_palette_index].data != bundle.private_palette_data:
        raise ValueError("Packaged private SPLT differs from the approved palette")
    private_colours = stock.splt_palette_colors(bundle.private_palette_data)
    # Untouched Warrior actions still reference retail SPLT 427, so its
    # fall-through companion must remain a literal stock palette record.
    if output_palettes[427].data != stock_palettes[427].data:
        raise ValueError("Packaged CAM changed the stock Warrior SPLT 427")

    output_tiles = stock.read_cam_entries(output_cam, b"TILE")
    first_private = len(stock_tiles)
    if any(entry.data for entry in output_tiles[:first_private]):
        raise ValueError("Packaged CAM overwrites a retail TILE slot")
    if sorted(private_tile_indices.values()) != list(
        range(first_private, first_private + (APPROVED_SLOT_END - APPROVED_SLOT_START))
    ):
        raise ValueError("Approved private TILEs were not the first appended block")
    if tuple(interface_tile_indices) != INTERFACE_SOURCE_SLOTS:
        raise ValueError("Approved interface TILE mapping is incomplete or reordered")
    if list(interface_tile_indices.values()) != list(
        range(len(output_tiles) - len(INTERFACE_SOURCE_SLOTS), len(output_tiles))
    ):
        raise ValueError("Approved interface TILEs were not appended at the table end")
    if len(interface_records) != len(INTERFACE_SOURCE_SLOTS):
        raise ValueError("Approved interface provenance is incomplete")

    records_by_slot = {record["stock_slot"]: record for record in bundle.records}
    for stock_slot, private_index in sorted(private_tile_indices.items()):
        if private_index >= len(output_tiles):
            raise ValueError(f"Packaged private TILE {private_index} is missing")
        payload = output_tiles[private_index].data
        record = records_by_slot[stock_slot]
        if sha256_bytes(payload) != record["packaged_tile_sha256"]:
            raise ValueError(f"Packaged TILE for stock slot {stock_slot} changed")
        if struct.unpack_from("<H", payload, 20)[0] != 0:
            raise ValueError(f"Packaged TILE for stock slot {stock_slot} embeds a palette")
        if struct.unpack_from("<I", payload, 22)[0] != bundle.private_palette_index:
            raise ValueError(
                f"Packaged TILE for stock slot {stock_slot} uses the wrong SPLT"
            )
        packaged_rows = _tile_rows(stock, payload)
        packaged_indices = bytes(value for row in packaged_rows for value in row)
        if sha256_bytes(_visible_body_plane(packaged_rows)) != record["indexed_pixel_sha256"]:
            raise ValueError(f"Packaged TILE body pixels changed for stock slot {stock_slot}")
        if sha256_bytes(packaged_indices) != record["full_indexed_pixel_sha256"]:
            raise ValueError(f"Packaged TILE full index plane changed for stock slot {stock_slot}")
        if any(index > 250 for index in packaged_indices):
            raise ValueError(
                f"Packaged hero TILE for stock slot {stock_slot} uses index 251..255"
            )
        if not any(index in CONTROL_INDICES for index in packaged_indices):
            raise ValueError(f"Packaged hero TILE for stock slot {stock_slot} has no shadow")
        validate_split_control_segments(payload)

        body_rows = [
            [0 if value in CONTROL_INDICES else value for value in row]
            for row in packaged_rows
        ]
        body_tile = stock.encode_indexed_v3_tile_like_original(
            payload,
            body_rows,
            split_shadow_controls=True,
        )
        expected_tile, expected_shadow = project_approved_shadow_controls(
            stock,
            body_tile,
            private_colours,
        )
        if _tile_rows(stock, expected_tile) != packaged_rows:
            raise ValueError(
                f"Packaged body-derived shadow changed for stock slot {stock_slot}"
            )
        if expected_shadow != record["shadow"]:
            raise ValueError(
                f"Packaged body-derived shadow provenance changed for stock slot {stock_slot}"
            )

    records_by_interface_slot = {
        record["source_stock_slot"]: record for record in interface_records
    }
    if tuple(records_by_interface_slot) != INTERFACE_SOURCE_SLOTS:
        raise ValueError("Approved interface provenance order changed")
    for source_slot, private_index in interface_tile_indices.items():
        record = records_by_interface_slot[source_slot]
        if record["private_tile_index"] != private_index:
            raise ValueError("Approved interface provenance TILE mapping changed")
        payload = output_tiles[private_index].data
        if not payload:
            raise ValueError(f"Approved interface TILE {private_index} is empty")
        if sha256_bytes(payload) != record["packaged_tile_sha256"]:
            raise ValueError(f"Approved interface TILE {private_index} changed")
        if len(payload) < 16 or struct.unpack_from("<H", payload, 0)[0] != 1:
            raise ValueError(f"Approved interface TILE {private_index} is not TILE v1")
        height, width = struct.unpack_from("<HH", payload, 2)
        if [width, height] != record["canvas"]:
            raise ValueError(f"Approved interface TILE {private_index} canvas changed")
        if stock.tile_palette_index(payload) != record["palette_index"]:
            raise ValueError(f"Approved interface TILE {private_index} palette changed")

    packaged_imag = stock.read_cam_entry(
        output_cam, b"IMAG", b"ALC1Alchemist"
    ).data
    expected_imag = remap_approved_warrior_imag(
        stock, warrior_imag, private_tile_indices
    )
    expected_imag = stock.remap_imag_low16_tile_indices(
        expected_imag,
        interface_tile_indices,
    )
    if packaged_imag != expected_imag:
        raise ValueError(
            "Packaged ALC1 IMAG differs from the audited Walk/Stand/interface remap"
        )
    for source_slot, expected_offset in EXPECTED_INTERFACE_IMAG_OFFSETS.items():
        before = struct.unpack_from("<I", warrior_imag, expected_offset)[0]
        after = struct.unpack_from("<I", packaged_imag, expected_offset)[0]
        if (before & 0xFFFF) != source_slot:
            raise ValueError(f"Stock interface IMAG offset changed for TILE {source_slot}")
        expected = (before & 0xFFFF0000) | interface_tile_indices[source_slot]
        if after != expected:
            raise ValueError(f"Private interface IMAG offset changed for TILE {source_slot}")

    # Unapproved animation placeholders stay empty so unchanged ALC1 refs fall
    # through to stock action art. The three interface frames above are private
    # appended copies and do not populate any retail slot.
    for start, end in UNTOUCHED_WARRIOR_SLOT_RANGES:
        if any(output_tiles[index].data for index in range(start, end)):
            raise ValueError(
                f"Packaged CAM contains private art in untouched stock range {start}..{end - 1}"
            )


def package_provenance(
    bundle: ApprovedSpriteBundle,
    private_tile_indices: dict[int, int],
    interface_tile_indices: dict[int, int],
    interface_records: Sequence[dict[str, Any]],
    output_cam: Path,
) -> dict[str, Any]:
    if sorted(private_tile_indices) != list(range(APPROVED_SLOT_START, APPROVED_SLOT_END)):
        raise ValueError("Packaged private TILE mapping is incomplete")
    records = []
    for record in bundle.records:
        item = dict(record)
        item["private_tile_index"] = private_tile_indices[item["stock_slot"]]
        records.append(item)
    return {
        "schema": "majesty-alchemist-approved-sprite-test-set-v1",
        "scope": "local compiled package; not deployed",
        "cache_policy": "fresh build; regular art cache bypassed and not updated",
        "stock_clone": {
            "source_imag": "AVL1Warrior",
            "private_imag": "ALC1Alchemist",
            "remapped_stock_slots": [APPROVED_SLOT_START, APPROVED_SLOT_END - 1],
            "interface_remapped_stock_slots": list(INTERFACE_SOURCE_SLOTS),
            "untouched_stock_slot_ranges": [
                [start, end - 1] for start, end in UNTOUCHED_WARRIOR_SLOT_RANGES
            ],
            "direction_order": list(DIRECTION_ORDER),
            "walk_frames_per_direction": 8,
            "stand_frames_per_direction": 1,
            "runtime_timing": "inherited byte-for-byte from stock AVL1Warrior IMAG",
        },
        "palette": {
            "private_splt_index": bundle.private_palette_index,
            "retail_splt_count": EXPECTED_RETAIL_SPLT_COUNT,
            "visible_palette_content_sha256": PALETTE_CONTENT_SHA256,
            "visible_indices": [1, 246],
            "reserved_controls": {
                str(index): list(colour) for index, colour in CONTROL_RGB.items()
            },
        },
        "shadows": {
            "authority": "proven Phantoms body-derived Majesty control-mask pipeline",
            "algorithm": "projected_floating_hero_shadow",
            "algorithm_source_sha256": PROJECTED_SHADOW_FUNCTION_SHA256,
            "output_indices": [247, 250],
            "body_precedence": "approved visible indices 1..246 win on overlap",
            "body_contract": "no crop, recenter, scale, palette, or visible-index changes",
            "expected_totals": EXPECTED_SHADOW_TOTALS,
            "expected_retained_bands": {
                str(index): count
                for index, count in EXPECTED_RETAINED_SHADOW_BANDS.items()
            },
            "expected_body_conflict_bands": {
                str(index): count
                for index, count in EXPECTED_CONFLICT_SHADOW_BANDS.items()
            },
        },
        "source_hashes": bundle.source_hashes,
        "frames": records,
        "interface_frames": [dict(record) for record in interface_records],
        "output": {
            "maindata_cam": "Data/alchemist_maindata.cam",
            "maindata_cam_sha256": sha256_file(output_cam),
        },
    }
