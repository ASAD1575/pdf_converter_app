from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from mangum import Mangum
import os
import logging # Import logging module

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- Login ---
@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    # This line is crucial for debugging
    root_path = request.scope.get("root_path", "")
    logger.info(f"DEBUG: root_path in login_form: '{root_path}'") 
    
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "message": message, "error": error})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # This line is crucial for debugging
    root_path = request.scope.get("root_path", "")
    logger.info(f"DEBUG: root_path in login POST: '{root_path}'") 

    if verify_user(username, password):
        # Ensure your verify_user function is imported or defined
        # For now, let's assume it always returns True for testing the redirect
        # In a real app: if database.verify_user(username, password):
        return RedirectResponse(f"{root_path}/dashboard?username={username}", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "root_path": root_path, "error": "Invalid username or password"})

# --- Placeholder for database functions (replace with your actual database.py imports) ---
# You'll need to ensure your database functions are available here.
# For example:
# from .database import verify_user, create_user, get_user_by_email, update_user_password, save_password_reset_token, verify_password_reset_token, invalidate_token
# For demonstration purposes, a dummy function:
def verify_user(username, password):
    # This is a dummy function. Replace with actual database verification.
    return True 

# --- Register ---
@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    root_path = request.scope.get("root_path", "")
    logger.info(f"DEBUG: root_path in register_form: '{root_path}'")
    error = request.query_params.get("error")
    return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": error})

@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    logger.info(f"DEBUG: root_path in register POST: '{root_path}'")

    if password != confirm_password:
        return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": "Passwords do not match."})
    
    # Placeholder for user creation logic (replace with your actual database.create_user)
    # For now, always return success for testing the redirect
    # In a real app: if database.create_user(username, email, password):
    if True: # Simulating successful user creation
        return RedirectResponse(f"{root_path}/login?message=Registration successful! Please log in.", status_code=303)
    else:
        return templates.TemplateResponse("register.html", {"request": request, "root_path": root_path, "error": "Username or email already exists."})

# --- Forgot Password ---
@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_form(request: Request):
    root_path = request.scope.get("root_path", "")
    logger.info(f"DEBUG: root_path in forgot_password_form: '{root_path}'")
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    return templates.TemplateResponse("forgot_password.html", {"request": request, "root_path": root_path, "message": message, "error": error})

@app.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_request(request: Request, email: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    logger.info(f"DEBUG: root_path in forgot_password_request POST: '{root_path}'")

    # In a real application, you would:
    # 1. Check if the email exists in your database.
    # 2. Generate a unique token.
    # 3. Save the token with an expiration time in your database.
    # 4. Send an email to the user with a link containing the token.
    
    # For demonstration:
    # if database.get_user_by_email(email):
    #     token = "dummy_reset_token" # Replace with actual token generation
    #     expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)
    #     database.save_password_reset_token(email, token, expires_at)
    #     reset_link = f"{request.url.scheme}://{request.url.netloc}{root_path}/reset-password?token={token}"
    #     print(f"Password reset link: {reset_link}") # In production, send via email service
    
    return templates.TemplateResponse("forgot_password.html", {
        "request": request,
        "root_path": root_path,
        "message": "If an account with that email exists, a password reset link has been sent."
    })

# --- Reset Password ---
@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_form(request: Request, token: str):
    root_path = request.scope.get("root_path", "")
    logger.info(f"DEBUG: root_path in reset_password_form: '{root_path}'")

    # In a real application, you would verify the token's validity and expiration
    # if database.verify_password_reset_token(token):
    #     return templates.TemplateResponse("reset_password.html", {"request": request, "root_path": root_path, "token": token})
    # else:
    #     return templates.TemplateResponse("message.html", {"request": request, "root_path": root_path, "message": "Invalid or expired password reset token."})
    
    # For demonstration:
    if token == "dummy_reset_token": # Simulate a valid token
        return templates.TemplateResponse("reset_password.html", {"request": request, "root_path": root_path, "token": token})
    else:
        return templates.TemplateResponse("message.html", {"request": request, "root_path": root_path, "message": "Invalid or expired password reset token."})


@app.post("/reset-password", response_class=HTMLResponse)
async def reset_password_submit(request: Request, token: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    root_path = request.scope.get("root_path", "")
    logger.info(f"DEBUG: root_path in reset_password_submit POST: '{root_path}'")

    if new_password != confirm_password:
        return templates.TemplateResponse("reset_password.html", {"request": request, "root_path": root_path, "token": token, "error": "Passwords do not match."})

    # In a real application, you would:
    # 1. Verify the token again.
    # 2. Get the user's email associated with the token.
    # 3. Update the user's password in the database.
    # 4. Invalidate the token.
    
    # For demonstration:
    # email = database.verify_password_reset_token(token)
    # if email:
    #     database.update_user_password(email, new_password)
    #     database.invalidate_token(token)
    #     return RedirectResponse(f"{root_path}/login?message=Password successfully reset. Please log in.", status_code=303)
    # else:
    #     return templates.TemplateResponse("message.html", {"request": request, "root_path": root_path, "message": "Invalid or expired password reset token."})

    if token == "dummy_reset_token": # Simulate successful reset
        return RedirectResponse(f"{root_path}/login?message=Password successfully reset. Please log in.", status_code=303)
    else:
        return templates.TemplateResponse("message.html", {"request": request, "root_path": root_path, "message": "Invalid or expired password reset token."})

# --- Dashboard (Example protected route) ---
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = "Guest"):
    root_path = request.scope.get("root_path", "")
    logger.info(f"DEBUG: root_path in dashboard: '{root_path}'")
    return templates.TemplateResponse("dashboard.html", {"request": request, "root_path": root_path, "username": username})

# Handler for AWS Lambda
handler = Mangum(app)
