/**
 * Theme Switcher JavaScript
 * Handles dynamic theme switching functionality
 */

class ThemeSwitcher {
    constructor() {
        this.currentTheme = this.getStoredTheme() || 'auto';
        this.init();
    }

    init() {
        // Apply initial theme
        this.applyTheme(this.currentTheme);
        
        // Set up theme selector change handler
        const themeSelector = document.getElementById('theme-selector');
        if (themeSelector) {
            themeSelector.value = this.currentTheme;
            themeSelector.addEventListener('change', (e) => {
                this.changeTheme(e.target.value);
            });
        }

        // Listen for system theme changes (for auto theme)
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener((e) => {
                if (this.currentTheme === 'auto') {
                    this.applyTheme('auto');
                }
            });
        }

        // Add theme change handler for settings form
        this.setupThemeFormHandler();
    }

    changeTheme(theme) {
        this.currentTheme = theme;
        this.applyTheme(theme);
        this.storeTheme(theme);
        this.showThemeChangeNotification(theme);
    }

    applyTheme(theme) {
        // Remove existing theme classes
        document.body.classList.remove('theme-light', 'theme-dark', 'theme-auto');
        
        // Add new theme class
        document.body.classList.add(`theme-${theme}`);
        
        // Set data-theme attribute for CSS variables
        document.body.setAttribute('data-theme', theme);
        
        // Apply theme to all cards
        document.querySelectorAll('.card').forEach(card => {
            card.setAttribute('data-theme', theme);
        });
        
        // Apply theme to navbar
        document.querySelectorAll('.navbar').forEach(navbar => {
            navbar.setAttribute('data-theme', theme);
        });
        
        // Apply theme to sidebar
        document.querySelectorAll('.sidebar').forEach(sidebar => {
            sidebar.setAttribute('data-theme', theme);
        });
        
        // Apply theme to form controls
        document.querySelectorAll('.form-control').forEach(control => {
            control.setAttribute('data-theme', theme);
        });
        
        // Apply theme to tables
        document.querySelectorAll('.table').forEach(table => {
            table.setAttribute('data-theme', theme);
        });

        // Update theme selector if it exists
        const themeSelector = document.getElementById('theme-selector');
        if (themeSelector) {
            themeSelector.value = theme;
        }

        // Update theme icon in settings
        this.updateThemeIcon(theme);
    }

    getStoredTheme() {
        try {
            return localStorage.getItem('xwepo-theme');
        } catch (e) {
            return 'light';
        }
    }

    storeTheme(theme) {
        try {
            localStorage.setItem('xwepo-theme', theme);
        } catch (e) {
            console.warn('Could not save theme preference:', e);
        }
    }

    updateThemeIcon(theme) {
        // Update theme icon in settings page
        const themeIcon = document.querySelector('.setting-item .fas');
        if (themeIcon) {
            switch (theme) {
                case 'light':
                    themeIcon.className = 'fas fa-sun me-2 text-primary';
                    break;
                case 'dark':
                    themeIcon.className = 'fas fa-moon me-2 text-primary';
                    break;
                case 'auto':
                    themeIcon.className = 'fas fa-adjust me-2 text-primary';
                    break;
            }
        }

        // Theme toggle button removed - theme switching only available in settings
    }

    showThemeChangeNotification(theme) {
        // Create a temporary notification
        const notification = document.createElement('div');
        notification.className = 'theme-change-notification';
        
        // Get appropriate icon for notification
        let iconClass = 'fas fa-sun';
        switch (theme) {
            case 'light':
                iconClass = 'fas fa-sun';
                break;
            case 'dark':
                iconClass = 'fas fa-moon';
                break;
            case 'auto':
                iconClass = 'fas fa-adjust';
                break;
        }
        
        notification.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                <i class="${iconClass} me-2"></i>
                Theme changed to <strong>${theme.charAt(0).toUpperCase() + theme.slice(1)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    setupThemeFormHandler() {
        const themeForm = document.getElementById('theme-form');
        if (themeForm) {
            themeForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(themeForm);
                const theme = formData.get('theme');
                
                if (theme && theme !== this.currentTheme) {
                    this.changeTheme(theme);
                }
            });
        }
    }

    // Public method to get current theme
    getCurrentTheme() {
        return this.currentTheme;
    }

    // Public method to set theme programmatically
    setTheme(theme) {
        if (['light', 'dark', 'auto'].includes(theme)) {
            this.changeTheme(theme);
        }
    }
}

// Initialize theme switcher when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.themeSwitcher = new ThemeSwitcher();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeSwitcher;
}
