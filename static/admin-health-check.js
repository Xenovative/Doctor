// Admin Health Check System
class HealthCheckManager {
    constructor() {
        this.healthData = null;
        this.refreshInterval = null;
        this.toastContainer = null;
        this.init();
    }

    init() {
        this.createToastContainer();
        this.loadHealthStatus();
        this.startAutoRefresh();
        this.bindEvents();
    }

    createToastContainer() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('health-toast-container')) {
            const container = document.createElement('div');
            container.id = 'health-toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
            this.toastContainer = container;
        } else {
            this.toastContainer = document.getElementById('health-toast-container');
        }
    }

    async loadHealthStatus() {
        try {
            const response = await fetch('/admin/api/system-health');
            if (response.ok) {
                this.healthData = await response.json();
                this.updateHealthDisplay();
                this.checkForAlerts();
            } else {
                console.error('Failed to load health status:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading health status:', error);
        }
    }

    updateHealthDisplay() {
        if (!this.healthData) return;

        // Update health status cards if they exist
        const healthCards = document.querySelectorAll('.health-status-card');
        healthCards.forEach(card => {
            const component = card.dataset.component;
            const status = this.healthData.current_status[component];
            
            if (status) {
                this.updateHealthCard(card, status);
            }
        });

        // Update last check timestamp
        const lastUpdateElement = document.getElementById('health-last-update');
        if (lastUpdateElement) {
            const lastUpdate = new Date(this.healthData.last_updated);
            lastUpdateElement.textContent = `Last updated: ${lastUpdate.toLocaleString()}`;
        }
    }

    updateHealthCard(card, status) {
        const statusBadge = card.querySelector('.health-status-badge');
        const errorMessage = card.querySelector('.health-error-message');
        const responseTime = card.querySelector('.health-response-time');
        const lastCheck = card.querySelector('.health-last-check');

        // Update status badge
        if (statusBadge) {
            statusBadge.className = 'health-status-badge badge';
            statusBadge.textContent = status.status;
            
            switch (status.status) {
                case 'healthy':
                    statusBadge.classList.add('bg-success');
                    break;
                case 'unhealthy':
                    statusBadge.classList.add('bg-danger');
                    break;
                case 'disabled':
                    statusBadge.classList.add('bg-secondary');
                    break;
                default:
                    statusBadge.classList.add('bg-warning');
            }
        }

        // Update error message
        if (errorMessage) {
            if (status.error) {
                errorMessage.textContent = status.error;
                errorMessage.style.display = 'block';
            } else {
                errorMessage.style.display = 'none';
            }
        }

        // Update response time
        if (responseTime && status.response_time_ms) {
            responseTime.textContent = `${status.response_time_ms}ms`;
        }

        // Update last check time
        if (lastCheck && status.last_check) {
            const checkTime = new Date(status.last_check);
            lastCheck.textContent = checkTime.toLocaleString();
        }
    }

    checkForAlerts() {
        if (!this.healthData) return;

        const unhealthyComponents = [];
        Object.entries(this.healthData.current_status).forEach(([component, status]) => {
            if (status.status === 'unhealthy') {
                unhealthyComponents.push({
                    component,
                    error: status.error || 'Unknown error'
                });
            }
        });

        if (unhealthyComponents.length > 0) {
            this.showHealthAlert(unhealthyComponents);
        }
    }

    showHealthAlert(unhealthyComponents) {
        const alertId = 'health-alert-' + Date.now();
        
        let alertMessage = 'System Health Alert:\n';
        unhealthyComponents.forEach(comp => {
            alertMessage += `• ${comp.component}: ${comp.error}\n`;
        });

        this.showToast({
            id: alertId,
            title: '🚨 System Health Warning',
            message: alertMessage,
            type: 'danger',
            autoHide: false
        });
    }

    showToast({ id, title, message, type = 'info', autoHide = true, delay = 5000 }) {
        const toastHtml = `
            <div id="${id}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <strong>${title}</strong><br>
                        ${message.replace(/\n/g, '<br>')}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        this.toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(id);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: autoHide,
            delay: delay
        });
        
        toast.show();

        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    async runManualHealthCheck() {
        try {
            this.showToast({
                id: 'health-check-running',
                title: '🔄 Running Health Check',
                message: 'Please wait while we check system health...',
                type: 'info',
                autoHide: true,
                delay: 3000
            });

            const response = await fetch('/admin/api/run-health-check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const result = await response.json();
                
                // Reload health status after manual check
                setTimeout(() => {
                    this.loadHealthStatus();
                }, 1000);

                const passedChecks = Object.values(result.results).filter(r => r).length;
                const totalChecks = Object.keys(result.results).length;

                this.showToast({
                    id: 'health-check-complete',
                    title: '✅ Health Check Complete',
                    message: `${passedChecks}/${totalChecks} components are healthy`,
                    type: passedChecks === totalChecks ? 'success' : 'warning',
                    autoHide: true,
                    delay: 5000
                });
            } else {
                throw new Error('Failed to run health check');
            }
        } catch (error) {
            console.error('Manual health check failed:', error);
            this.showToast({
                id: 'health-check-error',
                title: '❌ Health Check Failed',
                message: 'Failed to run manual health check. Please try again.',
                type: 'danger',
                autoHide: true,
                delay: 5000
            });
        }
    }

    startAutoRefresh() {
        // Refresh health status every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadHealthStatus();
        }, 5 * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    bindEvents() {
        // Bind manual health check button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#run-health-check-btn')) {
                e.preventDefault();
                this.runManualHealthCheck();
            }
        });

        // Bind refresh button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#refresh-health-status-btn')) {
                e.preventDefault();
                this.loadHealthStatus();
            }
        });
    }

    destroy() {
        this.stopAutoRefresh();
        if (this.toastContainer) {
            this.toastContainer.remove();
        }
    }
}

// Initialize health check manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.admin-dashboard') || document.querySelector('.health-status-section')) {
        window.healthCheckManager = new HealthCheckManager();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.healthCheckManager) {
        window.healthCheckManager.destroy();
    }
});
