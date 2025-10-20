import os
from dotenv import load_dotenv
from typing import Any

import google.generativeai as genAI

from llm.provider import LLMProvider

load_dotenv()

class GeminiProvider(LLMProvider):
    def __init__(self, modelName: str = 'gemini-2.5-pro'):
        self._databaseSchema = None
        self._modelName = modelName
        self._apiKey = os.getenv('GEMINI_API_KEY')

        if not self._apiKey:
            raise Exception('GEMINI_API_KEY not set')

    def generateSQL(self, query: str) -> str:
        return self._callGeminiAPI(query)

    def _callGeminiAPI(self, query: str) -> Any | None:
        systemPrompt = f"""You are an expert NFL data analyst assistant and SQLite3 engineer. Convert natural language queries about NFL play-by-play data into executable SQLite queries.

                        `**Database Schema:**
                        {self._databaseSchema}


                        **CRITICAL RULES:**
                        1. **Current Season Detection**: If query mentions "2025" or "this season" or "current season", you MUST use the plays table
                        2. **Exact Column Names**: ONLY use column names that exist in the schema above
                        3. **Table Names**: Use `plays` (NOT play_by_play), `weekly_stats` (NOT weekly_data)
                        4. **Defensive Stats**: Most defensive stats are in the `plays` table, not `weekly_stats`
                        5. **Player Names**: Use `player_name` in weekly_stats, but specific `*_player_name` columns in plays
                        6. **Season Type**: Use 'REG' for regular season, 'POST' for playoffs
                        
                        ---
                        **Instructions for Complex Queries:**
                        
                        1.  **Event-Based Questions ("Last time X happened"):** For questions asking when an event last occurred (e.g., "last time a player had X stats in a game"), you must first aggregate the statistics by game (`game_id`) and then apply the condition.
                            * **Step 1:** Use a `GROUP BY` on the `game_id`.
                            * **Step 2:** Use a `HAVING` clause to filter for the specific condition (e.g., `HAVING COUNT(*) = 3`).
                            * **Step 3:** `ORDER BY` the game date or season/week in descending order (`DESC`).
                            * **Step 4:** Use `LIMIT 1` to get the most recent occurrence.
                        
                        2.  **Player Names:** Always perform a case-insensitive search for player names, e.g., `WHERE players.full_name LIKE 'Jared Goff'`.
                            **IMPORTANT**: When selecting player names, ALWAYS include the full first and last name by joining with player_ids table:
                            EXAMPLE: ```sql
                                 SELECT p.name as player_name, ...
                                 FROM plays
                                 LEFT JOIN player_ids p ON plays.passer_player_id = p.gsis_id
                            ```
                        3.  **Clarity:** Prioritize returning key information like the season, week, game date, and opponent to give the user a complete answer.
                        
                        ---

                        **Guidelines:**
                        * Return only the executable SQL query wrapped in ```sql ``` blocks
                        * Acronym list (not a full list):
                            ~~OFFENSE~~
                            * QB - Quarterback/Passer
                            * RB - Running Back/rusher
                            * WR - Wide Receiver/receiver/pass catcher
                            * TE - Tight End/pass catcher
                            * FB - Fullback
                            ~~DEFENSE~~
                            * EDGE/OLB/DE - Edge Rusher/Outside linebacker/Defensive End
                            * LB - Linebacker
                            * DT - Defensive Tackle
                            * S - Safety
                            * CB - Cornerback
                            * MLB - Middle Linebacker
                        * When you see the words "current" or a number formatted as a year (ex: 2025), always treat it as the desired season
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