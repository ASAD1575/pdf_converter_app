from fastapi import FastAPI, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
# The 'dotenv' import and 'load_dotenv()' call are removed for Lambda deployment.
# AWS Lambda will directly inject environment variables configured via Terraform.
# from dotenv import load_dotenv
# load_dotenv() # This loads variables from .env into os.environ

# Assuming these functions exist in your database.py and handle user/token operations
from database import create_user, verify_user, get_user_by_email, get_user_by_username, update_user_password
import os
import subprocess
import uuid
import boto3 # Import boto3 for AWS S3 interaction
import tempfile # For creating temporary files in Lambda's /tmp directory

app = FastAPI()
templates = Jinja2Templates(directory="templates")
# In Lambda, static files are typically served from S3 or CloudFront, not directly by FastAPI.
# For local development, this mount is fine. For Lambda, you'd likely use CloudFront.
app.mount("/static", StaticFiles(directory="static"), name="static")

# Get S3 bucket name from environment variables
# This will be set by Terraform when deploying to Lambda
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Initialize S3 client (will use IAM role credentials in Lambda)
s3_client = boto3.client("s3")

# --- PDF conversion endpoint ---
@app.post("/convert")
async def convert_to_pdf(file: UploadFile = File(...)):
    if not S3_BUCKET_NAME:
        return JSONResponse({"status": "failed", "message": "S3 bucket name not configured."}, status_code=500)

    file_id = str(uuid.uuid4())
    original_filename = file.filename
    docx_s3_key = f"uploads/{file_id}.docx"
    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    # Use tempfile to create temporary files in Lambda's /tmp directory
    # The /tmp directory is the only writable location in Lambda
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_docx_file:
        # Read the uploaded file content and write to the temporary file
        content = await file.read()
        temp_docx_file.write(content)
        temp_docx_file_path = temp_docx_file.name

    # Upload the original DOCX file to S3 (optional, but good for auditing/reprocessing)
    try:
        s3_client.upload_file(temp_docx_file_path, S3_BUCKET_NAME, docx_s3_key)
        print(f"Uploaded {original_filename} to s3://{S3_BUCKET_NAME}/{docx_s3_key}")
    except Exception as e:
        print(f"Error uploading DOCX to S3: {e}")
        os.remove(temp_docx_file_path) # Clean up temp file
        return JSONResponse({"status": "failed", "message": "Failed to upload DOCX to S3."}, status_code=500)

    # Prepare output path in /tmp for PDF conversion
    temp_pdf_file_path = os.path.join(tempfile.gettempdir(), f"{file_id}.pdf")

    # Ensure libreoffice is installed and accessible in your environment (via Lambda Layer)
    try:
        # LibreOffice command to convert DOCX to PDF
        # The --outdir must be a writable directory, so we use /tmp
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", temp_docx_file_path, "--outdir", tempfile.gettempdir()],
            check=True
        )
        print(f"Converted {temp_docx_file_path} to {temp_pdf_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"LibreOffice conversion failed: {e}")
        return JSONResponse({"status": "failed", "message": "PDF conversion failed."}, status_code=500)
    except FileNotFoundError:
        print("LibreOffice command not found. Please ensure LibreOffice is installed and in your PATH (via Lambda Layer).")
        return JSONResponse({"status": "failed", "message": "Server error: PDF converter not found."}, status_code=500)
    finally:
        # Clean up the temporary DOCX file immediately
        os.remove(temp_docx_file_path)

    # Check if PDF was created and upload to S3
    if os.path.exists(temp_pdf_file_path):
        try:
            s3_client.upload_file(temp_pdf_file_path, S3_BUCKET_NAME, pdf_s3_key)
            print(f"Uploaded converted PDF to s3://{S3_BUCKET_NAME}/{pdf_s3_key}")
            return JSONResponse({"status": "completed", "file_id": file_id})
        except Exception as e:
            print(f"Error uploading PDF to S3: {e}")
            return JSONResponse({"status": "failed", "message": "Failed to upload converted PDF to S3."}, status_code=500)
        finally:
            os.remove(temp_pdf_file_path) # Clean up temporary PDF file
    else:
        return JSONResponse({"status": "failed", "message": "PDF output file not found after conversion."}, status_code=500)


@app.get("/download/{file_id}")
async def download_pdf(file_id: str):
    if not S3_BUCKET_NAME:
        return JSONResponse({"status": "failed", "message": "S3 bucket name not configured."}, status_code=500)

    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    try:
        # Generate a pre-signed URL for direct download/view from S3
        # This is more efficient than streaming through Lambda
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': pdf_s3_key},
            ExpiresIn=300 # URL valid for 5 minutes
        )
        # Redirect the client to the pre-signed URL
        return RedirectResponse(presigned_url, status_code=303)
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return JSONResponse({"error": "File not found"}, status_code=404)
        else:
            print(f"Error generating presigned URL: {e}")
            return JSONResponse({"error": "Could not generate download link."}, status_code=500)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return JSONResponse({"error": "An unexpected server error occurred."}, status_code=500)


# --- Registration ---
@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if create_user(username, email, password): # Assumes create_user handles unique username/email
        return RedirectResponse("/login?message=registration_success", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "error": "Username or Email already exists"})

# --- Login ---
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "message": message, "error": error})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if verify_user(username, password):
        return RedirectResponse(f"/dashboard?username={username}", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

# --- Direct Password Reset ---
@app.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("forgot_password.html", {"request": request, "error": error})

@app.post("/reset_password_direct")
async def reset_password_direct(request: Request, username_or_email: str = Form(...), new_password: str = Form(...), confirm_new_password: str = Form(...)):
    if new_password != confirm_new_password:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "error": "Passwords do not match."})

    user = get_user_by_email(username_or_email)
    if not user:
        user = get_user_by_username(username_or_email)

    if user:
        if update_user_password(user["email"], new_password):
            return RedirectResponse("/login?message=password_reset_success", status_code=303)
        else:
            return templates.TemplateResponse("forgot_password.html", {"request": request, "error": "Failed to reset password. Please try again."})
    else:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "error": "No account found with that username or email."})

# --- Root and dashboard ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Query("Guest")):
    user = {"username": username}
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
