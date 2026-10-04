/**
 * ReverseMarket - Universal API Client
 * Compatible with local dev (127.0.0.1:8000) and Cloud deployments (PostgreSQL + Vercel / Cloud).
 */

const getApiBaseUrl = () => {
    if (window.API_BASE_URL) return window.API_BASE_URL;

    // If served directly by FastAPI (e.g. port 8000) or under cloud domain with reverse proxy
    if (window.location.port === "8000") return "";

    // If loaded from Vercel or cloud web host using relative API routes
    if (window.location.hostname.includes("vercel.app") || window.location.hostname.includes("render.com")) {
        return "";
    }

    // If running on local dev server (e.g. VS Code Live Server / file protocol)
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.protocol === "file:") {
        return "http://127.0.0.1:8000";
    }

    return "";
};

const API_BASE_URL = getApiBaseUrl();

async function apiRequest(endpoint, options = {}) {
    try {
        const token = localStorage.getItem("authToken");

        const headers = {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {}),
            ...options.headers
        };

        const url = `${API_BASE_URL}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle 401 Unauthorized
        if (response.status === 401) {
            const currentPath = window.location.pathname.toLowerCase();
            if (!currentPath.includes("login.html") && !currentPath.includes("register.html") && !currentPath.endsWith("index.html") && currentPath !== "/") {
                localStorage.removeItem("authToken");
                localStorage.removeItem("isLoggedIn");
                localStorage.removeItem("user");
                // Check if in subfolder (client/ or dealer/)
                const prefix = (currentPath.includes("/client/") || currentPath.includes("/dealer/")) ? "../" : "";
                window.location.href = `${prefix}login.html?expired=1`;
            }
        }

        const data = await response.json();

        if (!response.ok) {
            const detailMsg = typeof data.detail === "string" ? data.detail : (Array.isArray(data.detail) ? data.detail.map(d => d.msg).join(", ") : "Request failed");
            throw new Error(detailMsg || "Something went wrong");
        }

        return data;

    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error.message);
        throw error;
    }
}

// Global Auth helpers
function getAuthUser() {
    try {
        return JSON.parse(localStorage.getItem("user")) || null;
    } catch (e) {
        return null;
    }
}

function isAuthenticated() {
    return !!localStorage.getItem("authToken") && localStorage.getItem("isLoggedIn") === "true";
}

function handleLogout() {
    localStorage.removeItem("authToken");
    localStorage.removeItem("user");
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("userEmail");
    const isSub = window.location.pathname.includes("/client/") || window.location.pathname.includes("/dealer/");
    window.location.href = isSub ? "../index.html" : "index.html";
}

window.apiRequest = apiRequest;
window.getAuthUser = getAuthUser;
window.isAuthenticated = isAuthenticated;
window.handleLogout = handleLogout;
