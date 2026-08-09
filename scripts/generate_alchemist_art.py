from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


MAGENTA = (255, 0, 255)
HERO_RANGES = {
    "walk": (3934, 3998, 8),
    "stand": (3998, 4006, 1),
    "special": (4006, 4038, 4),
    "attack": (4038, 4070, 4),
    "cast": (4070, 4102, 4),
}
ENGINE_DIRECTION_MAP = (3, 2, 2, 1, 0, 5, 4, 4)


def chroma_crop(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    px = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = px[x, y]
            keyed = a == 0 or (r > 205 and b > 175 and g < 105 and r > g * 1.7 and b > g * 1.5)
            if keyed:
                px[x, y] = (0, 0, 0, 0)
            elif r > 75 and b > 65 and abs(r - b) < 95 and r + b > g * 2.15:
                # Despill generated antialiasing without deleting dark outlines.
                px[x, y] = (min(r, g + 20), g, min(b, g + 20), a)
    # Peel only purple-dominant pixels connected to the transparent exterior.
    # This removes the generator's soft chroma fringe without eroding copper,
    # skin, green cloth, or internally enclosed dark outlines.
    for _ in range(4):
        remove: list[tuple[int, int]] = []
        for y in range(image.height):
            for x in range(image.width):
                r, g, b, a = px[x, y]
                if not a or not (r > 55 and b > 50 and abs(r - b) < 90 and r + b > g * 2.05):
                    continue
                if any(
                    px[nx, ny][3] == 0
                    for ny in range(max(0, y - 1), min(image.height, y + 2))
                    for nx in range(max(0, x - 1), min(image.width, x + 2))
                ):
                    remove.append((x, y))
        if not remove:
            break
        for x, y in remove:
            px[x, y] = (0, 0, 0, 0)
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else Image.new("RGBA", (1, 1))


def grid(image: Image.Image, columns: int, rows: int) -> list[Image.Image]:
    w, h = image.size
    result = []
    for row in range(rows):
        for column in range(columns):
            left = column * w // columns
            right = (column + 1) * w // columns
            top = row * h // rows
            bottom = (row + 1) * h // rows
            result.append(keep_primary_component(chroma_crop(image.crop((left, top, right, bottom)))))
    return result


def keep_primary_component(image: Image.Image) -> Image.Image:
    """Discard detached cross-cell artifacts while retaining the main silhouette."""
    alpha = image.getchannel("A")
    points = {(x, y) for y in range(image.height) for x in range(image.width) if alpha.getpixel((x, y))}
    components: list[set[tuple[int, int]]] = []
    while points:
        seed = points.pop()
        component = {seed}
        stack = [seed]
        while stack:
            x, y = stack.pop()
            for ny in range(max(0, y - 1), min(image.height, y + 2)):
                for nx in range(max(0, x - 1), min(image.width, x + 2)):
                    point = (nx, ny)
                    if point in points:
                        points.remove(point)
                        component.add(point)
                        stack.append(point)
        components.append(component)
    if not components:
        return image
    primary = max(components, key=lambda component: (len(component), max(y for _, y in component)))
    px = image.load()
    for component in components:
        if component is primary:
            continue
        for x, y in component:
            px[x, y] = (0, 0, 0, 0)
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else image


def transform_pose(base: Image.Image, action: str, stage: int, count: int) -> Image.Image:
    phase = stage / max(1, count - 1)
    image = base.copy()
    if action == "walk":
        bob = (0, -2, -3, -2, 0, 1, 0, -1)[stage % 8]
        shear = (-0.035, -0.02, 0.0, 0.025, 0.035, 0.02, 0.0, -0.025)[stage % 8]
        image = image.transform(
            (image.width, image.height),
            Image.Transform.AFFINE,
            (1, shear, -shear * image.height / 2, 0, 1, -bob),
            Image.Resampling.BICUBIC,
        )
    elif action == "attack":
        angle = (-8, -3, 5, 0)[stage]
        image = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    elif action == "cast":
        image = ImageEnhance.Brightness(image).enhance(0.94 + phase * 0.15)
        image = ImageEnhance.Color(image).enhance(1.0 + phase * 0.10)
    elif action == "special":
        scale = (0.98, 1.0, 1.025, 1.0)[stage]
        image = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height / scale))),
            Image.Resampling.LANCZOS,
        )
    return image


