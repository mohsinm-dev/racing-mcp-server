"""
Tool handlers — execute each MCP tool by calling The Racing API.

Each handler:
1. Receives the tool input dict from Claude
2. Normalizes/converts inputs (going strings, distance to yards, etc.)
3. Calls the Racing API client
4. Returns a clean result dict
"""

import logging
from typing import Any

from .client import get_racing_client
from .config import furlongs_to_yards, normalize_going, normalize_race_type, parse_distance_to_yards
from .tools import TOOL_MAP

logger = logging.getLogger(__name__)


# ── Shared helpers ───────────────────────────────────────────────────────────────

def _validate_name(name: str, entity: str) -> None:
    """Raise ValueError if name is empty or whitespace-only."""
    if not name or not name.strip():
        raise ValueError(f"A non-empty name is required to search for a {entity}.")


def _parse_distance_param(distance_str: str | None) -> int | None:
    """Convert human distance string to yards for the API."""
    if not distance_str:
        return None
    yards = parse_distance_to_yards(distance_str)
    if yards is None:
        logger.warning(f"Could not parse distance: {distance_str}")
    return yards


def _normalize_going_list(going_list: list[str] | None) -> list[str] | None:
    """Normalize a list of going strings to API-accepted values."""
    if not going_list:
        return None
    normalized = []
    for g in going_list:
        norm = normalize_going(g)
        if norm:
            normalized.append(norm)
        else:
            logger.warning(f"Unknown going value: {g} — skipping")
    return normalized or None


def _normalize_type_list(type_list: list[str] | None) -> list[str] | None:
    if not type_list:
        return None
    normalized = []
    for t in type_list:
        norm = normalize_race_type(t)
        if norm:
            normalized.append(norm)
        else:
            # Pass through if already valid
            normalized.append(t)
    return normalized


def _base_filters(args: dict) -> dict:
    """Extract and normalize all common filter params."""
    params: dict[str, Any] = {}

    if args.get("start_date"):
        params["start_date"] = args["start_date"]
    if args.get("end_date"):
        params["end_date"] = args["end_date"]
    if args.get("region"):
        params["region"] = args["region"]
    if args.get("course"):
        params["course"] = args["course"]
    if args.get("type"):
        normalized = _normalize_type_list(args["type"])
        if normalized:
            params["type"] = normalized
    if args.get("going"):
        normalized = _normalize_going_list(args["going"])
        if normalized:
            params["going"] = normalized
    if args.get("race_class"):
        params["race_class"] = args["race_class"]
    if args.get("age_band"):
        params["age_band"] = args["age_band"]
    if args.get("sex_restriction"):
        params["sex_restriction"] = args["sex_restriction"]

    # Distance conversion
    min_dist = _parse_distance_param(args.get("min_distance"))
    max_dist = _parse_distance_param(args.get("max_distance"))
    if min_dist:
        params["min_distance_y"] = min_dist
    if max_dist:
        params["max_distance_y"] = max_dist

    # Pagination
    if args.get("limit"):
        limit = int(args["limit"])
        if limit < 1:
            raise ValueError("limit must be at least 1.")
        params["limit"] = min(limit, 100)
    if args.get("skip"):
        skip = int(args["skip"])
        if skip < 0:
            raise ValueError("skip must be non-negative.")
        params["skip"] = skip

    return params


# ── Handlers ─────────────────────────────────────────────────────────────────────

async def handle_tool(tool_name: str, args: dict) -> Any:
    """Route a tool call to the appropriate handler with input validation."""
    handler = _HANDLERS.get(tool_name)
    if not handler:
        raise ValueError(f"Unknown tool: {tool_name}")

    # Validate required arguments against tool schema
    tool = TOOL_MAP.get(tool_name)
    if tool:
        required = tool.inputSchema.get("required", [])
        missing = [r for r in required if r not in args]
        if missing:
            raise ValueError(
                f"Missing required argument(s) for {tool_name}: {', '.join(missing)}"
            )

    return await handler(args)


