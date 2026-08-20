from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

from alchemist_art_package import write_interfacedata, write_maindata
from approved_sprite_bundle import sha256_file


MAGIC = b"CYLBPC  \x01\x00\x01\x00"
HEADER_SIZE = 20
DIR_ENTRY_SIZE = 8
SECTION_HEADER_SIZE = 8
ENTRY_HEADER_SIZE = 28

MOD_ID = "{42ba4603-2b13-446d-a2a4-6cf3a55ddac3}"
DIALOG_ID = b"CGAL"
SOURCE_DIALOG_ID = b"AP10"
BREWING_DIALOG_ID = b"CGBR"
SOURCE_BREWING_DIALOG_ID = b"AP69"
SOURCE_RAGE_DIALOG_ID = b"AP24"
SOURCE_RESEARCH_DIALOG_ID = b"APa1"
SOURCE_MARKET_RESEARCH_DIALOG_ID = b"APa3"
SOURCE_VISITORS_DIALOG_ID = b"AP02"
RAGE_PROGRESS_RECORD_OFFSET = 0x0C28
RAGE_PROGRESS_INNER_OFFSET = 0x40
RAGE_PROGRESS_OUTER_RECT_OFFSET = 0x08
RAGE_PROGRESS_OUTER_RECT = (7, 219, 140, 21)
RAGE_PROGRESS_CONTROL_ID = 0x2009
RAGE_ACTIVE_DISPLAY_CONTROL_ID = 0x227A
RAGE_ACTIVE_DISPLAY_ID_OFFSET = RAGE_PROGRESS_INNER_OFFSET + 0x90
RAGE_ACTIVE_DISPLAY_LABEL_OPCODE_OFFSET = 0x94
RAGE_ACTIVE_DISPLAY_LABEL_INDEX_OFFSET = 0x98
RAGE_PROGRESS_PREFIX_OFFSET = RAGE_PROGRESS_INNER_OFFSET + 0x40
RAGE_PROGRESS_PREFIX = 2
RAGE_PROGRESS_RECT_OFFSET = RAGE_PROGRESS_INNER_OFFSET + 0x44
RAGE_PROGRESS_RECT = (8, 222, 138, 15)
AP69_FIRST_BREW_RECT_OFFSET = 0x0240
AP69_FIRST_BREW_RECT = (150, 63, 40, 17)
AP69_FIRST_BREW_OUTER_RECT_OFFSET = 0x0184
AP69_FIRST_BREW_OUTER_RECT = (30, 62, 162, 20)
AP69_FIRST_BREW_ICON_RECT_OFFSET = 0x0128
AP69_FIRST_BREW_ICON_RECT = (3, 60, 25, 25)
AP69_TERMINAL_RECORD_OFFSET = 0x06D8
AP69_TERMINAL_INNER_OFFSET = 0x28
AP69_TERMINAL_RECORD_HEADER = struct.pack(
    "<11I4s", 0, 2, 3, 0xDF, 0x19, 0x14, 0x21, 0x0C, 0x0A, 2, 12, b"INTG"
)
VIGOR_ROW_OUTER_RECT = (30, 114, 162, 20)
VIGOR_ROW_PRICE_RECT = (151, 117, 40, 17)
VIGOR_ROW_ICON_RECT = (3, 113, 25, 25)
BREWING_PROGRESS_RECT = (31, 117, 160, 14)
BREWING_PROGRESS_OUTER_RECT = VIGOR_ROW_OUTER_RECT
STOCK_FERVUS_FIRST_SPELL_CONTROL_ID = 0x1140
BREWING_INVIGORATING_CONTROL_ID = 0x2A10
BREWING_INVIGORATING_ICON_CONTROL_ID = BREWING_INVIGORATING_CONTROL_ID + 1000
BREWING_INVIGORATING_PRICE_CONTROL_ID = BREWING_INVIGORATING_CONTROL_ID - 1000
BREWING_FIRST_BUTTON_ID_OFFSET = 0x0204
BREWING_FIRST_ICON_ID_OFFSET = 0x0174
BREWING_FIRST_PRICE_ID_OFFSET = 0x02A4
AP69_SECOND_RECIPE_RECORD_START = 0x0478
AP69_SECOND_RECIPE_RECORD_END = 0x0620
APA1_ARROWS_RECORD_START = 0x0120
APA1_ARROWS_RECORD_END = 0x0218
APA1_ARROWS_ICON_RECORD_START = 0x0480
APA1_ARROWS_ICON_RECORD_END = 0x04CC
APA1_ARROWS_PRICE_RECORD_START = 0x0518
APA1_ARROWS_PRICE_RECORD_END = 0x05B0
RESEARCH_ROW_OUTER_Y_OFFSET = 0x000C
RESEARCH_ROW_OUTER_X_OFFSET = 0x0008
RESEARCH_ROW_OUTER_WIDTH_OFFSET = 0x0010
RESEARCH_ROW_LABEL_INDEX_OFFSET = 0x0030
RESEARCH_ROW_TOOLTIP_INDEX_OFFSET = 0x0038
RESEARCH_ROW_CONTROL_ID_OFFSET = 0x0088
STOCK_ARROWS_RESEARCH_CONTROL_ID = 0x139C
BREWING_WEAPON_OIL_CONTROL_ID = 0x2A13
BREWING_WEAPON_OIL_PROGRESS_CONTROL_ID = 0x2A11
BREWING_WEAPON_OIL_ACTIVE_DISPLAY_CONTROL_ID = 0x2A12
BREWING_WEAPON_OIL_ICON_CONTROL_ID = BREWING_WEAPON_OIL_CONTROL_ID + 500
BREWING_WEAPON_OIL_PRICE_CONTROL_ID = BREWING_WEAPON_OIL_CONTROL_ID + 1000
BREWING_PHOENIX_PHIAL_CONTROL_ID = 0x2A16
BREWING_PHOENIX_PHIAL_PROGRESS_CONTROL_ID = 0x2A17
BREWING_PHOENIX_PHIAL_ACTIVE_DISPLAY_CONTROL_ID = 0x2A18
BREWING_PHOENIX_PHIAL_ICON_CONTROL_ID = BREWING_PHOENIX_PHIAL_CONTROL_ID + 500
BREWING_PHOENIX_PHIAL_PRICE_CONTROL_ID = BREWING_PHOENIX_PHIAL_CONTROL_ID + 1000
ALCHEMY_OIL_INTENT_INDEX = 177
ALCHEMY_OIL_INTENT_TEXT = "Applying weapon oil at the alchemy lab"
PHOENIX_PHIAL_INTENT_INDEX = 178
PHOENIX_PHIAL_INTENT_TEXT = "Purchasing a Phoenix Phial at the alchemy lab"
WEAPON_OIL_PROGRESS_OUTER_RECT = (30, 62, 162, 20)
WEAPON_OIL_PROGRESS_LABEL_RECT = (31, 65, 160, 14)
PHOENIX_PHIAL_PROGRESS_OUTER_RECT = (30, 87, 162, 20)
PHOENIX_PHIAL_PROGRESS_LABEL_RECT = (31, 90, 160, 14)
WEAPON_OIL_PRICE_RECT = (151, 63, 40, 17)
PHOENIX_PHIAL_PRICE_RECT = (151, 90, 40, 17)
AP10_SPELL_BUTTON_RECT_OFFSET = 0x0D34
AP10_SPELL_BUTTON_RECT = (103, 162, 93, 26)
BREWING_FINAL_RECT = (7, 217, 93, 26)
AP10_TERMINAL_MARKER_OFFSET = 0x0DF0
AP02_VISITORS_RECORD_START = 0x013C
AP02_VISITORS_RECORD_END = 0x01D4
VISITORS_CONTROL_ID = 0x1F55
VISITORS_FINAL_RECT = AP10_SPELL_BUTTON_RECT
BUILDING_IDS = ("ALB1", "ALB2", "ALB3")
ALCHEMIST_HERO_ID = "ALC1"
ALCHEMIST_HERO_NAME = "Alchemist"
BUILDING_NAMES = (
    "AlchemistsLaboratory1",
    "AlchemistsLaboratory2",
    "AlchemistsLaboratory3",
)
SOURCE_BUILDING_NAMES = ("Temple_Fervus1", "Temple_Fervus2", "Temple_Fervus3")
ALCHEMIST_BDEP_RULE = b"ALB1 : ABJ2 ABJ3 NOT NOT ||"
PHANTOM_BDEP_RULE = b"PHG1 : ABJ2 ABJ3 NOT NOT ||"
SOURCE_ROOT = Path(__file__).resolve().parent
GPL_SOURCE_ROOT = SOURCE_ROOT / "gpl"
APPROVED_SPRITE_PIPELINE_ROOT = (
    SOURCE_ROOT.parents[1] / "majesty-gold-hd-sprite-art-pipeline"
)
APPROVED_SPRITE_PROVENANCE_NAME = "ApprovedSpriteTestSet.json"


def require_approved_sprite_output_root(output_root: Path) -> Path:
    approved_dist = (SOURCE_ROOT.parent / "dist").resolve()
    regular_probe = (approved_dist / "CustomGuildAlchemistProbe").resolve()
    resolved = output_root.resolve()
    if resolved == approved_dist:
        raise ValueError("Approved sprite output must be a child of the repository dist directory")
    if resolved == regular_probe:
        raise ValueError("Approved sprite output may not replace the regular probe build")
    try:
        resolved.relative_to(approved_dist)
    except ValueError as exc:
        raise ValueError(
            f"Approved sprite output must stay inside {approved_dist}: {resolved}"
        ) from exc
    return resolved


def extract_gpl_function(source: str, function_name: str) -> str:
    match = re.search(
        rf"(?im)^function\s+{re.escape(function_name)}\s*\(", source
    )
    if match is None:
        raise ValueError(f"Stock GPL function not found: {function_name}")
    next_function = re.search(r"(?im)^function\s+", source[match.end() :])
    end = len(source) if next_function is None else match.end() + next_function.start()
    return source[match.start() : end].rstrip()


def build_siege_test_fixture(stock_quests: Path) -> str:
    source = stock_quests.read_text(encoding="cp1252")
    function = extract_gpl_function(source, "SIEGE")
    declare_anchor = "\tagent palace, enemypalace;"
    if function.count(declare_anchor) != 1:
        raise ValueError("The Siege agent declarations no longer match the SDK fixture")
    function = function.replace(
        declare_anchor,
        "\tagent palace, enemypalace, alchemyLab, oilRogue, oilWarrior, oilAlchemist;",
        1,
    )
    anchor = '\tpalace = $GetPlayerOnePalace ();'
    if function.count(anchor) != 1:
        raise ValueError("The Siege Palace initialization no longer matches the SDK fixture")
    spawns = (
        anchor
        + '\n\t$AdjustPlayerData ( palace, "gold", 100000 );'
        + '\n\t$SpawnUnit ( palace, "Wizards_Guild3", '
        '$RandomCoord ( palace, 400, 525 ), "MaxHP" );'
        + '\n\t$SpawnUnit ( palace, "Temple_Fervus1", '
        '$RandomCoord ( palace, 550, 750 ), "MaxHP" );'
        + '\n\t$SpawnUnit ( palace, "Temple_Krolm", '
        '$RandomCoord ( palace, 700, 900 ), "MaxHP" );'
        + '\n\talchemyLab = $SpawnUnit ( palace, "AlchemistsLaboratory1", '
        '$RandomCoord ( palace, 850, 1050 ), "MaxHP" );'
        + '\n\toilRogue = $SpawnUnit ( palace, "Rogue", '
        '$RandomCoord ( alchemyLab, 100, 150 ) );'
        + '\n\toilWarrior = $SpawnUnit ( palace, "Warrior", '
        '$RandomCoord ( alchemyLab, 150, 200 ) );'
        + '\n\toilAlchemist = $SpawnUnit ( palace, "Alchemist", '
        '$RandomCoord ( alchemyLab, 200, 250 ) );'
    )
    setup = ""
    for buyer in ("oilRogue", "oilWarrior", "oilAlchemist"):
        setup += (
            f'\n\t$Advance_To_Level ( {buyer}, 10 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Experience, 0 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Gold, 5000 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Intelligence, 100 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Weapon_Struct_Bonus, 3 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Armor_Struct_Bonus, 3 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Weapon_Magic_Bonus, 3 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Armor_Magic_Bonus, 3 );'
            f'\n\t$SetThreadInterval ( {buyer}\'s "ActiveScript", 1000 );'
            f'\n\t{buyer}\'s "ActiveScript" = $Alchemist_Oil_Test_Buyer;'
        )
    fixture = function.replace(anchor, spawns + setup, 1)
    return (
        fixture
        + "\n\n"
        + "Function Alchemist_Oil_Test_Buyer (agent ThisAgent)\n"
        + "Declare\n\n"
        + "Begin\n"
        + "\t$Purchase_Equipment (ThisAgent);\n"
        + "End\n"
    )


