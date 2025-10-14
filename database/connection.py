import sqlite3
import pandas as pd

import logging


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
            self._connection = sqlite3.connect(self._db_path, check_same_thread=False)
            self._isConnected = True

            cursor = self._connection.execute("SELECT COUNT(*) FROM plays")
            totalPlays = cursor.fetchone()[0]
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
        if not self._isConnected or self._connection is None:
            logger.error("Cannot execute query, database connection was not established")
            raise ConnectionError("Database not connected")

        try:
            df = pd.read_sql_query(sql, self._connection)
            logger.info(f"Query executed successfully: {len(df)} rows returned")
            return df

        except Exception as e:
            logger.error(f"Query execute failed: {e}")
            raise ValueError(f"Query execute failed: {e}")


