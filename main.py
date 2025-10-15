#!/usr/bin/env python3
"""
FastAPI Backend for NFL Natural Language Query System
Refactored with OOP architecture
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from contextlib import asynccontextmanager


from services.queryProcessor import QueryProcessor
from llm.geminiProvider import GeminiProvider


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===========================
# Pydantic Models (API Layer)
# ===========================

class QueryRequest(BaseModel):
    # Request model for query endpoint
    question: str = Field(..., description="What do you want to know?")
    include_sql: bool = Field(default=False, description="Include generated SQL in response")
    model: str = Field(default="gemini", description="LLM model to use (currently only 'gemini')")


class QueryResponse(BaseModel):
    # Response model for query endpoint
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    sqlQuery: Optional[str] = None
    error: Optional[str] = None
    timing: Dict[str, float] = Field(default_factory=dict)
    rowsReturned: int = 0


class DatabaseStatus(BaseModel):
    # Response model for status endpoint
    connected: bool
    totalPlays: int = 0
    error: Optional[str] = None




queryProcessor: Optional[QueryProcessor] = None
geminiProvider: Optional[GeminiProvider] = None


# ==============
# Initialization
# ==============

@asynccontextmanager
async def lifespan(app: FastAPI):

    global queryProcessor, geminiProvider

    # Startup: Initialize provider and processor
    logger.info("🚀 Initializing Ask me NFL...")

    try:
        geminiProvider = GeminiProvider(modelName='gemini-2.5-pro')
        logger.info(f"✓ Gemini Provider initialized")

        queryProcessor = QueryProcessor(
            db_path='nfl_complete_database.db',
            llm_provider=geminiProvider
        )

        queryProcessor.connect()

        schema = queryProcessor.getFullSchema()
        geminiProvider._databaseSchema = schema

        logger.info(f"✓ Database connected: {queryProcessor.isConnected}")
        logger.info(f"✓ Total plays loaded: {queryProcessor.totalPlays:,}")
        logger.info("✓ Ask me NFL ready!")

    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise

    yield

    logger.info("Shutting down Ask Me NFL...")
    if queryProcessor:
        queryProcessor.disconnect()


# ==========
# Main App
# ==========

app = FastAPI(
    title="🏈 Ask me NFL",
    description="Natural language interface for granular NFL statistics",
    version="2.0.0",
    lifespan=lifespan
)

# CORS connector to React front
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============
# API Endpoints
# =============

@app.get("/", summary="Root endpoint")
async def root():
    return {
        "message": "🏈 Ask me NFL v2.0",
        "architecture": "Object-Oriented Design",
        "version": "2.0.0",
        "endpoints": {
            "/query": "POST - Execute request queries",
            "/status": "GET - Check database status",
            "/models": "GET - Get available LLM models",
            "/health": "GET - Health check",
            "/examples": "GET - Get example queries"
        }
    }


@app.get("/health", summary="Health check")
async def health_check():
    return {
        "status": "healthy",
        "databaseConnected": queryProcessor.isConnected if queryProcessor else False
    }


@app.get("/status", response_model=DatabaseStatus, summary="Database status")
async def get_status():
    if not queryProcessor:
        raise HTTPException(status_code=503, detail="Service not initialized")

    if queryProcessor.isConnected:
        return DatabaseStatus(
            connected=True,
            totalPlays=queryProcessor.totalPlays
        )
    else:
        return DatabaseStatus(
            connected=False,
            error="Database not connected"
        )


@app.get("/models", summary="Available LLM models")
async def get_available_models():
    models = []

    if geminiProvider:
        models.append({
            "id": "gemini",
            "name": geminiProvider.getProviderName(),
            "model": geminiProvider._modelName,
            "available": True,
            "description": "Google Gemini AI"
        })

    return {"models": models}


@app.post("/query", response_model=QueryResponse, summary="Execute query")
async def execute_query(request: QueryRequest):

    if not queryProcessor:
        raise HTTPException(status_code=503, detail="Service not initialized")

    if request.model != "gemini":
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model: {request.model}. Currently only 'gemini' is supported."
        )


    result = queryProcessor.processInput(
        query=request.question,
        includeSQL=request.include_sql
    )


    if not result['success']:
        return QueryResponse(
            success=False,
            error=result.get('error', 'Unknown error'),
            timing=result.get('responseTime', {}),
            sqlQuery=result.get('sqlQuery')
        )


    return QueryResponse(
        success=True,
        data=result['data'],
        columns=result['columns'],
        rowsReturned=result['rowsReturned'],
        sqlQuery=result.get('sqlQuery'),
        timing=result['responseTime']
    )


@app.get("/examples", summary="Example queries")
async def get_examples():

    return {
        "examples": [
            "Top 5 QBs by passing yards per attempt in 2024",
            "Jared Goff vs. Patrick Mahomes major statistics",
            "Team Third down conversion leaders with minimum 50 attempts",
            "Top 10 teams redzone touchdown percentage",
            "Compare Sam Darnold and Baker Mayfield all passing stats",
            "Which defenders have the most sacks in 2024?",
            "Show me Myles Garrett's career statistics"
        ]
    }

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Ask me NFL...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )