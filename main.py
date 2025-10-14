#!/usr/bin/env python3
"""
FastAPI Backend for NFL Natural Language Query System
Exposes REST API endpoints for React frontend
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sqlite3
import pandas as pd
import google.generativeai as genai
import requests
import json
import time
import re
import asyncio
import logging
import os
from contextlib import asynccontextmanager

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language NFL question")
    include_sql: bool = Field(default=False, description="Include generated SQL in response")
    model: str = Field(default="gpt-oss", description="LLM model to use: 'gpt-oss' or 'Gemini'")

class QueryResponse(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    sql_query: Optional[str] = None
    error: Optional[str] = None
    timing: Dict[str, float] = Field(default_factory=dict)
    rows_returned: int = 0

class DatabaseStatus(BaseModel):
    connected: bool
    total_plays: int = 0
    available_quarterbacks: List[str] = Field(default_factory=list)
    error: Optional[str] = None

class NFLQueryService:
    def __init__(self, db_path: str = "nfl_complete_database.db"):
        self.db_path = db_path
        self.ollama_url = "http://localhost:11434/api/generate"

        try:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_available = True
            logger.info("Gemini API configured successfully")
        except Exception as e:
            self.gemini_available = False
            logger.warning(f"Gemini API not available: {e}")

        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database connection and test it"""
        print(f"DEBUG: Looking for database at: {os.path.abspath(self.db_path)}")
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.execute("SELECT COUNT(*) FROM plays")
            total_plays = cursor.fetchone()[0]
            conn.close()
            self.db_connected = True
            self.total_plays = total_plays
            logger.info(f"Database connected successfully. {total_plays:,} plays loaded.")
        except Exception as e:
            self.db_connected = False
            self.db_error = str(e)
            logger.error(f"Database connection failed: {e}")
    
    

    async def query_gpt_oss(self, user_query: str) -> Optional[str]:
        """Send query to local gpt-oss model via Ollama"""
        
        system_prompt = """You are an expert NFL data analyst assistant. Convert natural language queries about NFL play-by-play data into executable SQLite queries.

**Database Schema:**

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
* Always use LIMIT for large result sets (default 10-20 unless specified)
* For defensive comparisons, aggregate from the `plays` table using the defensive columns above
* Use LIKE '%LastName%' for player name matching (e.g., LIKE '%Garrett%' for Myles Garrett)
* For drops, use incomplete_pass = 1 and check desc field for 'drop' mentions
"""

        prompt = f"{system_prompt}\n\nUser query: {user_query}\nResponse:"
        
        payload = {
            "model": "gpt-oss:20b",
            "prompt": prompt,
            "stream": False
        }
        
        try:
            # Use asyncio for non-blocking request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(self.ollama_url, json=payload, timeout=500)
            )
            response.raise_for_status()
            result = json.loads(response.text)
            return result.get('response', '').strip()
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return None

    def query_gemini_sync(self, user_query: str) -> Optional[str]:
        """Synchronous Gemini call"""
        api_key = os.getenv('GEMINI_API_KEY')
        system_prompt = """You are an expert NFL data analyst assistant. Convert natural language queries about NFL play-by-play data into executable SQLite queries.

**Database Schema:**

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
* Always use LIMIT for large result sets (default 10-20 unless specified)
* For defensive comparisons, aggregate from the `plays` table using the defensive columns above
* Use LIKE '%LastName%' for player name matching (e.g., LIKE '%Garrett%' for Myles Garrett)
* For drops, use incomplete_pass = 1 and check desc field for 'drop' mentions
"""

        prompt = f"{system_prompt}\n\nUser query: {user_query}\nResponse:"

        try:
            import google.generativeai as genai
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            print(f"Gemini error: {e}")
            return None

    def _extract_sql(self, response: str) -> Optional[str]:
        """Extract SQL code from LLM response"""
        if "```sql" in response:
            try:
                return response.split("```sql")[1].split("```")[0].strip()
            except IndexError:
                pass
        
        # Fallback: look for SELECT statements
        lines = response.split("\n")
        query = ""
        in_query = False
        
        for line in lines:
            if line.strip().upper().startswith('SELECT'):
                in_query = True
            if in_query:
                query += line + " "
                if line.strip().endswith(';'):
                    return query.strip()
        
        return query.strip() if query else None


    
    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        """Execute natural language query and return results"""
        timing = {}
        
        # Check database connection
        if not self.db_connected:
            return QueryResponse(
                success=False,
                error=getattr(self, 'db_error', 'Database not connected'),
                timing=timing
            )
        
        try:
            # Step 1: Get LLM response
            print(f"STEP 2: Starting LLM call ({request.model})")
            llm_start = time.time()

            if request.model == "gemini":
                llm_response = self.query_gemini_sync(request.question)
            elif request.model == "gpt-oss":
                llm_response = await self.query_gpt_oss(request.question)
            else:
                return QueryResponse(
                    success=False,
                    error=f"Unknown model: {request.model}. Use 'gpt-oss' or 'gemini'",
                    timing=timing
                )

            timing['llm_time'] = time.time() - llm_start
            print(f"STEP 3: LLM finished in {timing['llm_time']:.2f}s")
            
            if not llm_response:
                return QueryResponse(
                    success=False,
                    error="Failed to get response from LLM. Make sure Ollama is running.",
                    timing=timing
                )
            
            # Step 2: Extract SQL
            sql_query = self._extract_sql(llm_response)
            if not sql_query:
                return QueryResponse(
                    success=False,
                    error="Could not extract SQL query from LLM response",
                    timing=timing,
                    sql_query=llm_response if request.include_sql else None
                )
            
            # Step 3: Execute query
            db_start = time.time()
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            timing['db_time'] = time.time() - db_start
            timing['total_time'] = timing['llm_time'] + timing['db_time']
            
            # Convert DataFrame to JSON-serializable format
            data = df.to_dict('records')
            columns = df.columns.tolist()
            
            return QueryResponse(
                success=True,
                data=data,
                columns=columns,
                sql_query=sql_query if request.include_sql else None,
                timing=timing,
                rows_returned=len(data)
            )
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResponse(
                success=False,
                error=f"Query execution failed: {str(e)}",
                timing=timing,
                sql_query=sql_query if request.include_sql and 'sql_query' in locals() else None
            )

