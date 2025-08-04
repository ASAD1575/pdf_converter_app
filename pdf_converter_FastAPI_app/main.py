from fastapi import FastAPI, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from mangum import Mangum
from database import create_user, verify_user, get_user_by_email, get_user_by_username, update_user_password
import os, subprocess, uuid, boto3, tempfile

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# S3 bucket setup
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client("s3")

# --- PDF conversion endpoint ---
@app.post("/convert")
async def convert_to_pdf(file: UploadFile = File(...)):
    # (Unchanged conversion logic)
    ...

@app.get("/download/{file_id}")
async def download_pdf(file_id: str):
    # (Unchanged download logic)
    ...

# --- Registration ---
@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    root_path = request.scope.get("root_path", "")  # Handles /prod in API Gateway
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "root_path": root_path}
    )

@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    if create_user(username, email, password):
        return RedirectResponse(f"{root_path}/login?message=registration_success", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": "Username or Email already exists"})

# --- Login ---
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    root_path = request.scope.get("root_path", "")
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "message": message, "error": error})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    if verify_user(username, password):
        return RedirectResponse(f"{root_path}/dashboard?username={username}", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "error": "Invalid username or password"})

# --- Forgot Password ---
@app.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    base_url = str(request.base_url).rstrip("/")
    error = request.query_params.get("error")
    return templates.TemplateResponse("forgot_password.html", {"request": request, "base_url": base_url, "error": error})

@app.post("/reset_password_direct")
async def reset_password_direct(request: Request, username_or_email: str = Form(...), new_password: str = Form(...), confirm_new_password: str = Form(...)):
    base_url = str(request.base_url).rstrip("/")
    if new_password != confirm_new_password:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "base_url": base_url, "error": "Passwords do not match."})

    user = get_user_by_email(username_or_email) or get_user_by_username(username_or_email)
    if user and update_user_password(user["email"], new_password):
        return RedirectResponse(f"{base_url}/login?message=password_reset_success", status_code=303)
    else:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "base_url": base_url, "error": "No account found or reset failed."})

# --- Root and Dashboard ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse("login.html", {"request": request, "base_url": base_url})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Query("Guest")):
    base_url = str(request.base_url).rstrip("/")
    user = {"username": username}
    return templates.TemplateResponse("dashboard.html", {"request": request, "base_url": base_url, "user": user})

# Lambda entry point
handler = Mangum(app)
