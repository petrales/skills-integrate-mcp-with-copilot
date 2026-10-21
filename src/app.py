"""
High School Management System API

A super simple FastAPI application that lets students view and teachers manage
extracurricular activities at Mergington High School.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing extracurricular activities and managing signups",
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

SESSION_COOKIE = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60


class LoginCredentials(BaseModel):
    username: str
    password: str


def _teacher_configuration() -> tuple[dict[str, str], str]:
    configured_credentials = os.getenv("TEACHER_CREDENTIALS")
    session_secret = os.getenv("TEACHER_SESSION_SECRET")
    if not configured_credentials or not session_secret or len(session_secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication is not configured",
        )
    try:
        credentials = json.loads(configured_credentials)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication configuration is invalid",
        ) from None
    if (
        not isinstance(credentials, dict)
        or not credentials
        or any(
            not isinstance(username, str)
            or not username
            or not isinstance(password, str)
            or not password
            for username, password in credentials.items()
        )
    ):
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication configuration is invalid",
        )
    return credentials, session_secret


def _create_session_token(username: str, session_secret: str) -> str:
    payload = json.dumps(
        {"username": username, "expires_at": int(time.time()) + SESSION_DURATION_SECONDS},
        separators=(",", ":"),
    ).encode()
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode()
    signature = hmac.new(
        session_secret.encode(), encoded_payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def _session_username(token: str | None, session_secret: str) -> str | None:
    if not token:
        return None
    try:
        encoded_payload, supplied_signature = token.split(".", 1)
        expected_signature = hmac.new(
            session_secret.encode(), encoded_payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return None
        payload_bytes = base64.urlsafe_b64decode(
            encoded_payload + "=" * (-len(encoded_payload) % 4)
        )
        payload = json.loads(payload_bytes)
        if not isinstance(payload, dict):
            return None
        username = payload.get("username")
        expires_at = payload.get("expires_at")
        if (
            not isinstance(username, str)
            or not isinstance(expires_at, int)
            or expires_at <= time.time()
        ):
            return None
        return username
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def require_teacher(request: Request) -> str:
    configured_credentials, session_secret = _teacher_configuration()
    username = _session_username(
        request.cookies.get(SESSION_COOKIE), session_secret
    )
    if not username or username not in configured_credentials:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(credentials: LoginCredentials, request: Request, response: Response):
    """Authenticate a teacher and start an eight-hour browser session."""
    teacher_credentials, session_secret = _teacher_configuration()
    expected_password = teacher_credentials.get(
        credentials.username, "invalid-teacher-login"
    )
    username_matches = credentials.username in teacher_credentials
    password_matches = hmac.compare_digest(credentials.password, expected_password)
    if not username_matches or not password_matches:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=SESSION_COOKIE,
        value=_create_session_token(credentials.username, session_secret),
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        max_age=SESSION_DURATION_SECONDS,
        path="/",
    )
    return {"message": "Teacher login successful"}


@app.get("/auth/session")
def get_session(request: Request):
    """Report whether this browser has an active teacher session."""
    teacher_credentials, session_secret = _teacher_configuration()
    session_username = _session_username(
        request.cookies.get(SESSION_COOKIE), session_secret
    )
    return {
        "authenticated": bool(
            session_username and session_username in teacher_credentials
        )
    }


@app.post("/auth/logout")
def logout(response: Response):
    """End the teacher session in this browser."""
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        samesite="strict",
        path="/",
    )
    return {"message": "Teacher logout successful"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str, email: str, _: str = Depends(require_teacher)
):
    """Register a student for an activity; teachers only."""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str, email: str, _: str = Depends(require_teacher)
):
    """Unregister a student from an activity; teachers only."""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
