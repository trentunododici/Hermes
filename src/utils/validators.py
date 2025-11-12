import re

def validate_username(value: str) -> str:
        value = value.lower().strip()

        if len(value) < 3 or len(value) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
            raise ValueError('Username can only contain letters, numbers, and _ . - characters')
        if value.lower() in {'admin', 'root', 'superuser', 'system'}:
            raise ValueError('This username is reserved and cannot be used')
        return value

def validate_password(value: str) -> str:
    if len(value) < 8:
            raise ValueError('Password must be at least 8 characters')
    if len(value) > 128:
        raise ValueError('Password must be at most 128 characters')

    if not re.search(r"[A-Z]", value):
        raise ValueError('Password must contain at least one uppercase letter')
    if not re.search(r"[a-z]", value):
        raise ValueError('Password must contain at least one lowercase letter')
    if not re.search(r"[0-9]", value):
        raise ValueError('Password must contain at least one digit')
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError('Password must contain at least one special character')
    return value

def normalize_username(value: str) -> str:
    value = value.lower().strip()

    if len(value) == 0:
        raise ValueError("Username cannot be empty")
    if len(value) < 3:
        raise ValueError("Username must be at least 3 characters")
    if len(value) > 50:
        raise ValueError("Username must be at most 50 characters")
    if ' ' in value:
        raise ValueError("Username cannot contain spaces")
    return value