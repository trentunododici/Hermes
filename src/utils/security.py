from pwdlib import PasswordHash
import hashlib

password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def hash_token(token: str) -> str:
    """Hash a token using SHA256 for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()