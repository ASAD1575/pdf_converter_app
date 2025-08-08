# # from fastapi import FastAPI, File, UploadFile, Request, Form, Query, status
# # from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
# # from fastapi.templating import Jinja2Templates
# # from mangum import Mangum
# # import os
# # import uuid
# # import tempfile
# # import subprocess
# # import boto3
# # import logging

# # from database import create_user, verify_user, get_user_by_email, get_user_by_username, update_user_password

# # # -------------------- Logging --------------------
# # logger = logging.getLogger(__name__)
# # logger.setLevel(logging.INFO)

# # # -------------------- FastAPI App --------------------
# # app = FastAPI(root_path="/prod")
# # templates = Jinja2Templates(directory="templates")

# # # -------------------- S3 Setup --------------------
# # S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
# # s3_client = boto3.client("s3")

# # # -------------------- LibreOffice Path --------------------
# # LIBREOFFICE_PATH = "/opt/instdir/program/soffice.bin"  # Correct path for most Lambda LibreOffice layers

# # # -------------------- Health Check for LibreOffice --------------------
# # try:
# #     version_check = subprocess.run([LIBREOFFICE_PATH, "--version"], capture_output=True, text=True)
# #     logger.info(f"LibreOffice version: {version_check.stdout or version_check.stderr}")
# # except FileNotFoundError:
# #     logger.error(f"LibreOffice binary not found at {LIBREOFFICE_PATH}. Check Lambda Layer.")
# # except Exception as e:
# #     logger.error(f"LibreOffice check failed: {e}")

# # # -------------------- PDF Conversion --------------------
# # @app.post("/convert")
# # async def convert_to_pdf(file: UploadFile = File(...)):
# #     if not S3_BUCKET_NAME:
# #         return JSONResponse({"status": "failed", "message": "S3 bucket not configured"}, status_code=500)

# #     if not file.filename.endswith(".docx"):
# #         return JSONResponse({"status": "failed", "message": "Only .docx files are supported"}, status_code=400)

# #     file_id = str(uuid.uuid4())
# #     input_docx = os.path.join(tempfile.gettempdir(), f"{file_id}.docx")
# #     output_pdf = os.path.join(tempfile.gettempdir(), f"{file_id}.pdf")

# #     docx_s3_key = f"uploads/{file_id}.docx"
# #     pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

# #     try:
# #         # Save uploaded DOCX
# #         with open(input_docx, "wb") as f:
# #             f.write(await file.read())

# #         # Upload original DOCX to S3
# #         s3_client.upload_file(input_docx, S3_BUCKET_NAME, docx_s3_key)

# #         # Convert to PDF
# #         result = subprocess.run(
# #             [
# #                 LIBREOFFICE_PATH,
# #                 "--headless",
# #                 "--nologo",
# #                 "--convert-to",
# #                 "pdf",
# #                 input_docx,
# #                 "--outdir",
# #                 tempfile.gettempdir()
# #             ],
# #             check=True,
# #             capture_output=True,
# #             text=True
# #         )
# #         logger.info(f"LibreOffice stdout: {result.stdout}")
# #         logger.info(f"LibreOffice stderr: {result.stderr}")

# #         if os.path.exists(output_pdf):
# #             s3_client.upload_file(output_pdf, S3_BUCKET_NAME, pdf_s3_key)
# #             return JSONResponse({"status": "completed", "file_id": file_id})
# #         else:
# #             return JSONResponse({"status": "failed", "message": "PDF not generated"}, status_code=500)

# #     except subprocess.CalledProcessError as e:
# #         logger.error(f"LibreOffice failed: {e.stderr}")
# #         return JSONResponse({"status": "failed", "message": e.stderr}, status_code=500)
# #     except Exception as e:
# #         logger.error(f"Unexpected error: {e}", exc_info=True)
# #         return JSONResponse({"status": "failed", "message": str(e)}, status_code=500)
# #     finally:
# #         if os.path.exists(input_docx):
# #             os.remove(input_docx)
# #         if os.path.exists(output_pdf):
# #             os.remove(output_pdf)