# ── Reference Data ────────────────────────────────────────────────────────────────

async def _get_regions(args: dict) -> list:
    client = get_racing_client()
    return await client.get("/courses/regions")


async def _get_courses(args: dict) -> dict:
    client = get_racing_client()
    params = {}
    if args.get("region_codes"):
        # The Racing API accepts repeated `region` query params
        params["region"] = args["region_codes"]
    return await client.get("/courses", params)


# ── Search ────────────────────────────────────────────────────────────────────────

async def _search_horse(args: dict) -> dict:
    _validate_name(args["name"], "horse")
    client = get_racing_client()
    return await client.get("/horses/search", {"name": args["name"]})


async def _search_jockey(args: dict) -> dict:
    _validate_name(args["name"], "jockey")
    client = get_racing_client()
    return await client.get("/jockeys/search", {"name": args["name"]})


async def _search_trainer(args: dict) -> dict:
    _validate_name(args["name"], "trainer")
    client = get_racing_client()
    return await client.get("/trainers/search", {"name": args["name"]})


async def _search_owner(args: dict) -> dict:
    _validate_name(args["name"], "owner")
    client = get_racing_client()
    return await client.get("/owners/search", {"name": args["name"]})


async def _search_sire(args: dict) -> dict:
    _validate_name(args["name"], "sire")
    client = get_racing_client()
    return await client.get("/sires/search", {"name": args["name"]})


async def _search_dam(args: dict) -> dict:
    _validate_name(args["name"], "dam")
    client = get_racing_client()
    return await client.get("/dams/search", {"name": args["name"]})


async def _search_damsire(args: dict) -> dict:
    _validate_name(args["name"], "damsire")
    client = get_racing_client()
    return await client.get("/damsires/search", {"name": args["name"]})


# ── Racecards ─────────────────────────────────────────────────────────────────────

async def _get_racecards(args: dict) -> dict:
    client = get_racing_client()
    params: dict[str, Any] = {}

    if args.get("date"):
        params["date"] = args["date"]
    if args.get("course"):
        params["course"] = args["course"]
    if args.get("region"):
        params["region"] = args["region"]
    if args.get("type"):
        normalized = _normalize_type_list(args["type"])
        if normalized:
            params["type"] = normalized

    # Standard or Pro racecard
    endpoint = "/racecards/pro" if args.get("pro") else "/racecards/standard"
    return await client.get(endpoint, params)


# ── Results ───────────────────────────────────────────────────────────────────────

async def _get_results(args: dict) -> dict:
    client = get_racing_client()
    params = _base_filters(args)

    # Single date shortcut
    if args.get("date") and not args.get("start_date"):
        params["start_date"] = args["date"]
        params["end_date"] = args["date"]

    return await client.get("/results/standard", params)


async def _get_race(args: dict) -> dict:
    client = get_racing_client()
    race_id = args["race_id"]
    return await client.get(f"/results/{race_id}")


# ── Horse ─────────────────────────────────────────────────────────────────────────

async def _get_horse_results(args: dict) -> dict:
    client = get_racing_client()
    horse_id = args["horse_id"]
    params = _base_filters(args)
    return await client.get(f"/horses/{horse_id}/results", params)


async def _get_horse_analysis(args: dict) -> dict:
    client = get_racing_client()
    horse_id = args["horse_id"]
    breakdown = args["breakdown"]  # classes | distances | going | courses
    params = _base_filters(args)
    return await client.get(f"/horses/{horse_id}/analysis/{breakdown}", params)


# ── Jockey ────────────────────────────────────────────────────────────────────────

async def _get_jockey_results(args: dict) -> dict:
    client = get_racing_client()
    jockey_id = args["jockey_id"]
    params = _base_filters(args)
    return await client.get(f"/jockeys/{jockey_id}/results", params)


