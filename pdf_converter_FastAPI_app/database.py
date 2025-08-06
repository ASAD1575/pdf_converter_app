# import os
# import psycopg2
# from psycopg2 import Error
# from passlib.hash import bcrypt
# import datetime

# # Database connection details from environment variables
# # These will be set by your Terraform Lambda module when deployed to AWS.
# # For local testing, ensure these are set in your .env file and loaded by main.py.
# DB_HOST = os.getenv("DB_HOST")
# DB_NAME = os.getenv("DB_NAME")
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_PORT = os.getenv("DB_PORT", "5432") # Default PostgreSQL port

# def get_db_connection():
#     """
#     Establishes and returns a new PostgreSQL database connection.
#     Handles potential connection errors.
#     """
#     conn = None
#     try:
#         conn = psycopg2.connect(
#             host=DB_HOST,
#             database=DB_NAME,
#             user=DB_USER,
#             password=DB_PASSWORD,
#             port=DB_PORT
#         )
#         return conn
#     except Error as e:
#         print(f"Error connecting to PostgreSQL database: {e}")
#         # In a production environment, you might want to log this error
#         # and potentially re-raise a custom exception or handle it gracefully.
#         return None

# def init_db():
#     """
#     Initializes the database by creating necessary tables if they don't exist.
#     Uses PostgreSQL-specific syntax for table creation.
#     This function should be called ONCE when the application starts up.
#     """
#     conn = get_db_connection()
#     if conn:
#         try:
#             cursor = conn.cursor()
#             # Create users table
#             # SERIAL PRIMARY KEY: Auto-incrementing integer primary key in PostgreSQL
#             cursor.execute("""
#             CREATE TABLE IF NOT EXISTS users (
#                 id SERIAL PRIMARY KEY,
#                 username VARCHAR(255) UNIQUE NOT NULL,
#                 email VARCHAR(255) UNIQUE NOT NULL,
#                 password TEXT NOT NULL
#             )
#             """)
#             # Create password_reset_tokens table
#             # TIMESTAMP WITH TIME ZONE: Recommended for storing timestamps in PostgreSQL
#             cursor.execute("""
#             CREATE TABLE IF NOT EXISTS password_reset_tokens (
#                 id SERIAL PRIMARY KEY,
#                 email VARCHAR(255) NOT NULL,
#                 token VARCHAR(255) UNIQUE NOT NULL,
#                 expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
#                 used BOOLEAN DEFAULT FALSE
#             )
#             """)
#             conn.commit()
#             print("Database tables initialized successfully.")
#         except Error as e:
#             print(f"Error initializing database tables: {e}")
#         finally:
#             conn.close()
#     else:
#         print("Could not establish database connection for initialization.")


# # Create a new user
# def create_user(username: str, email: str, password: str) -> bool:
#     """
#     Creates a new user in the database.
#     Returns True on success, False if username or email already exists.
#     """
#     conn = get_db_connection()
#     if conn:
#         try:
#             hashed_password = bcrypt.hash(password)
#             cursor = conn.cursor()
#             # RETURNING id: Returns the ID of the newly inserted row (PostgreSQL specific)
#             cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
#                            (username, email, hashed_password))
#             conn.commit()
#             new_user_id = cursor.fetchone()[0] # Fetch the returned ID
#             print(f"User '{username}' created with ID: {new_user_id}")
#             return True
#         except Error as e:
#             print(f"Error creating user '{username}': {e}")
#             conn.rollback() # Rollback in case of error
#             # Check for unique constraint violation (specific to psycopg2)
#             if e.pgcode == '23505': # PostgreSQL unique_violation error code
#                 print("Username or email already exists.")
#             return False
#         finally:
#             conn.close()
#     return False

# # Verify existing user credentials
# def verify_user(username: str, password: str) -> bool:
#     """
#     Verifies existing user credentials against the database.
#     Returns True if credentials are valid, False otherwise.
#     """
#     conn = get_db_connection()
#     if conn:
#         try:
#             cursor = conn.cursor()
#             cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
#             row = cursor.fetchone()
#             if row and bcrypt.verify(password, row[0]):
#                 return True
#             return False
#         except Error as e:
#             print(f"Error verifying user '{username}': {e}")
#             return False
#         finally:
#             if conn:
#                 conn.close()
#     return False

