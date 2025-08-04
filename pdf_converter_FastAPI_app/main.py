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
    if not S3_BUCKET_NAME:
        return JSONResponse({"status": "failed", "message": "S3 bucket name not configured."}, status_code=500)

    file_id = str(uuid.uuid4())
    original_filename = file.filename
    docx_s3_key = f"uploads/{file_id}.docx"
    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_docx_file:
        content = await file.read()
        temp_docx_file.write(content)
        temp_docx_file_path = temp_docx_file.name

    try:
        s3_client.upload_file(temp_docx_file_path, S3_BUCKET_NAME, docx_s3_key)
        print(f"Uploaded {original_filename} to s3://{S3_BUCKET_NAME}/{docx_s3_key}")
    except Exception as e:
        print(f"Error uploading DOCX to S3: {e}")
        os.remove(temp_docx_file_path)
        return JSONResponse({"status": "failed", "message": "Failed to upload DOCX to S3."}, status_code=500)

    temp_pdf_file_path = os.path.join(tempfile.gettempdir(), f"{file_id}.pdf")

    try:
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
        os.remove(temp_docx_file_path)

    if os.path.exists(temp_pdf_file_path):
        try:
            s3_client.upload_file(temp_pdf_file_path, S3_BUCKET_NAME, pdf_s3_key)
            print(f"Uploaded converted PDF to s3://{S3_BUCKET_NAME}/{pdf_s3_key}")
            return JSONResponse({"status": "completed", "file_id": file_id})
        except Exception as e:
            print(f"Error uploading PDF to S3: {e}")
            return JSONResponse({"status": "failed", "message": "Failed to upload converted PDF to S3."}, status_code=500)
        finally:
            os.remove(temp_pdf_file_path)
    else:
        return JSONResponse({"status": "failed", "message": "PDF output file not found after conversion."}, status_code=500)


@app.get("/download/{file_id}")
async def download_pdf(file_id: str):
    if not S3_BUCKET_NAME:
        return JSONResponse({"status": "failed", "message": "S3 bucket name not configured."}, status_code=500)

    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    try:
        # S3 presigned URLs are full URLs and do not need the API Gateway stage prefix.
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': pdf_s3_key},
            ExpiresIn=300
        )
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
    # Get the root_path (e.g., /prod) from the request scope
    root_path = request.scope.get("root_path", "")
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "root_path": root_path} # Pass root_path to template
    )

@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    if create_user(username, email, password):
        # Prepend root_path to the redirect URL
        return RedirectResponse(f"{root_path}/login?message=registration_success", status_code=303)
    # Pass root_path to template on error
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": "Username or Email already exists"})

# --- Login (Handles both root "/" and "/login" for flexibility) ---
@app.get("/", response_class=HTMLResponse) # This will handle the root path (e.g., /prod)
@app.get("/login", response_class=HTMLResponse) # This will also handle /login explicitly (e.g., /prod/login)
async def login_form(request: Request):
    root_path = request.scope.get("root_path", "")
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    # Pass root_path to template
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "message": message, "error": error})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    if verify_user(username, password):
        # Prepend root_path to the redirect URL
        return RedirectResponse(f"{root_path}/dashboard?username={username}", status_code=303)
    # Pass root_path to template on error
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "error": "Invalid username or password"})

# --- Forgot Password ---
@app.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    root_path = request.scope.get("root_path", "")
    error = request.query_params.get("error")
    # Pass root_path to template
    return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": error})

@app.post("/reset_password_direct")
async def reset_password_direct(request: Request, username_or_email: str = Form(...), new_password: str = Form(...), confirm_new_password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    if new_password != confirm_new_password:
        # Pass root_path to template on error
        return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": "Passwords do not match."})

    user = get_user_by_email(username_or_email) or get_user_by_username(username_or_email)
    if user and update_user_password(user["email"], new_password):
        # Prepend root_path to the redirect URL
        return RedirectResponse(f"{root_path}/login?message=password_reset_success", status_code=303)
    else:
        # Pass root_path to template on error
        return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": "No account found or reset failed."})

# --- Dashboard ---
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Query("Guest")):
    root_path = request.scope.get("root_path", "")
    user = {"username": username}
    # Pass root_path to template
    return templates.TemplateResponse("dashboard.html", {"request": request, "root_path": root_path, "user": user})

# Lambda entry point
handler = Mangum(app)
