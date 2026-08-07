// ==========================================================
// ADMIN INCIDENT PAGE
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {
    checkAdminAndLoadIncidents();
});


// ==========================================================
// GET TOKEN
// ==========================================================

function getToken() {

    return (
        localStorage.getItem("access_token") ||
        localStorage.getItem("token")
    );
}


// ==========================================================
// GET USER
// ==========================================================

function getLoggedInUser() {

    const userData = localStorage.getItem("user");

    if (!userData) {
        return null;
    }

    try {
        return JSON.parse(userData);
    } catch (error) {
        console.error("Invalid user data");
        return null;
    }
}


// ==========================================================
// CHECK LOGIN + ADMIN
// ==========================================================

async function checkAdminAndLoadIncidents() {

    const token = getToken();

    // ------------------------------------------------------
    // NOT LOGGED IN
    // ------------------------------------------------------

    if (!token) {

        window.location.href = "/login";

        return;
    }

    const user = getLoggedInUser();

    // ------------------------------------------------------
    // NO USER INFORMATION
    // ------------------------------------------------------

    if (!user) {

        localStorage.removeItem("access_token");
        localStorage.removeItem("token");

        window.location.href = "/login";

        return;
    }

    // ------------------------------------------------------
    // CHECK ROLE
    // ------------------------------------------------------

    const role = (
        user.role ||
        user.user_role ||
        ""
    ).toString().toLowerCase();

    if (role !== "admin") {

        document.getElementById(
            "incidentContainer"
        ).innerHTML = `
            <div class="error-message">
                <h2>Access Denied</h2>
                <p>
                    Incidents are available only
                    to Admin users.
                </p>
            </div>
        `;

        return;
    }

    // ------------------------------------------------------
    // ADMIN VERIFIED
    // ------------------------------------------------------

    await loadIncidents();
}


// ==========================================================
// LOAD INCIDENTS
// ==========================================================

async function loadIncidents() {

    const container =
        document.getElementById(
            "incidentContainer"
        );

    try {

        const token = getToken();

        const response = await fetch(
            "/api/incidents",
            {
                method: "GET",

                headers: {
                    "Authorization":
                        `Bearer ${token}`,

                    "Content-Type":
                        "application/json"
                }
            }
        );

        // --------------------------------------------------
        // UNAUTHORIZED
        // --------------------------------------------------

        if (response.status === 401) {

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "token"
            );

            localStorage.removeItem(
                "user"
            );

            window.location.href = "/login";

            return;
        }

        // --------------------------------------------------
        // NOT ADMIN
        // --------------------------------------------------

        if (response.status === 403) {

            container.innerHTML = `
                <div class="error-message">
                    <h2>Access Denied</h2>
                    <p>
                        Only Admin users can view incidents.
                    </p>
                </div>
            `;

            return;
        }

        // --------------------------------------------------
        // OTHER ERROR
        // --------------------------------------------------

        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const incidents =
            await response.json();

        displayIncidents(incidents);

    } catch (error) {

        console.error(
            "Incident loading error:",
            error
        );

        container.innerHTML = `
            <div class="error-message">
                <h2>Unable to load incidents</h2>
                <p>
                    ${error.message}
                </p>
            </div>
        `;
    }
}


// ==========================================================
// DISPLAY INCIDENTS
// ==========================================================

function displayIncidents(incidents) {

    const container =
        document.getElementById(
            "incidentContainer"
        );

    // ------------------------------------------------------
    // NO INCIDENTS
    // ------------------------------------------------------

    if (
        !incidents ||
        incidents.length === 0
    ) {

        container.innerHTML = `
            <div class="no-incidents">

                <h2>No Incidents Found</h2>

                <p>
                    There are currently no
                    traffic incidents recorded.
                </p>

            </div>
        `;

        return;
    }

    // ------------------------------------------------------
    // INCIDENT CARDS
    // ------------------------------------------------------

    container.innerHTML = `
        <div class="incident-grid">

            ${incidents.map(
                incident => `

                <div class="incident-card">

                    <h3>
                        ${escapeHTML(
                            incident.title ||
                            "Traffic Incident"
                        )}
                    </h3>

                    <span class="severity">
                        ${escapeHTML(
                            incident.severity ||
                            "Unknown"
                        )}
                    </span>

                    <span class="status">
                        ${escapeHTML(
                            incident.status ||
                            "Active"
                        )}
                    </span>

                    <p>
                        <strong>Location:</strong>
                        ${escapeHTML(
                            incident.location ||
                            "Unknown"
                        )}
                    </p>

                    <p>
                        <strong>Type:</strong>
                        ${escapeHTML(
                            incident.alert_type ||
                            "Traffic"
                        )}
                    </p>

                    <p>
                        ${escapeHTML(
                            incident.description ||
                            incident.message ||
                            "No description available."
                        )}
                    </p>

                    <p>
                        <strong>Time:</strong>
                        ${formatDate(
                            incident.created_at
                        )}
                    </p>

                </div>

            `
            ).join("")}

        </div>
    `;
}


// ==========================================================
// HTML SAFETY
// ==========================================================

function escapeHTML(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value == null
            ? ""
            : String(value);

    return div.innerHTML;
}


// ==========================================================
// DATE
// ==========================================================

function formatDate(dateValue) {

    if (!dateValue) {
        return "Unknown";
    }

    const date =
        new Date(dateValue);

    if (isNaN(date.getTime())) {
        return dateValue;
    }

    return date.toLocaleString();
}