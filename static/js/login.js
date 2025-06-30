// login.js - SafeStream Login Page Authentication

// Check if user is already authenticated on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Login page loaded, checking authentication status...');
    
    // Check if user is already logged in
    const token = localStorage.getItem('safestream_token');
    const username = localStorage.getItem('safestream_username');
    
    if (token && username) {
        console.log('Found stored token, validating...');
        showLoading(true);
        
        try {
            const response = await fetch('/auth/me', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                console.log('Token is valid, redirecting to app...');
                // Token is valid, redirect to main app
                window.location.href = '/app';
                return;
            } else {
                console.log('Token is invalid, clearing storage');
                // Token is expired or invalid, clear storage
                localStorage.removeItem('safestream_token');
                localStorage.removeItem('safestream_username');
            }
        } catch (error) {
            console.error('Failed to validate token:', error);
            localStorage.removeItem('safestream_token');
            localStorage.removeItem('safestream_username');
        }
        
        showLoading(false);
    }
    
    // Set up event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // Tab switching
    document.getElementById('loginTab').addEventListener('click', () => switchTab('login'));
    document.getElementById('registerTab').addEventListener('click', () => switchTab('register'));
    
    // Form submissions
    document.getElementById('loginButton').addEventListener('click', handleLogin);
    document.getElementById('registerButton').addEventListener('click', handleRegister);
    
    // Enter key handlers
    document.getElementById('loginPassword').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
    
    document.getElementById('registerPasswordConfirm').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleRegister();
    });
    
    // Auto-fill password when username is selected from dropdown (Login form)
    document.getElementById('loginUsername').addEventListener('input', (e) => {
        const username = e.target.value;
        const passwordField = document.getElementById('loginPassword');
        
        // Auto-fill password (same as username) for demo accounts
        const demoAccounts = ['demo_user', 'test_streamer', 'chat_viewer'];
        if (demoAccounts.includes(username)) {
            passwordField.value = username;
        }
    });
    
    // Auto-fill password when username is selected from dropdown (Register form)
    document.getElementById('registerUsername').addEventListener('input', (e) => {
        const username = e.target.value;
        const passwordField = document.getElementById('registerPassword');
        const confirmPasswordField = document.getElementById('registerPasswordConfirm');
        
        // Auto-fill password (same as username) for demo accounts
        const demoAccounts = ['demo_user', 'test_streamer', 'chat_viewer'];
        if (demoAccounts.includes(username)) {
            passwordField.value = username;
            confirmPasswordField.value = username;
        }
    });
}

function switchTab(tabName) {
    // Update tab buttons
    document.getElementById('loginTab').classList.toggle('active', tabName === 'login');
    document.getElementById('registerTab').classList.toggle('active', tabName === 'register');
    
    // Update forms
    document.getElementById('loginForm').classList.toggle('active', tabName === 'login');
    document.getElementById('registerForm').classList.toggle('active', tabName === 'register');
    
    // Clear errors
    clearError('login');
    clearError('register');
}

function showError(formType, message) {
    const errorElement = document.getElementById(formType + 'Error');
    errorElement.textContent = message;
}

function clearError(formType) {
    const errorElement = document.getElementById(formType + 'Error');
    errorElement.textContent = '';
}

function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    const loginButton = document.getElementById('loginButton');
    const registerButton = document.getElementById('registerButton');
    
    if (show) {
        spinner.style.display = 'block';
        loginButton.disabled = true;
        registerButton.disabled = true;
    } else {
        spinner.style.display = 'none';
        loginButton.disabled = false;
        registerButton.disabled = false;
    }
}

async function handleLogin() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showError('login', 'Please enter both username and password');
        return;
    }
    
    clearError('login');
    showLoading(true);
    
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch('/auth/login', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Store credentials
            localStorage.setItem('safestream_token', data.access_token);
            localStorage.setItem('safestream_username', data.username);
            
            console.log(`Login successful for user: ${data.username}`);
            
            // Redirect to main app
            window.location.href = '/app';
        } else {
            const errorData = await response.json();
            showError('login', errorData.detail || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('login', 'Network error. Please try again.');
    } finally {
        showLoading(false);
    }
}

async function handleRegister() {
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;
    
    if (!username || !password) {
        showError('register', 'Please enter username and password');
        return;
    }
    
    if (password !== passwordConfirm) {
        showError('register', 'Passwords do not match');
        return;
    }
    
    if (password.length < 6) {
        showError('register', 'Password must be at least 6 characters');
        return;
    }
    
    clearError('register');
    showLoading(true);
    
    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                email: email || null
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Store credentials
            localStorage.setItem('safestream_token', data.access_token);
            localStorage.setItem('safestream_username', data.username);
            
            console.log(`Registration successful for user: ${data.username}`);
            
            // Redirect to main app
            window.location.href = '/app';
        } else {
            const errorData = await response.json();
            showError('register', errorData.detail || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('register', 'Network error. Please try again.');
    } finally {
        showLoading(false);
    }
} 