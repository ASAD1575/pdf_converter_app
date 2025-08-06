from fastapi import FastAPI, File, UploadFile, Request, Form, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from mangum import Mangum
import os
import uuid
import tempfile
import subprocess
import boto3
import logging

from database import create_user, verify_user, get_user_by_email, get_user_by_username, update_user_password

# -------------------- Logging --------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -------------------- FastAPI App --------------------
app = FastAPI(root_path="/prod")
templates = Jinja2Templates(directory="templates")

# -------------------- S3 Setup --------------------
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client("s3")

# -------------------- LibreOffice Path --------------------
LIBREOFFICE_PATH = "/opt/instdir/program/soffice.bin"  # Correct path for most Lambda LibreOffice layers

# -------------------- Health Check for LibreOffice --------------------
try:
    version_check = subprocess.run([LIBREOFFICE_PATH, "--version"], capture_output=True, text=True)
    logger.info(f"LibreOffice version: {version_check.stdout or version_check.stderr}")
except FileNotFoundError:
    logger.error(f"LibreOffice binary not found at {LIBREOFFICE_PATH}. Check Lambda Layer.")
except Exception as e:
    logger.error(f"LibreOffice check failed: {e}")

# -------------------- PDF Conversion --------------------
@app.post("/convert")
async def convert_to_pdf(file: UploadFile = File(...)):
    if not S3_BUCKET_NAME:
        return JSONResponse({"status": "failed", "message": "S3 bucket not configured"}, status_code=500)

    if not file.filename.endswith(".docx"):
        return JSONResponse({"status": "failed", "message": "Only .docx files are supported"}, status_code=400)

    file_id = str(uuid.uuid4())
    input_docx = os.path.join(tempfile.gettempdir(), f"{file_id}.docx")
    output_pdf = os.path.join(tempfile.gettempdir(), f"{file_id}.pdf")

    docx_s3_key = f"uploads/{file_id}.docx"
    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    try:
        # Save uploaded DOCX
        with open(input_docx, "wb") as f:
            f.write(await file.read())

        # Upload original DOCX to S3
        s3_client.upload_file(input_docx, S3_BUCKET_NAME, docx_s3_key)

        # Convert to PDF
        result = subprocess.run(
            [
                LIBREOFFICE_PATH,
                "--headless",
                "--nologo",
                "--convert-to",
                "pdf",
                input_docx,
                "--outdir",
                tempfile.gettempdir()
            ],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"LibreOffice stdout: {result.stdout}")
        logger.info(f"LibreOffice stderr: {result.stderr}")

        if os.path.exists(output_pdf):
            s3_client.upload_file(output_pdf, S3_BUCKET_NAME, pdf_s3_key)
            return JSONResponse({"status": "completed", "file_id": file_id})
        else:
            return JSONResponse({"status": "failed", "message": "PDF not generated"}, status_code=500)

    except subprocess.CalledProcessError as e:
        logger.error(f"LibreOffice failed: {e.stderr}")
        return JSONResponse({"status": "failed", "message": e.stderr}, status_code=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return JSONResponse({"status": "failed", "message": str(e)}, status_code=500)
    finally:
        if os.path.exists(input_docx):
            os.remove(input_docx)
        if os.path.exists(output_pdf):
            os.remove(output_pdf)

# -------------------- Download PDF --------------------
@app.get("/download/{file_id}")
async def download_pdf(file_id: str):
    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': pdf_s3_key},
            ExpiresIn=300
        )
        return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return JSONResponse({"error": "File not found or link generation failed"}, status_code=404)

# -------------------- Authentication & Dashboard --------------------
@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "/prod")
    if create_user(username, email, password):
        return RedirectResponse(f"{root_path}/?message=registration_success", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": "Username or Email already exists"})

@app.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    root_path = request.scope.get("root_path", "/prod")
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "message": message, "error": error})

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    root_path = request.scope.get("root_path", "/prod")
    error = request.query_params.get("error")
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": error})

@app.post("/", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "/prod")
    if verify_user(username, password):
        return RedirectResponse(f"{root_path}/dashboard?username={username}", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "error": "Invalid username or password"})

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

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Query("Guest")):
    root_path = request.scope.get("root_path", "/prod")
    user = {"username": username}
    return templates.TemplateResponse("dashboard.html", {"request": request, "root_path": root_path, "user": user})

# -------------------- Lambda Entry --------------------
handler = Mangum(app)
