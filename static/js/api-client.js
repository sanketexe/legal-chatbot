/**
 * Legal Chatbot - API Client & Utilities
 * Centralized JavaScript library for all API interactions
 */

// ============================================================================
// AUTHENTICATION & TOKEN MANAGEMENT
// ============================================================================

class AuthManager {
    constructor() {
        this.TOKEN_KEY = 'legal_chatbot_token';
        this.USER_KEY = 'legal_chatbot_user';
    }

    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    }

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    removeToken() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    }

    setUser(user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }

    getUser() {
        const userData = localStorage.getItem(this.USER_KEY);
        return userData ? JSON.parse(userData) : null;
    }

    isAuthenticated() {
        return !!this.getToken();
    }

    getAuthHeaders() {
        const token = this.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }
}

const authManager = new AuthManager();

// ============================================================================
// API CLIENT
// ============================================================================

class APIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...authManager.getAuthHeaders(),
                ...options.headers
            }
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    // GET request
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    // POST request
    async post(endpoint, body) {
        return this.request(endpoint, { method: 'POST', body });
    }

    // PATCH request
    async patch(endpoint, body) {
        return this.request(endpoint, { method: 'PATCH', body });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

const api = new APIClient();

// ============================================================================
// UX ENHANCEMENTS API - CONVERSATIONS
// ============================================================================

const ConversationsAPI = {
    // List all conversations
    async list(page = 1, perPage = 20) {
        return api.get('/ux/conversations', { page, per_page: perPage });
    },

    // Get a specific conversation
    async get(conversationId) {
        return api.get(`/ux/conversations/${conversationId}`);
    },

    // Create a new conversation
    async create(title = null) {
        return api.post('/ux/conversations', { title });
    },

    // Update conversation
    async update(conversationId, updates) {
        return api.patch(`/ux/conversations/${conversationId}`, updates);
    },

    // Delete conversation (soft delete)
    async delete(conversationId) {
        return api.delete(`/ux/conversations/${conversationId}`);
    },

    // Add message to conversation
    async addMessage(conversationId, role, content) {
        return api.post(`/ux/conversations/${conversationId}/messages`, {
            role,
            content
        });
    }
};

// ============================================================================
// UX ENHANCEMENTS API - BOOKMARKS
// ============================================================================

const BookmarksAPI = {
    // List bookmarks with optional filters
    async list(filters = {}) {
        return api.get('/ux/bookmarks', filters);
    },

    // Create a bookmark
    async create(bookmarkData) {
        return api.post('/ux/bookmarks', bookmarkData);
    },

    // Update bookmark
    async update(bookmarkId, updates) {
        return api.patch(`/ux/bookmarks/${bookmarkId}`, updates);
    },

    // Delete bookmark
    async delete(bookmarkId) {
        return api.delete(`/ux/bookmarks/${bookmarkId}`);
    },

    // Record bookmark access
    async recordAccess(bookmarkId) {
        return api.post(`/ux/bookmarks/${bookmarkId}/access`);
    }
};

// ============================================================================
// UX ENHANCEMENTS API - EXPORTS
// ============================================================================

const ExportsAPI = {
    // Export conversation
    async exportConversation(conversationId, format = 'pdf') {
        return api.post(`/ux/export/conversation/${conversationId}`, { format });
    },

    // Get export history
    async getHistory() {
        return api.get('/ux/export/history');
    }
};

// ============================================================================
// AI ENHANCEMENTS API
// ============================================================================

const AIEnhancementsAPI = {
    // Case Outcome Prediction
    async predictCaseOutcome(predictionData) {
        return api.post('/ai/predict', predictionData);
    },

    // Document Drafting
    async listTemplates() {
        return api.get('/ai/document/templates');
    },

    async getTemplate(templateId) {
        return api.get(`/ai/document/template/${templateId}`);
    },

    async draftDocument(draftData) {
        return api.post('/ai/document/draft', draftData);
    },

    async exportDocument(exportData) {
        return api.post('/ai/document/export', exportData);
    },

    // Research Summarization
    async summarizeResearch(query, maxCases = 10) {
        return api.post('/ai/research/summarize', { query, max_cases: maxCases });
    },

    async generateResearchMemo(query, cases = null) {
        return api.post('/ai/research/memo', { query, cases });
    },

    // Health check
    async checkHealth() {
        return api.get('/ai/health');
    }
};

// ============================================================================
// UI UTILITIES
// ============================================================================

const UIUtils = {
    // Show notification
    showNotification(message, type = 'info', duration = 3000) {
        const container = document.getElementById('notification-container') || this.createNotificationContainer();
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${this.getNotificationIcon(type)}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('notification-show');
        }, 10);
        
        if (duration > 0) {
            setTimeout(() => {
                notification.classList.remove('notification-show');
                setTimeout(() => notification.remove(), 300);
            }, duration);
        }
    },

    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
        return container;
    },

    getNotificationIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    },

    // Show loading spinner
    showLoading(element, message = 'Loading...') {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.innerHTML = `
            <div class="spinner"></div>
            <p class="loading-message">${message}</p>
        `;
        element.innerHTML = '';
        element.appendChild(spinner);
    },

    // Hide loading spinner
    hideLoading(element) {
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    },

    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Format relative time (e.g., "2 hours ago")
    formatRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
        
        return this.formatDate(dateString);
    },

    // Truncate text
    truncateText(text, maxLength = 100) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    // Show modal
    showModal(title, content, buttons = []) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <div class="modal-body">${content}</div>
                <div class="modal-footer">
                    ${buttons.map(btn => `
                        <button class="btn btn-${btn.type || 'secondary'}" onclick="${btn.onclick}">
                            ${btn.label}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('modal-show'), 10);
    },

    // Close modal
    closeModal() {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.classList.remove('modal-show');
            setTimeout(() => modal.remove(), 300);
        }
    },

    // Confirm dialog
    confirm(message, onConfirm, onCancel = null) {
        this.showModal('Confirm', `<p>${message}</p>`, [
            {
                label: 'Cancel',
                type: 'secondary',
                onclick: `UIUtils.closeModal(); ${onCancel ? `(${onCancel})()` : ''}`
            },
            {
                label: 'Confirm',
                type: 'primary',
                onclick: `UIUtils.closeModal(); (${onConfirm})()`
            }
        ]);
    },

    // Copy to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            this.showNotification('Failed to copy to clipboard', 'error');
        }
    },

    // Download file
    downloadFile(content, filename, mimeType = 'text/plain') {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
};

// ============================================================================
// EXPORT UTILITIES
// ============================================================================

const ExportUtils = {
    async showExportModal(conversationId) {
        const formats = ['pdf', 'docx', 'txt', 'json'];
        
        UIUtils.showModal('Export Conversation', `
            <p>Select export format:</p>
            <div class="export-format-grid">
                ${formats.map(format => `
                    <button class="export-format-btn" data-format="${format}" 
                            onclick="ExportUtils.exportConversation('${conversationId}', '${format}')">
                        <span class="format-icon">${this.getFormatIcon(format)}</span>
                        <span class="format-name">${format.toUpperCase()}</span>
                    </button>
                `).join('')}
            </div>
        `, [{
            label: 'Cancel',
            type: 'secondary',
            onclick: 'UIUtils.closeModal()'
        }]);
    },

    async exportConversation(conversationId, format) {
        UIUtils.closeModal();
        UIUtils.showNotification(`Exporting as ${format.toUpperCase()}...`, 'info');
        
        try {
            const result = await ExportsAPI.exportConversation(conversationId, format);
            UIUtils.showNotification(`Export successful! File: ${result.file_name}`, 'success', 5000);
            
            // Optionally trigger download
            if (result.file_path) {
                window.location.href = result.file_path;
            }
        } catch (error) {
            UIUtils.showNotification(`Export failed: ${error.message}`, 'error');
        }
    },

    getFormatIcon(format) {
        const icons = {
            pdf: '📄',
            docx: '📝',
            txt: '📃',
            json: '{ }'
        };
        return icons[format] || '📁';
    }
};

// ============================================================================
// BOOKMARK UTILITIES
// ============================================================================

const BookmarkUtils = {
    async showBookmarkModal(itemType, itemId, itemTitle, itemContent = null) {
        const folders = ['General', 'Important', 'Research', 'Cases', 'Queries'];
        
        UIUtils.showModal('Create Bookmark', `
            <form id="bookmark-form" onsubmit="event.preventDefault(); BookmarkUtils.createBookmark()">
                <div class="form-group">
                    <label>Title</label>
                    <input type="text" id="bookmark-title" class="form-control" 
                           value="${itemTitle}" required>
                </div>
                <div class="form-group">
                    <label>Folder</label>
                    <select id="bookmark-folder" class="form-control">
                        ${folders.map(f => `<option value="${f}">${f}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Tags (comma-separated)</label>
                    <input type="text" id="bookmark-tags" class="form-control" 
                           placeholder="e.g., contract, employment, important">
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="bookmark-favorite"> Mark as favorite
                    </label>
                </div>
                <input type="hidden" id="bookmark-type" value="${itemType}">
                <input type="hidden" id="bookmark-id" value="${itemId}">
                <input type="hidden" id="bookmark-content" value="${itemContent || ''}">
            </form>
        `, [
            {
                label: 'Cancel',
                type: 'secondary',
                onclick: 'UIUtils.closeModal()'
            },
            {
                label: 'Create Bookmark',
                type: 'primary',
                onclick: 'document.getElementById("bookmark-form").requestSubmit()'
            }
        ]);
    },

    async createBookmark() {
        const title = document.getElementById('bookmark-title').value;
        const folder = document.getElementById('bookmark-folder').value;
        const tags = document.getElementById('bookmark-tags').value.split(',').map(t => t.trim()).filter(t => t);
        const isFavorite = document.getElementById('bookmark-favorite').checked;
        const itemType = document.getElementById('bookmark-type').value;
        const itemId = document.getElementById('bookmark-id').value;
        const itemContent = document.getElementById('bookmark-content').value;

        try {
            await BookmarksAPI.create({
                item_type: itemType,
                item_id: itemId,
                title: title,
                content: itemContent || null,
                folder: folder,
                tags: tags,
                is_favorite: isFavorite
            });

            UIUtils.closeModal();
            UIUtils.showNotification('Bookmark created successfully!', 'success');
            
            // Reload bookmarks if on bookmarks page
            if (typeof loadBookmarks === 'function') {
                loadBookmarks();
            }
        } catch (error) {
            UIUtils.showNotification(`Failed to create bookmark: ${error.message}`, 'error');
        }
    }
};

// ============================================================================
// INITIALIZE ON PAGE LOAD
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Check authentication status
    if (authManager.isAuthenticated()) {
        const user = authManager.getUser();
        if (user) {
            // Update UI with user info
            const userInfoElements = document.querySelectorAll('.user-info');
            userInfoElements.forEach(el => {
                el.textContent = user.username || user.email || 'User';
            });
        }
    }

    // Add global error handler for API calls
    window.addEventListener('unhandledrejection', (event) => {
        if (event.reason && event.reason.message) {
            console.error('Unhandled API error:', event.reason);
        }
    });
});

// Export to global scope
window.authManager = authManager;
window.api = api;
window.ConversationsAPI = ConversationsAPI;
window.BookmarksAPI = BookmarksAPI;
window.ExportsAPI = ExportsAPI;
window.AIEnhancementsAPI = AIEnhancementsAPI;
window.UIUtils = UIUtils;
window.ExportUtils = ExportUtils;
window.BookmarkUtils = BookmarkUtils;