def build_alchemist_economy(stock_purchase_equipment: Path) -> str:
    """Generate the stock-cloned Laboratory oil-purchase gate."""
    source = stock_purchase_equipment.read_text(encoding="cp1252")
    function = extract_gpl_function(source, "Purchase_Equipment")
    boolean_anchor = "\tboolean \tFlag,Wants_Armor,Wants_Weapon,Wants_Poison;"
    if function.count(boolean_anchor) != 1:
        raise ValueError("Stock Purchase_Equipment boolean declaration changed")
    function = function.replace(
        boolean_anchor,
        "\tboolean \tFlag,Wants_Armor,Wants_Weapon,Wants_Poison,Wants_Oil;",
        1,
    )
    weapon_gate_anchor = (
        "\tIf ($GetAttribute (ThisAgent, #ATTRIB_WeaponTypeIndex) > 0)"
        "\n\t\tbegin"
        "\n\t\t\tIf (ThisAgent's \"Upgrade_Weapon_Chance\" > $RandomNumber (100) + 1)"
        "\n\t\t\t\tWants_Weapon = TRUE;"
        "\n\t\tend"
    )
    if function.count(weapon_gate_anchor) != 1:
        raise ValueError("Stock Purchase_Equipment weapon gate changed")
    oil_classification = (
        weapon_gate_anchor
        + "\n\t// Weapon Oil is for every ordinary weapon-upgrading combatant."
        + "\n\t// Upgrade_Weapon_Chance is a stock hero-class capability marker here,"
        + "\n\t// not a second random purchase roll."
        + "\n\tIf (($GetAttribute (ThisAgent, #ATTRIB_WeaponTypeIndex) > 0) &&"
        + "\n\t\t(ThisAgent's \"Upgrade_Weapon_Chance\" > 0))"
        + "\n\t\tWants_Oil = TRUE;"
    )
    function = function.replace(weapon_gate_anchor, oil_classification, 1)
    list_anchor = "\tlist blacksmiths,wizguilds,markets,shops,fairgrounds,buildings;"
    if function.count(list_anchor) != 1:
        raise ValueError("Stock Purchase_Equipment list declaration changed")
    function = function.replace(
        list_anchor,
        "\tlist blacksmiths,wizguilds,markets,shops,fairgrounds,buildings,alchemyLabs,phoenixLabs;",
        1,
    )
    wizard_anchor = '\twizGuilds = $listTitles(buildings,"Wizards_Guild");'
    if function.count(wizard_anchor) != 1:
        raise ValueError("Stock Purchase_Equipment Wizard list construction changed")
    gate = (
        wizard_anchor
        + '\n\talchemyLabs = $listTitles(buildings,"AlchemistsLaboratory");'
        + '\n\tphoenixLabs = $List_Attribs(alchemyLabs,#ATTRIB_ResearchPowerfulItem);'
        + "\n\talchemyLabs = $List_Attribs(alchemyLabs,#ATTRIB_ResearchArrows);"
    )
    function = function.replace(wizard_anchor, gate, 1)

    poison_anchor = (
        "\t\t\t\t\t\tIf (Wants_Poison && $Poison_Check (ThisAgent))"
        "\n\t\t\t\t\t\t\tbegin"
        "\n\t\t\t\t\t\t\t\tFlag = TRUE;"
        "\n\t\t\t\t\t\t\tend"
    )
    if function.count(poison_anchor) != 1:
        raise ValueError("Stock Purchase_Equipment poison branch changed")
    oil_then_poison = (
        "\t\t\t\t\t\tIf (Wants_Oil && $Alchemy_Oil_Check (ThisAgent,alchemyLabs))"
        "\n\t\t\t\t\t\t\tbegin"
        "\n\t\t\t\t\t\t\t\tFlag = TRUE;"
        "\n\t\t\t\t\t\t\tend"
        "\n\t\t\t\t\t\tElse"
        "\n" + poison_anchor
    )
    function = function.replace(poison_anchor, oil_then_poison, 1)
    market_anchor = (
        "\t\t\t\t\t\t\t\t\tIf ($Market3_Check (ThisAgent,markets))"
        "\n\t\t\t\t\t\t\t\t\t\tbegin"
        "\n\t\t\t\t\t\t\t\t\t\t\tFlag = TRUE;"
        "\n\t\t\t\t\t\t\t\t\t\tend"
    )
    if function.count(market_anchor) != 1:
        raise ValueError("Stock Purchase_Equipment Market3 branch changed")
    phoenix_after_market = (
        market_anchor
        + "\n\t\t\t\t\t\t\t\t\tElse"
        + "\n\t\t\t\t\t\t\t\t\t\tIf ($Phoenix_Phial_Check (ThisAgent,phoenixLabs))"
        + "\n\t\t\t\t\t\t\t\t\t\t\tbegin"
        + "\n\t\t\t\t\t\t\t\t\t\t\t\tFlag = TRUE;"
        + "\n\t\t\t\t\t\t\t\t\t\t\tend"
    )
    return function.replace(market_anchor, phoenix_after_market, 1) + "\n"


def build_gpl_project(include_siege_test_fixture: bool) -> str:
    sources = [
        'source="Alchemist_Rogue.gpl"',
        'source="Alchemist_Brewing.gpl"',
        'source="Alchemist_Economy.gpl"',
        'source="Alchemist_Weapon_Oil.gpl"',
        'source="Alchemist_Phoenix_Phial.gpl"',
    ]
    if include_siege_test_fixture:
        sources.append('source="Alchemist_Siege_Test.gpl"')
    return (
        'data="Alchemist_Building_Data.dat"\n'
        'data="Alchemist_Hero_Data.dat"\n'
        'data="Alchemist_Phoenix_Phial.dat"\n'
        + "\n".join(sources)
        + "\n"
    )


@dataclass(frozen=True)
class CamEntry:
    name: bytes
    data: bytes


@dataclass(frozen=True)
class CamSection:
    extension: bytes
    entries: tuple[CamEntry, ...]
    padding: bytes = b"\x00\x00\x00\x00"


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def pad_name(name: bytes) -> bytes:
    if len(name) > 20:
        raise ValueError(f"CAM entry name is too long: {name!r}")
    return name.ljust(20, b"\x00")


def fourcc_id(value: str) -> int:
    raw = value.encode("ascii")
    if len(raw) != 4:
        raise ValueError(f"Expected a FourCC, got {value!r}")
    return struct.unpack("<I", raw)[0]


def read_cam_entries(path: Path, extension: bytes) -> list[CamEntry]:
    data = path.read_bytes()
    if data[: len(MAGIC)] != MAGIC:
        raise ValueError(f"Not a CYLBPC CAM archive: {path}")
    section_count = u32(data, 12)
    cursor = HEADER_SIZE
    directory: list[tuple[bytes, int]] = []
    for _ in range(section_count):
        directory.append((data[cursor : cursor + 4], u32(data, cursor + 4)))
        cursor += DIR_ENTRY_SIZE
    for section_extension, section_offset in directory:
        if section_extension != extension:
            continue
        count = u32(data, section_offset)
        cursor = section_offset + SECTION_HEADER_SIZE
        entries: list[CamEntry] = []
        for _ in range(count):
            raw_name = data[cursor : cursor + 20]
            payload_offset = u32(data, cursor + 20)
            payload_size = u32(data, cursor + 24)
            cursor += ENTRY_HEADER_SIZE
            entries.append(
                CamEntry(raw_name, data[payload_offset : payload_offset + payload_size])
            )
        return entries
    raise ValueError(f"Could not find {extension.decode()} section in {path}")


def read_cam_entry(path: Path, extension: bytes, name: bytes) -> CamEntry:
    for entry in read_cam_entries(path, extension):
        if entry.name.rstrip(b"\x00") == name:
            return entry
    raise ValueError(f"Could not find {extension.decode()}/{name.decode()} in {path}")


def write_cam(path: Path, sections: tuple[CamSection, ...]) -> None:
    section_count = len(sections)
    file_header_size = HEADER_SIZE + section_count * DIR_ENTRY_SIZE
    content_header_size = sum(
        SECTION_HEADER_SIZE + len(section.entries) * ENTRY_HEADER_SIZE
        for section in sections
    )
    cursor = file_header_size + content_header_size
    payload_offsets: list[list[int]] = []
    for section in sections:
        offsets: list[int] = []
        for entry in section.entries:
            offsets.append(cursor)
            cursor += len(entry.data)
        payload_offsets.append(offsets)

    output = bytearray(MAGIC)
    output += struct.pack("<II", section_count, content_header_size)
    section_offset = file_header_size
    for section in sections:
        output += section.extension + struct.pack("<I", section_offset)
        section_offset += SECTION_HEADER_SIZE + len(section.entries) * ENTRY_HEADER_SIZE
    for section_index, section in enumerate(sections):
        output += struct.pack("<I", len(section.entries)) + section.padding
        for entry_index, entry in enumerate(section.entries):
            output += entry.name
            output += struct.pack(
                "<II", payload_offsets[section_index][entry_index], len(entry.data)
            )
    for section in sections:
        for entry in section.entries:
            output += entry.data
    path.write_bytes(output)


def patch_strt_by_id(data: bytes, replacements: dict[int, str]) -> bytes:
    count = struct.unpack_from("<H", data, 0)[0]
    version = data[2:4]
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    records: list[tuple[int, bytes]] = []
    seen: set[int] = set()
    for offset in offsets:
        string_id = u32(data, offset)
        end = data.index(b"\x00", offset + 4)
        text = data[offset + 4 : end]
        if string_id in replacements:
            text = replacements[string_id].encode("cp1252")
            seen.add(string_id)
        records.append((string_id, text))
    for string_id, text in replacements.items():
        if string_id not in seen:
            records.append((string_id, text.encode("cp1252")))
    return encode_strt(version, records)


def patch_strt_by_index(data: bytes, replacements: dict[int, str]) -> bytes:
    count = struct.unpack_from("<H", data, 0)[0]
    version = data[2:4]
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    records: list[tuple[int, bytes]] = []
    target_count = max(count, max(replacements, default=-1) + 1)
    for index in range(target_count):
        if index < count:
            offset = offsets[index]
            string_id = u32(data, offset)
            end = data.index(b"\x00", offset + 4)
            stock_text = data[offset + 4 : end].decode("cp1252")
        else:
            # SMNU text properties address STRT records positionally. Preserve
            # that stock contract by padding missing AP69 slots with matching
            # numeric IDs before adding AP24's active-display index 28.
            string_id = index
            stock_text = ""
        text = replacements.get(index, stock_text)
        records.append((string_id, text.encode("cp1252")))
    return encode_strt(version, records)


def encode_strt(version: bytes, records: list[tuple[int, bytes]]) -> bytes:
    output = bytearray(struct.pack("<H", len(records)) + version)
    output += b"\x00\x00\x00\x00" * len(records)
    offsets: list[int] = []
    for string_id, text in records:
        offsets.append(len(output))
        output += struct.pack("<I", string_id) + text + b"\x00"
    for index, offset in enumerate(offsets):
        struct.pack_into("<I", output, 4 + index * 4, offset)
    return bytes(output)


