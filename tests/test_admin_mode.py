import json
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import app as activity_app


class AdminModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = activity_app.hash_teacher_password("correct-horse-battery")

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.original_teachers_file = activity_app.TEACHERS_FILE
        activity_app.TEACHERS_FILE = Path(self.temp_directory.name) / "teachers.json"
        activity_app.TEACHERS_FILE.write_text(
            json.dumps({"teachers": [{"username": "teacher", "password_hash": self.password_hash}]}),
            encoding="utf-8",
        )
        self.original_participants = list(activity_app.activities["Chess Club"]["participants"])
        activity_app.teacher_sessions.clear()
        self.client = TestClient(activity_app.app)

    def tearDown(self):
        self.client.close()
        activity_app.activities["Chess Club"]["participants"] = self.original_participants
        activity_app.teacher_sessions.clear()
        activity_app.TEACHERS_FILE = self.original_teachers_file
        self.temp_directory.cleanup()

    def test_students_can_view_activities_without_authentication(self):
        response = self.client.get("/activities")
        self.assertEqual(response.status_code, 200)
        self.assertIn("michael@mergington.edu", response.json()["Chess Club"]["participants"])

    def test_anonymous_users_cannot_change_rosters(self):
        signup = self.client.post(
            "/activities/Chess Club/signup",
            params={"email": "new-student@mergington.edu"},
        )
        unregister = self.client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"},
        )
        self.assertEqual(signup.status_code, 401)
        self.assertEqual(unregister.status_code, 401)

    def test_teacher_can_change_rosters_and_logout_revokes_session(self):
        login = self.client.post(
            "/auth/login",
            json={"username": "teacher", "password": "correct-horse-battery"},
        )
        self.assertEqual(login.status_code, 200)

        signup = self.client.post(
            "/activities/Chess Club/signup",
            params={"email": "new-student@mergington.edu"},
        )
        self.assertEqual(signup.status_code, 200)

        unregister = self.client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "new-student@mergington.edu"},
        )
        self.assertEqual(unregister.status_code, 200)

        logout = self.client.post("/auth/logout")
        self.assertEqual(logout.status_code, 200)
        denied = self.client.post(
            "/activities/Chess Club/signup",
            params={"email": "new-student@mergington.edu"},
        )
        self.assertEqual(denied.status_code, 401)

    def test_invalid_teacher_credentials_are_rejected(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "teacher", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()