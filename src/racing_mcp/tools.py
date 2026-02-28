"""
MCP Tool definitions for The Racing API.

Each tool maps to one or more Racing API endpoints.
Descriptions are written for Claude to understand when and how to use each tool.
"""

from mcp.types import Tool

# ── Shared filter parameter descriptions ────────────────────────────────────────

_DATE_FROM = "Start date (YYYY-MM-DD). Defaults to 365 days ago. Can go back to 1988-01-01."
_DATE_TO = "End date (YYYY-MM-DD). Defaults to today."
_REGION = "Region code(s). Use get_regions to see all options. E.g. 'gb', 'ire', 'fr', 'hk'."
_COURSE = "Course ID(s). Use get_courses or search results to find course IDs."
_GOING = (
    "Going condition(s). Options: fast, firm, good, good_to_firm, good_to_soft, "
    "good_to_yielding, hard, heavy, holding, muddy, sloppy, slow, soft, soft_to_heavy, "
    "standard, standard_to_fast, standard_to_slow, very_soft, yielding, yielding_to_soft. "
    "You can also write 'g/f', 'g/s', 'good to firm' etc — they will be normalized."
)
_RACE_CLASS = "Race class(es). Options: class_1, class_2, class_3, class_4, class_5, class_6, class_7."
_RACE_TYPE = "Race type(s). Options: flat, chase, hurdle, nh_flat (bumper)."
_DISTANCE_MIN = "Minimum race distance. Accepts furlongs (e.g. '6f', '1m2f', '2m') or yards."
_DISTANCE_MAX = "Maximum race distance. Accepts furlongs (e.g. '6f', '1m2f', '2m') or yards."
_AGE_BAND = (
    "Age band(s). Options: 2yo, 2yo+, 3yo, 3yo+, 4yo, 4yo+, 5yo, 5yo+, 6yo, 6yo+, "
    "7yo+, 8yo+, 9yo+, 10yo+, 2-3yo, 3-4yo, 3-5yo, 3-6yo, 4-5yo, 4-6yo, 4-7yo, "
    "4-8yo, 5-6yo, 5-7yo, 5-8yo, 6-7yo."
)
_SEX = "Sex restriction(s). Options: c&f (colts & fillies), c&g (colts & geldings), f (fillies), f&m (fillies & mares), m (mares), m&g (mares & geldings)."
_LIMIT = "Max results per page (1-100). Default 50."
_SKIP = "Offset for pagination. Default 0."


# ── Tool definitions ─────────────────────────────────────────────────────────────

