// Admin Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if data is available
    if (window.chartData) {
        initializeDashboardCharts();
    }
});

function initializeDashboardCharts() {
    // Process data for charts
    const dailyLabels = window.chartData.dailyStats ? window.chartData.dailyStats.map(stat => stat[0]) : [];
    const dailyData = window.chartData.dailyStats ? window.chartData.dailyStats.map(stat => stat[1]) : [];
    const specialtyLabels = window.chartData.specialtyStats ? window.chartData.specialtyStats.map(specialty => specialty[0]) : [];
    const specialtyData = window.chartData.specialtyStats ? window.chartData.specialtyStats.map(specialty => specialty[1]) : [];

    // Daily Chart
    const dailyCtx = document.getElementById('dailyChart').getContext('2d');
    const dailyChart = new Chart(dailyCtx, {
        type: 'line',
        data: {
            labels: dailyLabels,
            datasets: [{
                label: '查詢數',
                data: dailyData,
                borderColor: 'rgb(102, 126, 234)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Specialty Chart
    const specialtyCtx = document.getElementById('specialtyChart').getContext('2d');
    const specialtyChart = new Chart(specialtyCtx, {
        type: 'doughnut',
        data: {
            labels: specialtyLabels,
            datasets: [{
                data: specialtyData,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(23, 162, 184, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}
