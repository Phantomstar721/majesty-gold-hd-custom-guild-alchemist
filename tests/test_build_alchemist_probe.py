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
        self.assertIn("(member_basicscript cultist_tree)", data)
        self.assertNotIn("fervus_Birth", data)

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
            'data="Alchemist_Building_Data.dat"\nsource="Alchemist_Brewing.gpl"\n',
        )
        self.assertIn(
            'source="Alchemist_Siege_Test.gpl"', builder.build_gpl_project(True)
        )

    def test_brewing_source_uses_a_guarded_realm_wide_speed_tier(self) -> None:
        source = (builder.GPL_SOURCE_ROOT / "Alchemist_Brewing.gpl").read_text(
            encoding="utf-8"
        )
        self.assertIn('ThisAgent\'s "Title" == "AlchemistsLaboratory"', source)
        self.assertIn('"hero"', source)
        self.assertIn('"monster"', source)
        self.assertIn("#ATTRIB_MovementRateModifier, -200", source)
        self.assertIn("#ATTRIB_MovementRateModifier, 200", source)
        self.assertIn("30000", source)

    def test_brewing_overlay_has_a_private_callback(self) -> None:
        stock = """<Majesty><Description type="Unit" subType="Overlay" ID="XR01" Name="Speed_Tonic_Icon" Description="Speed Tonic"><Engine><ImageIDBase value="XR01"/><Script type="0" cProc="0" GPLFunction="Speed_Tonic_End"/></Engine><Game/></Description></Majesty>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "MX_Overlays.xml"
            path.write_text(stock, encoding="utf-8")
            output = ET.fromstring(builder.build_brewing_overlays_xml(path))
        overlay = output.find("Description")
        self.assertEqual(overlay.get("ID"), "AXE1")
        self.assertEqual(overlay.get("Name"), "alchemist_invigorating_elixer_icon")
        self.assertEqual(
            overlay.find("./Engine/Script").get("GPLFunction"),
            "Alchemist_Invigorating_Elixer_End",
        )


if __name__ == "__main__":
    unittest.main()