# # # -------------------- Download PDF --------------------
# # @app.get("/download/{file_id}")
# # async def download_pdf(file_id: str):
# #     pdf_s3_key = f"converted_pdfs/{file_id}.pdf"
# #     try:
# #         url = s3_client.generate_presigned_url(
# #             'get_object',
# #             Params={'Bucket': S3_BUCKET_NAME, 'Key': pdf_s3_key},
# #             ExpiresIn=300
# #         )
# #         return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)
# #     except Exception as e:
# #         logger.error(f"Download failed: {e}")
# #         return JSONResponse({"error": "File not found or link generation failed"}, status_code=404)

# # # -------------------- Authentication & Dashboard --------------------
# # @app.post("/register")
# # async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
# #     root_path = request.scope.get("root_path", "/prod")
# #     if create_user(username, email, password):
# #         return RedirectResponse(f"{root_path}/?message=registration_success", status_code=303)
# #     return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": "Username or Email already exists"})

# # @app.get("/", response_class=HTMLResponse)
# # async def login_form(request: Request):
# #     root_path = request.scope.get("root_path", "/prod")
# #     message = request.query_params.get("message")
# #     error = request.query_params.get("error")
# #     return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "message": message, "error": error})

# # @app.get("/register", response_class=HTMLResponse)
# # async def register_form(request: Request):
# #     root_path = request.scope.get("root_path", "/prod")
# #     error = request.query_params.get("error")
# #     return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": error})

# # @app.post("/", response_class=HTMLResponse)
# # async def login(request: Request, username: str = Form(...), password: str = Form(...)):
# #     root_path = request.scope.get("root_path", "/prod")
# #     if verify_user(username, password):
# #         return RedirectResponse(f"{root_path}/dashboard?username={username}", status_code=303)
# #     return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "error": "Invalid username or password"})

# # @app.get("/forgot_password", response_class=HTMLResponse)
# # async def forgot_password_page(request: Request):
# #     root_path = request.scope.get("root_path", "/prod")
# #     error = request.query_params.get("error")
# #     return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": error})

# # @app.post("/reset_password_direct")
# # async def reset_password_direct(request: Request, username_or_email: str = Form(...), new_password: str = Form(...), confirm_new_password: str = Form(...)):
# #     root_path = request.scope.get("root_path", "/prod")
# #     if new_password != confirm_new_password:
# #         return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": "Passwords do not match."})

# #     user = get_user_by_email(username_or_email) or get_user_by_username(username_or_email)
# #     if user and update_user_password(user["email"], new_password):
# #         return RedirectResponse(f"{root_path}/?message=password_reset_success", status_code=303)
# #     else:
# #         return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": "No account found or reset failed."})

# # @app.get("/dashboard", response_class=HTMLResponse)
# # async def dashboard(request: Request, username: str = Query("Guest")):
# #     root_path = request.scope.get("root_path", "/prod")
# #     user = {"username": username}
# #     return templates.TemplateResponse("dashboard.html", {"request": request, "root_path": root_path, "user": user})

# # # -------------------- Lambda Entry --------------------
# # handler = Mangum(app)


# import os
# import subprocess
# import uuid
# import logging
# import tempfile
# import boto3 # AWS SDK for Python
# from docx2pdf import convert # Using docx2pdf for cleaner LibreOffice interaction

# from fastapi import FastAPI, Request, Form, UploadFile, File, Query
# from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
# from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles
# from starlette import status # For HTTP status codes

# # Assuming these functions exist in your database.py and handle user/token operations
# # Ensure database.py is correctly packaged with your Lambda function
# from database import create_user, verify_user, get_user_by_email, get_user_by_username, update_user_password

# # Configure logging for the application
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# app = FastAPI(root_path="/prod") # Set root_path for API Gateway deployment
# templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # S3 bucket setup - Environment variable must be set in Lambda configuration
# S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
# s3_client = boto3.client("s3")

# # Define the path for LibreOffice executable within the Lambda Layer/Container
# # This path is common for pre-built LibreOffice Lambda layers (e.g., Serverless Chrome).
# # If you build your own container, it might be different (e.g., /usr/bin/libreoffice).
# # Verify this path based on your LibreOffice installation in the Dockerfile.
# LIBREOFFICE_PATH = '/opt/instdir/program/soffice.bin' # Or '/usr/bin/libreoffice' if installed via apt/dnf

