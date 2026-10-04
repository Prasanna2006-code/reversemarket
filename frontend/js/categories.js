/**
 * ReverseMarket - Category Specifications Configuration
 * Defines dynamic, category-specific fields for Product Catalog and Requirements.
 * None of these fields are compulsory; both clients and dealers can fill what is known.
 */

const CATEGORY_SPECS = {
    computers: {
        name: "Computers & Laptops",
        fields: [
            { key: "brand", label: "Brand", placeholder: "e.g. Dell, HP, Lenovo, Apple" },
            { key: "model", label: "Model", placeholder: "e.g. Latitude 5420, ThinkPad T14" },
            { key: "processor", label: "Processor", placeholder: "e.g. Intel Core i7, AMD Ryzen 7" },
            { key: "ram", label: "RAM Memory", placeholder: "e.g. 16GB DDR4, 32GB" },
            { key: "storage", label: "Storage Capacity", placeholder: "e.g. 512GB SSD, 1TB NVMe" },
            { key: "screen_size", label: "Screen Size", placeholder: "e.g. 14 inch FHD, 15.6 inch" }
        ]
    },
    electronics: {
        name: "Electronics & AV",
        fields: [
            { key: "brand", label: "Brand", placeholder: "e.g. Sony, Samsung, LG" },
            { key: "model", label: "Model Number", placeholder: "e.g. Bravia 55X, WH-1000XM5" },
            { key: "power", label: "Power / Battery", placeholder: "e.g. 500W, 30 Hours Playtime" },
            { key: "connectivity", label: "Connectivity", placeholder: "e.g. HDMI 2.1, Bluetooth 5.3, Wi-Fi 6" }
        ]
    },
    furniture: {
        name: "Furniture & Office Setup",
        fields: [
            { key: "material", label: "Material", placeholder: "e.g. Breathable Korean Mesh, Solid Teakwood, Mild Steel" },
            { key: "dimensions", label: "Dimensions (L x W x H)", placeholder: "e.g. 120cm x 60cm x 75cm" },
            { key: "color", label: "Color / Finish", placeholder: "e.g. Matte Black, Walnut Brown" },
            { key: "weight_capacity", label: "Weight Capacity", placeholder: "e.g. 150 kg" }
        ]
    },
    vehicle: {
        name: "Commercial & Private Vehicles",
        fields: [
            { key: "brand", label: "Brand / Make", placeholder: "e.g. Tata, Mahindra, Toyota, Ashok Leyland" },
            { key: "model", label: "Model / Variant", placeholder: "e.g. Ace Gold, Bolero Maxi Truck, Innova" },
            { key: "year", label: "Manufacturing Year", placeholder: "e.g. 2022, 2023, 2024" },
            { key: "fuel_type", label: "Fuel Type", placeholder: "e.g. Diesel, CNG, Electric, Petrol" },
            { key: "mileage", label: "Mileage / Odometer Reading", placeholder: "e.g. 18 kmpl or Under 30,000 km" },
            { key: "transmission", label: "Transmission", placeholder: "e.g. Manual, Automatic" }
        ]
    },
    industrial: {
        name: "Industrial Equipment & Machinery",
        fields: [
            { key: "brand", label: "Brand / Manufacturer", placeholder: "e.g. Bosch, Kirloskar, L&T, Siemens" },
            { key: "model", label: "Model / Series", placeholder: "e.g. KEC Heavy Duty, GWS 600" },
            { key: "capacity", label: "Capacity / Workload", placeholder: "e.g. 500 Litres, 10 KVA, 5 Tons" },
            { key: "power", label: "Power Rating", placeholder: "e.g. 15 HP, 10 kW" },
            { key: "voltage", label: "Operating Voltage", placeholder: "e.g. 415V Three Phase, 230V Single Phase" }
        ]
    },
    services: {
        name: "Maintenance & Professional Services",
        fields: [
            { key: "service_type", label: "Service Type", placeholder: "e.g. Annual Maintenance (AMC), Installation, Audit" },
            { key: "experience", label: "Experience Level", placeholder: "e.g. 5+ Years Certified Technicians" },
            { key: "service_area", label: "Service Area / Coverage", placeholder: "e.g. Chennai Metro & Surrounding Districts" },
            { key: "availability", label: "Availability", placeholder: "e.g. 24/7 Emergency Support, Mon-Sat 9AM-6PM" },
            { key: "response_time", label: "Response Time SLA", placeholder: "e.g. Within 4 hours" },
            { key: "pricing_type", label: "Pricing Model", placeholder: "e.g. Fixed Project, Per Day, Hourly" }
        ]
    }
};

/**
 * Renders dynamic specification fields inside a container element based on selected category.
 * None of the generated inputs have the required attribute.
 */
function renderCategorySpecs(categoryKey, containerElement, initialValues = {}) {
    if (!containerElement) return;

    const catKey = String(categoryKey || "").toLowerCase();
    // Normalize aliases
    let resolvedKey = null;
    if (CATEGORY_SPECS[catKey]) {
        resolvedKey = catKey;
    } else if (catKey === "home") {
        resolvedKey = "furniture";
    } else if (catKey === "business") {
        resolvedKey = "industrial";
    }

    if (!resolvedKey) {
        containerElement.innerHTML = `
            <p style="color:#777; font-size:13px; font-style:italic;">
                Select a category above to unlock tailored technical specification fields (optional).
            </p>
        `;
        return;
    }

    const config = CATEGORY_SPECS[resolvedKey];
    const fields = config.fields || [];

    containerElement.innerHTML = `
        <div style="background:#fafafa; border:1px solid #e2e8f0; border-radius:6px; padding:18px; margin-top:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <strong style="color:#111; font-size:14px;">
                    🔧 ${config.name} Specifications <span style="font-weight:normal; color:#666; font-size:12px;">(All Optional)</span>
                </strong>
                <small style="color:#777;">Fill whatever is known</small>
            </div>
            <div class="form-grid" style="display:grid; grid-template-columns:1fr 1fr; gap:14px;">
                ${fields.map(f => {
                    const val = initialValues[f.key] || "";
                    return `
                        <div class="form-group" style="display:flex; flex-direction:column;">
                            <label style="font-size:13px; font-weight:600; color:#333; margin-bottom:5px;">
                                ${f.label} <small style="color:#888; font-weight:normal;">(optional)</small>
                            </label>
                            <input 
                                type="text" 
                                class="spec-input" 
                                data-spec-key="${f.key}" 
                                placeholder="${f.placeholder}" 
                                value="${String(val).replace(/"/g, '&quot;')}"
                                style="border:1px solid #ccc; border-radius:4px; padding:9px 11px; font-size:13px;"
                            >
                        </div>
                    `;
                }).join("")}
            </div>
        </div>
    `;
}

/**
 * Collects values from all .spec-input elements inside a container.
 */
function collectCategorySpecs(containerElement) {
    if (!containerElement) return {};
    const specs = {};
    const inputs = containerElement.querySelectorAll(".spec-input");
    inputs.forEach(input => {
        const key = input.getAttribute("data-spec-key");
        const val = input.value.trim();
        if (key && val) {
            specs[key] = val;
        }
    });
    return specs;
}

window.CATEGORY_SPECS = CATEGORY_SPECS;
window.renderCategorySpecs = renderCategorySpecs;
window.collectCategorySpecs = collectCategorySpecs;