# def get_user_by_email(email: str):
#     """
#     Retrieves user data by email.
#     Returns a dictionary with user info if found, None otherwise.
#     """
#     conn = get_db_connection()
#     if conn:
#         try:
#             cursor = conn.cursor()
#             cursor.execute("SELECT id, username, email FROM users WHERE email = %s", (email,))
#             row = cursor.fetchone()
#             if row:
#                 return {"id": row[0], "username": row[1], "email": row[2]}
#             return None
#         except Error as e:
#             print(f"Error getting user by email '{email}': {e}")
#             return None
#         finally:
#             conn.close()
#     return None

# def get_user_by_username(username: str):
#     """
#     Retrieves user data by username.
#     Returns a dictionary with user info if found, None otherwise.
#     """
#     conn = get_db_connection()
#     if conn:
#         try:
#             cursor = conn.cursor()
#             cursor.execute("SELECT id, username, email FROM users WHERE username = %s", (username,))
#             row = cursor.fetchone()
#             if row:
#                 return {"id": row[0], "username": row[1], "email": row[2]}
#             return None
#         except Error as e:
#             print(f"Error getting user by username '{username}': {e}")
#             return None
#         finally:
#             conn.close()
#     return None

# def update_user_password(email: str, new_password: str) -> bool:
#     """
#     Updates a user's password in the database.
#     Returns True on success, False on failure (e.g., user not found).
#     """
#     conn = get_db_connection()
#     if conn:
#         try:
#             cursor = conn.cursor()
#             hashed_password = bcrypt.hash(new_password)
#             cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
#             conn.commit()
#             success = cursor.rowcount > 0
#             return success
#         except Error as e:
#             print(f"Error updating password for email '{email}': {e}")
#             conn.rollback()
#             return False
#         finally:
#             conn.close()
#     return False

# # --- Password Reset Token Management Functions (Adjusted for PostgreSQL) ---

# def save_password_reset_token(email: str, token: str, expires_at: datetime.datetime) -> bool:
#     """
#     Saves a password reset token to the database.
#     If a token already exists for the email, it will be updated (or replaced).
#     """
#     conn = get_db_connection()
#     if conn:
#         try:
#             cursor = conn.cursor()
#             # First, invalidate any existing tokens for this email
#             cursor.execute("UPDATE password_reset_tokens SET used = TRUE WHERE email = %s AND used = FALSE", (email,))

#             # Insert the new token
#             cursor.execute("INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (%s, %s, %s)",
#                            (email, token, expires_at))
#             conn.commit()
#             return True
#         except Error as e:
#             print(f"Error saving password reset token: {e}")
#             conn.rollback()
#             return False
#         finally:
#             conn.close()
#     return False

# def verify_password_reset_token(token: str) -> str | None:
#     """
#     Verifies a password reset token.
#     Returns the user's email if the token is valid and not expired, None otherwise.
#     Should also check if the token has already been used.
#     """
#     conn = get_db_connection()
#     if conn:
#         try:
#             cursor = conn.cursor()
#             cursor.execute("SELECT email, expires_at, used FROM password_reset_tokens WHERE token = %s", (token,))
#             row = cursor.fetchone()
#             if row:
#                 email, expires_at, used = row # expires_at is already a datetime object from psycopg2
#                 if not used and datetime.datetime.now(datetime.timezone.utc) < expires_at: # Compare timezone-aware datetimes
#                     return email
#             return None
#         except Error as e:
#             print(f"Error verifying password reset token: {e}")
#             return None
#         finally:
#             conn.close()
#     return False

# def invalidate_token(token: str) -> bool:
#     """
#     Invalidates a password reset token after it has been used.
#     """
#     conn = get_db_connection()
#     if conn:
#         try:
#             cursor = conn.cursor()
#             cursor.execute("UPDATE password_reset_tokens SET used = TRUE WHERE token = %s", (token,))
#             conn.commit()
#             success = cursor.rowcount > 0
#             return success
#         except Error as e:
#             print(f"Error invalidating token: {e}")
#             conn.rollback()
#             return False
#         finally:
#             conn.close()
#     return False

