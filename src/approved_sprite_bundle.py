from __future__ import annotations

from dataclasses import dataclass
import hashlib
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
COMPLETED_HANDOFF_MANIFEST_SHA256 = (
    "4fb60e6cc838ab8a2ed12c667f8f403fd0a5e877b05e4663a4774daea38164ff"
)
COMPLETED_HANDOFF_AGGREGATE_SHA256 = (
    "b4be60597ee06d61a2f785c706b40aed3bccfd0cf395a777977abcb5bd3dcb53"
)
COMPLETED_HANDOFF_AUTHORITY_SHA256 = (
    "66759658dfb06ff1fb87330d9d8966b31c326fc38b26546711d8ac719b7e529b"
)
COMPLETED_ACTION_COUNTS = {
    "walk": 64,
    "stand": 8,
    "attack": 64,
    "cast": 56,
    "special": 56,
    "death": 32,
    "dead": 1,
}
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
GROUNDED_SHADOW_POLICY = "stock-warrior-contact+phantoms-seam-v1"
GROUNDED_SHADOW_POLICY_SHA256 = (
    "acc40e1f2beb74f6cebfdf1e687c4cb2607ed79359192e16b396a5bb9cc6e5ec"
)
PHANTOMS_SHADOW_CONTRACT_COMMIT = (
    "1ac887f55e4c1c67dc8d90829cb099eea87b15ae"
)
PHANTOMS_SHADOW_CONTRACT_PATH = "docs/majesty-building-shadow-encoding.md"
EXPECTED_SHADOW_TOTALS = {
    "projected": 21171,
    "body_conflicts": 3732,
    "retained_projected": 17439,
    "direct_seam": 3057,
    "gap_fill_seam": 366,
    "retained": 17805,
    "ground_contact_seam": 2061,
}
EXPECTED_PROJECTED_SHADOW_BANDS = {
    247: 0,
    248: 10216,
    249: 8755,
    250: 2200,
}
EXPECTED_RETAINED_SHADOW_BANDS = {
    247: 3423,
    248: 7387,
    249: 5526,
    250: 1469,
}
EXPECTED_CONFLICT_SHADOW_BANDS = {
    247: 0,
    248: 1706,
    249: 1639,
    250: 387,
}
EXPECTED_CONTROL_PLANE_SHA256 = (
    "2723c6f8a55880ac0f5ab57d2f81f08da462b9b65663c58cf96e26770c3af890"
)
EXPECTED_FULL_INDEX_PLANE_SHA256 = (
    "6172a1e92fcde51b760363f8fd8b8524363b71a166953908c293cbdd08c68b45"
)
EXPECTED_BODY_PLANE_SHA256 = (
    "661f18fd2833ccd805a53a440919e20a95b5fbb93ef7fde910183a24ed7a937d"
)
EXPECTED_FRAME_HASH_LIST_SHA256 = {
    "projected_control": "de01d522c16a7ad7f3642ad70b4f816a237618a5a7cacee99db7f2c74f6dd65d",
    "retained_control": "8e1e85d82db0c57f6f1f8b4b8986e2314dad9bbc1b7d708300271231bb85d4ec",
    "full": "e8d4b85eb76a98c70f7ff0e3f3c2938ec0e267fbdca44f6df26991dd785bc26d",
    "body": "203a485528ac8fb0906ffc5519f7f1d3f24c590ce0a2c6564d59e0d3aac5ef8e",
}


@dataclass(frozen=True)
class ApprovedSpriteBundle:
    private_palette_index: int
    private_palette_data: bytes
    tiles_by_stock_slot: dict[int, bytes]
    records: tuple[dict[str, Any], ...]
    source_hashes: dict[str, str]
    imag_patches: tuple[dict[str, Any], ...] = ()
    handoff_manifest_sha256: str | None = None


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


def _tile_indices(
    stock: Any, tile: bytes, expected_canvas: tuple[int, int] = NATIVE_CANVAS
) -> bytes:
    decoded = stock.decode_indexed_v3_tile(tile)
    if decoded is None:
        raise ValueError("Approved payload is not an indexed TILE-v3 record")
    height, width, rows = decoded
    if (width, height) != expected_canvas:
        raise ValueError(f"Approved TILE canvas changed: {(width, height)}")
    return bytes(index for row in rows for index in row)


def _tile_rows(
    stock: Any, tile: bytes, expected_canvas: tuple[int, int] = NATIVE_CANVAS
) -> list[list[int]]:
    decoded = stock.decode_indexed_v3_tile(tile)
    if decoded is None:
        raise ValueError("Approved payload is not an indexed TILE-v3 record")
    height, width, rows = decoded
    if (width, height) != expected_canvas:
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


def _neighbors8(
    width: int,
    height: int,
    x: int,
    y: int,
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (neighbor_x, neighbor_y)
        for neighbor_y in range(max(0, y - 1), min(height, y + 2))
        for neighbor_x in range(max(0, x - 1), min(width, x + 2))
        if (neighbor_x, neighbor_y) != (x, y)
    )


def _control_component_sizes(rows: Sequence[Sequence[int]]) -> tuple[int, ...]:
    height = len(rows)
    width = len(rows[0]) if rows else 0
    remaining = {
        (x, y)
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if value in CONTROL_INDICES
    }
    sizes: list[int] = []
    while remaining:
        pending = [remaining.pop()]
        size = 0
        while pending:
            x, y = pending.pop()
            size += 1
            for neighbor in _neighbors8(width, height, x, y):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
        sizes.append(size)
    return tuple(sorted(sizes, reverse=True))


