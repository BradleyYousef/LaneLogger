import bcrypt

def hash_password(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt())

def check_password(p, hashed):
    return bcrypt.checkpw(p.encode(), hashed)