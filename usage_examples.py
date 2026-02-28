"""
usage_examples.py

Demonstrates how Claude uses the MCP server tools to answer
horse racing questions. These show the tool call sequences
Claude will use for different query types.

NOT runnable directly — these are documentation examples.
"""

# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1: "What races are on today at Cheltenham?"
# Tool flow: get_courses → get_racecards
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_1_FLOW = """
User: "What races are on today at Cheltenham?"

Claude's tool calls:
1. get_courses(region_codes=["gb"])
   → finds Cheltenham course_id: "crs_cheltenham_01"

2. get_racecards(course=["crs_cheltenham_01"])
   → returns today's full racecard

Claude: "There are 7 races at Cheltenham today.
  2:05 - The Opening Novices Hurdle (2m, Class 4, Soft)
    1. Runners: Stage Star, Three Card Brag, Banbridge...
  ...
"
"""

# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2: "How does William Buick perform on soft ground?"
# Tool flow: search_jockey → get_jockey_analysis(breakdown=going)
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_2_FLOW = """
User: "How does William Buick perform on soft ground?"

Claude's tool calls:
1. search_jockey(name="William Buick")
   → {"jockey": "William Buick", "jockey_id": "jky_257379"}

2. get_jockey_analysis(
     jockey_id="jky_257379",
     breakdown="going",
     going=["soft", "good_to_soft", "soft_to_heavy"]
   )
   → {
     "going": [
       {"going": "soft", "rides": 312, "1st": 68, "win_%": 0.218, "a/e": 1.05, "1_pl": 12.4},
       {"going": "good_to_soft", "rides": 445, "1st": 89, "win_%": 0.200, "a/e": 0.98, "1_pl": -8.2},
       ...
     ]
   }

Claude: "William Buick has a strong record on soft ground:
- Soft: 312 rides, 21.8% win rate, A/E of 1.05 (slightly outperforming market)
- Good to Soft: 445 rides, 20.0% win rate, A/E of 0.98 (roughly market expectations)
The A/E above 1.0 on pure soft ground suggests he genuinely performs well in these
conditions rather than just riding winners the market expected."
"""

# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3: "Analyze Frankel's sire record at distances over 1m2f"
# Tool flow: search_sire → get_sire_analysis(breakdown=distances, min_distance=1m2f)
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_3_FLOW = """
User: "How do Frankel's progeny perform over middle distances?"

Claude's tool calls:
1. search_sire(name="Frankel")
   → {"sire": "Frankel", "sire_id": "sre_frankel_01"}

2. get_sire_analysis(
     sire_id="sre_frankel_01",
     breakdown="distances",
     min_distance="1m",
     max_distance="1m4f"
   )
   → {
     "distances": [
       {"distance": "1m", "runners": 156, "wins": 45, "win_%": 0.288, "a/e": 1.12},
       {"distance": "1m1f", "runners": 89, "wins": 22, "win_%": 0.247, "a/e": 1.08},
       {"distance": "1m2f", "runners": 203, "wins": 71, "win_%": 0.350, "a/e": 1.18},
       ...
     ]
   }

Claude: "Frankel's progeny show exceptional form over middle distances.
Their A/E of 1.18 at 1m2f is particularly impressive — they're consistently
outperforming their market prices at that trip..."
"""

# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 4: "What's Aidan O'Brien's record in Group 1 races?"
# Tool flow: search_trainer → get_trainer_analysis(breakdown=classes, race_class=class_1)
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_4_FLOW = """
User: "What's Aidan O'Brien's record in Group 1 flat races?"

Claude's tool calls:
1. search_trainer(name="Aidan O'Brien")
   → {"trainer": "Aidan O'Brien", "trainer_id": "tra_obrien_a_01"}

2. get_trainer_analysis(
     trainer_id="tra_obrien_a_01",
     breakdown="classes",
     race_class=["class_1"],
     type=["flat"]
   )
   → {
     "classes": [
       {
         "class": "class_1",
         "rides": 1847,
         "1st": 412,
         "2nd": 298,
         "3rd": 224,
         "win_%": 0.223,
         "a/e": 0.97,
         "1_pl": -89.40
       }
     ]
   }

Claude: "Aidan O'Brien has an outstanding record in Class 1 (Group 1) flat races:
- 412 wins from 1,847 runners — a 22.3% win rate
- A/E ratio of 0.97, very close to market expectations
- Net loss of £89.40 to level stakes — typical for a top trainer (market prices in short)
The slight negative P&L tells us the market prices him accurately, so there's no
systematic value to backing his Group 1 runners blindly."
"""

# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 5: Multi-step comparison
# "Compare Dettori and Buick in Class 1 races at Ascot"
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_5_FLOW = """
User: "Compare Dettori and Buick's records in Class 1 races at Ascot"

Claude's tool calls:
1. search_jockey(name="Dettori")
   → {"jockey_id": "jky_dettori_01"}

2. search_jockey(name="Buick")
   → {"jockey_id": "jky_257379"}

3. get_courses(region_codes=["gb"])
   → finds Ascot: "crs_ascot_01"

4. get_jockey_analysis(
     jockey_id="jky_dettori_01",
     breakdown="courses",
     course=["crs_ascot_01"],
     race_class=["class_1"]
   )

5. get_jockey_analysis(
     jockey_id="jky_257379",
     breakdown="courses",
     course=["crs_ascot_01"],
     race_class=["class_1"]
   )

Claude: "Head-to-head at Ascot in Class 1 races:
Dettori: 89 rides, 24 wins (27.0%), A/E 1.08 — slightly outperforms market
Buick:   67 rides, 16 wins (23.9%), A/E 1.01 — tracks market closely
Dettori's higher A/E at Ascot suggests his course knowledge gives him a
genuine edge over and above what his mounts' prices imply."
"""
