// Admin Console JavaScript for real-time log streaming
class AdminConsole {
    constructor() {
        this.autoScroll = true;
        this.eventSource = null;
        this.isStreaming = false;
        this.consoleBody = document.getElementById('consoleBody');
        this.autoScrollIcon = document.getElementById('autoScrollIcon');
        this.consoleToggleIcon = document.getElementById('consoleToggleIcon');
        
        this.initializeConsole();
        this.setupEventListeners();
    }

    initializeConsole() {
        // Load initial logs when console is opened
        const consoleWindow = document.getElementById('consoleWindow');
        if (consoleWindow) {
            consoleWindow.addEventListener('shown.bs.collapse', () => {
                this.loadInitialLogs();
                this.startStreaming();
                this.updateToggleIcon(true);
            });
            
            consoleWindow.addEventListener('hidden.bs.collapse', () => {
                this.stopStreaming();
                this.updateToggleIcon(false);
            });
        }
    }

    setupEventListeners() {
        // Auto-scroll toggle
        if (this.autoScrollIcon) {
            this.autoScrollIcon.parentElement.addEventListener('click', () => {
                this.toggleAutoScroll();
            });
        }
    }

    updateToggleIcon(isOpen) {
        if (this.consoleToggleIcon) {
            this.consoleToggleIcon.className = isOpen ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
        }
    }

    async loadInitialLogs() {
        try {
            this.showLoading();
            const response = await fetch('/admin/api/console-logs');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.clearConsole();
            
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(log => this.appendLogLine(log));
            } else {
                this.showEmptyState();
            }
            
        } catch (error) {
            console.error('Failed to load initial logs:', error);
            this.showError('Failed to load logs: ' + error.message);
        }
    }

    startStreaming() {
        if (this.isStreaming) return;
        
        try {
            this.eventSource = new EventSource('/admin/api/console-logs/stream');
            this.isStreaming = true;
            
            this.eventSource.onmessage = (event) => {
                try {
                    const log = JSON.parse(event.data);
                    this.appendLogLine(log);
                } catch (error) {
                    console.error('Failed to parse log data:', error);
                }
            };
            
            this.eventSource.onerror = (error) => {
                console.error('EventSource error:', error);
                this.stopStreaming();
                // Try to reconnect after 5 seconds
                setTimeout(() => {
                    if (document.getElementById('consoleWindow').classList.contains('show')) {
                        this.startStreaming();
                    }
                }, 5000);
            };
            
        } catch (error) {
            console.error('Failed to start streaming:', error);
            this.showError('Failed to start log streaming: ' + error.message);
        }
    }

    stopStreaming() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isStreaming = false;
    }

    appendLogLine(log) {
        const logLine = document.createElement('div');
        logLine.className = 'console-line';
        
        const timestamp = document.createElement('span');
        timestamp.className = 'log-timestamp';
        timestamp.textContent = log.timestamp;
        
        const level = document.createElement('span');
        level.className = `log-level-${log.level}`;
        level.textContent = `[${log.level}]`;
        
        const message = document.createElement('span');
        message.textContent = ` ${log.message}`;
        
        logLine.appendChild(timestamp);
        logLine.appendChild(level);
        logLine.appendChild(message);
        
        this.consoleBody.appendChild(logLine);
        
        // Remove old logs if too many (keep last 500)
        const lines = this.consoleBody.querySelectorAll('.console-line');
        if (lines.length > 500) {
            lines[0].remove();
        }
        
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }

    showLoading() {
        this.consoleBody.innerHTML = `
            <div class="console-loading text-center p-3">
                <i class="fas fa-spinner fa-spin me-2"></i>載入日誌中...
            </div>
        `;
    }

    showEmptyState() {
        this.consoleBody.innerHTML = `
            <div class="console-loading text-center p-3">
                <i class="fas fa-info-circle me-2"></i>暫無日誌記錄
            </div>
        `;
    }

    showError(message) {
        this.consoleBody.innerHTML = `
            <div class="console-line" style="color: #F44336;">
                <span class="log-timestamp">${new Date().toLocaleTimeString()}</span>
                <span class="log-level-ERROR">[ERROR]</span>
                <span> ${message}</span>
            </div>
        `;
    }

    clearConsole() {
        this.consoleBody.innerHTML = '';
    }

    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        
        if (this.autoScrollIcon) {
            this.autoScrollIcon.className = this.autoScroll ? 'fas fa-arrow-down' : 'fas fa-pause';
            this.autoScrollIcon.parentElement.title = this.autoScroll ? '停用自動滾動' : '啟用自動滾動';
        }
        
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }

    scrollToBottom() {
        this.consoleBody.scrollTop = this.consoleBody.scrollHeight;
    }

    refreshLogs() {
        this.stopStreaming();
        this.loadInitialLogs().then(() => {
            this.startStreaming();
        });
    }
}

// Global functions for button onclick handlers
function clearConsole() {
    if (window.adminConsole) {
        window.adminConsole.clearConsole();
    }
}

function toggleAutoScroll() {
    if (window.adminConsole) {
        window.adminConsole.toggleAutoScroll();
    }
}

function refreshLogs() {
    if (window.adminConsole) {
        window.adminConsole.refreshLogs();
    }
}

// Initialize console when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if console elements exist (super admin only)
    if (document.getElementById('consoleBody')) {
        window.adminConsole = new AdminConsole();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.adminConsole) {
        window.adminConsole.stopStreaming();
    }
});