def generate_hero(repo: Path, out_dir: Path) -> None:
    direction_cells = grid(Image.open(repo / "assets/source/hero/directionals.png"), 3, 2)
    authored = direction_cells
    direction_frames = [authored[index] for index in ENGINE_DIRECTION_MAP]
    action_directions = {
        action: [cell[index] for index in ENGINE_DIRECTION_MAP]
        for action, cell in (
            ("walk", grid(Image.open(repo / "assets/source/hero/walk-directionals.png"), 3, 2)),
            ("attack", grid(Image.open(repo / "assets/source/hero/attack-directionals.png"), 3, 2)),
            ("cast", grid(Image.open(repo / "assets/source/hero/cast-directionals.png"), 3, 2)),
            ("death", grid(Image.open(repo / "assets/source/hero/death-directionals.png"), 3, 2)),
        )
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for action, (start, end, per_direction) in HERO_RANGES.items():
        for tile_index in range(start, end):
            relative = tile_index - start
            direction = relative // per_direction
            stage = relative % per_direction
            if action == "walk":
                source = direction_frames[direction] if stage in (0, 4) else action_directions["walk"][direction]
            elif action == "attack":
                source = direction_frames[direction] if stage in (0, 3) else action_directions["attack"][direction]
            elif action in ("cast", "special"):
                source = direction_frames[direction] if stage == 0 else action_directions["cast"][direction]
            else:
                source = direction_frames[direction]
            image = transform_pose(source, action, stage, per_direction)
            image.save(out_dir / f"hero_tile_{tile_index:05d}.png")

    # Cultist death is a stock two-part lifecycle: 16 directional body frames,
    # followed by 19 shared settle/fade frames. Preserve those counts exactly.
    for tile_index in range(4102, 4118):
        direction = (tile_index - 4102) // 2
        stage = (tile_index - 4102) % 2
        base = action_directions["death"][direction]
        angle = (-10 if direction < 4 else 10) * stage
        fallen = base.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        fallen = fallen.resize((fallen.width, max(1, round(fallen.height * (1.0 - stage * 0.24)))), Image.Resampling.LANCZOS)
        fallen.save(out_dir / f"hero_tile_{tile_index:05d}.png")
    shared = action_directions["death"][4].rotate(-28, resample=Image.Resampling.BICUBIC, expand=True)
    shared = shared.resize((shared.width, max(1, round(shared.height * 0.62))), Image.Resampling.LANCZOS)
    for tile_index in range(4118, 4137):
        stage = tile_index - 4118
        alpha = max(0.0, 1.0 - stage / 18.0)
        image = shared.copy()
        channel = image.getchannel("A").point(lambda value, a=alpha: round(value * a))
        image.putalpha(channel)
        if stage > 8:
            image = image.filter(ImageFilter.GaussianBlur((stage - 8) * 0.10))
        image.save(out_dir / f"hero_tile_{tile_index:05d}.png")


def load_haunt_building_module(repo: Path):
    path = repo.parent / "majesty-gold-hd-custom-guild-phantoms-haunt" / "scripts" / "generate_phantom_building_sprites.py"
    spec = importlib.util.spec_from_file_location("stock_building_pipeline", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load proven Haunt building pipeline: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Keep the proven geometry/shadow/seam pipeline while removing only the
    # Phantom-specific ice recolor and cyan pulse.
    module.grade_for_ice_palette = lambda image: image
    module.pulse_cyan = pulse_alchemy
    # The approved Lab footprint is wider than the Haunt. Keep Majesty's
    # upper-left projection direction while shortening reach enough to retain
    # the mandatory transparent side gutter on the same Fervus canvases.
    module.SHADOW_PROFILES = {
        **module.SHADOW_PROFILES,
        "build_0": (0.08, 0.95),
        "build_1": (0.20, 0.89),
        "build_2": (0.30, 0.84),
        "inactive": (0.34, 0.80),
        "active": (0.34, 0.80),
        "damaged": (0.35, 0.82),
        "damaged_b": (0.31, 0.84),
        "collapsed_intermediate": (0.20, 0.90),
        "destroyed": (0.09, 0.94),
    }
    stock_gutter_validator = module.assert_transparent_side_gutter

    def repair_and_validate_gutter(image, *, label, include_top=False):
        # The Lab is asymmetrically wider on its shadow-facing side. Preserve
        # every pixel by translating the complete encoded body+shadow layer
        # into the stock canvas before applying the untouched Haunt validator.
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        bbox = alpha.getbbox()
        if bbox and bbox[0] < 2:
            shift = 2 - bbox[0]
            moved = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
            moved.alpha_composite(rgba, (shift, 0))
            image.paste(moved)
        stock_gutter_validator(image, label=label, include_top=include_top)

    module.assert_transparent_side_gutter = repair_and_validate_gutter
    return module


def pulse_alchemy(image: Image.Image, pulse: float) -> Image.Image:
    output = image.copy().convert("RGBA")
    px = output.load()
    for y in range(output.height):
        for x in range(output.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            liquid = g > 75 and g > r * 1.08 and g > b * 1.05
            copper = r > 85 and r > g * 1.25 and g > b * 1.15
            if liquid or copper:
                px[x, y] = (
                    min(255, round(r * pulse)),
                    min(255, round(g * pulse)),
                    min(255, round(b * (1.0 + (pulse - 1.0) * 0.45))),
                    a,
                )
    return output


def inset_source(image: Image.Image, scale: float) -> Image.Image:
    width = max(1, round(image.width * scale))
    height = max(1, round(image.height * scale))
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
    canvas.alpha_composite(resized, ((image.width - width) // 2, image.height - height))
    return canvas


def generate_buildings(repo: Path, out_root: Path) -> None:
    module = load_haunt_building_module(repo)
    for level in (1, 2, 3):
        cells = grid(Image.open(repo / f"assets/source/buildings/lab/level-{level}/states.png"), 4, 2)
        variants = {
            "inactive": cells[0],
            "active": cells[1],
            "damaged": cells[4],
            "damaged_b": cells[5],
            "collapsed_intermediate": cells[6],
            "destroyed": cells[7],
        }
        # Fervus's fixed construction canvases reserve narrow transparent side
        # gutters for the engine shadow seam. Keep the authored footprint but
        # inset the high-resolution construction paintings before conformance.
        construction = {
            0: inset_source(cells[2], 0.78),
            1: inset_source(cells[2], 0.78),
            2: inset_source(cells[3], 0.82),
        }
        out_dir = out_root / f"level-{level}"
        out_dir.mkdir(parents=True, exist_ok=True)
        specs = module.TILE_SPECS_BY_LEVEL[level]
        for tile_index, (variant, width, height) in specs.items():
            image = module.render_variant(variants, variant, width, height, construction, level=level)
            image.save(out_dir / f"building_tile_{tile_index:05d}.png")
        width, height = next((w, h) for name, w, h in specs.values() if name == "active_0")
        for frame in range(module.ACTIVE_FRAME_COUNT):
            image = module.render_variant(variants, f"active_{frame}", width, height, construction, level=level)
            image.save(out_dir / f"building_active_frame_{frame:02d}.png")


def fit_panel(source: Path, target: Path) -> None:
    image = Image.open(source).convert("RGB")
    ratio = 200 / 245
    current = image.width / image.height
    if current > ratio:
        width = round(image.height * ratio)
        left = (image.width - width) // 2
        image = image.crop((left, 0, left + width, image.height))
    else:
        height = round(image.width / ratio)
        top = (image.height - height) // 2
        image = image.crop((0, top, image.width, top + height))
    image.resize((200, 245), Image.Resampling.LANCZOS).save(target)


def generate_interface(repo: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fit_panel(repo / "assets/source/interface/building-panel.png", out_dir / "building-panel-200x245.png")
    fit_panel(repo / "assets/source/interface/brewing-panel.png", out_dir / "brewing-panel-200x245.png")
    portrait = Image.open(repo / "assets/source/interface/building-portrait.png").convert("RGB")
    portrait.resize((100, 100), Image.Resampling.LANCZOS).save(out_dir / "building-portrait-100.png")
    icon = Image.open(repo / "assets/source/interface/building-icon.png").convert("RGB")
    icon.resize((34, 34), Image.Resampling.LANCZOS).filter(ImageFilter.SMOOTH_MORE).resize((25, 25), Image.Resampling.LANCZOS).save(out_dir / "building-icon-25.png")
    hero = Image.open(repo / "assets/source/hero/portrait.png").convert("RGB")
    w, h = hero.size
    hero = hero.crop((round(w * .14), round(h * .05), round(w * .86), round(h * .80)))
    hero.resize((34, 34), Image.Resampling.LANCZOS).filter(ImageFilter.SMOOTH_MORE).resize((25, 25), Image.Resampling.LANCZOS).save(out_dir / "hero-icon-25.png")
    brew = chroma_crop(Image.open(repo / "assets/source/interface/brewing-button-icon.png"))
    brew.thumbnail((16, 16), Image.Resampling.LANCZOS)
    brew.save(out_dir / "brewing-button-icon-16.png")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    generate_hero(args.repo, args.out_dir / "hero")
    generate_buildings(args.repo, args.out_dir / "buildings")
    generate_interface(args.repo, args.out_dir / "interface")
    print(f"Generated Alchemist art at {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
