/**
 * Optional Authentication UI Component
 * Shows signup prompts to anonymous users while keeping app functional
 */

class OptionalAuthUI {
    constructor() {
        this.isAuthenticated = this.checkAuthStatus();
        this.init();
    }

    /**
     * Check if user is authenticated
     */
    checkAuthStatus() {
        const token = localStorage.getItem('access_token');
        return !!token;
    }

    /**
     * Initialize optional auth UI
     */
    init() {
        if (!this.isAuthenticated) {
            this.showSignupBanner();
            this.setupFeaturePrompts();
        }
    }

    /**
     * Show persistent signup banner for anonymous users
     */
    showSignupBanner() {
        const banner = document.createElement('div');
        banner.id = 'signup-banner';
        banner.className = 'signup-banner';
        banner.innerHTML = `
            <div class="signup-banner-content">
                <span class="signup-icon">📝</span>
                <span class="signup-message">
                    <strong>Try it free!</strong> Sign up to save your chat history and access premium features.
                </span>
                <div class="signup-actions">
                    <button class="btn-signup" onclick="window.location.href='/admin/register'">
                        Sign Up Free
                    </button>
                    <button class="btn-learn-more" onclick="optionalAuthUI.showFeatureComparison()">
                        Learn More
                    </button>
                    <button class="btn-close" onclick="optionalAuthUI.dismissBanner()">&times;</button>
                </div>
            </div>
        `;

        // Check if banner was dismissed
        const dismissed = sessionStorage.getItem('signup-banner-dismissed');
        if (dismissed) {
            return;
        }

        // Insert banner at top of page
        document.body.insertBefore(banner, document.body.firstChild);

        // Add styles
        this.addStyles();
    }

    /**
     * Dismiss the signup banner
     */
    dismissBanner() {
        const banner = document.getElementById('signup-banner');
        if (banner) {
            banner.style.animation = 'slideUp 0.3s ease-out';
            setTimeout(() => {
                banner.remove();
            }, 300);
            sessionStorage.setItem('signup-banner-dismissed', 'true');
        }
    }

