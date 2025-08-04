from fastapi import FastAPI, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from mangum import Mangum
from database import create_user, verify_user, get_user_by_email, get_user_by_username, update_user_password
import os, subprocess, uuid, boto3, tempfile

app = FastAPI(root_path="/prod")
templates = Jinja2Templates(directory="templates")

# S3 bucket setup
S3_BUCKET_NAME = os.getenv("pdflambdabucket1575")
s3_client = boto3.client("s3")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- PDF conversion endpoint ---
@app.post("/convert")
async def convert_to_pdf(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, file_id + ".docx")
    output_path = os.path.join(UPLOAD_DIR, file_id + ".pdf")

    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Ensure libreoffice is installed and accessible in your environment
    try:
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", UPLOAD_DIR], check=True)
    except subprocess.CalledProcessError as e:
        print(f"LibreOffice conversion failed: {e}")
        return JSONResponse({"status": "failed", "message": "PDF conversion failed."}, status_code=500)
    except FileNotFoundError:
        print("LibreOffice command not found. Please ensure LibreOffice is installed and in your PATH.")
        return JSONResponse({"status": "failed", "message": "Server error: PDF converter not found."}, status_code=500)

    if os.path.exists(output_path):
        return JSONResponse({"status": "completed", "file_id": file_id})
    else:
        return JSONResponse({"status": "failed", "message": "PDF output file not found after conversion."}, status_code=500)


@app.get("/download/{file_id}")
async def download_pdf(file_id: str):
    pdf_path = os.path.join(UPLOAD_DIR, file_id + ".pdf")
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, filename="converted.pdf")
    return JSONResponse({"error": "File not found"}, status_code=404)

# --- Registration ---
@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    root_path = request.scope.get("root_path", "/prod")  # Default to /prod for API Gateway
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "root_path": root_path}
    )

@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "/prod")  # Default to /prod for API Gateway
    if create_user(username, email, password):
        return RedirectResponse(f"{root_path}/login?message=registration_success", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": "Username or Email already exists"})

# --- Login ---
@app.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    root_path = request.scope.get("root_path", "/prod")  # Default to /prod for API Gateway
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "message": message, "error": error})

@app.post("/", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "/prod")  # Default to /prod for API Gateway
    if verify_user(username, password):
        return RedirectResponse(f"{root_path}/dashboard?username={username}", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "error": "Invalid username or password"})

# --- Forgot Password ---
@app.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    root_path = request.scope.get("root_path", "/prod")
    error = request.query_params.get("error")
    return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": error})

@app.post("/reset_password_direct")
async def reset_password_direct(request: Request, username_or_email: str = Form(...), new_password: str = Form(...), confirm_new_password: str = Form(...)):
    root_path = request.scope.get("root_path", "/prod")
    if new_password != confirm_new_password:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": "Passwords do not match."})

    user = get_user_by_email(username_or_email) or get_user_by_username(username_or_email)
    if user and update_user_password(user["email"], new_password):
        return RedirectResponse(f"{root_path}/?message=password_reset_success", status_code=303)
    else:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": "No account found or reset failed."})

# ---Dashboard ---
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Query("Guest")):
    root_path = request.scope.get("root_path", "/prod")
    user = {"username": username}
    return templates.TemplateResponse("dashboard.html", {"request": request, "root_path": root_path, "user": user})

# Lambda entry point
handler = Mangum(app)
