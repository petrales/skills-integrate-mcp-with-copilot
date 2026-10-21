# Admin Mode

## Problem

Students are removing each other to free up space for themselves in the activities.

## Recommended Solution

Add a user icon in the top right. When clicked it shows a login button. When the login button is clicked, it presents a window to enter a username and password. Teachers can log out when they are done.

- Only the teachers (logged in) have the ability to register and unregister students to activities.

- The students (not logged in) can still view who is registered.

- There is no need for an account maintenance page. Teachers will be assigned passwords.

## Security requirement

Teacher credentials must not be stored in a checked-in file. Configure the teacher username, password, and a private session-signing secret through environment variables or a deployment secret manager. Enforce teacher authentication in the API, not only by hiding controls in the UI.