    /**
     * Show feature comparison modal
     */
    showFeatureComparison() {
        const modal = document.createElement('div');
        modal.className = 'feature-modal';
        modal.innerHTML = `
            <div class="feature-modal-content">
                <button class="modal-close" onclick="this.closest('.feature-modal').remove()">&times;</button>
                <h2>🚀 Features Comparison</h2>
                <table class="feature-table">
                    <thead>
                        <tr>
                            <th>Feature</th>
                            <th>Anonymous</th>
                            <th>Registered</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>💬 Legal Chat</td>
                            <td>✅</td>
                            <td>✅</td>
                        </tr>
                        <tr>
                            <td>🔍 Case Search</td>
                            <td>✅</td>
                            <td>✅</td>
                        </tr>
                        <tr>
                            <td>📄 Document Analysis</td>
                            <td>✅</td>
                            <td>✅</td>
                        </tr>
                        <tr>
                            <td>🌐 Translation</td>
                            <td>✅</td>
                            <td>✅</td>
                        </tr>
                        <tr class="premium-row">
                            <td>💾 Save Chat History</td>
                            <td>❌</td>
                            <td>✅</td>
                        </tr>
                        <tr class="premium-row">
                            <td>📊 Personal Dashboard</td>
                            <td>❌</td>
                            <td>✅</td>
                        </tr>
                        <tr class="premium-row">
                            <td>⭐ Rate Responses</td>
                            <td>❌</td>
                            <td>✅</td>
                        </tr>
                        <tr class="premium-row">
                            <td>⚙️ Custom Preferences</td>
                            <td>❌</td>
                            <td>✅</td>
                        </tr>
                        <tr class="premium-row">
                            <td>📈 Advanced Analytics</td>
                            <td>❌</td>
                            <td>✅</td>
                        </tr>
                        <tr class="premium-row">
                            <td>🔄 Session Management</td>
                            <td>❌</td>
                            <td>✅</td>
                        </tr>
                    </tbody>
                </table>
                <div class="modal-footer">
                    <button class="btn-signup-large" onclick="window.location.href='/admin/register'">
                        Sign Up Free - Get Full Access
                    </button>
                    <p class="signup-note">✨ No credit card required • Free forever</p>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    /**
     * Setup prompts for premium features
     */
    setupFeaturePrompts() {
        // Intercept dashboard clicks
        const dashboardLinks = document.querySelectorAll('a[href="/dashboard"]');
        dashboardLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                if (!this.isAuthenticated) {
                    e.preventDefault();
                    this.showFeaturePrompt('Dashboard', 
                        'Access your personal dashboard with analytics and saved conversations.');
                }
            });
        });
    }

    /**
     * Show prompt when anonymous user tries to access premium feature
     */
    showFeaturePrompt(featureName, description) {
        const toast = document.createElement('div');
        toast.className = 'feature-prompt-toast';
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">🔒</span>
                <div class="toast-text">
                    <strong>${featureName}</strong>
                    <p>${description}</p>
                </div>
                <button class="toast-action" onclick="window.location.href='/admin/register'">
                    Sign Up Free
                </button>
            </div>
        `;

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    /**
     * Handle rating attempt by anonymous user
     */
    handleRatingAttempt() {
        this.showFeaturePrompt('Rate Responses', 
            'Sign up to rate responses and help us improve the AI assistant!');
    }

    /**
     * Add CSS styles
     */
    addStyles() {
        if (document.getElementById('optional-auth-styles')) {
            return; // Already added
        }

        const style = document.createElement('style');
        style.id = 'optional-auth-styles';
        style.textContent = `
            /* Signup Banner */
            .signup-banner {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 9999;
                animation: slideDown 0.3s ease-out;
            }

            .signup-banner-content {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                align-items: center;
                gap: 15px;
            }

            .signup-icon {
                font-size: 24px;
            }

            .signup-message {
                flex: 1;
                font-size: 14px;
            }

            .signup-message strong {
                font-weight: 600;
            }

            .signup-actions {
                display: flex;
                gap: 10px;
                align-items: center;
            }

            .btn-signup, .btn-learn-more {
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 14px;
            }

            .btn-signup {
                background: white;
                color: #667eea;
            }

            .btn-signup:hover {
                background: #f0f0f0;
                transform: translateY(-1px);
            }

            .btn-learn-more {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
            }

            .btn-learn-more:hover {
                background: rgba(255,255,255,0.3);
            }

            .btn-close {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                padding: 0 8px;
                opacity: 0.8;
            }

            .btn-close:hover {
                opacity: 1;
            }

            /* Feature Modal */
            .feature-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.2s;
            }

            .feature-modal-content {
                background: white;
                border-radius: 10px;
                padding: 30px;
                max-width: 600px;
                max-height: 90vh;
                overflow-y: auto;
                position: relative;
                animation: slideUp 0.3s ease-out;
            }

            .modal-close {
                position: absolute;
                top: 15px;
                right: 15px;
                background: none;
                border: none;
                font-size: 28px;
                cursor: pointer;
                color: #666;
            }

            .feature-modal-content h2 {
                margin-top: 0;
                color: #333;
                font-size: 24px;
            }

            .feature-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }

            .feature-table th {
                background: #f5f5f5;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                border-bottom: 2px solid #ddd;
            }

            .feature-table td {
                padding: 12px;
                border-bottom: 1px solid #eee;
            }

            .premium-row {
                background: #f9f9ff;
            }

            .modal-footer {
                text-align: center;
                margin-top: 20px;
            }

            .btn-signup-large {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 14px 32px;
                border-radius: 25px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
            }

            .btn-signup-large:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(102,126,234,0.4);
            }

            .signup-note {
                margin-top: 10px;
                color: #666;
                font-size: 14px;
            }

            /* Feature Prompt Toast */
            .feature-prompt-toast {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 5px 25px rgba(0,0,0,0.2);
                padding: 20px;
                max-width: 400px;
                z-index: 9999;
                animation: slideIn 0.3s ease-out;
            }

            .toast-content {
                display: flex;
                gap: 15px;
                align-items: flex-start;
            }

            .toast-icon {
                font-size: 24px;
            }

            .toast-text {
                flex: 1;
            }

            .toast-text strong {
                display: block;
                margin-bottom: 5px;
                color: #333;
            }

            .toast-text p {
                margin: 0;
                color: #666;
                font-size: 14px;
            }

            .toast-action {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: 500;
                cursor: pointer;
                white-space: nowrap;
            }

            .toast-action:hover {
                opacity: 0.9;
            }

            /* Animations */
            @keyframes slideDown {
                from {
                    transform: translateY(-100%);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }

            @keyframes slideUp {
                from {
                    transform: translateY(20px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }

            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            /* Mobile Responsive */
            @media (max-width: 768px) {
                .signup-banner-content {
                    flex-wrap: wrap;
                }

                .signup-actions {
                    width: 100%;
                    justify-content: space-between;
                }

                .feature-modal-content {
                    margin: 20px;
                    padding: 20px;
                }

                .feature-prompt-toast {
                    left: 20px;
                    right: 20px;
                    max-width: none;
                }
            }

            /* Adjust body padding when banner is shown */
            body.has-signup-banner {
                padding-top: 60px;
            }
        `;

        document.head.appendChild(style);

        // Add body class when banner is present
        if (!this.isAuthenticated) {
            document.body.classList.add('has-signup-banner');
        }
    }

    /**
     * Show notification when trying to access auth-required feature
     */
    showAuthRequiredNotification(feature) {
        const features = {
            'history': {
                title: 'Chat History',
                description: 'Sign up to save and access your conversation history across devices.'
            },
            'dashboard': {
                title: 'Dashboard',
                description: 'View your personal analytics, statistics, and saved conversations.'
            },
            'preferences': {
                title: 'Preferences',
                description: 'Customize your experience with personal settings and preferences.'
            },
            'rating': {
                title: 'Rate Responses',
                description: 'Help us improve by rating responses and providing feedback.'
            }
        };

        const info = features[feature] || {
            title: 'Premium Feature',
            description: 'This feature requires a free account.'
        };

        this.showFeaturePrompt(info.title, info.description);
    }
}

// Initialize on page load
let optionalAuthUI;
document.addEventListener('DOMContentLoaded', () => {
    optionalAuthUI = new OptionalAuthUI();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OptionalAuthUI;
}
