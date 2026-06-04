from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_FILE = BASE_DIR / "data.json"

MISSION_SKILLS = {
    403: {
        0: "power", 1: "power", 2: "diplomacy", 3: "logistics", 4: "intel",
        5: "intel", 6: "diplomacy", 7: "power", 8: "power", 9: "diplomacy",
        10: "power", 11: "intel", 12: "logistics", 13: "logistics", 14: "logistics",
        15: "logistics", 16: "diplomacy", 17: "logistics", 18: "diplomacy", 19: "intel",
        20: "intel", 21: "intel", 22: "power", 23: "power", 24: "power",
        25: "intel", 26: "diplomacy", 27: "diplomacy", 28: "intel",
    },
    404: {
        0: "diplomacy", 1: "intel", 2: "intel", 3: "logistics", 4: "power",
        5: "power", 6: "logistics", 7: "diplomacy", 8: "power", 9: "logistics",
        10: "special", 11: "special", 12: "power", 13: "power", 14: "logistics",
        15: "logistics", 16: "intel", 17: "intel", 18: "diplomacy", 19: "diplomacy",
    },
    399: {
        0: "logistics", 1: "logistics", 2: "logistics", 3: "intel", 4: "logistics",
        5: "logistics", 6: "logistics", 7: "logistics", 8: "logistics", 9: "logistics",
        10: "logistics", 11: "power", 12: "diplomacy", 13: "intel", 14: "logistics",
        15: "logistics", 16: "logistics", 17: "logistics", 18: "intel", 19: "intel",
        20: "intel", 21: "power", 22: "power", 23: "power", 24: "logistics",
        25: "diplomacy", 26: "diplomacy", 27: "diplomacy", 28: "power", 29: "power",
        30: "intel", 31: "diplomacy", 32: "diplomacy", 33: "diplomacy", 34: "power",
        35: "power", 36: "intel", 37: "power", 38: "diplomacy",
    },
    400: {
        0: "power", 1: "logistics", 2: "power", 3: "logistics", 4: "diplomacy",
        5: "diplomacy", 6: "logistics", 7: "intel", 8: "logistics", 9: "special",
        10: "special", 11: "intel", 12: "logistics", 13: "logistics", 14: "diplomacy",
        15: "diplomacy", 16: "power", 17: "power", 18: "logistics", 19: "logistics",
        20: "logistics", 21: "logistics", 22: "intel", 23: "intel",
    },
}

BASE_WORKSHOP = "674546583.json"
ULTIMATE_WORKSHOP = "2005019272.json"
MISSION_FILES = {
    "rebel": "rebel 48 missions.json",
    "imperial": "empire 48 missions.json",
}

FAN_TAGS = {"WFL", "POTW", "DOTR", "KOTCW", "ASE", "GSDECK"}
TITLE_FIXES = {
    "BOBA FETTT? WHERE?": "Boba Fett? Where?",
    "DISCREDIT REBELION": "Discredit Rebellion",
    "MAKE AN EXPAMPLE": "Make an Example",
}