# # Initialize the database tables when the script starts (once on application startup)
# init_db()

import os
import psycopg2
from psycopg2 import Error
from passlib.hash import pbkdf2_sha256 # Using pbkdf2_sha256 for stronger hashing
import datetime
import logging
import re # For regular expressions, used in email and password validation

# Configure logging for the database module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Database connection details from environment variables
# These must be set in your Lambda configuration (Terraform)
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432") # Default PostgreSQL port

def get_db_connection():
    """
    Establishes and returns a new PostgreSQL database connection.
    Handles potential connection errors.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        logger.debug("Successfully connected to PostgreSQL database.")
        return conn
    except Error as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}", exc_info=True)
        return None

def init_db():
    """
    Initializes the database by creating necessary tables if they don't exist.
    This function should be called ONCE when the application starts up.
    In a Lambda context, it's often called during cold starts.
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Create users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """)
            # Create password_reset_tokens table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used BOOLEAN DEFAULT FALSE
            )
            """)
            conn.commit()
            logger.info("Database tables initialized successfully.")
        except Error as e:
            logger.error(f"Error initializing database tables: {e}", exc_info=True)
        finally:
            conn.close()
    else:
        logger.error("Could not establish database connection for initialization.")


# --- Validation Helper Functions ---

def _is_valid_email(email: str) -> bool:
    """Basic email format validation."""
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        logger.warning(f"Validation failed: Invalid email format: {email}")
        return False
    return True

def _is_strong_password(password: str) -> bool:
    """
    Checks if a password meets complexity requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (non-alphanumeric)
    """
    if len(password) < 8:
        logger.warning("Validation failed: Password too short (min 8 characters).")
        return False
    if not re.search(r"[A-Z]", password):
        logger.warning("Validation failed: Password must contain at least one uppercase letter.")
        return False
    if not re.search(r"[a-z]", password):
        logger.warning("Validation failed: Password must contain at least one lowercase letter.")
        return False
    if not re.search(r"\d", password):
        logger.warning("Validation failed: Password must contain at least one digit.")
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        logger.warning("Validation failed: Password must contain at least one special character.")
        return False
    return True

def _is_valid_username(username: str) -> bool:
    """Basic username validation: minimum length."""
    if len(username) < 3:
        logger.warning("Validation failed: Username too short (min 3 characters).")
        return False
    return True

# --- User Management Functions ---

def create_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """
    Creates a new user in the database after validating inputs.
    Returns (True, "Success message") on success,
    (False, "Error message") if validation fails or username/email already exists.
    """
    # Input validation
    if not _is_valid_username(username):
        return False, "Username must be at least 3 characters long."
    if not _is_valid_email(email):
        return False, "Invalid email format."
    if not _is_strong_password(password):
        return False, "Password must be at least 8 characters, include uppercase, lowercase, digit, and special character."

    conn = get_db_connection()
    if not conn:
        return False, "Database connection error."

    try:
        hashed_password = pbkdf2_sha256.hash(password) # Using pbkdf2_sha256
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
                       (username, email, hashed_password))
        conn.commit()
        new_user_id = cursor.fetchone()[0]
        logger.info(f"User '{username}' created with ID: {new_user_id}")
        return True, "Registration successful!"
    except Error as e:
        logger.error(f"Error creating user '{username}': {e}", exc_info=True)
        conn.rollback()
        if e.pgcode == '23505': # PostgreSQL unique_violation error code
            return False, "Username or Email already exists."
        return False, "Failed to create user due to a database error."
    finally:
        if conn:
            conn.close()

