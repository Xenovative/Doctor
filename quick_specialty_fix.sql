-- Quick SQL fixes for specialty data quality issues
-- Run these queries to identify and fix doctor names appearing in specialty fields

-- 1. Find doctors where specialty fields contain English names (the main issue)
SELECT id, name_zh, name_en, specialty_zh, specialty_en, specialty
FROM doctors 
WHERE specialty_zh REGEXP '[A-Z][a-z]+ [A-Z][a-z]+' -- English name pattern in Chinese field
   OR specialty_zh REGEXP '[A-Z][a-z]+, [A-Z][a-z]+' -- Last, First format
   OR specialty_en REGEXP '^[A-Z][a-z]+ [A-Z][a-z]+$' -- Full English name as specialty
   OR specialty REGEXP '^[A-Z][a-z]+ [A-Z][a-z]+$'
   OR specialty_zh LIKE '%Dr.%' 
   OR specialty_en LIKE '%Dr.%'
   OR specialty LIKE '%Dr.%';

-- 2. Find doctors where specialty field contains their own English name
SELECT d1.id, d1.name_zh, d1.name_en, d1.specialty_zh, d1.specialty_en, d1.specialty
FROM doctors d1
WHERE (d1.name_en IS NOT NULL AND d1.specialty_zh LIKE '%' || d1.name_en || '%')
   OR (d1.name_en IS NOT NULL AND d1.specialty_en LIKE '%' || d1.name_en || '%')
   OR (d1.name_en IS NOT NULL AND d1.specialty LIKE '%' || d1.name_en || '%');

-- 3. Clear problematic specialty fields (BACKUP YOUR DATABASE FIRST!)
-- Uncomment these lines after reviewing the results above:

-- Clear specialty fields that contain English names (the main fix needed)
-- UPDATE doctors SET specialty_zh = NULL 
-- WHERE specialty_zh REGEXP '[A-Z][a-z]+ [A-Z][a-z]+' -- English names in Chinese field
--    OR specialty_zh REGEXP '[A-Z][a-z]+, [A-Z][a-z]+' -- Last, First format
--    OR specialty_zh LIKE '%Dr.%';

-- UPDATE doctors SET specialty_en = NULL
-- WHERE specialty_en REGEXP '^[A-Z][a-z]+ [A-Z][a-z]+$' -- Full English name as specialty
--    OR specialty_en LIKE '%Dr.%';

-- UPDATE doctors SET specialty = NULL
-- WHERE specialty REGEXP '^[A-Z][a-z]+ [A-Z][a-z]+$' -- Full English name as specialty
--    OR specialty LIKE '%Dr.%';

-- 4. Clear specialty fields that contain the doctor's own English name
-- UPDATE doctors SET specialty_zh = NULL 
-- WHERE name_en IS NOT NULL AND specialty_zh LIKE '%' || name_en || '%';

-- UPDATE doctors SET specialty_en = NULL
-- WHERE name_en IS NOT NULL AND specialty_en LIKE '%' || name_en || '%';

-- UPDATE doctors SET specialty = NULL
-- WHERE name_en IS NOT NULL AND specialty LIKE '%' || name_en || '%';

-- 5. Verify the fixes
SELECT COUNT(*) as total_doctors FROM doctors;
SELECT COUNT(*) as doctors_with_specialty FROM doctors 
WHERE specialty_zh IS NOT NULL OR specialty_en IS NOT NULL OR specialty IS NOT NULL;

-- 6. Show doctors that still need specialty assignment
SELECT id, name_zh, name_en, qualifications_zh, qualifications_en
FROM doctors 
WHERE (specialty_zh IS NULL OR specialty_zh = '') 
  AND (specialty_en IS NULL OR specialty_en = '') 
  AND (specialty IS NULL OR specialty = '')
LIMIT 10;
