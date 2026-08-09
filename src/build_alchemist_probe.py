from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET


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
RAGE_PROGRESS_RECORD_OFFSET = 0x0C40
RAGE_PROGRESS_CONTROL_ID = 0x2009
BREWING_PROGRESS_RECT = (29, 223, 127, 15)
STOCK_FERVUS_FIRST_SPELL_CONTROL_ID = 0x1140
BREWING_INVIGORATING_CONTROL_ID = 0x2A10
BREWING_FIRST_BUTTON_ID_OFFSET = 0x0204
AP10_SPELL_BUTTON_RECT_OFFSET = 0x0D34
AP10_SPELL_BUTTON_RECT = (103, 162, 93, 26)
BUILDING_IDS = ("ALB1", "ALB2", "ALB3")
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
    anchor = '\tpalace = $GetPlayerOnePalace ();'
    if function.count(anchor) != 1:
        raise ValueError("The Siege Palace initialization no longer matches the SDK fixture")
    spawns = (
        anchor
        + '\n\t$SpawnUnit ( palace, "Temple_Fervus1", '
        '$RandomCoord ( palace, 550, 750 ), "MaxHP" );'
        + '\n\t$SpawnUnit ( palace, "AlchemistsLaboratory1", '
        '$RandomCoord ( palace, 850, 1050 ), "MaxHP" );'
    )
    return function.replace(anchor, spawns, 1) + "\n"


def build_gpl_project(include_siege_test_fixture: bool) -> str:
    sources = ['source="Alchemist_Brewing.gpl"']
    if include_siege_test_fixture:
        sources.append('source="Alchemist_Siege_Test.gpl"')
    return 'data="Alchemist_Building_Data.dat"\n' + "\n".join(sources) + "\n"


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


def read_cam_entry(path: Path, extension: bytes, name: bytes) -> CamEntry:
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
        for _ in range(count):
            raw_name = data[cursor : cursor + 20]
            payload_offset = u32(data, cursor + 20)
            payload_size = u32(data, cursor + 24)
            cursor += ENTRY_HEADER_SIZE
            if raw_name.rstrip(b"\x00") == name:
                return CamEntry(raw_name, data[payload_offset : payload_offset + payload_size])
        break
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
    for index, offset in enumerate(offsets):
        string_id = u32(data, offset)
        end = data.index(b"\x00", offset + 4)
        text = replacements.get(index, data[offset + 4 : end].decode("cp1252"))
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


def build_units_xml(stock_buildings_xml: Path) -> bytes:
    stock_root = ET.parse(stock_buildings_xml).getroot()
    output = ET.Element("Majesty")
    for level, source_name in enumerate(SOURCE_BUILDING_NAMES):
        source = stock_root.find(f'.//Description[@Name="{source_name}"]')
        if source is None:
            raise ValueError(f"Stock building description is missing: {source_name}")
        description = ET.fromstring(ET.tostring(source, encoding="utf-8"))
        description.set("ID", BUILDING_IDS[level])
        description.set("Name", BUILDING_NAMES[level])
        description.set(
            "Description",
            "Alchemist's Laboratory" if level == 0 else f"Alchemist's Laboratory Level {level + 1}",
        )
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
        # The first panel/constructor probe intentionally recruits the stock
        # Cultist. A custom ALC1 description needs its own GPL decision wiring.
        produced = description.find("./Game/Produces/Unit")
        if produced is None:
            raise ValueError(f"{source_name} has no recruitable unit")
        produced.set("ID", "Cultist")
        output.append(description)
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
    """Append AP24's stock INSr child to CGBR's serialized child stream."""
    if brewing_menu.count(b"INSr") != 0:
        raise ValueError("CGBR already contains an INSr progress control")
    if rage_menu[RAGE_PROGRESS_RECORD_OFFSET + 0x2C : RAGE_PROGRESS_RECORD_OFFSET + 0x30] != b"INSr":
        raise ValueError("Stock AP24 progress-control layout changed")
    progress_record = bytearray(rage_menu[RAGE_PROGRESS_RECORD_OFFSET:])
    if struct.pack("<I", RAGE_PROGRESS_CONTROL_ID) not in progress_record:
        raise ValueError("Stock AP24 progress control ID is missing")
    # AP69 already owns Back/Next controls along its bottom edge. Preserve the
    # native Rage bar itself, but fit it precisely between those stock buttons.
    struct.pack_into("<4I", progress_record, 0x68, *BREWING_PROGRESS_RECT)
    output = bytearray(brewing_menu)
    output += progress_record
    return bytes(output)


