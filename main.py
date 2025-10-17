#!/usr/bin/env python3
"""
FastAPI Backend for NFL Natural Language Query System
Refactored with OOP architecture
"""
import sqlite3

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from contextlib import asynccontextmanager
from database.userDB import UserDatabase
from models.user import User
from utils.authDependencies import setUserDatabase, getCurrentUser
from utils.jwt import createAccessToken
from services.queryProcessor import QueryProcessor
from llm.geminiProvider import GeminiProvider
from utils.password import hashPassword, verifyPassword

# GLOBAL VARIABLES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
userDb: Optional[UserDatabase] = None

# DB NAMES

NFL_DB = 'nfl_complete_database.db'
USER_DB = 'nfl_users.db'

# Pydantic Models (API Layer)

class QueryRequest(BaseModel):
    question: str = Field(..., description = "What do you want to know?")
    include_sql: bool = Field(default = False, description = "Include generated SQL in response")
    model: str = Field(default = "gemini", description = "LLM model to use (currently only 'gemini')")


# Query response endpoint class
class QueryResponse(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    sqlQuery: Optional[str] = None
    error: Optional[str] = None
    timing: Dict[str, float] = Field(default_factory=dict)
    rowsReturned: int = 0


# db status endpoint class
class DatabaseStatus(BaseModel):
    connected: bool
    totalPlays: int = 0
    error: Optional[str] = None


# AUTH REQUEST CLASSES

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length = 3, max_length = 50, description = "Username")
    email: str = Field(..., description = "Email address")
    password: str = Field(..., min_length = 8, description = "Password (minimum 8 characters)")


class LoginRequest(BaseModel):
    username: str = Field(..., description = "Username")
    password: str = Field(..., description = "Password"

                          )
class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = Field(None, min_length = 3, max_length = 50, description = "Username")
    email: Optional[str] = Field(None)


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(..., description = "Verify your current password")
    newPassword: str = Field(..., min_length = 8, description = "New password (minimum 8 characters)")


class MessageResponse(BaseModel):
    success: bool
    message: str


# SAVED QUERY REQUEST CLASSES
class SaveQueryRequest(BaseModel):
    queryText: str = Field(..., description = "Query text")
    queryName: Optional[str] = Field(None, description = "Query name")


class SavedQueryResponse(BaseModel):
    success: bool
    message: str
    query: Optional[Dict[str, Any]] = None


class SavedQueriesListResponse(BaseModel):
    success: bool
    queries: List[Dict[str, Any]] = Field(default_factory = list)
    count: int = 0


# ====================================================================


# Initialization

queryProcessor: Optional[QueryProcessor] = None
geminiProvider: Optional[GeminiProvider] = None

@asynccontextmanager
async def lifespan(app: FastAPI):

    global queryProcessor, geminiProvider, userDb

    logger.info("Initializing Ask me NFL...")

    try:
        geminiProvider = GeminiProvider(modelName = 'gemini-2.5-pro')
        logger.info(f"✓ Gemini Provider initialized")

        queryProcessor = QueryProcessor(
            db_path = NFL_DB,
            llm_provider = geminiProvider
        )

        userDb = UserDatabase(USER_DB)
        userDb.createTable()
        setUserDatabase(userDb)
        logger.info('User database initialized')

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
    allow_origins=["*"],
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


@app.post("/query", response_model = QueryResponse, summary = "Execute query")
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


@app.get("/examples", summary = "Example queries")
async def get_examples():

    return {
        "examples": [
            "Top 5 QBs by passing yards per attempt in 2025",
            "Jared Goff vs. Patrick Mahomes major QB statistics",
            "When was the last time Jared Goff threw 3 interceptions in a single game?",
            "2024 QB leaders in redzone interceptions",
            "Compare Sam Darnold and Baker Mayfield all passing stats 2025",
            "What's the highest single game sack count for a defender, all-time?",
            "Which teams have turned the ball over the most on third down?",
            "Show me TJ Watt's total sacks vs. divisional opponents all-time"
        ]
    }

# =====================================

# AUTH ENDPOINTS

@app.post("/auth/register", response_model = AuthResponse, summary = "Register new user")
async def register_user(request: RegisterRequest):
    if not userDb:
        raise HTTPException(status_code = 503, detail="Service not initialized")

    if userDb.getUserByUsername(request.username):
        return AuthResponse(success = False, message = "Username already registered")
    if userDb.getUserByEmail(request.email):
        return AuthResponse(success = False, message = "Email already registered")

    encPassword = hashPassword(request.password)

    try:
        newUser = userDb.createUser(request.username, request.email, encPassword)
        token = createAccessToken({"sub": newUser.username})

        return AuthResponse(success = True, message = "User registered successfully",
                            token = token, user = newUser.toDict())

    except sqlite3.IntegrityError as ie:
        return AuthResponse(success = False, message = "Username or email already registered")
    except Exception as ex:
        logger.error(f"Registration failed: ")
        return AuthResponse(success = False, message = str(ex))


@app.post("/auth/login", response_model = AuthResponse, summary = "Login")
async def login_user(request: LoginRequest):
    if not userDb:
        raise HTTPException(status_code = 503, detail="Service not initialized")

    user = userDb.getUserByUsername(request.username)
    if user is None:
        return AuthResponse(success = False, message = "Invalid credentials")

    if not verifyPassword(request.password, user.encPassword):
        return AuthResponse(success = False, message = "Invalid credentials")

    token = createAccessToken({"sub": user.username})
    return AuthResponse(success = True, message = "Login successful", token = token, user = user.toDict())


@app.get("/auth/profile", response_model = Dict[str, Any], summary = "Get user profile")
async def get_profile(currentUser: User = Depends(getCurrentUser)):
    return currentUser.toDict()


@app.put("/auth/profile", response_model = MessageResponse, summary = "Update user profile")
async def update_profile(request: UpdateProfileRequest, currentUser: User = Depends(getCurrentUser)):
    if not userDb:
        raise HTTPException(status_code = 503, detail="Service not initialized")

    if request.username is None and request.email is None:
        return MessageResponse(success = False, message = "No user to update")

    try:
        userDb.updateUser(
            currentUser.id,
            username = request.username,
            email = request.email
        )

        return MessageResponse(success = True, message = "User profile updated successfully")

    except sqlite3.IntegrityError as ie:
        return MessageResponse(success = False, message = "Username or email already exists")
    except Exception as ex:
        logger.error(f"Profile update failed: ")
        return MessageResponse(success = False, message = str(ex))


@app.put("/auth/password", response_model = MessageResponse, summary = "Change password")
async def change_password(request: ChangePasswordRequest, currentUser: User = Depends(getCurrentUser)):
    if not userDb:
        raise HTTPException(status_code = 503, detail="Service not initialized")

    if not verifyPassword(request.currentPassword, currentUser.encPassword):
        return MessageResponse(success = False, message = "Current password is incorrect")

    encPassword = hashPassword(request.newPassword)

    try:
        userDb.updatePassword(
            currentUser.id,
            encPassword
        )

        return MessageResponse(success = True, message = "Password changed successfully")

    except Exception as ex:
        logger.error(f"Change password failed: ")
        return MessageResponse(success = False, message = str(ex))


@app.delete("/auth/account", response_model = MessageResponse, summary = "Delete account")
async def delete_account(currentUser: User = Depends(getCurrentUser)):
    if not userDb:
        raise HTTPException(status_code = 503, detail = "Service not initialized")

    isDeleted = userDb.deleteUser(currentUser.id)
    if not isDeleted:
        return MessageResponse(success = False, message = "Account could not be deleted")

    return MessageResponse(success = True, message = "Account deleted successfully")


# SAVED QUERY ENDPOINTS

@app.post("/queries/save", response_model = SavedQueryResponse, summary = "Save a query")
async def save_query(request: SaveQueryRequest, currentUser: User = Depends(getCurrentUser)):
    if not userDb:
        raise HTTPException(status_code = 503, detail = "Service not initialized")

    try:
        if request.queryName:
            queryName = request.queryName
        else:
            queryName = "Untitled query"

        savedQuery = userDb.createSavedQuery(
            userID = currentUser.id,
            queryContent = request.queryText,
            queryName = queryName
        )

        return SavedQueryResponse(
            success = True,
            message = "Query saved successfully",
            query = savedQuery.toDict()
        )

    except Exception as e:
        logger.error(f"Failed to save query: {e}")
        return SavedQueryResponse(
            success = False,
            message = "Failed to save query"
        )


@app.get("/queries", response_model = SavedQueriesListResponse, summary = "Get all saved queries")
async def get_saved_queries(currentUser: User = Depends(getCurrentUser)):
    if not userDb:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        queries = userDb.getAllSavedQueries(currentUser.id)
        queriesList = [q.toDict() for q in queries]

        return SavedQueriesListResponse(
            success = True,
            queries = queriesList,
            count = len(queriesList)
        )

    except Exception as e:
        logger.error(f"Failed to get saved queries: {e}")
        return SavedQueriesListResponse(
            success = False,
            queries = [],
            count = 0
        )


@app.put("/queries/{queryId}", response_model = SavedQueryResponse, summary = "Update a saved query")
async def update_saved_query(
        queryId: int,
        request: SaveQueryRequest,
        currentUser: User = Depends(getCurrentUser)
):

    if not userDb:
        raise HTTPException(status_code = 503, detail = "Service not initialized")

    query = userDb.getQueryByID(queryId)

    if query is None:
        return SavedQueryResponse(
            success = False,
            message = "Query not found"
        )

    if query.userID != currentUser.id:
        return SavedQueryResponse(
            success = False,
            message = "Unauthorized to modify this query"
        )

    try:
        updatedQuery = userDb.updateSavedQuery(
            queryID = queryId,
            queryContent = request.queryText,
            queryName = request.queryName
        )

        return SavedQueryResponse(
            success = True,
            message = "Query updated successfully",
            query = updatedQuery.toDict()
        )

    except Exception as e:
        logger.error(f"Failed to update query: {e}")
        return SavedQueryResponse(
            success = False,
            message = "Failed to update query"
        )


@app.delete("/queries/{queryId}", response_model = MessageResponse, summary = "Delete a saved query")
async def delete_saved_query(
        queryId: int,
        currentUser: User = Depends(getCurrentUser)
):

    if not userDb:
        raise HTTPException(status_code = 503, detail = "Service not initialized")

    query = userDb.getQueryByID(queryId)

    if query is None:
        return MessageResponse(
            success = False,
            message = "Query not found"
        )

    if query.userID != currentUser.id:
        return MessageResponse(
            success = False,
            message = "Unauthorized to delete this query"
        )

    try:
        success = userDb.deleteSavedQuery(queryId)

        if not success:
            return MessageResponse(
                success = False,
                message = "Failed to delete query"
            )

        return MessageResponse(
            success = True,
            message = "Query deleted successfully"
        )

    except Exception as e:
        logger.error(f"Failed to delete query: {e}")
        return MessageResponse(
            success = False,
            message = "Failed to delete query"
        )


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