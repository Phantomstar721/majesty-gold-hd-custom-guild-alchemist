from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


MAGENTA = (255, 0, 255)
HERO_RANGES = {
    "walk": (5919, 5983, 8),
    "stand": (5983, 5991, 1),
    "attack": (6055, 6119, 8),
}
WARRIOR_SPECIAL_GROUPS = (5991, 5994, 5997, 6001, 6005, 6009, 6013, 6017, 6020)
# Literal stock Warrior movement-slot order, verified in motion. Do not infer
# this mapping from how a decoded tile appears in isolation: doing so reverses
# the actor against its engine movement vector.
ENGINE_DIRECTION_MAP = (3, 4, 4, 5, 0, 1, 2, 2)
WALK_ENGINE_DIRECTIONS = (
    "north-v2.png",
    "northeast-v2.png",
    "east-v2.png",
    "southeast-v2.png",
    "south-v2.png",
    "southwest-v2.png",
    "west-v2.png",
    "northwest-v2.png",
)


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


def load_haunt_hero_module(repo: Path):
    path = (
        repo.parent
        / "majesty-gold-hd-custom-guild-phantoms-haunt"
        / "scripts"
        / "generate_phantom_hero_sprites.py"
    )
    spec = importlib.util.spec_from_file_location("proven_haunt_hero_pipeline", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load proven Haunt hero pipeline: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_walk_frames(image: Image.Image, haunt) -> list[Image.Image]:
    """Extract eight complete actors without assuming evenly spaced cells."""
    keyed = haunt.chroma_key(image.convert("RGBA"))
    alpha = keyed.getchannel("A")
    mask = alpha.load()
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for y in range(keyed.height):
        for x in range(keyed.width):
            if not mask[x, y] or (x, y) in seen:
                continue
            points: list[tuple[int, int]] = []
            stack = [(x, y)]
            seen.add((x, y))
            while stack:
                current_x, current_y = stack.pop()
                points.append((current_x, current_y))
                for neighbor_y in range(max(0, current_y - 1), min(keyed.height, current_y + 2)):
                    for neighbor_x in range(max(0, current_x - 1), min(keyed.width, current_x + 2)):
                        point = (neighbor_x, neighbor_y)
                        if mask[neighbor_x, neighbor_y] and point not in seen:
                            seen.add(point)
                            stack.append(point)
            components.append(points)

    if len(components) < 8:
        raise ValueError(f"Walk sheet contains only {len(components)} alpha components")
    bodies = sorted(components, key=len, reverse=True)[:8]
    body_sizes = [len(points) for points in bodies]
    if min(body_sizes) < max(body_sizes) * 0.62:
        raise ValueError(f"Walk sheet has an incomplete body component: {body_sizes}")
    bodies.sort(key=lambda points: sum(x for x, _y in points) / len(points))

    frames: list[Image.Image] = []
    for frame_index, points in enumerate(bodies):
        xs = [x for x, _y in points]
        ys = [y for _x, y in points]
        pad = 18
        crop_box = (
            max(0, min(xs) - pad),
            max(0, min(ys) - pad),
            min(keyed.width, max(xs) + 1 + pad),
            min(keyed.height, max(ys) + 1 + pad),
        )
        # Copy only the verified full-body component. Tiny detached chroma
        # fragments near the west/southwest actors otherwise survive the
        # Haunt proximity filter and flicker beside the hero in game.
        frame = Image.new(
            "RGBA",
            (crop_box[2] - crop_box[0], crop_box[3] - crop_box[1]),
            (0, 0, 0, 0),
        )
        frame_pixels = frame.load()
        keyed_pixels = keyed.load()
        for source_x, source_y in points:
            frame_pixels[source_x - crop_box[0], source_y - crop_box[1]] = keyed_pixels[
                source_x, source_y
            ]
        frame = haunt.prepare_frame(frame, "hover")
        # crop_alpha cannot invent padding where the authored sheet itself
        # ends (notably the rightmost actor). Give every isolated body a real,
        # symmetric safety canvas before it reaches TILE fitting.
        safety = 12
        padded = Image.new(
            "RGBA",
            (frame.width + safety * 2, frame.height + safety * 2),
            (0, 0, 0, 0),
        )
        padded.alpha_composite(frame, (safety, safety))
        frame = padded
        bounds = frame.getchannel("A").getbbox()
        if bounds is None:
            raise ValueError(f"Walk frame {frame_index} is empty")
        left, top, right, bottom = bounds
        if left < 5 or top < 5 or right > frame.width - 5 or bottom > frame.height - 5:
            raise ValueError(
                f"Walk frame {frame_index} lacks Haunt-style source padding: "
                f"{bounds} in {frame.size}"
            )
        frames.append(frame)
    return frames


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
        # The source is already one authored frame in the exact eight-frame
        # Warrior cycle. Do not add transforms that alter cadence or footing.
        pass
    elif action == "attack":
        angle = (-2, -5, -8, -3, 4, 7, 3, 0)[stage]
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
    haunt = load_haunt_hero_module(repo)
    direction_cells = grid(Image.open(repo / "assets/source/hero/directionals.png"), 3, 2)
    authored = direction_cells
    direction_frames = [authored[index] for index in ENGINE_DIRECTION_MAP]
    # Warrior owns eight genuinely different travel headings. The neutral and
    # one-pose action sheets can still use the approved six-view duplication,
    # but Walk may not: borrowing an oblique pose made west/southwest actors
    # visibly face northeast. Keep one authored eight-frame strip for each
    # literal Warrior engine direction and consume it without remapping.  The
    # stock Warrior movement slot order is the literal list above. Decoded
    # visual facing alone is not a valid substitute for an in-motion trace.
    walk_cycles = [
        extract_walk_frames(
            Image.open(repo / "assets/source/hero/walk-cycles-engine" / name),
            haunt,
        )
        for name in WALK_ENGINE_DIRECTIONS
    ]
    action_directions = {
        action: [cell[index] for index in ENGINE_DIRECTION_MAP]
        for action, cell in (
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
                source = walk_cycles[direction][stage]
            elif action == "attack":
                source = direction_frames[direction] if stage in (0, 3) else action_directions["attack"][direction]
            else:
                source = direction_frames[direction]
            image = transform_pose(source, action, stage, per_direction)
            image.save(out_dir / f"hero_tile_{tile_index:05d}.png")

    # Warrior Special and Cast share these exact 29 source tiles and their
    # stock sequencing.  Render each unique directional pose once; the cloned
    # Warrior IMAG retains its original repeated-frame order and timing.
    for direction in range(8):
        start = WARRIOR_SPECIAL_GROUPS[direction]
        end = WARRIOR_SPECIAL_GROUPS[direction + 1]
        for tile_index in range(start, end):
            stage = tile_index - start
            image = transform_pose(
                action_directions["cast"][direction], "cast", stage, end - start
            )
            image.save(out_dir / f"hero_tile_{tile_index:05d}.png")

    # Warrior's death lifecycle owns four unique directional collapse poses;
    # its stock IMAG then holds the last pose before switching to Dead tile
    # 6052. Preserve that lifecycle and only replace its private artwork.
    for tile_index in range(6020, 6052):
        direction = (tile_index - 6020) // 4
        stage = (tile_index - 6020) % 4
        base = action_directions["death"][direction]
        angle = (-7 if direction < 4 else 7) * stage
        fallen = base.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        fallen = fallen.resize(
            (fallen.width, max(1, round(fallen.height * (1.0 - stage * 0.16)))),
            Image.Resampling.LANCZOS,
        )
        fallen.save(out_dir / f"hero_tile_{tile_index:05d}.png")
    dead = action_directions["death"][4].rotate(
        -28, resample=Image.Resampling.BICUBIC, expand=True
    )
    dead = dead.resize(
        (dead.width, max(1, round(dead.height * 0.52))), Image.Resampling.LANCZOS
    )
    dead.save(out_dir / "hero_tile_06052.png")


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
    stock_prepare_building_source = module.prepare_building_source

    def prepare_lab_building_source(image, *args, **kwargs):
        # The Laboratory is wider than the Haunt art fitted by the shared
        # renderer.  Give the finished/damage silhouettes real pre-fit room so
        # Majesty's upper-left shadow projection can taper inside the fixed
        # Fervus TILE instead of being cut off at column zero.  Padding here is
        # intentional: render_variant includes it in its stock-shaped fit,
        # whereas padding the authored sheet would be removed by chroma_crop.
        source = stock_prepare_building_source(image, *args, **kwargs)
        pad_x = max(6, round(source.width * 0.07))
        pad_top = max(3, round(source.height * 0.025))
        # Level 3's foreground rail was visually clamped by the inherited
        # Fervus canvas. Preserve real transparent room below the body before
        # the stock fitter/shadow encoder runs; do not shift a finished frame.
        level = getattr(module, "_alchemist_render_level", 1)
        pad_bottom = (
            max(12, round(source.height * 0.065))
            if level == 3
            else pad_top
        )
        padded = Image.new(
            "RGBA",
            (source.width + pad_x * 2, source.height + pad_top + pad_bottom),
            (0, 0, 0, 0),
        )
        padded.alpha_composite(source, (pad_x, pad_top))
        return padded

    module.prepare_building_source = prepare_lab_building_source
    stock_state_x_offset = module.state_x_offset

    def lab_state_x_offset(variant_name, *, level):
        # The retained left tower makes the upgraded Laboratory footprint
        # asymmetric.  Center the actual ground footprint—not the transparent
        # source rectangle—inside the inherited Fervus canvas.
        return stock_state_x_offset(variant_name, level=level) + (8 if level in (2, 3) else 0)

    module.state_x_offset = lab_state_x_offset
    stock_add_cast_shadow = module.add_cast_shadow

    def add_lab_cast_shadow(image, shear=module.SHADOW_SHEAR, vertical_scale=module.SHADOW_VERTICAL_SCALE, **kwargs):
        # Use Haunt's exact projected-shadow implementation, but keep its
        # exposed foreground-clearance control nonzero for this wider Lab.
        # This leaves the projection exclusively northwest of the footprint
        # instead of wrapping the tall silhouette down its front-left edge.
        kwargs["shadow_bottom_clearance"] = max(
            42,
            kwargs.get("shadow_bottom_clearance", 0),
        )
        return stock_add_cast_shadow(image, shear, vertical_scale, **kwargs)

    module.add_cast_shadow = add_lab_cast_shadow
    # The approved Lab footprint is wider than the Haunt. Keep Majesty's
    # upper-left projection direction while shortening reach enough to retain
    # the mandatory transparent side gutter on the same Fervus canvases.
    module.SHADOW_PROFILES = {
        **module.SHADOW_PROFILES,
        "build_0": (0.02, 0.97),
        "build_1": (0.05, 0.94),
        "build_2": (0.10, 0.90),
        "inactive": (0.22, 0.80),
        "active": (0.22, 0.80),
        "damaged": (0.23, 0.82),
        "damaged_b": (0.20, 0.84),
        "collapsed_intermediate": (0.14, 0.90),
        "destroyed": (0.06, 0.94),
    }
    stock_gutter_validator = module.assert_transparent_side_gutter

    def validate_lab_gutter(image, *, label, include_top=False):
        # Haunt's boundary check caught the original clipping regression.  The
        # Laboratory needs a wider, visible taper because its footprint nearly
        # fills the Fervus canvas.  Never "repair" a finished frame by shifting
        # it after shadow generation: that merely transfers clipping to the
        # opposite edge.
        stock_gutter_validator(image, label=label, include_top=include_top)
        bbox = image.convert("RGBA").getchannel("A").getbbox()
        if bbox and (bbox[0] < 6 or bbox[2] > image.width - 6):
            raise ValueError(
                f"{label} lacks the Laboratory's six-pixel side safety gutter: {bbox}"
            )

    module.assert_transparent_side_gutter = validate_lab_gutter
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
        # Haunt's proven state rule: active and inactive share one canonical
        # architecture silhouette. Activity is expressed only by the stock
        # animation color pulse. This prevents occupancy from moving walls,
        # roofs, shadows, or hotspots and removes L3's active-only roof hole.
        variants = {
            "inactive": cells[0],
            "active": cells[0],
            "damaged": cells[4],
            "damaged_b": cells[5],
            "collapsed_intermediate": cells[6],
            "destroyed": cells[7],
        }
        # Haunt's renderer already conforms construction art to the inherited
        # fixed canvas. Do not inset it a second time: the double scale made
        # upgrade scaffolds markedly smaller than the completed structure.
        if level == 1:
            construction_sources = (cells[2], cells[2], cells[3])
        else:
            construction_sources = (
                chroma_crop(Image.open(repo / f"assets/source/buildings/lab/level-{level}/construction-early-v{3 if level == 3 else 2}.png")),
                chroma_crop(Image.open(repo / f"assets/source/buildings/lab/level-{level}/construction-early-v{3 if level == 3 else 2}.png")),
                chroma_crop(Image.open(repo / f"assets/source/buildings/lab/level-{level}/construction-late-v2.png")),
            )
        construction_scales = {
            1: (0.97, 0.97, 0.97),
            # The additive late-upgrade masters contain the entire prior
            # building plus outward scaffolding. Give only those broad late
            # silhouettes enough side gutter for Haunt's fixed TILE check.
            2: (0.97, 0.97, 0.90),
            # Haunt's level-3 late-frame renderer already applies its own
            # 0.84 safety fit. A second 0.90 inset made the Lab visibly shrink
            # between its early frame and completed state.
            3: (0.94, 0.94, 0.99),
        }[level]
        construction = {
            stage: inset_source(source, construction_scales[stage])
            for stage, source in enumerate(construction_sources)
        }
        out_dir = out_root / f"level-{level}"
        out_dir.mkdir(parents=True, exist_ok=True)
        specs = module.TILE_SPECS_BY_LEVEL[level]
        module._alchemist_render_level = level
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
    brew.thumbnail((19, 19), Image.Resampling.LANCZOS)
    brew.save(out_dir / "brewing-button-icon-19.png")
    vigor = Image.open(repo / "assets/source/interface/vigor-elixir-icon-v1.png").convert("RGB")
    vigor.resize((32, 32), Image.Resampling.LANCZOS).filter(ImageFilter.SHARPEN).resize(
        (24, 24), Image.Resampling.LANCZOS
    ).save(out_dir / "vigor-elixir-icon-24.png")


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