def grounded_shadow_contact_metrics(
    rows: Sequence[Sequence[int]],
) -> dict[str, Any]:
    """Measure Majesty shadow/body contact without interpreting preview RGB.

    Stock Warrior Walk/Stand TILEs establish the grounded invariant: at least
    one control pixel directly touches the lowest six rows of visible body art.
    The stricter private-Alchemist contract additionally reserves 247 for that
    seam and forbids a transparent moat between body and bands 248..250.
    """

    height = len(rows)
    width = len(rows[0]) if rows else 0
    if not width or any(len(row) != width for row in rows):
        raise ValueError("Grounded shadow metrics require a rectangular index plane")
    body = {
        (x, y)
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if 1 <= value <= 246
    }
    controls = {
        (x, y)
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if value in CONTROL_INDICES
    }
    if not body or not controls:
        raise ValueError("Grounded shadow metrics require both body and control pixels")
    body_base = max(y for _x, y in body)
    ground_body = {(x, y) for x, y in body if y >= body_base - 5}
    seam = {
        (x, y)
        for x, y in controls
        if rows[y][x] == 247
    }
    magenta = controls - seam

    def touching(points: set[tuple[int, int]], target: set[tuple[int, int]]) -> set[tuple[int, int]]:
        return {
            (x, y)
            for x, y in points
            if any(
                neighbor in target
                for neighbor in _neighbors8(width, height, x, y)
            )
        }

    transparent_gap_points: list[tuple[int, int]] = []
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            if value != 0:
                continue
            neighbors = _neighbors8(width, height, x, y)
            if any(point in body for point in neighbors) and any(
                point in magenta for point in neighbors
            ):
                transparent_gap_points.append((x, y))

    return {
        "body_base_y": body_base,
        "body_control_contact_total": len(touching(controls, body)),
        "ground_control_contact_total": len(touching(controls, ground_body)),
        "ground_seam_contact_total": len(touching(seam, ground_body)),
        "magenta_body_contact_total": len(touching(magenta, body)),
        "transparent_magenta_body_gap_total": len(transparent_gap_points),
        "transparent_magenta_body_gap_examples": transparent_gap_points[:12],
        "edge_control_total": sum(
            x in (0, width - 1) or y in (0, height - 1)
            for x, y in controls
        ),
        "control_counts": {
            str(index): sum(value == index for row in rows for value in row)
            for index in sorted(CONTROL_INDICES)
        },
    }


def validate_grounded_shadow_contact(
    rows: Sequence[Sequence[int]],
    expected_canvas: tuple[int, int] = NATIVE_CANVAS,
) -> dict[str, Any]:
    """Reject the disconnected-shadow failure seen in the first game gate."""

    if (len(rows[0]) if rows else 0, len(rows)) != expected_canvas:
        raise ValueError("Grounded Alchemist shadow changed the native canvas")
    metrics = grounded_shadow_contact_metrics(rows)
    if not metrics["ground_control_contact_total"]:
        raise ValueError("Grounded Alchemist shadow has a transparent moat at the feet")
    if not metrics["ground_seam_contact_total"]:
        raise ValueError("Grounded Alchemist shadow has no index-247 foot seam")
    if metrics["magenta_body_contact_total"]:
        raise ValueError("Grounded Alchemist shadow has magenta touching body without a seam")
    if metrics["transparent_magenta_body_gap_total"]:
        raise ValueError(
            "Grounded Alchemist shadow has transparent pixels between magenta and body"
        )
    if metrics["edge_control_total"]:
        raise ValueError("Grounded Alchemist shadow writes controls on a TILE edge")
    if any(not count for count in metrics["control_counts"].values()):
        raise ValueError("Grounded Alchemist shadow lost a required 247..250 control band")
    return metrics


