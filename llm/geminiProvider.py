import os
from typing import Any

import google.generativeai as genAI

from llm.provider import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, modelName: str = 'gemini-2.5-pro'):
        self._modelName = modelName
        self._apiKey = os.getenv('GEMINI_API_KEY')

        if not self._apiKey:
            raise Exception('GEMINI_API_KEY not set')

    def generateSQL(self, query: str) -> str:
        return self._callGeminiAPI(query)

    def _callGeminiAPI(self, query: str) -> Any | None:
        systemPrompt = """You are an expert NFL data analyst assistant. Convert natural language queries about NFL play-by-play data into executable SQLite queries.

                        `**Database Schema:**

                        **Main Table: `plays`** 
                        Contains play-by-play data with these key columns:
                        * Basic Info: play_id, game_id, season, week, season_type, qtr, down, ydstogo, yards_gained, play_type
                        * Teams: home_team, away_team, posteam, defteam  
                        * Players: passer_player_name, receiver_player_name, rusher_player_name
                        * Pass Data: pass_attempt, complete_pass, incomplete_pass, passing_yards, receiving_yards, air_yards, yards_after_catch
                        * Rush Data: rush_attempt, rushing_yards, rusher_player_name
                        * Scoring: touchdown, pass_touchdown, rush_touchdown, field_goal_attempt, extra_point_attempt
                        * Turnovers: interception, interception_player_name, fumble, fumble_lost

                        **DEFENSIVE STATS in plays table - EXACT COLUMN NAMES:**
                        * Sacks: sack, sack_player_id, sack_player_name, half_sack_1_player_name, half_sack_2_player_name
                        * QB Hits: qb_hit, qb_hit_1_player_id, qb_hit_1_player_name, qb_hit_2_player_id, qb_hit_2_player_name  
                        * Tackles for Loss: tackled_for_loss, tackle_for_loss_1_player_id, tackle_for_loss_1_player_name, tackle_for_loss_2_player_name
                        * Forced Fumbles: fumble_forced, forced_fumble_player_1_player_id, forced_fumble_player_1_player_name, forced_fumble_player_2_player_name
                        * Interceptions: interception, interception_player_id, interception_player_name
                        * Tackles: solo_tackle, solo_tackle_1_player_name, solo_tackle_2_player_name, assist_tackle, assist_tackle_1_player_name, assist_tackle_2_player_name, assist_tackle_3_player_name, assist_tackle_4_player_name

                        **Table: `weekly_stats`**
                        Player stats by week with columns:
                        * Identity: player_id, player_name, player_display_name, position, position_group, recent_team, season, week
                        * Passing: completions, attempts, passing_yards, passing_tds, interceptions, sacks (sacks allowed), sack_yards
                        * Rushing: carries, rushing_yards, rushing_tds, rushing_fumbles, rushing_fumbles_lost  
                        * Receiving: receptions, targets, receiving_yards, receiving_tds, receiving_fumbles, receiving_fumbles_lost
                        * Special: special_teams_tds, fantasy_points, fantasy_points_ppr

                        **Other Tables:**
                        * `seasonal_stats` - season aggregated stats (similar structure to weekly_stats)
                        * `ngs_passing`, `ngs_rushing`, `ngs_receiving` - Next Gen Stats
                        * `seasonal_rosters`, `weekly_rosters` - roster info with player details
                        * `schedules`, `draft_picks`, `combine_results` - contextual data

                        **CRITICAL RULES:**
                        1. **Exact Column Names**: ONLY use column names that exist in the schema above
                        2. **Table Names**: Use `plays` (NOT play_by_play), `weekly_stats` (NOT weekly_data)
                        3. **Defensive Stats**: Most defensive stats are in the `plays` table, not `weekly_stats`
                        4. **Player Names**: Use `player_name` in weekly_stats, but specific `*_player_name` columns in plays
                        5. **Season Type**: Use 'REG' for regular season, 'POST' for playoffs

                        **Guidelines:**
                        * Return only the executable SQL query wrapped in ```sql ``` blocks
                        * Always use LIMIT for large result sets (default 10 unless specified)
                        * For defensive comparisons, aggregate from the `plays` table using the defensive columns above
                        * Use LIKE '%LastName%' for player name matching (e.g., LIKE '%Garrett%' for Myles Garrett)
                        * For drops, use incomplete_pass = 1 and check desc field for 'drop' mentions"""

        prompt = f"{systemPrompt}\n\nUser query: {query}\nResponse:"

        try:
            genAI.configure(api_key=self._apiKey)
            model = genAI.GenerativeModel(self._modelName)

            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"There was an error retrieving a response from Gemini. Error {e}")
            return None

    def getProviderName(self) -> str:
        return "Gemini"