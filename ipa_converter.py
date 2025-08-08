# Add this fallback system to your ipa_converter.py

import json
import subprocess
import shutil
import os

# Load HCE mappings
try:
    with open("hce_map.json", "r", encoding='utf-8') as f:
        HCE_MAP = json.load(f)
except FileNotFoundError:
    # Fallback HCE mappings if file not found
    HCE_MAP = {
        "ɪə": "ɪə̯",
        "ʊə": "ʊə̯", 
        "eə": "eə̯",
        "æ": "æː",
        "ʉ": "ʉː",
        "ɜː": "ɜː",
        "ə": "əː",
        "əʉ": "əʊ",
        "æɪ": "æɪ",
        "ɑe": "ɑɪ",
        "ɑ": "ɑː",
        "oː": "oː",
        "iː": "iː",
        "uː": "uː",
        "ɔː": "oː",
        "ɛ": "e",
        "ɔ": "ɔ"
    }

def check_espeak_available():
    """Check if espeak-ng is available"""
    return shutil.which("espeak-ng") is not None

def get_ipa_espeak(text):
    """Get IPA using espeak-ng (if available)"""
    if not check_espeak_available():
        return None
    
    try:
        result = subprocess.run([
            "espeak-ng", "-q", "-v", "en-au", "--ipa", text
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def get_ipa_fallback(word):
    """Fallback IPA generation using basic rules"""
    # This is a simplified fallback for common Australian English patterns
    fallback_mappings = {
        # Common Australian English words with known IPA
        "dance": ["dæːns", "dɑːns"],
        "cant": ["kæːnt", "kɑːnt"], 
        "can't": ["kæːnt", "kɑːnt"],
        "castle": ["kæːsəl", "kɑːsəl"],
        "bath": ["bæːθ", "bɑːθ"],
        "path": ["pæːθ", "pɑːθ"],
        "laugh": ["læːf", "lɑːf"],
        "ask": ["æːsk", "ɑːsk"],
        "answer": ["æːnsə", "ɑːnsə"],
        "plant": ["plæːnt", "plɑːnt"],
        "example": ["ɪɡzæːmpəl", "ɪɡzɑːmpəl"],
        "chance": ["tʃæːns", "tʃɑːns"],
        "australia": ["əˈstreɪljə", "ɒˈstreɪljə"],
        "about": ["əˈbaʊt"],
        "house": ["haʊs"],
        "time": ["taɪm"],
        "day": ["deɪ"],
        "way": ["weɪ"],
        "go": ["ɡəʊ", "ɡoː"],
        "no": ["nəʊ", "noː"],
        "know": ["nəʊ", "noː"],
        "make": ["meɪk"],
        "take": ["teɪk"],
        "see": ["siː"],
        "be": ["biː"],
        "me": ["miː"],
        "he": ["hiː"],
        "she": ["ʃiː"],
        "we": ["wiː"],
        "you": ["juː"],
        "do": ["duː"],
        "to": ["tuː", "tə"],
        "too": ["tuː"],
        "new": ["njuː", "nuː"],
        "view": ["vjuː"],
        "few": ["fjuː"],
        "blue": ["bluː"],
        "true": ["truː"],
        "school": ["skuːl"],
        "cool": ["kuːl"],
        "food": ["fuːd"],
        "good": ["ɡʊd"],
        "book": ["bʊk"],
        "look": ["lʊk"],
        "took": ["tʊk"],
        "put": ["pʊt"],
        "could": ["kʊd"],
        "would": ["wʊd"],
        "should": ["ʃʊd"]
    }
    
    word_lower = word.lower().strip(".,!?;:")
    if word_lower in fallback_mappings:
        return fallback_mappings[word_lower]
    
    # Basic phonetic approximation for unknown words
    # This is very simplified but provides something for deployment
    basic_ipa = word_lower
    basic_ipa = basic_ipa.replace("th", "θ")
    basic_ipa = basic_ipa.replace("sh", "ʃ") 
    basic_ipa = basic_ipa.replace("ch", "tʃ")
    basic_ipa = basic_ipa.replace("ng", "ŋ")
    basic_ipa = basic_ipa.replace("oo", "uː")
    basic_ipa = basic_ipa.replace("ee", "iː")
    basic_ipa = basic_ipa.replace("ay", "eɪ")
    basic_ipa = basic_ipa.replace("ow", "aʊ")
    
    return [basic_ipa]

def process_text(text):
    """Process text into IPA with cloud-friendly fallbacks"""
    words = text.split()
    results = []
    
    for word in words:
        clean = word.lower().strip(".,!?;:")
        
        if not clean.replace("'", "").isalnum():
            # Non-word elements (punctuation, etc.)
            results.append({
                "original": word,
                "clean": clean,
                "ipa_options": [word],
                "selected": word
            })
            continue
        
        # Try espeak first (if available)
        ipa_options = []
        espeak_result = get_ipa_espeak(clean)
        
        if espeak_result:
            # Process espeak result
            ipa_clean = espeak_result.replace("_", "").replace(" ", "")
            # Apply HCE mappings
            for standard, hce in HCE_MAP.items():
                ipa_clean = ipa_clean.replace(standard, hce)
            ipa_options.append(ipa_clean)
        
        # Add fallback options
        fallback_options = get_ipa_fallback(clean)
        if fallback_options:
            for option in fallback_options:
                # Apply HCE mappings to fallback too
                for standard, hce in HCE_MAP.items():
                    option = option.replace(standard, hce)
                if option not in ipa_options:
                    ipa_options.append(option)
        
        # Ensure we always have at least one option
        if not ipa_options:
            ipa_options = [clean]  # Last resort: use the original word
        
        results.append({
            "original": word,
            "clean": clean, 
            "ipa_options": ipa_options,
            "selected": ipa_options[0] if ipa_options else clean
        })
    
    return results

def reconstruct_sentence(word_results):
    """Reconstruct the full sentence IPA"""
    ipa_parts = []
    for word_result in word_results:
        if word_result.get('correction'):
            ipa_parts.append(word_result['correction'])
        elif word_result.get('selected'):
            ipa_parts.append(word_result['selected'])
        else:
            ipa_parts.append(word_result.get('ipa_options', [''])[0])
    return ' '.join(ipa_parts)

def clean_word(word):
    """Clean word for processing"""
    return word.lower().strip(".,!?;:")

# Show system info for debugging
def get_system_info():
    """Get system info for debugging deployment issues"""
    info = {
        "espeak_available": check_espeak_available(),
        "espeak_path": shutil.which("espeak-ng"),
        "hce_map_loaded": bool(HCE_MAP),
        "fallback_words": len(get_ipa_fallback.__defaults__[0] if hasattr(get_ipa_fallback, '__defaults__') else {})
    }
    return info