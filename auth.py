from fastapi import Request

SESSION_TIMEOUT = 1000

USERS = {
    "admin": "data260"
}

def login_user(request: Request, username: str, password: str) -> bool:
    if username not in USERS or USERS[username] != password:
        return False

    request.session["username"] = username
    request.session["last_activity"] = __import__("time").time()
    return True

def logout_user(request: Request):
    request.session.clear()

def is_authenticated(request: Request) -> bool:
    username = request.session.get("username")
    last_activity = request.session.get("last_activity")

    if not username or not last_activity:
        return False

    now = __import__("time").time()

    if now - last_activity > SESSION_TIMEOUT:
        request.session.clear()
        return False

    request.session["last_activity"] = now
    return True