def verify_user(username: str, password: str) -> bool:
    """
    Verifies user credentials against the database.
    Returns True if credentials are valid, False otherwise.
    """
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection error during user verification.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row and pbkdf2_sha256.verify(password, row[0]): # Using pbkdf2_sha256
            logger.info(f"User '{username}' authenticated successfully.")
            return True
        logger.warning(f"Failed login attempt for user '{username}': invalid credentials.")
        return False
    except Error as e:
        logger.error(f"Error verifying user '{username}': {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()

def get_user_by_email(email: str) -> dict | None:
    """
    Retrieves user data by email.
    Returns a dictionary with user info if found, None otherwise.
    """
    if not email:
        logger.warning("Attempted to get user with empty email.")
        return None
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection error during get_user_by_email.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "email": row[2]}
        return None
    except Error as e:
        logger.error(f"Error getting user by email '{email}': {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

def get_user_by_username(username: str) -> dict | None:
    """
    Retrieves user data by username.
    Returns a dictionary with user info if found, None otherwise.
    """
    if not username:
        logger.warning("Attempted to get user with empty username.")
        return None
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection error during get_user_by_username.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "email": row[2]}
        return None
    except Error as e:
        logger.error(f"Error getting user by username '{username}': {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

def update_user_password(username_or_email: str, new_password: str) -> tuple[bool, str]:
    """
    Updates a user's password in the database after validation.
    Returns (True, "Success message") on success,
    (False, "Error message") on failure (e.g., user not found, weak password).
    """
    if not _is_strong_password(new_password):
        return False, "New password does not meet complexity requirements."

    user = get_user_by_email(username_or_email)
    if not user:
        user = get_user_by_username(username_or_email)

    if not user:
        return False, "No account found with that username or email."

    conn = get_db_connection()
    if not conn:
        return False, "Database connection error."

    try:
        cursor = conn.cursor()
        hashed_password = pbkdf2_sha256.hash(new_password) # Using pbkdf2_sha256
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, user["email"]))
        conn.commit()
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Password updated for user: {user['email']}")
            return True, "Password reset successfully!"
        else:
            logger.warning(f"Password update failed for email '{user['email']}'. User might not exist (though checked).")
            return False, "Failed to update password."
    except Error as e:
        logger.error(f"Error updating password for email '{user['email']}': {e}", exc_info=True)
        conn.rollback()
        return False, "Failed to update password due to a database error."
    finally:
        if conn:
            conn.close()

# --- Password Reset Token Management Functions (Adjusted for PostgreSQL) ---

def save_password_reset_token(email: str, token: str, expires_at: datetime.datetime) -> bool:
    """
    Saves a password reset token to the database.
    If a token already exists for the email, it will be updated (or replaced).
    """
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection error during save_password_reset_token.")
        return False
    try:
        cursor = conn.cursor()
        # Invalidate any existing tokens for this email
        cursor.execute("UPDATE password_reset_tokens SET used = TRUE WHERE email = %s AND used = FALSE", (email,))

        # Insert the new token
        cursor.execute("INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (%s, %s, %s)",
                       (email, token, expires_at))
        conn.commit()
        logger.info(f"Password reset token saved for email: {email}")
        return True
    except Error as e:
        logger.error(f"Error saving password reset token for '{email}': {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verify_password_reset_token(token: str) -> str | None:
    """
    Verifies a password reset token.
    Returns the user's email if the token is valid and not expired, None otherwise.
    """
    if not token:
        logger.warning("Attempted to verify empty token.")
        return None
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection error during verify_password_reset_token.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT email, expires_at, used FROM password_reset_tokens WHERE token = %s", (token,))
        row = cursor.fetchone()
        if row:
            email, expires_at, used = row
            # Compare timezone-aware datetimes
            if not used and datetime.datetime.now(datetime.timezone.utc) < expires_at:
                logger.info(f"Password reset token '{token}' is valid for email '{email}'.")
                return email
            logger.warning(f"Password reset token '{token}' is invalid (used or expired).")
            return None
        logger.warning(f"Password reset token '{token}' not found.")
        return None
    except Error as e:
        logger.error(f"Error verifying password reset token '{token}': {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

def invalidate_token(token: str) -> bool:
    """
    Invalidates a password reset token after it has been used.
    """
    if not token:
        logger.warning("Attempted to invalidate empty token.")
        return False
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection error during invalidate_token.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE password_reset_tokens SET used = TRUE WHERE token = %s", (token,))
        conn.commit()
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Password reset token '{token}' invalidated successfully.")
        else:
            logger.warning(f"Token '{token}' not found for invalidation.")
        return success
    except Error as e:
        logger.error(f"Error invalidating token '{token}': {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# Initialize the database tables when the script starts
# This will run once per cold start of the Lambda function.
# Ensure your Lambda's IAM role has permissions to create tables if they don't exist.
init_db()

