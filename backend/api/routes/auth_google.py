import os
import json
import base64
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
from fastapi import APIRouter, Request, HTTPException
from google_auth_oauthlib.flow import Flow
from db.singleton import get_db

router = APIRouter()

SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_flow(state=None):
    client_config = {
        "web": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [os.environ.get("GOOGLE_REDIRECT_URI")],
        }
    }
    
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=os.environ.get("GOOGLE_REDIRECT_URI"),
        state=state
    )

@router.get("/auth/google/login")
async def login(user_id: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
        
    flow = create_flow()
    
    # Manually generate verifier to sync with state
    import secrets
    code_verifier = secrets.token_urlsafe(64)
    flow.code_verifier = code_verifier
    
    # Pack the verifier into state
    packed_state = base64.urlsafe_b64encode(f"{user_id}:{code_verifier}".encode()).decode()
    
    # Generate URL (it will use the verifier we just set)
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=packed_state
    )
    
    return {"auth_url": auth_url}

@router.get("/auth/google/callback")
async def callback(request: Request, code: str, state: str):
    try:
        # Unpack the state to get user_id and verifier
        decoded_state = base64.urlsafe_b64decode(state.encode()).decode()
        user_id, code_verifier = decoded_state.split(":", 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed state parameter")
        
    flow = create_flow(state=state)
    flow.code_verifier = code_verifier
    
    current_url = str(request.url).replace("127.0.0.1", "localhost")
    
    try:
        flow.fetch_token(authorization_response=current_url, code_verifier=code_verifier)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google Authentication Failed: {str(e)}")
        
    credentials = flow.credentials
    creds_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    try:
        db = get_db()
        # Save the auth info into the user's document
        await db.db.collection('users').document(user_id).set({'google_calendar_creds': creds_data}, merge=True)
    except Exception as db_err:
        print(f"DATABASE SAVE ERROR: {str(db_err)}")
        raise HTTPException(status_code=500, detail=f"Database Sync Failed: {str(db_err)}")
    
    return {"message": "Google Calendar connected successfully! You can close this window.", "user_id": user_id}