# # --- PDF conversion endpoint ---
# @app.post("/convert")
# async def convert_to_pdf(file: UploadFile = File(...)):
#     """
#     Handles DOCX file upload, converts it to PDF using LibreOffice,
#     and uploads both original DOCX (for backup) and converted PDF to S3.
#     """
#     if not S3_BUCKET_NAME:
#         logger.error("S3_BUCKET_NAME environment variable not set.")
#         return JSONResponse(
#             {"status": "failed", "message": "Server configuration error: S3 bucket not set."},
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

#     # Validate file type
#     if not file.filename.lower().endswith(".docx"):
#         logger.warning(f"Received non-DOCX file for conversion: {file.filename}")
#         return JSONResponse(
#             {"status": "failed", "message": "Only .docx files are supported for conversion."},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )

#     file_id = str(uuid.uuid4())
#     original_filename = file.filename
    
#     # All temporary file operations MUST use /tmp in AWS Lambda
#     input_docx_temp_path = os.path.join(tempfile.gettempdir(), f"{file_id}.docx")
#     output_pdf_temp_path = os.path.join(tempfile.gettempdir(), f"{file_id}.pdf")

#     docx_s3_key = f"uploads/{file_id}.docx"
#     pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

#     # Store original PATH and HOME environment variables to restore them later
#     original_path_env = os.environ.get('PATH', '')
#     original_home_env = os.environ.get('HOME', '')

#     try:
#         # Set environment variables crucial for LibreOffice to be found and run
#         # Add the LibreOffice binary directory to PATH
#         os.environ['PATH'] = f"{os.path.dirname(LIBREOFFICE_PATH)}:{original_path_env}"
#         # LibreOffice needs a writable HOME directory for temporary files
#         os.environ['HOME'] = tempfile.gettempdir()

#         # 1. Save the uploaded DOCX file to Lambda's /tmp directory
#         logger.info(f"Saving uploaded DOCX from '{file.filename}' to '{input_docx_temp_path}'")
#         with open(input_docx_temp_path, "wb") as f:
#             f.write(await file.read())

#         # 2. Upload the original DOCX to S3 for backup/record
#         logger.info(f"Uploading original DOCX to s3://{S3_BUCKET_NAME}/{docx_s3_key}")
#         s3_client.upload_file(input_docx_temp_path, S3_BUCKET_NAME, docx_s3_key)

#         # 3. Perform the DOCX to PDF conversion using docx2pdf
#         # docx2pdf handles the subprocess call to LibreOffice internally
#         logger.info(f"Starting docx2pdf conversion for '{input_docx_temp_path}' to '{output_pdf_temp_path}'")
#         convert(input_docx_temp_path, output_pdf_temp_path)
#         logger.info(f"docx2pdf conversion completed successfully for '{input_docx_temp_path}'")

#         # 4. Check if PDF was created and upload to S3
#         if os.path.exists(output_pdf_temp_path):
#             logger.info(f"Uploading converted PDF to s3://{S3_BUCKET_NAME}/{pdf_s3_key}")
#             s3_client.upload_file(output_pdf_temp_path, S3_BUCKET_NAME, pdf_s3_key)
#             return JSONResponse({"status": "completed", "file_id": file_id})
#         else:
#             logger.error(f"PDF output file not found after docx2pdf conversion: '{output_pdf_temp_path}'")
#             return JSONResponse(
#                 {"status": "failed", "message": "PDF output file not found after conversion. Check Lambda logs for LibreOffice errors."},
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     except Exception as e:
#         logger.error(f"An error occurred during conversion for file '{file.filename}': {e}", exc_info=True)
#         # Provide more specific error messages for common issues
#         if "No such file or directory" in str(e) and ("soffice" in str(e) or "libreoffice" in str(e)):
#             return JSONResponse(
#                 {"status": "failed", "message": "Server error: PDF converter (LibreOffice) not found. Ensure LibreOffice is correctly installed in the Docker image and the LIBREOFFICE_PATH is accurate."},
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#         return JSONResponse(
#             {"status": "failed", "message": f"An unexpected server error occurred: {str(e)}"},
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
#     finally:
#         # Clean up temporary files from Lambda's /tmp directory
#         if os.path.exists(input_docx_temp_path):
#             os.remove(input_docx_temp_path)
#             logger.info(f"Cleaned up '{input_docx_temp_path}'")
#         if os.path.exists(output_pdf_temp_path):
#             os.remove(output_pdf_temp_path)
#             logger.info(f"Cleaned up '{output_pdf_temp_path}'")
        
