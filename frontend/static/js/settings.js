// ==========================================================
// settings.js
// AI Traffic Management System
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {

    loadSettings();

    loadSystemInfo();

});


// ==========================================================
// TOKEN
// ==========================================================

function getSettingsToken() {

    return (
        localStorage.getItem("access_token") ||
        localStorage.getItem("token")
    );

}


// ==========================================================
// LOAD SETTINGS
// ==========================================================

async function loadSettings() {

    const token = getSettingsToken();

    if (!token) {
        console.error("Authentication token not found.");
        return;
    }

    try {

        const response = await fetch("/settings/", {

            method: "GET",

            headers: {
                "Authorization": `Bearer ${token}`,
                "Accept": "application/json"
            }

        });


        if (!response.ok) {

            console.error(
                "Settings request failed:",
                response.status
            );

            return;
        }


        const data = await response.json();

        console.log("Settings:", data);


        // Appearance

        if (data.theme !== undefined) {

            document.getElementById("themeSelect").value =
                data.theme;

        }


        if (data.language !== undefined) {

            document.getElementById("languageInput").value =
                data.language;

        }


        // Notifications

        if (data.notifications_enabled !== undefined) {

            document.getElementById("notificationsToggle").checked =
                Boolean(data.notifications_enabled);

        }


        if (data.email_alerts !== undefined) {

            document.getElementById("emailAlertsToggle").checked =
                Boolean(data.email_alerts);

        }


        if (data.sms_alerts !== undefined) {

            document.getElementById("smsAlertsToggle").checked =
                Boolean(data.sms_alerts);

        }

    }

    catch (error) {

        console.error(
            "Error loading settings:",
            error
        );

    }

}


// ==========================================================
// SAVE APPEARANCE
// ==========================================================

async function saveAppearance() {

    const token = getSettingsToken();

    if (!token) {
        showMessage(
            "appearanceMsg",
            "Please login again.",
            "danger"
        );
        return;
    }


    const payload = {

        theme:
            document.getElementById("themeSelect").value,

        language:
            document.getElementById("languageInput").value

    };


    await saveSettings(
        payload,
        "appearanceMsg"
    );

}


// ==========================================================
// SAVE NOTIFICATIONS
// ==========================================================

async function saveNotifications() {

    const token = getSettingsToken();

    if (!token) {

        showMessage(
            "notificationsMsg",
            "Please login again.",
            "danger"
        );

        return;
    }


    const payload = {

        notifications_enabled:
            document.getElementById(
                "notificationsToggle"
            ).checked,

        email_alerts:
            document.getElementById(
                "emailAlertsToggle"
            ).checked,

        sms_alerts:
            document.getElementById(
                "smsAlertsToggle"
            ).checked

    };


    await saveSettings(
        payload,
        "notificationsMsg"
    );

}


// ==========================================================
// SAVE SETTINGS
// ==========================================================

async function saveSettings(payload, messageElement) {

    const token = getSettingsToken();


    try {

        const response = await fetch("/settings/", {

            method: "PUT",

            headers: {

                "Authorization":
                    `Bearer ${token}`,

                "Content-Type":
                    "application/json",

                "Accept":
                    "application/json"

            },

            body: JSON.stringify(payload)

        });


        const data = await response.json()
            .catch(() => ({}));


        if (!response.ok) {

            throw new Error(
                data.detail ||
                `HTTP ${response.status}`
            );

        }


        showMessage(
            messageElement,
            "Settings saved successfully.",
            "success"
        );


        console.log(
            "Settings saved:",
            data
        );

    }

    catch (error) {

        console.error(
            "Save settings error:",
            error
        );


        showMessage(
            messageElement,
            error.message,
            "danger"
        );

    }

}


// ==========================================================
// SYSTEM INFORMATION
// ==========================================================

async function loadSystemInfo() {

    const token = getSettingsToken();

    if (!token) {
        return;
    }


    const table =
        document.getElementById("systemInfoTable");


    try {

        const response =
            await fetch("/settings/system-info", {

                headers: {

                    "Authorization":
                        `Bearer ${token}`,

                    "Accept":
                        "application/json"

                }

            });


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "System information:",
            data
        );


        table.innerHTML = "";


        Object.entries(data).forEach(
            ([key, value]) => {

                const row =
                    document.createElement("tr");


                row.innerHTML = `

                    <td class="text-secondary">
                        ${formatKey(key)}
                    </td>

                    <td>
                        ${value ?? "-"}
                    </td>

                `;


                table.appendChild(row);

            }
        );

    }

    catch (error) {

        console.error(
            "System info error:",
            error
        );


        table.innerHTML = `

            <tr>

                <td class="text-danger">

                    Unable to load system information.

                </td>

            </tr>

        `;

    }

}


// ==========================================================
// MESSAGE
// ==========================================================

function showMessage(
    elementId,
    message,
    type
) {

    const element =
        document.getElementById(elementId);


    if (!element) {
        return;
    }


    element.className =
        `mt-2 small text-${type}`;


    element.textContent =
        message;


    setTimeout(() => {

        element.textContent = "";

    }, 4000);

}


// ==========================================================
// FORMAT KEY
// ==========================================================

function formatKey(key) {

    return String(key)
        .replaceAll("_", " ")
        .replace(/\b\w/g, letter =>
            letter.toUpperCase()
        );

}