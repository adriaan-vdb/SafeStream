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
    
    // Initialize local video stream for all authenticated users
    initLocalStream();
    
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
    
    // Scroll to bottom button
    document.getElementById('scrollToBottom').addEventListener('click', () => {
        scrollChatToBottom();
        hideScrollToBottomButton();
    });
    
    // Chat scroll listener
    document.getElementById('chatMessages').addEventListener('scroll', handleChatScroll);
    
    // Heart reactions - send gifts when clicked
    setupHeartReactions();
}

function setupHeartReactions() {
    const heartReactions = document.querySelectorAll('.heart-reaction');
    
    // Map each heart emoji to a gift_id
    const heartGiftMap = {
        '❤️': 1,    // Red heart
        '💖': 2,    // Sparkling heart
        '💕': 3,    // Two hearts
        '💗': 4,    // Growing heart
        '💓': 5     // Beating heart
    };
    
    heartReactions.forEach(heart => {
        heart.addEventListener('click', () => {
            const heartEmoji = heart.textContent.trim();
            const giftId = heartGiftMap[heartEmoji];
            
            if (giftId && username) {
                sendGift(giftId, heartEmoji);
                
                // Add visual feedback
                animateHeartClick(heart);
            }
        });
        
        // Add hover effect styling
        heart.style.cursor = 'pointer';
        heart.style.transition = 'all 0.2s ease';
        heart.addEventListener('mouseenter', () => {
            heart.style.transform = 'scale(1.2)';
            heart.style.filter = 'brightness(1.3)';
        });
        heart.addEventListener('mouseleave', () => {
            heart.style.transform = 'scale(1)';
            heart.style.filter = 'brightness(1)';
        });
    });
}

function animateHeartClick(heartElement) {
    // Add a pulsing animation when heart is clicked
    heartElement.style.transform = 'scale(1.5)';
    heartElement.style.filter = 'brightness(1.5) drop-shadow(0 0 10px currentColor)';
    
    setTimeout(() => {
        heartElement.style.transform = 'scale(1)';
        heartElement.style.filter = 'brightness(1)';
    }, 200);
    
    // Create floating heart animation
    createFloatingHeart(heartElement);
}

function createFloatingHeart(sourceElement) {
    const floatingHeart = document.createElement('div');
    floatingHeart.textContent = sourceElement.textContent;
    floatingHeart.style.position = 'absolute';
    floatingHeart.style.fontSize = '24px';
    floatingHeart.style.pointerEvents = 'none';
    floatingHeart.style.zIndex = '1000';
    
    // Position relative to the source heart
    const rect = sourceElement.getBoundingClientRect();
    floatingHeart.style.left = rect.left + 'px';
    floatingHeart.style.top = rect.top + 'px';
    
    // Animation styles
    floatingHeart.style.animation = 'floatUp 2s ease-out forwards';
    
    document.body.appendChild(floatingHeart);
    
    // Remove after animation
    setTimeout(() => {
        floatingHeart.remove();
    }, 2000);
}

async function sendGift(giftId, heartEmoji) {
    if (!username) {
        console.error('Cannot send gift: no username');
        return;
    }
    
    try {
        const giftData = {
            from: username,
            gift_id: giftId,
            amount: 1
        };
        
        const response = await fetch('/api/gift', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(giftData)
        });
        
        if (response.ok) {
            console.log(`Gift sent successfully: ${heartEmoji} (ID: ${giftId})`);
        } else {
            console.error('Failed to send gift:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('Error sending gift:', error);
    }
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
    console.log(`[${username}] Received WebSocket message:`, data);
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
        console.log(`Duplicate message prevented: ${msg.user}: ${msg.message.substring(0, 20)}...`);
        return; // Already rendered
    }
    renderedMessageIds.add(uniqueId);
    
    // Debug logging for message tracking
    console.log(`Rendering message ${renderedMessageIds.size}: ${msg.user}: ${msg.message.substring(0, 20)}...`);
    
    // Store current scroll position and whether user was near bottom
    const wasAtBottom = isUserAtBottom(chatMessages);
    
    // Store current focus to restore it if needed
    const activeElement = document.activeElement;
    const wasInputFocused = activeElement && activeElement.id === 'messageInput';
    
    const div = document.createElement('div');
    div.className = 'chat-message';
    
    // Store the unique message ID for cleanup purposes
    div.dataset.messageId = uniqueId;
    
    if (msg.blocked) {
        div.classList.add('blocked');
        div.setAttribute('data-blocked', `Message blocked (${(msg.score * 100).toFixed(1)}% toxic)`);
    } else if (msg.toxic) {
        div.classList.add('toxic');
        div.setAttribute('data-toxicity', `Toxicity: ${(msg.score * 100).toFixed(1)}%`);
    }
    
    div.innerHTML = `<span class="chat-username">${msg.user}</span> <span class="chat-text">${msg.message}</span>`;
    chatMessages.appendChild(div);
    
    // Manage message history to prevent too many DOM elements
    manageChatHistory(chatMessages);
    
    // Use requestAnimationFrame to avoid blocking the main thread
    requestAnimationFrame(() => {
        setChatMessageOpacities();
        
        // Only auto-scroll if user was already at the bottom
        if (wasAtBottom) {
            scrollChatToBottom();
        }
        
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
            const opacity = Math.max(1 - (total - 1 - i) * 0.1, 0.2);
            msg.style.opacity = opacity;
        }
    } else {
        // Set opacity on all messages if count is reasonable
        messages.forEach((msg, i) => {
            const opacity = Math.max(1 - (total - 1 - i) * 0.15, 0.15);
            msg.style.opacity = opacity;
        });
    }
}

