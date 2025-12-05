# ✅ AI Analysis Report in Reservation Details

## Feature Overview
Doctors can now view the complete AI analysis report for each reservation in the "預約詳情" (Reservation Details) section. This includes the patient's symptoms analysis, severity level, and recommended specialty.

## Changes Made

### 1. Backend - Enhanced Query

**File: `doctor_portal_routes.py`** (lines 537-566)

Updated the reservations query to include analysis report data:

```python
query = """
    SELECT 
        r.*,
        uq.analysis_report,           # AI analysis report
        uq.recommended_specialty,      # Recommended specialty
        uq.severity_level,             # Severity level (severe/moderate/mild)
        uq.created_at as query_created_at  # When query was created
    FROM reservations r
    LEFT JOIN user_queries uq ON r.query_id = uq.id
    WHERE r.doctor_id = ?
"""
```

**Before:**
```sql
SELECT * FROM reservations
WHERE doctor_id = ?
```

**After:**
- Uses `LEFT JOIN` with `user_queries` table
- Includes `analysis_report` field
- Includes `recommended_specialty` field
- Includes `severity_level` field
- Links via `query_id` foreign key

### 2. Frontend - Collapsible Report Display

**File: `templates/doctor/reservations.html`** (lines 166-191)

Added collapsible analysis report section:

```html
{% if reservation.analysis_report %}
<div class="mb-2 mt-3">
    <button class="btn btn-sm btn-outline-primary" type="button" 
            data-bs-toggle="collapse" 
            data-bs-target="#analysisReport{{ reservation.id }}">
        <i class="fas fa-file-medical me-1"></i>查看AI分析報告
    </button>
    
    <div class="collapse mt-2" id="analysisReport{{ reservation.id }}">
        <div class="card card-body bg-light">
            <!-- Severity and Specialty Badges -->
            <div class="mb-2">
                <span class="badge bg-danger/warning/info">
                    嚴重程度: {{ reservation.severity_level }}
                </span>
                <span class="badge bg-secondary">
                    建議專科: {{ reservation.recommended_specialty }}
                </span>
            </div>
            
            <!-- Analysis Report Text -->
            <div class="analysis-text" style="white-space: pre-wrap;">
                {{ reservation.analysis_report }}
            </div>
        </div>
    </div>
</div>
{% endif %}
```

## Display Features

### Collapsible Button
- **Icon:** 📋 Medical file icon
- **Text:** "查看AI分析報告" (View AI Analysis Report)
- **Style:** Outline primary button
- **Behavior:** Toggles report visibility

### Severity Badge Colors
- **Severe:** Red badge (`bg-danger`)
- **Moderate:** Yellow badge (`bg-warning`)
- **Mild:** Blue badge (`bg-info`)

### Report Layout
- **Background:** Light gray card
- **Format:** Pre-wrapped text (preserves line breaks)
- **Font:** Slightly smaller (0.9em) for readability

## User Experience

### Reservation Card Display

**Before (without analysis):**
```
┌────────────────────────────────────────────┐
│ Walk-in Patient          [聯絡請求]        │
│ 📅 2024-11-13  🕐 10:00                   │
│                                            │
│ 症狀: 頭痛, 發燒                           │
│ 長期病患: 高血壓                           │
│                                            │
│ [✓ 確認並安排預約]  [✗ 忽略請求]          │
└────────────────────────────────────────────┘
```

**After (with analysis):**
```
┌────────────────────────────────────────────┐
│ Walk-in Patient          [聯絡請求]        │
│ 📅 2024-11-13  🕐 10:00                   │
│                                            │
│ 症狀: 頭痛, 發燒                           │
│ 長期病患: 高血壓                           │
│                                            │
│ [📋 查看AI分析報告] ← NEW                 │
│                                            │
│ [✓ 確認並安排預約]  [✗ 忽略請求]          │
└────────────────────────────────────────────┘
```

**When expanded:**
```
┌────────────────────────────────────────────┐
│ Walk-in Patient          [聯絡請求]        │
│ 📅 2024-11-13  🕐 10:00                   │
│                                            │
│ 症狀: 頭痛, 發燒                           │
│ 長期病患: 高血壓                           │
│                                            │
│ [📋 查看AI分析報告] ▼                     │
│ ┌────────────────────────────────────────┐│
│ │ [嚴重程度: moderate] [建議專科: 內科]  ││
│ │                                        ││
│ │ 根據您描述的症狀（頭痛和發燒），       ││
│ │ 這可能是以下幾種情況：                 ││
│ │                                        ││
│ │ 1. 普通感冒或流感                      ││
│ │    - 症狀通常包括頭痛、發燒、咳嗽等   ││
│ │    - 建議多休息，補充水分              ││
│ │                                        ││
│ │ 2. 偏頭痛伴隨發燒                      ││
│ │    - 可能需要專科醫生評估              ││
│ │                                        ││
│ │ 建議：儘快就醫，特別是如果發燒持續... ││
│ └────────────────────────────────────────┘│
│                                            │
│ [✓ 確認並安排預約]  [✗ 忽略請求]          │
└────────────────────────────────────────────┘
```

