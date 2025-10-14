#!/usr/bin/env python3
"""
NFL Natural Language Query Interface
Uses gpt-oss:20b to parse natural language into pandas filters
"""

import pandas as pd
import requests
import json
import sys
import os


class NFLQueryParser:
    def __init__(self, csvPath="passing_plays_2024.csv"):
        """Initialize with NFL play-by-play data"""
        print("Loading NFL data...")
        try:
            self.df = pd.read_csv(csvPath)
            print(f"✅ Loaded {len(self.df):,} passing plays from 2024")
        except FileNotFoundError:
            print(f"❌ Could not find {csvPath}")
            print("Make sure you've exported your R data to this file!")
            sys.exit(1)

        # Ollama API endpoint
        self.ollamaUrl = "http://localhost:11434/api/generate"

    def queryGptOss(self, userQuery):
        """Send query to local gpt-oss model via Ollama"""

        # System prompt to guide the model
        systemPrompt = """You are an NFL data analyst assistant. Convert natural language queries about NFL play-by-play data into pandas filter conditions.

Available columns include: passer_player_name, down, ydstogo, yards_gained, complete_pass, pass_touchdown, qtr, yardline_100, score_differential, air_yards, yards_after_catch, shotgun, no_huddle, and many others.

Important data notes:
- complete_pass: 1 = completion, 0 = incompletion  
- score_differential: positive = leading, negative = trailing
- yardline_100: yards from opponent's end zone (red zone = <= 20)
- Player names may be abbreviated (e.g., "J.Allen" for Josh Allen)

Return ONLY the pandas filter code, nothing else. Use this format:
```python
result = df[CONDITIONS]
```

Example:
User: "Josh Allen 3rd down completions"
Response: 
```python
result = df[(df['passer_player_name'] == 'J.Allen') & (df['down'] == 3) & (df['complete_pass'] == 1)]
```

Reasoning: Low"""

        prompt = f"{systemPrompt}\n\nUser query: {userQuery}\nResponse:"

        payload = {
            "model": "gpt-oss:20b",
            "prompt": prompt,
            "stream": False
        }

        try:
            print("🤖 Parsing query with gpt-oss...")
            response = requests.post(self.ollamaUrl, json=payload, timeout=30)
            response.raise_for_status()

            result = json.loads(response.text)
            return result.get('response', '').strip()

        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to Ollama: {e}")
            print("Make sure Ollama is running: 'ollama serve'")
            return None

    def extractCode(self, response):
        """Extract Python code from the model response"""
        # Look for code between ```python and ```
        if "```python" in response and "```" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            return response[start:end].strip()

        # If no code blocks, look for df[ patterns
        lines = response.split('\n')
        for line in lines:
            if 'df[' in line and '=' in line:
                return line.strip()

        return None

    def executeQuery(self, userQuery):
        """Process a natural language query and return results"""

        # Get parsed query from gpt-oss
        llmResponse = self.queryGptOss(userQuery)
        if not llmResponse:
            return None, None

        print(f"🧠 Model response:\n{llmResponse}\n")

        # Extract the pandas code
        pandasCode = self.extractCode(llmResponse)
        if not pandasCode:
            print("❌ Could not extract pandas code from response")
            return None, None

        print(f"🔍 Executing: {pandasCode}")

        # Execute the pandas filter
        try:
            # Create a safe execution environment
            localVars = {'df': self.df, 'pd': pd}
            exec(pandasCode, {}, localVars)
            result = localVars.get('result', None)

            if result is None:
                print("❌ No 'result' variable found in executed code")
                return None, None

            return result, pandasCode

        except Exception as e:
            print(f"❌ Error executing pandas code: {e}")
            return None, None

    def displayResults(self, resultDf, query, code):
        """Display query results in a nice format"""
        if resultDf is None or len(resultDf) == 0:
            print("📭 No plays found matching your query")
            return

        print(f"\n📊 Found {len(resultDf):,} plays matching: '{query}'")
        print(f"🔍 Filter: {code}")
        print("\n" + "=" * 80)

        # Show key columns in a readable format
        displayCols = ['passer_player_name', 'down', 'ydstogo', 'yards_gained',
                       'complete_pass', 'qtr', 'yardline_100']

        # Only show columns that exist in the data
        availableCols = [col for col in displayCols if col in resultDf.columns]

        if availableCols:
            print(resultDf[availableCols].head(10).to_string(index=False))
            if len(resultDf) > 10:
                print(f"\n... and {len(resultDf) - 10} more plays")
        else:
            print(resultDf.head(10).to_string(index=False))

        print("=" * 80)


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
            resultDf, code = parser.executeQuery(userQuery)

            # Display results
            parser.displayResults(resultDf, userQuery, code)
            print()  # Blank line before next query

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("Please try again with a different query.\n")


if __name__ == "__main__":
    main()