TOOLS: list[Tool] = [

    # ── Reference Data ───────────────────────────────────────────────────────────

    Tool(
        name="get_regions",
        description=(
            "Get a list of all region codes used by The Racing API. "
            "Use this to find the correct region code for filtering results. "
            "Common codes: gb (Great Britain), ire (Ireland), fr (France), hk (Hong Kong), "
            "usa (USA). Call this first if you need to filter by region."
        ),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),

    Tool(
        name="get_courses",
        description=(
            "Get a list of all racecourses with their IDs and regions. "
            "Use this to find course IDs when filtering by a specific course. "
            "Optionally filter by region code."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "region_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter to specific regions. E.g. ['gb', 'ire'].",
                }
            },
            "required": [],
        },
    ),

    # ── Search / Entity Resolution ───────────────────────────────────────────────

    Tool(
        name="search_horse",
        description=(
            "Search for a horse by name to get its horse_id. "
            "ALWAYS call this first before using any horse analysis endpoints. "
            "Returns a list of matching horses — pick the most relevant one."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Horse name to search for."}
            },
            "required": ["name"],
        },
    ),

    Tool(
        name="search_jockey",
        description=(
            "Search for a jockey by name to get their jockey_id. "
            "ALWAYS call this before using jockey analysis endpoints. "
            "Partial names work — e.g. 'Buick' will find William Buick."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Jockey name to search for."}
            },
            "required": ["name"],
        },
    ),

    Tool(
        name="search_trainer",
        description=(
            "Search for a trainer by name to get their trainer_id. "
            "ALWAYS call this before using trainer analysis endpoints."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trainer name to search for."}
            },
            "required": ["name"],
        },
    ),

    Tool(
        name="search_owner",
        description="Search for an owner by name to get their owner_id.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Owner name to search for."}
            },
            "required": ["name"],
        },
    ),

    Tool(
        name="search_sire",
        description=(
            "Search for a sire (stallion) by name to get their sire_id. "
            "Use for breeding/pedigree analysis queries."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Sire name to search for."}
            },
            "required": ["name"],
        },
    ),

    Tool(
        name="search_dam",
        description=(
            "Search for a dam (mare) by name to get their dam_id. "
            "Use for breeding/pedigree analysis queries."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Dam name to search for."}
            },
            "required": ["name"],
        },
    ),

    Tool(
        name="search_damsire",
        description=(
            "Search for a damsire (maternal grandsire) by name to get their damsire_id. "
            "ALWAYS call this before using get_damsire_analysis. "
            "The damsire is the sire of the dam — used for pedigree analysis on the maternal side."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Damsire name to search for."}
            },
            "required": ["name"],
        },
    ),

    # ── Racecards ────────────────────────────────────────────────────────────────

    Tool(
        name="get_racecards",
        description=(
            "Get today's or a specific date's racecards showing all races with runners, "
            "going, distance, class, jockeys, trainers, and form. "
            "Use this when asked about today's races, upcoming fixtures, runners in a race, "
            "or race schedules. Returns the full card for the day."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today.",
                },
                "course": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _COURSE,
                },
                "region": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _REGION,
                },
                "type": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _RACE_TYPE,
                },
                "pro": {
                    "type": "boolean",
                    "description": "Use Pro racecard (more data fields). Requires Standard plan.",
                    "default": False,
                },
            },
            "required": [],
        },
    ),

    # ── Results ──────────────────────────────────────────────────────────────────

    Tool(
        name="get_results",
        description=(
            "Get race results filtered by date, course, region, going, and class. "
            "Use for recent results, today's results, or results from a specific meeting. "
            "Returns finishing positions, SPs, BSPs, and horse/jockey/trainer details."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Specific date (YYYY-MM-DD). Use for a single day's results.",
                },
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "course": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _COURSE,
                },
                "region": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _REGION,
                },
                "type": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _RACE_TYPE,
                },
                "going": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _GOING,
                },
                "race_class": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _RACE_CLASS,
                },
                "limit": {"type": "integer", "description": _LIMIT, "default": 50},
                "skip": {"type": "integer", "description": _SKIP, "default": 0},
            },
            "required": [],
        },
    ),

    Tool(
        name="get_race",
        description=(
            "Get full detailed results for a single race by race_id. "
            "Use when you have a specific race_id from other results."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "race_id": {
                    "type": "string",
                    "description": "Race ID (rce_xxxxxx format).",
                }
            },
            "required": ["race_id"],
        },
    ),

    # ── Horse ────────────────────────────────────────────────────────────────────

    Tool(
        name="get_horse_results",
        description=(
            "Get full historical race results for a specific horse. "
            "Requires horse_id — use search_horse first if you only have a name. "
            "Filterable by date range, going, class, distance, course, and race type. "
            "Historical data available back to 1988."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "horse_id": {"type": "string", "description": "Horse ID (hrs_xxxxxx)."},
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "course": {"type": "array", "items": {"type": "string"}, "description": _COURSE},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
                "min_distance": {"type": "string", "description": _DISTANCE_MIN},
                "max_distance": {"type": "string", "description": _DISTANCE_MAX},
                "age_band": {"type": "array", "items": {"type": "string"}, "description": _AGE_BAND},
                "sex_restriction": {"type": "array", "items": {"type": "string"}, "description": _SEX},
                "limit": {"type": "integer", "description": _LIMIT, "default": 50},
                "skip": {"type": "integer", "description": _SKIP, "default": 0},
            },
            "required": ["horse_id"],
        },
    ),

    Tool(
        name="get_horse_analysis",
        description=(
            "Get statistical analysis for a horse broken down by class, distance, going, or course. "
            "Returns win%, A/E ratio (actual vs expected based on SP), and P&L per £1 stake. "
            "Use to answer: 'How does X horse perform on soft ground?' or "
            "'What's X horse's record at Cheltenham?'"
            "breakdown parameter: 'classes', 'distances', 'going', or 'courses'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "horse_id": {"type": "string", "description": "Horse ID (hrs_xxxxxx)."},
                "breakdown": {
                    "type": "string",
                    "enum": ["classes", "distances", "going", "courses"],
                    "description": "How to break down the stats.",
                },
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "course": {"type": "array", "items": {"type": "string"}, "description": _COURSE},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
                "min_distance": {"type": "string", "description": _DISTANCE_MIN},
                "max_distance": {"type": "string", "description": _DISTANCE_MAX},
            },
            "required": ["horse_id", "breakdown"],
        },
    ),

    # ── Jockey ───────────────────────────────────────────────────────────────────

    Tool(
        name="get_jockey_results",
        description=(
            "Get full historical ride results for a jockey. "
            "Requires jockey_id — use search_jockey first. Pro plan required."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "jockey_id": {"type": "string", "description": "Jockey ID (jky_xxxxxx)."},
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "course": {"type": "array", "items": {"type": "string"}, "description": _COURSE},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
                "min_distance": {"type": "string", "description": _DISTANCE_MIN},
                "max_distance": {"type": "string", "description": _DISTANCE_MAX},
                "limit": {"type": "integer", "description": _LIMIT, "default": 50},
                "skip": {"type": "integer", "description": _SKIP, "default": 0},
            },
            "required": ["jockey_id"],
        },
    ),

    Tool(
        name="get_jockey_analysis",
        description=(
            "Get statistical analysis for a jockey. "
            "Returns win%, A/E ratio, and P&L broken down by class, distance, going, "
            "course, trainer partnerships, or owner partnerships. "
            "Use to answer: 'How does Buick perform at Ascot?', "
            "'Which trainer does X jockey ride best for?', "
            "'What's Frankie's record in Class 1 races?'"
            "breakdown options: 'classes', 'distances', 'going', 'courses', 'trainers', 'owners'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "jockey_id": {"type": "string", "description": "Jockey ID (jky_xxxxxx)."},
                "breakdown": {
                    "type": "string",
                    "enum": ["classes", "distances", "going", "courses", "trainers", "owners"],
                    "description": "How to break down the statistics.",
                },
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "course": {"type": "array", "items": {"type": "string"}, "description": _COURSE},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
                "min_distance": {"type": "string", "description": _DISTANCE_MIN},
                "max_distance": {"type": "string", "description": _DISTANCE_MAX},
            },
            "required": ["jockey_id", "breakdown"],
        },
    ),

    # ── Trainer ──────────────────────────────────────────────────────────────────

    Tool(
        name="get_trainer_results",
        description=(
            "Get full historical results for a trainer. "
            "Requires trainer_id — use search_trainer first. Pro plan required."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "trainer_id": {"type": "string", "description": "Trainer ID (tra_xxxxxx)."},
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "course": {"type": "array", "items": {"type": "string"}, "description": _COURSE},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
                "min_distance": {"type": "string", "description": _DISTANCE_MIN},
                "max_distance": {"type": "string", "description": _DISTANCE_MAX},
                "limit": {"type": "integer", "description": _LIMIT, "default": 50},
                "skip": {"type": "integer", "description": _SKIP, "default": 0},
            },
            "required": ["trainer_id"],
        },
    ),

    Tool(
        name="get_trainer_analysis",
        description=(
            "Get statistical analysis for a trainer broken down by class, distance, going, "
            "course, or jockey partnerships. "
            "Use to answer: 'Which jockey does Aidan O'Brien use most?', "
            "'What's Nicholls' record at Cheltenham?', "
            "'How does Willie Mullins perform in Grade 1 hurdles?'"
            "breakdown options: 'classes', 'distances', 'going', 'courses', 'jockeys', 'owners'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "trainer_id": {"type": "string", "description": "Trainer ID (tra_xxxxxx)."},
                "breakdown": {
                    "type": "string",
                    "enum": ["classes", "distances", "going", "courses", "jockeys", "owners"],
                    "description": "How to break down the statistics.",
                },
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "course": {"type": "array", "items": {"type": "string"}, "description": _COURSE},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
                "min_distance": {"type": "string", "description": _DISTANCE_MIN},
                "max_distance": {"type": "string", "description": _DISTANCE_MAX},
            },
            "required": ["trainer_id", "breakdown"],
        },
    ),

    # ── Owner ────────────────────────────────────────────────────────────────────

    Tool(
        name="get_owner_results",
        description=(
            "Get full historical race results for an owner. "
            "Requires owner_id — use search_owner first. Standard plan required. "
            "Use when asked about an owner's race history, recent wins, or horse roster."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "owner_id": {"type": "string", "description": "Owner ID (own_xxxxxx)."},
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "course": {"type": "array", "items": {"type": "string"}, "description": _COURSE},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
                "age_band": {"type": "array", "items": {"type": "string"}, "description": _AGE_BAND},
                "sex_restriction": {"type": "array", "items": {"type": "string"}, "description": _SEX},
                "min_distance": {"type": "string", "description": _DISTANCE_MIN},
                "max_distance": {"type": "string", "description": _DISTANCE_MAX},
                "limit": {"type": "integer", "description": _LIMIT, "default": 50},
                "skip": {"type": "integer", "description": _SKIP, "default": 0},
            },
            "required": ["owner_id"],
        },
    ),

    Tool(
        name="get_owner_analysis",
        description=(
            "Get statistical analysis for an owner broken down by class, distance, going, "
            "course, jockey, or trainer. "
            "Use to answer: 'How does Godolphin perform in Group 1s?', "
            "'Which trainer does JP McManus use most?'"
            "breakdown options: 'classes', 'distances', 'going', 'courses', 'jockeys', 'trainers'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "owner_id": {"type": "string", "description": "Owner ID (own_xxxxxx)."},
                "breakdown": {
                    "type": "string",
                    "enum": ["classes", "distances", "going", "courses", "jockeys", "trainers"],
                    "description": "How to break down the statistics.",
                },
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "course": {"type": "array", "items": {"type": "string"}, "description": _COURSE},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
            },
            "required": ["owner_id", "breakdown"],
        },
    ),

    # ── Breeding ─────────────────────────────────────────────────────────────────

    Tool(
        name="get_sire_analysis",
        description=(
            "Get statistical analysis for a sire's progeny broken down by class or distance. "
            "Use for breeding queries: 'Which distances do Galileo's progeny excel at?', "
            "'How does Frankel's progeny perform on soft ground?'"
            "breakdown options: 'classes', 'distances'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "sire_id": {"type": "string", "description": "Sire ID (sre_xxxxxx)."},
                "breakdown": {
                    "type": "string",
                    "enum": ["classes", "distances"],
                    "description": "How to break down the statistics.",
                },
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
                "min_distance": {"type": "string", "description": _DISTANCE_MIN},
                "max_distance": {"type": "string", "description": _DISTANCE_MAX},
            },
            "required": ["sire_id", "breakdown"],
        },
    ),

    Tool(
        name="get_dam_analysis",
        description=(
            "Get statistical analysis for a dam's progeny. "
            "Use for mare/family line queries."
            "breakdown options: 'classes', 'distances'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dam_id": {"type": "string", "description": "Dam ID (dam_xxxxxx)."},
                "breakdown": {
                    "type": "string",
                    "enum": ["classes", "distances"],
                    "description": "How to break down the statistics.",
                },
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
            },
            "required": ["dam_id", "breakdown"],
        },
    ),

    Tool(
        name="get_damsire_analysis",
        description=(
            "Get statistical analysis for a damsire's progeny broken down by class or distance. "
            "The damsire is the sire of the dam — used for maternal pedigree analysis. "
            "Requires damsire_id — use search_damsire first. Pro plan required. "
            "Use for: 'How do Sadler's Wells damsire-line horses perform at 1m4f?'"
            "breakdown options: 'classes', 'distances'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "damsire_id": {"type": "string", "description": "Damsire ID (dsi_xxxxxx)."},
                "breakdown": {
                    "type": "string",
                    "enum": ["classes", "distances"],
                    "description": "How to break down the statistics.",
                },
                "start_date": {"type": "string", "description": _DATE_FROM},
                "end_date": {"type": "string", "description": _DATE_TO},
                "region": {"type": "array", "items": {"type": "string"}, "description": _REGION},
                "type": {"type": "array", "items": {"type": "string"}, "description": _RACE_TYPE},
                "going": {"type": "array", "items": {"type": "string"}, "description": _GOING},
                "race_class": {"type": "array", "items": {"type": "string"}, "description": _RACE_CLASS},
                "min_distance": {"type": "string", "description": _DISTANCE_MIN},
                "max_distance": {"type": "string", "description": _DISTANCE_MAX},
            },
            "required": ["damsire_id", "breakdown"],
        },
    ),

    # ── Odds ─────────────────────────────────────────────────────────────────────

    Tool(
        name="get_odds",
        description=(
            "Get current odds for today's races across multiple bookmakers. "
            "Use when asked about current prices, SP, or betting market for upcoming races."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "course": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _COURSE,
                },
                "region": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": _REGION,
                },
            },
            "required": [],
        },
    ),
]


# Tool lookup dict for fast access
TOOL_MAP: dict[str, Tool] = {tool.name: tool for tool in TOOLS}
