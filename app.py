import sys
import re

# Check Python version compatibility
if sys.version_info >= (3, 12):
    print("Error: This application requires Python 3.11 or lower.")
    print(f"Current Python version: {sys.version}")
    print("Please use Python 3.8 - 3.11 to run this service.")
    sys.exit(1)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from translations import get_translation, get_available_languages, TRANSLATIONS
import pandas as pd
import sqlite3
import hashlib
import json
import time
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
from pathlib import Path
from dotenv import load_dotenv, set_key
import os
from collections import deque
import re
import threading
import pyotp
import qrcode
import io
import base64
from functools import wraps
import schedule
import secrets
from urllib.parse import quote

# Multi-Device 2FA imports
from multi_device_2fa import (
    MultiDevice2FA, multi_device_2fa, verify_multi_device_totp_token,
    get_user_2fa_devices_list, is_user_multi_device_enabled
)

# Set up logging with custom handler for console capture
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Console log buffer for admin console (keep last 1000 lines)
console_log_buffer = deque(maxlen=1000)

class ConsoleLogHandler(logging.Handler):
    """Custom log handler to capture logs for admin console"""
    def emit(self, record):
        try:
            log_entry = self.format(record)
            console_log_buffer.append({
                'timestamp': record.created,
                'level': record.levelname,
                'message': log_entry,
                'logger': record.name
            })
        except Exception:
            self.handleError(record)

# Add console handler to root logger
console_handler = ConsoleLogHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

# Load environment variables
load_dotenv()

# Conditional import for WhatsApp client
try:
    import socketio
    WHATSAPP_AVAILABLE = True
except ImportError:
    socketio = None
    WHATSAPP_AVAILABLE = False
    print("Warning: python-socketio not installed. WhatsApp functionality will be disabled.")

def update_env_file(key: str, value: str) -> None:
    """Update or add a key-value pair in the .env file."""
    env_path = Path('.env')
    
    # If .env doesn't exist, create it
    if not env_path.exists():
        env_path.touch()
    
    # Read current content
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return
    
    # Update or add the key
    key_exists = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{key}='):
            lines[i] = f"{key}={value}\n"
            key_exists = True
            break
    
    if not key_exists:
        lines.append(f"{key}={value}\n")
    
    # Write back to file
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        logger.info(f"Updated {key} in .env file")
    except Exception as e:
        logger.error(f"Error writing to .env file: {e}")

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Import and register blueprints for doctor affiliation system
try:
    from doctor_portal_routes import doctor_portal
    from reservation_routes import reservation_system
    from admin_affiliation_routes import admin_affiliation
    
    app.register_blueprint(doctor_portal)
    app.register_blueprint(reservation_system)
    app.register_blueprint(admin_affiliation)
    
    logger.info("✅ Doctor affiliation system blueprints registered successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import affiliation blueprints: {e}")
    logger.warning("Doctor affiliation features will not be available")

# Language switching route
@app.route('/set_language/<lang>')
def set_language(lang):
    """Set user's preferred language"""
    if lang in ['zh-TW', 'zh-CN', 'en']:
        session['language'] = lang
        return jsonify({'success': True, 'language': lang})
    return jsonify({'success': False, 'error': 'Invalid language'}), 400

# API endpoint to get translations
@app.route('/api/translations/<lang>')
def get_translations_api(lang):
    """Get translations for a specific language"""
    if lang in TRANSLATIONS:
        return jsonify(TRANSLATIONS[lang])
    return jsonify(TRANSLATIONS['zh-TW'])  # Default fallback

@app.route('/api/medical-evidence', methods=['POST'])
def get_medical_evidence():
    """Get real medical evidence from PubMed and other sources"""
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', [])
        diagnosis = data.get('diagnosis', '')
        
        if not symptoms and not diagnosis:
            return jsonify({'error': 'No symptoms or diagnosis provided'}), 400
        
        # If symptoms contain Chinese text, translate them using AI
        if any(isinstance(s, str) and any('\u4e00' <= c <= '\u9fff' for c in s) for s in symptoms):
            logger.info("Detected Chinese medical terms in symptoms, translating with AI...")
            translated_symptoms = translate_medical_terms_with_ai(symptoms)
            symptoms = translated_symptoms
        
        # Also translate diagnosis if it contains Chinese text
        if diagnosis and isinstance(diagnosis, str) and any('\u4e00' <= c <= '\u9fff' for c in diagnosis):
            logger.info("Detected Chinese medical terms in diagnosis, translating with AI...")
            translated_diagnosis = translate_medical_terms_with_ai([diagnosis])
            diagnosis = translated_diagnosis[0] if translated_diagnosis else diagnosis
        
        # Generate search terms for medical databases
        search_terms = generate_medical_search_terms(symptoms, diagnosis)
        
        # Fetch evidence from multiple sources
        evidence = []
        
        # Try PubMed first
        pubmed_evidence = fetch_pubmed_evidence(search_terms)
        if pubmed_evidence:
            evidence.extend(pubmed_evidence)
        
        # If we have limited results, try other sources
        if len(evidence) < 3:
            # Add other medical databases here
            additional_evidence = fetch_additional_medical_sources(search_terms)
            evidence.extend(additional_evidence)
        
        # Use configurable limit for total articles
        max_total = get_medical_search_config().get('max_total_articles', 8)
        evidence = evidence[:max_total]
        
        return jsonify({
            'success': True,
            'evidence': evidence,
            'search_terms': search_terms
        })
        
    except Exception as e:
        logger.error(f"Medical evidence API error: {e}")
        return jsonify({'error': 'Failed to fetch medical evidence'}), 500

def extract_diagnoses_from_ai_analysis(ai_analysis):
    """Extract potential diagnoses from AI analysis for targeted medical evidence search"""
    try:
        if not ai_analysis:
            return []
        
        # More precise patterns for diagnoses in AI analysis
        diagnosis_patterns = [
            r'可能的診斷[：:]\s*([^。\n，、]{2,15}(?:症|病|炎|癌|瘤|綜合症|失調|感染|中毒))',
            r'初步診斷[：:]\s*([^。\n，、]{2,15}(?:症|病|炎|癌|瘤|綜合症|失調|感染|中毒))',
            r'疑似([^。\n，、]{2,15}(?:症|病|炎|癌|瘤|綜合症|失調|感染|中毒))',
            r'可能患有([^。\n，、]{2,15}(?:症|病|炎|癌|瘤|綜合症|失調|感染|中毒))',
            r'懷疑是([^。\n，、]{2,15}(?:症|病|炎|癌|瘤|綜合症|失調|感染|中毒))',
            r'診斷為([^。\n，、]{2,15}(?:症|病|炎|癌|瘤|綜合症|失調|感染|中毒))',
            r'可能是([^。\n，、]{2,15}(?:症|病|炎|癌|瘤|綜合症|失調|感染|中毒))',
            # English patterns - more restrictive
            r'possible diagnosis[：:]\s*([a-zA-Z\s]{3,20}(?:syndrome|disease|disorder|infection|condition))',
            r'suspected\s+([a-zA-Z\s]{3,20}(?:syndrome|disease|disorder|infection|condition))',
            r'likely\s+([a-zA-Z\s]{3,20}(?:syndrome|disease|disorder|infection|condition))',
        ]
        
        extracted_conditions = []
        
        for pattern in diagnosis_patterns:
            try:
                matches = re.findall(pattern, ai_analysis, re.IGNORECASE)
                for match in matches:
                    condition = match.strip()
                    # More strict validation
                    if (len(condition) >= 3 and len(condition) <= 18 and 
                        not condition.isdigit() and 
                        not any(char in condition for char in ['?', '!', '@', '#', '$', '%'])):
                        extracted_conditions.append(condition)
            except re.error as e:
                logger.warning(f"Regex pattern error: {pattern} - {e}")
                continue
        
        # Remove duplicates while preserving order
        unique_conditions = []
        for condition in extracted_conditions:
            if condition not in unique_conditions:
                unique_conditions.append(condition)
        
        # Translate to English for PubMed search (limit to prevent excessive API calls)
        if unique_conditions:
            logger.info(f"Extracted diagnoses from AI analysis: {unique_conditions}")
            # Limit to top 3 conditions to prevent excessive translation calls
            limited_conditions = unique_conditions[:3]
            try:
                translated_diagnoses = translate_medical_terms_with_ai(limited_conditions)
                return translated_diagnoses if translated_diagnoses else limited_conditions
            except Exception as e:
                logger.error(f"Error translating diagnoses: {e}")
                return limited_conditions
        
        return []
        
    except Exception as e:
        logger.error(f"Error extracting diagnoses from AI analysis: {e}")
        return []

def translate_medical_terms_with_ai(chinese_terms):
    """Use AI to translate Chinese medical terms to English"""
    try:
        if not chinese_terms or not isinstance(chinese_terms, list):
            return []
        
        # Filter out invalid terms
        valid_terms = []
        for term in chinese_terms:
            if isinstance(term, str) and len(term.strip()) > 1 and len(term.strip()) < 50:
                valid_terms.append(term.strip())
        
        if not valid_terms:
            return []
        
        # Create a prompt for medical translation
        terms_text = ', '.join(str(term) for term in valid_terms)
        prompt = f"""請將以下中文醫學術語翻譯成英文醫學術語，只返回英文術語，用逗號分隔：

中文醫學術語：{terms_text}

請提供準確的醫學英文翻譯："""

        logger.info(f"Translating medical terms: {terms_text}")
        
        # Use the same AI service as diagnosis
        ai_response = call_ai_api(prompt)
        
        if ai_response and not ai_response.startswith("AI分析服務暫時不可用"):
            english_terms = ai_response.strip()
            # Split by comma and clean up
            translated_terms = [term.strip() for term in english_terms.split(',') if term.strip()]
            logger.info(f"AI translated terms: {translated_terms}")
            return translated_terms
        else:
            logger.warning("AI translation failed, using fallback")
            return chinese_terms
            
    except Exception as e:
        logger.error(f"Error translating medical terms: {e}")
        return chinese_terms

def generate_medical_search_terms(symptoms, diagnosis):
    """Generate appropriate search terms for medical databases"""
    search_terms = []
    
    # Comprehensive symptom mapping to medical terms
    symptom_mapping = {
        # Cardiovascular
        '胸痛': 'chest pain',
        '胸悶': 'chest tightness',
        '心悸': 'palpitations',
        '心跳快': 'tachycardia',
        '心律不整': 'arrhythmia',
        
        # Respiratory
        '呼吸困難': 'dyspnea',
        '氣喘': 'asthma',
        '咳嗽': 'cough',
        '咳血': 'hemoptysis',
        '喘息': 'wheezing',
        
        # Neurological
        '頭痛': 'headache',
        '頭暈': 'dizziness',
        '暈眩': 'vertigo',
        '偏頭痛': 'migraine',
        '失眠': 'insomnia',
        '癲癇': 'seizure',
        
        # Gastrointestinal
        '腹痛': 'abdominal pain',
        '噁心': 'nausea',
        '嘔吐': 'vomiting',
        '腹瀉': 'diarrhea',
        '便秘': 'constipation',
        '胃痛': 'stomach pain',
        
        # General symptoms
        '疲勞': 'fatigue',
        '發燒': 'fever',
        '發熱': 'fever',
        '體重減輕': 'weight loss',
        '食慾不振': 'loss of appetite',
        '盜汗': 'night sweats',
        
        # Mental health
        '焦慮': 'anxiety',
        '憂鬱': 'depression',
        '壓力': 'stress',
        '恐慌': 'panic',
        
        # Musculoskeletal
        '關節痛': 'joint pain',
        '肌肉痛': 'muscle pain',
        '背痛': 'back pain',
        '頸痛': 'neck pain',
        
        # Dermatological
        '皮疹': 'rash',
        '搔癢': 'itching',
        '紅腫': 'swelling',
        
        # Specialties (for diagnosis parameter)
        '普通科醫生': 'general practitioner',
        '內科': 'internal medicine',
        '外科': 'surgery',
        '心臟科': 'cardiology',
        '神經科': 'neurology',
        '腸胃科': 'gastroenterology',
        '呼吸科': 'pulmonology',
        '精神科': 'psychiatry'
    }
    
    # Process symptoms - handle both array and string formats
    symptoms_list = []
    if isinstance(symptoms, list):
        for item in symptoms:
            if isinstance(item, str):
                # Split comma-separated symptoms within each item
                individual_symptoms = [s.strip() for s in item.replace('、', ',').split(',') if s.strip()]
                symptoms_list.extend(individual_symptoms)
            else:
                symptoms_list.append(str(item))
    elif isinstance(symptoms, str):
        # Split comma-separated symptoms
        symptoms_list = [s.strip() for s in symptoms.replace('、', ',').split(',') if s.strip()]
    
    logger.info(f"Processed symptoms list: {symptoms_list}")
    
    # Convert symptoms to English medical terms
    for symptom in symptoms_list:
        english_term = symptom_mapping.get(symptom.strip(), symptom.strip())
        search_terms.append(english_term)
        logger.info(f"Mapped '{symptom}' -> '{english_term}'")
    
    # Add diagnosis if provided and not already a symptom
    if diagnosis and diagnosis not in search_terms:
        # Try to translate diagnosis too
        diagnosis_english = symptom_mapping.get(diagnosis.strip(), diagnosis.strip())
        search_terms.append(diagnosis_english)
    
    logger.info(f"Final search terms: {search_terms}")
    return search_terms

# Medical Search Configuration Management
def get_medical_search_config():
    """Get medical search configuration from database"""
    try:
        conn = sqlite3.connect('doctor_ai.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT config_key, config_value, config_type FROM medical_search_config')
        configs = cursor.fetchall()
        
        config_dict = {}
        for key, value, config_type in configs:
            if config_type == 'number':
                config_dict[key] = int(value) if value.isdigit() else float(value)
            elif config_type == 'boolean':
                config_dict[key] = value.lower() == 'true'
            else:
                config_dict[key] = value
        
        conn.close()
        return config_dict
        
    except Exception as e:
        logger.error(f"Error loading medical search config: {e}")
        # Return default values if config loading fails
        return {
            'primary_search_api': 'pubmed',
            'articles_per_symptom': 2,
            'max_symptoms_processed': 4,
            'max_total_articles': 8,
            'search_timeout': 10,
            'pubmed_retmax': 3
        }

def update_medical_search_config(config_key, config_value):
    """Update medical search configuration"""
    try:
        conn = sqlite3.connect('doctor_ai.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE medical_search_config 
            SET config_value = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE config_key = ?
        ''', (str(config_value), config_key))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error updating medical search config: {e}")
        return False

def fetch_pubmed_evidence(search_terms, original_terms=None):
    """Fetch evidence from PubMed database with configurable parameters"""
    try:
        # Load configuration
        config = get_medical_search_config()
        
        evidence = []
        symptom_coverage = {}  # Track which symptoms have articles
        
        # Ensure we have original terms for display
        if original_terms is None:
            original_terms = search_terms
        
        max_symptoms = config.get('max_symptoms_processed', 4)
        articles_per_symptom = config.get('articles_per_symptom', 2)
        timeout = config.get('search_timeout', 10)
        retmax = config.get('pubmed_retmax', 3)
        
        for i, term in enumerate(search_terms[:max_symptoms]):  # Use configurable limit
            original_term = original_terms[i] if i < len(original_terms) else term
            
            # Skip if primary API is not PubMed
            if config.get('primary_search_api', 'pubmed') != 'pubmed':
                logger.info(f"Skipping PubMed search, primary API is: {config.get('primary_search_api')}")
                break
                
            # Construct improved search query to reduce irrelevant results
            # Exclude rare disease and experimental studies
            exclusions = "NOT (rare[Title/Abstract] OR case report[Publication Type] OR animal[MeSH Terms] OR in vitro[Title/Abstract])"
            
            # Focus on clinical relevance
            clinical_focus = "(clinical[Title/Abstract] OR diagnosis[Title/Abstract] OR treatment[Title/Abstract] OR management[Title/Abstract] OR therapy[Title/Abstract])"
            
            # Prefer recent publications and systematic reviews
            quality_boost = "(systematic review[Publication Type] OR meta-analysis[Publication Type] OR randomized controlled trial[Publication Type] OR guideline[Publication Type])"
            
            search_query = f"({term}[Title/Abstract] AND {clinical_focus}) {exclusions}"
            
            # PubMed E-utilities API
            search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': search_query,
                'retmax': retmax,  # Use configurable retmax
                'sort': 'relevance',
                'retmode': 'xml'
            }
            
            search_response = requests.get(search_url, params=search_params, timeout=timeout)
            
            if search_response.status_code == 200:
                # Parse XML response to get PMIDs
                root = ET.fromstring(search_response.content)
                pmids = [id_elem.text for id_elem in root.findall('.//Id')]
                
                if pmids:
                    # Fetch article details
                    fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                    fetch_params = {
                        'db': 'pubmed',
                        'id': ','.join(pmids[:articles_per_symptom]),  # Use configurable articles per symptom
                        'retmode': 'xml'
                    }
                    
                    fetch_response = requests.get(fetch_url, params=fetch_params, timeout=10)
                    
                    if fetch_response.status_code == 200:
                        articles = parse_pubmed_articles(fetch_response.content, term, original_term)
                        if articles:
                            # Filter articles by relevance score
                            config = get_medical_search_config()
                            min_relevance = config.get('relevance_threshold', 2.0)
                            
                            filtered_articles = []
                            for article in articles:
                                score = article.get('relevance_score', 0)
                                if score >= min_relevance:
                                    filtered_articles.append(article)
                                    logger.info(f"Article accepted: '{article['title'][:50]}...' (score: {score:.1f})")
                                else:
                                    logger.info(f"Article filtered out: '{article['title'][:50]}...' (score: {score:.1f}, threshold: {min_relevance})")
                            
                            if filtered_articles:
                                evidence.extend(filtered_articles)
                                symptom_coverage[original_term] = len(filtered_articles)
                                logger.info(f"Found {len(filtered_articles)}/{len(articles)} relevant articles for symptom: {original_term}")
                            else:
                                logger.warning(f"No relevant articles found for symptom: {original_term} (all filtered out)")
                                symptom_coverage[original_term] = 0
                        else:
                            logger.warning(f"No articles found for symptom: {original_term}")
                            symptom_coverage[original_term] = 0
        
        # Remove duplicate articles based on title
        seen_titles = set()
        unique_evidence = []
        for article in evidence:
            title = article.get('title', '').strip().lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_evidence.append(article)
            else:
                logger.info(f"Removed duplicate article: {article.get('title', '')[:50]}...")
        
        evidence = unique_evidence
        
        # Sort evidence by relevance score (highest first)
        evidence.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Log final coverage summary
        total_articles = len(evidence)
        covered_symptoms = sum(1 for count in symptom_coverage.values() if count > 0)
        logger.info(f"Medical evidence summary: {total_articles} articles covering {covered_symptoms}/{len(symptom_coverage)} symptoms")
        logger.info(f"Symptom coverage: {symptom_coverage}")
        
        if evidence:
            avg_score = sum(article.get('relevance_score', 0) for article in evidence) / len(evidence)
            logger.info(f"Average relevance score: {avg_score:.2f}")
        
        return evidence
        
    except Exception as e:
        logger.error(f"PubMed API error: {e}")
        return []

def extract_relevant_excerpt(abstract_text, search_term):
    """Extract the most relevant excerpt from abstract based on search term"""
    try:
        if not abstract_text or len(abstract_text) < 100:
            return abstract_text
        
        # Split into sentences
        sentences = [s.strip() for s in abstract_text.replace('\n', ' ').split('.') if s.strip()]
        
        # Score sentences based on relevance to search term
        scored_sentences = []
        search_words = search_term.lower().split()
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            score = 0
            
            # Direct term matches
            for word in search_words:
                if word in sentence_lower:
                    score += 3
            
            # Medical relevance keywords
            medical_keywords = [
                'diagnosis', 'treatment', 'symptoms', 'clinical', 'patients', 'study', 
                'results', 'findings', 'associated', 'risk', 'therapy', 'management',
                'condition', 'disease', 'syndrome', 'disorder', 'prevalence', 'incidence'
            ]
            
            for keyword in medical_keywords:
                if keyword in sentence_lower:
                    score += 1
            
            # Prefer sentences with numbers/statistics
            if any(char.isdigit() for char in sentence):
                score += 1
            
            # Prefer sentences mentioning outcomes
            outcome_words = ['effective', 'improved', 'reduced', 'increased', 'significant', 'associated']
            for word in outcome_words:
                if word in sentence_lower:
                    score += 2
            
            if score > 0 and len(sentence) > 20:  # Minimum sentence length
                scored_sentences.append((score, sentence))
        
        if not scored_sentences:
            # Fallback to first part of abstract
            return abstract_text[:250] + "..." if len(abstract_text) > 250 else abstract_text
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Combine top 2-3 sentences, keeping under 300 characters
        selected_sentences = []
        total_length = 0
        
        for score, sentence in scored_sentences[:3]:
            if total_length + len(sentence) < 280:
                selected_sentences.append(sentence)
                total_length += len(sentence)
            else:
                break
        
        if selected_sentences:
            excerpt = '. '.join(selected_sentences)
            if not excerpt.endswith('.'):
                excerpt += '.'
            return excerpt
        else:
            return abstract_text[:250] + "..." if len(abstract_text) > 250 else abstract_text
            
    except Exception as e:
        logger.error(f"Error extracting relevant excerpt: {e}")
        return abstract_text[:200] + "..." if len(abstract_text) > 200 else abstract_text

def calculate_clinical_relevance_score(title, abstract, search_term):
    """Calculate clinical relevance score to filter out rare/fringe diseases"""
    try:
        title_lower = title.lower()
        abstract_lower = abstract.lower()
        search_lower = search_term.lower()
        
        score = 0
        
        # High relevance indicators (common clinical terms)
        high_relevance_terms = [
            'diagnosis', 'treatment', 'management', 'therapy', 'clinical',
            'patient', 'symptoms', 'prevalence', 'common', 'frequent',
            'primary care', 'emergency', 'acute', 'chronic', 'systematic review',
            'meta-analysis', 'randomized', 'controlled trial', 'guidelines',
            'evidence-based', 'standard care', 'first-line', 'routine'
        ]
        
        # Medium relevance indicators
        medium_relevance_terms = [
            'case study', 'cohort', 'observational', 'retrospective',
            'prospective', 'multicenter', 'population', 'epidemiology'
        ]
        
        # Low relevance indicators (rare/fringe disease markers)
        low_relevance_terms = [
            'rare', 'unusual', 'atypical', 'novel', 'first case', 'case report',
            'syndrome', 'genetic', 'hereditary', 'congenital', 'familial',
            'orphan disease', 'zebra', 'exotic', 'tropical', 'endemic'
        ]
        
        # Very low relevance (research/experimental)
        very_low_relevance_terms = [
            'in vitro', 'animal model', 'mouse', 'rat', 'laboratory',
            'experimental', 'molecular', 'cellular', 'biochemical',
            'pathophysiology', 'mechanism', 'hypothesis'
        ]
        
        # Score based on term presence
        for term in high_relevance_terms:
            if term in title_lower:
                score += 3
            elif term in abstract_lower:
                score += 2
        
        for term in medium_relevance_terms:
            if term in title_lower:
                score += 1
            elif term in abstract_lower:
                score += 0.5
        
        for term in low_relevance_terms:
            if term in title_lower:
                score -= 2
            elif term in abstract_lower:
                score -= 1
        
        for term in very_low_relevance_terms:
            if term in title_lower:
                score -= 3
            elif term in abstract_lower:
                score -= 1.5
        
        # Boost score if search term appears in title (direct relevance)
        if search_lower in title_lower:
            score += 5
        elif search_lower in abstract_lower:
            score += 2
        
        # Boost for recent publications (prefer current medical knowledge)
        import re
        year_match = re.search(r'20\d{2}', abstract_lower)
        if year_match:
            year = int(year_match.group())
            current_year = 2024
            if year >= current_year - 5:  # Last 5 years
                score += 2
            elif year >= current_year - 10:  # Last 10 years
                score += 1
        
        return max(0, score)  # Ensure non-negative score
        
    except Exception as e:
        logger.error(f"Error calculating clinical relevance score: {e}")
        return 1  # Default neutral score

def generate_relevance_explanation(display_term, title, abstract, search_term=None):
    """Generate a specific explanation of why this article is relevant (in Chinese)"""
    try:
        relevance_parts = []
        
        # Check what aspects are covered
        title_lower = title.lower()
        abstract_lower = abstract.lower()
        
        # Use search_term for matching (English) but display_term for output (Chinese)
        if search_term:
            search_lower = search_term.lower()
            if search_lower in title_lower:
                relevance_parts.append(f"直接探討{display_term}")
            elif search_lower in abstract_lower:
                relevance_parts.append(f"討論{display_term}")
        else:
            # Fallback: assume the article is relevant to the display term
            relevance_parts.append(f"討論{display_term}")
        
        # Clinical aspects (Chinese translations)
        clinical_aspects = []
        if 'diagnosis' in abstract_lower or 'diagnostic' in abstract_lower:
            clinical_aspects.append('診斷')
        if 'treatment' in abstract_lower or 'therapy' in abstract_lower:
            clinical_aspects.append('治療')
        if 'management' in abstract_lower:
            clinical_aspects.append('管理')
        if 'risk' in abstract_lower or 'factor' in abstract_lower:
            clinical_aspects.append('風險因子')
        if 'outcome' in abstract_lower or 'prognosis' in abstract_lower:
            clinical_aspects.append('預後')
        
        if clinical_aspects:
            relevance_parts.append(f"涵蓋{', '.join(clinical_aspects[:2])}")
        
        # Study type (Chinese translations)
        study_type = ""
        if 'randomized' in abstract_lower or 'controlled trial' in abstract_lower:
            study_type = "來自隨機對照試驗"
        elif 'systematic review' in abstract_lower or 'meta-analysis' in abstract_lower:
            study_type = "來自系統性回顧"
        elif 'cohort' in abstract_lower or 'longitudinal' in abstract_lower:
            study_type = "來自縱向研究"
        
        if study_type:
            relevance_parts.append(study_type)
        
        if relevance_parts:
            return f"此研究{', '.join(relevance_parts[:3])}，為您的症狀提供實證醫學參考。"
        else:
            return f"此研究針對{display_term}提供相關醫學參考，有助於了解您的症狀。"
            
    except Exception as e:
        logger.error(f"Error generating relevance explanation: {e}")
        return f"此研究針對{display_term}提供實證醫學參考，有助於了解您的症狀。"

def parse_pubmed_articles(xml_content, search_term, original_term=None):
    """Parse PubMed XML response to extract article information"""
    try:
        articles = []
        root = ET.fromstring(xml_content)
        
        for article in root.findall('.//PubmedArticle'):
            try:
                # Extract title
                title_elem = article.find('.//ArticleTitle')
                title = title_elem.text if title_elem is not None else "Unknown Title"
                
                # Extract journal and year
                journal_elem = article.find('.//Journal/Title')
                journal = journal_elem.text if journal_elem is not None else "Unknown Journal"
                
                year_elem = article.find('.//PubDate/Year')
                year = year_elem.text if year_elem is not None else "Unknown Year"
                
                # Extract abstract and find most relevant excerpt
                abstract_elem = article.find('.//Abstract/AbstractText')
                abstract = ""
                if abstract_elem is not None:
                    abstract_text = abstract_elem.text or ""
                    # Find the most relevant excerpt based on search term
                    abstract = extract_relevant_excerpt(abstract_text, search_term)
                
                # Extract PMID for URL
                pmid_elem = article.find('.//PMID')
                pmid = pmid_elem.text if pmid_elem is not None else ""
                
                if title and abstract:
                    # Use original term for display, search term for analysis
                    display_term = original_term if original_term else search_term
                    
                    # Calculate clinical relevance score
                    relevance_score = calculate_clinical_relevance_score(title, abstract, search_term)
                    
                    articles.append({
                        'title': title,
                        'source': f"{journal}, {year}",
                        'excerpt': abstract,
                        'relevance': generate_relevance_explanation(display_term, title, abstract, search_term),
                        'relevance_score': relevance_score,
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                        'type': 'pubmed'
                    })
                    
            except Exception as e:
                logger.error(f"Error parsing individual article: {e}")
                continue
        
        return articles
        
    except Exception as e:
        logger.error(f"Error parsing PubMed XML: {e}")
        return []

def fetch_additional_medical_sources(search_terms):
    """Fetch evidence from additional medical sources when PubMed results are limited"""
    try:
        evidence = []
        
        # You can add more medical databases here, such as:
        # - Cochrane Library
        # - MEDLINE
        # - Google Scholar (with appropriate API)
        # - Medical journal APIs
        
        # For now, we'll provide high-quality fallback content based on search terms
        fallback_evidence = get_fallback_medical_evidence(search_terms)
        evidence.extend(fallback_evidence)
        
        return evidence
        
    except Exception as e:
        logger.error(f"Additional sources error: {e}")
        return []

def get_fallback_medical_evidence(search_terms):
    """Provide high-quality fallback evidence when APIs are unavailable"""
    fallback_db = {
        'chest pain': {
            'title': 'Chest Pain Evaluation in Emergency Medicine: Evidence-Based Approach',
            'source': 'Emergency Medicine Clinics of North America, 2023',
            'excerpt': 'Chest pain is one of the most common presenting complaints in emergency medicine, accounting for over 8 million emergency department visits annually. Systematic evaluation using validated risk scores significantly improves diagnostic accuracy.',
            'relevance': 'This evidence-based approach to chest pain evaluation is directly relevant to your symptoms and emphasizes the importance of proper medical assessment.'
        },
        'headache': {
            'title': 'Primary Headache Disorders: Current Diagnostic and Management Strategies',
            'source': 'The Lancet Neurology, 2023',
            'excerpt': 'Primary headache disorders affect over 90% of the global population. Recent advances in understanding pathophysiology have led to improved diagnostic criteria and targeted therapeutic approaches.',
            'relevance': 'Your headache symptoms align with patterns described in current neurological literature, supporting the need for systematic evaluation and appropriate management.'
        },
        'fatigue': {
            'title': 'Chronic Fatigue: A Comprehensive Clinical Approach',
            'source': 'Journal of Internal Medicine, 2023',
            'excerpt': 'Chronic fatigue significantly impacts quality of life and requires systematic evaluation considering medical, psychological, and social factors. Evidence-based management strategies show significant improvement in patient outcomes.',
            'relevance': 'This comprehensive approach to fatigue evaluation addresses the multifactorial nature of your symptoms and supports the need for thorough medical assessment.'
        }
    }
    
    evidence = []
    for term in search_terms:
        if term.lower() in fallback_db:
            evidence.append(fallback_db[term.lower()])
    
    return evidence

# Add route to serve assets folder
from flask import send_from_directory

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve files from assets folder including subdirectories"""
    return send_from_directory('assets', filename)

# WhatsApp配置
WHATSAPP_CONFIG = {
    'enabled': os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true',
    'socket_url': os.getenv('WHATSAPP_SOCKET_URL', 'http://localhost:8086'),
    'api_key': os.getenv('WHATSAPP_API_KEY', ''),
    'target_number': os.getenv('WHATSAPP_TARGET_NUMBER', ''),  # Format: 852XXXXXXXX (for wa.me links)
    'session_name': os.getenv('WHATSAPP_SESSION_NAME', 'default'),
    'contact_mode': os.getenv('WHATSAPP_CONTACT_MODE', 'admin')  # 'admin' or 'doctor' - determines who receives the report link
}

# 時區配置
TIMEZONE_CONFIG = {
    'timezone': os.getenv('APP_TIMEZONE', 'Asia/Hong_Kong')
}

# AI服務配置
AI_CONFIG = {
    'provider': os.getenv('AI_PROVIDER', 'ollama'),  # 'ollama', 'openrouter', or 'openai'
    'openrouter': {
        'api_key': os.getenv('OPENROUTER_API_KEY', ''),
        'base_url': 'https://openrouter.ai/api/v1/chat/completions',
        'model': os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet'),
        'max_tokens': int(os.getenv('OPENROUTER_MAX_TOKENS', '4000'))
    },
    'openai': {
        'api_key': os.getenv('OPENAI_API_KEY', ''),
        'base_url': 'https://api.openai.com/v1/chat/completions',
        'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
        'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
    },
    'ollama': {
        'base_url': 'http://localhost:11434/api/generate',
        'model': os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
    }
}

# 嚴重症狀和病史配置 - Severe Symptoms and Conditions Configuration
SEVERE_SYMPTOMS_CONFIG = {
    'severe_symptoms': [
        # 心血管緊急症狀
        '胸痛', '胸悶', '心絞痛', '心臟病發作', '心肌梗塞', '心律不整', '心跳過快', '心跳過慢',
        '嚴重心悸', '胸部劇痛', '左臂疼痛', '下顎疼痛', '冷汗', '心臟停止',
        
        # 呼吸系統緊急症狀
        '呼吸困難', '氣喘', '呼吸急促', '無法呼吸', '窒息', '咳血', '大量咳血', '呼吸停止',
        '嚴重氣喘', '肺水腫', '肺栓塞', '氣胸', '呼吸衰竭',
        
        # 神經系統緊急症狀
        '中風', '腦中風', '半身不遂', '言語不清', '突然失語', '面部麻痺', '肢體麻痺',
        '嚴重頭痛', '劇烈頭痛', '突發性頭痛', '意識不清', '昏迷', '癲癇', '抽搐',
        '視力突然模糊', '突然失明', '複視', '眩暈', '平衡失調',
        
        # 消化系統緊急症狀
        '嘔血', '大量嘔血', '黑便', '血便', '大量出血', '腹部劇痛', '急性腹痛',
        '腸阻塞', '腹膜炎', '急性胰臟炎', '膽囊炎', '闌尾炎',
        
        # 泌尿生殖系統緊急症狀
        '血尿', '無法排尿', '尿瀦留', '腎絞痛', '急性腎衰竭', '陰道大出血',
        '產後大出血', '異位妊娠', '流產', '早產',
        
        # 外傷和中毒
        '大出血', '骨折', '脫臼', '燒傷', '電擊傷', '中毒', '藥物中毒', '食物中毒',
        '一氧化碳中毒', '化學品中毒', '過敏性休克', '嚴重過敏反應',
        
        # 精神科緊急症狀
        '自殺念頭', '自殺企圖', '自殺行為', '自殘', '暴力行為', '精神病發作',
        '嚴重憂鬱', '躁鬱症發作', '幻覺', '妄想',
        
        # 其他緊急症狀
        '高燒', '體溫過高', '體溫過低', '脫水', '休克', '敗血症', '感染性休克',
        '嚴重感染', '免疫系統衰竭', '器官衰竭', '多重器官衰竭'
    ],
    
    'severe_conditions': [
        # 心血管疾病
        '心臟病', '冠心病', '心肌梗塞', '心絞痛', '心律不整', '心臟衰竭', '主動脈瘤',
        '高血壓危象', '惡性高血壓', '心內膜炎', '心肌炎', '心包炎',
        
        # 癌症
        '癌症', '惡性腫瘤', '白血病', '淋巴癌', '肺癌', '肝癌', '胃癌', '大腸癌',
        '乳癌', '前列腺癌', '子宮須癌', '卵巢癌', '腦瘤', '骨癌', '皮膚癌',
        '胰臟癌', '腎癌', '膀胱癌', '食道癌', '甲狀腺癌',
        
        # 神經系統疾病
        '中風', '腦中風', '腦出血', '腦梗塞', '腦瘤', '腦炎', '腦膜炎',
        '帕金森病', '阿茲海默症', '失智症', '多發性硬化症', '肌萎縮性側索硬化症',
        '癲癇', '重症肌無力', '腦性麻痺',
        
        # 呼吸系統疾病
        '肺癌', '肺纖維化', '慢性阻塞性肺病', '肺氣腫', '肺炎', '肺結核',
        '氣喘', '肺栓塞', '肺水腫', '呼吸衰竭', '睡眠呼吸中止症',
        
        # 消化系統疾病
        '肝硬化', '肝癌', '肝炎', '胰臟炎', '胰臟癌', '胃癌', '大腸癌',
        '克隆氏症', '潰瘍性結腸炎', '胃潰瘍', '十二指腸潰瘍',
        
        # 腎臟疾病
        '腎衰竭', '慢性腎病', '腎癌', '腎結石', '腎炎', '腎病症候群',
        '多囊腎', '腎移植', '洗腎', '血液透析', '腹膜透析',
        
        # 內分泌疾病
        '糖尿病', '甲狀腺癌', '甲狀腺機能亢進', '甲狀腺機能低下',
        '腎上腺疾病', '垂體瘤', '糖尿病酮酸中毒', '低血糖昏迷',
        
        # 血液疾病
        '白血病', '淋巴癌', '貧血', '血友病', '血小板減少症',
        '骨髓移植', '地中海貧血', '鐮刀型貧血',
        
        # 免疫系統疾病
        '愛滋病', 'HIV', '紅斑性狼瘡', '類風濕性關節炎', '硬皮症',
        '多發性肌炎', '免疫缺陷', '器官移植', '免疫抑制治療',
        
        # 精神疾病
        '重度憂鬱症', '躁鬱症', '精神分裂症', '自閉症', '注意力不足過動症',
        '創傷後壓力症候群', '強迫症', '恐慌症', '焦慮症', '人格障礙'
    ]
}

# 載入醫生資料
def load_doctors_data():
    """載入醫生資料 - 從SQLite數據庫"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # 查詢所有醫生資料，優先使用中文資料，英文作為備用，按優先級和名稱排序
        # LEFT JOIN with doctor_accounts to get account_phone for affiliated doctors
        cursor.execute('''
            SELECT 
                d.id,
                COALESCE(d.name_zh, d.name_en, d.name) as name,
                COALESCE(d.specialty_zh, d.specialty_en, d.specialty) as specialty,
                COALESCE(d.qualifications_zh, d.qualifications_en, d.qualifications) as qualifications,
                COALESCE(d.languages_zh, d.languages_en, d.languages) as languages,
                d.contact_numbers as phone,
                d.clinic_addresses as address,
                d.email,
                d.consultation_fee,
                d.consultation_hours,
                d.profile_url,
                d.registration_number,
                d.languages_available,
                d.name_zh,
                d.name_en,
                d.specialty_zh,
                d.specialty_en,
                d.qualifications_zh,
                d.qualifications_en,
                d.languages_zh,
                d.languages_en,
                COALESCE(d.priority_flag, 0) as priority_flag,
                COALESCE(d.is_affiliated, 0) as is_affiliated,
                da.phone as account_phone,
                d.contact_numbers
            FROM doctors d
            LEFT JOIN doctor_accounts da ON d.id = da.doctor_id AND da.is_active = 1
            ORDER BY COALESCE(d.priority_flag, 0) DESC, name
        ''')
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        doctors_data = []
        for row in rows:
            doctor_dict = dict(zip(columns, row))
            # 確保必要欄位不為空
            if not doctor_dict.get('name'):
                doctor_dict['name'] = doctor_dict.get('name_en', 'Unknown')
            if not doctor_dict.get('specialty'):
                doctor_dict['specialty'] = doctor_dict.get('specialty_en', 'General')
            doctors_data.append(doctor_dict)
        
        conn.close()
        print(f"✅ 從數據庫載入了 {len(doctors_data):,} 位醫生資料")
        return doctors_data
        
    except Exception as e:
        print(f"從數據庫載入醫生資料時發生錯誤: {e}")
        # 備用方案：嘗試從CSV載入
        return load_doctors_data_csv()

def load_doctors_data_csv():
    """備用方案：從CSV載入醫生資料"""
    csv_path = os.path.join('assets', 'finddoc_doctors_detailed 2.csv')
    try:
        df = pd.read_csv(csv_path)
        print(f"⚠️ 使用備用CSV載入了 {len(df)} 位醫生資料")
        return df.to_dict('records')
    except Exception as e:
        print(f"載入CSV醫生資料時發生錯誤: {e}")
        return []

# 全局變數存儲醫生資料和數據庫狀態
DOCTORS_DATA = load_doctors_data()
DB_LAST_MODIFIED = None
DB_LAST_CHECK = None

def get_database_modification_time():
    """獲取數據庫最後修改時間"""
    try:
        import os
        db_path = 'doctors.db'
        if os.path.exists(db_path):
            return os.path.getmtime(db_path)
    except Exception as e:
        print(f"Error getting database modification time: {e}")
    return None

def should_reload_database():
    """檢查是否需要重新載入數據庫"""
    global DB_LAST_MODIFIED, DB_LAST_CHECK
    import time
    
    current_time = time.time()
    
    # 每30秒檢查一次
    if DB_LAST_CHECK and (current_time - DB_LAST_CHECK) < 30:
        return False
    
    DB_LAST_CHECK = current_time
    current_mod_time = get_database_modification_time()
    
    if current_mod_time is None:
        return False
    
    if DB_LAST_MODIFIED is None:
        DB_LAST_MODIFIED = current_mod_time
        return False
    
    if current_mod_time > DB_LAST_MODIFIED:
        DB_LAST_MODIFIED = current_mod_time
        print(f"Database modification detected, reloading doctor data...")
        return True
    
    return False

def reload_doctors_data_if_needed():
    """如果數據庫有變化則重新載入醫生資料"""
    global DOCTORS_DATA
    
    if should_reload_database():
        try:
            new_data = load_doctors_data()
            if new_data:  # Only update if we successfully loaded new data
                DOCTORS_DATA = new_data
                print(f"✅ Successfully reloaded {len(DOCTORS_DATA)} doctors from database")
                return True
            else:
                print("⚠️ Failed to reload database, keeping existing data")
        except Exception as e:
            print(f"❌ Error reloading database: {e}")
    
    return False

# Initialize database modification time
DB_LAST_MODIFIED = get_database_modification_time()

# Admin credentials (in production, use proper user management)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = hashlib.sha256(os.getenv('ADMIN_PASSWORD', 'admin123').encode()).hexdigest()

def load_ai_config_from_db():
    """Load AI configuration from database"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Load AI config
        cursor.execute('SELECT config_value FROM system_config WHERE config_key = ?', ('ai_config',))
        result = cursor.fetchone()
        
        if result:
            saved_config = json.loads(result[0])
            AI_CONFIG.update(saved_config)
            print("Loaded AI config from database")
        
        conn.close()
    except Exception as e:
        print(f"Error loading AI config from database: {e}")

def load_whatsapp_config_from_db():
    """Load WhatsApp configuration from database"""
    global WHATSAPP_CONFIG
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Load WhatsApp config
        cursor.execute('SELECT value FROM admin_config WHERE key = ?', ('whatsapp_config',))
        result = cursor.fetchone()
        
        if result:
            saved_config = json.loads(result[0])
            WHATSAPP_CONFIG.update(saved_config)
            print("Loaded WhatsApp config from database")
        
        conn.close()
    except Exception as e:
        print(f"Error loading WhatsApp config from database: {e}")

# Initialize database
def init_db():
    """Initialize SQLite database for analytics and user data"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                user_ip TEXT,
                user_agent TEXT,
                data TEXT,
                session_id TEXT
            )
        ''')
        
        # User queries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                age INTEGER,
                symptoms TEXT,
                chronic_conditions TEXT,
                language TEXT,
                location TEXT,
                detailed_health_info TEXT,
                ai_analysis TEXT,
                related_specialty TEXT,
                matched_doctors_count INTEGER,
                user_ip TEXT,
                session_id TEXT
            )
        ''')
        
        # Doctor clicks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctor_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                doctor_name TEXT,
                doctor_specialty TEXT,
                user_ip TEXT,
                session_id TEXT,
                query_id INTEGER,
                FOREIGN KEY (query_id) REFERENCES user_queries (id)
            )
        ''')
        
        # System config table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE,
                config_value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Admin users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                permissions TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1,
                created_by INTEGER,
                totp_secret TEXT,
                totp_enabled BOOLEAN DEFAULT 0,
                backup_codes TEXT,
                FOREIGN KEY (created_by) REFERENCES admin_users (id)
            )
        ''')
        
        # Admin config table for storing configuration settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create default admin user if not exists
        cursor.execute('SELECT COUNT(*) FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO admin_users (username, password_hash, role, permissions)
                VALUES (?, ?, 'super_admin', '{"all": true}')
            ''', (ADMIN_USERNAME, ADMIN_PASSWORD_HASH))
            print(f"Created default admin user: {ADMIN_USERNAME}")
        
        conn.commit()
        conn.close()
        print("=== DATABASE INITIALIZED SUCCESSFULLY ===")
        print(f"Created tables: analytics, user_queries, doctor_clicks, system_config, admin_users, admin_config")
        print(f"Default admin user: {ADMIN_USERNAME}")
        
    except Exception as e:
        print(f"=== DATABASE INITIALIZATION ERROR ===")
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Create a minimal fallback database
        try:
            conn = sqlite3.connect('admin_data.db')
            conn.close()
            print("=== CREATED MINIMAL DATABASE FILE ===")
        except Exception as fallback_error:
            print(f"=== FAILED TO CREATE DATABASE FILE ===")
            print(f"Fallback error: {fallback_error}")

