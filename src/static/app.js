document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authStatus = document.getElementById("auth-status");
  const authMessage = document.getElementById("auth-message");
  const loginForm = document.getElementById("login-form");
  const logoutButton = document.getElementById("logout-button");
  const signupNote = document.getElementById("signup-note");
  const emailInput = document.getElementById("email");

  let currentUser = null;

  function canManageRegistrations() {
    return currentUser && ["admin", "club_manager"].includes(currentUser.role);
  }

  function showFlash(target, text, type) {
    target.textContent = text;
    target.className = type;
    target.classList.remove("hidden");

    setTimeout(() => {
      target.classList.add("hidden");
    }, 5000);
  }

  function updateAuthUI() {
    if (currentUser) {
      authStatus.textContent = `Signed in as ${currentUser.display_name} (${currentUser.role})`;
      loginForm.classList.add("hidden");
      logoutButton.classList.remove("hidden");
    } else {
      authStatus.textContent = "Not signed in";
      loginForm.classList.remove("hidden");
      logoutButton.classList.add("hidden");
    }

    const canManage = canManageRegistrations();
    signupNote.textContent = canManage
      ? "You can register and unregister students for activities."
      : "Sign in as an admin or club manager to manage registrations.";

    emailInput.disabled = !canManage;
    activitySelect.disabled = !canManage;
    signupForm.querySelector("button[type='submit']").disabled = !canManage;
  }

  async function fetchSession() {
    try {
      const response = await fetch("/auth/session");
      const result = await response.json();
      currentUser = result.authenticated ? result.user : null;
    } catch (error) {
      currentUser = null;
      console.error("Error fetching session:", error);
    }

    updateAuthUI();
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span>${
                        canManageRegistrations()
                          ? `<button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button>`
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

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showFlash(messageDiv, result.message, "success");
        fetchActivities();
      } else {
        showFlash(messageDiv, result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showFlash(messageDiv, "Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const credentials = {
      username: document.getElementById("username").value,
      password: document.getElementById("password").value,
    };

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
      });

      const result = await response.json();
      if (!response.ok) {
        showFlash(authMessage, result.detail || "Failed to sign in", "error");
        return;
      }

      currentUser = result.user;
      loginForm.reset();
      updateAuthUI();
      await fetchActivities();
      showFlash(authMessage, result.message, "success");
    } catch (error) {
      showFlash(authMessage, "Failed to sign in. Please try again.", "error");
      console.error("Error signing in:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      const result = await response.json();

      currentUser = null;
      updateAuthUI();
      await fetchActivities();
      showFlash(authMessage, result.message, "info");
    } catch (error) {
      showFlash(authMessage, "Failed to sign out. Please try again.", "error");
      console.error("Error signing out:", error);
    }
  });

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!canManageRegistrations()) {
      showFlash(messageDiv, "You must sign in as an admin or club manager.", "error");
      return;
    }

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        signupForm.reset();
        showFlash(messageDiv, result.message, "success");
        fetchActivities();
      } else {
        showFlash(messageDiv, result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showFlash(messageDiv, "Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  fetchSession().then(fetchActivities);
});
