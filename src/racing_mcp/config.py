"""Configuration management for the Racing MCP Server."""

import os
import re
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Racing API credentials
    username: str = field(default_factory=lambda: os.getenv("RACING_API_USERNAME", ""))
    password: str = field(default_factory=lambda: os.getenv("RACING_API_PASSWORD", ""))
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "RACING_API_BASE_URL", "https://api.theracingapi.com/v1"
        )
    )

    # Server settings
    host: str = field(default_factory=lambda: os.getenv("MCP_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "8080")))

    # Cache TTLs (seconds)
    cache_ttl_static: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_STATIC", "86400"))
    )
    cache_ttl_racecards: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_RACECARDS", "180"))
    )
    cache_ttl_results: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_RESULTS", "180"))
    )
    cache_ttl_analysis: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_ANALYSIS", "900"))
    )
    cache_ttl_search: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_SEARCH", "3600"))
    )

    def validate(self) -> None:
        if not self.username or not self.password:
            raise ValueError(
                "RACING_API_USERNAME and RACING_API_PASSWORD must be set. "
                "Copy .env.example to .env and add your credentials."
            )


# Singleton config
config = Config()


# ── Conversion helpers ──────────────────────────────────────────────────────────

FURLONGS_TO_YARDS = 220

# Pre-compiled regex patterns for distance parsing
_RE_MILES = re.compile(r"(\d+(?:\.\d+)?)m")
_RE_FURLONGS = re.compile(r"(\d+(?:\.\d+)?)f")

def furlongs_to_yards(furlongs: float) -> int:
    """Convert furlongs to yards (the unit the Racing API uses for distance)."""
    return int(furlongs * FURLONGS_TO_YARDS)


def parse_distance_to_yards(distance_str: str) -> int | None:
    """
    Parse a human distance string to yards.
    Handles: '6f', '1m', '1m2f', '1m4f', '2m', '2m4f', '14f', '2400y'
    Returns None if unparseable.
    """
    s = distance_str.lower().strip()

    # Already yards
    if s.endswith("y") or s.endswith("yds"):
        try:
            return int(s.rstrip("yds").rstrip("y"))
        except ValueError:
            return None

    total_furlongs = 0.0

    # e.g. "1m4f" or "2m" or "6f"
    miles = _RE_MILES.search(s)
    furlongs = _RE_FURLONGS.search(s)

    if miles:
        total_furlongs += float(miles.group(1)) * 8
    if furlongs:
        total_furlongs += float(furlongs.group(1))

    if total_furlongs > 0:
        return int(total_furlongs * FURLONGS_TO_YARDS)

    # Pure number assumed to be furlongs
    try:
        return int(float(s) * FURLONGS_TO_YARDS)
    except ValueError:
        return None


# ── Going normalizer ────────────────────────────────────────────────────────────

GOING_MAP = {
    # Exact API values
    "fast": "fast",
    "firm": "firm",
    "good": "good",
    "good_to_firm": "good_to_firm",
    "good_to_soft": "good_to_soft",
    "good_to_yielding": "good_to_yielding",
    "hard": "hard",
    "heavy": "heavy",
    "holding": "holding",
    "muddy": "muddy",
    "sloppy": "sloppy",
    "slow": "slow",
    "soft": "soft",
    "soft_to_heavy": "soft_to_heavy",
    "standard": "standard",
    "standard_to_fast": "standard_to_fast",
    "standard_to_slow": "standard_to_slow",
    "very_soft": "very_soft",
    "yielding": "yielding",
    "yielding_to_soft": "yielding_to_soft",
    # Common aliases / user inputs
    "good to firm": "good_to_firm",
    "good to soft": "good_to_soft",
    "good to yielding": "good_to_yielding",
    "soft to heavy": "soft_to_heavy",
    "yielding to soft": "yielding_to_soft",
    "very soft": "very_soft",
    "standard to fast": "standard_to_fast",
    "standard to slow": "standard_to_slow",
    "g/f": "good_to_firm",
    "g/s": "good_to_soft",
    "g/y": "good_to_yielding",
    "s/h": "soft_to_heavy",
    "y/s": "yielding_to_soft",
    "gf": "good_to_firm",
    "gs": "good_to_soft",
}


def normalize_going(going: str) -> str | None:
    """Normalize a human going string to the API's accepted value."""
    key = going.lower().strip()
    return GOING_MAP.get(key)


# ── Race type normalizer ────────────────────────────────────────────────────────

RACE_TYPE_MAP = {
    "flat": "flat",
    "chase": "chase",
    "hurdle": "hurdle",
    "nh_flat": "nh_flat",
    "nh flat": "nh_flat",
    "national hunt flat": "nh_flat",
    "bumper": "nh_flat",
    "jump": "chase",
    "jumps": "chase",
    "steeplechase": "chase",
}


def normalize_race_type(race_type: str) -> str | None:
    return RACE_TYPE_MAP.get(race_type.lower().strip())
