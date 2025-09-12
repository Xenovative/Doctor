// Timestamp formatting utility for frontend
class TimestampFormatter {
    constructor() {
        this.timezone = 'Asia/Hong_Kong';
    }
    
    /**
     * Format timestamp string to clean readable format
     * @param {string} timestampStr - Raw timestamp string
     * @returns {string} - Formatted timestamp
     */
    format(timestampStr) {
        try {
            if (!timestampStr) return 'N/A';
            
            let date;
            
            // Handle different timestamp formats
            if (timestampStr.includes('T') || timestampStr.includes('+')) {
                // ISO format
                date = new Date(timestampStr);
            } else {
                // Simple format
                date = new Date(timestampStr);
            }
            
            // Check if date is valid
            if (isNaN(date.getTime())) {
                return timestampStr; // Return original if can't parse
            }
            
            // Format to Hong Kong timezone
            const options = {
                timeZone: this.timezone,
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            };
            
            return date.toLocaleString('zh-HK', options);
            
        } catch (error) {
            console.error('Error formatting timestamp:', error);
            return timestampStr;
        }
    }
    
    /**
     * Format timestamp to relative time (e.g., "2 hours ago")
     * @param {string} timestampStr - Raw timestamp string
     * @returns {string} - Relative time string
     */
    formatRelative(timestampStr) {
        try {
            const date = new Date(timestampStr);
            const now = new Date();
            const diffMs = now - date;
            const diffSecs = Math.floor(diffMs / 1000);
            const diffMins = Math.floor(diffSecs / 60);
            const diffHours = Math.floor(diffMins / 60);
            const diffDays = Math.floor(diffHours / 24);
            
            if (diffSecs < 60) return '剛剛';
            if (diffMins < 60) return `${diffMins}分鐘前`;
            if (diffHours < 24) return `${diffHours}小時前`;
            if (diffDays < 7) return `${diffDays}天前`;
            
            // For older dates, return formatted date
            return this.format(timestampStr);
            
        } catch (error) {
            console.error('Error formatting relative timestamp:', error);
            return this.format(timestampStr);
        }
    }
    
    /**
     * Format all timestamps in a container
     * @param {HTMLElement} container - Container element
     * @param {string} selector - CSS selector for timestamp elements
     */
    formatAllInContainer(container, selector = '.timestamp') {
        const timestampElements = container.querySelectorAll(selector);
        timestampElements.forEach(element => {
            const originalTimestamp = element.textContent || element.getAttribute('data-timestamp');
            if (originalTimestamp) {
                element.textContent = this.format(originalTimestamp);
                element.setAttribute('title', originalTimestamp); // Keep original as tooltip
            }
        });
    }
}

// Global instance
window.timestampFormatter = new TimestampFormatter();

// Auto-format timestamps when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Format all elements with timestamp class
    window.timestampFormatter.formatAllInContainer(document);
    
    // Format table cells that look like timestamps
    const tableCells = document.querySelectorAll('td');
    tableCells.forEach(cell => {
        const text = cell.textContent.trim();
        // Check if it looks like a timestamp
        if (text.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/) || 
            text.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/)) {
            cell.textContent = window.timestampFormatter.format(text);
            cell.setAttribute('title', text); // Keep original as tooltip
        }
    });
});