async def _get_jockey_analysis(args: dict) -> dict:
    client = get_racing_client()
    jockey_id = args["jockey_id"]
    breakdown = args["breakdown"]  # classes | distances | going | courses | trainers | owners
    params = _base_filters(args)
    return await client.get(f"/jockeys/{jockey_id}/analysis/{breakdown}", params)


# ── Trainer ───────────────────────────────────────────────────────────────────────

async def _get_trainer_results(args: dict) -> dict:
    client = get_racing_client()
    trainer_id = args["trainer_id"]
    params = _base_filters(args)
    return await client.get(f"/trainers/{trainer_id}/results", params)


async def _get_trainer_analysis(args: dict) -> dict:
    client = get_racing_client()
    trainer_id = args["trainer_id"]
    breakdown = args["breakdown"]  # classes | distances | going | courses | jockeys | owners
    params = _base_filters(args)
    return await client.get(f"/trainers/{trainer_id}/analysis/{breakdown}", params)


# ── Owner ─────────────────────────────────────────────────────────────────────────

async def _get_owner_results(args: dict) -> dict:
    client = get_racing_client()
    owner_id = args["owner_id"]
    params = _base_filters(args)
    return await client.get(f"/owners/{owner_id}/results", params)


async def _get_owner_analysis(args: dict) -> dict:
    client = get_racing_client()
    owner_id = args["owner_id"]
    breakdown = args["breakdown"]
    params = _base_filters(args)
    return await client.get(f"/owners/{owner_id}/analysis/{breakdown}", params)


# ── Breeding ──────────────────────────────────────────────────────────────────────

async def _get_sire_analysis(args: dict) -> dict:
    client = get_racing_client()
    sire_id = args["sire_id"]
    breakdown = args["breakdown"]  # classes | distances
    params = _base_filters(args)
    return await client.get(f"/sires/{sire_id}/analysis/{breakdown}", params)


async def _get_dam_analysis(args: dict) -> dict:
    client = get_racing_client()
    dam_id = args["dam_id"]
    breakdown = args["breakdown"]  # classes | distances
    params = _base_filters(args)
    return await client.get(f"/dams/{dam_id}/analysis/{breakdown}", params)


# ── Damsire ───────────────────────────────────────────────────────────────────────

async def _get_damsire_analysis(args: dict) -> dict:
    client = get_racing_client()
    damsire_id = args["damsire_id"]
    breakdown = args["breakdown"]  # classes | distances
    params = _base_filters(args)
    return await client.get(f"/damsires/{damsire_id}/analysis/{breakdown}", params)


# ── Odds ──────────────────────────────────────────────────────────────────────────

async def _get_odds(args: dict) -> dict:
    client = get_racing_client()
    params: dict[str, Any] = {}
    if args.get("course"):
        params["course"] = args["course"]
    if args.get("region"):
        params["region"] = args["region"]
    return await client.get("/odds", params)


# ── Handler dispatch table ────────────────────────────────────────────────────────

_HANDLERS: dict[str, Any] = {
    "get_regions": _get_regions,
    "get_courses": _get_courses,
    "search_horse": _search_horse,
    "search_jockey": _search_jockey,
    "search_trainer": _search_trainer,
    "search_owner": _search_owner,
    "search_sire": _search_sire,
    "search_dam": _search_dam,
    "search_damsire": _search_damsire,
    "get_racecards": _get_racecards,
    "get_results": _get_results,
    "get_race": _get_race,
    "get_horse_results": _get_horse_results,
    "get_horse_analysis": _get_horse_analysis,
    "get_jockey_results": _get_jockey_results,
    "get_jockey_analysis": _get_jockey_analysis,
    "get_trainer_results": _get_trainer_results,
    "get_trainer_analysis": _get_trainer_analysis,
    "get_owner_results": _get_owner_results,
    "get_owner_analysis": _get_owner_analysis,
    "get_sire_analysis": _get_sire_analysis,
    "get_dam_analysis": _get_dam_analysis,
    "get_damsire_analysis": _get_damsire_analysis,
    "get_odds": _get_odds,
}