def privateize_brewing_action_control(brewing_menu: bytes) -> bytes:
    """Detach the first recipe from AP69's built-in Fervus spell metadata."""
    output = bytearray(brewing_menu)
    actual = u32(output, BREWING_FIRST_BUTTON_ID_OFFSET)
    if actual != STOCK_FERVUS_FIRST_SPELL_CONTROL_ID:
        raise ValueError(
            f"Stock AP69 first spell control changed: 0x{actual:04X}"
        )
    struct.pack_into(
        "<I", output, BREWING_FIRST_BUTTON_ID_OFFSET, BREWING_INVIGORATING_CONTROL_ID
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


def build_text_cam(
    stock_text_cam: Path,
    output_path: Path,
    enable_unsafe_brewing_control: bool = False,
) -> None:
    menu = read_cam_entry(stock_text_cam, b"SMNU", SOURCE_DIALOG_ID).data
    if not enable_unsafe_brewing_control:
        menu = disable_ap10_secondary_control(menu)
    strings = read_cam_entry(stock_text_cam, b"STRT", SOURCE_DIALOG_ID).data
    brewing_menu = read_cam_entry(
        stock_text_cam, b"SMNU", SOURCE_BREWING_DIALOG_ID
    ).data
    brewing_menu = privateize_brewing_action_control(brewing_menu)
    rage_menu = read_cam_entry(stock_text_cam, b"SMNU", SOURCE_RAGE_DIALOG_ID).data
    brewing_menu = add_native_rage_progress_control(brewing_menu, rage_menu)
    brewing_strings = read_cam_entry(
        stock_text_cam, b"STRT", SOURCE_BREWING_DIALOG_ID
    ).data
    unit_names = read_cam_entry(stock_text_cam, b"STRT", b"UNTN").data
    patched_units = patch_strt_by_id(
        unit_names,
        {
            fourcc_id("ALB1"): "Alchemist's Laboratory",
            fourcc_id("ALB2"): "Alchemist's Laboratory",
            fourcc_id("ALB3"): "Alchemist's Laboratory",
        },
    )
    patched_strings = patch_strt_by_index(
        strings,
        {
            0: "ALCHEMIST'S LABORATORY",
            1: "RECRUIT Test Alchemist",
            2: "Recruit a stock Cultist as the temporary Alchemist.",
            3: "Destroy this Alchemist's Laboratory.",
            29: "BREWING",
            30: "Open this Laboratory's experimental Brewing window.",
        },
    )
    patched_brewing_strings = patch_strt_by_index(
        brewing_strings,
        {
            0: "ALCHEMIST'S LABORATORY",
            1: "Invigorating Elixer",
            2: "Invigorate every unit for 30 seconds: faster movement, 20 bonus hit points, and greater confidence.",
            3: "1",
            4: "Future Brew",
            5: "This brewing slot is not yet available.",
            6: "",
            7: "Future Brew",
            8: "This brewing slot is not yet available.",
            9: "",
            13: "BREWING",
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


def build_manifest(use_ap10_title_alias: bool = False) -> str:
    probe_detail = (
        "Temporary fixture using stock Fervus and Cultist resources; its GPL title "
        "aliases Temple_Fervus to isolate the AP10 spell callback."
        if use_ap10_title_alias
        else "Temporary fixture using stock Fervus and Cultist resources."
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
\t\t\t\t\t<CAM>Data\\alchemist_probe_miscdata.cam</CAM>
\t\t\t\t\t<Descriptions>Data\\alchemist_probe_units.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_brewing_overlays.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_brewing_sounds.xml</Descriptions>
\t\t\t\t\t<GPL>
\t\t\t\t\t\t<Target>Data\\Alchemist.bcd</Target>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Building_Data.dat</Source>
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
) -> None:
    expected = {
        output_root / "CustomGuildAlchemistProbe.mmxml",
        output_root / "Data" / "alchemist_probe_units.xml",
        output_root / "Data" / "alchemist_brewing_overlays.xml",
        output_root / "Data" / "alchemist_brewing_sounds.xml",
        output_root / "Data" / "alchemist_probe_textdata.cam",
        output_root / "Data" / "alchemist_probe_miscdata.cam",
        output_root / "Data" / "Alchemist.bcd",
        output_root / "GPL" / "Alchemist.gplproj",
        output_root / "GPL" / "Alchemist_Building_Data.dat",
        output_root / "GPL" / "Alchemist_Brewing.gpl",
    }
    if include_siege_test_fixture:
        expected.add(output_root / "GPL" / "Alchemist_Siege_Test.gpl")
    actual = {path for path in output_root.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError(f"Unexpected package files: {sorted(str(p) for p in actual ^ expected)}")
    root = ET.parse(output_root / "Data" / "alchemist_probe_units.xml").getroot()
    descriptions = root.findall("Description")
    if [item.get("ID") for item in descriptions] != list(BUILDING_IDS):
        raise ValueError("Building ID sequence is invalid")
    if any(item.find("./Game/DialogID").get("value") != "CGAL" for item in descriptions):
        raise ValueError("Every Laboratory level must use CGAL")
    text_cam = output_root / "Data" / "alchemist_probe_textdata.cam"
    menu = read_cam_entry(text_cam, b"SMNU", DIALOG_ID).data
    if menu == b"":
        raise ValueError("CGAL menu is empty")
    brewing_menu = read_cam_entry(text_cam, b"SMNU", BREWING_DIALOG_ID).data
    if brewing_menu == b"":
        raise ValueError("CGBR menu is empty")
    brewing_strings = read_cam_entry(text_cam, b"STRT", BREWING_DIALOG_ID).data
    if b"Invigorating Elixer\x00" not in brewing_strings:
        raise ValueError("CGBR Invigorating Elixer label is missing")
    if brewing_menu.count(b"INSr") != 1:
        raise ValueError("CGBR native progress control is missing or duplicated")
    if struct.pack("<I", RAGE_PROGRESS_CONTROL_ID) not in brewing_menu:
        raise ValueError("CGBR native progress control ID is missing")
    if u32(brewing_menu, BREWING_FIRST_BUTTON_ID_OFFSET) != BREWING_INVIGORATING_CONTROL_ID:
        raise ValueError("CGBR still uses Fervus's first spell control ID")
    rect = struct.unpack_from("<4I", menu, AP10_SPELL_BUTTON_RECT_OFFSET)
    expected_rect = AP10_SPELL_BUTTON_RECT if enable_unsafe_brewing_control else (103, 162, 0, 0)
    if rect != expected_rect:
        raise ValueError(f"Unexpected CGAL secondary-control rectangle: {rect}")
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
    expected_title = "Temple_Fervus" if use_ap10_title_alias else "AlchemistsLaboratory"
    if building_data.count(f"(title {expected_title})") != 3:
        raise ValueError(f"Expected all GPL levels to use title {expected_title}")
    if building_data.count("(Alchemist_Brewing True)") != 3:
        raise ValueError("Every Laboratory level must carry its Brewing marker")
    for contract in (
        "(birthscript basic_birth)",
        "(birthScript2 Guild_Birth)",
        "(member_basicscript cultist_tree)",
        "(upgradescript basic_upgrade)",
    ):
        if contract not in building_data:
            raise ValueError(f"GPL construction contract is missing: {contract}")
    compiled = output_root / "Data" / "Alchemist.bcd"
    if compiled.stat().st_size == 0:
        raise ValueError("Compiled Alchemist bytecode is empty")


def build(
    game_path: Path,
    output_root: Path,
    include_phantoms: bool,
    use_ap10_title_alias: bool = False,
    enable_unsafe_brewing_control: bool = False,
    include_siege_test_fixture: bool = False,
) -> None:
    data_dir = output_root / "Data"
    gpl_dir = output_root / "GPL"
    if output_root.exists():
        shutil.rmtree(output_root)
    data_dir.mkdir(parents=True)
    gpl_dir.mkdir(parents=True)
    sdk_data = game_path / "SDK" / "OriginalQuests" / "Data"
    game_data = game_path / "Data"
    (data_dir / "alchemist_probe_units.xml").write_bytes(
        build_units_xml(sdk_data / "M_Buildings.xml")
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
    build_misc_cam(
        game_data / "miscdata.cam",
        data_dir / "alchemist_probe_miscdata.cam",
        include_phantoms,
    )
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
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Brewing.gpl", gpl_dir)
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
        build_manifest(use_ap10_title_alias).encode("utf-8")
    )
    validate_output(
        output_root,
        include_phantoms,
        use_ap10_title_alias,
        enable_unsafe_brewing_control,
        include_siege_test_fixture,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the runnable CGAL panel probe")
    parser.add_argument("--game-path", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--include-phantoms-haunt-probe", action="store_true")
    parser.add_argument("--use-ap10-title-alias-probe", action="store_true")
    parser.add_argument("--enable-unsafe-brewing-control", action="store_true")
    parser.add_argument("--include-siege-test-fixture", action="store_true")
    args = parser.parse_args()
    build(
        args.game_path,
        args.output_root,
        args.include_phantoms_haunt_probe,
        args.use_ap10_title_alias_probe,
        args.enable_unsafe_brewing_control,
        args.include_siege_test_fixture,
    )
    print(f"Built and validated Alchemist probe: {args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