def build_units_xml(stock_buildings_xml: Path, stock_characters_xml: Path) -> bytes:
    stock_root = ET.parse(stock_buildings_xml).getroot()
    output = ET.Element("Majesty")
    character_root = ET.parse(stock_characters_xml).getroot()
    stock_cultist = character_root.find('.//Description[@Name="Cultist"]')
    if stock_cultist is None:
        raise ValueError("Stock Cultist character description is missing")
    alchemist = ET.fromstring(ET.tostring(stock_cultist, encoding="utf-8"))
    alchemist.set("ID", ALCHEMIST_HERO_ID)
    alchemist.set("Name", ALCHEMIST_HERO_NAME)
    alchemist.set("Description", ALCHEMIST_HERO_NAME)
    alchemist.find("./Engine/ImageIDBase").set("value", ALCHEMIST_HERO_ID)
    movement = alchemist.find('./Engine/Attachment[@kind="Movement"]')
    if movement is None:
        raise ValueError("Stock Cultist movement attachment is missing")
    # The private IMAG is a literal Warrior animation/timing clone, so retain
    # Warrior's matching stock movement class rather than Cultist Class 3.
    movement.set("ID", "Class 1")
    output.append(alchemist)
    for level, source_name in enumerate(SOURCE_BUILDING_NAMES):
        source = stock_root.find(f'.//Description[@Name="{source_name}"]')
        if source is None:
            raise ValueError(f"Stock building description is missing: {source_name}")
        description = ET.fromstring(ET.tostring(source, encoding="utf-8"))
        description.set("ID", BUILDING_IDS[level])
        description.set("Name", BUILDING_NAMES[level])
        description.set(
            "Description",
            "Alchemy Lab" if level == 0 else f"Alchemy Lab Level {level + 1}",
        )
        description.find("./Engine/ImageIDBase").set("value", BUILDING_IDS[level])
        dialog = description.find("./Game/DialogID")
        if dialog is None:
            raise ValueError(f"{source_name} has no DialogID")
        dialog.set("value", DIALOG_ID.decode("ascii"))
        upgrade_to = description.find("./Game/UpgradeTo")
        upgrade_from = description.find("./Game/UpgradeFrom")
        if upgrade_to is not None:
            upgrade_to.set("value", BUILDING_NAMES[level + 1])
        if upgrade_from is not None:
            upgrade_from.set("value", BUILDING_NAMES[level - 1])
        # Preserve the complete stock Cultist contract under a private identity.
        produced = description.find("./Game/Produces/Unit")
        if produced is None:
            raise ValueError(f"{source_name} has no recruitable unit")
        produced.set("ID", ALCHEMIST_HERO_NAME)
        output.append(description)
    # SDK SpecialItemsExample contract: a named inventory item is a normal
    # character description carrying IsInventoryItem and its own inventory
    # attribute. It is never spawned on the map in this prototype.
    phoenix = ET.SubElement(
        output,
        "Description",
        {
            "type": "Unit",
            "subType": "Character",
            "ID": "PXF1",
            "Name": "PhoenixPhial",
            "Description": "Phoenix Phial",
        },
    )
    engine = ET.SubElement(phoenix, "Engine", {"version": "1"})
    ET.SubElement(engine, "Info", {"value": "Static"})
    ET.SubElement(engine, "Info", {"value": "Directionless"})
    ET.SubElement(engine, "CanUse", {"value": "HumanPlayer"})
    ET.SubElement(engine, "Menu", {"value": "11"})
    ET.SubElement(engine, "ImageIDBase", {"value": "PXF1"})
    ET.SubElement(engine, "DefaultSound", {"value": "0"})
    game = ET.SubElement(phoenix, "Game", {"version": "1"})
    ET.SubElement(game, "DialogID", {"value": "0"})
    ET.SubElement(game, "MaxHP", {"value": "10"})
    ET.SubElement(game, "Flags", {"value": "NotFlaggable"})
    ET.SubElement(game, "Flags", {"value": "NotSpellTarget"})
    ET.SubElement(game, "Flags", {"value": "IsInventoryItem"})
    attributes = ET.SubElement(game, "Attributes")
    ET.SubElement(attributes, "Attribute", {"ID": "CanDropItem", "Value": "0"})
    ET.SubElement(attributes, "Attribute", {"ID": "PhoenixPhial", "Value": "0"})
    ET.indent(output, space="\t")
    return ET.tostring(output, encoding="utf-8", xml_declaration=False) + b"\n"


def build_brewing_overlays_xml(stock_overlays_xml: Path) -> bytes:
    stock_root = ET.parse(stock_overlays_xml).getroot()
    source = stock_root.find('.//Description[@Name="Rage_icon"]')
    if source is None:
        raise ValueError("Stock Rage_icon overlay is missing")
    overlay = ET.fromstring(ET.tostring(source, encoding="utf-8"))
    overlay.set("ID", "AXE1")
    overlay.set("Name", "alchemist_invigorating_elixer_icon")
    overlay.set("Description", "Invigorating Elixer")
    image = overlay.find("./Engine/ImageIDBase")
    script = overlay.find("./Engine/Script")
    if image is None or script is None:
        raise ValueError("Stock Rage_icon overlay contract changed")
    image.set("value", "XR01")
    script.set("GPLFunction", "Alchemist_Invigorating_Elixer_End")
    output = ET.Element("Majesty")
    output.append(overlay)
    resurrection_source = stock_root.find(
        './/Description[@Name="resurrection_effector"]'
    )
    if resurrection_source is None:
        raise ValueError("Stock resurrection_effector overlay is missing")
    resurrection = ET.fromstring(
        ET.tostring(resurrection_source, encoding="utf-8")
    )
    resurrection.set("ID", "PXE1")
    resurrection.set("Name", "phoenix_phial_resurrection_effector")
    resurrection.set("Description", "Phoenix Phial Resurrection")
    resurrection_script = resurrection.find("./Engine/Script")
    if resurrection_script is None:
        raise ValueError("Stock resurrection effector callback is missing")
    resurrection_script.set("GPLFunction", "Phoenix_Phial_Resurrection_End")
    output.append(resurrection)
    ET.indent(output, space="\t")
    return ET.tostring(output, encoding="utf-8", xml_declaration=False) + b"\n"


def build_brewing_sounds_xml(stock_sounds_xml: Path) -> bytes:
    stock_root = ET.parse(stock_sounds_xml).getroot()
    source = stock_root.find('.//Description[@Name="Drink_Potion"]')
    if source is None:
        raise ValueError("Stock Drink_Potion sound is missing")
    sound = ET.fromstring(ET.tostring(source, encoding="utf-8"))
    sound.set("ID", "AXS1")
    sound.set("Name", "alchemist_invigorating_elixer_sound")
    phase = sound.find('./Engine/Phase[@ID="Effector Begin"]')
    if phase is None or phase.find("./Wave") is None:
        raise ValueError("Stock Drink_Potion sound contract changed")
    output = ET.Element("Majesty")
    output.append(sound)
    ET.indent(output, space="\t")
    return ET.tostring(output, encoding="utf-8", xml_declaration=False) + b"\n"


def add_native_rage_progress_control(brewing_menu: bytes, rage_menu: bytes) -> bytes:
    """Insert AP24's complete Rage display before AP69's terminal control."""
    if brewing_menu.count(b"INSr") != 0:
        raise ValueError("CGBR already contains an INSr progress control")
    if struct.unpack_from("<4I", brewing_menu, AP69_FIRST_BREW_RECT_OFFSET) != AP69_FIRST_BREW_RECT:
        raise ValueError("Stock AP69 first-recipe rectangle changed")
    if struct.unpack_from(
        "<4I", brewing_menu, AP69_FIRST_BREW_OUTER_RECT_OFFSET
    ) != AP69_FIRST_BREW_OUTER_RECT:
        raise ValueError("Stock AP69 first-recipe outer rectangle changed")
    if struct.unpack_from(
        "<4I", brewing_menu, AP69_FIRST_BREW_ICON_RECT_OFFSET
    ) != AP69_FIRST_BREW_ICON_RECT:
        raise ValueError("Stock AP69 first-recipe icon rectangle changed")
    if (
        brewing_menu[
            AP69_TERMINAL_RECORD_OFFSET :
            AP69_TERMINAL_RECORD_OFFSET + len(AP69_TERMINAL_RECORD_HEADER)
        ]
        != AP69_TERMINAL_RECORD_HEADER
    ):
        raise ValueError("Stock AP69 terminal-control layout changed")
    if u32(rage_menu, RAGE_PROGRESS_RECORD_OFFSET) != 9:
        raise ValueError("Stock AP24 progress-control subtype changed")
    if struct.unpack_from(
        "<4I",
        rage_menu,
        RAGE_PROGRESS_RECORD_OFFSET + RAGE_PROGRESS_OUTER_RECT_OFFSET,
    ) != RAGE_PROGRESS_OUTER_RECT:
        raise ValueError("Stock AP24 progress-control outer rectangle changed")
    inner_offset = RAGE_PROGRESS_RECORD_OFFSET + RAGE_PROGRESS_INNER_OFFSET
    if rage_menu[inner_offset : inner_offset + 8] != struct.pack("<I4s", 12, b"INSr"):
        raise ValueError("Stock AP24 progress-control layout changed")
    output = bytearray(brewing_menu)
    struct.pack_into("<4I", output, AP69_FIRST_BREW_RECT_OFFSET, *VIGOR_ROW_PRICE_RECT)
    struct.pack_into("<4I", output, AP69_FIRST_BREW_OUTER_RECT_OFFSET, *VIGOR_ROW_OUTER_RECT)
    struct.pack_into("<4I", output, AP69_FIRST_BREW_ICON_RECT_OFFSET, *VIGOR_ROW_ICON_RECT)
    brewing_menu = bytes(output)
    progress_record = bytearray(rage_menu[RAGE_PROGRESS_RECORD_OFFSET:])
    if progress_record[-8:] != b"\xff" * 8:
        raise ValueError("Stock AP24 progress stream terminator changed")
    if struct.pack("<I", RAGE_PROGRESS_CONTROL_ID) not in progress_record:
        raise ValueError("Stock AP24 progress control ID is missing")
    if u32(progress_record, RAGE_ACTIVE_DISPLAY_ID_OFFSET) != RAGE_ACTIVE_DISPLAY_CONTROL_ID:
        raise ValueError("Stock AP24 active-display child changed")
    if u32(progress_record, RAGE_PROGRESS_PREFIX_OFFSET) != RAGE_PROGRESS_PREFIX:
        raise ValueError("Stock AP24 progress-control prefix changed")
    if struct.unpack_from("<4I", progress_record, RAGE_PROGRESS_RECT_OFFSET) != RAGE_PROGRESS_RECT:
        raise ValueError("Stock AP24 progress-control rectangle changed")
    # Preserve AP24's complete INSr/0x227A active display. Only move its Y
    # coordinates from AP24's primary-panel row to AP69's first recipe row.
    struct.pack_into(
        "<4I",
        progress_record,
        RAGE_PROGRESS_OUTER_RECT_OFFSET,
        *BREWING_PROGRESS_OUTER_RECT,
    )
    struct.pack_into(
        "<4I", progress_record, RAGE_PROGRESS_RECT_OFFSET, *BREWING_PROGRESS_RECT
    )
    # AP69's final INTG is the menu's terminal/root ornament control. Keep it
    # last, as stock AP69 does. AP31 demonstrates that INSr is a normal member
    # of the streamed control sequence and may be followed by later controls.
    # AP24 owns the end of its own dialog and therefore ends this record with
    # both a record terminator and an end-of-stream terminator. CGBR still has
    # AP69's stock title and terminal controls after this insertion, so retain
    # the record terminator and let AP69 continue to own the stream terminator.
    # Keeping both AP24 words here makes Majesty stop before it constructs the
    # stock GUILD SPELLS/Brewing title control.
    progress_record = progress_record[:-4]
    return bytes(
        brewing_menu[:AP69_TERMINAL_RECORD_OFFSET]
        + progress_record
        + brewing_menu[AP69_TERMINAL_RECORD_OFFSET:]
    )


