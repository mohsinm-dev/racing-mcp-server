# Racing API MCP Server

A Model Context Protocol (MCP) server that connects Claude and other LLMs to 
The Racing API (theracingapi.com), giving them live access to horse racing data,
statistics, and analysis.

## Features

- Full entity resolution (name → ID) for horses, jockeys, trainers, owners, sires, dams
- Racecards (today's races, upcoming fixtures)
- Race results (historical, filterable by going/class/distance/region)
- Statistical analysis (win%, A/E ratio, P&L by class/distance/going/course)
- Breeding analysis (sire/dam/damsire progeny stats)
- Automatic furlongs → yards conversion
- Built-in caching (TTL-based) to respect rate limits
- Supports both stdio (local/Claude Desktop) and HTTP/SSE (remote/hosted) transport

## Requirements

- Python 3.11+
- The Racing API subscription (Standard plan minimum recommended)
- `uv` package manager (recommended) or `pip`

## Installation

```bash
# Clone the repo
git clone https://github.com/mohsinm-dev/racing-mcp-server
cd racing-mcp-server

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
RACING_API_USERNAME=your_username
RACING_API_PASSWORD=your_password
RACING_API_BASE_URL=https://api.theracingapi.com/v1
```

## Running

### stdio mode (for Claude Desktop)
```bash
python -m racing_mcp.server
```

### HTTP/SSE mode (for hosted/remote use)
```bash
python -m racing_mcp.server --transport sse --host 0.0.0.0 --port 8080
```

### With uvicorn directly
```bash
uvicorn racing_mcp.http_server:app --host 0.0.0.0 --port 8080
```

## Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "racing-api": {
      "command": "python",
      "args": ["-m", "racing_mcp.server"],
      "cwd": "/path/to/racing-mcp-server",
      "env": {
        "RACING_API_USERNAME": "your_username",
        "RACING_API_PASSWORD": "your_password"
      }
    }
  }
}
```

## Available Tools

### Reference Data
- `get_regions` — List all region codes (gb, ire, fr, hk, usa, etc.)
- `get_courses` — List all courses with IDs, optionally filtered by region

### Search / Entity Resolution
- `search_horse` — Find horse by name → returns horse_id
- `search_jockey` — Find jockey by name → returns jockey_id  
- `search_trainer` — Find trainer by name → returns trainer_id
- `search_owner` — Find owner by name → returns owner_id
- `search_sire` — Find sire by name → returns sire_id
- `search_dam` — Find dam by name → returns dam_id

### Racecards & Results
- `get_racecards` — Today's/upcoming racecards with runners, odds, form
- `get_results` — Race results filtered by date/course/region/going/class
- `get_race` — Single race detailed result by race_id

### Horse Analysis
- `get_horse_results` — Full historical results for a horse
- `get_horse_analysis_classes` — Performance by race class
- `get_horse_analysis_distances` — Performance by distance
- `get_horse_analysis_going` — Performance by going conditions
- `get_horse_analysis_courses` — Performance by course

### Jockey Analysis
- `get_jockey_results` — Full historical rides
- `get_jockey_analysis_classes` — By race class
- `get_jockey_analysis_distances` — By distance
- `get_jockey_analysis_going` — By going
- `get_jockey_analysis_courses` — By course
- `get_jockey_analysis_trainers` — Jockey/trainer partnerships
- `get_jockey_analysis_owners` — Jockey/owner breakdowns

### Trainer Analysis
- `get_trainer_results` — Full historical results
- `get_trainer_analysis_classes` — By class
- `get_trainer_analysis_distances` — By distance
- `get_trainer_analysis_going` — By going
- `get_trainer_analysis_courses` — By course
- `get_trainer_analysis_jockeys` — Trainer/jockey partnerships

### Owner Analysis
- `get_owner_results` — All races for an owner's horses
- `get_owner_analysis_classes` — By class
- `get_owner_analysis_trainers` — Owner/trainer breakdowns

### Breeding Analysis
- `get_sire_results` — Sire progeny results
- `get_sire_analysis_distances` — Sire progeny by distance
- `get_sire_analysis_classes` — Sire progeny by class
- `get_dam_results` — Dam progeny results
- `get_dam_analysis_distances` — Dam progeny by distance

## Plan Requirements

| Tool Group | Min Plan |
|---|---|
| Courses, Regions | Free |
| Racecards (basic) | Basic |
| Results, Horse/Jockey/Trainer analysis | Standard |
| Full historical results, Breeding | Pro |

## Rate Limits

The Racing API enforces 5 req/sec (1 req/sec for courses/regions).
This server includes automatic rate limiting and TTL caching to stay within limits.
