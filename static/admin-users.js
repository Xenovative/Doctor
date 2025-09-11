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

function viewUserReports(userIp) {
    // Show loading state
    document.getElementById('userReportsContent').innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">載入中...</span>
            </div>
            <p class="mt-2">載入診斷報告...</p>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('userReportsModal'));
    modal.show();
    
    // Fetch user diagnosis reports
    fetch(`/admin/api/user-reports/${encodeURIComponent(userIp)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            let reportsHtml = '';
            if (data.reports && data.reports.length > 0) {
                reportsHtml = data.reports.map(report => `
                    <div class="card mb-3">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">診斷報告 #${report.id}</h6>
                            <small class="text-muted">${report.timestamp}</small>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>患者信息</h6>
                                    <p><strong>年齡:</strong> ${report.age}歲</p>
                                    <p><strong>生理性別:</strong> ${report.gender || '未提供'}</p>
                                    <p><strong>症狀:</strong> ${report.symptoms}</p>
                                    <p><strong>慢性疾病:</strong> ${report.chronic_conditions || '無'}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>診斷結果</h6>
                                    <p><strong>推薦專科:</strong> ${report.specialty}</p>
                                    <p><strong>緊急程度:</strong> ${report.emergency_level}</p>
                                    <p><strong>語言:</strong> ${report.language}</p>
                                    <p><strong>地區:</strong> ${report.location}</p>
                                </div>
                            </div>
                            ${report.diagnosis_report ? `
                                <hr>
                                <h6>完整診斷報告</h6>
                                <div class="bg-light p-3 rounded">
                                    <pre style="white-space: pre-wrap; font-family: inherit;">${report.diagnosis_report}</pre>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `).join('');
            } else {
                reportsHtml = '<div class="alert alert-info">暫無診斷報告記錄</div>';
            }
            
            document.getElementById('userReportsContent').innerHTML = `
                <div class="mb-3">
                    <h6>用戶 ${userIp} 的診斷報告 (共 ${data.reports ? data.reports.length : 0} 筆)</h6>
                </div>
                ${reportsHtml}
            `;
        })
        .catch(error => {
            console.error('Error fetching user reports:', error);
            document.getElementById('userReportsContent').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    載入診斷報告失敗: ${error.message}
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
