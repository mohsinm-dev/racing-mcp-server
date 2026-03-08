"""
Tests for the Racing API MCP Server.

Run with: uv run pytest tests/ -v
"""

import pytest
from unittest.mock import AsyncMock, patch

from racing_mcp.config import (
    Config,
    parse_distance_to_yards,
    normalize_going,
    normalize_race_type,
    furlongs_to_yards,
)
from racing_mcp.tools import TOOLS, TOOL_MAP
from racing_mcp.handlers import handle_tool, _HANDLERS


# ── Config / conversion tests ────────────────────────────────────────────────────

class TestDistanceConversion:
    def test_furlongs_simple(self):
        assert parse_distance_to_yards("6f") == 1320

    def test_miles_simple(self):
        assert parse_distance_to_yards("1m") == 1760

    def test_miles_and_furlongs(self):
        assert parse_distance_to_yards("1m4f") == 2640

    def test_two_miles(self):
        assert parse_distance_to_yards("2m") == 3520

    def test_two_miles_four_furlongs(self):
        assert parse_distance_to_yards("2m4f") == 4400

    def test_yards_direct(self):
        assert parse_distance_to_yards("1760y") == 1760

    def test_yards_suffix_yds(self):
        assert parse_distance_to_yards("1320yds") == 1320

    def test_one_mile_two_furlongs(self):
        assert parse_distance_to_yards("1m2f") == 2200

    def test_decimal_miles(self):
        # 1.5m = 12 furlongs = 2640 yards
        assert parse_distance_to_yards("1.5m") == 2640

    def test_invalid_returns_none(self):
        assert parse_distance_to_yards("blah") is None

    def test_furlongs_helper(self):
        assert furlongs_to_yards(6) == 1320
        assert furlongs_to_yards(8) == 1760


class TestGoingNormalization:
    def test_exact_values_passthrough(self):
        assert normalize_going("good") == "good"
        assert normalize_going("soft") == "soft"
        assert normalize_going("heavy") == "heavy"
        assert normalize_going("firm") == "firm"

    def test_human_readable(self):
        assert normalize_going("good to firm") == "good_to_firm"
        assert normalize_going("good to soft") == "good_to_soft"
        assert normalize_going("very soft") == "very_soft"
        assert normalize_going("soft to heavy") == "soft_to_heavy"

    def test_shorthand(self):
        assert normalize_going("g/f") == "good_to_firm"
        assert normalize_going("g/s") == "good_to_soft"
        assert normalize_going("gf") == "good_to_firm"

    def test_case_insensitive(self):
        assert normalize_going("GOOD") == "good"
        assert normalize_going("Good To Firm") == "good_to_firm"

    def test_unknown_returns_none(self):
        assert normalize_going("wet") is None
        assert normalize_going("frozen") is None


class TestRaceTypeNormalization:
    def test_flat(self):
        assert normalize_race_type("flat") == "flat"

    def test_chase_aliases(self):
        assert normalize_race_type("chase") == "chase"
        assert normalize_race_type("jump") == "chase"
        assert normalize_race_type("jumps") == "chase"
        assert normalize_race_type("steeplechase") == "chase"

    def test_hurdle(self):
        assert normalize_race_type("hurdle") == "hurdle"

    def test_bumper_aliases(self):
        assert normalize_race_type("nh_flat") == "nh_flat"
        assert normalize_race_type("bumper") == "nh_flat"
        assert normalize_race_type("nh flat") == "nh_flat"

    def test_case_insensitive(self):
        assert normalize_race_type("FLAT") == "flat"
        assert normalize_race_type("Chase") == "chase"


# ── Config validation tests ──────────────────────────────────────────────────

class TestConfigValidation:
    def test_validate_raises_when_username_missing(self):
        cfg = Config(username="", password="secret")
        with pytest.raises(ValueError, match="RACING_API_USERNAME"):
            cfg.validate()

    def test_validate_raises_when_password_missing(self):
        cfg = Config(username="user", password="")
        with pytest.raises(ValueError, match="RACING_API_PASSWORD"):
            cfg.validate()

    def test_validate_raises_when_both_missing(self):
        cfg = Config(username="", password="")
        with pytest.raises(ValueError):
            cfg.validate()

    def test_validate_passes_with_credentials(self):
        cfg = Config(username="user", password="pass")
        cfg.validate()  # should not raise

    def test_default_base_url(self):
        cfg = Config()
        assert "theracingapi.com" in cfg.base_url

    def test_default_cache_ttls_are_positive(self):
        cfg = Config()
        assert cfg.cache_ttl_static > 0
        assert cfg.cache_ttl_racecards > 0
        assert cfg.cache_ttl_results > 0
        assert cfg.cache_ttl_analysis > 0
        assert cfg.cache_ttl_search > 0


# ── Tool definition tests ────────────────────────────────────────────────────────

