import platform
import shutil
import subprocess
import json
import os
import re

# Load HCE IPA mappings
with open("hce_map.json", "r", encoding='utf-8') as f:
    HCE_MAP = json.load(f)

# Load override dict if exists
override_dict = {}
if os.path.exists("override_dict.json"):
    with open("override_dict.json", "r", encoding='utf-8') as f:
        override_dict = json.load(f)

def get_espeak_path():
    """Detect the espeak-ng executable path depending on OS."""
    if platform.system() == "Windows":
        path = r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe"
        if os.path.exists(path):
            return path
        else:
            # fallback to PATH search
            return shutil.which("espeak-ng.exe")
    else:
        return shutil.which("espeak-ng")

espeak_path = get_espeak_path()
if espeak_path is None:
    raise FileNotFoundError("espeak-ng executable not found. Please install it or add to PATH.")

def clean_word(word):
    """Clean word for dictionary lookup (lowercase, remove punctuation except apostrophes/hyphens)."""
    return re.sub(r'[^\w\'-]', '', word.lower())

def get_espeak_ipa_word(word: str) -> str:
    """Get IPA transcription of a single word from espeak-ng."""
    try:
        result = subprocess.run(
            [espeak_path, "-v", "en-au", "-q", "--ipa", word],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def get_espeak_ipa_sentence(text: str) -> str:
    """Get IPA transcription of a full sentence from espeak-ng."""
    try:
        result = subprocess.run(
            [espeak_path, "-v", "en-au", "-q", "--ipa", text],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def apply_hce_mapping(ipa_text: str) -> str:
    """Apply HCE IPA mapping replacements to IPA text."""
    for original, hce in HCE_MAP.items():
        ipa_text = ipa_text.replace(original, hce)
    return ipa_text

def process_text(text: str):
    """
    Process text word by word applying learned overrides and generating IPA options.

    Returns a list of dicts with each word's info:
    - original
    - clean
    - ipa_options (list)
    - has_override (bool)
    - selected (default None)
    - correction (default None)
    """
    # Tokenize into words and punctuation
    words = re.findall(r'\b\w+(?:\'[a-z]+)?\b|[^\w\s]', text)
    word_results = []

    for word in words:
        if re.match(r'\w', word):  # Word token
            clean = clean_word(word)

            # Default IPA transcription
            default_ipa = get_default_word_transcription(word)

            # Generate alternatives for common Aussie variants
            alternatives = generate_alternatives(default_ipa)

            # Use override if exists
            if clean in override_dict:
                ipa_options = [override_dict[clean]]
                if default_ipa not in ipa_options:
                    ipa_options.append(default_ipa)
                ipa_options.extend([alt for alt in alternatives if alt not in ipa_options])
            else:
                ipa_options = [default_ipa] + alternatives

            word_results.append({
                "original": word,
                "clean": clean,
                "ipa_options": list(dict.fromkeys(ipa_options)),  # Deduplicate while preserving order
                "has_override": clean in override_dict,
                "selected": None,
                "correction": None
            })
        else:
            # Punctuation or other non-word tokens
            word_results.append({
                "original": word,
                "clean": word,
                "ipa_options": [word],
                "has_override": False,
                "selected": word,
                "correction": None
            })

    return word_results

def generate_alternatives(default_ipa):
    """Generate common Australian English vowel pronunciation alternatives."""
    alternatives = []

    # Simple vowel replacements representing common Aussie variants
    alt1 = default_ipa.replace("æː", "ɐː")  # TRAP vowel variant
    alt2 = default_ipa.replace("ɐː", "æː")  # Reverse variant
    alt3 = default_ipa.replace("ɑː", "æː")  # BATH vowel variant
    alt4 = default_ipa.replace("æː", "ɑː")  # Reverse BATH variant

    for alt in [alt1, alt2, alt3, alt4]:
        if alt != default_ipa and alt not in alternatives:
            alternatives.append(alt)

    return alternatives[:2]  # Limit to 2 alternatives

def get_default_word_transcription(word: str):
    """Get the default IPA transcription for a word with HCE mapping applied."""
    raw_ipa = get_espeak_ipa_word(word)
    return apply_hce_mapping(raw_ipa)

def reconstruct_sentence(word_results):
    """Rebuild the full IPA transcription sentence from word results."""
    result = []
    for word_data in word_results:
        if word_data["correction"]:
            result.append(word_data["correction"])
        elif word_data["selected"]:
            result.append(word_data["selected"])
        else:
            result.append(word_data["ipa_options"][0])
    return " ".join(result)

# Backwards compatible helpers

def get_ipa_options(text: str):
    """Get IPA options for a word or sentence."""
    if len(text.split()) == 1:
        word_results = process_text(text)
        return word_results[0]["ipa_options"] if word_results else [text]
    else:
        default = get_espeak_ipa_sentence(text)
        return [apply_hce_mapping(default)]

def get_default_transcription(text: str):
    """Get default IPA transcription for full text."""
    default = get_espeak_ipa_sentence(text)
    return apply_hce_mapping(default)