def privateize_brewing_action_control(brewing_menu: bytes) -> bytes:
    """Privatize AP69's complete first-row control family for Vigor."""
    output = bytearray(brewing_menu)
    actual_action = u32(output, BREWING_FIRST_BUTTON_ID_OFFSET)
    actual_icon = u32(output, BREWING_FIRST_ICON_ID_OFFSET)
    actual_price = u32(output, BREWING_FIRST_PRICE_ID_OFFSET)
    if actual_action != STOCK_FERVUS_FIRST_SPELL_CONTROL_ID:
        raise ValueError(
            f"Stock AP69 first spell control changed: 0x{actual_action:04X}"
        )
    if actual_icon != STOCK_FERVUS_FIRST_SPELL_CONTROL_ID + 1000:
        raise ValueError(
            f"Stock AP69 first spell icon changed: 0x{actual_icon:04X}"
        )
    if actual_price != STOCK_FERVUS_FIRST_SPELL_CONTROL_ID - 1000:
        raise ValueError(
            f"Stock AP69 first spell price changed: 0x{actual_price:04X}"
        )
    # AP69's stock row presenter derives the two children directly from the
    # action ID: price = action - 1000 and icon = action + 1000. Move exactly
    # those three controls together so no Fervus/Vines identity remains.
    struct.pack_into(
        "<I", output, BREWING_FIRST_BUTTON_ID_OFFSET,
        BREWING_INVIGORATING_CONTROL_ID,
    )
    struct.pack_into(
        "<I", output, BREWING_FIRST_ICON_ID_OFFSET,
        BREWING_INVIGORATING_ICON_CONTROL_ID,
    )
    struct.pack_into(
        "<I", output, BREWING_FIRST_PRICE_ID_OFFSET,
        BREWING_INVIGORATING_PRICE_CONTROL_ID,
    )
    return bytes(output)


def disable_ap10_secondary_control(data: bytes) -> bytes:
    output = bytearray(data)
    actual = struct.unpack_from("<4I", output, AP10_SPELL_BUTTON_RECT_OFFSET)
    if actual != AP10_SPELL_BUTTON_RECT:
        raise ValueError(
            f"Stock AP10 secondary-control layout changed: expected "
            f"{AP10_SPELL_BUTTON_RECT}, found {actual}"
        )
    struct.pack_into("<2I", output, AP10_SPELL_BUTTON_RECT_OFFSET + 8, 0, 0)
    return bytes(output)


def add_stock_weapon_oil_research_control(
    brewing_menu: bytes, research_menu: bytes
) -> bytes:
    """Replace AP69's second visual recipe with APa1's native Arrows row.

    This preserves the Guardhouse research control's complete streamed-control
    shape. Only its private-dialog position and CGBR string indices change.
    The executable continues to own cost, timing, progress, completion, and
    disabled-state rendering through the stock ResearchArrows descriptor.
    """
    source = bytearray(
        research_menu[APA1_ARROWS_RECORD_START:APA1_ARROWS_RECORD_END]
    )
    if len(source) != 0xF8:
        raise ValueError("Stock APa1 Arrows research row size changed")
    if u32(source, RESEARCH_ROW_CONTROL_ID_OFFSET) != STOCK_ARROWS_RESEARCH_CONTROL_ID:
        raise ValueError("Stock APa1 Arrows research control ID changed")
    if u32(source, RESEARCH_ROW_LABEL_INDEX_OFFSET) != 1:
        raise ValueError("Stock APa1 Arrows label index changed")
    if u32(source, RESEARCH_ROW_TOOLTIP_INDEX_OFFSET) != 2:
        raise ValueError("Stock APa1 Arrows tooltip index changed")
    if u32(source, RESEARCH_ROW_OUTER_Y_OFFSET) != 61:
        raise ValueError("Stock APa1 Arrows row position changed")
    if (
        u32(source, RESEARCH_ROW_OUTER_X_OFFSET) != 26
        or u32(source, RESEARCH_ROW_OUTER_WIDTH_OFFSET) != 172
    ):
        raise ValueError("Stock APa1 Arrows row width changed")
    if u32(brewing_menu, AP69_SECOND_RECIPE_RECORD_START - 4) != 0xFFFFFFFF:
        raise ValueError("Stock AP69 preceding recipe terminator changed")
    if u32(brewing_menu, AP69_SECOND_RECIPE_RECORD_END) != 0:
        raise ValueError("Stock AP69 following recipe boundary changed")
    if len(brewing_menu[AP69_SECOND_RECIPE_RECORD_START:AP69_SECOND_RECIPE_RECORD_END]) != 0x1A8:
        raise ValueError("Stock AP69 second recipe record size changed")
    # CGBR indices 7 and 8 are the private second-row label and tooltip.
    struct.pack_into("<I", source, RESEARCH_ROW_OUTER_X_OFFSET, 30)
    struct.pack_into("<I", source, RESEARCH_ROW_OUTER_Y_OFFSET, 62)
    struct.pack_into("<I", source, RESEARCH_ROW_OUTER_WIDTH_OFFSET, 162)
    # Preserve APa1's complete compound-control record but privatize its
    # command key. The runtime resolves 0x2A13 to a byte-for-byte clone of the
    # stock 0x139C descriptor, so Guardhouse Arrows retains its own identity.
    struct.pack_into(
        "<I",
        source,
        RESEARCH_ROW_CONTROL_ID_OFFSET,
        BREWING_WEAPON_OIL_CONTROL_ID,
    )
    struct.pack_into("<I", source, RESEARCH_ROW_LABEL_INDEX_OFFSET, 7)
    struct.pack_into("<I", source, RESEARCH_ROW_TOOLTIP_INDEX_OFFSET, 8)
    if source.count(b"INBb") != 1:
        raise ValueError("Stock APa1 Arrows row background reference changed")
    source = source.replace(b"INBb", b"ALBB")
    result = bytes(
        brewing_menu[:AP69_SECOND_RECIPE_RECORD_START]
        + source
        + brewing_menu[AP69_SECOND_RECIPE_RECORD_END:]
    )
    new_end = AP69_SECOND_RECIPE_RECORD_START + len(source)
    if (
        u32(result, AP69_SECOND_RECIPE_RECORD_START - 4) != 0xFFFFFFFF
        or u32(result, AP69_SECOND_RECIPE_RECORD_START) != 0
        or u32(result, new_end - 4) != 0xFFFFFFFF
        or u32(result, new_end) != 0
    ):
        raise ValueError("CGBR Weapon Oil splice broke SMNU record boundaries")
    return result


def add_stock_phoenix_phial_research_control(
    brewing_menu: bytes, research_menu: bytes
) -> bytes:
    """Clone Weapon Oil's exact APa1 compound row for Phoenix research."""
    source = bytearray(
        research_menu[APA1_ARROWS_RECORD_START:APA1_ARROWS_RECORD_END]
    )
    if len(source) != 0xF8 or source[-4:] != b"\xff" * 4:
        raise ValueError("Stock APa1 Arrows row boundary changed")
    if u32(source, RESEARCH_ROW_CONTROL_ID_OFFSET) != STOCK_ARROWS_RESEARCH_CONTROL_ID:
        raise ValueError("Stock APa1 Arrows control ID changed")
    if (
        u32(source, RESEARCH_ROW_LABEL_INDEX_OFFSET) != 1
        or u32(source, RESEARCH_ROW_TOOLTIP_INDEX_OFFSET) != 2
    ):
        raise ValueError("Stock APa1 Arrows string contract changed")
    if u32(brewing_menu, 0x320) != 0xFFFFFFFF or u32(brewing_menu, 0x324) != 0:
        raise ValueError("Stock AP69 remaining recipe boundary changed")
    struct.pack_into("<I", source, RESEARCH_ROW_OUTER_X_OFFSET, 30)
    struct.pack_into("<I", source, RESEARCH_ROW_OUTER_Y_OFFSET, 87)
    struct.pack_into("<I", source, RESEARCH_ROW_OUTER_WIDTH_OFFSET, 162)
    struct.pack_into(
        "<I", source, RESEARCH_ROW_CONTROL_ID_OFFSET, BREWING_PHOENIX_PHIAL_CONTROL_ID
    )
    struct.pack_into("<I", source, RESEARCH_ROW_LABEL_INDEX_OFFSET, 4)
    struct.pack_into("<I", source, RESEARCH_ROW_TOOLTIP_INDEX_OFFSET, 5)
    if source.count(b"INBb") != 1:
        raise ValueError("Stock APa1 Arrows background changed")
    source = source.replace(b"INBb", b"ALBB", 1)
    result = bytes(brewing_menu[:0x324] + source + brewing_menu[0x478:])
    if u32(result, 0x320) != 0xFFFFFFFF or u32(result, 0x324) != 0:
        raise ValueError("CGBR Phoenix Phial splice broke its leading boundary")
    return result


def add_native_weapon_oil_progress_control(
    brewing_menu: bytes, rage_menu: bytes
) -> bytes:
    """Clone AP24's proven display pair for Weapon Oil's research row."""
    rage_art = brewing_menu.find(b"INSr")
    if rage_art < 0 or brewing_menu.find(b"INSr", rage_art + 1) >= 0:
        raise ValueError("CGBR Vigor display is missing or ambiguous")
    vigor_record = rage_art - 4 - RAGE_PROGRESS_INNER_OFFSET
    if vigor_record < 4 or u32(brewing_menu, vigor_record) != 9:
        raise ValueError("CGBR Vigor display boundary changed")
    if u32(brewing_menu, vigor_record - 4) != 0xFFFFFFFF:
        raise ValueError("CGBR pre-Vigor terminator changed")

    source = rage_menu[RAGE_PROGRESS_RECORD_OFFSET:]
    if len(source) != 0xEC or source[-8:] != b"\xff" * 8:
        raise ValueError("Stock AP24 terminal display layout changed")
    # The final word is AP24's end-of-stream marker. This private clone is
    # followed by CGBR's existing AP24 clone, so retain the label terminator
    # and let the final clone continue to own the stream terminator.
    display = bytearray(source[:-4])
    if u32(display, 0x6C) != RAGE_PROGRESS_CONTROL_ID:
        raise ValueError("Stock AP24 progress display ID changed")
    if u32(display, RAGE_ACTIVE_DISPLAY_ID_OFFSET) != RAGE_ACTIVE_DISPLAY_CONTROL_ID:
        raise ValueError("Stock AP24 active label ID changed")
    if (
        u32(display, RAGE_ACTIVE_DISPLAY_LABEL_OPCODE_OFFSET) != 7
        or u32(display, RAGE_ACTIVE_DISPLAY_LABEL_INDEX_OFFSET) != 28
    ):
        raise ValueError("Stock AP24 active label string contract changed")
    struct.pack_into("<4I", display, 0x08, *WEAPON_OIL_PROGRESS_OUTER_RECT)
    struct.pack_into(
        "<4I", display, RAGE_PROGRESS_RECT_OFFSET, *WEAPON_OIL_PROGRESS_LABEL_RECT
    )
    struct.pack_into(
        "<I", display, 0x6C, BREWING_WEAPON_OIL_PROGRESS_CONTROL_ID
    )
    struct.pack_into(
        "<I",
        display,
        RAGE_ACTIVE_DISPLAY_ID_OFFSET,
        BREWING_WEAPON_OIL_ACTIVE_DISPLAY_CONTROL_ID,
    )
    struct.pack_into("<I", display, RAGE_ACTIVE_DISPLAY_LABEL_INDEX_OFFSET, 29)
    return bytes(
        brewing_menu[:vigor_record] + display + brewing_menu[vigor_record:]
    )


