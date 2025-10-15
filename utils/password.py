import bcrypt


def hashPassword(plainPassword: str) -> str:
    passwordBytes = plainPassword.encode('utf-8')
    encBytes = bcrypt.hashpw(passwordBytes, bcrypt.gensalt())
    encPassword = encBytes.decode('utf-8')

    return encPassword


def verifyPassword(plainPassword: str, hashedPassword: str) -> bool:
    plainBytes = plainPassword.encode('utf-8')
    hashedBytes = hashedPassword.encode('utf-8')

    return bcrypt.checkpw(plainBytes, hashedBytes)