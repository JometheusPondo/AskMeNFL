import time
import re
import logging
from typing import Optional, Dict, Any

from database.connection import DatabaseConnection
from llm.provider import LLMProvider

logger = logging.getLogger(__name__)

class QueryProcessor(DatabaseConnection):
    def __init__(self, db_path: str, llm_provider: LLMProvider):
        super().__init__(db_path)
        self._llm_provider = llm_provider
        self._queryHistory = []
        self._successfulQueries = 0
        self._failedQueries = 0

    def _extractSQL(self, llmResponse: str) -> Optional[str]:
        if "```sql" in llmResponse:
            try:
                return llmResponse.split("```sql")[1].split("```")[0].strip()
            except IndexError:
                pass


        lines = llmResponse.split("\n")
        query = ""
        in_query = False

        # Fallback: look for SELECT statements
        for line in lines:
            if line.strip().upper().startswith('SELECT'):
                in_query = True
            if in_query:
                query += line + " "
                if line.strip().endswith(';'):
                    return query.strip()

        return query.strip() if query else None

    def _validateSQL(self, sql: str) -> bool:
        if not sql or not sql.strip():
            logger.error("SQL query is empty")
            return False

        sqlUpper = sql.upper().strip()

        if not sqlUpper.startswith("SELECT"):
            logger.error("SQL query is invalid")
            return False

        riskKeywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC']

        for keyword in riskKeywords:
            if keyword in sqlUpper:
                logger.error("Prevented dropping table information")
                return False

        return True


    def processInput(self, query: str, includeSQL: bool = False) -> Dict[str, Any]:
        responseTime = {}
        sqlQuery = None

        try:
            llmStart = time.time()
            llmResponse = self._llm_provider.generateSQL(query)
            responseTime['llm_time'] = time.time() - llmStart

            if not llmResponse:
                logger.error(f"Service could not reach provider")
                self._failedQueries += 1
                return {
                    'success': False,
                    'error': "Service could not reach provider"
                }

            sqlQuery = self._extractSQL(llmResponse)

            if not sqlQuery:
                logger.error(f"Service could not extract SQL query")
                self._failedQueries += 1
                return {
                    'success': False,
                    'error': "Service could not extract SQL query"
                }

            if not self._validateSQL(sqlQuery):
                logger.error(f"Service could not extract SQL query")
                self._failedQueries += 1
                return {
                    'success': False,
                    'error': "Service could not validate SQL query",
                    'sqlQuery': sqlQuery if includeSQL else None
                }

            dbStart = time.time()
            df = self.executeQuery(sqlQuery)
            self._successfulQueries += 1
            responseTime['db_time'] = time.time() - dbStart
            responseTime['total_time'] = responseTime['llm_time'] + responseTime['db_time']

            data = df.to_dict('records')
            columns = df.columns.tolist()

            return {
                'success': True,
                'data': data,
                'columns': columns,
                'sqlQuery': sqlQuery if includeSQL else None,
                'responseTime': responseTime,
                'rowsReturned': len(data)
            }

        except Exception as e:
            logger.error(f"Service could not reach provider: {e}")
            self._failedQueries += 1
            return {
                'success': False,
                'error': "Service could not reach provider",
                'responseTime': responseTime,
                'sqlQuery': sqlQuery if includeSQL else None
            }
