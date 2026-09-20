from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import login_user, logout_user, is_authenticated

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def home(request: Request):
    user = request.session.get("username") if is_authenticated(request) else None

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user
        }
    )


@router.get("/login")
def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse(
            url="/dashboard",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "error": None
        }
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if login_user(request, username, password):
        return RedirectResponse(
            url="/dashboard",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "error": "Invalid username or password."
        },
        status_code=401
    )


@router.get("/dashboard")
def dashboard(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": request.session.get("username")
        }
    )


@router.get("/logout")
def logout(request: Request):
    logout_user(request)

    return RedirectResponse(
        url="/",
        status_code=303
    )
