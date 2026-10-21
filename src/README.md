# Mergington High School Activities API

A super simple FastAPI application that lets students view extracurricular activities and authenticated teachers manage registrations.

## Features

- View all available extracurricular activities
- View activity participants without logging in
- Register and unregister students as an authenticated teacher

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Configure the teacher accounts and a private session-signing secret in the environment. `TEACHER_CREDENTIALS` is a JSON object mapping each teacher username to a strong password. Do not commit these values or store passwords in a checked-in file:

   ```
   export TEACHER_CREDENTIALS='{"teacher":"choose-a-strong-password","another-teacher":"another-strong-password"}'
   export TEACHER_SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

   Keep the session secret stable across application restarts and use a secret manager in deployed environments. The API will report that teacher authentication is not configured until both variables are set.

3. Run the application from this directory:

   ```
   uvicorn app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

Use HTTPS when deploying the application; teacher session cookies are marked secure when served over HTTPS.

## API Endpoints

| Method | Endpoint                                                               | Description                                      |
| ------ | ---------------------------------------------------------------------- | ------------------------------------------------ |
| GET    | `/activities`                                                          | Get activities and participants (public)        |
| POST   | `/auth/login`                                                          | Log in with a configured teacher account         |
| GET    | `/auth/session`                                                        | Check for an active teacher session              |
| POST   | `/auth/logout`                                                         | Log out of the current browser session           |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`      | Register a student (teacher session required)    |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher session required)  |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.

Teacher sessions use signed, HTTP-only, same-site cookies and expire after eight hours. Activity viewing remains public, but the API enforces teacher authentication for both registration and removal; hiding controls in the browser is not the security boundary.
