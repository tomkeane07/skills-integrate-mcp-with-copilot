# Mergington High School Activities API

A simple FastAPI application that allows visitors to browse extracurricular activities and uses role-based authentication for managing registrations.

## Features

- View all available extracurricular activities
- Role-based authentication for `admin`, `club_manager`, `student`, and `registered_user`
- Protected registration management for admins and club managers
- Sign up and unregister students from activities
- Check the current session and route access matrix

## Getting Started

1. Install the dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Get all activities with their details and current participant count |
| POST | `/auth/login` | Sign in and create a session |
| POST | `/auth/logout` | End the current session |
| GET | `/auth/session` | Get the current authenticated user |
| GET | `/auth/access-matrix` | View the role-based route access matrix |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student for an activity |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Remove a student from an activity |

## Bootstrap Users

The app ships with development-only bootstrap users in `users.json`:

| Username | Password | Role |
| -------- | -------- | ---- |
| `admin_user` | `admin123` | `admin` |
| `club_lead` | `club123` | `club_manager` |
| `student_demo` | `student123` | `student` |
| `guest_demo` | `guest123` | `registered_user` |

## Access Rules

- Public users can view activities and participants
- Signed-in `admin` and `club_manager` users can register and unregister students
- `student` and `registered_user` roles are authenticated but view-only in this iteration

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Users** - Bootstrap users are stored in `users.json`:

   - Username
   - SHA-256 password hash
   - Role
   - Display name

Activities are still stored in memory, which means activity data resets when the server restarts.
User bootstrap data is stored in `users.json` for local development.
