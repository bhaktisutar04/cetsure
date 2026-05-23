"""
firebase_auth.py — Firebase Authentication Dependency for FastAPI (F3)

Validates incoming Firebase ID tokens passed via Authorization Bearer headers.
"""

import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.exceptions import FirebaseError
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Setup structured logger
logger = logging.getLogger("cetsure_firebase_auth")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Firebase Admin SDK Initialization
# ---------------------------------------------------------------------------
if not firebase_admin._apps:
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            cred_dict = json.loads(service_account_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK successfully initialized using FIREBASE_SERVICE_ACCOUNT_JSON.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin using environment variable: {e}")
            try:
                firebase_admin.initialize_app()
                logger.info("Fallback: Firebase Admin SDK initialized with default credentials.")
            except Exception as fe:
                logger.critical(f"Critical: Fallback initialization failed: {fe}")
    else:
        # Local development fallback
        try:
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized using default credentials (local environment).")
        except Exception as e:
            logger.warning(f"Firebase Admin SDK not initialized: default credentials missing ({e}). Token verification will fail unless env vars are provided.")

# ---------------------------------------------------------------------------
# Bearer Token Security Configuration
# ---------------------------------------------------------------------------
# Disable auto_error to manually customize the missing header 401 response
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    FastAPI dependency that extracts and validates the Firebase ID token
    from the Authorization: Bearer <token> header.
    
    Raises HTTP 401 with clean, user-friendly messages for missing/invalid tokens.
    """
    if not credentials:
        logger.warning("Authentication failed: Missing Authorization Bearer header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",  # Keep it simple and clean
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials
    try:
        # Lightweight check: verify the token using firebase_admin
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except ExpiredIdTokenError as e:
        logger.warning(f"Firebase token expired: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidIdTokenError as e:
        logger.warning(f"Firebase token invalid: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error verifying Firebase ID token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