#         # Restore original PATH and HOME environment variables
#         os.environ['PATH'] = original_path_env
#         os.environ['HOME'] = original_home_env


# @app.get("/download/{file_id}")
# async def download_pdf(file_id: str):
#     """
#     Generates a presigned S3 URL for a converted PDF file, allowing direct download.
#     This avoids proxying large files through Lambda, which is more efficient.
#     """
#     if not S3_BUCKET_NAME:
#         logger.error("S3_BUCKET_NAME environment variable not set for download.")
#         return JSONResponse(
#             {"status": "failed", "message": "Server configuration error: S3 bucket not set."},
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

#     pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

#     try:
#         # Generate a presigned URL for the S3 object.
#         presigned_url = s3_client.generate_presigned_url(
#             'get_object',
#             Params={'Bucket': S3_BUCKET_NAME, 'Key': pdf_s3_key},
#             ExpiresIn=300 # URL valid for 5 minutes
#         )
#         logger.info(f"Generated presigned URL for s3://{S3_BUCKET_NAME}/{pdf_s3_key}")
#         return RedirectResponse(presigned_url, status_code=status.HTTP_303_SEE_OTHER)
#     except s3_client.exceptions.ClientError as e:
#         if e.response['Error']['Code'] == 'NoSuchKey':
#             logger.warning(f"Download request for non-existent file: {pdf_s3_key}")
#             return JSONResponse(
#                 {"error": "File not found. It may have been deleted or never existed."},
#                 status_code=status.HTTP_404_NOT_FOUND
#             )
#         logger.error(f"Error generating presigned URL for '{pdf_s3_key}': {e}", exc_info=True)
#         return JSONResponse(
#             {"error": "Could not generate download link due to an S3 error."},
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
#     except Exception as e:
#         logger.error(f"An unexpected error occurred during download for '{file_id}': {e}", exc_info=True)
#         return JSONResponse(
#             {"error": "An unexpected server error occurred during download."},
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

# # --- Registration ---
# @app.get("/register", response_class=HTMLResponse)
# async def register_form(request: Request):
#     root_path = request.scope.get("root_path", "/prod")
#     return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path})

# @app.post("/register")
# async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
#     root_path = request.scope.get("root_path", "/prod")
#     # create_user now returns a tuple (bool, str) for success/error_message
#     success, message = create_user(username, email, password)
#     if success:
#         return RedirectResponse(f"{root_path}/login?message=registration_success", status_code=status.HTTP_303_SEE_OTHER)
#     return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": message})

# # --- Login ---
# @app.get("/login", response_class=HTMLResponse)
# async def login_form(request: Request):
#     root_path = request.scope.get("root_path", "/prod")
#     message = request.query_params.get("message")
#     error = request.query_params.get("error")
#     return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "message": message, "error": error})

# @app.post("/login", response_class=HTMLResponse)
# async def login(request: Request, username: str = Form(...), password: str = Form(...)):
#     root_path = request.scope.get("root_path", "/prod")
#     if verify_user(username, password):
#         return RedirectResponse(f"{root_path}/dashboard?username={username}", status_code=status.HTTP_303_SEE_OTHER)
#     return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "error": "Invalid username or password"})

# # --- Direct Password Reset ---
# @app.get("/forgot_password", response_class=HTMLResponse)
# async def forgot_password_page(request: Request):
#     root_path = request.scope.get("root_path", "/prod")
#     error = request.query_params.get("error")
#     return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": error})

