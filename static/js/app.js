// app.js - SafeStream Main Application with Authentication Protection

let ws = null;
let username = null;
let authToken = null;
let metricsInterval = null;

// Track rendered message IDs to avoid duplicates
const renderedMessageIds = new Set();

// Check authentication on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('App page loaded, checking authentication...');
    
    // Show loading overlay
    showLoadingOverlay(true);
    
    // Check if user is authenticated
    const isAuthenticated = await checkAuthentication();
    
    if (!isAuthenticated) {
        console.log('User not authenticated, redirecting to login...');
        window.location.href = '/login';
        return;
    }
    
    // User is authenticated, initialize app
    console.log(`Authenticated user: ${username}`);
    initializeApp();
    
    // Hide loading overlay
    showLoadingOverlay(false);
});

async function checkAuthentication() {
    const token = localStorage.getItem('safestream_token');
    const savedUsername = localStorage.getItem('safestream_username');
    
    if (!token || !savedUsername) {
        console.log('No stored credentials found');
        return false;
    }
    
    try {
        console.log('Validating stored authentication token...');
        const response = await fetch('/auth/me', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            // Token is valid, set global variables
            authToken = token;
            username = savedUsername;
            console.log(`Authentication successful for user: ${username}`);
            return true;
        } else {
            // Token is expired or invalid
            console.log('Stored token is invalid or expired');
            localStorage.removeItem('safestream_token');
            localStorage.removeItem('safestream_username');
            return false;
        }
    } catch (error) {
        console.error('Failed to validate authentication:', error);
        localStorage.removeItem('safestream_token');
        localStorage.removeItem('safestream_username');
        return false;
    }
}

function initializeApp() {
    // Update UI with user info
    document.getElementById('userName').textContent = username;
    
    // Set up event listeners
    setupEventListeners();
    
    // Start WebSocket connection
    connectWebSocket();
    
    // Start metrics polling
    startMetricsPolling();
    
    console.log('App initialized successfully');
}

