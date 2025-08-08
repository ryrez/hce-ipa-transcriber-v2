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

# Load override dict if exists
OVERRIDE_DICT = {}
if os.path.exists("override_dict.json"):
    try:
        with open("override_dict.json", "r", encoding='utf-8') as f:
            OVERRIDE_DICT = json.load(f)
    except:
        pass

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
        
        # Diphthongs and vowels
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
        "here": ["hɪə"],
        "there": ["ðeə"],
        "where": ["weə"],
        "care": ["keə"],
        "hair": ["heə"],
        "near": ["nɪə"],
        "beer": ["bɪə"],
        "year": ["jɪə"],
        "poor": ["pʊə"],
        "sure": ["ʃʊə"],
        "tour": ["tʊə"],
        
        # Monophthongs
        "see": ["siː"],
        "be": ["biː"],
        "me": ["miː"],
        "he": ["hiː"],
        "she": ["ʃiː"],
        "we": ["wiː"],
        "tree": ["triː"],
        "free": ["friː"],
        "green": ["ɡriːn"],
        "meet": ["miːt"],
        "feet": ["fiːt"],
        "seat": ["siːt"],
        "heat": ["hiːt"],
        "beat": ["biːt"],
        
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
        "mood": ["muːd"],
        "boot": ["buːt"],
        "root": ["ruːt"],
        
        "good": ["ɡʊd"],
        "book": ["bʊk"],
        "look": ["lʊk"],
        "took": ["tʊk"],
        "put": ["pʊt"],
        "could": ["kʊd"],
        "would": ["wʊd"],
        "should": ["ʃʊd"],
        "pull": ["pʊl"],
        "full": ["fʊl"],
        "push": ["pʊʃ"],
        
        "bird": ["bɜːd"],
        "word": ["wɜːd"],
        "first": ["fɜːst"],
        "work": ["wɜːk"],
        "turn": ["tɜːn"],
        "burn": ["bɜːn"],
        "learn": ["lɜːn"],
        "heard": ["hɜːd"],
        "early": ["ɜːli"],
        "earth": ["ɜːθ"],
        
        "car": ["kɑː"],
        "far": ["fɑː"],
        "start": ["stɑːt"],
        "heart": ["hɑːt"],
        "part": ["pɑːt"],
        "dark": ["dɑːk"],
        "park": ["pɑːk"],
        "mark": ["mɑːk"],
        "hard": ["hɑːd"],
        "card": ["kɑːd"],
        
        "all": ["ɔːl"],
        "call": ["kɔːl"],
        "fall": ["fɔːl"],
        "wall": ["wɔːl"],
        "small": ["smɔːl"],
        "talk": ["tɔːk"],
        "walk": ["wɔːk"],
        "thought": ["θɔːt"],
        "caught": ["kɔːt"],
        "taught": ["tɔːt"],
        
        # Short vowels
        "cat": ["kæt"],
        "hat": ["hæt"],
        "man": ["mæn"],
        "hand": ["hænd"],
        "land": ["lænd"],
        "stand": ["stænd"],
        "sand": ["sænd"],
        "plan": ["plæn"],
        "ran": ["ræn"],
        "can": ["kæn"],
        
        "dog": ["dɒɡ"],
        "hot": ["hɒt"],
        "not": ["nɒt"],
        "got": ["ɡɒt"],
        "lot": ["lɒt"],
        "top": ["tɒp"],
        "stop": ["stɒp"],
        "shop": ["ʃɒp"],
        "rock": ["rɒk"],
        "clock": ["klɒk"],
        
        "but": ["bʌt"],
        "cut": ["kʌt"],
        "run": ["rʌn"],
        "sun": ["sʌn"],
        "fun": ["fʌn"],
        "come": ["kʌm"],
        "some": ["sʌm"],
        "love": ["lʌv"],
        "above": ["əˈbʌv"],
        "money": ["ˈmʌni"],
        
        "sit": ["sɪt"],
        "hit": ["hɪt"],
        "big": ["bɪɡ"],
        "this": ["ðɪs"],
        "with": ["wɪð"],
        "will": ["wɪl"],
        "fish": ["fɪʃ"],
        "ship": ["ʃɪp"],
        "rich": ["rɪtʃ"],
        "which": ["wɪtʃ"],
        
        "get": ["ɡet"],
        "bed": ["bed"],
        "red": ["red"],
        "head": ["hed"],
        "said": ["sed"],
        "bread": ["bred"],
        "dead": ["ded"],
        "read": ["red"],
        "left": ["left"],
        "next": ["nekst"],
        
        # Common function words
        "the": ["ðə", "ði"],
        "a": ["ə", "eɪ"],
        "an": ["ən", "æn"],
        "and": ["ənd", "ænd"],
        "or": ["ɔː", "ə"],
        "but": ["bʌt", "bət"],
        "if": ["ɪf"],
        "when": ["wen"],
        "what": ["wɒt"],
        "who": ["huː"],
        "why": ["waɪ"],
        "how": ["haʊ"],
        "where": ["weə"],
        "which": ["wɪtʃ"],
        "that": ["ðæt", "ðət"],
        "this": ["ðɪs"],
        "these": ["ðiːz"],
        "those": ["ðəʊz"],
        "they": ["ðeɪ"],
        "them": ["ðem", "ðəm"],
        "their": ["ðeə"],
        "there": ["ðeə"],
        "then": ["ðen"],
        "than": ["ðæn"],
        "is": ["ɪz"],
        "are": ["ɑː", "ə"],
        "was": ["wɒz", "wəz"],
        "were": ["wɜː", "wə"],
        "been": ["biːn"],
        "have": ["hæv", "həv"],
        "has": ["hæz", "həz"],
        "had": ["hæd", "həd"],
        "will": ["wɪl"],
        "would": ["wʊd"],
        "shall": ["ʃæl"],
        "should": ["ʃʊd"],
        "can": ["kæn", "kən"],
        "could": ["kʊd"],
        "may": ["meɪ"],
        "might": ["maɪt"],
        "must": ["mʌst"],
        "need": ["niːd"],
        "want": ["wɒnt"],
        "like": ["laɪk"],
        "know": ["nəʊ"],
        "think": ["θɪŋk"],
        "say": ["seɪ"],
        "tell": ["tel"],
        "give": ["ɡɪv"],
        "get": ["ɡet"],
        "make": ["meɪk"],
        "take": ["teɪk"],
        "come": ["kʌm"],
        "go": ["ɡəʊ"],
        "see": ["siː"],
        "look": ["lʊk"],
        "use": ["juːz"],
        "find": ["faɪnd"],
        "work": ["wɜːk"],
        "call": ["kɔːl"],
        "try": ["traɪ"],
        "ask": ["ɑːsk"],
        "seem": ["siːm"],
        "feel": ["fiːl"],
        "leave": ["liːv"],
        "put": ["pʊt"],
        
        # Numbers
        "one": ["wʌn"],
        "two": ["tuː"],
        "three": ["θriː"],
        "four": ["fɔː"],
        "five": ["faɪv"],
        "six": ["sɪks"],
        "seven": ["sevən"],
        "eight": ["eɪt"],
        "nine": ["naɪn"],
        "ten": ["ten"],
        "eleven": ["ɪlevən"],
        "twelve": ["twelv"],
        "thirteen": ["θɜːtiːn"],
        "fourteen": ["fɔːtiːn"],
        "fifteen": ["fɪftiːn"],
        "sixteen": ["sɪkstiːn"],
        "seventeen": ["sevəntiːn"],
        "eighteen": ["eɪtiːn"],
        "nineteen": ["naɪntiːn"],
        "twenty": ["twenti"],
        "thirty": ["θɜːti"],
        "forty": ["fɔːti"],
        "fifty": ["fɪfti"],
        "sixty": ["sɪksti"],
        "seventy": ["sevənti"],
        "eighty": ["eɪti"],
        "ninety": ["naɪnti"],
        "hundred": ["hʌndrəd"],
        "thousand": ["θaʊzənd"],
        "million": ["mɪljən"],
        
        # Days and months
        "monday": ["mʌndeɪ"],
        "tuesday": ["tjuːzdeɪ"],
        "wednesday": ["wenzdeɪ"],
        "thursday": ["θɜːzdeɪ"],
        "friday": ["fraɪdeɪ"],
        "saturday": ["sætədeɪ"],
        "sunday": ["sʌndeɪ"],
        "january": ["dʒænjuəri"],
        "february": ["febjuəri"],
        "march": ["mɑːtʃ"],
        "april": ["eɪprəl"],
        "may": ["meɪ"],
        "june": ["dʒuːn"],
        "july": ["dʒuˈlaɪ"],
        "august": ["ɔːɡəst"],
        "september": ["sepˈtembə"],
        "october": ["ɒkˈtəʊbə"],
        "november": ["nəʊˈvembə"],
        "december": ["dɪˈsembə"],
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
    return word.lower().strip(".,!?;:")

def process_text(text):
    """Process text into IPA with cloud-friendly fallbacks"""
    words = text.split()
    results = []
    
    for word in words:
        clean = clean_word(word)
        
        # Check override dictionary first
        if clean in OVERRIDE_DICT:
            results.append({
                "original": word,
                "clean": clean,
                "ipa_options": [OVERRIDE_DICT[clean]],
                "selected": OVERRIDE_DICT[clean],
                "has_override": True
            })
            continue
        
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

def get_system_info():
    """Get system info for debugging deployment issues"""
    info = {
        "espeak_available": check_espeak_available(),
        "espeak_path": shutil.which("espeak-ng"),
        "hce_map_loaded": bool(HCE_MAP),
        "override_dict_loaded": bool(OVERRIDE_DICT),
        "fallback_words_count": len(get_ipa_fallback.__code__.co_consts[1]) if hasattr(get_ipa_fallback, '__code__') else "unknown"
    }
    return info