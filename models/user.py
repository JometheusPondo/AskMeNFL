class User:
    def __init__(self, userID, username, email, encPassword, createdAt, updatedAt):
        self.id = userID
        self.username = username
        self.email = email
        self.encPassword = encPassword
        self.createdAt = createdAt
        self.updatedAt = updatedAt

    def toDict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'createdAt': self.createdAt,
            'updatedAt': self.updatedAt,
        }