function setupEventListeners() {
    // Logout button
    document.getElementById('logoutButton').addEventListener('click', handleLogout);
    
    // Message input and send button
    document.getElementById('sendButton').addEventListener('click', sendMessage);
    document.getElementById('messageInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}

function handleLogout() {
    console.log('User logged out');
    
    // Clear stored credentials
    localStorage.removeItem('safestream_token');
    localStorage.removeItem('safestream_username');
    
    // Close WebSocket connection
    if (ws) {
        ws.close();
        ws = null;
    }
    
    // Stop metrics polling
    stopMetricsPolling();
    
    // Redirect to login page
    window.location.href = '/login';
}

function showLoadingOverlay(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

function setConnectionStatus(status) {
    const statusElement = document.getElementById('connectionStatus');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    
    // Remove all status classes
    statusElement.classList.remove('connected', 'connecting', 'disconnected', 'hidden');
    
    switch (status) {
        case 'connected':
            statusElement.classList.add('connected');
            statusElement.textContent = '🟢 Connected';
            messageInput.disabled = false;
            sendButton.disabled = false;
            // Hide status after 2 seconds when connected
            setTimeout(() => statusElement.classList.add('hidden'), 2000);
            break;
        case 'connecting':
            statusElement.classList.add('connecting');
            statusElement.textContent = '🟡 Connecting...';
            messageInput.disabled = true;
            sendButton.disabled = true;
            break;
        case 'disconnected':
            statusElement.classList.add('disconnected');
            statusElement.textContent = '🔴 Disconnected';
            messageInput.disabled = true;
            sendButton.disabled = true;
            break;
    }
}

function connectWebSocket() {
    if (!authToken || !username) {
        console.error('Cannot connect WebSocket: missing authentication');
        return;
    }
    
    console.log('Connecting to WebSocket...');
    setConnectionStatus('connecting');
    
    // Close existing connection
    if (ws) {
        ws.onclose = null;
        ws.close();
        ws = null;
    }
    
    const wsUrl = `ws://${location.host}/ws/${encodeURIComponent(username)}?token=${encodeURIComponent(authToken)}`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected successfully');
        setConnectionStatus('connected');
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    };
    
    ws.onclose = (event) => {
        console.log(`WebSocket disconnected: ${event.code} - ${event.reason}`);
        setConnectionStatus('disconnected');
        
        // Handle different close codes
        if (event.code === 1008 || event.code === 1007) {
            // Authentication failed
            console.log('WebSocket authentication failed, redirecting to login...');
            handleLogout();
        } else if (event.code !== 1000) {
            // Unexpected disconnection, try to reconnect
            console.log('Attempting to reconnect WebSocket...');
            setTimeout(() => {
                if (authToken && username) {
                    connectWebSocket();
                }
            }, 2000);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('disconnected');
    };
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'chat':
            renderChatMessage(data);
            break;
        case 'gift':
            renderGift(data);
            break;
        case 'metrics':
            updateMetrics(data.viewer_count || 0, data.gift_count || 0);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

function getMessageUniqueId(msg) {
    // Use database ID if available (guaranteed unique)
    if (msg.id) return msg.id;
    
    // Fallback for messages without ID: use timestamp with high precision
    const timestamp = msg.ts || msg.timestamp || Date.now();
    const user = msg.user || 'unknown';
    const message = msg.message || '';
    
    // Include a random component to ensure uniqueness even for identical content
    const randomSuffix = Math.random().toString(36).substr(2, 9);
    return `${timestamp}:${user}:${btoa(message)}:${randomSuffix}`;
}

function renderChatMessage(msg) {
    const chatMessages = document.getElementById('chatMessages');
    const uniqueId = getMessageUniqueId(msg);
    
    if (renderedMessageIds.has(uniqueId)) {
        return; // Already rendered
    }
    renderedMessageIds.add(uniqueId);
    
    // Store current focus to restore it if needed
    const activeElement = document.activeElement;
    const wasInputFocused = activeElement && activeElement.id === 'messageInput';
    
    const div = document.createElement('div');
    div.className = 'chat-message';
    
    if (msg.toxic) {
        div.classList.add('toxic');
        div.setAttribute('data-toxicity', `Toxicity: ${(msg.score * 100).toFixed(1)}%`);
    }
    
    div.innerHTML = `<span class="chat-username">${msg.user}</span> <span class="chat-text">${msg.message}</span>`;
    chatMessages.appendChild(div);
    
    // Use requestAnimationFrame to avoid blocking the main thread
    requestAnimationFrame(() => {
        setChatMessageOpacities();
        scrollChatToBottom();
        
        // Restore focus if it was on the input and got lost
        if (wasInputFocused && document.activeElement !== activeElement) {
            activeElement.focus();
        }
    });
}

function renderGift(gift) {
    const videoBg = document.querySelector('.video-bg');
    const badge = document.createElement('div');
    badge.className = 'gift-badge';
    badge.innerText = `🎁 x${gift.amount}`;
    
    // Random positioning
    const horizontalPos = 15 + Math.random() * 70;
    const startBottom = 5 + Math.random() * 15;
    
    badge.style.left = `${horizontalPos}%`;
    badge.style.bottom = `${startBottom}%`;
    
    // Animation duration
    const animationDuration = 3.5 + Math.random() * 1;
    badge.style.animationDuration = `${animationDuration}s`;
    
    // Add gift info
    badge.setAttribute('data-sender', gift.from || 'anonymous');
    badge.setAttribute('data-amount', gift.amount);
    
    videoBg.appendChild(badge);
    
    // Remove after animation
    setTimeout(() => {
        if (badge.parentNode) {
            badge.remove();
        }
    }, animationDuration * 1000 + 500);
}

function setChatMessageOpacities() {
    const chatMessages = document.getElementById('chatMessages');
    const messages = Array.from(chatMessages.children);
    const total = messages.length;
    
    if (total > 50) {
        // For performance, only set opacity on the last 20 messages
        const startIndex = Math.max(0, total - 20);
        for (let i = startIndex; i < total; i++) {
            const msg = messages[i];
            const opacity = Math.max(1 - (total - 1 - i) * 0.15, 0.05);
            msg.style.opacity = opacity;
        }
    } else {
        // Set opacity on all messages if count is reasonable
        messages.forEach((msg, i) => {
            const opacity = Math.max(1 - (total - 1 - i) * 0.15, 0.05);
            msg.style.opacity = opacity;
        });
    }
}

function scrollChatToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    const threshold = 40;
    const isAtBottom = chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight < threshold;
    
    if (isAtBottom) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    
    if (!text) return;
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'chat', message: text }));
        input.value = '';
        setTimeout(() => input.focus(), 0);
    } else {
        console.warn('Cannot send message: WebSocket not connected');
    }
}

function updateMetrics(viewerCount = 0, giftCount = 0) {
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
            updateMetrics(data.viewer_count || 0, data.gift_count || 0);
        } else if (response.status === 401) {
            console.log('Authentication expired, logging out...');
            handleLogout();
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