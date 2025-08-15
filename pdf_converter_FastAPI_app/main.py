# main.py
import os
import subprocess
import uuid
import logging
import tempfile
import boto3
from fastapi import FastAPI, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles
from starlette import status
from mangum import Mangum
from database import create_user, verify_user, get_user_by_email, get_user_by_username, update_user_password

# -------------------- Logging --------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -------------------- FastAPI App --------------------
# Removed root_path="/prod". Mangum handles this automatically with API Gateway.
app = FastAPI(root_path=FASTAPI_ROOT_PATH)
templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------- S3 Setup --------------------
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client("s3")

# -------------------- LibreOffice Path --------------------
LIBREOFFICE_PATH = '/mnt/libreoffice/instdir/program/soffice.bin'

# -------------------- Health Check for LibreOffice --------------------
try:
    version_check = subprocess.run([LIBREOFFICE_PATH, "--version"], capture_output=True, text=True)
    logger.info(f"LibreOffice version: {version_check.stdout.strip()}")
except FileNotFoundError:
    logger.error(f"LibreOffice binary not found at {LIBREOFFICE_PATH}. Check Lambda Layer ARN.")
except Exception as e:
    logger.error(f"LibreOffice check failed: {e}")

# -------------------- PDF Conversion Endpoint --------------------
@app.post("/convert")
async def convert_to_pdf(file: UploadFile = File(...)):
    if not S3_BUCKET_NAME:
        logger.error("S3_BUCKET_NAME environment variable not set.")
        return JSONResponse(
            {"status": "failed", "message": "Server configuration error: S3 bucket not set."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if not file.filename.lower().endswith(".docx"):
        logger.warning(f"Received non-DOCX file for conversion: {file.filename}")
        return JSONResponse(
            {"status": "failed", "message": "Only .docx files are supported for conversion."},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    file_id = str(uuid.uuid4())
    input_docx_temp_path = os.path.join(tempfile.gettempdir(), f"{file_id}.docx")
    output_pdf_temp_path = os.path.join(tempfile.gettempdir(), f"{file_id}.pdf")
    docx_s3_key = f"uploads/{file_id}.docx"
    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    original_path_env = os.environ.get('PATH', '')
    original_home_env = os.environ.get('HOME', '')

    try:
        os.environ['PATH'] = f"{os.path.dirname(LIBREOFFICE_PATH)}:{original_path_env}"
        os.environ['HOME'] = tempfile.gettempdir()

        logger.info(f"Saving uploaded DOCX from '{file.filename}' to '{input_docx_temp_path}'")
        with open(input_docx_temp_path, "wb") as f:
            f.write(await file.read())

        logger.info(f"Uploading original DOCX to s3://{S3_BUCKET_NAME}/{docx_s3_key}")
        s3_client.upload_file(input_docx_temp_path, S3_BUCKET_NAME, docx_s3_key)

        logger.info(f"Starting LibreOffice conversion for '{input_docx_temp_path}' to '{output_pdf_temp_path}'")
        result = subprocess.run(
            [
                LIBREOFFICE_PATH,
                "--headless",
                "--nologo",
                "--convert-to",
                "pdf",
                input_docx_temp_path,
                "--outdir",
                tempfile.gettempdir()
            ],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"LibreOffice stdout: {result.stdout}")
        logger.info(f"LibreOffice stderr: {result.stderr}")

        if os.path.exists(output_pdf_temp_path):
            logger.info(f"Uploading converted PDF to s3://{S3_BUCKET_NAME}/{pdf_s3_key}")
            s3_client.upload_file(output_pdf_temp_path, S3_BUCKET_NAME, pdf_s3_key)
            return JSONResponse({"status": "completed", "file_id": file_id})
        else:
            logger.error(f"PDF output file not found after conversion: '{output_pdf_temp_path}'")
            return JSONResponse(
                {"status": "failed", "message": "PDF output file not found after conversion."},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except subprocess.CalledProcessError as e:
        logger.error(f"LibreOffice failed: {e.stderr}")
        return JSONResponse(
            {"status": "failed", "message": f"LibreOffice conversion failed: {e.stderr}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"An error occurred during conversion for file '{file.filename}': {e}", exc_info=True)
        return JSONResponse(
            {"status": "failed", "message": f"An unexpected server error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if os.path.exists(input_docx_temp_path):
            os.remove(input_docx_temp_path)
            logger.info(f"Cleaned up '{input_docx_temp_path}'")
        if os.path.exists(output_pdf_temp_path):
            os.remove(output_pdf_temp_path)
            logger.info(f"Cleaned up '{output_pdf_temp_path}'")
        os.environ['PATH'] = original_path_env
        os.environ['HOME'] = original_home_env

# -------------------- Download PDF --------------------
@app.get("/download/{file_id}")
async def download_pdf(file_id: str):
    if not S3_BUCKET_NAME:
        logger.error("S3_BUCKET_NAME environment variable not set for download.")
        return JSONResponse(
            {"status": "failed", "message": "Server configuration error: S3 bucket not set."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': pdf_s3_key},
            ExpiresIn=300
        )
        logger.info(f"Generated presigned URL for s3://{S3_BUCKET_NAME}/{pdf_s3_key}")
        return RedirectResponse(presigned_url, status_code=status.HTTP_303_SEE_OTHER)
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"Download request for non-existent file: {pdf_s3_key}")
            return JSONResponse(
                {"error": "File not found. It may have been deleted or never existed."},
                status_code=status.HTTP_404_NOT_FOUND
            )
        logger.error(f"Error generating presigned URL for '{pdf_s3_key}': {e}", exc_info=True)
        return JSONResponse(
            {"error": "Could not generate download link due to an S3 error."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during download for '{file_id}': {e}", exc_info=True)
        return JSONResponse(
            {"error": "An unexpected server error occurred during download."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# -------------------- Authentication & Dashboard Endpoints --------------------
@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    root_path = request.scope.get("root_path", "")
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path})

@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    success, message = create_user(username, email, password)
    if success:
        return RedirectResponse(f"{root_path}/?message=registration_success", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": message})

@app.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    root_path = request.scope.get("root_path", "")
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "message": message, "error": error})

@app.post("/", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    if verify_user(username, password):
        return RedirectResponse(f"{root_path}/dashboard?username={username}", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "error": "Invalid username or password"})

@app.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    root_path = request.scope.get("root_path", "")
    error = request.query_params.get("error")
    return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": error})

@app.post("/reset_password_direct")
async def reset_password_direct(request: Request, username_or_email: str = Form(...), new_password: str = Form(...), confirm_new_password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    if new_password != confirm_new_password:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": "Passwords do not match."})
    success, message = update_user_password(username_or_email, new_password)
    if success:
        return RedirectResponse(f"{root_path}/?message=password_reset_success", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": message})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Query("Guest")):
    root_path = request.scope.get("root_path", "")
    user = {"username": username}
    return templates.TemplateResponse("dashboard.html", {"request": request, "root_path": root_path, "user": user})

# -------------------- Lambda Entry Point --------------------
handler = Mangum(app, api_gateway_base_path=FASTAPI_ROOT_PATH)
