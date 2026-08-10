from pathlib import Path
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import build_alchemist_probe as builder


class AlchemistProbeTests(unittest.TestCase):
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

    def test_building_data_registers_every_xml_name(self) -> None:
        data = (builder.GPL_SOURCE_ROOT / "Alchemist_Building_Data.dat").read_text(
            encoding="utf-8"
        )
        for name in builder.BUILDING_NAMES:
            self.assertIn(f"[{name}]", data)
        self.assertIn("(birthscript basic_birth)", data)
        self.assertIn("(birthScript2 Guild_Birth)", data)
        self.assertIn("(member_basicscript Alchemist_tree)", data)
        self.assertEqual(data.count("(member_title Alchemist)"), 3)
        self.assertNotIn("fervus_Birth", data)

    def test_alchemist_hero_uses_private_stock_rogue_behavior(self) -> None:
        data = (builder.GPL_SOURCE_ROOT / "Alchemist_Hero_Data.dat").read_text(
            encoding="utf-8"
        )
        self.assertIn("[Alchemist]", data)
        self.assertIn("(title Alchemist)", data)
        self.assertEqual(data.count("Alchemist_tree"), 3)
        self.assertIn("(attack_action \t\tCultist_Dagger)", data)
        self.assertIn("(special_attack_action  Fire_Dagger)", data)
        self.assertIn("(Greed 26)", data)
        self.assertIn("(Upgrade_Armor_Chance\t100)", data)
        self.assertIn("(Upgrade_Weapon_Chance\t100)", data)
        self.assertIn("(evaluationScript\teval_enemies_nearby)", data)

    def test_private_rogue_tree_preserves_stock_greed_lifecycle(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Rogue.gpl").read_text(
            encoding="utf-8"
        )
        expected = (
            "$Check_rewards",
            "$Purchase_equipment",
            "$Loot_Gravestones(ThisAgent,100)",
            "$Steal_Check(thisagent,95)",
            '$Collect_Resource(thisagent,"poison_plants",90)',
            "$Go_home(thisagent,95)",
        )
        positions = [source.index(token) for token in expected]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("Cultist_tree", source)

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
        self.assertIn('"AlchemistsLaboratory1"', fixture)
        self.assertEqual(fixture.count('"MaxHP"'), 2)
        self.assertNotIn("function NEXT", fixture)

    def test_siege_fixture_is_an_explicit_project_source(self) -> None:
        self.assertEqual(
            builder.build_gpl_project(False),
            'data="Alchemist_Building_Data.dat"\n'
            'data="Alchemist_Hero_Data.dat"\n'
            'source="Alchemist_Rogue.gpl"\n'
            'source="Alchemist_Brewing.gpl"\n',
        )
        self.assertIn(
            'source="Alchemist_Siege_Test.gpl"', builder.build_gpl_project(True)
        )

    def test_brewing_source_copies_stock_rage_for_true_heroes(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Brewing.gpl").read_text(
            encoding="utf-8"
        )
        self.assertIn('$HasAttribute("Alchemist_Brewing", ThisAgent)', source)
        self.assertIn('ThisAgent\'s "Alchemist_Brewing" == True', source)
        self.assertIn("function Alchemist_Invigorating_Elixer_End(agent ThisAgent)", source)
        self.assertIn("$IsDead(Hero) == False", source)
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
        self.assertIn('$AdjustPlayerData(Palace, "Gold", -1)', source)
        self.assertIn("#ATTRIB_MaxHP, 20", source)
        self.assertIn("#ATTRIB_HP, 20", source)
        self.assertIn('Hero\'s "Self_Estimation" += 1', source)
        self.assertIn("$turnonSPeedTrail(Hero, 4)", source)
        self.assertIn("#ATTRIB_RageOfKrolmCount, HeroCount", source)
        self.assertIn("function DoRageOfKrolm", source)
        self.assertIn("function Alchemist_DoInvigoratingElixer", source)
        self.assertIn("$Alchemist_Stock_RageOfKrolm(ThisAgent)", source)
        self.assertLess(
            source.index(
                '$CreateEffector(Hero, "alchemist_invigorating_elixer_icon", 30000)'
            ),
            source.index("$AdjustAttribute(Hero, #ATTRIB_MaxHP, 20)"),
        )

    def test_brewing_overlay_has_a_private_callback(self) -> None:
        stock = """<Majesty><Description type="Unit" subType="Overlay" ID="QRa1" Name="Rage_icon" Description="Rage of Krolm"><Engine><Info value="Directionless"/><Info value="DontBlock"/><ImageIDBase value="QRa1"/><Script type="0" cProc="0" GPLFunction="rage_end"/></Engine><Game><StackPriority value="1"/></Game></Description></Majesty>"""
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
        brewing = bytearray(builder.AP69_FIRST_BREW_RECT_OFFSET + 0x10)
        struct.pack_into("<I", brewing, 0x28, 12)
        struct.pack_into(
            "<4I",
            brewing,
            builder.AP69_FIRST_BREW_RECT_OFFSET,
            *builder.AP69_FIRST_BREW_RECT,
        )
        rage = bytearray(builder.RAGE_PROGRESS_RECORD_OFFSET)
        record = bytearray(builder.RAGE_ACTIVE_DISPLAY_ID_OFFSET + 4)
        record[0x2C:0x30] = b"INSr"
        struct.pack_into("<I", record, 0x54, builder.RAGE_PROGRESS_CONTROL_ID)
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
        rage += record
        output = builder.add_native_rage_progress_control(bytes(brewing), bytes(rage))
        self.assertEqual(struct.unpack_from("<I", output, 0x28)[0], 12)
        self.assertEqual(output.count(b"INSr"), 1)
        self.assertIn(
            struct.pack("<I", builder.RAGE_ACTIVE_DISPLAY_CONTROL_ID), output
        )
        self.assertEqual(
            struct.unpack_from(
                "<4I", output, len(brewing) + builder.RAGE_PROGRESS_RECT_OFFSET
            ),
            builder.BREWING_PROGRESS_RECT,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I", output, len(brewing) + builder.RAGE_PROGRESS_PREFIX_OFFSET
            )[0],
            builder.RAGE_PROGRESS_PREFIX,
        )

    def test_brewing_action_uses_a_private_control_id(self) -> None:
        menu = bytearray(builder.BREWING_FIRST_BUTTON_ID_OFFSET + 4)
        struct.pack_into(
            "<I",
            menu,
            builder.BREWING_FIRST_BUTTON_ID_OFFSET,
            builder.STOCK_FERVUS_FIRST_SPELL_CONTROL_ID,
        )
        output = builder.privateize_brewing_action_control(bytes(menu))
        self.assertEqual(
            struct.unpack_from(
                "<I", output, builder.BREWING_FIRST_BUTTON_ID_OFFSET
            )[0],
            builder.BREWING_INVIGORATING_CONTROL_ID,
        )

    def test_panel_uses_stock_length_display_labels(self) -> None:
        source = Path(builder.__file__).read_text(encoding="utf-8")
        self.assertIn('0: "ALCHEMY LAB"', source)
        self.assertIn('1: "Vigor Elixir"', source)
        self.assertIn('29: "Brewing"', source)
        self.assertIn('13: "Brewing"', source)
        self.assertNotIn('29: "BREWING"', source)
        self.assertEqual(source.count('fourcc_id("ALB1"): "Alchemy Lab"'), 1)
        self.assertEqual(source.count('fourcc_id("ALB2"): "Alchemy Lab"'), 1)
        self.assertEqual(source.count('fourcc_id("ALB3"): "Alchemy Lab"'), 1)
        self.assertNotIn('0: "ALCHEMIST\'S LABORATORY"', source)


if __name__ == "__main__":
    unittest.main()