ACTION_SET_CONFIG = {
    "rebel": [
        {
            "name": "Luke and Wedge",
            "leaders": ["Luke Skywalker", "Wedge Antilles"],
            "actions": [
                ("TARGET THE STAR DESTROYERS", "base"),
                ("ONE IN A MILLION", "base"),
                ("SON OF SKYWALKER", "rote"),
            ],
        },
        {
            "name": "Ackbar and Madine",
            "leaders": ["Admiral Ackbar", "General Madine"],
            "actions": [("IT'S A TRAP", "base"), ("POINT-BLANK ASSAULT", "base"), ("AMBUSH", "base")],
        },
        {
            "name": "Han and Chewbacca",
            "leaders": ["Han Solo", "Chewbacca"],
            "actions": [("AN OLD FRIEND", "base"), ("THE MILLENNIUM FALCON", "base"), ("WOOKIEE GUARDIAN", "base")],
        },
        {
            "name": "Obi-Wan and Lando",
            "leaders": ["Obi-Wan Kenobi", "Lando Calrissian"],
            "actions": [("NOBLE SACRIFICE", "base"), ("INDEPENDENT OPERATION", "base"), ("UNDERCOVER", "base")],
        },
        {
            "name": "Jyn and Chirrut",
            "leaders": ["Jyn Erso", "Chirrut Imwe"],
            "actions": [("SOMETHING TO FIGHT FOR", "rote"), ("BAZE'S LOYALTY", "rote"), ("TRUST IN THE FORCE", "rote")],
        },
        {
            "name": "Cassian and Saw",
            "leaders": ["Cassian Andor", "Saw Gerrera"],
            "actions": [("HE MEANS WELL", "rote"), ("UNDER THE RADAR", "rote")],
        },
    ],
    "imperial": [
        {
            "name": "Boba and Janus",
            "leaders": ["Boba Fett", "Janus Greejatus"],
            "actions": [("BOBA FETT? WHERE?", "base"), ("BLINDSIDE", "base"), ("PUBLIC SUPPORT", "base")],
        },
        {
            "name": "Veers and Piett",
            "leaders": ["General Veers", "Admiral Piett"],
            "actions": [("TARGET THE GENERATOR", "base"), ("KEEP THEM FROM ESCAPING", "base"), ("READY FOR ACTION", "base")],
        },
        {
            "name": "Ozzel and Jerjerrod",
            "leaders": ["Admiral Ozzel", "Moff Jerjerrod"],
            "actions": [("CATCH THEM BY SURPRISE", "base"), ("FULLY OPERATIONAL", "base"), ("PROCEEDING AS PLANNED", "base")],
        },
        {
            "name": "Yularen and Soontir",
            "leaders": ["Colonel Yularen", "Soontir Fel"],
            "actions": [
                ("SCOUTING MISSION", "base"),
                ("LOCAL RUMORS", "base"),
                ("GOOD INTEL", "rote"),
            ],
        },
        {
            "name": "Motti and Jabba",
            "leaders": ["Admiral Motti", "Jabba the Hutt"],
            "actions": [("AMBITIONS OF POWER", "rote"), ("POST BOUNTY", "rote")],
        },
        {
            "name": "Krennic and Krennic's Finest",
            "leaders": ["Director Krennic", "Krennic's Finest"],
            "actions": [("SWEEP THE AREA", "rote"), ("LORD VADER'S ORDERS", "rote"), ("SECRET FACILITY", "rote")],
        },
    ],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def tokens(description: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;,\n]+", description or "") if item.strip()]


def normalized_url_key(url: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", url)


def find_cached_image(tts_path: Path, url: str) -> Path:
    image_dir = tts_path / "Mods" / "Images"
    key = normalized_url_key(url)
    for ext in ("jpg", "png", "jpeg"):
        candidate = image_dir / f"{key}.{ext}"
        if candidate.exists():
            return candidate
    matches = list(image_dir.glob(f"{key}.*"))
    if matches:
        return matches[0]
    hash_match = re.search(r"/([A-Fa-f0-9]{32,})/?$", url)
    if hash_match:
        hash_matches = list(image_dir.glob(f"*{hash_match.group(1)}.*"))
        if hash_matches:
            return hash_matches[0]
    raise FileNotFoundError(f"No cached image for {url}")


def copy_asset(tts_path: Path, url: str, folder: str, name: str) -> str:
    source = find_cached_image(tts_path, url)
    ext = ".jpg" if source.suffix.lower() == ".jpeg" else source.suffix.lower()
    relative = Path("/assets") / folder / f"{name}{ext}"
    target = STATIC_DIR / relative.relative_to("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return str(relative)


def collect_custom_decks(*roots: dict[str, Any]) -> dict[int, dict[str, Any]]:
    decks: dict[int, dict[str, Any]] = {}
    for root in roots:
        for obj in walk(root):
            custom = obj.get("CustomDeck")
            if isinstance(custom, dict):
                for deck_id, deck in custom.items():
                    decks[int(deck_id)] = deck
    return decks


def sprite_for(card_id: int, decks: dict[int, dict[str, Any]], tts_path: Path) -> dict[str, Any]:
    deck_id = card_id // 100
    index = card_id % 100
    deck = decks[deck_id]
    cols = int(deck["NumWidth"])
    rows = int(deck["NumHeight"])
    return {
        "path": copy_asset(tts_path, deck["FaceURL"], "sheets", str(deck_id)),
        "deck": deck_id,
        "index": index,
        "x": index % cols,
        "y": index // cols,
        "cols": cols,
        "rows": rows,
    }


def parse_leader(description: str) -> str:
    for item in tokens(description):
        if item.lower().startswith("leader:"):
            leader = item.split(":", 1)[1].strip()
            return "Boba Fett" if leader == "Boba" else leader
    return ""


def card_source(description: str) -> str:
    return "rote" if any(item.lower() == "rote" for item in tokens(description)) else "base"


def card_record(card: dict[str, Any], decks: dict[int, dict[str, Any]], tts_path: Path) -> dict[str, Any]:
    card_id = int(card["CardID"])
    deck_id = card_id // 100
    index = card_id % 100
    description = card.get("Description", "")
    leader = parse_leader(description)
    return {
        "id": card_id,
        "title": normalize_title(card.get("Nickname") or "Untitled"),
        "description": description,
        "source": card_source(description),
        "leader": leader,
        "vader_icon": any(item.lower() == "vadericon" for item in tokens(description)),
        "include_in_base": bool(leader),
        "skill": MISSION_SKILLS.get(deck_id, {}).get(index, "unknown"),
        "sprite": sprite_for(card_id, decks, tts_path),
    }


def normalize_title(value: str) -> str:
    title = value.strip()
    return TITLE_FIXES.get(title.upper(), title)


def relevant_action_card(card: dict[str, Any], faction: str, starting: bool) -> bool:
    parts = {item.upper() for item in tokens(card.get("Description", ""))}
    if "ACTION" not in parts or faction.upper() not in parts:
        return False
    if bool("STARTING" in parts) != starting:
        return False
    return not bool(parts & FAN_TAGS)


def objective_card(card: dict[str, Any], decks: dict[int, dict[str, Any]], tts_path: Path) -> dict[str, Any] | None:
    parts = tokens(card.get("Description", ""))
    upper = {part.upper() for part in parts}
    if "OBJECTIVE" not in upper or "REBEL" not in upper or upper & FAN_TAGS:
        return None
    tier = next((part for part in parts if part in {"I", "II", "III"}), "")
    record = card_record(card, decks, tts_path)
    record["tier"] = tier
    return record


def action_cards_for_faction(
    workshop: dict[str, Any],
    decks: dict[int, dict[str, Any]],
    tts_path: Path,
    faction: str,
    starting: bool,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    seen: set[int] = set()
    wanted_rebel = faction == "rebel"
    for obj in workshop["ObjectStates"]:
        nickname = obj.get("Nickname", "")
        pos_z = obj.get("Transform", {}).get("posZ", 0)
        contained = obj.get("ContainedObjects") or []
        use_deck = False
        if starting and nickname == "Starting Action Cards":
            use_deck = (pos_z > 0) == wanted_rebel
        elif not starting and wanted_rebel and nickname == "Rebel Action Cards":
            use_deck = True
        elif not starting and not wanted_rebel and nickname == "Imperial Action Deck":
            use_deck = True
        if use_deck:
            for card in contained:
                if card.get("CardID") and int(card["CardID"]) not in seen:
                    seen.add(int(card["CardID"]))
                    cards.append(card_record(card, decks, tts_path))

    for card in walk(workshop):
        if not card.get("CardID") or not relevant_action_card(card, faction, starting):
            continue
        card_id = int(card["CardID"])
        if card_id in seen:
            continue
        seen.add(card_id)
        cards.append(card_record(card, decks, tts_path))
    return cards


def base_objective_records(workshop: dict[str, Any], decks: dict[int, dict[str, Any]], tts_path: Path) -> list[dict[str, Any]]:
    records = []
    for obj in workshop["ObjectStates"]:
        nickname = obj.get("Nickname", "")
        if "Shuffled" in obj.get("Description", ""):
            continue
        tier_match = re.fullmatch(r"Rebel Objective Deck (I{1,3})\s*", nickname)
        if not tier_match:
            continue
        for card in obj.get("ContainedObjects") or []:
            record = card_record(card, decks, tts_path)
            record["source"] = "base"
            record["tier"] = tier_match.group(1)
            records.append(record)
    return records


def objective_records(workshop: dict[str, Any], decks: dict[int, dict[str, Any]], tts_path: Path) -> list[dict[str, Any]]:
    records = []
    seen = set()
    for obj in workshop["ObjectStates"]:
        if obj.get("Nickname") not in {"Objectives I", "Objectives II", "Objectives III"}:
            continue
        for card in obj.get("ContainedObjects") or []:
            parts = {item.upper() for item in tokens(card.get("Description", ""))}
            if "OBJECTIVECARD" not in parts or "REBEL" not in parts or parts & FAN_TAGS:
                continue
            card_id = int(card["CardID"])
            if card_id in seen:
                continue
            seen.add(card_id)
            record = card_record(card, decks, tts_path)
            record["tier"] = next((item for item in tokens(card.get("Description", "")) if item in {"I", "II", "III"}), "")
            records.append(record)
    return records


def mission_cards(path: Path, faction: str, decks: dict[int, dict[str, Any]], tts_path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    cards = []
    for card in data["ObjectStates"][0]["ContainedObjects"]:
        if f"MissionCard;{faction.title()}" in card.get("Description", ""):
            cards.append(card_record(card, decks, tts_path))
    return sorted(cards, key=lambda item: (item["sprite"]["deck"], item["sprite"]["index"], item["id"]))


def leader_records(workshop: dict[str, Any], faction: str, tts_path: Path) -> list[dict[str, Any]]:
    wanted = "Rebel" if faction == "rebel" else "Imperial"
    leaders: dict[str, dict[str, Any]] = {}
    for obj in walk(workshop):
        if obj.get("Name") != "Custom_Model":
            continue
        role = obj.get("Description", "")
        name = obj.get("Nickname", "").strip()
        if not name or not role.startswith(wanted):
            continue
        url = obj.get("CustomMesh", {}).get("DiffuseURL", "")
        if not url:
            continue
        source = "rote" if obj.get("Transform", {}).get("posX", 0) < -40 else "base"
        try:
            image = copy_asset(tts_path, url, "leaders", slug(name))
        except FileNotFoundError:
            image = ""
        leaders[name] = {
            "name": name,
            "role": role,
            "source": source,
            "image": image,
        }
    return list(leaders.values())


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "asset"


def action_sets(leaders: list[dict[str, Any]], actions: list[dict[str, Any]], faction: str) -> list[dict[str, Any]]:
    leader_by_name = {leader["name"]: leader for leader in leaders}
    action_by_key = {(card["title"].upper(), card["source"]): card for card in actions}
    configured = []
    for item in ACTION_SET_CONFIG[faction]:
        configured.append(
            {
                "name": item["name"],
                "leaders": [leader_by_name[name] for name in item["leaders"] if name in leader_by_name],
                "actions": [action_by_key[key] for key in item["actions"] if key in action_by_key],
            }
        )
    if configured:
        return configured

    recruitable = [
        leader
        for leader in leaders
        if leader["name"] not in starting_leaders(faction) and leader["name"] not in non_recruitable_leaders(faction)
    ]
    base_leaders = [leader for leader in recruitable if leader["source"] == "base"]
    rote_leaders = [leader for leader in recruitable if leader["source"] == "rote"]
    base_actions = [card for card in actions if card["source"] == "base"]
    rote_actions = [card for card in actions if card["source"] == "rote"]
    sets = []
    sets.extend(chunk_sets("Base", base_leaders, base_actions))
    sets.extend(chunk_sets("RotE", rote_leaders, rote_actions))
    return sets


def starting_leaders(faction: str) -> set[str]:
    if faction == "rebel":
        return {"Mon Mothma", "Princess Leia", "General Rieekan", "Jan Dodonna"}
    return {"Emperor Palpatine", "Darth Vader", "Grand Moff Tarkin", "General Tagge"}


def non_recruitable_leaders(faction: str) -> set[str]:
    return {"Jedi Luke Skywalker"} if faction == "rebel" else set()


def chunk_sets(prefix: str, leaders: list[dict[str, Any]], actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = []
    max_groups = max((len(leaders) + 1) // 2, (len(actions) + 2) // 3)
    for idx in range(max_groups):
        grouped.append(
            {
                "name": f"{prefix} set {idx + 1}",
                "leaders": leaders[idx * 2 : idx * 2 + 2],
                "actions": actions[idx * 3 : idx * 3 + 3],
            }
        )
    return grouped


def build_data(tts_path: Path) -> dict[str, Any]:
    workshop_path = tts_path / "Mods" / "Workshop" / BASE_WORKSHOP
    ultimate_path = tts_path / "Mods" / "Workshop" / ULTIMATE_WORKSHOP
    saved_objects = tts_path / "Saves" / "Saved Objects"
    workshop = load_json(workshop_path)
    ultimate = load_json(ultimate_path)
    mission_roots = {faction: load_json(saved_objects / filename) for faction, filename in MISSION_FILES.items()}
    decks = collect_custom_decks(workshop, ultimate, *mission_roots.values())

    all_cards = [obj for obj in walk(workshop) if obj.get("Name") in {"Card", "Deck"}]
    output = {
        "generated_from": str(tts_path),
        "factions": {},
        "missions": {},
        "objectives": [],
    }

    for faction in ("rebel", "imperial"):
        leaders = leader_records(workshop, faction, tts_path)
        leaders.sort(key=lambda item: (item["source"] == "rote", item["name"]))
        starting = action_cards_for_faction(workshop, decks, tts_path, faction, starting=True)
        actions = action_cards_for_faction(workshop, decks, tts_path, faction, starting=False)
        starting.sort(key=lambda item: (item["source"], item["sprite"]["deck"], item["sprite"]["index"]))
        actions.sort(key=lambda item: (item["source"], item["sprite"]["deck"], item["sprite"]["index"]))
        output["factions"][faction] = {
            "leaders": leaders,
            "starting_actions": starting,
            "action_sets": action_sets(leaders, actions, faction),
        }
        output["missions"][faction] = mission_cards(saved_objects / MISSION_FILES[faction], faction, decks, tts_path)

    objectives = objective_records(ultimate, decks, tts_path)
    output["objectives"] = sorted(objectives, key=lambda item: (item["tier"], item["source"], item["sprite"]["deck"], item["sprite"]["index"]))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tts-path",
        default="/Users/mihailk/Library/Tabletop Simulator",
        type=Path,
        help="Path to the Tabletop Simulator user folder.",
    )
    args = parser.parse_args()
    data = build_data(args.tts_path.expanduser())
    DATA_FILE.write_text(json.dumps(data, indent=2))
    print(f"Wrote {DATA_FILE}")


if __name__ == "__main__":
    main()
