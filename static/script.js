document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('patientForm');
    const results = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const doctorList = document.getElementById('doctorList');
    const diagnosisResult = document.getElementById('diagnosisResult');
    
    // Location cascade data with coordinates for geolocation matching
    const locationData = {
        '香港島': {
            '中西區': ['中環', '上環', '西環', '金鐘', '堅尼地城', '石塘咀', '西營盤'],
            '東區': ['銅鑼灣', '天后', '炮台山', '北角', '鰂魚涌', '西灣河', '筲箕灣', '柴灣', '小西灣'],
            '南區': ['香港仔', '鴨脷洲', '黃竹坑', '深水灣', '淺水灣', '赤柱', '石澳'],
            '灣仔區': ['灣仔', '跑馬地', '大坑', '渣甸山', '寶馬山']
        },
        '九龍': {
            '九龍城區': ['九龍城', '土瓜灣', '馬頭角', '馬頭圍', '啟德', '紅磡', '何文田'],
            '觀塘區': ['觀塘', '牛頭角', '九龍灣', '彩虹', '坪石', '秀茂坪', '藍田', '油塘'],
            '深水埗區': ['深水埗', '長沙灣', '荔枝角', '美孚', '石硤尾', '又一村'],
            '黃大仙區': ['黃大仙', '新蒲崗', '樂富', '橫頭磡', '東頭', '竹園', '慈雲山', '鑽石山'],
            '油尖旺區': ['油麻地', '尖沙咀', '旺角', '大角咀', '太子', '佐敦']
        },
        '新界': {
            '離島區': ['長洲', '南丫島', '坪洲', '大嶼山', '東涌', '愉景灣'],
            '葵青區': ['葵涌', '青衣', '葵芳', '荔景'],
            '北區': ['上水', '粉嶺', '打鼓嶺', '沙頭角', '鹿頸'],
            '西貢區': ['西貢', '將軍澳', '坑口', '調景嶺', '寶林', '康盛花園'],
            '沙田區': ['沙田', '大圍', '火炭', '馬鞍山', '烏溪沙'],
            '大埔區': ['大埔', '太和', '大埔墟', '林村', '汀角'],
            '荃灣區': ['荃灣', '梨木樹', '象山', '城門'],
            '屯門區': ['屯門', '友愛', '安定', '山景', '大興', '良景', '建生'],
            '元朗區': ['元朗', '天水圍', '洪水橋', '流浮山', '錦田', '八鄉']
        }
    };

    // Area coordinates for precise geolocation matching
    const areaCoordinates = {
        // 中西區
        '中環': { lat: 22.2810, lng: 114.1577, district: '中西區' },
        '上環': { lat: 22.2866, lng: 114.1506, district: '中西區' },
        '西環': { lat: 22.2855, lng: 114.1286, district: '中西區' },
        '金鐘': { lat: 22.2783, lng: 114.1647, district: '中西區' },
        '堅尼地城': { lat: 22.2816, lng: 114.1256, district: '中西區' },
        '石塘咀': { lat: 22.2855, lng: 114.1356, district: '中西區' },
        '西營盤': { lat: 22.2855, lng: 114.1406, district: '中西區' },
        
        // 東區
        '銅鑼灣': { lat: 22.2783, lng: 114.1847, district: '東區' },
        '天后': { lat: 22.2833, lng: 114.1947, district: '東區' },
        '炮台山': { lat: 22.2883, lng: 114.2047, district: '東區' },
        '北角': { lat: 22.2933, lng: 114.2097, district: '東區' },
        '鰂魚涌': { lat: 22.2983, lng: 114.2197, district: '東區' },
        '西灣河': { lat: 22.2833, lng: 114.2297, district: '東區' },
        '筲箕灣': { lat: 22.2783, lng: 114.2397, district: '東區' },
        '柴灣': { lat: 22.2683, lng: 114.2497, district: '東區' },
        '小西灣': { lat: 22.2633, lng: 114.2597, district: '東區' },
        
        // 南區
        '香港仔': { lat: 22.2461, lng: 114.1628, district: '南區' },
        '鴨脷洲': { lat: 22.2411, lng: 114.1578, district: '南區' },
        '黃竹坑': { lat: 22.2511, lng: 114.1728, district: '南區' },
        '深水灣': { lat: 22.2361, lng: 114.1878, district: '南區' },
        '淺水灣': { lat: 22.2311, lng: 114.1978, district: '南區' },
        '赤柱': { lat: 22.2161, lng: 114.2078, district: '南區' },
        '石澳': { lat: 22.2011, lng: 114.2278, district: '南區' },
        
        // 灣仔區
        '灣仔': { lat: 22.2783, lng: 114.1747, district: '灣仔區' },
        '跑馬地': { lat: 22.2733, lng: 114.1847, district: '灣仔區' },
        '大坑': { lat: 22.2833, lng: 114.1897, district: '灣仔區' },
        '渣甸山': { lat: 22.2883, lng: 114.1947, district: '灣仔區' },
        '寶馬山': { lat: 22.2933, lng: 114.1997, district: '灣仔區' },
        
        // 九龍城區
        '九龍城': { lat: 22.3193, lng: 114.1847, district: '九龍城區' },
        '土瓜灣': { lat: 22.3143, lng: 114.1797, district: '九龍城區' },
        '馬頭角': { lat: 22.3093, lng: 114.1747, district: '九龍城區' },
        '馬頭圍': { lat: 22.3043, lng: 114.1697, district: '九龍城區' },
        '啟德': { lat: 22.3243, lng: 114.1997, district: '九龍城區' },
        '紅磡': { lat: 22.3043, lng: 114.1847, district: '九龍城區' },
        '何文田': { lat: 22.3143, lng: 114.1747, district: '九龍城區' },
        
        // 觀塘區
        '觀塘': { lat: 22.3193, lng: 114.2267, district: '觀塘區' },
        '牛頭角': { lat: 22.3143, lng: 114.2217, district: '觀塘區' },
        '九龍灣': { lat: 22.3243, lng: 114.2167, district: '觀塘區' },
        '彩虹': { lat: 22.3293, lng: 114.2017, district: '觀塘區' },
        '坪石': { lat: 22.3343, lng: 114.1967, district: '觀塘區' },
        '秀茂坪': { lat: 22.3393, lng: 114.2117, district: '觀塘區' },
        '藍田': { lat: 22.3043, lng: 114.2367, district: '觀塘區' },
        '油塘': { lat: 22.2993, lng: 114.2417, district: '觀塘區' },
        
        // 深水埗區
        '深水埗': { lat: 22.3303, lng: 114.1627, district: '深水埗區' },
        '長沙灣': { lat: 22.3353, lng: 114.1577, district: '深水埗區' },
        '荔枝角': { lat: 22.3403, lng: 114.1527, district: '深水埗區' },
        '美孚': { lat: 22.3453, lng: 114.1377, district: '深水埗區' },
        '石硤尾': { lat: 22.3353, lng: 114.1677, district: '深水埗區' },
        '又一村': { lat: 22.3403, lng: 114.1727, district: '深水埗區' },
        
        // 黃大仙區
        '黃大仙': { lat: 22.3423, lng: 114.1937, district: '黃大仙區' },
        '新蒲崗': { lat: 22.3373, lng: 114.1887, district: '黃大仙區' },
        '樂富': { lat: 22.3473, lng: 114.1837, district: '黃大仙區' },
        '橫頭磡': { lat: 22.3523, lng: 114.1787, district: '黃大仙區' },
        '東頭': { lat: 22.3573, lng: 114.1737, district: '黃大仙區' },
        '竹園': { lat: 22.3623, lng: 114.1687, district: '黃大仙區' },
        '慈雲山': { lat: 22.3673, lng: 114.1987, district: '黃大仙區' },
        '鑽石山': { lat: 22.3423, lng: 114.2037, district: '黃大仙區' },
        
        // 油尖旺區
        '油麻地': { lat: 22.3053, lng: 114.1693, district: '油尖旺區' },
        '尖沙咀': { lat: 22.2953, lng: 114.1743, district: '油尖旺區' },
        '旺角': { lat: 22.3153, lng: 114.1693, district: '油尖旺區' },
        '大角咀': { lat: 22.3203, lng: 114.1643, district: '油尖旺區' },
        '太子': { lat: 22.3253, lng: 114.1693, district: '油尖旺區' },
        '佐敦': { lat: 22.3003, lng: 114.1743, district: '油尖旺區' },
        
        // 離島區
        '長洲': { lat: 22.2097, lng: 114.0297, district: '離島區' },
        '南丫島': { lat: 22.2147, lng: 114.1347, district: '離島區' },
        '坪洲': { lat: 22.2897, lng: 114.0447, district: '離島區' },
        '大嶼山': { lat: 22.2597, lng: 113.9427, district: '離島區' },
        '東涌': { lat: 22.2897, lng: 113.9427, district: '離島區' },
        '愉景灣': { lat: 22.2647, lng: 114.0027, district: '離島區' },
        
        // 葵青區
        '葵涌': { lat: 22.3573, lng: 114.1287, district: '葵青區' },
        '青衣': { lat: 22.3473, lng: 114.1087, district: '葵青區' },
        '葵芳': { lat: 22.3623, lng: 114.1237, district: '葵青區' },
        '荔景': { lat: 22.3523, lng: 114.1187, district: '葵青區' },
        
        // 北區
        '上水': { lat: 22.4953, lng: 114.1287, district: '北區' },
        '粉嶺': { lat: 22.4903, lng: 114.1387, district: '北區' },
        '打鼓嶺': { lat: 22.5253, lng: 114.1587, district: '北區' },
        '沙頭角': { lat: 22.5453, lng: 114.2087, district: '北區' },
        '鹿頸': { lat: 22.5353, lng: 114.2387, district: '北區' },
        
        // 西貢區
        '西貢': { lat: 22.3143, lng: 114.2677, district: '西貢區' },
        '將軍澳': { lat: 22.3043, lng: 114.2577, district: '西貢區' },
        '坑口': { lat: 22.2943, lng: 114.2677, district: '西貢區' },
        '調景嶺': { lat: 22.3143, lng: 114.2477, district: '西貢區' },
        '寶林': { lat: 22.3243, lng: 114.2577, district: '西貢區' },
        '康盛花園': { lat: 22.3043, lng: 114.2377, district: '西貢區' },
        
        // 沙田區
        '沙田': { lat: 22.3823, lng: 114.1977, district: '沙田區' },
        '大圍': { lat: 22.3723, lng: 114.1827, district: '沙田區' },
        '火炭': { lat: 22.3973, lng: 114.1827, district: '沙田區' },
        '馬鞍山': { lat: 22.4273, lng: 114.2327, district: '沙田區' },
        '烏溪沙': { lat: 22.4373, lng: 114.2427, district: '沙田區' },
        
        // 大埔區
        '大埔': { lat: 22.4453, lng: 114.1647, district: '大埔區' },
        '太和': { lat: 22.4553, lng: 114.1597, district: '大埔區' },
        '大埔墟': { lat: 22.4403, lng: 114.1697, district: '大埔區' },
        '林村': { lat: 22.4303, lng: 114.1447, district: '大埔區' },
        '汀角': { lat: 22.4653, lng: 114.1897, district: '大埔區' },
        
        // 荃灣區
        '荃灣': { lat: 22.3693, lng: 114.1147, district: '荃灣區' },
        '梨木樹': { lat: 22.3793, lng: 114.1047, district: '荃灣區' },
        '象山': { lat: 22.3643, lng: 114.1097, district: '荃灣區' },
        '城門': { lat: 22.3743, lng: 114.1197, district: '荃灣區' },
        
        // 屯門區
        '屯門': { lat: 22.3913, lng: 113.9767, district: '屯門區' },
        '友愛': { lat: 22.3863, lng: 113.9717, district: '屯門區' },
        '安定': { lat: 22.3963, lng: 113.9817, district: '屯門區' },
        '山景': { lat: 22.4013, lng: 113.9867, district: '屯門區' },
        '大興': { lat: 22.4063, lng: 113.9917, district: '屯門區' },
        '良景': { lat: 22.4113, lng: 113.9967, district: '屯門區' },
        '建生': { lat: 22.4163, lng: 114.0017, district: '屯門區' },
        
        // 元朗區
        '元朗': { lat: 22.4453, lng: 114.0347, district: '元朗區' },
        '天水圍': { lat: 22.4653, lng: 114.0047, district: '元朗區' },
        '洪水橋': { lat: 22.4253, lng: 114.0147, district: '元朗區' },
        '流浮山': { lat: 22.4753, lng: 113.9947, district: '元朗區' },
        '錦田': { lat: 22.4353, lng: 114.0547, district: '元朗區' },
        '八鄉': { lat: 22.4153, lng: 114.0747, district: '元朗區' }
    };

    // District coordinates for fallback (approximate centers)
    const districtCoordinates = {
        '中西區': { lat: 22.2855, lng: 114.1577 },
        '東區': { lat: 22.2783, lng: 114.2367 },
        '南區': { lat: 22.2461, lng: 114.1628 },
        '灣仔區': { lat: 22.2783, lng: 114.1747 },
        '九龍城區': { lat: 22.3193, lng: 114.1847 },
        '觀塘區': { lat: 22.3193, lng: 114.2267 },
        '深水埗區': { lat: 22.3303, lng: 114.1627 },
        '黃大仙區': { lat: 22.3423, lng: 114.1937 },
        '油尖旺區': { lat: 22.3053, lng: 114.1693 },
        '離島區': { lat: 22.2587, lng: 113.9427 },
        '葵青區': { lat: 22.3573, lng: 114.1287 },
        '北區': { lat: 22.4953, lng: 114.1287 },
        '西貢區': { lat: 22.3143, lng: 114.2677 },
        '沙田區': { lat: 22.3823, lng: 114.1977 },
        '大埔區': { lat: 22.4453, lng: 114.1647 },
        '荃灣區': { lat: 22.3693, lng: 114.1147 },
        '屯門區': { lat: 22.3913, lng: 113.9767 },
        '元朗區': { lat: 22.4453, lng: 114.0347 }
    };

    // Geolocation functionality
    let userLocation = null;
    let geolocationAttempted = false;
    
    // Calculate distance between two coordinates using Haversine formula
    function calculateDistance(lat1, lng1, lat2, lng2) {
        const R = 6371; // Earth's radius in kilometers
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLng = (lng2 - lng1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    // Find closest area based on user's coordinates (with fallback to district)
    function findClosestLocation(userLat, userLng) {
        let closestArea = null;
        let closestDistrict = null;
        let closestRegion = null;
        let minDistance = Infinity;

        // First try to find closest specific area
        for (const [area, coords] of Object.entries(areaCoordinates)) {
            const distance = calculateDistance(userLat, userLng, coords.lat, coords.lng);
            if (distance < minDistance) {
                minDistance = distance;
                closestArea = area;
                closestDistrict = coords.district;
                
                // Find which region this district belongs to
                for (const [region, districts] of Object.entries(locationData)) {
                    if (districts.hasOwnProperty(closestDistrict)) {
                        closestRegion = region;
                        break;
                    }
                }
            }
        }

        // If no area found within reasonable distance, fallback to district matching
        if (minDistance > 5) { // 5km threshold
            minDistance = Infinity;
            closestArea = null;
            
            for (const [district, coords] of Object.entries(districtCoordinates)) {
                const distance = calculateDistance(userLat, userLng, coords.lat, coords.lng);
                if (distance < minDistance) {
                    minDistance = distance;
                    closestDistrict = district;
                    
                    // Find which region this district belongs to
                    for (const [region, districts] of Object.entries(locationData)) {
                        if (districts.hasOwnProperty(district)) {
                            closestRegion = region;
                            break;
                        }
                    }
                }
            }
        }

        return { 
            region: closestRegion, 
            district: closestDistrict, 
            area: closestArea,
            distance: minDistance 
        };
    }

    // Track if user has manually selected location
    let userHasSelectedLocation = false;
    
    // Auto-select location based on geolocation (including area)
    function autoSelectLocation(region, district, area = null) {
        const regionSelect = document.getElementById('region');
        const districtSelect = document.getElementById('district');
        const areaSelect = document.getElementById('area');
        
        // Only auto-select if no location is currently selected AND user hasn't manually selected
        if (regionSelect.value || userHasSelectedLocation) return;
        
        setTimeout(() => {
            regionSelect.value = region;
            regionSelect.dispatchEvent(new Event('change'));
            
            setTimeout(() => {
                districtSelect.value = district;
                districtSelect.dispatchEvent(new Event('change'));
                
                if (area) {
                    setTimeout(() => {
                        areaSelect.value = area;
                        areaSelect.dispatchEvent(new Event('change'));
                        
                        // Show success message with area
                        const message = translateText('geolocation_auto_selected') || '已自動選擇您附近的地區';
                        showLocationMessage(`${message}：${region} - ${district} - ${area}`, 'success');
                    }, 200);
                } else {
                    // Show success message without area
                    const message = translateText('geolocation_auto_selected') || '已自動選擇您附近的地區';
                    showLocationMessage(`${message}：${region} - ${district}`, 'success');
                }
            }, 100);
        }, 100);
    }

    // Show location message
    function showLocationMessage(message, type = 'info') {
        const existingMessage = document.querySelector('.location-message');
        if (existingMessage) {
            existingMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `location-message alert alert-${type === 'success' ? 'success' : 'info'}`;
        messageDiv.style.cssText = `
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            background-color: ${type === 'success' ? '#d4edda' : '#d1ecf1'};
            border: 1px solid ${type === 'success' ? '#c3e6cb' : '#bee5eb'};
            color: ${type === 'success' ? '#155724' : '#0c5460'};
            font-size: 14px;
        `;
        messageDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            ${message}
        `;

        const locationSection = document.querySelector('.form-group:has(#region)') || 
                               document.querySelector('#region').closest('.form-group');
        if (locationSection) {
            locationSection.appendChild(messageDiv);
            
            // Auto-remove message after 5 seconds
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, 5000);
        }
    }

    // Request geolocation
    function requestGeolocation() {
        if (geolocationAttempted || !navigator.geolocation) {
            return;
        }
        
        geolocationAttempted = true;
        
        const options = {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000 // 5 minutes
        };

        navigator.geolocation.getCurrentPosition(
            function(position) {
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                const closest = findClosestLocation(userLocation.lat, userLocation.lng);
                if (closest.region && closest.district) {
                    autoSelectLocation(closest.region, closest.district, closest.area);
                }
            },
            function(error) {
                console.log('Geolocation error:', error);
                let errorMessage = translateText('geolocation_error') || '無法獲取您的位置';
                
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = translateText('geolocation_permission_denied') || '位置權限被拒絕，請手動選擇地區';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = translateText('geolocation_unavailable') || '位置信息不可用，請手動選擇地區';
                        break;
                    case error.TIMEOUT:
                        errorMessage = translateText('geolocation_timeout') || '獲取位置超時，請手動選擇地區';
                        break;
                }
                
                showLocationMessage(errorMessage, 'info');
            },
            options
        );
    }

    // Location cascade handlers
    const regionSelect = document.getElementById('region');
    const districtSelect = document.getElementById('district');
    const areaSelect = document.getElementById('area');

    // Auto-request geolocation when page loads
    setTimeout(() => {
        requestGeolocation();
    }, 1000);
    
    areaSelect.addEventListener('change', function() {
        // Mark that user has manually selected location
        if (this.value) {
            userHasSelectedLocation = true;
        }
    });    

    regionSelect.addEventListener('change', function() {
        const selectedRegion = this.value;
        
        // Mark that user has manually selected location
        if (selectedRegion) {
            userHasSelectedLocation = true;
        }
        
        // Reset and hide subsequent dropdowns
        const districtPlaceholder = window.currentTranslations && window.currentTranslations['select_district'] 
            ? window.currentTranslations['select_district'] : '請選擇地區';
        const areaPlaceholder = window.currentTranslations && window.currentTranslations['select_area'] 
            ? window.currentTranslations['select_area'] : '請選擇具體位置 (可選)';
            
        districtSelect.innerHTML = `<option value="" data-translate="select_district">${districtPlaceholder}</option>`;
        areaSelect.innerHTML = `<option value="" data-translate="select_area">${areaPlaceholder}</option>`;
        districtSelect.style.display = 'none';
        areaSelect.style.display = 'none';
        
        if (selectedRegion && locationData[selectedRegion]) {
            // Populate district dropdown
            Object.keys(locationData[selectedRegion]).forEach(district => {
                const option = document.createElement('option');
                option.value = district;
                option.setAttribute('data-translate', district);
                
                // Use current translation if available
                if (window.currentTranslations && window.currentTranslations[district]) {
                    option.textContent = window.currentTranslations[district];
                } else {
                    option.textContent = district;
                }
                
                districtSelect.appendChild(option);
            });
            districtSelect.style.display = 'block';
        }
    });
    
    districtSelect.addEventListener('change', function() {
        const selectedRegion = regionSelect.value;
        const selectedDistrict = this.value;
        
        // Mark that user has manually selected location
        if (selectedDistrict) {
            userHasSelectedLocation = true;
        }
        
        // Reset and hide area dropdown
        const areaPlaceholder = window.currentTranslations && window.currentTranslations['select_area'] 
            ? window.currentTranslations['select_area'] : '請選擇具體位置 (可選)';
            
        areaSelect.innerHTML = `<option value="" data-translate="select_area">${areaPlaceholder}</option>`;
        areaSelect.style.display = 'none';
        
        if (selectedRegion && selectedDistrict && locationData[selectedRegion][selectedDistrict]) {
            // Populate area dropdown
            locationData[selectedRegion][selectedDistrict].forEach(area => {
                const option = document.createElement('option');
                option.value = area;
                option.setAttribute('data-translate', area);
                
                // Use current translation if available
                if (window.currentTranslations && window.currentTranslations[area]) {
                    option.textContent = window.currentTranslations[area];
                } else {
                    option.textContent = area;
                }
                
                areaSelect.appendChild(option);
            });
            areaSelect.style.display = 'block';
        }
    });
    
    // 處理「其他」選項的顯示/隱藏
    const otherCheckbox = document.getElementById('other-condition-checkbox');
    const otherInput = document.getElementById('other-condition-input');
    
    if (otherCheckbox && otherInput) {
        otherCheckbox.addEventListener('change', function() {
            if (this.checked) {
                otherInput.style.display = 'block';
                document.getElementById('other-condition-text').focus();
            } else {
                otherInput.style.display = 'none';
                document.getElementById('other-condition-text').value = '';
            }
        });
    }
    
    // 處理「更多資料」按鈕的展開/收縮
    const moreInfoBtn = document.getElementById('more-info-btn');
    const moreInfoSection = document.getElementById('more-info-section');
    
    if (moreInfoBtn && moreInfoSection) {
        moreInfoBtn.addEventListener('click', function() {
            const isVisible = moreInfoSection.style.display !== 'none';
            
            if (isVisible) {
                moreInfoSection.style.display = 'none';
                this.classList.remove('expanded');
                const moreText = translateText('more_info');
                this.innerHTML = `<i class="fas fa-plus-circle"></i> ${moreText}`;
            } else {
                moreInfoSection.style.display = 'block';
                this.classList.add('expanded');
                const lessText = translateText('less_info');
                this.innerHTML = `<i class="fas fa-minus-circle"></i> ${lessText}`;
            }
        });
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const age = document.getElementById('age').value;
        const gender = document.getElementById('gender').value;
        const symptoms = document.getElementById('symptoms').value;
        const language = document.getElementById('language').value;
        
        // Collect 3-tier location data
        const region = document.getElementById('region').value;
        const district = document.getElementById('district').value;
        const area = document.getElementById('area').value;
        
        // Create location string for backend compatibility
        const location = area || district || region;
        
        // 收集長期病史複選框數據
        const chronicConditions = (function() {
            const checkboxes = document.querySelectorAll('input[name="chronic-condition"]:checked');
            const conditions = [];
            
            checkboxes.forEach(checkbox => {
                if (checkbox.value === '其他') {
                    const otherText = document.getElementById('other-condition-text').value.trim();
                    if (otherText) {
                        conditions.push(otherText);
                    }
                } else {
                    conditions.push(checkbox.value);
                }
            });
            
            return conditions.join('、');
        })();
        
        // 驗證症狀數量 - 使用新的tag系統
        if (!validateSymptoms(symptoms)) {
            alert('請至少輸入3個症狀，以便 AI 進行準確分析。');
            return;
        }

        // 收集詳細健康信息
        const detailedHealthInfo = (function() {
            const height = document.getElementById('height').value;
            const weight = document.getElementById('weight').value;
            const medications = document.getElementById('medications').value;
            const allergies = document.getElementById('allergies').value;
            const surgeries = document.getElementById('surgeries').value;
            
            const bloodThinner = document.getElementById('blood-thinner').checked;
            const recentVisit = document.getElementById('recent-visit').checked;
            const cpapMachine = document.getElementById('cpap-machine').checked;
            const looseTeeth = document.getElementById('loose-teeth').checked;
            
            return {
                height: height,
                weight: weight,
                medications: medications,
                allergies: allergies,
                surgeries: surgeries,
                bloodThinner: bloodThinner,
                recentVisit: recentVisit,
                cpapMachine: cpapMachine,
                looseTeeth: looseTeeth
            };
        })();
        
        // Get current UI language from language manager
        const currentUILanguage = window.languageManager ? window.languageManager.currentLang : 'zh-TW';
        
        // 收集表單數據
        const formData = {
            age: age,
            gender: gender,
            symptoms: symptoms,
            chronicConditions: chronicConditions,
            language: language,
            location: location,
            locationDetails: {
                region: region,
                district: district,
                area: area
            },
            detailedHealthInfo: detailedHealthInfo,
            uiLanguage: currentUILanguage  // Add UI language for diagnosis
        };

        // Check for severe symptoms first
        if (window.severeWarningSystem) {
            const severeCheck = await window.severeWarningSystem.checkSevereSymptoms(formData);
            
            if (severeCheck.is_severe) {
                // Show severe warning modal and wait for user decision
                window.severeWarningSystem.showWarning(severeCheck, formData, proceedWithDiagnosis);
                return; // Stop here, let user decide
            }
        }
        
        // If no severe symptoms detected, proceed with normal diagnosis
        await proceedWithDiagnosis(formData);
    });
    
    // Function to handle the actual diagnosis request
    async function proceedWithDiagnosis(formData) {
        // 顯示載入動畫
        loading.style.display = 'block';
        results.style.display = 'none';

        try {
            // Debug logging
            console.log('Sending formData:', formData);
            console.log('FormData keys:', Object.keys(formData));
            console.log('FormData values:', {
                age: formData.age,
                symptoms: formData.symptoms,
                language: formData.language,
                location: formData.location
            });
            
            // Validate required fields before sending
            if (!formData.age || formData.age <= 0) {
                throw new Error('年齡是必填項目且必須大於0');
            }
            if (!formData.symptoms || formData.symptoms.trim() === '') {
                throw new Error('症狀是必填項目');
            }
            if (!formData.language || formData.language.trim() === '') {
                throw new Error('語言是必填項目');
            }
            if (!formData.location || formData.location.trim() === '') {
                throw new Error('地區是必填項目');
            }
            
            // 發送請求到後端
            const response = await fetch('/find_doctor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                // Try to get the error message from the server
                let errorMessage = '網絡請求失敗';
                let responseText = '';
                try {
                    responseText = await response.text();
                    console.log('Raw server response:', responseText);
                    const errorData = JSON.parse(responseText);
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    console.error('Could not parse server error response:', e);
                    console.log('Raw response text:', responseText);
                    errorMessage = `服務器錯誤 (${response.status}): ${responseText || '未知錯誤'}`;
                }
                console.error('Server error:', response.status, errorMessage);
                throw new Error(errorMessage);
            }

            const data = await response.json();
            
            // 隱藏載入動畫
            loading.style.display = 'none';
            
            // 檢查是否有症狀驗證錯誤
            if (data.validation_error) {
                showValidationError(data);
                return;
            }
            
            // 顯示結果
            displayResults(data);
            
        } catch (error) {
            console.error('錯誤:', error);
            loading.style.display = 'none';
            
            // Show graceful error message
            results.style.display = 'block';
            const serviceUnavailableTitle = window.currentTranslations && window.currentTranslations['service_unavailable'] 
                ? window.currentTranslations['service_unavailable'] : '服務暫時不可用';
            doctorList.innerHTML = `
                <div class="alert alert-warning" style="text-align: center; padding: 20px; margin: 20px 0; border-radius: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: #856404; margin-bottom: 10px;"></i>
                    <h4 style="color: #856404; margin-bottom: 10px;">${serviceUnavailableTitle}</h4>
                    <p style="color: #856404; margin-bottom: 15px;">我們的服務暫時遇到問題，請稍後再試。如有緊急醫療需要，請直接聯繫醫療機構。</p>
                    <p style="color: #856404; font-size: 0.9rem;">錯誤代碼: ${error.message || 'Unknown error'}</p>
                </div>
            `;
            results.scrollIntoView({ behavior: 'smooth' });
        }
    }

    // Make proceedWithDiagnosis globally accessible for severe warning system
    window.proceedWithDiagnosis = proceedWithDiagnosis;

    function showValidationError(data) {
        results.style.display = 'block';
        doctorList.innerHTML = '';
        
        // Create validation error card
        const errorCard = document.createElement('div');
        errorCard.className = 'validation-error-card';
        errorCard.style.cssText = `
            background: linear-gradient(135deg, #fff5f5, #fed7d7);
            border: 2px solid #fc8181;
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 4px 12px rgba(252, 129, 129, 0.2);
        `;
        
        let issuesHtml = '';
        if (data.validation_issues && data.validation_issues.length > 0) {
            issuesHtml = `
                <div style="margin: 15px 0; text-align: left;">
                    <h5 style="color: #c53030; margin-bottom: 10px;">
                        <i class="fas fa-exclamation-triangle"></i> 發現的問題：
                    </h5>
                    <ul style="color: #742a2a; margin-left: 20px;">
                        ${data.validation_issues.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        let suggestionsHtml = '';
        if (data.validation_suggestions && data.validation_suggestions.length > 0) {
            suggestionsHtml = `
                <div style="margin: 15px 0; text-align: left;">
                    <h5 style="color: #2d3748; margin-bottom: 10px;">
                        <i class="fas fa-lightbulb"></i> 改善建議：
                    </h5>
                    <ul style="color: #4a5568; margin-left: 20px;">
                        ${data.validation_suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        errorCard.innerHTML = `
            <div style="font-size: 3rem; color: #fc8181; margin-bottom: 15px;">
                <i class="fas fa-exclamation-circle"></i>
            </div>
            <h3 style="color: #c53030; margin-bottom: 15px;">輸入內容不是症狀</h3>
            <p style="color: #742a2a; font-size: 1.1rem; margin-bottom: 20px;">
                ${data.validation_message || '您輸入的內容不是有效的醫療症狀。請重新輸入真實的身體不適症狀。'}
            </p>
            ${issuesHtml}
            ${suggestionsHtml}
            <div style="margin-top: 25px; padding: 15px; background: rgba(255,255,255,0.7); border-radius: 8px;">
                <h5 style="color: #2d3748; margin-bottom: 10px;">
                    <i class="fas fa-info-circle"></i> 請提供有效的症狀描述：
                </h5>
                <ul style="color: #4a5568; text-align: left; margin-left: 20px;">
                    <li>具體的身體不適感受（如：頭痛、發燒、咳嗽）</li>
                    <li>症狀的持續時間和嚴重程度</li>
                    <li>避免使用測試文字或無關內容</li>
                    <li>至少描述3個不同的症狀</li>
                </ul>
            </div>
            <button onclick="scrollToSymptoms()" style="
                background: linear-gradient(135deg, #805ad5, #9f7aea);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 25px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                margin-top: 20px;
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(128, 90, 213, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                <i class="fas fa-edit"></i> 重新輸入症狀
            </button>
        `;
        
        doctorList.appendChild(errorCard);
        results.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Function to scroll back to symptom input
    window.scrollToSymptoms = function() {
        const symptomContainer = document.querySelector('.symptom-input-container');
        if (symptomContainer) {
            symptomContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Focus on symptom input
            const symptomInput = document.getElementById('symptomInput');
            if (symptomInput) {
                setTimeout(() => symptomInput.focus(), 500);
            }
        }
    };

    // Global variables for pagination
    let allDoctors = [];
    let currentlyDisplayed = 0;
    const doctorsPerPage = 5;

    function displayResults(data) {
        doctorList.innerHTML = '';
        
        // Reset pagination state
        allDoctors = data.doctors || [];
        currentlyDisplayed = 0;
        
        // Store all doctors globally for modal access
        doctorsData = {};
        allDoctors.forEach(doctor => {
            doctorsData[doctor.id] = doctor;
        });
        
        // 顯示用戶數據摘要
        if (data.user_summary) {
            const summaryCard = createUserSummaryCard(data.user_summary);
            doctorList.appendChild(summaryCard);
        }
        
        // 顯示AI診斷結果
        if (data.diagnosis) {
            // Check if diagnosis contains error messages
            if (data.diagnosis.includes('AI分析服務暫時不可用') || 
                data.diagnosis.includes('AI服務配置不完整') ||
                data.diagnosis.includes('請稍後再試')) {
                
                const errorCard = document.createElement('div');
                errorCard.className = 'alert alert-warning';
                errorCard.style.cssText = 'text-align: center; padding: 20px; margin: 20px 0; border-radius: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7;';
                const aiUnavailableTitle = window.currentTranslations && window.currentTranslations['ai_diagnosis_unavailable'] 
                    ? window.currentTranslations['ai_diagnosis_unavailable'] : 'AI診斷暫時不可用';
                const aiUnavailableDesc = window.currentTranslations && window.currentTranslations['ai_diagnosis_unavailable_desc'] 
                    ? window.currentTranslations['ai_diagnosis_unavailable_desc'] : '我們的AI診斷服務暫時無法使用，但您仍可以查看推薦的醫生。建議直接諮詢醫療專業人士。';
                errorCard.innerHTML = `
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: #856404; margin-bottom: 10px;"></i>
                    <h4 style="color: #856404; margin-bottom: 10px;">${aiUnavailableTitle}</h4>
                    <p style="color: #856404; margin-bottom: 15px;">${aiUnavailableDesc}</p>
                `;
                doctorList.appendChild(errorCard);
            } else {
                const diagnosisCard = createDiagnosisCard(data.diagnosis, data.recommended_specialty);
                doctorList.appendChild(diagnosisCard);
            }
        }
        
        // Store doctor results globally for language switching
        window.lastDoctorResults = allDoctors;
        
        // 顯示醫生結果
        if (allDoctors.length > 0) {
            // 添加醫生推薦標題
            const doctorHeader = document.createElement('h3');
            const headerText = window.currentTranslations && window.currentTranslations['doctor_list_header'] 
                ? window.currentTranslations['doctor_list_header'] : '醫生列表';
            doctorHeader.innerHTML = `<i class="fas fa-user-doctor"></i> ${headerText}`;
            doctorHeader.style.cssText = 'margin: 30px 0 20px 0; color: #333; font-size: 1.5rem; display: flex; align-items: center; gap: 10px;';
            doctorList.appendChild(doctorHeader);
            
            // Create container for doctors
            const doctorsContainer = document.createElement('div');
            doctorsContainer.id = 'doctorsContainer';
            doctorList.appendChild(doctorsContainer);
            
            // Show initial doctors
            showMoreDoctors();
            
            results.style.display = 'block';
            results.scrollIntoView({ behavior: 'smooth' });
        } else {
            const noResultsMsg = document.createElement('p');
            const noResultsText = window.currentTranslations && window.currentTranslations['no_doctors_found'] 
                ? window.currentTranslations['no_doctors_found'] : '抱歉，未能找到合適的醫生。請嘗試修改搜索條件。';
            noResultsMsg.innerHTML = noResultsText;
            noResultsMsg.style.cssText = 'text-align: center; color: #666; font-size: 1.1rem; margin-top: 20px;';
            doctorList.appendChild(noResultsMsg);
            results.style.display = 'block';
        }
    }

    function showMoreDoctors() {
        const doctorsContainer = document.getElementById('doctorsContainer');
        const startIndex = currentlyDisplayed;
        const endIndex = Math.min(startIndex + doctorsPerPage, allDoctors.length);
        
        // Add doctors to display
        for (let i = startIndex; i < endIndex; i++) {
            const doctor = allDoctors[i];
            // Store doctor data globally for modal access
            doctorsData[doctor.id] = doctor;
            const doctorCard = createDoctorCard(doctor, i + 1);
            doctorsContainer.appendChild(doctorCard);
        }
        
        currentlyDisplayed = endIndex;
        
        // Remove existing "Show More" button
        const existingButton = document.getElementById('showMoreButton');
        if (existingButton) {
            existingButton.remove();
        }
        
        // Add "Show More" button if there are more doctors
        if (currentlyDisplayed < allDoctors.length) {
            const showMoreButton = document.createElement('div');
            showMoreButton.id = 'showMoreButton';
            showMoreButton.className = 'show-more-container';
            const showMoreText = window.currentTranslations && window.currentTranslations['show_more_doctors'] 
                ? window.currentTranslations['show_more_doctors'] : '顯示更多醫生';
            showMoreButton.innerHTML = `
                <button class="show-more-btn" id="showMoreBtn">
                    <i class="fas fa-plus-circle"></i>
                    ${showMoreText} (還有 ${allDoctors.length - currentlyDisplayed} 位)
                </button>
            `;
            
            // Add event listener to the button
            const showMoreBtn = showMoreButton.querySelector('#showMoreBtn');
            showMoreBtn.addEventListener('click', showMoreDoctors);
            doctorList.appendChild(showMoreButton);
        }
    }

    function translateSpecialty(specialty) {
        if (!specialty || !window.currentTranslations) {
            console.log('translateSpecialty: No specialty or no translations available', { specialty, hasTranslations: !!window.currentTranslations });
            return specialty;
        }
        
        // Try to find translation for the specialty
        const translated = window.currentTranslations[specialty];
        console.log('translateSpecialty:', { specialty, translated, found: !!translated });
        return translated || specialty;
    }

    function translateText(key) {
        if (!key) {
            return '';
        }
        
        let result = key;
        
        // Use language manager if available
        if (window.languageManager) {
            result = window.languageManager.getTranslation(key);
        }
        // Fallback to window.currentTranslations
        else if (window.currentTranslations) {
            const translated = window.currentTranslations[key];
            result = translated !== undefined ? translated : key;
        }
        
        // Handle bilingual objects immediately
        if (typeof result === 'object' && result !== null) {
            const currentLang = window.languageManager ? window.languageManager.getCurrentLanguage() : 'zh-TW';
            if (currentLang === 'en' && result.en) {
                return result.en;
            } else if (result['zh-TW']) {
                return result['zh-TW'];
            } else if (result.zh) {
                return result.zh;
            } else if (result.en) {
                return result.en;
            }
            // If object doesn't have expected language properties, return the key as fallback
            console.warn(`Translation object for key "${key}" missing expected language properties:`, result);
            return key;
        }
        
        // Ensure we always return a string
        return String(result || key);
    }

    // Helper function to get bilingual text based on current language
    function getBilingualText(doctor, field, currentLang) {
        if (!doctor) return '';
        
        const isEnglish = currentLang === 'en';
        let result = '';
        
        // For English UI, prefer English then Chinese
        if (isEnglish) {
            result = doctor[field + '_en'] || doctor[field + '_zh'] || doctor[field] || '';
        }
        // For Chinese UI, prefer Chinese then English
        else {
            result = doctor[field + '_zh'] || doctor[field + '_en'] || doctor[field] || '';
        }
        
        // Ensure we return a string, not an object
        if (typeof result === 'object') {
            console.warn(`getBilingualText returned object for field ${field}:`, result);
            return String(result) || '';
        }
        
        return result || '';
    }

    // Make createDoctorCard globally accessible
    window.createDoctorCard = function createDoctorCard(doctor, rank) {
        const card = document.createElement('div');
        card.className = 'doctor-card';
        
        // Get current language from language manager
        const currentLang = window.languageManager ? window.languageManager.getCurrentLanguage() : 'zh-TW';
        
        // Use bilingual data based on current language
        const doctorName = getBilingualText(doctor, 'name', currentLang);
        const doctorSpecialty = getBilingualText(doctor, 'specialty', currentLang);
        const doctorQualifications = getBilingualText(doctor, 'qualifications', currentLang);
        const doctorLanguages = getBilingualText(doctor, 'languages', currentLang);
        
        // 獲取醫生姓名的第一個字符作為頭像
        const avatarText = doctorName ? doctorName.charAt(0) : 'Dr';
        
        // 處理聯絡電話（可能有多個）
        const phones = doctor.contact_numbers ? doctor.contact_numbers.split(',').map(p => p.trim()) : [];
        const phoneDisplay = phones.length > 0 ? phones.join(' / ') : translateText('not_provided');
        
        // 處理地址
        const address = doctor.clinic_addresses || translateText('not_provided');
        
        card.innerHTML = `
            ${doctor.is_emergency ? `
            <div class="emergency-alert">
                <i class="fas fa-exclamation-triangle"></i>
                ${doctor.emergency_message || translateText('emergency_care_needed')}
            </div>
            ` : ''}
            <div class="whatsapp-hint">
                <i class="fab fa-whatsapp"></i>
                ${translateText('click_to_contact')}
            </div>
            
            <div class="doctor-header">
                <div class="doctor-avatar">
                    ${avatarText}
                </div>
                <div class="doctor-info">
                    <h3>${doctorName || translateText('unknown_doctor')}</h3>
                    <div class="doctor-specialty">${translateSpecialty(doctorSpecialty || translateText('general_specialist'))}</div>
                </div>
            </div>
            
            <div class="doctor-details">
                <div class="detail-item">
                    <i class="fas fa-language"></i>
                    <div>
                        <strong>${translateText('language_label')}</strong>
                        ${doctorLanguages || translateText('not_provided')}
                    </div>
                </div>
                
                <div class="detail-item">
                    <i class="fas fa-phone"></i>
                    <div>
                        <strong>${translateText('phone_label')}</strong>
                        ${phoneDisplay}
                    </div>
                </div>
                
                <div class="detail-item">
                    <i class="fas fa-envelope"></i>
                    <div>
                        <strong>${translateText('email_label')}</strong>
                        ${doctor.email || translateText('not_provided')}
                    </div>
                </div>
                
                <div class="detail-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <div>
                        <strong>${translateText('clinic_address_label')}</strong>
                        ${address}
                    </div>
                </div>
            </div>
            
            <div class="detail-item" style="margin-top: 15px;">
                <i class="fas fa-graduation-cap"></i>
                <div>
                    <strong>${translateText('qualifications_label')}</strong>
                    ${doctorQualifications || translateText('not_provided')}
                </div>
            </div>
            
            
            <div class="card-actions">
                <button class="more-info-btn" data-doctor-id="${doctor.id}" onclick="showDoctorDetailsById(event, ${doctor.id})">
                    <i class="fas fa-info-circle"></i>
                    ${(() => {
                        const translation = translateText('more_info');
                        return typeof translation === 'object' ? (translation['zh-TW'] || translation.zh || translation.en || 'More Info') : translation;
                    })()}
                </button>
                <button class="contact-btn" onclick="contactDoctor(event, '${doctor.name}', '${doctor.specialty}')">
                    <i class="fab fa-whatsapp"></i>
                    ${(() => {
                        const translation = translateText('contact');
                        return typeof translation === 'object' ? (translation['zh-TW'] || translation.zh || translation.en || 'Contact') : translation;
                    })()}
                </button>
            </div>
        `;
        
        // 添加hover效果
        card.addEventListener('mouseenter', function() {
            card.style.transform = 'translateY(-2px)';
            card.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
        });
        
        return card;
    }

    // Store doctors data globally for modal access
    let doctorsData = {};

    // Function to show doctor details by ID
    window.showDoctorDetailsById = function(event, doctorId) {
        event.stopPropagation();
        
        const doctor = doctorsData[doctorId];
        if (!doctor) {
            console.error('Doctor not found:', doctorId);
            return;
        }
        
        showDoctorDetails(event, doctor);
    };

    // Function to show doctor details in modal
    window.showDoctorDetails = function(event, doctor) {
        event.stopPropagation();
        
        const modal = document.getElementById('doctorModal') || createDoctorModal();
        const modalContent = modal.querySelector('.modal-content');
        
        // Get current language
        const currentLang = window.languageManager ? window.languageManager.getCurrentLanguage() : 'zh-TW';
        const isEnglish = currentLang === 'en';
        
        // Extract doctor data directly to avoid [object Object] issues
        const doctorName = isEnglish ? 
            (doctor.name_en || doctor.name_zh || doctor.name || 'Unknown Doctor') :
            (doctor.name_zh || doctor.name_en || doctor.name || '未知醫生');
            
        const doctorSpecialty = isEnglish ?
            (doctor.specialty_en || doctor.specialty_zh || doctor.specialty || 'General Practice') :
            (doctor.specialty_zh || doctor.specialty_en || doctor.specialty || '全科');
            
        const doctorQualifications = isEnglish ?
            (doctor.qualifications_en || doctor.qualifications_zh || doctor.qualifications || 'Not provided') :
            (doctor.qualifications_zh || doctor.qualifications_en || doctor.qualifications || '未提供');
            
        const doctorLanguages = isEnglish ?
            (doctor.languages_en || doctor.languages_zh || doctor.languages || 'Not provided') :
            (doctor.languages_zh || doctor.languages_en || doctor.languages || '未提供');
        
        const phones = doctor.phone ? doctor.phone.split(',').map(p => p.trim()) : [];
        const phoneDisplay = phones.length > 0 ? phones.join(' / ') : (isEnglish ? 'Not provided' : '未提供');
        const address = doctor.address || (isEnglish ? 'Not provided' : '未提供');
        
        const consultationFee = doctor.consultation_fee || (isEnglish ? 'Not specified' : '未指定');
        const consultationHours = doctor.consultation_hours || (isEnglish ? 'Not specified' : '未指定');
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <h2><i class="fas fa-user-md"></i> ${doctorName}</h2>
                <span class="close" onclick="closeDoctorModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="doctor-detail-section">
                    <h3><i class="fas fa-stethoscope"></i> ${isEnglish ? 'Specialty' : '專科'}</h3>
                    <p>${doctorSpecialty}</p>
                </div>
                
                <div class="doctor-detail-section">
                    <h3><i class="fas fa-graduation-cap"></i> ${isEnglish ? 'Qualifications' : '專業資格'}</h3>
                    <p>${doctorQualifications}</p>
                </div>
                
                <div class="doctor-detail-section">
                    <h3><i class="fas fa-language"></i> ${isEnglish ? 'Languages' : '語言'}</h3>
                    <p>${doctorLanguages}</p>
                </div>
                
                <div class="doctor-detail-section">
                    <h3><i class="fas fa-phone"></i> ${isEnglish ? 'Contact Information' : '聯絡資訊'}</h3>
                    <p><strong>${isEnglish ? 'Phone:' : '電話：'}</strong> ${phoneDisplay}</p>
                    <p><strong>${isEnglish ? 'Email:' : '電郵：'}</strong> ${doctor.email || (isEnglish ? 'Not provided' : '未提供')}</p>
                </div>
                
                <div class="doctor-detail-section">
                    <h3><i class="fas fa-map-marker-alt"></i> ${isEnglish ? 'Clinic Address' : '診所地址'}</h3>
                    <p>${address}</p>
                </div>
                
                <div class="doctor-detail-section">
                    <h3><i class="fas fa-dollar-sign"></i> ${isEnglish ? 'Consultation Fee' : '診金'}</h3>
                    <p>${consultationFee}</p>
                </div>
                
                <div class="doctor-detail-section">
                    <h3><i class="fas fa-clock"></i> ${isEnglish ? 'Consultation Hours' : '應診時間'}</h3>
                    <p>${consultationHours}</p>
                </div>
                
                ${doctor.website ? `
                <div class="doctor-detail-section">
                    <h3><i class="fas fa-globe"></i> ${isEnglish ? 'Website' : '網站'}</h3>
                    <p><a href="${doctor.website}" target="_blank">${doctor.website}</a></p>
                </div>
                ` : ''}
            </div>
            <div class="modal-footer">
                <button class="contact-btn-modal" onclick="contactDoctor(event, '${doctorName}', '${doctorSpecialty}')">
                    <i class="fab fa-whatsapp"></i>
                    ${isEnglish ? 'Contact via WhatsApp' : '透過WhatsApp聯絡'}
                </button>
            </div>
        `;
        
        modal.style.display = 'block';
    }

    // Function to create doctor modal if it doesn't exist
    function createDoctorModal() {
        const modal = document.createElement('div');
        modal.id = 'doctorModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <!-- Content will be populated by showDoctorDetails -->
            </div>
        `;
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeDoctorModal();
            }
        });
        
        return modal;
    }

    // Function to close doctor modal
    window.closeDoctorModal = function() {
        const modal = document.getElementById('doctorModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Function to handle doctor contact
    window.contactDoctor = async function(event, doctorName, doctorSpecialty) {
        event.stopPropagation();
        
        try {
            // Get WhatsApp URL with diagnosis report
            const response = await fetch('/get_whatsapp_url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    doctor_name: doctorName,
                    doctor_specialty: doctorSpecialty
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.whatsapp_url) {
                // Open WhatsApp with pre-filled diagnosis report
                window.open(data.whatsapp_url, '_blank');
            } else {
                // Fallback to basic WhatsApp URL if there's an error
                const fallbackUrl = 'https://wa.me/85294974070';
                window.open(fallbackUrl, '_blank');
                console.error('Failed to generate WhatsApp URL:', data.error);
            }
        } catch (error) {
            // Fallback to basic WhatsApp URL if request fails
            const fallbackUrl = 'https://wa.me/85294974070';
            window.open(fallbackUrl, '_blank');
            console.error('Error contacting doctor:', error);
        }
        
        // Close modal if it's open
        closeDoctorModal();
    }

    function createUserSummaryCard(userSummary) {
        const card = document.createElement('div');
        card.className = 'user-summary-card';
        
        // 格式化用戶摘要文本
        const formattedSummary = userSummary.replace(/\n/g, '<br>');
        
        card.innerHTML = `
            <div class="summary-header">
                <div class="summary-icon">
                    <i class="fas fa-user-circle"></i>
                </div>
                <div class="summary-title">
                    <h3 data-translate="user_health_summary">您的健康資料摘要</h3>
                </div>
            </div>
            
            <div class="summary-content">
                <div class="summary-text">
                    ${formattedSummary}
                </div>
            </div>
        `;
        
        // Apply translations to newly created card
        setTimeout(() => {
            if (window.currentTranslations) {
                card.querySelectorAll('[data-translate]').forEach(element => {
                    const key = element.getAttribute('data-translate');
                    if (window.currentTranslations[key]) {
                        element.textContent = window.currentTranslations[key];
                    }
                });
            }
        }, 0);
        
        return card;
    }

    function createDiagnosisCard(diagnosis, recommendedSpecialty) {
        const card = document.createElement('div');
        card.className = 'diagnosis-card';
        
        // 處理診斷文本，保留換行格式
        const formattedDiagnosis = diagnosis.replace(/\n/g, '<br>');
        
        card.innerHTML = `
            <div class="diagnosis-header">
                <div class="diagnosis-icon">
                    <i class="fas fa-stethoscope"></i>
                </div>
                <div class="diagnosis-title">
                    <h3 data-translate="ai_diagnosis_analysis">AI 智能診斷分析</h3>
                    <div class="recommended-specialty"><span data-translate="recommended_specialty">推薦專科</span>：${translateSpecialty(recommendedSpecialty)}</div>
                </div>
            </div>
            
            <div class="diagnosis-content">
                <div class="diagnosis-text">
                    ${formattedDiagnosis}
                </div>
            </div>
            
            <div class="diagnosis-disclaimer">
                <i class="fas fa-exclamation-triangle"></i>
                <strong data-translate="important_reminder">重要提醒：</strong><span data-translate="ai_disclaimer">此AI分析僅供參考，不能替代專業醫療診斷。請務必諮詢合格醫生進行正式診斷。</span>
            </div>
        `;
        
        // Apply translations to newly created diagnosis card
        setTimeout(() => {
            if (window.currentTranslations) {
                card.querySelectorAll('[data-translate]').forEach(element => {
                    const key = element.getAttribute('data-translate');
                    if (window.currentTranslations[key]) {
                        element.textContent = window.currentTranslations[key];
                    }
                });
            }
        }, 0);
        
        return card;
    }

    function validateSymptoms(symptoms) {
        if (!symptoms || symptoms.trim().length === 0) {
            return false;
        }
        
        // 如果使用新的tag系統，檢查symptomInput實例
        if (window.symptomInput && window.symptomInput.getSymptoms) {
            const symptomTags = window.symptomInput.getSymptoms();
            return symptomTags.length >= 3;
        }
        
        // 回退到舊的驗證方法（向後兼容）
        const separators = ['、', ',', '，', ';', '；', '和', '及', '還有', '以及', '\n', '。'];
        let symptomCount = 1;
        
        for (const separator of separators) {
            const parts = symptoms.split(separator);
            if (parts.length > symptomCount) {
                symptomCount = parts.filter(part => part.trim().length > 0).length;
            }
        }
        
        return symptomCount >= 3;
    }

    // Function to track doctor clicks
    function trackDoctorClick(doctorName, doctorSpecialty) {
        fetch('/track_click', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                doctor_name: doctorName,
                doctor_specialty: doctorSpecialty
            })
        }).catch(error => {
            console.log('Click tracking failed:', error);
        });
    }
});