class TestToolDefinitions:
    def test_all_tools_have_names(self):
        for tool in TOOLS:
            assert tool.name
            assert len(tool.name) > 0

    def test_all_tools_have_descriptions(self):
        for tool in TOOLS:
            assert tool.description
            assert len(tool.description) > 20  # meaningful description

    def test_all_tools_have_schemas(self):
        for tool in TOOLS:
            assert tool.inputSchema
            assert "type" in tool.inputSchema

    def test_required_tools_present(self):
        required = [
            "get_regions", "get_courses",
            "search_horse", "search_jockey", "search_trainer",
            "search_owner", "search_sire", "search_dam", "search_damsire",
            "get_racecards", "get_results", "get_race",
            "get_horse_results", "get_horse_analysis",
            "get_jockey_results", "get_jockey_analysis",
            "get_trainer_results", "get_trainer_analysis",
            "get_owner_results", "get_owner_analysis",
            "get_sire_analysis", "get_dam_analysis", "get_damsire_analysis",
            "get_odds",
        ]
        for name in required:
            assert name in TOOL_MAP, f"Missing required tool: {name}"

    def test_tool_map_matches_tools_list(self):
        assert len(TOOL_MAP) == len(TOOLS)

    def test_no_duplicate_tool_names(self):
        names = [tool.name for tool in TOOLS]
        assert len(names) == len(set(names)), "Duplicate tool names found"

    def test_breakdown_tools_have_enum(self):
        """Analysis tools should have breakdown as a required enum field."""
        breakdown_tools = [
            "get_horse_analysis", "get_jockey_analysis",
            "get_trainer_analysis", "get_owner_analysis",
            "get_sire_analysis", "get_dam_analysis", "get_damsire_analysis",
        ]
        for name in breakdown_tools:
            tool = TOOL_MAP[name]
            props = tool.inputSchema.get("properties", {})
            assert "breakdown" in props, f"{name} missing breakdown property"
            assert "enum" in props["breakdown"], f"{name} breakdown missing enum"


# ── Handler tests ────────────────────────────────────────────────────────────────

