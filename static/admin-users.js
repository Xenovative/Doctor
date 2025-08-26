// Admin Users JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize user chart if data is available
    if (window.userData) {
        initializeUserChart();
    }
});

function initializeUserChart() {
    const ctx = document.getElementById('userActivityChart').getContext('2d');
    const activityData = window.userData.userStats ? window.userData.userStats.map(user => user[1]) : [];
    const userLabels = window.userData.userStats ? window.userData.userStats.map(user => user[0]) : [];
    
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: userLabels,
            datasets: [{
                label: '查詢次數',
                data: activityData,
                backgroundColor: function(context) {
                    const value = context.parsed.y;
                    if (value >= 10) return 'rgba(40, 167, 69, 0.8)';
                    if (value >= 3) return 'rgba(255, 193, 7, 0.8)';
                    return 'rgba(108, 117, 125, 0.8)';
                },
                borderColor: function(context) {
                    const value = context.parsed.y;
                    if (value >= 10) return 'rgba(40, 167, 69, 1)';
                    if (value >= 3) return 'rgba(255, 193, 7, 1)';
                    return 'rgba(108, 117, 125, 1)';
                },
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function viewUserDetails(userIp) {
    // Show loading state
    document.getElementById('userDetailsContent').innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">載入中...</span>
            </div>
            <p class="mt-2">載入用戶詳細信息...</p>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('userDetailsModal'));
    modal.show();
    
    // Fetch actual user details
    fetch(`/admin/api/user-details/${encodeURIComponent(userIp)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            let recentQueriesHtml = '';
            if (data.recent_queries && data.recent_queries.length > 0) {
                recentQueriesHtml = data.recent_queries.map(query => `
                    <div class="border-bottom pb-2 mb-2">
                        <small class="text-muted">${query.timestamp}</small>
                        <p class="mb-1"><strong>症狀:</strong> ${query.symptoms}</p>
                        <p class="mb-0"><strong>推薦專科:</strong> ${query.specialty || '無'}</p>
                    </div>
                `).join('');
            } else {
                recentQueriesHtml = '<div class="alert alert-info">暫無查詢記錄</div>';
            }
            
            document.getElementById('userDetailsContent').innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>基本信息</h6>
                        <p><strong>IP地址:</strong> ${userIp}</p>
                        <p><strong>地理位置:</strong> 香港</p>
                        <p><strong>設備類型:</strong> 桌面端</p>
                    </div>
                    <div class="col-md-6">
                        <h6>使用統計</h6>
                        <p><strong>總查詢數:</strong> ${data.total_queries}</p>
                        <p><strong>活躍天數:</strong> ${data.active_days} 天</p>
                        <p><strong>最常查詢專科:</strong> ${data.top_specialty}</p>
                    </div>
                </div>
                <hr>
                <h6>最近查詢記錄</h6>
                ${recentQueriesHtml}
            `;
        })
        .catch(error => {
            console.error('Error fetching user details:', error);
            document.getElementById('userDetailsContent').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    載入用戶詳細信息失敗: ${error.message}
                </div>
            `;
        });
}

function blockUser(userIp) {
    if (confirm(`確定要封鎖用戶 ${userIp} 嗎？`)) {
        // Implement user blocking functionality
        alert('用戶封鎖功能開發中...');
    }
}
