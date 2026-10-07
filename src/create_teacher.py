import getpass
import json
import os
import tempfile

from app import TEACHERS_FILE, hash_teacher_password


def main():
    username = input("Teacher username: ").strip()
    if not username:
        raise SystemExit("Username cannot be empty.")

    password = getpass.getpass("Teacher password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if not password:
        raise SystemExit("Password cannot be empty.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    if TEACHERS_FILE.exists():
        try:
            data = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SystemExit(f"Could not read {TEACHERS_FILE}: {error}") from error
    else:
        data = {"teachers": []}

    teachers = data.get("teachers") if isinstance(data, dict) else None
    if not isinstance(teachers, list):
        raise SystemExit("Teacher file must contain a 'teachers' list.")
    if any(isinstance(teacher, dict) and teacher.get("username") == username for teacher in teachers):
        raise SystemExit("That username already exists.")

    teachers.append({"username": username, "password_hash": hash_teacher_password(password)})
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=TEACHERS_FILE.parent, delete=False
    ) as temporary_file:
        json.dump(data, temporary_file, indent=2)
        temporary_file.write("\n")
        temporary_path = temporary_file.name
    os.replace(temporary_path, TEACHERS_FILE)
    print(f"Teacher account '{username}' added to {TEACHERS_FILE}.")


if __name__ == "__main__":
    main()