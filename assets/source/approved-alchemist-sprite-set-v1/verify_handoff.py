from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys


ROOT = Path(__file__).resolve().parent
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
NON_PAYLOAD = {
    "manifest.json",
    "PAYLOAD_SHA256SUMS.txt",
    "README.md",
    "verify_handoff.py",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(relative: str) -> dict:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{relative} is not a JSON object")
    return value


def png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    require(
        len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n",
        f"not a PNG: {path}",
    )
    return struct.unpack(">II", header[16:24])


def require_file_hash(relative: str, expected: str, label: str) -> None:
    path = ROOT / relative
    require(path.is_file(), f"{label} is missing: {relative}")
    actual = sha256_file(path)
    require(actual == expected, f"{label} hash changed: {relative}: {actual}")


def validate_payload(manifest: dict) -> None:
    integrity = manifest["payload_integrity"]
    records = integrity["files"]
    expected_paths = [record["path"] for record in records]
    require(len(expected_paths) == len(set(expected_paths)), "duplicate payload path")
    require(expected_paths == sorted(expected_paths), "payload paths are not sorted")

    actual_paths = sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path.name not in NON_PAYLOAD
    )
    require(
        actual_paths == expected_paths,
        "payload inventory differs from manifest",
    )

    lines: list[str] = []
    total_bytes = 0
    for record in records:
        relative = record["path"]
        path = ROOT / relative
        size = path.stat().st_size
        digest = sha256_file(path)
        require(size == record["bytes"], f"byte count changed: {relative}")
        require(digest == record["sha256"], f"SHA-256 changed: {relative}")
        total_bytes += size
        lines.append(f"{digest}  {relative}")

    canonical = ("\n".join(lines) + "\n").encode("utf-8")
    aggregate = hashlib.sha256(canonical).hexdigest()
    require(len(records) == integrity["file_count"], "payload count changed")
    require(total_bytes == integrity["total_bytes"], "payload byte total changed")
    require(
        aggregate == integrity["aggregate_sha256"],
        "payload aggregate SHA-256 changed",
    )
    require(
        (ROOT / "PAYLOAD_SHA256SUMS.txt").read_text(encoding="utf-8")
        == canonical.decode("utf-8"),
        "PAYLOAD_SHA256SUMS.txt differs from the canonical manifest inventory",
    )


def validate_geometry() -> None:
    expected_png_sets = {
        "stand": (8, (96, 92)),
        "attack": (64, (96, 92)),
        "cast": (48, (96, 92)),
        "special": (56, (96, 92)),
        "death": (32, (112, 92)),
        "dead": (1, (35, 33)),
    }
    for action, (count, expected_size) in expected_png_sets.items():
        paths = sorted((ROOT / action).rglob("*.png"))
        require(len(paths) == count, f"{action} PNG count changed")
        for path in paths:
            require(png_size(path) == expected_size, f"{action} canvas changed: {path}")

    walk_paths = sorted((ROOT / "walk").rglob("*.tile"))
    require(len(walk_paths) == 64, "Walk TILE count changed")
    for path in walk_paths:
        data = path.read_bytes()
        require(len(data) >= 26, f"truncated Walk TILE: {path}")
        version, height, width = struct.unpack_from("<3H", data, 0)
        hotspot_x, hotspot_y = struct.unpack_from("<2H", data, 10)
        palette_mode = struct.unpack_from("<H", data, 20)[0]
        palette_reference = struct.unpack_from("<I", data, 22)[0]
        require(
            (version, width, height) == (3, 96, 92),
            f"Walk TILE header changed: {path}",
        )
        require(
            (hotspot_x, hotspot_y) == (48, 70),
            f"Walk TILE hotspot changed: {path}",
        )
        require(palette_mode == 0, f"Walk TILE is not external-palette mode: {path}")
        require(
            palette_reference == 0xFFFFFFFF,
            f"Walk TILE lost unresolved palette sentinel: {path}",
        )


