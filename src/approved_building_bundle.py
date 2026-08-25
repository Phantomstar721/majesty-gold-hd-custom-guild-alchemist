from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
from typing import Any, Sequence

from PIL import Image


HANDOFF_SCHEMA = "majesty-building-sprite-handoff/accepted-as-is-v1"
LIFECYCLE_SCHEMA = "alchemist-building-sprite-lifecycle-map/accepted-as-is-v1"
AUTHORITY_SCHEMA = "majesty-building-stock-authority/v1"
HANDOFF_SHA256 = "6361ca46b0b6b920bb2742100a2feba495e35faa66684f2839474f0009bbccb8"
LIFECYCLE_SHA256 = "f2e92661f7d88eed18f00a5198509d6d2e634602b51f31fd098d01341c05e947"
CHECKSUMS_SHA256 = "8f13f52c984a5febcf99adc22e7987e7034a118c75a9b433c75da3a3ea44dfc7"
PAYLOAD_AGGREGATE_SHA256 = "a658e3a7ca6458895cf22c210043ca1f9da9267ac312e621a9b4de9a7d8187c5"
SOURCE_CAM_SHA256 = "92b1a4caa111495aebe483e5617c7cc4f291eb1d897877860cfbdbc632a0d213"
SOURCE_PALETTE_INDEX = 68
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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


@dataclass(frozen=True)
class ApprovedBuildingBundle:
    root: Path
    source_imags: tuple[bytes, bytes, bytes]
    states_by_level: tuple[
        tuple[ApprovedBuildingState, ...],
        tuple[ApprovedBuildingState, ...],
        tuple[ApprovedBuildingState, ...],
    ]


def _verify_transfer_checksums(root: Path) -> None:
    checksums_path = root / "checksums.sha256"
    if sha256_file(checksums_path) != CHECKSUMS_SHA256:
        raise ValueError("Approved building transfer checksum list changed")
    rows = checksums_path.read_text(encoding="ascii").splitlines()
    if len(rows) != 116:
        raise ValueError(f"Approved building transfer expected 116 files, found {len(rows)}")
    for row in rows:
        expected, relative = row.split("  ", 1)
        path = root / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Approved building transfer changed: {relative}")


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


