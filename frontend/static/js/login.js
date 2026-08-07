// ==========================================================
// AI TRAFFIC MANAGEMENT & CONGESTION DETECTION SYSTEM
// Login & Authentication Controller (login.js)
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm") || document.querySelector("form");
    const usernameInput = document.getElementById("username") || document.querySelector("input[name='username']");
    const passwordInput = document.getElementById("password") || document.querySelector("input[name='password']");
    const errorMessageDiv = document.getElementById("error-message") || createErrorContainer();

    // ----------------------------------------------------------
    // SAFETY CHECK: Clear any lingering invalid/expired tokens on login page load
    // ----------------------------------------------------------
    // This prevents stale tokens from being accidentally attached to subsequent requests.
    if (window.location.pathname === "/" || window.location.pathname.includes("login")) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user_role");
        localStorage.removeItem("username");
    }

    if (!loginForm) {
        console.warn("Login form element not found in the DOM.");
        return;
    }

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError();

        const username = usernameInput ? usernameInput.value.trim() : "";
        const password = passwordInput ? passwordInput.value.trim() : "";

        if (!username || !password) {
            showError("Please enter both username and password.");
            return;
        }

        // FastAPI OAuth2PasswordRequestForm expects x-www-form-urlencoded data
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        try {
            // NOTE: No Authorization header is attached here because the user is logging in.
            const response = await fetch("/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: formData.toString()
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Invalid username or password.");
            }

            // Successful authentication: Securely store token and metadata
            if (data.access_token) {
                localStorage.setItem("access_token", data.access_token);
                if (data.user) {
                    localStorage.setItem("user_role", data.user.role || "Traffic Officer");
                    localStorage.setItem("username", data.user.username || username);
                }

                // Redirect cleanly to the protected dashboard
                window.location.href = "/dashboard";
            } else {
                throw new Error("Authentication token missing from server response.");
            }

        } catch (error) {
            console.error("Login error:", error);
            showError(error.message || "An error occurred during login. Please try again.");
        }
    });

    // Helper Functions for UI Feedback
    function createErrorContainer() {
        let errDiv = document.createElement("div");
        errDiv.id = "error-message";
        errDiv.style.color = "#dc3545";
        errDiv.style.backgroundColor = "#f8d7da";
        errDiv.style.border = "1px solid #f5c6cb";
        errDiv.style.padding = "10px";
        errDiv.style.borderRadius = "4px";
        errDiv.style.marginBottom = "15px";
        errDiv.style.display = "none";
        
        if (loginForm) {
            loginForm.prepend(errDiv);
        }
        return errDiv;
    }

    function showError(message) {
        if (errorMessageDiv) {
            errorMessageDiv.textContent = message;
            errorMessageDiv.style.display = "block";
        } else {
            alert(message);
        }
    }

    function hideError() {
        if (errorMessageDiv) {
            errorMessageDiv.textContent = "";
            errorMessageDiv.style.display = "none";
        }
    }
});