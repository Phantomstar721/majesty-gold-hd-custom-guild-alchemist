from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import wave
import xml.etree.ElementTree as ET

from alchemist_art_package import (
    ARCANE_INFUSION_ANIMATION_SET,
    ARCANE_INFUSION_DELAY_MS,
    ARCANE_INFUSION_EFFECT_CUSTOM,
    ARCANE_INFUSION_FRAMES,
    ARCANE_INFUSION_HEADER,
    ARCANE_INFUSION_PALETTE,
    FLASH_FLASK_ACTIVATION_CUSTOM,
    FLASH_FLASK_ACTIVATION_DELAY_MS,
    FLASH_FLASK_ACTIVATION_HEADER,
    FLASH_FLASK_ACTIVATION_SOURCE_DELAY_MS,
    FLASH_FLASK_BUFF_CUSTOM,
    PHOENIX_EFFECT_HEADER,
    PHOENIX_EFFECT_PALETTE,
    PHOENIX_EFFECT_TEMPLATE_ANIMATION_SET,
    PHOENIX_EFFECT_TEMPLATE_SOURCE,
    PHOENIX_LIFECYCLE_ANIMATION_SET,
    PHOENIX_LIFECYCLE_CUSTOM,
    PHOENIX_LIFECYCLE_FRAMES,
    PHOENIX_VISIBLE_FRAMES,
    PARALYTIC_OIL_RESTRAINT_CUSTOM,
    PHILOSOPHERS_STONE_HIT_CUSTOM,
    PHILOSOPHERS_STONE_ANIMATION_SET,
    PHILOSOPHERS_STONE_DELAY_MS,
    PHILOSOPHERS_STONE_FRAMES,
    PHILOSOPHERS_STONE_HEADER,
    PHILOSOPHERS_STONE_CURSOR_SET_ID,
    REAGENT_READY_CUSTOM,
    REAGENT_READY_CUSTOM_TILE_AGGREGATE_SHA256,
    REAGENT_READY_ART_SOURCE,
    REAGENT_READY_ART_SOURCE_SHA256,
    REAGENT_READY_CANVAS,
    REAGENT_READY_EFFECT_CENTER,
    REAGENT_READY_FRAME_COUNT,
    REAGENT_READY_PALETTE,
    REAGENT_READY_POOL_CENTER_NATIVE,
    REAGENT_READY_SOURCE,
    REAGENT_READY_SOURCE_PALETTES,
    REAGENT_READY_SOURCE_SHA256,
    REAGENT_READY_SOURCE_TILE_AGGREGATE_SHA256,
    REAGENT_READY_SOURCE_TILES,
    REAGENT_READY_STREAM_COUNT,
    REAGENT_READY_STREAM_REFERENCE_OFFSETS,
    RECIPE_PRIVATE_PLATE_TILE_GROUPS,
    STUN_SERUM_DEBUFF_CUSTOM,
    STUN_SERUM_IMPACT_CUSTOM,
    STUN_SERUM_RESTRAINT_CUSTOM,
    TACTICAL_CURSOR_CUSTOM,
    TACTICAL_CURSOR_SOURCE,
    TACTICAL_CURSOR_TEMPLATE_SET_ID,
    VIGOR_ACTIVATION_ANIMATION_SET,
    VIGOR_ACTIVATION_DELAY_MS,
    VIGOR_ACTIVATION_EFFECT_CUSTOM,
    VIGOR_ACTIVATION_FRAMES,
    VIGOR_ACTIVATION_HEADER,
    VIGOR_ACTIVATION_PALETTE,
    VIGOR_EFFECT_CUSTOM,
    RUNTIME_BUILDING_SCALE,
    generated_discrete_strip_tile,
    generated_frost_armor_hold_tile,
    VINES_FIXED_HEADER,
    load_stock_pipeline,
    set_single_overlay_animation_delay,
    write_interfacedata,
    write_maindata,
)
from approved_sprite_bundle import (
    COMPLETED_HANDOFF_AGGREGATE_SHA256,
    COMPLETED_HANDOFF_MANIFEST_SHA256,
    sha256_file,
)


MAGIC = b"CYLBPC  \x01\x00\x01\x00"
HEADER_SIZE = 20
DIR_ENTRY_SIZE = 8
SECTION_HEADER_SIZE = 8
ENTRY_HEADER_SIZE = 28

MOD_ID = "{42ba4603-2b13-446d-a2a4-6cf3a55ddac3}"
PACKAGE_NAME = "CustomGuildAlchemist"
MANIFEST_FILENAME = f"{PACKAGE_NAME}.mmxml"
MOD_DEFINITION_FILENAME = "mod-definition.json"
RUNTIME_FEATURE_IDENTITIES = (
    ("stock.name-generator.v1", "NM18"),
    ("stock.ap78-enchantment-row.v1", "ALo1"),
    ("stock.ap78-enchantment-row.v1", "ALo2"),
    ("stock.ap10-ap69-secondary-panel.v1", "brewing"),
    ("stock.ap22-resource-meter.v1", "reagents"),
    ("stock.ap99-research-row.v1", "phoenix-phial"),
    ("stock.ap99-research-row.v1", "weapon-oil"),
    ("stock.ap17-upgrade-research-gate.v1", "AlchemistsLaboratory"),
    ("stock.ap24-timed-rage-action.v1", "vigor-elixir"),
    ("stock.ap24-rage-command-action.v1", "arcane-infusion"),
    ("stock.ap69-sovereign-target-action.v1", "philosophers-stone"),
)
DIALOG_ID = b"CGAL"
SOURCE_DIALOG_ID = b"AP10"
BREWING_DIALOG_ID = b"CGBR"
SOURCE_BREWING_DIALOG_ID = b"AP69"
SOURCE_RAGE_DIALOG_ID = b"AP24"
SOURCE_RESEARCH_DIALOG_ID = b"APa1"
SOURCE_MARKET_RESEARCH_DIALOG_ID = b"APa3"
SOURCE_VISITORS_DIALOG_ID = b"AP02"
SOURCE_ITEMS_DIALOG_ID = b"AP22"
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
VIGOR_ROW_PRICE_RECT = (151, 115, 40, 17)
VIGOR_ROW_ICON_RECT = (3, 112, 25, 25)
BREWING_PROGRESS_RECT = (30, 117, 162, 14)
BREWING_PROGRESS_OUTER_RECT = (30, 114, 162, 20)
STOCK_FERVUS_FIRST_SPELL_CONTROL_ID = 0x1140
STOCK_FERVUS_SECOND_SPELL_CONTROL_ID = 0x1132
STOCK_FERVUS_THIRD_SPELL_CONTROL_ID = 0x1133
BREWING_INVIGORATING_CONTROL_ID = 0x2A10
BREWING_INVIGORATING_ICON_CONTROL_ID = BREWING_INVIGORATING_CONTROL_ID + 1000
BREWING_INVIGORATING_PRICE_CONTROL_ID = BREWING_INVIGORATING_CONTROL_ID - 1000
BREWING_FIRST_BUTTON_ID_OFFSET = 0x0204
BREWING_FIRST_ICON_ID_OFFSET = 0x0174
BREWING_FIRST_PRICE_ID_OFFSET = 0x02A4
AP69_SECOND_RECIPE_RECORD_START = 0x0478
AP69_SECOND_RECIPE_RECORD_END = 0x0620
AP69_FIRST_RECIPE_RECORD_START = 0x0120
AP69_FIRST_RECIPE_RECORD_END = 0x02D0
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
BREWING_ARCANE_INFUSION_CONTROL_ID = 0x2A20
BREWING_PHILOSOPHERS_STONE_CONTROL_ID = 0x2A21
BREWING_REAGENT_METER_LABEL_CONTROL_ID = 0x2A23
BREWING_REAGENT_COUNT_CONTROL_ID = 0x2A24
BREWING_PHILOSOPHERS_STONE_PRICE_CONTROL_ID = (
    BREWING_PHILOSOPHERS_STONE_CONTROL_ID - 1000
)
AP69_TITLE_RECORD_START = 0x074C
AP69_TITLE_RECORD_END = 0x07A0
AP69_TITLE_RECT = (33, 32, 137, 20)
AP69_TITLE_TEXT_INDEX_OFFSET = 0x1C
AP69_TITLE_CONTROL_ID_OFFSET = 0x44
AP69_TITLE_CONTROL_ID = 0x0002
AP69_TITLE_FONT_OFFSET = 0x4C
REAGENT_LABEL_RECT = (47, 193, 78, 15)
AP22_HEALING_COUNT_RECORD_START = 0x05EC
AP22_HEALING_COUNT_RECORD_END = 0x0688
AP22_HEALING_COUNT_RECT = (161, 198, 32, 17)
AP22_HEALING_COUNT_TEXT_INDEX_OFFSET = 0x1C
AP22_HEALING_COUNT_TOOLTIP_INDEX_OFFSET = 0x24
AP22_HEALING_COUNT_CONTROL_ID_OFFSET = 0x44
AP22_HEALING_COUNT_CONTROL_ID = 0x03F8
AP22_HEALING_COUNT_BINDING_ID_OFFSET = 0x74
AP22_HEALING_COUNT_BINDING_ID = 0x232A
REAGENT_COUNT_RECT = (125, 193, 32, 15)
BREWING_REAGENT_COUNT_BINDING_ID = 0x2A25
# Northern Expansion's final stock AITX table contains 309 records. Private
# intents append after it so expansion statuses are never replaced.
ALCHEMY_OIL_INTENT_INDEX = 309
ALCHEMY_OIL_INTENT_TEXT = "Applying weapon oil at the alchemy lab"
PARALYTIC_OIL_STATUS_ID = "ALo1"
PARALYTIC_OIL_STATUS_NAME = "alchemist_paralytic_weapon_oil_status"
TRANSMUTATION_OIL_STATUS_ID = "ALo2"
TRANSMUTATION_OIL_STATUS_NAME = "alchemist_transmutation_weapon_oil_status"
POISONED_WEAPON_STATUS_ID = "ALo3"
POISONED_WEAPON_STATUS_NAME = "alchemist_poisoned_weapon_status"
ALCHEMIST_VIGOR_SOUND = "Alchy_Vigor"
ALCHEMIST_BOTTLE_BREAK_SOUND = "Alchy_Bottle"
ALCHEMIST_LAB_SOUND = "Alchy_Lab"
ALCHEMIST_HERO_SOUND = "Alchy_Hero"
ALCHEMIST_CAST_VOICE_SOUND = "Alchy_Cast"
ALCHEMIST_HIRED_VOICE_SOUND = "Alchy_Hired"
ALCHEMIST_VIGOR_SOUND_ID = b"AXV1"
ALCHEMIST_BOTTLE_BREAK_SOUND_ID = b"AXB1"
ALCHEMIST_LAB_SOUND_ID = b"AXL1"
ALCHEMIST_HERO_SOUND_ID = b"AXH1"
ALCHEMIST_CAST_VOICE_SOUND_ID = b"AXC1"
ALCHEMIST_HIRED_VOICE_SOUND_ID = b"AXR1"
ALCHEMIST_BOTTLE_BREAK_WAVE_ID = b"AXBK"
ALCHEMIST_LAB_WAVE_ID = b"AXLB"
ALCHEMIST_VOICE_WAVES = (
    (b"AHS1", "recruitment", b"Hire Voice"),
    (b"AHD1", "deciding", b"Decide Voice"),
    (b"AHI1", "idle", b"Idle Voice"),
    (b"AHH1", "see-hostile", b"Hostile"),
    (b"AHC1", "combat", b"Combat Voice"),
    (b"AHF1", "flee", b"Flee Voice"),
    (b"AHR1", "reward", b"Reward Voice"),
    (b"AHN1", "find-item", b"Item Voice"),
    (b"AHC2", "cast", b"Cast Voice"),
    (b"AHL1", "level-up", b"Level Voice"),
    (b"AH10", "level-10", b"Level Ten"),
    (b"AHE1", "easter-egg", b"Easter Voice"),
    (b"AHDH", "death", b"Death Voice"),
)
ALCHEMIST_HERO_VOICE_PHASES = (
    ("VFX_GO_COMBAT", b"CTGT", b"AHC1"),
    ("VFX_FLEE_COMBAT", b"CTFT", b"AHF1"),
    ("VFX_DECIDING", b"CTDO", b"AHD1"),
    ("VFX_GO_REWARD", b"CTDG", b"AHR1"),
    ("VFX_FIND_COOL", b"CTFL", b"AHN1"),
    ("VFX_SPECIAL1", b"CTSS", b"AHI1"),
    ("Death", b"CTDH", b"AHDH"),
    ("VFX_GAIN_LEVEL", b"CTGL", b"AHL1"),
    ("VFX_SEE_HOSTILE", b"CTSE", b"AHH1"),
    ("Easter_Egg", b"CTE1", b"AHE1"),
    ("VFX_LEVEL_10", b"CTTL", b"AH10"),
)
PHOENIX_PHIAL_INTENT_INDEX = 310
PHOENIX_PHIAL_INTENT_TEXT = "Purchasing a Phoenix Phial at the alchemy lab"
PHOENIX_PHIAL_ITEM_ID = 113
PHOENIX_PHIAL_ITEM_TEXT = (
    "Phoenix Phial\n\x01FFDDAA(75% chance to revive after death)"
)
PHANTOM_COWL_TIER_NAMES = (
    "Frozen Cowl",
    "Icy Cowl",
    "Hardened Ice Cowl",
    "Eternal Ice Cowl",
)
PHANTOM_ICEROD_TIER_NAMES = (
    "Black Icerod",
    "Dark Icerod",
    "Deep Icerod",
    "Eternal Icerod",
)
ALCHEMIST_STRENGTH_ACTION_ID = "APS1"
ALCHEMIST_STRENGTH_ACTION_NAME = "alchemist_strength_potion"
ALCHEMIST_SHAPESHIFT_ACTION_ID = "APS2"
ALCHEMIST_SHAPESHIFT_ACTION_NAME = "alchemist_shapeshift_potion"
ALCHEMIST_FIRE_BALM_ACTION_ID = "APS3"
ALCHEMIST_FIRE_BALM_ACTION_NAME = "alchemist_fire_balm"
ALCHEMIST_REGENERATION_ACTION_ID = "APS4"
ALCHEMIST_REGENERATION_ACTION_NAME = "alchemist_regeneration_elixer"
ALCHEMIST_CONSUMABLE_VALIDATION = "alchemist_combat_consumable_check"
FLASH_FLASK_ACTION_ID = "AFa1"
FLASH_FLASK_ACTION_NAME = "flash_flask"
FLASH_FLASK_ICON_ID = "AFF1"
FLASH_FLASK_EFFECT_ID = "AFF2"
FLASH_FLASK_DURATION_MS = "30000"
FLASH_FLASK_COOLDOWN_MS = "45000"
STUN_SERUM_ACTION_ID = "ASs1"
STUN_SERUM_ACTION_NAME = "stun_serum"
STUN_SERUM_IMPACT_ID = "ASS1"
STUN_SERUM_RESTRAINT_ID = "ASS2"
STUN_SERUM_DEBUFF_ID = "ASS3"
STUN_SERUM_DURATION_MS = "5000"
STUN_SERUM_COOLDOWN_MS = "45000"
MIASMA_MIST_ACTION_ID = "AMa1"
MIASMA_MIST_ACTION_NAME = "miasma_mist"
MIASMA_MIST_CLOUD_UNIT_ID = "AMM1"
MIASMA_MIST_MISSILE_ID = "AMM2"
MIASMA_MIST_CLOUD_OVERLAY_ID = "AMM3"
MIASMA_MIST_PARTICLE_ID = "AMM4"
MIASMA_MIST_DEBUFF_ID = "AMM5"
MIASMA_MIST_DURATION_MS = "21000"
MIASMA_MIST_COOLDOWN_MS = "60000"
MIASMA_MIST_DEBUFF_DURATION_MS = "10000"
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
ALCHEMIST_HERO_HELP_ID = "hAL0"
ALCHEMIST_BUILDING_HELP_IDS = ("hAL1", "hAL2", "hAL3")
ALCHEMIST_NAME_GENERATOR_ID = "NM18"
ALCHEMIST_RECRUIT_COST = "600"
ALCHEMIST_BUILDING_COSTS = ("1400", "1800", "2200")
ALCHEMIST_NAME_TABLE_IDS = (b"HN69", b"HN70", b"HN71", b"HN72")
ALCHEMIST_NAME_GIVENS = (
    "Adalia",
    "Aeris",
    "Alys",
    "Ameline",
    "Anora",
    "Beatrix",
    "Brinna",
    "Bryony",
    "Calista",
    "Celandra",
    "Cerys",
    "Corvina",
    "Delphine",
    "Delyra",
    "Elara",
    "Elspeth",
    "Eudora",
    "Evania",
    "Fenella",
    "Hester",
    "Ilyra",
    "Isolde",
    "Jessamine",
    "Katell",
    "Lavinia",
    "Lenora",
    "Maelis",
    "Melisande",
    "Mirabel",
    "Mirelda",
    "Nerissa",
    "Odette",
    "Petra",
    "Rosamund",
    "Rowena",
    "Sabine",
    "Selene",
    "Sybilla",
    "Tamsin",
    "Verena",
    "Vespera",
    "Olyra",
    "Zora",
)
ALCHEMIST_NAME_ENDINGS = (
    "Alembic",
    "Amberglass",
    "Ashvial",
    "Blackflask",
    "Brasscoil",
    "Brightbottle",
    "Cinderbrew",
    "Fireglass",
    "Emberglass",
    "Flamebrew",
    "Flaskwise",
    "Fullflask",
    "Glassweaver",
    "Giltglass",
    "Brightvial",
    "Mortarwise",
    "Quickmeasure",
    "Quicksilver",
    "Silverstill",
    "Singedbrow",
    "Smokesleeve",
    "Sootsleeve",
    "Stonepestle",
    "Vitriol",
    "of the Brass Crucible",
    "of the Copper Coil",
    "of the Emerald Flask",
    "of the Golden Measure",
    "of the Scarlet Flask",
    "of the Viridian Flame",
    "of the Silver Still",
    "the Apothecary",
    "the Artificer",
    "the Bottlemaker",
    "the Brewmistress",
    "the Catalyst",
    "the Distiller",
    "the Experimenter",
    "the Formula Keeper",
    "the Crucible Keeper",
    "the Singed",
    "the Meticulous",
    "the Transmuter",
)
ALCHEMIST_HELP_PAGES = {
    ALCHEMIST_HERO_HELP_ID: (
        "- Fights in melee with a dagger, but prepares for combat from a distance\n\n"
        "- Seeks out Magic Bazaar potions, Weapon Oil and Phoenix Phials\n\n"
        "- Immune to poison\n\n"
        "- Learns Flash Flask at level 3, Stun Serum at level 5 and Miasma Mist at level 8\n\n\n"
        "\x01BCBCFFAlchemists are restless scholars who carry their experiments out of the workshop "
        "and into the wilds of Ardania. They lack a Warrior's discipline and a Wizard's "
        "raw command of magic, but careful preparation makes them elusive and dangerous "
        "opponents. Every battle is another field trial, and every monster is a promising "
        "source of ingredients, provided the formula survives its inventor."
    ),
    ALCHEMIST_BUILDING_HELP_IDS[0]: (
        "- Requires a level 2 Palace\n\n"
        "- Recruits Alchemists\n\n"
        "- Houses up to four guild members\n\n"
        "- Can research Weapon Oil for 250 gold\n\n"
        "- Researched Weapon Oil may be purchased by visiting weapon-wielding heroes for 100 gold\n\n"
        "\x01DDBB44Upgrading the Laboratory adds\n"
        "+ Phoenix Phial research\n"
        "+ Increased building hit points\n\n\n"
        "\x01BCBCFFBehind the stained windows of an Alchemy Lab, copper vessels simmer beside ranks "
        "of carefully labeled bottles. Its practitioners promise that every scorch mark, "
        "shattered flask and alarming odor is simply another step toward a reliable result."
    ),
    ALCHEMIST_BUILDING_HELP_IDS[1]: (
        "- Allows Phoenix Phials to be researched for 750 gold\n\n"
        "- Researched Phoenix Phials may be purchased by visiting heroes for 750 gold\n\n"
        "- A carried Phoenix Phial is consumed at death and has a 75% chance to revive its owner\n\n"
        "\x01DDBB44Upgrading the Laboratory adds\n"
        "+ Vigor Elixir\n"
        "+ Increased building hit points\n\n\n"
        "\x01BCBCFFWith a larger still and a better-stocked workbench, the Laboratory's experiments "
        "turn from useful preparations to improbable feats. The Phoenix Phial is its proudest "
        "achievement, although the alchemists remain evasive when asked about the other "
        "twenty-five percent."
    ),
    ALCHEMIST_BUILDING_HELP_IDS[2]: (
        "- Allows the sovereign to brew Vigor Elixir for 1,500 gold\n\n"
        "- Vigor Elixir invigorates every hero in the realm for 30 seconds\n\n"
        "- Invigorated heroes move faster, gain 20 maximum and current hit points, and fight with greater confidence\n\n"
        "- Vigor Elixir and Rage of Krolm cannot be active at the same time\n\n\n"
        "\x01BCBCFFCrowned by an elaborate distiller, a master Laboratory turns the wealth and "
        "curiosities of an entire realm into bottled possibility. Its furnaces never cool, "
        "its glassworks never empty and its alchemists insist that the occasional explosion "
        "is a sign of vigorous scholarship."
    ),
}
ALCHEMIST_BDEP_RULE = b"ALB1 : ABJ2 ABJ3 NOT NOT ||"
PHANTOM_BDEP_RULE = b"PHG1 : ABJ2 ABJ3 NOT NOT ||"
ALCHEMIST_BDEP_COMMENT = b"Alchemist Lab requires Palace level 2"
PHANTOM_BDEP_COMMENT = b"Compatibility: Phantoms Haunt"
STOCK_BDEP_CAM_RELATIVE_PATH = Path("DataMX") / "mx_miscdata.cam"
STOCK_EXPANSION_BDEP_RULES = (
    b"ABo1 : ABJ3 ABm1 || ABo1 NOT &&",
    b"ABl1 : ABJ2 ABJ3 NOT NOT || ABm1 ||",
    b"ABm1 : ABJ2 ABJ3 NOT NOT || ABm1 ||",
    b"ABr1 : ABJ2 ABJ3 NOT NOT || ABm1 ||",
    b"ABq1 : ABq1 NOT ABq2 NOT ABq3 NOT && && "
    b"ABl1 ABl2 NOT NOT || ABl3 NOT NOT || &&",
)
SOURCE_ROOT = Path(__file__).resolve().parent
GPL_SOURCE_ROOT = SOURCE_ROOT / "gpl"
APPROVED_SPRITE_PIPELINE_ROOT = (
    SOURCE_ROOT.parent / "assets" / "source" / "approved-alchemist-sprite-set-v1"
)
APPROVED_SPRITE_PROVENANCE_NAME = "ApprovedSpriteTestSet.json"


def current_alchemist_art_input_sha256() -> str:
    """Fingerprint every input whose output can be reused as an art package."""
    repo = SOURCE_ROOT.parent
    inputs = [
        *(repo / "assets" / "source").rglob("*"),
        repo / "scripts" / "generate_alchemist_art.py",
        repo / "src" / "alchemist_art_package.py",
        repo / "src" / "approved_sprite_bundle.py",
        repo / "src" / "approved_building_bundle.py",
    ]
    files = sorted(
        (path for path in inputs if path.is_file()),
        key=lambda path: path.relative_to(repo).as_posix().casefold(),
    )
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(repo).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "little"))
        digest.update(relative)
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def require_verified_approved_art_package(reuse_root: Path) -> Path:
    """Fail closed unless reusable CAMs carry the approved sprite provenance."""
    resolved = reuse_root.resolve()
    repo_root = SOURCE_ROOT.parent.resolve()
    if repo_root not in resolved.parents and resolved != repo_root:
        raise ValueError("Reusable art package must stay inside the Alchemist repository")
    package_root = resolved.parent if resolved.name.casefold() == "data" else resolved
    data_root = package_root / "Data"
    if not data_root.is_dir():
        raise ValueError(f"Reusable art package has no Data directory: {package_root}")
    provenance_path = package_root / APPROVED_SPRITE_PROVENANCE_NAME
    if not provenance_path.is_file():
        raise ValueError(
            "Reusable art package is not an approved Alchemist sprite package: "
            f"missing {provenance_path}"
        )
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if provenance.get("schema") != "majesty-alchemist-approved-sprite-test-set-v2":
        raise ValueError("Reusable art package has an unknown approved-sprite schema")
    handoff = provenance.get("handoff", {})
    if handoff.get("manifest_sha256") != COMPLETED_HANDOFF_MANIFEST_SHA256:
        raise ValueError("Reusable art package does not match the approved handoff manifest")
    if handoff.get("payload_aggregate_sha256") != COMPLETED_HANDOFF_AGGREGATE_SHA256:
        raise ValueError("Reusable art package does not match the approved sprite payload")
    if (
        provenance.get("art_inputs", {}).get("aggregate_sha256")
        != current_alchemist_art_input_sha256()
    ):
        raise ValueError(
            "Reusable approved art package is stale for the current Alchemist art inputs; "
            "rebuild -ApprovedSpriteTestSet first"
        )
    package_hashes = provenance.get("output", {}).get("package_file_sha256", {})
    for relative_name in (
        "Data/alchemist_maindata.cam",
        "Data/alchemist_interfacedata.cam",
    ):
        path = package_root / Path(relative_name)
        if not path.is_file():
            raise ValueError(f"Reusable approved art package is missing {path}")
        if package_hashes.get(relative_name) != sha256_file(path):
            raise ValueError(
                f"Reusable approved art hash does not match provenance: {relative_name}"
            )
    return package_root


def require_approved_sprite_output_root(output_root: Path) -> Path:
    approved_dist = (SOURCE_ROOT.parent / "dist").resolve()
    regular_package = (approved_dist / PACKAGE_NAME).resolve()
    resolved = output_root.resolve()
    if resolved == approved_dist:
        raise ValueError("Approved sprite output must be a child of the repository dist directory")
    if resolved == regular_package:
        raise ValueError("Approved sprite output may not replace the production build")
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


def build_alchemist_embassy(
    stock_embassy: Path,
    include_phantoms: bool,
    phantom_gpl: Path | None = None,
) -> str:
    """Add Alchemist to the stock Embassy/Outpost random-hero selector.

    Standalone builds clone Northern Expansion's complete 16-result selector
    and append Alchemist as result 17. The explicit Haunt compatibility build
    starts from Haunt's proven merged selector, retains its Paladin exclusion
    only while a Haunt is placed, and appends Alchemist as result 18.
    """
    if include_phantoms:
        if phantom_gpl is None or not phantom_gpl.is_file():
            raise ValueError(
                "Phantoms Haunt compatibility requires its source GPL checkout"
            )
        source = phantom_gpl.read_text(encoding="utf-8")
        function = extract_gpl_function(source, "Random_Hero_Type")
        haunt_check = "$Phantom_Player_Has_Placed_Haunt(ThisAgent)"
        private_check = "$Alchemist_Compat_Phantom_Max_Haunt_Level(ThisAgent) > 0"
        if function.count(haunt_check) != 1:
            raise ValueError("Haunt Random_Hero_Type placement gate changed")
        function = function.replace(haunt_check, private_check, 1)
        if function.count("Random = $RandomNumber(16) + 1;") != 1:
            raise ValueError("Haunt filtered Embassy selector size changed")
        if function.count("Random = $RandomNumber(17) + 1;") != 1:
            raise ValueError("Haunt ordinary Embassy selector size changed")
        function = function.replace(
            "Random = $RandomNumber(17) + 1;",
            "Random = $RandomNumber(18) + 1;",
            1,
        )
        function = function.replace(
            "Random = $RandomNumber(16) + 1;",
            "Random = $RandomNumber(17) + 1;",
            1,
        )
        function = function.replace(
            '\t\t\t\tElse\n\t\t\t\t\treturn "Phantom";',
            '\t\t\t\tElse if (Random == 16)\n'
            '\t\t\t\t\treturn "Phantom";\n'
            '\t\t\t\tElse\n'
            '\t\t\t\t\treturn "Alchemist";',
            1,
        )
        function = function.replace(
            '\tElse\n\t\treturn "Phantom";',
            '\tElse if (Random == 17)\n'
            '\t\treturn "Phantom";\n'
            '\tElse\n'
            '\t\treturn "Alchemist";',
            1,
        )
        if function.count('return "Alchemist";') != 2:
            raise ValueError("Haunt-compatible Embassy selector lost Alchemist")
        return function + "\n"

    source = stock_embassy.read_text(encoding="cp1252")
    function = extract_gpl_function(source, "Random_Hero_Type")
    size_anchor = "Random = $RandomNumber (16) + 1;"
    tail_anchor = (
        '\tElse if (Random == 15)\n'
        '\t\treturn "Elf";\n'
        '\tElse\n'
        '\t\treturn "Gnome";'
    )
    if function.count(size_anchor) != 1 or function.count(tail_anchor) != 1:
        raise ValueError("Stock Northern Expansion Random_Hero_Type changed")
    function = function.replace(size_anchor, "Random = $RandomNumber (17) + 1;", 1)
    function = function.replace(
        tail_anchor,
        '\tElse if (Random == 15)\n'
        '\t\treturn "Elf";\n'
        '\tElse if (Random == 16)\n'
        '\t\treturn "Gnome";\n'
        '\tElse\n'
        '\t\treturn "Alchemist";',
        1,
    )
    if 'return "Paladin";' not in function or 'return "Phantom";' in function:
        raise ValueError("Standalone Embassy selector changed stock Paladin behavior")
    return function + "\n"