def add_stock_weapon_oil_icon_control(
    brewing_menu: bytes, research_menu: bytes
) -> bytes:
    """Clone APa1's separate Arrows icon control beside Weapon Oil."""
    source = bytearray(
        research_menu[APA1_ARROWS_ICON_RECORD_START:APA1_ARROWS_ICON_RECORD_END]
    )
    if len(source) != 0x4C or source[-4:] != b"\xff" * 4:
        raise ValueError("Stock APa1 Arrows icon control boundary changed")
    if struct.unpack_from("<4I", source, 0x08) != (3, 60, 25, 25):
        raise ValueError("Stock APa1 Arrows icon rectangle changed")
    if source.count(b"INCr") != 1 or u32(source, 0x2C) != 1007:
        raise ValueError("Stock APa1 Arrows icon art contract changed")
    if u32(source, 0x3C) != 0x1590:
        raise ValueError("Stock APa1 Arrows icon control ID changed")
    struct.pack_into("<I", source, 0x0C, 60)
    source = source.replace(b"INCr", b"ALWI", 1)
    struct.pack_into("<I", source, 0x3C, BREWING_WEAPON_OIL_ICON_CONTROL_ID)

    rage_art = brewing_menu.find(b"INSr")
    if rage_art < 0 or brewing_menu.find(b"INSr", rage_art + 1) >= 0:
        raise ValueError("CGBR Vigor display is missing or ambiguous")
    vigor_record = rage_art - 4 - RAGE_PROGRESS_INNER_OFFSET
    if vigor_record < 4 or u32(brewing_menu, vigor_record - 4) != 0xFFFFFFFF:
        raise ValueError("CGBR pre-Vigor icon insertion boundary changed")
    return bytes(brewing_menu[:vigor_record] + source + brewing_menu[vigor_record:])


def add_stock_phoenix_phial_icon_control(
    brewing_menu: bytes, research_menu: bytes
) -> bytes:
    """Clone Weapon Oil's exact APa1 icon control for Phoenix Phial."""
    source = bytearray(
        research_menu[APA1_ARROWS_ICON_RECORD_START:APA1_ARROWS_ICON_RECORD_END]
    )
    if len(source) != 0x4C or source[-4:] != b"\xff" * 4:
        raise ValueError("Stock APa1 Arrows icon boundary changed")
    if struct.unpack_from("<4I", source, 0x08) != (3, 60, 25, 25):
        raise ValueError("Stock APa1 Arrows icon rectangle changed")
    if source.count(b"INCr") != 1 or u32(source, 0x3C) != 0x1590:
        raise ValueError("Stock APa1 Arrows icon contract changed")
    struct.pack_into("<I", source, 0x0C, 86)
    source = source.replace(b"INCr", b"ALPI", 1)
    struct.pack_into("<I", source, 0x3C, BREWING_PHOENIX_PHIAL_ICON_CONTROL_ID)
    vigor_id = struct.pack("<I", RAGE_PROGRESS_CONTROL_ID)
    vigor_record = brewing_menu.index(vigor_id) - 0x6C
    if vigor_record < 4 or u32(brewing_menu, vigor_record - 4) != 0xFFFFFFFF:
        raise ValueError("CGBR pre-Vigor Phoenix icon insertion boundary changed")
    return bytes(brewing_menu[:vigor_record] + source + brewing_menu[vigor_record:])


def add_stock_research_price_control(
    brewing_menu: bytes,
    research_menu: bytes,
    control_id: int,
    rectangle: tuple[int, int, int, int],
) -> bytes:
    """Clone APa1's separate gold-cost display beside a private research row."""
    source = bytearray(
        research_menu[APA1_ARROWS_PRICE_RECORD_START:APA1_ARROWS_PRICE_RECORD_END]
    )
    if len(source) != 0x98 or source[-4:] != b"\xff" * 4:
        raise ValueError("Stock APa1 Arrows price-control boundary changed")
    if struct.unpack_from("<4I", source, 0x08) != (154, 64, 40, 17):
        raise ValueError("Stock APa1 Arrows price rectangle changed")
    if u32(source, 0x1C) != 9 or u32(source, 0x6C) != 0x1784:
        raise ValueError("Stock APa1 Arrows price string/control contract changed")
    if source.count(b"INTI") != 1:
        raise ValueError("Stock APa1 Arrows price art contract changed")
    struct.pack_into("<4I", source, 0x08, *rectangle)
    struct.pack_into("<I", source, 0x6C, control_id)
    source = source.replace(b"INTI", b"ALTI", 1)

    vigor_id = struct.pack("<I", RAGE_PROGRESS_CONTROL_ID)
    vigor_record = brewing_menu.index(vigor_id) - 0x6C
    if vigor_record < 4 or u32(brewing_menu, vigor_record - 4) != 0xFFFFFFFF:
        raise ValueError("CGBR pre-Vigor research-price insertion boundary changed")
    return bytes(brewing_menu[:vigor_record] + source + brewing_menu[vigor_record:])


def add_native_phoenix_phial_progress_control(
    brewing_menu: bytes, rage_menu: bytes
) -> bytes:
    """Clone the proven AP24 display pair over the Phoenix research row."""
    source = rage_menu[RAGE_PROGRESS_RECORD_OFFSET:]
    if len(source) != 0xEC or source[-8:] != b"\xff" * 8:
        raise ValueError("Stock AP24 terminal display layout changed")
    display = bytearray(source[:-4])
    if (
        u32(display, 0x6C) != RAGE_PROGRESS_CONTROL_ID
        or u32(display, RAGE_ACTIVE_DISPLAY_ID_OFFSET) != RAGE_ACTIVE_DISPLAY_CONTROL_ID
    ):
        raise ValueError("Stock AP24 Phoenix display IDs changed")
    struct.pack_into("<4I", display, 0x08, *PHOENIX_PHIAL_PROGRESS_OUTER_RECT)
    struct.pack_into(
        "<4I", display, RAGE_PROGRESS_RECT_OFFSET, *PHOENIX_PHIAL_PROGRESS_LABEL_RECT
    )
    struct.pack_into("<I", display, 0x6C, BREWING_PHOENIX_PHIAL_PROGRESS_CONTROL_ID)
    struct.pack_into(
        "<I",
        display,
        RAGE_ACTIVE_DISPLAY_ID_OFFSET,
        BREWING_PHOENIX_PHIAL_ACTIVE_DISPLAY_CONTROL_ID,
    )
    struct.pack_into("<I", display, RAGE_ACTIVE_DISPLAY_LABEL_INDEX_OFFSET, 30)
    vigor_id = struct.pack("<I", RAGE_PROGRESS_CONTROL_ID)
    vigor_record = brewing_menu.index(vigor_id) - 0x6C
    if vigor_record < 4 or u32(brewing_menu, vigor_record - 4) != 0xFFFFFFFF:
        raise ValueError("CGBR pre-Vigor Phoenix progress boundary changed")
    return bytes(brewing_menu[:vigor_record] + display + brewing_menu[vigor_record:])


def add_stock_visitors_probe_control(
    laboratory_menu: bytes, blacksmith_menu: bytes
) -> bytes:
    """Clone AP02's Visitors button into AP10's former Brewing slot."""
    if laboratory_menu[AP10_TERMINAL_MARKER_OFFSET - 4 :] != b"\xff" * 8:
        raise ValueError("Stock AP10 terminal control boundary changed")
    source = bytearray(
        blacksmith_menu[AP02_VISITORS_RECORD_START:AP02_VISITORS_RECORD_END]
    )
    if len(source) != 0x98 or source[-4:] != b"\xff" * 4:
        raise ValueError("Stock AP02 Visitors control boundary changed")
    if struct.unpack_from("<4I", source, 0x08) != (32, 162, 139, 26):
        raise ValueError("Stock AP02 Visitors rectangle changed")
    if (
        u32(source, 0x18) != 7
        or u32(source, 0x1C) != 2
        or u32(source, 0x20) != 0x21
        or u32(source, 0x24) != 3
    ):
        raise ValueError("Stock AP02 Visitors string contract changed")
    if source.count(b"INBb") != 1 or u32(source, 0x64) != VISITORS_CONTROL_ID:
        raise ValueError("Stock AP02 Visitors command contract changed")
    struct.pack_into("<4I", source, 0x08, *VISITORS_FINAL_RECT)
    struct.pack_into("<I", source, 0x1C, 31)
    struct.pack_into("<I", source, 0x24, 32)
    source = source.replace(b"INBb", b"ALBB", 1)
    return bytes(
        laboratory_menu[:AP10_TERMINAL_MARKER_OFFSET]
        + source
        + laboratory_menu[AP10_TERMINAL_MARKER_OFFSET:]
    )


def move_brewing_control_below_recruit(laboratory_menu: bytes) -> bytes:
    """Move AP10's complete secondary-control parent below Recruit."""
    output = bytearray(laboratory_menu)
    actual = struct.unpack_from("<4I", output, AP10_SPELL_BUTTON_RECT_OFFSET)
    if actual != AP10_SPELL_BUTTON_RECT:
        raise ValueError(
            f"Stock AP10 Brewing rectangle changed: expected "
            f"{AP10_SPELL_BUTTON_RECT}, found {actual}"
        )
    struct.pack_into("<4I", output, AP10_SPELL_BUTTON_RECT_OFFSET, *BREWING_FINAL_RECT)
    return bytes(output)


def privateize_cgal_menu(menu: bytes) -> bytes:
    """Clone AP10's visual resources for CGAL without touching stock AP10."""
    if menu.count(b"AVC1") != 1:
        raise ValueError(
            "Stock AP10 Cultist member/count icon contract changed: expected one AVC1"
        )
    return (
        # AP10 embeds AVC1 for the Cultist guild member/count portrait.
        # Privatize that reference in the cloned CGAL resource exactly as the
        # proven Haunt panel does; never alter AP10 or the stock AVC1 IMAG.
        menu.replace(b"AVC1", b"ALC1")
        .replace(b"INTI", b"ALTI")
        .replace(b"INBb", b"ALBB")
        .replace(b"INBg", b"ALBG")
    )


