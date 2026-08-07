// ==========================================================
// users.js
// AI Traffic Management System
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {
    checkAdminAccess();
    loadUsers();

    const form = document.getElementById("addUserForm");

    if (form) {
        form.addEventListener("submit", createUser);
    }
});


// ==========================================================
// GET JWT TOKEN
// ==========================================================

function getAuthToken() {
    return (
        localStorage.getItem("access_token") ||
        localStorage.getItem("token")
    );
}


// ==========================================================
// GET CURRENT USER
// ==========================================================

function getCurrentUser() {

    const userData = localStorage.getItem("user");

    if (!userData) {
        return null;
    }

    try {
        return JSON.parse(userData);
    } catch (error) {
        console.error("Invalid user data:", error);
        return null;
    }
}


// ==========================================================
// CHECK ADMIN
// ==========================================================

function checkAdminAccess() {

    const user = getCurrentUser();

    const usersCard = document.getElementById("usersCard");
    const accessDenied = document.getElementById("accessDenied");
    const addUserButton = document.getElementById("addUserButton");

    if (!user) {
        showAccessDenied();
        return;
    }

    const role = String(
        user.role ||
        user.user_role ||
        ""
    ).toLowerCase();

    if (role !== "admin") {

        if (usersCard) {
            usersCard.classList.add("d-none");
        }

        if (addUserButton) {
            addUserButton.classList.add("d-none");
        }

        if (accessDenied) {
            accessDenied.classList.remove("d-none");
        }

        return;
    }

    if (usersCard) {
        usersCard.classList.remove("d-none");
    }

    if (addUserButton) {
        addUserButton.classList.remove("d-none");
    }

    if (accessDenied) {
        accessDenied.classList.add("d-none");
    }
}


// ==========================================================
// ACCESS DENIED
// ==========================================================

function showAccessDenied() {

    const usersCard = document.getElementById("usersCard");
    const accessDenied = document.getElementById("accessDenied");

    if (usersCard) {
        usersCard.classList.add("d-none");
    }

    if (accessDenied) {
        accessDenied.classList.remove("d-none");
    }
}


// ==========================================================
// LOAD USERS
// ==========================================================

async function loadUsers() {

    const tableBody = document.getElementById("usersTableBody");

    if (!tableBody) {
        return;
    }

    const token = getAuthToken();

    if (!token) {

        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger">
                    Please login again. Authentication token not found.
                </td>
            </tr>
        `;

        return;
    }

    tableBody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center text-secondary">
                <i class="fas fa-spinner fa-spin me-2"></i>
                Loading users...
            </td>
        </tr>
    `;

    try {

        const response = await fetch("/users/", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Accept": "application/json"
            }
        });

        if (response.status === 401) {

            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger">
                        Authentication expired. Please login again.
                    </td>
                </tr>
            `;

            return;
        }

        if (response.status === 403) {

            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger">
                        Admin permission required.
                    </td>
                </tr>
            `;

            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        console.log("Users API response:", data);

        let users = data;

        // Support different backend response formats
        if (data.users) {
            users = data.users;
        }

        if (data.data) {
            users = data.data;
        }

        if (!Array.isArray(users)) {
            users = [];
        }

        displayUsers(users);

    } catch (error) {

        console.error("Error loading users:", error);

        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger">
                    Failed to load users.
                    <br>
                    <small>${error.message}</small>
                </td>
            </tr>
        `;
    }
}


// ==========================================================
// DISPLAY USERS
// ==========================================================

function displayUsers(users) {

    const tableBody = document.getElementById("usersTableBody");

    if (!tableBody) {
        return;
    }

    if (users.length === 0) {

        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-secondary">
                    No users found.
                </td>
            </tr>
        `;

        return;
    }

    tableBody.innerHTML = "";

    users.forEach(user => {

        const id = user.id ?? "-";
        const fullname = user.fullname ?? user.full_name ?? "-";
        const username = user.username ?? "-";
        const email = user.email ?? "-";
        const role = user.role ?? user.user_role ?? "Traffic Officer";

        const active =
            user.is_active ??
            user.active ??
            true;

        const statusBadge = active
            ? `<span class="badge bg-success">ACTIVE</span>`
            : `<span class="badge bg-danger">INACTIVE</span>`;

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${escapeHtml(id)}</td>

            <td>${escapeHtml(fullname)}</td>

            <td>
                <strong>${escapeHtml(username)}</strong>
            </td>

            <td>${escapeHtml(email)}</td>

            <td>
                ${getRoleBadge(role)}
            </td>

            <td>
                ${statusBadge}
            </td>

            <td>
                <button
                    class="btn btn-sm btn-outline-danger"
                    onclick="deleteUser(${id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;

        tableBody.appendChild(row);
    });
}


