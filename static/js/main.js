// main.js - SafeStream Frontend WebSocket Client with JWT Authentication

let ws = null;
let username = null;
let authToken = null;
let metricsInterval = null;

// Check if user is already authenticated
function checkAuthStatus() {
    const token = localStorage.getItem('safestream_token');
    const savedUsername = localStorage.getItem('safestream_username');
    
    if (token && savedUsername) {
        authToken = token;
        username = savedUsername;
        return true;
    }
    return false;
}

function showModal(show) {
    const modal = document.getElementById('authModal');
    if (show) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

function switchTab(tabName) {
    // Update tab buttons
    document.getElementById('loginTab').classList.toggle('active', tabName === 'login');
    document.getElementById('registerTab').classList.toggle('active', tabName === 'register');
    
    // Update forms
    document.getElementById('loginForm').classList.toggle('hidden', tabName !== 'login');
    document.getElementById('registerForm').classList.toggle('hidden', tabName !== 'register');
    
    // Clear errors
    document.getElementById('loginError').textContent = '';
    document.getElementById('registerError').textContent = '';
}

function showError(formId, message) {
    const errorElement = document.getElementById(formId + 'Error');
    errorElement.textContent = message;
}

function clearError(formId) {
    const errorElement = document.getElementById(formId + 'Error');
    errorElement.textContent = '';
}

async function login() {
    const loginUsername = document.getElementById('loginUsername').value.trim();
    const loginPassword = document.getElementById('loginPassword').value;
    
    if (!loginUsername || !loginPassword) {
        showError('login', 'Please enter both username and password');
        return;
    }
    
    clearError('login');
    
    try {
        const formData = new FormData();
        formData.append('username', loginUsername);
        formData.append('password', loginPassword);
        
        const response = await fetch('/auth/login', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            username = data.username;
            
            // Store in localStorage
            localStorage.setItem('safestream_token', authToken);
            localStorage.setItem('safestream_username', username);
            
            showModal(false);
            connectWS();
        } else {
            const errorData = await response.json();
            showError('login', errorData.detail || 'Login failed');
        }
    } catch (error) {
        showError('login', 'Network error. Please try again.');
    }
}

async function register() {
    const registerUsername = document.getElementById('registerUsername').value.trim();
    const registerEmail = document.getElementById('registerEmail').value.trim();
    const registerPassword = document.getElementById('registerPassword').value;
    const registerPasswordConfirm = document.getElementById('registerPasswordConfirm').value;
    
    if (!registerUsername || !registerPassword) {
        showError('register', 'Please enter username and password');
        return;
    }
    
    if (registerPassword !== registerPasswordConfirm) {
        showError('register', 'Passwords do not match');
        return;
    }
    
    if (registerPassword.length < 6) {
        showError('register', 'Password must be at least 6 characters');
        return;
    }
    
    clearError('register');
    
    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: registerUsername,
                password: registerPassword,
                email: registerEmail || null
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            username = data.username;
            
            // Store in localStorage
            localStorage.setItem('safestream_token', authToken);
            localStorage.setItem('safestream_username', username);
            
            showModal(false);
            connectWS();
        } else {
            const errorData = await response.json();
            showError('register', errorData.detail || 'Registration failed');
        }
    } catch (error) {
        showError('register', 'Network error. Please try again.');
    }
}

function logout() {
    authToken = null;
    username = null;
    localStorage.removeItem('safestream_token');
    localStorage.removeItem('safestream_username');
    
    if (ws) {
        ws.close();
        ws = null;
    }
    
    showModal(true);
    switchTab('login');
}

function scrollChatToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updateLiveMetrics(viewerCount = 0, giftCount = 0) {
    const metricsElement = document.getElementById('live-metrics');
    if (metricsElement) {
        metricsElement.textContent = `👥 ${viewerCount}  🎁 ${giftCount}`;
    }
}

async function fetchMetrics() {
    try {
        const response = await fetch('/metrics');
        if (response.ok) {
            const data = await response.json();
            updateLiveMetrics(data.viewer_count || 0, data.gift_count || 0);
        }
    } catch (error) {
        console.warn('Failed to fetch metrics:', error);
    }
}

