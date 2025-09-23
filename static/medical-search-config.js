/**
 * Medical Search Configuration Management
 * Handles admin panel configuration for medical reference search APIs
 */

class MedicalSearchConfig {
    constructor() {
        this.config = {};
        this.init();
    }

    init() {
        this.loadConfiguration();
        this.bindEvents();
    }

    async loadConfiguration() {
        try {
            const response = await fetch('/admin/api/medical-search-config');
            const data = await response.json();
            
            if (data.success) {
                this.config = data.config;
                this.renderConfiguration();
            } else {
                console.error('Failed to load medical search configuration');
            }
        } catch (error) {
            console.error('Error loading medical search configuration:', error);
        }
    }

    renderConfiguration() {
        const container = document.getElementById('medicalSearchConfig');
        if (!container) return;

        let html = `
            <div class="config-section">
                <h4><i class="fas fa-search-plus"></i> 醫學參考搜尋設定</h4>
                <div class="config-grid">
        `;

        // Group configurations by category
        const categories = {
            'API Settings': ['primary_search_api', 'secondary_search_api', 'search_timeout'],
            'Search Parameters': ['articles_per_symptom', 'max_symptoms_processed', 'max_total_articles', 'pubmed_retmax'],
            'Advanced Options': ['search_filters', 'relevance_threshold', 'cache_duration'],
            'Future APIs': ['enable_cochrane', 'enable_google_scholar']
        };

        for (const [category, keys] of Object.entries(categories)) {
            html += `<div class="config-category">
                        <h5>${category}</h5>
                        <div class="config-items">`;

            keys.forEach(key => {
                if (this.config[key]) {
                    const config = this.config[key];
                    html += this.renderConfigItem(key, config);
                }
            });

            html += `</div></div>`;
        }

        html += `
                </div>
                <div class="config-actions">
                    <button type="button" class="btn btn-primary" onclick="medicalSearchConfig.saveConfiguration()">
                        <i class="fas fa-save"></i> 儲存設定
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="medicalSearchConfig.resetToDefaults()">
                        <i class="fas fa-undo"></i> 重置為預設值
                    </button>
                    <button type="button" class="btn btn-info" onclick="medicalSearchConfig.testConfiguration()">
                        <i class="fas fa-vial"></i> 測試設定
                    </button>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    renderConfigItem(key, config) {
        const { value, description, type } = config;
        
        let inputHtml = '';
        
        switch (type) {
            case 'select':
                if (key === 'primary_search_api' || key === 'secondary_search_api') {
                    inputHtml = `
                        <select class="form-control config-input" data-key="${key}">
                            <option value="pubmed" ${value === 'pubmed' ? 'selected' : ''}>PubMed</option>
                            <option value="cochrane" ${value === 'cochrane' ? 'selected' : ''}>Cochrane Library</option>
                            <option value="google_scholar" ${value === 'google_scholar' ? 'selected' : ''}>Google Scholar</option>
                            <option value="none" ${value === 'none' ? 'selected' : ''}>None</option>
                        </select>
                    `;
                }
                break;
            case 'number':
                inputHtml = `
                    <input type="number" class="form-control config-input" 
                           data-key="${key}" value="${value}" 
                           min="1" max="${key.includes('timeout') ? '60' : '20'}">
                `;
                break;
            case 'boolean':
                inputHtml = `
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input config-input" 
                               data-key="${key}" ${value ? 'checked' : ''}>
                        <label class="form-check-label">啟用</label>
                    </div>
                `;
                break;
            case 'text':
            default:
                inputHtml = `
                    <input type="text" class="form-control config-input" 
                           data-key="${key}" value="${value}">
                `;
                break;
        }

        return `
            <div class="config-item">
                <label class="config-label">
                    ${this.getDisplayName(key)}
                    <small class="text-muted">${description}</small>
                </label>
                ${inputHtml}
            </div>
        `;
    }

    getDisplayName(key) {
        const displayNames = {
            'primary_search_api': '主要搜尋API',
            'secondary_search_api': '備用搜尋API',
            'articles_per_symptom': '每症狀文章數',
            'max_symptoms_processed': '最大症狀處理數',
            'max_total_articles': '最大總文章數',
            'search_timeout': '搜尋逾時 (秒)',
            'pubmed_retmax': 'PubMed 搜尋限制',
            'enable_cochrane': '啟用 Cochrane',
            'enable_google_scholar': '啟用 Google Scholar',
            'search_filters': '搜尋過濾器',
            'relevance_threshold': '相關性門檻',
            'cache_duration': '快取持續時間 (秒)'
        };
        return displayNames[key] || key;
    }

    bindEvents() {
        // Auto-save on input change
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('config-input')) {
                this.updateConfigValue(e.target.dataset.key, e.target);
            }
        });
    }

    updateConfigValue(key, element) {
        let value;
        
        if (element.type === 'checkbox') {
            value = element.checked;
        } else if (element.type === 'number') {
            value = parseInt(element.value) || 0;
        } else {
            value = element.value;
        }

        // Update local config
        if (this.config[key]) {
            this.config[key].value = value;
        }

        // Show save indicator
        this.showSaveIndicator(key, 'pending');
    }

    async saveConfiguration() {
        const saveBtn = document.querySelector('.config-actions .btn-primary');
        const originalText = saveBtn.innerHTML;
        
        try {
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 儲存中...';
            saveBtn.disabled = true;

            // Save all configurations
            const promises = Object.keys(this.config).map(key => 
                this.saveConfigItem(key, this.config[key].value)
            );

            await Promise.all(promises);
            
            this.showNotification('設定已成功儲存', 'success');
            
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showNotification('儲存設定時發生錯誤', 'error');
        } finally {
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        }
    }

    async saveConfigItem(key, value) {
        const response = await fetch('/admin/api/medical-search-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                config_key: key,
                config_value: value
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to save ${key}`);
        }

        return response.json();
    }

    async resetToDefaults() {
        if (!confirm('確定要重置所有設定為預設值嗎？')) {
            return;
        }

        try {
            // Reset to default values
            const defaults = {
                'primary_search_api': 'pubmed',
                'secondary_search_api': 'none',
                'articles_per_symptom': 2,
                'max_symptoms_processed': 4,
                'max_total_articles': 8,
                'search_timeout': 10,
                'pubmed_retmax': 3,
                'enable_cochrane': false,
                'enable_google_scholar': false,
                'search_filters': 'clinical,diagnosis,treatment',
                'relevance_threshold': 0.5,
                'cache_duration': 3600
            };

            const promises = Object.entries(defaults).map(([key, value]) => 
                this.saveConfigItem(key, value)
            );

            await Promise.all(promises);
            
            // Reload configuration
            await this.loadConfiguration();
            
            this.showNotification('設定已重置為預設值', 'success');
            
        } catch (error) {
            console.error('Error resetting configuration:', error);
            this.showNotification('重置設定時發生錯誤', 'error');
        }
    }

    async testConfiguration() {
        const testBtn = document.querySelector('.config-actions .btn-info');
        const originalText = testBtn.innerHTML;
        
        try {
            testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 測試中...';
            testBtn.disabled = true;

            // Test with sample symptoms
            const testSymptoms = ['headache', 'nausea'];
            
            // This would call the medical evidence API to test current configuration
            const response = await fetch('/api/medical-evidence', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symptoms: testSymptoms
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`測試成功！找到 ${data.evidence.length} 篇文章`, 'success');
            } else {
                this.showNotification('測試失敗：無法獲取醫學參考', 'warning');
            }
            
        } catch (error) {
            console.error('Error testing configuration:', error);
            this.showNotification('測試設定時發生錯誤', 'error');
        } finally {
            testBtn.innerHTML = originalText;
            testBtn.disabled = false;
        }
    }

    showSaveIndicator(key, status) {
        const element = document.querySelector(`[data-key="${key}"]`);
        if (!element) return;

        element.classList.remove('config-saved', 'config-pending', 'config-error');
        element.classList.add(`config-${status}`);

        if (status === 'saved') {
            setTimeout(() => {
                element.classList.remove('config-saved');
            }, 2000);
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to page
        const container = document.querySelector('.container-fluid') || document.body;
        container.insertBefore(notification, container.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('medicalSearchConfig')) {
        window.medicalSearchConfig = new MedicalSearchConfig();
    }
});
