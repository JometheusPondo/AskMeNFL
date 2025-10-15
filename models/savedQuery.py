class SavedQuery:
    def __init__(self, id, userID, queryContent, queryName, createdAt):
        self.id = id
        self.userID = userID
        self.queryContent = queryContent
        self.queryName = queryName
        self.createdAt = createdAt


    def toDict(self):
        return {
            'id': self.id,
            'userID': self.userID,
            'queryContent': self.queryContent,
            'queryName': self.queryName,
            'createdAt': self.createdAt,
        }