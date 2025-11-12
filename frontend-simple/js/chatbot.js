/**
 * Simplified Chatbot with FAQ Bubbles & RAG
 */

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    window.utils.requireAuth();
    loadFAQBubbles();
    loadChatHistory();
    setupEnterKeyListener();
});

// Load FAQ bubbles (5 quick questions)
async function loadFAQBubbles() {
    const container = document.getElementById('faq-bubbles');
    if (!container) return;

    try {
        const response = await window.api.getFAQs();
        const faqs = response.data || response || [];

        if (faqs.length > 0) {
            container.innerHTML = faqs.map(faq => `
                <button 
                    class="faq-bubble" 
                    onclick="handleFAQClick(${faq.id}, '${escapeHtml(faq.question)}')"
                >
                    ${faq.question}
                </button>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-muted">No quick questions available</p>';
        }
    } catch (error) {
        console.error('Error loading FAQs:', error);
        container.innerHTML = '<p class="text-error">Failed to load quick questions</p>';
    }
}

// Load chat history
async function loadChatHistory() {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    try {
        const response = await window.api.getChatHistory();
        const messages = response.data || response || [];

        if (messages.length > 0) {
            // Clear welcome message
            messagesContainer.innerHTML = messages.map(msg => renderMessage(msg)).join('');
            scrollToBottom();
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

// Handle FAQ bubble click
async function handleFAQClick(faqId, question) {
    // Disable all FAQ bubbles during request
    disableFAQBubbles(true);

    // Add user message to UI
    addMessageToUI('user', question);

    try {
        const response = await window.api.sendChatMessage({
            faq_id: faqId,
            message: question
        });

        const assistantMessage = response.message || response.data?.message || 'Sorry, I couldn\'t process that.';
        addMessageToUI('assistant', assistantMessage);
    } catch (error) {
        console.error('Error sending FAQ:', error);
        addMessageToUI('assistant', 'Sorry, something went wrong. Please try again.');
    } finally {
        disableFAQBubbles(false);
    }
}

// Send custom message
async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (!message) {
        showAlert('error', 'Please enter a message');
        return;
    }

    // Disable input during request
    setInputState(true);

    // Add user message to UI
    addMessageToUI('user', message);
    input.value = '';

    try {
        const response = await window.api.sendChatMessage({
            message: message
        });

        const assistantMessage = response.message || response.data?.message || 'Sorry, I couldn\'t process that.';
        addMessageToUI('assistant', assistantMessage);
    } catch (error) {
        console.error('Error sending message:', error);
        addMessageToUI('assistant', 'Sorry, something went wrong. Please try again.');
    } finally {
        setInputState(false);
        input.focus();
    }
}

// Add message to UI
function addMessageToUI(role, content) {
    const messagesContainer = document.getElementById('chat-messages');
    
    // Remove welcome message if exists
    const welcomeMsg = messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}-message`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-role">${role === 'user' ? '👤 You' : '🤖 Assistant'}</div>
            <div class="message-text">${escapeHtml(content)}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Render message from history
function renderMessage(msg) {
    const role = msg.role || 'user';
    const content = msg.content || '';
    const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : '';

    return `
        <div class="chat-message ${role}-message">
            <div class="message-content">
                <div class="message-role">${role === 'user' ? '👤 You' : '🤖 Assistant'}</div>
                <div class="message-text">${escapeHtml(content)}</div>
                <div class="message-time">${timestamp}</div>
            </div>
        </div>
    `;
}

// Utility functions
function setInputState(loading) {
    const input = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const sendText = document.getElementById('send-btn-text');
    const sendLoading = document.getElementById('send-btn-loading');

    if (loading) {
        input.disabled = true;
        sendBtn.disabled = true;
        sendText.classList.add('hidden');
        sendLoading.classList.remove('hidden');
    } else {
        input.disabled = false;
        sendBtn.disabled = false;
        sendText.classList.remove('hidden');
        sendLoading.classList.add('hidden');
    }
}

function disableFAQBubbles(disabled) {
    document.querySelectorAll('.faq-bubble').forEach(bubble => {
        bubble.disabled = disabled;
        if (disabled) {
            bubble.style.opacity = '0.5';
            bubble.style.cursor = 'not-allowed';
        } else {
            bubble.style.opacity = '1';
            bubble.style.cursor = 'pointer';
        }
    });
}

function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
}

function setupEnterKeyListener() {
    const input = document.getElementById('message-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAlert(type, message) {
    alert(message);
}

function logout() {
    window.utils.logout();
}
