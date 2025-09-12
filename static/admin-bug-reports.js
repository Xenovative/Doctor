// Bug Reports Admin Management
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

function refreshReports() {
    location.reload();
}

function markAllAsRead() {
    if (confirm('確定要將所有新問題標記為已讀嗎？')) {
        const newReports = document.querySelectorAll('[data-status="new"]');
        newReports.forEach(report => {
            const reportId = report.getAttribute('data-id');
            updateStatus(reportId, 'in-progress', false);
        });
        
        setTimeout(() => {
            location.reload();
        }, 1000);
    }
}

function updateStatus(reportId, newStatus, showConfirm = true) {
    if (showConfirm) {
        const statusText = {
            'new': '新問題',
            'in-progress': '處理中',
            'resolved': '已解決'
        };
        
        if (!confirm(`確定要將此問題標記為「${statusText[newStatus]}」嗎？`)) {
            return;
        }
    }
    
    fetch(`/admin/api/bug-reports/${reportId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            if (showConfirm) {
                setTimeout(() => location.reload(), 1000);
            }
        } else {
            showNotification(data.error || '更新失敗', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('網絡錯誤', 'error');
    });
}

function deleteReport(reportId) {
    if (!confirm('確定要刪除此問題回報嗎？此操作無法撤銷。')) {
        return;
    }
    
    fetch(`/admin/api/bug-reports/${reportId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(data.error || '刪除失敗', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('網絡錯誤', 'error');
    });
}

function filterReports() {
    const statusFilter = document.getElementById('statusFilter').value;
    const dateFilter = document.getElementById('dateFilter').value;
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    
    const reports = document.querySelectorAll('.bug-report-card');
    
    reports.forEach(report => {
        let showReport = true;
        
        // Status filter
        if (statusFilter !== 'all') {
            const reportStatus = report.getAttribute('data-status');
            if (reportStatus !== statusFilter) {
                showReport = false;
            }
        }
        
        // Date filter
        if (dateFilter !== 'all' && showReport) {
            const reportDate = new Date(report.getAttribute('data-date'));
            const now = new Date();
            
            switch (dateFilter) {
                case 'today':
                    if (reportDate.toDateString() !== now.toDateString()) {
                        showReport = false;
                    }
                    break;
                case 'week':
                    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    if (reportDate < weekAgo) {
                        showReport = false;
                    }
                    break;
                case 'month':
                    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                    if (reportDate < monthAgo) {
                        showReport = false;
                    }
                    break;
            }
        }
        
        // Search filter
        if (searchInput && showReport) {
            const description = report.querySelector('.bug-description').textContent.toLowerCase();
            if (!description.includes(searchInput)) {
                showReport = false;
            }
        }
        
        report.style.display = showReport ? 'block' : 'none';
    });
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotification = document.querySelector('.admin-notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} admin-notification`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.3s ease-out;
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
`;
document.head.appendChild(style);
