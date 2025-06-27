// main.js - SafeStream Frontend WebSocket Client

let ws = null;
let username = null;

function showModal(show) {
    const modal = document.getElementById('usernameModal');
    if (show) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

function scrollChatToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
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
    // Random horizontal position (10% to 80% of width)
    badge.style.left = `${10 + Math.random() * 70}%`;
    badge.style.bottom = '10px';
    videoBg.appendChild(badge);
    setTimeout(() => {
        badge.remove();
    }, 3000);
}

function connectWS() {
    ws = new WebSocket(`ws://${location.host}/ws/${encodeURIComponent(username)}`);
    ws.onopen = () => {
        showModal(false);
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
        }
    };
    ws.onclose = () => {
        document.getElementById('messageInput').disabled = true;
        document.getElementById('sendButton').disabled = true;
        setTimeout(connectWS, 2000); // Try to reconnect
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
    // Modal logic
    showModal(true);
    document.getElementById('joinButton').onclick = () => {
        const val = document.getElementById('usernameInput').value.trim();
        if (val) {
            username = val;
            connectWS();
        }
    };
    document.getElementById('usernameInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('joinButton').click();
        }
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