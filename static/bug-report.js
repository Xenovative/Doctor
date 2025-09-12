// Bug Report Modal Functionality
document.addEventListener('DOMContentLoaded', function() {
    const bugReportBtn = document.getElementById('bugReportBtn');
    const bugReportModal = document.getElementById('bugReportModal');
    const closeBugModal = document.getElementById('closeBugModal');
    const cancelBugReport = document.getElementById('cancelBugReport');
    const bugReportForm = document.getElementById('bugReportForm');

    // Open modal
    bugReportBtn.addEventListener('click', function() {
        bugReportModal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    });

    // Close modal functions
    function closeModal() {
        bugReportModal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore scrolling
        bugReportForm.reset(); // Clear form
    }

    closeBugModal.addEventListener('click', closeModal);
    cancelBugReport.addEventListener('click', closeModal);

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === bugReportModal) {
            closeModal();
        }
    });

    // Handle form submission
    bugReportForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = bugReportForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        // Show loading state
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span data-translate="sending">發送中...</span>';
        submitBtn.disabled = true;

        const formData = new FormData(bugReportForm);
        const bugData = {
            description: formData.get('bugDescription'),
            contact: formData.get('contactInfo') || '未提供',
            timestamp: new Date().toLocaleString('zh-HK'),
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        try {
            const response = await fetch('/submit-bug-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bugData)
            });

            const result = await response.json();

            if (response.ok) {
                // Success
                showNotification('問題回報已成功發送！我們會盡快處理。', 'success');
                closeModal();
            } else {
                // Error
                showNotification(result.error || '發送失敗，請稍後再試。', 'error');
            }
        } catch (error) {
            console.error('Error submitting bug report:', error);
            showNotification('網絡錯誤，請檢查連接後重試。', 'error');
        } finally {
            // Restore button state
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });

    // Notification system
    function showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);

        // Allow manual close
        notification.addEventListener('click', () => {
            notification.remove();
        });
    }

    // Add notification styles dynamically
    const notificationStyles = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 3000;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            cursor: pointer;
            animation: slideInRight 0.3s ease-out;
            max-width: 400px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }

        .notification-success {
            background: linear-gradient(135deg, #28a745, #20c997);
        }

        .notification-error {
            background: linear-gradient(135deg, #dc3545, #fd7e14);
        }

        .notification-info {
            background: linear-gradient(135deg, #17a2b8, #6f42c1);
        }

        .notification-content {
            display: flex;
            align-items: center;
            gap: 10px;
        }

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

        @media (max-width: 768px) {
            .notification {
                top: 10px;
                right: 10px;
                left: 10px;
                max-width: none;
            }
        }
    `;

    // Inject styles
    const styleSheet = document.createElement('style');
    styleSheet.textContent = notificationStyles;
    document.head.appendChild(styleSheet);
});
