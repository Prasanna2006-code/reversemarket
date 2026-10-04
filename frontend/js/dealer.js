/**
 * ReverseMarket - Dealer Portal JavaScript Module
 * Fully powered by FastAPI REST API & Database.
 * No marketplace reliance on localStorage mock data.
 */

const DealerModule = {
    getUser() {
        return window.getAuthUser ? window.getAuthUser() : JSON.parse(localStorage.getItem("user") || "null");
    },

    requireDealerAuth() {
        const token = localStorage.getItem("authToken");
        const user = this.getUser();
        if (!token || !user) {
            window.location.href = "../login.html";
            return false;
        }
        return true;
    },

    // Fetch open requirements posted across marketplace
    async getMarketplaceRequirements() {
        return await apiRequest("/api/requirements");
    },

    // Fetch single requirement
    async getRequirement(id) {
        return await apiRequest(`/api/requirements/${id}`);
    },

    // Product catalog management (Dealer creates product once)
    async getProducts() {
        return await apiRequest("/api/products");
    },

    async getProduct(id) {
        return await apiRequest(`/api/products/${id}`);
    },

    async addProduct(productData) {
        return await apiRequest("/api/products", {
            method: "POST",
            body: JSON.stringify(productData)
        });
    },

    async updateProduct(id, productData) {
        return await apiRequest(`/api/products/${id}`, {
            method: "PUT",
            body: JSON.stringify(productData)
        });
    },

    async deleteProduct(id) {
        return await apiRequest(`/api/products/${id}`, {
            method: "DELETE"
        });
    },

    // Submit quotation using existing catalog product or custom entry
    async submitOffer(offerData) {
        return await apiRequest("/api/offers", {
            method: "POST",
            body: JSON.stringify(offerData)
        });
    },

    // Fetch offers submitted by this dealer
    async getDealerOffers() {
        return await apiRequest("/api/dealers/my-offers");
    },

    // Orders received by this dealer
    async getDealerOrders() {
        return await apiRequest("/api/dealers/my-orders");
    }
};

window.DealerModule = DealerModule;
