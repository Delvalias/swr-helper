from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "data.json"

app = FastAPI(title="Star Wars Rebellion Helper")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")


def load_data() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {
            "factions": {"rebel": {"leaders": [], "actions": []}, "imperial": {"leaders": [], "actions": []}},
            "missions": {"rebel": [], "imperial": []},
            "objectives": [],
            "advanced_tactics": [],
            "generated_from": None,
        }
    return json.loads(DATA_FILE.read_text())


def faction_label(faction: str) -> str:
    return "Rebels" if faction == "rebel" else "Empire"


def is_starting_mission(card: dict[str, Any]) -> bool:
    return "starting" in str(card.get("description", "")).lower()


def mission_type(card: dict[str, Any]) -> int | None:
    if is_starting_mission(card):
        return 5

    source = card.get("source")
    has_leader = bool(card.get("leader"))
    has_vader_icon = bool(card.get("vader_icon"))

    if source == "base" and not has_leader and not has_vader_icon:
        return 1
    if source == "base" and has_leader and not has_vader_icon:
        return 2
    if source == "rote" and has_leader and not has_vader_icon:
        return 3
    if source == "rote" and has_vader_icon:
        return 4
    return None


def mission_visible(card: dict[str, Any], game: str, deck: str) -> bool:
    card_type = mission_type(card)
    if card_type in {None, 5}:
        return False

    if game == "base":
        return card_type in {1, 2}

    if deck == "base":
        return card_type in {1, 2, 3}

    return card_type in {2, 3, 4}


def collapse_duplicates(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collapsed: dict[tuple[str, str, str], dict[str, Any]] = {}
    for card in cards:
        key = (card.get("title", "").lower(), card.get("source", ""), card.get("skill", ""))
        if key not in collapsed:
            item = dict(card)
            item["count"] = 1
            collapsed[key] = item
        else:
            collapsed[key]["count"] += 1
    return list(collapsed.values())


def group_by_skill(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = ["power", "diplomacy", "intel", "logistics", "special", "unknown"]
    labels = {
        "power": "Power",
        "diplomacy": "Diplomacy",
        "intel": "Intel",
        "logistics": "Logistics",
        "special": "Special",
        "unknown": "Unsorted",
    }
    grouped = []
    for key in order:
        items = [card for card in cards if card.get("skill", "unknown") == key]
        if items:
            grouped.append({"key": key, "label": labels[key], "cards": items})
    return grouped


def group_objectives(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = []
    for tier in ["I", "II", "III"]:
        items = [card for card in cards if card.get("tier") == tier]
        if items:
            grouped.append({"key": tier, "label": f"Objective {tier}", "cards": items})
    return grouped


def group_advanced_tactics(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = []
    labels = {
        ("rebel", "space"): "Space Rebel Cards",
        ("rebel", "ground"): "Ground Rebel Cards",
        ("imperial", "space"): "Space Imperial Cards",
        ("imperial", "ground"): "Ground Imperial Cards",
    }
    for side, arena in [("rebel", "space"), ("rebel", "ground"), ("imperial", "space"), ("imperial", "ground")]:
        items = [card for card in cards if card.get("side") == side and card.get("arena") == arena]
        if items:
            groups.append({"key": f"{side}-{arena}", "label": labels[(side, arena)], "cards": items})
    return groups


@app.get("/", include_in_schema=False)
def index() -> RedirectResponse:
    return RedirectResponse(url="/rebels/actions")


@app.get("/{side}/actions")
def actions(request: Request, side: str):
    faction = "rebel" if side in {"rebel", "rebels"} else "imperial"
    data = load_data()
    faction_data = data["factions"][faction]
    return templates.TemplateResponse(
        "actions.html",
        {
            "request": request,
            "side": side,
            "faction": faction,
            "faction_label": faction_label(faction),
            "starting": faction_data["starting_actions"],
            "sets": faction_data["action_sets"],
            "leaders": faction_data["leaders"],
            "active": f"{faction}-actions",
        },
    )


@app.get("/{side}/missions")
def missions(
    request: Request,
    side: str,
    game: str = Query("base", pattern="^(base|rote)$"),
    deck: str = Query("base", pattern="^(base|rote)$"),
    expansion: str | None = Query(None, pattern="^(base|all)$"),
):
    faction = "rebel" if side in {"rebel", "rebels"} else "imperial"
    if expansion == "all":
        game = "rote"
        deck = "rote"
    elif expansion == "base":
        game = "base"
        deck = "base"
    if game == "base":
        deck = "base"
    data = load_data()
    cards = collapse_duplicates([card for card in data["missions"][faction] if mission_visible(card, game, deck)])
    return templates.TemplateResponse(
        "missions.html",
        {
            "request": request,
            "side": side,
            "faction": faction,
            "faction_label": faction_label(faction),
            "game": game,
            "deck": deck,
            "groups": group_by_skill(cards),
            "active": f"{faction}-missions",
        },
    )


@app.get("/rebels/objectives")
def objectives(request: Request, expansion: str = Query("base", pattern="^(base|all)$")):
    data = load_data()
    cards = [card for card in data["objectives"] if expansion == "all" or card.get("source") != "rote"]
    return templates.TemplateResponse(
        "objectives.html",
        {
            "request": request,
            "expansion": expansion,
            "groups": group_objectives(cards),
            "active": "rebel-objectives",
        },
    )


@app.get("/advanced-tactics")
def advanced_tactics(request: Request):
    data = load_data()
    return templates.TemplateResponse(
        "advanced_tactics.html",
        {
            "request": request,
            "groups": group_advanced_tactics(data.get("advanced_tactics", [])),
            "active": "advanced-tactics",
        },
    )