function startMetricsPolling() {
    // Initial fetch
    fetchMetrics();
    
    // Set up polling every 5 seconds
    metricsInterval = setInterval(fetchMetrics, 5000);
}

function stopMetricsPolling() {
    if (metricsInterval) {
        clearInterval(metricsInterval);
        metricsInterval = null;
    }
}

function renderMessage(msg) {
    const chatMessages = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'chat-message';
    if (msg.toxic) {
        div.classList.add('toxic');
        div.setAttribute('data-toxicity', `Toxicity: ${(msg.score * 100).toFixed(1)}%`);
    }
    div.innerHTML = `<span class="chat-username">${msg.user}</span> <span class="chat-text">${msg.message}</span>`;
    chatMessages.appendChild(div);
    scrollChatToBottom();
}

function renderGift(gift) {
    const videoBg = document.querySelector('.video-bg');
    const badge = document.createElement('div');
    badge.className = 'gift-badge';
    badge.innerText = `🎁 x${gift.amount}`;
    
    // Enhanced positioning - more dynamic spread across the screen
    const horizontalPos = 15 + Math.random() * 70; // 15% to 85% of width
    const startBottom = 5 + Math.random() * 15; // 5% to 20% from bottom
    
    badge.style.left = `${horizontalPos}%`;
    badge.style.bottom = `${startBottom}%`;
    
    // Add some randomness to the animation timing
    const animationDuration = 3.5 + Math.random() * 1; // 3.5-4.5 seconds
    badge.style.animationDuration = `${animationDuration}s`;
    
    // Add gift sender info as data attribute for potential future use
    badge.setAttribute('data-sender', gift.from || 'anonymous');
    badge.setAttribute('data-amount', gift.amount);
    
    videoBg.appendChild(badge);
    
    // Remove badge after animation completes
    setTimeout(() => {
        if (badge.parentNode) {
            badge.remove();
        }
    }, animationDuration * 1000 + 500); // Extra 500ms buffer
}

function connectWS() {
    if (!authToken || !username) {
        console.error('No authentication token or username');
        return;
    }
    
    ws = new WebSocket(`ws://${location.host}/ws/${encodeURIComponent(username)}?token=${encodeURIComponent(authToken)}`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendButton').disabled = false;
    };
    
    ws.onmessage = (event) => {
        let data;
        try {
            data = JSON.parse(event.data);
        } catch {
            return;
        }
        
        if (data.type === 'chat') {
            renderMessage(data);
        } else if (data.type === 'gift') {
            renderGift(data);
        } else if (data.type === 'metrics') {
            // Handle live metrics updates from WebSocket
            updateLiveMetrics(data.viewer_count || 0, data.gift_count || 0);
        }
    };
    
    ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        document.getElementById('messageInput').disabled = true;
        document.getElementById('sendButton').disabled = true;
        
        // If authentication failed, show login modal
        if (event.code === 1008) {
            logout();
        } else {
            // Try to reconnect after a delay
            setTimeout(() => {
                if (authToken && username) {
                    connectWS();
                }
            }, 2000);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    if (!text) return;
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'chat', message: text }));
        input.value = '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Create live metrics badge
    const metricsBadge = document.createElement('div');
    metricsBadge.id = 'live-metrics';
    metricsBadge.textContent = '👥 0  🎁 0';
    document.body.appendChild(metricsBadge);
    
    // Start metrics polling
    startMetricsPolling();
    
    // Check if user is already authenticated
    if (checkAuthStatus()) {
        connectWS();
    } else {
        showModal(true);
        switchTab('login');
    }
    
    // Tab switching
    document.getElementById('loginTab').onclick = () => switchTab('login');
    document.getElementById('registerTab').onclick = () => switchTab('register');
    
    // Form submissions
    document.getElementById('loginButton').onclick = login;
    document.getElementById('registerButton').onclick = register;
    
    // Enter key handlers
    document.getElementById('loginPassword').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') login();
    });
    
    document.getElementById('registerPasswordConfirm').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') register();
    });
    
    // Input bar logic
    document.getElementById('sendButton').onclick = sendMessage;
    document.getElementById('messageInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // Disable input until connected
    document.getElementById('messageInput').disabled = true;
    document.getElementById('sendButton').disabled = true;
}); 