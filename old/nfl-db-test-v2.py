#!/usr/bin/env python3
"""
NFL Natural Language Query Interface
Uses gpt-oss:20b to parse natural language into pandas filters
"""
import sqlite3
from sqlite3 import OperationalError
import pandas as pd
import requests
import time
import json
import sys


class NFLQueryParser:
    def __init__(self, dbPath="nfl_data_py.db"):
        """Initialize with NFL play-by-play data"""
        print("Loading NFL data...")
        try:
            self.conn = sqlite3.connect(dbPath)
            print(f"✅ Loaded stats database")
        except OperationalError:
            print(f"❌ Could not complete query")
            print("Query could not process or file is corrupt")
            sys.exit(1)

        # Ollama API endpoint
        self.ollamaUrl = "http://localhost:11434/api/generate"

    def queryGptOss(self, userQuery):
        """Send query to local gpt-oss model via Ollama"""

        # System prompt to guide the model
        systemPrompt = """You are an expert NFL data analyst assistant. Convert natural language queries about NFL play-by-play data into executable SQLite queries.

**Database Schema:**
Table: `plays` with key columns including:
* `passer_player_name`: Quarterback name
* `qb_dropback`: 1 if QB dropped back to pass, 0 otherwise
* `complete_pass`: 1 for completed passes, 0 for incomplete
* `sack`: 1 for sacks, 0 otherwise
* `qb_scramble`: 1 for QB scrambles, 0 otherwise
* `down`: Down number (1, 2, 3, 4)
* `yards_gained`: Yards gained on the play
* `season_type`: 'REG' for regular season, 'POST' for playoffs
* `qtr`: Quarter (1, 2, 3, 4)
* `yardline_100`: Yards from opponent's end zone
* `score_differential`: Positive when leading, negative when trailing

**CRITICAL - Player Name Format:**
Player names in database use abbreviated format: "F.LastName"
Examples: "J.Goff", "J.Burrow", "P.Mahomes", "J.Allen", "A.Richardson"
DO NOT use full names like "Jared Goff" - use "J.Goff" instead.

**NFL Statistics Context:**
* Most passing statistics exclude sacks (sacks count as rushing attempts in official stats)
* Regular season stats typically exclude playoffs unless specified
* For passing attempts, focus on plays where QB dropped back intending to pass
* Consider what would appear in official NFL statistical records
* Consider two-point conversion attempts that may have been excluded.

**Guidelines:**
* Return only the executable SQL query wrapped in ```sql ``` blocks
* Use descriptive column aliases (e.g., AS Quarterback, AS Completion_Percentage)  
* Default to regular season unless user specifies playoffs
* For rate calculations, use appropriate filtering to match official statistics

**Example patterns:**
* Basic filter: `WHERE passer_player_name = 'J.Allen' AND season_type = 'REG'`
* Passing attempts: `WHERE qb_dropback = 1 AND sack = 0`
* Third down: `WHERE down = 3`
* Aggregation: `GROUP BY passer_player_name ORDER BY [metric] DESC LIMIT 5`
"""

        prompt = f"{systemPrompt}\n\nUser query: {userQuery}\nResponse:"

        payload = {
            "model": "gpt-oss:20b",
            "prompt": prompt,
            "stream": False
        }

        try:
            print("🤖 Parsing query with gpt-oss...")
            response = requests.post(self.ollamaUrl, json=payload, timeout=500)
            response.raise_for_status()

            result = json.loads(response.text)
            return result.get('response', '').strip()

        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to Ollama: {e}")
            print("Make sure Ollama is running: 'ollama serve'")
            return None

    def extractCode(self, response):
        """Extract code from the model response"""
        if "```sql" in response:
            try:
                return response.split("```sql")[1].split("```")[0].strip()
            except IndexError:
                pass

        lines = response.split("\n")
        extractedQuery = ""
        inQuery = False
        for line in lines:
            if line.strip().upper().startswith('SELECT'):
                inQuery = True

            if inQuery:
                extractedQuery += line + " "
                if line.strip().endswith(';'):
                    return extractedQuery.strip()
        if extractedQuery:
            return extractedQuery.strip()

        print("❌ Could not extract SQL from response using any method.")
        return None




    def executeQuery(self, userQuery):
        """Process a natural language query and return results"""

        # Get parsed query from gpt-oss
        startTimeLLM = time.time()
        llmResponse = self.queryGptOss(userQuery)
        endTimeLLM = time.time()
        print(f"⏱️  LLM Processing Time: {endTimeLLM - startTimeLLM}")

        if not llmResponse:
            return None, None, None

        print(f"🧠 Model response:\n{llmResponse}\n")

        # Extract the query
        sqlQuery = self.extractCode(llmResponse)
        if not sqlQuery:
            print("❌ Could not extract query code from response")
            return None, None, None

        print(f"🔍 Executing: {sqlQuery}")

        # Execute the query
        try:
            startTimeDB = time.time()
            cursor = self.conn.execute(sqlQuery)
            result = cursor.fetchall()

            columnNames = [line[0] for line in cursor.description]
            endTimeDB = time.time()
            print(f"⏱️ Database Query Time: {endTimeDB - startTimeDB}")
            return result, columnNames, sqlQuery

        except Exception as e:
            print(f"❌ Error executing query: {e}")
            return None, None

    def displayResults(self, results, columnNames):
        """Display query results in a nice format"""

        df = pd.DataFrame(data=results, columns=columnNames)
        print("✅ Query successful! Here are the results:")
        print(df)


def main():
    """Main CLI interface"""

    print("🏈 NFL Natural Language Query Interface")
    print("Powered by gpt-oss-20b + 2024 NFL play-by-play data")
    print("Type 'quit' to exit\n")

    # Initialize the parser
    parser = NFLQueryParser()

    while True:
        try:
            # Get user query
            userQuery = input("🏈 Enter your NFL query: ").strip()

            if userQuery.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            if not userQuery:
                continue

            print()  # Blank line for readability

            # Process the query
            results, columnNames, sqlQuery = parser.executeQuery(userQuery)

            # Display results
            if results is not None and columnNames is not None:
                parser.displayResults(results, columnNames)
            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("Please try again with a different query.\n")


if __name__ == "__main__":
    main()
