import sys
sys.path.append('.')
from translations import TRANSLATIONS

# Check what's actually in the translations
print("English translations for recommendation keys:")
en_trans = TRANSLATIONS.get('en', {})
print(f"recommendation_rank: '{en_trans.get('recommendation_rank', 'NOT_FOUND')}'")
print(f"recommendation_suffix: '{en_trans.get('recommendation_suffix', 'NOT_FOUND')}'")
print(f"Type of recommendation_suffix: {type(en_trans.get('recommendation_suffix'))}")

# Check if it's actually empty string vs None
suffix = en_trans.get('recommendation_suffix')
print(f"Is empty string: {suffix == ''}")
print(f"Is None: {suffix is None}")
print(f"Length: {len(suffix) if suffix is not None else 'None'}")

# Check Chinese version for comparison
zh_trans = TRANSLATIONS.get('zh-TW', {})
print(f"\nChinese recommendation_suffix: '{zh_trans.get('recommendation_suffix', 'NOT_FOUND')}'")
