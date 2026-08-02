// ==========================================================
// frontend/static/js/notification.js
// Integrated Notification Workflows (Milestone 3 Requirement)
// ==========================================================

// Request browser notification permissions on initial load
document.addEventListener("DOMContentLoaded", () => {
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }
});

/**
 * Triggers Toast Alert Banners and Desktop Push Notifications
 * @param {string} title - Notification Header Title
 * @param {string} body - Detail message
 * @param {string} type - Alert severity type ('error' | 'warning' | 'info' | 'success')
 */
function triggerNotification(title, body, type = 'info') {
    // 1. In-App Banner Toast Display
    const banner = document.getElementById('notification-banner');
    if (banner) {
        const bgClass = type === 'error' ? 'alert-danger' : (type === 'warning' ? 'alert-warning' : 'alert-info');
        banner.className = `alert ${bgClass} alert-dismissible fade show mb-4`;
        banner.innerHTML = `
            <strong>${title}</strong>: ${body}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        banner.classList.remove('d-none');
    }

    // 2. System/Browser Push Notification
    if ("Notification" in window && Notification.permission === "granted") {
        new Notification(title, {
            body: body,
            icon: '/static/images/traffic_icon.png'
        });
    }
}