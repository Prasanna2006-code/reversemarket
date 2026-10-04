// frontend/js/auth.js
/**
 * ReverseMarket - Authentication Handler
 * Connects frontend forms to FastAPI Database-backed Authentication endpoints.
 */

document.addEventListener("DOMContentLoaded", () => {

    /* =========================
       LOGIN
    ========================= */
    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;
            const errorMessage = document.getElementById("errorMessage");

            errorMessage.style.display = "none";

            if (!email || !password) {
                errorMessage.textContent = "Please enter your email and password.";
                errorMessage.style.display = "block";
                return;
            }

            try {
                const res = await apiRequest("/api/auth/login", {
                    method: "POST",
                    body: JSON.stringify({ email, password })
                });

                if (res && res.token) {
                    localStorage.setItem("authToken", res.token);
                    localStorage.setItem("user", JSON.stringify({
                        id: res.user_id,
                        name: res.name,
                        email: res.email,
                        accountType: res.account_type
                    }));
                    localStorage.setItem("isLoggedIn", "true");
                    localStorage.setItem("userEmail", res.email);

                    // Redirect based on database account type
                    if (res.account_type === "dealer") {
                        window.location.href = "dealer/dashboard.html";
                    } else {
                        window.location.href = "client/home.html";
                    }
                }
            } catch (err) {
                errorMessage.textContent = err.message || "Invalid email or password.";
                errorMessage.style.display = "block";
            }
        });
    }

    /* =========================
       REGISTER
    ========================= */
    const registerForm = document.getElementById("registerForm");

    if (registerForm) {
        registerForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const name = document.getElementById("name").value.trim();
            const email = document.getElementById("email").value.trim();
            const phone = document.getElementById("phone").value.trim();
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirmPassword").value;
            const accountTypeInput = document.querySelector('input[name="accountType"]:checked');
            const accountType = accountTypeInput ? accountTypeInput.value : "client";

            const errorMessage = document.getElementById("errorMessage");
            const successMessage = document.getElementById("successMessage");

            errorMessage.style.display = "none";
            successMessage.style.display = "none";

            if (!name || !email || !password || !confirmPassword) {
                errorMessage.textContent = "Please fill in all required fields.";
                errorMessage.style.display = "block";
                return;
            }

            if (password.length < 6) {
                errorMessage.textContent = "Password must contain at least 6 characters.";
                errorMessage.style.display = "block";
                return;
            }

            if (password !== confirmPassword) {
                errorMessage.textContent = "Passwords do not match.";
                errorMessage.style.display = "block";
                return;
            }

            try {
                const res = await apiRequest("/api/auth/register", {
                    method: "POST",
                    body: JSON.stringify({
                        name,
                        email,
                        phone,
                        password,
                        account_type: accountType
                    })
                });

                if (res && res.token) {
                    localStorage.setItem("authToken", res.token);
                    localStorage.setItem("user", JSON.stringify({
                        id: res.user_id,
                        name: res.name,
                        email: res.email,
                        accountType: res.account_type
                    }));
                    localStorage.setItem("isLoggedIn", "true");
                    localStorage.setItem("userEmail", res.email);

                    successMessage.textContent = "Account created successfully! Redirecting...";
                    successMessage.style.display = "block";

                    setTimeout(() => {
                        if (res.account_type === "dealer") {
                            window.location.href = "dealer/dashboard.html";
                        } else {
                            window.location.href = "client/home.html";
                        }
                    }, 800);
                }
            } catch (err) {
                errorMessage.textContent = err.message || "Registration failed. Please try again.";
                errorMessage.style.display = "block";
            }
        });
    }

});