class TestHandlers:
    @pytest.mark.asyncio
    async def test_get_regions(self):
        mock_result = [{"region": "Great Britain", "region_code": "gb"}]
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mock_client

            result = await handle_tool("get_regions", {})
            assert result == mock_result
            mock_client.get.assert_called_once_with("/courses/regions")

    @pytest.mark.asyncio
    async def test_get_courses_passes_region(self):
        """region_codes input should be passed as 'region' to the API."""
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("get_courses", {"region_codes": ["gb", "ire"]})
            mock_client.get.assert_called_once_with("/courses", {"region": ["gb", "ire"]})

    @pytest.mark.asyncio
    async def test_search_horse(self):
        mock_result = {"horses": [{"horse": "Frankel", "horse_id": "hrs_123"}]}
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mock_client

            result = await handle_tool("search_horse", {"name": "Frankel"})
            assert result == mock_result
            mock_client.get.assert_called_once_with("/horses/search", {"name": "Frankel"})

    @pytest.mark.asyncio
    async def test_search_damsire(self):
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("search_damsire", {"name": "Sadler's Wells"})
            mock_client.get.assert_called_once_with("/damsires/search", {"name": "Sadler's Wells"})

    @pytest.mark.asyncio
    async def test_get_owner_results(self):
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("get_owner_results", {"owner_id": "own_123"})
            endpoint = mock_client.get.call_args[0][0]
            assert endpoint == "/owners/own_123/results"

    @pytest.mark.asyncio
    async def test_get_damsire_analysis(self):
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("get_damsire_analysis", {
                "damsire_id": "dsi_456",
                "breakdown": "distances",
            })
            endpoint = mock_client.get.call_args[0][0]
            assert endpoint == "/damsires/dsi_456/analysis/distances"

    @pytest.mark.asyncio
    async def test_get_horse_analysis_converts_distance(self):
        """Distance inputs should be converted from furlongs to yards."""
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("get_horse_analysis", {
                "horse_id": "hrs_123",
                "breakdown": "distances",
                "min_distance": "6f",
                "max_distance": "1m2f",
            })

            params = mock_client.get.call_args[0][1]
            assert params["min_distance_y"] == 1320   # 6f in yards
            assert params["max_distance_y"] == 2200   # 1m2f in yards

    @pytest.mark.asyncio
    async def test_get_jockey_analysis_normalizes_going(self):
        """Going values should be normalized to API format."""
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("get_jockey_analysis", {
                "jockey_id": "jky_257379",
                "breakdown": "going",
                "going": ["good to firm", "g/s", "soft"],
            })

            params = mock_client.get.call_args[0][1]
            assert params["going"] == ["good_to_firm", "good_to_soft", "soft"]

    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_tool("nonexistent_tool", {})

    @pytest.mark.asyncio
    async def test_permission_error_propagates(self):
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=PermissionError("Plan does not include this endpoint")
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(PermissionError):
                await handle_tool("get_horse_analysis", {
                    "horse_id": "hrs_123",
                    "breakdown": "classes",
                })

    @pytest.mark.asyncio
    async def test_racecards_uses_pro_endpoint(self):
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("get_racecards", {"pro": True})
            endpoint = mock_client.get.call_args[0][0]
            assert endpoint == "/racecards/pro"

    @pytest.mark.asyncio
    async def test_racecards_uses_standard_by_default(self):
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("get_racecards", {})
            endpoint = mock_client.get.call_args[0][0]
            assert endpoint == "/racecards/standard"

    @pytest.mark.asyncio
    async def test_results_date_shortcut(self):
        """Single 'date' param should set both start and end date."""
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("get_results", {"date": "2025-03-14"})
            params = mock_client.get.call_args[0][1]
            assert params["start_date"] == "2025-03-14"
            assert params["end_date"] == "2025-03-14"

    @pytest.mark.asyncio
    async def test_pagination_capped_at_100(self):
        """limit param should be capped at 100."""
        with patch("racing_mcp.handlers.get_racing_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value={})
            mock_get_client.return_value = mock_client

            await handle_tool("get_results", {"limit": 500})
            params = mock_client.get.call_args[0][1]
            assert params["limit"] == 100

    @pytest.mark.asyncio
    async def test_missing_required_arg_raises_value_error(self):
        """Missing required arguments should raise ValueError with clear message."""
        with pytest.raises(ValueError, match="Missing required argument"):
            await handle_tool("search_horse", {})

    @pytest.mark.asyncio
    async def test_missing_required_arg_horse_analysis(self):
        """get_horse_analysis requires horse_id and breakdown."""
        with pytest.raises(ValueError, match="Missing required argument"):
            await handle_tool("get_horse_analysis", {"horse_id": "hrs_123"})

    @pytest.mark.asyncio
    async def test_empty_name_search_raises(self):
        """Search handlers should reject empty name strings."""
        for tool_name in [
            "search_horse", "search_jockey", "search_trainer",
            "search_owner", "search_sire", "search_dam", "search_damsire",
        ]:
            with pytest.raises(ValueError, match="non-empty name"):
                await handle_tool(tool_name, {"name": ""})

    @pytest.mark.asyncio
    async def test_whitespace_name_search_raises(self):
        """Search handlers should reject whitespace-only name strings."""
        with pytest.raises(ValueError, match="non-empty name"):
            await handle_tool("search_horse", {"name": "   "})


# ── Handler/Tool sync test ───────────────────────────────────────────────────────

class TestHandlerToolSync:
    def test_every_tool_has_handler(self):
        """Every tool defined in TOOLS must have a corresponding handler."""
        for tool in TOOLS:
            assert tool.name in _HANDLERS, (
                f"Tool '{tool.name}' is defined in TOOLS but has no handler in _HANDLERS"
            )

    def test_every_handler_has_tool(self):
        """Every handler must have a corresponding tool definition."""
        for handler_name in _HANDLERS:
            assert handler_name in TOOL_MAP, (
                f"Handler '{handler_name}' exists in _HANDLERS but has no tool in TOOLS"
            )

    def test_handler_and_tool_counts_match(self):
        """Number of handlers must equal number of tools."""
        assert len(_HANDLERS) == len(TOOLS)


# ── Cache behavior tests ────────────────────────────────────────────────────────

class TestCacheSelection:
    def test_static_cache_for_courses(self):
        from racing_mcp.client import _select_cache, _cache_static
        assert _select_cache("/courses") is _cache_static

    def test_static_cache_for_regions(self):
        from racing_mcp.client import _select_cache, _cache_static
        assert _select_cache("/courses/regions") is _cache_static

    def test_racecards_cache(self):
        from racing_mcp.client import _select_cache, _cache_racecards
        assert _select_cache("/racecards/standard") is _cache_racecards

    def test_odds_cache(self):
        from racing_mcp.client import _select_cache, _cache_racecards
        assert _select_cache("/odds") is _cache_racecards

    def test_results_cache(self):
        from racing_mcp.client import _select_cache, _cache_results
        assert _select_cache("/results/standard") is _cache_results

    def test_analysis_cache(self):
        from racing_mcp.client import _select_cache, _cache_analysis
        assert _select_cache("/horses/hrs_123/analysis/distances") is _cache_analysis

    def test_search_cache(self):
        from racing_mcp.client import _select_cache, _cache_search
        assert _select_cache("/horses/search") is _cache_search

    def test_results_analysis_not_in_results_cache(self):
        """URLs with both /results and /analysis should go to analysis cache."""
        from racing_mcp.client import _select_cache, _cache_analysis
        assert _select_cache("/results/analysis/something") is _cache_analysis


class TestCacheKey:
    def test_same_inputs_same_key(self):
        from racing_mcp.client import _cache_key
        key1 = _cache_key("/test", {"a": 1, "b": 2})
        key2 = _cache_key("/test", {"b": 2, "a": 1})
        assert key1 == key2

    def test_different_inputs_different_key(self):
        from racing_mcp.client import _cache_key
        key1 = _cache_key("/test", {"a": 1})
        key2 = _cache_key("/test", {"a": 2})
        assert key1 != key2