// ==========================================================
// ROLE BADGE
// ==========================================================

function getRoleBadge(role) {

    const normalized = String(role).toLowerCase();

    if (normalized === "admin") {
        return `<span class="badge bg-danger">ADMIN</span>`;
    }

    if (normalized === "supervisor") {
        return `<span class="badge bg-warning text-dark">SUPERVISOR</span>`;
    }

    return `<span class="badge bg-primary">TRAFFIC OFFICER</span>`;
}


// ==========================================================
// CREATE USER
// ==========================================================

async function createUser(event) {

    event.preventDefault();

    const token = getAuthToken();

    if (!token) {
        showAddUserError("Authentication token not found. Please login again.");
        return;
    }

    const submitButton =
        document.getElementById("addUserSubmitBtn");

    const fullname =
        document.getElementById("newFullname").value.trim();

    const username =
        document.getElementById("newUsername").value.trim();

    const email =
        document.getElementById("newEmail").value.trim();

    const phone =
        document.getElementById("newPhone").value.trim();

    const role =
        document.getElementById("newRole").value;

    const password =
        document.getElementById("newPassword").value;

    const payload = {
        fullname: fullname,
        username: username,
        email: email,
        phone: phone || null,
        role: role,
        password: password
    };

    console.log("Creating user:", payload);

    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <i class="fas fa-spinner fa-spin me-1"></i>
            Creating...
        `;
    }

    try {

        const response = await fetch("/users/", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        console.log("Create user response:", data);

        if (!response.ok) {

            let message = "Failed to create user.";

            if (data.detail) {

                if (Array.isArray(data.detail)) {
                    message = data.detail
                        .map(error => error.msg)
                        .join(", ");
                } else {
                    message = data.detail;
                }
            }

            throw new Error(message);
        }

        // Reset form
        document.getElementById("addUserForm").reset();

        // Close modal
        const modalElement =
            document.getElementById("addUserModal");

        if (modalElement && window.bootstrap) {

            const modal =
                bootstrap.Modal.getInstance(modalElement);

            if (modal) {
                modal.hide();
            }
        }

        // Reload table
        await loadUsers();

    } catch (error) {

        console.error("Create user error:", error);

        showAddUserError(error.message);

    } finally {

        if (submitButton) {

            submitButton.disabled = false;

            submitButton.innerHTML = `
                Create User
            `;
        }
    }
}


// ==========================================================
// DELETE USER
// ==========================================================

async function deleteUser(userId) {

    if (!confirm("Are you sure you want to delete this user?")) {
        return;
    }

    const token = getAuthToken();

    if (!token) {
        alert("Authentication token not found.");
        return;
    }

    try {

        const response = await fetch(`/users/${userId}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Accept": "application/json"
            }
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {

            throw new Error(
                data.detail ||
                `Failed to delete user (${response.status})`
            );
        }

        await loadUsers();

    } catch (error) {

        console.error("Delete user error:", error);

        alert(error.message);
    }
}


// ==========================================================
// ERROR MESSAGE
// ==========================================================

function showAddUserError(message) {

    const errorBox =
        document.getElementById("addUserError");

    if (!errorBox) {
        return;
    }

    errorBox.textContent = message;

    errorBox.classList.remove("d-none");
}


// ==========================================================
// HTML ESCAPE
// ==========================================================

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}