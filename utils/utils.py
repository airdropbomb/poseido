import random
import time
import requests
from io import BytesIO
from gtts import gTTS
from gtts.lang import tts_langs
from .logger import log_warn, log_error

# Map Poseidon language codes to gTTS valid codes
LANGUAGE_MAP = {
    "en": "en",       # English
    "es": "es",       # Spanish
    "fr": "fr",       # French
    "de": "de",       # German
    "ko": "ko",       # Korean
    "ja": "ja",       # Japanese
    "zh": "zh-CN",    # Chinese (Simplified)
    "mr": "hi",       # Marathi -> fallback to Hindi
    "ur": "hi",       # Urdu -> fallback to Hindi
    "ar": "ar",       # Arabic
    "id": "id",       # Indonesian
    "vi": "vi",       # Vietnamese
    "tr": "tr",       # Turkish
    "ru": "ru",       # Russian
    "pt": "pt",       # Portuguese
    "hi": "hi"        # Hindi
}

def generate_audio_buffer(text, lang):
    # Map to gTTS supported code
    gtts_lang = LANGUAGE_MAP.get(lang, "en")
    
    # Ensure the language is supported by gTTS
    if gtts_lang not in tts_langs().keys():
        log_warn(f"Language '{lang}' not supported, falling back to English")
        gtts_lang = "en"

    mp3_fp = BytesIO()
    tts = gTTS(text=text, lang=gtts_lang)
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp.read()

def get_random_ua(uas):
    return random.choice(uas)

def request_with_retry(method, url, token=None, data=None, headers=None, retries=5, timeout=60):
    for i in range(retries):
        try:
            hdr = headers or {}
            if token:
                hdr['Authorization'] = f'Bearer {token}'
            hdr['Accept'] = 'application/json'
            hdr['Content-Type'] = 'application/json'
            if method.lower() == 'get':
                r = requests.get(url, headers=hdr, timeout=timeout)
            else:
                r = requests.post(url, json=data, headers=hdr, timeout=timeout)
            if r.status_code in [200, 201]:
                return r.json()
            elif r.status_code == 401:
                log_error(f"Unauthorized (401) on {url}, response: {r.text} [ERR]")
                return None
            elif r.status_code == 429:
                retry_after = r.headers.get('Retry-After')
                if retry_after:
                    try:
                        wait_time = int(retry_after)
                    except ValueError:
                        wait_time = 60  # Default to 60 seconds if Retry-After is not an integer
                else:
                    wait_time = 60 * (2 ** i)  # Exponential backoff: 60, 120, 240, 480, 960 seconds
                log_warn(f"Rate limit hit (429) on {url}, waiting {wait_time} seconds, attempt {i+1} ⚠️")
                time.sleep(wait_time)
            else:
                log_warn(f"Status {r.status_code} on {url}, response: {r.text}, attempt {i+1} ⚠️")
        except Exception as e:
            log_warn(f"Request error {e} on {url}, attempt {i+1} ⚠️")
        time.sleep(5 * (i+1))  # Increased fallback delay for non-429 errors
    return None