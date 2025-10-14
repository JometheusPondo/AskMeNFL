import os
from typing import Any

import google.generativeai as genAI

from llm.provider import LLMProvider

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
        systemPrompt = f"""You are an expert NFL data analyst assistant. Convert natural language queries about NFL play-by-play data into executable SQLite queries.

                        `**Database Schema:**
                        {self._databaseSchema}


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