## Data Flow

### When Patient Searches Symptoms:

1. **Patient enters symptoms:**
   ```
   Age: 35
   Symptoms: "頭痛, 發燒"
   Chronic: "高血壓"
   ```

2. **AI generates analysis:**
   ```sql
   INSERT INTO user_queries
   (age, gender, symptoms, chronic_conditions, analysis_report, 
    recommended_specialty, severity_level)
   VALUES (35, 'Male', '頭痛, 發燒', '高血壓', 
           '根據您描述的症狀...', '內科', 'moderate')
   ```
   Returns `query_id: 456`

3. **Patient contacts doctor:**
   ```sql
   INSERT INTO reservations
   (doctor_id, query_id, symptoms, chronic_conditions, ...)
   VALUES (123, 456, '頭痛, 發燒', '高血壓', ...)
   ```

4. **Doctor views reservation:**
   ```sql
   SELECT r.*, uq.analysis_report, uq.recommended_specialty, uq.severity_level
   FROM reservations r
   LEFT JOIN user_queries uq ON r.query_id = uq.id
   WHERE r.id = 789
   ```

5. **Doctor sees:**
   - Patient symptoms
   - Chronic conditions
   - **AI analysis report** ← NEW
   - **Severity level** ← NEW
   - **Recommended specialty** ← NEW

## Benefits

✅ **Complete context** - Doctors see full AI analysis  
✅ **Better preparation** - Review analysis before contact  
✅ **Severity awareness** - Color-coded severity badges  
✅ **Specialty validation** - Confirm patient matched correctly  
✅ **Clean UI** - Collapsible to avoid clutter  
✅ **Preserved formatting** - Line breaks maintained  
✅ **Optional display** - Only shows if analysis exists

## Edge Cases Handled

### 1. No Analysis Report
If `query_id` is NULL or no analysis exists:
- Button doesn't appear
- No error shown
- Reservation displays normally

### 2. Walk-in Patients
Patients who didn't search symptoms first:
- `query_id` = NULL
- No analysis report
- Only shows basic symptoms/conditions

### 3. Old Reservations
Reservations created before this feature:
- May not have `query_id`
- LEFT JOIN returns NULL for analysis fields
- Gracefully handled with `{% if %}`

## Database Schema

### user_queries table
```sql
- id (INTEGER)
- age (INTEGER)
- gender (TEXT)
- symptoms (TEXT)
- chronic_conditions (TEXT)
- analysis_report (TEXT)        ← Used
- recommended_specialty (TEXT)  ← Used
- severity_level (TEXT)         ← Used
- created_at (DATETIME)         ← Used
```

### reservations table
```sql
- id (INTEGER)
- doctor_id (INTEGER)
- query_id (INTEGER)            ← Foreign key
- patient_name (TEXT)
- symptoms (TEXT)
- chronic_conditions (TEXT)
- ...
```

### JOIN Result
```sql
reservations.* + 
    user_queries.analysis_report +
    user_queries.recommended_specialty +
    user_queries.severity_level +
    user_queries.created_at
```

## Testing

**Test the complete flow:**

1. **As Patient:**
   - Go to main page
   - Enter symptoms: "頭痛, 發燒"
   - Age: 35, Gender: Male
   - Click "尋找醫生"
   - Wait for AI analysis
   - Click "Contact via WhatsApp" on a doctor
   - Select time slot
   - Confirm

2. **As Doctor:**
   - Login to doctor portal
   - Go to "預約管理"
   - Find the new reservation
   - **Should see:** "查看AI分析報告" button
   - Click the button
   - **Should see:**
     - Severity badge (moderate/severe/mild)
     - Recommended specialty badge
     - Full AI analysis text
     - Properly formatted with line breaks

3. **Test Walk-in Patient:**
   - Create reservation without symptom search
   - **Should NOT see:** Analysis report button
   - **Should see:** Only basic symptoms field

## Files Modified

1. **doctor_portal_routes.py** (lines 537-566)
   - Added LEFT JOIN with `user_queries`
   - Included `analysis_report`, `recommended_specialty`, `severity_level`

2. **templates/doctor/reservations.html** (lines 166-191)
   - Added collapsible analysis report section
   - Added severity and specialty badges
   - Added formatted analysis text display

---

**Status**: ✅ Doctors can now view complete AI analysis reports in reservation details!
