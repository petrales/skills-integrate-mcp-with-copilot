document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const signupContainer = document.getElementById("signup-container");
  const messageDiv = document.getElementById("message");
  const accountButton = document.getElementById("account-button");
  const accountPanel = document.getElementById("account-panel");
  const loginButton = document.getElementById("login-button");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  const teacherControls = document.getElementById("teacher-controls");
  const logoutButton = document.getElementById("logout-button");
  let isTeacher = false;

  function displayMessage(element, text, className) {
    element.textContent = text;
    element.className = className;
    element.classList.remove("hidden");
    setTimeout(() => element.classList.add("hidden"), 5000);
  }

  function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (character) => {
      const entities = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };
      return entities[character];
    });
  }

  function updateTeacherView(authenticated) {
    isTeacher = authenticated;
    signupContainer.classList.toggle("hidden", !isTeacher);
    loginButton.classList.toggle("hidden", isTeacher);
    teacherControls.classList.toggle("hidden", !isTeacher);
    fetchActivities();
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      if (!response.ok) {
        throw new Error("Activity request failed");
      }
      const activities = await response.json();
      activitiesList.innerHTML = "";
      activitySelect.replaceChildren(new Option("-- Select an activity --", ""));

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";
        const spotsLeft =
          details.max_participants - details.participants.length;
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${escapeHTML(email)}</span>${
                        isTeacher
                          ? `<button class="delete-btn" data-activity="${escapeHTML(name)}" data-email="${escapeHTML(email)}" aria-label="Unregister ${escapeHTML(email)}">Remove</button>`
                          : ""
                      }</li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;
        activitiesList.appendChild(activityCard);
        activitySelect.add(new Option(name, name));
      });

      activitiesList.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function handleUnregister(event) {
    const button = event.currentTarget;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      const result = await response.json();
      if (!response.ok) {
        if (response.status === 401) {
          updateTeacherView(false);
        }
        throw new Error(result.detail || "Could not unregister student");
      }
      displayMessage(messageDiv, result.message, "success");
      fetchActivities();
    } catch (error) {
      displayMessage(
        messageDiv,
        error.message || "Failed to unregister. Please try again.",
        "error"
      );
      console.error("Error unregistering:", error);
    }
  }

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const activity = activitySelect.value;
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        { method: "POST" }
      );
      const result = await response.json();
      if (!response.ok) {
        if (response.status === 401) {
          updateTeacherView(false);
        }
        throw new Error(result.detail || "Could not register student");
      }
      displayMessage(messageDiv, result.message, "success");
      signupForm.reset();
      fetchActivities();
    } catch (error) {
      displayMessage(
        messageDiv,
        error.message || "Failed to sign up. Please try again.",
        "error"
      );
      console.error("Error signing up:", error);
    }
  });

  accountButton.addEventListener("click", () => {
    const isExpanded = accountButton.getAttribute("aria-expanded") === "true";
    accountButton.setAttribute("aria-expanded", String(!isExpanded));
    accountPanel.classList.toggle("hidden", isExpanded);
  });

  loginButton.addEventListener("click", () => {
    accountPanel.classList.add("hidden");
    accountButton.setAttribute("aria-expanded", "false");
    loginMessage.className = "hidden";
    loginForm.reset();
    loginDialog.showModal();
  });

  document.getElementById("close-login-button").addEventListener("click", () => {
    loginDialog.close();
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const credentials = Object.fromEntries(new FormData(loginForm));
    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Login failed");
      }
      loginDialog.close();
      updateTeacherView(true);
      displayMessage(messageDiv, result.message, "success");
    } catch (error) {
      displayMessage(
        loginMessage,
        error.message || "Login failed. Please try again.",
        "error"
      );
      console.error("Error logging in:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Logout failed");
      }
      updateTeacherView(false);
      accountPanel.classList.add("hidden");
      accountButton.setAttribute("aria-expanded", "false");
      displayMessage(messageDiv, result.message, "success");
    } catch (error) {
      displayMessage(
        messageDiv,
        error.message || "Failed to log out. Please try again.",
        "error"
      );
      console.error("Error logging out:", error);
    }
  });

  async function checkTeacherSession() {
    try {
      const response = await fetch("/auth/session");
      const result = await response.json();
      if (response.status === 503) {
        displayMessage(
          messageDiv,
          "Teacher login is not configured. Contact the site administrator.",
          "error"
        );
        console.error("Teacher authentication is not configured:", result.detail);
        fetchActivities();
        return;
      }
      if (!response.ok) {
        throw new Error(result.detail || "Could not check login status");
      }
      updateTeacherView(result.authenticated);
    } catch (error) {
      displayMessage(
        messageDiv,
        "Could not check teacher login status. Please refresh the page.",
        "error"
      );
      console.error("Error checking teacher session:", error);
      fetchActivities();
    }
  }

  fetchActivities();
  checkTeacherSession();
});
