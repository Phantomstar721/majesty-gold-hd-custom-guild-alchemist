import json
import math
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import build_custom_guild_alchemist as builder
import alchemist_art_package as art_package
import approved_building_bundle as building_bundle
import approved_sprite_bundle as sprite_bundle


class AlchemistGuildTests(unittest.TestCase):
    def test_mod_manager_definition_is_complete_v3_contract(self) -> None:
        definition = json.loads(
            (builder.SOURCE_ROOT.parent / builder.MOD_DEFINITION_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(definition["schema_version"], 3)
        self.assertEqual(definition["mod_id"], builder.MOD_ID)
        self.assertEqual(definition["internal_name"], builder.PACKAGE_NAME)
        self.assertEqual(
            definition["custom_buildings"],
            [
                {
                    "local_name": "AlchemistsLaboratory",
                    "controller_base": "AP10",
                    "panel_resource_template": "AP10",
                }
            ],
        )
        identity_fields = {
            "stock.name-generator.v1": "generator_id",
            "stock.ap78-enchantment-row.v1": "overlay_id",
            "stock.ap10-ap69-secondary-panel.v1": "panel_key",
            "stock.ap22-resource-meter.v1": "resource_key",
            "stock.ap99-research-row.v1": "recipe_key",
            "stock.ap17-upgrade-research-gate.v1": "parent_building",
            "stock.ap24-timed-rage-action.v1": "action_key",
            "stock.ap24-rage-command-action.v1": "action_key",
            "stock.ap69-sovereign-target-action.v1": "action_key",
        }
        self.assertEqual(
            tuple(
                (feature["type"], feature[identity_fields[feature["type"]]])
                for feature in definition["runtime_features"]
            ),
            builder.RUNTIME_FEATURE_IDENTITIES,
        )
        self.assertEqual(
            definition["runtime_features"][0]["name_tables"],
            ["HN69", "HN70", "HN71", "HN72"],
        )

    def test_building_v2_and_ready_overlay_contract_is_frozen(self) -> None:
        self.assertEqual(
            art_package.APPROVED_BUILDING_ROOT,
            Path("assets/source/approved-alchemist-building-set-v2"),
        )
        self.assertEqual(
            art_package.REAGENT_READY_SOURCE,
            b"WRF1super_charge_e",
        )
        self.assertEqual(
            art_package.REAGENT_READY_SOURCE_TILES,
            tuple(range(2296, 2326)),
        )
        self.assertEqual(
            art_package.REAGENT_READY_SOURCE_PALETTES,
            (*(175 for _ in range(5)), *(176 for _ in range(24)), 177),
        )
        self.assertEqual(
            building_bundle.KRYPTA_FOOTPRINT_AUTHORITY_IMAGS,
            (
                b"ABT1Temple, Krypta1",
                b"ABT2Temple, Krypta2",
                b"ABT3Temple, Krypta3",
            ),
        )
        self.assertEqual(
            building_bundle.KRYPTA_HOTSPOT_GEOMETRY,
            (35, 8, 11, 97),
        )
        self.assertEqual(art_package.REAGENT_READY_FRAME_COUNT, 30)
        self.assertEqual(
            art_package.REAGENT_READY_PALETTE,
            building_bundle.ACTIVE_GLOW_PALETTE_INDEX,
        )
        self.assertEqual(art_package.REAGENT_READY_CANVAS, (213, 269))
        self.assertEqual(art_package.REAGENT_READY_EFFECT_CENTER, (162, 208))
        self.assertEqual(
            art_package.REAGENT_READY_ART_SOURCE_SHA256,
            "9db29df515ba925aafa08fec380dc1647bde558c43b39ec4757c037e1d35ea98",
        )
        self.assertEqual(
            art_package.REAGENT_READY_CUSTOM_TILE_AGGREGATE_SHA256,
            "67d98633728322b93aba81a992b3dc05086d7b8e904386a1dc6a7b75c6d7f889",
        )
        self.assertEqual(art_package.REAGENT_READY_POOL_CENTER_NATIVE, (165, 149))
        self.assertEqual(
            building_bundle.ACTIVE_PULSE_FACTORS,
            (
                1.0,
                1.0707106781186548,
                1.1,
                1.0707106781186548,
                1.0,
                0.9292893218813453,
                0.9,
                0.9292893218813453,
            ),
        )
        self.assertEqual(building_bundle.ACTIVE_GLOW_PALETTE_INDEX, 855)
        self.assertEqual(
            art_package.LAB_LEVEL3_ROOT_EFFECT_HOTSPOT_DELTA,
            (-4, 50),
        )
        self.assertEqual(
            art_package.LAB_LEVEL3_GROUND_ALIGNED_EFFECT_HOTSPOT,
            (136, 115),
        )
        self.assertEqual(
            art_package.ARCANE_INFUSION_HEADER[5:7],
            art_package.LAB_LEVEL3_GROUND_ALIGNED_EFFECT_HOTSPOT,
        )
        self.assertEqual(
            art_package.VIGOR_ACTIVATION_HEADER[5:7],
            art_package.LAB_LEVEL3_GROUND_ALIGNED_EFFECT_HOTSPOT,
        )
        self.assertEqual(
            building_bundle.HIRES_AUTHORITY_DIRECTORY,
            "approved-alchemist-building-hires-v2",
        )
        self.assertEqual(
            building_bundle.HIRES_AUTHORITY_MANIFEST_SHA256,
            "b4649a3d04b829a9815eded14d640c0f22ba2ae45e2c213f877d6c522ffc5e78",
        )

    def test_wizard_ground_comparison_covers_complete_body_lifecycle(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        retail = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\maindata.cam"
        )
        stock = art_package.load_stock_pipeline(repo)
        authority = building_bundle.validate_stock_wizard_ground_authority(
            stock,
            retail,
            stock.read_cam_entries(retail, b"TILE"),
        )
        self.assertEqual(authority["analogue"], "ABY1/2/3 Wizard Guild")
        self.assertEqual(
            authority["ground_base_offset"],
            building_bundle.WIZARD_GUILD_GROUND_BASE_OFFSET,
        )
        self.assertEqual(len(authority["levels"]), 3)
        expected_roles = [
            "construction_handoff",
            "inactive",
            "damage_a",
            "damage_b",
            "rubble",
        ]
        for level in authority["levels"]:
            self.assertEqual(
                [state["role"] for state in level["states"]],
                expected_roles,
            )
            self.assertTrue(
                all(
                    state["ground_base_offset"]
                    == building_bundle.WIZARD_GUILD_GROUND_BASE_OFFSET
                    for state in level["states"]
                )
            )

    def test_brewing_header_keeps_stock_ornament_and_private_backing(self) -> None:
        class StockTileFixture:
            @staticmethod
            def tile_from_png_native_size(template, palettes, dialog_path):
                self.assertEqual(template, b"stock")
                self.assertEqual(palettes, [])
                self.assertEqual(dialog_path, Path("private.png"))
                return b"private"

            @staticmethod
            def decode_indexed_v3_tile(tile):
                if tile == b"stock":
                    row = [12, 247, 249, 254]
                elif tile == b"private":
                    row = [81, 82, 83, 84]
                else:
                    raise AssertionError(f"Unexpected TILE fixture: {tile!r}")
                return 60, 4, [list(row) for _ in range(60)]

            @staticmethod
            def encode_indexed_v3_tile_like_original(template, rows):
                self.assertEqual(template, b"stock")
                return rows

        rows = art_package.brewing_dialog_tile(
            StockTileFixture(), b"stock", Path("private.png")
        )
        self.assertEqual(rows[0], [12, 82, 83, 84])
        self.assertEqual(rows[56], [12, 82, 83, 84])
        self.assertEqual(rows[57], [81, 82, 83, 84])

    def test_approved_sprite_bundle_is_hash_pinned_and_covers_complete_action_set(self) -> None:
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
            bundle.handoff_manifest_sha256,
            sprite_bundle.COMPLETED_HANDOFF_MANIFEST_SHA256,
        )
        self.assertEqual(len(bundle.records), 281)
        self.assertEqual(len(bundle.imag_patches), 378)
        self.assertEqual(
            {
                action: sum(record["kind"] == action for record in bundle.records)
                for action in sprite_bundle.COMPLETED_ACTION_COUNTS
            },
            sprite_bundle.COMPLETED_ACTION_COUNTS,
        )
        self.assertEqual(
            [
                record["direction"]
                for record in bundle.records
                if record["kind"] == "walk" and record["frame"] == 0
            ],
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

        proven = [
            record for record in bundle.records
            if record["kind"] in {"walk", "stand"}
        ]
        shadow_totals = {
            "projected": sum(
                record["shadow"]["projected_control_total"] for record in proven
            ),
            "body_conflicts": sum(
                record["shadow"]["body_conflict_total"] for record in proven
            ),
            "retained_projected": sum(
                record["shadow"]["retained_projected_control_total"]
                for record in proven
            ),
            "direct_seam": sum(
                record["shadow"]["direct_seam_total"] for record in proven
            ),
            "gap_fill_seam": sum(
                record["shadow"]["gap_fill_seam_total"] for record in proven
            ),
            "retained": sum(
                record["shadow"]["retained_control_total"] for record in proven
            ),
            "ground_contact_seam": sum(
                record["shadow"]["ground_contact_seam_total"]
                for record in proven
            ),
        }
        self.assertEqual(shadow_totals, sprite_bundle.EXPECTED_SHADOW_TOTALS)
        for record in bundle.records:
            payload = record["packaged_tile"]
            decoded = stock.decode_indexed_v3_tile(payload)
            self.assertIsNotNone(decoded)
            height, width, rows = decoded
            self.assertEqual([width, height], record["canvas"])
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
            contact = sprite_bundle.validate_grounded_shadow_contact(
                rows, tuple(record["canvas"])
            )
            self.assertEqual(contact["magenta_body_contact_total"], 0)
            self.assertEqual(contact["transparent_magenta_body_gap_total"], 0)
            self.assertEqual(contact["edge_control_total"], 0)
            self.assertGreater(contact["ground_seam_contact_total"], 0)
            self.assertEqual(
                contact["ground_seam_contact_total"],
                record["shadow"]["ground_contact_seam_total"],
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
        # write_maindata records source-art paths relative to the repository.
        # Keep the disposable fixture under that root, then let the temporary
        # directory remove it so the test never depends on artifacts/ residue.
        with tempfile.TemporaryDirectory(
            dir=repo,
            prefix=".test-alchemist-art-",
        ) as directory:
            generated_art = Path(directory) / "generated-art"
            subprocess.run(
                (
                    sys.executable,
                    str(repo / "scripts" / "generate_alchemist_art.py"),
                    "--repo",
                    str(repo),
                    "--out-dir",
                    str(generated_art),
                ),
                check=True,
            )
            output = Path(directory) / "alchemist_maindata.cam"
            provenance = art_package.write_maindata(
                repo,
                game_data,
                generated_art,
                output,
                builder.APPROVED_SPRITE_PIPELINE_ROOT,
            )
            self.assertIsNotNone(provenance)
            output_tiles = stock.read_cam_entries(output, b"TILE")
            output_palettes = stock.read_cam_entries(output, b"SPLT")
            stock_tiles = stock.read_cam_entries(game_data / "maindata.cam", b"TILE")
            packaged_imag = stock.read_cam_entry(
                output, b"IMAG", art_package.HERO_CUSTOM
            ).data
            phoenix_lifecycle_imag = stock.read_cam_entry(
                output, b"IMAG", art_package.PHOENIX_LIFECYCLE_CUSTOM
            ).data
            packaged_effects = {
                name: stock.read_cam_entry(output, b"IMAG", name).data
                for name in (
                    art_package.VIGOR_EFFECT_CUSTOM,
                    art_package.FLASH_FLASK_BUFF_CUSTOM,
                    art_package.FLASH_FLASK_ACTIVATION_CUSTOM,
                    art_package.MIASMA_DEBUFF_CUSTOM,
                    art_package.PHILOSOPHERS_STONE_HIT_CUSTOM,
                    art_package.ARCANE_INFUSION_EFFECT_CUSTOM,
                    art_package.VIGOR_ACTIVATION_EFFECT_CUSTOM,
                )
            }
            stock_imag = stock.read_cam_entry(
                game_data / "maindata.cam", b"IMAG", art_package.HERO_SOURCE
            ).data
            packaged_building_imags = tuple(
                stock.read_cam_entry(output, b"IMAG", name).data
                for name in art_package.BUILDING_CUSTOM
            )

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
        building_provenance = provenance["building_art"]
        self.assertEqual(
            building_provenance["payload_aggregate_sha256"],
            building_bundle.PAYLOAD_AGGREGATE_SHA256,
        )
        self.assertEqual(len(building_provenance["states"]), 25)
        self.assertEqual(
            [row["imag"] for row in building_provenance["source_topology"]],
            [name.decode("ascii") for name in building_bundle.SOURCE_IMAG_NAMES],
        )
        self.assertEqual(
            [struct.unpack_from("<I", imag, 20)[0] for imag in packaged_building_imags],
            list(building_bundle.SOURCE_IMAG_SET_COUNTS),
        )
        building_states = building_provenance["states"]
        level_three_active = next(
            record
            for record in building_states
            if record["level"] == 3 and record["role"] == "active"
        )
        self.assertEqual(
            tuple(level_three_active["packaged_hotspot"]),
            art_package.LAB_LEVEL3_MARKETPLACE_GROUND_HOTSPOT,
        )
        self.assertEqual(
            tuple(
                current - previous
                for current, previous in zip(
                    level_three_active["packaged_hotspot"],
                    art_package.LAB_LEVEL3_PRE_GROUND_FIX_HOTSPOT,
                )
            ),
            art_package.LAB_LEVEL3_ROOT_EFFECT_HOTSPOT_DELTA,
        )
        self.assertEqual(
            building_provenance["active_glow_mask"],
            "registered-inactive-liquid-surfaces-v1",
        )
        self.assertEqual(
            building_provenance["runtime_body_manifest_sha256"],
            building_bundle.HIRES_AUTHORITY_MANIFEST_SHA256,
        )
        self.assertEqual(
            building_provenance["runtime_hotspot_mechanism"],
            "marketplace-visible-ground-center-v1",
        )
        self.assertEqual(
            building_provenance["native_owner_to_pool_registration"],
            list(building_bundle.LAB_OWNER_TO_POOL_DISPLACEMENT),
        )
        self.assertEqual(
            building_provenance["wizard_ground_comparison"][
                "ground_base_offset"
            ],
            building_bundle.WIZARD_GUILD_GROUND_BASE_OFFSET,
        )
        footprint_policy = building_provenance["building_footprint_policy"]
        self.assertEqual(footprint_policy["set_id"], building_bundle.HOTSPOT_SET_ID)
        self.assertEqual(
            footprint_policy["stock_analogue"],
            "ABT1/2/3 Temple to Krypta",
        )
        self.assertEqual(
            footprint_policy["ownership"],
            "private-inactive-tile-alias",
        )
        self.assertEqual(
            footprint_policy["geometry"],
            list(building_bundle.KRYPTA_HOTSPOT_GEOMETRY),
        )
        self.assertEqual(
            footprint_policy["authority_imag_sha256"],
            list(building_bundle.KRYPTA_FOOTPRINT_AUTHORITY_IMAG_SHA256),
        )
        for packaged_building_imag, authority_name in zip(
            packaged_building_imags,
            building_bundle.KRYPTA_FOOTPRINT_AUTHORITY_IMAGS,
        ):
            authority_imag = stock.read_cam_entry(
                game_data / "maindata.cam",
                b"IMAG",
                authority_name,
            ).data
            inactive_tile = (
                building_bundle._single_frame_reference_for_set(
                    packaged_building_imag,
                    building_bundle.INACTIVE_SET_ID,
                )
                & 0xFFFF
            )
            expected_hotspot = building_bundle.apply_krypta_building_footprint(
                packaged_building_imag,
                authority_imag,
                inactive_tile,
            )
            self.assertEqual(
                building_bundle._imag_set_chunk(
                    packaged_building_imag,
                    building_bundle.HOTSPOT_SET_ID,
                ),
                building_bundle._imag_set_chunk(
                    expected_hotspot,
                    building_bundle.HOTSPOT_SET_ID,
                ),
            )
            self.assertEqual(
                building_bundle._single_frame_reference_for_set(
                    packaged_building_imag,
                    building_bundle.HOTSPOT_SET_ID,
                )
                & 0xFFFF,
                inactive_tile,
            )
        self.assertEqual(
            building_provenance["runtime_shadow_mechanism"],
            "literal-haunt-add_cast_shadow",
        )
        self.assertEqual(
            building_provenance["runtime_shadow_source_sha256"],
            building_bundle.HAUNT_SHADOW_SOURCE_SHA256,
        )
        for record in building_provenance["states"]:
            self.assertEqual(record["source_canvas"], record["object_canvas"])
            self.assertEqual(
                record["packaged_canvas"],
                [
                    round(value * building_bundle.RUNTIME_BUILDING_SCALE)
                    for value in record["object_canvas"]
                ],
            )
            self.assertEqual(record["body_source_offset_in_object"], [0, 0])
            self.assertEqual(
                record["runtime_visible_resample"],
                "approved-r14-source-direct-to-final-canvas",
            )
            self.assertEqual(len(record["runtime_body_source_sha256"]), 64)
            self.assertEqual(len(record["accepted_native_body_sha256"]), 64)
            self.assertEqual(
                record["runtime_body_paste_offset"],
                [
                    round(value * building_bundle.RUNTIME_BUILDING_SCALE)
                    for value in record["native_body_paste_offset"]
                ],
            )
            self.assertEqual(
                [
                    pool - hotspot
                    for pool, hotspot in zip(
                        record["native_pool_center"],
                        record["source_hotspot"],
                    )
                ],
                list(building_bundle.LAB_OWNER_TO_POOL_DISPLACEMENT),
            )
            self.assertEqual(
                record["runtime_pool_center"],
                [
                    round(value * building_bundle.RUNTIME_BUILDING_SCALE)
                    for value in record["native_pool_center"]
                ],
            )
            self.assertEqual(
                record["runtime_owner_to_pool_displacement"],
                [
                    pool - hotspot
                    for pool, hotspot in zip(
                        record["runtime_pool_center"],
                        record["packaged_hotspot"],
                    )
                ],
            )
            tile = output_tiles[record["private_tile_index"]].data
            self.assertEqual(
                stock.tile_palette_index(tile),
                (
                    building_bundle.ACTIVE_GLOW_PALETTE_INDEX
                    if record["role"] == "active"
                    else building_bundle.SOURCE_PALETTE_INDEX
                ),
            )
            self.assertEqual(
                list(struct.unpack_from("<hh", tile, 10)),
                record["packaged_hotspot"],
            )
            decoded = stock.decode_indexed_v3_tile(tile)
            self.assertIsNotNone(decoded)
            self.assertEqual([decoded[1], decoded[0]], record["packaged_canvas"])
            expected_hotspot, ground_alignment = (
                building_bundle.marketplace_ground_aligned_hotspot(
                    stock,
                    stock_tiles[record["source_tile_index"]].data,
                    decoded[2],
                )
            )
            self.assertEqual(list(expected_hotspot), record["packaged_hotspot"])
            self.assertEqual(ground_alignment, record["runtime_ground_alignment"])
            runtime_body_edge = building_bundle.runtime_body_edge_metrics(
                decoded[2],
                stock.splt_palette_colors(
                    output_palettes[stock.tile_palette_index(tile)].data
                ),
            )
            self.assertEqual(runtime_body_edge, record["runtime_body_edge"])
            self.assertEqual(runtime_body_edge["below_42_boundary_total"], 0)
            runtime_shadow = building_bundle.runtime_shadow_contact_metrics(
                decoded[2]
            )
            self.assertEqual(runtime_shadow, record["runtime_shadow"])
            self.assertEqual(
                record["runtime_front_ground_offset"],
                runtime_shadow["body_bbox"][3] - record["packaged_hotspot"][1],
            )
            self.assertEqual(
                record["runtime_front_ground_offset"],
                ground_alignment["source_front_ground_offset"],
            )
            self.assertEqual(
                record["wizard_front_ground_offset_difference"],
                record["runtime_front_ground_offset"]
                - building_bundle.WIZARD_GUILD_GROUND_BASE_OFFSET,
            )
            shadow_plane = bytes(
                value if value in building_bundle.CONTROL_INDICES else 0
                for row in decoded[2]
                for value in row
            )
            self.assertEqual(
                building_bundle.sha256_bytes(shadow_plane),
                record["runtime_shadow_control_plane_sha256"],
            )
            self.assertEqual(
                record["runtime_shadow_mechanism"],
                "literal-haunt-add_cast_shadow",
            )
            self.assertEqual(
                record["runtime_shadow_source_sha256"],
                building_bundle.HAUNT_SHADOW_SOURCE_SHA256,
            )
            self.assertGreater(runtime_shadow["contact_seam_total"], 0)
            self.assertGreater(runtime_shadow["shadow_band_total"], 0)
            self.assertEqual(runtime_shadow["direct_band_body_contact_total"], 0)
            self.assertEqual(runtime_shadow["transparent_band_body_gap_total"], 0)
            self.assertEqual(runtime_shadow["orphan_seam_total"], 0)
            self.assertEqual(
                runtime_shadow["band_envelope_notch_violation_total"], 0
            )
            if record["role"] == "active":
                inactive = next(
                    candidate
                    for candidate in building_states
                    if candidate["level"] == record["level"]
                    and candidate["role"] == "inactive"
                )
                self.assertEqual(
                    record["runtime_body_source_state"],
                    inactive["runtime_body_source_state"],
                )
                self.assertEqual(
                    record["runtime_body_source_sha256"],
                    inactive["runtime_body_source_sha256"],
                )
                self.assertEqual(
                    record["runtime_body_authority_role"],
                    "level-inactive-baseline",
                )
                self.assertEqual(
                    record["active_liquid_mask"],
                    building_bundle.LIQUID_MASK_EXPECTED_BY_LEVEL[record["level"]],
                )
                self.assertEqual(
                    record["active_glow_ramp_lift_steps"],
                    building_bundle.ACTIVE_GLOW_RAMP_LIFT_STEPS,
                )
                frame_indices = record["active_frame_private_indices"]
                self.assertEqual(len(frame_indices), 8)
                decoded_frames = []
                frame_payloads = []
                for frame_index in frame_indices:
                    frame_tile = output_tiles[frame_index].data
                    frame_payloads.append(frame_tile)
                    self.assertEqual(
                        stock.tile_palette_index(frame_tile),
                        building_bundle.ACTIVE_GLOW_PALETTE_INDEX,
                    )
                    self.assertEqual(
                        list(struct.unpack_from("<hh", frame_tile, 10)),
                        record["packaged_hotspot"],
                    )
                    frame_decoded = stock.decode_indexed_v3_tile(frame_tile)
                    self.assertIsNotNone(frame_decoded)
                    self.assertEqual(
                        [frame_decoded[1], frame_decoded[0]],
                        record["packaged_canvas"],
                    )
                    decoded_frames.append(frame_decoded[2])
                    sprite_bundle.validate_split_control_segments(frame_tile)

                liquid_points = {
                    (x, y)
                    for y, row in enumerate(decoded_frames[0])
                    for x, value in enumerate(row)
                    if value in building_bundle.ACTIVE_GLOW_VIOLET_INDICES
                }
                expected_liquid = record["active_liquid_mask"]
                self.assertEqual(len(liquid_points), expected_liquid["runtime_count"])
                self.assertEqual(
                    [
                        min(x for x, _y in liquid_points),
                        min(y for _x, y in liquid_points),
                        max(x for x, _y in liquid_points) + 1,
                        max(y for _x, y in liquid_points) + 1,
                    ],
                    list(expected_liquid["runtime_bbox"]),
                )
                outside_reference = None
                shadow_reference = None
                for rows in decoded_frames:
                    current_liquid = {
                        (x, y)
                        for y, row in enumerate(rows)
                        for x, value in enumerate(row)
                        if value in building_bundle.ACTIVE_GLOW_VIOLET_INDICES
                    }
                    self.assertEqual(current_liquid, liquid_points)
                    self.assertFalse(
                        any(
                            value in building_bundle.ACTIVE_GLOW_AMBER_INDICES
                            for row in rows
                            for value in row
                        )
                    )
                    outside = tuple(
                        value
                        for y, row in enumerate(rows)
                        for x, value in enumerate(row)
                        if (x, y) not in liquid_points
                    )
                    current_shadow = bytes(
                        value if value in building_bundle.CONTROL_INDICES else 0
                        for row in rows
                        for value in row
                    )
                    if outside_reference is None:
                        outside_reference = outside
                        shadow_reference = current_shadow
                    else:
                        self.assertEqual(outside, outside_reference)
                        self.assertEqual(current_shadow, shadow_reference)
                    self.assertEqual(
                        building_bundle.sha256_bytes(current_shadow),
                        record["runtime_shadow_control_plane_sha256"],
                    )
                for first, second in ((0, 4), (1, 3), (5, 7)):
                    self.assertEqual(frame_payloads[first], frame_payloads[second])
            sprite_bundle.validate_split_control_segments(tile)
        ready = building_provenance["reagents_ready"]
        self.assertEqual(ready["stock_analogue"], "WRF1super_charge_e")
        self.assertEqual(len(ready["private_tile_indices"]), 60)
        self.assertEqual(
            [stream["layer"] for stream in ready["private_streams"]],
            ["body", "motes"],
        )
        self.assertEqual(
            [len(stream["frames"]) for stream in ready["private_streams"]],
            [30, 30],
        )
        self.assertEqual(
            ready["private_palette_index"],
            building_bundle.ACTIVE_GLOW_PALETTE_INDEX,
        )
        self.assertEqual(ready["private_canvas"], [213, 269])
        self.assertEqual(ready["private_effect_center"], [162, 208])
        self.assertEqual(
            ready["private_art_source_sha256"],
            art_package.REAGENT_READY_ART_SOURCE_SHA256,
        )
        self.assertEqual(
            ready["private_tile_aggregate_sha256"],
            art_package.REAGENT_READY_CUSTOM_TILE_AGGREGATE_SHA256,
        )
        self.assertEqual(
            sum(
                entry.name.rstrip(b"\x00").startswith(b"ALR1Ready")
                for entry in output_tiles
            ),
            60,
        )
        flash_activation = packaged_effects[
            art_package.FLASH_FLASK_ACTIVATION_CUSTOM
        ]
        flash_set_offset = struct.unpack_from("<I", flash_activation, 28)[0]
        self.assertEqual(
            struct.unpack_from("<I", flash_activation, flash_set_offset + 28)[0],
            art_package.FLASH_FLASK_ACTIVATION_DELAY_MS,
        )
        stone_impact = packaged_effects[
            art_package.PHILOSOPHERS_STONE_HIT_CUSTOM
        ]
        stone_set_offset = struct.unpack_from("<I", stone_impact, 28)[0]
        self.assertEqual(
            struct.unpack_from("<I", stone_impact, stone_set_offset + 28)[0],
            art_package.PHILOSOPHERS_STONE_DELAY_MS,
        )
        stone_indices = stock.animation_tile_indices(
            stone_impact,
            len(output_tiles),
        )
        self.assertEqual(
            len(stone_indices), art_package.PHILOSOPHERS_STONE_FRAMES
        )
        self.assertEqual(
            len(set(stone_indices)), art_package.PHILOSOPHERS_STONE_FRAMES
        )
        for tile_index in stone_indices:
            self.assertEqual(
                struct.unpack_from("<8H", output_tiles[tile_index].data, 0),
                art_package.PHILOSOPHERS_STONE_HEADER,
            )
        infusion_effect = packaged_effects[
            art_package.ARCANE_INFUSION_EFFECT_CUSTOM
        ]
        infusion_set_offset = struct.unpack_from("<I", infusion_effect, 28)[0]
        self.assertEqual(
            struct.unpack_from("<I", infusion_effect, infusion_set_offset + 28)[0],
            art_package.ARCANE_INFUSION_DELAY_MS,
        )
        infusion_indices = stock.animation_tile_indices(
            infusion_effect,
            len(output_tiles),
        )
        self.assertEqual(
            len(infusion_indices), art_package.ARCANE_INFUSION_FRAMES
        )
        self.assertEqual(
            len(set(infusion_indices)), art_package.ARCANE_INFUSION_FRAMES
        )
        infusion_visible_counts = []
        for tile_index in infusion_indices:
            self.assertEqual(
                struct.unpack_from("<8H", output_tiles[tile_index].data, 0),
                art_package.ARCANE_INFUSION_HEADER,
            )
            self.assertEqual(
                stock.tile_palette_index(output_tiles[tile_index].data),
                art_package.ARCANE_INFUSION_PALETTE,
            )
            infusion_rows = stock.decode_indexed_v3_tile(
                output_tiles[tile_index].data
            )[2]
            infusion_visible_counts.append(
                sum(pixel != 0 for row in infusion_rows for pixel in row)
            )
        infusion_peak = infusion_visible_counts.index(max(infusion_visible_counts))
        self.assertIn(infusion_peak, range(14, 19))
        self.assertTrue(
            all(
                current >= previous * 0.96
                for previous, current in zip(
                    infusion_visible_counts[:infusion_peak],
                    infusion_visible_counts[1 : infusion_peak + 1],
                )
            )
        )
        self.assertTrue(
            all(
                current <= previous * 1.04
                for previous, current in zip(
                    infusion_visible_counts[infusion_peak:-1],
                    infusion_visible_counts[infusion_peak + 1 :],
                )
            )
        )
        vigor_activation = packaged_effects[
            art_package.VIGOR_ACTIVATION_EFFECT_CUSTOM
        ]
        vigor_set_offset = struct.unpack_from("<I", vigor_activation, 28)[0]
        self.assertEqual(
            struct.unpack_from("<I", vigor_activation, vigor_set_offset + 28)[0],
            art_package.VIGOR_ACTIVATION_DELAY_MS,
        )
        vigor_indices = stock.animation_tile_indices(
            vigor_activation,
            len(output_tiles),
        )
        self.assertEqual(
            len(vigor_indices), art_package.VIGOR_ACTIVATION_FRAMES
        )
        self.assertEqual(
            len(set(vigor_indices)), art_package.VIGOR_ACTIVATION_FRAMES
        )
        vigor_visible_counts = []
        for tile_index in vigor_indices:
            self.assertEqual(
                struct.unpack_from("<8H", output_tiles[tile_index].data, 0),
                art_package.VIGOR_ACTIVATION_HEADER,
            )
            self.assertEqual(
                stock.tile_palette_index(output_tiles[tile_index].data),
                art_package.VIGOR_ACTIVATION_PALETTE,
            )
            vigor_rows = stock.decode_indexed_v3_tile(
                output_tiles[tile_index].data
            )[2]
            vigor_visible_counts.append(
                sum(pixel != 0 for row in vigor_rows for pixel in row)
            )
        vigor_peak = vigor_visible_counts.index(max(vigor_visible_counts))
        self.assertIn(vigor_peak, range(14, 19))
        self.assertTrue(
            all(
                current >= previous * 0.96
                for previous, current in zip(
                    vigor_visible_counts[:vigor_peak],
                    vigor_visible_counts[1 : vigor_peak + 1],
                )
            )
        )
        self.assertTrue(
            all(
                current <= previous * 1.04
                for previous, current in zip(
                    vigor_visible_counts[vigor_peak:-1],
                    vigor_visible_counts[vigor_peak + 1 :],
                )
            )
        )
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
        for name, prefix, frame_count, palette in (
            (art_package.VIGOR_EFFECT_CUSTOM, b"ALV1Spark", 29, 560),
            (art_package.FLASH_FLASK_BUFF_CUSTOM, b"AFF1Flask", 29, 560),
            (art_package.FLASH_FLASK_ACTIVATION_CUSTOM, b"AFF2Flash", 6, 505),
            (art_package.MIASMA_DEBUFF_CUSTOM, b"AMm5Drop", 29, 505),
        ):
            indices = stock.animation_tile_indices(
                packaged_effects[name], len(output_tiles)
            )
            self.assertEqual(len(indices), frame_count)
            self.assertEqual(len(set(indices)), frame_count)
            self.assertTrue(
                all(
                    output_tiles[index].name.rstrip(b"\x00").startswith(prefix)
                    and stock.tile_palette_index(output_tiles[index].data) == palette
                    for index in indices
                )
            )
            self.assertTrue(
                all(
                    any(value != 0 for row in stock.decode_indexed_v3_tile(
                        output_tiles[index].data
                    )[2] for value in row)
                    for index in indices
                )
            )
        for name in (
            art_package.VIGOR_EFFECT_CUSTOM,
            art_package.FLASH_FLASK_BUFF_CUSTOM,
            art_package.MIASMA_DEBUFF_CUSTOM,
        ):
            for index in stock.animation_tile_indices(
                packaged_effects[name], len(output_tiles)
            ):
                height, width, rows = stock.decode_indexed_v3_tile(
                    output_tiles[index].data
                )
                visible = [
                    (x, y)
                    for y, row in enumerate(rows)
                    for x, value in enumerate(row)
                    if value != 0
                ]
                self.assertTrue(visible)
                visible_width = max(x for x, _y in visible) - min(x for x, _y in visible) + 1
                visible_height = max(y for _x, y in visible) - min(y for _x, y in visible) + 1
                self.assertLessEqual(visible_width, math.ceil(width * 0.82))
                self.assertLessEqual(visible_height, math.ceil(height * 0.82))
        activation_indices = stock.animation_tile_indices(
            packaged_effects[art_package.FLASH_FLASK_ACTIVATION_CUSTOM],
            len(output_tiles),
        )
        self.assertTrue(
            all(
                struct.unpack_from("<8H", output_tiles[index].data, 0)
                == art_package.FLASH_FLASK_ACTIVATION_HEADER
                for index in activation_indices
            )
        )
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
        tiles = stock.read_cam_entries(retail, b"TILE")
        palettes = stock.read_cam_entries(retail, b"SPLT")
        bundle = sprite_bundle.load_approved_sprite_bundle(
            builder.APPROVED_SPRITE_PIPELINE_ROOT,
            stock,
            retail,
            tiles,
            palettes,
            warrior_imag,
        )
        private_indices = list(range(20000, 20000 + len(bundle.records)))
        patched = sprite_bundle.patch_completed_warrior_imag(
            warrior_imag, bundle, private_indices
        )
        changed_offsets = []
        for offset in range(0, len(warrior_imag) - 3, 4):
            before = struct.unpack_from("<I", warrior_imag, offset)[0]
            after = struct.unpack_from("<I", patched, offset)[0]
            if before != after:
                changed_offsets.append(offset)
        self.assertEqual(
            changed_offsets,
            [patch["offset"] for patch in bundle.imag_patches],
        )
        self.assertEqual(len(changed_offsets), 378)

    def test_approved_sprite_mode_is_explicit_and_cannot_use_regular_art_cache(self) -> None:
        source = Path(builder.__file__).read_text(encoding="utf-8")
        self.assertIn('"--approved-sprite-test-set"', source)
        self.assertIn(
            "cache_current = (reuse_art_from is None) and (not approved_sprite_test_set) and all(",
            source,
        )
        self.assertIn("if approved_sprite_test_set and reuse_art_from is not None:", source)
        self.assertIn("if not approved_sprite_test_set:", source)
        self.assertIn(
            '"fresh build; regular art cache bypassed and not updated"',
            Path(sprite_bundle.__file__).read_text(encoding="utf-8"),
        )
        powershell = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "Build-CustomGuildAlchemist.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn('.\\dist\\CustomGuildAlchemistSpriteTest', powershell)
        self.assertIn(
            "$effectiveIncludePhantomsHauntCompatibility = "
            "$IncludePhantomsHauntCompatibility -or $ApprovedSpriteTestSet",
            powershell,
        )
        self.assertIn(
            "$effectiveIncludeSiegeTestFixture = "
            "$IncludeSiegeTestFixture -or $ApprovedSpriteTestSet",
            powershell,
        )
        self.assertIn(
            'Join-Path $repoRoot "dist\\CustomGuildAlchemistSpriteTest"',
            powershell,
        )

    def test_reusable_art_requires_approved_sprite_provenance(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as root:
            package = Path(root)
            (package / "Data").mkdir()
            (package / "Data" / "alchemist_maindata.cam").write_bytes(b"stale")
            (package / "Data" / "alchemist_interfacedata.cam").write_bytes(b"stale")
            with self.assertRaisesRegex(ValueError, "not an approved Alchemist sprite package"):
                builder.require_verified_approved_art_package(package)

    def test_canonical_reusable_art_matches_completed_handoff(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        package = repo / "dist" / "CustomGuildAlchemistSpriteTest"
        self.assertEqual(
            builder.require_verified_approved_art_package(package), package.resolve()
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
                repo / "dist" / "CustomGuildAlchemist"
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
            art_package.VIGOR_ICON_STYLES[199]
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
        self.assertEqual(mod.findtext("Name"), "CustomGuildAlchemist")
        self.assertEqual(
            mod.findtext("DisplayName[@lang='en_US']"),
            "Custom Guild: Alchemist Lab",
        )
        self.assertEqual(
            mod.findtext("Description[@lang='en_US']/Short"),
            "Adds the Alchemy Lab, Alchemist heroes, and sovereign brews.",
        )

    def test_public_repository_privacy_contract_is_explicit(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        ignored = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
        for private_path in (
            "assets/",
            "docs/internal/",
            "private/",
            "dist/",
            "artifacts/",
        ):
            self.assertIn(private_path, ignored)
        self.assertTrue((repo / "README.md").is_file())
        self.assertTrue((repo / "WORKSHOP.md").is_file())

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

    def test_embassy_and_outpost_selector_preserves_stock_paladin(self) -> None:
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        source = builder.build_alchemist_embassy(
            game
            / "SDK"
            / "OriginalQuests"
            / "GPLMx"
            / "TaskModules"
            / "Buildings"
            / "Embassy.gpl",
            False,
        )
        self.assertEqual(source.count('return "Alchemist";'), 1)
        self.assertIn('return "Paladin";', source)
        self.assertNotIn('return "Phantom";', source)
        self.assertIn("$RandomNumber (17) + 1", source)

    def test_mausoleum_home_mapping_is_literal_stock_guild_title_clone(self) -> None:
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        stock_path = (
            game
            / "SDK"
            / "OriginalQuests"
            / "GPLMx"
            / "TaskModules"
            / "Buildings"
            / "Mausoleum.gpl"
        )
        source = builder.build_alchemist_guild_title(stock_path)
        stock = stock_path.read_text(encoding="cp1252")
        stock_function = builder.extract_gpl_function(stock, "Guild_Title")
        stock_anchor = (
            '\telse if ( ThisAgent\'s "title" == "Wizard" )\n'
            '\t\treturn "Wizards_Guild";\n'
            "\telse\n"
        )
        private_anchor = (
            '\telse if ( ThisAgent\'s "title" == "Wizard" )\n'
            '\t\treturn "Wizards_Guild";\n'
            '\telse if ( ThisAgent\'s "title" == "Alchemist" )\n'
            '\t\treturn "AlchemistsLaboratory";\n'
            "\telse\n"
        )
        self.assertEqual(
            source,
            stock_function.replace(stock_anchor, private_anchor, 1) + "\n",
        )
        self.assertEqual(source.count("function Guild_Title"), 1)
        self.assertEqual(source.count('return "AlchemistsLaboratory";'), 1)
        self.assertNotIn("Mausoleum_Resurrect_Finish", source)

    def test_vigor_adoption_cleanup_is_literal_stock_rage_clone(self) -> None:
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        stock_path = (
            game
            / "SDK"
            / "OriginalQuests"
            / "GPLMx"
            / "mx_Building_Births.gpl"
        )
        source = builder.build_alchemist_adopt(stock_path)
        stock = stock_path.read_text(encoding="cp1252")
        stock_function = builder.extract_gpl_function(stock, "adopt")
        private_cleanup = (
            '\n\tIf ( $CheckEffector ( Stray, '
            '"alchemist_invigorating_elixer_icon" ))\n'
            "\t\tbegin\n"
            "\n"
            '\t\t\t$DeleteEffector ( Stray, '
            '"alchemist_invigorating_elixer_icon" );\n'
            "\n"
            "\t\tend\n"
        )
        infusion_reapply = (
            '\tif ( stray\'s "title" == "Alchemist" )\n'
            "\t\t$Alchemist_Apply_Arcane_Infusion ( stray );\n"
        )
        self.assertEqual(source.count("function adopt"), 1)
        self.assertEqual(source.count(private_cleanup), 1)
        self.assertEqual(source.count(infusion_reapply), 1)
        self.assertEqual(
            source.replace(private_cleanup, "", 1).replace(
                infusion_reapply, "", 1
            ),
            stock_function + "\n",
        )
        self.assertLess(
            source.index(private_cleanup),
            source.index('thisguild\'s "members" << stray;'),
        )

    def test_haunt_compatibility_selector_retains_haunt_paladin_rule(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        source = builder.build_alchemist_embassy(
            game
            / "SDK"
            / "OriginalQuests"
            / "GPLMx"
            / "TaskModules"
            / "Buildings"
            / "Embassy.gpl",
            True,
            repo.parent
            / "majesty-gold-hd-custom-guild-phantoms-haunt"
            / "src"
            / "gpl"
            / "phantom.gpl",
        )
        self.assertEqual(source.count('return "Alchemist";'), 2)
        self.assertEqual(source.count('return "Phantom";'), 2)
        self.assertEqual(source.count('return "Paladin";'), 1)
        self.assertEqual(
            source.count("$Alchemist_Compat_Phantom_Max_Haunt_Level(ThisAgent) > 0"),
            1,
        )
        self.assertIn("$RandomNumber(17) + 1", source)
        self.assertIn("$RandomNumber(18) + 1", source)

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
        self.assertEqual(
            data.count(
                "(birthScript2 Alchemist_Laboratory_Birth_Or_Upgrade)"
            ),
            3,
        )
        self.assertEqual(
            data.count("(upgradescript Alchemist_Laboratory_Upgrade)"), 2
        )
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
        self.assertIn("(castingrange 130)", data)
        self.assertIn("(PercentageHPRetreat 30)", data)
        self.assertIn("(enemy_estimation .9)", data)
        self.assertIn("(self_estimation 1.4)", data)
        self.assertIn("(birthScript\t\tAlchemist_birth)", data)
        self.assertNotIn("Cultist_Dagger", data)
        self.assertNotIn("Fire_Dagger", data)
        self.assertIn("(special_attack_action basic_attack)", data)
        self.assertIn("(Greed 22)", data)
        self.assertIn("(Luck 18)", data)
        self.assertIn("(Immune_to_poison 1)", data)
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
            "$Alchemist_Return_Full_Reagent_Load(thisagent)",
            "$Alchemist_Purchase_Nearby_Equipment(thisagent)",
            "$Alchemist_Purchase_Nearby_Bazaar(thisagent, 75)",
            "$Alchemist_Funded_Resupply(thisagent)",
            "$Check_rewards(thisagent,FALSE)",
            "$Alchemist_Purchase_Bazaar(thisagent, 75)",
            "$Defend_home(thisagent)",
            '$defend_building(thisagent,"Gambling_hall")',
            "$rest(thisagent)",
            "$Purchase_equipment(thisagent)",
            "$pursue_entertainment(thisagent)",
            "$collect_special_item (ThisAgent, 90)",
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
        self.assertNotIn("$Loot_Gravestones", source)
        self.assertNotIn('"poison_plants"', source)
        self.assertNotIn("Cultist_tree", source)
        self.assertEqual(source.count("$Purchase_equipment(thisagent)"), 1)
        self.assertEqual(
            source.count("$Alchemist_Purchase_Bazaar(thisagent, 75)"), 1
        )
        self.assertEqual(
            source.count("$Alchemist_Purchase_Nearby_Equipment(thisagent)"), 1
        )
        self.assertEqual(
            source.count("$Alchemist_Purchase_Nearby_Bazaar(thisagent, 75)"), 1
        )
        self.assertEqual(source.count("$Alchemist_Funded_Resupply(thisagent)"), 1)
        self.assertLess(
            source.index("$Alchemist_Return_Full_Reagent_Load(thisagent)"),
            source.index("$Check_rewards(thisagent,FALSE)"),
        )
        self.assertLess(
            source.index("$Alchemist_Purchase_Nearby_Equipment(thisagent)"),
            source.index("$Check_rewards(thisagent,FALSE)"),
        )
        self.assertLess(
            source.index("$Alchemist_Purchase_Nearby_Bazaar(thisagent, 75)"),
            source.index("$Check_rewards(thisagent,FALSE)"),
        )
        self.assertLess(
            source.index("$Alchemist_Funded_Resupply(thisagent)"),
            source.index("$Check_rewards(thisagent,FALSE)"),
        )
        self.assertLess(
            source.index("$Check_rewards(thisagent,FALSE)"),
            source.index("$Alchemist_Purchase_Bazaar(thisagent, 75)"),
        )
        self.assertLess(
            source.index("$Check_rewards(thisagent,FALSE)"),
            source.index("$Purchase_equipment(thisagent)"),
        )
        for cultist_only in ("$Build_Pack", "$Swarm", "$Seed_Resource_Check"):
            self.assertNotIn(cultist_only, source)

    def test_alchemist_uses_haunt_proven_speed_and_spell_confidence_paths(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Rogue.gpl").read_text(
            encoding="utf-8"
        )
        self.assertIn("expression #Alchemist_Base_Movement_Bonus -45", source)
        self.assertIn("expression #Alchemist_Hire_Grant 100", source)
        self.assertIn("expression #Alchemist_Town_Shopping_Range 500", source)
        self.assertIn("expression #Alchemist_Funded_Resupply_Gold 2000", source)
        self.assertIn("expression #Alchemist_Flash_Flask_Confidence 60", source)
        self.assertIn("expression #Alchemist_Stun_Serum_Confidence 100", source)
        self.assertIn("expression #Alchemist_Miasma_Mist_Confidence 30", source)
        self.assertIn("Function Alchemist_Sync_Speed_Profile", source)
        self.assertIn('"AlchemistBaseMovementApplied"', source)
        self.assertIn("#ATTRIB_MovementRateModifier", source)
        self.assertIn("$SetAttribute(ThisAgent, #ATTRIB_Speed, 2)", source)
        self.assertIn("Function Alchemist_birth", source)
        self.assertIn("$hero_birth(ThisAgent)", source)
        self.assertIn("$Alchemist_Apply_Arcane_Infusion(ThisAgent)", source)
        self.assertIn(
            "$AdjustAttribute(\n\t\tThisAgent,\n\t\t#ATTRIB_StoredGold,\n"
            "\t\t#Alchemist_Hire_Grant\n\t);",
            source,
        )
        self.assertIn('Home\'s "Title" == "AlchemistsLaboratory"', source)
        self.assertIn('"AlchemistRecruitmentVoice"', source)
        self.assertIn("$RandomNumber(100) + 1 <= 20", source)
        self.assertIn(
            '$PlaySound(ThisAgent, "Alchy_Hired", "Begin")', source
        )
        self.assertIn("function spell_extra_value(agent thisagent) is integer", source)
        for spell, weight in (
            ("flash_flask", "#Alchemist_Flash_Flask_Confidence"),
            ("stun_serum", "#Alchemist_Stun_Serum_Confidence"),
            ("miasma_mist", "#Alchemist_Miasma_Mist_Confidence"),
        ):
            self.assertIn(f'$isspellavailable(thisagent,"{spell}",1)', source)
            self.assertIn(f"value += {weight};", source)
        for stock_spell in (
            "energy_blast",
            "fire_blast",
            "fire_ball",
            "teleport",
            "resist_magic",
            "meteor_storm",
            "drain_life",
            "sun_scorch",
        ):
            self.assertIn(f'$isspellavailable(thisagent,"{stock_spell}",1)', source)
        self.assertIn('if (thisagent\'s "Title" == "Phantom")', source)

    def test_private_bazaar_selector_preserves_stock_purchase_lifecycle(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\SDK\OriginalQuests\GPLMx\TaskModules\Buildings\Magic_Bazaar.gpl"
        )
        source = builder.build_alchemist_magic_bazaar(stock)
        self.assertIn("Function Alchemist_Purchase_Bazaar", source)
        self.assertIn("Function Alchemist_Purchase_Nearby_Bazaar", source)
        self.assertIn("Function Alchemist_Bazaar_Item_Check", source)
        self.assertNotIn("Function Purchase_Bazaar", source)
        self.assertNotIn("Function Bazaar_Item_Check", source)
        positions = [
            source.index(f"Item_list << #Bazaar_Item_{name}")
            for name in ("Five", "Six", "Two", "Four", "Three", "One")
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("thisagent's \"title\" != \"alchemist\"", source)
        for stock_owner in (
            "$Researched_Item",
            "$Get_Bazaar_Cost",
            "$Use_Building",
            "$SetBuyerIntent",
        ):
            self.assertIn(stock_owner, source)
        self.assertIn(
            "Search_Dist = #Alchemist_Town_Shopping_Range;",
            source,
        )

    def test_nearby_equipment_is_a_stock_clone_with_only_local_radius(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\SDK\OriginalQuests\GPLMx\DecisionTrees\Modules\mx_Purchase_Equipment.gpl"
        )
        source = builder.build_alchemist_nearby_equipment(stock)
        self.assertIn("Function Alchemist_Purchase_Nearby_Equipment", source)
        self.assertIn("Function Alchemist_Funded_Resupply", source)
        self.assertIn("Function Alchemist_Nearby_Poison_Check", source)
        self.assertNotIn("Function Purchase_Equipment", source)
        self.assertNotIn("Function Poison_Check", source)
        nearby = source.split("Function Alchemist_Funded_Resupply", 1)[0]
        funded = source.split("Function Alchemist_Funded_Resupply", 1)[1].split(
            "Function Alchemist_Nearby_Poison_Check", 1
        )[0]
        self.assertEqual(
            nearby.count("Search_Dist = #Alchemist_Town_Shopping_Range;"),
            1,
        )
        self.assertNotIn("#ATTRIB_Intelligence) / 2", nearby)
        self.assertIn("#ATTRIB_Intelligence) / 2", funded)
        self.assertIn(
            "$Total_Gold (ThisAgent) < #Alchemist_Funded_Resupply_Gold",
            funded,
        )
        self.assertIn(
            "$GetAttribute (ThisAgent, #ATTRIB_NumHealingPotions) == 0",
            funded,
        )
        for stock_dispatch in (
            "$BlackSmith_Check",
            "$WizGuild_Check",
            "$Potion_Check",
            "$Ring_Check",
            "$Market3_Check",
            "$Stat_Boost_Check",
        ):
            self.assertIn(stock_dispatch, source)
        self.assertIn("$Alchemist_Nearby_Poison_Check", source)
        self.assertEqual(source.count("$Alchemy_Oil_Check"), 2)
        self.assertEqual(source.count("$Phoenix_Phial_Check"), 2)

    def test_alchemist_potion_dispatch_is_private_and_stock_shaped(self) -> None:
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        inventory = builder.build_alchemist_inventory(
            game
            / "SDK"
            / "OriginalQuests"
            / "GPLMx"
            / "TaskModules"
            / "Subtasks"
            / "mx_Inventory.gpl"
        )
        self.assertEqual(inventory.count("Function QItem_Stat_Boost"), 1)
        self.assertIn(builder.ALCHEMIST_STRENGTH_ACTION_NAME, inventory)
        self.assertIn(builder.ALCHEMIST_SHAPESHIFT_ACTION_NAME, inventory)
        self.assertIn(builder.ALCHEMIST_FIRE_BALM_ACTION_NAME, inventory)
        self.assertIn(builder.ALCHEMIST_REGENERATION_ACTION_NAME, inventory)
        self.assertIn('$LearnSpell ( thisagent, "Strength_Potion", FALSE )', inventory)
        self.assertIn('$LearnSpell ( thisagent, "Shapeshift_Potion", FALSE )', inventory)

        actions = ET.fromstring(
            builder.build_alchemist_combat_potions_xml(
                game / "SDK" / "OriginalQuests" / "DataMX" / "MX_Actions.xml"
            )
        )
        self.assertEqual(len(actions.findall("Description")), 4)
        for name in (
            builder.ALCHEMIST_STRENGTH_ACTION_NAME,
            builder.ALCHEMIST_SHAPESHIFT_ACTION_NAME,
            builder.ALCHEMIST_FIRE_BALM_ACTION_NAME,
            builder.ALCHEMIST_REGENERATION_ACTION_NAME,
        ):
            action = actions.find(f'./Description[@Name="{name}"]')
            self.assertIsNotNone(action)
            self.assertEqual(
                action.find("./Game/ValidationScript").get("value"),
                builder.ALCHEMIST_CONSUMABLE_VALIDATION,
            )
            self.assertEqual(action.find("./Game/SpellType").get("value"), "Attack")

        strength = builder.build_alchemist_strength_potion(
            game
            / "SDK"
            / "OriginalQuests"
            / "GPLMx"
            / "TaskModules"
            / "Subtasks"
            / "mx_Spells.gpl"
        )
        self.assertIn("function Alchemist_Strength_Potion_Effect", strength)
        self.assertIn(builder.ALCHEMIST_STRENGTH_ACTION_NAME, strength)
        self.assertNotIn('$ForgetSpell ( ThisAgent, "Strength_Potion" )', strength)

        threat = builder.build_alchemist_consumable_threat(
            game
            / "SDK"
            / "OriginalQuests"
            / "GPLMx"
            / "DecisionTrees"
            / "Modules"
            / "mx_target_eval.gpl",
            game
            / "SDK"
            / "OriginalQuests"
            / "GPLMx"
            / "TaskModules"
            / "Subtasks"
            / "mx_Spells.gpl",
        )
        self.assertIn("function Alchemist_Base_List_Eval", threat)
        self.assertIn("integer spell_mod;", threat)
        self.assertIn("spell_mod = $spell_extra_value(thisagent);", threat)
        self.assertIn("return hitstildead - hitstokill + spell_mod;", threat)
        self.assertIn("Spell_Score = $spell_extra_value(ThisAgent);", threat)
        self.assertIn("Base_Score -= (Spell_Score * 3) / 4;", threat)
        self.assertIn("If (Base_Score < 1)", threat)
        self.assertIn("ThisAgent's \"Hostiles\"", threat)
        self.assertIn("function alchemist_combat_consumable_check", threat)
        self.assertIn("function Alchemist_Fire_Balm_Effect", threat)
        self.assertIn("function Alchemist_Regeneration_Elixer_Effect", threat)
        self.assertNotIn('$ForgetSpell ( ThisAgent, "Fire_Balm" )', threat)
        self.assertNotIn('$ForgetSpell ( ThisAgent, "Regeneration_Elixer" )', threat)

    def test_alchemist_shapeshift_clones_stock_with_spider_stat_branch(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\SDK\OriginalQuests"
            r"\GPLMx\TaskModules\Subtasks\mx_Spells.gpl"
        )
        source = builder.build_alchemist_shapeshift(stock)
        self.assertEqual(source.count("function Alchemist_Shapeshift_Potion_Effect"), 1)
        self.assertEqual(source.count("function Shapeshift_Potion_End"), 1)
        self.assertIn(builder.ALCHEMIST_SHAPESHIFT_ACTION_NAME, source)
        self.assertEqual(
            source.count('$ChangeUnitType ( thisagent, "Giant_Spider" )'), 1
        )
        for stock_form in ("Dryad", "Medusa", "Minotaur"):
            self.assertIn(f'$ChangeUnitType ( thisagent, "{stock_form}" )', source)
        for gain, loss in (
            ("#ATTRIB_Strength, 18", "#ATTRIB_Strength, -18"),
            ("#ATTRIB_Vitality, 15", "#ATTRIB_Vitality, -15"),
            ("#ATTRIB_MaxHP, 30", "#ATTRIB_MaxHP, -30"),
            ("#ATTRIB_ActionRateModifier, -50", "#ATTRIB_ActionRateModifier, 50"),
        ):
            self.assertIn(gain, source)
            self.assertIn(loss, source)
        self.assertIn("$RevertUnitType ( thisagent )", source)
        self.assertIn("#ATTRIB_MaxHP, 40", source)

    def test_alchemist_unit_uses_only_private_alchemist_spells(self) -> None:
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        units = builder.build_units_xml(
            game / "SDK" / "OriginalQuests" / "Data" / "M_Buildings.xml",
            game / "SDK" / "OriginalQuests" / "Data" / "M_Characters.xml",
        )
        root = ET.fromstring(units)
        hero = root.find('./Description[@Name="Alchemist"]')
        self.assertIsNotNone(hero)
        self.assertEqual(
            hero.find("./Game/HelpID").get("value"),
            builder.ALCHEMIST_HERO_HELP_ID,
        )
        self.assertEqual(
            hero.find("./Game/NameGenType").get("value"),
            builder.ALCHEMIST_NAME_GENERATOR_ID,
        )
        self.assertEqual(
            hero.find("./Engine/DefaultSound").get("value"),
            builder.ALCHEMIST_HERO_SOUND,
        )
        buildings = [
            root.find(f'./Description[@Name="{name}"]')
            for name in builder.BUILDING_NAMES
        ]
        self.assertEqual(
            [building.find("./Game/HelpID").get("value") for building in buildings],
            list(builder.ALCHEMIST_BUILDING_HELP_IDS),
        )
        self.assertEqual(
            [building.find("./Engine/DefaultSound").get("value") for building in buildings],
            [builder.ALCHEMIST_LAB_SOUND] * 3,
        )
        self.assertEqual(
            hero.find("./Game/Cost").get("value"),
            builder.ALCHEMIST_RECRUIT_COST,
        )
        self.assertEqual(
            [building.find("./Game/Cost").get("value") for building in buildings],
            list(builder.ALCHEMIST_BUILDING_COSTS),
        )
        spells = hero.findall("./Game/AllowedSpells/Spell")
        self.assertEqual(
            [(spell.get("ID"), spell.get("Value")) for spell in spells],
            [
                ("0", "stun_serum"),
                ("1", "flash_flask"),
                ("2", "miasma_mist"),
            ],
        )
        units_text = units.decode("utf-8")
        for cultist_spell in ("camouflage", "change_shape", "charm_monster"):
            self.assertNotIn(cultist_spell, units_text)
        attack_range = hero.find("./Game/AttackRange")
        self.assertIsNotNone(attack_range)
        self.assertEqual((attack_range.get("min"), attack_range.get("max")), ("1", "1"))
        for field_name, expected in (
            ("Vitality", "11"),
            ("Intelligence", "18"),
            ("Artifice", "20"),
            ("Attack", "45"),
            ("Parry", "35"),
            ("Dodge", "40"),
            ("WeaponBasicDamage", "6"),
        ):
            self.assertEqual(hero.find(f"./Game/{field_name}").get("value"), expected)

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
        self.assertIn('"AlchemistsLaboratory3"', fixture)
        self.assertEqual(fixture.count('"MaxHP"'), 1)
        self.assertIn('alchemyLab\'s "num_resources" = 20;', fixture)
        self.assertIn(
            "$SetAttribute ( alchemyLab, #ATTRIB_ReturnAmount, 20 )", fixture
        )
        self.assertIn(
            "$Alchemist_Update_Reagent_Ready_Effector ( alchemyLab )", fixture
        )
        self.assertEqual(
            fixture.count('$SpawnUnit ( palace, "Warrior"'),
            2,
        )
        self.assertEqual(
            fixture.count('$SpawnUnit ( alchemyLab, "Alchemist"'),
            2,
        )
        self.assertEqual(fixture.count("$Advance_To_Level"), 4)
        self.assertEqual(fixture.count("#ATTRIB_Gold, 5000"), 4)
        for attribute in (
            "#ATTRIB_Weapon_Struct_Bonus, 3",
            "#ATTRIB_Armor_Struct_Bonus, 3",
            "#ATTRIB_Weapon_Magic_Bonus, 3",
            "#ATTRIB_Armor_Magic_Bonus, 3",
        ):
            self.assertEqual(fixture.count(attribute), 4)
        for removed in (
            '"Temple_Fervus1"',
            '"Temple_Krolm"',
            '"Wizards_Guild3"',
            '"MagicBazaar3"',
            '"Rogues_Guild1"',
            '"Warriors_Guild"',
            "#ATTRIB_ResearchArrows",
            "#ATTRIB_ResearchPowerfulItem",
            "#ATTRIB_ResearchBazaar_Item_",
            "#ATTRIB_Intelligence, 100",
            "Alchemist_Oil_Test_Buyer",
            '"ActiveScript"',
        ):
            self.assertNotIn(removed, fixture)
        self.assertNotIn("function NEXT", fixture)

    def test_siege_fixture_is_an_explicit_project_source(self) -> None:
        self.assertEqual(
            builder.build_gpl_project(False),
            'data="Alchemist_Building_Data.dat"\n'
            'data="Alchemist_Hero_Data.dat"\n'
            'data="Alchemist_Phoenix_Phial.dat"\n'
            'source="Alchemist_Rogue.gpl"\n'
            'source="Alchemist_Embassy.gpl"\n'
            'source="Alchemist_Guild_Title.gpl"\n'
            'source="Alchemist_Adopt.gpl"\n'
            'source="Alchemist_Magic_Bazaar.gpl"\n'
            'source="Alchemist_Nearby_Equipment.gpl"\n'
            'source="Alchemist_Inventory.gpl"\n'
            'source="Alchemist_Consumable_Threat.gpl"\n'
            'source="Alchemist_Strength_Potion.gpl"\n'
            'source="Alchemist_Shapeshift.gpl"\n'
            'source="Alchemist_Stun_Serum.gpl"\n'
            'source="Alchemist_Flash_Flask.gpl"\n'
            'source="Alchemist_Miasma_Mist.gpl"\n'
            'source="Alchemist_Brewing.gpl"\n'
            'source="Alchemist_Economy.gpl"\n'
            'source="Alchemist_Weapon_Oil.gpl"\n'
            'source="Alchemist_Combat_Oils.gpl"\n'
            'source="Alchemist_Damage.gpl"\n'
            'source="Alchemist_Phoenix_Phial.gpl"\n'
            'source="Alchemist_Reagents.gpl"\n',
        )
        self.assertIn(
            'source="Alchemist_Siege_Test.gpl"', builder.build_gpl_project(True)
        )
        fixture_manifest = builder.build_manifest(include_siege_test_fixture=True)
        self.assertIn(
            "<Source>GPL\\Alchemist_Shapeshift.gpl</Source>", fixture_manifest
        )
        self.assertIn(
            "<Source>GPL\\Alchemist_Consumable_Threat.gpl</Source>",
            fixture_manifest,
        )
        self.assertIn(
            "<Descriptions>Data\\alchemist_combat_potions.xml</Descriptions>",
            fixture_manifest,
        )
        self.assertIn(
            "<Source>GPL\\Alchemist_Siege_Test.gpl</Source>", fixture_manifest
        )
        self.assertNotIn(
            "<Source>GPL\\Alchemist_Siege_Test.gpl</Source>",
            builder.build_manifest(),
        )

    def test_siege_fixture_compiled_symbols_are_fail_closed(self) -> None:
        compiled = b"SIEGE\x00"
        builder.validate_siege_test_symbols(compiled, True)
        builder.validate_siege_test_symbols(b"ordinary package", False)
        with self.assertRaisesRegex(ValueError, "lost symbols"):
            builder.validate_siege_test_symbols(b"ordinary package", True)
        with self.assertRaisesRegex(ValueError, "unexpectedly exports"):
            builder.validate_siege_test_symbols(compiled, False)
        with self.assertRaisesRegex(ValueError, "retains removed symbols"):
            builder.validate_siege_test_symbols(
                b"SIEGE\x00Alchemist_Oil_Test_Buyer\x00", True
            )

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
        self.assertEqual(
            generated.count(
                'If (ThisAgent\'s "Poison_Weapon_Chance" > $RandomNumber (100) + 1)'
            ),
            1,
        )
        self.assertNotIn(
            "If ($GetAttribute (ThisAgent, #ATTRIB_WeaponPoisoned) == 0)",
            generated,
        )
        self.assertIn("$Phoenix_Phial_Check (ThisAgent,phoenixLabs)", generated)
        self.assertLess(
            generated.index("$Ring_Check"),
            generated.index("$Phoenix_Phial_Check"),
        )
        self.assertLess(
            generated.index("$Phoenix_Phial_Check"),
            generated.index("$Market3_Check"),
        )
        self.assertLess(
            generated.index("$Alchemy_Oil_Check"), generated.index("$Poison_Check")
        )

    def test_weapon_oil_selects_private_coating_from_stock_greed(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Weapon_Oil.gpl").read_text(
            encoding="utf-8"
        )
        self.assertIn('$HasAttribute ("AlchemyWeaponOilType", ThisAgent)', source)
        self.assertIn('ThisAgent\'s "AlchemyWeaponOilType" > 0', source)
        self.assertIn("expression #Alchemy_Weapon_Oil_Price 100", source)
        self.assertNotIn("#Cost_Per_Magic_Enchantment1", source)
        self.assertNotIn("Intel_Roll", source)
        self.assertNotIn("$RandomNumber (30)", source)
        self.assertIn("#Enchant_Equipment_Visit_Duration", source)
        self.assertIn("$Spend_Gold (ThisAgent, ThisBuilding, Gold)", source)
        self.assertNotIn("$SetAttribute (ThisAgent, What_To_Upgrade, Upgrade)", source)
        self.assertEqual(source.count("#ATTRIB_WeaponPoisoned"), 1)
        self.assertIn(
            '$AddAttribute (\n\t\t\t\t\tThisAgent,\n\t\t\t\t\t"AlchemyWeaponOilType"',
            source,
        )
        self.assertIn('ThisAgent\'s "AlchemyWeaponOilType" = Upgrade', source)
        self.assertIn("$Alchemist_Done_Enhancing_Equipment", source)
        self.assertNotIn("#ATTRIB_Weapon_Magic_Bonus", source)
        self.assertNotIn("#ATTRIB_Armor_Magic_Bonus", source)
        self.assertIn("expression #Intent_Applying_Weapon_Oil 309", source)
        self.assertIn(
            "$SpecifyIntent (ThisAgent, #Intent_Applying_Weapon_Oil)", source
        )
        self.assertNotIn("#Intent_Poisoning_Weapon", source)
        self.assertIn("expression #Alchemy_Transmutation_Greed 20", source)
        self.assertIn('ThisAgent\'s "Greed" > #Alchemy_Transmutation_Greed', source)
        self.assertIn("Upgrade = 1", source)
        self.assertIn("Upgrade = 2", source)
        self.assertIn("Function Alchemist_Done_Enhancing_Equipment", source)
        self.assertIn('"alchemist_paralytic_weapon_oil_status"', source)
        self.assertIn('"alchemist_transmutation_weapon_oil_status"', source)
        self.assertIn("Function Obtain_Poison", source)
        self.assertIn(
            '$SetAttribute (ThisAgent, #ATTRIB_WeaponPoisoned, 1)', source
        )
        self.assertIn('"alchemist_poisoned_weapon_status"', source)
        self.assertIn(
            'ThisAgent\'s "ActiveScript" = $Done_Poisoning_Weapon', source
        )
        self.assertEqual(source.count('"Infinite"'), 3)
        self.assertLess(
            source.index('$Exit_Building (ThisAgent, ThisAgent\'s "Target")'),
            source.index('"alchemist_paralytic_weapon_oil_status"'),
        )
        self.assertIn(
            'ThisAgent\'s "ActiveScript" = $Alchemist_Done_Enhancing_Equipment',
            source,
        )

    def test_damage_is_a_literal_stock_clone_with_two_private_oil_branches(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\SDK\OriginalQuests"
            r"\GPLMx\TaskModules\Subtasks\mx_make_attack.gpl"
        )
        generated = builder.build_alchemist_damage(stock)
        self.assertEqual(generated.count("function damage"), 1)
        self.assertIn("#ATTRIB_weaponpoisoned ) == 1", generated)
        self.assertEqual(generated.count("$poison_begin ( attacker, defender )"), 1)
        self.assertIn('$HasAttribute ("AlchemyWeaponOilType", Attacker)', generated)
        self.assertIn('Attacker\'s "AlchemyWeaponOilType" == 1', generated)
        self.assertIn("$Alchemy_Paralytic_Oil_Begin (Attacker, Defender)", generated)
        self.assertIn('Attacker\'s "AlchemyWeaponOilType" == 2', generated)
        self.assertIn("$Alchemy_Transmutation_Oil_Hit (Attacker, Defender)", generated)

    def test_paralytic_oil_uses_fixed_restraint_and_private_target_immunity(self) -> None:
        source = (
            builder.GPL_SOURCE_ROOT / "Alchemist_Combat_Oils.gpl"
        ).read_text(encoding="utf-8")
        immunity_check = (
            '$CheckEffector (Target, "alchemist_paralytic_oil_immunity")'
        )
        immunity_create = '"alchemist_paralytic_oil_immunity",'
        self.assertIn("expression #Alchemy_Paralytic_Duration 2000", source)
        self.assertIn(
            "expression #Alchemy_Paralytic_Immunity_Duration 10000", source
        )
        self.assertIn(immunity_check, source)
        self.assertEqual(source.count(immunity_create), 1)
        self.assertLess(
            source.index(immunity_check),
            source.index('"alchemist_paralytic_oil_restraint"'),
        )
        self.assertNotIn("Alchemy_Paralytic_Stage", source)
        self.assertNotIn("Duration = 3000", source)
        self.assertNotIn("Duration = 1000", source)
        self.assertNotIn('"alchemist_stun_serum_impact"', source)
        self.assertNotIn('"alchemist_stun_serum_restraint"', source)
        self.assertNotIn('"alchemist_paralytic_oil_icon"', source)
        self.assertIn('"after"', source)

    def test_private_oil_intent_appends_to_stock_aitx(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\DataMX\mx_gpltext.cam"
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "oil_gpltext.cam"
            builder.build_gpl_text_cam(stock, output)
            intents = builder.read_cam_entry(output, b"STRT", b"AITX").data
            items = builder.read_cam_entry(output, b"STRT", b"QITM").data
            help_pages = builder.read_cam_entry(output, b"STRT", b"HPTX").data
            name_tables = {
                table_id: builder.read_cam_entry(output, b"STRT", table_id).data
                for table_id in builder.ALCHEMIST_NAME_TABLE_IDS
            }
        stock_intents = builder.read_cam_entry(stock, b"STRT", b"AITX").data
        stock_count = struct.unpack_from("<H", stock_intents, 0)[0]
        self.assertEqual(stock_count, builder.ALCHEMY_OIL_INTENT_INDEX)
        count = struct.unpack_from("<H", intents, 0)[0]
        self.assertEqual(count, builder.PHOENIX_PHIAL_INTENT_INDEX + 1)
        stock_offsets = struct.unpack_from(f"<{stock_count}I", stock_intents, 4)
        offsets = struct.unpack_from(f"<{count}I", intents, 4)
        for index in range(stock_count):
            stock_end = stock_intents.index(b"\x00", stock_offsets[index] + 4)
            output_end = intents.index(b"\x00", offsets[index] + 4)
            self.assertEqual(
                stock_intents[stock_offsets[index] + 4 : stock_end],
                intents[offsets[index] + 4 : output_end],
                f"stock AITX entry {index} changed",
            )
        offset = offsets[builder.ALCHEMY_OIL_INTENT_INDEX]
        end = intents.index(b"\x00", offset + 4)
        self.assertEqual(
            intents[offset + 4 : end].decode("cp1252"),
            builder.ALCHEMY_OIL_INTENT_TEXT,
        )
        item_count = struct.unpack_from("<H", items, 0)[0]
        self.assertEqual(item_count, builder.PHOENIX_PHIAL_ITEM_ID + 1)
        item_offset = struct.unpack_from(
            "<I", items, 4 + builder.PHOENIX_PHIAL_ITEM_ID * 4
        )[0]
        item_end = items.index(b"\x00", item_offset + 4)
        self.assertEqual(
            items[item_offset + 4 : item_end].decode("cp1252"),
            builder.PHOENIX_PHIAL_ITEM_TEXT,
        )
        help_count = struct.unpack_from("<H", help_pages, 0)[0]
        help_offsets = struct.unpack_from(f"<{help_count}I", help_pages, 4)
        decoded_help = {}
        for help_offset in help_offsets:
            help_end = help_pages.index(b"\x00", help_offset + 4)
            decoded_help[struct.unpack_from("<I", help_pages, help_offset)[0]] = (
                help_pages[help_offset + 4 : help_end].decode("cp1252")
            )
        for help_id, expected_text in builder.ALCHEMIST_HELP_PAGES.items():
            self.assertEqual(decoded_help[builder.fourcc_id(help_id)], expected_text)
        self.assertFalse(
            any("\u2014" in text for text in builder.ALCHEMIST_HELP_PAGES.values())
        )
        expected_name_tables = (
            builder.ALCHEMIST_NAME_GIVENS,
            tuple(f" {ending}" for ending in builder.ALCHEMIST_NAME_ENDINGS),
            (),
            (),
        )
        self.assertEqual(len(builder.ALCHEMIST_NAME_GIVENS), 43)
        self.assertEqual(len(builder.ALCHEMIST_NAME_ENDINGS), 43)
        self.assertEqual(len(set(builder.ALCHEMIST_NAME_GIVENS)), 43)
        self.assertEqual(len(set(builder.ALCHEMIST_NAME_ENDINGS)), 43)
        for table_id, expected_names in zip(
            builder.ALCHEMIST_NAME_TABLE_IDS, expected_name_tables
        ):
            table = name_tables[table_id]
            table_count = struct.unpack_from("<H", table, 0)[0]
            table_offsets = struct.unpack_from(f"<{table_count}I", table, 4)
            actual_names = []
            for index, table_offset in enumerate(table_offsets):
                self.assertEqual(struct.unpack_from("<I", table, table_offset)[0], index)
                table_end = table.index(b"\x00", table_offset + 4)
                actual_names.append(
                    table[table_offset + 4 : table_end].decode("cp1252")
                )
            self.assertEqual(tuple(actual_names), expected_names)
        self.assertFalse(
            any(
                "\u2014" in text
                for text in (
                    *builder.ALCHEMIST_NAME_GIVENS,
                    *builder.ALCHEMIST_NAME_ENDINGS,
                )
            )
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
        reagent_charge = "$Alchemist_Consume_Reagent_Stock(ThisAgent, 1)"
        self.assertIn(reagent_charge, source)
        self.assertLess(
            source.index(reagent_charge),
            source.index('$AdjustPlayerData(Palace, "Gold", -1500)'),
        )
        vigor_visual = (
            '$CreateEffector(ThisAgent, '
            '"alchemist_vigor_activation_effector", 0)'
        )
        self.assertIn(vigor_visual, source)
        self.assertLess(
            source.index('$AdjustPlayerData(Palace, "Gold", -1500)'),
            source.index(vigor_visual),
        )
        self.assertLess(source.index(vigor_visual), source.index("$ListObjects"))
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
        stock = """<Majesty><Description type="Unit" subType="Overlay" ID="QRa1" Name="Rage_icon" Description="Rage of Krolm"><Engine><Info value="Directionless"/><Info value="DontBlock"/><ImageIDBase value="QRa1"/><Script type="0" cProc="0" GPLFunction="rage_end"/></Engine><Game><StackPriority value="1"/></Game></Description><Description type="Unit" subType="Overlay" ID="QRd0" Name="ring_icon" Description="This hero has the Magic Ring."><Engine><Info value="Static"/><Info value="Directionless"/><Info value="DontBlock"/><Menu value="11"/><ImageIDBase value="QRd0"/><DefaultSound value="0"/></Engine><Game><DialogID value="0"/><StackPriority value="0"/></Game></Description><Description type="Unit" subType="Overlay" ID="HRC1" Name="resurrection_effector" Description="Resurrection"><Engine><Info value="Directionless"/><Info value="DontBlock"/><Menu value="11"/><ImageIDBase value="HRC1"/><DefaultSound value="Resurrection"/><Script type="0" cProc="0" GPLFunction="Resurrection_End"/></Engine><Game><StackPriority value="0"/><Flags value="TransparentToMouse"/></Game></Description><Description type="Unit" subType="Overlay" ID="ARB2" Name="Got_Gold" Description="Got gold"><Engine><Info value="Directionless"/><Info value="DontBlock"/><CanUse value="HumanPlayer"/><Menu value="11"/><ImageIDBase value="ARB2"/><DefaultSound value="Got_Gold"/></Engine><Game><DialogID value="0"/><StackPriority value="0"/></Game></Description><Description type="Unit" subType="Overlay" ID="WRF1" Name="super_charge_effector" Description="Super Charge"><Engine><Info value="Directionless"/><Info value="DontBlock"/><Menu value="11"/><ImageIDBase value="WRF1"/><DefaultSound value="Supercharge"/></Engine><Game><DialogID value="0"/><StackPriority value="0"/><Flags value="TransparentToMouse"/></Game></Description></Majesty>"""
        stock = stock.replace(
            "</Majesty>",
            '<Description type="Unit" subType="Overlay" ID="ARD1" '
            'Name="got_gold_bldg" Description="Building getting gold">'
            '<Engine><Info value="Directionless"/><Info value="DontBlock"/>'
            '<CanUse value="HumanPlayer"/><Menu value="11"/>'
            '<ImageIDBase value="ARD1"/><DefaultSound value="Got_Gold"/>'
            '</Engine><Game><DialogID value="0"/><StackPriority value="0"/>'
            '</Game></Description></Majesty>',
        )
        mx_stock = '<Majesty><Description type="Unit" subType="Overlay" ID="XR01" Name="Speed_Tonic_Icon" Description="Speed Tonic"><Engine><Info value="Directionless"/><Info value="DontBlock"/><Menu value="11"/><ImageIDBase value="XR01"/><Script type="0" cProc="0" GPLFunction="Speed_Tonic_End"/><DefaultSound value="0"/></Engine><Game><DialogID value="0"/><StackPriority value="1"/></Game></Description><Description type="Unit" subType="Overlay" ID="XR30" Name="Frost_Field_Hit_Effector" Description="Frost Field"><Engine><Info value="Directionless"/><Info value="DontBlock"/><Menu value="11"/><ImageIDBase value="XR30"/><AttachmentPointID value="2"/><DefaultSound value="Frost_Field_hit"/></Engine><Game><DialogID value="0"/><StackPriority value="0"/><Flags value="TransparentToMouse"/></Game></Description></Majesty>'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "M_Overlays.xml"
            mx_path = Path(directory) / "MX_Overlays.xml"
            path.write_text(stock, encoding="utf-8")
            mx_path.write_text(mx_stock, encoding="utf-8")
            output = ET.fromstring(
                builder.build_brewing_overlays_xml(path, mx_path)
            )
        overlay = output.find("Description")
        self.assertEqual(overlay.get("ID"), "AXE1")
        self.assertEqual(overlay.get("Name"), "alchemist_invigorating_elixer_icon")
        self.assertEqual(
            overlay.find("./Engine/Script").get("GPLFunction"),
            "Alchemist_Invigorating_Elixer_End",
        )
        self.assertEqual(overlay.find("./Engine/ImageIDBase").get("value"), "ALV1")
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
        stone = output.findall("Description")[2]
        self.assertEqual(stone.get("ID"), "AST1")
        self.assertEqual(stone.get("Name"), "philosophers_stone_hit_effector")
        self.assertEqual(stone.find("./Engine/ImageIDBase").get("value"), "AST1")
        self.assertEqual(stone.find("./Engine/DefaultSound").get("value"), "0")
        self.assertIsNone(stone.find("./Engine/AttachmentPointID"))
        self.assertEqual(stone.find("./Engine/CanUse").get("value"), "HumanPlayer")
        infusion = output.findall("Description")[3]
        self.assertEqual(infusion.get("ID"), "AIF1")
        self.assertEqual(
            infusion.get("Name"), "alchemist_arcane_infusion_effector"
        )
        self.assertEqual(
            infusion.find("./Engine/ImageIDBase").get("value"), "AIF1"
        )
        self.assertEqual(infusion.find("./Engine/DefaultSound").get("value"), "0")
        self.assertIsNone(infusion.find("./Engine/AttachmentPointID"))
        self.assertEqual(
            infusion.find("./Engine/CanUse").get("value"), "HumanPlayer"
        )
        vigor_activation = output.findall("Description")[4]
        self.assertEqual(vigor_activation.get("ID"), "AIV1")
        self.assertEqual(
            vigor_activation.get("Name"),
            "alchemist_vigor_activation_effector",
        )
        self.assertEqual(
            vigor_activation.find("./Engine/ImageIDBase").get("value"),
            "AIV1",
        )
        self.assertEqual(
            vigor_activation.find("./Engine/DefaultSound").get("value"), "0"
        )
        self.assertIsNone(vigor_activation.find("./Engine/AttachmentPointID"))
        self.assertEqual(
            vigor_activation.find("./Engine/CanUse").get("value"),
            "HumanPlayer",
        )
        ready = output.findall("Description")[5]
        self.assertEqual(ready.get("ID"), "ARR1")
        self.assertEqual(ready.get("Name"), "alchemist_reagent_ready_effector")
        self.assertEqual(ready.find("./Engine/ImageIDBase").get("value"), "ALR1")
        self.assertEqual(ready.find("./Engine/DefaultSound").get("value"), "0")
        self.assertIsNone(ready.find("./Engine/AttachmentPointID"))
        self.assertIsNotNone(ready.find('./Engine/Info[@value="Directionless"]'))
        self.assertEqual(ready.find("./Game/StackPriority").get("value"), "0")
        statuses = output.findall("Description")[6:]
        self.assertEqual(len(statuses), 3)
        self.assertEqual(
            [
                (item.get("ID"), item.get("Name"), item.get("Description"))
                for item in statuses
            ],
            [
                (
                    builder.PARALYTIC_OIL_STATUS_ID,
                    builder.PARALYTIC_OIL_STATUS_NAME,
                    "Paralytic Weapon Oil",
                ),
                (
                    builder.TRANSMUTATION_OIL_STATUS_ID,
                    builder.TRANSMUTATION_OIL_STATUS_NAME,
                    "Transmutation Weapon Oil",
                ),
                (
                    builder.POISONED_WEAPON_STATUS_ID,
                    builder.POISONED_WEAPON_STATUS_NAME,
                    "Poisoned Weapon",
                ),
            ],
        )
        for status in statuses:
            self.assertEqual(status.find("./Engine/Menu").get("value"), "11")
            self.assertEqual(
                status.find("./Engine/ImageIDBase").get("value"), "XR01"
            )
            self.assertIsNotNone(
                status.find('./Engine/Info[@value="NotVisibleInISOView"]')
            )
            self.assertIsNotNone(status.find('./Engine/Info[@value="Static"]'))
            self.assertIsNone(status.find("./Engine/Script"))
            self.assertEqual(
                status.find("./Game/StackPriority").get("value"), "0"
            )
        self.assertEqual(len(output.findall("Description")), 9)
        self.assertIsNone(
            output.find('./Description[@Name="phoenix_phial_visual_effector"]')
        )

    def test_flash_flask_is_a_private_shield_of_light_clone(self) -> None:
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        data = game / "SDK" / "OriginalQuests" / "Data"
        output = ET.fromstring(
            builder.build_flash_flask_xml(
                data / "M_Actions.xml",
                data / "M_Overlays.xml",
            )
        )
        action, icon, effect = output.findall("Description")
        self.assertEqual(
            (action.get("ID"), action.get("Name"), action.get("Description")),
            ("AFa1", "flash_flask", "Flash Flask"),
        )
        self.assertEqual(action.find("./Engine/ImageSet").get("value"), "Special")
        self.assertEqual(
            action.find("./Engine/CompletionImageSet").get("value"), "Stand"
        )
        self.assertEqual(
            action.find("./Engine/Script").get("GPLFunction"),
            "Alchemist_Flash_Flask_Begin",
        )
        self.assertEqual(action.find("./Game/EffectorDuration").get("value"), "30000")
        self.assertEqual(action.find("./Game/TimeoutDuration").get("value"), "45000")
        self.assertEqual(action.find("./Game/SpellType").get("value"), "Attack")
        self.assertEqual(action.find("./Game/CharacterLevel").get("value"), "3")
        self.assertEqual(action.find("./Game/SpellRank").get("value"), "4")
        self.assertEqual(icon.get("Name"), "alchemist_flash_flask_icon")
        self.assertEqual(icon.find("./Engine/ImageIDBase").get("value"), "AFF1")
        self.assertEqual(
            icon.find("./Engine/Script").get("GPLFunction"),
            "Alchemist_Flash_Flask_End",
        )
        self.assertEqual(effect.get("Name"), "alchemist_flash_flask_effector")
        self.assertEqual(effect.find("./Engine/ImageIDBase").get("value"), "AFF2")
        self.assertEqual(effect.find("./Engine/AttachmentPointID").get("value"), "2")
        self.assertIsNone(action.find("./Engine/Sound"))
        self.assertIsNone(action.find("./Engine/SoundPhase"))
        self.assertEqual(
            effect.find("./Engine/DefaultSound").get("value"), "Drink_Potion"
        )

    def test_flash_flask_copies_stock_duration_owned_stat_cleanup(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Flash_Flask.gpl").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '$GetSpellAttribute("flash_flask", "effector_duration")', source
        )
        self.assertIn(
            '$CreateEffector(ThisAgent, "alchemist_flash_flask_effector", 0)', source
        )
        for begin, end in (
            ("#ATTRIB_Dodge, 10", "#ATTRIB_Dodge, -10"),
            ("#ATTRIB_Parry, 10", "#ATTRIB_Parry, -10"),
            ("#ATTRIB_ActionRateModifier, -400", "#ATTRIB_ActionRateModifier, 400"),
        ):
            self.assertIn(begin, source)
            self.assertIn(end, source)
        for forbidden in ("$RunThread", "$Sleep", "$CheckEffector"):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("Alchy_Cast", source)

    def test_stun_serum_clones_paralytic_gaze_and_vines_cleanup(self) -> None:
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        data = game / "SDK" / "OriginalQuests" / "Data"
        output = ET.fromstring(
            builder.build_stun_serum_xml(
                data / "M_Actions.xml",
                data / "M_Overlays.xml",
            )
        )
        action = output.find('./Description[@Name="stun_serum"]')
        self.assertEqual(action.find("./Engine/ImageSet").get("value"), "Cast")
        self.assertEqual(action.find("./Game/EffectorDuration").get("value"), "5000")
        self.assertEqual(action.find("./Game/TimeoutDuration").get("value"), "45000")
        self.assertEqual(action.find("./Game/CharacterLevel").get("value"), "5")
        self.assertEqual(action.find("./Game/SpellRank").get("value"), "5")
        self.assertEqual(
            action.find("./Engine/Sound").get("value"),
            builder.ALCHEMIST_CAST_VOICE_SOUND,
        )
        self.assertEqual(
            action.find("./Game/ValidationScript").get("value"),
            "Alchemist_Stun_Serum_Check",
        )
        restraint = output.find(
            './Description[@Name="alchemist_stun_serum_restraint"]'
        )
        self.assertEqual(restraint.find("./Engine/ImageIDBase").get("value"), "ASS2")
        self.assertEqual(
            restraint.find("./Engine/Script").get("GPLFunction"),
            "Alchemist_Stun_Serum_End",
        )
        icon = output.find('./Description[@Name="alchemist_stun_serum_icon"]')
        self.assertIsNone(icon)
        oil_restraint = output.find(
            './Description[@Name="alchemist_paralytic_oil_restraint"]'
        )
        self.assertIsNotNone(oil_restraint)
        self.assertEqual(
            oil_restraint.find("./Engine/ImageIDBase").get("value"), "ASO3"
        )
        self.assertEqual(
            oil_restraint.find("./Engine/Script").get("GPLFunction"),
            "Alchemy_Paralytic_Oil_End",
        )
        self.assertIsNone(
            output.find('./Description[@Name="alchemist_paralytic_oil_icon"]')
        )
        immunity = output.find(
            './Description[@Name="alchemist_paralytic_oil_immunity"]'
        )
        self.assertIsNotNone(
            immunity.find('./Engine/Info[@value="NotVisibleInISOView"]')
        )
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Stun_Serum.gpl").read_text(
            encoding="utf-8"
        )
        for stock_call in ("$Freeze_Unit (Target)", "$UnFreeze_Unit (ThisAgent)"):
            self.assertIn(stock_call, source)
        self.assertIn("Function Alchemist_Stun_Serum_Check", source)
        self.assertIn('Target\'s "Type" != "Lair"', source)
        self.assertIn('Target\'s "Type" != "Building"', source)
        self.assertIn('ThisAgent\'s "castingrange"', source)
        self.assertIn('"alchemist_stun_serum_restraint",', source)
        self.assertIn('"after"', source)
        self.assertNotIn("Alchy_Cast", source)
        self.assertNotIn('"alchemist_stun_serum_icon"', source)
        for forbidden in ("$RunThread", "$Sleep", "$CheckEffector"):
            self.assertNotIn(forbidden, source)

    def test_miasma_mist_clones_meteor_storm_and_endless_winter(self) -> None:
        game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD")
        data = game / "SDK" / "OriginalQuests" / "Data"
        output = ET.fromstring(
            builder.build_miasma_mist_xml(
                data / "M_Actions.xml",
                data / "M_Characters.xml",
                data / "M_Projectiles.xml",
                data / "M_Overlays.xml",
                data / "M_ParticleSystems.xml",
            )
        )
        action = output.find('./Description[@Name="miasma_mist"]')
        self.assertIsNotNone(action)
        self.assertEqual(action.find("./Engine/ImageSet").get("value"), "Cast")
        self.assertEqual(action.find("./Game/EffectorDuration").get("value"), "21000")
        self.assertEqual(action.find("./Game/TimeoutDuration").get("value"), "60000")
        self.assertEqual(action.find("./Game/CharacterLevel").get("value"), "8")
        self.assertEqual(action.find("./Game/SpellRank").get("value"), "4")
        self.assertEqual(
            action.find("./Engine/Sound").get("value"),
            builder.ALCHEMIST_CAST_VOICE_SOUND,
        )
        self.assertEqual(
            action.find("./Game/ValidationScript").get("value"),
            "Alchemist_Miasma_Mist_Check",
        )
        expected = {
            "miasma_mist_cloud": ("AMm6", "Alchemist_Miasma_Mist_Unit_Created"),
            "miasma_mist_missile": ("AMm2", "Alchemist_Miasma_Mist_Missile_Hit"),
            "miasma_mist_cloud_effector": ("AMm1", None),
            "miasma_mist_debuff_icon": ("AMm5", None),
            "miasma_mist_cloud_attachment": ("AMm4", None),
        }
        for name, (image, callback) in expected.items():
            description = output.find(f'./Description[@Name="{name}"]')
            self.assertIsNotNone(description)
            self.assertEqual(description.find("./Engine/ImageIDBase").get("value"), image)
            if callback is not None:
                self.assertEqual(
                    description.find("./Engine/Script").get("GPLFunction"), callback
                )

        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Miasma_Mist.gpl").read_text(
            encoding="utf-8"
        )
        for stock_contract in (
            "expression #Alchemist_Miasma_Mist_Radius 175",
            "expression #Alchemist_Miasma_Mist_Debuff_Duration 10000",
            '$NewThread(ThisAgent\'s "ActiveScript", 1600, ThisAgent)',
            "$Alchemist_Miasma_Mist_Active(ThisAgent)",
            "$player_spell_attack(Target, 1, 1)",
            "$compile_enemies(ThisAgent, #Alchemist_Miasma_Mist_Radius)",
            "$ListSize(Targets) > 0",
            'Target\'s "Type" == "Building"',
            'Target\'s "Type" == "Lair"',
            "#ATTRIB_Dodge, -10",
            "#ATTRIB_Dodge, 10",
            "#ATTRIB_Parry, -10",
            "#ATTRIB_Parry, 10",
            "#ATTRIB_MovementRateModifier, 100",
            "#ATTRIB_MovementRateModifier, -100",
            "#ATTRIB_ActionRateModifier, 1000",
            "#ATTRIB_ActionRateModifier, -1000",
            '"miasma_mist_debuff_icon", 1, "infinite"',
        ):
            self.assertIn(stock_contract, source)
        self.assertNotIn("$alchemist_combat_consumable_check(ThisAgent)", source)
        check_source = source.split(
            "function Alchemist_Miasma_Mist_Hit", 1
        )[0]
        self.assertNotIn("foreach Target in Targets do", check_source)
        self.assertEqual(source.count("#Alchemist_Miasma_Mist_Debuff_Duration;"), 1)
        self.assertIn("$SetSpellUnitTimeout(ThisAgent, Duration)", source)
        self.assertNotIn("Alchy_Cast", source)
        for forbidden_tracking in (
            "MiasmaMistTracking",
            "MiasmaMistCleanup",
            "Alchemist_Miasma_Mist_Track",
            "$SetParent",
            "$TeleportToUnit",
        ):
            self.assertNotIn(forbidden_tracking, source)

        reagent_source = (
            builder.GPL_SOURCE_ROOT / "Alchemist_Reagents.gpl"
        ).read_text(encoding="utf-8")
        for stock_resource_contract in (
            "function Alchemist_Arcane_Infusion",
            "function Alchemist_Apply_Arcane_Infusion",
            "#ATTRIB_ResearchArrows",
            "#ATTRIB_MagicResistance, 25",
            '"AlchemistArcaneInfusionApplied"',
            '"resist_magic_effector"',
            '"alchemist_arcane_infusion_effector"',
            '$ListObjects ( laboratory, "hero", -1, Heroes, #MyPlayer,',
            'alchemist\'s "num_picked_goodies" += 1',
            '$Drop_Off_Goodies ( ThisAgent, ThisBuilding )',
            "#Alchemist_Reagent_Carry_Limit 3",
            "$Alchemist_Update_Reagent_Ready_Effector ( ThisBuilding )",
            "$Alchemist_Update_Reagent_Ready_Effector ( laboratory )",
            'laboratory\'s "Level" >= 3',
            'laboratory\'s "num_resources" >= 10',
            '"alchemist_reagent_ready_effector"',
            '"Infinite"',
        ):
            self.assertIn(stock_resource_contract, reagent_source)
        infusion_source = reagent_source.split(
            "function Alchemist_Arcane_Infusion", 1
        )[1].split(
            "function Philosophers_Stone_Hit", 1
        )[0]
        consume = "$Alchemist_Consume_Reagent_Stock ( laboratory, 10 )"
        visual = (
            '$CreateEffector ( laboratory, '
            '"alchemist_arcane_infusion_effector", 0 )'
        )
        self.assertIn(visual, infusion_source)
        self.assertLess(infusion_source.index(consume), infusion_source.index(visual))
        self.assertLess(
            infusion_source.index(visual),
            infusion_source.index("#ATTRIB_ResearchArrows, 1"),
        )
        ready_source = reagent_source.split(
            "function Alchemist_Update_Reagent_Ready_Effector", 1
        )[1].split(
            "function Alchemist_Consume_Reagent_Stock", 1
        )[0]
        self.assertEqual(ready_source.count("$CheckEffector"), 1)
        self.assertEqual(ready_source.count("$CreateEffector"), 1)
        self.assertEqual(ready_source.count("$DeleteEffector"), 1)
        self.assertNotIn("$NewThread", ready_source)
        self.assertNotIn("$RunThread", ready_source)
        ready_birth = reagent_source.split(
            "function Alchemist_Laboratory_Birth_Or_Upgrade", 1
        )[1].split(
            "function Alchemist_Laboratory_Upgrade", 1
        )[0]
        ready_upgrade = reagent_source.split(
            "function Alchemist_Laboratory_Upgrade", 1
        )[1].split(
            "function Alchemist_Update_Reagent_Ready_Effector", 1
        )[0]
        self.assertEqual(ready_birth.count("$Guild_Birth"), 1)
        self.assertEqual(ready_birth.count("$RunThread"), 1)
        self.assertEqual(
            ready_birth.count("$Alchemist_Update_Reagent_Ready_Effector"), 2
        )
        self.assertIn("#ATTRIB_FirstStageBuilt", ready_birth)
        self.assertIn("#ATTRIB_CurrentStageBuilt", ready_birth)
        self.assertIn("#palace_upgrade_check", ready_birth)
        self.assertEqual(ready_upgrade.count("$basic_upgrade"), 1)
        self.assertEqual(ready_upgrade.count("$RunThread"), 1)
        self.assertIn("#palace_upgrade_check", ready_upgrade)
        self.assertNotIn("BuildingReachedMaxHP", reagent_source)
        for nonstock_inventory_contract in (
            "AlchemistReagent",
            "$CreateNewInventoryItem",
            "$AgentHasInventoryItem",
            "$DeleteInventoryItem",
            "#Allow_Cloned_Quest_Item",
            "function Hero_Drop_Quest_Items",
        ):
            self.assertNotIn(nonstock_inventory_contract, reagent_source)
        self.assertIn(
            "$spelldamage ( $nullagent(), target, 100000, 100000 )",
            reagent_source,
        )
        self.assertIn(
            'target\'s "type" != "monster" && target\'s "type" != "hero"',
            reagent_source,
        )
        self.assertNotIn("Alchemical_Tempest", reagent_source)
        self.assertIn("$compile_enemies ( thisagent, 45 )", reagent_source)
        stone_source = reagent_source.split(
            "function Philosophers_Stone_Hit", 1
        )[1]
        self.assertNotIn(
            "$player_spell_attack ( target, 100000, 100000 )",
            stone_source,
        )
        self.assertNotIn(
            '$CreateEffector ( thisagent, "miasma_mist_cloud_effector", 2300 )',
            reagent_source,
        )

    def test_phoenix_phial_composes_stock_purchase_rebirth_and_flee(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Phoenix_Phial.gpl").read_text(
            encoding="utf-8"
        )
        self.assertIn("expression #Phoenix_Phial_Price 750", source)
        self.assertIn("expression #Phoenix_Phial_Revive_Chance 75", source)
        self.assertIn("$AgentHasInventoryItem (#PhoenixPhial, ThisAgent)", source)
        self.assertIn("$CreateNewInventoryItem (#PhoenixPhial", source)
        self.assertIn("$DeleteInventoryItem (#PhoenixPhial, ThisAgent)", source)
        self.assertIn("$Shared_Begin_Resurrect (ThisAgent)", source)
        self.assertIn("$Shared_End_Resurrect (ThisAgent)", source)
        self.assertEqual(
            source.count(
                '$CreateEffector (ThisAgent, "phoenix_phial_resurrection_effector", 1500)'
            ),
            1,
        )
        self.assertNotIn("phoenix_phial_visual_effector", source)
        self.assertIn("$Flee_Absolute (ThisAgent, #intent_flee_lowHP)", source)
        self.assertNotIn("$Flee (ThisAgent, #intent_flee_lowHP)", source)
        self.assertIn("function gravestone(agent thisagent)", source)
        self.assertNotIn("$RunThread", source)

    def test_brewing_sound_has_a_private_description(self) -> None:
        stock = """<Majesty>
<Description type="Sound" subType="Standard" ID="DP01" Name="Drink_Potion"><Engine><Category value="0"/><Phase ID="Effector Begin"><Wave value="DP01"/></Phase></Engine></Description>
<Description type="Sound" subType="Standard" ID="SL35" Name="Shield_of_Light"><Engine><Category value="0"/><Phase ID="Begin"><Wave value="SL35"/><Group value="Spell_Group"/></Phase></Engine></Description>
<Description type="Sound" subType="Standard" ID="BT01" Name="FervisTemple"><Engine><Category value="0"/><Phase ID="Select"><Wave value="BT01"/><DistanceModifier value="10000.0"/></Phase><Phase ID="GetHit"><Wave value="HG36"/></Phase></Engine></Description>
<Description type="Sound" subType="Standard" ID="SL06" Name="Lightning_Storm"><Engine><Category value="0"/><Phase ID="Effector Begin"><Wave value="SL06"/><Group value="Guild_Spell_Group"/></Phase></Engine></Description>
<Description type="Sound" subType="Standard" ID="CT01" Name="Cultist"><Engine><Category value="0"/><Phase ID="VFX_GO_COMBAT"><Wave value="CTGT"/></Phase><Phase ID="VFX_FLEE_COMBAT"><Wave value="CTFT"/></Phase><Phase ID="VFX_DECIDING"><Wave value="CTDO"/></Phase><Phase ID="VFX_GO_REWARD"><Wave value="CTDG"/></Phase><Phase ID="VFX_FIND_COOL"><Wave value="CTFL"/></Phase><Phase ID="VFX_SPECIAL1"><Wave value="CTSS"/></Phase><Phase ID="Death"><Wave value="CTDH"/></Phase><Phase ID="VFX_GAIN_LEVEL"><Wave value="CTGL"/></Phase><Phase ID="VFX_SEE_HOSTILE"><Wave value="CTSE"/></Phase><Phase ID="Easter_Egg"><Wave value="CTE1"/></Phase><Phase ID="VFX_LEVEL_10"><Wave value="CTTL"/></Phase><Phase ID="Attack"><Wave value="WU04"/><Group value="Attack_Group"/></Phase></Engine></Description>
<Description type="Sound" subType="Standard" ID="RM01" Name="Rage_of_Krolm"><Engine><Category value="0"/><Phase ID="Begin"><Wave value="RM01"/><DistanceModifier value="10000.0"/></Phase></Engine></Description>
</Majesty>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "M_Sounds.xml"
            path.write_text(stock, encoding="utf-8")
            output = ET.fromstring(builder.build_brewing_sounds_xml(path))
        sound = output.find(
            f'./Description[@Name="{builder.ALCHEMIST_VIGOR_SOUND}"]'
        )
        self.assertEqual(
            sound.get("ID"), builder.ALCHEMIST_VIGOR_SOUND_ID.decode("ascii")
        )
        self.assertEqual(sound.get("Name"), builder.ALCHEMIST_VIGOR_SOUND)
        self.assertEqual(
            sound.find('./Engine/Phase[@ID="Effector Begin"]/Wave').get("value"),
            "DP01",
        )
        bottle = output.find(
            f'./Description[@Name="{builder.ALCHEMIST_BOTTLE_BREAK_SOUND}"]'
        )
        self.assertEqual(
            bottle.find('./Engine/Phase[@ID="Begin"]/Wave').get("value"), "AXBK"
        )
        self.assertEqual(
            bottle.find('./Engine/Phase[@ID="Begin"]/Group').get("value"),
            "Spell_Group",
        )
        laboratory = output.find(
            f'./Description[@Name="{builder.ALCHEMIST_LAB_SOUND}"]'
        )
        self.assertEqual(
            laboratory.find('./Engine/Phase[@ID="Select"]/Wave').get("value"),
            "AXLB",
        )
        self.assertEqual(
            laboratory.find('./Engine/Phase[@ID="GetHit"]/Wave').get("value"),
            "HG36",
        )
        hero = output.find(f'./Description[@Name="{builder.ALCHEMIST_HERO_SOUND}"]')
        self.assertEqual(
            hero.find('./Engine/Phase[@ID="Attack"]/Wave').get("value"), "WU03"
        )
        self.assertEqual(
            hero.find('./Engine/Phase[@ID="VFX_GO_COMBAT"]/Wave').get("value"),
            "AHC1",
        )
        self.assertIsNone(hero.find('./Engine/Phase[@ID="VFX_CAST_SPELL1"]'))
        cast = output.find(
            f'./Description[@Name="{builder.ALCHEMIST_CAST_VOICE_SOUND}"]'
        )
        self.assertEqual(
            cast.find('./Engine/Phase[@ID="Begin"]/Wave').get("value"), "AHC2"
        )
        self.assertEqual(
            cast.find('./Engine/Phase[@ID="Begin"]/Group').get("value"),
            "Hero_Cast_Voice_Group",
        )
        hired = output.find(
            f'./Description[@Name="{builder.ALCHEMIST_HIRED_VOICE_SOUND}"]'
        )
        self.assertEqual(
            hired.find('./Engine/Phase[@ID="Begin"]/Wave').get("value"), "AHS1"
        )

    def test_private_audio_cam_packages_only_approved_pcm_waves(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "alchemist_audio.cam"
            builder.write_alchemist_audio_cam(repo / "assets" / "audio", output)
            entries = builder.read_cam_entries(output, b"WAVE")
        self.assertEqual(
            [entry.name.rstrip(b"\x00")[:4] for entry in entries],
            [
                builder.ALCHEMIST_BOTTLE_BREAK_WAVE_ID,
                builder.ALCHEMIST_LAB_WAVE_ID,
                *(wave_id for wave_id, _event, _description in builder.ALCHEMIST_VOICE_WAVES),
            ],
        )
        for entry in entries:
            builder.validate_game_wave(entry.data, entry.name.decode("ascii"))

    def test_private_sounddesc_cam_clones_stock_phase_contracts(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\sounddesc.cam"
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "alchemist_sounddesc.cam"
            builder.write_alchemist_sounddesc_cam(stock, output)
            entries = builder.read_cam_entries(output, b"DSND")
        by_name = {entry.name.rstrip(b"\x00"): entry.data for entry in entries}
        expected_names = {
            builder.ALCHEMIST_VIGOR_SOUND_ID
            + builder.ALCHEMIST_VIGOR_SOUND.encode("ascii"),
            builder.ALCHEMIST_BOTTLE_BREAK_SOUND_ID
            + builder.ALCHEMIST_BOTTLE_BREAK_SOUND.encode("ascii"),
            builder.ALCHEMIST_LAB_SOUND_ID
            + builder.ALCHEMIST_LAB_SOUND.encode("ascii"),
            builder.ALCHEMIST_HERO_SOUND_ID
            + builder.ALCHEMIST_HERO_SOUND.encode("ascii"),
            builder.ALCHEMIST_CAST_VOICE_SOUND_ID
            + builder.ALCHEMIST_CAST_VOICE_SOUND.encode("ascii"),
            builder.ALCHEMIST_HIRED_VOICE_SOUND_ID
            + builder.ALCHEMIST_HIRED_VOICE_SOUND.encode("ascii"),
        }
        self.assertEqual(set(by_name), expected_names)
        bottle = by_name[
            builder.ALCHEMIST_BOTTLE_BREAK_SOUND_ID
            + builder.ALCHEMIST_BOTTLE_BREAK_SOUND.encode("ascii")
        ]
        laboratory = by_name[
            builder.ALCHEMIST_LAB_SOUND_ID
            + builder.ALCHEMIST_LAB_SOUND.encode("ascii")
        ]
        hero = by_name[
            builder.ALCHEMIST_HERO_SOUND_ID
            + builder.ALCHEMIST_HERO_SOUND.encode("ascii")
        ]
        cast = by_name[
            builder.ALCHEMIST_CAST_VOICE_SOUND_ID
            + builder.ALCHEMIST_CAST_VOICE_SOUND.encode("ascii")
        ]
        hired = by_name[
            builder.ALCHEMIST_HIRED_VOICE_SOUND_ID
            + builder.ALCHEMIST_HIRED_VOICE_SOUND.encode("ascii")
        ]
        self.assertEqual(bottle.count(builder.ALCHEMIST_BOTTLE_BREAK_WAVE_ID), 1)
        self.assertEqual(laboratory.count(builder.ALCHEMIST_LAB_WAVE_ID), 1)
        self.assertEqual(hero.count(b"WU03"), 1)
        self.assertNotIn(b"SL35", bottle)
        self.assertNotIn(b"BT01", laboratory)
        self.assertNotIn(b"WU04", hero)
        self.assertIn(b"HG36", laboratory)
        for _phase, source_wave, private_wave in builder.ALCHEMIST_HERO_VOICE_PHASES:
            self.assertNotIn(source_wave, hero)
            self.assertEqual(hero.count(private_wave), 1)
        self.assertNotIn(b"AHC2", hero)
        self.assertEqual(cast.count(b"AHC2"), 1)
        self.assertEqual(hired.count(b"AHS1"), 1)
        self.assertIn(b"SG21", cast)
        self.assertIn(b"SG14", hired)

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

    def test_reagent_count_clones_stock_healing_potion_count_control(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\textdata.cam"
        )
        brewing = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_BREWING_DIALOG_ID
        ).data
        rage = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_RAGE_DIALOG_ID
        ).data
        items = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_ITEMS_DIALOG_ID
        ).data
        brewing = builder.add_reagent_label_control(brewing, brewing)
        output = builder.add_reagent_count_control(brewing, items)
        label_marker = output.index(
            struct.pack("<I", builder.BREWING_REAGENT_METER_LABEL_CONTROL_ID)
        )
        label_record = label_marker - builder.AP69_TITLE_CONTROL_ID_OFFSET
        self.assertEqual(struct.unpack_from("<I", output, label_record)[0], 5)
        self.assertEqual(
            struct.unpack_from("<4I", output, label_record + 0x08),
            builder.REAGENT_LABEL_RECT,
        )
        self.assertEqual(
            output[
                label_record + builder.AP69_TITLE_FONT_OFFSET :
                label_record + builder.AP69_TITLE_FONT_OFFSET + 4
            ],
            b"fnt4",
        )
        marker = output.index(
            struct.pack("<I", builder.BREWING_REAGENT_COUNT_CONTROL_ID)
        )
        record = marker - builder.AP22_HEALING_COUNT_CONTROL_ID_OFFSET
        self.assertEqual(struct.unpack_from("<I", output, record)[0], 5)
        self.assertEqual(
            struct.unpack_from("<4I", output, record + 0x08),
            builder.REAGENT_COUNT_RECT,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I",
                output,
                record + builder.AP22_HEALING_COUNT_TEXT_INDEX_OFFSET,
            )[0],
            39,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I",
                output,
                record + builder.AP22_HEALING_COUNT_TOOLTIP_INDEX_OFFSET,
            )[0],
            40,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I",
                output,
                record + builder.AP22_HEALING_COUNT_BINDING_ID_OFFSET,
            )[0],
            builder.BREWING_REAGENT_COUNT_BINDING_ID,
        )
        self.assertEqual(output[record + 0x3C : record + 0x40], b"ALTI")
        self.assertEqual(output[-8:], b"\xff" * 8)

    def test_cgal_clones_stock_visitors_control_for_layout(self) -> None:
        stock = Path(
            r"C:\Program Files (x86)\Steam\steamapps\common\Majesty HD\Data\textdata.cam"
        )
        laboratory = builder.privateize_cgal_menu(
            builder.read_cam_entry(stock, b"SMNU", builder.SOURCE_DIALOG_ID).data
        )
        blacksmith = builder.read_cam_entry(
            stock, b"SMNU", builder.SOURCE_VISITORS_DIALOG_ID
        ).data
        output = builder.add_stock_visitors_control(laboratory, blacksmith)
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
