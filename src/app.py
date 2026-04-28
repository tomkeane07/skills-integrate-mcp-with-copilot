"""
High School Management System API

A simple FastAPI application for viewing extracurricular activities, with
role-based authentication for managing registrations.
"""

import hashlib
import json
import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

current_dir = Path(__file__).parent
users_file = current_dir / "users.json"
session_key = "authenticated_user"

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-only-session-secret"),
    same_site="lax",
)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(current_dir, "static")),
    name="static",
)


class LoginRequest(BaseModel):
    username: str
    password: str


def load_users():
    with users_file.open("r", encoding="utf-8") as file_handle:
        user_data = json.load(file_handle)

    return {user["username"]: user for user in user_data.get("users", [])}


def hash_password(password: str):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def serialize_user(user_record):
    return {
        "username": user_record["username"],
        "role": user_record["role"],
        "display_name": user_record["display_name"],
    }


def get_current_user(request: Request):
    session_user = request.session.get(session_key)
    if not session_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_record = load_users().get(session_user["username"])
    if not user_record:
        request.session.pop(session_key, None)
        raise HTTPException(status_code=401, detail="Session is no longer valid")

    return serialize_user(user_record)


def require_roles(*allowed_roles):
    def dependency(current_user=Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this action",
            )
        return current_user

    return dependency


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/auth/login")
def login(request: Request, credentials: LoginRequest):
    user_record = load_users().get(credentials.username)

    if not user_record or user_record["password_hash"] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user_payload = serialize_user(user_record)
    request.session[session_key] = user_payload
    return {
        "message": f"Signed in as {user_payload['display_name']}",
        "user": user_payload,
    }


@app.post("/auth/logout")
def logout(request: Request):
    request.session.pop(session_key, None)
    return {"message": "Signed out successfully"}


@app.get("/auth/session")
def get_session(request: Request):
    session_user = request.session.get(session_key)
    if not session_user:
        return {"authenticated": False, "user": None}

    user_record = load_users().get(session_user["username"])
    if not user_record:
        request.session.pop(session_key, None)
        return {"authenticated": False, "user": None}

    return {"authenticated": True, "user": serialize_user(user_record)}


@app.get("/auth/access-matrix")
def get_access_matrix():
    return {
        "public_routes": ["GET /", "GET /activities", "GET /auth/session"],
        "admin_and_club_manager_routes": [
            "POST /activities/{activity_name}/signup",
            "DELETE /activities/{activity_name}/unregister",
        ],
        "roles": ["admin", "club_manager", "student", "registered_user"],
    }


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    current_user=Depends(require_roles("admin", "club_manager")),
):
    """Register a student for an activity."""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]

    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is already full")

    activity["participants"].append(email)
    return {
        "message": f"Signed up {email} for {activity_name}",
        "managed_by": current_user["username"],
    }


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    current_user=Depends(require_roles("admin", "club_manager")),
):
    """Unregister a student from an activity."""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]

    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity",
        )

    activity["participants"].remove(email)
    return {
        "message": f"Unregistered {email} from {activity_name}",
        "managed_by": current_user["username"],
    }
