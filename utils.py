import re

def check_password(password):
    if not 16 < len(password) < 8:
        return False
    if not re.match(r'^[A-Za-z0-9_-]*$', password):
        return False
    return True