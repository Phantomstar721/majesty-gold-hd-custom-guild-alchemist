import json
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import build_alchemist_probe as builder
import alchemist_art_package as art_package
import approved_sprite_bundle as sprite_bundle


class AlchemistProbeTests(unittest.TestCase):
    def test_approved_sprite_bundle_is_hash_pinned_and_covers_only_walk_stand(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        stock = art_package.load_stock_pipeline(repo)
        retail = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\maindata.cam"
        )
        tiles = stock.read_cam_entries(retail, b"TILE")
        palettes = stock.read_cam_entries(retail, b"SPLT")
        warrior_imag = stock.read_cam_entry(
            retail, b"IMAG", art_package.HERO_SOURCE
        ).data
        bundle = sprite_bundle.load_approved_sprite_bundle(
            builder.APPROVED_SPRITE_PIPELINE_ROOT,
            stock,
            retail,
            tiles,
            palettes,
            warrior_imag,
        )
        self.assertEqual(bundle.private_palette_index, len(palettes))
        self.assertEqual(bundle.private_palette_index, 854)
        self.assertEqual(
            sorted(bundle.tiles_by_stock_slot), list(range(5919, 5991))
        )
        self.assertEqual(
            [record["direction"] for record in bundle.records[:64:8]],
            list(sprite_bundle.DIRECTION_ORDER),
        )
        self.assertEqual(
            [record["direction"] for record in bundle.records[64:]],
            list(sprite_bundle.DIRECTION_ORDER),
        )
        private_colours = stock.splt_palette_colors(bundle.private_palette_data)
        visible = private_colours[1:247]
        self.assertEqual(
            sprite_bundle.palette_content_sha256(visible),
            sprite_bundle.PALETTE_CONTENT_SHA256,
        )
        self.assertEqual(
            {index: private_colours[index] for index in sprite_bundle.CONTROL_RGB},
            sprite_bundle.CONTROL_RGB,
        )

        shadow_totals = {
            "projected": sum(
                record["shadow"]["projected_control_total"] for record in bundle.records
            ),
            "body_conflicts": sum(
                record["shadow"]["body_conflict_total"] for record in bundle.records
            ),
            "retained_projected": sum(
                record["shadow"]["retained_projected_control_total"]
                for record in bundle.records
            ),
            "direct_seam": sum(
                record["shadow"]["direct_seam_total"] for record in bundle.records
            ),
            "gap_fill_seam": sum(
                record["shadow"]["gap_fill_seam_total"] for record in bundle.records
            ),
            "retained": sum(
                record["shadow"]["retained_control_total"] for record in bundle.records
            ),
            "ground_contact_seam": sum(
                record["shadow"]["ground_contact_seam_total"]
                for record in bundle.records
            ),
        }
        self.assertEqual(shadow_totals, sprite_bundle.EXPECTED_SHADOW_TOTALS)
        control_planes = bytearray()
        full_planes = bytearray()
        body_planes = bytearray()
        for record in bundle.records:
            payload = bundle.tiles_by_stock_slot[record["stock_slot"]]
            decoded = stock.decode_indexed_v3_tile(payload)
            self.assertIsNotNone(decoded)
            _height, _width, rows = decoded
            indices = bytes(value for row in rows for value in row)
            body = bytes(
                0 if value in sprite_bundle.CONTROL_INDICES else value
                for value in indices
            )
            self.assertEqual(
                sprite_bundle.sha256_bytes(body), record["indexed_pixel_sha256"]
            )
            self.assertTrue(any(value in sprite_bundle.CONTROL_INDICES for value in indices))
            self.assertFalse(any(value > 250 for value in indices))
            sprite_bundle.validate_split_control_segments(payload)
            contact = sprite_bundle.validate_grounded_shadow_contact(rows)
            self.assertEqual(contact["magenta_body_contact_total"], 0)
            self.assertEqual(contact["transparent_magenta_body_gap_total"], 0)
            self.assertEqual(contact["edge_control_total"], 0)
            self.assertGreaterEqual(contact["ground_seam_contact_total"], 14)
            self.assertLessEqual(contact["ground_seam_contact_total"], 47)
            self.assertEqual(
                contact["ground_seam_contact_total"],
                record["shadow"]["ground_contact_seam_total"],
            )
            control_planes.extend(sprite_bundle._control_plane(rows))
            full_planes.extend(indices)
            body_planes.extend(sprite_bundle._visible_body_plane(rows))

        self.assertEqual(
            sprite_bundle.sha256_bytes(bytes(control_planes)),
            sprite_bundle.EXPECTED_CONTROL_PLANE_SHA256,
        )
        self.assertEqual(
            sprite_bundle.sha256_bytes(bytes(full_planes)),
            sprite_bundle.EXPECTED_FULL_INDEX_PLANE_SHA256,
        )
        self.assertEqual(
            sprite_bundle.sha256_bytes(bytes(body_planes)),
            sprite_bundle.EXPECTED_BODY_PLANE_SHA256,
        )
        frame_hash_lists = {
            "projected_control": [
                record["shadow"]["projected_control_sha256"]
                for record in bundle.records
            ],
            "retained_control": [
                record["shadow"]["retained_control_sha256"]
                for record in bundle.records
            ],
            "full": [
                record["full_indexed_pixel_sha256"] for record in bundle.records
            ],
            "body": [record["indexed_pixel_sha256"] for record in bundle.records],
        }
        self.assertEqual(
            {
                name: sprite_bundle.sha256_bytes(
                    json.dumps(values, separators=(",", ":")).encode("ascii")
                )
                for name, values in frame_hash_lists.items()
            },
            sprite_bundle.EXPECTED_FRAME_HASH_LIST_SHA256,
        )
        northwest_four = next(
            record
            for record in bundle.records
            if record["kind"] == "walk"
            and record["direction"] == "northwest"
            and record["frame"] == 4
        )
        self.assertEqual(
            northwest_four["shadow"]["projected_component_sizes"],
            [259, 35],
        )

    def test_stock_warrior_walk_and_stand_shadows_contact_the_grounded_body(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        stock = art_package.load_stock_pipeline(repo)
        retail = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\maindata.cam"
        )
        tiles = stock.read_cam_entries(retail, b"TILE")
        contact_counts = []
        for stock_slot in range(
            sprite_bundle.APPROVED_SLOT_START,
            sprite_bundle.APPROVED_SLOT_END,
        ):
            decoded = stock.decode_indexed_v3_tile(tiles[stock_slot].data)
            self.assertIsNotNone(decoded)
            _height, _width, rows = decoded
            metrics = sprite_bundle.grounded_shadow_contact_metrics(rows)
            contact_counts.append(metrics["ground_control_contact_total"])
        self.assertEqual(len(contact_counts), 72)
        self.assertTrue(all(count > 0 for count in contact_counts))

    def test_grounded_shadow_validator_rejects_a_transparent_foot_moat(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        stock = art_package.load_stock_pipeline(repo)
        retail = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\maindata.cam"
        )
        tiles = stock.read_cam_entries(retail, b"TILE")
        palettes = stock.read_cam_entries(retail, b"SPLT")
        warrior_imag = stock.read_cam_entry(
            retail, b"IMAG", art_package.HERO_SOURCE
        ).data
        bundle = sprite_bundle.load_approved_sprite_bundle(
            builder.APPROVED_SPRITE_PIPELINE_ROOT,
            stock,
            retail,
            tiles,
            palettes,
            warrior_imag,
        )
        payload = bundle.tiles_by_stock_slot[sprite_bundle.APPROVED_SLOT_START]
        _height, width, rows = stock.decode_indexed_v3_tile(payload)
        moated = [list(row) for row in rows]
        body = {
            (x, y)
            for y, row in enumerate(rows)
            for x, value in enumerate(row)
            if 1 <= value <= 246
        }
        body_base = max(y for _x, y in body)
        ground_body = {(x, y) for x, y in body if y >= body_base - 5}
        for y, row in enumerate(rows):
            for x, value in enumerate(row):
                if value not in sprite_bundle.CONTROL_INDICES:
                    continue
                if any(
                    (neighbor_x, neighbor_y) in ground_body
                    for neighbor_x, neighbor_y in sprite_bundle._neighbors8(
                        width, len(rows), x, y
                    )
                ):
                    moated[y][x] = 0
        with self.assertRaisesRegex(ValueError, "transparent moat"):
            sprite_bundle.validate_grounded_shadow_contact(moated)

    def test_approved_sprite_rle_rejects_mixed_body_shadow_segments(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        stock = art_package.load_stock_pipeline(repo)
        rows = [[0] * 96 for _ in range(92)]
        rows[70][48:50] = [1, 247]
        mixed = stock.encode_indexed_v3_tile(
            rows,
            854,
            (3, 92, 96, 0, 32, 48, 70, 1),
        )
        with self.assertRaisesRegex(ValueError, "mixes visible and shadow-control"):
            sprite_bundle.validate_split_control_segments(mixed)

    def test_approved_sprite_privateizes_all_three_hero_interface_frames(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        game_data = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data"
        )
        stock = art_package.load_stock_pipeline(repo)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "alchemist_maindata.cam"
            provenance = art_package.write_maindata(
                repo,
                game_data,
                repo / "artifacts" / "generated-art",
                output,
                builder.APPROVED_SPRITE_PIPELINE_ROOT,
            )
            self.assertIsNotNone(provenance)
            output_tiles = stock.read_cam_entries(output, b"TILE")
            stock_tiles = stock.read_cam_entries(game_data / "maindata.cam", b"TILE")
            packaged_imag = stock.read_cam_entry(
                output, b"IMAG", art_package.HERO_CUSTOM
            ).data
            phoenix_lifecycle_imag = stock.read_cam_entry(
                output, b"IMAG", art_package.PHOENIX_LIFECYCLE_CUSTOM
            ).data
            stock_imag = stock.read_cam_entry(
                game_data / "maindata.cam", b"IMAG", art_package.HERO_SOURCE
            ).data

        interface_records = provenance["interface_frames"]
        self.assertEqual(
            [record["source_stock_slot"] for record in interface_records],
            list(sprite_bundle.INTERFACE_SOURCE_SLOTS),
        )
        self.assertEqual(
            [record["private_tile_index"] for record in interface_records],
            list(range(len(output_tiles) - 3, len(output_tiles))),
        )
        for record in interface_records:
            source_slot = record["source_stock_slot"]
            private_index = record["private_tile_index"]
            self.assertEqual(output_tiles[source_slot].data, b"")
            self.assertNotEqual(output_tiles[private_index].data, b"")
            offset = sprite_bundle.EXPECTED_INTERFACE_IMAG_OFFSETS[source_slot]
            before = struct.unpack_from("<I", stock_imag, offset)[0]
            after = struct.unpack_from("<I", packaged_imag, offset)[0]
            self.assertEqual(before & 0xFFFF, source_slot)
            self.assertEqual(after & 0xFFFF, private_index)
            self.assertEqual(
                sprite_bundle.sha256_bytes(output_tiles[private_index].data),
                record["packaged_tile_sha256"],
            )
        self.assertGreater(len(output_tiles), len(stock_tiles))
        lifecycle_sets = stock.single_direction_imag_animation_sets(
            phoenix_lifecycle_imag
        )
        self.assertEqual(len(lifecycle_sets), 1)
        self.assertEqual(
            lifecycle_sets[0][0],
            art_package.PHOENIX_LIFECYCLE_ANIMATION_SET,
        )
        lifecycle_indices = stock.animation_tile_indices(
            phoenix_lifecycle_imag,
            len(output_tiles),
        )
        self.assertEqual(
            len(lifecycle_indices), art_package.PHOENIX_LIFECYCLE_FRAMES
        )
        self.assertEqual(
            len(set(lifecycle_indices)), art_package.PHOENIX_LIFECYCLE_FRAMES
        )
        self.assertTrue(
            all(
                output_tiles[tile_index].name.rstrip(b"\x00").startswith(
                    b"PXE1Phoenix"
                )
                for tile_index in lifecycle_indices
            )
        )
        visible_pixel_counts = []
        for tile_index in lifecycle_indices:
            tile = output_tiles[tile_index].data
            self.assertEqual(
                struct.unpack_from("<8H", tile, 0),
                art_package.PHOENIX_EFFECT_HEADER,
            )
            self.assertEqual(
                stock.tile_palette_index(tile),
                art_package.PHOENIX_EFFECT_PALETTE,
            )
            decoded = stock.decode_indexed_v3_tile(tile)
            self.assertIsNotNone(decoded)
            visible_pixel_counts.append(
                sum(value != 0 for row in decoded[2] for value in row)
            )
        visible_phase_counts = visible_pixel_counts[
            : art_package.PHOENIX_VISIBLE_FRAMES
        ]
        transparent_tail_counts = visible_pixel_counts[
            art_package.PHOENIX_VISIBLE_FRAMES :
        ]
        self.assertTrue(all(visible_phase_counts[:-1]))
        self.assertEqual(visible_phase_counts[-1], 0)
        self.assertTrue(all(value == 0 for value in transparent_tail_counts))
        self.assertGreater(max(visible_phase_counts), visible_phase_counts[0])

    def test_approved_sprite_imag_remap_preserves_every_other_warrior_word(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        stock = art_package.load_stock_pipeline(repo)
        retail = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\maindata.cam"
        )
        warrior_imag = stock.read_cam_entry(
            retail, b"IMAG", art_package.HERO_SOURCE
        ).data
        replacements = {
            source: 20000 + source - sprite_bundle.APPROVED_SLOT_START
            for source in range(
                sprite_bundle.APPROVED_SLOT_START,
                sprite_bundle.APPROVED_SLOT_END,
            )
        }
        patched = sprite_bundle.remap_approved_warrior_imag(
            stock, warrior_imag, replacements
        )
        changed = []
        changed_offsets = []
        for offset in range(0, len(warrior_imag) - 3, 4):
            before = struct.unpack_from("<I", warrior_imag, offset)[0]
            after = struct.unpack_from("<I", patched, offset)[0]
            if before != after:
                changed.append(before & 0xFFFF)
                changed_offsets.append(offset)
                self.assertGreaterEqual(before & 0xFFFF, 5919)
                self.assertLessEqual(before & 0xFFFF, 5990)
        self.assertEqual(set(changed), set(range(5919, 5991)))
        self.assertEqual(
            tuple(changed_offsets), sprite_bundle.EXPECTED_REMAPPED_IMAG_OFFSETS
        )
        self.assertEqual(len(changed_offsets), 73)

    def test_approved_sprite_mode_is_explicit_and_cannot_use_regular_art_cache(self) -> None:
        source = Path(builder.__file__).read_text(encoding="utf-8")
        self.assertIn('"--approved-sprite-test-set"', source)
        self.assertIn("cache_current = (not approved_sprite_test_set) and all(", source)
        self.assertIn("if not approved_sprite_test_set:", source)
        self.assertIn(
            '"fresh build; regular art cache bypassed and not updated"',
            Path(sprite_bundle.__file__).read_text(encoding="utf-8"),
        )
        powershell = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "Build-AlchemistProbe.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn('.\\dist\\CustomGuildAlchemistSpriteTest', powershell)
        self.assertIn(
            "$effectiveIncludePhantomsHauntProbe = "
            "$IncludePhantomsHauntProbe -or $ApprovedSpriteTestSet",
            powershell,
        )
        self.assertIn(
            "$effectiveIncludeSiegeTestFixture = "
            "$IncludeSiegeTestFixture -or $ApprovedSpriteTestSet",
            powershell,
        )

    def test_approved_sprite_output_is_confined_to_repository_dist(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        accepted = repo / "dist" / "CustomGuildAlchemistSpriteTest"
        self.assertEqual(
            builder.require_approved_sprite_output_root(accepted), accepted.resolve()
        )
        with self.assertRaisesRegex(ValueError, "must stay inside"):
            builder.require_approved_sprite_output_root(repo.parent / "outside")
        with self.assertRaisesRegex(ValueError, "must be a child"):
            builder.require_approved_sprite_output_root(repo / "dist")
        with self.assertRaisesRegex(ValueError, "may not replace"):
            builder.require_approved_sprite_output_root(
                repo / "dist" / "CustomGuildAlchemistProbe"
            )

    def test_cgal_privateizes_stock_cultist_member_icon(self) -> None:
        stock = b"prefix AVC1 suffix INTI INBb INBg"
        cloned = builder.privateize_cgal_menu(stock)
        self.assertIn(b"ALC1", cloned)
        self.assertNotIn(b"AVC1", cloned)
        self.assertEqual(stock, b"prefix AVC1 suffix INTI INBb INBg")

    def test_cgal_member_icon_clone_rejects_stock_layout_drift(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected one AVC1"):
            builder.privateize_cgal_menu(b"INTI INBb INBg")

    def test_vigor_enabled_icon_is_colored_and_disabled_mask_is_grey(self) -> None:
        enabled_background, enabled_border, enabled_brightness = (
            art_package.VIGOR_ICON_STYLES[212]
        )
        _disabled_background, _disabled_border, disabled_brightness = (
            art_package.VIGOR_ICON_STYLES[342]
        )
        self.assertEqual(enabled_background, (9, 31, 14))
        self.assertEqual(enabled_border, (184, 151, 42))
        self.assertEqual(enabled_brightness, 1.0)
        self.assertLess(disabled_brightness, 0.7)

    def test_fourcc_is_little_endian(self) -> None:
        self.assertEqual(builder.fourcc_id("CGAL"), struct.unpack("<I", b"CGAL")[0])

    def test_cam_reader_returns_a_complete_section(self) -> None:
        entries = (
            builder.CamEntry(builder.pad_name(b"First"), b""),
            builder.CamEntry(builder.pad_name(b"Second"), b"payload"),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.cam"
            builder.write_cam(
                path,
                (builder.CamSection(b"TILE", entries),),
            )
            parsed = builder.read_cam_entries(path, b"TILE")
        self.assertEqual(parsed, list(entries))

    def test_manifest_is_distinct_and_additive(self) -> None:
        root = ET.fromstring(builder.build_manifest())
        mod = root.find("Mod")
        self.assertEqual(mod.get("id"), builder.MOD_ID)
        self.assertEqual(mod.findtext("Name"), "CustomGuildAlchemistProbe")
        self.assertEqual(
            mod.findtext("DisplayName[@lang='en_US']"),
            "Custom Guild: Alchemist (CGAL Probe)",
        )

    def test_alias_manifest_identifies_the_runtime_experiment(self) -> None:
        manifest = builder.build_manifest(use_ap10_title_alias=True)
        self.assertIn("aliases Temple_Fervus", manifest)

    def test_append_bdep_is_idempotent(self) -> None:
        stock = b"AB01 : ABJ1\r\n"
        once = builder.append_bdep_rule(stock, builder.ALCHEMIST_BDEP_RULE, b"test")
        twice = builder.append_bdep_rule(once, builder.ALCHEMIST_BDEP_RULE, b"test")
        self.assertEqual(once, twice)
        self.assertEqual(once.count(builder.ALCHEMIST_BDEP_RULE), 1)

    def test_universal_bdep_uses_stock_expansion_overlay(self) -> None:
        game_path = Path("Majesty HD")
        self.assertEqual(
            builder.stock_building_dependency_cam(game_path),
            game_path / "DataMX" / "mx_miscdata.cam",
        )

    def test_expansion_bdep_regression_rules_cover_gated_buildings(self) -> None:
        self.assertEqual(
            builder.STOCK_EXPANSION_BDEP_RULES,
            (
                b"ABo1 : ABJ3 ABm1 || ABo1 NOT &&",
                b"ABl1 : ABJ2 ABJ3 NOT NOT || ABm1 ||",
                b"ABm1 : ABJ2 ABJ3 NOT NOT || ABm1 ||",
                b"ABr1 : ABJ2 ABJ3 NOT NOT || ABm1 ||",
                b"ABq1 : ABq1 NOT ABq2 NOT ABq3 NOT && && "
                b"ABl1 ABl2 NOT NOT || ABl3 NOT NOT || &&",
            ),
        )

    def test_bdep_payload_preserves_every_stock_expansion_byte(self) -> None:
        stock = (
            b"# stock Expansion table\r\n"
            + b"\r\n".join(builder.STOCK_EXPANSION_BDEP_RULES)
            + b"\r\n"
        )
        built = builder.build_bdep_payload(stock, include_phantoms=True)
        self.assertTrue(built.startswith(stock))
        self.assertEqual(built.count(builder.PHANTOM_BDEP_RULE), 1)
        self.assertEqual(built.count(builder.ALCHEMIST_BDEP_RULE), 1)
        self.assertTrue(
            built.endswith(
                b"# "
                + builder.PHANTOM_BDEP_COMMENT
                + b"\r\n"
                + builder.PHANTOM_BDEP_RULE
                + b"\r\n\r\n# "
                + builder.ALCHEMIST_BDEP_COMMENT
                + b"\r\n"
                + builder.ALCHEMIST_BDEP_RULE
                + b"\r\n"
            )
        )
        builder.validate_bdep_payload(built, stock, include_phantoms=True)

    def test_bdep_validation_rejects_one_altered_stock_byte(self) -> None:
        stock = (
            b"# stock Expansion table\r\n"
            + b"\r\n".join(builder.STOCK_EXPANSION_BDEP_RULES)
            + b"\r\n"
        )
        built = bytearray(builder.build_bdep_payload(stock, include_phantoms=False))
        built[2] ^= 1
        with self.assertRaisesRegex(ValueError, "differs from the complete stock"):
            builder.validate_bdep_payload(
                bytes(built), stock, include_phantoms=False
            )

    def test_bdep_builder_rejects_incomplete_or_prepatched_stock(self) -> None:
        with self.assertRaisesRegex(ValueError, "lost canonical"):
            builder.build_bdep_payload(b"# incomplete\r\n", include_phantoms=False)
        stock = (
            b"\r\n".join(builder.STOCK_EXPANSION_BDEP_RULES)
            + b"\r\n"
            + builder.ALCHEMIST_BDEP_RULE
            + b"\r\n"
        )
        with self.assertRaisesRegex(ValueError, "unexpectedly contains"):
            builder.build_bdep_payload(stock, include_phantoms=False)

    def test_building_data_registers_every_xml_name(self) -> None:
        data = (builder.GPL_SOURCE_ROOT / "Alchemist_Building_Data.dat").read_text(
            encoding="utf-8"
        )
        for name in builder.BUILDING_NAMES:
            self.assertIn(f"[{name}]", data)
        self.assertIn("(birthscript basic_birth)", data)
        self.assertIn("(birthScript2 Guild_Birth)", data)
        self.assertIn("(member_basicscript Alchemist_tree)", data)
        self.assertEqual(data.count("(Visited_Script Alchemy_Lab_Visited)"), 3)
        self.assertEqual(data.count("(member_title Alchemist)"), 3)
        self.assertNotIn("fervus_Birth", data)

    def test_alchemist_hero_uses_private_stock_rogue_behavior(self) -> None:
        data = (builder.GPL_SOURCE_ROOT / "Alchemist_Hero_Data.dat").read_text(
            encoding="utf-8"
        )
        self.assertIn("[Alchemist]", data)
        self.assertIn("(title Alchemist)", data)
        self.assertEqual(data.count("Alchemist_tree"), 3)
        self.assertIn("(attack_action basic_attack)", data)
        self.assertIn("(attacktype 1)", data)
        self.assertIn("(castingrange 25)", data)
        self.assertNotIn("Cultist_Dagger", data)
        self.assertNotIn("Fire_Dagger", data)
        self.assertNotIn("special_attack_action", data)
        self.assertIn("(Greed 26)", data)
        self.assertIn("(Upgrade_Armor_Chance\t100)", data)
        self.assertIn("(Upgrade_Weapon_Chance\t100)", data)
        self.assertIn("(evaluationScript\teval_enemies_nearby)", data)

    def test_private_rogue_tree_preserves_stock_greed_lifecycle_without_stealing(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Rogue.gpl").read_text(
            encoding="utf-8"
        )
        expected = (
            '$createeffector(thisagent,"thought_bubble_think",#think_bubble_time)',
            "$SpecifyIntent (ThisAgent, #Intent_Thinking)",
            "$check_nearby(thisagent)",
            "$Check_rewards(thisagent,FALSE)",
            "$Defend_home(thisagent)",
            '$defend_building(thisagent,"Gambling_hall")',
            "$rest(thisagent)",
            "$Purchase_equipment(thisagent)",
            "$pursue_entertainment(thisagent)",
            "$Loot_Gravestones(ThisAgent,100)",
            "$collect_special_item (ThisAgent, 90)",
            '$Collect_Resource(thisagent,"poison_plants",90)',
            '$check_library(thisagent,15, "Train_magic_resist")',
            '$check_library(thisagent,25, "Learn_generic_spell")',
            "$Combat_wandering(thisagent,65)",
            "$combat_wandering_heroes(thisagent,55)",
            '$Visit_Building(ThisAgent, "Inn", 35)',
            "$explore_map(thisagent,20)",
            '$Visit_Building(ThisAgent, "Royal_gardens", 30)',
            "$Go_home(thisagent,95)",
            "$SpecifyIntent (ThisAgent, #intent_wandering)",
        )
        positions = [source.index(token) for token in expected]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("$Steal_Check", source)
        self.assertNotIn("Cultist_tree", source)
        for cultist_only in ("$Build_Pack", "$Swarm", "$Seed_Resource_Check"):
            self.assertNotIn(cultist_only, source)

    def test_alchemist_unit_strips_cultist_spells_and_uses_stock_melee_range(self) -> None:
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        units = builder.build_units_xml(
            game / "SDK" / "OriginalQuests" / "Data" / "M_Buildings.xml",
            game / "SDK" / "OriginalQuests" / "Data" / "M_Characters.xml",
        )
        root = ET.fromstring(units)
        hero = root.find('./Description[@Name="Alchemist"]')
        self.assertIsNotNone(hero)
        self.assertIsNone(hero.find("./Game/AllowedSpells"))
        attack_range = hero.find("./Game/AttackRange")
        self.assertIsNotNone(attack_range)
        self.assertEqual((attack_range.get("min"), attack_range.get("max")), ("1", "1"))

    def test_title_alias_changes_only_the_gpl_title_token(self) -> None:
        data = (builder.GPL_SOURCE_ROOT / "Alchemist_Building_Data.dat").read_text(
            encoding="utf-8"
        )
        aliased = data.replace(
            "(title AlchemistsLaboratory)", "(title Temple_Fervus)"
        )
        self.assertEqual(aliased.count("(title Temple_Fervus)"), 3)
        for name in builder.BUILDING_NAMES:
            self.assertIn(f"[{name}]", aliased)
        self.assertNotIn("fervus_Birth", aliased)

    def test_safe_panel_disables_the_known_ap10_control(self) -> None:
        menu = bytearray(builder.AP10_SPELL_BUTTON_RECT_OFFSET + 16)
        struct.pack_into(
            "<4I",
            menu,
            builder.AP10_SPELL_BUTTON_RECT_OFFSET,
            *builder.AP10_SPELL_BUTTON_RECT,
        )
        safe = builder.disable_ap10_secondary_control(bytes(menu))
        self.assertEqual(
            struct.unpack_from("<4I", safe, builder.AP10_SPELL_BUTTON_RECT_OFFSET),
            (103, 162, 0, 0),
        )

    def test_safe_panel_rejects_an_unknown_stock_layout(self) -> None:
        menu = bytes(builder.AP10_SPELL_BUTTON_RECT_OFFSET + 16)
        with self.assertRaisesRegex(ValueError, "layout changed"):
            builder.disable_ap10_secondary_control(menu)

    def test_siege_fixture_spawns_both_completed_player_buildings(self) -> None:
        source = """function SIEGE ()
declare
\tagent palace, enemypalace;
begin
\tpalace = $GetPlayerOnePalace ();
end

function NEXT ()
begin
end
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Quests_3.gpl"
            path.write_text(source, encoding="cp1252")
            fixture = builder.build_siege_test_fixture(path)
        self.assertIn('"Temple_Fervus1"', fixture)
        self.assertIn('"Temple_Krolm"', fixture)
        self.assertIn('"Wizards_Guild3"', fixture)
        self.assertIn('"AlchemistsLaboratory1"', fixture)
        self.assertIn('rogueGuild = $SpawnUnit ( palace, "Rogues_Guild1"', fixture)
        self.assertIn('warriorGuild = $SpawnUnit ( palace, "Warriors_Guild"', fixture)
        self.assertEqual(fixture.count('"MaxHP"'), 6)
        self.assertIn('$AdjustPlayerData ( palace, "gold", 100000 )', fixture)
        self.assertNotIn("#ATTRIB_ResearchArrows, 1", fixture)
        self.assertIn('oilRogue = $SpawnUnit ( rogueGuild, "Rogue"', fixture)
        self.assertIn('oilWarrior = $SpawnUnit ( warriorGuild, "Warrior"', fixture)
        self.assertIn('oilAlchemist = $SpawnUnit ( alchemyLab, "Alchemist"', fixture)
        self.assertNotIn('$SpawnUnit ( palace, "Rogue"', fixture)
        self.assertNotIn('$SpawnUnit ( palace, "Warrior"', fixture)
        self.assertNotIn('$SpawnUnit ( palace, "Alchemist"', fixture)
        self.assertEqual(fixture.count("$Advance_To_Level"), 3)
        self.assertEqual(fixture.count("#ATTRIB_Gold, 5000"), 3)
        self.assertEqual(fixture.count("#ATTRIB_Intelligence, 100"), 3)
        self.assertEqual(fixture.count("$Alchemist_Oil_Test_Buyer"), 3)
        self.assertIn("Function Alchemist_Oil_Test_Buyer", fixture)
        self.assertIn("$Purchase_Equipment (ThisAgent)", fixture)
        self.assertNotIn("function NEXT", fixture)

    def test_siege_fixture_is_an_explicit_project_source(self) -> None:
        self.assertEqual(
            builder.build_gpl_project(False),
            'data="Alchemist_Building_Data.dat"\n'
            'data="Alchemist_Hero_Data.dat"\n'
            'data="Alchemist_Phoenix_Phial.dat"\n'
            'source="Alchemist_Rogue.gpl"\n'
            'source="Alchemist_Brewing.gpl"\n'
            'source="Alchemist_Economy.gpl"\n'
            'source="Alchemist_Weapon_Oil.gpl"\n'
            'source="Alchemist_Phoenix_Phial.gpl"\n',
        )
        self.assertIn(
            'source="Alchemist_Siege_Test.gpl"', builder.build_gpl_project(True)
        )
        fixture_manifest = builder.build_manifest(include_siege_test_fixture=True)
        self.assertIn(
            "<Source>GPL\\Alchemist_Siege_Test.gpl</Source>", fixture_manifest
        )
        self.assertNotIn(
            "<Source>GPL\\Alchemist_Siege_Test.gpl</Source>",
            builder.build_manifest(),
        )

    def test_siege_fixture_compiled_symbols_are_fail_closed(self) -> None:
        compiled = b"SIEGE\x00Alchemist_Oil_Test_Buyer\x00"
        builder.validate_siege_test_symbols(compiled, True)
        builder.validate_siege_test_symbols(b"ordinary probe", False)
        with self.assertRaisesRegex(ValueError, "lost symbols"):
            builder.validate_siege_test_symbols(b"SIEGE", True)
        with self.assertRaisesRegex(ValueError, "unexpectedly exports"):
            builder.validate_siege_test_symbols(compiled, False)

    def test_economy_keeps_labs_out_of_stock_wizard_candidates(self) -> None:
        stock = (
            builder.SOURCE_ROOT.parents[1]
            / "external"
            / "BrandonWill-Majesty"
            / "SDK"
            / "OriginalQuests"
            / "GPL"
            / "DecisionTrees"
            / "Modules"
            / "Purchase_Equipment.gpl"
        )
        generated = builder.build_alchemist_economy(stock)
        self.assertIn(
            'alchemyLabs = $List_Attribs(alchemyLabs,#ATTRIB_ResearchArrows);',
            generated,
        )
        self.assertIn(
            'phoenixLabs = $List_Attribs(alchemyLabs,#ATTRIB_ResearchPowerfulItem);',
            generated,
        )
        self.assertNotIn("wizGuilds << AlchemyLab", generated)
        self.assertIn("$Alchemy_Oil_Check (ThisAgent,alchemyLabs)", generated)
        self.assertIn("Wants_Poison,Wants_Oil", generated)
        self.assertIn(
            "ThisAgent's \"Upgrade_Weapon_Chance\" > 0", generated
        )
        self.assertIn(
            "If (Wants_Oil && $Alchemy_Oil_Check (ThisAgent,alchemyLabs))",
            generated,
        )
        self.assertIn(
            "If (Wants_Poison && $Poison_Check (ThisAgent))", generated
        )
        self.assertIn("$Phoenix_Phial_Check (ThisAgent,phoenixLabs)", generated)
        self.assertLess(
            generated.index("$Alchemy_Oil_Check"), generated.index("$Poison_Check")
        )

    def test_weapon_oil_is_a_single_stock_poison_purchase(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Weapon_Oil.gpl").read_text(
            encoding="utf-8"
        )
        self.assertIn("#ATTRIB_WeaponPoisoned", source)
        self.assertIn("expression #Alchemy_Weapon_Oil_Price 100", source)
        self.assertNotIn("#Cost_Per_Magic_Enchantment1", source)
        self.assertNotIn("Intel_Roll", source)
        self.assertNotIn("$RandomNumber (30)", source)
        self.assertIn("#Enchant_Equipment_Visit_Duration", source)
        self.assertIn("$Spend_Gold (ThisAgent, ThisBuilding, Gold)", source)
        self.assertIn("$SetAttribute (ThisAgent, What_To_Upgrade, Upgrade)", source)
        self.assertIn("$Done_Enhancing_Equipment", source)
        self.assertNotIn("#ATTRIB_Weapon_Magic_Bonus", source)
        self.assertNotIn("#ATTRIB_Armor_Magic_Bonus", source)
        self.assertIn("expression #Intent_Applying_Weapon_Oil 177", source)
        self.assertIn(
            "$SpecifyIntent (ThisAgent, #Intent_Applying_Weapon_Oil)", source
        )
        self.assertNotIn("#Intent_Poisoning_Weapon", source)

    def test_private_oil_intent_appends_to_stock_aitx(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\gpltext.cam"
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "oil_gpltext.cam"
            builder.build_gpl_text_cam(stock, output)
            intents = builder.read_cam_entry(output, b"STRT", b"AITX").data
        count = struct.unpack_from("<H", intents, 0)[0]
        self.assertEqual(count, builder.PHOENIX_PHIAL_INTENT_INDEX + 1)
        offsets = struct.unpack_from(f"<{count}I", intents, 4)
        offset = offsets[builder.ALCHEMY_OIL_INTENT_INDEX]
        end = intents.index(b"\x00", offset + 4)
        self.assertEqual(
            intents[offset + 4 : end].decode("cp1252"),
            builder.ALCHEMY_OIL_INTENT_TEXT,
        )

    def test_brewing_source_copies_stock_rage_for_true_heroes(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Brewing.gpl").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('$HasAttribute("Alchemist_Brewing", ThisAgent)', source)
        self.assertIn("function Alchemist_Invigorating_Elixer_End(agent ThisAgent)", source)
        self.assertIn("$IsDead(Hero) == False", source)
        self.assertNotIn("#ATTRIB_ExperienceLevel", source)
        self.assertNotIn("$RunThread", source)
        self.assertNotIn("Alchemist_Invigorated", source)
        self.assertIn('"hero"', source)
        self.assertIn('#CheckSubtypes, "Hero"', source)
        self.assertNotIn("Henchman", source)
        self.assertNotIn("$GetBuildingContents", source)
        self.assertNotIn("$DebugOut", source)
        self.assertNotIn("$CheckEffector", source)
        self.assertIn("foreach Hero in Heroes", source)
        self.assertNotIn('$ListObjects(ThisAgent, "monster"', source)
        self.assertIn("#ATTRIB_MovementRateModifier, -200", source)
        self.assertIn("#ATTRIB_MovementRateModifier, 200", source)
        self.assertIn("30000", source)
        self.assertIn('$AdjustPlayerData(Palace, "Gold", -1500)', source)
        self.assertIn("#ATTRIB_MaxHP, 20", source)
        self.assertIn("#ATTRIB_HP, 20", source)
        self.assertIn('Hero\'s "Self_Estimation" += 1', source)
        self.assertIn("$turnonSPeedTrail(Hero, 4)", source)
        self.assertIn("#ATTRIB_RageOfKrolmCount, HeroCount", source)
        self.assertIn("function Alchemist_DoInvigoratingElixer", source)
        self.assertNotIn("function DoRageOfKrolm", source)
        self.assertNotIn("function Alchemist_Stock_RageOfKrolm", source)
        self.assertLess(
            source.index(
                '$CreateEffector(Hero, "alchemist_invigorating_elixer_icon", 30000)'
            ),
            source.index("$AdjustAttribute(Hero, #ATTRIB_MaxHP, 20)"),
        )

    def test_brewing_overlay_has_a_private_callback(self) -> None:
        stock = """<Majesty><Description type="Unit" subType="Overlay" ID="QRa1" Name="Rage_icon" Description="Rage of Krolm"><Engine><Info value="Directionless"/><Info value="DontBlock"/><ImageIDBase value="QRa1"/><Script type="0" cProc="0" GPLFunction="rage_end"/></Engine><Game><StackPriority value="1"/></Game></Description><Description type="Unit" subType="Overlay" ID="HRC1" Name="resurrection_effector" Description="Resurrection"><Engine><Info value="Directionless"/><Info value="DontBlock"/><Menu value="11"/><ImageIDBase value="HRC1"/><DefaultSound value="Resurrection"/><Script type="0" cProc="0" GPLFunction="Resurrection_End"/></Engine><Game><StackPriority value="0"/><Flags value="TransparentToMouse"/></Game></Description><Description type="Unit" subType="Overlay" ID="XR30" Name="Frost_Field_Hit_Effector" Description="Frost Field"><Engine><Info value="Directionless"/><Info value="DontBlock"/><Menu value="11"/><ImageIDBase value="XR30"/><AttachmentPointID value="2"/><DefaultSound value="Frost_Field_hit"/></Engine><Game><DialogID value="0"/><StackPriority value="0"/><Flags value="TransparentToMouse"/></Game></Description></Majesty>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "M_Overlays.xml"
            path.write_text(stock, encoding="utf-8")
            output = ET.fromstring(builder.build_brewing_overlays_xml(path))
        overlay = output.find("Description")
        self.assertEqual(overlay.get("ID"), "AXE1")
        self.assertEqual(overlay.get("Name"), "alchemist_invigorating_elixer_icon")
        self.assertEqual(
            overlay.find("./Engine/Script").get("GPLFunction"),
            "Alchemist_Invigorating_Elixer_End",
        )
        self.assertEqual(overlay.find("./Engine/ImageIDBase").get("value"), "XR01")
        resurrection = output.findall("Description")[1]
        self.assertEqual(resurrection.get("Name"), "phoenix_phial_resurrection_effector")
        self.assertEqual(
            resurrection.find("./Engine/Script").get("GPLFunction"),
            "Phoenix_Phial_Resurrection_End",
        )
        self.assertEqual(
            resurrection.find("./Engine/ImageIDBase").get("value"), "PXE1"
        )
        self.assertEqual(
            resurrection.find("./Engine/AttachmentPointID").get("value"), "2"
        )
        self.assertEqual(len(output.findall("Description")), 2)
        self.assertIsNone(
            output.find('./Description[@Name="phoenix_phial_visual_effector"]')
        )

    def test_phoenix_phial_composes_stock_purchase_rebirth_and_flee(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Phoenix_Phial.gpl").read_text(
            encoding="utf-8"
        )
        self.assertIn("expression #Phoenix_Phial_Price 1000", source)
        self.assertIn("expression #Phoenix_Phial_Revive_Chance 75", source)
        self.assertIn('$AgentHasInventoryItem ("PhoenixPhial", ThisAgent)', source)
        self.assertIn('$CreateNewInventoryItem ("PhoenixPhial"', source)
        self.assertIn('$DeleteInventoryItem ("PhoenixPhial", ThisAgent)', source)
        self.assertIn("$Shared_Begin_Resurrect (ThisAgent)", source)
        self.assertIn("$Shared_End_Resurrect (ThisAgent)", source)
        self.assertEqual(
            source.count(
                '$CreateEffector (ThisAgent, "phoenix_phial_resurrection_effector", 1500)'
            ),
            1,
        )
        self.assertNotIn("phoenix_phial_visual_effector", source)
        self.assertIn("$Flee (ThisAgent, #Intent_Flee)", source)
        self.assertIn("function gravestone(agent thisagent)", source)
        self.assertNotIn("$RunThread", source)

    def test_brewing_sound_has_a_private_description(self) -> None:
        stock = """<Majesty><Description type="Sound" subType="Standard" ID="DP01" Name="Drink_Potion"><Engine><Category value="0"/><Phase ID="Effector Begin"><Wave value="DP01"/></Phase></Engine></Description></Majesty>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "M_Sounds.xml"
            path.write_text(stock, encoding="utf-8")
            output = ET.fromstring(builder.build_brewing_sounds_xml(path))
        sound = output.find("Description")
        self.assertEqual(sound.get("ID"), "AXS1")
        self.assertEqual(sound.get("Name"), "alchemist_invigorating_elixer_sound")
        self.assertEqual(
            sound.find('./Engine/Phase[@ID="Effector Begin"]/Wave').get("value"),
            "DP01",
        )

    def test_brewing_menu_adds_stock_native_progress_child(self) -> None:
        brewing = bytearray(
            builder.AP69_TERMINAL_RECORD_OFFSET
            + len(builder.AP69_TERMINAL_RECORD_HEADER)
        )
        struct.pack_into("<I", brewing, 0x28, 12)
        struct.pack_into(
            "<4I",
            brewing,
            builder.AP69_FIRST_BREW_RECT_OFFSET,
            *builder.AP69_FIRST_BREW_RECT,
        )
        struct.pack_into(
            "<4I",
            brewing,
            builder.AP69_FIRST_BREW_OUTER_RECT_OFFSET,
            *builder.AP69_FIRST_BREW_OUTER_RECT,
        )
        struct.pack_into(
            "<4I",
            brewing,
            builder.AP69_FIRST_BREW_ICON_RECT_OFFSET,
            *builder.AP69_FIRST_BREW_ICON_RECT,
        )
        brewing[
            builder.AP69_TERMINAL_RECORD_OFFSET :
            builder.AP69_TERMINAL_RECORD_OFFSET
            + len(builder.AP69_TERMINAL_RECORD_HEADER)
        ] = builder.AP69_TERMINAL_RECORD_HEADER
        rage = bytearray(builder.RAGE_PROGRESS_RECORD_OFFSET)
        record = bytearray(0xEC)
        struct.pack_into("<I", record, 0, 9)
        struct.pack_into(
            "<4I",
            record,
            builder.RAGE_PROGRESS_OUTER_RECT_OFFSET,
            *builder.RAGE_PROGRESS_OUTER_RECT,
        )
        struct.pack_into(
            "<I4s", record, builder.RAGE_PROGRESS_INNER_OFFSET, 12, b"INSr"
        )
        struct.pack_into(
            "<I",
            record,
            builder.RAGE_PROGRESS_INNER_OFFSET + 0x2C,
            builder.RAGE_PROGRESS_CONTROL_ID,
        )
        struct.pack_into(
            "<I",
            record,
            builder.RAGE_PROGRESS_PREFIX_OFFSET,
            builder.RAGE_PROGRESS_PREFIX,
        )
        struct.pack_into(
            "<4I",
            record,
            builder.RAGE_PROGRESS_RECT_OFFSET,
            *builder.RAGE_PROGRESS_RECT,
        )
        struct.pack_into(
            "<I",
            record,
            builder.RAGE_ACTIVE_DISPLAY_ID_OFFSET,
            builder.RAGE_ACTIVE_DISPLAY_CONTROL_ID,
        )
        record[-8:] = b"\xff" * 8
        rage += record
        output = builder.add_native_rage_progress_control(bytes(brewing), bytes(rage))
        self.assertEqual(struct.unpack_from("<I", output, 0x28)[0], 12)
        self.assertEqual(output.count(b"INSr"), 1)
        self.assertIn(
            struct.pack("<I", builder.RAGE_ACTIVE_DISPLAY_CONTROL_ID), output
        )
        self.assertEqual(
            struct.unpack_from(
                "<4I",
                output,
                builder.AP69_TERMINAL_RECORD_OFFSET
                + builder.RAGE_PROGRESS_OUTER_RECT_OFFSET,
            ),
            builder.BREWING_PROGRESS_OUTER_RECT,
        )
        self.assertEqual(
            struct.unpack_from(
                "<4I",
                output,
                builder.AP69_TERMINAL_RECORD_OFFSET
                + builder.RAGE_PROGRESS_RECT_OFFSET,
            ),
            builder.BREWING_PROGRESS_RECT,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I",
                output,
                builder.AP69_TERMINAL_RECORD_OFFSET
                + builder.RAGE_PROGRESS_PREFIX_OFFSET,
            )[0],
            builder.RAGE_PROGRESS_PREFIX,
        )
        self.assertEqual(
            output[
                builder.AP69_TERMINAL_RECORD_OFFSET + len(record) - 4 :
                builder.AP69_TERMINAL_RECORD_OFFSET
                + len(record) - 4
                + len(builder.AP69_TERMINAL_RECORD_HEADER)
            ],
            builder.AP69_TERMINAL_RECORD_HEADER,
        )
        self.assertEqual(
            output[
                builder.AP69_TERMINAL_RECORD_OFFSET + len(record) - 8 :
                builder.AP69_TERMINAL_RECORD_OFFSET + len(record) - 4
            ],
            b"\xff" * 4,
        )

    def test_weapon_oil_clones_the_stock_arrows_icon_control(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\textdata.cam"
        )
        brewing = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_BREWING_DIALOG_ID
        ).data
        rage = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_RAGE_DIALOG_ID
        ).data
        research = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_RESEARCH_DIALOG_ID
        ).data
        brewing = builder.add_native_rage_progress_control(brewing, rage)
        output = builder.add_stock_weapon_oil_icon_control(brewing, research)
        marker = output.index(b"ALWI")
        record = marker - 0x24
        self.assertEqual(struct.unpack_from("<4I", output, record + 0x08), (3, 60, 25, 25))
        self.assertEqual(
            struct.unpack_from("<I", output, record + 0x3C)[0],
            builder.BREWING_WEAPON_OIL_ICON_CONTROL_ID,
        )
        self.assertNotIn(b"INCr", output)

    def test_phoenix_row_and_icon_clone_weapon_oil_geometry(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\textdata.cam"
        )
        brewing = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_BREWING_DIALOG_ID
        ).data
        research = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_RESEARCH_DIALOG_ID
        ).data
        rage = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_RAGE_DIALOG_ID
        ).data
        brewing = builder.add_native_rage_progress_control(brewing, rage)
        weapon = builder.add_stock_weapon_oil_research_control(brewing, research)
        output = builder.add_stock_phoenix_phial_research_control(weapon, research)
        private_id = struct.pack("<I", builder.BREWING_PHOENIX_PHIAL_CONTROL_ID)
        control_id_offset = output.index(private_id)
        record = control_id_offset - builder.RESEARCH_ROW_CONTROL_ID_OFFSET
        self.assertEqual(
            struct.unpack_from("<3I", output, record + 0x08),
            (30, 87, 162),
        )

        output = builder.add_stock_phoenix_phial_icon_control(output, research)
        marker = output.index(b"ALPI")
        icon_record = marker - 0x24
        self.assertEqual(
            struct.unpack_from("<4I", output, icon_record + 0x08),
            (3, 86, 25, 25),
        )
        self.assertEqual(
            struct.unpack_from("<I", output, icon_record + 0x3C)[0],
            builder.BREWING_PHOENIX_PHIAL_ICON_CONTROL_ID,
        )

    def test_research_rows_clone_stock_arrows_gold_price_controls(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\textdata.cam"
        )
        brewing = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_BREWING_DIALOG_ID
        ).data
        research = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_RESEARCH_DIALOG_ID
        ).data
        rage = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_RAGE_DIALOG_ID
        ).data
        output = builder.add_native_rage_progress_control(brewing, rage)
        for control_id, rectangle in (
            (builder.BREWING_WEAPON_OIL_PRICE_CONTROL_ID, builder.WEAPON_OIL_PRICE_RECT),
            (builder.BREWING_PHOENIX_PHIAL_PRICE_CONTROL_ID, builder.PHOENIX_PHIAL_PRICE_RECT),
        ):
            output = builder.add_stock_research_price_control(
                output, research, control_id, rectangle
            )
            marker = output.index(struct.pack("<I", control_id))
            record = marker - 0x6C
            self.assertEqual(struct.unpack_from("<4I", output, record + 0x08), rectangle)
            self.assertEqual(struct.unpack_from("<I", output, record + 0x1C)[0], 9)
            self.assertEqual(output[record + 0x3C : record + 0x40], b"ALTI")

        self.assertEqual(
            builder.BREWING_WEAPON_OIL_ICON_CONTROL_ID,
            builder.BREWING_WEAPON_OIL_CONTROL_ID + 500,
        )
        self.assertEqual(
            builder.BREWING_WEAPON_OIL_PRICE_CONTROL_ID,
            builder.BREWING_WEAPON_OIL_CONTROL_ID + 1000,
        )

    def test_cgal_clones_stock_visitors_control_for_layout_probe(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\textdata.cam"
        )
        laboratory = builder.privateize_cgal_menu(
            builder.read_cam_entry(stock, b"SMNU", builder.SOURCE_DIALOG_ID).data
        )
        blacksmith = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_VISITORS_DIALOG_ID
        ).data
        output = builder.add_stock_visitors_probe_control(laboratory, blacksmith)
        marker = output.index(struct.pack("<I", builder.VISITORS_CONTROL_ID))
        record = marker - 0x64
        self.assertEqual(
            struct.unpack_from("<4I", output, record + 0x08),
            builder.VISITORS_FINAL_RECT,
        )
        self.assertEqual(output[record + 0x34 : record + 0x38], b"ALBB")
        self.assertEqual(output[-8:], b"\xff" * 8)

    def test_brewing_moves_below_recruit_without_resizing(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\textdata.cam"
        )
        laboratory = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_DIALOG_ID
        ).data
        output = builder.move_brewing_control_below_recruit(laboratory)
        self.assertEqual(
            struct.unpack_from(
                "<4I", output, builder.AP10_SPELL_BUTTON_RECT_OFFSET
            ),
            builder.BREWING_FINAL_RECT,
        )
        self.assertEqual(builder.BREWING_FINAL_RECT[2:], builder.AP10_SPELL_BUTTON_RECT[2:])

    def test_brewing_action_uses_a_private_control_id(self) -> None:
        menu = bytearray(
            max(
                builder.BREWING_FIRST_BUTTON_ID_OFFSET + 4,
                builder.BREWING_FIRST_ICON_ID_OFFSET + 4,
                builder.BREWING_FIRST_PRICE_ID_OFFSET + 4,
                builder.AP69_FIRST_BREW_RECT_OFFSET + 16,
                builder.AP69_FIRST_BREW_OUTER_RECT_OFFSET + 16,
                builder.AP69_FIRST_BREW_ICON_RECT_OFFSET + 16,
            )
        )
        struct.pack_into(
            "<I",
            menu,
            builder.BREWING_FIRST_BUTTON_ID_OFFSET,
            builder.STOCK_FERVUS_FIRST_SPELL_CONTROL_ID,
        )
        struct.pack_into(
            "<I",
            menu,
            builder.BREWING_FIRST_ICON_ID_OFFSET,
            builder.STOCK_FERVUS_FIRST_SPELL_CONTROL_ID + 1000,
        )
        struct.pack_into(
            "<I",
            menu,
            builder.BREWING_FIRST_PRICE_ID_OFFSET,
            builder.STOCK_FERVUS_FIRST_SPELL_CONTROL_ID - 1000,
        )
        struct.pack_into(
            "<4I", menu, builder.AP69_FIRST_BREW_RECT_OFFSET,
            *builder.AP69_FIRST_BREW_RECT,
        )
        struct.pack_into(
            "<4I", menu, builder.AP69_FIRST_BREW_OUTER_RECT_OFFSET,
            *builder.AP69_FIRST_BREW_OUTER_RECT,
        )
        struct.pack_into(
            "<4I", menu, builder.AP69_FIRST_BREW_ICON_RECT_OFFSET,
            *builder.AP69_FIRST_BREW_ICON_RECT,
        )
        output = builder.privateize_brewing_action_control(bytes(menu))
        self.assertEqual(
            struct.unpack_from(
                "<I", output, builder.BREWING_FIRST_BUTTON_ID_OFFSET
            )[0],
            builder.BREWING_INVIGORATING_CONTROL_ID,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I", output, builder.BREWING_FIRST_ICON_ID_OFFSET
            )[0],
            builder.BREWING_INVIGORATING_ICON_CONTROL_ID,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I", output, builder.BREWING_FIRST_PRICE_ID_OFFSET
            )[0],
            builder.BREWING_INVIGORATING_PRICE_CONTROL_ID,
        )

    def test_panel_uses_stock_length_display_labels(self) -> None:
        source = Path(builder.__file__).read_text(encoding="utf-8")
        self.assertIn('0: "ALCHEMY LAB"', source)
        self.assertIn('1: "Vigor Elixir"', source)
        self.assertIn('29: "Brewing"', source)
        self.assertIn('13: "Brewing"', source)
        self.assertIn('3: "1500"', source)
        self.assertIn('9: "250"', source)
        self.assertIn('28: "Invigorated"', source)
        self.assertNotIn('29: "BREWING"', source)
        self.assertEqual(source.count('fourcc_id("ALB1"): "Alchemy Lab"'), 1)
        self.assertEqual(source.count('fourcc_id("ALB2"): "Alchemy Lab"'), 1)
        self.assertEqual(source.count('fourcc_id("ALB3"): "Alchemy Lab"'), 1)
        self.assertNotIn('0: "ALCHEMIST\'S LABORATORY"', source)

    def test_strt_index_patch_pads_missing_stock_slots(self) -> None:
        source = builder.encode_strt(
            b"\x01\x00", [(0, b"zero"), (1, b"one")]
        )
        output = builder.patch_strt_by_index(source, {4: "four"})
        self.assertEqual(struct.unpack_from("<H", output, 0)[0], 5)
        offsets = struct.unpack_from("<5I", output, 4)
        records = []
        for offset in offsets:
            string_id = struct.unpack_from("<I", output, offset)[0]
            end = output.index(b"\x00", offset + 4)
            records.append((string_id, output[offset + 4 : end]))
        self.assertEqual(
            records,
            [(0, b"zero"), (1, b"one"), (2, b""), (3, b""), (4, b"four")],
        )


if __name__ == "__main__":
    unittest.main()