function isUserAtBottom(chatMessages) {
    const threshold = 50; // pixels from bottom
    return chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight < threshold;
}

function scrollChatToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function manageChatHistory(chatMessages) {
    const maxMessages = 200; // Keep up to 200 messages in DOM
    const messages = chatMessages.children;
    
    if (messages.length > maxMessages) {
        // Remove oldest messages but keep scroll position stable
        const removeCount = messages.length - maxMessages;
        const scrollHeight = chatMessages.scrollHeight;
        const scrollTop = chatMessages.scrollTop;
        
        console.log(`Cleaning up ${removeCount} messages. RenderedMessageIds size before: ${renderedMessageIds.size}`);
        
        // Remove oldest messages
        for (let i = 0; i < removeCount; i++) {
            if (messages[0]) {
                const messageId = getMessageIdFromElement(messages[0]);
                if (messageId) {
                    const deleted = renderedMessageIds.delete(messageId);
                    if (!deleted) {
                        console.warn('Failed to delete message ID from set:', messageId);
                    }
                }
                messages[0].remove();
            }
        }
        
        console.log(`RenderedMessageIds size after: ${renderedMessageIds.size}`);
        
        // Maintain scroll position after removing messages
        const newScrollHeight = chatMessages.scrollHeight;
        const heightDiff = scrollHeight - newScrollHeight;
        chatMessages.scrollTop = Math.max(0, scrollTop - heightDiff);
    }
    
    // Additional safeguard: If renderedMessageIds set grows too large, clear it
    if (renderedMessageIds.size > 1000) {
        console.warn(`RenderedMessageIds set too large (${renderedMessageIds.size}), clearing to prevent memory issues`);
        renderedMessageIds.clear();
    }
}

function getMessageIdFromElement(element) {
    // Get the stored message ID from the element's data attribute
    return element.dataset.messageId || null;
}

function handleChatScroll() {
    const chatMessages = document.getElementById('chatMessages');
    const scrollButton = document.getElementById('scrollToBottom');
    
    if (isUserAtBottom(chatMessages)) {
        hideScrollToBottomButton();
    } else {
        showScrollToBottomButton();
    }
}

function showScrollToBottomButton() {
    const scrollButton = document.getElementById('scrollToBottom');
    scrollButton.classList.add('visible');
}

function hideScrollToBottomButton() {
    const scrollButton = document.getElementById('scrollToBottom');
    scrollButton.classList.remove('visible');
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    
    if (!text) return;
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        console.log(`[${username}] Sending message:`, text);
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

// Initialize local video stream for streamers
async function initLocalStream() {
    try {
        console.log('Requesting camera and microphone access...');
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: true 
        });
        
        // Get video element and placeholder
        const localVideo = document.getElementById('localVideo');
        const videoPlaceholder = document.getElementById('videoPlaceholder');
        
        // Attach stream to video element
        localVideo.srcObject = stream;
        
        // Show video and hide placeholder
        localVideo.style.display = 'block';
        videoPlaceholder.style.display = 'none';
        
        console.log('✓ Local video stream initialized successfully');
        showToast('📹 Camera connected!', 'success');
        
    } catch (error) {
        console.error('Failed to access camera:', error);
        let errorMessage = 'Cannot access camera';
        
        // Provide more specific error messages
        if (error.name === 'NotAllowedError') {
            errorMessage = 'Camera access denied. Please allow camera permissions.';
        } else if (error.name === 'NotFoundError') {
            errorMessage = 'No camera found on this device.';
        } else if (error.name === 'NotReadableError') {
            errorMessage = 'Camera is being used by another application.';
        }
        
        showToast(errorMessage, 'error');
    }
}

// Show toast notifications
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Style the toast
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? '#ff4444' : type === 'success' ? '#44ff44' : '#4444ff'};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        z-index: 10000;
        opacity: 0;
        transition: opacity 0.3s ease, transform 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        max-width: 90%;
        text-align: center;
    `;
    
    // Add to DOM
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';
    }, 100);
    
    // Remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(-20px)';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 4000);
} 