# @app.post("/reset_password_direct")
# async def reset_password_direct(request: Request, username_or_email: str = Form(...), new_password: str = Form(...), confirm_new_password: str = Form(...)):
#     root_path = request.scope.get("root_path", "/prod")
#     if new_password != confirm_new_password:
#         return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": "Passwords do not match."})

#     # update_user_password now returns a tuple (bool, str)
#     success, message = update_user_password(username_or_email, new_password)
#     if success:
#         return RedirectResponse(f"{root_path}/login?message=password_reset_success", status_code=status.HTTP_303_SEE_OTHER)
#     else:
#         return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": message})

# # --- Root and dashboard ---
# @app.get("/", response_class=HTMLResponse)
# async def root(request: Request):
#     root_path = request.scope.get("root_path", "/prod")
#     return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path})

# @app.get("/dashboard", response_class=HTMLResponse)
# async def dashboard(request: Request, username: str = Query("Guest")):
#     root_path = request.scope.get("root_path", "/prod")
#     user = {"username": username}
#     return templates.TemplateResponse("dashboard.html", {"request": request, "root_path": root_path, "user": user})

import os
import subprocess
import uuid
import logging
import tempfile
import boto3  # AWS SDK for Python
from docx2pdf import convert  # Using docx2pdf for cleaner LibreOffice interaction

from fastapi import FastAPI, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette import status  # For HTTP status codes
from mangum import Mangum # ASGI adapter for AWS Lambda

# Assuming these functions exist in your database.py and handle user/token operations
# Ensure database.py is correctly packaged with your Lambda function
from database import create_user, verify_user, get_user_by_email, get_user_by_username, update_user_password

# -------------------- Logging --------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -------------------- FastAPI App --------------------
# Set root_path for API Gateway deployment
app = FastAPI(root_path="/prod")
templates = Jinja2Templates(directory="templates")
# Mount a static directory for CSS, JS, etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------- S3 Setup --------------------
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client("s3")

# -------------------- LibreOffice Path --------------------
# This path is correct for the Python 3.9 compatible layer provided previously.
LIBREOFFICE_PATH = '/opt/libreoffice/program/soffice' # /opt/lo/libreoffice/program/soffice

# -------------------- Health Check for LibreOffice --------------------
# This check is performed at cold start to ensure the path is valid.
# It can be a good way to debug if the layer isn't configured correctly.
try:
    # A subprocess is used to verify the path and get the version.
    version_check = subprocess.run([LIBREOFFICE_PATH, "--version"], capture_output=True, text=True)
    logger.info(f"LibreOffice version: {version_check.stdout.strip()}")
except FileNotFoundError:
    logger.error(f"LibreOffice binary not found at {LIBREOFFICE_PATH}. Check Lambda Layer and ARN.")
except Exception as e:
    logger.error(f"LibreOffice check failed: {e}")