def projected_grounded_hero_shadow(
    body_rows: Sequence[Sequence[int]],
    expected_canvas: tuple[int, int] = NATIVE_CANVAS,
) -> list[list[int]]:
    """Project a grounded Majesty hero shadow from the approved body plane.

    Authority, in priority order:

    * stock Warrior Walk/Stand TILEs 5919..5990: the ground shadow touches the
      lower body in every one of the 72 source frames;
    * Phantoms Haunt commit ``1ac887f55e4c1c67dc8d90829cb099eea87b15ae``,
      ``docs/majesty-building-shadow-encoding.md``: 247 is the contact seam,
      248..250 are projected bands, and index 0 is forbidden at contact;
    * ``generate_phantom_building_sprites.py:add_cast_shadow``: the grounded
      base anchor, body precedence, literal seam repair, and split-RLE order;
    * ``build_phantom_guild.py:projected_floating_hero_shadow``: only its
      central-mass limiter and 0.44/0.36 projection geometry. Its -3/-3 hover
      displacement, body clearance, and component prune are forbidden here.

    Do not call ``projected_floating_hero_shadow`` here. Its constant -3/-3
    base displacement, body-clearance pass, and largest-component cleanup are
    deliberate Phantom hovering behavior. They created the visible transparent
    band when copied to this grounded hero.
    """

    height = len(body_rows)
    width = len(body_rows[0]) if body_rows else 0
    if (width, height) != expected_canvas or any(
        len(row) != width for row in body_rows
    ):
        raise ValueError("Grounded shadow projection changed the approved canvas")
    if any(
        value < 0 or value > 246
        for row in body_rows
        for value in row
    ):
        raise ValueError("Grounded shadow caster must contain indices 0..246 only")

    points_by_row: dict[int, list[int]] = {}
    for y, row in enumerate(body_rows):
        for x, value in enumerate(row):
            if value:
                points_by_row.setdefault(y, []).append(x)
    if not points_by_row:
        raise ValueError("Grounded shadow caster has no visible body")

    # Preserve the proven Phantom central-mass limiter so a changing arm,
    # dagger, or bottle cannot turn the projection into a horizontal bar. All
    # visible Alchemist indices cast; the Phantom-only cyan/white exclusions do
    # not apply to ordinary grounded costume highlights or carried equipment.
    caster_points: list[tuple[int, int]] = []
    for y, row_xs in points_by_row.items():
        row_xs.sort()
        row_center = row_xs[len(row_xs) // 2]
        row_span = row_xs[-1] - row_xs[0] + 1
        half_width = max(3, min(12, round(row_span * 0.38)))
        caster_points.extend(
            (x, y)
            for x in row_xs
            if abs(x - row_center) <= half_width
        )

    base_y = max(y for _x, y in caster_points)
    hits: dict[tuple[int, int], int] = {}
    for x, y in caster_points:
        vertical_height = base_y - y
        shadow_x = round(x - vertical_height * 0.44)
        shadow_y = round(base_y - vertical_height * 0.36)
        if 0 <= shadow_x < width and 0 <= shadow_y < height:
            point = (shadow_x, shadow_y)
            hits[point] = hits.get(point, 0) + 1

    projected = [[0 for _x in range(width)] for _y in range(height)]
    core = set(hits)
    for (x, y), hit_count in hits.items():
        projected[y][x] = 248 if hit_count >= 2 else 249
    for x, y in sorted(core, key=lambda point: (point[1], point[0])):
        for neighbor_x, neighbor_y in _neighbors8(width, height, x, y):
            if (neighbor_x, neighbor_y) in core:
                continue
            diagonal = neighbor_x != x and neighbor_y != y
            value = 250 if diagonal else 249
            current = projected[neighbor_y][neighbor_x]
            projected[neighbor_y][neighbor_x] = min(current or 250, value)

    # No body-clearance or component-prune pass belongs here. The raw NW Walk
    # frame 4 projection legitimately has a small second foot component; the
    # floating Phantom cleanup would silently discard it.
    return projected


def project_approved_shadow_controls(
    stock: Any,
    approved_tile: bytes,
    palette_colours: Sequence[tuple[int, int, int]],
    expected_canvas: tuple[int, int] = NATIVE_CANVAS,
    expected_hotspot: tuple[int, int] = NATIVE_ROOT,
    clip_edge_controls: bool = False,
) -> tuple[bytes, dict[str, Any]]:
    """Add grounded Majesty 247..250 controls without changing approved art."""

    if sha256_bytes(GROUNDED_SHADOW_POLICY.encode("ascii")) != GROUNDED_SHADOW_POLICY_SHA256:
        raise ValueError("Grounded shadow policy identity changed")
    approved_decoded = stock.decode_indexed_v3_tile(approved_tile)
    if approved_decoded is None:
        raise ValueError("Approved shadow projection requires an indexed TILE-v3 record")
    approved_height, approved_width, approved_rows = approved_decoded
    if (approved_width, approved_height) != expected_canvas:
        raise ValueError("Shadow projection changed the approved native canvas")
    if len(palette_colours) < 251:
        raise ValueError("Shadow projection palette is incomplete")
    if any(
        value in CONTROL_INDICES or value > 246
        for row in approved_rows
        for value in row
    ):
        raise ValueError("Shadow projection target must contain body indices 0..246 only")
    if struct.unpack_from("<HH", approved_tile, 10) != expected_hotspot:
        raise ValueError("Shadow projection target hotspot changed")

    projected_rows = projected_grounded_hero_shadow(
        approved_rows, expected_canvas=expected_canvas
    )
    if clip_edge_controls:
        # Approved action art may legitimately reach closer to the fixed
        # canvas edge than Walk/Stand. The stock control contract forbids
        # encoded shadow controls on an edge, so discard only projected
        # controls there; never crop, move, or rewrite visible body pixels.
        for x in range(approved_width):
            projected_rows[0][x] = 0
            projected_rows[-1][x] = 0
        for y in range(approved_height):
            projected_rows[y][0] = 0
            projected_rows[y][-1] = 0
    projected_component_sizes = _control_component_sizes(projected_rows)
    target_rows = [list(row) for row in approved_rows]
    projected_counts = {index: 0 for index in sorted(CONTROL_INDICES)}
    retained_projected_counts = {index: 0 for index in sorted(CONTROL_INDICES)}
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
            retained_projected_counts[value] += 1

    # Phantoms' documented contact rule: projected magenta that directly
    # touches authored body becomes the red index-247 transition seam.
    direct_seam_total = 0
    direct_source = [list(row) for row in target_rows]
    for y, row in enumerate(direct_source):
        for x, value in enumerate(row):
            if not 248 <= value <= 250:
                continue
            if any(
                1 <= direct_source[neighbor_y][neighbor_x] <= 246
                for neighbor_x, neighbor_y in _neighbors8(
                    approved_width, approved_height, x, y
                )
            ):
                target_rows[y][x] = 247
                direct_seam_total += 1

    # Literal final seam rule from generate_phantom_building_sprites.py: fill
    # only a zero pixel that touches both magenta and real body. Use a snapshot
    # so this cannot grow a seam recursively into unrelated transparency.
    gap_fill_seam_total = 0
    gap_source = [list(row) for row in target_rows]
    for y, row in enumerate(gap_source):
        for x, value in enumerate(row):
            if value != 0:
                continue
            neighbors = _neighbors8(approved_width, approved_height, x, y)
            if any(
                1 <= gap_source[neighbor_y][neighbor_x] <= 246
                for neighbor_x, neighbor_y in neighbors
            ) and any(
                248 <= gap_source[neighbor_y][neighbor_x] <= 250
                for neighbor_x, neighbor_y in neighbors
            ):
                target_rows[y][x] = 247
                gap_fill_seam_total += 1

    projected_total = sum(projected_counts.values())
    conflict_total = sum(conflict_counts.values())
    retained_projected_total = sum(retained_projected_counts.values())
    retained_counts = {
        index: sum(value == index for row in target_rows for value in row)
        for index in sorted(CONTROL_INDICES)
    }
    retained_total = sum(retained_counts.values())
    if not projected_total or not retained_total:
        raise ValueError("Approved frame has no retained grounded shadow")
    if projected_total != conflict_total + retained_projected_total:
        raise AssertionError("Grounded shadow projected-pixel accounting is incomplete")
    if retained_total != retained_projected_total + gap_fill_seam_total:
        raise AssertionError("Grounded shadow seam-fill accounting is incomplete")
    contact_metrics = validate_grounded_shadow_contact(
        target_rows, expected_canvas=expected_canvas
    )

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
    if _tile_rows(stock, output, expected_canvas) != target_rows:
        raise AssertionError("Shadow projection TILE does not decode exactly")
    validate_split_control_segments(output)
    stats: dict[str, Any] = {
        "algorithm": GROUNDED_SHADOW_POLICY,
        "algorithm_policy_sha256": GROUNDED_SHADOW_POLICY_SHA256,
        "authority": {
            "stock": "AVL1Warrior TILE 5919..5990 grounded contact",
            "contract_commit": PHANTOMS_SHADOW_CONTRACT_COMMIT,
            "contract_path": PHANTOMS_SHADOW_CONTRACT_PATH,
            "contract": (
                "../majesty-gold-hd-custom-guild-phantoms-haunt/docs/"
                "majesty-building-shadow-encoding.md"
            ),
            "grounding_implementation": (
                "../majesty-gold-hd-custom-guild-phantoms-haunt/scripts/"
                "generate_phantom_building_sprites.py:add_cast_shadow"
            ),
            "projection_geometry": (
                "../majesty-gold-hd-custom-guild-phantoms-haunt/src/"
                "build_phantom_guild.py:projected_floating_hero_shadow "
                "central-mass and 0.44/0.36 terms only"
            ),
        },
        "caster_body_sha256": sha256_bytes(_visible_body_plane(approved_rows)),
        "projected_control_counts": {str(k): v for k, v in projected_counts.items()},
        "projected_control_total": projected_total,
        "projected_component_sizes": list(projected_component_sizes),
        "body_conflict_counts": {str(k): v for k, v in conflict_counts.items()},
        "body_conflict_total": conflict_total,
        "retained_projected_control_counts": {
            str(k): v for k, v in retained_projected_counts.items()
        },
        "retained_projected_control_total": retained_projected_total,
        "direct_seam_total": direct_seam_total,
        "gap_fill_seam_total": gap_fill_seam_total,
        "retained_control_counts": {str(k): v for k, v in retained_counts.items()},
        "retained_control_total": retained_total,
        "ground_contact_seam_total": contact_metrics["ground_seam_contact_total"],
        "body_control_contact_total": contact_metrics["body_control_contact_total"],
        "magenta_body_contact_total": contact_metrics["magenta_body_contact_total"],
        "transparent_magenta_body_gap_total": contact_metrics[
            "transparent_magenta_body_gap_total"
        ],
        "edge_control_total": contact_metrics["edge_control_total"],
        "projected_control_sha256": sha256_bytes(_control_plane(projected_rows)),
        "retained_control_sha256": sha256_bytes(_control_plane(target_rows)),
    }
    if clip_edge_controls:
        stats["edge_control_policy"] = (
            "discard projected edge controls; visible body unchanged"
        )
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


def _verify_completed_handoff(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = root / "manifest.json"
    require_sha256(
        manifest_path,
        COMPLETED_HANDOFF_MANIFEST_SHA256,
        "Completed Alchemist sprite manifest",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("schema_version") != 1
        or manifest.get("bundle_id")
        != "majesty-alchemist-approved-humanoid-sprite-set-v1"
        or manifest.get("approval_status") != "approved_for_packaging_and_ingame_test"
    ):
        raise ValueError("Completed Alchemist sprite manifest identity changed")
    if manifest.get("direction_order") != list(DIRECTION_ORDER):
        raise ValueError("Completed Alchemist direction order changed")
    integrity = manifest.get("payload_integrity", {})
    files = integrity.get("files")
    if not isinstance(files, list) or len(files) != 290:
        raise ValueError("Completed Alchemist payload inventory changed")
    lines: list[str] = []
    total_bytes = 0
    paths: list[str] = []
    for record in files:
        relative = record.get("path")
        expected_hash = record.get("sha256")
        expected_bytes = record.get("bytes")
        if not isinstance(relative, str) or not isinstance(expected_hash, str):
            raise ValueError("Completed Alchemist payload record is malformed")
        path = root / relative
        require_sha256(path, expected_hash, f"Completed sprite payload {relative}")
        if path.stat().st_size != expected_bytes:
            raise ValueError(f"Completed sprite payload size changed: {relative}")
        paths.append(relative)
        total_bytes += expected_bytes
        lines.append(f"{expected_hash}  {relative}")
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValueError("Completed Alchemist payload order is not canonical")
    aggregate = sha256_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    if (
        total_bytes != integrity.get("total_bytes")
        or aggregate != COMPLETED_HANDOFF_AGGREGATE_SHA256
        or aggregate != integrity.get("aggregate_sha256")
    ):
        raise ValueError("Completed Alchemist payload aggregate changed")
    authority_relative = manifest["stock_authority"]["authority_path"]
    authority_path = root / authority_relative
    require_sha256(
        authority_path,
        COMPLETED_HANDOFF_AUTHORITY_SHA256,
        "Completed Alchemist Warrior authority",
    )
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    if authority.get("authority_id") != "majesty-warrior-action-authority-v1":
        raise ValueError("Completed Alchemist Warrior authority identity changed")
    return manifest, authority


def _encode_approved_rgba_tile(
    stock: Any,
    path: Path,
    visible_colours: Sequence[tuple[int, int, int]],
    private_palette_index: int,
    canvas: tuple[int, int],
    hotspot: tuple[int, int],
) -> tuple[bytes, bytes]:
    with Image.open(path) as loaded:
        image = loaded.convert("RGBA")
    if image.size != canvas:
        raise ValueError(f"Approved sprite canvas changed for {path}: {image.size}")
    indices = rgba_to_indices(image, visible_colours)
    width, height = canvas
    rows = [list(indices[y * width : (y + 1) * width]) for y in range(height)]
    tile = stock.encode_indexed_v3_tile(
        rows,
        private_palette_index,
        (3, height, width, 0, 32, hotspot[0], hotspot[1], 1),
    )
    if _tile_indices(stock, tile, canvas) != indices:
        raise AssertionError(f"Approved sprite TILE did not round-trip: {path}")
    return tile, indices


def _authority_by_key(authority: dict[str, Any]) -> dict[str, dict[str, Any]]:
    values = authority.get("action_authorities")
    if not isinstance(values, list):
        raise ValueError("Warrior action authority has no action table")
    return {
        value["authority_key"]: value
        for value in values
        if value.get("actor_key") == "warrior"
    }


def _authority_offsets(
    authority: dict[str, Any], authority_key: str
) -> list[list[int]]:
    records = authority.get("records")
    if not isinstance(records, list):
        raise ValueError("Warrior action authority has no occurrence records")
    grouped: dict[int, list[tuple[int, int]]] = {}
    for record in records:
        if record.get("authority_key") != authority_key:
            continue
        grouped.setdefault(record["direction_slot"], []).append(
            (record["frame"], record["tile_reference"]["field_offset"])
        )
    return [
        [offset for _frame, offset in sorted(grouped[slot])]
        for slot in sorted(grouped)
    ]


def load_completed_handoff_bundle(
    root: Path,
    stock: Any,
    stock_cam: Path,
    stock_tiles: Sequence[Any],
    stock_palettes: Sequence[Any],
    warrior_imag: bytes,
) -> ApprovedSpriteBundle:
    """Import the approved complete humanoid set through Warrior's exact topology."""

    manifest, authority = _verify_completed_handoff(root)
    if sha256_file(stock_cam) != RETAIL_MAINDATA_SHA256:
        raise ValueError("Installed maindata.cam does not match the approved retail authority")
    if sha256_bytes(warrior_imag) != WARRIOR_IMAG_SHA256:
        raise ValueError("Stock AVL1Warrior IMAG changed from the approved authority")
    if len(stock_palettes) != EXPECTED_RETAIL_SPLT_COUNT:
        raise ValueError("Retail SPLT table changed from the approved authority")

    palette_manifest = _load_json(
        root / "palette" / "candidate-palette.json",
        PALETTE_MANIFEST_SHA256,
        "Completed Alchemist candidate palette",
    )
    visible_colours = _load_visible_palette(palette_manifest)
    private_palette_index = len(stock_palettes)
    private_palette_data = build_private_splt(
        stock_palettes[427].data, visible_colours
    )
    private_colours = stock.splt_palette_colors(private_palette_data)

    action_authorities = _authority_by_key(authority)
    required_authorities = {
        "attack": "warrior_attack_16",
        "special": "warrior_special_64",
        "cast": "warrior_cast_128",
        "death": "warrior_die_96",
        "dead": "warrior_dead_224",
    }
    if not set(required_authorities.values()).issubset(action_authorities):
        raise ValueError("Warrior action authority is incomplete")

    records: list[dict[str, Any]] = []
    patches: list[dict[str, Any]] = []
    tiles_by_stock_slot: dict[int, bytes] = {}

    def add_record(
        *,
        action: str,
        direction: str,
        frame: int,
        source_path: Path,
        source_stock_slot: int,
        imag_offsets: Sequence[int],
        canvas: tuple[int, int] = NATIVE_CANVAS,
        hotspot: tuple[int, int] = NATIVE_ROOT,
        source_tile: bytes | None = None,
    ) -> None:
        if source_tile is None:
            tile, body_indices = _encode_approved_rgba_tile(
                stock,
                source_path,
                visible_colours,
                private_palette_index,
                canvas,
                hotspot,
            )
        else:
            tile = _patch_walk_palette(source_tile, private_palette_index)
            body_indices = _tile_indices(stock, tile)
            if any(index > 246 for index in body_indices):
                raise ValueError(f"Approved Walk uses reserved indices: {source_path}")
        try:
            shadowed_tile, shadow_stats = project_approved_shadow_controls(
                stock,
                tile,
                private_colours,
                expected_canvas=canvas,
                expected_hotspot=hotspot,
                clip_edge_controls=action not in {"walk", "stand"},
            )
        except ValueError as error:
            raise ValueError(
                f"Approved {action} shadow failed for {source_path}: {error}"
            ) from error
        full_indices = _tile_indices(stock, shadowed_tile, canvas)
        relative = source_path.relative_to(root).as_posix()
        record_index = len(records)
        record = {
            "record_index": record_index,
            "kind": action,
            "direction": direction,
            "frame": frame,
            "stock_slot": source_stock_slot,
            "source": relative,
            "source_sha256": sha256_file(source_path),
            "indexed_pixel_sha256": sha256_bytes(body_indices),
            "full_indexed_pixel_sha256": sha256_bytes(full_indices),
            "shadow": shadow_stats,
            "packaged_tile_sha256": sha256_bytes(shadowed_tile),
            "packaged_tile": shadowed_tile,
            "imag_offsets": list(imag_offsets),
            "canvas": list(canvas),
            "hotspot": list(hotspot),
            "clip_edge_controls": action not in {"walk", "stand"},
        }
        records.append(record)
        for offset in imag_offsets:
            before = struct.unpack_from("<I", warrior_imag, offset)[0]
            if (before & 0xFFFF) != source_stock_slot:
                raise ValueError(
                    f"Warrior {action} authority changed at IMAG offset {offset:#x}"
                )
            patches.append(
                {
                    "offset": offset,
                    "record_index": record_index,
                    "source_stock_slot": source_stock_slot,
                    "source_word": before,
                }
            )
        tiles_by_stock_slot.setdefault(source_stock_slot, shadowed_tile)

    # Walk and Stand were already live-proven. Their copied handoff payloads
    # retain the exact established order, plus set 400's stock reuse of Walk 0.
    for direction_slot, direction in enumerate(DIRECTION_ORDER):
        for frame in range(8):
            stock_slot = WALK_START + direction_slot * 8 + frame
            path = root / "walk" / direction / f"frame-{frame:02d}-a128.tile"
            offsets = [0x630 + direction_slot * 0x58 + frame * 8]
            if stock_slot == WALK_START:
                offsets.insert(0, 0x1C8)
            add_record(
                action="walk",
                direction=direction,
                frame=frame,
                source_path=path,
                source_stock_slot=stock_slot,
                imag_offsets=offsets,
                source_tile=path.read_bytes(),
            )
        stock_slot = STAND_START + direction_slot
        add_record(
            action="stand",
            direction=direction,
            frame=0,
            source_path=root / "stand" / direction / "frame-00-soft-b.png",
            source_stock_slot=stock_slot,
            imag_offsets=[0x960 + direction_slot * 0x30],
        )

    attack_offsets = _authority_offsets(authority, required_authorities["attack"])
    for direction_slot, direction in enumerate(DIRECTION_ORDER):
        for frame, offset in enumerate(attack_offsets[direction_slot]):
            add_record(
                action="attack",
                direction=direction,
                frame=frame,
                source_path=root / "attack" / direction / f"frame-{frame:02d}-soft-b.png",
                source_stock_slot=6055 + direction_slot * 8 + frame,
                imag_offsets=[offset],
            )

    cast_offsets = _authority_offsets(authority, required_authorities["cast"])
    cast_keys = ("A", "B", "C", "B", "D", "E", "F")
    special_offsets = _authority_offsets(authority, required_authorities["special"])
    special_keys = ("A", "B", "C", "D", "E", "F", "G")
    for action, offsets_by_direction, keys in (
        ("cast", cast_offsets, cast_keys),
        ("special", special_offsets, special_keys),
    ):
        for direction_slot, direction in enumerate(DIRECTION_ORDER):
            if len(offsets_by_direction[direction_slot]) != len(keys):
                raise ValueError(f"Warrior {action} occurrence count changed")
            for frame, (offset, key) in enumerate(
                zip(offsets_by_direction[direction_slot], keys)
            ):
                source_slot = struct.unpack_from("<I", warrior_imag, offset)[0] & 0xFFFF
                add_record(
                    action=action,
                    direction=direction,
                    frame=frame,
                    source_path=root / action / direction / f"key-{key}-soft-b.png",
                    source_stock_slot=source_slot,
                    imag_offsets=[offset],
                )

    death_offsets = _authority_offsets(authority, required_authorities["death"])
    for direction_slot, direction in enumerate(DIRECTION_ORDER):
        keys = ("a", "b", "c", "d")
        for frame, key in enumerate(keys):
            offsets = death_offsets[direction_slot][frame : frame + 1]
            if frame == 3:
                offsets = death_offsets[direction_slot][3:]
            source_slot = struct.unpack_from("<I", warrior_imag, offsets[0])[0] & 0xFFFF
            add_record(
                action="death",
                direction=direction,
                frame=frame,
                source_path=root / "death" / direction / f"key-{key}.png",
                source_stock_slot=source_slot,
                imag_offsets=offsets,
                canvas=(112, 92),
                hotspot=(62, 57),
            )

    dead_offset = _authority_offsets(authority, required_authorities["dead"])[0][0]
    dead_slot = struct.unpack_from("<I", warrior_imag, dead_offset)[0] & 0xFFFF
    add_record(
        action="dead",
        direction="shared",
        frame=0,
        source_path=root / "dead" / "alchemist-gravestone-B-native-35x33.png",
        source_stock_slot=dead_slot,
        imag_offsets=[dead_offset],
        canvas=(35, 33),
        hotspot=(22, 15),
    )

    actual_counts = {
        action: sum(record["kind"] == action for record in records)
        for action in COMPLETED_ACTION_COUNTS
    }
    if actual_counts != COMPLETED_ACTION_COUNTS:
        raise ValueError(f"Completed Alchemist action counts changed: {actual_counts}")
    if len(records) != 281 or len(patches) != 378:
        raise ValueError("Completed Alchemist private TILE/occurrence topology changed")
    if len({patch["offset"] for patch in patches}) != len(patches):
        raise ValueError("Completed Alchemist IMAG authority overlaps itself")

    # Preserve the already-live-proven Walk/Stand conversion bit-for-bit.
    proven = [record for record in records if record["kind"] in {"walk", "stand"}]
    shadow_totals = {
        "projected": sum(r["shadow"]["projected_control_total"] for r in proven),
        "body_conflicts": sum(r["shadow"]["body_conflict_total"] for r in proven),
        "retained_projected": sum(r["shadow"]["retained_projected_control_total"] for r in proven),
        "direct_seam": sum(r["shadow"]["direct_seam_total"] for r in proven),
        "gap_fill_seam": sum(r["shadow"]["gap_fill_seam_total"] for r in proven),
        "retained": sum(r["shadow"]["retained_control_total"] for r in proven),
        "ground_contact_seam": sum(r["shadow"]["ground_contact_seam_total"] for r in proven),
    }
    if shadow_totals != EXPECTED_SHADOW_TOTALS:
        raise ValueError("Completed handoff changed the proven Walk/Stand shadows")

    return ApprovedSpriteBundle(
        private_palette_index=private_palette_index,
        private_palette_data=private_palette_data,
        tiles_by_stock_slot=tiles_by_stock_slot,
        records=tuple(records),
        source_hashes={
            "manifest.json": COMPLETED_HANDOFF_MANIFEST_SHA256,
            "payload aggregate": COMPLETED_HANDOFF_AGGREGATE_SHA256,
            "authority/warrior-action-authority-v1.json": COMPLETED_HANDOFF_AUTHORITY_SHA256,
            "retail_maindata.cam": RETAIL_MAINDATA_SHA256,
            "AVL1Warrior IMAG": WARRIOR_IMAG_SHA256,
        },
        imag_patches=tuple(sorted(patches, key=lambda value: value["offset"])),
        handoff_manifest_sha256=COMPLETED_HANDOFF_MANIFEST_SHA256,
    )


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
    if (sprite_pipeline_root / "manifest.json").is_file():
        return load_completed_handoff_bundle(
            sprite_pipeline_root,
            stock,
            stock_cam,
            stock_tiles,
            stock_palettes,
            warrior_imag,
        )
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
        "retained_projected": 0,
        "direct_seam": 0,
        "gap_fill_seam": 0,
        "retained": 0,
        "ground_contact_seam": 0,
    }
    projected_shadow_bands = {index: 0 for index in sorted(CONTROL_INDICES)}
    retained_shadow_bands = {index: 0 for index in sorted(CONTROL_INDICES)}
    conflict_shadow_bands = {index: 0 for index in sorted(CONTROL_INDICES)}

    def record_shadow_stats(stats: dict[str, Any]) -> None:
        shadow_totals["projected"] += stats["projected_control_total"]
        shadow_totals["body_conflicts"] += stats["body_conflict_total"]
        shadow_totals["retained_projected"] += stats[
            "retained_projected_control_total"
        ]
        shadow_totals["direct_seam"] += stats["direct_seam_total"]
        shadow_totals["gap_fill_seam"] += stats["gap_fill_seam_total"]
        shadow_totals["retained"] += stats["retained_control_total"]
        shadow_totals["ground_contact_seam"] += stats[
            "ground_contact_seam_total"
        ]
        for index in sorted(CONTROL_INDICES):
            projected_shadow_bands[index] += stats["projected_control_counts"][str(index)]
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
            f"Approved grounded shadow totals changed: {shadow_totals!r}"
        )
    if projected_shadow_bands != EXPECTED_PROJECTED_SHADOW_BANDS:
        raise ValueError(
            "Approved projected grounded-shadow bands changed: "
            f"{projected_shadow_bands!r}"
        )
    if retained_shadow_bands != EXPECTED_RETAINED_SHADOW_BANDS:
        raise ValueError(
            "Approved retained grounded-shadow bands changed: "
            f"{retained_shadow_bands!r}"
        )
    if conflict_shadow_bands != EXPECTED_CONFLICT_SHADOW_BANDS:
        raise ValueError(
            "Approved body-conflict shadow bands changed: "
            f"{conflict_shadow_bands!r}"
        )

    ordered_rows = [
        _tile_rows(stock, tiles_by_stock_slot[stock_slot])
        for stock_slot in range(APPROVED_SLOT_START, APPROVED_SLOT_END)
    ]
    aggregate_control_plane = b"".join(_control_plane(rows) for rows in ordered_rows)
    aggregate_full_plane = b"".join(
        bytes(value for row in rows for value in row)
        for rows in ordered_rows
    )
    aggregate_body_plane = b"".join(
        _visible_body_plane(rows) for rows in ordered_rows
    )
    aggregate_hashes = {
        "control": sha256_bytes(aggregate_control_plane),
        "full": sha256_bytes(aggregate_full_plane),
        "body": sha256_bytes(aggregate_body_plane),
    }
    expected_aggregate_hashes = {
        "control": EXPECTED_CONTROL_PLANE_SHA256,
        "full": EXPECTED_FULL_INDEX_PLANE_SHA256,
        "body": EXPECTED_BODY_PLANE_SHA256,
    }
    if aggregate_hashes != expected_aggregate_hashes:
        raise ValueError(
            "Approved grounded-shadow aggregate plane hashes changed: "
            f"{aggregate_hashes!r}"
        )
    frame_hash_lists = {
        "projected_control": [
            record["shadow"]["projected_control_sha256"]
            for record in output_records
        ],
        "retained_control": [
            record["shadow"]["retained_control_sha256"]
            for record in output_records
        ],
        "full": [record["full_indexed_pixel_sha256"] for record in output_records],
        "body": [record["indexed_pixel_sha256"] for record in output_records],
    }
    frame_hash_list_sha256 = {
        name: sha256_bytes(
            json.dumps(values, separators=(",", ":")).encode("ascii")
        )
        for name, values in frame_hash_lists.items()
    }
    if frame_hash_list_sha256 != EXPECTED_FRAME_HASH_LIST_SHA256:
        raise ValueError(
            "Approved grounded-shadow per-frame hash lists changed: "
            f"{frame_hash_list_sha256!r}"
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


def patch_completed_warrior_imag(
    warrior_imag: bytes,
    bundle: ApprovedSpriteBundle,
    private_tile_indices: Sequence[int],
) -> bytes:
    """Patch only the manifest-authorized low16 occurrence words."""

    if bundle.handoff_manifest_sha256 is None:
        raise ValueError("Completed Warrior patch requires the handoff bundle")
    if len(private_tile_indices) != len(bundle.records):
        raise ValueError("Completed Warrior private TILE map is incomplete")
    patched = bytearray(warrior_imag)
    expected_offsets = {patch["offset"] for patch in bundle.imag_patches}
    for patch in bundle.imag_patches:
        offset = patch["offset"]
        before = struct.unpack_from("<I", warrior_imag, offset)[0]
        if before != patch["source_word"]:
            raise ValueError(f"Warrior source word changed at IMAG offset {offset:#x}")
        private_index = private_tile_indices[patch["record_index"]]
        if not 0 <= private_index <= 0xFFFF:
            raise ValueError("Completed Warrior private TILE index exceeds low16")
        struct.pack_into("<I", patched, offset, (before & 0xFFFF0000) | private_index)
    changed_offsets = {
        offset
        for offset in range(0, len(warrior_imag) - 3, 4)
        if warrior_imag[offset : offset + 4] != patched[offset : offset + 4]
    }
    if changed_offsets != expected_offsets:
        raise ValueError("Completed Warrior patch changed an unauthorized IMAG word")
    return bytes(patched)


def _validate_completed_sprite_cam(
    stock: Any,
    output_cam: Path,
    stock_tiles: Sequence[Any],
    stock_palettes: Sequence[Any],
    warrior_imag: bytes,
    bundle: ApprovedSpriteBundle,
    private_tile_indices: Sequence[int],
    interface_tile_indices: dict[int, int],
    interface_records: Sequence[dict[str, Any]],
) -> None:
    output_palettes = stock.read_cam_entries(output_cam, b"SPLT")
    if len(output_palettes) != bundle.private_palette_index + 1:
        raise ValueError("Completed package does not end at its private SPLT")
    if output_palettes[bundle.private_palette_index].data != bundle.private_palette_data:
        raise ValueError("Completed package changed its private SPLT")
    if output_palettes[427].data != stock_palettes[427].data:
        raise ValueError("Completed package changed stock Warrior SPLT 427")

    output_tiles = stock.read_cam_entries(output_cam, b"TILE")
    first_private = len(stock_tiles)
    if any(entry.data for entry in output_tiles[:first_private]):
        raise ValueError("Completed package overwrites a retail TILE slot")
    expected_private = list(range(first_private, first_private + len(bundle.records)))
    if list(private_tile_indices) != expected_private:
        raise ValueError("Completed humanoid TILEs are not the first private block")
    private_colours = stock.splt_palette_colors(bundle.private_palette_data)
    for record, private_index in zip(bundle.records, private_tile_indices):
        payload = output_tiles[private_index].data
        if sha256_bytes(payload) != record["packaged_tile_sha256"]:
            raise ValueError(
                f"Completed {record['kind']} TILE {record['record_index']} changed"
            )
        if stock.tile_palette_index(payload) != bundle.private_palette_index:
            raise ValueError("Completed humanoid TILE uses the wrong private SPLT")
        rows = _tile_rows(stock, payload, tuple(record["canvas"]))
        flat = bytes(value for row in rows for value in row)
        if sha256_bytes(flat) != record["full_indexed_pixel_sha256"]:
            raise ValueError("Completed humanoid indexed pixels changed")
        if any(value > 250 for value in flat):
            raise ValueError("Completed humanoid TILE uses index 251..255")
        if not any(value in CONTROL_INDICES for value in flat):
            raise ValueError("Completed humanoid TILE has no grounded shadow")
        validate_split_control_segments(payload)
        validate_grounded_shadow_contact(rows, tuple(record["canvas"]))
        body_rows = [
            [0 if value in CONTROL_INDICES else value for value in row]
            for row in rows
        ]
        body_tile = stock.encode_indexed_v3_tile_like_original(
            payload, body_rows, split_shadow_controls=True
        )
        rebuilt, shadow = project_approved_shadow_controls(
            stock,
            body_tile,
            private_colours,
            expected_canvas=tuple(record["canvas"]),
            expected_hotspot=tuple(record["hotspot"]),
            clip_edge_controls=record["clip_edge_controls"],
        )
        if (
            _tile_rows(stock, rebuilt, tuple(record["canvas"])) != rows
            or shadow != record["shadow"]
        ):
            raise ValueError("Completed humanoid grounded-shadow clone changed")

    if tuple(interface_tile_indices) != INTERFACE_SOURCE_SLOTS:
        raise ValueError("Completed interface TILE mapping is incomplete")
    if list(interface_tile_indices.values()) != list(
        range(len(output_tiles) - len(INTERFACE_SOURCE_SLOTS), len(output_tiles))
    ):
        raise ValueError("Completed interface TILEs are not the final private block")
    if len(interface_records) != len(INTERFACE_SOURCE_SLOTS):
        raise ValueError("Completed interface provenance is incomplete")
    for record in interface_records:
        payload = output_tiles[record["private_tile_index"]].data
        if not payload or sha256_bytes(payload) != record["packaged_tile_sha256"]:
            raise ValueError("Completed interface TILE changed")

    expected_imag = patch_completed_warrior_imag(
        warrior_imag, bundle, private_tile_indices
    )
    expected_imag = stock.remap_imag_low16_tile_indices(
        expected_imag, interface_tile_indices
    )
    packaged_imag = stock.read_cam_entry(output_cam, b"IMAG", b"ALC1Alchemist").data
    if packaged_imag != expected_imag:
        raise ValueError("Completed ALC1 IMAG differs from the stock-authorized clone")



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

    if bundle.handoff_manifest_sha256 is not None:
        _validate_completed_sprite_cam(
            stock,
            output_cam,
            stock_tiles,
            stock_palettes,
            warrior_imag,
            bundle,
            list(private_tile_indices.values()),
            interface_tile_indices,
            interface_records,
        )
        return

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
                f"Packaged grounded shadow changed for stock slot {stock_slot}"
            )
        if expected_shadow != record["shadow"]:
            raise ValueError(
                f"Packaged grounded-shadow provenance changed for stock slot {stock_slot}"
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
    if bundle.handoff_manifest_sha256 is not None:
        if list(private_tile_indices) != list(range(len(bundle.records))):
            raise ValueError("Completed private TILE mapping is incomplete or reordered")
        records = []
        for record in bundle.records:
            item = {
                key: value
                for key, value in record.items()
                if key != "packaged_tile"
            }
            item["private_tile_index"] = private_tile_indices[record["record_index"]]
            records.append(item)
        return {
            "schema": "majesty-alchemist-approved-sprite-test-set-v2",
            "scope": "local compiled package; validated for deployment",
            "cache_policy": "fresh build; regular art cache bypassed and not updated",
            "handoff": {
                "manifest_sha256": bundle.handoff_manifest_sha256,
                "payload_aggregate_sha256": COMPLETED_HANDOFF_AGGREGATE_SHA256,
                "source_hashes": bundle.source_hashes,
            },
            "stock_clone": {
                "source_imag": "AVL1Warrior",
                "private_imag": "ALC1Alchemist",
                "private_tile_count": len(bundle.records),
                "patched_occurrence_count": len(bundle.imag_patches),
                "action_counts": COMPLETED_ACTION_COUNTS,
                "direction_order": list(DIRECTION_ORDER),
                "runtime_timing": "inherited byte-for-byte from stock AVL1Warrior IMAG",
                "mutation_boundary": "authorized low16 TILE words only",
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
            "interface_frames": list(interface_records),
            "records": records,
            "output": {
                "maindata_cam_sha256": sha256_file(output_cam),
            },
        }
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
            "authority": {
                "stock": "AVL1Warrior TILE 5919..5990 grounded contact",
                "contract_commit": PHANTOMS_SHADOW_CONTRACT_COMMIT,
                "contract_path": PHANTOMS_SHADOW_CONTRACT_PATH,
                "contract": (
                    "../majesty-gold-hd-custom-guild-phantoms-haunt/docs/"
                    "majesty-building-shadow-encoding.md"
                ),
                "grounding_implementation": (
                    "../majesty-gold-hd-custom-guild-phantoms-haunt/scripts/"
                    "generate_phantom_building_sprites.py:add_cast_shadow"
                ),
                "projection_geometry": (
                    "../majesty-gold-hd-custom-guild-phantoms-haunt/src/"
                    "build_phantom_guild.py:projected_floating_hero_shadow "
                    "central-mass and 0.44/0.36 terms only"
                ),
            },
            "algorithm": GROUNDED_SHADOW_POLICY,
            "algorithm_policy_sha256": GROUNDED_SHADOW_POLICY_SHA256,
            "output_indices": [247, 250],
            "body_precedence": "approved visible indices 1..246 win on overlap",
            "ground_contact": (
                "index 247 directly touches the lowest six body rows in every frame"
            ),
            "forbidden_analogue": (
                "projected_floating_hero_shadow deliberately clears body contact"
            ),
            "body_contract": "no crop, recenter, scale, palette, or visible-index changes",
            "expected_totals": EXPECTED_SHADOW_TOTALS,
            "expected_projected_bands": {
                str(index): count
                for index, count in EXPECTED_PROJECTED_SHADOW_BANDS.items()
            },
            "expected_retained_bands": {
                str(index): count
                for index, count in EXPECTED_RETAINED_SHADOW_BANDS.items()
            },
            "expected_body_conflict_bands": {
                str(index): count
                for index, count in EXPECTED_CONFLICT_SHADOW_BANDS.items()
            },
            "aggregate_plane_sha256": {
                "control": EXPECTED_CONTROL_PLANE_SHA256,
                "full": EXPECTED_FULL_INDEX_PLANE_SHA256,
                "body": EXPECTED_BODY_PLANE_SHA256,
            },
            "per_frame_hash_list_sha256": EXPECTED_FRAME_HASH_LIST_SHA256,
        },
        "source_hashes": bundle.source_hashes,
        "frames": records,
        "interface_frames": [dict(record) for record in interface_records],
        "output": {
            "maindata_cam": "Data/alchemist_maindata.cam",
            "maindata_cam_sha256": sha256_file(output_cam),
        },
    }