# Global service instance
nfl_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global nfl_service
    nfl_service = NFLQueryService('nfl_complete_database.db')
    logger.info("NFL Query Service initialized")
    yield
    # Shutdown
    logger.info("NFL Query Service shutting down")

# FastAPI app
app = FastAPI(
    title="🏈 NFL Query API",
    description="Natural language interface for NFL statistics using GPT-OSS and 2024 play-by-play data",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/", summary="Root endpoint")
async def root():
    return {
        "message": "🏈 NFL Natural Language Query API",
        "version": "1.0.0",
        "endpoints": {
            "/query": "POST - Execute natural language queries",
            "/status": "GET - Check database status",
            "/health": "GET - Health check"
        }
    }


@app.get("/models", summary="Get available LLM models")
async def get_available_models():
    models = [
        {
            "id": "gpt-oss",
            "name": "GPT-OSS (Local)",
            "description": "Local model",
            "available": True,
            "cost": "Free"
        }
    ]

    # Check if Gemini is available
    if nfl_service and getattr(nfl_service, 'gemini_available', False):
        models.append({
            "id": "gemini",
            "name": "Google Gemini Pro",
            "description": "Gemini",
            "available": True,
            "cost": "N/A"
        })
    else:
        models.append({
            "id": "gemini",
            "name": "Google Gemini Pro",
            "description": "Testing with Gemini",
            "available": False,
            "cost": "N/A"
        })

    return {"models": models}

@app.get("/health", summary="Health check")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/status", response_model=DatabaseStatus, summary="Get database status")
async def get_status():
    if nfl_service.db_connected:
        return DatabaseStatus(
            connected=True,
            total_plays=nfl_service.total_plays
        )
    else:
        return DatabaseStatus(
            connected=False,
            error=getattr(nfl_service, 'db_error', 'Unknown error')
        )

@app.post("/query", response_model=QueryResponse, summary="Execute natural language query")
async def execute_query(request: QueryRequest):
    if not nfl_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await nfl_service.execute_query(request)
    
    if not result.success and "failed" in result.error.lower():
        raise HTTPException(status_code=400, detail=result.error)
    
    return result

@app.get("/examples", summary="Get example queries")
async def get_examples():
    return {
        "examples": [
            "Top 5 QBs by passing yards",
            "Jared Goff completion percentage", 
            "Third down conversion leaders with minimum 50 attempts",
            "Red zone touchdown percentage for top QBs",
            "QBs with most 300+ yard games",
            "Joe Burrow vs Patrick Mahomes passing stats",
            "Worst interception rate among starting QBs"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )