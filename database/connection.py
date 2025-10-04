import sqlite3

from llm.provider import LLMProvider
import logging
import requests

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, db_path: str):
        self._totalPlays = None
        self._db_path = db_path
        self._connection = None
        self._isConnected = False

    @property
    def isConnected(self):
        return self._isConnected

    @property
    def totalPlays(self):
        return self._totalPlays

    @property
    def db_path(self):
        return self._db_path


    def connect(self):
        try:
            self._connection = sqlite3.connect(self._db_path)
            cursor = self._connection.execute("SELECT COUNT(*) FROM plays")
            totalPlays = cursor.fetchone()[0]
            self._isConnected = True
            self._totalPlays = totalPlays
            logger.info(f"Database connection established: {self._totalPlays} plays loaded")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self._isConnected = False
            self._connection = None



    def disconnect(self):
        if self._isConnected:
            self._connection.close()
            self._isConnected = False
        else:
            logger.info("Database has already been disconnected")

    def executeQuery(self, sql: str):
        pass


class QueryProcessor(DatabaseConnection):
    def __init__(self, db_path: str, llm_provider: LLMProvider):
        super().__init__(db_path)
        self._llm_provider = llm_provider

    def processInput(self, query: str):
        sql = self._llm_provider.generateSQL(query)
        return self.executeQuery(sql)