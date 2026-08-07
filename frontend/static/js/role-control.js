// ==========================================================
// static/js/role-control.js
// Handles role-based visibility, session validation, and sidebar identity across pages
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {
    applyRoleControls();
});

function applyRoleControls() {
    // 1. Validate session token existence
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");

    if (!token) {
        window.location.href = "/login";
        return;
    }

    // 2. Retrieve user profile data from storage
    const userRaw = localStorage.getItem("user");

    if (!userRaw) {
        // Token exists but no cached user — fall back to fetching directly from server
        fetchUserFromServer(token);
        return;
    }

    try {
        const user = JSON.parse(userRaw);
        applyRolePermissions(user.role);
        updateSidebarIdentity(user);
    } catch (e) {
        console.error("Could not parse cached user, refetching from server:", e);
        fetchUserFromServer(token);
    }
}

async function fetchUserFromServer(token) {
    try {
        const response = await fetch("/auth/me", {
            headers: { "Authorization": "Bearer " + token }
        });

        if (!response.ok) throw new Error("Authentication failed");

        const user = await response.json();
        localStorage.setItem("user", JSON.stringify(user));

        applyRolePermissions(user.role);
        updateSidebarIdentity(user);

    } catch (error) {
        console.error("Role loading error:", error);

        localStorage.removeItem("access_token");
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        localStorage.removeItem("role");
        localStorage.removeItem("user_role");

        window.location.href = "/login";
    }
}

function applyRolePermissions(role) {
    // Fallback to standalone role keys if user object role is missing
    const rawRole = role || localStorage.getItem("role") || localStorage.getItem("user_role") || "Traffic Officer";
    
    // Normalize role string using toLowerCase()
    const normalizedRole = String(rawRole).trim().toLowerCase();

    console.log("Applying role control permissions for role:", normalizedRole);

    const adminItems = document.querySelectorAll(".admin-only");
    const supervisorItems = document.querySelectorAll(".supervisor-only");

    // Hide all initially
    adminItems.forEach(item => { item.style.display = "none"; });
    supervisorItems.forEach(item => { item.style.display = "none"; });

    const isAdmin = normalizedRole === "admin" || normalizedRole === "administrator";
    const isSupervisor = normalizedRole === "traffic supervisor" || normalizedRole === "supervisor";

    // Admin should have access to: .admin-only and .supervisor-only
    if (isAdmin) {
        adminItems.forEach(item => { item.style.display = ""; });
        supervisorItems.forEach(item => { item.style.display = ""; });
    } 
    // Traffic Supervisor should have access only to: .supervisor-only
    else if (isSupervisor) {
        supervisorItems.forEach(item => { item.style.display = ""; });
    }
    // Traffic Officer (and default fallback) sees neither.
}

function updateSidebarIdentity(user) {
    const nameEl = document.getElementById("sidebarUsername");
    const roleEl = document.getElementById("sidebarRole");

    if (nameEl) {
        nameEl.textContent = user.fullname || user.username || "User";
    }

    if (roleEl) {
        roleEl.textContent = user.role || "Unknown";

        const role = String(user.role || "").toLowerCase();
        roleEl.className = "badge role-badge " + (
            role === "admin" || role === "administrator" ? "bg-danger" :
            role === "supervisor" || role === "traffic supervisor" ? "bg-warning text-dark" :
            "bg-secondary"
        );
    }
}

// Re-run application if DOM changes dynamically
window.applyRoleControls = applyRoleControls;