def build_alchemist_guild_title(stock_mausoleum: Path) -> str:
    """Clone stock Guild_Title and add only the Alchemist home mapping."""

    source = stock_mausoleum.read_text(encoding="cp1252")
    function = extract_gpl_function(source, "Guild_Title")
    anchor = (
        '\telse if ( ThisAgent\'s "title" == "Wizard" )\n'
        '\t\treturn "Wizards_Guild";\n'
        "\telse\n"
    )
    if function.count(anchor) != 1:
        raise ValueError("Stock Guild_Title Wizard fallback anchor changed")
    replacement = (
        '\telse if ( ThisAgent\'s "title" == "Wizard" )\n'
        '\t\treturn "Wizards_Guild";\n'
        '\telse if ( ThisAgent\'s "title" == "Alchemist" )\n'
        '\t\treturn "AlchemistsLaboratory";\n'
        "\telse\n"
    )
    return function.replace(anchor, replacement, 1) + "\n"


def build_alchemist_adopt(stock_building_births: Path) -> str:
    """Clone stock adopt and privatize Alchemist ownership transitions."""

    source = stock_building_births.read_text(encoding="cp1252")
    function = extract_gpl_function(source, "adopt")
    stock_cleanup = (
        '\tIf ( $CheckEffector ( Stray, "Rage_Icon" ))\n'
        "\t\tbegin\n"
        "\n"
        '\t\t\t$DeleteEffector ( Stray, "Rage_Icon" );\n'
        "\n"
        "\t\tend\n"
    )
    if function.count(stock_cleanup) != 1:
        raise ValueError("Stock adopt Rage ownership-transition cleanup changed")
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
    function = function.replace(
        stock_cleanup, stock_cleanup + private_cleanup, 1
    )
    ownership_anchor = (
        '\t$setunitplayernumber ( stray, $getunitplayernumber ( thisguild ));\n'
    )
    if function.count(ownership_anchor) != 1:
        raise ValueError("Stock adopt player-ownership boundary changed")
    infusion_reapply = (
        ownership_anchor
        + '\tif ( stray\'s "title" == "Alchemist" )\n'
        + "\t\t$Alchemist_Apply_Arcane_Infusion ( stray );\n"
    )
    return function.replace(ownership_anchor, infusion_reapply, 1) + "\n"


