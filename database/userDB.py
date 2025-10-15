import sqlite3
from typing import List

from models.savedQuery import SavedQuery
from models.user import User


class UserDatabase:
    def __init__(self, dbPath: str):
        self.dbPath = dbPath


    def createTable(self):
        createStatement = ["""CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            encPassword TEXT NOT NULL,
                            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updatedAT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                            
                          CREATE TABLE IF NOT EXISTS saved_queries (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            userID INTEGER NOT NULL,
                            queryContent TEXT NOT NULL,
                            queryName TEXT,
                            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (userID) REFERENCES users (id)
                            );"""
                       ]

        with sqlite3.connect(self.dbPath) as dbConnected:
            cursor = dbConnected.cursor()

            for statement in createStatement:
                cursor.execute(statement)
            dbConnected.commit()


    def createUser(self, username: str, email: str, encPassword: str) -> User:

        insertStatement = """INSERT INTO users (username, email, encPassword)
                                VALUES (?, ?, ?)"""

        with sqlite3.connect(self.dbPath) as dbConnected:
            cursor = dbConnected.cursor()
            cursor.execute(insertStatement, (username, email, encPassword))
            dbConnected.commit()

            newUserID = cursor.lastrowid

            selectStatement = """SELECT * FROM users WHERE id = ?"""
            cursor.execute(selectStatement, (newUserID,))

            userRow = cursor.fetchone()

            newUser = User (
                userID = userRow[0],
                username = userRow[1],
                email = userRow[2],
                encPassword = userRow[3],
                createdAt = userRow[4],
                updatedAt = userRow[5]
            )

            return newUser


    def getUserByID(self, userID: int) -> User | None:

        userStatement = """SELECT * FROM users WHERE id = ?"""

        with sqlite3.connect(self.dbPath) as dbConnected:
            cursor = dbConnected.cursor()
            cursor.execute(userStatement, (userID,))
            userRow = cursor.fetchone()

            if userRow is None:
                return None

            getUser = User (
                userID = userRow[0],
                username = userRow[1],
                email = userRow[2],
                encPassword = userRow[3],
                createdAt = userRow[4],
                updatedAt = userRow[5]
            )
            return getUser


    def getUserByUsername(self, username: str) -> User | None:
        userStatement = """SELECT * FROM users WHERE username = ?"""

        with sqlite3.connect(self.dbPath) as dbConnected:
            cursor = dbConnected.cursor()
            cursor.execute(userStatement, (username,))
            userRow = cursor.fetchone()

            if userRow is None:
                return None

            return User(
                userID=userRow[0],
                username=userRow[1],
                email=userRow[2],
                encPassword=userRow[3],
                createdAt=userRow[4],
                updatedAt=userRow[5]
            )


    def getUserByEmail(self, email: str) -> User | None:
        emailStatement = """SELECT * FROM users WHERE email = ?"""

        with sqlite3.connect(self.dbPath) as dbConnected:
            cursor = dbConnected.cursor()
            cursor.execute(emailStatement, (email,))
            userRow = cursor.fetchone()

            if userRow is None:
                return None

            getUser = User (
                userID = userRow[0],
                username = userRow[1],
                email = userRow[2],
                encPassword = userRow[3],
                createdAt = userRow[4],
                updatedAt = userRow[5]
            )
            return getUser


    def updateUser(self, userID: int, username: str = None, email: str = None) -> User | None:
        updateFields = []
        params = []

        if username is not None:
            updateFields.append("username = ?")
            params.append(username)

        if email is not None:
            updateFields.append("email = ?")
            params.append(email)

        if not updateFields:
            return self.getUserByID(userID)

        updateFields.append("updatedAt = CURRENT_TIMESTAMP")
        params.append(userID)

        updateStatement = f"""UPDATE users SET {', '.join(updateFields)} WHERE id = ?"""

        try:
            with sqlite3.connect(self.dbPath) as dbConnected:
                cursor = dbConnected.cursor()
                cursor.execute(updateStatement, params)
                dbConnected.commit()

                return self.getUserByID(userID)

        except sqlite3.IntegrityError as error:
            print("Update failed - username or email already exists:", error)
            raise
        except sqlite3.Error as error:
            print("Could not update user:", error)
            raise


    def deleteUser(self, userID: int) -> bool:
        deleteQueryStatement = """DELETE FROM saved_queries WHERE userID = ?"""
        deleteUserStatement = """DELETE FROM users WHERE id = ?"""

        try:
            with sqlite3.connect(self.dbPath) as dbConnected:
                cursor = dbConnected.cursor()

                cursor.execute(deleteQueryStatement, (userID,))
                cursor.execute(deleteUserStatement, (userID,))

                dbConnected.commit()
                return True

        except sqlite3.Error as error:
            print("Could not delete user", error)
            return False


    def updatePassword(self, userID: int, newEncPassword: str) -> bool:
        updateStatement = """UPDATE users 
                            SET encPassword = ?, updatedAt = CURRENT_TIMESTAMP 
                            WHERE id = ?"""

        try:
            with sqlite3.connect(self.dbPath) as dbConnected:
                cursor = dbConnected.cursor()
                cursor.execute(updateStatement, (newEncPassword, userID))
                dbConnected.commit()


                if cursor.rowcount == 0:
                    return False

                return True

        except sqlite3.Error as error:
            print("Could not update password:", error)
            return False


    def createSavedQuery(self, userID: int, queryContent: str, queryName: str) -> SavedQuery:
        saveQuery = """INSERT INTO saved_queries (userID, queryContent, queryName)
                        VALUES (?, ?, ?)"""

        with sqlite3.connect(self.dbPath) as dbConnected:
            cursor = dbConnected.cursor()
            cursor.execute(saveQuery, (userID, queryContent, queryName))
            dbConnected.commit()

            newQueryID = cursor.lastrowid

            selectStatement = """SELECT * FROM saved_queries WHERE id = ?"""
            cursor.execute(selectStatement, (newQueryID,))
            queryRow = cursor.fetchone()

            newSavedQuery = SavedQuery(
                id = queryRow[0],
                userID = queryRow[1],
                queryContent = queryRow[2],
                queryName = queryRow[3],
                createdAt = queryRow[4],
            )

            return newSavedQuery


    def getAllSavedQueries(self, userID: int) -> List[SavedQuery]:
        getStatement = """SELECT * FROM saved_queries WHERE userID = ?
                            ORDER BY createdAt DESC"""

        with sqlite3.connect(self.dbPath) as dbConnected:
            cursor = dbConnected.cursor()
            getSavedQueries = cursor.execute(getStatement, (userID,)).fetchall()

            allSavedQueries = []

            for row in getSavedQueries:
                query = SavedQuery(
                    id = row[0],
                    userID = row[1],
                    queryContent = row[2],
                    queryName = row[3],
                    createdAt = row[4],
                )
                allSavedQueries.append(query)

            return allSavedQueries


    def getQueryByID(self, queryID: int) -> SavedQuery | None:
        getStatement = """SELECT * FROM saved_queries WHERE id = ?"""

        with sqlite3.connect(self.dbPath) as dbConnected:
            cursor = dbConnected.cursor()
            queryRow = cursor.execute(getStatement, (queryID,)).fetchone()

            if queryRow is None:
                return None

            return SavedQuery(
                id = queryRow[0],
                userID = queryRow[1],
                queryContent = queryRow[2],
                queryName = queryRow[3],
                createdAt = queryRow[4],
            )


    def updateSavedQuery(self, queryID: int, queryContent: str = None, queryName: str = None) -> SavedQuery:

        updateFields = []
        params = []

        if queryContent is not None:
            updateFields.append("queryContent = ?")
            params.append(queryContent)

        if queryName is not None:
            updateFields.append("queryName = ?")
            params.append(queryName)

        if not updateFields:
            return self.getQueryByID(queryID)

        params.append(queryID)
        updateStatement = f"""UPDATE saved_queries SET {', '.join(updateFields)} WHERE id = ?"""

        with sqlite3.connect(self.dbPath) as dbConnected:
            cursor = dbConnected.cursor()
            cursor.execute(updateStatement, params)
            dbConnected.commit()

            return self.getQueryByID(queryID)


    def deleteSavedQuery(self, queryID: int) -> bool:
        deleteStatement = """DELETE FROM saved_queries WHERE id = ?"""

        try:
            with sqlite3.connect(self.dbPath) as dbConnected:
                cursor = dbConnected.cursor()
                cursor.execute(deleteStatement, (queryID,))
                dbConnected.commit()
                return True
        except sqlite3.Error as error:
            print("Could not delete saved query", error)
            return False