def build_text_cam(
    stock_text_cam: Path,
    output_path: Path,
    enable_unsafe_brewing_control: bool = False,
) -> None:
    menu = read_cam_entry(stock_text_cam, b"SMNU", SOURCE_DIALOG_ID).data
    menu = privateize_cgal_menu(menu)
    if enable_unsafe_brewing_control:
        menu = move_brewing_control_below_recruit(menu)
    else:
        menu = disable_ap10_secondary_control(menu)
    visitors_source = read_cam_entry(
        stock_text_cam, b"SMNU", SOURCE_VISITORS_DIALOG_ID
    ).data
    menu = add_stock_visitors_probe_control(menu, visitors_source)
    strings = read_cam_entry(stock_text_cam, b"STRT", SOURCE_DIALOG_ID).data
    brewing_menu = read_cam_entry(
        stock_text_cam, b"SMNU", SOURCE_BREWING_DIALOG_ID
    ).data
    brewing_menu = (
        brewing_menu.replace(b"INTI", b"ALTI")
        .replace(b"INBb", b"ALBB")
        .replace(b"INBg", b"ALBG")
        .replace(b"INTN", b"ALIN")
    )
    brewing_menu = privateize_brewing_action_control(brewing_menu)
    rage_menu = read_cam_entry(stock_text_cam, b"SMNU", SOURCE_RAGE_DIALOG_ID).data
    brewing_menu = add_native_rage_progress_control(brewing_menu, rage_menu)
    research_menu = read_cam_entry(
        stock_text_cam, b"SMNU", SOURCE_RESEARCH_DIALOG_ID
    ).data
    brewing_menu = add_stock_weapon_oil_research_control(
        brewing_menu, research_menu
    )
    brewing_menu = add_stock_phoenix_phial_research_control(
        brewing_menu, research_menu
    )
    brewing_menu = add_stock_weapon_oil_icon_control(
        brewing_menu, research_menu
    )
    brewing_menu = add_stock_phoenix_phial_icon_control(
        brewing_menu, research_menu
    )
    brewing_menu = add_stock_research_price_control(
        brewing_menu,
        research_menu,
        BREWING_WEAPON_OIL_PRICE_CONTROL_ID,
        WEAPON_OIL_PRICE_RECT,
    )
    brewing_menu = add_stock_research_price_control(
        brewing_menu,
        research_menu,
        BREWING_PHOENIX_PHIAL_PRICE_CONTROL_ID,
        PHOENIX_PHIAL_PRICE_RECT,
    )
    brewing_menu = add_native_weapon_oil_progress_control(
        brewing_menu, rage_menu
    )
    brewing_menu = add_native_phoenix_phial_progress_control(
        brewing_menu, rage_menu
    )
    if brewing_menu.count(b"INSr") != 3:
        raise ValueError("CGBR must contain exactly three stock Rage progress-art references")
    brewing_menu = brewing_menu.replace(b"INSr", b"ALSR")
    brewing_strings = read_cam_entry(
        stock_text_cam, b"STRT", SOURCE_BREWING_DIALOG_ID
    ).data
    unit_names = read_cam_entry(stock_text_cam, b"STRT", b"UNTN").data
    patched_units = patch_strt_by_id(
        unit_names,
        {
            fourcc_id("ALB1"): "Alchemy Lab",
            fourcc_id("ALB2"): "Alchemy Lab",
            fourcc_id("ALB3"): "Alchemy Lab",
            fourcc_id(ALCHEMIST_HERO_ID): ALCHEMIST_HERO_NAME,
        },
    )
    patched_strings = patch_strt_by_index(
        strings,
        {
            0: "ALCHEMY LAB",
            1: "RECRUIT Alchemist",
            2: "Recruit an Alchemist.",
            3: "Destroy this Alchemist's Laboratory.",
            29: "Brewing",
            30: "Open this Laboratory's experimental Brewing window.",
            31: "VISITORS",
            32: "Go to this building's Visitors Window.",
        },
    )
    patched_brewing_strings = patch_strt_by_index(
        brewing_strings,
        {
            0: "ALCHEMY LAB",
            1: "Vigor Elixir",
            2: "Invigorate every unit for 30 seconds: faster movement, 20 bonus hit points, and greater confidence.",
            3: "1500",
            4: "Phoenix Phial",
            5: "Research Phoenix Phials for sale to heroes.",
            6: "",
            7: "Weapon Oil",
            8: "Research weapon oil for the Laboratory's stock enchanting service.",
            # APa1's presenter replaces this fallback with each descriptor's
            # live price (250 for Oil, 750 for Phoenix).
            9: "250",
            13: "Brewing",
            28: "Invigorated",
            29: "Researching Weapon Oil",
            30: "Researching Phoenix Phial",
        },
    )
    write_cam(
        output_path,
        (
            CamSection(
                b"SMNU",
                (
                    CamEntry(pad_name(DIALOG_ID), menu),
                    CamEntry(pad_name(BREWING_DIALOG_ID), brewing_menu),
                ),
            ),
            CamSection(
                b"STRT",
                (
                    CamEntry(pad_name(b"UNTN"), patched_units),
                    CamEntry(pad_name(DIALOG_ID), patched_strings),
                    CamEntry(pad_name(BREWING_DIALOG_ID), patched_brewing_strings),
                ),
            ),
        ),
    )


def build_gpl_text_cam(stock_gpl_text_cam: Path, output_path: Path) -> None:
    """Append private Alchemist intents while preserving every stock AITX record."""
    stock_intents = read_cam_entry(stock_gpl_text_cam, b"STRT", b"AITX").data
    stock_count = struct.unpack_from("<H", stock_intents, 0)[0]
    if stock_count != ALCHEMY_OIL_INTENT_INDEX:
        raise ValueError(
            f"Stock AITX count changed: expected {ALCHEMY_OIL_INTENT_INDEX}, got {stock_count}"
        )
    patched_intents = patch_strt_by_index(
        stock_intents,
        {
            ALCHEMY_OIL_INTENT_INDEX: ALCHEMY_OIL_INTENT_TEXT,
            PHOENIX_PHIAL_INTENT_INDEX: PHOENIX_PHIAL_INTENT_TEXT,
        },
    )
    write_cam(
        output_path,
        (CamSection(b"STRT", (CamEntry(pad_name(b"AITX"), patched_intents),)),),
    )


def append_bdep_rule(data: bytes, rule: bytes, comment: bytes) -> bytes:
    if rule in data:
        return data
    if not data.endswith(b"\r\n"):
        raise ValueError("Stock BDEP no longer ends in CRLF")
    return data + b"\r\n# " + comment + b"\r\n" + rule + b"\r\n"


def build_misc_cam(stock_misc_cam: Path, output_path: Path, include_phantoms: bool) -> None:
    bdep = read_cam_entry(stock_misc_cam, b"DATA", b"BDEP").data
    if include_phantoms:
        bdep = append_bdep_rule(bdep, PHANTOM_BDEP_RULE, b"Two-mod probe: Phantoms Haunt")
    bdep = append_bdep_rule(bdep, ALCHEMIST_BDEP_RULE, b"Alchemist probe requires Palace level 2")
    write_cam(
        output_path,
        (CamSection(b"DATA", (CamEntry(pad_name(b"BDEP"), bdep),)),),
    )


def build_manifest(
    use_ap10_title_alias: bool = False,
    include_siege_test_fixture: bool = False,
) -> str:
    probe_detail = (
        "Temporary fixture using stock Fervus and Cultist resources; its GPL title "
        "aliases Temple_Fervus to isolate the AP10 spell callback."
        if use_ap10_title_alias
        else "Temporary fixture using stock Fervus and Cultist resources."
    )
    siege_source = (
        "\n\t\t\t\t\t\t<Source>GPL\\Alchemist_Siege_Test.gpl</Source>"
        if include_siege_test_fixture
        else ""
    )
    return f'''<Majesty>
\t<Mod id="{MOD_ID}">
\t\t<Name>CustomGuildAlchemistProbe</Name>
\t\t<DisplayName lang="en_US">Custom Guild: Alchemist (CGAL Probe)</DisplayName>
\t\t<Description lang="en_US">
\t\t\t<Short>Tests a custom AP10-derived Alchemist guild and Brewing panel.</Short>
\t\t\t<Long>{probe_detail}</Long>
\t\t</Description>
\t\t<DataConfiguration>
\t\t\t<Dataset base="Any">
\t\t\t\t<Load>
\t\t\t\t\t<CAM>Data\\alchemist_probe_textdata.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_probe_gpltext.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_probe_miscdata.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_maindata.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_interfacedata.cam</CAM>
\t\t\t\t\t<Descriptions>Data\\alchemist_probe_units.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_brewing_overlays.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_brewing_sounds.xml</Descriptions>
\t\t\t\t\t<GPL>
\t\t\t\t\t\t<Target>Data\\Alchemist.bcd</Target>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Building_Data.dat</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Hero_Data.dat</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Phoenix_Phial.dat</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Rogue.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Brewing.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Economy.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Weapon_Oil.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Phoenix_Phial.gpl</Source>{siege_source}
\t\t\t\t\t</GPL>
\t\t\t\t</Load>
\t\t\t</Dataset>
\t\t</DataConfiguration>
\t</Mod>
</Majesty>
'''


