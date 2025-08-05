from fastapi import FastAPI, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette import status # Import status codes
from mangum import Mangum
import os, subprocess, uuid, boto3, tempfile
import logging # Import logging module

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(root_path="/prod")
templates = Jinja2Templates(directory="templates")

# S3 bucket setup
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client("s3")

# Define the full path to the LibreOffice executable within the Lambda layer
# Assuming LibreOffice is extracted to /opt/lo/instdir
LIBREOFFICE_PATH = "/opt/lo/instdir/program/soffice"

# --- PDF conversion endpoint ---
@app.post("/convert")
async def convert_to_pdf(file: UploadFile = File(...)):
    if not S3_BUCKET_NAME:
        logger.error("S3_BUCKET_NAME environment variable not set.")
        return JSONResponse({"status": "failed", "message": "Server configuration error: S3 bucket not set."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not file.filename.endswith(".docx"):
        return JSONResponse({"status": "failed", "message": "Only .docx files are supported for conversion."}, status_code=status.HTTP_400_BAD_REQUEST)

    file_id = str(uuid.uuid4())
    # original_filename = file.filename # Not used directly in this logic, but good to keep for metadata if needed
    
    # All temporary file operations MUST use /tmp in AWS Lambda
    input_docx_temp_path = os.path.join(tempfile.gettempdir(), file_id + ".docx")
    output_pdf_temp_path = os.path.join(tempfile.gettempdir(), file_id + ".pdf")

    docx_s3_key = f"uploads/{file_id}.docx"
    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    try:
        # 1. Save uploaded DOCX to /tmp
        logger.info(f"Saving uploaded DOCX to {input_docx_temp_path}")
        with open(input_docx_temp_path, "wb") as f:
            f.write(await file.read())

        # 2. (Optional) Upload original DOCX to S3 for backup/record
        logger.info(f"Uploading original DOCX to s3://{S3_BUCKET_NAME}/{docx_s3_key}")
        s3_client.upload_file(input_docx_temp_path, S3_BUCKET_NAME, docx_s3_key)

        # 3. Perform conversion using LibreOffice
        logger.info(f"Starting LibreOffice conversion for {input_docx_temp_path}")
        
        # Ensure the LibreOffice executable path is correct
        # Use a list for subprocess.run command and arguments
        result = subprocess.run(
            [LIBREOFFICE_PATH, "--headless", "--convert-to", "pdf", input_docx_temp_path, "--outdir", tempfile.gettempdir()],
            check=True, # Raise CalledProcessError if the command returns a non-zero exit code
            capture_output=True, # Capture stdout/stderr
            text=True # Decode stdout/stderr as text
        )
        logger.info(f"LibreOffice stdout: {result.stdout}")
        # LibreOffice often prints warnings/info to stderr even on success, so log as info
        if result.stderr:
            logger.info(f"LibreOffice stderr: {result.stderr}") 

        # 4. Check if PDF was created and upload to S3
        if os.path.exists(output_pdf_temp_path):
            logger.info(f"Uploading converted PDF to s3://{S3_BUCKET_NAME}/{pdf_s3_key}")
            s3_client.upload_file(output_pdf_temp_path, S3_BUCKET_NAME, pdf_s3_key)
            return JSONResponse({"status": "completed", "file_id": file_id})
        else:
            logger.error(f"PDF output file not found after conversion: {output_pdf_temp_path}")
            return JSONResponse({"status": "failed", "message": "PDF output file not found after conversion. Check LibreOffice logs."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except subprocess.CalledProcessError as e:
        logger.error(f"LibreOffice conversion failed: Command '{' '.join(e.cmd)}' returned {e.returncode}. "
                     f"Stdout: {e.stdout}. Stderr: {e.stderr}")
        return JSONResponse({"status": "failed", "message": "PDF conversion failed. Check server logs for details."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except FileNotFoundError:
        logger.error(f"LibreOffice command not found at {LIBREOFFICE_PATH}. Ensure Lambda Layer is correctly configured and the path is accurate.")
        return JSONResponse({"status": "failed", "message": "Server error: PDF converter (LibreOffice) not found or path is incorrect."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"An unexpected error occurred during conversion: {e}", exc_info=True)
        return JSONResponse({"status": "failed", "message": f"An unexpected server error occurred: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        # Clean up temporary files regardless of success or failure
        if os.path.exists(input_docx_temp_path):
            os.remove(input_docx_temp_path)
            logger.info(f"Cleaned up {input_docx_temp_path}")
        if os.path.exists(output_pdf_temp_path):
            os.remove(output_pdf_temp_path)
            logger.info(f"Cleaned up {output_pdf_temp_path}")


@app.get("/download/{file_id}")
async def download_pdf(file_id: str):
    if not S3_BUCKET_NAME:
        logger.error("S3_BUCKET_NAME environment variable not set for download.")
        return JSONResponse({"status": "failed", "message": "Server configuration error: S3 bucket not set."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    try:
        # Generate a presigned URL for direct download from S3
        # This avoids proxying large files through Lambda and is more efficient
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': pdf_s3_key},
            ExpiresIn=300 # URL valid for 5 minutes (300 seconds)
        )
        logger.info(f"Generated presigned URL for {pdf_s3_key}")
        # Use 303 for POST-redirect-GET pattern, especially if the conversion was a POST request
        return RedirectResponse(presigned_url, status_code=status.HTTP_303_SEE_OTHER) 
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"Download request for non-existent file: {pdf_s3_key}")
            return JSONResponse({"error": "File not found"}, status_code=status.HTTP_404_NOT_FOUND)
        logger.error(f"Error generating presigned URL for {pdf_s3_key}: {e}", exc_info=True)
        return JSONResponse({"error": "Could not generate download link."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"An unexpected error occurred during download: {e}", exc_info=True)
        return JSONResponse({"error": "An unexpected server error occurred."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Helper function to get root_path for templates and redirects
# Using app.root_path which is set in FastAPI() initialization
def get_current_root_path(request: Request) -> str:
    # FastAPI's root_path is automatically prepended by Mangum if configured correctly
    # or explicitly set in FastAPI(root_path=...)
    return request.app.root_path

@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "/prod")  # Default to /prod for API Gateway
    if create_user(username, email, password):
        return RedirectResponse(f"{root_path}/?message=registration_success", status_code=303)
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