def validate_provenance() -> None:
    walk = load_json("provenance/walk-review.json")
    walk_records = walk["indexed"]["records"]
    require(len(walk_records) == 64, "Walk provenance record count changed")
    for record in walk_records:
        target = (
            f"walk/{record['direction']}/"
            f"{Path(record['tile_path']).name}"
        )
        require_file_hash(target, record["tile_sha256"], "Walk frame")

    stand = load_json("provenance/stand-review.json")
    require(len(stand["frames"]) == 8, "Stand provenance frame count changed")
    for record in stand["frames"]:
        source = record["native"]["alchemist_soft_b"]
        target = f"stand/{record['direction']}/frame-00-soft-b.png"
        require_file_hash(target, stand["output_sha256"][source], "Stand frame")
    require_file_hash(
        "provenance/stand-render.json",
        stand["renderer_provenance_sha256"],
        "Stand render provenance",
    )

    attack = load_json("provenance/attack-review.json")
    require(len(attack["records"]) == 64, "Attack provenance frame count changed")
    for record in attack["records"]:
        target = f"attack/{record['direction']}/{Path(record['soft_b']).name}"
        require_file_hash(target, record["soft_b_sha256"], "Attack frame")
    require_file_hash(
        "provenance/attack-render.json",
        attack["render_provenance_sha256"],
        "Attack render provenance",
    )

    cast = load_json("provenance/cast-review.json")
    cast_records = [record for record in cast["frames"] if record["action"] == "cast"]
    require(len(cast_records) == 48, "Cast provenance frame count changed")
    for record in cast_records:
        source = record["native"]["soft_b"]
        target = f"cast/{record['direction']}/{Path(source).name}"
        require_file_hash(target, cast["output_sha256"][source], "Cast frame")
    require_file_hash(
        "provenance/cast-render.json",
        cast["renderer_provenance_sha256"],
        "Cast render provenance",
    )

    special = load_json("provenance/special-review.json")
    special_records = [
        record for record in special["frames"] if record["action"] == "special"
    ]
    require(len(special_records) == 56, "Special provenance frame count changed")
    for record in special_records:
        source = record["native"]["soft_b"]
        target = f"special/{record['direction']}/{Path(source).name}"
        require_file_hash(target, special["output_sha256"][source], "Special frame")
    require_file_hash(
        "provenance/special-render.json",
        special["renderer_provenance_sha256"],
        "Special render provenance",
    )

    death = load_json("provenance/death-review.json")
    death_records = death["outputs"]["frame_records"]
    require(len(death_records) == 32, "Death provenance frame count changed")
    for record in death_records:
        target = f"death/{record['direction']}/{Path(record['soft_b']).name}"
        require_file_hash(target, record["soft_b_sha256"], "Death frame")
    require_file_hash(
        "provenance/death-render.json",
        death["renderer"]["provenance_sha256"],
        "Death render provenance",
    )

    grave = load_json("provenance/gravestone-review.json")
    require_file_hash(
        "dead/alchemist-gravestone-B-native-35x33.png",
        grave["artifacts"]["native/alchemist-gravestone-B-native-35x33.png"],
        "Gravestone B",
    )


def validate_contract(manifest: dict) -> None:
    require(
        manifest["schema_version"] == 1
        and manifest["bundle_id"]
        == "majesty-alchemist-approved-humanoid-sprite-set-v1",
        "handoff manifest identity changed",
    )
    require(manifest["game_loadable"] is False, "handoff unexpectedly claims loadability")
    require(manifest["direction_order"] == list(DIRECTIONS), "direction order changed")
    require_file_hash(
        manifest["stock_authority"]["authority_path"],
        manifest["stock_authority"]["authority_sha256"],
        "Warrior action authority",
    )
    expected_counts = {
        "walk": 64,
        "stand": 8,
        "attack": 64,
        "cast": 48,
        "special": 56,
        "death": 32,
        "dead": 1,
    }
    for action, count in expected_counts.items():
        require(
            manifest["action_sets"][action]["file_count"] == count,
            f"{action} contract count changed",
        )


def main() -> int:
    manifest = load_json("manifest.json")
    validate_contract(manifest)
    validate_payload(manifest)
    validate_geometry()
    validate_provenance()
    print(
        "PASS: approved Alchemist handoff; "
        f"{manifest['payload_integrity']['file_count']} payload files; "
        f"aggregate {manifest['payload_integrity']['aggregate_sha256']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)

