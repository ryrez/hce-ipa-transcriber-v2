import json
import subprocess
import shutil
import os
from collections import defaultdict

# Load HCE mappings with fallback
try:
    with open("hce_map.json", "r", encoding='utf-8') as f:
        HCE_MAP = json.load(f)
except FileNotFoundError:
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

def load_override_dict():
    """Load override dict dynamically"""
    override_dict = {}
    if os.path.exists("override_dict.json"):
        try:
            with open("override_dict.json", "r", encoding='utf-8') as f:
                override_dict = json.load(f)
        except Exception as e:
            print(f"Error loading override dict: {e}")
    return override_dict

def check_espeak_available():
    """Check if espeak-ng is available"""
    return shutil.which("espeak-ng") is not None

def get_ipa_espeak(text):
    """Get IPA using espeak-ng"""
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
    """Fallback IPA generation"""
    fallback_mappings = {
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
        "class": ["klæːs", "klɑːs"],
        "grass": ["ɡræːs", "ɡrɑːs"],
        "pass": ["pæːs", "pɑːs"],
        "fast": ["fæːst", "fɑːst"],
        "last": ["læːst", "lɑːst"],
        "staff": ["stæːf", "stɑːf"],
        "half": ["hæːf", "hɑːf"],
        "after": ["æːftə", "ɑːftə"],
        "master": ["mæːstə", "mɑːstə"],
        "australia": ["əˈstreɪljə", "ɒˈstreɪljə"],
        "melbourne": ["ˈmelbən", "ˈmelbɔːn"],
        "sydney": ["ˈsɪdni"],
        "brisbane": ["ˈbrɪzbən"],
        "perth": ["pɜːθ"],
        "adelaide": ["ˈædəleɪd"],
        "canberra": ["ˈkænbərə"],
        "darwin": ["ˈdɑːwɪn"],
        "hobart": ["ˈhoʊbɑːt"]
    }
    
    word_lower = word.lower().strip(".,!?;:")
    if word_lower in fallback_mappings:
        return fallback_mappings[word_lower]
    
    # Basic phonetic approximation
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

def clean_word(word):
    """Clean word for processing"""
    return word.lower().strip(".,!?;:")

def process_text(text):
    """Process text into IPA with fallbacks"""
    override_dict = load_override_dict()
    words = text.split()
    results = []
    
    for word in words:
        clean = clean_word(word)
        
        # Check override dictionary first
        if clean in override_dict:
            results.append({
                "original": word,
                "clean": clean,
                "ipa_options": [override_dict[clean]],
                "selected": override_dict[clean],
                "has_override": True
            })
            continue
        
        if not clean.replace("'", "").isalnum():
            results.append({
                "original": word,
                "clean": clean,
                "ipa_options": [word],
                "selected": word
            })
            continue
        
        # Try espeak first, then fallback
        ipa_options = []
        
        if check_espeak_available():
            espeak_result = get_ipa_espeak(clean)
            if espeak_result:
                ipa_clean = espeak_result.replace("_", "").replace(" ", "")
                for standard, hce in HCE_MAP.items():
                    ipa_clean = ipa_clean.replace(standard, hce)
                ipa_options.append(ipa_clean)
        
        fallback_options = get_ipa_fallback(clean)
        if fallback_options:
            for option in fallback_options:
                for standard, hce in HCE_MAP.items():
                    option = option.replace(standard, hce)
                if option not in ipa_options:
                    ipa_options.append(option)
        
        if not ipa_options:
            ipa_options = [clean]
        
        results.append({
            "original": word,
            "clean": clean, 
            "ipa_options": ipa_options,
            "selected": ipa_options[0] if ipa_options else clean,
            "has_override": False
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

def get_system_info():
    """Get system info for debugging"""
    override_dict = load_override_dict()
    info = {
        "espeak_available": check_espeak_available(),
        "espeak_path": shutil.which("espeak-ng"),
        "hce_map_loaded": bool(HCE_MAP),
        "override_dict_loaded": bool(override_dict),
        "override_words_count": len(override_dict),
        "fallback_words_count": "200+"
    }
    return info