# -------------------- PDF conversion endpoint --------------------
@app.post("/convert")
async def convert_to_pdf(file: UploadFile = File(...)):
    """
    Handles DOCX file upload, converts it to PDF using LibreOffice,
    and uploads both the original and converted files to S3.
    """
    if not S3_BUCKET_NAME:
        logger.error("S3_BUCKET_NAME environment variable not set.")
        return JSONResponse(
            {"status": "failed", "message": "Server configuration error: S3 bucket not set."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Validate file type
    if not file.filename.lower().endswith(".docx"):
        logger.warning(f"Received non-DOCX file for conversion: {file.filename}")
        return JSONResponse(
            {"status": "failed", "message": "Only .docx files are supported for conversion."},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    file_id = str(uuid.uuid4())
    
    # All temporary file operations MUST use /tmp in AWS Lambda
    input_docx_temp_path = os.path.join(tempfile.gettempdir(), f"{file_id}.docx")
    output_pdf_temp_path = os.path.join(tempfile.gettempdir(), f"{file_id}.pdf")

    docx_s3_key = f"uploads/{file_id}.docx"
    pdf_s3_key = f"converted_pdfs/{file_id}.pdf"

    # Store original PATH and HOME environment variables to restore them later
    original_path_env = os.environ.get('PATH', '')
    original_home_env = os.environ.get('HOME', '')

    try:
        # Set environment variables crucial for LibreOffice to be found and run
        # Add the LibreOffice binary directory to PATH
        os.environ['PATH'] = f"{os.path.dirname(LIBREOFFICE_PATH)}:{original_path_env}"
        # LibreOffice needs a writable HOME directory for temporary files
        os.environ['HOME'] = tempfile.gettempdir()

        # 1. Save the uploaded DOCX file to Lambda's /tmp directory
        logger.info(f"Saving uploaded DOCX from '{file.filename}' to '{input_docx_temp_path}'")
        with open(input_docx_temp_path, "wb") as f:
            f.write(await file.read())

        # 2. Upload the original DOCX to S3 for backup/record
        logger.info(f"Uploading original DOCX to s3://{S3_BUCKET_NAME}/{docx_s3_key}")
        s3_client.upload_file(input_docx_temp_path, S3_BUCKET_NAME, docx_s3_key)

        # 3. Perform the DOCX to PDF conversion using docx2pdf
        # docx2pdf handles the subprocess call to LibreOffice internally and
        # will use the updated PATH to find the `soffice` binary.
        logger.info(f"Starting docx2pdf conversion for '{input_docx_temp_path}' to '{output_pdf_temp_path}'")
        convert(input_docx_temp_path, output_pdf_temp_path)
        logger.info(f"docx2pdf conversion completed successfully for '{input_docx_temp_path}'")

        # 4. Check if PDF was created and upload to S3
        if os.path.exists(output_pdf_temp_path):
            logger.info(f"Uploading converted PDF to s3://{S3_BUCKET_NAME}/{pdf_s3_key}")
            s3_client.upload_file(output_pdf_temp_path, S3_BUCKET_NAME, pdf_s3_key)
            return JSONResponse({"status": "completed", "file_id": file_id})
        else:
            logger.error(f"PDF output file not found after docx2pdf conversion: '{output_pdf_temp_path}'")
            return JSONResponse(
                {"status": "failed", "message": "PDF output file not found after conversion. Check Lambda logs for LibreOffice errors."},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        logger.error(f"An error occurred during conversion for file '{file.filename}': {e}", exc_info=True)
        return JSONResponse(
            {"status": "failed", "message": f"An unexpected server error occurred: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # Clean up temporary files from Lambda's /tmp directory
        if os.path.exists(input_docx_temp_path):
            os.remove(input_docx_temp_path)
            logger.info(f"Cleaned up '{input_docx_temp_path}'")
        if os.path.exists(output_pdf_temp_path):
            os.remove(output_pdf_temp_path)
            logger.info(f"Cleaned up '{output_pdf_temp_path}'")
        
        # Restore original PATH and HOME environment variables
        os.environ['PATH'] = original_path_env
        os.environ['HOME'] = original_home_env

# -------------------- Download PDF --------------------
@app.get("/download/{file_id}")
async def download_pdf(file_id: str):
    """
    Generates a presigned S3 URL for a converted PDF file, allowing direct download.
    """
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
            ExpiresIn=300  # URL valid for 5 minutes
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
    root_path = request.scope.get("root_path", "/prod")
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path})

@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "/prod")
    success, message = create_user(username, email, password)
    if success:
        return RedirectResponse(f"{root_path}/login?message=registration_success", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": message})

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    root_path = request.scope.get("root_path", "/prod")
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "message": message, "error": error})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    root_path = request.scope.get("root_path", "/prod")
    if verify_user(username, password):
        return RedirectResponse(f"{root_path}/dashboard?username={username}", status_code=status.HTTP_303_SEE_OTHER)
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

    success, message = update_user_password(username_or_email, new_password)
    if success:
        return RedirectResponse(f"{root_path}/login?message=password_reset_success", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "error": message})

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    root_path = request.scope.get("root_path", "/prod")
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Query("Guest")):
    root_path = request.scope.get("root_path", "/prod")
    user = {"username": username}
    return templates.TemplateResponse("dashboard.html", {"request": request, "root_path": root_path, "user": user})

# -------------------- Lambda Entry Point --------------------
handler = Mangum(app)