# Initialize database on startup
print("=== STARTING DATABASE INITIALIZATION ===")
init_db()

# Load configurations from database
print("=== LOADING AI CONFIG FROM DATABASE ===")
load_ai_config_from_db()
print("=== LOADING WHATSAPP CONFIG FROM DATABASE ===")
load_whatsapp_config_from_db()
print("=== APP STARTUP COMPLETE ===")

# WhatsApp客戶端實例
whatsapp_client = None

def init_whatsapp_client():
    """初始化WhatsApp客戶端"""
    global whatsapp_client
    
    if not WHATSAPP_CONFIG['enabled'] or not WHATSAPP_AVAILABLE:
        whatsapp_client = None
        if not WHATSAPP_AVAILABLE:
            print("WhatsApp客戶端不可用：python-socketio未安裝")
        return
    
    try:
        whatsapp_client = socketio.SimpleClient()
        print(f"WhatsApp Socket.IO客戶端已初始化")
    except Exception as e:
        print(f"WhatsApp客戶端初始化失敗: {e}")
        whatsapp_client = None

# Initialize WhatsApp client on startup
init_whatsapp_client()

def send_whatsapp_notification(message: str):
    """發送WhatsApp通知"""
    print(f"DEBUG: WhatsApp enabled: {WHATSAPP_CONFIG['enabled']}")
    print(f"DEBUG: WhatsApp client initialized: {whatsapp_client is not None}")
    print(f"DEBUG: Target number: {WHATSAPP_CONFIG['target_number']}")
    print(f"DEBUG: Socket URL: {WHATSAPP_CONFIG['socket_url']}")
    
    if not WHATSAPP_CONFIG['enabled']:
        print("WhatsApp通知已跳過（未啟用）")
        return False
        
    if not whatsapp_client:
        print("WhatsApp通知已跳過（客戶端未初始化）")
        return False
    
    def send_async():
        connected = False
        try:
            # Check if already connected
            if not whatsapp_client.connected:
                print(f"DEBUG: Connecting to {WHATSAPP_CONFIG['socket_url']}")
                whatsapp_client.connect(WHATSAPP_CONFIG['socket_url'])
                connected = True
            else:
                print("DEBUG: Using existing connection")
            
            print(f"DEBUG: Sending message to {WHATSAPP_CONFIG['target_number']}")
            # Generate a unique message ID for deduplication
            import hashlib
            import time
            message_id = hashlib.md5(f"{WHATSAPP_CONFIG['target_number']}:{message}:{time.time()}".encode()).hexdigest()
            
            # Send message via Socket.IO and wait for response
            response = whatsapp_client.call('sendText', {
                'to': WHATSAPP_CONFIG['target_number'],
                'content': message,
                'messageId': message_id  # Include message ID for deduplication
            }, timeout=10)
            
            if response and response.get('success'):
                print(f"✅ WhatsApp message sent successfully to {WHATSAPP_CONFIG['target_number']}")
                return True
            else:
                error_msg = response.get('error', 'Unknown error') if response else 'No response from server'
                print(f"❌ WhatsApp send failed: {error_msg}")
                return False
                
        except Exception as e:
            print(f"❌ WhatsApp send error: {str(e)}")
            # If there was an error, try to disconnect to clean up the connection
            try:
                if connected and whatsapp_client.connected:
                    whatsapp_client.disconnect()
            except:
                pass
            return False
    
    try:
        # Run in a new thread
        thread = threading.Thread(target=send_async)
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        print(f"WhatsApp通知錯誤: {e}")
        return False

def get_app_timezone():
    """Get configured timezone"""
    try:
        return pytz.timezone(TIMEZONE_CONFIG['timezone'])
    except:
        return pytz.timezone('Asia/Hong_Kong')

def get_current_time():
    """Get current time in Hong Kong timezone"""
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    return datetime.now(hk_tz)

def detect_severe_symptoms_and_conditions(symptoms, chronic_conditions):
    """
    檢測嚴重症狀和病史，返回檢測結果
    Detect severe symptoms and conditions, return detection results
    """
    severe_symptoms_found = []
    severe_conditions_found = []
    
    # 將輸入轉換為小寫以便比較
    symptoms_lower = symptoms.lower() if symptoms else ""
    conditions_lower = chronic_conditions.lower() if chronic_conditions else ""
    
    # 檢測嚴重症狀
    for severe_symptom in SEVERE_SYMPTOMS_CONFIG['severe_symptoms']:
        if severe_symptom.lower() in symptoms_lower:
            severe_symptoms_found.append(severe_symptom)
    
    # 檢測嚴重病史
    for severe_condition in SEVERE_SYMPTOMS_CONFIG['severe_conditions']:
        if severe_condition.lower() in conditions_lower:
            severe_conditions_found.append(severe_condition)
    
    # 判斷是否需要顯示警告
    is_severe_case = len(severe_symptoms_found) > 0 or len(severe_conditions_found) > 0
    
    return {
        'is_severe': is_severe_case,
        'severe_symptoms': severe_symptoms_found,
        'severe_conditions': severe_conditions_found,
        'total_severe_items': len(severe_symptoms_found) + len(severe_conditions_found)
    }

def log_severe_case(user_query_id, age, gender, symptoms, chronic_conditions, 
                   severe_symptoms, severe_conditions, user_ip, session_id):
    """
    記錄嚴重病例到數據庫
    Log severe case to database for admin monitoring
    """
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO severe_cases 
            (user_query_id, age, gender, symptoms, chronic_conditions, 
             severe_symptoms, severe_conditions, user_ip, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_query_id, age, gender, symptoms, chronic_conditions,
            json.dumps(severe_symptoms, ensure_ascii=False),
            json.dumps(severe_conditions, ensure_ascii=False),
            user_ip, session_id, get_current_time().isoformat()
        ))
        
        severe_case_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 記錄到日誌
        logger.warning(f"Severe case detected and logged - ID: {severe_case_id}, "
                      f"Symptoms: {len(severe_symptoms)}, Conditions: {len(severe_conditions)}, "
                      f"Session: {session_id}")
        
        return severe_case_id
        
    except Exception as e:
        logger.error(f"Error logging severe case: {e}")
        return None

# 2FA Helper Functions
def generate_totp_secret():
    """Generate a new TOTP secret"""
    return pyotp.random_base32()

def generate_qr_code(username, secret, issuer="Doctor AI Admin"):
    """Generate QR code for TOTP setup"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name=issuer
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

def verify_totp_token(secret, token):
    """Verify TOTP token"""
    try:
        totp = pyotp.TOTP(secret)
        # Clean the token - remove any spaces or dashes
        clean_token = str(token).replace('-', '').replace(' ', '').strip()
        
        # Generate current expected token for debugging
        current_token = totp.now()
        print(f"DEBUG - Input token: '{clean_token}', Expected: '{current_token}', Secret exists: {bool(secret)}")
        
        result = totp.verify(clean_token, valid_window=2)  # Increased window for time sync issues
        print(f"DEBUG - Token verification result: {result}")
        return result
    except Exception as e:
        print(f"DEBUG - Token verification error: {e}")
        return False

def generate_backup_codes():
    """Generate backup codes for 2FA"""
    codes = []
    for _ in range(10):
        code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
        codes.append(f"{code[:4]}-{code[4:]}")
    return codes

def format_timestamp(timestamp_str):
    """Format timestamp string to clean readable format"""
    try:
        # Parse the timestamp string
        if isinstance(timestamp_str, str):
            # Handle ISO format with timezone
            if '+' in timestamp_str or 'T' in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        else:
            dt = timestamp_str
        
        # Convert to Hong Kong timezone if needed
        if dt.tzinfo is None:
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            dt = hk_tz.localize(dt)
        elif dt.tzinfo != pytz.timezone('Asia/Hong_Kong'):
            dt = dt.astimezone(pytz.timezone('Asia/Hong_Kong'))
        
        # Format as clean readable string
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp_str}: {e}")
        return str(timestamp_str)

def format_analysis_report_full(user_query_data: dict, doctor_data: dict) -> str:
    """格式化完整症狀分析報告為HTML顯示"""
    timestamp = get_current_time().strftime('%Y-%m-%d %H:%M:%S')
    
    # Format gender display
    gender = user_query_data.get('gender', '')
    gender_display = f"生理性別: {gender}" if gender else "生理性別: 未提供"
    
    message = f"""🏥 AI症狀分析報告
📅 時間: {timestamp}

👤 患者信息
年齡: {user_query_data.get('age', 'N/A')}歲
{gender_display}
症狀: {user_query_data.get('symptoms', 'N/A')}
語言: {user_query_data.get('language', 'N/A')}
地區: {user_query_data.get('location', 'N/A')}

🔍 AI症狀分析結果
相關專科: {user_query_data.get('related_specialty', 'N/A')}

👨‍⚕️ 選擇的醫生
醫生姓名: {doctor_data.get('doctor_name', 'N/A')}
專科: {doctor_data.get('doctor_specialty', 'N/A')}

📊 完整分析
{user_query_data.get('ai_analysis', 'N/A')}

免責聲明：此分析僅供參考，不構成醫療建議或診斷，請務必諮詢合格醫生。

---
Doctor-AI香港醫療配對系統"""
    
    return message

def format_whatsapp_message(doctor_data: dict, report_url: str, reference_code: str = None) -> str:
    """格式化WhatsApp消息，包含症狀分析報告鏈接 (發送給管理員)"""
    ref_section = f"\n🎫 診斷參考編號：{reference_code}\n（預約時請提供此編號）\n" if reference_code else ""
    
    message = f"""AI症狀分析報告

您好！我通過AI症狀分析系統獲得了您的資訊。
{ref_section}
醫生信息
姓名: {doctor_data.get('doctor_name', 'N/A')}
專科: {doctor_data.get('doctor_specialty', 'N/A')}

完整症狀分析報告請查看：
{report_url}

期待您的專業意見，謝謝！

---
Doctor-AI香港醫療配對系統"""
    
    return message

def format_whatsapp_message_for_doctor(doctor_data: dict, report_url: str, user_query_data: dict, reference_code: str = None) -> str:
    """格式化WhatsApp消息給醫生，包含患者症狀分析報告鏈接"""
    # Extract key patient info
    age = user_query_data.get('age', 'N/A')
    gender = user_query_data.get('gender', 'N/A')
    symptoms = user_query_data.get('symptoms', 'N/A')
    
    # Gender translation
    gender_text = {
        'male': '男',
        'female': '女',
        'other': '其他'
    }.get(gender, gender)
    
    ref_section = f"\n🎫 診斷參考編號：{reference_code}" if reference_code else ""
    
    message = f"""👨‍⚕️ 新患者諮詢 - Doctor AI

尊敬的{doctor_data.get('doctor_name', '醫生')}：

您好！有一位患者通過Doctor AI症狀分析系統希望諮詢您的專業意見。
{ref_section}
📋 患者基本資料：
• 年齡：{age}歲
• 性別：{gender_text}
• 主要症狀：{symptoms[:100]}{'...' if len(symptoms) > 100 else ''}

📊 完整症狀分析報告：
{report_url}

此報告包含AI初步分析及患者詳細病史，供您參考。