def build_siege_test_fixture(stock_quests: Path) -> str:
    source = stock_quests.read_text(encoding="cp1252")
    function = extract_gpl_function(source, "SIEGE")
    declare_anchor = "\tagent palace, enemypalace;"
    if function.count(declare_anchor) != 1:
        raise ValueError("The Siege agent declarations no longer match the SDK fixture")
    function = function.replace(
        declare_anchor,
        "\tagent palace, enemypalace, alchemyLab, testAlchemistOne, "
        "testAlchemistTwo, testWarriorOne, testWarriorTwo;",
        1,
    )
    anchor = '\tpalace = $GetPlayerOnePalace ();'
    if function.count(anchor) != 1:
        raise ValueError("The Siege Palace initialization no longer matches the SDK fixture")
    spawns = (
        anchor
        + '\n\talchemyLab = $SpawnUnit ( palace, "AlchemistsLaboratory3", '
        '$RandomCoord ( palace, 400, 525 ), "MaxHP" );'
        + '\n\talchemyLab\'s "num_resources" = 20;'
        + '\n\t$SetAttribute ( alchemyLab, #ATTRIB_ReturnAmount, 20 );'
        + '\n\t$Alchemist_Update_Reagent_Ready_Effector ( alchemyLab );'
        + '\n\t$AdjustPlayerData ( palace, "gold", 100000 );'
        + '\n\ttestWarriorOne = $SpawnUnit ( palace, "Warrior", '
        '$RandomCoord ( alchemyLab, 150, 200 ) );'
        + '\n\ttestWarriorTwo = $SpawnUnit ( palace, "Warrior", '
        '$RandomCoord ( alchemyLab, 175, 225 ) );'
        + '\n\ttestAlchemistOne = $SpawnUnit ( alchemyLab, "Alchemist", '
        '$RandomCoord ( alchemyLab, 200, 250 ) );'
        + '\n\ttestAlchemistTwo = $SpawnUnit ( alchemyLab, "Alchemist", '
        '$RandomCoord ( alchemyLab, 225, 275 ) );'
    )
    setup = ""
    for buyer in (
        "testWarriorOne",
        "testWarriorTwo",
        "testAlchemistOne",
        "testAlchemistTwo",
    ):
        setup += (
            f'\n\t$Advance_To_Level ( {buyer}, 10 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Experience, 0 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Gold, 5000 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Weapon_Struct_Bonus, 3 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Armor_Struct_Bonus, 3 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Weapon_Magic_Bonus, 3 );'
            f'\n\t$SetAttribute ( {buyer}, #ATTRIB_Armor_Magic_Bonus, 3 );'
        )
    return function.replace(anchor, spawns + setup, 1)


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
    poison_roll_anchor = (
        '\t\t\t\t\t\tIf (ThisAgent\'s "Poison_Weapon_Chance" > $RandomNumber (100) + 1)'
        "\n\t\t\t\t\t\t\tWants_Poison = TRUE;"
    )
    if function.count(poison_roll_anchor) != 1:
        raise ValueError("Stock Purchase_Equipment poison roll changed")
    list_anchor = "\tlist blacksmiths,wizguilds,markets,shops,fairgrounds,buildings;"
    if function.count(list_anchor) != 1:
        raise ValueError("Stock Purchase_Equipment list declaration changed")
    function = function.replace(
        list_anchor,
        "\tlist blacksmiths,wizguilds,markets,shops,fairgrounds,buildings,alchemyLabs,phoenixLabs;",
        1,
    )
    wizard_anchors = (
        '\twizGuilds = $listTitles(buildings,"Wizards_Guild");',
        '\twizGuilds = $RemoveTitles(buildings,"Wizards_Guild");',
    )
    matching_wizard_anchors = [
        anchor for anchor in wizard_anchors if function.count(anchor) == 1
    ]
    if len(matching_wizard_anchors) != 1:
        raise ValueError("Stock Purchase_Equipment Wizard list construction changed")
    wizard_anchor = matching_wizard_anchors[0]
    lab_list_function = (
        "$RemoveTitles" if "$RemoveTitles" in wizard_anchor else "$listTitles"
    )
    gate = (
        wizard_anchor
        + f'\n\talchemyLabs = {lab_list_function}(buildings,"AlchemistsLaboratory");'
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
    # Phoenix Phial is the Laboratory's consumable defensive item. Preserve
    # the stock single-item check and nested Else chain, but evaluate it after
    # Ring of Protection and before the permanent Teleportation Amulet.
    phoenix_before_market = (
        "\t\t\t\t\t\t\t\t\tIf ($Phoenix_Phial_Check (ThisAgent,phoenixLabs))"
        + "\n\t\t\t\t\t\t\t\t\t\tbegin"
        + "\n\t\t\t\t\t\t\t\t\t\t\tFlag = TRUE;"
        + "\n\t\t\t\t\t\t\t\t\t\tend"
        + "\n\t\t\t\t\t\t\t\t\tElse"
        + "\n"
        + market_anchor
    )
    return function.replace(market_anchor, phoenix_before_market, 1) + "\n"


def build_alchemist_damage(stock_make_attack: Path) -> str:
    """Clone stock damage and extend only its confirmed-hit coating branch."""
    source = stock_make_attack.read_text(encoding="cp1252")
    function = extract_gpl_function(source, "damage")
    stock_poison = (
        '\t\t\t\t\tif ( $getattribute ( attacker, #ATTRIB_weaponpoisoned ) == 1 )\n'
        "\t\t\t\t\t\tbegin\n"
        "\t\t\t\t\t\t\tdo_poison = TRUE;\n"
        '\t\t\t\t\t\t\tif ( $hasattribute ( "Immune_to_poison", defender ))\n'
        '\t\t\t\t\t\t\t\tif ( defender\'s "immune_to_poison" == TRUE )\n'
        "\t\t\t\t\t\t\t\t\tdo_poison = FALSE;\n\n"
        "\t\t\t\t\t\t\tif ( do_poison )\n"
        "\t\t\t\t\t\t\t\t$poison_begin ( attacker, defender );\n"
        "\t\t\t\t\t\tend"
    )
    if function.count(stock_poison) != 1:
        raise ValueError("Stock damage poison-on-hit branch changed")
    private_oils = (
        stock_poison
        + "\n\n\t\t\t\t\tIf ($HasAttribute (\"AlchemyWeaponOilType\", Attacker))"
        + "\n\t\t\t\t\t\tbegin"
        + "\n\t\t\t\t\t\t\tIf (Attacker's \"AlchemyWeaponOilType\" == 1)"
        + "\n\t\t\t\t\t\t\t\t$Alchemy_Paralytic_Oil_Begin (Attacker, Defender);"
        + "\n\t\t\t\t\t\t\tElse If (Attacker's \"AlchemyWeaponOilType\" == 2)"
        + "\n\t\t\t\t\t\t\t\t$Alchemy_Transmutation_Oil_Hit (Attacker, Defender);"
        + "\n\t\t\t\t\t\tend"
    )
    return function.replace(stock_poison, private_oils, 1) + "\n"


def build_alchemist_magic_bazaar(stock_magic_bazaar: Path) -> str:
    """Privatize only Bazaar selection; retain the complete stock transaction."""
    source = stock_magic_bazaar.read_text(encoding="cp1252")
    purchase = extract_gpl_function(source, "Purchase_Bazaar")
    check = extract_gpl_function(source, "Bazaar_Item_Check")

    stock_signature = (
        "Function Purchase_Bazaar ( agent ThisAgent, integer bazaar_chance ) is boolean"
    )
    if purchase.count(stock_signature) != 1:
        raise ValueError("Stock Purchase_Bazaar signature changed")
    purchase = purchase.replace(
        stock_signature,
        "Function Alchemist_Purchase_Bazaar ( agent ThisAgent, integer bazaar_chance ) is boolean",
        1,
    )
    stock_order = (
        "\tItem_list << #Bazaar_Item_One;\n"
        " \tItem_list << #Bazaar_Item_Two;\n"
        " \tItem_list << #Bazaar_Item_Three;\n"
        "\tItem_list << #Bazaar_Item_Four;\n"
        " \tItem_list << #Bazaar_Item_Five;\n"
        " \tItem_list << #Bazaar_Item_Six;"
    )
    # Stock checks every item and the last successful check owns TaskName.
    # Iterating lowest-to-highest yields the requested final priority:
    # Speed > Strength > Regeneration > Fire > Shapeshift > Invisibility.
    private_order = (
        "\tItem_list << #Bazaar_Item_Five;\n"
        "\tItem_list << #Bazaar_Item_Six;\n"
        "\tItem_list << #Bazaar_Item_Two;\n"
        "\tItem_list << #Bazaar_Item_Four;\n"
        "\tItem_list << #Bazaar_Item_Three;\n"
        "\tItem_list << #Bazaar_Item_One;"
    )
    if purchase.count(stock_order) != 1:
        raise ValueError("Stock Purchase_Bazaar item order changed")
    purchase = purchase.replace(stock_order, private_order, 1)
    if purchase.count("$Bazaar_Item_Check") != 1:
        raise ValueError("Stock Purchase_Bazaar item-check call changed")
    purchase = purchase.replace(
        "$Bazaar_Item_Check", "$Alchemist_Bazaar_Item_Check", 1
    )

    stock_check_signature = (
        "Function Bazaar_Item_Check ( agent ThisAgent, integer item, list potentials, integer Item_cost ) is boolean"
    )
    if check.count(stock_check_signature) != 1:
        raise ValueError("Stock Bazaar_Item_Check signature changed")
    check = check.replace(
        stock_check_signature,
        "Function Alchemist_Bazaar_Item_Check ( agent ThisAgent, integer item, list potentials, integer Item_cost ) is boolean",
        1,
    )
    stock_fire_gate = (
        '\t\tif (( thisagent\'s "title" != "ranger"  ) && '
        '( thisagent\'s "title" != "rogue" ) && '
        '( thisagent\'s "title" != "elf" ))'
    )
    private_fire_gate = (
        '\t\tif (( thisagent\'s "title" != "ranger"  ) && '
        '( thisagent\'s "title" != "rogue" ) && '
        '( thisagent\'s "title" != "elf" ) && '
        '( thisagent\'s "title" != "alchemist" ))'
    )
    if check.count(stock_fire_gate) != 1:
        raise ValueError("Stock Bazaar fire-balm eligibility changed")
    check = check.replace(stock_fire_gate, private_fire_gate, 1)

    nearby_purchase = purchase.replace(
        "Function Alchemist_Purchase_Bazaar",
        "Function Alchemist_Purchase_Nearby_Bazaar",
        1,
    )
    stock_search = (
        "\tSearch_Dist = $GetAttribute (ThisAgent, #ATTRIB_SightRange ) * "
        "( $GetAttribute ( ThisAgent, #ATTRIB_Intelligence ) / 2 );"
    )
    nearby_search = "\tSearch_Dist = #Alchemist_Town_Shopping_Range;"
    if nearby_purchase.count(stock_search) != 1:
        raise ValueError("Stock Bazaar intelligence search radius changed")
    nearby_purchase = nearby_purchase.replace(stock_search, nearby_search, 1)
    return purchase + "\n\n" + nearby_purchase + "\n\n" + check + "\n"


def build_alchemist_nearby_equipment(stock_purchase_equipment: Path) -> str:
    """Build local and funded variants of the private stock shopping clone."""

    source = stock_purchase_equipment.read_text(encoding="cp1252")
    poison = extract_gpl_function(source, "Poison_Check")

    # Begin from the same complete private clone packaged as Purchase_Equipment.
    # This is important: deriving the local pass directly from the retail
    # function silently omits Weapon Oil and Phoenix Phial.
    purchase = build_alchemist_economy(stock_purchase_equipment).rstrip()

    stock_purchase_signature = (
        "Function Purchase_Equipment (agent ThisAgent) is boolean"
    )
    if purchase.count(stock_purchase_signature) != 1:
        raise ValueError("Stock Purchase_Equipment signature changed")
    purchase = purchase.replace(
        stock_purchase_signature,
        "Function Alchemist_Purchase_Nearby_Equipment (agent ThisAgent) is boolean",
        1,
    )
    stock_purchase_search = (
        "\tSearch_Dist = $GetAttribute (ThisAgent, #ATTRIB_SightRange) * "
        "($GetAttribute (ThisAgent, #ATTRIB_Intelligence) / 2);"
    )
    nearby_purchase_search = "\tSearch_Dist = #Alchemist_Town_Shopping_Range;"
    if purchase.count(stock_purchase_search) != 1:
        raise ValueError("Stock equipment intelligence search radius changed")
    purchase = purchase.replace(
        stock_purchase_search, nearby_purchase_search, 1
    )
    if purchase.count("$Poison_Check") != 1:
        raise ValueError("Stock equipment Poison_Check dispatch changed")
    purchase = purchase.replace(
        "$Poison_Check", "$Alchemist_Nearby_Poison_Check", 1
    )

    stock_poison_signature = (
        "Function Poison_Check (agent ThisAgent) is boolean"
    )
    if poison.count(stock_poison_signature) != 1:
        raise ValueError("Stock Poison_Check signature changed")
    poison = poison.replace(
        stock_poison_signature,
        "Function Alchemist_Nearby_Poison_Check (agent ThisAgent) is boolean",
        1,
    )
    stock_poison_search = (
        "\tSearch_Dist = $GetAttribute (ThisAgent, #ATTRIB_SightRange) * "
        "($GetAttribute (ThisAgent, #ATTRIB_Artifice) / 2);"
    )
    nearby_poison_search = "\tSearch_Dist = #Alchemist_Town_Shopping_Range;"
    if poison.count(stock_poison_search) != 1:
        raise ValueError("Stock poison Artifice search radius changed")
    poison = poison.replace(stock_poison_search, nearby_poison_search, 1)

    funded = build_alchemist_economy(stock_purchase_equipment).rstrip()
    if funded.count(stock_purchase_signature) != 1:
        raise ValueError("Private funded Purchase_Equipment signature changed")
    funded = funded.replace(
        stock_purchase_signature,
        "Function Alchemist_Funded_Resupply (agent ThisAgent) is boolean",
        1,
    )
    funded_begin = "Begin\n\t//See if ThisAgent can use Weapons"
    funded_gate = (
        "Begin\n"
        "\t// Keep distant bounty work ahead of incidental shopping. A funded\n"
        "\t// resupply uses the complete stock selector only after the hero has\n"
        "\t// accumulated a substantial purse.\n"
        "\tIf ($Total_Gold (ThisAgent) < #Alchemist_Funded_Resupply_Gold)\n"
        "\t\treturn False;\n\n"
        "\t//See if ThisAgent can use Weapons"
    )
    if funded.count(funded_begin) != 1:
        raise ValueError("Private funded Purchase_Equipment Begin changed")
    funded = funded.replace(funded_begin, funded_gate, 1)
    stock_potion_dispatch = "If ($Potion_Check (ThisAgent,shops))"
    funded_potion_dispatch = (
        "If (($GetAttribute (ThisAgent, #ATTRIB_NumHealingPotions) == 0) && "
        "$Potion_Check (ThisAgent,shops))"
    )
    if funded.count(stock_potion_dispatch) != 1:
        raise ValueError("Private funded Potion_Check dispatch changed")
    funded = funded.replace(
        stock_potion_dispatch, funded_potion_dispatch, 1
    )

    return purchase + "\n\n" + funded + "\n\n" + poison + "\n"


def build_alchemist_inventory(stock_inventory: Path) -> str:
    """Clone stock item dispatch and privatize four Alchemist potion spells."""
    source = stock_inventory.read_text(encoding="cp1252")
    boost = extract_gpl_function(source, "QItem_Stat_Boost")
    replacements = (
        (
            '$LearnSpell ( thisagent, "Strength_Potion", FALSE );',
            'If ( ThisAgent\'s "Title" == "Alchemist" )\n'
            f'\t\t\t\t$LearnSpell ( thisagent, "{ALCHEMIST_STRENGTH_ACTION_NAME}", FALSE );\n'
            "\t\t\tElse\n"
            '\t\t\t\t$LearnSpell ( thisagent, "Strength_Potion", FALSE );',
        ),
        (
            '$LearnSpell ( thisagent, "Shapeshift_Potion", FALSE );',
            'If ( ThisAgent\'s "Title" == "Alchemist" )\n'
            f'\t\t\t\t$LearnSpell ( thisagent, "{ALCHEMIST_SHAPESHIFT_ACTION_NAME}", FALSE );\n'
            "\t\t\tElse\n"
                '\t\t\t\t$LearnSpell ( thisagent, "Shapeshift_Potion", FALSE );',
        ),
        (
            '$LearnSpell ( thisagent, "Fire_Balm", FALSE );',
            'If ( ThisAgent\'s "Title" == "Alchemist" )\n'
            f'\t\t\t\t$LearnSpell ( thisagent, "{ALCHEMIST_FIRE_BALM_ACTION_NAME}", FALSE );\n'
            "\t\t\tElse\n"
            '\t\t\t\t$LearnSpell ( thisagent, "Fire_Balm", FALSE );',
        ),
        (
            '$LearnSpell ( thisagent, "Regeneration_Elixer", FALSE );',
            'If ( ThisAgent\'s "Title" == "Alchemist" )\n'
            f'\t\t\t\t$LearnSpell ( thisagent, "{ALCHEMIST_REGENERATION_ACTION_NAME}", FALSE );\n'
            "\t\t\tElse\n"
            '\t\t\t\t$LearnSpell ( thisagent, "Regeneration_Elixer", FALSE );',
        ),
    )
    for stock_line, private_branch in replacements:
        if boost.count(stock_line) != 1:
            raise ValueError(f"Stock QItem spell dispatch changed: {stock_line}")
        boost = boost.replace(stock_line, private_branch, 1)
    return boost + "\n"


def build_alchemist_combat_potions_xml(stock_actions: Path) -> bytes:
    """Private stock actions gated at Majesty's native losing-fight boundary."""
    stock_root = ET.parse(stock_actions).getroot()
    output = ET.Element("Majesty")
    specs = (
        (
            "Strength_Potion",
            ALCHEMIST_STRENGTH_ACTION_ID,
            ALCHEMIST_STRENGTH_ACTION_NAME,
            "Alchemist_Strength_Potion_Effect",
        ),
        (
            "Shapeshift_Potion",
            ALCHEMIST_SHAPESHIFT_ACTION_ID,
            ALCHEMIST_SHAPESHIFT_ACTION_NAME,
            "Alchemist_Shapeshift_Potion_Effect",
        ),
        (
            "Fire_Balm",
            ALCHEMIST_FIRE_BALM_ACTION_ID,
            ALCHEMIST_FIRE_BALM_ACTION_NAME,
            "Alchemist_Fire_Balm_Effect",
        ),
        (
            "Regeneration_Elixer",
            ALCHEMIST_REGENERATION_ACTION_ID,
            ALCHEMIST_REGENERATION_ACTION_NAME,
            "Alchemist_Regeneration_Elixer_Effect",
        ),
    )
    for stock_name, action_id, action_name, gpl_function in specs:
        source = stock_root.find(f'.//Description[@Name="{stock_name}"]')
        if source is None:
            raise ValueError(f"Stock Bazaar action is missing: {stock_name}")
        action = ET.fromstring(ET.tostring(source, encoding="utf-8"))
        action.set("ID", action_id)
        action.set("Name", action_name)
        script = action.find("./Engine/Script")
        game = action.find("./Game")
        validation = action.find("./Game/ValidationScript")
        if script is None or game is None:
            raise ValueError(f"Stock {stock_name} action contract changed")
        if stock_name in ("Strength_Potion", "Shapeshift_Potion"):
            if validation is None or validation.get("value") != "berserk_check":
                raise ValueError(f"Stock {stock_name} berserk-only contract changed")
        elif validation is not None:
            raise ValueError(f"Stock {stock_name} unexpectedly gained validation")
        script.set("GPLFunction", gpl_function)
        if validation is None:
            validation = ET.SubElement(game, "ValidationScript")
        validation.set("value", ALCHEMIST_CONSUMABLE_VALIDATION)
        output.append(action)
    ET.indent(output, space="\t")
    return ET.tostring(output, encoding="utf-8", xml_declaration=False) + b"\n"


def build_alchemist_strength_potion(stock_spells: Path) -> str:
    """Clone stock Strength Potion while consuming the private learned spell."""
    source = stock_spells.read_text(encoding="cp1252")
    effect = extract_gpl_function(source, "Strength_Potion_Effect")
    effect = effect.replace(
        "function Strength_potion_effect",
        "function Alchemist_Strength_Potion_Effect",
        1,
    )
    stock_spell = '"Strength_Potion"'
    if effect.count(stock_spell) != 2:
        raise ValueError("Stock Strength Potion spell-name contract changed")
    return effect.replace(stock_spell, f'"{ALCHEMIST_STRENGTH_ACTION_NAME}"') + "\n"


def build_alchemist_consumable_threat(
    stock_target_eval: Path, stock_spells: Path
) -> str:
    """Clone stock list_eval, then tune only its consumable-use boundary."""
    target_source = stock_target_eval.read_text(encoding="cp1252")
    evaluator = extract_gpl_function(target_source, "list_eval")
    if evaluator.count("function list_eval") != 1:
        raise ValueError("Stock list_eval signature changed")
    evaluator = evaluator.replace(
        "function list_eval", "function Alchemist_Base_List_Eval", 1
    )
    if evaluator.count("\tinteger spell_mod;") != 1:
        raise ValueError("Stock list_eval spell declaration changed")
    spell_line = "\tspell_mod = $spell_extra_value(thisagent);\n"
    if evaluator.count(spell_line) != 1:
        raise ValueError("Stock list_eval spell-confidence call changed")
    stock_return = "\treturn hitstildead - hitstokill + spell_mod;"
    if evaluator.count(stock_return) != 1:
        raise ValueError("Stock list_eval return changed")

    validation = f'''function {ALCHEMIST_CONSUMABLE_VALIDATION}(agent ThisAgent) is integer

declare
\tlist Threats;
\tagent Target;
\tinteger Base_Score;
\tinteger Spell_Score;

begin
\t// Use the encounter list already owned by stock eval_enemies_nearby. Reward
\t// targets have no Hostiles entry until contact, so the current target is the
\t// stock-shaped fallback.
\tThreats = ThisAgent's "Hostiles";
\tIf ($ListSize(Threats) == 0)
\t\tbegin
\t\t\tTarget = ThisAgent's "Target";
\t\t\tIf ($NotValid(Target))
\t\t\t\treturn 0;
\t\t\tIf (Target == ThisAgent)
\t\t\t\treturn 0;
\t\t\tThreats << Target;
\t\tend

\tBase_Score = $Alchemist_Base_List_Eval(ThisAgent, Threats);
\t// The stock evaluator counts every available spell at full flee-confidence
\t// weight. That is correct for retreat behavior, but the Alchemist's private
\t// 60 + 100 confidence made every finite combat flask invalid. Retain one
\t// quarter of that exact stock spell term for the consumable decision only:
\t// easy fights still get steel, while dangerous fights can spend a flask.
\tSpell_Score = $spell_extra_value(ThisAgent);
\tBase_Score -= (Spell_Score * 3) / 4;
\tIf (Base_Score < 1)
\t\treturn 1;
\treturn 0;
end'''

    spell_source = stock_spells.read_text(encoding="cp1252")
    effects: list[str] = []
    for stock_function, private_function, stock_spell_names, private_spell in (
        (
            "Fire_Balm_Effect",
            "Alchemist_Fire_Balm_Effect",
            ("Fire_Balm", "Fire_balm"),
            ALCHEMIST_FIRE_BALM_ACTION_NAME,
        ),
        (
            "Regeneration_Elixer_Effect",
            "Alchemist_Regeneration_Elixer_Effect",
            ("Regeneration_Elixer",),
            ALCHEMIST_REGENERATION_ACTION_NAME,
        ),
    ):
        effect = extract_gpl_function(spell_source, stock_function)
        signature = re.compile(
            rf"(?im)^function\s+{re.escape(stock_function)}\s*\("
        )
        if len(signature.findall(effect)) != 1:
            raise ValueError(f"Stock {stock_function} signature changed")
        effect = signature.sub(f"function {private_function}(", effect, count=1)
        expected_counts = {
            "Fire_Balm_Effect": (1, 1),
            "Regeneration_Elixer_Effect": (2,),
        }[stock_function]
        for stock_spell, expected_count in zip(stock_spell_names, expected_counts):
            quoted_stock = f'"{stock_spell}"'
            if effect.count(quoted_stock) != expected_count:
                raise ValueError(f"Stock {stock_function} spell-name contract changed")
            effect = effect.replace(quoted_stock, f'"{private_spell}"')
        effects.append(effect)

    return evaluator + "\n\n" + validation + "\n\n" + "\n\n".join(effects) + "\n"


def build_alchemist_shapeshift(stock_spells: Path) -> str:
    """Clone stock Shapeshift Potion with one Alchemist-only Spider branch."""
    source = stock_spells.read_text(encoding="cp1252")
    effect = extract_gpl_function(source, "Shapeshift_Potion_Effect")
    cleanup = extract_gpl_function(source, "Shapeshift_Potion_End")

    effect = effect.replace(
        "function Shapeshift_Potion_Effect",
        "function Alchemist_Shapeshift_Potion_Effect",
        1,
    )
    stock_spell = '"Shapeshift_Potion"'
    if effect.count(stock_spell) != 2:
        raise ValueError("Stock Shapeshift Potion spell-name contract changed")
    effect = effect.replace(stock_spell, f'"{ALCHEMIST_SHAPESHIFT_ACTION_NAME}"')

    effect_anchor = '\tif ( thisagent\'s "AttackType" == 2 )'
    if effect.count(effect_anchor) != 1:
        raise ValueError("Stock Shapeshift Potion form dispatch changed")
    spider_effect = (
        '\tif ( title == "Alchemist" )\n'
        "\t\tbegin // Alchemists become Giant Spiders.\n"
        '\t\t\t$ChangeUnitType ( thisagent, "Giant_Spider" );\n'
        "\t\t\t$adjustattribute ( thisagent, #ATTRIB_Armor_Basic_Damage, 5 );\n"
        "\t\t\t$MagicalAdjustAttribute ( thisagent, #ATTRIB_HtoH, 10 );\n"
        "\t\t\t$MagicalAdjustAttribute ( thisagent, #ATTRIB_Strength, 18 );\n"
        "\t\t\t$MagicalAdjustAttribute ( thisagent, #ATTRIB_Vitality, 15 );\n"
        "\t\t\t$adjustattribute ( thisagent, #ATTRIB_ActionRateModifier, -50 );\n"
        "\t\t\t$adjustattribute ( thisagent, #ATTRIB_MaxHP, 30 );\n"
        "\t\t\t$adjustattribute ( thisagent, #ATTRIB_HP, 30 );\n"
        "\t\tend\n"
        "\telse "
    )
    effect = effect.replace(effect_anchor, spider_effect + effect_anchor, 1)

    cleanup_anchor = '\tif ( thisagent\'s "AttackType" == 2 )'
    if cleanup.count(cleanup_anchor) != 1:
        raise ValueError("Stock Shapeshift Potion cleanup dispatch changed")
    spider_cleanup = (
        '\tif ( title == "Alchemist" )\n'
        "\t\tbegin // Revert from Giant Spider.\n"
        "\t\t\t$adjustattribute (thisagent, #ATTRIB_Armor_Basic_Damage, -5 );\n"
        "\t\t\t$MagicalAdjustAttribute ( thisagent, #ATTRIB_HtoH, -10 );\n"
        "\t\t\t$MagicalAdjustAttribute ( thisagent, #ATTRIB_Strength, -18 );\n"
        "\t\t\t$MagicalAdjustAttribute ( thisagent, #ATTRIB_Vitality, -15 );\n"
        "\t\t\t$adjustattribute ( thisagent, #ATTRIB_ActionRateModifier, 50 );\n"
        "\t\t\t$adjustattribute ( thisagent, #ATTRIB_MaxHP, -30 );\n"
        "\t\tend\n"
        "\telse "
    )
    cleanup = cleanup.replace(cleanup_anchor, spider_cleanup + cleanup_anchor, 1)
    return effect + "\n\n" + cleanup + "\n"


def build_gpl_project(include_siege_test_fixture: bool) -> str:
    sources = [
        'source="Alchemist_Rogue.gpl"',
        'source="Alchemist_Embassy.gpl"',
        'source="Alchemist_Guild_Title.gpl"',
        'source="Alchemist_Adopt.gpl"',
        'source="Alchemist_Magic_Bazaar.gpl"',
        'source="Alchemist_Nearby_Equipment.gpl"',
        'source="Alchemist_Inventory.gpl"',
        'source="Alchemist_Consumable_Threat.gpl"',
        'source="Alchemist_Strength_Potion.gpl"',
        'source="Alchemist_Shapeshift.gpl"',
        'source="Alchemist_Stun_Serum.gpl"',
        'source="Alchemist_Flash_Flask.gpl"',
        'source="Alchemist_Miasma_Mist.gpl"',
        'source="Alchemist_Brewing.gpl"',
        'source="Alchemist_Economy.gpl"',
        'source="Alchemist_Weapon_Oil.gpl"',
        'source="Alchemist_Combat_Oils.gpl"',
        'source="Alchemist_Damage.gpl"',
        'source="Alchemist_Phoenix_Phial.gpl"',
        'source="Alchemist_Reagents.gpl"',
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


def read_cam_sections(path: Path) -> tuple[CamSection, ...]:
    """Read every CAM section so a private record can be appended losslessly."""
    data = path.read_bytes()
    if data[: len(MAGIC)] != MAGIC:
        raise ValueError(f"Not a CYLBPC CAM archive: {path}")
    section_count = u32(data, 12)
    cursor = HEADER_SIZE
    directory: list[tuple[bytes, int]] = []
    for _ in range(section_count):
        directory.append((data[cursor : cursor + 4], u32(data, cursor + 4)))
        cursor += DIR_ENTRY_SIZE
    sections: list[CamSection] = []
    for extension, section_offset in directory:
        count = u32(data, section_offset)
        padding = data[section_offset + 4 : section_offset + SECTION_HEADER_SIZE]
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
        sections.append(CamSection(extension, tuple(entries), padding))
    return tuple(sections)


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


def install_paralytic_oil_restraint_image(game_data: Path, main_art: Path) -> None:
    """Append the private Vines-clone restraint to reused approved art."""
    stock = load_stock_pipeline(SOURCE_ROOT.parent)
    sections = list(read_cam_sections(main_art))
    imag_index = next(
        (index for index, section in enumerate(sections) if section.extension == b"IMAG"),
        None,
    )
    tile_index = next(
        (index for index, section in enumerate(sections) if section.extension == b"TILE"),
        None,
    )
    if imag_index is None or tile_index is None:
        raise ValueError("Alchemist main art lacks IMAG/TILE sections")
    existing = next(
        (
            entry
            for entry in sections[imag_index].entries
            if entry.name.startswith(PARALYTIC_OIL_RESTRAINT_CUSTOM[:4])
        ),
        None,
    )
    existing_private_indices: dict[bytes, int] = {}
    if existing is not None:
        existing_private_indices = {
            entry.name.rstrip(b"\x00"): index
            for index, entry in enumerate(sections[tile_index].entries)
            if entry.name.startswith(b"ASO3Bind")
        }
        private_indices = set(existing_private_indices.values())
        referenced_indices = {
            struct.unpack_from("<H", existing.data, offset)[0]
            for offset in range(0, len(existing.data) - 1, 2)
        }
        if len(private_indices) != 30 or not private_indices.issubset(referenced_indices):
            raise ValueError("Existing private Paralytic Oil restraint is malformed")

    source = game_data / "maindata.cam"
    palettes = stock.read_cam_entries(source, b"SPLT")
    source_imag = stock.read_cam_entry(source, b"IMAG", b"CRB1vines_e").data
    source_indices = tuple(range(2578, 2608))
    source_png = (
        SOURCE_ROOT.parent
        / "assets/source/effects/paralytic-oil/approved-restraint-master.png"
    )
    if not source_png.is_file():
        raise FileNotFoundError(source_png)
    output_tiles = list(sections[tile_index].entries)
    replacements: dict[int, int] = {}
    for frame, source_index in enumerate(source_indices):
        tile_name = f"ASO3Bind{frame:02d}".encode("ascii")
        rendered = CamEntry(
            pad_name(tile_name),
            generated_frost_armor_hold_tile(
                stock,
                palettes,
                source_png,
                PHOENIX_EFFECT_PALETTE,
                VINES_FIXED_HEADER,
                frame if source_index <= 2594 else None,
            ),
        )
        if existing is None:
            replacements[source_index] = len(output_tiles)
            output_tiles.append(rendered)
        else:
            output_index = existing_private_indices.get(tile_name)
            if output_index is None:
                raise ValueError(f"Existing Paralytic Oil TILE is missing: {tile_name!r}")
            replacements[source_index] = output_index
            output_tiles[output_index] = rendered
    private_imag = stock.remap_imag_low16_tile_indices(source_imag, replacements)
    section = sections[imag_index]
    if existing is None:
        image_entries = section.entries + (
            CamEntry(pad_name(PARALYTIC_OIL_RESTRAINT_CUSTOM), private_imag),
        )
    else:
        image_entries = tuple(
            CamEntry(entry.name, private_imag) if entry is existing else entry
            for entry in section.entries
        )
    sections[imag_index] = CamSection(
        section.extension,
        image_entries,
        section.padding,
    )
    tile_section = sections[tile_index]
    sections[tile_index] = CamSection(
        tile_section.extension,
        tuple(output_tiles),
        tile_section.padding,
    )
    write_cam(main_art, tuple(sections))


def install_refined_stun_serum_images(game_path: Path, main_art: Path) -> None:
    """Repaint private Stun art and preserve corrected effect attachment anchors."""
    stock = load_stock_pipeline(SOURCE_ROOT.parent)
    sections = list(read_cam_sections(main_art))
    imag_index = next(
        (index for index, section in enumerate(sections) if section.extension == b"IMAG"),
        None,
    )
    tile_index = next(
        (index for index, section in enumerate(sections) if section.extension == b"TILE"),
        None,
    )
    if imag_index is None or tile_index is None:
        raise ValueError("Alchemist main art lacks IMAG/TILE sections")
    image_entries = list(sections[imag_index].entries)
    output_tiles = list(sections[tile_index].entries)
    private_tile_indices = {
        entry.name.rstrip(b"\x00"): index
        for index, entry in enumerate(output_tiles)
        if entry.name.startswith((b"ASS1Impact", b"ASS2Bind"))
    }
    if len([name for name in private_tile_indices if name.startswith(b"ASS1Impact")]) != 6:
        raise ValueError("Existing private Stun Serum impact art is incomplete")
    if len([name for name in private_tile_indices if name.startswith(b"ASS2Bind")]) != 30:
        raise ValueError("Existing private Stun Serum restraint art is incomplete")

    flash_frames = 0
    old_flash_header = (3, 99, 103, 0, 32, 56, 43, 8)
    for index, entry in enumerate(output_tiles):
        if not entry.name.startswith(b"AFF2Flash"):
            continue
        header = struct.unpack_from("<8H", entry.data, 0)
        if header not in (old_flash_header, FLASH_FLASK_ACTIVATION_HEADER):
            raise ValueError("Existing Flash Flask frame has an unknown anchor")
        corrected = bytearray(entry.data)
        struct.pack_into("<8H", corrected, 0, *FLASH_FLASK_ACTIVATION_HEADER)
        output_tiles[index] = CamEntry(entry.name, bytes(corrected))
        flash_frames += 1
    if flash_frames != 6:
        raise ValueError("Existing private Flash Flask activation art is incomplete")

    data = game_path / "Data" / "maindata.cam"
    data_mx = game_path / "DataMX" / "mx_maindata.cam"
    palettes = stock.read_cam_entries(data, b"SPLT")
    impact_source = stock.read_cam_entry(
        data_mx,
        b"IMAG",
        b"XR30frost_fld_hit",
    ).data
    impact_source_indices = stock.animation_tile_indices(
        impact_source,
        len(stock.read_cam_entries(data_mx, b"TILE")),
    )
    if len(impact_source_indices) != 6:
        raise ValueError("Stock XR30 Stun impact topology changed")
    impact_png = SOURCE_ROOT.parent / "assets/source/spells/stun-serum/impact-strip.png"
    impact_phase_indices = (0, 1, 2, 3, 5, 7)
    impact_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(impact_source_indices):
        tile_name = f"ASS1Impact{frame:02d}".encode("ascii")
        output_index = private_tile_indices[tile_name]
        impact_replacements[source_index] = output_index
        output_tiles[output_index] = CamEntry(
            pad_name(tile_name),
            generated_discrete_strip_tile(
                stock,
                palettes,
                impact_png,
                8,
                impact_phase_indices[frame],
                PHOENIX_EFFECT_PALETTE,
                FLASH_FLASK_ACTIVATION_HEADER,
            ),
        )
    private_impact = stock.remap_imag_animation_tiles(
        impact_source,
        impact_replacements,
    )

    restraint_source = stock.read_cam_entry(data, b"IMAG", b"CRB1vines_e").data
    restraint_source_indices = tuple(range(2578, 2608))
    restraint_png = SOURCE_ROOT.parent / "assets/source/spells/stun-serum/restraint-strip.png"
    restraint_replacements: dict[int, int] = {}
    for frame, source_index in enumerate(restraint_source_indices):
        tile_name = f"ASS2Bind{frame:02d}".encode("ascii")
        output_index = private_tile_indices[tile_name]
        restraint_replacements[source_index] = output_index
        output_tiles[output_index] = CamEntry(
            pad_name(tile_name),
            generated_frost_armor_hold_tile(
                stock,
                palettes,
                restraint_png,
                PHOENIX_EFFECT_PALETTE,
                VINES_FIXED_HEADER,
                frame if source_index <= 2594 else None,
                source_frame_count=8,
                peak_frame_index=4,
            ),
        )
    private_restraint = stock.remap_imag_low16_tile_indices(
        restraint_source,
        restraint_replacements,
    )

    phoenix_frames = 0
    old_phoenix_header = (3, 99, 103, 0, 32, 56, 49, 8)
    for index, entry in enumerate(output_tiles):
        if not entry.name.startswith(b"PXE1Phoenix"):
            continue
        header = struct.unpack_from("<8H", entry.data, 0)
        if header not in (old_phoenix_header, PHOENIX_EFFECT_HEADER):
            raise ValueError("Existing private Phoenix frame has an unknown anchor")
        corrected = bytearray(entry.data)
        struct.pack_into("<8H", corrected, 0, *PHOENIX_EFFECT_HEADER)
        output_tiles[index] = CamEntry(entry.name, bytes(corrected))
        phoenix_frames += 1
    if phoenix_frames != PHOENIX_LIFECYCLE_FRAMES:
        raise ValueError("Existing private Phoenix lifecycle art is incomplete")

    replacements = {
        STUN_SERUM_IMPACT_CUSTOM[:4]: private_impact,
        STUN_SERUM_RESTRAINT_CUSTOM[:4]: private_restraint,
    }
    seen: set[bytes] = set()
    for index, entry in enumerate(image_entries):
        key = entry.name[:4]
        if key == FLASH_FLASK_ACTIVATION_CUSTOM[:4]:
            image_entries[index] = CamEntry(
                entry.name,
                set_single_overlay_animation_delay(
                    entry.data,
                    96,
                    (
                        FLASH_FLASK_ACTIVATION_SOURCE_DELAY_MS,
                        FLASH_FLASK_ACTIVATION_DELAY_MS,
                    ),
                    FLASH_FLASK_ACTIVATION_DELAY_MS,
                ),
            )
        if key in replacements:
            image_entries[index] = CamEntry(entry.name, replacements[key])
            seen.add(key)
    if seen != set(replacements):
        raise ValueError("Private Stun Serum IMAG records are missing")

    imag_section = sections[imag_index]
    sections[imag_index] = CamSection(
        imag_section.extension,
        tuple(image_entries),
        imag_section.padding,
    )
    tile_section = sections[tile_index]
    sections[tile_index] = CamSection(
        tile_section.extension,
        tuple(output_tiles),
        tile_section.padding,
    )
    write_cam(main_art, tuple(sections))


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
    alchemist.find("./Engine/DefaultSound").set("value", ALCHEMIST_HERO_SOUND)
    recruit_cost = alchemist.find("./Game/Cost")
    if recruit_cost is None:
        raise ValueError("Stock Cultist recruitment cost contract is missing")
    recruit_cost.set("value", ALCHEMIST_RECRUIT_COST)
    hero_help = alchemist.find("./Game/HelpID")
    if hero_help is None:
        raise ValueError("Stock Cultist help contract is missing")
    hero_help.set("value", ALCHEMIST_HERO_HELP_ID)
    name_generator = alchemist.find("./Game/NameGenType")
    if name_generator is None:
        raise ValueError("Stock Cultist name-generator contract is missing")
    name_generator.set("value", ALCHEMIST_NAME_GENERATOR_ID)
    movement = alchemist.find('./Engine/Attachment[@kind="Movement"]')
    if movement is None:
        raise ValueError("Stock Cultist movement attachment is missing")
    # The private IMAG is a literal Warrior animation/timing clone, so retain
    # Warrior's matching stock movement class rather than Cultist Class 3.
    movement.set("ID", "Class 1")
    # Speed is Majesty's AI-facing chase/escape rating, not world movement.
    # Actual movement is the Haunt-proven one-time MovementRateModifier in GPL.
    speed = alchemist.find("./Game/Speed")
    if speed is None:
        raise ValueError("Stock Cultist Speed contract is missing")
    speed.set("value", "2")
    # User-approved Alchemist balance line. Preserve the Cultist character
    # schema and change only these explicit numeric gameplay values.
    balance_values = {
        "Vitality": "11",
        "Intelligence": "18",
        "Artifice": "20",
        "Attack": "45",
        "Parry": "35",
        "Dodge": "40",
        "WeaponBasicDamage": "6",
    }
    for field_name, field_value in balance_values.items():
        field = alchemist.find(f"./Game/{field_name}")
        if field is None:
            raise ValueError(f"Stock Cultist {field_name} contract is missing")
        field.set("value", field_value)
    # Do not inherit the Cultist's class-local spell surface. Replace its three
    # spells with the Alchemist's one private Shield-of-Light-derived combat
    # spells, preserving the stock AllowedSpells dispatch contract. Paralytic
    # Gaze's rank-5 Stun Serum precedes the rank-1 Flash Flask at combat entry.
    allowed_spells = alchemist.find("./Game/AllowedSpells")
    if allowed_spells is None:
        raise ValueError("Stock Cultist AllowedSpells contract is missing")
    for inherited_spell in list(allowed_spells):
        allowed_spells.remove(inherited_spell)
    ET.SubElement(
        allowed_spells,
        "Spell",
        {"ID": "0", "Value": STUN_SERUM_ACTION_NAME},
    )
    ET.SubElement(
        allowed_spells,
        "Spell",
        {"ID": "1", "Value": FLASH_FLASK_ACTION_NAME},
    )
    ET.SubElement(
        allowed_spells,
        "Spell",
        {"ID": "2", "Value": MIASMA_MIST_ACTION_NAME},
    )
    # Warrior's direct bladed-melee contract is attacktype 1 (in GPL),
    # attack_action basic_attack (in GPL), and a 1..1 engine attack range.
    # ALC1 already clones Warrior's Attack animation/timing table.
    attack_range = alchemist.find("./Game/AttackRange")
    if attack_range is None:
        raise ValueError("Stock Cultist AttackRange contract is missing")
    attack_range.set("min", "1")
    attack_range.set("max", "1")
    output.append(alchemist)
    stock_lightning_storm = character_root.find(
        './/Description[@Name="lightning_storm"]'
    )
    if stock_lightning_storm is None:
        raise ValueError("Stock Lightning Storm spell-unit description is missing")
    for unit_id, unit_name, script_name, description, default_sound in (
        (
            "ALS1",
            "philosophers_stone",
            "Philosophers_Stone_Hit",
            "Philosopher's Stone",
            "0",
        ),
    ):
        spell_unit = ET.fromstring(
            ET.tostring(stock_lightning_storm, encoding="utf-8")
        )
        spell_unit.set("ID", unit_id)
        spell_unit.set("Name", unit_name)
        spell_unit.set("Description", description)
        spell_unit.find("./Engine/ImageIDBase").set("value", "AMm6")
        spell_unit.find("./Engine/DefaultSound").set("value", default_sound)
        spell_unit.find("./Engine/Script").set("GPLFunction", script_name)
        output.append(spell_unit)
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
        description.find("./Engine/DefaultSound").set("value", ALCHEMIST_LAB_SOUND)
        dialog = description.find("./Game/DialogID")
        if dialog is None:
            raise ValueError(f"{source_name} has no DialogID")
        dialog.set("value", DIALOG_ID.decode("ascii"))
        building_help = description.find("./Game/HelpID")
        if building_help is None:
            raise ValueError(f"{source_name} has no HelpID")
        building_help.set("value", ALCHEMIST_BUILDING_HELP_IDS[level])
        building_cost = description.find("./Game/Cost")
        if building_cost is None:
            raise ValueError(f"{source_name} has no Cost")
        building_cost.set("value", ALCHEMIST_BUILDING_COSTS[level])
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


def build_brewing_overlays_xml(
    stock_overlays_xml: Path,
    stock_mx_overlays_xml: Path,
) -> bytes:
    stock_root = ET.parse(stock_overlays_xml).getroot()
    stock_mx_root = ET.parse(stock_mx_overlays_xml).getroot()
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
    image.set("value", VIGOR_EFFECT_CUSTOM[:4].decode("ascii"))
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
    resurrection_image = resurrection.find("./Engine/ImageIDBase")
    resurrection_script = resurrection.find("./Engine/Script")
    resurrection_engine = resurrection.find("./Engine")
    if (
        resurrection_image is None
        or resurrection_script is None
        or resurrection_engine is None
    ):
        raise ValueError("Stock resurrection effector visual/callback contract is missing")
    resurrection_image.set("value", "PXE1")
    attachment = resurrection_engine.find("./AttachmentPointID")
    if attachment is None:
        attachment = ET.SubElement(
            resurrection_engine, "AttachmentPointID", {"value": "2"}
        )
    else:
        attachment.set("value", "2")
    resurrection_script.set("GPLFunction", "Phoenix_Phial_Resurrection_End")
    output.append(resurrection)

    # The Stone's selected monster dies in the same callback, so its one-shot
    # visual must be owned by Lightning Storm's surviving spell unit. Clone
    # Got_Gold's literal position-owned overlay presenter and replace only its
    # private identity, art, and silent sound reference. The private IMAG still
    # retains Gravechill's approved six-frame XR30 animation topology.
    stone_source = stock_root.find('.//Description[@Name="Got_Gold"]')
    if stone_source is None:
        raise ValueError("Stock Got_Gold position overlay is missing")
    stone = ET.fromstring(ET.tostring(stone_source, encoding="utf-8"))
    stone.set("ID", "AST1")
    stone.set("Name", "philosophers_stone_hit_effector")
    stone.set("Description", "Philosopher's Stone Transmutation")
    stone.find("./Engine/ImageIDBase").set(
        "value", PHILOSOPHERS_STONE_HIT_CUSTOM[:4].decode("ascii")
    )
    stone.find("./Engine/DefaultSound").set("value", "0")
    output.append(stone)

    # Arcane Infusion is a successful one-shot event on the selected
    # Laboratory. Stock building income creates got_gold_bldg directly on its
    # exact building owner, so clone that literal presenter and replace only
    # identity/art/sound. Its private IMAG owns HRC1's 29-frame lifetime.
    infusion_source = stock_root.find('.//Description[@Name="got_gold_bldg"]')
    if infusion_source is None:
        raise ValueError("Stock got_gold_bldg position overlay is missing")
    infusion = ET.fromstring(ET.tostring(infusion_source, encoding="utf-8"))
    infusion.set("ID", "AIF1")
    infusion.set("Name", "alchemist_arcane_infusion_effector")
    infusion.set("Description", "Arcane Infusion")
    infusion.find("./Engine/ImageIDBase").set(
        "value", ARCANE_INFUSION_EFFECT_CUSTOM[:4].decode("ascii")
    )
    infusion.find("./Engine/DefaultSound").set("value", "0")
    output.append(infusion)

    # Vigor is issued by the selected Laboratory through the same stock Rage
    # command owner. Present its successful activation with the same literal
    # got_gold_bldg building-owned one-shot and distinct private artwork.
    vigor_activation = ET.fromstring(
        ET.tostring(infusion_source, encoding="utf-8")
    )
    vigor_activation.set("ID", "AIV1")
    vigor_activation.set("Name", "alchemist_vigor_activation_effector")
    vigor_activation.set("Description", "Vigor Elixir Activation")
    vigor_activation.find("./Engine/ImageIDBase").set(
        "value", VIGOR_ACTIVATION_EFFECT_CUSTOM[:4].decode("ascii")
    )
    vigor_activation.find("./Engine/DefaultSound").set("value", "0")
    output.append(vigor_activation)

    # Wizard Guild Supercharge is the exact stock root-owned, directionless
    # persistent spell loop shown above a charged guild.  Clone its complete
    # overlay contract; only privatize identity/art and silence the one-time
    # Supercharge sound because this indicator can start from ordinary reagent
    # deposits and save initialization.
    ready_source = stock_root.find(
        './/Description[@Name="super_charge_effector"]'
    )
    if ready_source is None:
        raise ValueError("Stock Wizard Guild Supercharge overlay is missing")
    ready = ET.fromstring(ET.tostring(ready_source, encoding="utf-8"))
    ready.set("ID", "ARR1")
    ready.set("Name", "alchemist_reagent_ready_effector")
    ready.set("Description", "Laboratory Reagents Ready")
    ready_image = ready.find("./Engine/ImageIDBase")
    ready_sound = ready.find("./Engine/DefaultSound")
    if (
        ready_image is None
        or ready_sound is None
        or ready.find('./Engine/Info[@value="Directionless"]') is None
        or ready.find("./Engine/AttachmentPointID") is not None
        or ready.find("./Game/StackPriority") is None
        or ready.find("./Game/StackPriority").get("value") != "0"
    ):
        raise ValueError("Stock Wizard Guild Supercharge contract changed")
    ready_image.set("value", REAGENT_READY_CUSTOM[:4].decode("ascii"))
    ready_sound.set("value", "0")
    output.append(ready)

    # Oil ownership is permanent and multi-owner. Vines supplies the exact
    # non-Static, invisible Menu-11 presenter contract, while Charm proves the
    # same non-Static ownership shape is valid for multiple Infinite effectors.
    # ALo3 remains description-only so old saves containing the retired poison
    # presenter can resolve it; no new GPL path creates it or exposes its row.
    status_source = stock_root.find(
        './/Description[@ID="CRB2"][@Name="vines_icon"]'
    )
    if status_source is None:
        raise ValueError("Stock Vines invisible presenter is missing")
    charm_source = stock_root.find(
        './/Description[@ID="QRb1"][@Name="charm_icon"]'
    )
    if charm_source is None:
        raise ValueError("Stock Charm multi-owner presenter is missing")
    speed_icon_source = stock_mx_root.find(
        './/Description[@ID="XR01"][@Name="Speed_Tonic_Icon"]'
    )
    if speed_icon_source is None:
        raise ValueError("Stock Speed Tonic status art is missing")
    status_image = status_source.find("./Engine/ImageIDBase")
    status_menu = status_source.find("./Engine/Menu")
    if (
        status_source.find("./Engine") is None
        or status_image is None
        or status_image.get("value") != "CRB2"
        or status_menu is None
        or status_menu.get("value") != "11"
        or status_source.find('./Engine/Info[@value="Static"]') is not None
        or status_source.find('./Engine/Info[@value="NotVisibleInISOView"]') is None
        or status_source.find("./Game") is None
        or status_source.find("./Game/StackPriority").get("value") != "0"
        or status_source.find("./Engine/Script") is not None
        or charm_source.find('./Engine/Info[@value="Static"]') is not None
        or charm_source.find("./Engine/Menu").get("value") != "11"
        or charm_source.find("./Engine/Script") is not None
    ):
        raise ValueError("Stock Vines/Charm presenter contract changed")
    for status_id, status_name, description in (
        (
            PARALYTIC_OIL_STATUS_ID,
            PARALYTIC_OIL_STATUS_NAME,
            "Paralytic Weapon Oil",
        ),
        (
            TRANSMUTATION_OIL_STATUS_ID,
            TRANSMUTATION_OIL_STATUS_NAME,
            "Transmutation Weapon Oil",
        ),
        (
            POISONED_WEAPON_STATUS_ID,
            POISONED_WEAPON_STATUS_NAME,
            "Poisoned Weapon",
        ),
    ):
        status = ET.fromstring(ET.tostring(status_source, encoding="utf-8"))
        status.set("ID", status_id)
        status.set("Name", status_name)
        status.set("Description", description)
        status_engine = status.find("./Engine")
        status_engine.find("./ImageIDBase").set("value", "XR01")
        output.append(status)
    ET.indent(output, space="\t")
    return ET.tostring(output, encoding="utf-8", xml_declaration=False) + b"\n"


def build_flash_flask_xml(stock_actions_xml: Path, stock_overlays_xml: Path) -> bytes:
    """Privatize Shield of Light's full action/effector lifecycle."""
    actions_root = ET.parse(stock_actions_xml).getroot()
    overlays_root = ET.parse(stock_overlays_xml).getroot()
    stock_action = actions_root.find('.//Description[@Name="shield_of_light"]')
    stock_icon = overlays_root.find('.//Description[@Name="shield_of_light_icon"]')
    stock_effect = overlays_root.find('.//Description[@Name="shield_of_light_effector"]')
    if stock_action is None or stock_icon is None or stock_effect is None:
        raise ValueError("Stock Shield of Light lifecycle is incomplete")

    action = ET.fromstring(ET.tostring(stock_action, encoding="utf-8"))
    action.set("ID", FLASH_FLASK_ACTION_ID)
    action.set("Name", FLASH_FLASK_ACTION_NAME)
    action.set("Description", "Flash Flask")
    action.find("./Engine/ImageSet").set("value", "Special")
    # Stock healing potions play Drink_Potion from the duration-0 visual
    # effector, not from their action. Preserve that ownership exactly so the
    # cork pop occurs once when Flash Flask activates.
    action_engine = action.find("./Engine")
    for inherited_sound in (
        action_engine.find("./Sound"),
        action_engine.find("./SoundPhase"),
    ):
        if inherited_sound is not None:
            action_engine.remove(inherited_sound)
    action.find("./Engine/Script").set(
        "GPLFunction", "Alchemist_Flash_Flask_Begin"
    )
    action.find("./Game/EffectorDuration").set("value", FLASH_FLASK_DURATION_MS)
    action.find("./Game/TimeoutDuration").set("value", FLASH_FLASK_COOLDOWN_MS)
    action.find("./Game/CharacterLevel").set("value", "3")
    # Stock getbestspell orders combat buffs by SpellRank.  Stun Serum remains
    # rank 5; rank 4 places Flash Flask immediately after it and before the
    # native Bazaar attack potions (Fire Balm 3, Shapeshift 2, others 1).
    action.find("./Game/SpellRank").set("value", "4")

    icon = ET.fromstring(ET.tostring(stock_icon, encoding="utf-8"))
    icon.set("ID", FLASH_FLASK_ICON_ID)
    icon.set("Name", "alchemist_flash_flask_icon")
    icon.set("Description", "Flash Flask")
    icon.find("./Engine/ImageIDBase").set(
        "value", FLASH_FLASK_BUFF_CUSTOM[:4].decode("ascii")
    )
    icon.find("./Engine/Script").set(
        "GPLFunction", "Alchemist_Flash_Flask_End"
    )

    effect = ET.fromstring(ET.tostring(stock_effect, encoding="utf-8"))
    effect.set("ID", FLASH_FLASK_EFFECT_ID)
    effect.set("Name", "alchemist_flash_flask_effector")
    effect.set("Description", "Flash Flask")
    effect.find("./Engine/ImageIDBase").set(
        "value", FLASH_FLASK_ACTIVATION_CUSTOM[:4].decode("ascii")
    )
    effect.find("./Engine/DefaultSound").set("value", "Drink_Potion")

    output = ET.Element("Majesty")
    output.extend((action, icon, effect))
    ET.indent(output, space="\t")
    return ET.tostring(output, encoding="utf-8", xml_declaration=False) + b"\n"


def build_stun_serum_xml(stock_actions_xml: Path, stock_overlays_xml: Path) -> bytes:
    """Privatize stock Paralytic Gaze/Vines freeze ownership for Stun Serum."""
    actions_root = ET.parse(stock_actions_xml).getroot()
    overlays_root = ET.parse(stock_overlays_xml).getroot()
    stock_action = actions_root.find('.//Description[@Name="paralytic_gaze"]')
    stock_impact = overlays_root.find(
        './/Description[@Name="paralytic_gaze_effector"]'
    )
    stock_restraint = overlays_root.find('.//Description[@Name="vines_effector"]')
    stock_invisible_icon = overlays_root.find('.//Description[@Name="vines_icon"]')
    if any(
        item is None
        for item in (
            stock_action,
            stock_impact,
            stock_restraint,
            stock_invisible_icon,
        )
    ):
        raise ValueError("Stock Stun Serum action/freeze/art lifecycle is incomplete")

    action = ET.fromstring(ET.tostring(stock_action, encoding="utf-8"))
    action.set("ID", STUN_SERUM_ACTION_ID)
    action.set("Name", STUN_SERUM_ACTION_NAME)
    action.set("Description", "Stun Serum")
    # The stock action Begin phase owns cast-timing audio. Use it for the voice;
    # the private GPL impact callback plays the bottle break on the target.
    action.find("./Engine/Sound").set("value", ALCHEMIST_CAST_VOICE_SOUND)
    action.find("./Engine/Script").set("GPLFunction", "Alchemist_Stun_Serum_Begin")
    action.find("./Game/EffectorDuration").set("value", STUN_SERUM_DURATION_MS)
    action.find("./Game/TimeoutDuration").set("value", STUN_SERUM_COOLDOWN_MS)
    validation = action.find("./Game/ValidationScript")
    if validation is None:
        validation = ET.SubElement(action.find("./Game"), "ValidationScript")
    validation.set("value", "Alchemist_Stun_Serum_Check")
    level = action.find("./Game/CharacterLevel")
    if level is None:
        level = ET.SubElement(action.find("./Game"), "CharacterLevel")
    level.set("value", "5")

    impact = ET.fromstring(ET.tostring(stock_impact, encoding="utf-8"))
    impact.set("ID", STUN_SERUM_IMPACT_ID)
    impact.set("Name", "alchemist_stun_serum_impact")
    impact.set("Description", "Stun Serum Impact")
    impact.find("./Engine/ImageIDBase").set(
        "value", STUN_SERUM_IMPACT_CUSTOM[:4].decode("ascii")
    )

    restraint = ET.fromstring(ET.tostring(stock_restraint, encoding="utf-8"))
    restraint.set("ID", STUN_SERUM_RESTRAINT_ID)
    restraint.set("Name", "alchemist_stun_serum_restraint")
    restraint.set("Description", "Stun Serum Restraint")
    restraint.find("./Engine/ImageIDBase").set(
        "value", STUN_SERUM_RESTRAINT_CUSTOM[:4].decode("ascii")
    )
    restraint.find("./Engine/DefaultSound").set("value", "0")
    restraint_script = restraint.find("./Engine/Script")
    if restraint_script is None:
        raise ValueError("Stock Vines restraint lost its cleanup callback")
    restraint_script.set("GPLFunction", "Alchemist_Stun_Serum_End")

    oil_restraint = ET.fromstring(ET.tostring(stock_restraint, encoding="utf-8"))
    oil_restraint.set("ID", "ASO1")
    oil_restraint.set("Name", "alchemist_paralytic_oil_restraint")
    oil_restraint.set("Description", "Paralytic Oil")
    oil_restraint.find("./Engine/ImageIDBase").set(
        "value", PARALYTIC_OIL_RESTRAINT_CUSTOM[:4].decode("ascii")
    )
    oil_restraint.find("./Engine/DefaultSound").set("value", "0")
    oil_restraint_script = oil_restraint.find("./Engine/Script")
    if oil_restraint_script is None:
        raise ValueError("Stock Vines restraint lost its cleanup callback")
    oil_restraint_script.set("GPLFunction", "Alchemy_Paralytic_Oil_End")

    immunity = ET.fromstring(ET.tostring(stock_invisible_icon, encoding="utf-8"))
    immunity.set("ID", "ASO2")
    immunity.set("Name", "alchemist_paralytic_oil_immunity")
    immunity.set("Description", "Paralytic Oil Immunity")
    ET.SubElement(
        immunity.find("./Engine"),
        "Script",
        {
            "type": "0",
            "cProc": "0",
            "GPLFunction": "Alchemy_Paralytic_Oil_Immunity_End",
        },
    )

    output = ET.Element("Majesty")
    output.extend((action, impact, restraint, oil_restraint, immunity))
    ET.indent(output, space="\t")
    return ET.tostring(output, encoding="utf-8", xml_declaration=False) + b"\n"


def build_miasma_mist_xml(
    stock_actions_xml: Path,
    stock_characters_xml: Path,
    stock_projectiles_xml: Path,
    stock_overlays_xml: Path,
    stock_particles_xml: Path,
) -> bytes:
    """Privatize Meteor Storm/Endless Winter's complete area-spell contract."""
    actions_root = ET.parse(stock_actions_xml).getroot()
    characters_root = ET.parse(stock_characters_xml).getroot()
    projectiles_root = ET.parse(stock_projectiles_xml).getroot()
    overlays_root = ET.parse(stock_overlays_xml).getroot()
    particles_root = ET.parse(stock_particles_xml).getroot()

    stock_action = actions_root.find('.//Description[@Name="meteor_storm"]')
    stock_unit = characters_root.find('.//Description[@Name="meteor_storm"]')
    stock_missile = projectiles_root.find(
        './/Description[@Name="meteor_storm_missile"]'
    )
    stock_cloud = overlays_root.find(
        './/Description[@Name="meteor_storm_effector2"]'
    )
    stock_icon = overlays_root.find('.//Description[@Name="Poison_icon"]')
    stock_particle = particles_root.find(
        './/Description[@Name="Meteor_Storm_attachment"]'
    )
    if any(
        item is None
        for item in (
            stock_action,
            stock_unit,
            stock_missile,
            stock_cloud,
            stock_icon,
            stock_particle,
        )
    ):
        raise ValueError("Stock Meteor Storm/Poison presentation contract is incomplete")

    action = ET.fromstring(ET.tostring(stock_action, encoding="utf-8"))
    action.set("ID", MIASMA_MIST_ACTION_ID)
    action.set("Name", MIASMA_MIST_ACTION_NAME)
    action.set("Description", "Miasma Mist")
    action_engine = action.find("./Engine")
    ET.SubElement(action_engine, "Sound", {"value": ALCHEMIST_CAST_VOICE_SOUND})
    ET.SubElement(action_engine, "SoundPhase", {"begin": "Begin"})
    action.find("./Engine/Script").set(
        "GPLFunction", "Alchemist_Miasma_Mist_Hit"
    )
    action.find("./Game/EffectorDuration").set("value", MIASMA_MIST_DURATION_MS)
    action.find("./Game/TimeoutDuration").set("value", MIASMA_MIST_COOLDOWN_MS)
    action.find("./Game/CharacterLevel").set("value", "8")
    # Stun Serum rank 5 must remain the first combat-start spell. Rank 4 keeps
    # Miasma beside Flash Flask and above every native Bazaar flask.
    action.find("./Game/SpellRank").set("value", "4")
    validation = action.find("./Game/ValidationScript")
    if validation is None:
        validation = ET.SubElement(action.find("./Game"), "ValidationScript")
    validation.set("value", "Alchemist_Miasma_Mist_Check")

    unit = ET.fromstring(ET.tostring(stock_unit, encoding="utf-8"))
    unit.set("ID", MIASMA_MIST_CLOUD_UNIT_ID)
    unit.set("Name", "miasma_mist_cloud")
    unit.set("Description", "Miasma Mist")
    unit.find("./Engine/ImageIDBase").set("value", "AMm6")
    unit.find("./Engine/Script").set(
        "GPLFunction", "Alchemist_Miasma_Mist_Unit_Created"
    )

    missile = ET.fromstring(ET.tostring(stock_missile, encoding="utf-8"))
    missile.set("ID", MIASMA_MIST_MISSILE_ID)
    missile.set("Name", "miasma_mist_missile")
    missile.set("Description", "Miasma Mist")
    missile.find("./Engine/ImageIDBase").set("value", "AMm2")
    missile.find("./Engine/Script").set(
        "GPLFunction", "Alchemist_Miasma_Mist_Missile_Hit"
    )

    cloud = ET.fromstring(ET.tostring(stock_cloud, encoding="utf-8"))
    cloud.set("ID", MIASMA_MIST_CLOUD_OVERLAY_ID)
    cloud.set("Name", "miasma_mist_cloud_effector")
    cloud.set("Description", "Miasma Mist")
    cloud.find("./Engine/ImageIDBase").set("value", "AMm1")
    attachment = cloud.find("./Engine/AttachmentPointID")
    if attachment is None:
        attachment = ET.SubElement(cloud.find("./Engine"), "AttachmentPointID")
    attachment.set("value", "2")

    icon = ET.fromstring(ET.tostring(stock_icon, encoding="utf-8"))
    icon.set("ID", MIASMA_MIST_DEBUFF_ID)
    icon.set("Name", "miasma_mist_debuff_icon")
    icon.set("Description", "Miasma Mist")
    icon.find("./Engine/ImageIDBase").set("value", "AMm5")

    particle = ET.fromstring(ET.tostring(stock_particle, encoding="utf-8"))
    particle.set("ID", MIASMA_MIST_PARTICLE_ID)
    particle.set("Name", "miasma_mist_cloud_attachment")
    particle.set("Description", "Miasma Mist")
    particle.find("./Engine/ImageIDBase").set("value", "AMm4")

    output = ET.Element("Majesty")
    output.extend(
        (
            action,
            unit,
            missile,
            cloud,
            icon,
            particle,
        )
    )
    ET.indent(output, space="\t")
    return ET.tostring(output, encoding="utf-8", xml_declaration=False) + b"\n"


def build_brewing_sounds_xml(stock_sounds_xml: Path) -> bytes:
    stock_root = ET.parse(stock_sounds_xml).getroot()
    source = stock_root.find('.//Description[@Name="Drink_Potion"]')
    if source is None:
        raise ValueError("Stock Drink_Potion sound is missing")
    sound = ET.fromstring(ET.tostring(source, encoding="utf-8"))
    sound.set("ID", ALCHEMIST_VIGOR_SOUND_ID.decode("ascii"))
    sound.set("Name", ALCHEMIST_VIGOR_SOUND)
    phase = sound.find('./Engine/Phase[@ID="Effector Begin"]')
    if phase is None or phase.find("./Wave") is None:
        raise ValueError("Stock Drink_Potion sound contract changed")
    output = ET.Element("Majesty")
    output.append(sound)

    # One private spell sound, cloned from Shield of Light's Begin/Spell_Group
    # contract, is shared by both thrown-flask actions.
    spell_source = stock_root.find('.//Description[@Name="Shield_of_Light"]')
    if spell_source is None:
        raise ValueError("Stock Shield_of_Light sound is missing")
    bottle_break = ET.fromstring(ET.tostring(spell_source, encoding="utf-8"))
    bottle_break.set("ID", ALCHEMIST_BOTTLE_BREAK_SOUND_ID.decode("ascii"))
    bottle_break.set("Name", ALCHEMIST_BOTTLE_BREAK_SOUND)
    bottle_phase = bottle_break.find('./Engine/Phase[@ID="Begin"]')
    if bottle_phase is None or bottle_phase.find("./Wave") is None:
        raise ValueError("Stock Shield_of_Light Begin sound contract changed")
    bottle_phase.find("./Wave").set(
        "value", ALCHEMIST_BOTTLE_BREAK_WAVE_ID.decode("ascii")
    )
    output.append(bottle_break)

    # The Laboratory retains every Fervus building sound phase except Select.
    # Only the selected wave is privatized to the approved bubbling/glass cue.
    lab_source = stock_root.find('.//Description[@Name="FervisTemple"]')
    if lab_source is None:
        raise ValueError("Stock FervisTemple sound is missing")
    lab_sound = ET.fromstring(ET.tostring(lab_source, encoding="utf-8"))
    lab_sound.set("ID", ALCHEMIST_LAB_SOUND_ID.decode("ascii"))
    lab_sound.set("Name", ALCHEMIST_LAB_SOUND)
    lab_phase = lab_sound.find('./Engine/Phase[@ID="Select"]')
    if lab_phase is None or lab_phase.find("./Wave") is None:
        raise ValueError("Stock FervisTemple Select sound contract changed")
    lab_phase.find("./Wave").set("value", ALCHEMIST_LAB_WAVE_ID.decode("ascii"))
    output.append(lab_sound)

    # Cultist is the exact stock event surface needed here: it owns every
    # approved personality phase except casting. Keeping cast out of the hero
    # descriptor prevents Flash Flask from speaking through stock Cast.gpl.
    hero_source = stock_root.find('.//Description[@Name="Cultist"]')
    if hero_source is None:
        raise ValueError("Stock Cultist sound is missing")
    hero_sound = ET.fromstring(ET.tostring(hero_source, encoding="utf-8"))
    hero_sound.set("ID", ALCHEMIST_HERO_SOUND_ID.decode("ascii"))
    hero_sound.set("Name", ALCHEMIST_HERO_SOUND)
    for phase_name, _source_wave, private_wave in ALCHEMIST_HERO_VOICE_PHASES:
        voice_phase = hero_sound.find(f'./Engine/Phase[@ID="{phase_name}"]/Wave')
        if voice_phase is None:
            raise ValueError(f"Stock Cultist voice phase is missing: {phase_name}")
        voice_phase.set("value", private_wave.decode("ascii"))
    attack_phase = hero_sound.find('./Engine/Phase[@ID="Attack"]')
    if attack_phase is None or attack_phase.find("./Wave") is None:
        raise ValueError("Stock Cultist Attack sound contract changed")
    attack_phase.find("./Wave").set("value", "WU03")
    output.append(hero_sound)

    # Majesty has no per-class recruitment phase, and the common Cast helper
    # always asks the unit's default sound for VFX_CAST_SPELL1. Follow Haunt's
    # proven single-phase Rage clone instead: recruitment is called once from
    # birth, while the stock Cast clone voices only the two thrown-bottle spells.
    begin_source = stock_root.find('.//Description[@Name="Rage_of_Krolm"]')
    if begin_source is None:
        raise ValueError("Stock Rage_of_Krolm sound is missing")
    for sound_id, sound_name, wave_id, group_name in (
        (
            ALCHEMIST_CAST_VOICE_SOUND_ID,
            ALCHEMIST_CAST_VOICE_SOUND,
            b"AHC2",
            "Hero_Cast_Voice_Group",
        ),
        (
            ALCHEMIST_HIRED_VOICE_SOUND_ID,
            ALCHEMIST_HIRED_VOICE_SOUND,
            b"AHS1",
            "Voice_Special_1_Group",
        ),
    ):
        private_sound = ET.fromstring(ET.tostring(begin_source, encoding="utf-8"))
        private_sound.set("ID", sound_id.decode("ascii"))
        private_sound.set("Name", sound_name)
        private_phase = private_sound.find('./Engine/Phase[@ID="Begin"]')
        if private_phase is None or private_phase.find("./Wave") is None:
            raise ValueError("Stock Rage_of_Krolm Begin sound contract changed")
        private_phase.find("./Wave").set("value", wave_id.decode("ascii"))
        distance = private_phase.find("./DistanceModifier")
        if distance is not None:
            private_phase.remove(distance)
        ET.SubElement(private_phase, "Group", {"value": group_name})
        output.append(private_sound)
    ET.indent(output, space="\t")
    return ET.tostring(output, encoding="utf-8", xml_declaration=False) + b"\n"


def validate_game_wave(payload: bytes, label: str) -> None:
    with wave.open(io.BytesIO(payload), "rb") as source:
        if source.getnchannels() != 1:
            raise ValueError(f"{label} must be mono")
        if source.getsampwidth() != 2:
            raise ValueError(f"{label} must use signed 16-bit PCM")
        if source.getframerate() != 22050:
            raise ValueError(f"{label} must use a 22050 Hz sample rate")
        if source.getcomptype() != "NONE":
            raise ValueError(f"{label} must use uncompressed PCM")
        if source.getnframes() == 0:
            raise ValueError(f"{label} contains no audio frames")


def write_alchemist_audio_cam(audio_root: Path, output_path: Path) -> None:
    inputs = [
        (
            ALCHEMIST_BOTTLE_BREAK_WAVE_ID,
            b"Flask Break",
            audio_root / "alchemist-bottle-break-game.wav",
        ),
        (
            ALCHEMIST_LAB_WAVE_ID,
            b"Lab Select",
            audio_root / "alchemist-laboratory-select-game.wav",
        ),
    ]
    inputs.extend(
        (
            wave_id,
            description,
            audio_root / f"alchemist-{event}-game.wav",
        )
        for wave_id, event, description in ALCHEMIST_VOICE_WAVES
    )
    entries = []
    for wave_id, description, source_path in inputs:
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        payload = source_path.read_bytes()
        validate_game_wave(payload, source_path.name)
        entries.append(CamEntry(pad_name(wave_id + description), payload))
    write_cam(
        output_path,
        (CamSection(b"WAVE", tuple(entries)),),
    )


def dsnd_head_size(sound_name: bytes) -> int:
    """Return the stock DSND HEAD identity-body size for *sound_name*."""
    return 8 + len(sound_name) + 2


def clone_dsnd_identity(
    template: bytes,
    source_id: bytes,
    source_name: bytes,
    private_id: bytes,
    private_name: bytes,
) -> bytes:
    """Privatize one stock DSND while preserving its complete phase table."""
    if len(source_id) != 4 or len(private_id) != 4:
        raise ValueError("DSND identities must use four-byte IDs")
    head_offset = template.find(b"HEAD")
    if head_offset < 0:
        raise ValueError("Stock DSND template has no HEAD block")
    head_size = u32(template, head_offset + 4)
    identity_offset = head_offset + 16
    name_offset = head_offset + 24
    head_end = head_offset + 16 + head_size
    if template[identity_offset : identity_offset + 4] != source_id:
        raise ValueError("Stock DSND HEAD identity changed")
    if template[name_offset:head_end] != source_name + b"\x00\x00":
        raise ValueError("Stock DSND HEAD name changed")
    payload = bytearray(
        template[:identity_offset]
        + private_id
        + template[identity_offset + 4 : name_offset]
        + private_name
        + b"\x00\x00"
        + template[head_end:]
    )
    struct.pack_into("<I", payload, 4, len(payload) - 16)
    struct.pack_into("<I", payload, 20, len(payload) - 32)
    struct.pack_into("<I", payload, head_offset + 4, dsnd_head_size(private_name))
    return bytes(payload)


def replace_single_dsnd_wave(
    payload: bytes, source_wave: bytes, private_wave: bytes
) -> bytes:
    """Replace exactly one phase WAVE target in an already-private DSND."""
    if len(source_wave) != 4 or len(private_wave) != 4:
        raise ValueError("DSND WAVE targets must use four-byte IDs")
    count = payload.count(source_wave)
    if count != 1:
        raise ValueError(
            f"Private DSND expected one {source_wave!r} phase target, found {count}"
        )
    return payload.replace(source_wave, private_wave)


def write_alchemist_sounddesc_cam(source_path: Path, output_path: Path) -> None:
    """Compile private Alchemist effects and voices through stock DSNDs."""
    specifications = (
        (
            b"DP01Drink_Potion",
            b"DP01",
            b"Drink_Potion",
            ALCHEMIST_VIGOR_SOUND_ID,
            ALCHEMIST_VIGOR_SOUND.encode("ascii"),
            None,
        ),
        (
            b"SL35Shield_of_Light",
            b"SL35",
            b"Shield_of_Light",
            ALCHEMIST_BOTTLE_BREAK_SOUND_ID,
            ALCHEMIST_BOTTLE_BREAK_SOUND.encode("ascii"),
            (b"SL35", ALCHEMIST_BOTTLE_BREAK_WAVE_ID),
        ),
        (
            b"BT01FervisTemple",
            b"BT01",
            b"FervisTemple",
            ALCHEMIST_LAB_SOUND_ID,
            ALCHEMIST_LAB_SOUND.encode("ascii"),
            (b"BT01", ALCHEMIST_LAB_WAVE_ID),
        ),
    )
    entries: list[CamEntry] = []
    for (
        template_entry,
        source_id,
        source_name,
        private_id,
        private_name,
        wave_replacement,
    ) in specifications:
        template = read_cam_entry(source_path, b"DSND", template_entry).data
        payload = clone_dsnd_identity(
            template, source_id, source_name, private_id, private_name
        )
        if wave_replacement is not None:
            payload = replace_single_dsnd_wave(payload, *wave_replacement)
        entries.append(CamEntry(pad_name(private_id + private_name), payload))

    # Preserve Cultist's complete non-cast hero voice topology and cooldown
    # groups. Replace only the approved event WAVE targets and the dagger hit.
    hero_template = read_cam_entry(source_path, b"DSND", b"CT01Cultist").data
    hero_payload = clone_dsnd_identity(
        hero_template,
        b"CT01",
        b"Cultist",
        ALCHEMIST_HERO_SOUND_ID,
        ALCHEMIST_HERO_SOUND.encode("ascii"),
    )
    for _phase_name, source_wave, private_wave in ALCHEMIST_HERO_VOICE_PHASES:
        hero_payload = replace_single_dsnd_wave(
            hero_payload, source_wave, private_wave
        )
    hero_payload = replace_single_dsnd_wave(hero_payload, b"WU04", b"WU03")
    entries.append(
        CamEntry(
            pad_name(
                ALCHEMIST_HERO_SOUND_ID + ALCHEMIST_HERO_SOUND.encode("ascii")
            ),
            hero_payload,
        )
    )

    # Clone the exact single-phase descriptor already proven by Haunt for
    # class-specific recruitment and explicit GPL voice dispatch. SG21 is the
    # stock Wizard Hero_Cast_Voice_Group; SG14 is Voice_Special_1_Group.
    begin_template = read_cam_entry(
        source_path, b"DSND", b"RM01Rage_of_Krolm"
    ).data
    for sound_id, sound_name, wave_id, group_id in (
        (
            ALCHEMIST_CAST_VOICE_SOUND_ID,
            ALCHEMIST_CAST_VOICE_SOUND.encode("ascii"),
            b"AHC2",
            b"SG21",
        ),
        (
            ALCHEMIST_HIRED_VOICE_SOUND_ID,
            ALCHEMIST_HIRED_VOICE_SOUND.encode("ascii"),
            b"AHS1",
            b"SG14",
        ),
    ):
        payload = clone_dsnd_identity(
            begin_template,
            b"RM01",
            b"Rage_of_Krolm",
            sound_id,
            sound_name,
        )
        payload = replace_single_dsnd_wave(payload, b"RM01", wave_id)
        phase_offset = payload.find(b"EBE0")
        if phase_offset < 0 or len(payload) - phase_offset != 56:
            raise ValueError("Stock Rage_of_Krolm Begin phase layout changed")
        payload = (
            payload[: phase_offset + 8]
            + group_id
            + bytes(44)
            + payload[phase_offset + 56 :]
        )
        entries.append(CamEntry(pad_name(sound_id + sound_name), payload))
    write_cam(output_path, (CamSection(b"DSND", tuple(entries)),))


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


def add_stock_sovereign_brewing_row(
    brewing_menu: bytes,
    stock_brewing_menu: bytes,
    control_id: int,
    y: int,
    label_index: int,
    tooltip_index: int,
) -> bytes:
    """Clone AP69's complete spell row and change only its private identity.

    The row remains an ordinary AP69 spell control with a genuine stock Fervus
    visual identity, so Majesty constructs and draws the complete button/icon/
    price family. The scoped CGBR controller translates only its click into a
    private level-three Lightning Storm clone; stock Fervus remains unchanged.
    """
    source = bytearray(
        stock_brewing_menu[
            AP69_FIRST_RECIPE_RECORD_START:AP69_FIRST_RECIPE_RECORD_END
        ]
    )
    if len(source) != 0x1B0 or source[-4:] != b"\xff" * 4:
        raise ValueError("Stock AP69 first sovereign-row template changed")
    if (
        u32(source, 0xE4) == 0
        or u32(source, 0x54) != u32(source, 0xE4) + 1000
        or u32(source, 0x184) != u32(source, 0xE4) - 1000
    ):
        raise ValueError("Stock AP69 first spell-row control family changed")
    if source[0xA4:0xA8] != b"INBb" or u32(source, 0xAC) != 0x405:
        raise ValueError("Stock AP69 first spell-row background contract changed")
    struct.pack_into("<I", source, 0x0C, y - 2)
    struct.pack_into("<I", source, 0x68, y)
    struct.pack_into("<I", source, 0x124, y + 1)
    struct.pack_into("<I", source, 0x88, label_index)
    struct.pack_into("<I", source, 0x94, tooltip_index)
    struct.pack_into("<I", source, 0x54, control_id + 1000)
    struct.pack_into("<I", source, 0xE4, control_id)
    struct.pack_into("<I", source, 0x184, control_id - 1000)
    source = (
        source.replace(b"INBb", b"ALBB")
        .replace(b"INTI", b"ALTI")
        .replace(b"INTN", b"ALIN")
    )
    # AP69 keeps its ordinary spell-row records before specialized streamed
    # displays.  CGBR already has AP24's INSr display inserted ahead of AP69's
    # terminal ornament, so inserting another AP69 row at the terminal would
    # put the row after INSr.  Majesty then scans the compound button's ALBB
    # member as an unrelated top-level record and its stock skip routine lands
    # on image-set 0x407 as though it were an opcode.  Preserve AP69's literal
    # control ordering by placing this complete row immediately before the
    # first AP24 display instead.
    progress_art = brewing_menu.find(b"INSr")
    if progress_art < 0:
        raise ValueError("CGBR has no stock AP24 display insertion boundary")
    insertion = progress_art - 4 - RAGE_PROGRESS_INNER_OFFSET
    if insertion < 4 or u32(brewing_menu, insertion - 4) != 0xFFFFFFFF:
        raise ValueError("CGBR pre-display row insertion boundary changed")
    return bytes(brewing_menu[:insertion] + source + brewing_menu[insertion:])


def restore_native_fervus_probe_rows(
    brewing_menu: bytes, stock_brewing_menu: bytes
) -> bytes:
    """Restore AP69's real lower spell rows in their native stream slots."""
    output = bytearray(brewing_menu)
    output[0x02D0:0x0620] = stock_brewing_menu[0x02D0:0x0620]
    expected = (
        (0x02DC, 114, 137, "Fervus second-row icon"),
        (0x0330, 116, 139, "Fervus second-row action"),
        (0x03EC, 117, 140, "Fervus second-row price"),
        (0x0484, 87, 162, "Fervus third-row icon"),
        (0x04D8, 89, 164, "Fervus third-row action"),
        (0x0594, 90, 165, "Fervus third-row price"),
    )
    for offset, stock_y, private_y, label in expected:
        if u32(output, offset) != stock_y:
            raise ValueError(f"Stock AP69 {label} position changed")
        struct.pack_into("<I", output, offset, private_y)
    # Use Majesty's stock compact centered button font for the two long private
    # names.  Their full 162-pixel fields below preserve centering; fnt4's
    # shadow clips between the words and appears as a black center tick.
    for offset, label in (
        (0x03B4, "Fervus second-row action font"),
        (0x055C, "Fervus third-row action font"),
    ):
        if output[offset : offset + 4] != b"fnt4":
            raise ValueError(f"Stock AP69 {label} changed")
        output[offset : offset + 4] = b"fnt7"
    return bytes(output)


def normalize_brewing_recipe_button_plates(brewing_menu: bytes) -> bytes:
    """Use private AP69 copies of APa1's stock gold button plate.

    Weapon Oil and Phoenix Phial already use the stock Guardhouse Arrows
    compound button with INBb image-set 0x3FD. Preserve every AP69 action
    control, descriptor, image-set identity, and 162x20 geometry. Only route
    the two restored lower rows to private ALBB, whose three AP69 image sets
    contain dimension-matched copies of APa1's complete gold plate.
    """
    output = bytearray(brewing_menu)
    if output.count(b"INTN") != 2:
        raise ValueError("CGBR lower recipe icon count changed")
    # Preserve AP69's two real icon controls and image-set IDs. Route only
    # their art owner to the existing private INTN clone, where 0x3F6 and
    # 0x3F7 carry the approved Tempest and Stone state families.
    output = bytearray(bytes(output).replace(b"INTN", b"ALIN"))
    # AP69 reserves 42 pixels of each action label for its price child. The
    # Parts actions hide that complete child, so widen only the stock label
    # field from 120 to the full 162-pixel action plate. Its native centering
    # and fnt4 rendering remain unchanged.
    for width_offset, label in (
        (0x0348, "Arcane Infusion"),
        (0x04F0, "Philosopher's Stone"),
    ):
        if u32(output, width_offset) != 120:
            raise ValueError(f"CGBR {label} stock text width changed")
        struct.pack_into("<I", output, width_offset, 162)
    for art_offset, stock_art, image_set, label in (
        (0x01C4, b"ALBB", 0x405, "Vigor Elixir"),
        (0x036C, b"INBb", 0x406, "Arcane Infusion"),
        (0x0514, b"INBb", 0x407, "Philosopher's Stone"),
    ):
        if output[art_offset : art_offset + 4] != stock_art:
            raise ValueError(f"CGBR {label} stock button art changed")
        if u32(output, art_offset + 8) != image_set:
            raise ValueError(f"CGBR {label} stock button image-set changed")
        output[art_offset : art_offset + 4] = b"ALBB"
    for rect_offset, expected, label in (
        (0x0184, VIGOR_ROW_OUTER_RECT, "Vigor Elixir"),
        (0x032C, (30, 139, 162, 20), "Arcane Infusion"),
        (0x04D4, (30, 164, 162, 20), "Philosopher's Stone"),
    ):
        if struct.unpack_from("<4I", output, rect_offset) != expected:
            raise ValueError(f"CGBR {label} stock button rectangle changed")
    return bytes(output)


def append_stock_research_action_control(
    brewing_menu: bytes,
    research_menu: bytes,
    control_id: int,
    y: int,
    label_index: int,
    tooltip_index: int,
) -> bytes:
    """Append APa1's complete native action record ahead of CGBR displays."""
    source = bytearray(
        research_menu[APA1_ARROWS_RECORD_START:APA1_ARROWS_RECORD_END]
    )
    if len(source) != 0xF8 or source[-4:] != b"\xff" * 4:
        raise ValueError("Stock APa1 Arrows action record changed")
    if u32(source, RESEARCH_ROW_CONTROL_ID_OFFSET) != STOCK_ARROWS_RESEARCH_CONTROL_ID:
        raise ValueError("Stock APa1 Arrows action ID changed")
    struct.pack_into("<I", source, RESEARCH_ROW_OUTER_X_OFFSET, 30)
    struct.pack_into("<I", source, RESEARCH_ROW_OUTER_Y_OFFSET, y)
    struct.pack_into("<I", source, RESEARCH_ROW_OUTER_WIDTH_OFFSET, 162)
    struct.pack_into("<I", source, RESEARCH_ROW_CONTROL_ID_OFFSET, control_id)
    struct.pack_into("<I", source, RESEARCH_ROW_LABEL_INDEX_OFFSET, label_index)
    struct.pack_into("<I", source, RESEARCH_ROW_TOOLTIP_INDEX_OFFSET, tooltip_index)
    if source.count(b"INBb") != 1:
        raise ValueError("Stock APa1 Arrows action background changed")
    source = source.replace(b"INBb", b"ALBB", 1)
    progress_art = brewing_menu.find(b"INSr")
    if progress_art < 0:
        raise ValueError("CGBR has no stock AP24 display insertion boundary")
    insertion = progress_art - 4 - RAGE_PROGRESS_INNER_OFFSET
    if insertion < 4 or u32(brewing_menu, insertion - 4) != 0xFFFFFFFF:
        raise ValueError("CGBR pre-display action insertion boundary changed")
    return bytes(brewing_menu[:insertion] + source + brewing_menu[insertion:])


def add_reagent_label_control(
    brewing_menu: bytes, stock_brewing_menu: bytes
) -> bytes:
    """Clone AP69's gold title text control as the Reagents label."""
    source = bytearray(
        stock_brewing_menu[AP69_TITLE_RECORD_START:AP69_TITLE_RECORD_END]
    )
    if len(source) != 0x54 or source[-4:] != b"\xff" * 4:
        raise ValueError("Stock AP69 title-label template changed")
    if (
        u32(source, 0) != 5
        or struct.unpack_from("<4I", source, 0x08) != AP69_TITLE_RECT
        or u32(source, 0x18) != 7
        or u32(source, AP69_TITLE_TEXT_INDEX_OFFSET) != 13
        or u32(source, AP69_TITLE_CONTROL_ID_OFFSET) != AP69_TITLE_CONTROL_ID
        or source[AP69_TITLE_FONT_OFFSET : AP69_TITLE_FONT_OFFSET + 4] != b"fnt4"
    ):
        raise ValueError("Stock AP69 title-label contract changed")
    struct.pack_into("<4I", source, 0x08, *REAGENT_LABEL_RECT)
    struct.pack_into("<I", source, AP69_TITLE_TEXT_INDEX_OFFSET, 33)
    struct.pack_into(
        "<I",
        source,
        AP69_TITLE_CONTROL_ID_OFFSET,
        BREWING_REAGENT_METER_LABEL_CONTROL_ID,
    )
    if brewing_menu[-8:] != b"\xff" * 8:
        raise ValueError("CGBR terminal marker changed before reagent-label insertion")
    return bytes(brewing_menu[:-4] + source + b"\xff" * 4)


def add_reagent_count_control(brewing_menu: bytes, items_menu: bytes) -> bytes:
    """Clone AP22's Healing Potion quantity field beside the Reagents label."""
    source = bytearray(
        items_menu[
            AP22_HEALING_COUNT_RECORD_START:AP22_HEALING_COUNT_RECORD_END
        ]
    )
    if (
        len(source) != 0x9C
        or u32(source, len(source) - 8) != 0x26
        or source[-4:] != b"\x00" * 4
    ):
        raise ValueError("Stock AP22 Healing Potion count record changed")
    if u32(source, 0) != 5:
        raise ValueError("Stock AP22 Healing Potion count control type changed")
    if struct.unpack_from("<4I", source, 0x08) != AP22_HEALING_COUNT_RECT:
        raise ValueError("Stock AP22 Healing Potion count rectangle changed")
    if (
        u32(source, AP22_HEALING_COUNT_TEXT_INDEX_OFFSET) != 15
        or u32(source, AP22_HEALING_COUNT_TOOLTIP_INDEX_OFFSET) != 16
        or u32(source, AP22_HEALING_COUNT_CONTROL_ID_OFFSET)
        != AP22_HEALING_COUNT_CONTROL_ID
        or u32(source, AP22_HEALING_COUNT_BINDING_ID_OFFSET)
        != AP22_HEALING_COUNT_BINDING_ID
    ):
        raise ValueError("Stock AP22 Healing Potion count bindings changed")
    struct.pack_into("<4I", source, 0x08, *REAGENT_COUNT_RECT)
    struct.pack_into(
        "<I", source, AP22_HEALING_COUNT_TEXT_INDEX_OFFSET, 39
    )
    struct.pack_into(
        "<I", source, AP22_HEALING_COUNT_TOOLTIP_INDEX_OFFSET, 40
    )
    struct.pack_into(
        "<I",
        source,
        AP22_HEALING_COUNT_CONTROL_ID_OFFSET,
        BREWING_REAGENT_COUNT_CONTROL_ID,
    )
    struct.pack_into(
        "<I",
        source,
        AP22_HEALING_COUNT_BINDING_ID_OFFSET,
        BREWING_REAGENT_COUNT_BINDING_ID,
    )
    if source.count(b"INTI") != 1:
        raise ValueError("Stock AP22 Healing Potion count art changed")
    source = source.replace(b"INTI", b"ALTI", 1)
    if brewing_menu[-8:] != b"\xff" * 8:
        raise ValueError("CGBR terminal marker changed before reagent-count insertion")
    # Retain the previous final-control terminator, append AP22's complete
    # count record, then add that record's terminator and the stream terminator.
    return bytes(brewing_menu[:-4] + source + b"\xff" * 8)


def add_stock_visitors_control(
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
    enable_brewing_control: bool = False,
) -> None:
    menu = read_cam_entry(stock_text_cam, b"SMNU", SOURCE_DIALOG_ID).data
    menu = privateize_cgal_menu(menu)
    if enable_brewing_control:
        menu = move_brewing_control_below_recruit(menu)
    else:
        menu = disable_ap10_secondary_control(menu)
    rage_menu = read_cam_entry(stock_text_cam, b"SMNU", SOURCE_RAGE_DIALOG_ID).data
    visitors_source = read_cam_entry(
        stock_text_cam, b"SMNU", SOURCE_VISITORS_DIALOG_ID
    ).data
    menu = add_stock_visitors_control(menu, visitors_source)
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
    stock_brewing_menu = read_cam_entry(
        stock_text_cam, b"SMNU", SOURCE_BREWING_DIALOG_ID
    ).data
    brewing_menu = restore_native_fervus_probe_rows(
        brewing_menu, stock_brewing_menu
    )
    brewing_menu = privateize_brewing_action_control(brewing_menu)
    brewing_menu = add_native_rage_progress_control(brewing_menu, rage_menu)
    brewing_menu = normalize_brewing_recipe_button_plates(brewing_menu)
    research_menu = read_cam_entry(
        stock_text_cam, b"SMNU", SOURCE_RESEARCH_DIALOG_ID
    ).data
    items_menu = read_cam_entry(
        stock_text_cam, b"SMNU", SOURCE_ITEMS_DIALOG_ID
    ).data
    brewing_menu = append_stock_research_action_control(
        brewing_menu,
        research_menu,
        BREWING_WEAPON_OIL_CONTROL_ID,
        62,
        36,
        37,
    )
    brewing_menu = append_stock_research_action_control(
        brewing_menu,
        research_menu,
        BREWING_PHOENIX_PHIAL_CONTROL_ID,
        87,
        34,
        35,
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
    brewing_menu = add_reagent_label_control(brewing_menu, stock_brewing_menu)
    brewing_menu = add_reagent_count_control(brewing_menu, items_menu)
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
            2: "Invigorate every unit for 30 seconds: faster movement, 20 bonus hit points, and greater confidence. Costs 1 Reagent.",
            3: "1500",
            # Keep AP69's two complete lower spell controls unchanged. Their
            # streamed text properties still address the same stock STRT
            # positions; only CGBR's private copies of those strings differ.
            4: "Arcane Infusion",
            5: "Permanently grant all current and future Alchemists 25 Magic Resistance. Requires 10 Reagents. One use per kingdom.",
            6: "",
            7: "Philosopher's Stone",
            8: "Transmute one ordinary enemy into 3000 gold. Requires 10 Reagents.",
            # APa1's presenter replaces this fallback with each descriptor's
            # live price (250 for Oil, 750 for Phoenix).
            9: "250",
            13: "Brewing",
            28: "Invigorated",
            29: "Researching Weapon Oil",
            30: "Researching Phoenix Phial",
            33: "Reagents",
            34: "Phoenix Phial",
            35: "Research Phoenix Phials for sale to heroes.",
            36: "Weapon Oil",
            37: "Research weapon oil for the Laboratory's stock enchanting service.",
            39: "0",
            40: "This Laboratory's current number of stored Reagents.",
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
    """Append private intents, inventory text, help pages, and hero names."""
    stock_intents = read_cam_entry(stock_gpl_text_cam, b"STRT", b"AITX").data
    stock_items = read_cam_entry(stock_gpl_text_cam, b"STRT", b"QITM").data
    stock_help = read_cam_entry(stock_gpl_text_cam, b"STRT", b"HPTX").data
    stock_name_template = read_cam_entry(
        stock_gpl_text_cam, b"STRT", b"HN61"
    ).data
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
    shared_item_text: dict[int, str] = {
        PHOENIX_PHIAL_ITEM_ID: PHOENIX_PHIAL_ITEM_TEXT,
        82: "Frost Armor\n\x01FFDDAA(+10 armor)",
    }
    for family, base_id, first_variant, names in (
        ("cowl", 80, 83, PHANTOM_COWL_TIER_NAMES),
        ("icerod", 81, 98, PHANTOM_ICEROD_TIER_NAMES),
    ):
        for struct_level in range(4):
            for magic_level in range(4):
                combination = struct_level * 4 + magic_level
                item_id = base_id if combination == 0 else first_variant + combination - 1
                if family == "cowl":
                    bonus = f"(+{2 + struct_level} armor, +{magic_level} magic armor)"
                else:
                    bonus = (
                        f"(+{8 + struct_level} damage, +{magic_level} magic, "
                        f"+{5 + struct_level * 5} parry, "
                        f"+{10 + magic_level * 10} cast range)"
                    )
                shared_item_text[item_id] = f"{names[struct_level]}\n\x01FFDDAA{bonus}"
    patched_items = patch_strt_by_index(stock_items, shared_item_text)
    patched_help = patch_strt_by_id(
        stock_help,
        {
            fourcc_id(help_id): text
            for help_id, text in ALCHEMIST_HELP_PAGES.items()
        },
    )
    if len(ALCHEMIST_NAME_GIVENS) != 43 or len(ALCHEMIST_NAME_ENDINGS) != 43:
        raise ValueError("Approved Alchemist name pools must contain 43 entries each")
    if len(set(ALCHEMIST_NAME_GIVENS)) != len(ALCHEMIST_NAME_GIVENS) or len(
        set(ALCHEMIST_NAME_ENDINGS)
    ) != len(ALCHEMIST_NAME_ENDINGS):
        raise ValueError("Approved Alchemist name pools must be unique")
    if any("\u2014" in text for text in (*ALCHEMIST_NAME_GIVENS, *ALCHEMIST_NAME_ENDINGS)):
        raise ValueError("Approved Alchemist names contain a forbidden em dash")
    name_version = stock_name_template[2:4]
    private_name_tables = (
        encode_strt(
            name_version,
            [
                (index, text.encode("cp1252"))
                for index, text in enumerate(ALCHEMIST_NAME_GIVENS)
            ],
        ),
        encode_strt(
            name_version,
            [
                (index, f" {text}".encode("cp1252"))
                for index, text in enumerate(ALCHEMIST_NAME_ENDINGS)
            ],
        ),
        encode_strt(name_version, []),
        encode_strt(name_version, []),
    )
    write_cam(
        output_path,
        (
            CamSection(
                b"STRT",
                (
                    CamEntry(pad_name(b"AITX"), patched_intents),
                    CamEntry(pad_name(b"QITM"), patched_items),
                    CamEntry(pad_name(b"HPTX"), patched_help),
                    *(
                        CamEntry(pad_name(name), table)
                        for name, table in zip(
                            ALCHEMIST_NAME_TABLE_IDS, private_name_tables
                        )
                    ),
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


def stock_building_dependency_cam(game_path: Path) -> Path:
    """Return the final stock BDEP provider used by Northern Expansion.

    Gold HD loads Original Majesty's Data/miscdata.cam first, then replaces the
    complete DATA/BDEP resource with DataMX/mx_miscdata.cam.  The universal
    package must extend that final stock record so it does not erase expansion
    Palace gates or Outpost alternatives.
    """

    return game_path / STOCK_BDEP_CAM_RELATIVE_PATH


def build_bdep_payload(stock_data: bytes, include_phantoms: bool) -> bytes:
    """Append the private guild rows to an unmodified stock Expansion table."""

    for private_rule in (PHANTOM_BDEP_RULE, ALCHEMIST_BDEP_RULE):
        if private_rule in stock_data:
            raise ValueError(
                f"Stock Expansion BDEP unexpectedly contains {private_rule!r}"
            )
    stock_lines = stock_data.splitlines()
    missing_expansion_rules = [
        rule for rule in STOCK_EXPANSION_BDEP_RULES if rule not in stock_lines
    ]
    if missing_expansion_rules:
        raise ValueError(
            "Stock Expansion BDEP lost canonical building prerequisites: "
            f"{missing_expansion_rules}"
        )

    output = stock_data
    if include_phantoms:
        output = append_bdep_rule(output, PHANTOM_BDEP_RULE, PHANTOM_BDEP_COMMENT)
    return append_bdep_rule(
        output,
        ALCHEMIST_BDEP_RULE,
        ALCHEMIST_BDEP_COMMENT,
    )


def validate_bdep_payload(
    building_dependencies: bytes,
    stock_data: bytes,
    include_phantoms: bool,
) -> None:
    """Require exact stock Expansion bytes followed by the selected private rows."""

    expected = build_bdep_payload(stock_data, include_phantoms)
    if building_dependencies == expected:
        return
    mismatch = next(
        (
            index
            for index, (actual, wanted) in enumerate(
                zip(building_dependencies, expected)
            )
            if actual != wanted
        ),
        min(len(building_dependencies), len(expected)),
    )
    raise ValueError(
        "Alchemist BDEP differs from the complete stock Expansion table plus "
        f"the selected private rules at byte {mismatch} "
        f"(built={len(building_dependencies)} bytes, expected={len(expected)} bytes)"
    )


def validate_siege_test_symbols(
    compiled_symbols: bytes,
    include_siege_test_fixture: bool,
) -> None:
    required = (b"SIEGE",)
    forbidden = (b"Alchemist_Oil_Test_Buyer",)
    present = tuple(symbol for symbol in required if symbol in compiled_symbols)
    if include_siege_test_fixture and len(present) != len(required):
        missing = [symbol for symbol in required if symbol not in compiled_symbols]
        raise ValueError(f"Compiled Siege QA fixture lost symbols: {missing}")
    if not include_siege_test_fixture and present:
        raise ValueError(
            f"Compiled non-Siege package unexpectedly exports QA symbols: {present}"
        )
    leaked = tuple(symbol for symbol in forbidden if symbol in compiled_symbols)
    if leaked:
        raise ValueError(f"Compiled Siege QA fixture retains removed symbols: {leaked}")


def build_misc_cam(stock_misc_cam: Path, output_path: Path, include_phantoms: bool) -> None:
    bdep = read_cam_entry(stock_misc_cam, b"DATA", b"BDEP").data
    bdep = build_bdep_payload(bdep, include_phantoms)
    write_cam(
        output_path,
        (CamSection(b"DATA", (CamEntry(pad_name(b"BDEP"), bdep),)),),
    )


def build_manifest(include_siege_test_fixture: bool = False) -> str:
    siege_source = (
        "\n\t\t\t\t\t\t<Source>GPL\\Alchemist_Siege_Test.gpl</Source>"
        if include_siege_test_fixture
        else ""
    )
    return f'''<Majesty>
\t<Mod id="{MOD_ID}">
\t\t<Name>{PACKAGE_NAME}</Name>
\t\t<DisplayName lang="en_US">Custom Guild: Alchemist Lab</DisplayName>
\t\t<Description lang="en_US">
\t\t\t<Short>Adds the Alchemy Lab, Alchemist heroes, and sovereign brews.</Short>
\t\t\t<Long>Recruit potion-minded Alchemists, research useful concoctions for visiting heroes, and brew the kingdom-wide Vigor Elixir.</Long>
\t\t</Description>
\t\t<DataConfiguration>
\t\t\t<Dataset base="Any">
\t\t\t\t<Load>
\t\t\t\t\t<CAM>Data\\alchemist_textdata.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_gpltext.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_miscdata.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_maindata.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_interfacedata.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_audio.cam</CAM>
\t\t\t\t\t<CAM>Data\\alchemist_sounddesc.cam</CAM>
\t\t\t\t\t<Descriptions>Data\\alchemist_units.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_brewing_overlays.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_brewing_sounds.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_combat_potions.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_flash_flask.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_stun_serum.xml</Descriptions>
\t\t\t\t\t<Descriptions>Data\\alchemist_miasma_mist.xml</Descriptions>
\t\t\t\t\t<GPL>
\t\t\t\t\t\t<Target>Data\\Alchemist.bcd</Target>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Building_Data.dat</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Hero_Data.dat</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Phoenix_Phial.dat</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Rogue.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Embassy.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Guild_Title.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Adopt.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Magic_Bazaar.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Nearby_Equipment.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Inventory.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Consumable_Threat.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Strength_Potion.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Shapeshift.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Stun_Serum.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Flash_Flask.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Miasma_Mist.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Brewing.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Economy.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Weapon_Oil.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Combat_Oils.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Damage.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Phoenix_Phial.gpl</Source>
\t\t\t\t\t\t<Source>GPL\\Alchemist_Reagents.gpl</Source>{siege_source}
\t\t\t\t\t</GPL>
\t\t\t\t</Load>
\t\t\t</Dataset>
\t\t</DataConfiguration>
\t</Mod>
</Majesty>
'''


def validate_output(
    output_root: Path,
    game_path: Path,
    include_phantoms: bool,
    enable_brewing_control: bool = True,
    include_siege_test_fixture: bool = False,
    approved_sprite_test_set: bool = False,
) -> None:
    expected = {
        output_root / MANIFEST_FILENAME,
        output_root / MOD_DEFINITION_FILENAME,
        output_root / "Data" / "alchemist_units.xml",
        output_root / "Data" / "alchemist_brewing_overlays.xml",
        output_root / "Data" / "alchemist_brewing_sounds.xml",
        output_root / "Data" / "alchemist_combat_potions.xml",
        output_root / "Data" / "alchemist_flash_flask.xml",
        output_root / "Data" / "alchemist_stun_serum.xml",
        output_root / "Data" / "alchemist_miasma_mist.xml",
        output_root / "Data" / "alchemist_textdata.cam",
        output_root / "Data" / "alchemist_gpltext.cam",
        output_root / "Data" / "alchemist_miscdata.cam",
        output_root / "Data" / "alchemist_maindata.cam",
        output_root / "Data" / "alchemist_interfacedata.cam",
        output_root / "Data" / "alchemist_audio.cam",
        output_root / "Data" / "alchemist_sounddesc.cam",
        output_root / "Data" / "Alchemist.bcd",
        output_root / "GPL" / "Alchemist.gplproj",
        output_root / "GPL" / "Alchemist_Building_Data.dat",
        output_root / "GPL" / "Alchemist_Hero_Data.dat",
        output_root / "GPL" / "Alchemist_Phoenix_Phial.dat",
        output_root / "GPL" / "Alchemist_Rogue.gpl",
        output_root / "GPL" / "Alchemist_Embassy.gpl",
        output_root / "GPL" / "Alchemist_Guild_Title.gpl",
        output_root / "GPL" / "Alchemist_Adopt.gpl",
        output_root / "GPL" / "Alchemist_Magic_Bazaar.gpl",
        output_root / "GPL" / "Alchemist_Nearby_Equipment.gpl",
        output_root / "GPL" / "Alchemist_Inventory.gpl",
        output_root / "GPL" / "Alchemist_Consumable_Threat.gpl",
        output_root / "GPL" / "Alchemist_Strength_Potion.gpl",
        output_root / "GPL" / "Alchemist_Shapeshift.gpl",
        output_root / "GPL" / "Alchemist_Flash_Flask.gpl",
        output_root / "GPL" / "Alchemist_Stun_Serum.gpl",
        output_root / "GPL" / "Alchemist_Miasma_Mist.gpl",
        output_root / "GPL" / "Alchemist_Brewing.gpl",
        output_root / "GPL" / "Alchemist_Economy.gpl",
        output_root / "GPL" / "Alchemist_Weapon_Oil.gpl",
        output_root / "GPL" / "Alchemist_Combat_Oils.gpl",
        output_root / "GPL" / "Alchemist_Damage.gpl",
        output_root / "GPL" / "Alchemist_Phoenix_Phial.gpl",
        output_root / "GPL" / "Alchemist_Reagents.gpl",
    }
    if include_siege_test_fixture:
        expected.add(output_root / "GPL" / "Alchemist_Siege_Test.gpl")
    if approved_sprite_test_set:
        expected.add(output_root / APPROVED_SPRITE_PROVENANCE_NAME)
    actual = {path for path in output_root.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError(f"Unexpected package files: {sorted(str(p) for p in actual ^ expected)}")
    mod_definition = json.loads(
        (output_root / MOD_DEFINITION_FILENAME).read_text(encoding="utf-8")
    )
    if mod_definition.get("schema_version") != 3:
        raise ValueError("Mod Manager definition is not schema version 3")
    if mod_definition.get("mod_id") != MOD_ID:
        raise ValueError("Mod Manager definition UUID does not match the manifest")
    if mod_definition.get("internal_name") != PACKAGE_NAME:
        raise ValueError("Mod Manager definition internal name changed")
    if mod_definition.get("display_name") != "Custom Guild: Alchemist Lab":
        raise ValueError("Mod Manager definition display name changed")
    if mod_definition.get("custom_buildings") != [
        {
            "local_name": "AlchemistsLaboratory",
            "controller_base": "AP10",
            "panel_resource_template": "AP10",
        }
    ]:
        raise ValueError("Mod Manager custom-building contract changed")
    runtime_features = mod_definition.get("runtime_features")
    if not isinstance(runtime_features, list):
        raise ValueError("Mod Manager runtime features are missing")
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
    try:
        runtime_feature_identities = tuple(
            (feature["type"], feature[identity_fields[feature["type"]]])
            for feature in runtime_features
        )
    except (KeyError, TypeError) as exc:
        raise ValueError("Mod Manager runtime feature shape changed") from exc
    if runtime_feature_identities != RUNTIME_FEATURE_IDENTITIES:
        raise ValueError("Mod Manager typed runtime feature contract changed")
    name_generator = runtime_features[0]
    if name_generator.get("name_tables") != ["HN69", "HN70", "HN71", "HN72"]:
        raise ValueError("Alchemist private name tables changed")
    if approved_sprite_test_set:
        provenance_path = output_root / APPROVED_SPRITE_PROVENANCE_NAME
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        if provenance.get("schema") != "majesty-alchemist-approved-sprite-test-set-v2":
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
    root = ET.parse(output_root / "Data" / "alchemist_units.xml").getroot()
    descriptions = root.findall("Description")
    if [item.get("ID") for item in descriptions] != [
        ALCHEMIST_HERO_ID,
        "ALS1",
        *BUILDING_IDS,
        "PXF1",
    ]:
        raise ValueError("Alchemist unit ID sequence is invalid")
    hero = descriptions[0]
    sovereign_units = descriptions[1:2]
    buildings = descriptions[2:5]
    phoenix = descriptions[5]
    if [item.get("Name") for item in sovereign_units] != [
        "philosophers_stone",
    ]:
        raise ValueError("Private sovereign spell-unit descriptions are missing")
    sovereign_unit_contract = [
        (
            item.find("./Engine/ImageIDBase").get("value"),
            item.find("./Engine/DefaultSound").get("value"),
            item.find("./Engine/Script").get("GPLFunction"),
        )
        for item in sovereign_units
    ]
    if sovereign_unit_contract != [
        ("AMm6", "0", "Philosophers_Stone_Hit"),
    ]:
        raise ValueError(
            "Private sovereign units retained Lightning art, sound, or callbacks"
        )
    if hero.get("Name") != ALCHEMIST_HERO_NAME:
        raise ValueError("Private Alchemist hero description is missing")
    if hero.find("./Engine/ImageIDBase").get("value") != ALCHEMIST_HERO_ID:
        raise ValueError("Alchemist must use its private image record")
    if hero.find("./Game/HelpID").get("value") != ALCHEMIST_HERO_HELP_ID:
        raise ValueError("Alchemist must use its private help page")
    if hero.find("./Game/NameGenType").get("value") != ALCHEMIST_NAME_GENERATOR_ID:
        raise ValueError("Alchemist must use the private NM18 name generator")
    if hero.find("./Engine/DefaultSound").get("value") != ALCHEMIST_HERO_SOUND:
        raise ValueError("Alchemist hero lost its private stock voice clone")
    if hero.find("./Game/Cost").get("value") != ALCHEMIST_RECRUIT_COST:
        raise ValueError("Alchemist recruitment price changed")
    movement = hero.find('./Engine/Attachment[@kind="Movement"]')
    if movement is None or movement.get("ID") != "Class 1":
        raise ValueError("Alchemist must use the stock Warrior movement class")
    speed = hero.find("./Game/Speed")
    if speed is None or speed.get("value") != "2":
        raise ValueError("Alchemist AI speed rating must remain 2")
    allowed_spells = hero.findall("./Game/AllowedSpells/Spell")
    if [(spell.get("ID"), spell.get("Value")) for spell in allowed_spells] != [
        ("0", STUN_SERUM_ACTION_NAME),
        ("1", FLASH_FLASK_ACTION_NAME),
        ("2", MIASMA_MIST_ACTION_NAME),
    ]:
        raise ValueError("Alchemist private combat-spell order changed")
    attack_range = hero.find("./Game/AttackRange")
    if (
        attack_range is None
        or attack_range.get("min") != "1"
        or attack_range.get("max") != "1"
    ):
        raise ValueError("Alchemist must use Warrior's stock 1..1 melee range")
    if any(item.find("./Game/DialogID").get("value") != "CGAL" for item in buildings):
        raise ValueError("Every Laboratory level must use CGAL")
    if any(
        item.find("./Engine/DefaultSound").get("value") != ALCHEMIST_LAB_SOUND
        for item in buildings
    ):
        raise ValueError("Every Laboratory level must use the private Fervus sound clone")
    if [item.find("./Game/HelpID").get("value") for item in buildings] != list(
        ALCHEMIST_BUILDING_HELP_IDS
    ):
        raise ValueError("Every Laboratory level must use its private help page")
    if [item.find("./Game/Cost").get("value") for item in buildings] != list(
        ALCHEMIST_BUILDING_COSTS
    ):
        raise ValueError("Laboratory costs must match Phantoms Haunt progression")
    if phoenix.get("Name") != "PhoenixPhial" or phoenix.find(
        './Game/Flags[@value="IsInventoryItem"]'
    ) is None:
        raise ValueError("Phoenix Phial inventory-item description is missing")
    if phoenix.find("./Engine/ImageIDBase").get("value") != "PXF1":
        raise ValueError("Phoenix Phial must use its private inventory-item art")
    potion_root = ET.parse(
        output_root / "Data" / "alchemist_combat_potions.xml"
    ).getroot()
    potion_specs = (
        (
            ALCHEMIST_STRENGTH_ACTION_NAME,
            "Alchemist_Strength_Potion_Effect",
            "1",
        ),
        (
            ALCHEMIST_SHAPESHIFT_ACTION_NAME,
            "Alchemist_Shapeshift_Potion_Effect",
            "2",
        ),
        (
            ALCHEMIST_FIRE_BALM_ACTION_NAME,
            "Alchemist_Fire_Balm_Effect",
            "3",
        ),
        (
            ALCHEMIST_REGENERATION_ACTION_NAME,
            "Alchemist_Regeneration_Elixer_Effect",
            "1",
        ),
    )
    for potion_name, gpl_function, rank in potion_specs:
        potion = potion_root.find(f'./Description[@Name="{potion_name}"]')
        if potion is None:
            raise ValueError(f"Private combat potion action is missing: {potion_name}")
        validation = potion.find("./Game/ValidationScript")
        if (
            validation is None
            or validation.get("value") != ALCHEMIST_CONSUMABLE_VALIDATION
        ):
            raise ValueError(f"Private {potion_name} lost its stock-composed threat gate")
        if (
            potion.find("./Engine/Script").get("GPLFunction") != gpl_function
            or potion.find("./Game/SpellType").get("value") != "Attack"
            or potion.find("./Game/SpellRank").get("value") != rank
        ):
            raise ValueError(f"Private {potion_name} lost its stock action contract")
    flash_root = ET.parse(output_root / "Data" / "alchemist_flash_flask.xml").getroot()
    flash_action = flash_root.find('./Description[@Name="flash_flask"]')
    flash_icon = flash_root.find(
        './Description[@Name="alchemist_flash_flask_icon"]'
    )
    flash_effect = flash_root.find(
        './Description[@Name="alchemist_flash_flask_effector"]'
    )
    if flash_action is None or flash_icon is None or flash_effect is None:
        raise ValueError("Private Flash Flask stock-clone descriptions are incomplete")
    if (
        flash_action.find("./Engine/ImageSet").get("value") != "Special"
        or flash_action.find("./Game/EffectorDuration").get("value")
        != FLASH_FLASK_DURATION_MS
        or flash_action.find("./Game/TimeoutDuration").get("value")
        != FLASH_FLASK_COOLDOWN_MS
        or flash_action.find("./Game/CharacterLevel").get("value") != "3"
        or flash_action.find("./Game/SpellType").get("value") != "Attack"
    ):
        raise ValueError("Flash Flask lost its stock combat-spell timing contract")
    if flash_icon.find("./Engine/ImageIDBase").get("value") != "AFF1" or (
        flash_icon.find("./Engine/Script").get("GPLFunction")
        != "Alchemist_Flash_Flask_End"
    ):
        raise ValueError("Flash Flask icon lost its private callback/art contract")
    if flash_effect.find("./Engine/ImageIDBase").get("value") != "AFF2" or (
        flash_effect.find("./Engine/AttachmentPointID").get("value") != "2"
    ):
        raise ValueError("Flash Flask activation lost its stock self-cast contract")
    if flash_action.find("./Engine/Sound") is not None or flash_action.find(
        "./Engine/SoundPhase"
    ) is not None:
        raise ValueError("Flash Flask must not retain Shield of Light's action sound")
    if flash_effect.find("./Engine/DefaultSound").get("value") != "Drink_Potion":
        raise ValueError("Flash Flask lost the stock healing-potion cork sound")
    stun_root = ET.parse(output_root / "Data" / "alchemist_stun_serum.xml").getroot()
    stun_action = stun_root.find('./Description[@Name="stun_serum"]')
    stun_impact = stun_root.find(
        './Description[@Name="alchemist_stun_serum_impact"]'
    )
    stun_restraint = stun_root.find(
        './Description[@Name="alchemist_stun_serum_restraint"]'
    )
    stun_icon = stun_root.find('./Description[@Name="alchemist_stun_serum_icon"]')
    if any(item is None for item in (stun_action, stun_impact, stun_restraint)):
        raise ValueError("Private Stun Serum stock-clone descriptions are incomplete")
    if stun_icon is not None:
        raise ValueError("Stun Serum must not create a separate overhead debuff icon")
    if (
        stun_action.find("./Engine/ImageSet").get("value") != "Cast"
        or stun_action.find("./Game/EffectorDuration").get("value")
        != STUN_SERUM_DURATION_MS
        or stun_action.find("./Game/TimeoutDuration").get("value")
        != STUN_SERUM_COOLDOWN_MS
        or stun_action.find("./Game/CharacterLevel").get("value") != "5"
        or stun_action.find("./Game/SpellRank").get("value") != "5"
        or stun_action.find("./Game/ValidationScript").get("value")
        != "Alchemist_Stun_Serum_Check"
        or stun_action.find("./Engine/Sound").get("value")
        != ALCHEMIST_CAST_VOICE_SOUND
    ):
        raise ValueError("Stun Serum lost Paralytic Gaze's stock action contract")
    if stun_impact.find("./Engine/ImageIDBase").get("value") != "ASS1":
        raise ValueError("Stun Serum impact lost its private art")
    if (
        stun_restraint.find("./Engine/ImageIDBase").get("value") != "ASS2"
        or stun_restraint.find("./Engine/Script").get("GPLFunction")
        != "Alchemist_Stun_Serum_End"
    ):
        raise ValueError("Stun Serum cage lost stock Vines cleanup ownership")
    miasma_root = ET.parse(
        output_root / "Data" / "alchemist_miasma_mist.xml"
    ).getroot()
    miasma_action = miasma_root.find('./Description[@Name="miasma_mist"]')
    miasma_unit = miasma_root.find(
        './Description[@Name="miasma_mist_cloud"]'
    )
    miasma_missile = miasma_root.find(
        './Description[@Name="miasma_mist_missile"]'
    )
    miasma_cloud = miasma_root.find(
        './Description[@Name="miasma_mist_cloud_effector"]'
    )
    miasma_icon = miasma_root.find(
        './Description[@Name="miasma_mist_debuff_icon"]'
    )
    miasma_particle = miasma_root.find(
        './Description[@Name="miasma_mist_cloud_attachment"]'
    )
    if any(
        item is None
        for item in (
            miasma_action,
            miasma_unit,
            miasma_missile,
            miasma_cloud,
            miasma_icon,
            miasma_particle,
        )
    ):
        raise ValueError("Miasma Mist stock-clone descriptions are incomplete")
    if (
        miasma_action.find("./Engine/ImageSet").get("value") != "Cast"
        or miasma_action.find("./Game/EffectorDuration").get("value")
        != MIASMA_MIST_DURATION_MS
        or miasma_action.find("./Game/TimeoutDuration").get("value")
        != MIASMA_MIST_COOLDOWN_MS
        or miasma_action.find("./Game/CharacterLevel").get("value") != "8"
        or miasma_action.find("./Game/SpellRank").get("value") != "4"
        or miasma_action.find("./Game/ValidationScript").get("value")
        != "Alchemist_Miasma_Mist_Check"
        or miasma_action.find("./Engine/Sound").get("value")
        != ALCHEMIST_CAST_VOICE_SOUND
    ):
        raise ValueError("Miasma Mist lost its stock Meteor Storm action contract")
    if (
        miasma_unit.find("./Engine/ImageIDBase").get("value") != "AMm6"
        or miasma_unit.find("./Engine/Script").get("GPLFunction")
        != "Alchemist_Miasma_Mist_Unit_Created"
        or miasma_missile.find("./Engine/ImageIDBase").get("value") != "AMm2"
        or miasma_missile.find("./Engine/Script").get("GPLFunction")
        != "Alchemist_Miasma_Mist_Missile_Hit"
    ):
        raise ValueError("Miasma Mist lost its private spell-unit/projectile contract")
    if (
        miasma_cloud.find("./Engine/ImageIDBase").get("value") != "AMm1"
        or miasma_cloud.find("./Engine/AttachmentPointID").get("value") != "2"
        or miasma_icon.find("./Engine/ImageIDBase").get("value") != "AMm5"
        or miasma_icon.find("./Game/StackPriority").get("value") != "1"
        or miasma_particle.find("./Engine/ImageIDBase").get("value") != "AMm4"
    ):
        raise ValueError("Miasma Mist lost its private cloud/debuff presentation")
    sounds_root = ET.parse(
        output_root / "Data" / "alchemist_brewing_sounds.xml"
    ).getroot()
    expected_sounds = {
        ALCHEMIST_VIGOR_SOUND: {"Effector Begin": "DP01"},
        ALCHEMIST_BOTTLE_BREAK_SOUND: {
            "Begin": ALCHEMIST_BOTTLE_BREAK_WAVE_ID.decode("ascii")
        },
        ALCHEMIST_LAB_SOUND: {
            "Select": ALCHEMIST_LAB_WAVE_ID.decode("ascii")
        },
        ALCHEMIST_HERO_SOUND: {
            **{
                phase_name: private_wave.decode("ascii")
                for phase_name, _source_wave, private_wave
                in ALCHEMIST_HERO_VOICE_PHASES
            },
            "Attack": "WU03",
        },
        ALCHEMIST_CAST_VOICE_SOUND: {"Begin": "AHC2"},
        ALCHEMIST_HIRED_VOICE_SOUND: {"Begin": "AHS1"},
    }
    for sound_name, phases in expected_sounds.items():
        sound = sounds_root.find(f'./Description[@Name="{sound_name}"]')
        if sound is None:
            raise ValueError(f"Private Alchemist sound is missing: {sound_name}")
        for phase_name, wave_id in phases.items():
            wave_node = sound.find(f'./Engine/Phase[@ID="{phase_name}"]/Wave')
            if wave_node is None or wave_node.get("value") != wave_id:
                raise ValueError(
                    f"Private Alchemist sound routing changed: {sound_name}"
                )
    if sounds_root.find(
        f'./Description[@Name="{ALCHEMIST_HERO_SOUND}"]'
        '/Engine/Phase[@ID="VFX_CAST_SPELL1"]'
    ) is not None:
        raise ValueError("Alchemist default voice must not speak for Flash Flask")
    audio_entries = read_cam_entries(
        output_root / "Data" / "alchemist_audio.cam", b"WAVE"
    )
    if len(audio_entries) != 2 + len(ALCHEMIST_VOICE_WAVES):
        raise ValueError("Alchemist audio CAM has an unexpected private WAVE count")
    audio_by_id = {
        entry.name.rstrip(b"\x00")[:4]: entry.data for entry in audio_entries
    }
    expected_audio = [
        (ALCHEMIST_BOTTLE_BREAK_WAVE_ID, "alchemist-bottle-break-game.wav"),
        (ALCHEMIST_LAB_WAVE_ID, "alchemist-laboratory-select-game.wav"),
    ]
    expected_audio.extend(
        (wave_id, f"alchemist-{event}-game.wav")
        for wave_id, event, _description in ALCHEMIST_VOICE_WAVES
    )
    for wave_id, filename in expected_audio:
        expected_wave = (SOURCE_ROOT.parent / "assets" / "audio" / filename).read_bytes()
        validate_game_wave(expected_wave, filename)
        if audio_by_id.get(wave_id) != expected_wave:
            raise ValueError(f"Alchemist audio CAM lost private WAVE {wave_id!r}")
    sounddesc_entries = read_cam_entries(
        output_root / "Data" / "alchemist_sounddesc.cam", b"DSND"
    )
    expected_sounddesc = {
        ALCHEMIST_VIGOR_SOUND_ID + ALCHEMIST_VIGOR_SOUND.encode("ascii"): (
            b"DP01",
        ),
        ALCHEMIST_BOTTLE_BREAK_SOUND_ID
        + ALCHEMIST_BOTTLE_BREAK_SOUND.encode("ascii"): (
            ALCHEMIST_BOTTLE_BREAK_WAVE_ID,
        ),
        ALCHEMIST_LAB_SOUND_ID + ALCHEMIST_LAB_SOUND.encode("ascii"): (
            ALCHEMIST_LAB_WAVE_ID,
        ),
        ALCHEMIST_HERO_SOUND_ID + ALCHEMIST_HERO_SOUND.encode("ascii"): (
            *(private_wave for _phase, _source, private_wave in ALCHEMIST_HERO_VOICE_PHASES),
            b"WU03",
        ),
        ALCHEMIST_CAST_VOICE_SOUND_ID
        + ALCHEMIST_CAST_VOICE_SOUND.encode("ascii"): (b"AHC2",),
        ALCHEMIST_HIRED_VOICE_SOUND_ID
        + ALCHEMIST_HIRED_VOICE_SOUND.encode("ascii"): (b"AHS1",),
    }
    if len(sounddesc_entries) != len(expected_sounddesc):
        raise ValueError("Alchemist sounddesc CAM has an unexpected private DSND count")
    for entry in sounddesc_entries:
        name = entry.name.rstrip(b"\x00")
        expected_waves = expected_sounddesc.get(name)
        if expected_waves is None:
            raise ValueError(f"Unexpected private Alchemist DSND: {name!r}")
        internal_name = name[4:]
        if internal_name + b"\x00\x00" not in entry.data:
            raise ValueError(f"Private Alchemist DSND identity changed: {name!r}")
        for wave_id in expected_waves:
            if entry.data.count(wave_id) != 1:
                raise ValueError(
                    f"Private Alchemist DSND lost WAVE target {wave_id!r}: {name!r}"
                )
    overlays = ET.parse(
        output_root / "Data" / "alchemist_brewing_overlays.xml"
    ).getroot()
    phoenix_overlay = overlays.find(
        './Description[@Name="phoenix_phial_resurrection_effector"]'
    )
    if phoenix_overlay is None:
        raise ValueError("Private Phoenix resurrection effector is missing")
    if phoenix_overlay.find("./Engine/ImageIDBase").get("value") != "PXE1":
        raise ValueError("Phoenix resurrection effector still borrows stock HRC1 art")
    if phoenix_overlay.find("./Engine/AttachmentPointID").get("value") != "2":
        raise ValueError("Phoenix resurrection effector lost Eternal Soul's anchor")
    if (
        phoenix_overlay.find("./Engine/Script").get("GPLFunction")
        != "Phoenix_Phial_Resurrection_End"
    ):
        raise ValueError("Phoenix resurrection effector lost its private callback")
    if phoenix_overlay.find("./Engine/DefaultSound").get("value") != "Resurrection":
        raise ValueError("Phoenix resurrection effector lost the stock resurrection sound")
    if overlays.find('./Description[@Name="phoenix_phial_visual_effector"]') is not None:
        raise ValueError("Obsolete second Phoenix visual effector is still packaged")
    stone_overlay = overlays.find(
        './Description[@Name="philosophers_stone_hit_effector"]'
    )
    if stone_overlay is None:
        raise ValueError("Private Philosopher's Stone impact effector is missing")
    stock_stone_root = ET.parse(
        game_path
        / "SDK"
        / "OriginalQuests"
        / "Data"
        / "M_Overlays.xml"
    ).getroot()
    stock_stone_overlay = stock_stone_root.find('.//Description[@Name="Got_Gold"]')
    if stock_stone_overlay is None:
        raise ValueError("Stock Got_Gold position overlay is missing during validation")
    expected_stone_overlay = ET.fromstring(
        ET.tostring(stock_stone_overlay, encoding="utf-8")
    )
    expected_stone_overlay.set("ID", "AST1")
    expected_stone_overlay.set("Name", "philosophers_stone_hit_effector")
    expected_stone_overlay.set("Description", "Philosopher's Stone Transmutation")
    expected_stone_overlay.find("./Engine/ImageIDBase").set("value", "AST1")
    expected_stone_overlay.find("./Engine/DefaultSound").set("value", "0")
    def normalized_xml_node(node: ET.Element):
        return (
            node.tag,
            tuple(sorted(node.attrib.items())),
            (node.text or "").strip(),
            tuple(normalized_xml_node(child) for child in node),
        )

    if normalized_xml_node(stone_overlay) != normalized_xml_node(
        expected_stone_overlay
    ):
        raise ValueError(
            "Philosopher's Stone impact diverged from stock Got_Gold presenter"
        )
    infusion_overlay = overlays.find(
        './Description[@Name="alchemist_arcane_infusion_effector"]'
    )
    if infusion_overlay is None:
        raise ValueError("Private Arcane Infusion building effector is missing")
    stock_infusion_overlay = stock_stone_root.find(
        './/Description[@Name="got_gold_bldg"]'
    )
    if stock_infusion_overlay is None:
        raise ValueError("Stock got_gold_bldg is missing during validation")
    expected_infusion_overlay = ET.fromstring(
        ET.tostring(stock_infusion_overlay, encoding="utf-8")
    )
    expected_infusion_overlay.set("ID", "AIF1")
    expected_infusion_overlay.set("Name", "alchemist_arcane_infusion_effector")
    expected_infusion_overlay.set("Description", "Arcane Infusion")
    expected_infusion_overlay.find("./Engine/ImageIDBase").set("value", "AIF1")
    expected_infusion_overlay.find("./Engine/DefaultSound").set("value", "0")
    if normalized_xml_node(infusion_overlay) != normalized_xml_node(
        expected_infusion_overlay
    ):
        raise ValueError(
            "Arcane Infusion diverged from stock got_gold_bldg presenter"
        )
    vigor_activation_overlay = overlays.find(
        './Description[@Name="alchemist_vigor_activation_effector"]'
    )
    if vigor_activation_overlay is None:
        raise ValueError("Private Vigor activation building effector is missing")
    expected_vigor_activation = ET.fromstring(
        ET.tostring(stock_infusion_overlay, encoding="utf-8")
    )
    expected_vigor_activation.set("ID", "AIV1")
    expected_vigor_activation.set(
        "Name", "alchemist_vigor_activation_effector"
    )
    expected_vigor_activation.set("Description", "Vigor Elixir Activation")
    expected_vigor_activation.find("./Engine/ImageIDBase").set("value", "AIV1")
    expected_vigor_activation.find("./Engine/DefaultSound").set("value", "0")
    if normalized_xml_node(vigor_activation_overlay) != normalized_xml_node(
        expected_vigor_activation
    ):
        raise ValueError(
            "Vigor activation diverged from stock got_gold_bldg presenter"
        )
    ready_overlay = overlays.find(
        './Description[@Name="alchemist_reagent_ready_effector"]'
    )
    if ready_overlay is None:
        raise ValueError("Private Reagents Ready building effector is missing")
    stock_ready_overlay = stock_stone_root.find(
        './/Description[@Name="super_charge_effector"]'
    )
    if stock_ready_overlay is None:
        raise ValueError("Stock Wizard Guild Supercharge is missing")
    expected_ready_overlay = ET.fromstring(
        ET.tostring(stock_ready_overlay, encoding="utf-8")
    )
    expected_ready_overlay.set("ID", "ARR1")
    expected_ready_overlay.set(
        "Name", "alchemist_reagent_ready_effector"
    )
    expected_ready_overlay.set("Description", "Laboratory Reagents Ready")
    expected_ready_overlay.find("./Engine/ImageIDBase").set("value", "ALR1")
    expected_ready_overlay.find("./Engine/DefaultSound").set("value", "0")
    if normalized_xml_node(ready_overlay) != normalized_xml_node(
        expected_ready_overlay
    ):
        raise ValueError(
            "Reagents Ready diverged from stock Supercharge presenter"
        )
    oil_statuses = (
        (
            PARALYTIC_OIL_STATUS_ID,
            PARALYTIC_OIL_STATUS_NAME,
            "Paralytic Weapon Oil",
        ),
        (
            TRANSMUTATION_OIL_STATUS_ID,
            TRANSMUTATION_OIL_STATUS_NAME,
            "Transmutation Weapon Oil",
        ),
        (
            POISONED_WEAPON_STATUS_ID,
            POISONED_WEAPON_STATUS_NAME,
            "Poisoned Weapon",
        ),
    )
    for status_id, status_name, description in oil_statuses:
        status = overlays.find(f'./Description[@Name="{status_name}"]')
        if status is None:
            raise ValueError(f"Private oil status overlay is missing: {status_name}")
        if status.get("ID") != status_id or status.get("Description") != description:
            raise ValueError(f"Private oil status identity changed: {status_name}")
        if (
            status.find("./Engine/Menu").get("value") != "11"
            or status.find("./Engine/ImageIDBase").get("value") != "XR01"
            or status.find('./Engine/Info[@value="Static"]') is not None
            or status.find('./Engine/Info[@value="NotVisibleInISOView"]') is None
            or status.find("./Game/StackPriority").get("value") != "0"
            or status.find("./Engine/Script") is not None
        ):
            raise ValueError(
                f"Private oil status lost stock Vines/Charm contract: {status_name}"
            )
    oil_restraint = stun_root.find(
        './Description[@Name="alchemist_paralytic_oil_restraint"]'
    )
    if oil_restraint is None:
        raise ValueError("Private Paralytic Oil restraint overlay is missing")
    if (
        oil_restraint.find("./Engine/ImageIDBase").get("value") != "ASO3"
        or oil_restraint.find("./Engine/Script").get("GPLFunction")
        != "Alchemy_Paralytic_Oil_End"
    ):
        raise ValueError("Private Paralytic Oil lost the stock Vines owner contract")
    oil_restraint_imag = read_cam_entry(
        output_root / "Data" / "alchemist_maindata.cam",
        b"IMAG",
        PARALYTIC_OIL_RESTRAINT_CUSTOM,
    )
    oil_restraint_tiles = read_cam_entries(
        output_root / "Data" / "alchemist_maindata.cam",
        b"TILE",
    )
    stock_pipeline = load_stock_pipeline(SOURCE_ROOT.parent)
    oil_restraint_indices = {
        index
        for index, entry in enumerate(oil_restraint_tiles)
        if entry.name.startswith(b"ASO3Bind")
    }
    oil_restraint_references = {
        struct.unpack_from("<H", oil_restraint_imag.data, offset)[0]
        for offset in range(0, len(oil_restraint_imag.data) - 1, 2)
    }
    if (
        len(oil_restraint_indices) != 30
        or not oil_restraint_indices.issubset(oil_restraint_references)
    ):
        raise ValueError("Private Paralytic Oil restraint art is incomplete")
    for tile_prefix in (b"ASS2Bind", b"ASO3Bind"):
        restraint_frames = sorted(
            (
                entry.name.rstrip(b"\x00"),
                entry.data,
            )
            for entry in oil_restraint_tiles
            if entry.name.startswith(tile_prefix)
        )
        if len(restraint_frames) != 30:
            raise ValueError(f"Private restraint frame count changed: {tile_prefix!r}")
        if any(
            struct.unpack_from("<8H", tile, 0) != VINES_FIXED_HEADER
            for _name, tile in restraint_frames
        ):
            raise ValueError(f"Private restraint lost its fixed canvas: {tile_prefix!r}")
        opening_counts = []
        for _name, tile in restraint_frames[:5]:
            decoded = stock_pipeline.decode_indexed_v3_tile(tile)
            if decoded is None:
                raise ValueError(f"Private restraint TILE is invalid: {tile_prefix!r}")
            opening_counts.append(
                sum(value != 0 for row in decoded[2] for value in row)
            )
        if opening_counts != sorted(opening_counts) or len(set(opening_counts)) != 5:
            raise ValueError(f"Private restraint lost Frost Armor growth: {tile_prefix!r}")
        held_frame = restraint_frames[4][1]
        if any(tile != held_frame for _name, tile in restraint_frames[5:]):
            raise ValueError(f"Private restraint active loop is pulsing: {tile_prefix!r}")

    impact_frames = sorted(
        (
            entry
            for entry in oil_restraint_tiles
            if entry.name.startswith(b"ASS1Impact")
        ),
        key=lambda entry: entry.name,
    )
    if len(impact_frames) != 6 or any(
        struct.unpack_from("<8H", entry.data, 0)
        != FLASH_FLASK_ACTIVATION_HEADER
        for entry in impact_frames
    ):
        raise ValueError("Stun Serum impact lost its discrete fixed-canvas phases")
    if [item.find("./Engine/ImageIDBase").get("value") for item in buildings] != list(BUILDING_IDS):
        raise ValueError("Every Laboratory level must use its private image record")
    text_cam = output_root / "Data" / "alchemist_textdata.cam"
    gpl_text_cam = output_root / "Data" / "alchemist_gpltext.cam"
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
    item_strings = read_cam_entry(gpl_text_cam, b"STRT", b"QITM").data
    item_count = struct.unpack_from("<H", item_strings, 0)[0]
    if item_count <= PHOENIX_PHIAL_ITEM_ID:
        raise ValueError("Phoenix Phial QITM slot was not appended")
    item_offset = struct.unpack_from(
        "<I", item_strings, 4 + PHOENIX_PHIAL_ITEM_ID * 4
    )[0]
    item_end = item_strings.index(b"\x00", item_offset + 4)
    if (
        u32(item_strings, item_offset) != PHOENIX_PHIAL_ITEM_ID
        or item_strings[item_offset + 4 : item_end].decode("cp1252")
        != PHOENIX_PHIAL_ITEM_TEXT
    ):
        raise ValueError("Phoenix Phial QITM inventory text is incorrect")
    help_strings = read_cam_entry(gpl_text_cam, b"STRT", b"HPTX").data
    help_count = struct.unpack_from("<H", help_strings, 0)[0]
    help_offsets = struct.unpack_from(f"<{help_count}I", help_strings, 4)
    packaged_help: dict[int, str] = {}
    for help_offset in help_offsets:
        help_end = help_strings.index(b"\x00", help_offset + 4)
        packaged_help[u32(help_strings, help_offset)] = help_strings[
            help_offset + 4 : help_end
        ].decode("cp1252")
    for help_id, expected_text in ALCHEMIST_HELP_PAGES.items():
        if packaged_help.get(fourcc_id(help_id)) != expected_text:
            raise ValueError(f"Approved Alchemist help page is missing: {help_id}")
    if any("\u2014" in text for text in ALCHEMIST_HELP_PAGES.values()):
        raise ValueError("Approved Alchemist help copy contains a forbidden em dash")
    expected_name_tables = (
        ALCHEMIST_NAME_GIVENS,
        tuple(f" {ending}" for ending in ALCHEMIST_NAME_ENDINGS),
        (),
        (),
    )
    for table_id, expected_names in zip(
        ALCHEMIST_NAME_TABLE_IDS, expected_name_tables
    ):
        name_data = read_cam_entry(gpl_text_cam, b"STRT", table_id).data
        name_count = struct.unpack_from("<H", name_data, 0)[0]
        if name_count != len(expected_names):
            raise ValueError(
                f"Private {table_id.decode()} count changed: "
                f"expected {len(expected_names)}, got {name_count}"
            )
        name_offsets = struct.unpack_from(f"<{name_count}I", name_data, 4)
        packaged_names: list[str] = []
        for index, name_offset in enumerate(name_offsets):
            if u32(name_data, name_offset) != index:
                raise ValueError(
                    f"Private {table_id.decode()} slot {index} has the wrong ID"
                )
            name_end = name_data.index(b"\x00", name_offset + 4)
            packaged_names.append(
                name_data[name_offset + 4 : name_end].decode("cp1252")
            )
        if tuple(packaged_names) != expected_names:
            raise ValueError(f"Private {table_id.decode()} name pool changed")
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
        if enable_brewing_control
        else (103, 162, 0, 0)
    )
    if brewing_rect != expected_brewing_rect:
        raise ValueError(f"Unexpected CGAL Brewing rectangle: {brewing_rect}")
    brewing_menu = read_cam_entry(text_cam, b"SMNU", BREWING_DIALOG_ID).data
    if brewing_menu == b"":
        raise ValueError("CGBR menu is empty")
    reagent_label_marker = struct.pack(
        "<I", BREWING_REAGENT_METER_LABEL_CONTROL_ID
    )
    if brewing_menu.count(reagent_label_marker) != 1:
        raise ValueError("CGBR AP22 Reagents label is missing or duplicated")
    reagent_label_record = (
        brewing_menu.index(reagent_label_marker)
        - AP69_TITLE_CONTROL_ID_OFFSET
    )
    if (
        u32(brewing_menu, reagent_label_record) != 5
        or struct.unpack_from("<4I", brewing_menu, reagent_label_record + 0x08)
        != REAGENT_LABEL_RECT
        or u32(
            brewing_menu,
            reagent_label_record + AP69_TITLE_TEXT_INDEX_OFFSET,
        )
        != 33
        or brewing_menu[
            reagent_label_record + AP69_TITLE_FONT_OFFSET :
            reagent_label_record + AP69_TITLE_FONT_OFFSET + 4
        ]
        != b"fnt4"
    ):
        raise ValueError("CGBR AP69 Reagents title-label clone changed")
    count_marker = struct.pack("<I", BREWING_REAGENT_COUNT_CONTROL_ID)
    if brewing_menu.count(count_marker) != 1:
        raise ValueError("CGBR AP22 Reagent count control changed")
    reagent_count_record = brewing_menu.index(count_marker) - (
        AP22_HEALING_COUNT_CONTROL_ID_OFFSET
    )
    if (
        u32(brewing_menu, reagent_count_record) != 5
        or struct.unpack_from("<4I", brewing_menu, reagent_count_record + 0x08)
        != REAGENT_COUNT_RECT
        or u32(
            brewing_menu,
            reagent_count_record + AP22_HEALING_COUNT_TEXT_INDEX_OFFSET,
        )
        != 39
        or u32(
            brewing_menu,
            reagent_count_record + AP22_HEALING_COUNT_TOOLTIP_INDEX_OFFSET,
        )
        != 40
        or u32(
            brewing_menu,
            reagent_count_record + AP22_HEALING_COUNT_BINDING_ID_OFFSET,
        )
        != BREWING_REAGENT_COUNT_BINDING_ID
    ):
        raise ValueError("CGBR AP22 Reagent count clone changed")
    if brewing_menu[-8:] != b"\xff" * 8 or brewing_menu[-12:] == b"\xff" * 12:
        raise ValueError("CGBR SMNU stream does not have the stock two-word terminator")
    for menu_name, menu_data in (("CGAL", menu), ("CGBR", brewing_menu)):
        if b"ALTI" not in menu_data or b"ALBB" not in menu_data or b"ALBG" not in menu_data:
            raise ValueError(f"{menu_name} does not use the private interface art")
    if b"INTI" in menu or b"INBb" in menu or b"INBg" in menu:
        raise ValueError("CGAL still references stock interface art")
    if (
        brewing_menu.count(b"INTI") != 2
        or b"INBb" in brewing_menu
        or b"INTN" in brewing_menu
        or brewing_menu.count(b"ALBB") != 5
        or brewing_menu.count(b"ALIN") != 3
        or b"INBg" in brewing_menu
    ):
        raise ValueError(
            "CGBR recipe rows do not use five matching stock gold button plates"
        )
    if b"ALIN" not in brewing_menu:
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
        PHOENIX_LIFECYCLE_CUSTOM,
        VIGOR_EFFECT_CUSTOM,
        FLASH_FLASK_BUFF_CUSTOM,
        FLASH_FLASK_ACTIVATION_CUSTOM,
        STUN_SERUM_IMPACT_CUSTOM,
        STUN_SERUM_RESTRAINT_CUSTOM,
        STUN_SERUM_DEBUFF_CUSTOM,
        PHILOSOPHERS_STONE_HIT_CUSTOM,
        ARCANE_INFUSION_EFFECT_CUSTOM,
        VIGOR_ACTIVATION_EFFECT_CUSTOM,
        REAGENT_READY_CUSTOM,
    ):
        if not read_cam_entry(main_art, b"IMAG", name).data:
            raise ValueError(f"Private main art record is empty: {name!r}")

    art_stock = load_stock_pipeline(SOURCE_ROOT.parent)
    phoenix_lifecycle_imag = art_stock.read_cam_entry(
        main_art, b"IMAG", PHOENIX_LIFECYCLE_CUSTOM
    ).data
    phoenix_tiles = art_stock.read_cam_entries(main_art, b"TILE")
    lifecycle_sets = art_stock.single_direction_imag_animation_sets(
        phoenix_lifecycle_imag
    )
    if (
        len(lifecycle_sets) != 1
        or lifecycle_sets[0][0] != PHOENIX_LIFECYCLE_ANIMATION_SET
    ):
        raise ValueError("Private Phoenix animation lost stock HRC1 timing")
    lifecycle_indices = art_stock.animation_tile_indices(
        phoenix_lifecycle_imag,
        len(phoenix_tiles),
    )
    if len(lifecycle_indices) != PHOENIX_LIFECYCLE_FRAMES:
        raise ValueError("Private Phoenix animation lost HRC1's 29-frame lifecycle")
    if len(set(lifecycle_indices)) != PHOENIX_LIFECYCLE_FRAMES:
        raise ValueError("Phoenix resurrection does not own 29 private frame TILEs")
    visible_pixel_counts: list[int] = []
    for tile_index in lifecycle_indices:
        tile_entry = phoenix_tiles[tile_index]
        if not tile_entry.name.rstrip(b"\x00").startswith(b"PXE1Phoenix"):
            raise ValueError("Phoenix resurrection references non-private artwork")
        tile = tile_entry.data
        if struct.unpack_from("<8H", tile, 0) != PHOENIX_EFFECT_HEADER:
            raise ValueError("Phoenix animation frame lost its fixed Eternal Soul anchor")
        if art_stock.tile_palette_index(tile) != PHOENIX_EFFECT_PALETTE:
            raise ValueError("Phoenix animation frame is not using stock fire palette 505")
        decoded = art_stock.decode_indexed_v3_tile(tile)
        if decoded is None:
            raise ValueError("Phoenix animation frame is not a valid indexed TILE")
        visible_pixel_counts.append(
            sum(value != 0 for row in decoded[2] for value in row)
        )
    visible_phase_counts = visible_pixel_counts[:PHOENIX_VISIBLE_FRAMES]
    transparent_tail_counts = visible_pixel_counts[PHOENIX_VISIBLE_FRAMES:]
    if (
        not all(visible_phase_counts[:-1])
        or visible_phase_counts[-1] != 0
        or max(visible_phase_counts) <= visible_phase_counts[0]
        or any(transparent_tail_counts)
    ):
        raise ValueError("Phoenix animation lost its growth/peak/fade progression")
    if any(
        entry.name.startswith((b"HRC1", b"XR30", b"PXV1"))
        for entry in art_stock.read_cam_entries(main_art, b"IMAG")
    ):
        raise ValueError("Alchemist art CAM contains a stock or obsolete Phoenix channel")

    reagent_ready_imag = art_stock.read_cam_entry(
        main_art, b"IMAG", REAGENT_READY_CUSTOM
    ).data
    stock_main = game_path / "Data" / "maindata.cam"
    stock_reagent_ready_imag = art_stock.read_cam_entry(
        stock_main, b"IMAG", REAGENT_READY_SOURCE
    ).data
    if (
        hashlib.sha256(stock_reagent_ready_imag).hexdigest()
        != REAGENT_READY_SOURCE_SHA256
    ):
        raise ValueError("Stock Wizard Guild Supercharge IMAG changed")
    if struct.unpack_from("<I", reagent_ready_imag, 104)[0] != (
        (REAGENT_READY_FRAME_COUNT << 16) | REAGENT_READY_STREAM_COUNT
    ):
        raise ValueError("Reagents Ready lost Supercharge's 30-frame/two-stream table")
    reagent_ready_entries = {
        entry.name.rstrip(b"\x00"): (index, entry.data)
        for index, entry in enumerate(phoenix_tiles)
        if entry.name.rstrip(b"\x00").startswith(b"ALR1Ready")
    }
    if len(reagent_ready_entries) != (
        REAGENT_READY_FRAME_COUNT * REAGENT_READY_STREAM_COUNT
    ):
        raise ValueError("Reagents Ready lost its 60 private stream TILEs")
    stock_main_tiles = art_stock.read_cam_entries(stock_main, b"TILE")
    stock_ready_payloads = tuple(
        stock_main_tiles[index].data for index in REAGENT_READY_SOURCE_TILES
    )
    if (
        hashlib.sha256(b"".join(stock_ready_payloads)).hexdigest()
        != REAGENT_READY_SOURCE_TILE_AGGREGATE_SHA256
    ):
        raise ValueError("Stock Wizard Guild Supercharge TILE family changed")
    if tuple(
        art_stock.tile_palette_index(payload) for payload in stock_ready_payloads
    ) != REAGENT_READY_SOURCE_PALETTES:
        raise ValueError("Stock Wizard Guild Supercharge palette family changed")
    ready_source_path = SOURCE_ROOT.parent / REAGENT_READY_ART_SOURCE
    if sha256_file(ready_source_path) != REAGENT_READY_ART_SOURCE_SHA256:
        raise ValueError("Approved Reagents Ready enchantment source changed")
    owner_candidates = [
        entry.data
        for entry in phoenix_tiles
        if entry.name.rstrip(b"\x00") == b"ALB3Act1027F00"
    ]
    if len(owner_candidates) != 1:
        raise ValueError("Reagents Ready lost its level-3 Laboratory owner")
    owner_hotspot = struct.unpack_from("<hh", owner_candidates[0], 10)
    pool_center = tuple(
        round(value * RUNTIME_BUILDING_SCALE)
        for value in REAGENT_READY_POOL_CENTER_NATIVE
    )
    owner_to_pool = tuple(
        pool - owner for pool, owner in zip(pool_center, owner_hotspot)
    )
    effective_hotspot = tuple(
        center - displacement
        for center, displacement in zip(
            REAGENT_READY_EFFECT_CENTER,
            owner_to_pool,
        )
    )
    ready_payloads_by_stream: list[list[bytes]] = [[], []]
    ready_counts_by_stream: list[list[int]] = [[], []]
    ready_bounds_by_stream: list[list[tuple[int, int, int, int]]] = [[], []]
    restored_reagent_ready = bytearray(reagent_ready_imag)
    for stream, (prefix, offsets) in enumerate(
        zip(("ALR1ReadyB", "ALR1ReadyM"), REAGENT_READY_STREAM_REFERENCE_OFFSETS)
    ):
        for frame, offset in enumerate(offsets):
            source_word = struct.unpack_from("<I", stock_reagent_ready_imag, offset)[0]
            private_word = struct.unpack_from("<I", reagent_ready_imag, offset)[0]
            reference_flags = source_word >> 16
            if private_word >> 16 != reference_flags:
                raise ValueError("Reagents Ready changed a stock mirror flag")
            name = f"{prefix}{frame:02d}".encode("ascii")
            private_index, private_payload = reagent_ready_entries[name]
            if private_word & 0xFFFF != private_index:
                raise ValueError("Reagents Ready IMAG references the wrong private TILE")
            if art_stock.tile_palette_index(private_payload) != REAGENT_READY_PALETTE:
                raise ValueError("Reagents Ready lost its private purple palette")
            decoded = art_stock.decode_indexed_v3_tile(private_payload)
            if decoded is None or (decoded[1], decoded[0]) != REAGENT_READY_CANVAS:
                raise ValueError("Reagents Ready lost its fixed custom canvas")
            authored_hotspot = list(struct.unpack_from("<hh", private_payload, 10))
            visible = [
                [x, y, value]
                for y, row in enumerate(decoded[2])
                for x, value in enumerate(row)
                if value != 0
            ]
            if not visible or any(247 <= value[2] <= 250 for value in visible):
                raise ValueError("Reagents Ready custom art is empty or has controls")
            if reference_flags & 0x2000:
                authored_hotspot[0] = REAGENT_READY_CANVAS[0] - 1 - authored_hotspot[0]
                for value in visible:
                    value[0] = REAGENT_READY_CANVAS[0] - 1 - value[0]
            if reference_flags & 0x4000:
                authored_hotspot[1] = REAGENT_READY_CANVAS[1] - 1 - authored_hotspot[1]
                for value in visible:
                    value[1] = REAGENT_READY_CANVAS[1] - 1 - value[1]
            if tuple(authored_hotspot) != effective_hotspot:
                raise ValueError("Reagents Ready lost its fixed pool registration")
            xs = [value[0] for value in visible]
            ys = [value[1] for value in visible]
            bounds = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
            ready_payloads_by_stream[stream].append(private_payload)
            ready_counts_by_stream[stream].append(len(visible))
            ready_bounds_by_stream[stream].append(bounds)
            struct.pack_into("<I", restored_reagent_ready, offset, source_word)
    body_bounds = ready_bounds_by_stream[0]
    if hashlib.sha256(
        b"".join(
            payload
            for stream_payloads in ready_payloads_by_stream
            for payload in stream_payloads
        )
    ).hexdigest() != REAGENT_READY_CUSTOM_TILE_AGGREGATE_SHA256:
        raise ValueError("Reagents Ready private TILE family changed")
    if (
        any(len(set(payloads)) != REAGENT_READY_FRAME_COUNT for payloads in ready_payloads_by_stream)
        or min(ready_counts_by_stream[0]) < 180
        or max(ready_counts_by_stream[0]) > min(ready_counts_by_stream[0]) * 1.45
        or min(ready_counts_by_stream[1]) < 5
        or max(bound[0] for bound in body_bounds) - min(bound[0] for bound in body_bounds) > 8
        or max(bound[2] for bound in body_bounds) - min(bound[2] for bound in body_bounds) > 8
        or any(
            not bound[0] <= REAGENT_READY_EFFECT_CENTER[0] <= bound[2]
            or abs(bound[3] - REAGENT_READY_EFFECT_CENTER[1]) > 5
            for bound in body_bounds
        )
    ):
        raise ValueError("Reagents Ready custom stream loop changed size or density")
    if bytes(restored_reagent_ready) != stock_reagent_ready_imag:
        raise ValueError("Reagents Ready changed Supercharge stream timing/topology")

    for image_name, tile_prefix, frame_count, palette_index in (
        (VIGOR_EFFECT_CUSTOM, b"ALV1Spark", 29, 560),
        (FLASH_FLASK_BUFF_CUSTOM, b"AFF1Flask", 29, 560),
        (FLASH_FLASK_ACTIVATION_CUSTOM, b"AFF2Flash", 6, 505),
        (
            PHILOSOPHERS_STONE_HIT_CUSTOM,
            b"AST1StoneHit",
            PHILOSOPHERS_STONE_FRAMES,
            505,
        ),
    ):
        image = art_stock.read_cam_entry(main_art, b"IMAG", image_name).data
        indices = art_stock.animation_tile_indices(image, len(phoenix_tiles))
        if len(indices) != frame_count or len(set(indices)) != frame_count:
            raise ValueError(f"Private overlay frame table changed: {image_name!r}")
        for index in indices:
            tile_entry = phoenix_tiles[index]
            if not tile_entry.name.rstrip(b"\x00").startswith(tile_prefix):
                raise ValueError(f"Private overlay references stock art: {image_name!r}")
            if art_stock.tile_palette_index(tile_entry.data) != palette_index:
                raise ValueError(f"Private overlay palette changed: {image_name!r}")
            decoded = art_stock.decode_indexed_v3_tile(tile_entry.data)
            if decoded is None or not any(
                value != 0 for row in decoded[2] for value in row
            ):
                raise ValueError(f"Private overlay has a blank frame: {image_name!r}")
            if image_name == FLASH_FLASK_ACTIVATION_CUSTOM and (
                struct.unpack_from("<8H", tile_entry.data, 0)
                != FLASH_FLASK_ACTIVATION_HEADER
            ):
                raise ValueError("Flash Flask activation lost Eternal Soul's anchor")
        if image_name == FLASH_FLASK_ACTIVATION_CUSTOM:
            set_offset = struct.unpack_from("<I", image, 28)[0]
            if (
                struct.unpack_from("<I", image, set_offset + 28)[0]
                != FLASH_FLASK_ACTIVATION_DELAY_MS
            ):
                raise ValueError("Flash Flask activation lost stock default cadence")

    stock_mx_main = game_path / "DataMX" / "mx_maindata.cam"
    stock_stone_image = art_stock.read_cam_entry(
        game_path / "Data" / "maindata.cam",
        b"IMAG",
        b"HRC1resurrect_e",
    ).data
    stock_mx_tiles = art_stock.read_cam_entries(
        game_path / "Data" / "maindata.cam", b"TILE"
    )
    stock_stone_indices = art_stock.animation_tile_indices(
        stock_stone_image, len(stock_mx_tiles)
    )
    private_stone_image = art_stock.read_cam_entry(
        main_art, b"IMAG", PHILOSOPHERS_STONE_HIT_CUSTOM
    ).data
    private_stone_indices = art_stock.animation_tile_indices(
        private_stone_image, len(phoenix_tiles)
    )
    if (
        len(stock_stone_indices) != PHILOSOPHERS_STONE_FRAMES
        or len(private_stone_indices) != PHILOSOPHERS_STONE_FRAMES
    ):
        raise ValueError("Philosopher's Stone lost HRC1's 29-frame lifecycle")
    restored_stone_image = art_stock.remap_imag_animation_tiles(
        private_stone_image,
        dict(zip(private_stone_indices, stock_stone_indices)),
    )
    restored_stone_image = set_single_overlay_animation_delay(
        restored_stone_image,
        PHILOSOPHERS_STONE_ANIMATION_SET,
        (PHILOSOPHERS_STONE_DELAY_MS,),
        0,
    )
    if restored_stone_image != stock_stone_image:
        raise ValueError("Philosopher's Stone changed HRC1 timing or topology")
    stone_set_offset = struct.unpack_from("<I", private_stone_image, 28)[0]
    if (
        struct.unpack_from("<I", private_stone_image, stone_set_offset + 28)[0]
        != PHILOSOPHERS_STONE_DELAY_MS
    ):
        raise ValueError("Philosopher's Stone lost HRC1's stock default cadence")
    for private_index in private_stone_indices:
        if (
            struct.unpack_from("<8H", phoenix_tiles[private_index].data, 0)
            != PHILOSOPHERS_STONE_HEADER
        ):
            raise ValueError("Philosopher's Stone lost its enlarged centered canvas")

    for (
        effect_label,
        effect_name,
        expected_set,
        expected_frames,
        expected_delay,
        expected_header,
        expected_palette,
    ) in (
        (
            "Arcane Infusion",
            ARCANE_INFUSION_EFFECT_CUSTOM,
            ARCANE_INFUSION_ANIMATION_SET,
            ARCANE_INFUSION_FRAMES,
            ARCANE_INFUSION_DELAY_MS,
            ARCANE_INFUSION_HEADER,
            ARCANE_INFUSION_PALETTE,
        ),
        (
            "Vigor activation",
            VIGOR_ACTIVATION_EFFECT_CUSTOM,
            VIGOR_ACTIVATION_ANIMATION_SET,
            VIGOR_ACTIVATION_FRAMES,
            VIGOR_ACTIVATION_DELAY_MS,
            VIGOR_ACTIVATION_HEADER,
            VIGOR_ACTIVATION_PALETTE,
        ),
    ):
        effect_image = art_stock.read_cam_entry(
            main_art, b"IMAG", effect_name
        ).data
        effect_set_id, effect_set_offset = struct.unpack_from(
            "<II", effect_image, 24
        )
        if (
            effect_set_id != expected_set
            or struct.unpack_from("<I", effect_image, effect_set_offset + 28)[0]
            != expected_delay
        ):
            raise ValueError(f"{effect_label} lost HRC1's stock cadence")
        effect_indices = art_stock.animation_tile_indices(
            effect_image, len(phoenix_tiles)
        )
        if (
            len(effect_indices) != expected_frames
            or len(set(effect_indices)) != expected_frames
        ):
            raise ValueError(f"{effect_label} lost its 29 private frames")
        for tile_index in effect_indices:
            tile = phoenix_tiles[tile_index].data
            if struct.unpack_from("<8H", tile, 0) != expected_header:
                raise ValueError(f"{effect_label} lost its fixed Laboratory canvas")
            if art_stock.tile_palette_index(tile) != expected_palette:
                raise ValueError(f"{effect_label} lost its private effect palette")
            decoded = art_stock.decode_indexed_v3_tile(tile)
            if decoded is None or not any(
                pixel != 0 for row in decoded[2] for pixel in row
            ):
                raise ValueError(f"{effect_label} has a blank or invalid frame")

    for name in (
        b"ALTIraw textures",
        b"ALBBbuilding frame",
        b"ALBGbuilding dialog",
        b"ALINrecipe icons",
        b"ALWIweapon oil icon",
        b"ALPIphial icon",
        b"ALSRalchemy progress",
        TACTICAL_CURSOR_CUSTOM,
    ):
        if not read_cam_entry(interface_art, b"IMAG", name).data:
            raise ValueError(f"Private interface art record is empty: {name!r}")
    main_tile_entries = read_cam_entries(main_art, b"TILE")
    main_prefixes = (
        b"ALC1",
        b"ALB1",
        b"ALB2",
        b"ALB3",
        b"PXF1",
        b"PXE1",
        b"ALV1",
        b"AFF1",
        b"AFF2",
        b"AST1",
        b"AIF1",
        b"AIV1",
        b"AMm",
        b"ATm",
    )
    first_private_main = next(
        (
            index
            for index, entry in enumerate(main_tile_entries)
            if entry.name.rstrip(b"\x00").startswith(main_prefixes)
        ),
        None,
    )
    if first_private_main is None or not main_tile_entries[first_private_main].data:
        raise ValueError("Private TILE payloads are missing from alchemist_maindata.cam")
    if any(entry.data for entry in main_tile_entries[:first_private_main]):
        raise ValueError("alchemist_maindata.cam overwrites a stock TILE slot")

    # CUR1 is a complete stock expansion record. Retain every original cursor
    # set literally, then append Stone's exact set-1014 clone whose four
    # visible Lightning glyph references point at its private icon TILE.
    stock_interface_art = game_path / "DataMX" / "mx_interfacedata.cam"
    stock_cursor = read_cam_entry(
        stock_interface_art, b"IMAG", TACTICAL_CURSOR_SOURCE
    ).data
    private_cursor = read_cam_entry(
        interface_art, b"IMAG", TACTICAL_CURSOR_CUSTOM
    ).data
    if len(stock_cursor) != 8024 or len(private_cursor) != 8312:
        raise ValueError("Private CUR1 record length changed")
    stock_cursor_count = u32(stock_cursor, 20)
    private_cursor_count = u32(private_cursor, 20)
    if stock_cursor_count != 34 or private_cursor_count != 35:
        raise ValueError("Private CUR1 animation-set count changed")
    stock_cursor_entries = [
        struct.unpack_from("<II", stock_cursor, 24 + index * 8)
        for index in range(stock_cursor_count)
    ]
    private_cursor_entries = [
        struct.unpack_from("<II", private_cursor, 24 + index * 8)
        for index in range(private_cursor_count)
    ]
    if private_cursor[:20] != stock_cursor[:20] or private_cursor_entries[:34] != [
        (set_id, offset + 8) for set_id, offset in stock_cursor_entries
    ]:
        raise ValueError("Private CUR1 changed a stock animation-set entry")
    if private_cursor_entries[34:] != [
        (PHILOSOPHERS_STONE_CURSOR_SET_ID, 8032),
    ]:
        raise ValueError("Private CUR1 cursor set identities or offsets changed")
    if private_cursor[304:8032] != stock_cursor[296:8024]:
        raise ValueError("Private CUR1 changed a stock animation body")
    stock_entry_map = dict(stock_cursor_entries)
    private_entry_map = dict(private_cursor_entries)
    stock_lightning_body = stock_cursor[
        stock_entry_map[TACTICAL_CURSOR_TEMPLATE_SET_ID] :
        min(
            offset
            for _set_id, offset in stock_cursor_entries
            if offset > stock_entry_map[TACTICAL_CURSOR_TEMPLATE_SET_ID]
        )
    ]
    if len(stock_lightning_body) != 280 or private_cursor[
        private_entry_map[TACTICAL_CURSOR_TEMPLATE_SET_ID] :
        private_entry_map[TACTICAL_CURSOR_TEMPLATE_SET_ID] + 280
    ] != stock_lightning_body:
        raise ValueError("Private CUR1 changed stock Lightning cursor set 1014")

    interface_tile_entries = read_cam_entries(interface_art, b"TILE")
    disabled_plate_names = {
        b"ALBB" + f"{group[2]:05d}".encode("ascii")
        for group in RECIPE_PRIVATE_PLATE_TILE_GROUPS
    }
    packaged_disabled_plates = [
        (index, entry)
        for index, entry in enumerate(interface_tile_entries)
        if entry.name.rstrip(b"\x00") in disabled_plate_names
    ]
    if len(packaged_disabled_plates) != len(disabled_plate_names):
        raise ValueError("Private disabled recipe plates are missing or duplicated")
    for _index, entry in packaged_disabled_plates:
        decoded = art_stock.decode_indexed_v3_tile(entry.data)
        if decoded is None or any(
            decoded[2][y][x] == 0
            for y in range(1, len(decoded[2]) - 1)
            for x in range(1, len(decoded[2][y]) - 1)
        ):
            raise ValueError("Packaged disabled recipe plate retained stock holes")
    private_building_frame = read_cam_entry(
        interface_art, b"IMAG", b"ALBBbuilding frame"
    ).data
    private_building_frame_refs = {
        u32(private_building_frame, offset) & 0xFFFF
        for offset in range(0, len(private_building_frame) - 3, 4)
    }
    if not {
        index for index, _entry in packaged_disabled_plates
    }.issubset(private_building_frame_refs):
        raise ValueError("ALBB does not reference all private disabled recipe plates")
    cursor_tile_indices: dict[bytes, int] = {}
    for index, entry in enumerate(interface_tile_entries):
        short_name = entry.name.rstrip(b"\x00")
        if short_name == b"ALCSStoneCursor":
            cursor_tile_indices[short_name] = index
    if set(cursor_tile_indices) != {b"ALCSStoneCursor"}:
        raise ValueError("Private tactical cursor TILEs are missing or duplicated")
    glyph_offsets = (0x7C, 0xAC, 0xE4, 0x10C)
    for set_id, tile_name in (
        (PHILOSOPHERS_STONE_CURSOR_SET_ID, b"ALCSStoneCursor"),
    ):
        expected_body = bytearray(stock_lightning_body)
        tile_index = cursor_tile_indices[tile_name]
        for offset in glyph_offsets:
            original_ref = u32(expected_body, offset)
            struct.pack_into(
                "<I",
                expected_body,
                offset,
                (original_ref & 0xFFFF0000) | tile_index,
            )
        actual_body = private_cursor[
            private_entry_map[set_id] : private_entry_map[set_id] + 280
        ]
        if actual_body != bytes(expected_body):
            raise ValueError(f"Private CUR1 set {set_id} is not an exact stock clone")
        tile = interface_tile_entries[tile_index].data
        if (
            struct.unpack_from("<H", tile, 0)[0] != 3
            or struct.unpack_from("<HH", tile, 2) != (40, 40)
            or struct.unpack_from("<H", tile, 20)[0] != 1
            or u32(tile, 22) >= len(tile)
        ):
            raise ValueError(f"Private CUR1 set {set_id} has an invalid cursor TILE")
        decoded = art_stock.decode_indexed_v3_tile(tile)
        if decoded is None or not any(
            pixel != 0 for row in decoded[2] for pixel in row
        ):
            raise ValueError(f"Private CUR1 set {set_id} has a blank cursor TILE")
        if any(
            pixel >= 247 for row in decoded[2] for pixel in row
        ):
            raise ValueError(
                f"Private CUR1 set {set_id} uses stock cursor/control indices"
            )

    stock_expansion_tiles = read_cam_entries(stock_interface_art, b"TILE")
    if len(interface_tile_entries) <= 53 or len(stock_expansion_tiles) <= 53:
        raise ValueError("Expansion CUR1 stock TILE range changed")
    for tile_index in range(17, 54):
        if interface_tile_entries[tile_index] != stock_expansion_tiles[tile_index]:
            raise ValueError(
                f"Private CUR1 did not preserve DataMX TILE {tile_index} literally"
            )
    interface_prefixes = (
        b"ALTI",
        b"ALBB",
        b"ALBG",
        b"ALIN",
        b"ALWI",
        b"ALPI",
        b"ALSR",
        b"ALCS",
    )
    first_private_interface = next(
        (
            index
            for index, entry in enumerate(interface_tile_entries)
            if entry.name.rstrip(b"\x00").startswith(interface_prefixes)
        ),
        None,
    )
    if (
        first_private_interface is None
        or not interface_tile_entries[first_private_interface].data
    ):
        raise ValueError(
            "Private TILE payloads are missing from alchemist_interfacedata.cam"
        )
    if any(
        entry.data
        for index, entry in enumerate(interface_tile_entries[:first_private_interface])
        if not 17 <= index <= 53
    ):
        raise ValueError(
            "alchemist_interfacedata.cam overwrites an unrelated stock TILE slot"
        )
    brewing_strings = read_cam_entry(text_cam, b"STRT", BREWING_DIALOG_ID).data
    if b"Vigor Elixir\x00" not in brewing_strings:
        raise ValueError("CGBR Vigor Elixir label is missing")
    if b"Invigorated\x00" not in brewing_strings:
        raise ValueError("CGBR active progress label is missing")
    if b"Phoenix Phial\x00" not in brewing_strings:
        raise ValueError("CGBR Phoenix Phial label is missing")
    if b"Reagents\x00" not in brewing_strings or b"0\x00" not in brewing_strings:
        raise ValueError("CGBR AP22-shaped Reagent label/count strings are missing")
    for private_text in (
        b"Arcane Infusion\x00",
        b"Permanently grant all current and future Alchemists 25 Magic Resistance. Requires 10 Reagents. One use per kingdom.\x00",
        b"Philosopher's Stone\x00",
        b"Transmute one ordinary enemy into 3000 gold. Requires 10 Reagents.\x00",
    ):
        if private_text not in brewing_strings:
            raise ValueError(f"CGBR private stock-row text is missing: {private_text!r}")
    brewing_string_count = struct.unpack_from("<H", brewing_strings, 0)[0]
    if brewing_string_count <= 28:
        raise ValueError("CGBR active progress label is not present at STRT index 28")
    brewing_string_offsets = struct.unpack_from(
        f"<{brewing_string_count}I", brewing_strings, 4
    )
    for index, expected_text in (
        (4, b"Arcane Infusion"),
        (
            5,
            b"Permanently grant all current and future Alchemists 25 Magic Resistance. Requires 10 Reagents. One use per kingdom.",
        ),
        (7, b"Philosopher's Stone"),
        (8, b"Transmute one ordinary enemy into 3000 gold. Requires 10 Reagents."),
        (33, b"Reagents"),
        (39, b"0"),
        (40, b"This Laboratory's current number of stored Reagents."),
    ):
        string_offset = brewing_string_offsets[index]
        string_end = brewing_strings.index(b"\x00", string_offset + 4)
        if brewing_strings[string_offset + 4 : string_end] != expected_text:
            raise ValueError(
                f"CGBR stock-row STRT index {index} changed from {expected_text!r}"
            )
    active_label_offset = brewing_string_offsets[28]
    active_label_end = brewing_strings.index(b"\x00", active_label_offset + 4)
    if brewing_strings[active_label_offset + 4 : active_label_end] != b"Invigorated":
        raise ValueError("CGBR STRT index 28 is not the Invigorated label")
    if brewing_menu.count(b"ALSR") != 3 or b"INSr" in brewing_menu:
        raise ValueError("CGBR private progress art displays are missing")
    first_progress_art = brewing_menu.index(b"ALSR")
    for control_id, control_offset, label in (
        (STOCK_FERVUS_SECOND_SPELL_CONTROL_ID, 0x03AC, "stock Fervus 0x1132"),
        (STOCK_FERVUS_THIRD_SPELL_CONTROL_ID, 0x0554, "stock Fervus 0x1133"),
    ):
        marker = struct.pack("<I", control_id)
        if brewing_menu.count(marker) != 1 or u32(brewing_menu, control_offset) != control_id:
            raise ValueError(f"CGBR {label} native row is missing or moved")
        if control_offset >= first_progress_art:
            raise ValueError(f"CGBR {label} no longer occupies its native AP69 slot")
    for art_offset, image_set, label in (
        (0x01C4, 0x405, "Vigor Elixir"),
        (0x036C, 0x406, "Arcane Infusion"),
        (0x0514, 0x407, "Philosopher's Stone"),
    ):
        if (
            brewing_menu[art_offset : art_offset + 4] != b"ALBB"
            or u32(brewing_menu, art_offset + 8) != image_set
        ):
            raise ValueError(f"CGBR {label} lost its private AP69 button plate")
    if brewing_menu[0x03B4:0x03B8] != b"fnt7" or brewing_menu[0x055C:0x0560] != b"fnt7":
        raise ValueError("CGBR private stock rows lost Majesty's centered spell font")
    if u32(brewing_menu, 0x0348) != 162 or u32(brewing_menu, 0x04F0) != 162:
        raise ValueError("CGBR Parts labels do not own their complete action plates")
    for offset, rectangle, label in (
        (0x02D8, (2, 137, 25, 25), "0x1132 icon"),
        (0x032C, (30, 139, 162, 20), "0x1132 action"),
        (0x03E8, (150, 140, 40, 17), "0x1132 price"),
        (0x0480, (2, 162, 25, 25), "0x1133 icon"),
        (0x04D4, (30, 164, 162, 20), "0x1133 action"),
        (0x0590, (150, 165, 40, 17), "0x1133 price"),
    ):
        if struct.unpack_from("<4I", brewing_menu, offset) != rectangle:
            raise ValueError(f"CGBR stock Fervus {label} rectangle changed")
    for private_id in (
        BREWING_ARCANE_INFUSION_CONTROL_ID,
        BREWING_PHILOSOPHERS_STONE_CONTROL_ID,
    ):
        if struct.pack("<I", private_id) in brewing_menu:
            raise ValueError(
                "CGBR sovereign visuals must retain genuine stock Fervus IDs"
            )
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
        output_root / "Data" / "alchemist_miscdata.cam", b"DATA", b"BDEP"
    ).data
    stock_bdep_path = stock_building_dependency_cam(game_path)
    stock_bdep = read_cam_entry(stock_bdep_path, b"DATA", b"BDEP").data
    validate_bdep_payload(bdep, stock_bdep, include_phantoms)
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
    if "(attack_action basic_attack)" not in hero_data:
        raise ValueError("Alchemist must use Warrior's stock basic melee action")
    if "(attacktype 1)" not in hero_data:
        raise ValueError("Alchemist must use stock hand-to-hand hit resolution")
    if "(special_attack_action basic_attack)" not in hero_data:
        raise ValueError("Alchemist Fire Balm must retain a valid stock melee action")
    if "Cultist_Dagger" in hero_data or "Fire_Dagger" in hero_data:
        raise ValueError("Alchemist must not retain Cultist projectile attacks")
    for balance_contract in (
        "(PercentageHPRetreat 30)",
        "(enemy_estimation .9)",
        "(self_estimation 1.4)",
    ):
        if balance_contract not in hero_data:
            raise ValueError(
                f"Alchemist early-survival contract is missing: {balance_contract}"
            )
    alchemist_tree = (output_root / "GPL" / "Alchemist_Rogue.gpl").read_text(
        encoding="utf-8"
    )
    for grant_contract in (
        "expression #Alchemist_Hire_Grant 100",
        "#ATTRIB_StoredGold",
        "#Alchemist_Hire_Grant",
    ):
        if grant_contract not in alchemist_tree:
            raise ValueError(f"Alchemist hire grant is missing: {grant_contract}")
    if "expression #Alchemist_Town_Shopping_Range 500" not in alchemist_tree:
        raise ValueError("Alchemist shopping lost the Call to Grave spacing boundary")
    if "expression #Alchemist_Funded_Resupply_Gold 2000" not in alchemist_tree:
        raise ValueError("Alchemist funded-resupply purse threshold changed")
    embassy_source = (output_root / "GPL" / "Alchemist_Embassy.gpl").read_text(
        encoding="utf-8"
    )
    if embassy_source.count("Function Random_Hero_Type") != 1:
        raise ValueError("Alchemist Embassy support lost stock Random_Hero_Type")
    if include_phantoms:
        if (
            embassy_source.count('return "Alchemist";') != 2
            or embassy_source.count('return "Phantom";') != 2
            or "$Alchemist_Compat_Phantom_Max_Haunt_Level(ThisAgent) > 0"
            not in embassy_source
        ):
            raise ValueError("Haunt-compatible Embassy selector is incomplete")
    else:
        if (
            embassy_source.count('return "Alchemist";') != 1
            or 'return "Paladin";' not in embassy_source
            or 'return "Phantom";' in embassy_source
        ):
            raise ValueError("Standalone Embassy selector changed stock eligibility")
    guild_title_source = (
        output_root / "GPL" / "Alchemist_Guild_Title.gpl"
    ).read_text(encoding="utf-8")
    expected_guild_title = build_alchemist_guild_title(
        game_path
        / "SDK"
        / "OriginalQuests"
        / "GPLMx"
        / "TaskModules"
        / "Buildings"
        / "Mausoleum.gpl"
    )
    if guild_title_source != expected_guild_title:
        raise ValueError(
            "Alchemist mausoleum support is not the literal stock Guild_Title clone"
        )
    if guild_title_source.count(
        'else if ( ThisAgent\'s "title" == "Alchemist" )'
    ) != 1 or guild_title_source.count(
        'return "AlchemistsLaboratory";'
    ) != 1:
        raise ValueError("Alchemist mausoleum home mapping is missing or duplicated")
    for forbidden_mausoleum_override in (
        "Mausoleum_Resurrect_Begin",
        "Mausoleum_Resurrect_Finish",
        "Find_New_Home",
        "Guild_Placement_Check",
    ):
        if forbidden_mausoleum_override in guild_title_source:
            raise ValueError(
                "Alchemist mausoleum support replaced more than stock Guild_Title"
            )
    brewing_source = (
        output_root / "GPL" / "Alchemist_Brewing.gpl"
    ).read_text(encoding="utf-8")
    vigor_charge = '$AdjustPlayerData(Palace, "Gold", -1500)'
    vigor_visual = (
        '$CreateEffector(ThisAgent, '
        '"alchemist_vigor_activation_effector", 0)'
    )
    vigor_targets = "$ListObjects(ThisAgent, \"hero\", -1, Heroes"
    if (
        brewing_source.count(vigor_visual) != 1
        or vigor_charge not in brewing_source
        or vigor_targets not in brewing_source
        or not (
            brewing_source.index(vigor_charge)
            < brewing_source.index(vigor_visual)
            < brewing_source.index(vigor_targets)
        )
    ):
        raise ValueError(
            "Vigor activation lost its stock selected-building one-shot order"
        )
    adopt_source = (output_root / "GPL" / "Alchemist_Adopt.gpl").read_text(
        encoding="utf-8"
    )
    expected_adopt = build_alchemist_adopt(
        game_path
        / "SDK"
        / "OriginalQuests"
        / "GPLMx"
        / "mx_Building_Births.gpl"
    )
    if adopt_source != expected_adopt:
        raise ValueError(
            "Alchemist adoption hooks diverged from the literal stock clone"
        )
    if adopt_source.count(
        '$DeleteEffector ( Stray, "alchemist_invigorating_elixer_icon" );'
    ) != 1:
        raise ValueError("Vigor adoption cleanup is missing or duplicated")
    if adopt_source.count("$Alchemist_Apply_Arcane_Infusion ( stray );") != 1:
        raise ValueError("Arcane Infusion adoption grant is missing or duplicated")
    stock_gplmx = game_path / "SDK" / "OriginalQuests" / "GPLMx"
    bazaar_source = (
        output_root / "GPL" / "Alchemist_Magic_Bazaar.gpl"
    ).read_text(encoding="utf-8")
    expected_bazaar_source = build_alchemist_magic_bazaar(
        stock_gplmx / "TaskModules" / "Buildings" / "Magic_Bazaar.gpl"
    )
    if bazaar_source != expected_bazaar_source:
        raise ValueError("Alchemist Bazaar shopping diverged from its stock clones")
    nearby_equipment_source = (
        output_root / "GPL" / "Alchemist_Nearby_Equipment.gpl"
    ).read_text(encoding="utf-8")
    expected_nearby_equipment_source = build_alchemist_nearby_equipment(
        stock_gplmx
        / "DecisionTrees"
        / "Modules"
        / "mx_Purchase_Equipment.gpl"
    )
    if nearby_equipment_source != expected_nearby_equipment_source:
        raise ValueError(
            "Alchemist nearby equipment shopping diverged from its stock clone"
        )
    priority_contract = (
        "$Alchemist_Return_Full_Reagent_Load(thisagent)",
        "$Alchemist_Purchase_Nearby_Equipment(thisagent)",
        "$Alchemist_Purchase_Nearby_Bazaar(thisagent, 75)",
        "$Alchemist_Funded_Resupply(thisagent)",
        "$Check_rewards(thisagent,FALSE)",
        "$Alchemist_Purchase_Bazaar(thisagent, 75)",
        "$Purchase_equipment(thisagent)",
    )
    priority_offsets = [alchemist_tree.find(token) for token in priority_contract]
    if -1 in priority_offsets or priority_offsets != sorted(priority_offsets):
        raise ValueError(
            "Alchemist reagent-return, shopping, and reward priority changed"
        )
    if "$Steal_Check" in alchemist_tree:
        raise ValueError("Alchemist must not retain Rogue stealing")
    for recruitment_contract in (
        'Home\'s "Title" == "AlchemistsLaboratory"',
        '"AlchemistRecruitmentVoice"',
        "$RandomNumber(100) + 1 <= 20",
        '$PlaySound(ThisAgent, "Alchy_Hired", "Begin")',
    ):
        if recruitment_contract not in alchemist_tree:
            raise ValueError(
                f"Alchemist recruitment voice contract is missing: "
                f"{recruitment_contract}"
            )
    flash_source = (
        output_root / "GPL" / "Alchemist_Flash_Flask.gpl"
    ).read_text(encoding="utf-8")
    stun_source = (
        output_root / "GPL" / "Alchemist_Stun_Serum.gpl"
    ).read_text(encoding="utf-8")
    miasma_source = (
        output_root / "GPL" / "Alchemist_Miasma_Mist.gpl"
    ).read_text(encoding="utf-8")
    reagent_source = (
        output_root / "GPL" / "Alchemist_Reagents.gpl"
    ).read_text(encoding="utf-8")
    cast_voice_call = '"Alchy_Cast"'
    impact_sound_call = '$PlaySound (Target, "Alchy_Bottle", "Begin");'
    if cast_voice_call in flash_source:
        raise ValueError("Flash Flask must retain only its stock potion sound")
    if impact_sound_call not in stun_source or impact_sound_call not in miasma_source:
        raise ValueError("Thrown-bottle spells lost their stock impact-phase bottle sound")
    for infusion_contract in (
        "function Alchemist_Arcane_Infusion",
        "function Alchemist_Apply_Arcane_Infusion",
        "#ATTRIB_ResearchArrows",
        "#ATTRIB_MagicResistance, 25",
        '"AlchemistArcaneInfusionApplied"',
        '"resist_magic_effector"',
        '"alchemist_arcane_infusion_effector"',
        '$ListObjects ( laboratory, "hero", -1, Heroes, #MyPlayer,',
    ):
        if infusion_contract not in reagent_source:
            raise ValueError(
                f"Arcane Infusion lost its stock-derived lifecycle: {infusion_contract}"
            )
    if "Alchemical_Tempest" in reagent_source:
        raise ValueError("Retired Alchemical Tempest gameplay remains in GPL")
    for meteor_eligibility_contract in (
        "$compile_enemies(ThisAgent, #Alchemist_Miasma_Mist_Radius)",
        "$ListSize(Targets) > 0",
        'Target\'s "Type" == "Building"',
        'Target\'s "Type" == "Lair"',
    ):
        if meteor_eligibility_contract not in miasma_source:
            raise ValueError(
                "Miasma Mist lost its stock Meteor Storm eligibility lifecycle"
            )
    if "$alchemist_combat_consumable_check(ThisAgent)" in miasma_source:
        raise ValueError("Miasma Mist retained the retired consumable danger gate")
    for reagent_stock_contract in (
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
        if reagent_stock_contract not in reagent_source:
            raise ValueError(
                "Monster Reagents lost their stock carried-goodies lifecycle"
            )
    ready_function = extract_gpl_function(
        reagent_source,
        "Alchemist_Update_Reagent_Ready_Effector",
    )
    if (
        ready_function.count("$CreateEffector") != 1
        or ready_function.count("$DeleteEffector") != 1
        or ready_function.count("$CheckEffector") != 1
        or "$NewThread" in ready_function
        or "$RunThread" in ready_function
        or "ActiveScript" in ready_function
    ):
        raise ValueError(
            "Reagents Ready diverged from the stock Tower effector lifecycle"
        )
    ready_birth_function = extract_gpl_function(
        reagent_source,
        "Alchemist_Laboratory_Birth_Or_Upgrade",
    )
    ready_upgrade_function = extract_gpl_function(
        reagent_source,
        "Alchemist_Laboratory_Upgrade",
    )
    if (
        ready_birth_function.count("$Guild_Birth") != 1
        or ready_birth_function.count(
            '$HasAttribute ( "EconomyBuilding", laboratory )'
        )
        != 1
        or ready_birth_function.count(
            '$AddAttribute (\n\t\t\tlaboratory,\n\t\t\t"EconomyBuilding",'
        )
        != 1
        or '"boolean",\n\t\t\tTRUE' not in ready_birth_function
        or ready_birth_function.count("$RunThread") != 1
        or ready_birth_function.count(
            "$Alchemist_Update_Reagent_Ready_Effector"
        )
        != 2
        or "#ATTRIB_FirstStageBuilt" not in ready_birth_function
        or "#ATTRIB_CurrentStageBuilt" not in ready_birth_function
        or "#palace_upgrade_check" not in ready_birth_function
        or ready_upgrade_function.count("$basic_upgrade") != 1
        or ready_upgrade_function.count("$RunThread") != 1
        or "#palace_upgrade_check" not in ready_upgrade_function
        or "BuildingReachedMaxHP" in reagent_source
    ):
        raise ValueError(
            "Reagents Ready lost the stock Palace/Restore Zoo upgrade poll"
        )
    for unsafe_reagent_contract in (
        "AlchemistReagent",
        "$CreateNewInventoryItem",
        "$AgentHasInventoryItem",
        "$DeleteInventoryItem",
        "#AlchemistReagent",
        "#Allow_Cloned_Quest_Item",
        "function Hero_Drop_Quest_Items",
    ):
        if unsafe_reagent_contract in reagent_source:
            raise ValueError(
                "Monster Reagents retained a non-stock inventory-item path"
            )
    stone_effect_call = (
        '$CreateEffector ( thisagent, "philosophers_stone_hit_effector", 0 );'
    )
    stone_gold_call = '$CreateEffector ( thisagent, "Got_Gold", 0, 3000 );'
    stone_effect_offset = reagent_source.find(stone_effect_call)
    stone_gold_offset = reagent_source.find(stone_gold_call)
    stone_attack_offset = reagent_source.find(
        "$spelldamage ( $nullagent(), target, 100000, 100000 );",
        stone_effect_offset,
    )
    if (
        reagent_source.count(stone_effect_call) != 1
        or reagent_source.count(stone_gold_call) != 1
        or stone_effect_offset < 0
        or stone_gold_offset < 0
        or stone_attack_offset <= stone_effect_offset
        or reagent_source.find(
            "$SetSpellUnitTimeout ( thisagent, 3500 );",
            stone_attack_offset,
        ) <= stone_attack_offset
    ):
        raise ValueError(
            "Philosopher's Stone lost its stock position-owned impact and gold lifecycle"
        )
    if building_data.count("(title AlchemistsLaboratory)") != 3:
        raise ValueError("Every GPL Laboratory level must use its production title")
    if building_data.count("(Alchemist_Brewing True)") != 3:
        raise ValueError("Every Laboratory level must carry its Brewing marker")
    if "EconomyBuilding" in building_data:
        raise ValueError(
            "EconomyBuilding must be installed as a live GPL attribute, not DAT"
        )
    if building_data.count("(Visited_Script Alchemy_Lab_Visited)") != 3:
        raise ValueError("Every Laboratory level must use the combined stock visit dispatcher")
    for contract in (
        "(birthscript basic_birth)",
        "(member_basicscript Alchemist_tree)",
    ):
        if contract not in building_data:
            raise ValueError(f"GPL construction contract is missing: {contract}")
    if building_data.count(
        "(birthScript2 Alchemist_Laboratory_Birth_Or_Upgrade)"
    ) != 3 or building_data.count(
        "(upgradescript Alchemist_Laboratory_Upgrade)"
    ) != 2:
        raise ValueError(
            "Laboratory data lost the private stock upgrade-completion slots"
        )
    compiled = output_root / "Data" / "Alchemist.bcd"
    if compiled.stat().st_size == 0:
        raise ValueError("Compiled Alchemist bytecode is empty")
    compiled_symbols = compiled.read_bytes()
    validate_siege_test_symbols(compiled_symbols, include_siege_test_fixture)
    if b"Alchemist_DoInvigoratingElixer" not in compiled_symbols:
        raise ValueError("Compiled Alchemist bytecode lost its private Vigor symbol")
    if b"Alchemist_Arcane_Infusion" not in compiled_symbols:
        raise ValueError("Compiled Alchemist bytecode lost Arcane Infusion")
    for symbol in (
        b"Alchemist_Update_Reagent_Ready_Effector",
        b"Alchemist_Laboratory_Birth_Or_Upgrade",
        b"Alchemist_Laboratory_Upgrade",
    ):
        if symbol not in compiled_symbols:
            raise ValueError(
                f"Compiled Alchemist bytecode lost Reagents Ready symbol {symbol!r}"
            )
    for symbol in (
        b"Alchemist_Flash_Flask_Begin",
        b"Alchemist_Flash_Flask_End",
        b"Alchemist_Stun_Serum_Begin",
        b"Alchemist_Stun_Serum_End",
        b"Alchemist_Recruitment_Voice",
    ):
        if symbol not in compiled_symbols:
            raise ValueError(f"Compiled Alchemist bytecode lost Flash Flask symbol {symbol!r}")
    if b"Purchase_Equipment" not in compiled_symbols:
        raise ValueError("Compiled Alchemist bytecode lost its stock-derived economy gate")
    if b"Random_Hero_Type" not in compiled_symbols:
        raise ValueError("Compiled Alchemist bytecode lost Embassy/Outpost support")
    for symbol in (
        b"Alchemist_Purchase_Bazaar",
        b"Alchemist_Bazaar_Item_Check",
    ):
        if symbol not in compiled_symbols:
            raise ValueError(f"Compiled Alchemist bytecode lost Bazaar symbol {symbol!r}")
    for symbol in (
        b"QItem_Stat_Boost",
        b"Alchemist_Strength_Potion_Effect",
        b"Alchemist_Shapeshift_Potion_Effect",
        b"Alchemist_Fire_Balm_Effect",
        b"Alchemist_Regeneration_Elixer_Effect",
        b"Alchemist_Base_List_Eval",
        b"alchemist_combat_consumable_check",
        b"Shapeshift_Potion_End",
    ):
        if symbol not in compiled_symbols:
            raise ValueError(f"Compiled Alchemist bytecode lost potion symbol {symbol!r}")
    for symbol in (
        b"Alchemy_Oil_Check",
        b"Alchemy_Oil_Enchant_Equipment",
        b"Obtain_Alchemy_Oil",
        b"Alchemist_Done_Enhancing_Equipment",
        b"Obtain_Poison",
        b"Alchemy_Paralytic_Oil_Begin",
        b"Alchemy_Paralytic_Oil_End",
        b"Alchemy_Paralytic_Oil_Immunity_End",
        b"Alchemy_Transmutation_Oil_Hit",
        b"Alchemy_Weapon_Oil",
        b"damage",
        b"Phoenix_Phial_Check",
        b"Purchase_Phoenix_Phial",
        b"Phoenix_Phial_Resurrection_End",
        PARALYTIC_OIL_STATUS_NAME.encode("ascii"),
        TRANSMUTATION_OIL_STATUS_NAME.encode("ascii"),
    ):
        if symbol not in compiled_symbols:
            raise ValueError(f"Compiled Alchemist bytecode lost oil symbol {symbol!r}")
    if b"DoRageOfKrolm" in compiled_symbols or b"Alchemist_Stock_RageOfKrolm" in compiled_symbols:
        raise ValueError("Alchemist bytecode must not override or reimplement stock Rage")


def build(
    game_path: Path,
    output_root: Path,
    include_phantoms: bool,
    enable_brewing_control: bool = True,
    include_siege_test_fixture: bool = False,
    approved_sprite_test_set: bool = False,
    reuse_art_from: Path | None = None,
) -> None:
    if approved_sprite_test_set and reuse_art_from is not None:
        raise ValueError("Approved sprite generation and art reuse are mutually exclusive")
    if not approved_sprite_test_set and reuse_art_from is None:
        raise ValueError(
            "Normal Alchemist builds must reuse a verified approved-sprite package; "
            "build -ApprovedSpriteTestSet first or pass --reuse-art-from"
        )
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
        SOURCE_ROOT.parent / "src" / "approved_sprite_bundle.py",
        SOURCE_ROOT.parent / "src" / "approved_building_bundle.py",
    ]
    newest_input = max(path.stat().st_mtime for path in art_inputs if path.is_file())
    # The accepted Walk/Stand bundle has independent, hash-pinned source
    # artifacts and a new SPLT record. Never let the regular generated-art CAM
    # cache satisfy or absorb this in-game test mode.
    cache_current = (reuse_art_from is None) and (not approved_sprite_test_set) and all(
        path.is_file() and path.stat().st_mtime >= newest_input
        for path in (cached_main, cached_interface)
    )
    if reuse_art_from is None and not cache_current:
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
    (data_dir / "alchemist_units.xml").write_bytes(
        build_units_xml(sdk_data / "M_Buildings.xml", sdk_data / "M_Characters.xml")
    )
    (data_dir / "alchemist_brewing_overlays.xml").write_bytes(
        build_brewing_overlays_xml(
            sdk_data / "M_Overlays.xml",
            game_path / "SDK" / "OriginalQuests" / "DataMX" / "MX_Overlays.xml",
        )
    )
    (data_dir / "alchemist_brewing_sounds.xml").write_bytes(
        build_brewing_sounds_xml(sdk_data / "M_Sounds.xml")
    )
    write_alchemist_audio_cam(
        SOURCE_ROOT.parent / "assets" / "audio",
        data_dir / "alchemist_audio.cam",
    )
    write_alchemist_sounddesc_cam(
        game_path / "Data" / "sounddesc.cam",
        data_dir / "alchemist_sounddesc.cam",
    )
    (data_dir / "alchemist_combat_potions.xml").write_bytes(
        build_alchemist_combat_potions_xml(
            sdk_data.parent / "DataMX" / "MX_Actions.xml"
        )
    )
    (data_dir / "alchemist_flash_flask.xml").write_bytes(
        build_flash_flask_xml(
            sdk_data / "M_Actions.xml",
            sdk_data / "M_Overlays.xml",
        )
    )
    (data_dir / "alchemist_stun_serum.xml").write_bytes(
        build_stun_serum_xml(
            sdk_data / "M_Actions.xml",
            sdk_data / "M_Overlays.xml",
        )
    )
    (data_dir / "alchemist_miasma_mist.xml").write_bytes(
        build_miasma_mist_xml(
            sdk_data / "M_Actions.xml",
            sdk_data / "M_Characters.xml",
            sdk_data / "M_Projectiles.xml",
            sdk_data / "M_Overlays.xml",
            sdk_data / "M_ParticleSystems.xml",
        )
    )
    build_text_cam(
        game_data / "textdata.cam",
        data_dir / "alchemist_textdata.cam",
        enable_brewing_control,
    )
    build_gpl_text_cam(
        game_path / "DataMX" / "mx_gpltext.cam",
        data_dir / "alchemist_gpltext.cam",
    )
    build_misc_cam(
        stock_building_dependency_cam(game_path),
        data_dir / "alchemist_miscdata.cam",
        include_phantoms,
    )
    approved_art_provenance = None
    if reuse_art_from is not None:
        reuse_root = require_verified_approved_art_package(reuse_art_from)
        reuse_data = reuse_root / "Data"
        for filename in ("alchemist_maindata.cam", "alchemist_interfacedata.cam"):
            source_art = reuse_data / filename
            if not source_art.is_file():
                raise ValueError(f"Reusable art package is missing {source_art}")
            shutil.copy2(source_art, data_dir / filename)
    elif cache_current:
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
    install_paralytic_oil_restraint_image(
        game_data,
        data_dir / "alchemist_maindata.cam",
    )
    install_refined_stun_serum_images(
        game_path,
        data_dir / "alchemist_maindata.cam",
    )
    if approved_sprite_test_set:
        if approved_art_provenance is None:
            raise AssertionError("Approved sprite test unexpectedly used cached art")
    (gpl_dir / "Alchemist.gplproj").write_text(
        build_gpl_project(include_siege_test_fixture), encoding="utf-8"
    )
    building_data = (GPL_SOURCE_ROOT / "Alchemist_Building_Data.dat").read_text(
        encoding="utf-8"
    )
    (gpl_dir / "Alchemist_Building_Data.dat").write_bytes(building_data.encode("utf-8"))
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Hero_Data.dat", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Phoenix_Phial.dat", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Rogue.gpl", gpl_dir)
    embassy_source = build_alchemist_embassy(
        sdk_data.parent / "GPLMx" / "TaskModules" / "Buildings" / "Embassy.gpl",
        include_phantoms,
        SOURCE_ROOT.parent.parent
        / "majesty-gold-hd-custom-guild-phantoms-haunt"
        / "src"
        / "gpl"
        / "phantom.gpl",
    )
    (gpl_dir / "Alchemist_Embassy.gpl").write_text(
        embassy_source, encoding="utf-8"
    )
    guild_title_source = build_alchemist_guild_title(
        sdk_data.parent
        / "GPLMx"
        / "TaskModules"
        / "Buildings"
        / "Mausoleum.gpl"
    )
    (gpl_dir / "Alchemist_Guild_Title.gpl").write_text(
        guild_title_source, encoding="utf-8"
    )
    adopt_source = build_alchemist_adopt(
        sdk_data.parent / "GPLMx" / "mx_Building_Births.gpl"
    )
    (gpl_dir / "Alchemist_Adopt.gpl").write_text(
        adopt_source, encoding="utf-8"
    )
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Stun_Serum.gpl", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Flash_Flask.gpl", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Miasma_Mist.gpl", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Brewing.gpl", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Weapon_Oil.gpl", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Combat_Oils.gpl", gpl_dir)
    damage_source = build_alchemist_damage(
        sdk_data.parent / "GPLMx" / "TaskModules" / "Subtasks" / "mx_make_attack.gpl"
    )
    (gpl_dir / "Alchemist_Damage.gpl").write_text(
        damage_source, encoding="utf-8"
    )
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Phoenix_Phial.gpl", gpl_dir)
    shutil.copy2(GPL_SOURCE_ROOT / "Alchemist_Reagents.gpl", gpl_dir)
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
    bazaar_source = build_alchemist_magic_bazaar(
        sdk_data.parent / "GPLMx" / "TaskModules" / "Buildings" / "Magic_Bazaar.gpl"
    )
    (gpl_dir / "Alchemist_Magic_Bazaar.gpl").write_text(
        bazaar_source, encoding="utf-8"
    )
    nearby_equipment_source = build_alchemist_nearby_equipment(
        sdk_data.parent
        / "GPLMx"
        / "DecisionTrees"
        / "Modules"
        / "mx_Purchase_Equipment.gpl"
    )
    (gpl_dir / "Alchemist_Nearby_Equipment.gpl").write_text(
        nearby_equipment_source, encoding="utf-8"
    )
    inventory_source = build_alchemist_inventory(
        sdk_data.parent / "GPLMx" / "TaskModules" / "Subtasks" / "mx_Inventory.gpl"
    )
    (gpl_dir / "Alchemist_Inventory.gpl").write_text(
        inventory_source, encoding="utf-8"
    )
    consumable_threat_source = build_alchemist_consumable_threat(
        sdk_data.parent
        / "GPLMx"
        / "DecisionTrees"
        / "Modules"
        / "mx_target_eval.gpl",
        sdk_data.parent / "GPLMx" / "TaskModules" / "Subtasks" / "mx_Spells.gpl",
    )
    (gpl_dir / "Alchemist_Consumable_Threat.gpl").write_text(
        consumable_threat_source, encoding="utf-8"
    )
    strength_source = build_alchemist_strength_potion(
        sdk_data.parent / "GPLMx" / "TaskModules" / "Subtasks" / "mx_Spells.gpl"
    )
    (gpl_dir / "Alchemist_Strength_Potion.gpl").write_text(
        strength_source, encoding="utf-8"
    )
    shapeshift_source = build_alchemist_shapeshift(
        sdk_data.parent / "GPLMx" / "TaskModules" / "Subtasks" / "mx_Spells.gpl"
    )
    (gpl_dir / "Alchemist_Shapeshift.gpl").write_text(
        shapeshift_source, encoding="utf-8"
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
    (output_root / MANIFEST_FILENAME).write_bytes(
        build_manifest(include_siege_test_fixture).encode("utf-8")
    )
    shutil.copy2(
        SOURCE_ROOT.parent / MOD_DEFINITION_FILENAME,
        output_root / MOD_DEFINITION_FILENAME,
    )
    if approved_sprite_test_set:
        assert approved_art_provenance is not None
        approved_art_provenance["art_inputs"] = {
            "aggregate_sha256": current_alchemist_art_input_sha256(),
        }
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
            and path != output_root / APPROVED_SPRITE_PROVENANCE_NAME
        }
        (output_root / APPROVED_SPRITE_PROVENANCE_NAME).write_text(
            json.dumps(approved_art_provenance, indent=2) + "\n",
            encoding="utf-8",
        )
    validate_output(
        output_root,
        game_path,
        include_phantoms,
        enable_brewing_control,
        include_siege_test_fixture,
        approved_sprite_test_set,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Custom Guild: Alchemist Lab")
    parser.add_argument("--game-path", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--include-phantoms-haunt-compatibility", action="store_true")
    parser.add_argument("--enable-brewing-control", action="store_true")
    parser.add_argument("--include-siege-test-fixture", action="store_true")
    parser.add_argument(
        "--approved-sprite-test-set",
        action="store_true",
        help=(
            "build a fresh, cache-bypassed in-game gate with approved Walk V4 "
            "and Stand V5 art only"
        ),
    )
    parser.add_argument(
        "--reuse-art-from",
        type=Path,
        help="Reuse verified Alchemist CAM art from an existing repo-confined package",
    )
    args = parser.parse_args()
    build(
        args.game_path,
        args.output_root,
        args.include_phantoms_haunt_compatibility,
        args.enable_brewing_control,
        args.include_siege_test_fixture,
        args.approved_sprite_test_set,
        args.reuse_art_from,
    )
    print(f"Built and validated Custom Guild: Alchemist Lab: {args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
