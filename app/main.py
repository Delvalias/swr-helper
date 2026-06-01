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
            "generated_from": None,
        }
    return json.loads(DATA_FILE.read_text())


def faction_label(faction: str) -> str:
    return "Rebels" if faction == "rebel" else "Empire"


def has_leader_icon(card: dict[str, Any]) -> bool:
    return bool(card.get("leader") or card.get("vader_icon"))


def is_starting_mission(card: dict[str, Any]) -> bool:
    return "starting" in str(card.get("description", "")).lower()


def mission_visible(card: dict[str, Any], game: str, deck: str) -> bool:
    if is_starting_mission(card):
        return False

    source = card.get("source")
    leader_icon = has_leader_icon(card)

    if game == "base":
        return source == "base"

    if deck == "base":
        return (source == "base" and not leader_icon) or leader_icon

    return leader_icon or (source == "rote" and not leader_icon)


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