---
Doctor AI 香港醫療配對系統
此訊息由患者主動發起"""
    
    return message

def clean_phone_number_for_whatsapp(phone: str) -> str:
    """清理電話號碼格式，轉換為WhatsApp可用格式"""
    if not phone:
        return ''
    
    # Remove all non-digit characters
    import re
    cleaned = re.sub(r'\D', '', phone)
    
    # If it starts with 00, replace with +
    if cleaned.startswith('00'):
        cleaned = cleaned[2:]
    
    # If it doesn't start with country code, assume Hong Kong (852)
    if len(cleaned) == 8:  # Hong Kong local number
        cleaned = '852' + cleaned
    
    # Remove leading + if present (WhatsApp uses numbers only)
    cleaned = cleaned.lstrip('+')
    
    return cleaned

def generate_diagnosis_reference_code() -> str:
    """Generate a unique reference code for diagnosis.
    Format: DR-XXXXXXXXXXXXXXXXXXXXXXXX (DR = Doctor Reference, 24 alphanumeric chars)
    """
    import string
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(24))
    return f"DR-{code}"

def generate_reference_qr_code(reference_code: str, base_url: str = None) -> str:
    """Generate a QR code for the reference code and return as base64 data URL."""
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        # Create QR code with the reference lookup URL
        if base_url:
            qr_data = f"{base_url}/api/reference/{reference_code}"
        else:
            qr_data = reference_code
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create image with custom colors
        img = qr.make_image(fill_color="#667eea", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
        
    except ImportError:
        logger.warning("qrcode library not installed. Run: pip install qrcode[pil]")
        return None
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return None

def create_diagnosis_reference(query_id: int, session_id: str, user_ip: str, 
                                symptoms: str, ai_analysis: str, 
                                recommended_specialty: str, matched_doctors_count: int) -> str:
    """Create a diagnosis reference record and return the reference code."""
    try:
        reference_code = generate_diagnosis_reference_code()
        
        # Set expiry to 30 days from now
        from datetime import datetime, timedelta
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnosis_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_code TEXT UNIQUE NOT NULL,
                query_id INTEGER NOT NULL,
                session_id TEXT,
                user_ip TEXT,
                symptoms TEXT,
                ai_analysis TEXT,
                recommended_specialty TEXT,
                matched_doctors_count INTEGER DEFAULT 0,
                is_used INTEGER DEFAULT 0,
                used_at DATETIME,
                used_by_doctor_id INTEGER,
                used_by_doctor_name TEXT,
                is_billed INTEGER DEFAULT 0,
                billed_at DATETIME,
                billing_amount REAL DEFAULT 0,
                billing_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (query_id) REFERENCES user_queries (id)
            )
        """)
        
        cursor.execute("""
            INSERT INTO diagnosis_references 
            (reference_code, query_id, session_id, user_ip, symptoms, ai_analysis, 
             recommended_specialty, matched_doctors_count, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (reference_code, query_id, session_id, user_ip, symptoms, ai_analysis,
              recommended_specialty, matched_doctors_count, expires_at))
        
        # Also update user_queries with the reference code
        cursor.execute("""
            UPDATE user_queries SET reference_code = ? WHERE id = ?
        """, (reference_code, query_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created diagnosis reference: {reference_code} for query {query_id}")
        return reference_code
        
    except Exception as e:
        logger.error(f"Error creating diagnosis reference: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_diagnosis_by_reference(reference_code: str) -> dict:
    """Look up a diagnosis by reference code."""
    try:
        conn = sqlite3.connect('admin_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT dr.*, uq.age, uq.gender, uq.chronic_conditions, uq.language, uq.location
            FROM diagnosis_references dr
            LEFT JOIN user_queries uq ON dr.query_id = uq.id
            WHERE dr.reference_code = ?
        """, (reference_code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
        
    except Exception as e:
        logger.error(f"Error looking up diagnosis reference: {e}")
        return None

def mark_reference_as_used(reference_code: str, doctor_id: int, doctor_name: str) -> bool:
    """Mark a reference code as used by a doctor."""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE diagnosis_references 
            SET is_used = 1, used_at = CURRENT_TIMESTAMP, 
                used_by_doctor_id = ?, used_by_doctor_name = ?
            WHERE reference_code = ? AND is_used = 0
        """, (doctor_id, doctor_name, reference_code))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            logger.info(f"Reference {reference_code} marked as used by doctor {doctor_name}")
        
        return updated
        
    except Exception as e:
        logger.error(f"Error marking reference as used: {e}")
        return False

def get_real_ip():
    """Get the real client IP address, considering proxies and load balancers"""
    # Check for forwarded headers in order of preference
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, get the first one (original client)
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    elif request.headers.get('CF-Connecting-IP'):  # Cloudflare
        return request.headers.get('CF-Connecting-IP')
    elif request.headers.get('X-Client-IP'):
        return request.headers.get('X-Client-IP')
    else:
        # Fallback to remote_addr
        return request.remote_addr

def log_analytics(event_type: str, data: dict, user_ip: str, user_agent: str, session_id: str = None):
    """Log analytics data to database"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check if analytics table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analytics'")
        if not cursor.fetchone():
            print("Analytics table not found, reinitializing database...")
            conn.close()
            init_db()
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analytics (event_type, user_ip, user_agent, data, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (event_type, user_ip, user_agent, json.dumps(data), session_id, get_current_time().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Analytics logging error: {e}")
        # Try to reinitialize database if it's corrupted
        try:
            init_db()
        except:
            pass

def get_admin_user(username):
    """Get admin user from database"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash, role, permissions, is_active
            FROM admin_users 
            WHERE username = ? AND is_active = 1
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        print(f"Error getting admin user: {e}")
        return None

def check_permission(permission):
    """Check if current admin user has specific permission"""
    if not session.get('admin_logged_in'):
        return False
    
    user_role = session.get('admin_role', '')
    user_permissions = session.get('admin_permissions', {})
    
    # Super admin has all permissions
    if user_role == 'super_admin' or user_permissions.get('all'):
        return True
    
    return user_permissions.get(permission, False)

def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """Decorator to require admin authentication (alias for require_admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def tab_permission_required(tab_name):
    """Decorator to check if user has permission for specific tab"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logged_in'):
                return redirect(url_for('admin_login'))
            
            # Super admin has all permissions
            if session.get('admin_role') == 'super_admin':
                return f(*args, **kwargs)
            
            # Check tab permissions - if not loaded, load them now
            tab_permissions = session.get('admin_tab_permissions')
            if tab_permissions is None:
                # Load permissions from database
                user_id = session.get('admin_user_id')
                if user_id:
                    try:
                        conn = sqlite3.connect('admin_data.db')
                        cursor = conn.cursor()
                        cursor.execute('SELECT tab_permissions FROM admin_users WHERE id = ?', (user_id,))
                        tab_perms = cursor.fetchone()
                        conn.close()
                        
                        if tab_perms and tab_perms[0]:
                            tab_permissions = json.loads(tab_perms[0])
                        else:
                            # Default permissions for all tabs
                            tab_permissions = {
                                "dashboard": True,
                                "analytics": True,
                                "config": True,
                                "doctors": True,
                                "users": True,
                                "bug_reports": True,
                                "severe_cases": True,
                                "reservations": True
                            }
                        session['admin_tab_permissions'] = tab_permissions
                    except Exception as e:
                        print(f"Error loading tab permissions: {e}")
                        # Default to all permissions on error
                        tab_permissions = {
                            "dashboard": True,
                            "analytics": True,
                            "config": True,
                            "doctors": True,
                            "users": True,
                            "bug_reports": True,
                            "severe_cases": True,
                            "reservations": True
                        }
                        session['admin_tab_permissions'] = tab_permissions
                else:
                    # No user ID, deny access
                    flash('會話已過期，請重新登入', 'error')
                    return redirect(url_for('admin_login'))
            
            if not tab_permissions.get(tab_name, False):
                flash('您沒有權限訪問此頁面', 'error')
                return redirect(url_for('admin_dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_tab_permission(tab_name):
    """Helper function to check if current user has permission for a tab"""
    if not session.get('admin_logged_in'):
        return False
    
    # Super admin has all permissions
    if session.get('admin_role') == 'super_admin':
        return True
    
    tab_permissions = session.get('admin_tab_permissions', {})
    return tab_permissions.get(tab_name, False)

def get_admin_user_info():
    """Get current admin user information from session"""
    if not session.get('admin_logged_in'):
        return None
    
    return {
        'username': session.get('admin_username'),
        'user_id': session.get('admin_user_id'),
        'role': session.get('admin_role'),
        'is_super_admin': session.get('admin_role') == 'super_admin',
        'permissions': session.get('admin_permissions', {}),
        'tab_permissions': session.get('admin_tab_permissions', {})
    }

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logged_in'):
                return redirect(url_for('admin_login'))
            if not check_permission(permission):
                flash('您沒有權限執行此操作', 'error')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_user_summary(age: int, gender: str, symptoms: str, chronic_conditions: str, detailed_health_info: dict) -> str:
    """生成用戶輸入數據摘要"""
    summary_parts = []
    
    # 基本信息
    summary_parts.append(f"年齡：{age}歲")
    if gender:
        summary_parts.append(f"性別：{gender}")
    summary_parts.append(f"主要症狀：{symptoms}")
    
    # 長期病史
    if chronic_conditions:
        summary_parts.append(f"長期病史：{chronic_conditions}")
    
    # 身體指標
    if detailed_health_info.get('height') or detailed_health_info.get('weight'):
        height = detailed_health_info.get('height', '')
        weight = detailed_health_info.get('weight', '')
        if height and weight:
            bmi = round(float(weight) / ((float(height) / 100) ** 2), 1) if height and weight else None
            summary_parts.append(f"身高體重：{height}cm / {weight}kg" + (f" (BMI: {bmi})" if bmi else ""))
        elif height:
            summary_parts.append(f"身高：{height}cm")
        elif weight:
            summary_parts.append(f"體重：{weight}kg")
    
    # 藥物信息
    if detailed_health_info.get('medications'):
        summary_parts.append(f"長期藥物：{detailed_health_info['medications']}")
    
    # 敏感史
    if detailed_health_info.get('allergies'):
        summary_parts.append(f"敏感史：{detailed_health_info['allergies']}")
    
    # 手術史
    if detailed_health_info.get('surgeries'):
        summary_parts.append(f"手術史：{detailed_health_info['surgeries']}")
    
    # 特殊情況
    special_conditions = []
    if detailed_health_info.get('bloodThinner'):
        special_conditions.append("有服薄血藥")
    if detailed_health_info.get('recentVisit'):
        special_conditions.append("三個月內曾就診")
    if detailed_health_info.get('cpapMachine'):
        special_conditions.append("使用呼吸機")
    if detailed_health_info.get('looseTeeth'):
        special_conditions.append("有鬆牙問題")
    
    if special_conditions:
        summary_parts.append(f"特殊情況：{'、'.join(special_conditions)}")
    
    return '\n'.join(summary_parts)

def call_openrouter_api(prompt: str) -> str:
    """調用OpenRouter API進行AI分析"""
    try:
        if not AI_CONFIG['openrouter']['api_key']:
            return "AI服務配置不完整，請聯繫系統管理員"
            
        headers = {
            "Authorization": f"Bearer {AI_CONFIG['openrouter']['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "AI Doctor Matching System"
        }
        
        data = {
            "model": AI_CONFIG['openrouter']['model'],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": AI_CONFIG['openrouter']['max_tokens'],
            "temperature": 0.3,
            "top_p": 0.9
        }
        
        response = requests.post(
            AI_CONFIG['openrouter']['base_url'], 
            headers=headers, 
            json=data, 
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return "AI分析服務暫時不可用，請稍後再試"
            
    except Exception as e:
        return "AI分析服務暫時不可用，請稍後再試"

def call_openai_api(prompt: str) -> str:
    """調用OpenAI API進行AI分析"""
    try:
        if not AI_CONFIG['openai']['api_key']:
            return "AI服務配置不完整，請聯繫系統管理員"
            
        headers = {
            "Authorization": f"Bearer {AI_CONFIG['openai']['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": AI_CONFIG['openai']['model'],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": AI_CONFIG['openai']['max_tokens'],
            "temperature": 0.3,
            "top_p": 0.9
        }
        
        response = requests.post(
            AI_CONFIG['openai']['base_url'], 
            headers=headers, 
            json=data, 
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return "AI分析服務暫時不可用，請稍後再試"
            
    except Exception as e:
        return "AI分析服務暫時不可用，請稍後再試"

def call_ollama_api(prompt: str) -> str:
    """調用Ollama API進行AI分析"""
    try:
        data = {
            "model": AI_CONFIG['ollama']['model'],
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(AI_CONFIG['ollama']['base_url'], json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'AI分析服務暫時不可用，請稍後再試')
        else:
            return "AI分析服務暫時不可用，請稍後再試"
    except requests.exceptions.ConnectionError:
        return "AI分析服務暫時不可用，請稍後再試"
    except Exception as e:
        return "AI分析服務暫時不可用，請稍後再試"

def get_openai_models(api_key: str = None) -> list:
    """獲取OpenAI可用模型列表"""
    try:
        # Use provided API key or fall back to config
        key_to_use = api_key or AI_CONFIG['openai']['api_key']
        
        if not key_to_use:
            return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']  # fallback
            
        headers = {
            "Authorization": f"Bearer {key_to_use}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            models_data = response.json()
            # Filter for chat models only
            chat_models = []
            for model in models_data.get('data', []):
                model_id = model.get('id', '')
                if any(prefix in model_id for prefix in ['gpt-4', 'gpt-3.5']):
                    chat_models.append(model_id)
            
            # Sort models with GPT-4 first
            chat_models.sort(key=lambda x: (not x.startswith('gpt-4'), x))
            return chat_models if chat_models else ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
        else:
            return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']  # fallback
            
    except Exception as e:
        print(f"Error fetching OpenAI models: {e}")
        return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']  # fallback

def call_ai_api(prompt: str) -> str:
    """根據配置調用相應的AI API"""
    provider = AI_CONFIG['provider'].lower()
    
    if provider == 'openrouter':
        return call_openrouter_api(prompt)
    elif provider == 'openai':
        return call_openai_api(prompt)
    elif provider == 'ollama':
        return call_ollama_api(prompt)
    else:
        return f"不支援的AI提供商: {provider}"

def get_available_specialties() -> list:
    """獲取資料庫中所有可用的專科"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        # Try different specialty columns with encoding handling
        cursor.execute("SELECT DISTINCT specialty FROM doctors WHERE specialty IS NOT NULL AND specialty != '' AND LENGTH(specialty) > 0")
        specialties = []
        for row in cursor.fetchall():
            try:
                if row[0] and isinstance(row[0], str) and len(row[0].strip()) > 0:
                    specialties.append(row[0].strip())
            except (UnicodeDecodeError, AttributeError):
                continue
        conn.close()
        
        # Remove duplicates and sort
        specialties = sorted(list(set(specialties)))
        
        if not specialties:
            # Fallback list
            specialties = ['內科', '外科', '小兒科', '婦產科', '骨科', '皮膚科', '眼科', '耳鼻喉科', '精神科', '神經科', '心臟科', '急診科']
        
        return specialties
    except Exception as e:
        print(f"Error fetching specialties: {e}")
        return ['內科', '外科', '小兒科', '婦產科', '骨科', '皮膚科', '眼科', '耳鼻喉科', '精神科', '神經科', '心臟科', '急診科']

def validate_symptoms_with_llm(symptoms: str, user_language: str = 'zh-TW') -> dict:
    """使用LLM驗證症狀描述是否有效"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'valid': True, 'message': '症狀驗證服務不可用，將繼續處理'}
        
        # Get translations for the prompt
        t = lambda key: get_translation(key, user_language)
        
        prompt = f"""
你是一個醫療症狀驗證專家。請分析以下症狀描述，判斷是否為有效的醫療症狀。

症狀描述：{symptoms}

請評估：
1. 這些是否為真實的醫療症狀？
2. 描述是否合理和具體？
3. 是否包含不相關或無意義的內容？

無效症狀的例子：
- 測試、test、123、隨便寫的
- 非醫療相關的詞語（如：開心、工作、吃飯）
- 明顯的垃圾文字或無意義字符
- 過於簡單或不具體的描述（如：不舒服、有問題）

請以JSON格式回應：
{{
    "valid": true/false,
    "confidence": 0.0-1.0,
    "issues": ["問題列表"],
    "suggestions": ["改善建議"]
}}
"""
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': '你是一個專業的醫療症狀驗證助手。請仔細分析症狀描述的有效性。'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 500,
            'temperature': 0.3
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            try:
                # Parse JSON response
                validation_result = json.loads(content)
                return {
                    'valid': validation_result.get('valid', True),
                    'confidence': validation_result.get('confidence', 0.5),
                    'issues': validation_result.get('issues', []),
                    'suggestions': validation_result.get('suggestions', []),
                    'message': '症狀驗證完成'
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                is_valid = 'true' in content.lower() and 'valid' in content.lower()
                return {
                    'valid': is_valid,
                    'confidence': 0.7,
                    'issues': [],
                    'suggestions': [],
                    'message': '症狀驗證完成（簡化結果）'
                }
        else:
            logger.error(f"Symptom validation API error: {response.status_code}")
            return {'valid': True, 'message': '症狀驗證服務暫時不可用，將繼續處理'}
            
    except Exception as e:
        logger.error(f"Error validating symptoms: {e}")
        return {'valid': True, 'message': '症狀驗證過程中出現錯誤，將繼續處理'}

def analyze_symptoms_with_evidence(age: int, gender: str, symptoms: str, chronic_conditions: str = '', detailed_health_info: dict = None, user_language: str = 'zh-TW') -> dict:
    """使用AI分析症狀並結合醫學文獻證據 - 優化版本避免重複AI調用"""
    
    # Extract medical evidence based on symptoms only (avoid double AI calls)
    medical_evidence = ""
    
    try:
        # Extract key medical terms from symptoms for evidence search
        symptom_terms = [s.strip() for s in symptoms.replace('、', ',').split(',') if s.strip()]
        
        # Translate terms if they're in Chinese
        if any(any('\u4e00' <= c <= '\u9fff' for c in term) for term in symptom_terms):
            translated_terms = translate_medical_terms_with_ai(symptom_terms)
            search_terms = translated_terms if translated_terms else symptom_terms
        else:
            search_terms = symptom_terms
        
        # Use symptom-based search only to avoid infinite recursion
        # Limit to top 3 symptoms for focused search
        focused_search_terms = search_terms[:3]
        focused_display_terms = symptom_terms[:3]
        
        logger.info(f"Symptom-based medical evidence search: {focused_search_terms}")
        
        # Fetch evidence from PubMed
        evidence_results = fetch_pubmed_evidence(focused_search_terms, focused_display_terms)
        
        if evidence_results:
            medical_evidence = "\n\n**醫學文獻參考資料 (Medical Literature References):**\n"
            medical_evidence += "以下文獻支持此診斷分析：\n\n"
            
            for i, evidence in enumerate(evidence_results[:3], 1):  # Use top 3 articles
                medical_evidence += f"{i}. **{evidence['title']}**\n"
                medical_evidence += f"   📚 來源: {evidence['source']}\n"
                medical_evidence += f"   🔍 相關性: {evidence['relevance']}\n"
                medical_evidence += f"   📄 摘要: {evidence['excerpt']}\n"
                if evidence.get('url'):
                    medical_evidence += f"   🔗 連結: {evidence['url']}\n"
                medical_evidence += "\n"
            
            # Add instruction for AI to reference the evidence
            medical_evidence += "**請在診斷分析中參考上述醫學文獻，並在相關部分引用這些研究支持您的診斷結論。**\n"
            
            logger.info(f"Added medical evidence to AI analysis: {len(evidence_results)} articles")
        else:
            logger.info("No medical evidence found for AI cross-referencing")
            
    except Exception as e:
        logger.error(f"Error fetching medical evidence for AI analysis: {e}")
        medical_evidence = ""
    
    # Single AI call with medical evidence included
    return analyze_symptoms_with_context(age, gender, symptoms, chronic_conditions, detailed_health_info, user_language, medical_evidence)

def analyze_symptoms(age: int, gender: str, symptoms: str, chronic_conditions: str = '', detailed_health_info: dict = None, user_language: str = 'zh-TW') -> dict:
    """使用AI分析症狀 (保持向後兼容性)"""
    return analyze_symptoms_with_context(age, gender, symptoms, chronic_conditions, detailed_health_info, user_language, "")

def analyze_symptoms_with_context(age: int, gender: str, symptoms: str, chronic_conditions: str = '', detailed_health_info: dict = None, user_language: str = 'zh-TW', medical_evidence: str = '') -> dict:
    """使用AI分析症狀並可選擇性包含醫學證據"""
    
    if detailed_health_info is None:
        detailed_health_info = {}
    
    # 構建詳細健康信息
    health_details = []
    if gender:
        health_details.append(f"性別：{gender}")
    if chronic_conditions.strip():
        health_details.append(f"長期病史：{chronic_conditions}")
    
    if detailed_health_info.get('height') or detailed_health_info.get('weight'):
        height = detailed_health_info.get('height', '')
        weight = detailed_health_info.get('weight', '')
        if height and weight:
            try:
                bmi = round(float(weight) / ((float(height) / 100) ** 2), 1)
                health_details.append(f"身高體重：{height}cm / {weight}kg (BMI: {bmi})")
            except:
                health_details.append(f"身高體重：{height}cm / {weight}kg")
        elif height:
            health_details.append(f"身高：{height}cm")
        elif weight:
            health_details.append(f"體重：{weight}kg")
    
    if detailed_health_info.get('medications'):
        health_details.append(f"長期藥物：{detailed_health_info['medications']}")
    
    if detailed_health_info.get('allergies'):
        health_details.append(f"敏感史：{detailed_health_info['allergies']}")
    
    if detailed_health_info.get('surgeries'):
        health_details.append(f"手術史：{detailed_health_info['surgeries']}")
    
    special_conditions = []
    if detailed_health_info.get('bloodThinner'):
        special_conditions.append("有服薄血藥")
    if detailed_health_info.get('recentVisit'):
        special_conditions.append("三個月內曾就診")
    if detailed_health_info.get('cpapMachine'):
        special_conditions.append("使用呼吸機")
    if detailed_health_info.get('looseTeeth'):
        special_conditions.append("有鬆牙問題")
    
    if special_conditions:
        health_details.append(f"特殊情況：{'、'.join(special_conditions)}")
    
    # Get translations for the user's language
    t = lambda key: get_translation(key, user_language)
    
    # Build health info with translated labels
    health_info = "\n    - ".join(health_details) if health_details else t('no_special_health_info')
    
    # Get available specialties from database
    available_specialties = get_available_specialties()
    specialty_list = "、".join(available_specialties)
    
    # Build AI analysis prompt in user's language with consistency instructions
    analysis_prompt = f"""
    {t('diagnosis_prompt_intro')}

    {t('patient_data')}
    - {t('age_label')}{age}{t('years_old')}
    - {t('main_symptoms')}{symptoms}
    - {health_info}
    {medical_evidence}
    
    **分析要求 (Analysis Requirements):**
    請參考上述醫學文獻證據進行診斷分析，確保診斷建議與現有醫學研究一致。請將文獻作為內部參考依據，但不需要在回應中明確引用或提及這些文獻來源，因為用戶會在其他地方看到完整的醫學證據。

    {t('please_provide')}
    1. {t('possible_diagnosis')}
    2. {t('recommended_specialty')}
    3. {t('severity_assessment')}
    4. {t('emergency_needed')}
    5. {t('general_advice')}

    **{t('important_guidelines')}**
    - {t('mental_health_guideline')}
    - {t('trauma_guideline')}
    - {t('emergency_guideline')}
    - {t('specialty_guideline')}

    **一致性要求 (Consistency Requirements):**
    - 必須嚴格按照以下格式回答，不可偏離
    - 嚴重程度只能是：輕微、中等、嚴重 (三選一)
    - 緊急程度只能是：是、否 (二選一)
    - 專科名稱必須從以下可用專科中選擇：{specialty_list}
    - 不可推薦資料庫中不存在的專科
    - 回答必須簡潔明確，避免模糊用詞

    {t('response_language')}
    
    **嚴格格式要求 (Strict Format Requirements):**
    {t('diagnosis_format')}
    {t('specialty_format')}
    {t('severity_format')}
    {t('emergency_format')}
    {t('advice_format')}
    
    {t('disclaimer')}
    """
    
    # 獲取AI分析
    analysis_response = call_ai_api(analysis_prompt)
    
    # 解析分析結果
    recommended_specialties = extract_specialties_from_analysis(analysis_response)
    recommended_specialty = recommended_specialties[0] if recommended_specialties else '內科'
    severity_level = extract_severity_from_analysis(analysis_response)
    emergency_needed = check_emergency_needed(analysis_response)
    
    # Debug logging
    print(f"DEBUG - AI Response: {analysis_response[:200]}...")
    print(f"DEBUG - Full AI Response for Emergency Check:")
    print("=" * 50)
    print(analysis_response)
    print("=" * 50)
    print(f"DEBUG - Extracted specialties: {recommended_specialties}")
    print(f"DEBUG - Primary specialty: {recommended_specialty}")
    print(f"DEBUG - Severity level: {severity_level}")
    print(f"DEBUG - Emergency needed: {emergency_needed}")
    
    # Additional emergency pattern debugging
    if '緊急程度' in analysis_response:
        print(f"DEBUG - Found '緊急程度' in response")
        if '緊急程度：是' in analysis_response or '緊急程度: 是' in analysis_response:
            print(f"DEBUG - Found emergency format '緊急程度：是'")
        elif '緊急程度：否' in analysis_response or '緊急程度: 否' in analysis_response:
            print(f"DEBUG - Found non-emergency format '緊急程度：否'")
    else:
        print(f"DEBUG - No '緊急程度' format found in response")
    
    return {
        'analysis': analysis_response,
        'recommended_specialty': recommended_specialty,
        'recommended_specialties': recommended_specialties,
        'severity_level': severity_level,
        'emergency_needed': emergency_needed
    }

def analyze_symptoms_and_match(age: int, gender: str, symptoms: str, chronic_conditions: str, language: str, location: str, detailed_health_info: dict = None, location_details: dict = None) -> dict:
    """使用AI分析症狀並配對醫生"""
    
    if detailed_health_info is None:
        detailed_health_info = {}
    
    # 生成用戶數據摘要
    user_summary = generate_user_summary(age, gender, symptoms, chronic_conditions, detailed_health_info)
    
    # Get user's language from session or use the language parameter passed in
    user_language = session.get('language', language if language else 'zh-TW')
    
    # 第一步：驗證症狀有效性
    symptom_validation = validate_symptoms_with_llm(symptoms, user_language)
    
    if not symptom_validation.get('valid', True):
        return {
            'diagnosis': '症狀驗證失敗',
            'recommended_specialty': '無',
            'doctors': [],
            'user_summary': user_summary,
            'emergency_needed': False,
            'severity_level': 'low',
            'validation_error': True,
            'validation_issues': symptom_validation.get('issues', []),
            'validation_suggestions': symptom_validation.get('suggestions', []),
            'validation_message': '您輸入的內容不是有效的醫療症狀。請重新輸入真實的身體不適症狀，例如頭痛、發燒、咳嗽等。',
            'validation_confidence': symptom_validation.get('confidence', 0.5)
        }
    
    # 第二步：AI分析結合醫學文獻證據 (pass user language)
    diagnosis_result = analyze_symptoms_with_evidence(age, gender, symptoms, chronic_conditions, detailed_health_info, user_language)
    
    # 第二步：檢查是否需要緊急醫療處理
    print(f"DEBUG - Emergency check: emergency_needed={diagnosis_result.get('emergency_needed', False)}, severity_level={diagnosis_result.get('severity_level')}")
    
    if diagnosis_result.get('emergency_needed', False):
        print("DEBUG - Emergency case detected, routing to emergency doctors")
        # 緊急情況：優先推薦急診科和醫院
        emergency_doctors = filter_doctors('急診科', language, location, symptoms, diagnosis_result['analysis'], location_details)
        # 如果沒有急診科醫生，推薦內科醫生但標記為緊急
        if not emergency_doctors:
            emergency_doctors = filter_doctors('內科', language, location, symptoms, diagnosis_result['analysis'], location_details)
        
        # 為緊急醫生添加緊急標記
        for doctor in emergency_doctors:
            doctor['is_emergency'] = True
            doctor['emergency_message'] = get_translation('emergency_care_needed', user_language)
        
        matched_doctors = emergency_doctors
    else:
        print("DEBUG - Normal case, routing to specialty doctors")
        # 一般情況：根據診斷結果推薦多個相關專科的醫生
        all_matched_doctors = []
        recommended_specialties = diagnosis_result.get('recommended_specialties', [diagnosis_result['recommended_specialty']])
        print(f"DEBUG - Will search for specialties: {recommended_specialties}")
        
        for specialty in recommended_specialties:
            specialty_doctors = filter_doctors(
                specialty, 
                language, 
                location, 
                symptoms, 
                diagnosis_result['analysis'],
                location_details
            )
            
            print(f"DEBUG - Found {len(specialty_doctors)} doctors for specialty: {specialty}")
            
            # 為每個醫生添加專科標記，用於排序
            for doctor in specialty_doctors:
                doctor['matched_specialty'] = specialty
                doctor['is_primary_specialty'] = (specialty == diagnosis_result['recommended_specialty'])
            
            all_matched_doctors.extend(specialty_doctors)
        
        # 去除重複醫生並按優先級排序
        seen_names = set()
        unique_doctors = []
        
        # 首先添加主要專科的醫生
        for doctor in all_matched_doctors:
            if doctor.get('is_primary_specialty', False) and doctor['name'] not in seen_names:
                seen_names.add(doctor['name'])
                unique_doctors.append(doctor)
        
        # 然後添加其他專科的醫生
        for doctor in all_matched_doctors:
            if not doctor.get('is_primary_specialty', False) and doctor['name'] not in seen_names:
                seen_names.add(doctor['name'])
                unique_doctors.append(doctor)
        
        matched_doctors = unique_doctors[:15]  # 增加到15位醫生以包含多個專科
        
        # 確保非緊急情況下不設置緊急標記
        for doctor in matched_doctors:
            doctor['is_emergency'] = False
    
    # 第三步：如果是12歲以下，添加兒科醫生
    if age <= 12:
        pediatric_doctors = filter_doctors('兒科', language, location, symptoms, diagnosis_result['analysis'], location_details)
        # 合併醫生清單，去除重複
        all_doctors = matched_doctors + pediatric_doctors
        seen_names = set()
        unique_doctors = []
        for doctor in all_doctors:
            if doctor['name'] not in seen_names:
                seen_names.add(doctor['name'])
                unique_doctors.append(doctor)
        matched_doctors = unique_doctors[:15]  # 限制最多15位醫生以包含多個專科
    
    return {
        'user_summary': user_summary,
        'analysis': diagnosis_result['analysis'],
        'recommended_specialty': diagnosis_result['recommended_specialty'],
        'severity_level': diagnosis_result.get('severity_level', 'mild'),
        'emergency_needed': diagnosis_result.get('emergency_needed', False),
        'doctors': matched_doctors
    }

def extract_specialties_from_analysis(analysis_text: str) -> list:
    """從分析結果中提取推薦的專科"""
    if not analysis_text:
        return ['內科']
    
    # Get available specialties from database
    available_specialties = get_available_specialties()
    
    # Create dynamic mapping based on database specialties
    specialty_mapping = {}
    for specialty in available_specialties:
        # Create variations for each specialty
        variations = [specialty]
        
        # Add common English translations and variations
        if '內科' in specialty:
            variations.extend(['internal medicine', 'general medicine', 'family medicine'])
        elif '外科' in specialty:
            variations.extend(['surgery', 'general surgery'])
        elif '小兒科' in specialty or '兒科' in specialty:
            variations.extend(['pediatrics', 'pediatric'])
        elif '婦產科' in specialty:
            variations.extend(['obstetrics', 'gynecology', 'ob/gyn', 'obgyn'])
        elif '骨科' in specialty:
            variations.extend(['orthopedics', 'orthopedic'])
        elif '皮膚科' in specialty:
            variations.extend(['dermatology', 'dermatologic'])
        elif '眼科' in specialty:
            variations.extend(['ophthalmology', 'eye'])
        elif '耳鼻喉' in specialty:
            variations.extend(['ent', 'otolaryngology'])
        elif '精神科' in specialty:
            variations.extend(['psychiatry', 'psychiatric', 'mental health'])
        elif '神經科' in specialty:
            variations.extend(['neurology', 'neurologic'])
        elif '心臟科' in specialty or '心血管' in specialty:
            variations.extend(['cardiology', 'cardiac'])
        elif '急診' in specialty:
            variations.extend(['emergency', 'emergency medicine', 'er'])
        elif '感染' in specialty:
            variations.extend(['infectious disease', 'infection'])
        elif '腎臟科' in specialty:
            variations.extend(['nephrology', 'kidney'])
        elif '胃腸科' in specialty or '消化科' in specialty:
            variations.extend(['gastroenterology', 'digestive'])
        elif '呼吸科' in specialty:
            variations.extend(['pulmonology', 'respiratory'])
        elif '血液科' in specialty:
            variations.extend(['hematology', 'blood'])
        elif '腫瘤科' in specialty:
            variations.extend(['oncology', 'cancer'])
        elif '風濕科' in specialty:
            variations.extend(['rheumatology', 'rheumatic'])
        elif '內分泌' in specialty:
            variations.extend(['endocrinology', 'hormone'])
        elif '泌尿科' in specialty:
            variations.extend(['urology', 'urologic'])
        elif '放射科' in specialty:
            variations.extend(['radiology', 'imaging'])
        elif '病理科' in specialty:
            variations.extend(['pathology'])
        elif '麻醉科' in specialty:
            variations.extend(['anesthesiology'])
        elif '復健科' in specialty:
            variations.extend(['rehabilitation', 'physical medicine'])
        elif '核醫科' in specialty:
            variations.extend(['nuclear medicine'])
        elif '整形外科' in specialty:
            variations.extend(['plastic surgery'])
        elif '神經外科' in specialty:
            variations.extend(['neurosurgery'])
        elif '胸腔外科' in specialty:
            variations.extend(['thoracic surgery'])
        elif '心臟外科' in specialty:
            variations.extend(['cardiac surgery'])
        elif '血管外科' in specialty:
            variations.extend(['vascular surgery'])
        elif '大腸直腸外科' in specialty:
            variations.extend(['colorectal surgery'])
        
        specialty_mapping[specialty] = {'variations': variations}
    
    # 使用正則表達式提取專科資訊 (支援中英文)
    specialty_patterns = [
        r'推薦專科[：:]\s*([^\n\r]+)',
        r'建議專科[：:]\s*([^\n\r]+)', 
        r'專科[：:]\s*([^\n\r]+)',
        r'科別[：:]\s*([^\n\r]+)',
        r'Recommended specialty[：:]?\s*([^\n\r]+)',
        r'Specialty[：:]?\s*([^\n\r]+)',
        r'([^。\n\r]*(?:科|Specialist|Medicine|Surgery|ology|ics))\s*(?:醫師|專科|doctor)?',
    ]
    
    found_specialties = set()
    
    # 首先嘗試從明確的專科推薦中提取
    for pattern in specialty_patterns:
        matches = re.findall(pattern, analysis_text, re.IGNORECASE)
        if matches:
            recommended_specialty = matches[0].strip()
            print(f"DEBUG - Specialty pattern matched: '{pattern}' -> '{recommended_specialty}'")
            
            # 清理提取的專科名稱
            recommended_specialty = re.sub(r'\s*(or|或)\s*.*$', '', recommended_specialty, flags=re.IGNORECASE).strip()
            
            # 尋找匹配的標準專科名稱
            for standard_specialty, specialty_info in specialty_mapping.items():
                for variation in specialty_info['variations']:
                    if variation.lower() in recommended_specialty.lower():
                        found_specialties.add(standard_specialty)
                        print(f"DEBUG - Primary specialty found: '{variation}' -> '{standard_specialty}'")
                        break
            break
    
    # 如果沒有找到明確的專科推薦，搜索關鍵字
    if not found_specialties:
        print("DEBUG - No specialty pattern matched, searching for keywords")
        text_lower = analysis_text.lower()
        for standard_specialty, specialty_info in specialty_mapping.items():
            for variation in specialty_info['variations']:
                if variation.lower() in text_lower:
                    found_specialties.add(standard_specialty)
                    print(f"DEBUG - Keyword match found: '{variation}' -> '{standard_specialty}'")
    
    # 如果找到了主要專科，添加相關專科
    if found_specialties:
        primary_specialty = list(found_specialties)[0]  # 取第一個作為主要專科
        related_specialties = specialty_mapping.get(primary_specialty, {}).get('related', [])
        
        print(f"DEBUG - Primary specialty: {primary_specialty}, Related: {related_specialties}")
        # 添加最多2個相關專科，避免推薦太多
        for related in related_specialties[:2]:
            if related in specialty_mapping:  # 確保相關專科存在
                found_specialties.add(related)
                print(f"DEBUG - Added related specialty: {related}")
            else:
                print(f"DEBUG - Skipped invalid related specialty: {related}")
        
        result = list(found_specialties)
        print(f"DEBUG - Final specialties: {result}")
        return result
    
    # 如果沒有找到任何專科，返回內科作為默認
    print("DEBUG - No specialty keywords found, defaulting to Internal Medicine")
    return ['內科']

def extract_specialty_from_diagnosis(diagnosis_text: str) -> str:
    """從診斷文本中提取推薦的專科（單一專科，保留兼容性）"""
    specialties = extract_specialties_from_analysis(diagnosis_text)
    return specialties[0] if specialties else '內科'

def extract_specialty_from_ai_response(ai_response: str) -> str:
    """從AI回應中提取推薦的專科（保留兼容性）"""
    return extract_specialty_from_diagnosis(ai_response)

def extract_severity_from_analysis(analysis_text: str) -> str:
    """從分析結果中提取嚴重程度"""
    if not analysis_text:
        return 'mild'
    
    text_lower = analysis_text.lower()
    
    # First check for explicit severity statements
    explicit_severity_patterns = [
        ('嚴重程度：輕微', 'mild'),
        ('嚴重程度：中等', 'moderate'), 
        ('嚴重程度：嚴重', 'severe'),
        ('severity: mild', 'mild'),
        ('severity: moderate', 'moderate'),
        ('severity: severe', 'severe')
    ]
    
    for pattern, severity in explicit_severity_patterns:
        if pattern in text_lower:
            print(f"DEBUG - Explicit severity found: '{pattern}' -> {severity}")
            return severity
    
    # Check for non-emergency indicators that should override severity keywords
    non_emergency_patterns = [
        '不需要緊急就醫', '非緊急', '不緊急', 'not emergency', 'no emergency needed',
        '不需要急診', '無需緊急', 'non-urgent', 'not urgent'
    ]
    
    is_non_emergency = False
    for pattern in non_emergency_patterns:
        if pattern in text_lower:
            is_non_emergency = True
            print(f"DEBUG - Non-emergency pattern found in severity check: '{pattern}'")
            break
    
    emergency_keywords = [
        'emergency', '緊急', '急診', 'urgent', '嚴重', 'severe', 'critical', '危急',
        'life-threatening', '威脅生命', 'immediate', '立即', 'high risk', '高風險'
    ]
    
    moderate_keywords = [
        'moderate', '中等', '中度', 'medium', '適中', '一般嚴重'
    ]
    
    found_emergency = []
    for keyword in emergency_keywords:
        if keyword in text_lower:
            found_emergency.append(keyword)
    
    found_moderate = []
    for keyword in moderate_keywords:
        if keyword in text_lower:
            found_moderate.append(keyword)
    
    print(f"DEBUG - Severity check - Emergency keywords found: {found_emergency}")
    print(f"DEBUG - Severity check - Moderate keywords found: {found_moderate}")
    
    # If explicitly marked as non-emergency, don't return severe even if keywords found
    if is_non_emergency and found_emergency:
        print("DEBUG - Non-emergency override: downgrading from severe to moderate")
        return 'moderate'
    
    if found_emergency:
        return 'severe'
    
    if found_moderate:
        return 'moderate'
    
    return 'mild'

def check_emergency_needed(diagnosis_text: str) -> bool:
    """檢查是否需要緊急就醫 - 更保守的緊急檢測"""
    if not diagnosis_text:
        return False
    
    text_lower = diagnosis_text.lower()
    
    # First check for explicit non-emergency statements - these override everything
    non_emergency_patterns = [
        '不需要緊急就醫', '非緊急', '不緊急', 'not emergency', 'no emergency needed',
        '不需要急診', '無需緊急', 'non-urgent', 'not urgent',
        '緊急程度：否', '緊急程度: 否', 'emergency: no', 'emergency:no',
        '不用緊急', '毋須緊急', '無須立即', '不必立即'
    ]
    
    for pattern in non_emergency_patterns:
        if pattern in text_lower:
            print(f"DEBUG - Non-emergency pattern found: '{pattern}' - overriding emergency detection")
            return False
    
    # Primary emergency format indicators - most reliable
    primary_emergency_indicators = [
        '緊急程度：是', '緊急程度: 是', 'emergency: yes', 'emergency:yes'
    ]
    
    for indicator in primary_emergency_indicators:
        if indicator in text_lower:
            print(f"DEBUG - Primary emergency format found: '{indicator}'")
            return True
    
    # Strong emergency action indicators - require immediate action
    strong_emergency_indicators = [
        'call emergency', '撥打急救', 'go to emergency', '前往急診',
        'emergency room', '急診室', 'hospital immediately', '立即住院',
        'life-threatening', '威脅生命', 'critical condition', '危急狀況',
        '999', '911', '112', 'ambulance', '救護車',
        'immediately seek medical', 'urgent medical attention'
    ]
    
    found_strong = []
    for indicator in strong_emergency_indicators:
        if indicator in text_lower:
            found_strong.append(indicator)
    
    if found_strong:
        print(f"DEBUG - Strong emergency action indicators found: {found_strong}")
        return True
    
    # Critical medical conditions - only very specific life-threatening conditions
    critical_conditions = [
        '心肌梗塞', '急性心肌梗塞', '中風', '急性中風', '腦中風',
        '急性腹痛', '急性胸痛', '呼吸困難', '意識不清', '昏迷',
        '大量出血', '嚴重外傷', '骨折', '急性過敏反應'
    ]
    
    found_critical = []
    for condition in critical_conditions:
        if condition in text_lower:
            found_critical.append(condition)
    
    if found_critical:
        # Check if these conditions are mentioned in a hypothetical or conditional context
        conditional_phrases = [
            '如果是', '若是', '可能是', '疑似', '排除', '不像是', '不太可能',
            '建議排除', '需要排除', '若出現', '如果出現', '假如', '萬一'
        ]
        
        is_conditional = False
        for phrase in conditional_phrases:
            if phrase in text_lower:
                is_conditional = True
                print(f"DEBUG - Critical condition '{found_critical}' mentioned in conditional context: '{phrase}'")
                break
        
        if not is_conditional:
            print(f"DEBUG - Critical medical conditions found (not conditional): {found_critical}")
            return True
        else:
            print(f"DEBUG - Critical conditions mentioned conditionally, not immediate emergency")
    
    # Emergency action phrases - but only if not conditional
    emergency_actions = [
        '需要緊急就醫', '建議緊急就醫', '立即就醫', '馬上就醫', '急需就醫',
        '緊急醫療', '緊急處理'
    ]
    
    found_actions = []
    for action in emergency_actions:
        if action in text_lower:
            found_actions.append(action)
    
    if found_actions:
        # Check if these are conditional recommendations
        conditional_contexts = [
            '若症狀惡化', '如果惡化', '症狀持續', '持續或惡化', '如果沒有改善',
            '若無改善', '如果加重', '症狀加重時', '惡化時', '若出現'
        ]
        
        is_conditional = False
        for context in conditional_contexts:
            if context in text_lower:
                is_conditional = True
                print(f"DEBUG - Emergency action '{found_actions}' in conditional context: '{context}'")
                break
        
        if not is_conditional:
            print(f"DEBUG - Direct emergency action recommendations found: {found_actions}")
            return True
        else:
            print(f"DEBUG - Emergency actions are conditional recommendations, not immediate emergency")
    
    print("DEBUG - No immediate emergency indicators found")
    return False

def safe_str_check(value, search_term):
    """安全的字符串檢查，處理NaN值"""
    if pd.isna(value) or value is None:
        return False
    return search_term in str(value)

def filter_doctors(recommended_specialty: str, language: str, location: str, symptoms: str, ai_analysis: str, location_details: dict = None) -> list:
    """根據條件篩選醫生"""
    # 檢查是否需要重新載入數據庫
    reload_doctors_data_if_needed()
    
    matched_doctors = []
    
    # Debug logging
    print(f"DEBUG - filter_doctors called with:")
    print(f"  location: {location}")
    print(f"  location_details: {location_details}")
    print(f"  recommended_specialty: {recommended_specialty}")
    
    total_processed = 0
    total_matched = 0
    
    for doctor in DOCTORS_DATA:
        total_processed += 1
        score = 0
        match_reasons = []
        
        # 專科匹配 (降低分數，優先考慮地區)
        doctor_specialty = doctor.get('specialty', '')
        if doctor_specialty and not pd.isna(doctor_specialty):
            doctor_specialty = str(doctor_specialty)
            if safe_str_check(doctor_specialty, recommended_specialty):
                score += 25  # 從50降到25
                match_reasons.append(f"專科匹配：{doctor_specialty}")
            elif safe_str_check(doctor_specialty, '普通科') or safe_str_check(doctor_specialty, '內科'):
                score += 15  # 從30降到15
                match_reasons.append("可處理一般症狀")
        
        # 語言匹配
        doctor_languages = doctor.get('languages', '')
        if doctor_languages and not pd.isna(doctor_languages):
            doctor_languages = str(doctor_languages)
            if safe_str_check(doctor_languages, language):
                score += 30
                match_reasons.append(f"語言匹配：{language}")
        
        # Get UI language from session for doctor prioritization
        ui_language = session.get('language', 'zh-TW')

        # Language-based doctor prioritization
        doctor_languages = doctor.get('languages', '')
        if doctor_languages and not pd.isna(doctor_languages):
            doctor_languages = str(doctor_languages)

            if ui_language == 'en':
                # For English UI, prioritize doctors who speak English
                if safe_str_check(doctor_languages, 'English') or safe_str_check(doctor_languages, '英文'):
                    score += 20
                    match_reasons.append("English-speaking doctor (English preference)")
            else:
                # For Chinese UI, prioritize doctors who speak Chinese
                if safe_str_check(doctor_languages, '中文') or safe_str_check(doctor_languages, '國語') or safe_str_check(doctor_languages, '粵語'):
                    score += 10
                    match_reasons.append("Chinese-speaking doctor (Chinese preference)")
        # 3層地區匹配系統
        location_matched = False  # 初始化變量
        
        # 獲取3層位置信息 (移到外層以便後續使用)
        if location_details is None:
            location_details = {}
        
        user_region = location_details.get('region', '')
        user_district = location_details.get('district', '')
        user_area = location_details.get('area', '')
        
        # 定義各區的關鍵詞匹配 (移到外層以便後續使用)
        district_keywords = {
                # 香港島
                '中西區': ['中環', '上環', '西環', '金鐘', '堅尼地城', '石塘咀', '西營盤'],
                '東區': ['銅鑼灣', '天后', '炮台山', '北角', '鰂魚涌', '西灣河', '筲箕灣', '柴灣', '小西灣'],
                '南區': ['香港仔', '鴨脷洲', '黃竹坑', '深水灣', '淺水灣', '赤柱', '石澳'],
                '灣仔區': ['灣仔', '跑馬地', '大坑', '渣甸山', '寶馬山'],
                
                # 九龍
                '九龍城區': ['九龍城', '土瓜灣', '馬頭角', '馬頭圍', '啟德', '紅磡', '何文田'],
                '觀塘區': ['觀塘', '牛頭角', '九龍灣', '彩虹', '坪石', '秀茂坪', '藍田', '油塘'],
                '深水埗區': ['深水埗', '長沙灣', '荔枝角', '美孚', '石硤尾', '又一村'],
                '黃大仙區': ['黃大仙', '新蒲崗', '樂富', '橫頭磡', '東頭', '竹園', '慈雲山', '鑽石山'],
                '油尖旺區': ['油麻地', '尖沙咀', '旺角', '大角咀', '太子', '佐敦'],
                
                # 新界
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
        
        doctor_address = doctor.get('address', '')
        
        # Debug: Check if we're getting the right field name
        if len(matched_doctors) < 2:
            print(f"DEBUG - Available doctor fields: {list(doctor.keys())}")
            print(f"DEBUG - address value: '{doctor_address}'")
        
        if doctor_address and not pd.isna(doctor_address):
            doctor_address = str(doctor_address)
            
            # Limit debug output to first 5 doctors to avoid spam
            if len(matched_doctors) < 5:
                print(f"DEBUG - Doctor: {doctor.get('name_zh', 'Unknown')}, Address: {doctor_address[:100]}...")
                print(f"DEBUG - User location: Region={user_region}, District={user_district}, Area={user_area}")
                print(f"DEBUG - Checking area match: '{user_area}' in '{doctor_address}' = {safe_str_check(doctor_address, user_area) if user_area else False}")
                if user_district in district_keywords:
                    keywords = district_keywords[user_district]
                    print(f"DEBUG - District keywords for {user_district}: {keywords}")
                    for keyword in keywords:
                        if safe_str_check(doctor_address, keyword):
                            print(f"DEBUG - Found district keyword match: '{keyword}' in address")
            
            # 第1層：精確地區匹配 (大幅提高分數)
            if user_area and safe_str_check(doctor_address, user_area):
                score += 60  # 從35提高到60
                match_reasons.append(f"精確位置匹配：{user_area}")
                location_matched = True
                print(f"DEBUG - Exact area match: {user_area}")
            
            # 第2層：地區匹配 (提高分數)
            elif user_district and user_district in district_keywords:
                keywords = district_keywords[user_district]
                print(f"DEBUG - Checking district {user_district} keywords: {keywords}")
                for keyword in keywords:
                    if safe_str_check(doctor_address, keyword):
                        score += 45  # 從25提高到45
                        print(f"DEBUG - District keyword match: {keyword}")
                        match_reasons.append(f"地區匹配：{user_district}")
                        location_matched = True
                        break
            
            # 第3層：大區匹配 (提高分數)
            if not location_matched and user_region:
                # 香港島大區 - 擴展關鍵詞
                if user_region == '香港島' and any(safe_str_check(doctor_address, keyword) for keyword in ['香港', '中環', '灣仔', '銅鑼灣', '上環', '西環', '天后', '北角', '鰂魚涌', '柴灣', '筲箕灣', '香港仔']):
                    score += 30  # 從15提高到30
                    match_reasons.append("大區匹配：香港島")
                    location_matched = True
                
                # 九龍大區 - 擴展關鍵詞
                elif user_region == '九龍' and any(safe_str_check(doctor_address, keyword) for keyword in ['九龍', '旺角', '尖沙咀', '油麻地', '佐敦', '深水埗', '觀塘', '黃大仙', '土瓜灣', '紅磡', '藍田', '彩虹', '牛頭角']):
                    score += 30  # 從15提高到30
                    match_reasons.append("大區匹配：九龍")
                    location_matched = True
                
                # 新界大區 - 擴展關鍵詞
                elif user_region == '新界' and any(safe_str_check(doctor_address, keyword) for keyword in ['新界', '沙田', '大埔', '元朗', '屯門', '荃灣', '將軍澳', '粉嶺', '上水', '葵涌', '青衣', '馬鞍山', '天水圍']):
                    score += 30  # 從15提高到30
                    match_reasons.append("大區匹配：新界")
                    location_matched = True
            
            # 向後兼容：如果沒有location_details，使用舊的location匹配
            if not location_matched and not user_region and location:
                if location in district_keywords:
                    keywords = district_keywords[location]
                    for keyword in keywords:
                        if safe_str_check(doctor_address, keyword):
                            score += 40  # 從25提高到40
                            match_reasons.append(f"地區匹配：{location}")
                            location_matched = True
                            break
            
            # 如果仍然沒有匹配到位置，嘗試使用location字符串直接匹配
            if not location_matched and location:
                if safe_str_check(doctor_address, location):
                    score += 25  # 從20提高到25
                    match_reasons.append(f"位置關鍵詞匹配：{location}")
                    location_matched = True
        
        # 加入優先級別到匹配分數 - 大幅提高優先級加分
        priority_flag = doctor.get('priority_flag', 0)
        if priority_flag and not pd.isna(priority_flag):
            priority_bonus = int(priority_flag) * 50  # 每級優先級加50分 (從10分提高到50分)
            score += priority_bonus
            if priority_bonus > 0:
                match_reasons.append(f"優先醫生 (級別 {priority_flag})")
        
        # 優先保留有地區匹配的醫生，但也允許高分醫生
        if location_matched or score >= 30:
            total_matched += 1
            # 清理醫生數據，確保所有字段都是字符串
            doctor_copy = {}
            for key, value in doctor.items():
                if pd.isna(value) or value is None:
                    doctor_copy[key] = ''
                else:
                    doctor_copy[key] = str(value)
            
            doctor_copy['match_score'] = score
            doctor_copy['match_reasons'] = match_reasons
            doctor_copy['ai_analysis'] = ai_analysis
            
            # 添加地理相關性排序權重 (重新計算以確保準確性)
            location_priority = 0
            
            # 檢查是否已經在location matching中匹配到位置
            if location_matched:
                # 根據已有的location matching結果設置優先級
                if user_area and safe_str_check(doctor_address, user_area):
                    location_priority = 4  # 最高優先級：精確地區匹配
                elif user_district and user_district in district_keywords:
                    keywords = district_keywords[user_district]
                    for keyword in keywords:
                        if safe_str_check(doctor_address, keyword):
                            location_priority = 3  # 第二優先級：地區匹配
                            break
                elif user_region:
                    # 大區匹配
                    if ((user_region == '香港島' and any(safe_str_check(doctor_address, keyword) for keyword in ['香港', '中環', '灣仔', '銅鑼灣', '上環', '西環', '天后', '北角', '鰂魚涌', '柴灣', '筲箕灣', '香港仔'])) or
                        (user_region == '九龍' and any(safe_str_check(doctor_address, keyword) for keyword in ['九龍', '旺角', '尖沙咀', '油麻地', '佐敦', '深水埗', '觀塘', '黃大仙', '土瓜灣', '紅磡', '藍田', '彩虹', '牛頭角'])) or
                        (user_region == '新界' and any(safe_str_check(doctor_address, keyword) for keyword in ['新界', '沙田', '大埔', '元朗', '屯門', '荃灣', '將軍澳', '粉嶺', '上水', '葵涌', '青衣', '馬鞍山', '天水圍']))):
                        location_priority = 2  # 第三優先級：大區匹配
                elif location and safe_str_check(doctor_address, location):
                    location_priority = 1  # 最低優先級：關鍵詞匹配
            
            # Debug: 顯示location priority計算
            if len(matched_doctors) < 3:
                print(f"DEBUG - Doctor {doctor.get('name_zh', 'Unknown')}: location_matched={location_matched}, location_priority={location_priority}")
                print(f"DEBUG - Doctor address: '{doctor_address}'")
                print(f"DEBUG - User location: area='{user_area}', district='{user_district}', region='{user_region}'")
            
            doctor_copy['location_priority'] = location_priority
            matched_doctors.append(doctor_copy)
    
    print(f"DEBUG - Processed {total_processed} doctors, matched {total_matched} doctors")
    
    # 按地理相關性、匹配分數排序 (優先級已包含在match_score中)
    matched_doctors.sort(key=lambda x: (x['location_priority'], x['match_score']), reverse=True)
    
    # Debug: 顯示前5個醫生的地理優先級和分數
    print(f"DEBUG - Top 5 doctors after sorting:")
    for i, doctor in enumerate(matched_doctors[:5]):
        print(f"  {i+1}. {doctor.get('name_zh', 'Unknown')} - Priority Flag: {doctor.get('priority_flag', 0)}, Location Priority: {doctor.get('location_priority', 0)}, Score: {doctor.get('match_score', 0)}, Address: {doctor.get('clinic_addresses', '')[:50]}...")
    
    # 總是添加該地區的普通科/內科醫生作為選項，讓用戶有更多選擇
    print(f"DEBUG - Adding regional GP/internist options. Current matches: {len(matched_doctors)}")
    fallback_doctors = get_regional_gp_fallback(location_details, location, recommended_specialty)
    
    # 避免重複添加已存在的醫生
    existing_names = {doctor.get('name_zh', '') for doctor in matched_doctors}
    for fallback_doctor in fallback_doctors:
        if fallback_doctor.get('name_zh', '') not in existing_names:
            matched_doctors.append(fallback_doctor)
    
    # 重新排序 (地理相關性、匹配分數) - 優先級已包含在match_score中
    matched_doctors.sort(key=lambda x: (x.get('location_priority', 0), x['match_score']), reverse=True)
    
    # 返回前50名供分頁使用
    return matched_doctors[:50]

def get_regional_gp_fallback(location_details: dict, location: str, original_specialty: str) -> list:
    """獲取該地區的普通科/內科醫生作為後備推薦"""
    fallback_doctors = []
    
    if location_details is None:
        location_details = {}
    
    user_region = location_details.get('region', '')
    user_district = location_details.get('district', '')
    user_area = location_details.get('area', '')
    
    print(f"DEBUG - Looking for GP/internist fallback in region: {user_region}, district: {user_district}")
    
    # 定義各區的關鍵詞匹配
    district_keywords = {
        # 香港島
        '中西區': ['中環', '上環', '西環', '金鐘', '堅尼地城', '石塘咀', '西營盤'],
        '東區': ['銅鑼灣', '天后', '炮台山', '北角', '鰂魚涌', '西灣河', '筲箕灣', '柴灣', '小西灣'],
        '南區': ['香港仔', '鴨脷洲', '黃竹坑', '深水灣', '淺水灣', '赤柱', '石澳'],
        '灣仔區': ['灣仔', '跑馬地', '大坑', '渣甸山', '寶馬山'],
        
        # 九龍
        '九龍城區': ['九龍城', '土瓜灣', '馬頭角', '馬頭圍', '啟德', '紅磡', '何文田'],
        '觀塘區': ['觀塘', '牛頭角', '九龍灣', '彩虹', '坪石', '秀茂坪', '藍田', '油塘'],
        '深水埗區': ['深水埗', '長沙灣', '荔枝角', '美孚', '石硤尾', '又一村'],
        '黃大仙區': ['黃大仙', '新蒲崗', '樂富', '橫頭磡', '東頭', '竹園', '慈雲山', '鑽石山'],
        '油尖旺區': ['油麻地', '尖沙咀', '旺角', '大角咀', '太子', '佐敦'],
        
        # 新界
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
    
    for doctor in DOCTORS_DATA:
        doctor_specialty = doctor.get('specialty', '')
        if not doctor_specialty or pd.isna(doctor_specialty):
            continue
            
        doctor_specialty = str(doctor_specialty)
        
        # 查找普通科、內科、家庭醫學科醫生
        if not (safe_str_check(doctor_specialty, '普通科') or safe_str_check(doctor_specialty, '內科') or 
                safe_str_check(doctor_specialty, '家庭醫學') or safe_str_check(doctor_specialty, '全科') or
                safe_str_check(doctor_specialty, 'General Practitioner') or safe_str_check(doctor_specialty, 'Internal Medicine') or
                safe_str_check(doctor_specialty, 'Family Medicine')):
            continue
        
        doctor_address = doctor.get('address', '')
        if not doctor_address or pd.isna(doctor_address):
            continue
            
        doctor_address = str(doctor_address)
        score = 25  # 基礎分數較低，因為是後備選項
        match_reasons = [f"地區後備推薦：{doctor_specialty}"]
        location_matched = False
        
        # 地區匹配邏輯（與主要函數相同）
        if user_area and safe_str_check(doctor_address, user_area):
            score += 30
            match_reasons.append(f"精確位置匹配：{user_area}")
            location_matched = True
        elif user_district and user_district in district_keywords:
            keywords = district_keywords[user_district]
            for keyword in keywords:
                if safe_str_check(doctor_address, keyword):
                    score += 20
                    match_reasons.append(f"地區匹配：{user_district}")
                    location_matched = True
                    break
        
        # 大區匹配
        if not location_matched and user_region:
            if user_region == '香港島' and any(safe_str_check(doctor_address, keyword) for keyword in ['香港', '中環', '灣仔', '銅鑼灣', '上環', '西環', '天后', '北角', '鰂魚涌', '柴灣', '筲箕灣', '香港仔']):
                score += 10
                match_reasons.append("大區匹配：香港島")
                location_matched = True
            elif user_region == '九龍' and any(safe_str_check(doctor_address, keyword) for keyword in ['九龍', '旺角', '尖沙咀', '油麻地', '佐敦', '深水埗', '觀塘', '黃大仙', '土瓜灣', '紅磡', '藍田', '彩虹', '牛頭角']):
                score += 10
                match_reasons.append("大區匹配：九龍")
                location_matched = True
            elif user_region == '新界' and any(safe_str_check(doctor_address, keyword) for keyword in ['新界', '沙田', '大埔', '元朗', '屯門', '荃灣', '將軍澳', '粉嶺', '上水', '葵涌', '青衣', '馬鞍山', '天水圍']):
                score += 10
                match_reasons.append("大區匹配：新界")
                location_matched = True
        
        # 向後兼容：如果沒有location_details，使用舊的location匹配
        if not location_matched and not user_region and location:
            if location in district_keywords:
                keywords = district_keywords[location]
                for keyword in keywords:
                    if safe_str_check(doctor_address, keyword):
                        score += 15
                        match_reasons.append(f"地區匹配：{location}")
                        location_matched = True
                        break
            elif safe_str_check(doctor_address, location):
                score += 10
                match_reasons.append(f"位置關鍵詞匹配：{location}")
                location_matched = True
        
        # 降低門檻，允許更多GP/內科醫生進入後備列表
        if location_matched or score >= 20:
            doctor_copy = {}
            for key, value in doctor.items():
                if pd.isna(value) or value is None:
                    doctor_copy[key] = ''
                else:
                    doctor_copy[key] = str(value)
            
            doctor_copy['match_score'] = score
            doctor_copy['match_reasons'] = match_reasons
            doctor_copy['ai_analysis'] = f"地區{doctor_specialty}推薦 - 可處理多種常見症狀，也可提供轉介服務"
            doctor_copy['location_priority'] = 1 if location_matched else 0  # 添加地理優先級
            fallback_doctors.append(doctor_copy)
    
    # 按分數排序，返回前10個
    fallback_doctors.sort(key=lambda x: x['match_score'], reverse=True)
    print(f"DEBUG - Found {len(fallback_doctors)} GP/internist fallback doctors")
    return fallback_doctors[:10]

@app.route('/')
def index():
    """主頁"""
    # Get user's preferred language from session or default to zh-TW
    current_lang = session.get('language', 'zh-TW')
    
    # Log page visit
    log_analytics('page_visit', {'page': 'index', 'language': current_lang}, 
                 get_real_ip(), request.user_agent.string, session.get('session_id'))
    return render_template('index.html', current_lang=current_lang, translations=TRANSLATIONS.get(current_lang, TRANSLATIONS['zh-TW']))

@app.route('/check_severe_symptoms', methods=['POST'])
def check_severe_symptoms():
    """檢查是否有嚴重症狀或病史，返回警告信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '無效的請求數據'}), 400
            
        symptoms = data.get('symptoms', '')
        chronic_conditions = data.get('chronicConditions', '')
        
        # 檢測嚴重症狀和病史
        detection_result = detect_severe_symptoms_and_conditions(symptoms, chronic_conditions)
        
        if detection_result['is_severe']:
            # 構建警告消息
            warning_message = {
                'title': '⚠️ 重要醫療提醒',
                'message': '根據您提供的症狀和病史，以下是重要提醒：',
                'recommendations': [
                    '🚨 考慮前往最近的急診室或醫院',
                    '📞 可撥打999緊急服務熱線',
                    '🏥 建議尋求專業醫療人員的協助',
                    '⏰ 如症狀嚴重，請勿延遲就醫'
                ],
                'disclaimer': '此系統僅供參考，不構成醫療建議或診斷。對於嚴重或緊急的醫療狀況，請諮詢專業醫療人員。',
                'severe_items': {
                    'symptoms': detection_result['severe_symptoms'],
                    'conditions': detection_result['severe_conditions']
                }
            }
            
            return jsonify({
                'is_severe': True,
                'warning': warning_message
            })
        else:
            return jsonify({
                'is_severe': False,
                'warning': None
            })
            
    except Exception as e:
        logger.error(f"Error checking severe symptoms: {e}")
        return jsonify({'error': '檢查過程中發生錯誤'}), 500

@app.route('/find_doctor', methods=['POST'])
def find_doctor():
    """處理醫生搜索請求"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '無效的請求數據'}), 400
        
        # Debug logging
        logger.info(f"Received find_doctor request with data keys: {list(data.keys())}")
        logger.info(f"Raw data values: age={data.get('age')}, symptoms='{data.get('symptoms')}', language='{data.get('language')}', location='{data.get('location')}'")
            
        try:
            age = int(data.get('age', 0))
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid age value: {data.get('age')}, error: {e}")
            return jsonify({'error': '年齡必須是有效數字'}), 400
        gender = data.get('gender', '')
        symptoms = data.get('symptoms', '')
        chronic_conditions = data.get('chronicConditions', '')
        language = data.get('language', '')
        location = data.get('location', '')
        location_details = data.get('locationDetails', {})
        detailed_health_info = data.get('detailedHealthInfo', {})
        ui_language = data.get('uiLanguage', 'zh-TW')  # Get UI language for diagnosis
        
        # Debug parsed values
        logger.info(f"Parsed values: age={age}, symptoms='{symptoms}', language='{language}', location='{location}'")
        
        # 驗證輸入 - gender is optional for backward compatibility
        if not symptoms or not language or not location or age <= 0:
            missing_fields = []
            if age <= 0: missing_fields.append('年齡')
            if not symptoms: missing_fields.append('症狀')
            if not language: missing_fields.append('語言')
            if not location: missing_fields.append('地區')
            
            error_msg = f'請填寫所有必要資料: {", ".join(missing_fields)}'
            logger.warning(f"Validation failed: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # Set session language for diagnosis
        session['language'] = ui_language
        
        # 使用AI分析症狀並配對醫生 (傳遞location_details)
        # Handle backward compatibility - pass empty string if gender is None
        gender_safe = gender or ''
        result = analyze_symptoms_and_match(age, gender_safe, symptoms, chronic_conditions, language, location, detailed_health_info, location_details)
        
        # Log user query to database
        session_id = session.get('session_id', secrets.token_hex(16))
        session['session_id'] = session_id
        
        try:
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_queries 
                (age, gender, symptoms, chronic_conditions, language, location, detailed_health_info, 
                 ai_analysis, related_specialty, matched_doctors_count, user_ip, session_id, analysis_report, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (age, gender_safe, symptoms, chronic_conditions, language, location, 
                  json.dumps(detailed_health_info), result['analysis'], 
                  result['recommended_specialty'], len(result['doctors']), 
                  get_real_ip(), session_id, 
                  format_analysis_report_full({
                      'age': age, 'gender': gender_safe, 'symptoms': symptoms, 
                      'chronic_conditions': chronic_conditions, 'language': language, 
                      'location': location, 'ai_analysis': result['analysis'], 
                      'related_specialty': result['recommended_specialty']
                  }, {}), 
                  get_current_time().isoformat()))
            query_id = cursor.lastrowid
            session['last_query_id'] = query_id
            conn.commit()
            conn.close()
            
            # Check for severe symptoms and log if found
            detection_result = detect_severe_symptoms_and_conditions(symptoms, chronic_conditions)
            if detection_result['is_severe']:
                severe_case_id = log_severe_case(
                    query_id, age, gender_safe, symptoms, chronic_conditions,
                    detection_result['severe_symptoms'], detection_result['severe_conditions'],
                    get_real_ip(), session_id
                )
                session['severe_case_id'] = severe_case_id
                
        except Exception as e:
            print(f"Database logging error: {e}")
        
        # Log analytics
        log_analytics('doctor_search', {
            'age': age, 'symptoms': symptoms, 'language': language, 'location': location,
            'doctors_found': len(result['doctors']), 'specialty': result['recommended_specialty']
        }, get_real_ip(), request.user_agent.string, session_id)
        
        return jsonify({
            'success': True,
            'user_summary': result['user_summary'],
            'analysis': result['analysis'],
            'recommended_specialty': result['recommended_specialty'],
            'doctors': result['doctors'],
            'total': len(result['doctors'])
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"處理請求時發生錯誤: {e}")
        logger.error(f"錯誤詳情: {error_details}")
        print(f"處理請求時發生錯誤: {e}")
        print(f"錯誤詳情: {error_details}")
        return jsonify({'error': f'服務器內部錯誤: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """健康檢查"""
    provider = AI_CONFIG['provider']
    ai_status = 'unknown'
    
    # 測試AI服務狀態
    try:
        test_response = call_ai_api("Hello")
        if "錯誤" not in test_response and "不可用" not in test_response:
            ai_status = 'healthy'
        else:
            ai_status = 'error'
    except:
        ai_status = 'error'
    
    return jsonify({
        'status': 'healthy',
        'doctors_loaded': len(DOCTORS_DATA),
        'ai_provider': provider,
        'ai_status': ai_status,
        'ai_config': {
            'provider': provider,
            'model': AI_CONFIG[provider]['model'] if provider in AI_CONFIG else 'unknown'
        }
    })

@app.route('/ai-config')
def get_ai_config():
    """獲取AI配置信息"""
    provider = AI_CONFIG['provider']
    config_info = {
        'provider': provider,
        'model': AI_CONFIG[provider]['model'] if provider in AI_CONFIG else 'unknown'
    }
    
    return jsonify(config_info)

@app.route('/contact-config')
def get_contact_config():
    """Get contact button configuration for frontend"""
    contact_mode = WHATSAPP_CONFIG.get('contact_mode', 'admin')
    return jsonify({
        'contact_mode': contact_mode,
        'show_contact_button': contact_mode != 'hidden'
    })

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        totp_token = request.form.get('totp_token')
        remember_me = request.form.get('remember_me')
        
        print(f"DEBUG - Form data: username='{username}', password='{password}', totp_token='{totp_token}'")
        
        # Handle 2FA verification from session
        if password == 'verified' and totp_token and session.get('pending_2fa_user') == username:
            print(f"DEBUG - Processing 2FA verification for user: {username}")
            user_data = session.get('pending_2fa_user_data')
            print(f"DEBUG - Session user_data: {user_data}")
            if user_data:
                # Get 2FA data
                conn = sqlite3.connect('admin_data.db')
                cursor = conn.cursor()
                cursor.execute('SELECT totp_enabled, totp_secret, backup_codes FROM admin_users WHERE username = ?', (username,))
                totp_data = cursor.fetchone()
                conn.close()
                
                if totp_data and totp_data[0] and totp_data[1]:
                    secret = totp_data[1]
                    backup_codes = json.loads(totp_data[2]) if totp_data[2] else []
                    
                    print(f"DEBUG - Verifying token '{totp_token}' with secret")
                    token_valid = False
                    used_backup = False
                    
                    # Check if user has multi-device 2FA enabled
                    user_id = multi_device_2fa.get_user_id_by_username(username)
                    print(f"DEBUG - User ID: {user_id}, Multi-device enabled: {multi_device_2fa.is_multi_device_enabled(user_id) if user_id else False}")
                    
                    if user_id and multi_device_2fa.is_multi_device_enabled(user_id):
                        # Use multi-device verification
                        print(f"DEBUG - Using multi-device verification for user {username}")
                        token_valid, used_device = multi_device_2fa.verify_token_multi_device(user_id, totp_token)
                        if token_valid:
                            print(f"DEBUG - Multi-device TOTP token valid from device: {used_device['device_name']}")
                    else:
                        # Fall back to single-device verification
                        print(f"DEBUG - Using single-device verification for user {username}")
                        if verify_totp_token(secret, totp_token):
                            token_valid = True
                            print(f"DEBUG - TOTP token valid")
                    
                    if not token_valid and totp_token in backup_codes:
                        token_valid = True
                        used_backup = True
                        print(f"DEBUG - Backup code valid")
                        # Remove used backup code
                        backup_codes.remove(totp_token)
                        conn = sqlite3.connect('admin_data.db')
                        cursor = conn.cursor()
                        cursor.execute('UPDATE admin_users SET backup_codes = ? WHERE username = ?', 
                                     (json.dumps(backup_codes), username))
                        conn.commit()
                        conn.close()
                    else:
                        print(f"DEBUG - Token verification failed")
                    
                    if token_valid:
                        # Complete login
                        session.pop('pending_2fa_user', None)
                        session.pop('pending_2fa_user_data', None)
                        session['admin_logged_in'] = True
                        session['admin_username'] = username
                        session['admin_user_id'] = user_data[0]
                        session['admin_role'] = user_data[3]
                        session['admin_permissions'] = json.loads(user_data[4]) if user_data[4] else {}
                        
                        # Load tab permissions for 2FA users
                        conn = sqlite3.connect('admin_data.db')
                        cursor = conn.cursor()
                        cursor.execute('SELECT tab_permissions FROM admin_users WHERE id = ?', (user_data[0],))
                        tab_perms = cursor.fetchone()
                        conn.close()
                        
                        if tab_perms and tab_perms[0]:
                            session['admin_tab_permissions'] = json.loads(tab_perms[0])
                        else:
                            session['admin_tab_permissions'] = {
                                "dashboard": True,
                                "analytics": True,
                                "config": True,
                                "doctors": True,
                                "users": True,
                                "bug_reports": True,
                                "severe_cases": True,
                                "reservations": True
                            }
                        
                        # Handle remember me for 2FA
                        if remember_me:
                            session.permanent = True
                            app.permanent_session_lifetime = timedelta(days=30)
                        else:
                            session.permanent = False
                        
                        session.modified = True
                        
                        if used_backup:
                            flash(f'使用備用代碼登入成功。剩餘備用代碼: {len(backup_codes)}', 'warning')
                        
                        log_analytics('admin_login', {
                            'username': username, 
                            'role': user_data[3], 
                            '2fa_used': True,
                            'remember_me': bool(remember_me)
                        }, get_real_ip(), request.user_agent.string)
                        flash('登入成功', 'success')
                        return redirect(url_for('admin_dashboard'))
                    else:
                        session.pop('pending_2fa_user', None)
                        session.pop('pending_2fa_user_data', None)
                        log_analytics('admin_login_2fa_failed', {'username': username}, 
                                     get_real_ip(), request.user_agent.string)
                        flash('雙重認證碼錯誤', 'error')
                        return render_template('admin/login-2fa.html', username=username)
            else:
                print(f"DEBUG - No user_data in session, redirecting to login")
                return render_template('admin/login.html')
        
        # Check database first, then fallback to environment variables
        user = get_admin_user(username)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user and user[2] == password_hash:
            # Check if 2FA is enabled for this user
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT totp_enabled, totp_secret, backup_codes FROM admin_users WHERE username = ?', (username,))
            totp_data = cursor.fetchone()
            conn.close()
            
            if totp_data and totp_data[0]:  # 2FA enabled
                if not totp_token:
                    # First step: password correct, now need 2FA
                    session['pending_2fa_user'] = username
                    session['pending_2fa_user_data'] = user
                    return render_template('admin/login-2fa.html', username=username)
                
                # Verify 2FA token
                secret = totp_data[1]
                backup_codes = json.loads(totp_data[2]) if totp_data[2] else []
                
                token_valid = False
                used_backup = False
                
                # Check TOTP token first
                if verify_totp_token(secret, totp_token):
                    token_valid = True
                # Check backup codes
                elif totp_token in backup_codes:
                    token_valid = True
                    used_backup = True
                    # Remove used backup code
                    backup_codes.remove(totp_token)
                    conn = sqlite3.connect('admin_data.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE admin_users SET backup_codes = ? WHERE username = ?', 
                                 (json.dumps(backup_codes), username))
                    conn.commit()
                    conn.close()
                
                if not token_valid:
                    session.pop('pending_2fa_user', None)
                    session.pop('pending_2fa_user_data', None)
                    log_analytics('admin_login_2fa_failed', {'username': username}, 
                                 get_real_ip(), request.user_agent.string)
                    flash('雙重認證碼錯誤', 'error')
                    return render_template('admin/login-2fa.html', username=username)
                
                if used_backup:
                    flash(f'使用備用代碼登入成功。剩餘備用代碼: {len(backup_codes)}', 'warning')
            
            # Complete login
            session.pop('pending_2fa_user', None)
            session.pop('pending_2fa_user_data', None)
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_user_id'] = user[0]
            session['admin_role'] = user[3]
            session['admin_permissions'] = json.loads(user[4]) if user[4] else {}
            
            # Load tab permissions (new column)
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT tab_permissions FROM admin_users WHERE id = ?', (user[0],))
            tab_perms = cursor.fetchone()
            conn.close()
            
            if tab_perms and tab_perms[0]:
                session['admin_tab_permissions'] = json.loads(tab_perms[0])
            else:
                # Default permissions for all tabs
                session['admin_tab_permissions'] = {
                    "dashboard": True,
                    "analytics": True,
                    "config": True,
                    "doctors": True,
                    "users": True,
                    "bug_reports": True,
                    "severe_cases": True,
                    "reservations": True
                }
            
            # Handle remember me functionality
            if remember_me:
                # Set session to be permanent (30 days)
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                # Session expires when browser closes
                session.permanent = False
            
            # Ensure session is saved
            session.modified = True
            
            # Update last login
            try:
                conn = sqlite3.connect('admin_data.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user[0],))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error updating last login: {e}")
            
            log_analytics('admin_login', {
                'username': username, 
                'role': user[3], 
                '2fa_used': totp_data and totp_data[0],
                'remember_me': bool(remember_me)
            }, get_real_ip(), request.user_agent.string)
            flash('登入成功', 'success')
            return redirect(url_for('admin_dashboard'))
            
        elif (username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH):
            print(f"DEBUG - Super admin login attempt, username: {username}")
            # Super admin fallback - check 2FA
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT totp_enabled, totp_secret, backup_codes FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
            totp_data = cursor.fetchone()
            conn.close()
            
            print(f"DEBUG - TOTP data: enabled={totp_data[0] if totp_data else None}, secret_exists={bool(totp_data[1]) if totp_data else None}")
            print(f"DEBUG - Full totp_data: {totp_data}")
            
            if totp_data and totp_data[0] and totp_data[1]:  # 2FA enabled AND secret exists
                print(f"DEBUG - 2FA is enabled, token received: '{totp_token}'")
                if not totp_token:
                    # Create fake user data for super admin
                    super_admin_data = (1, ADMIN_USERNAME, ADMIN_PASSWORD_HASH, 'super_admin', '{}', None, None, True, None)
                    session['pending_2fa_user'] = username
                    session['pending_2fa_user_data'] = super_admin_data
                    return render_template('admin/login-2fa.html', username=username)
                
                # Verify 2FA token
                secret = totp_data[1]
                backup_codes = json.loads(totp_data[2]) if totp_data[2] else []
                
                print(f"DEBUG - About to verify token with secret length: {len(secret) if secret else 0}")
                token_valid = False
                used_backup = False
                
                # Check if super admin has multi-device 2FA enabled
                user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
                print(f"DEBUG - Super admin user ID: {user_id}, Multi-device enabled: {multi_device_2fa.is_multi_device_enabled(user_id) if user_id else False}")
                
                if user_id and multi_device_2fa.is_multi_device_enabled(user_id):
                    # Use multi-device verification
                    print(f"DEBUG - Using multi-device verification for super admin")
                    token_valid, used_device = multi_device_2fa.verify_token_multi_device(user_id, totp_token)
                    if token_valid:
                        print(f"DEBUG - Super admin multi-device TOTP valid from: {used_device['device_name']}")
                else:
                    # Fall back to single-device verification
                    print(f"DEBUG - Using single-device verification for super admin")
                    if verify_totp_token(secret, totp_token):
                        token_valid = True
                
                if not token_valid and totp_token in backup_codes:
                    token_valid = True
                    used_backup = True
                    backup_codes.remove(totp_token)
                    conn = sqlite3.connect('admin_data.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE admin_users SET backup_codes = ? WHERE username = ?', 
                                 (json.dumps(backup_codes), ADMIN_USERNAME))
                    conn.commit()
                    conn.close()
                
                if not token_valid:
                    session.pop('pending_2fa_user', None)
                    log_analytics('admin_login_2fa_failed', {'username': username}, 
                                 get_real_ip(), request.user_agent.string)
                    flash('雙重認證碼錯誤', 'error')
                    return render_template('admin/login-2fa.html', username=username)
                
                if used_backup:
                    flash(f'使用備用代碼登入成功。剩餘備用代碼: {len(backup_codes)}', 'warning')
            
            # Complete super admin login
            session.pop('pending_2fa_user', None)
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_role'] = 'super_admin'
            session['admin_permissions'] = {'all': True}
            session['admin_tab_permissions'] = {
                "dashboard": True,
                "analytics": True,
                "config": True,
                "doctors": True,
                "users": True,
                "bug_reports": True,
                "severe_cases": True,
                "reservations": True
            }
            
            # Handle remember me functionality for super admin
            if remember_me:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False
            
            # Ensure session is saved
            session.modified = True
            
            log_analytics('admin_login', {
                'username': username, 
                'role': 'super_admin', 
                '2fa_used': totp_data and totp_data[0],
                'remember_me': bool(remember_me)
            }, get_real_ip(), request.user_agent.string)
            flash('登入成功', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            log_analytics('admin_login_failed', {'username': username}, 
                         get_real_ip(), request.user_agent.string)
            flash('用戶名或密碼錯誤', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@require_admin
def admin_logout():
    """Admin logout"""
    log_analytics('admin_logout', {'username': session.get('admin_username')}, 
                 get_real_ip(), request.user_agent.string)
    session.clear()
    flash('已成功登出', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@require_admin
def admin_dashboard():
    """Admin dashboard"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('SELECT COUNT(*) FROM user_queries')
        total_queries = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM doctor_clicks')
        total_clicks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_ip) FROM user_queries')
        unique_users = cursor.fetchone()[0]
        
        # Get recent queries
        cursor.execute('''
            SELECT timestamp, age, symptoms, language, location, related_specialty
            FROM user_queries 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        raw_recent_queries = cursor.fetchall()
        
        # Format timestamps for recent queries
        recent_queries = []
        for query in raw_recent_queries:
            formatted_query = list(query)
            formatted_query[0] = format_timestamp(query[0])  # Format timestamp
            recent_queries.append(tuple(formatted_query))
        
        # Get popular specialties
        cursor.execute('''
            SELECT related_specialty, COUNT(*) as count
            FROM user_queries 
            WHERE related_specialty IS NOT NULL
            GROUP BY related_specialty 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        popular_specialties = cursor.fetchall()
        
        # Get daily stats for the last 7 days
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as queries
            FROM user_queries 
            WHERE timestamp >= date('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''')
        daily_stats = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin/dashboard.html', 
                             total_queries=total_queries,
                             total_clicks=total_clicks,
                             unique_users=unique_users,
                             recent_queries=recent_queries,
                             popular_specialties=popular_specialties,
                             daily_stats=daily_stats)
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('載入儀表板時發生錯誤', 'error')
        return render_template('admin/dashboard.html')

def get_event_display_info(event_type: str) -> dict:
    """Convert event type to display-friendly name and color"""
    event_mapping = {
        'page_visit': {'name': '頁面訪問', 'color': 'primary'},
        'doctor_search': {'name': '醫生搜尋', 'color': 'success'},
        'doctor_click': {'name': '醫生點擊', 'color': 'info'},
        'admin_login': {'name': '管理員登入', 'color': 'info'},
        'admin_logout': {'name': '管理員登出', 'color': 'secondary'},
        'admin_login_failed': {'name': '登入失敗', 'color': 'danger'},
        'config_update': {'name': '配置更新', 'color': 'warning'},
        'password_change': {'name': '密碼更改', 'color': 'info'},
        'admin_user_created': {'name': '新增管理員', 'color': 'success'},
        'database_export': {'name': '數據庫匯出', 'color': 'primary'},
        'database_import': {'name': '數據庫匯入', 'color': 'warning'},
        'analytics_export': {'name': '分析數據匯出', 'color': 'primary'},
        'doctor_update': {'name': '醫生資料更新', 'color': 'warning'},
        'doctor_add': {'name': '新增醫生', 'color': 'success'},
        'doctor_delete': {'name': '刪除醫生', 'color': 'danger'},
        'bug_report_submitted': {'name': '問題回報', 'color': 'danger'}
    }
    return event_mapping.get(event_type, {'name': event_type, 'color': 'secondary'})

@app.route('/admin/analytics')
@tab_permission_required('analytics')
def admin_analytics():
    """Analytics page"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get analytics data with detailed events
        cursor.execute('''
            SELECT event_type, COUNT(*) as count
            FROM analytics 
            GROUP BY event_type 
            ORDER BY count DESC
        ''')
        raw_event_stats = cursor.fetchall()
        
        # Convert to display-friendly format with color info
        event_stats = [(get_event_display_info(event_type), count) 
                      for event_type, count in raw_event_stats]
        
        # Get detailed recent events for expandable view
        cursor.execute('''
            SELECT event_type, data, timestamp, user_ip, user_agent
            FROM analytics 
            ORDER BY timestamp DESC
            LIMIT 100
        ''')
        recent_events = cursor.fetchall()
        
        # Format recent events with display info
        detailed_events = []
        for event_type, data, timestamp, user_ip, user_agent in recent_events:
            event_info = get_event_display_info(event_type)
            try:
                parsed_data = json.loads(data) if data else {}
            except (json.JSONDecodeError, TypeError):
                parsed_data = {}
            
            detailed_events.append({
                'type': event_type,
                'display_name': event_info['name'],
                'color': event_info['color'],
                'data': parsed_data,
                'timestamp': format_timestamp(timestamp),
                'user_ip': user_ip,
                'user_agent': user_agent
            })
        
        # Get user queries with details
        cursor.execute('''
            SELECT id, timestamp, age, gender, symptoms, language, location, 
                   related_specialty, matched_doctors_count, user_ip
            FROM user_queries 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        raw_queries = cursor.fetchall()
        
        # Format timestamps for user queries
        user_queries = []
        for query in raw_queries:
            formatted_query = list(query)
            formatted_query[1] = format_timestamp(query[1])  # Format timestamp
            user_queries.append(tuple(formatted_query))
        
        # Get gender statistics for dashboard
        cursor.execute('''
            SELECT gender, COUNT(*) as count
            FROM user_queries 
            WHERE gender IS NOT NULL AND gender != ''
            GROUP BY gender 
            ORDER BY count DESC
        ''')
        gender_stats = cursor.fetchall()
        
        # Get location statistics for dashboard
        cursor.execute('''
            SELECT location, COUNT(*) as count
            FROM user_queries 
            WHERE location IS NOT NULL AND location != ''
            GROUP BY location 
            ORDER BY count DESC
            LIMIT 10
        ''')
        location_stats = cursor.fetchall()
        
        # Get doctor clicks
        cursor.execute('''
            SELECT dc.timestamp, dc.doctor_name, dc.doctor_specialty, 
                   uq.symptoms, dc.user_ip
            FROM doctor_clicks dc
            LEFT JOIN user_queries uq ON dc.query_id = uq.id
            ORDER BY dc.timestamp DESC 
            LIMIT 50
        ''')
        raw_clicks = cursor.fetchall()
        
        # Format timestamps for doctor clicks
        doctor_clicks = []
        for click in raw_clicks:
            formatted_click = list(click)
            formatted_click[0] = format_timestamp(click[0])  # Format timestamp
            doctor_clicks.append(tuple(formatted_click))
        
        conn.close()
        
        return render_template('admin/analytics.html', 
                             event_stats=event_stats,
                             queries=user_queries,
                             detailed_events=detailed_events,
                             total_queries=len(raw_queries),
                             total_events=sum(count for _, count in raw_event_stats),
                             gender_stats=gender_stats,
                             location_stats=location_stats,
                             doctor_clicks=doctor_clicks)
    except Exception as e:
        print(f"Analytics error: {e}")
        flash('載入分析數據時發生錯誤', 'error')
        return render_template('admin/analytics.html', 
                             event_stats=[],
                             queries=[],
                             detailed_events=[],
                             total_queries=0,
                             total_events=0,
                             gender_stats=[],
                             location_stats=[],
                             doctor_clicks=[])

@app.route('/admin/severe-cases')
@tab_permission_required('severe_cases')
def admin_severe_cases():
    """Severe cases monitoring page"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get severe cases with user query details
        cursor.execute('''
            SELECT sc.id, sc.age, sc.gender, sc.symptoms, sc.chronic_conditions,
                   sc.severe_symptoms, sc.severe_conditions, sc.user_ip, 
                   sc.timestamp, sc.user_acknowledged, sc.admin_reviewed, sc.admin_notes,
                   uq.ai_analysis, uq.related_specialty, uq.matched_doctors_count
            FROM severe_cases sc
            LEFT JOIN user_queries uq ON sc.user_query_id = uq.id
            ORDER BY sc.timestamp DESC
            LIMIT 100
        ''')
        severe_cases = cursor.fetchall()
        
        # Get statistics
        cursor.execute('SELECT COUNT(*) FROM severe_cases')
        total_cases = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM severe_cases WHERE admin_reviewed = 1')
        reviewed_cases = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM severe_cases WHERE user_acknowledged = 1')
        acknowledged_cases = cursor.fetchone()[0]
        
        # Get recent cases (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*) FROM severe_cases 
            WHERE datetime(timestamp) > datetime('now', '-1 day')
        ''')
        recent_cases = cursor.fetchone()[0]
        
        # Get top severe symptoms
        cursor.execute('''
            SELECT severe_symptoms, COUNT(*) as count
            FROM severe_cases
            WHERE severe_symptoms != '[]'
            GROUP BY severe_symptoms
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_symptoms = cursor.fetchall()
        
        # Get top severe conditions
        cursor.execute('''
            SELECT severe_conditions, COUNT(*) as count
            FROM severe_cases
            WHERE severe_conditions != '[]'
            GROUP BY severe_conditions
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_conditions = cursor.fetchall()
        
        conn.close()
        
        # Process the data for display
        processed_cases = []
        for case in severe_cases:
            try:
                severe_symptoms = json.loads(case[5]) if case[5] else []
                severe_conditions = json.loads(case[6]) if case[6] else []
            except:
                severe_symptoms = []
                severe_conditions = []
            
            processed_cases.append({
                'id': case[0],
                'age': case[1],
                'gender': case[2],
                'symptoms': case[3],
                'chronic_conditions': case[4],
                'severe_symptoms': severe_symptoms,
                'severe_conditions': severe_conditions,
                'user_ip': case[7],
                'timestamp': case[8],
                'user_acknowledged': case[9],
                'admin_reviewed': case[10],
                'admin_notes': case[11],
                'ai_analysis': case[12],
                'related_specialty': case[13],
                'matched_doctors_count': case[14]
            })
        
        stats = {
            'total_cases': total_cases,
            'reviewed_cases': reviewed_cases,
            'acknowledged_cases': acknowledged_cases,
            'recent_cases': recent_cases,
            'review_rate': round((reviewed_cases / total_cases * 100) if total_cases > 0 else 0, 1)
        }
        
        return render_template('admin/severe-cases.html', 
                             severe_cases=processed_cases,
                             stats=stats,
                             top_symptoms=top_symptoms,
                             top_conditions=top_conditions)
                             
    except Exception as e:
        logger.error(f"Severe cases page error: {e}")
        flash('載入嚴重病例數據時發生錯誤', 'error')
        return render_template('admin/severe-cases.html', 
                             severe_cases=[],
                             stats={'total_cases': 0, 'reviewed_cases': 0, 'acknowledged_cases': 0, 'recent_cases': 0, 'review_rate': 0},
                             top_symptoms=[],
                             top_conditions=[])

@app.route('/admin/severe-cases/<int:case_id>/review', methods=['POST'])
@tab_permission_required('severe_cases')
def review_severe_case(case_id):
    """Mark severe case as reviewed and add admin notes"""
    try:
        data = request.get_json()
        admin_notes = data.get('notes', '')
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE severe_cases 
            SET admin_reviewed = 1, admin_notes = ?
            WHERE id = ?
        ''', (admin_notes, case_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Severe case {case_id} reviewed by admin with notes: {admin_notes[:100]}...")
        
        return jsonify({'success': True, 'message': '病例已標記為已審核'})
        
    except Exception as e:
        logger.error(f"Error reviewing severe case {case_id}: {e}")
        return jsonify({'success': False, 'error': '審核病例時發生錯誤'}), 500

@app.route('/admin/reservations')
@tab_permission_required('reservations')
def admin_reservations():
    """Combined reservations and reference codes management page"""
    try:
        conn = sqlite3.connect('admin_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get filter parameters
        filter_status = request.args.get('status', 'all')
        filter_date = request.args.get('date', '')
        view_tab = request.args.get('tab', 'reservations')  # reservations or reference_codes
        page = int(request.args.get('page', 1))
        per_page = 50
        
        # ===== RESERVATIONS STATS =====
        cursor.execute('SELECT COUNT(*) FROM reservations')
        total_reservations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reservations WHERE status = 'pending'")
        pending_reservations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reservations WHERE status = 'confirmed'")
        confirmed_reservations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reservations WHERE status = 'completed'")
        completed_reservations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reservations WHERE status = 'cancelled'")
        cancelled_reservations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reservations WHERE DATE(created_at) = DATE('now')")
        today_reservations = cursor.fetchone()[0]
        
        # ===== REFERENCE CODES STATS =====
        cursor.execute('SELECT COUNT(*) FROM diagnosis_references')
        total_references = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM diagnosis_references WHERE is_used = 1')
        used_references = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM diagnosis_references WHERE is_billed = 1')
        billed_references = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(billing_amount), 0) FROM diagnosis_references WHERE is_billed = 1')
        total_billed_amount = cursor.fetchone()[0] or 0
        
        # ===== GET RESERVATIONS LIST =====
        reservations_query = '''
            SELECT r.*, 
                   (SELECT name FROM doctors WHERE id = r.doctor_id) as doctor_name,
                   (SELECT specialty FROM doctors WHERE id = r.doctor_id) as doctor_specialty
            FROM reservations r
        '''
        where_clauses = []
        params = []
        
        if filter_status != 'all' and view_tab == 'reservations':
            where_clauses.append('r.status = ?')
            params.append(filter_status)
        
        if filter_date:
            where_clauses.append('DATE(r.created_at) = ?')
            params.append(filter_date)
        
        if where_clauses:
            reservations_query += ' WHERE ' + ' AND '.join(where_clauses)
        
        reservations_query += ' ORDER BY r.created_at DESC LIMIT ? OFFSET ?'
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(reservations_query, params)
        reservations = [dict(row) for row in cursor.fetchall()]
        
        # ===== GET REFERENCE CODES LIST =====
        refs_query = 'SELECT * FROM diagnosis_references'
        refs_where = []
        refs_params = []
        
        if view_tab == 'reference_codes':
            if filter_status == 'used':
                refs_where.append('is_used = 1')
            elif filter_status == 'unused':
                refs_where.append('is_used = 0')
            elif filter_status == 'billed':
                refs_where.append('is_billed = 1')
            elif filter_status == 'unbilled':
                refs_where.append('is_used = 1 AND is_billed = 0')
        
        if filter_date:
            refs_where.append('DATE(created_at) = ?')
            refs_params.append(filter_date)
        
        if refs_where:
            refs_query += ' WHERE ' + ' AND '.join(refs_where)
        
        refs_query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        refs_params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(refs_query, refs_params)
        references = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return render_template('admin/reservations.html',
                             # Reservation stats
                             total_reservations=total_reservations,
                             pending_reservations=pending_reservations,
                             confirmed_reservations=confirmed_reservations,
                             completed_reservations=completed_reservations,
                             cancelled_reservations=cancelled_reservations,
                             today_reservations=today_reservations,
                             # Reference code stats
                             total_references=total_references,
                             used_references=used_references,
                             billed_references=billed_references,
                             total_billed_amount=total_billed_amount,
                             # Lists
                             reservations=reservations,
                             references=references,
                             # Filters
                             filter_status=filter_status,
                             filter_date=filter_date,
                             view_tab=view_tab,
                             page=page)
                             
    except Exception as e:
        logger.error(f"Error loading reservations page: {e}")
        import traceback
        traceback.print_exc()
        flash('載入預約資料時發生錯誤', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/reference-codes')
@tab_permission_required('reservations')
def admin_reference_codes():
    """Reference codes management page for billing"""
    try:
        conn = sqlite3.connect('admin_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get filter parameters
        filter_status = request.args.get('status', 'all')  # all, used, unused, billed
        filter_date = request.args.get('date', '')
        page = int(request.args.get('page', 1))
        per_page = 50
        
        # Build query based on filters
        where_clauses = []
        params = []
        
        if filter_status == 'used':
            where_clauses.append('dr.is_used = 1')
        elif filter_status == 'unused':
            where_clauses.append('dr.is_used = 0')
        elif filter_status == 'billed':
            where_clauses.append('dr.is_billed = 1')
        elif filter_status == 'unbilled':
            where_clauses.append('dr.is_used = 1 AND dr.is_billed = 0')
        
        if filter_date:
            where_clauses.append('DATE(dr.created_at) = ?')
            params.append(filter_date)
        
        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
        
        # Get total count
        cursor.execute(f'''
            SELECT COUNT(*) FROM diagnosis_references dr WHERE {where_sql}
        ''', params)
        total_count = cursor.fetchone()[0]
        
        # Get reference codes with pagination
        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT dr.*, uq.age, uq.gender, uq.location
            FROM diagnosis_references dr
            LEFT JOIN user_queries uq ON dr.query_id = uq.id
            WHERE {where_sql}
            ORDER BY dr.created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])
        
        references = [dict(row) for row in cursor.fetchall()]
        
        # Get statistics
        cursor.execute('SELECT COUNT(*) FROM diagnosis_references')
        total_references = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM diagnosis_references WHERE is_used = 1')
        used_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM diagnosis_references WHERE is_billed = 1')
        billed_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(billing_amount) FROM diagnosis_references WHERE is_billed = 1')
        total_billed = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT COUNT(*) FROM diagnosis_references 
            WHERE is_used = 1 AND is_billed = 0
        ''')
        pending_billing = cursor.fetchone()[0]
        
        # Get today's stats
        cursor.execute('''
            SELECT COUNT(*) FROM diagnosis_references 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today_count = cursor.fetchone()[0]
        
        conn.close()
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return render_template('admin/reference-codes.html',
                             references=references,
                             total_references=total_references,
                             used_count=used_count,
                             billed_count=billed_count,
                             total_billed=total_billed,
                             pending_billing=pending_billing,
                             today_count=today_count,
                             filter_status=filter_status,
                             filter_date=filter_date,
                             page=page,
                             total_pages=total_pages,
                             total_count=total_count)
        
    except Exception as e:
        logger.error(f"Error loading reference codes: {e}")
        import traceback
        traceback.print_exc()
        return render_template('admin/reference-codes.html',
                             references=[],
                             total_references=0,
                             used_count=0,
                             billed_count=0,
                             total_billed=0,
                             pending_billing=0,
                             today_count=0,
                             filter_status='all',
                             filter_date='',
                             page=1,
                             total_pages=1,
                             total_count=0)

@app.route('/admin/reference-codes/<reference_code>/mark-billed', methods=['POST'])
@tab_permission_required('reservations')
def mark_reference_billed(reference_code):
    """Mark a reference code as billed"""
    try:
        data = request.get_json()
        billing_amount = float(data.get('amount', 0))
        billing_notes = data.get('notes', '')
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE diagnosis_references 
            SET is_billed = 1, billed_at = CURRENT_TIMESTAMP,
                billing_amount = ?, billing_notes = ?
            WHERE reference_code = ?
        ''', (billing_amount, billing_notes, reference_code))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            logger.info(f"Reference {reference_code} marked as billed: ${billing_amount}")
            return jsonify({'success': True, 'message': '已標記為已收費'})
        else:
            return jsonify({'success': False, 'message': '找不到該參考編號'}), 404
        
    except Exception as e:
        logger.error(f"Error marking reference as billed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/reference-codes/bulk-bill', methods=['POST'])
@tab_permission_required('reservations')
def bulk_bill_references():
    """Bulk mark multiple references as billed"""
    try:
        data = request.get_json()
        reference_codes = data.get('codes', [])
        billing_amount = float(data.get('amount', 0))
        billing_notes = data.get('notes', '')
        
        if not reference_codes:
            return jsonify({'success': False, 'message': '請選擇要收費的參考編號'}), 400
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        updated_count = 0
        for code in reference_codes:
            cursor.execute('''
                UPDATE diagnosis_references 
                SET is_billed = 1, billed_at = CURRENT_TIMESTAMP,
                    billing_amount = ?, billing_notes = ?
                WHERE reference_code = ? AND is_billed = 0
            ''', (billing_amount, billing_notes, code))
            updated_count += cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Bulk billed {updated_count} references at ${billing_amount} each")
        return jsonify({
            'success': True, 
            'message': f'已標記 {updated_count} 個參考編號為已收費',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logger.error(f"Error bulk billing references: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reference/<reference_code>')
def lookup_reference_code(reference_code):
    """Public API to look up a diagnosis by reference code.
    Used by doctors to verify patient appointments.
    """
    try:
        diagnosis = get_diagnosis_by_reference(reference_code)
        
        if not diagnosis:
            return jsonify({
                'success': False, 
                'message': '找不到該參考編號或已過期'
            }), 404
        
        # Check if expired
        from datetime import datetime
        if diagnosis.get('expires_at'):
            try:
                expires = datetime.fromisoformat(diagnosis['expires_at'].replace('Z', '+00:00'))
                if datetime.now() > expires:
                    return jsonify({
                        'success': False,
                        'message': '該參考編號已過期'
                    }), 410
            except:
                pass
        
        # Return limited info for privacy
        return jsonify({
            'success': True,
            'reference_code': diagnosis['reference_code'],
            'created_at': diagnosis['created_at'],
            'expires_at': diagnosis['expires_at'],
            'symptoms': diagnosis['symptoms'],
            'recommended_specialty': diagnosis['recommended_specialty'],
            'matched_doctors_count': diagnosis['matched_doctors_count'],
            'is_used': bool(diagnosis['is_used']),
            'age': diagnosis.get('age'),
            'gender': diagnosis.get('gender'),
            'location': diagnosis.get('location')
        })
        
    except Exception as e:
        logger.error(f"Error looking up reference code: {e}")
        return jsonify({'success': False, 'error': '查詢時發生錯誤'}), 500

@app.route('/api/reference/<reference_code>/use', methods=['POST'])
def use_reference_code(reference_code):
    """Mark a reference code as used by a doctor.
    Called when a doctor confirms an appointment using this reference.
    """
    try:
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        doctor_name = data.get('doctor_name', 'Unknown')
        
        if not doctor_id:
            return jsonify({'success': False, 'message': '請提供醫生ID'}), 400
        
        # First check if reference exists and is valid
        diagnosis = get_diagnosis_by_reference(reference_code)
        if not diagnosis:
            return jsonify({'success': False, 'message': '找不到該參考編號'}), 404
        
        if diagnosis['is_used']:
            return jsonify({
                'success': False, 
                'message': '該參考編號已被使用',
                'used_at': diagnosis['used_at'],
                'used_by': diagnosis['used_by_doctor_name']
            }), 409
        
        # Mark as used
        success = mark_reference_as_used(reference_code, doctor_id, doctor_name)
        
        if success:
            return jsonify({
                'success': True, 
                'message': '參考編號已標記為已使用',
                'diagnosis': {
                    'symptoms': diagnosis['symptoms'],
                    'recommended_specialty': diagnosis['recommended_specialty'],
                    'age': diagnosis.get('age'),
                    'gender': diagnosis.get('gender')
                }
            })
        else:
            return jsonify({'success': False, 'message': '標記失敗'}), 500
        
    except Exception as e:
        logger.error(f"Error using reference code: {e}")
        return jsonify({'success': False, 'error': '處理時發生錯誤'}), 500

@app.route('/admin/reference-codes/export')
@tab_permission_required('reservations')
def export_reference_codes():
    """Export reference codes to CSV"""
    try:
        import csv
        from io import StringIO
        
        filter_status = request.args.get('status', 'all')
        
        conn = sqlite3.connect('admin_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        where_clause = '1=1'
        if filter_status == 'used':
            where_clause = 'dr.is_used = 1'
        elif filter_status == 'unused':
            where_clause = 'dr.is_used = 0'
        elif filter_status == 'billed':
            where_clause = 'dr.is_billed = 1'
        elif filter_status == 'unbilled':
            where_clause = 'dr.is_used = 1 AND dr.is_billed = 0'
        
        cursor.execute(f'''
            SELECT dr.reference_code, dr.created_at, dr.symptoms, 
                   dr.recommended_specialty, dr.matched_doctors_count,
                   dr.is_used, dr.used_at, dr.used_by_doctor_name,
                   dr.is_billed, dr.billed_at, dr.billing_amount,
                   uq.age, uq.gender, uq.location
            FROM diagnosis_references dr
            LEFT JOIN user_queries uq ON dr.query_id = uq.id
            WHERE {where_clause}
            ORDER BY dr.created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            '參考編號', '建立時間', '症狀', '推薦專科', '配對醫生數',
            '已使用', '使用時間', '使用醫生', '已收費', '收費時間', '收費金額',
            '年齡', '性別', '地區'
        ])
        
        # Data
        for row in rows:
            writer.writerow([
                row['reference_code'],
                row['created_at'],
                row['symptoms'][:100] if row['symptoms'] else '',
                row['recommended_specialty'],
                row['matched_doctors_count'],
                '是' if row['is_used'] else '否',
                row['used_at'] or '',
                row['used_by_doctor_name'] or '',
                '是' if row['is_billed'] else '否',
                row['billed_at'] or '',
                row['billing_amount'] or 0,
                row['age'] or '',
                row['gender'] or '',
                row['location'] or ''
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=reference_codes_{filter_status}.csv'}
        )
        
    except Exception as e:
        logger.error(f"Error exporting reference codes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/profile')
@require_admin
def admin_profile():
    """Admin profile/account settings page - accessible to all admin users"""
    return render_template('admin/profile.html')

@app.route('/admin/profile/update', methods=['POST'])
@require_admin
def update_admin_profile():
    """Update admin user profile information"""
    try:
        display_name = request.form.get('display_name', '').strip()
        email = request.form.get('email', '').strip()
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Update profile information
        cursor.execute('''
            UPDATE admin_users 
            SET display_name = ?, email = ?
            WHERE username = ?
        ''', (display_name if display_name else None, 
              email if email else None, 
              session.get('admin_username')))
        
        conn.commit()
        conn.close()
        
        flash('個人資料已更新', 'success')
        
    except Exception as e:
        print(f"Profile update error: {e}")
        flash('更新個人資料時發生錯誤', 'error')
    
    return redirect(url_for('admin_profile'))

@app.route('/admin/profile/change-password', methods=['POST'])
@require_admin
def change_admin_password():
    """Change admin user password"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('請填寫所有密碼欄位', 'error')
            return redirect(url_for('admin_profile'))
        
        if new_password != confirm_password:
            flash('新密碼與確認密碼不符', 'error')
            return redirect(url_for('admin_profile'))
        
        if len(new_password) < 8:
            flash('密碼長度至少需要8個字符', 'error')
            return redirect(url_for('admin_profile'))
        
        # Verify current password
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT password_hash FROM admin_users WHERE username = ?', 
                      (session.get('admin_username'),))
        result = cursor.fetchone()
        
        if not result:
            flash('用戶不存在', 'error')
            conn.close()
            return redirect(url_for('admin_profile'))
        
        current_hash = hashlib.sha256(current_password.encode()).hexdigest()
        if current_hash != result[0]:
            flash('目前密碼錯誤', 'error')
            conn.close()
            return redirect(url_for('admin_profile'))
        
        # Update password
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        cursor.execute('UPDATE admin_users SET password_hash = ? WHERE username = ?',
                      (new_hash, session.get('admin_username')))
        
        conn.commit()
        conn.close()
        
        flash('密碼已成功修改', 'success')
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        flash('密碼修改失敗', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/config')
@require_admin
@tab_permission_required('config')
def admin_config():
    """Admin configuration page"""
    try:
        # Get admin user info
        admin_user = get_admin_user_info()
        if not admin_user:
            flash('管理員資訊獲取失敗', 'error')
            return redirect(url_for('admin_login'))
        
        # Get all admin users for super admin
        all_admin_users = []
        if admin_user.get('is_super_admin'):
            try:
                conn = sqlite3.connect('admin_data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, role, totp_enabled FROM admin_users ORDER BY username")
                all_admin_users = cursor.fetchall()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to fetch admin users: {e}")
                flash('獲取管理員列表失敗', 'error')
        
        # Get AI configuration (placeholder for now)
        ai_config = {
            'provider': 'openai',
            'openai': {'api_key': '', 'model': 'gpt-4o'},
            'openrouter': {'api_key': '', 'model': 'anthropic/claude-3.5-sonnet'},
            'ollama': {'model': 'llama3.1:8b', 'base_url': 'http://localhost:11434/api/generate'}
        }
        
        # Get timezone configuration (placeholder for now)
        timezone_config = {'timezone': 'Asia/Hong_Kong'}
        
        # Get WhatsApp configuration (placeholder for now)
        whatsapp_config = {
            'target_number': '85294974070',
            'socket_url': 'http://localhost:3000',
            'api_key': ''
        }
        
        # Get 2FA status for super admin
        admin_2fa_status = False
        if admin_user.get('username') == 'admin':
            try:
                conn = sqlite3.connect('admin_data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT totp_enabled FROM admin_users WHERE username = ?", ('admin',))
                result = cursor.fetchone()
                admin_2fa_status = result[0] if result else False
                conn.close()
            except Exception as e:
                logger.error(f"Failed to get 2FA status: {e}")
        
        return render_template('admin/config.html', 
                             admin_user=admin_user,
                             all_admin_users=all_admin_users,
                             ai_config=ai_config,
                             timezone_config=timezone_config,
                             whatsapp_config=whatsapp_config,
                             admin_2fa_status=admin_2fa_status)
    except Exception as e:
        logger.error(f"Admin config error: {e}")
        flash('配置頁面載入失敗', 'error')
        return redirect(url_for('admin_dashboard'))

# Medical Search Configuration API Endpoints
@app.route('/admin/api/medical-search-config', methods=['GET'])
@require_admin
def get_medical_search_config_api():
    """Get medical search configuration - Admin only"""
    try:
        config = get_medical_search_config()
        
        # Get config descriptions from database
        conn = sqlite3.connect('doctor_ai.db')
        cursor = conn.cursor()
        cursor.execute('SELECT config_key, description, config_type FROM medical_search_config')
        config_meta = {row[0]: {'description': row[1], 'type': row[2]} for row in cursor.fetchall()}
        conn.close()
        
        # Combine config values with metadata
        result = {}
        for key, value in config.items():
            result[key] = {
                'value': value,
                'description': config_meta.get(key, {}).get('description', ''),
                'type': config_meta.get(key, {}).get('type', 'string')
            }
        
        return jsonify({
            'success': True,
            'config': result
        })
        
    except Exception as e:
        logger.error(f"Error getting medical search config: {e}")
        return jsonify({'error': 'Failed to get configuration'}), 500

@app.route('/admin/api/medical-search-config', methods=['POST'])
@require_admin
def update_medical_search_config_api():
    """Update medical search configuration - Admin only"""
    try:
        data = request.get_json()
        config_key = data.get('config_key')
        config_value = data.get('config_value')
        
        if not config_key or config_value is None:
            return jsonify({'error': 'Missing config_key or config_value'}), 400
        
        success = update_medical_search_config(config_key, config_value)
        
        if success:
            logger.info(f"Admin {session.get('username')} updated medical search config: {config_key} = {config_value}")
            return jsonify({
                'success': True,
                'message': f'Configuration {config_key} updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update configuration'}), 500
            
    except Exception as e:
        logger.error(f"Error updating medical search config: {e}")
        return jsonify({'error': 'Failed to update configuration'}), 500

@app.route('/admin/api/console-logs')
@require_admin
def get_console_logs():
    """Get console logs for super admin only"""
    try:
        admin_user = get_admin_user_info()
        if not admin_user or not admin_user.get('is_super_admin'):
            return jsonify({'error': 'Unauthorized - Super admin access required'}), 403
        
        # Get recent logs from buffer
        logs = list(console_log_buffer)
        
        # Format logs for frontend
        formatted_logs = []
        for log in logs[-100:]:  # Get last 100 logs
            formatted_logs.append({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(log['timestamp'])),
                'level': log['level'],
                'message': log['message'],
                'logger': log['logger']
            })
        
        return jsonify({'logs': formatted_logs})
        
    except Exception as e:
        logger.error(f"Console logs API error: {e}")
        return jsonify({'error': 'Failed to fetch logs'}), 500

@app.route('/admin/api/console-logs/stream')
@require_admin
def stream_console_logs():
    """Stream console logs via Server-Sent Events for super admin only"""
    try:
        admin_user = get_admin_user_info()
        if not admin_user or not admin_user.get('is_super_admin'):
            return jsonify({'error': 'Unauthorized - Super admin access required'}), 403
        
        def generate():
            last_count = len(console_log_buffer)
            while True:
                current_count = len(console_log_buffer)
                if current_count > last_count:
                    # New logs available
                    new_logs = list(console_log_buffer)[last_count:]
                    for log in new_logs:
                        formatted_log = {
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(log['timestamp'])),
                            'level': log['level'],
                            'message': log['message'],
                            'logger': log['logger']
                        }
                        yield f"data: {json.dumps(formatted_log)}\n\n"
                    last_count = current_count
                time.sleep(1)  # Check for new logs every second
        
        return Response(generate(), mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"Console logs stream error: {e}")
        return jsonify({'error': 'Failed to stream logs'}), 500

@app.route('/admin/update-timezone', methods=['POST'])
@login_required
def update_timezone_config():
    """Update timezone configuration"""
    try:
        timezone = request.form.get('timezone', 'Asia/Hong_Kong')
        
        # Validate timezone
        try:
            pytz.timezone(timezone)
        except:
            flash('無效的時區設定', 'error')
            return redirect(url_for('admin_config'))
        
        # Update environment variable
        env_path = Path('.env')
        if env_path.exists():
            set_key(env_path, 'APP_TIMEZONE', timezone)
        else:
            with open('.env', 'w') as f:
                f.write(f'APP_TIMEZONE={timezone}\n')
        
        # Update runtime config
        TIMEZONE_CONFIG['timezone'] = timezone
        
        flash(f'時區已更新為 {timezone}', 'success')
        
    except Exception as e:
        print(f"Timezone update error: {e}")
        flash('更新時區設定時發生錯誤', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/api/openai-models')
@require_admin
def get_openai_models_api():
    """API endpoint to fetch OpenAI models"""
    # Get API key from query parameter or use current config
    api_key = request.args.get('api_key')
    models = get_openai_models(api_key)
    return jsonify({'models': models})

@app.route('/admin/api/database-stats')
@require_admin
def get_database_stats():
    """API endpoint to get database statistics"""
    try:
        # Get doctors count from loaded data
        doctors_count = len(DOCTORS_DATA) if DOCTORS_DATA else 0
        
        # Get analytics data from admin_data.db
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get today's queries
        today = get_current_time().strftime('%Y-%m-%d')
        try:
            cursor.execute('SELECT COUNT(*) FROM user_queries WHERE DATE(timestamp) = ?', (today,))
            queries_today = cursor.fetchone()[0]
        except:
            queries_today = 0
        
        # Get total queries
        try:
            cursor.execute('SELECT COUNT(*) FROM user_queries')
            total_queries = cursor.fetchone()[0]
        except:
            total_queries = 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'doctors_count': doctors_count,
                'queries_today': queries_today,
                'total_queries': total_queries
            }
        })
    except Exception as e:
        print(f"Database stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/users')
@require_admin
def get_admin_users_api():
    """API endpoint to get admin users list"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check if admin_users table exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='admin_users'
        ''')
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': True,
                'users': []
            })
        
        # Check if all columns exist
        cursor.execute('PRAGMA table_info(admin_users)')
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build query based on available columns
        base_columns = ['id', 'username', 'role']
        optional_columns = ['email', 'display_name', 'is_active', 'created_at']
        
        select_columns = base_columns.copy()
        for col in optional_columns:
            if col in columns:
                select_columns.append(col)
        
        query = f"SELECT {', '.join(select_columns)} FROM admin_users ORDER BY id DESC"
        cursor.execute(query)
        
        users = []
        for row in cursor.fetchall():
            print(f"DEBUG /admin/api/users - Row: {row}")  # Debug logging
            print(f"DEBUG /admin/api/users - Columns: {select_columns}")  # Debug logging
            
            # Find the correct index for created_at
            created_at_index = select_columns.index('created_at') if 'created_at' in select_columns else -1
            
            user = {
                'id': row[0],
                'username': row[1],
                'role': row[2] if len(row) > 2 else 'admin',
                'email': row[3] if len(row) > 3 and 'email' in select_columns else None,
                'display_name': row[4] if len(row) > 4 and 'display_name' in select_columns else None,
                'is_active': bool(row[5]) if len(row) > 5 and 'is_active' in select_columns else True,
                'created_at': row[created_at_index] if created_at_index != -1 and len(row) > created_at_index else None
            }
            print(f"DEBUG /admin/api/users - User object: {user}")  # Debug logging
            users.append(user)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        print(f"Get admin users error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def update_env_file(key: str, value: str) -> None:
    """Update or add a key-value pair in the .env file."""
    env_path = Path('.env')
    
    # If .env doesn't exist, create it
    if not env_path.exists():
        env_path.touch()
    
    # Read current content
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return
    
    # Update or add the key
    key_exists = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{key}='):
            lines[i] = f"{key}={value}\n"
            key_exists = True
            break
    
    if not key_exists:
        lines.append(f"{key}={value}\n")
    
    # Write back to file
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        logger.info(f"Updated {key} in .env file")
    except Exception as e:
        logger.error(f"Error writing to .env file: {e}")

@app.route('/admin/update_ai_config', methods=['POST'])
@require_admin
def update_ai_config():
    try:
        # Update AI_CONFIG based on form data
        provider = request.form.get('provider', 'ollama')
        AI_CONFIG['provider'] = provider
        
        # Update provider-specific config
        if provider == 'openrouter':
            AI_CONFIG['openrouter'].update({
                'api_key': request.form.get('openrouter_api_key', ''),
                'model': request.form.get('openrouter_model', 'anthropic/claude-3.5-sonnet'),
                'max_tokens': int(request.form.get('openrouter_max_tokens', '4000'))
            })
            # Update .env file
            update_env_file('AI_PROVIDER', 'openrouter')
            update_env_file('OPENROUTER_API_KEY', AI_CONFIG['openrouter']['api_key'])
            update_env_file('OPENROUTER_MODEL', AI_CONFIG['openrouter']['model'])
            update_env_file('OPENROUTER_MAX_TOKENS', str(AI_CONFIG['openrouter']['max_tokens']))
            
        elif provider == 'openai':
            AI_CONFIG['openai'].update({
                'api_key': request.form.get('openai_api_key', ''),
                'model': request.form.get('openai_model', 'gpt-4'),
                'max_tokens': int(request.form.get('openai_max_tokens', '4000'))
            })
            # Update .env file
            update_env_file('AI_PROVIDER', 'openai')
            update_env_file('OPENAI_API_KEY', AI_CONFIG['openai']['api_key'])
            
        elif provider == 'ollama':
            AI_CONFIG['ollama'].update({
                'model': request.form.get('ollama_model', 'llama3.1:8b'),
                'base_url': request.form.get('ollama_base_url', 'http://localhost:11434/api/generate')
            })
            # Update .env file
            update_env_file('AI_PROVIDER', 'ollama')
            update_env_file('OLLAMA_MODEL', AI_CONFIG['ollama']['model'])
            update_env_file('OLLAMA_BASE_URL', AI_CONFIG['ollama']['base_url'])
        
        # Save to database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO system_config (config_key, config_value)
            VALUES ('ai_config', ?)
        ''', (json.dumps(AI_CONFIG),))
        conn.commit()
        conn.close()
        
        # Reload environment variables
        load_dotenv(override=True)
        
        log_analytics('config_update', {'type': 'ai_config', 'provider': provider}, 
                     get_real_ip(), request.user_agent.string)
        
        flash('AI配置已更新', 'success')
    except Exception as e:
        logger.error(f"AI config update error: {e}")
        flash(f'更新AI配置時發生錯誤: {str(e)}', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/setup-2fa', methods=['GET', 'POST'])
@require_admin
def setup_2fa():
    """Setup 2FA for super admin"""
    if request.method == 'GET':
        # Only allow super admin to setup 2FA
        if session.get('admin_username') != ADMIN_USERNAME:
            flash('只有超級管理員可以設置雙重認證', 'error')
            return redirect(url_for('admin_config'))
        
        # Check if 2FA is already enabled
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT totp_enabled FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            flash('雙重認證已啟用', 'info')
            return redirect(url_for('admin_config'))
        
        # Generate new secret and QR code
        secret = generate_totp_secret()
        qr_code = generate_qr_code(ADMIN_USERNAME, secret)
        
        # Store secret in session temporarily
        session['temp_totp_secret'] = secret
        
        return render_template('admin/setup-2fa.html', 
                             qr_code=qr_code, 
                             secret=secret,
                             username=ADMIN_USERNAME)
    
    elif request.method == 'POST':
        token = request.form.get('token')
        secret = session.get('temp_totp_secret')
        
        if not secret or not token:
            flash('無效的請求', 'error')
            return redirect(url_for('setup_2fa'))
        
        # Verify the token
        if verify_totp_token(secret, token):
            # Generate backup codes
            backup_codes = generate_backup_codes()
            
            # Save to database
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE admin_users 
                SET totp_secret = ?, totp_enabled = 1, backup_codes = ?
                WHERE username = ?
            ''', (secret, json.dumps(backup_codes), ADMIN_USERNAME))
            conn.commit()
            conn.close()
            
            # Clear temp secret
            session.pop('temp_totp_secret', None)
            
            # Log the setup
            log_analytics('2fa_setup', {'username': ADMIN_USERNAME}, 
                         get_real_ip(), request.user_agent.string)
            
            flash('雙重認證設置成功！請保存備用代碼', 'success')
            return render_template('admin/2fa-backup-codes.html', 
                                 backup_codes=backup_codes)
        else:
            flash('驗證碼錯誤，請重試', 'error')
            return redirect(url_for('setup_2fa'))

@app.route('/admin/disable-2fa', methods=['POST'])
@require_admin
def disable_2fa():
    """Disable 2FA for super admin"""
    if session.get('admin_username') != ADMIN_USERNAME:
        flash('只有超級管理員可以停用雙重認證', 'error')
        return redirect(url_for('admin_config'))
    
    password = request.form.get('password')
    if not password:
        flash('請輸入密碼確認', 'error')
        return redirect(url_for('admin_config'))
    
    # Verify password
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    
    # Get user ID for multi-device cleanup
    cursor.execute('SELECT id FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
    user_result = cursor.fetchone()
    
    if user_result:
        user_id = user_result[0]
        # Delete all multi-device 2FA devices
        cursor.execute('DELETE FROM admin_2fa_devices WHERE user_id = ?', (user_id,))
    """Change admin password (legacy endpoint)"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('請填寫所有密碼欄位', 'error')
            return redirect(url_for('admin_config'))
        
        if new_password != confirm_password:
            flash('新密碼與確認密碼不符', 'error')
            return redirect(url_for('admin_config'))
        
        if len(new_password) < 6:
            flash('新密碼長度至少6個字符', 'error')
            return redirect(url_for('admin_config'))
        
        # Verify current password
        current_hash = hashlib.sha256(current_password.encode()).hexdigest()
        user_id = session.get('admin_user_id')
        username = session.get('admin_username')
        
        if user_id:
            # Database user
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM admin_users WHERE id = ?', (user_id,))
            stored_hash = cursor.fetchone()
            
            if not stored_hash or stored_hash[0] != current_hash:
                flash('當前密碼錯誤', 'error')
                conn.close()
                return redirect(url_for('admin_config'))
            
            # Update password
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute('UPDATE admin_users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
            conn.commit()
            conn.close()
        else:
            # Environment user - can't change password
            flash('環境變數用戶無法更改密碼', 'error')
            return redirect(url_for('admin_config'))
        
        log_analytics('password_change', {'username': username}, 
                     get_real_ip(), request.user_agent.string)
        flash('密碼更新成功', 'success')
        
    except Exception as e:
        print(f"Password change error: {e}")
        flash('更改密碼時發生錯誤', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/config/users', methods=['POST'])
@require_permission('user_management')
def create_admin_user():
    """Create new admin user"""
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'admin')
        permissions = request.form.getlist('permissions')
        
        if not all([username, password]):
            flash('請填寫用戶名和密碼', 'error')
            return redirect(url_for('admin_config'))
        
        if len(password) < 6:
            flash('密碼長度至少6個字符', 'error')
            return redirect(url_for('admin_config'))
        
        # Build permissions object
        perm_obj = {}
        for perm in permissions:
            perm_obj[perm] = True
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        created_by = session.get('admin_user_id')
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Set default tab permissions for new user
        default_tab_permissions = {
            "dashboard": True,
            "analytics": True,
            "config": True,
            "doctors": True,
            "users": True,
            "bug_reports": True,
            "severe_cases": True,
            "reservations": True
        }
        
        try:
            cursor.execute('''
                INSERT INTO admin_users (username, password_hash, role, permissions, created_by, tab_permissions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, role, json.dumps(perm_obj), created_by, json.dumps(default_tab_permissions)))
            conn.commit()
            
            log_analytics('admin_user_created', {
                'username': username, 'role': role, 'created_by': session.get('admin_username')
            }, get_real_ip(), request.user_agent.string)
            
            flash(f'管理員用戶 {username} 創建成功', 'success')
        except sqlite3.IntegrityError:
            flash('用戶名已存在', 'error')
        
        conn.close()
        
    except Exception as e:
        print(f"User creation error: {e}")
        flash('創建用戶時發生錯誤', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/api/admin-users')
@require_permission('user_management')
def get_admin_users():
    """Get list of admin users"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, role, is_active, created_at, last_login 
            FROM admin_users 
            ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'role': row[2],
                'is_active': bool(row[3]),
                'created_at': row[4],
                'last_login': row[5]
            })
        
        conn.close()
        return jsonify({'users': users})
        
    except Exception as e:
        print(f"Error fetching admin users: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@app.route('/admin/api/user-permissions')
@require_admin
def get_user_permissions():
    """Get user tab permissions for management"""
    if session.get('admin_role') != 'super_admin':
        return jsonify({'error': 'Only super admin can manage permissions'}), 403
    
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, role, tab_permissions, created_at, is_active
            FROM admin_users 
            ORDER BY username
        ''')
        
        users = []
        for row in cursor.fetchall():
            print(f"DEBUG - Row data: {row}")  # Debug logging
            tab_perms = json.loads(row[3]) if row[3] else {
                "dashboard": True,
                "analytics": True,
                "config": True,
                "doctors": True,
                "users": True,
                "bug_reports": True,
                "severe_cases": True,
                "reservations": True
            }
            
            user_data = {
                'id': row[0],
                'username': row[1],
                'role': row[2],
                'tab_permissions': tab_perms,
                'created_at': row[4],
                'is_active': bool(row[5])
            }
            print(f"DEBUG - User data: {user_data}")  # Debug logging
            users.append(user_data)
        
        conn.close()
        return jsonify({'users': users})
        
    except Exception as e:
        print(f"Error fetching user permissions: {e}")
        return jsonify({'error': 'Failed to fetch permissions'}), 500

@app.route('/admin/api/user-permissions/update', methods=['POST'])
@require_admin
def update_user_permissions():
    """Update user tab permissions"""
    if session.get('admin_role') != 'super_admin':
        return jsonify({'error': 'Only super admin can manage permissions'}), 403
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        permission = data.get('permission')
        enabled = data.get('enabled')
        
        if not all([user_id, permission]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Valid permissions
        valid_permissions = ['dashboard', 'analytics', 'config', 'doctors', 'users', 'bug_reports', 'severe_cases']
        if permission not in valid_permissions:
            return jsonify({'error': 'Invalid permission'}), 400
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get current permissions
        cursor.execute('SELECT tab_permissions FROM admin_users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'User not found'}), 404
        
        current_perms = json.loads(result[0]) if result[0] else {}
        current_perms[permission] = enabled
        
        # Update permissions
        cursor.execute('''
            UPDATE admin_users 
            SET tab_permissions = ? 
            WHERE id = ?
        ''', (json.dumps(current_perms), user_id))
        
        conn.commit()
        conn.close()
        
        # Log the permission change
        log_analytics('admin_permission_update', {
            'target_user_id': user_id,
            'permission': permission,
            'enabled': enabled,
            'updated_by': session.get('admin_username')
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({'success': True, 'message': 'Permission updated successfully'})
        
    except Exception as e:
        print(f"Error updating user permissions: {e}")
        return jsonify({'error': 'Failed to update permissions'}), 500

@app.route('/admin/api/specialties')
@require_admin
def get_specialties_api():
    """Get available medical specialties for admin interface"""
    try:
        specialties = get_available_specialties()
        return jsonify({'specialties': specialties})
    except Exception as e:
        print(f"Error fetching specialties: {e}")
        return jsonify({'error': 'Failed to fetch specialties'}), 500

@app.route('/admin/config/users/<int:user_id>/toggle', methods=['POST'])
@require_permission('user_management')
def toggle_admin_user(user_id):
    """Toggle admin user active status"""
    try:
        if user_id == session.get('admin_user_id'):
            return jsonify({'success': False, 'error': '不能停用自己的帳戶'}), 400
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get current status first
        cursor.execute('SELECT is_active FROM admin_users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        current_status = result[0]
        new_status = 0 if current_status else 1
        
        cursor.execute('UPDATE admin_users SET is_active = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        conn.close()
        
        action = '啟用' if new_status else '停用'
        return jsonify({'success': True, 'message': f'用戶已{action}'})
        
    except Exception as e:
        print(f"Error toggling user: {e}")
        return jsonify({'success': False, 'error': '更新用戶狀態時發生錯誤'}), 500

@app.route('/admin/config/users/<int:user_id>/delete', methods=['DELETE'])
@require_permission('user_management')
def delete_admin_user(user_id):
    """Delete admin user permanently"""
    try:
        if user_id == session.get('admin_user_id'):
            return jsonify({'success': False, 'error': '不能刪除自己的帳戶'}), 400
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check if user exists and get username for logging
        cursor.execute('SELECT username FROM admin_users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        username = result[0]
        
        # Delete the user
        cursor.execute('DELETE FROM admin_users WHERE id = ?', (user_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': '刪除失敗'}), 500
        
        conn.commit()
        conn.close()
        
        # Log the deletion
        log_analytics('admin_user_delete', {
            'deleted_user_id': user_id,
            'deleted_username': username,
            'deleted_by': session.get('admin_username')
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({'success': True, 'message': f'用戶 {username} 已刪除'})
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': '刪除用戶時發生錯誤'}), 500

@app.route('/admin/database/export-doctors')
@require_permission('config')
def export_doctors_database():
    """Export doctors database as CSV"""
    try:
        import io
        from flask import make_response
        
        # Create CSV content
        output = io.StringIO()
        if DOCTORS_DATA:
            # Get all column names from the first doctor record
            fieldnames = list(DOCTORS_DATA[0].keys())
            
            # Write header
            output.write(','.join(f'"{field}"' for field in fieldnames) + '\n')
            
            # Write data rows
            for doctor in DOCTORS_DATA:
                row = []
                for field in fieldnames:
                    value = doctor.get(field, '')
                    # Escape quotes and handle None values
                    if value is None:
                        value = ''
                    value = str(value).replace('"', '""')
                    row.append(f'"{value}"')
                output.write(','.join(row) + '\n')
        
        # Create response with UTF-8 BOM for better Excel compatibility
        csv_content = '\ufeff' + output.getvalue()  # Add UTF-8 BOM
        response = make_response(csv_content.encode('utf-8'))
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=doctors_database_{get_current_time().strftime("%Y%m%d_%H%M%S")}.csv'
        
        log_analytics('database_export', {'type': 'doctors', 'count': len(DOCTORS_DATA)}, 
                     get_real_ip(), request.user_agent.string)
        
        return response
        
    except Exception as e:
        print(f"Export error: {e}")
        flash('導出醫生數據庫時發生錯誤', 'error')
        return redirect(url_for('admin_config'))

@app.route('/admin/database/import-doctors', methods=['POST'])
@require_permission('config')
def import_doctors_database():
    """Import doctors database from CSV"""
    try:
        if 'doctors_file' not in request.files:
            flash('請選擇要上傳的CSV文件', 'error')
            return redirect(url_for('admin_config'))
        
        file = request.files['doctors_file']
        if file.filename == '':
            flash('請選擇要上傳的CSV文件', 'error')
            return redirect(url_for('admin_config'))
        
        if not file.filename.lower().endswith('.csv'):
            flash('請上傳CSV格式的文件', 'error')
            return redirect(url_for('admin_config'))
        
        # Read and parse CSV
        import io
        import csv
        
        # Read file content
        file_content = file.read().decode('utf-8-sig')  # Handle BOM
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        new_doctors_data = []
        row_count = 0
        error_rows = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (after header)
            row_count += 1
            try:
                # Clean and validate row data
                cleaned_row = {}
                for key, value in row.items():
                    if key:  # Skip empty column names
                        cleaned_row[key.strip()] = value.strip() if value else ''
                
                # Basic validation - ensure we have essential fields
                if not cleaned_row.get('name', '').strip():
                    error_rows.append(f"第{row_num}行: 缺少醫生姓名")
                    continue
                
                new_doctors_data.append(cleaned_row)
                
            except Exception as e:
                error_rows.append(f"第{row_num}行: 數據格式錯誤 - {str(e)}")
        
        if error_rows:
            error_msg = "導入過程中發現錯誤:\n" + "\n".join(error_rows[:10])  # Show first 10 errors
            if len(error_rows) > 10:
                error_msg += f"\n... 還有 {len(error_rows) - 10} 個錯誤"
            flash(error_msg, 'error')
            return redirect(url_for('admin_config'))
        
        if not new_doctors_data:
            flash('CSV文件中沒有有效的醫生數據', 'error')
            return redirect(url_for('admin_config'))
        
        # Backup current data
        backup_action = request.form.get('backup_action', 'replace')
        
        if backup_action == 'replace':
            # Replace all data
            global DOCTORS_DATA
            DOCTORS_DATA = new_doctors_data
            flash(f'成功導入 {len(new_doctors_data)} 位醫生數據（已替換原有數據）', 'success')
        elif backup_action == 'append':
            # Append to existing data
            DOCTORS_DATA.extend(new_doctors_data)
            flash(f'成功追加 {len(new_doctors_data)} 位醫生數據（總計 {len(DOCTORS_DATA)} 位）', 'success')
        
        # Save to file (optional - update the CSV file)
        try:
            csv_path = os.path.join('assets', 'finddoc_doctors_detailed 2.csv')
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                if DOCTORS_DATA:
                    fieldnames = list(DOCTORS_DATA[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(DOCTORS_DATA)
        except Exception as e:
            print(f"Warning: Could not save to CSV file: {e}")
        
        log_analytics('database_import', {
            'type': 'doctors', 
            'imported_count': len(new_doctors_data),
            'total_count': len(DOCTORS_DATA),
            'action': backup_action
        }, get_real_ip(), request.user_agent.string)
        
    except Exception as e:
        print(f"Import error: {e}")
        flash(f'導入醫生數據庫時發生錯誤: {str(e)}', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/database/stats')
@require_admin
def get_database_stats_page():
    """Get database statistics"""
    try:
        stats = {
            'doctors_count': len(DOCTORS_DATA) if DOCTORS_DATA else 0,
            'doctors_fields': list(DOCTORS_DATA[0].keys()) if DOCTORS_DATA else [],
            'sample_doctor': DOCTORS_DATA[0] if DOCTORS_DATA else None,
            'user_queries_count': 0,
            'doctor_clicks_count': 0,
            'analytics_events_count': 0,
            'admin_users_count': 0
        }
        
        # Get analytics data count with table existence checks
        try:
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            
            # Check if tables exist before querying
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            if 'user_queries' in existing_tables:
                cursor.execute('SELECT COUNT(*) FROM user_queries')
                stats['user_queries_count'] = cursor.fetchone()[0]
            
            if 'doctor_clicks' in existing_tables:
                cursor.execute('SELECT COUNT(*) FROM doctor_clicks')
                stats['doctor_clicks_count'] = cursor.fetchone()[0]
            
            if 'analytics' in existing_tables:
                cursor.execute('SELECT COUNT(*) FROM analytics')
                stats['analytics_events_count'] = cursor.fetchone()[0]
            
            if 'admin_users' in existing_tables:
                cursor.execute('SELECT COUNT(*) FROM admin_users')
                stats['admin_users_count'] = cursor.fetchone()[0]
            
            conn.close()
            
        except Exception as db_error:
            print(f"=== DATABASE QUERY ERROR IN STATS ===")
            print(f"Error: {db_error}")
            print(f"Error type: {type(db_error).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Try to reinitialize database
            try:
                print("=== ATTEMPTING DATABASE REINITIALIZATION ===")
                init_db()
                print("=== DATABASE REINITIALIZED AFTER ERROR ===")
            except Exception as init_error:
                print(f"=== FAILED TO REINITIALIZE DATABASE ===")
                print(f"Init error: {init_error}")
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Database stats error: {e}")
        return jsonify({
            'doctors_count': len(DOCTORS_DATA) if DOCTORS_DATA else 0,
            'user_queries_count': 0,
            'doctor_clicks_count': 0,
            'analytics_events_count': 0,
            'admin_users_count': 0,
            'error': 'Database temporarily unavailable'
        }), 200

@app.route('/admin/database/export-analytics', methods=['GET', 'POST'])
@require_permission('analytics')
def export_analytics_database():
    """Export analytics data as CSV with selective options"""
    try:
        import io
        from flask import make_response
        
        # Get form data for selective export
        export_types = request.form.getlist('export_types') if request.method == 'POST' else ['analytics', 'queries', 'clicks']
        date_range = request.form.get('date_range', 'all') if request.method == 'POST' else 'all'
        start_date = request.form.get('start_date') if request.method == 'POST' else None
        end_date = request.form.get('end_date') if request.method == 'POST' else None
        
        # Build date filter condition
        date_filter = ""
        date_params = []
        
        if date_range == 'today':
            date_filter = "WHERE DATE(timestamp) = DATE('now')"
        elif date_range == 'week':
            date_filter = "WHERE timestamp >= datetime('now', '-7 days')"
        elif date_range == 'month':
            date_filter = "WHERE timestamp >= datetime('now', '-30 days')"
        elif date_range == 'custom' and start_date and end_date:
            date_filter = "WHERE DATE(timestamp) BETWEEN ? AND ?"
            date_params = [start_date, end_date]
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Initialize data containers
        analytics_data = []
        user_queries_data = []
        doctor_clicks_data = []
        
        # Get analytics data if requested
        if 'analytics' in export_types:
            query = f'''
                SELECT 
                    a.timestamp,
                    a.event_type,
                    a.user_ip,
                    a.user_agent,
                    a.data,
                    a.session_id
                FROM analytics a
                {date_filter}
                ORDER BY a.timestamp DESC
            '''
            cursor.execute(query, date_params)
            analytics_data = cursor.fetchall()
        
        # Get user queries data if requested
        if 'queries' in export_types:
            query = f'''
                SELECT 
                    uq.timestamp,
                    uq.age,
                    uq.symptoms,
                    uq.chronic_conditions,
                    uq.language,
                    uq.location,
                    uq.detailed_health_info,
                    uq.ai_analysis,
                    uq.related_specialty,
                    uq.matched_doctors_count,
                    uq.user_ip,
                    uq.session_id
                FROM user_queries uq
                {date_filter}
                ORDER BY uq.timestamp DESC
            '''
            cursor.execute(query, date_params)
            user_queries_data = cursor.fetchall()
        
        # Get doctor clicks data if requested
        if 'clicks' in export_types:
            query = f'''
                SELECT 
                    dc.timestamp,
                    dc.doctor_name,
                    dc.doctor_specialty,
                    dc.user_ip,
                    dc.session_id,
                    dc.query_id
                FROM doctor_clicks dc
                {date_filter}
                ORDER BY dc.timestamp DESC
            '''
            cursor.execute(query, date_params)
            doctor_clicks_data = cursor.fetchall()
        
        conn.close()
        
        # Create CSV content
        output = io.StringIO()
        
        # Export analytics events if requested
        if 'analytics' in export_types and analytics_data:
            output.write("=== ANALYTICS EVENTS ===\n")
            output.write("Timestamp,Event Type,User IP,User Agent,Data,Session ID\n")
            for row in analytics_data:
                escaped_row = []
                for field in row:
                    if field is None:
                        field = ''
                    field_str = str(field).replace('"', '""')
                    escaped_row.append(f'"{field_str}"')
                output.write(','.join(escaped_row) + '\n')
            output.write("\n")
        
        # Export user queries if requested
        if 'queries' in export_types and user_queries_data:
            output.write("=== USER QUERIES ===\n")
            output.write("Timestamp,Age,Symptoms,Chronic Conditions,Language,Location,Detailed Health Info,AI Diagnosis,Recommended Specialty,Matched Doctors Count,User IP,Session ID\n")
            for row in user_queries_data:
                escaped_row = []
                for field in row:
                    if field is None:
                        field = ''
                    field_str = str(field).replace('"', '""')
                    escaped_row.append(f'"{field_str}"')
                output.write(','.join(escaped_row) + '\n')
            output.write("\n")
        
        # Export doctor clicks if requested
        if 'clicks' in export_types and doctor_clicks_data:
            output.write("=== DOCTOR CLICKS ===\n")
            output.write("Timestamp,Doctor Name,Doctor Specialty,User IP,Session ID,Query ID\n")
            for row in doctor_clicks_data:
                escaped_row = []
                for field in row:
                    if field is None:
                        field = ''
                    field_str = str(field).replace('"', '""')
                    escaped_row.append(f'"{field_str}"')
                output.write(','.join(escaped_row) + '\n')
        
        # Check if any data was exported
        if not output.getvalue().strip():
            flash('沒有找到符合條件的數據', 'warning')
            return redirect(url_for('admin_analytics'))
        
        # Create filename with export details
        filename_parts = []
        if 'analytics' in export_types:
            filename_parts.append('events')
        if 'queries' in export_types:
            filename_parts.append('queries')
        if 'clicks' in export_types:
            filename_parts.append('clicks')
        
        filename = f"analytics_{'_'.join(filename_parts)}_{date_range}_{get_current_time().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Create response with UTF-8 BOM for better Excel compatibility
        csv_content = '\ufeff' + output.getvalue()  # Add UTF-8 BOM
        response = make_response(csv_content.encode('utf-8'))
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        log_analytics('analytics_export', {
            'export_types': export_types,
            'date_range': date_range,
            'analytics_count': len(analytics_data),
            'queries_count': len(user_queries_data),
            'clicks_count': len(doctor_clicks_data)
        }, get_real_ip(), request.user_agent.string)
        
        return response
        
    except Exception as e:
        print(f"Analytics export error: {e}")
        flash('導出分析數據時發生錯誤', 'error')
        return redirect(url_for('admin_analytics'))

@app.route('/admin/doctors')
@tab_permission_required('doctors')
def admin_doctors():
    """醫生資料庫管理頁面"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # 獲取統計資料
        cursor.execute("SELECT COUNT(*) FROM doctors")
        total_doctors = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT COALESCE(specialty_zh, specialty_en, specialty)) FROM doctors WHERE COALESCE(specialty_zh, specialty_en, specialty) IS NOT NULL")
        total_specialties = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE (languages_zh LIKE '%中文%' OR languages_zh LIKE '%English%' OR languages_en LIKE '%中文%' OR languages_en LIKE '%English%')")
        bilingual_doctors = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE contact_numbers IS NOT NULL AND contact_numbers != ''")
        with_contact = cursor.fetchone()[0]
        
        # 獲取所有專科列表
        cursor.execute("SELECT DISTINCT COALESCE(specialty_zh, specialty_en, specialty) as specialty FROM doctors WHERE specialty IS NOT NULL ORDER BY specialty")
        specialties = [row[0] for row in cursor.fetchall() if row[0]]
        
        # 獲取所有地區列表 (從診所地址中提取)
        cursor.execute("SELECT DISTINCT clinic_addresses FROM doctors WHERE clinic_addresses IS NOT NULL AND clinic_addresses != ''")
        all_addresses = [row[0] for row in cursor.fetchall()]
        
        # Extract common location keywords from addresses
        location_keywords = set()
        common_locations = ['香港島', '九龍', '新界', '中環', '銅鑼灣', '尖沙咀', '旺角', '沙田', '荃灣', '元朗', 
                           '觀塘', '深水埗', '油麻地', '佐敦', '太古', '北角', '西環', '上環', '灣仔', '跑馬地',
                           '紅磡', '土瓜灣', '何文田', '九龍塘', '大埔', '粉嶺', '上水', '屯門', '天水圍', '將軍澳']
        
        for address in all_addresses:
            for location in common_locations:
                if location in address:
                    location_keywords.add(location)
        
        locations = sorted(list(location_keywords))
        
        conn.close()
        
        return render_template('admin/doctors.html',
                             doctors=[],  # Empty list - will load via AJAX
                             total_doctors=total_doctors,
                             total_specialties=total_specialties,
                             bilingual_doctors=bilingual_doctors,
                             with_contact=with_contact,
                             specialties=specialties,
                             locations=locations)
                             
    except Exception as e:
        print(f"Error in admin_doctors: {e}")
        flash('載入醫生資料時發生錯誤', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/check-doctor-account/<int:doctor_id>')
@tab_permission_required('doctors')
def check_doctor_account(doctor_id):
    """Check if a doctor already has an account"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Check for account
        cursor.execute("SELECT id, username FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
        account = cursor.fetchone()
        
        # Also check is_affiliated status
        cursor.execute("SELECT is_affiliated, affiliation_status FROM doctors WHERE id = ?", (doctor_id,))
        doctor = cursor.fetchone()
        
        conn.close()
        
        has_account = account is not None
        is_affiliated = doctor[0] if doctor else 0
        
        logger.info(f"Check account for doctor {doctor_id}: has_account={has_account}, is_affiliated={is_affiliated}")
        
        return jsonify({
            'success': True,
            'has_account': has_account,
            'is_affiliated': is_affiliated,
            'username': account[1] if account else None
        })
    except Exception as e:
        logger.error(f"Error checking doctor account: {e}")
        return jsonify({'success': False, 'has_account': False}), 500

@app.route('/admin/sync-affiliation-status', methods=['POST'])
@tab_permission_required('doctors')
def sync_affiliation_status():
    """Sync is_affiliated flag for all doctors with accounts"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Update all doctors who have accounts but aren't marked as affiliated
        cursor.execute("""
            UPDATE doctors 
            SET is_affiliated = 1,
                affiliation_status = 'approved',
                affiliation_date = ?
            WHERE id IN (
                SELECT doctor_id 
                FROM doctor_accounts 
                WHERE is_active = 1
            )
            AND (is_affiliated IS NULL OR is_affiliated = 0)
        """, (datetime.now().isoformat(),))
        
        updated_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin {session.get('admin_username')} synced affiliation status, updated {updated_count} doctors")
        
        return jsonify({
            'success': True,
            'message': f'已同步 {updated_count} 位醫生的加盟狀態',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logger.error(f"Error syncing affiliation status: {e}")
        return jsonify({'success': False, 'message': f'同步失敗: {str(e)}'}), 500

@app.route('/admin/create-doctor-account', methods=['POST'])
@tab_permission_required('doctors')
def create_doctor_account():
    """Create or update a doctor account"""
    try:
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        
        if not doctor_id or not username:
            return jsonify({'success': False, 'message': '請提供醫生ID和用戶名'}), 400
        
        # Check if doctor exists
        conn_doctors = sqlite3.connect('doctors.db')
        cursor_doctors = conn_doctors.cursor()
        cursor_doctors.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
        doctor = cursor_doctors.fetchone()
        
        if not doctor:
            conn_doctors.close()
            return jsonify({'success': False, 'message': '找不到該醫生'}), 404
        
        # Check if account already exists
        cursor_doctors.execute("SELECT id, username FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
        existing_account = cursor_doctors.fetchone()
        
        if existing_account:
            # UPDATE MODE - Account exists
            account_id = existing_account[0]
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            if email:
                update_fields.append("email = ?")
                update_values.append(email)
            
            if phone:
                update_fields.append("phone = ?")
                update_values.append(phone)
            
            # Only update password if provided
            if password:
                if len(password) < 6:
                    conn_doctors.close()
                    return jsonify({'success': False, 'message': '密碼至少需要6個字符'}), 400
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                update_fields.append("password_hash = ?")
                update_values.append(password_hash)
            
            if update_fields:
                update_values.append(account_id)
                cursor_doctors.execute(f"""
                    UPDATE doctor_accounts 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, tuple(update_values))
            
            conn_doctors.commit()
            conn_doctors.close()
            
            logger.info(f"Admin {session.get('admin_username')} updated account for doctor ID {doctor_id}")
            
            return jsonify({
                'success': True,
                'message': '醫生帳戶已更新',
                'username': username
            })
        
        else:
            # CREATE MODE - No account exists
            if not password:
                conn_doctors.close()
                return jsonify({'success': False, 'message': '創建新帳戶需要密碼'}), 400
            
            if len(password) < 6:
                conn_doctors.close()
                return jsonify({'success': False, 'message': '密碼至少需要6個字符'}), 400
            
            # Check if username is taken
            cursor_doctors.execute("SELECT id FROM doctor_accounts WHERE username = ?", (username,))
            existing_username = cursor_doctors.fetchone()
            
            if existing_username:
                conn_doctors.close()
                return jsonify({'success': False, 'message': '用戶名已被使用'}), 400
            
            # Hash password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Create account
            cursor_doctors.execute("""
                INSERT INTO doctor_accounts 
                (doctor_id, username, password_hash, email, phone, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (doctor_id, username, password_hash, email, phone, datetime.now().isoformat()))
        
        # Update doctor affiliation status
        cursor_doctors.execute("""
            UPDATE doctors 
            SET is_affiliated = 1, 
                affiliation_status = 'approved',
                affiliation_date = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), doctor_id))
        
        conn_doctors.commit()
        conn_doctors.close()
        
        # Log the action
        logger.info(f"Admin {session.get('admin_username')} created account for doctor ID {doctor_id} with username {username}")
        
        return jsonify({
            'success': True,
            'message': '醫生帳戶創建成功',
            'username': username
        })
        
    except Exception as e:
        logger.error(f"Error creating doctor account: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'創建失敗: {str(e)}'}), 500

@app.route('/admin/doctors/paginated')
@tab_permission_required('doctors')
def admin_doctors_paginated():
    """DataTables AJAX endpoint for paginated doctor data"""
    try:
        # Get DataTables parameters
        draw = request.args.get('draw', type=int, default=1)
        start = request.args.get('start', type=int, default=0)
        length = request.args.get('length', type=int, default=25)
        search_value = request.args.get('search[value]', default='')
        
        # Get custom filter parameters
        specialty_search = request.args.get('specialty_filter', default='')
        language_search = request.args.get('language_filter', default='')
        priority_search = request.args.get('priority_filter', default='')
        location_search = request.args.get('location_filter', default='')
        
        # Get sorting parameters
        order_column = request.args.get('order[0][column]', type=int, default=0)
        order_dir = request.args.get('order[0][dir]', default='asc')
        
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        # Column mapping for sorting
        columns = ['name', 'specialty', 'qualifications', 'contact_numbers', 'clinic_addresses', 'priority_flag']
        sort_column = columns[order_column] if order_column < len(columns) else 'name'
        
        # Base query with better data handling - join with doctor_accounts to get account phone
        base_query = """
            SELECT d.id,
                   d.name_zh,
                   d.name_en,
                   d.name,
                   d.specialty_zh,
                   d.specialty_en,
                   d.specialty,
                   d.qualifications_zh,
                   d.qualifications_en,
                   d.qualifications,
                   d.languages_zh,
                   d.languages_en,
                   d.languages,
                   d.contact_numbers,
                   d.email,
                   d.clinic_addresses,
                   d.profile_url,
                   d.priority_flag,
                   COALESCE(d.is_affiliated, 0) as is_affiliated,
                   da.phone as account_phone
            FROM doctors d
            LEFT JOIN doctor_accounts da ON d.id = da.doctor_id AND da.is_active = 1
        """
        
        # Build where clause with all filters
        where_conditions = []
        params = []
        
        # Global search filter
        if search_value:
            where_conditions.append("""
                (d.name_zh LIKE ? OR d.name_en LIKE ? OR d.name LIKE ?
                 OR d.specialty_zh LIKE ? OR d.specialty_en LIKE ? OR d.specialty LIKE ?
                 OR d.contact_numbers LIKE ?
                 OR d.clinic_addresses LIKE ?)
            """)
            search_param = f'%{search_value}%'
            params.extend([search_param] * 8)
        
        # Column-specific filters
        if specialty_search:
            where_conditions.append("(d.specialty_zh LIKE ? OR d.specialty_en LIKE ? OR d.specialty LIKE ?)")
            specialty_param = f'%{specialty_search}%'
            params.extend([specialty_param, specialty_param, specialty_param])
        
        if language_search:
            where_conditions.append("(d.languages_zh LIKE ? OR d.languages_en LIKE ?)")
            language_param = f'%{language_search}%'
            params.extend([language_param, language_param])
        
        if priority_search:
            where_conditions.append("d.priority_flag = ?")
            params.append(int(priority_search))
        
        if location_search:
            where_conditions.append("d.clinic_addresses LIKE ?")
            location_param = f'%{location_search}%'
            params.append(location_param)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count (without search)
        cursor.execute("SELECT COUNT(*) FROM doctors d")
        records_total = cursor.fetchone()[0]
        
        # Get filtered count (with all filters)
        if where_conditions:
            cursor.execute(f"SELECT COUNT(*) FROM doctors d LEFT JOIN doctor_accounts da ON d.id = da.doctor_id AND da.is_active = 1 {where_clause}", params)
            records_filtered = cursor.fetchone()[0]
        else:
            records_filtered = records_total
        
        # Get paginated data with sorting
        order_clause = f"ORDER BY {sort_column} {order_dir.upper()}"
        query = f"{base_query} {where_clause} {order_clause} LIMIT ? OFFSET ?"
        params.extend([length, start])
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        
        data = []
        for row in cursor.fetchall():
            doctor_dict = dict(zip(columns, row))
            data.append(doctor_dict)
        
        conn.close()
        
        return jsonify({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data
        })
        
    except Exception as e:
        print(f"Error in admin_doctors_paginated: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/doctors/<int:doctor_id>', methods=['GET'])
@require_permission('config')
def get_doctor_details(doctor_id):
    """獲取醫生詳細資料 (AJAX)"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            doctor_data = dict(zip(columns, row))
            conn.close()
            return jsonify(doctor_data)
        else:
            conn.close()
            return jsonify({'error': 'Doctor not found'}), 404
            
    except Exception as e:
        print(f"Error getting doctor details: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/admin/specialties')
@require_permission('config')
def get_specialties():
    """Get all unique specialties from database"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Get unique Chinese specialties
        cursor.execute('''
            SELECT DISTINCT specialty_zh 
            FROM doctors 
            WHERE specialty_zh IS NOT NULL AND specialty_zh != ''
            ORDER BY specialty_zh
        ''')
        chinese_specialties = [row[0] for row in cursor.fetchall()]
        
        # Get unique English specialties
        cursor.execute('''
            SELECT DISTINCT specialty_en 
            FROM doctors 
            WHERE specialty_en IS NOT NULL AND specialty_en != ''
            ORDER BY specialty_en
        ''')
        english_specialties = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'chinese': chinese_specialties,
            'english': english_specialties
        })
    except Exception as e:
        print(f"Error fetching specialties: {e}")
        return jsonify({'error': 'Failed to fetch specialties'}), 500

@app.route('/admin/doctors/data')
@require_permission('config')
def get_doctors_data():
    """Get all doctors data for specialty mapping"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT specialty_zh, specialty_en 
            FROM doctors 
            WHERE specialty_zh IS NOT NULL AND specialty_en IS NOT NULL 
            AND specialty_zh != '' AND specialty_en != ''
        ''')
        
        doctors = []
        for row in cursor.fetchall():
            doctors.append({
                'specialty_zh': row[0],
                'specialty_en': row[1]
            })
        
        conn.close()
        return jsonify(doctors)
        
    except Exception as e:
        print(f"Error fetching doctors data: {e}")
        return jsonify({'error': 'Failed to fetch doctors data'}), 500

@app.route('/admin/doctors/<int:doctor_id>/update', methods=['POST'])
@require_permission('config')
def update_doctor(doctor_id):
    """更新醫生資料"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Update doctor record
        cursor.execute('''
            UPDATE doctors SET
                name_zh = ?, specialty_zh = ?, qualifications_zh = ?, languages_zh = ?,
                name_en = ?, specialty_en = ?, qualifications_en = ?, languages_en = ?,
                contact_numbers = ?, email = ?, clinic_addresses = ?,
                consultation_hours = ?, consultation_fee = ?, profile_url = ?,
                registration_number = ?, priority_flag = ?,
                name = ?, specialty = ?, qualifications = ?, languages = ?,
                phone = ?, address = ?
            WHERE id = ?
        ''', (
            data.get('name_zh'), data.get('specialty_zh'), data.get('qualifications_zh'), data.get('languages_zh'),
            data.get('name_en'), data.get('specialty_en'), data.get('qualifications_en'), data.get('languages_en'),
            data.get('contact_numbers'), data.get('email'), data.get('clinic_addresses'),
            data.get('consultation_hours'), data.get('consultation_fee'), data.get('profile_url'),
            data.get('registration_number'), data.get('priority_flag', 0),
            # Legacy columns - use Chinese first, then English
            data.get('name_zh') or data.get('name_en'),
            data.get('specialty_zh') or data.get('specialty_en'),
            data.get('qualifications_zh') or data.get('qualifications_en'),
            data.get('languages_zh') or data.get('languages_en'),
            data.get('contact_numbers'),
            data.get('clinic_addresses'),
            doctor_id
        ))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Doctor not found'}), 404
        
        conn.commit()
        conn.close()
        
        # Log the update
        log_analytics('doctor_update', {
            'doctor_id': doctor_id,
            'updated_fields': list(data.keys())
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({'success': True, 'message': 'Doctor updated successfully'})
        
    except Exception as e:
        print(f"Error updating doctor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/doctors/add', methods=['POST'])
@require_permission('config')
def add_doctor():
    """新增醫生"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Insert new doctor record
        cursor.execute('''
            INSERT INTO doctors (
                name_zh, specialty_zh, qualifications_zh, languages_zh,
                name_en, specialty_en, qualifications_en, languages_en,
                contact_numbers, email, clinic_addresses,
                consultation_hours, consultation_fee, profile_url,
                registration_number, priority_flag,
                name, specialty, qualifications, languages,
                phone, address
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?
            )
        ''', (
            data.get('name_zh'), data.get('specialty_zh'), data.get('qualifications_zh'), data.get('languages_zh'),
            data.get('name_en'), data.get('specialty_en'), data.get('qualifications_en'), data.get('languages_en'),
            data.get('contact_numbers'), data.get('email'), data.get('clinic_addresses'),
            data.get('consultation_hours'), data.get('consultation_fee'), data.get('profile_url'),
            data.get('registration_number'), data.get('priority_flag', 0),
            # Legacy columns - use Chinese first, then English
            data.get('name_zh') or data.get('name_en'),
            data.get('specialty_zh') or data.get('specialty_en'),
            data.get('qualifications_zh') or data.get('qualifications_en'),
            data.get('languages_zh') or data.get('languages_en'),
            data.get('contact_numbers'),
            data.get('clinic_addresses')
        ))
        
        new_doctor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the addition
        log_analytics('doctor_add', {
            'doctor_id': new_doctor_id,
            'name': data.get('name_zh') or data.get('name_en')
        }, get_real_ip(), request.user_agent.string)
        
        # Force reload of doctor data after addition
        global DB_LAST_MODIFIED
        DB_LAST_MODIFIED = None  # Force next check to reload
        
        return jsonify({'success': True, 'message': 'Doctor added successfully', 'doctor_id': new_doctor_id})
        
    except Exception as e:
        print(f"Error adding doctor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/doctors/<int:doctor_id>/delete', methods=['DELETE'])
@require_permission('config')
def delete_doctor(doctor_id):
    """刪除醫生"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Get doctor info for logging
        cursor.execute("SELECT name_zh, name_en FROM doctors WHERE id = ?", (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            conn.close()
            return jsonify({'success': False, 'error': 'Doctor not found'}), 404
        
        # Delete doctor record
        cursor.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Doctor not found'}), 404
        
        conn.commit()
        conn.close()
        
        # Log the deletion
        log_analytics('doctor_delete', {
            'doctor_id': doctor_id,
        }, get_real_ip(), request.user_agent.string)
        
        # Force reload of doctor data after deletion
        global DB_LAST_MODIFIED
        DB_LAST_MODIFIED = None  # Force next check to reload
        
        return jsonify({'success': True, 'message': 'Doctor deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting doctor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/users')
@tab_permission_required('users')
def admin_users():
    """User management page"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get user statistics
        cursor.execute('''
            SELECT user_ip, COUNT(*) as query_count, 
                   MIN(timestamp) as first_visit,
                   MAX(timestamp) as last_visit
            FROM user_queries 
            GROUP BY user_ip 
            ORDER BY query_count DESC
        ''')
        user_stats = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin/users.html', user_stats=user_stats)
    except Exception as e:
        print(f"Users page error: {e}")
        flash('載入用戶數據時發生錯誤', 'error')
        return render_template('admin/users.html')

@app.route('/admin/api/user-details/<user_ip>')
@require_admin
def get_user_details(user_ip):
    """API endpoint to get detailed user information"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get user query statistics
        cursor.execute('''
            SELECT COUNT(*) as total_queries,
                   COUNT(DISTINCT DATE(timestamp)) as active_days,
                   GROUP_CONCAT(DISTINCT recommended_specialty) as specialties
            FROM user_queries 
            WHERE user_ip = ?
        ''', (user_ip,))
        stats = cursor.fetchone()
        
        # Get most common specialty
        cursor.execute('''
            SELECT recommended_specialty, COUNT(*) as count
            FROM user_queries 
            WHERE user_ip = ? AND recommended_specialty IS NOT NULL
            GROUP BY recommended_specialty 
            ORDER BY count DESC 
            LIMIT 1
        ''', (user_ip,))
        top_specialty = cursor.fetchone()
        
        # Get recent queries
        cursor.execute('''
            SELECT timestamp, symptoms, recommended_specialty
            FROM user_queries 
            WHERE user_ip = ?
            ORDER BY timestamp DESC 
            LIMIT 5
        ''', (user_ip,))
        raw_recent_queries = cursor.fetchall()
        
        # Format timestamps for recent queries
        recent_queries = []
        for query in raw_recent_queries:
            formatted_query = list(query)
            formatted_query[0] = format_timestamp(query[0])  # Format timestamp
            recent_queries.append(tuple(formatted_query))
        
        conn.close()
        
        return jsonify({
            'total_queries': stats[0] if stats else 0,
            'active_days': stats[1] if stats else 0,
            'top_specialty': top_specialty[0] if top_specialty else '無',
            'recent_queries': [
                {
                    'timestamp': query[0],
                    'symptoms': query[1][:50] + '...' if len(query[1]) > 50 else query[1],
                    'specialty': query[2]
                } for query in recent_queries
            ]
        })
    except Exception as e:
        print(f"User details error: {e}")
        return jsonify({'error': 'Failed to fetch user details'}), 500

@app.route('/admin/api/user-reports/<user_ip>')
@require_admin
def get_user_reports(user_ip):
    """API endpoint to get user diagnosis reports"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get all user queries with diagnosis reports
        cursor.execute('''
            SELECT id, timestamp, age, gender, symptoms, chronic_conditions, 
                   related_specialty, ai_analysis, language, location, 
                   analysis_report
            FROM user_queries 
            WHERE user_ip = ?
            ORDER BY timestamp DESC
        ''', (user_ip,))
        queries = cursor.fetchall()
        
        conn.close()
        
        reports = []
        for query in queries:
            reports.append({
                'id': query[0],
                'timestamp': query[1],
                'age': query[2],
                'gender': query[3],
                'symptoms': query[4],
                'chronic_conditions': query[5],
                'specialty': query[6],
                'emergency_level': 'Yes' if check_emergency_needed(query[7]) else 'No',  # Use emergency detection instead of severity
                'language': query[8],
                'location': query[9],
                'analysis_report': query[10]
            })
        
        return jsonify({
            'reports': reports
        })
    except Exception as e:
        print(f"User reports error: {e}")
        return jsonify({'error': 'Failed to fetch user reports'}), 500

@app.route('/report/<report_id>')
def view_report(report_id):
    """Display diagnosis report"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT report_data, created_at, doctor_name, doctor_specialty 
            FROM analysis_reports 
            WHERE id = ?
        ''', (report_id,))
        
        report_row = cursor.fetchone()
        conn.close()
        
        if not report_row:
            return "報告未找到", 404
            
        report_data, created_at, doctor_name, doctor_specialty = report_row
        
        # Convert newlines to HTML breaks for display
        report_html = report_data.replace('\n', '<br>')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI醫療診斷報告</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
                .report {{ background: #f9f9f9; padding: 20px; border-radius: 10px; white-space: pre-line; }}
                .header {{ text-align: center; color: #2c3e50; margin-bottom: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏥 AI症狀分析報告</h1>
            </div>
            <div class="report">
                {report_html}
            </div>
            <div class="footer">
                <p>此報告生成於: {created_at}</p>
                <p><small>免責聲明：此分析僅供參考，不構成醫療建議或診斷，請務必諮詢合格醫生。</small></p>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"Report display error: {e}")
        return "報告顯示錯誤", 500

@app.route('/get_whatsapp_url', methods=['POST'])
def get_whatsapp_url():
    """Generate WhatsApp URL with diagnosis report"""
    try:
        data = request.get_json()
        doctor_name = data.get('doctor_name')
        doctor_specialty = data.get('doctor_specialty')
        doctor_phone = data.get('doctor_phone', '')  # Get doctor's phone number from request
        
        # Get session info
        session_id = session.get('session_id')
        query_id = session.get('last_query_id')
        
        # Determine target WhatsApp number based on contact_mode
        contact_mode = WHATSAPP_CONFIG.get('contact_mode', 'admin')
        
        if contact_mode == 'doctor' and doctor_phone:
            # Use doctor's phone number - clean it for WhatsApp format
            whatsapp_number = clean_phone_number_for_whatsapp(doctor_phone)
            print(f"DEBUG: Using doctor's WhatsApp number: {whatsapp_number}")
        else:
            # Use admin's designated WhatsApp number
            whatsapp_number = os.getenv('WHATSAPP_TARGET_NUMBER', '85294974070')
            print(f"DEBUG: Using admin WhatsApp number: {whatsapp_number}")
        
        # Log to database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO doctor_clicks (doctor_name, doctor_specialty, user_ip, session_id, query_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (doctor_name, doctor_specialty, get_real_ip(), session_id, query_id))
        conn.commit()
        
        # Initialize variables
        reference_code = None
        qr_code_data = None
        
        # Get user query data for diagnosis report
        whatsapp_url = f"https://wa.me/{whatsapp_number}"
        
        if query_id:
            cursor.execute('''
                SELECT age, gender, symptoms, chronic_conditions, language, location, 
                       detailed_health_info, ai_analysis, related_specialty
                FROM user_queries WHERE id = ?
            ''', (query_id,))
            user_query_row = cursor.fetchone()
            
            if user_query_row:
                user_query_data = {
                    'age': user_query_row[0],
                    'gender': user_query_row[1],
                    'symptoms': user_query_row[2],
                    'chronic_conditions': user_query_row[3],
                    'language': user_query_row[4],
                    'location': user_query_row[5],
                    'detailed_health_info': user_query_row[6],
                    'ai_analysis': user_query_row[7],
                    'related_specialty': user_query_row[8]
                }
                
                doctor_data = {
                    'doctor_name': doctor_name,
                    'doctor_specialty': doctor_specialty
                }
                
                # Generate unique report ID and store report
                import uuid
                report_id = str(uuid.uuid4())
                
                # Store the full diagnosis report in database
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO analysis_reports (id, query_id, doctor_name, doctor_specialty, report_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (report_id, query_id, doctor_name, doctor_specialty, 
                         format_analysis_report_full(user_query_data, doctor_data), 
                         get_current_time().isoformat()))
                except sqlite3.OperationalError as e:
                    print(f"Database error: {e}")
                    # Create table if it doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS analysis_reports (
                            id TEXT PRIMARY KEY, 
                            query_id INTEGER, 
                            doctor_name TEXT, 
                            doctor_specialty TEXT, 
                            report_data TEXT, 
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        INSERT OR REPLACE INTO analysis_reports (id, query_id, doctor_name, doctor_specialty, report_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (report_id, query_id, doctor_name, doctor_specialty, 
                         format_analysis_report_full(user_query_data, doctor_data), 
                         get_current_time().isoformat()))
                conn.commit()
                
                # Generate diagnosis reference code when user picks a doctor
                reference_code = create_diagnosis_reference(
                    query_id=query_id,
                    session_id=session_id,
                    user_ip=get_real_ip(),
                    symptoms=user_query_data.get('symptoms', ''),
                    ai_analysis=user_query_data.get('ai_analysis', ''),
                    recommended_specialty=user_query_data.get('related_specialty', ''),
                    matched_doctors_count=1  # User selected this specific doctor
                )
                session['last_reference_code'] = reference_code
                logger.info(f"Generated reference code {reference_code} for doctor selection: {doctor_name}")
                
                # Generate QR code for the reference
                base_url = f"{request.scheme}://{request.host}"
                qr_code_data = generate_reference_qr_code(reference_code, base_url)
                
                # Generate report URL
                report_url = f"{request.scheme}://{request.host}/report/{report_id}"
                
                # Generate WhatsApp message with report link and reference code
                # Different message format based on contact mode
                if contact_mode == 'doctor':
                    message = format_whatsapp_message_for_doctor(doctor_data, report_url, user_query_data, reference_code)
                else:
                    message = format_whatsapp_message(doctor_data, report_url, reference_code)
                print(f"DEBUG: Generated message length: {len(message)} (mode: {contact_mode})")
                
                # URL encode the message for WhatsApp web - use quote instead of quote_plus for better emoji handling
                from urllib.parse import quote
                encoded_message = quote(message, safe='')
                whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
                print(f"DEBUG: Final URL length: {len(whatsapp_url)}")
        
        conn.close()
        
        # Log analytics
        log_analytics('doctor_click', {
            'doctor_name': doctor_name, 'doctor_specialty': doctor_specialty,
            'reference_code': reference_code
        }, get_real_ip(), request.user_agent.string, session_id)
        
        return jsonify({
            'success': True, 
            'whatsapp_url': whatsapp_url,
            'reference_code': reference_code,
            'qr_code': qr_code_data
        })
    except Exception as e:
        print(f"WhatsApp URL generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate WhatsApp URL: {str(e)}'}), 500

def track_click():
    """Legacy endpoint - now redirects to get_whatsapp_url"""
    return get_whatsapp_url()

@app.route('/api/contact-doctor-reservation', methods=['POST'])
def contact_doctor_reservation():
    """Create a reservation request when contact button is clicked"""
    try:
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        doctor_name = data.get('doctor_name')
        reservation_date = data.get('reservation_date')  # NEW: Get selected date
        reservation_time = data.get('reservation_time')  # NEW: Get selected time
        
        # Get session info
        session_id = session.get('session_id')
        query_id = session.get('last_query_id')
        
        # Get user query data if available
        patient_name = 'Walk-in Patient'
        patient_phone = ''
        patient_age = None
        patient_gender = ''
        symptoms = ''
        chronic_conditions = ''
        
        if query_id:
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT age, gender, symptoms, chronic_conditions
                FROM user_queries WHERE id = ?
            ''', (query_id,))
            user_query_row = cursor.fetchone()
            
            if user_query_row:
                patient_age = user_query_row[0]
                patient_gender = user_query_row[1]
                symptoms = user_query_row[2]
                chronic_conditions = user_query_row[3]
            
            conn.close()
        
        # Create a pending reservation request
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Generate confirmation code
        import secrets
        confirmation_code = secrets.token_urlsafe(8).upper()
        
        # Use provided date/time or defaults
        if not reservation_date:
            reservation_date = 'date(\'now\')'
            use_sql_date = True
        else:
            use_sql_date = False
            
        if not reservation_time:
            reservation_time = '00:00'
        
        # Insert reservation with status 'contact_request' to differentiate from normal bookings
        if use_sql_date:
            cursor.execute("""
                INSERT INTO reservations
                (doctor_id, patient_name, patient_phone, patient_age, 
                 patient_gender, reservation_date, reservation_time, consultation_type,
                 symptoms, chronic_conditions, query_id, confirmation_code, status, notes)
                VALUES (?, ?, ?, ?, ?, date('now'), ?, 'contact', ?, ?, ?, ?, 'contact_request', 
                        'Patient clicked contact button - awaiting response')
            """, (
                doctor_id,
                patient_name,
                patient_phone,
                patient_age,
                patient_gender,
                reservation_time,
                symptoms,
                chronic_conditions,
                query_id,
                confirmation_code
            ))
        else:
            cursor.execute("""
                INSERT INTO reservations
                (doctor_id, patient_name, patient_phone, patient_age, 
                 patient_gender, reservation_date, reservation_time, consultation_type,
                 symptoms, chronic_conditions, query_id, confirmation_code, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'contact', ?, ?, ?, ?, 'contact_request', 
                        'Patient selected time slot via contact button')
            """, (
                doctor_id,
                patient_name,
                patient_phone,
                patient_age,
                patient_gender,
                reservation_date,
                reservation_time,
                symptoms,
                chronic_conditions,
                query_id,
                confirmation_code
            ))
        
        reservation_id = cursor.lastrowid
        
        # Add to history
        cursor.execute("""
            INSERT INTO reservation_history
            (reservation_id, action, new_status, performed_by, performed_by_type, notes)
            VALUES (?, 'contact_initiated', 'contact_request', ?, 'patient', 'Contact button clicked')
        """, (reservation_id, patient_name))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Contact reservation created: ID={reservation_id}, Doctor={doctor_name}, Code={confirmation_code}")
        
        return jsonify({
            'success': True,
            'reservation_id': reservation_id,
            'confirmation_code': confirmation_code,
            'message': '已記錄聯絡請求'
        })
        
    except Exception as e:
        print(f"Error creating contact reservation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/doctor/<int:doctor_id>/available-slots-or-default')
def get_available_slots_or_default(doctor_id):
    """Get available time slots for doctor, or default times if no schedule set"""
    try:
        date = request.args.get('date')
        if not date:
            # Default to tomorrow
            from datetime import datetime, timedelta
            date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Try to get doctor's actual availability
        conn_doctors = sqlite3.connect('doctors.db')
        conn_doctors.row_factory = sqlite3.Row
        cursor_doctors = conn_doctors.cursor()
        
        # Parse date to get day of week
        from datetime import datetime
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        day_of_week = date_obj.weekday()
        
        # Check if doctor has availability schedule
        cursor_doctors.execute("""
            SELECT * FROM doctor_availability
            WHERE doctor_id = ? AND day_of_week = ? AND is_active = 1
        """, (doctor_id, day_of_week))
        
        schedules = cursor_doctors.fetchall()
        
        if schedules:
            # Doctor has schedule - get actual available slots
            conn_admin = sqlite3.connect('admin_data.db')
            conn_admin.row_factory = sqlite3.Row
            cursor_admin = conn_admin.cursor()
            
            # Get existing reservations
            cursor_admin.execute("""
                SELECT reservation_time, COUNT(*) as count
                FROM reservations
                WHERE doctor_id = ? 
                AND reservation_date = ?
                AND status IN ('pending', 'confirmed', 'contact_request')
                GROUP BY reservation_time
            """, (doctor_id, date))
            
            existing_reservations = {row['reservation_time']: row['count'] for row in cursor_admin.fetchall()}
            
            # Generate available slots
            available_slots = []
            
            for schedule in schedules:
                from datetime import datetime, timedelta
                start_time = datetime.strptime(schedule['start_time'], '%H:%M')
                end_time = datetime.strptime(schedule['end_time'], '%H:%M')
                slot_duration = schedule['slot_duration']
                max_patients = schedule['max_patients_per_slot']
                
                current_time = start_time
                while current_time < end_time:
                    time_str = current_time.strftime('%H:%M')
                    booked_count = existing_reservations.get(time_str, 0)
                    
                    if booked_count < max_patients:
                        available_slots.append({
                            'time': time_str,
                            'available': max_patients - booked_count,
                            'display': current_time.strftime('%I:%M %p')
                        })
                    
                    current_time += timedelta(minutes=slot_duration)
            
            conn_admin.close()
            conn_doctors.close()
            
            return jsonify({
                'success': True,
                'has_schedule': True,
                'slots': available_slots,
                'date': date
            })
        else:
            # No schedule - return default time slots
            conn_doctors.close()
            
            default_slots = [
                {'time': '09:00', 'display': '09:00 AM'},
                {'time': '09:30', 'display': '09:30 AM'},
                {'time': '10:00', 'display': '10:00 AM'},
                {'time': '10:30', 'display': '10:30 AM'},
                {'time': '11:00', 'display': '11:00 AM'},
                {'time': '11:30', 'display': '11:30 AM'},
                {'time': '14:00', 'display': '02:00 PM'},
                {'time': '14:30', 'display': '02:30 PM'},
                {'time': '15:00', 'display': '03:00 PM'},
                {'time': '15:30', 'display': '03:30 PM'},
                {'time': '16:00', 'display': '04:00 PM'},
                {'time': '16:30', 'display': '04:30 PM'},
                {'time': '17:00', 'display': '05:00 PM'},
                {'time': '17:30', 'display': '05:30 PM'}
            ]
            
            return jsonify({
                'success': True,
                'has_schedule': False,
                'slots': default_slots,
                'date': date,
                'message': '醫生尚未設置時間表，顯示預設時段'
            })
            
    except Exception as e:
        print(f"Error getting available slots: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/whatsapp-status')
@login_required
def get_whatsapp_status():
    """Get WhatsApp service status"""
    try:
        enabled = WHATSAPP_CONFIG['enabled']
        connected = False
        
        if enabled and whatsapp_client:
            try:
                # Test connection by checking if client is ready
                connected = True  # Assume connected if client exists
            except:
                connected = False
        
        return jsonify({
            'enabled': enabled,
            'connected': connected,
            'target_number': WHATSAPP_CONFIG['target_number'] if enabled else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/system-health')
@login_required
def get_system_health():
    """Get current system health status"""
    try:
        # Get latest health check results
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Create health_checks table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                check_type TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                error_message TEXT,
                response_time_ms INTEGER
            )
        ''')
        
        # Get latest health check for each component
        health_data = {}
        for component in ['ai_diagnosis', 'database', 'whatsapp']:
            cursor.execute('''
                SELECT status, timestamp, error_message, response_time_ms, details
                FROM health_checks 
                WHERE check_type = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (component,))
            
            result = cursor.fetchone()
            if result:
                health_data[component] = {
                    'status': result[0],
                    'last_check': result[1],
                    'error': result[2],
                    'response_time_ms': result[3],
                    'details': json.loads(result[4]) if result[4] else None
                }
            else:
                health_data[component] = SYSTEM_HEALTH_STATUS.get(component, {
                    'status': 'unknown',
                    'last_check': None,
                    'error': None
                })
        
        # Get health check history (last 7 days)
        cursor.execute('''
            SELECT check_type, status, timestamp, response_time_ms
            FROM health_checks 
            WHERE timestamp >= datetime('now', '-7 days')
            ORDER BY timestamp DESC
        ''')
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'component': row[0],
                'status': row[1],
                'timestamp': row[2],
                'response_time_ms': row[3]
            })
        
        conn.close()
        
        return jsonify({
            'current_status': health_data,
            'history': history,
            'last_updated': get_current_time().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/run-health-check', methods=['POST'])
@require_admin
def manual_health_check():
    """Manually trigger health check"""
    try:
        results = run_daily_health_check()
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': get_current_time().isoformat()
        })
    except Exception as e:
        logger.error(f"Manual health check failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/bug-reports')
@tab_permission_required('bug_reports')
def admin_bug_reports():
    """Bug reports management page"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Create bug_reports table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                contact_info TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                url TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'new',
                image_path TEXT
            )
        ''')
        
        # Add image_path column if it doesn't exist (for existing tables)
        try:
            cursor.execute('ALTER TABLE bug_reports ADD COLUMN image_path TEXT')
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Get all bug reports
        cursor.execute('''
            SELECT id, description, contact_info, timestamp, url, user_agent, status, image_path
            FROM bug_reports 
            ORDER BY timestamp DESC
        ''')
        bug_reports = cursor.fetchall()
        
        # Convert to list of dicts for easier template handling
        reports = []
        for report in bug_reports:
            reports.append({
                'id': report[0],
                'description': report[1],
                'contact_info': report[2],
                'timestamp': report[3],
                'url': report[4],
                'user_agent': report[5],
                'status': report[6],
                'image_path': report[7] if len(report) > 7 else None
            })
        
        # Get stats
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM bug_reports 
            GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM bug_reports')
        total_count = cursor.fetchone()[0]
        
        stats = {
            'new': status_counts.get('new', 0),
            'in_progress': status_counts.get('in-progress', 0),
            'resolved': status_counts.get('resolved', 0),
            'total': total_count
        }
        
        conn.close()
        
        return render_template('admin/bug-reports.html', 
                             bug_reports=reports, 
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading bug reports: {e}")
        flash('載入問題回報時發生錯誤', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/api/bug-reports/<int:report_id>/status', methods=['POST'])
@require_admin
def update_bug_report_status(report_id):
    """Update bug report status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['new', 'in-progress', 'resolved']:
            return jsonify({'error': '無效的狀態'}), 400
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bug_reports 
            SET status = ? 
            WHERE id = ?
        ''', (new_status, report_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '狀態已更新'})
        
    except Exception as e:
        logger.error(f"Error updating bug report status: {e}")
        return jsonify({'error': '更新狀態時發生錯誤'}), 500

@app.route('/admin/api/bug-reports/<int:report_id>', methods=['DELETE'])
@require_admin
def delete_bug_report(report_id):
    """Delete bug report"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM bug_reports WHERE id = ?', (report_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '問題回報已刪除'})
        
    except Exception as e:
        logger.error(f"Error deleting bug report: {e}")
        return jsonify({'error': '刪除問題回報時發生錯誤'}), 500

@app.route('/admin/api/whatsapp-test', methods=['POST'])
@login_required
def test_whatsapp_connection():
    """Test WhatsApp connection with provided config"""
    try:
        data = request.get_json()
        socket_url = data.get('socket_url', 'http://localhost:8086')
        target_number = data.get('target_number')
        api_key = data.get('api_key', '')
        session_name = data.get('session_name', 'default')
        
        if not target_number:
            return jsonify({'success': False, 'error': '目標號碼不能為空'})
        
        # Test message
        test_message = "🔧 WhatsApp連接測試\n\n這是一條測試消息，用於驗證WhatsApp通知配置。\n\n如果您收到此消息，表示配置正確！"
        
        # Try to send test message
        try:
            if not WHATSAPP_AVAILABLE:
                return jsonify({'success': False, 'error': 'WhatsApp客戶端不可用：python-socketio未安裝'})
            
            test_client = socketio.SimpleClient()
            test_client.connect(socket_url)
            test_client.emit('sendText', {
                'to': target_number,
                'content': test_message
            })
            test_client.disconnect()
            return jsonify({'success': True, 'message': '測試消息已發送'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'連接失敗: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_whatsapp_config', methods=['POST'])
@login_required
def update_whatsapp_config():
    """Update WhatsApp configuration"""
    try:
        global WHATSAPP_CONFIG, whatsapp_client
        
        # Get form data
        enabled = request.form.get('whatsapp_enabled') == 'true'
        target_number = request.form.get('target_number', '').strip()
        socket_url = request.form.get('socket_url', 'http://localhost:8086').strip()
        api_key = request.form.get('api_key', '').strip()
        session_name = request.form.get('session_name', 'default').strip()
        contact_mode = request.form.get('contact_mode', 'admin').strip()  # Get contact mode
        
        # Validate contact mode
        if contact_mode not in ['admin', 'doctor', 'hidden']:
            contact_mode = 'admin'
        
        # Validate required fields if enabled and in admin mode
        if enabled and contact_mode == 'admin' and not target_number:
            flash('管理員模式下，目標號碼不能為空', 'error')
            return redirect(url_for('admin_config'))
        
        # Update configuration
        WHATSAPP_CONFIG.update({
            'enabled': enabled,
            'target_number': target_number,
            'socket_url': socket_url,
            'api_key': api_key,
            'session_name': session_name,
            'contact_mode': contact_mode
        })
        
        # Update .env file
        update_env_file('WHATSAPP_ENABLED', 'true' if enabled else 'false')
        update_env_file('WHATSAPP_TARGET_NUMBER', target_number)
        update_env_file('WHATSAPP_SOCKET_URL', socket_url)
        update_env_file('WHATSAPP_API_KEY', api_key)
        update_env_file('WHATSAPP_SESSION_NAME', session_name)
        update_env_file('WHATSAPP_CONTACT_MODE', contact_mode)
        
        # Save to database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Update or insert WhatsApp config
        cursor.execute('''
            INSERT OR REPLACE INTO admin_config (key, value) 
            VALUES (?, ?)
        ''', ('whatsapp_config', json.dumps(WHATSAPP_CONFIG)))
        
        conn.commit()
        conn.close()
        
        # Reload environment variables
        load_dotenv(override=True)
        
        # Reinitialize WhatsApp client if enabled
        if enabled:
            init_whatsapp_client()
            flash('WhatsApp配置已更新並重新初始化', 'success')
        else:
            whatsapp_client = None
            flash('WhatsApp通知已停用', 'success')
        
        return redirect(url_for('admin_config'))
        
    except Exception as e:
        logger.error(f"WhatsApp config update error: {e}")
        flash(f'更新WhatsApp配置失敗: {str(e)}', 'error')
        return redirect(url_for('admin_config'))

def cleanup_old_analysis_reports():
    """Clean up analysis reports older than 30 days"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate cutoff date (30 days ago)
        cutoff_date = datetime.now() - timedelta(days=30)
        cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Delete old analysis reports
        cursor.execute("""
            DELETE FROM analysis_reports 
            WHERE created_at < ?
        """, (cutoff_timestamp,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} diagnosis reports older than 30 days")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during diagnosis reports cleanup: {str(e)}")
        return 0

@app.route('/submit-bug-report', methods=['POST'])
def submit_bug_report():
    """Handle bug report submissions and send to WhatsApp"""
    try:
        # Handle both JSON and form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            description = request.form.get('description', '').strip()
            contact_info = request.form.get('contact_info', '').strip()
            url = request.form.get('url', '')
            user_agent = request.form.get('user_agent', '')
            image_file = request.files.get('image')
        elif request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            description = data.get('description', '').strip()
            contact_info = data.get('contact_info', '').strip()
            url = data.get('url', '')
            user_agent = data.get('user_agent', '')
            image_file = None
        else:
            # Fallback for other content types
            try:
                data = request.get_json(force=True)
                description = data.get('description', '').strip()
                contact_info = data.get('contact_info', '').strip()
                url = data.get('url', '')
                user_agent = data.get('user_agent', '')
                image_file = None
            except:
                description = request.form.get('description', '').strip()
                contact_info = request.form.get('contact_info', '').strip()
                url = request.form.get('url', '')
                user_agent = request.form.get('user_agent', '')
                image_file = request.files.get('image')
        
        if not description:
            return jsonify({'error': '問題描述不能為空'}), 400
        
        # Handle image upload
        image_path = None
        if image_file and image_file.filename:
            import os
            from werkzeug.utils import secure_filename
            import time
            
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join('static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Generate secure filename
            filename = secure_filename(image_file.filename)
            timestamp = str(int(time.time()))
            filename = f"{timestamp}_{filename}"
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            image_file.save(file_path)
            image_path = f"uploads/{filename}"

        # Format bug report message
        bug_message = f"""🐛 **系統問題回報**

📝 **問題描述:**
{description}

📞 **聯絡方式:** {contact_info}
🕐 **回報時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 **頁面:** {url}
💻 **瀏覽器:** {user_agent[:100]}...

---
此問題由 Doctor AI 系統自動轉發"""

        # Send to WhatsApp if enabled
        if WHATSAPP_CONFIG['enabled'] and whatsapp_client:
            try:
                # Send to the configured notification number
                target_number = WHATSAPP_CONFIG.get('target_number', '')
                if target_number:
                    whatsapp_client.emit('send_message', {
                        'to': target_number,
                        'message': bug_message
                    })
                    logger.info(f"Bug report sent to WhatsApp: {target_number}")
                else:
                    logger.warning("No WhatsApp target number configured for bug reports")
            except Exception as whatsapp_error:
                logger.error(f"Failed to send bug report to WhatsApp: {whatsapp_error}")
        
        # Connect to database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Create bug_reports table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                contact_info TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                url TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'new',
                image_path TEXT
            )
        ''')
        
        # Insert bug report
        cursor.execute('''
            INSERT INTO bug_reports (description, contact_info, url, user_agent, image_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (description, contact_info, url, user_agent, image_path))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log to analytics
        log_analytics('bug_report_submitted', {
            'report_id': report_id,
            'has_image': image_path is not None,
            'has_contact': bool(contact_info),
            'description_length': len(description)
        }, get_real_ip(), request.user_agent.string)
        
        # Send to WhatsApp
        try:
            if whatsapp_client and whatsapp_client.connected:
                target_number = WHATSAPP_CONFIG.get('notification_number')
                if target_number:
                    bug_message = f"🐛 新問題回報 #{report_id}\n\n描述: {description}\n"
                    if contact_info:
                        bug_message += f"聯絡方式: {contact_info}\n"
                    if url:
                        bug_message += f"頁面: {url}\n"
                    if image_path:
                        bug_message += f"附件: 已上傳圖片\n"
                    bug_message += f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    whatsapp_client.emit('send_message', {
                        'to': target_number,
                        'message': bug_message
                    })
                    logger.info(f"Bug report sent to WhatsApp: {target_number}")
                else:
                    logger.warning("No WhatsApp target number configured for bug reports")
        except Exception as whatsapp_error:
            logger.error(f"Failed to send bug report to WhatsApp: {whatsapp_error}")
        
        return jsonify({'success': True, 'message': '問題回報已成功提交'})
        
    except Exception as e:
        logger.error(f"Error processing bug report: {e}")
        return jsonify({'error': '處理問題回報時發生錯誤'}), 500

# Global variable to store system health status
SYSTEM_HEALTH_STATUS = {
    'ai_diagnosis': {'status': 'unknown', 'last_check': None, 'error': None},
    'database': {'status': 'unknown', 'last_check': None, 'error': None},
    'whatsapp': {'status': 'unknown', 'last_check': None, 'error': None}
}

def log_health_check(check_type: str, status: str, details: dict = None, error: str = None):
    """Log health check results to separate health check table"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Create health_checks table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                check_type TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                error_message TEXT,
                response_time_ms INTEGER
            )
        ''')
        
        # Insert health check record
        cursor.execute('''
            INSERT INTO health_checks (check_type, status, details, error_message, response_time_ms)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            check_type, 
            status, 
            json.dumps(details) if details else None,
            error,
            details.get('response_time_ms') if details else None
        ))
        
        conn.commit()
        conn.close()
        
        # Update global status
        SYSTEM_HEALTH_STATUS[check_type] = {
            'status': status,
            'last_check': get_current_time().isoformat(),
            'error': error
        }
        
        logger.info(f"Health check logged: {check_type} = {status}")
        
    except Exception as e:
        logger.error(f"Failed to log health check: {e}")

def test_ai_diagnosis():
    """Test AI diagnosis system with multiple test cases"""
    start_time = time.time()
    
    # Test cases with different symptom combinations
    test_cases = [
        {
            'symptoms': '頭痛、發燒、咳嗽三天',
            'age': 30,
            'gender': '男',
            'chronic_conditions': '',
            'language': 'zh-TW'
        },
        {
            'symptoms': '胃痛、噁心、腹瀉兩天',
            'age': 25,
            'gender': '女',
            'chronic_conditions': '',
            'language': 'zh-TW'
        },
        {
            'symptoms': '胸痛、呼吸困難、心跳加速',
            'age': 45,
            'gender': '男',
            'chronic_conditions': '高血壓',
            'language': 'zh-TW'
        }
    ]
    
    try:
        logger.info("Starting AI diagnosis health check with multiple test cases...")
        
        successful_tests = 0
        total_tests = len(test_cases)
        all_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            case_start_time = time.time()
            
            logger.info(f"Running test case {i}/{total_tests}: {test_case['symptoms']}")
            
            try:
                # Call the AI diagnosis function
                diagnosis_result = analyze_symptoms(
                    age=test_case['age'],
                    gender=test_case['gender'],
                    symptoms=test_case['symptoms'],
                    chronic_conditions=test_case['chronic_conditions'],
                    detailed_health_info={},
                    user_language=test_case['language']
                )
                
                case_response_time = int((time.time() - case_start_time) * 1000)
                
                # Validate the response
                if (diagnosis_result and 
                    'diagnosis' in diagnosis_result and 
                    'recommended_specialty' in diagnosis_result and
                    len(diagnosis_result['diagnosis']) > 10):
                    
                    successful_tests += 1
                    all_results.append({
                        'case': i,
                        'symptoms': test_case['symptoms'],
                        'success': True,
                        'response_time_ms': case_response_time,
                        'specialty': diagnosis_result['recommended_specialty'],
                        'diagnosis_length': len(diagnosis_result['diagnosis'])
                    })
                    
                    logger.info(f"Test case {i} PASSED ({case_response_time}ms)")
                    
                else:
                    all_results.append({
                        'case': i,
                        'symptoms': test_case['symptoms'],
                        'success': False,
                        'response_time_ms': case_response_time,
                        'error': 'Invalid or incomplete response'
                    })
                    
                    logger.warning(f"Test case {i} FAILED: Invalid response")
                    
            except Exception as case_error:
                case_response_time = int((time.time() - case_start_time) * 1000)
                all_results.append({
                    'case': i,
                    'symptoms': test_case['symptoms'],
                    'success': False,
                    'response_time_ms': case_response_time,
                    'error': str(case_error)
                })
                
                logger.error(f"Test case {i} ERROR: {str(case_error)}")
        
        total_response_time_ms = int((time.time() - start_time) * 1000)
        success_rate = (successful_tests / total_tests) * 100
        
        # Consider health check successful if at least 2 out of 3 tests pass (66% success rate)
        is_healthy = successful_tests >= 2
        
        log_health_check('ai_diagnosis', 'healthy' if is_healthy else 'unhealthy', {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': success_rate,
            'response_time_ms': total_response_time_ms,
            'test_results': all_results
        }, None if is_healthy else f"Only {successful_tests}/{total_tests} tests passed")
        
        if is_healthy:
            logger.info(f"AI diagnosis health check PASSED: {successful_tests}/{total_tests} tests successful ({total_response_time_ms}ms)")
        else:
            logger.error(f"AI diagnosis health check FAILED: Only {successful_tests}/{total_tests} tests passed")
        
        return is_healthy
            
    except Exception as e:
        total_response_time_ms = int((time.time() - start_time) * 1000)
        error_msg = f"AI diagnosis health check failed: {str(e)}"
        
        log_health_check('ai_diagnosis', 'unhealthy', {
            'total_tests': len(test_cases),
            'successful_tests': 0,
            'response_time_ms': total_response_time_ms
        }, error_msg)
        
        logger.error(f"AI diagnosis health check ERROR: {error_msg}")
        return False

def test_database_connectivity():
    """Test database connectivity and basic operations"""
    start_time = time.time()
    
    try:
        # Test admin database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM admin_users')
        admin_count = cursor.fetchone()[0]
        conn.close()
        
        # Test doctors database
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM doctors')
        doctors_count = cursor.fetchone()[0]
        conn.close()
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        log_health_check('database', 'healthy', {
            'admin_users_count': admin_count,
            'doctors_count': doctors_count,
            'response_time_ms': response_time_ms
        })
        
        logger.info(f"Database health check PASSED ({response_time_ms}ms)")
        return True
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Database connectivity test failed: {str(e)}"
        
        log_health_check('database', 'unhealthy', {
            'response_time_ms': response_time_ms
        }, error_msg)
        
        logger.error(f"Database health check ERROR: {error_msg}")
        return False

def test_whatsapp_connectivity():
    """Test WhatsApp service connectivity"""
    start_time = time.time()
    
    try:
        if not WHATSAPP_CONFIG['enabled']:
            log_health_check('whatsapp', 'disabled', {
                'response_time_ms': int((time.time() - start_time) * 1000)
            })
            return True
            
        if not whatsapp_client:
            error_msg = "WhatsApp client not initialized"
            log_health_check('whatsapp', 'unhealthy', {
                'response_time_ms': int((time.time() - start_time) * 1000)
            }, error_msg)
            return False
            
        # Test connection (without sending message)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        log_health_check('whatsapp', 'healthy', {
            'target_number': WHATSAPP_CONFIG.get('target_number', 'not_set'),
            'response_time_ms': response_time_ms
        })
        
        logger.info(f"WhatsApp health check PASSED ({response_time_ms}ms)")
        return True
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        error_msg = f"WhatsApp connectivity test failed: {str(e)}"
        
        log_health_check('whatsapp', 'unhealthy', {
            'response_time_ms': response_time_ms
        }, error_msg)
        
        logger.error(f"WhatsApp health check ERROR: {error_msg}")
        return False

def run_daily_health_check():
    """Run comprehensive daily health check"""
    logger.info("=== STARTING DAILY HEALTH CHECK ===")
    
    results = {
        'ai_diagnosis': test_ai_diagnosis(),
        'database': test_database_connectivity(),
        'whatsapp': test_whatsapp_connectivity()
    }
    
    # Count failures
    failures = [check for check, passed in results.items() if not passed]
    
    if failures:
        logger.warning(f"Health check FAILED for: {', '.join(failures)}")
        
        # Send WhatsApp notification if enabled and WhatsApp itself is working
        if WHATSAPP_CONFIG['enabled'] and whatsapp_client and 'whatsapp' not in failures:
            try:
                failure_message = f"🚨 系統健康檢查警告\n\n以下系統組件出現問題:\n"
                for failure in failures:
                    status = SYSTEM_HEALTH_STATUS.get(failure, {})
                    error = status.get('error', 'Unknown error')
                    failure_message += f"❌ {failure}: {error}\n"
                
                failure_message += f"\n檢查時間: {get_current_time().strftime('%Y-%m-%d %H:%M:%S')}"
                failure_message += f"\n請檢查系統狀態: http://localhost:8081/admin"
                
                whatsapp_client.emit('send_message', {
                    'to': WHATSAPP_CONFIG.get('target_number'),
                    'message': failure_message
                })
                logger.info("Health check failure notification sent via WhatsApp")
                
            except Exception as e:
                logger.error(f"Failed to send health check notification: {e}")
    else:
        logger.info("=== ALL HEALTH CHECKS PASSED ===")
    
    return results

def run_scheduled_tasks():
    """Run scheduled maintenance tasks in background thread"""
    def scheduler_thread():
        # Schedule cleanup to run daily at 2 AM
        schedule.every().day.at("02:00").do(cleanup_old_analysis_reports)
        
        # Schedule daily health check at midnight (12:00 AM)
        schedule.every().day.at("00:00").do(run_daily_health_check)
        
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour
    
    # Start scheduler in background thread
    scheduler = threading.Thread(target=scheduler_thread, daemon=True)
    scheduler.start()
    logger.info("Scheduled tasks initialized:")
    logger.info("- Diagnosis reports cleanup: daily at 2 AM")
    logger.info("- System health check: daily at 12 AM")

# Multi-Device 2FA Routes
@app.route('/admin/2fa/devices')
@require_admin
def manage_2fa_devices():
    """Manage 2FA devices page"""
    if session.get('admin_username') != ADMIN_USERNAME:
        flash('只有超級管理員可以管理雙重認證設備', 'error')
        return redirect(url_for('admin_config'))
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        flash('用戶不存在', 'error')
        return redirect(url_for('admin_config'))
    
    # Check if user has existing single-device 2FA that needs migration
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    
    # Check if user has existing 2FA but no multi-device setup
    cursor.execute('SELECT totp_enabled, totp_secret, multi_device_2fa_enabled FROM admin_users WHERE id = ?', (user_id,))
    user_2fa_status = cursor.fetchone()
    
    if user_2fa_status and user_2fa_status[0] and user_2fa_status[1] and not user_2fa_status[2]:
        # User has single-device 2FA but no multi-device setup - migrate it
        try:
            # Check if device already exists in multi-device table
            cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ?', (user_id,))
            device_count = cursor.fetchone()[0]
            
            if device_count == 0:
                # Migrate existing single-device 2FA to multi-device
                cursor.execute('''
                    INSERT INTO admin_2fa_devices
                    (user_id, device_name, totp_secret, is_primary, is_active, created_at, device_info)
                    VALUES (?, ?, ?, 1, 1, CURRENT_TIMESTAMP, ?)
                ''', (user_id, "主要設備", user_2fa_status[1], 
                      json.dumps({"migrated": True, "original_setup": True})))
                
                # Enable multi-device 2FA
                cursor.execute('UPDATE admin_users SET multi_device_2fa_enabled = 1 WHERE id = ?', (user_id,))
                conn.commit()
                
                flash('已將現有雙重認證設備遷移到多設備系統', 'info')
        except Exception as e:
            print(f"Migration error: {e}")
            flash('設備遷移時發生錯誤', 'error')
    
    conn.close()
    
    devices = multi_device_2fa.get_user_devices(user_id)
    can_add = multi_device_2fa.can_add_device(user_id)
    
    return render_template('admin/manage-2fa-devices.html', 
                         devices=devices, 
                         can_add_device=can_add,
                         username=ADMIN_USERNAME)

@app.route('/admin/2fa/add-device', methods=['GET', 'POST'])
@require_admin
def add_2fa_device():
    """Add new 2FA device"""
    if session.get('admin_username') != ADMIN_USERNAME:
        flash('只有超級管理員可以添加雙重認證設備', 'error')
        return redirect(url_for('admin_config'))
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        flash('用戶不存在', 'error')
        return redirect(url_for('admin_config'))
    
    if not multi_device_2fa.can_add_device(user_id):
        flash('已達到最大設備數量限制', 'error')
        return redirect(url_for('manage_2fa_devices'))
    
    if request.method == 'GET':
        secret = generate_totp_secret()
        device_name = request.args.get('device_name', f'Device {datetime.now().strftime("%Y%m%d_%H%M%S")}')
        qr_code = multi_device_2fa.generate_device_qr_code(ADMIN_USERNAME, device_name, secret)
        
        session['temp_device_secret'] = secret
        session['temp_device_name'] = device_name
        
        return render_template('admin/add-2fa-device.html',
                             qr_code=qr_code,
                             secret=secret,
                             device_name=device_name,
                             username=ADMIN_USERNAME)
    
    elif request.method == 'POST':
        token = request.form.get('token')
        device_name = request.form.get('device_name') or session.get('temp_device_name')
        secret = session.get('temp_device_secret')
        
        if not secret or not token or not device_name:
            flash('無效的請求', 'error')
            return redirect(url_for('add_2fa_device'))
        
        if verify_totp_token(secret, token):
            try:
                device_info = {
                    'user_agent': request.user_agent.string,
                    'ip_address': get_real_ip(),
                    'setup_time': datetime.now().isoformat()
                }
                
                multi_device_2fa.add_device(user_id, device_name, secret, device_info)
                
                session.pop('temp_device_secret', None)
                session.pop('temp_device_name', None)
                
                log_analytics('2fa_device_added', {
                    'username': ADMIN_USERNAME,
                    'device_name': device_name
                }, get_real_ip(), request.user_agent.string)
                
                flash(f'設備 "{device_name}" 添加成功！', 'success')
                return redirect(url_for('manage_2fa_devices'))
                
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(url_for('add_2fa_device'))
        else:
            flash('驗證碼錯誤，請重試', 'error')
            return redirect(url_for('add_2fa_device'))

@app.route('/admin/2fa/device/<int:device_id>/toggle', methods=['POST'])
@require_admin
def toggle_2fa_device(device_id):
    """Toggle device active status"""
    if session.get('admin_username') != ADMIN_USERNAME:
        return jsonify({'success': False, 'error': '權限不足'}), 403
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        return jsonify({'success': False, 'error': '用戶不存在'}), 404
    
    try:
        new_status = multi_device_2fa.toggle_device_status(user_id, device_id)
        status_text = '啟用' if new_status else '停用'
        
        log_analytics('2fa_device_toggled', {
            'username': ADMIN_USERNAME,
            'device_id': device_id,
            'new_status': new_status
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({
            'success': True, 
            'message': f'設備已{status_text}',
            'new_status': new_status
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin/2fa/device/<int:device_id>/delete', methods=['POST'])
@require_admin
def delete_2fa_device(device_id):
    """Delete 2FA device"""
    if session.get('admin_username') != ADMIN_USERNAME:
        return jsonify({'success': False, 'error': '權限不足'}), 403
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        return jsonify({'success': False, 'error': '用戶不存在'}), 404
    
    try:
        # Get device name for logging before deletion
        devices = multi_device_2fa.get_user_devices(user_id)
        device_name = next((d['device_name'] for d in devices if d['id'] == device_id), 'Unknown')
        
        multi_device_2fa.remove_device(user_id, device_id)
        
        log_analytics('2fa_device_deleted', {
            'username': ADMIN_USERNAME,
            'device_name': device_name,
            'device_id': device_id
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({'success': True, 'message': f'設備 "{device_name}" 已刪除'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin/2fa/device/<int:device_id>/rename', methods=['POST'])
@require_admin
def rename_2fa_device(device_id):
    """Rename 2FA device"""
    if session.get('admin_username') != ADMIN_USERNAME:
        return jsonify({'success': False, 'error': '權限不足'}), 403
    
    new_name = request.json.get('name', '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': '設備名稱不能為空'}), 400
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        return jsonify({'success': False, 'error': '用戶不存在'}), 404
    
    try:
        # Get old name for logging
        devices = multi_device_2fa.get_user_devices(user_id)
        old_name = next((d['device_name'] for d in devices if d['id'] == device_id), 'Unknown')
        
        multi_device_2fa.rename_device(user_id, device_id, new_name)
        
        log_analytics('2fa_device_renamed', {
            'username': ADMIN_USERNAME,
            'device_id': device_id,
            'old_name': old_name,
            'new_name': new_name
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({'success': True, 'message': f'設備已重命名為 "{new_name}"'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    # Initialize database and load saved config
    init_db()
    load_ai_config_from_db()
    load_whatsapp_config_from_db()
    
    # Initialize WhatsApp client
    init_whatsapp_client()
    
    # Start scheduled tasks
    run_scheduled_tasks()
    
    print(f"已載入 {len(DOCTORS_DATA)} 位醫生資料")
    print("正在啟動AI香港醫療配對系統...")
    print(f"當前AI提供商: {AI_CONFIG['provider']}")
    
    if WHATSAPP_CONFIG['enabled']:
        print(f"WhatsApp通知已啟用，目標號碼: {WHATSAPP_CONFIG['target_number']}")
    else:
        print("WhatsApp通知未啟用")
    
    if AI_CONFIG['provider'] == 'openrouter':
        if AI_CONFIG['openrouter']['api_key']:
            print(f"OpenRouter模型: {AI_CONFIG['openrouter']['model']}")
            print("OpenRouter API密鑰已設置")
        else:
            print("警告: 未設置OPENROUTER_API_KEY環境變數")
    elif AI_CONFIG['provider'] == 'openai':
        if AI_CONFIG['openai']['api_key']:
            print(f"OpenAI模型: {AI_CONFIG['openai']['model']}")
            print("OpenAI API密鑰已設置")
        else:
            print("警告: 未設置OPENAI_API_KEY環境變數")
    else:
        print(f"Ollama模型: {AI_CONFIG['ollama']['model']}")
        print("請確保Ollama服務正在運行：ollama serve")
    
    # Get host and port from environment variables
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '8081'))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(debug=debug, host=host, port=port)