def validate_output(
    output_root: Path,
    include_phantoms: bool,
    use_ap10_title_alias: bool = False,
    enable_unsafe_brewing_control: bool = False,
    include_siege_test_fixture: bool = False,
    approved_sprite_test_set: bool = False,
) -> None:
    expected = {
        output_root / "CustomGuildAlchemistProbe.mmxml",
        output_root / "Data" / "alchemist_probe_units.xml",
        output_root / "Data" / "alchemist_brewing_overlays.xml",
        output_root / "Data" / "alchemist_brewing_sounds.xml",
        output_root / "Data" / "alchemist_probe_textdata.cam",
        output_root / "Data" / "alchemist_probe_gpltext.cam",
        output_root / "Data" / "alchemist_probe_miscdata.cam",
        output_root / "Data" / "alchemist_maindata.cam",
        output_root / "Data" / "alchemist_interfacedata.cam",
        output_root / "Data" / "Alchemist.bcd",
        output_root / "GPL" / "Alchemist.gplproj",
        output_root / "GPL" / "Alchemist_Building_Data.dat",
        output_root / "GPL" / "Alchemist_Hero_Data.dat",
        output_root / "GPL" / "Alchemist_Phoenix_Phial.dat",
        output_root / "GPL" / "Alchemist_Rogue.gpl",
        output_root / "GPL" / "Alchemist_Brewing.gpl",
        output_root / "GPL" / "Alchemist_Economy.gpl",
        output_root / "GPL" / "Alchemist_Weapon_Oil.gpl",
        output_root / "GPL" / "Alchemist_Phoenix_Phial.gpl",
    }
    if include_siege_test_fixture:
        expected.add(output_root / "GPL" / "Alchemist_Siege_Test.gpl")
    if approved_sprite_test_set:
        expected.add(output_root / APPROVED_SPRITE_PROVENANCE_NAME)
    actual = {path for path in output_root.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError(f"Unexpected package files: {sorted(str(p) for p in actual ^ expected)}")
    if approved_sprite_test_set:
        provenance_path = output_root / APPROVED_SPRITE_PROVENANCE_NAME
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        if provenance.get("schema") != "majesty-alchemist-approved-sprite-test-set-v1":
            raise ValueError("Approved sprite test provenance schema changed")
        if provenance.get("cache_policy") != (
            "fresh build; regular art cache bypassed and not updated"
        ):
            raise ValueError("Approved sprite test did not bypass the regular art cache")
        packaged_main = output_root / "Data" / "alchemist_maindata.cam"
        if provenance.get("output", {}).get("maindata_cam_sha256") != sha256_file(
            packaged_main
        ):
            raise ValueError("Approved sprite test CAM hash does not match provenance")
        packaged_bcd = output_root / "Data" / "Alchemist.bcd"
        if provenance.get("output", {}).get("alchemist_bcd_sha256") != sha256_file(
            packaged_bcd
        ):
            raise ValueError("Approved sprite test BCD hash does not match provenance")
        expected_package_hashes = {
            path.relative_to(output_root).as_posix(): sha256_file(path)
            for path in sorted(output_root.rglob("*"))
            if path.is_file() and path != provenance_path
        }
        if provenance.get("output", {}).get("package_file_sha256") != expected_package_hashes:
            raise ValueError("Approved sprite test package-file hashes changed")
    root = ET.parse(output_root / "Data" / "alchemist_probe_units.xml").getroot()
    descriptions = root.findall("Description")
    if [item.get("ID") for item in descriptions] != [ALCHEMIST_HERO_ID, *BUILDING_IDS, "PXF1"]:
        raise ValueError("Alchemist unit ID sequence is invalid")
    hero = descriptions[0]
    buildings = descriptions[1:4]
    phoenix = descriptions[4]
    if hero.get("Name") != ALCHEMIST_HERO_NAME:
        raise ValueError("Private Alchemist hero description is missing")
    if hero.find("./Engine/ImageIDBase").get("value") != ALCHEMIST_HERO_ID:
        raise ValueError("Alchemist must use its private image record")
    if hero.find("./Engine/DefaultSound").get("value") != "Cultist":
        raise ValueError("Alchemist probe must retain the stock Cultist sound")
    movement = hero.find('./Engine/Attachment[@kind="Movement"]')
    if movement is None or movement.get("ID") != "Class 1":
        raise ValueError("Alchemist must use the stock Warrior movement class")
    if any(item.find("./Game/DialogID").get("value") != "CGAL" for item in buildings):
        raise ValueError("Every Laboratory level must use CGAL")
    if phoenix.get("Name") != "PhoenixPhial" or phoenix.find(
        './Game/Flags[@value="IsInventoryItem"]'
    ) is None:
        raise ValueError("Phoenix Phial inventory-item description is missing")
    if phoenix.find("./Engine/ImageIDBase").get("value") != "PXF1":
        raise ValueError("Phoenix Phial must use its private inventory-item art")
    if [item.find("./Engine/ImageIDBase").get("value") for item in buildings] != list(BUILDING_IDS):
        raise ValueError("Every Laboratory level must use its private image record")
    text_cam = output_root / "Data" / "alchemist_probe_textdata.cam"
    gpl_text_cam = output_root / "Data" / "alchemist_probe_gpltext.cam"
    intent_strings = read_cam_entry(gpl_text_cam, b"STRT", b"AITX").data
    intent_count = struct.unpack_from("<H", intent_strings, 0)[0]
    if intent_count != PHOENIX_PHIAL_INTENT_INDEX + 1:
        raise ValueError("Private AITX intents were not appended at the stock boundary")
    intent_offsets = struct.unpack_from(f"<{intent_count}I", intent_strings, 4)
    intent_offset = intent_offsets[ALCHEMY_OIL_INTENT_INDEX]
    intent_end = intent_strings.index(b"\x00", intent_offset + 4)
    if (
        intent_strings[intent_offset + 4 : intent_end].decode("cp1252")
        != ALCHEMY_OIL_INTENT_TEXT
    ):
        raise ValueError("Private Weapon Oil intent text is incorrect")
    phoenix_intent_offset = intent_offsets[PHOENIX_PHIAL_INTENT_INDEX]
    phoenix_intent_end = intent_strings.index(b"\x00", phoenix_intent_offset + 4)
    if (
        intent_strings[phoenix_intent_offset + 4 : phoenix_intent_end].decode("cp1252")
        != PHOENIX_PHIAL_INTENT_TEXT
    ):
        raise ValueError("Private Phoenix Phial intent text is incorrect")
    menu = read_cam_entry(text_cam, b"SMNU", DIALOG_ID).data
    if menu == b"":
        raise ValueError("CGAL menu is empty")
    if menu.count(struct.pack("<I", VISITORS_CONTROL_ID)) != 1:
        raise ValueError("CGAL stock Visitors control is missing or duplicated")
    visitor_marker = menu.index(struct.pack("<I", VISITORS_CONTROL_ID))
    visitor_record = visitor_marker - 0x64
    if struct.unpack_from("<4I", menu, visitor_record + 0x08) != VISITORS_FINAL_RECT:
        raise ValueError("CGAL Visitors final rectangle changed")
    brewing_rect = struct.unpack_from("<4I", menu, AP10_SPELL_BUTTON_RECT_OFFSET)
    expected_brewing_rect = (
        BREWING_FINAL_RECT
        if enable_unsafe_brewing_control
        else (103, 162, 0, 0)
    )
    if brewing_rect != expected_brewing_rect:
        raise ValueError(f"Unexpected CGAL Brewing rectangle: {brewing_rect}")
    brewing_menu = read_cam_entry(text_cam, b"SMNU", BREWING_DIALOG_ID).data
    if brewing_menu == b"":
        raise ValueError("CGBR menu is empty")
    for menu_name, menu_data in (("CGAL", menu), ("CGBR", brewing_menu)):
        if b"ALTI" not in menu_data or b"ALBB" not in menu_data or b"ALBG" not in menu_data:
            raise ValueError(f"{menu_name} does not use the private interface art")
        if b"INTI" in menu_data or b"INBb" in menu_data or b"INBg" in menu_data:
            raise ValueError(f"{menu_name} still references stock interface art")
    if b"ALIN" not in brewing_menu or b"INTN" in brewing_menu:
        raise ValueError("CGBR does not use the private Vigor recipe-icon art")
    if (
        b"ALWI" not in brewing_menu
        or b"ALPI" not in brewing_menu
        or b"INCr" in brewing_menu
    ):
        raise ValueError("CGBR does not use both private research-icon records")
    if b"ALSR" not in brewing_menu or b"INSr" in brewing_menu:
        raise ValueError("CGBR does not use the private full-width progress art")

    main_art = output_root / "Data" / "alchemist_maindata.cam"
    interface_art = output_root / "Data" / "alchemist_interfacedata.cam"
    for name in (
        b"ALC1Alchemist",
        b"ALB1Alchemy Lab 1",
        b"ALB2Alchemy Lab 2",
        b"ALB3Alchemy Lab 3",
        b"PXF1Phoenix Phial",
        b"XR01Speed_tonic_ico",
    ):
        if not read_cam_entry(main_art, b"IMAG", name).data:
            raise ValueError(f"Private main art record is empty: {name!r}")
    for name in (
        b"ALTIraw textures",
        b"ALBBbuilding frame",
        b"ALBGbuilding dialog",
        b"ALINrecipe icons",
        b"ALWIweapon oil icon",
        b"ALPIphial icon",
        b"ALSRalchemy progress",
    ):
        if not read_cam_entry(interface_art, b"IMAG", name).data:
            raise ValueError(f"Private interface art record is empty: {name!r}")
    for art_path, prefixes in (
        (main_art, (b"ALC1", b"ALB1", b"ALB2", b"ALB3", b"PXF1", b"XR01")),
        (
            interface_art,
            (b"ALTI", b"ALBB", b"ALBG", b"ALIN", b"ALWI", b"ALPI", b"ALSR"),
        ),
    ):
        tile_entries = read_cam_entries(art_path, b"TILE")
        first_private = next(
            (
                index
                for index, entry in enumerate(tile_entries)
                if entry.name.rstrip(b"\x00").startswith(prefixes)
            ),
            None,
        )
        if first_private is None or not tile_entries[first_private].data:
            raise ValueError(f"Private TILE payloads are missing from {art_path.name}")
        if any(entry.data for entry in tile_entries[:first_private]):
            raise ValueError(f"{art_path.name} overwrites a stock TILE slot")
    brewing_strings = read_cam_entry(text_cam, b"STRT", BREWING_DIALOG_ID).data
    if b"Vigor Elixir\x00" not in brewing_strings:
        raise ValueError("CGBR Vigor Elixir label is missing")
    if b"Invigorated\x00" not in brewing_strings:
        raise ValueError("CGBR active progress label is missing")
    if b"Phoenix Phial\x00" not in brewing_strings:
        raise ValueError("CGBR Phoenix Phial label is missing")
    brewing_string_count = struct.unpack_from("<H", brewing_strings, 0)[0]
    if brewing_string_count <= 28:
        raise ValueError("CGBR active progress label is not present at STRT index 28")
    brewing_string_offsets = struct.unpack_from(
        f"<{brewing_string_count}I", brewing_strings, 4
    )
    active_label_offset = brewing_string_offsets[28]
    active_label_end = brewing_strings.index(b"\x00", active_label_offset + 4)
    if brewing_strings[active_label_offset + 4 : active_label_end] != b"Invigorated":
        raise ValueError("CGBR STRT index 28 is not the Invigorated label")
    if brewing_menu.count(b"ALSR") != 3 or b"INSr" in brewing_menu:
        raise ValueError("CGBR private progress art displays are missing")
    if struct.pack("<I", RAGE_PROGRESS_CONTROL_ID) not in brewing_menu:
        raise ValueError("CGBR native progress control ID is missing")
    if struct.pack("<I", RAGE_ACTIVE_DISPLAY_CONTROL_ID) not in brewing_menu:
        raise ValueError("CGBR native Rage active-display child is missing")
    if brewing_menu.count(struct.pack("<I", BREWING_WEAPON_OIL_CONTROL_ID)) != 1:
        raise ValueError("CGBR native Weapon Oil research row is missing or duplicated")
    if brewing_menu.count(struct.pack("<I", BREWING_PHOENIX_PHIAL_CONTROL_ID)) != 1:
        raise ValueError("CGBR native Phoenix Phial research row is missing or duplicated")
    for control_id, rectangle, label in (
        (
            BREWING_WEAPON_OIL_PRICE_CONTROL_ID,
            WEAPON_OIL_PRICE_RECT,
            "Weapon Oil",
        ),
        (
            BREWING_PHOENIX_PHIAL_PRICE_CONTROL_ID,
            PHOENIX_PHIAL_PRICE_RECT,
            "Phoenix Phial",
        ),
    ):
        marker = struct.pack("<I", control_id)
        if brewing_menu.count(marker) != 1:
            raise ValueError(f"CGBR {label} stock price control is missing or duplicated")
        price_record = brewing_menu.index(marker) - 0x6C
        if struct.unpack_from("<4I", brewing_menu, price_record + 0x08) != rectangle:
            raise ValueError(f"CGBR {label} stock price rectangle changed")
    progress_record_offset = (
        brewing_menu.index(struct.pack("<I", RAGE_PROGRESS_CONTROL_ID)) - 0x6C
    )
    if u32(brewing_menu, progress_record_offset) != 9:
        raise ValueError("CGBR lost the stock Rage progress-control subtype")
    progress_outer_rect = struct.unpack_from(
        "<4I",
        brewing_menu,
        progress_record_offset + RAGE_PROGRESS_OUTER_RECT_OFFSET,
    )
    if progress_outer_rect != BREWING_PROGRESS_OUTER_RECT:
        raise ValueError(
            f"Unexpected CGBR progress-control outer rectangle: {progress_outer_rect}"
        )
    if u32(
        brewing_menu, progress_record_offset + RAGE_PROGRESS_PREFIX_OFFSET
    ) != RAGE_PROGRESS_PREFIX:
        raise ValueError("CGBR corrupted the native Rage progress-control prefix")
    progress_rect = struct.unpack_from(
        "<4I", brewing_menu, progress_record_offset + RAGE_PROGRESS_RECT_OFFSET
    )
    if progress_rect != BREWING_PROGRESS_RECT:
        raise ValueError(f"Unexpected CGBR progress-control rectangle: {progress_rect}")
    weapon_progress_record_offset = (
        brewing_menu.index(
            struct.pack("<I", BREWING_WEAPON_OIL_PROGRESS_CONTROL_ID)
        )
        - 0x6C
    )
    if u32(brewing_menu, weapon_progress_record_offset) != 9:
        raise ValueError("CGBR lost the stock Weapon Oil progress subtype")
    if struct.unpack_from(
        "<4I", brewing_menu, weapon_progress_record_offset + 0x08
    ) != WEAPON_OIL_PROGRESS_OUTER_RECT:
        raise ValueError("CGBR Weapon Oil progress rectangle changed")
    if struct.unpack_from(
        "<4I", brewing_menu, weapon_progress_record_offset + RAGE_PROGRESS_RECT_OFFSET
    ) != WEAPON_OIL_PROGRESS_LABEL_RECT:
        raise ValueError("CGBR Weapon Oil progress label rectangle changed")
    if u32(
        brewing_menu,
        weapon_progress_record_offset + RAGE_ACTIVE_DISPLAY_ID_OFFSET,
    ) != BREWING_WEAPON_OIL_ACTIVE_DISPLAY_CONTROL_ID:
        raise ValueError("CGBR Weapon Oil active label ID changed")
    phoenix_progress_record_offset = (
        brewing_menu.index(
            struct.pack("<I", BREWING_PHOENIX_PHIAL_PROGRESS_CONTROL_ID)
        )
        - 0x6C
    )
    if u32(brewing_menu, phoenix_progress_record_offset) != 9:
        raise ValueError("CGBR lost the stock Phoenix Phial progress subtype")
    if struct.unpack_from(
        "<4I", brewing_menu, phoenix_progress_record_offset + 0x08
    ) != PHOENIX_PHIAL_PROGRESS_OUTER_RECT:
        raise ValueError("CGBR Phoenix Phial progress rectangle changed")
    if struct.unpack_from(
        "<4I", brewing_menu, phoenix_progress_record_offset + RAGE_PROGRESS_RECT_OFFSET
    ) != PHOENIX_PHIAL_PROGRESS_LABEL_RECT:
        raise ValueError("CGBR Phoenix Phial progress label rectangle changed")
    if u32(
        brewing_menu,
        phoenix_progress_record_offset + RAGE_ACTIVE_DISPLAY_ID_OFFSET,
    ) != BREWING_PHOENIX_PHIAL_ACTIVE_DISPLAY_CONTROL_ID:
        raise ValueError("CGBR Phoenix Phial active label ID changed")
    if u32(brewing_menu, BREWING_FIRST_BUTTON_ID_OFFSET) != BREWING_INVIGORATING_CONTROL_ID:
        raise ValueError("CGBR still uses Fervus's first spell control ID")
    bdep = read_cam_entry(
        output_root / "Data" / "alchemist_probe_miscdata.cam", b"DATA", b"BDEP"
    ).data
    if bdep.count(ALCHEMIST_BDEP_RULE) != 1:
        raise ValueError("Alchemist BDEP rule is missing or duplicated")
    if include_phantoms and bdep.count(PHANTOM_BDEP_RULE) != 1:
        raise ValueError("Phantom coexistence BDEP rule is missing or duplicated")
    building_data = (output_root / "GPL" / "Alchemist_Building_Data.dat").read_text(
        encoding="utf-8"
    )
    for name in BUILDING_NAMES:
        if f"[{name}]" not in building_data:
            raise ValueError(f"GPL building record is missing: {name}")
    hero_data = (output_root / "GPL" / "Alchemist_Hero_Data.dat").read_text(
        encoding="utf-8"
    )
    if "[Alchemist]" not in hero_data or "(title Alchemist)" not in hero_data:
        raise ValueError("GPL Alchemist hero record is missing")
    if hero_data.count("Alchemist_tree") != 3:
        raise ValueError("Alchemist must retain all three private Rogue tree hooks")
    expected_title = "Temple_Fervus" if use_ap10_title_alias else "AlchemistsLaboratory"
    if building_data.count(f"(title {expected_title})") != 3:
        raise ValueError(f"Expected all GPL levels to use title {expected_title}")
    if building_data.count("(Alchemist_Brewing True)") != 3:
        raise ValueError("Every Laboratory level must carry its Brewing marker")
    if building_data.count("(Visited_Script Alchemy_Lab_Visited)") != 3:
        raise ValueError("Every Laboratory level must use the combined stock visit dispatcher")
    for contract in (
        "(birthscript basic_birth)",
        "(birthScript2 Guild_Birth)",
        "(member_basicscript Alchemist_tree)",
        "(upgradescript basic_upgrade)",
    ):
        if contract not in building_data:
            raise ValueError(f"GPL construction contract is missing: {contract}")
    compiled = output_root / "Data" / "Alchemist.bcd"
    if compiled.stat().st_size == 0:
        raise ValueError("Compiled Alchemist bytecode is empty")
    compiled_symbols = compiled.read_bytes()
    if b"Alchemist_DoInvigoratingElixer" not in compiled_symbols:
        raise ValueError("Compiled Alchemist bytecode lost its private Vigor symbol")
    if b"Purchase_Equipment" not in compiled_symbols:
        raise ValueError("Compiled Alchemist bytecode lost its stock-derived economy gate")
    for symbol in (
        b"Alchemy_Oil_Check",
        b"Alchemy_Oil_Enchant_Equipment",
        b"Obtain_Alchemy_Oil",
        b"Phoenix_Phial_Check",
        b"Purchase_Phoenix_Phial",
        b"Phoenix_Phial_Resurrection_End",
    ):
        if symbol not in compiled_symbols:
            raise ValueError(f"Compiled Alchemist bytecode lost oil symbol {symbol!r}")
    if b"DoRageOfKrolm" in compiled_symbols or b"Alchemist_Stock_RageOfKrolm" in compiled_symbols:
        raise ValueError("Alchemist bytecode must not override or reimplement stock Rage")


def build(
    game_path: Path,
    output_root: Path,
    include_phantoms: bool,
    use_ap10_title_alias: bool = False,
    enable_unsafe_brewing_control: bool = False,
    include_siege_test_fixture: bool = False,
    approved_sprite_test_set: bool = False,
) -> None:
    if approved_sprite_test_set:
        output_root = require_approved_sprite_output_root(output_root)
    data_dir = output_root / "Data"
    gpl_dir = output_root / "GPL"
    if output_root.exists():
        shutil.rmtree(output_root)
    data_dir.mkdir(parents=True)
    gpl_dir.mkdir(parents=True)
    sdk_data = game_path / "SDK" / "OriginalQuests" / "Data"
    game_data = game_path / "Data"
    generated_art = SOURCE_ROOT.parent / "artifacts" / "generated-art"
    art_cache = SOURCE_ROOT.parent / "artifacts" / "art-cache"
    cached_main = art_cache / "alchemist_maindata.cam"
    cached_interface = art_cache / "alchemist_interfacedata.cam"
    art_inputs = [
        *(SOURCE_ROOT.parent / "assets" / "source").rglob("*"),
        SOURCE_ROOT.parent / "scripts" / "generate_alchemist_art.py",
        SOURCE_ROOT.parent / "src" / "alchemist_art_package.py",
    ]
    newest_input = max(path.stat().st_mtime for path in art_inputs if path.is_file())
    # The accepted Walk/Stand bundle has independent, hash-pinned source
    # artifacts and a new SPLT record. Never let the regular generated-art CAM
    # cache satisfy or absorb this in-game test mode.
    cache_current = (not approved_sprite_test_set) and all(
        path.is_file() and path.stat().st_mtime >= newest_input
        for path in (cached_main, cached_interface)
    )
    if not cache_current:
        art_result = subprocess.run(
            (
                sys.executable,
                str(SOURCE_ROOT.parent / "scripts" / "generate_alchemist_art.py"),
                "--repo",
                str(SOURCE_ROOT.parent),
                "--out-dir",
                str(generated_art),
            ),
            check=False,
        )
        if art_result.returncode != 0:
            raise RuntimeError(f"Alchemist art generation failed with exit code {art_result.returncode}")
    (data_dir / "alchemist_probe_units.xml").write_bytes(
        build_units_xml(sdk_data / "M_Buildings.xml", sdk_data / "M_Characters.xml")
    )
    (data_dir / "alchemist_brewing_overlays.xml").write_bytes(
        build_brewing_overlays_xml(sdk_data / "M_Overlays.xml")
    )
    (data_dir / "alchemist_brewing_sounds.xml").write_bytes(
        build_brewing_sounds_xml(sdk_data / "M_Sounds.xml")
    )
    build_text_cam(
        game_data / "textdata.cam",
        data_dir / "alchemist_probe_textdata.cam",
        enable_unsafe_brewing_control,
    )
    build_gpl_text_cam(
        game_data / "gpltext.cam",
        data_dir / "alchemist_probe_gpltext.cam",
    )
    build_misc_cam(
        game_data / "miscdata.cam",
        data_dir / "alchemist_probe_miscdata.cam",
        include_phantoms,
    )
    approved_art_provenance = None
    if cache_current:
        shutil.copy2(cached_main, data_dir / "alchemist_maindata.cam")
        shutil.copy2(cached_interface, data_dir / "alchemist_interfacedata.cam")
    else:
        approved_art_provenance = write_maindata(
            SOURCE_ROOT.parent,
            game_data,
            generated_art,
            data_dir / "alchemist_maindata.cam",
            (
                APPROVED_SPRITE_PIPELINE_ROOT
                if approved_sprite_test_set
                else None
            ),
        )
        write_interfacedata(
            SOURCE_ROOT.parent,
            game_data,
            generated_art,
            data_dir / "alchemist_interfacedata.cam",
        )
        if not approved_sprite_test_set:
            art_cache.mkdir(parents=True, exist_ok=True)
            shutil.copy2(data_dir / "alchemist_maindata.cam", cached_main)
            shutil.copy2(data_dir / "alchemist_interfacedata.cam", cached_interface)
    if approved_sprite_test_set:
        if approved_art_provenance is None:
            raise AssertionError("Approved sprite test unexpectedly used cached art")
    (gpl_dir / "Alchemist.gplproj").write_text(
        build_gpl_project(include_siege_test_fixture), encoding="utf-8"
    )
    building_data = (GPL_SOURCE_ROOT / "Alchemist_Building_Data.dat").read_text(
        encoding="utf-8"
    )
    if use_ap10_title_alias:
        building_data = building_data.replace(
            "(title AlchemistsLaboratory)", "(title Temple_Fervus)"
        )
    (gpl_dir / "Alchemist_Building_Data.dat").write_bytes(building_data.encode("utf-8"))
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Hero_Data.dat", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Phoenix_Phial.dat", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Rogue.gpl", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Brewing.gpl", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Weapon_Oil.gpl", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Phoenix_Phial.gpl", gpl_dir)
    economy_source = build_alchemist_economy(
        sdk_data.parent
        / "GPL"
        / "DecisionTrees"
        / "Modules"
        / "Purchase_Equipment.gpl"
    )
    (gpl_dir / "Alchemist_Economy.gpl").write_text(
        economy_source, encoding="utf-8"
    )
    if include_siege_test_fixture:
        siege_source = build_siege_test_fixture(
            sdk_data.parent / "GPLMx" / "Rules" / "Quests_3.gpl"
        )
        (gpl_dir / "Alchemist_Siege_Test.gpl").write_text(
            siege_source, encoding="utf-8"
        )
    compiler = game_path / "SDK" / "Gplbcc.exe"
    if not compiler.is_file():
        raise FileNotFoundError(f"Majesty GPL compiler was not found: {compiler}")
    result = subprocess.run(
        (str(compiler), "-in", "Alchemist.gplproj", "-out", "Alchemist.bcd", "-stdout"),
        cwd=gpl_dir,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"GPL compiler failed with exit code {result.returncode}")
    compiled = gpl_dir / "Alchemist.bcd"
    if not compiled.is_file():
        raise FileNotFoundError(f"GPL compiler did not produce: {compiled}")
    shutil.copy2(compiled, data_dir / "Alchemist.bcd")
    compiled.unlink()
    (output_root / "CustomGuildAlchemistProbe.mmxml").write_bytes(
        build_manifest(use_ap10_title_alias, include_siege_test_fixture).encode("utf-8")
    )
    if approved_sprite_test_set:
        assert approved_art_provenance is not None
        approved_art_provenance["compiler"] = {
            "path": "SDK/Gplbcc.exe",
            "sha256": sha256_file(compiler),
        }
        approved_art_provenance["output"]["alchemist_bcd_sha256"] = sha256_file(
            data_dir / "Alchemist.bcd"
        )
        approved_art_provenance["output"]["package_file_sha256"] = {
            path.relative_to(output_root).as_posix(): sha256_file(path)
            for path in sorted(output_root.rglob("*"))
            if path.is_file()
        }
        (output_root / APPROVED_SPRITE_PROVENANCE_NAME).write_text(
            json.dumps(approved_art_provenance, indent=2) + "\n",
            encoding="utf-8",
        )
    validate_output(
        output_root,
        include_phantoms,
        use_ap10_title_alias,
        enable_unsafe_brewing_control,
        include_siege_test_fixture,
        approved_sprite_test_set,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the runnable CGAL panel probe")
    parser.add_argument("--game-path", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--include-phantoms-haunt-probe", action="store_true")
    parser.add_argument("--use-ap10-title-alias-probe", action="store_true")
    parser.add_argument("--enable-unsafe-brewing-control", action="store_true")
    parser.add_argument("--include-siege-test-fixture", action="store_true")
    parser.add_argument(
        "--approved-sprite-test-set",
        action="store_true",
        help=(
            "build a fresh, cache-bypassed in-game gate with approved Walk V4 "
            "and Stand V5 art only"
        ),
    )
    args = parser.parse_args()
    build(
        args.game_path,
        args.output_root,
        args.include_phantoms_haunt_probe,
        args.use_ap10_title_alias_probe,
        args.enable_unsafe_brewing_control,
        args.include_siege_test_fixture,
        args.approved_sprite_test_set,
    )
    print(f"Built and validated Alchemist probe: {args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
