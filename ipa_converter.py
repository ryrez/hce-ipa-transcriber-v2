import json
import subprocess
import shutil
import os

# Load HCE mappings with fallback
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

def load_override_dict():
    """Load override dict dynamically (called each time we need it)"""
    override_dict = {}
    if os.path.exists("override_dict.json"):
        try:
            with open("override_dict.json", "r", encoding='utf-8') as f:
                override_dict = json.load(f)
                print(f"DEBUG: Loaded {len(override_dict)} words from override_dict.json")
                print(f"DEBUG: Override dict contents: {override_dict}")
        except Exception as e:
            print(f"DEBUG: Failed to load override dict: {e}")
            pass
    else:
        print("DEBUG: override_dict.json not found")
    return override_dict

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
    """Fallback IPA generation using predefined mappings"""
    # Comprehensive Australian English word mappings
    fallback_mappings = {
        # HCE words - trap/bath split
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
        
        # Common Australian words
        "australia": ["əˈstreɪljə", "ɒˈstreɪljə"],
        "melbourne": ["ˈmelbən", "ˈmelbɔːn"],
        "sydney": ["ˈsɪdni"],
        "brisbane": ["ˈbrɪzbən"],
        "perth": ["pɜːθ"],
        "adelaide": ["ˈædəleɪd"],
        "canberra": ["ˈkænbərə"],
        "darwin": ["ˈdɑːwɪn"],
        "hobart": ["ˈhoʊbɑːt"],
        
        # Common words
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
        "blue": ["bluː"],
        "true": ["truː"],
        "good": ["ɡʊd"],
        "book": ["bʊk"],
        "look": ["lʊk"],
        "could": ["kʊd"],
        "would": ["wʊd"],
        "should": ["ʃʊd"],
        "cat": ["kæt"],
        "hat": ["hæt"],
        "man": ["mæn"],
        "can": ["kæn"],
        "dog": ["dɒɡ"],
        "hot": ["hɒt"],
        "not": ["nɒt"],
        "but": ["bʌt"],
        "run": ["rʌn"],
        "sun": ["sʌn"],
        "sit": ["sɪt"],
        "big": ["bɪɡ"],
        "this": ["ðɪs"],
        "get": ["ɡet"],
        "red": ["red"],
        "the": ["ðə", "ði"],
        "a": ["ə", "eɪ"],
        "and": ["ənd", "ænd"],
        "is": ["ɪz"],
        "are": ["ɑː", "ə"],
        "was": ["wɒz", "wəz"],
        "were": ["wɜː", "wə"],
        "have": ["hæv", "həv"],
        "has": ["hæz", "həz"],
        "had": ["hæd", "həd"],
        "will": ["wɪl"],
        "one": ["wʌn"],
        "two": ["tuː"],
        "three": ["θriː"],
        "four": ["fɔː"],
        "five": ["faɪv"]
    }
    
    word_lower = word.lower().strip(".,!?;:")
    if word_lower in fallback_mappings:
        return fallback_mappings[word_lower]
    
    # Basic phonetic approximation for unknown words
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
    cleaned = word.lower().strip(".,!?;:")
    print(f"DEBUG: clean_word({word}) -> {cleaned}")
    return cleaned

def process_text(text):
    """Process text into IPA with cloud-friendly fallbacks"""
    print(f"DEBUG: process_text called with: '{text}'")
    
    # IMPORTANT: Load override dict fresh each time
    override_dict = load_override_dict()
    
    words = text.split()
    results = []
    
    for word in words:
        clean = clean_word(word)
        print(f"DEBUG: Processing word '{word}' -> clean: '{clean}'")
        
        # Check override dictionary first (now freshly loaded)
        if clean in override_dict:
            print(f"DEBUG: Found '{clean}' in override dict with IPA: '{override_dict[clean]}'")
            results.append({
                "original": word,
                "clean": clean,
                "ipa_options": [override_dict[clean]],
                "selected": override_dict[clean],
                "has_override": True
            })
            continue
        else:
            print(f"DEBUG: '{clean}' NOT found in override dict")
        
        if not clean.replace("'", "").isalnum():
            # Non-word elements (punctuation, etc.)
            print(f"DEBUG: '{clean}' is not alphanumeric, treating as punctuation")
            results.append({
                "original": word,
                "clean": clean,
                "ipa_options": [word],
                "selected": word
            })
            continue
        
        # Try espeak first (if available), otherwise use fallback
        ipa_options = []
        
        if check_espeak_available():
            espeak_result = get_ipa_espeak(clean)
            if espeak_result:
                # Process espeak result
                ipa_clean = espeak_result.replace("_", "").replace(" ", "")
                # Apply HCE mappings
                for standard, hce in HCE_MAP.items():
                    ipa_clean = ipa_clean.replace(standard, hce)
                ipa_options.append(ipa_clean)
                print(f"DEBUG: espeak result for '{clean}': {ipa_clean}")
        
        # Add fallback options (always available)
        fallback_options = get_ipa_fallback(clean)
        if fallback_options:
            for option in fallback_options:
                # Apply HCE mappings to fallback too
                for standard, hce in HCE_MAP.items():
                    option = option.replace(standard, hce)
                if option not in ipa_options:
                    ipa_options.append(option)
            print(f"DEBUG: fallback options for '{clean}': {fallback_options}")
        
        # Ensure we always have at least one option
        if not ipa_options:
            ipa_options = [clean]  # Last resort: use the original word
            print(f"DEBUG: No options found for '{clean}', using original word")
        
        print(f"DEBUG: Final IPA options for '{clean}': {ipa_options}")
        
        results.append({
            "original": word,
            "clean": clean, 
            "ipa_options": ipa_options,
            "selected": ipa_options[0] if ipa_options else clean,
            "has_override": False
        })
    
    print(f"DEBUG: Final results: {results}")
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
    """Get system info for debugging deployment issues"""
    override_dict = load_override_dict()  # Load fresh for accurate count
    info = {
        "espeak_available": check_espeak_available(),
        "espeak_path": shutil.which("espeak-ng"),
        "hce_map_loaded": bool(HCE_MAP),
        "override_dict_loaded": bool(override_dict),
        "override_words_count": len(override_dict),
        "fallback_words_count": "200+"
    }
    return info