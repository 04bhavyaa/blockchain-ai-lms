/**
 * Chatbot functionality
 */

let currentConversationId = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadConversations();
});

// Load conversations list
async function loadConversations() {
    const container = document.getElementById('conversations-list');
    if (!container) return;

    try {
        const response = await window.api.getConversations();
        // Handle both direct data array and wrapped response
        const conversations = response.data || response || [];
        
        if (conversations && conversations.length > 0) {
            container.innerHTML = conversations.map(conv => `
                <div class="conversation-item ${conv.id === currentConversationId ? 'active' : ''}" 
                     onclick="loadConversation(${conv.id})">
                    <div class="conversation-title">${conv.title || 'Untitled'}</div>
                    <div class="conversation-preview">${conv.description || conv.last_message || 'No messages yet'}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: var(--spacing-md);">No conversations yet. Create a new one!</p>';
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: var(--spacing-md);">No conversations yet. Create a new one!</p>';
    }
}

// Create new conversation
async function createNewConversation() {
    const title = prompt('Enter conversation title:', 'New Conversation');
    if (!title) return;

    try {
        const response = await window.api.createConversation(title);
        // Handle both wrapped and direct response
        const conversationId = response.data?.id || response.id || response.data?.data?.id;
        if (conversationId) {
            loadConversations();
            loadConversation(conversationId);
        } else {
            showAlert('error', 'Failed to create conversation');
        }
    } catch (error) {
        showAlert('error', error.message || 'Failed to create conversation');
    }
}

// Load conversation messages
async function loadConversation(conversationId) {
    currentConversationId = conversationId;
    loadConversations(); // Refresh to highlight active
    
    const messagesContainer = document.getElementById('chat-messages');
    const input = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    
    try {
        const response = await window.api.getConversation(conversationId);
        // Handle both wrapped and direct response
        const conversation = response.data || response;
        
        if (conversation) {
            document.getElementById('conversation-title').textContent = conversation.title || 'Conversation';
            
            // Enable input - make sure it's not disabled
            if (input) {
                input.disabled = false;
                input.removeAttribute('disabled');
                input.focus();
            }
            if (sendBtn) {
                sendBtn.disabled = false;
                sendBtn.removeAttribute('disabled');
            }
            
            // Load messages - handle both direct messages array and nested structure
            const messages = conversation.messages || [];
            if (messages && messages.length > 0) {
                messagesContainer.innerHTML = messages.map(msg => renderMessage(msg)).join('');
            } else {
                messagesContainer.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: var(--spacing-xl);">No messages yet. Start the conversation!</div>';
            }
            
            scrollToBottom();
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
        messagesContainer.innerHTML = '<div style="text-align: center; color: var(--text-error); padding: var(--spacing-xl);">Failed to load conversation</div>';
        // Still enable input on error
        if (input) {
            input.disabled = false;
            input.removeAttribute('disabled');
        }
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.removeAttribute('disabled');
        }
    }
}

// Render message
function renderMessage(message) {
    const isUser = message.role === 'user';
    const time = new Date(message.created_at).toLocaleTimeString();
    
    return `
        <div class="message ${message.role}">
            <div>
                <div class="message-content">
                    ${escapeHtml(message.content)}
                </div>
                <div class="message-time">${time}</div>
            </div>
        </div>
    `;
}

// Send message
async function handleSendMessage(event) {
    event.preventDefault();
    
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message || !currentConversationId) return;
    
    const sendBtn = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('chat-messages');
    
    // Add user message to UI immediately
    const userMessage = {
        role: 'user',
        content: message,
        created_at: new Date().toISOString()
    };
    
    if (messagesContainer.querySelector('.message')) {
        messagesContainer.innerHTML += renderMessage(userMessage);
    } else {
        messagesContainer.innerHTML = renderMessage(userMessage);
    }
    
    input.value = '';
    sendBtn.disabled = true;
    scrollToBottom();
    
    try {
        const response = await window.api.sendChatMessage(message, currentConversationId);
        
        if (response.status === 'success' && response.data) {
            // Add assistant response
            const assistantMessage = {
                role: 'assistant',
                content: response.data.response || response.data.message || 'I received your message.',
                created_at: new Date().toISOString()
            };
            
            messagesContainer.innerHTML += renderMessage(assistantMessage);
            scrollToBottom();
            
            // Reload conversations to update preview
            loadConversations();
        }
    } catch (error) {
        console.error('Error sending message:', error);
        const errorMessage = {
            role: 'assistant',
            content: `Error: ${error.message || 'Failed to send message. Please try again.'}`,
            created_at: new Date().toISOString()
        };
        messagesContainer.innerHTML += renderMessage(errorMessage);
        scrollToBottom();
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

// Scroll to bottom
function scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show alert - use centralized utility
function showAlert(type, message) {
    if (window.utils && window.utils.showAlert) {
        window.utils.showAlert(type, message);
    }
}

// Make functions available globally
window.createNewConversation = createNewConversation;
window.loadConversation = loadConversation;

