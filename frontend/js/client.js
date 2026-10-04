/**
 * ReverseMarket - Client Portal JavaScript Module
 * Fully powered by FastAPI REST API & Database.
 * No marketplace reliance on localStorage mock data.
 */

const ClientModule = {
    getUser() {
        return window.getAuthUser ? window.getAuthUser() : JSON.parse(localStorage.getItem("user") || "null");
    },

    requireAuth() {
        const token = localStorage.getItem("authToken");
        const user = this.getUser();
        if (!token || !user) {
            window.location.href = "../login.html";
            return false;
        }
        return true;
    },

    // Fetch requirements posted by this client
    async getMyRequirements() {
        return await apiRequest("/api/requirements/my");
    },

    // Fetch single requirement
    async getRequirement(id) {
        return await apiRequest(`/api/requirements/${id}`);
    },

    // Create a new client requirement with optional specs & budget
    async createRequirement(reqData) {
        return await apiRequest("/api/requirements", {
            method: "POST",
            body: JSON.stringify(reqData)
        });
    },

    // Fetch raw offers received
    async getOffers(requirementId = null) {
        const endpoint = requirementId && requirementId !== "all"
            ? `/api/offers?requirement_id=${requirementId}`
            : "/api/offers";
        return await apiRequest(endpoint);
    },

    // Fetch offers for a specific requirement (used by dashboard)
    async getOffersForRequirement(requirementId) {
        return await apiRequest(`/api/offers?requirement_id=${requirementId}`);
    },

    // Requirement 9 & 10: Fetch neural network ranked offers for requirement
    async getRankedOffers(requirementId) {
        return await apiRequest(`/api/ai/rank-offers/${requirementId}`);
    },

    // Confirm order & trigger positive/negative training data logging
    async placeOrder(orderData) {
        return await apiRequest("/api/orders", {
            method: "POST",
            body: JSON.stringify(orderData)
        });
    },

    // Fetch completed/active orders
    async getMyOrders() {
        return await apiRequest("/api/orders");
    }
};

window.ClientModule = ClientModule;
