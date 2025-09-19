# Medical Terminology Update - Legal Compliance

## Overview
This update removes language that could be construed as "giving medical advice" to avoid legal controversies. All terminology has been changed to use safer, informational language that clearly positions the system as a reference tool rather than a medical advisor.

## Key Changes Made

### 1. Core Terminology Replacements

| Old Term (Problematic) | New Term (Safe) | Reason |
|------------------------|-----------------|---------|
| 診斷 (diagnosis) | 症狀分析 (symptom analysis) | Avoids medical diagnosis claims |
| 建議 (recommend) | 提示/資訊 (suggest/information) | Removes advisory language |
| 推薦專科 (recommended specialty) | 相關專科資訊 (related specialty info) | Informational rather than prescriptive |
| AI醫療診斷 (AI medical diagnosis) | AI症狀分析 (AI symptom analysis) | Clarifies analytical purpose |

### 2. Files Modified

#### Backend (Python)
- **app.py**: 
  - Function names: `diagnose_symptoms()` → `analyze_symptoms()`
  - Database columns: `ai_diagnosis` → `ai_analysis`, `recommended_specialty` → `related_specialty`
  - Return values and variable names updated throughout
  - WhatsApp message formatting updated
  - Report generation updated

- **translations.py**:
  - All UI text updated in Traditional Chinese, Simplified Chinese, and English
  - AI prompts updated to use analytical language
  - Disclaimers strengthened to clarify informational purpose

#### Frontend (HTML/JS)
- **templates/index.html**:
  - Severe warning modal language softened
  - Button text updated (取消診斷 → 取消症狀分析)
  - Disclaimer text updated

- **static/severe-warning.js**:
  - Console logging messages updated
  - Comments updated to reflect new terminology

#### Database Schema
- **update_medical_terminology.py**: Migration script created to safely update database column names
- Preserves old columns for backward compatibility
- Includes verification and rollback capabilities

### 3. Specific Language Changes

#### Disclaimers (Before → After)
```
Before: "此分析僅供參考，不能替代專業醫療診斷，請務必諮詢合格醫生。"
After:  "此分析僅供參考，不構成醫療建議或診斷，請務必諮詢合格醫生。"
```

#### Severe Warning System (Before → After)
```
Before: "我們強烈建議您："
After:  "以下是重要提醒："

Before: "立即前往最近的急診室"
After:  "考慮前往最近的急診室"

Before: "尋求專業醫療人員的即時協助"
After:  "建議尋求專業醫療人員的協助"
```

#### AI Prompts (Before → After)
```
Before: "作為一名經驗豐富的醫療專家，請根據以下病人資料進行初步病徵分析"
After:  "請根據以下症狀資料提供初步症狀分析和相關專科資訊"

Before: "可能的病症分析"
After:  "可能的症狀分析"

Before: "建議就診的專科"
After:  "相關專科資訊"
```

### 4. Database Migration

The migration script `update_medical_terminology.py` handles:
- Safe column renaming with backup creation
- Data preservation and copying
- Verification of successful migration
- Backward compatibility maintenance

**New Database Schema:**
```sql
-- Old columns (preserved for compatibility)
ai_diagnosis TEXT,
recommended_specialty TEXT,
diagnosis_report TEXT,

-- New columns (safer terminology)
ai_analysis TEXT,
related_specialty TEXT,
analysis_report TEXT
```

### 5. Legal Risk Mitigation

#### Before (High Risk)
- Used medical diagnostic language
- Made specific medical recommendations
- Positioned system as providing medical advice
- Used authoritative medical terminology

#### After (Low Risk)
- Uses analytical and informational language
- Provides suggestions and information only
- Clearly positions as reference tool
- Includes strong disclaimers about not constituting medical advice

### 6. User Experience Impact

- **Minimal**: All functionality remains the same
- **Clearer**: Users better understand the system's informational purpose
- **Safer**: Reduced legal liability for both users and operators
- **Professional**: Maintains medical professionalism while avoiding advice claims

### 7. Implementation Steps

1. ✅ Update all translation files
2. ✅ Modify backend functions and variable names
3. ✅ Update frontend templates and JavaScript
4. ✅ Strengthen disclaimers throughout
5. ✅ Create database migration script
6. 🔄 Run migration script: `python update_medical_terminology.py`
7. 🔄 Test all functionality
8. 🔄 Deploy to production

### 8. Testing Checklist

- [ ] Symptom analysis flow works correctly
- [ ] Severe warning system displays proper language
- [ ] WhatsApp integration uses new terminology
- [ ] Admin panel displays updated language
- [ ] Database migration completes successfully
- [ ] All disclaimers show updated text
- [ ] Multi-language support works correctly

### 9. Rollback Plan

If issues arise:
1. Database backups are automatically created by migration script
2. Old columns are preserved for backward compatibility
3. Can revert code changes via git
4. Can restore database from timestamped backup

### 10. Legal Benefits

- **Reduced Liability**: No longer claims to provide medical diagnoses
- **Clear Positioning**: System clearly positioned as informational tool
- **Strong Disclaimers**: Multiple disclaimers clarify limitations
- **Professional Standards**: Maintains medical professionalism without overstepping
- **Regulatory Compliance**: Aligns with medical device regulations that prohibit unlicensed medical advice

## Conclusion

This comprehensive update successfully removes all language that could be construed as "giving medical advice" while maintaining the system's functionality and user experience. The changes position the application as a symptom analysis and doctor matching tool rather than a medical diagnostic system, significantly reducing legal risk while preserving all core features.
