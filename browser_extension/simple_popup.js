// LegalAssist Pro Browser Extension
class LegalAssistExtension {
    constructor() {
        this.apiUrls = [
            'https://your-app.vercel.app',  // Replace with your deployed URL
            'https://your-app.netlify.app', // Replace with your deployed URL
            'http://127.0.0.1:5000',        // Local development
            'http://localhost:5000'         // Local development alternate
        ];
        
        this.currentApiUrl = null;
        this.chatHistory = [];
        this.isLoading = false;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.findWorkingAPI();
        this.updateStatus();
    }

    setupEventListeners() {
        // Send message on button click
        document.getElementById('sendButton').addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter (but allow Shift+Enter for new line)
        document.getElementById('userInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        document.getElementById('userInput').addEventListener('input', this.autoResize);
    }

    autoResize(e) {
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 80) + 'px';
    }

    async findWorkingAPI() {
        const statusText = document.getElementById('statusText');
        statusText.textContent = 'Connecting...';
        
        for (const url of this.apiUrls) {
            try {
                const response = await fetch(`${url}/api/health`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    signal: AbortSignal.timeout(5000) // 5 second timeout
                });
                
                if (response.ok) {
                    this.currentApiUrl = url;
                    statusText.textContent = 'Connected';
                    return;
                }
            } catch (error) {
                console.log(`Failed to connect to ${url}:`, error.message);
            }
        }
        
        statusText.textContent = 'Offline mode';
        this.showError('Unable to connect to legal assistant service. Please check your internet connection.');
    }

    updateStatus() {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.getElementById('statusText');
        
        if (this.currentApiUrl) {
            statusDot.style.background = '#27ae60';
            statusText.textContent = 'Ready to help';
        } else {
            statusDot.style.background = '#e74c3c';
            statusText.textContent = 'Connection failed';
        }
    }

    async sendMessage() {
        const input = document.getElementById('userInput');
        const message = input.value.trim();
        
        if (!message || this.isLoading) return;
        
        // Clear input and disable send button
        input.value = '';
        input.style.height = 'auto';
        this.setLoading(true);
        
        // Add user message to chat
        this.addMessage('user', message);
        
        try {
            if (!this.currentApiUrl) {
                await this.findWorkingAPI();
            }
            
            if (!this.currentApiUrl) {
                throw new Error('No API connection available');
            }
            
            // Show typing indicator
            this.showTyping();
            
            const response = await fetch(`${this.currentApiUrl}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    chat_history: this.chatHistory
                }),
                signal: AbortSignal.timeout(30000) // 30 second timeout
            });
            
            this.hideTyping();
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.response) {
                this.addMessage('assistant', data.response);
                
                // Update chat history
                this.chatHistory.push(
                    { role: 'user', content: message },
                    { role: 'assistant', content: data.response }
                );
                
                // Keep only last 10 messages
                if (this.chatHistory.length > 20) {
                    this.chatHistory = this.chatHistory.slice(-20);
                }
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
            
        } catch (error) {
            this.hideTyping();
            console.error('Chat error:', error);
            
            let errorMessage = 'I apologize, but I encountered an error. ';
            
            if (error.name === 'TimeoutError') {
                errorMessage += 'The request timed out. Please try again.';
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage += 'Unable to connect to the service. Please check your internet connection.';
            } else {
                errorMessage += 'Please try again later.';
            }
            
            this.addMessage('assistant', errorMessage);
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(role, content) {
        const messagesContainer = document.getElementById('messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        // Convert markdown-style formatting to HTML
        const formattedContent = this.formatMessage(content);
        messageDiv.innerHTML = formattedContent;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessage(content) {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold text
            .replace(/\n\n/g, '</p><p>') // Paragraph breaks
            .replace(/\n/g, '<br>') // Line breaks
            .replace(/^/, '<p>') // Start paragraph
            .replace(/$/, '</p>'); // End paragraph
    }

    showTyping() {
        const messagesContainer = document.getElementById('messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="loading">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTyping() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    setLoading(loading) {
        this.isLoading = loading;
        const sendButton = document.getElementById('sendButton');
        const userInput = document.getElementById('userInput');
        
        sendButton.disabled = loading;
        userInput.disabled = loading;
        
        if (loading) {
            sendButton.innerHTML = '⏳';
        } else {
            sendButton.innerHTML = '▶';
            userInput.focus();
        }
    }

    showError(message) {
        const messagesContainer = document.getElementById('messages');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        messagesContainer.appendChild(errorDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Quick action functions
function askQuick(question) {
    const input = document.getElementById('userInput');
    input.value = question;
    legalAssist.sendMessage();
}

// Initialize extension when DOM is loaded
let legalAssist;
document.addEventListener('DOMContentLoaded', () => {
    legalAssist = new LegalAssistExtension();
});