def load_approved_building_bundle(
    root: Path,
    stock: Any,
    source_cam: Path,
    tiles: Sequence[Any],
    palettes: Sequence[Any],
) -> ApprovedBuildingBundle:
    _verify_transfer_checksums(root)
    handoff = _load_json(root / "handoff.json", HANDOFF_SHA256)
    lifecycle = _load_json(
        root / "integration" / "lifecycle-map.json", LIFECYCLE_SHA256
    )
    authority = _load_json(root / "authority" / "stock-authority.json")
    if handoff.get("schema") != HANDOFF_SCHEMA:
        raise ValueError("Approved building handoff schema changed")
    if lifecycle.get("schema") != LIFECYCLE_SCHEMA:
        raise ValueError("Approved building lifecycle schema changed")
    if authority.get("schema") != AUTHORITY_SCHEMA:
        raise ValueError("Approved building stock authority schema changed")
    if handoff.get("payload_aggregate_sha256") != PAYLOAD_AGGREGATE_SHA256:
        raise ValueError("Approved building payload aggregate changed")
    if handoff.get("state_count") != 25 or lifecycle.get("state_count") != 25:
        raise ValueError("Approved building handoff no longer covers 25 states")
    if sha256_file(source_cam) != SOURCE_CAM_SHA256:
        raise ValueError("Retail maindata.cam no longer matches Marketplace authority")
    _validate_palette(stock, root, palettes)

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
        expected_canvas = tuple(item.get("source_canvas", ()))
        if decoded is None or (decoded[1], decoded[0]) != expected_canvas:
            raise ValueError(f"Marketplace source canvas changed: {key}")

        relative = item.get("indexed_object")
        object_path = root / relative
        expected_object_hash = item.get("indexed_object_sha256")
        if not object_path.is_file() or sha256_file(object_path) != expected_object_hash:
            raise ValueError(f"Approved indexed building object changed: {key}")
        with Image.open(object_path) as loaded:
            image = loaded.copy()
        rows, controls, body_bbox, shadow_bbox = _state_pixel_metrics(image)
        object_canvas = tuple(item.get("object_canvas", ()))
        if image.size != object_canvas or (len(rows[0]), len(rows)) != object_canvas:
            raise ValueError(f"Approved indexed building canvas changed: {key}")
        expected_controls = {
            int(index): count for index, count in item.get("control_counts", {}).items()
        }
        if controls != expected_controls:
            raise ValueError(f"Approved building shadow controls changed: {key}")
        if body_bbox != tuple(item.get("body_bbox_in_object", ())):
            raise ValueError(f"Approved building body bounds changed: {key}")
        if shadow_bbox != tuple(item.get("shadow_bbox_in_object", ())):
            raise ValueError(f"Approved building shadow bounds changed: {key}")
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
                body_bbox_in_object=tuple(item["body_bbox_in_object"]),
                shadow_bbox_in_object=tuple(item["shadow_bbox_in_object"]),
                control_counts=expected_controls,
                occurrences=occurrences,
            )
        )
        seen_keys.add(key)
    if len(seen_keys) != 25 or seen_keys != set(concepts_by_key):
        raise ValueError("Approved building lifecycle does not match Marketplace concepts")
    return ApprovedBuildingBundle(
        root=root,
        source_imags=(source_imags[0], source_imags[1], source_imags[2]),
        states_by_level=(tuple(states[0]), tuple(states[1]), tuple(states[2])),
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
    source_hotspot_x, source_hotspot_y = struct.unpack_from("<hh", template, 10)
    offset_x, offset_y = state.body_source_offset_in_object
    hotspot_x = source_hotspot_x + offset_x
    hotspot_y = source_hotspot_y + offset_y
    if not (-0x8000 <= hotspot_x <= 0x7FFF and -0x8000 <= hotspot_y <= 0x7FFF):
        raise ValueError(f"Approved building hotspot is out of range: {state.concept_key}")
    struct.pack_into("<hh", encoded, 10, hotspot_x, hotspot_y)
    if encoded[:2] != template[:2] or encoded[8:10] != template[8:10] or encoded[14:26] != template[14:26]:
        raise AssertionError(f"Approved building TILE header topology changed: {state.concept_key}")
    decoded = stock.decode_indexed_v3_tile(bytes(encoded))
    if decoded is None or decoded[2] != rows:
        raise AssertionError(f"Approved building TILE did not decode losslessly: {state.concept_key}")
    if stock.tile_palette_index(bytes(encoded)) != SOURCE_PALETTE_INDEX:
        raise AssertionError(f"Approved building TILE lost Marketplace palette: {state.concept_key}")
    return bytes(encoded)


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
    """Fail closed unless the output is a literal private Marketplace clone."""

    from approved_sprite_bundle import validate_split_control_segments

    if len(private_indices_by_level) != 3 or len(output_imag_names) != 3:
        raise ValueError("Approved building package must contain three levels")
    output_tiles = stock.read_cam_entries(output_cam, b"TILE")
    output_palettes = stock.read_cam_entries(output_cam, b"SPLT")
    if (
        len(output_palettes) <= SOURCE_PALETTE_INDEX
        or output_palettes[SOURCE_PALETTE_INDEX].data
        != stock_palettes[SOURCE_PALETTE_INDEX].data
    ):
        raise ValueError("Approved building package changed Marketplace palette 68")

    records_by_private = {record["private_tile_index"]: record for record in records}
    if len(records_by_private) != 25:
        raise ValueError("Approved building package does not contain 25 private states")
    seen_private: set[int] = set()
    for states, private_indices in zip(
        bundle.states_by_level, private_indices_by_level
    ):
        if set(private_indices) != {state.source_tile_index for state in states}:
            raise ValueError("Approved building private TILE map is incomplete")
        for state in states:
            private_index = private_indices[state.source_tile_index]
            if private_index in seen_private or private_index >= len(output_tiles):
                raise ValueError("Approved building private TILE index is invalid")
            seen_private.add(private_index)
            entry = output_tiles[private_index]
            expected_prefix = f"ALB{state.level}State".encode("ascii")
            if not entry.name.rstrip(b"\x00").startswith(expected_prefix):
                raise ValueError("Approved building private TILE name changed")
            record = records_by_private.get(private_index)
            if record is None or sha256_bytes(entry.data) != record["packaged_tile_sha256"]:
                raise ValueError(f"Approved building TILE changed: {state.concept_key}")
            if stock.tile_palette_index(entry.data) != SOURCE_PALETTE_INDEX:
                raise ValueError("Approved building private TILE lost palette 68")
            decoded = stock.decode_indexed_v3_tile(entry.data)
            if decoded is None or (decoded[1], decoded[0]) != state.object_canvas:
                raise ValueError("Approved building private TILE canvas changed")
            with Image.open(state.indexed_object_path) as loaded:
                expected_flat = list(loaded.getdata())
            actual_flat = [value for row in decoded[2] for value in row]
            if actual_flat != expected_flat:
                raise ValueError("Approved building private indexed object changed")
            source_hotspot = struct.unpack_from(
                "<hh", stock_tiles[state.source_tile_index].data, 10
            )
            expected_hotspot = (
                source_hotspot[0] + state.body_source_offset_in_object[0],
                source_hotspot[1] + state.body_source_offset_in_object[1],
            )
            if struct.unpack_from("<hh", entry.data, 10) != expected_hotspot:
                raise ValueError("Approved building private TILE anchor changed")
            validate_split_control_segments(entry.data)

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
        actual = stock.read_cam_entry(output_cam, b"IMAG", output_name).data
        if actual != expected:
            raise ValueError(
                f"Approved building level {level} changed Marketplace topology"
            )
