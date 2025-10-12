// LegalAssist Pro Browser Extension
class LegalAssistExtension {
    constructor() {
        this.apiUrls = [
            'https://legal-chatbot-ikpow5p6r-sankets-projects-34ae550b.vercel.app',  // Your deployed URL
            'http://127.0.0.1:5000',        // Local development
            'http://localhost:5000'         // Local development alternate
        ];
        
        this.currentApiUrl = null;
        this.chatHistory = [];
        this.isLoading = false;
        this.authToken = null;
        this.currentUser = null;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.findWorkingAPI();
        this.checkAuthStatus();
        this.updateStatus();
    }

    setupEventListeners() {
        // Send message on button click
        document.getElementById('sendButton').addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter (but allow Shift+Enter for new line)
        document.getElementById('messageInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        document.getElementById('messageInput').addEventListener('input', this.autoResize);
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
        const input = document.getElementById('messageInput');
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
            
            // Prepare headers
            const headers = { 'Content-Type': 'application/json' };
            if (this.authToken) {
                headers['Authorization'] = `Bearer ${this.authToken}`;
            }
            
            const response = await fetch(`${this.currentApiUrl}/api/chat`, {
                method: 'POST',
                headers: headers,
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
        
        // Remove welcome message when first message is sent
        const welcome = messagesContainer.querySelector('.welcome');
        if (welcome) {
            welcome.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Convert markdown-style formatting to HTML
        const formattedContent = this.formatMessage(content);
        messageContent.innerHTML = formattedContent;
        
        messageDiv.appendChild(messageContent);
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
        typingDiv.className = 'message assistant';
        typingDiv.id = 'typing-indicator';
        
        const typingContent = document.createElement('div');
        typingContent.className = 'loading';
        typingContent.innerHTML = `
            <span>LegalAssist is thinking</span>
            <div class="loading-dots">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        `;
        
        typingDiv.appendChild(typingContent);
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
        const messageInput = document.getElementById('messageInput');
        
        sendButton.disabled = loading;
        messageInput.disabled = loading;
        
        if (loading) {
            sendButton.innerHTML = '⏳';
            sendButton.style.opacity = '0.6';
        } else {
            sendButton.innerHTML = '▶';
            sendButton.style.opacity = '1';
            messageInput.focus();
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

    // Authentication methods
    checkAuthStatus() {
        chrome.storage.local.get(['authToken', 'currentUser'], (result) => {
            if (result.authToken && result.currentUser) {
                this.authToken = result.authToken;
                this.currentUser = result.currentUser;
                this.updateAuthUI();
            }
        });
    }

    updateAuthUI() {
        const authButtons = document.getElementById('authButtons');
        const userInfo = document.getElementById('userInfo');
        const userNameDisplay = document.getElementById('userNameDisplay');

        if (this.currentUser) {
            authButtons.style.display = 'none';
            userInfo.style.display = 'flex';
            userNameDisplay.textContent = this.currentUser.full_name || this.currentUser.username;
        } else {
            authButtons.style.display = 'flex';
            userInfo.style.display = 'none';
        }
    }

    async login(username, password) {
        try {
            const response = await fetch(`${this.currentApiUrl}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();

            if (result.success) {
                this.authToken = result.access_token;
                this.currentUser = result.user;
                
                // Store in extension storage
                chrome.storage.local.set({
                    authToken: this.authToken,
                    currentUser: this.currentUser
                });
                
                this.updateAuthUI();
                return { success: true };
            } else {
                return { success: false, error: result.error };
            }
        } catch (error) {
            return { success: false, error: 'Login failed. Please try again.' };
        }
    }

    async register(userData) {
        try {
            const response = await fetch(`${this.currentApiUrl}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });

            const result = await response.json();
            return result;
        } catch (error) {
            return { success: false, error: 'Registration failed. Please try again.' };
        }
    }

    async logout() {
        try {
            if (this.authToken) {
                await fetch(`${this.currentApiUrl}/api/auth/logout`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${this.authToken}` }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        }

        this.authToken = null;
        this.currentUser = null;
        chrome.storage.local.remove(['authToken', 'currentUser']);
        this.updateAuthUI();
        this.chatHistory = []; // Clear chat history on logout
    }
}

// Quick action functions
function askQuick(question) {
    const input = document.getElementById('messageInput');
    input.value = question;
    legalAssist.sendMessage();
}

// Clear chat function
function clearChat() {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = `
        <div class="welcome">
            <h3>👋 Welcome to LegalAssist Pro!</h3>
            <p>I'm here to help with your legal questions. Ask me about laws, rights, procedures, or get legal guidance.</p>
            <div class="quick-questions">
                <div class="quick-question" onclick="askQuick('What are my rights if I am arrested?')">
                    👮 What are my rights if I'm arrested?
                </div>
                <div class="quick-question" onclick="askQuick('How do I file a small claims case?')">
                    ⚖️ How do I file a small claims case?
                </div>
                <div class="quick-question" onclick="askQuick('What should I do after a car accident?')">
                    🚗 What should I do after a car accident?
                </div>
            </div>
        </div>
    `;
    
    // Clear chat history
    if (legalAssist) {
        legalAssist.chatHistory = [];
    }
}

// Authentication modal functions
function showAuth(type) {
    const overlay = document.getElementById('authModalOverlay');
    const content = document.getElementById('authModalContent');
    
    if (type === 'login') {
        content.innerHTML = `
            <h3>👤 Sign In</h3>
            <div id="authError" class="error-message" style="display: none;"></div>
            <form class="auth-form" onsubmit="handleAuth(event, 'login')">
                <div class="form-group">
                    <label>Username or Email</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="auth-submit">Sign In</button>
            </form>
            <div class="auth-toggle">
                Don't have an account? <a href="#" onclick="showAuth('register')">Register here</a>
            </div>
        `;
    } else {
        content.innerHTML = `
            <h3>➕ Create Account</h3>
            <div id="authError" class="error-message" style="display: none;"></div>
            <div id="authSuccess" class="success-message" style="display: none;"></div>
            <form class="auth-form" onsubmit="handleAuth(event, 'register')">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" required>
                </div>
                <div class="form-group">
                    <label>Full Name (Optional)</label>
                    <input type="text" name="full_name">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required minlength="6">
                </div>
                <div class="form-group">
                    <label>Confirm Password</label>
                    <input type="password" name="confirm_password" required>
                </div>
                <button type="submit" class="auth-submit">Create Account</button>
            </form>
            <div class="auth-toggle">
                Already have an account? <a href="#" onclick="showAuth('login')">Sign in here</a>
            </div>
        `;
    }
    
    overlay.style.display = 'block';
}

function closeAuthModal() {
    document.getElementById('authModalOverlay').style.display = 'none';
}

async function handleAuth(event, type) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const errorDiv = document.getElementById('authError');
    const successDiv = document.getElementById('authSuccess');
    
    // Clear previous messages
    if (errorDiv) errorDiv.style.display = 'none';
    if (successDiv) successDiv.style.display = 'none';
    
    if (type === 'login') {
        const result = await legalAssist.login(
            formData.get('username'),
            formData.get('password')
        );
        
        if (result.success) {
            closeAuthModal();
        } else {
            errorDiv.textContent = result.error;
            errorDiv.style.display = 'block';
        }
    } else {
        // Registration
        const password = formData.get('password');
        const confirmPassword = formData.get('confirm_password');
        
        if (password !== confirmPassword) {
            errorDiv.textContent = 'Passwords do not match';
            errorDiv.style.display = 'block';
            return;
        }
        
        const userData = {
            username: formData.get('username'),
            email: formData.get('email'),
            full_name: formData.get('full_name'),
            password: password
        };
        
        const result = await legalAssist.register(userData);
        
        if (result.success) {
            successDiv.textContent = 'Account created successfully! You can now sign in.';
            successDiv.style.display = 'block';
            form.reset();
            setTimeout(() => showAuth('login'), 2000);
        } else {
            errorDiv.textContent = result.error;
            errorDiv.style.display = 'block';
        }
    }
}

function logout() {
    legalAssist.logout();
}

function showChatHistory() {
    // TODO: Implement chat history modal
    alert('Chat history feature coming soon!');
}

// Initialize extension when DOM is loaded
let legalAssist;
document.addEventListener('DOMContentLoaded', () => {
    legalAssist = new LegalAssistExtension();
});