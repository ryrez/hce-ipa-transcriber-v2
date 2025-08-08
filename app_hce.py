import streamlit as st
import json
import os
from datetime import datetime
from collections import defaultdict
import requests
import pandas as pd
from ipa_converter import process_text, reconstruct_sentence, clean_word
from overrides import update_override_dict

# Import Google Sheets integration
try:
    from sheets_integration import SheetsLearningHistory
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

# Config
LOG_FILE = "corrections_log.jsonl"
AUTO_LEARN_FILE = "auto_learning_log.jsonl"
CUSTOM_DICT_FILE = "custom_dict.json"

# Page setup
st.set_page_config(
    page_title="HCE IPA Transcriber with Reverse Lookup", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "word_results" not in st.session_state:
    st.session_state.word_results = []
if "current_text" not in st.session_state:
    st.session_state.current_text = ""
if "auto_learn_enabled" not in st.session_state:
    st.session_state.auto_learn_enabled = True
if "confidence_threshold" not in st.session_state:
    st.session_state.confidence_threshold = 0.5

# Initialize Google Sheets
if SHEETS_AVAILABLE and 'sheets_history' not in st.session_state:
    st.session_state.sheets_history = SheetsLearningHistory()
    st.session_state.sheets_connected = st.session_state.sheets_history.initialize_connection()
    if 'session_id' not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

class DialectAwareIPATranscriber:
    def __init__(self):
        self.ipa_to_word_dict = defaultdict(list)
        self.word_to_ipa_dict = {}
        self.load_resources()
    
    def load_resources(self):
        """Load all pronunciation resources"""
        self.load_cmu_dict()
        self.load_aus_dict()
        self.load_custom_dict()
    
    def load_cmu_dict(self):
        """Load CMU dictionary with US dialect tag"""
        url = "https://raw.githubusercontent.com/Alexir/CMUdict/master/cmudict-0.7b"
        try:
            response = requests.get(url)
            cmu_lines = response.text.split('\n')
        except:
            try:
                with open("cmudict-0.7b", 'r', encoding='latin-1') as f:
                    cmu_lines = f.readlines()
            except:
                cmu_lines = []
                st.error("Couldn't load CMU dictionary")
        
        arpa_to_ipa = {
            'AA': 'ɑ', 'AE': 'æ', 'AH': 'ə', 'AO': 'ɔ', 
            'AW': 'aʊ', 'AY': 'aɪ', 'B': 'b', 'CH': 'tʃ',
            'D': 'd', 'DH': 'ð', 'EH': 'ɛ', 'ER': 'ɝ', 
            'EY': 'eɪ', 'F': 'f', 'G': 'ɡ', 'HH': 'h',
            'IH': 'ɪ', 'IY': 'i', 'JH': 'dʒ', 'K': 'k',
            'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ',
            'OW': 'oʊ', 'OY': 'ɔɪ', 'P': 'p', 'R': 'r',
            'S': 's', 'SH': 'ʃ', 'T': 't', 'TH': 'θ',
            'UH': 'ʊ', 'UW': 'u', 'V': 'v', 'W': 'w',
            'Y': 'j', 'Z': 'z', 'ZH': 'ʒ'
        }
        
        for line in cmu_lines:
            if line.startswith(';'): continue
            parts = line.split('  ')
            if len(parts) >= 2:
                word = parts[0].lower()
                phonemes = parts[1].strip().split()
                ipa = ' '.join([arpa_to_ipa.get(p, p) for p in phonemes])
                
                self._add_mapping(
                    ipa=ipa,
                    word=word,
                    source="cmu",
                    dialect="us"
                )
    
    def load_aus_dict(self):
        """Load Australian-specific pronunciations"""
        aus_mappings = {
            "dance": "dæːns",
            "castle": "kæːsəl",
            "path": "pɑːθ",
            "bath": "bɑːθ",
            "laugh": "lɑːf",
            "chance": "tʃɑːns",
            "plant": "plɑːnt",
            "graph": "ɡrɑːf",
            "example": "ɪɡzɑːmpəl"
        }
        
        for word, ipa in aus_mappings.items():
            self._add_mapping(
                ipa=ipa,
                word=word,
                source="aus_override",
                dialect="au"
            )
    
    def load_custom_dict(self):
        """Load user-corrected pronunciations"""
        if os.path.exists(CUSTOM_DICT_FILE):
            try:
                with open(CUSTOM_DICT_FILE, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                
                for entry in custom_data:
                    self._add_mapping(
                        ipa=entry['ipa'],
                        word=entry['word'],
                        source="user",
                        dialect=entry.get('dialect', 'au'),
                        is_custom=True
                    )
            except Exception as e:
                st.error(f"Error loading custom dict: {e}")
    
    def _add_mapping(self, ipa, word, source, dialect, is_custom=False):
        """Add a pronunciation mapping with metadata"""
        entry = {
            'word': word,
            'dialect': dialect,
            'source': source,
            'is_custom': is_custom
        }
        
        if entry not in self.ipa_to_word_dict[ipa]:
            self.ipa_to_word_dict[ipa].append(entry)
        
        if word not in self.word_to_ipa_dict:
            self.word_to_ipa_dict[word] = []
        
        ipa_entry = {
            'ipa': ipa,
            'dialect': dialect,
            'source': source,
            'is_custom': is_custom
        }
        
        if ipa_entry not in self.word_to_ipa_dict[word]:
            self.word_to_ipa_dict[word].append(ipa_entry)
    
    def find_word_candidates(self, ipa_input, dialect_preference=None):
        """Find words matching IPA, optionally filtered by dialect"""
        candidates = self.ipa_to_word_dict.get(ipa_input, [])
        
        if dialect_preference:
            candidates = sorted(
                candidates,
                key=lambda x: x['dialect'] == dialect_preference,
                reverse=True
            )
        
        return candidates
    
    def teach_pronunciation(self, word, ipa, dialect='au'):
        """Teach the system a new pronunciation"""
        word = word.lower().strip()
        
        custom_entry = {
            'word': word,
            'ipa': ipa,
            'dialect': dialect,
            'timestamp': datetime.now().isoformat()
        }
        
        custom_data = []
        if os.path.exists(CUSTOM_DICT_FILE):
            with open(CUSTOM_DICT_FILE, 'r', encoding='utf-8') as f:
                custom_data = json.load(f)
        
        custom_data.append(custom_entry)
        
        with open(CUSTOM_DICT_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_data, f, ensure_ascii=False, indent=2)
        
        self._add_mapping(
            ipa=ipa,
            word=word,
            source="user",
            dialect=dialect,
            is_custom=True
        )
        
        return True

# Initialize reverse transcriber
if 'reverse_transcriber' not in st.session_state:
    st.session_state.reverse_transcriber = DialectAwareIPATranscriber()

def force_save_to_override(word, ipa):
    """Force save a word-IPA pair to override dictionary"""
    override_dict = {}
    if os.path.exists("override_dict.json"):
        try:
            with open("override_dict.json", "r", encoding='utf-8') as f:
                override_dict = json.load(f)
        except:
            pass
    
    override_dict[word] = ipa
    
    with open("override_dict.json", "w", encoding='utf-8') as f:
        json.dump(override_dict, f, ensure_ascii=False, indent=2)
    
    st.success(f"✅ FORCED LEARNING: '{word}' → '{ipa}' saved to override dictionary!")
    return True

def auto_learn_from_selection(word_data, selected_option, interaction_type="selection"):
    """Enhanced auto-learning with immediate saving option"""
    clean_word_val = word_data.get('clean', word_data.get('original', '').lower())
    
    # Load existing auto-learning data
    auto_data = {}
    if os.path.exists(AUTO_LEARN_FILE):
        try:
            with open(AUTO_LEARN_FILE, "r", encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line)
                    word = entry.get('word')
                    if word not in auto_data:
                        auto_data[word] = {}
                    
                    ipa = entry.get('ipa_choice')
                    if ipa not in auto_data[word]:
                        auto_data[word][ipa] = {'count': 0}
                    
                    auto_data[word][ipa]['count'] += 1
        except:
            pass
    
    # Initialize word data
    if clean_word_val not in auto_data:
        auto_data[clean_word_val] = {}
    
    if selected_option not in auto_data[clean_word_val]:
        auto_data[clean_word_val][selected_option] = {'count': 0}
    
    # Update selection count
    auto_data[clean_word_val][selected_option]['count'] += 1
    
    # Calculate confidence
    total_selections = sum(data['count'] for data in auto_data[clean_word_val].values())
    base_confidence = auto_data[clean_word_val][selected_option]['count'] / total_selections
    
    # Boost for manual corrections and accept_all
    if interaction_type == "manual_correction":
        confidence_multiplier = 2.0
    elif interaction_type == "accept_all":
        confidence_multiplier = 1.5
    else:
        confidence_multiplier = 1.0
        
    final_confidence = min(1.0, base_confidence * confidence_multiplier)
    
    # Log the learning event
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "word": clean_word_val,
        "original_word": word_data.get('original'),
        "ipa_choice": selected_option,
        "interaction_type": interaction_type,
        "confidence": final_confidence,
        "selection_count": auto_data[clean_word_val][selected_option]['count']
    }
    
    with open(AUTO_LEARN_FILE, "a", encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # Google Sheets logging
    if SHEETS_AVAILABLE and st.session_state.get('sheets_connected', False):
        try:
            st.session_state.sheets_history.log_word_learning(
                word_data, selected_option, interaction_type, 
                final_confidence, auto_data[clean_word_val][selected_option]['count'],
                st.session_state.session_id
            )
        except Exception as e:
            st.sidebar.error(f"Sheets sync failed: {str(e)}")
    
    # Auto-promote to override dictionary with lower threshold
    should_promote = (
        final_confidence >= st.session_state.confidence_threshold 
        and auto_data[clean_word_val][selected_option]['count'] >= 1
    )
    
    if should_promote or interaction_type in ["manual_correction", "accept_all"]:
        override_dict = {}
        if os.path.exists("override_dict.json"):
            try:
                with open("override_dict.json", "r", encoding='utf-8') as f:
                    override_dict = json.load(f)
            except:
                pass
        
        override_dict[clean_word_val] = selected_option
        
        with open("override_dict.json", "w", encoding='utf-8') as f:
            json.dump(override_dict, f, ensure_ascii=False, indent=2)
        
        return True
    
    return False

# Main UI
st.title("🇦🇺 HCE IPA Transcriber")
st.markdown("*Australian English IPA Transcriber with Auto-Learning & Reverse Lookup*")

# Settings in sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    st.session_state.auto_learn_enabled = st.toggle(
        "Auto-Learning", 
        value=st.session_state.auto_learn_enabled
    )
    
    st.session_state.confidence_threshold = st.slider(
        "Auto-Promote Threshold",
        min_value=0.3,
        max_value=1.0,
        value=st.session_state.confidence_threshold,
        step=0.1
    )
    
    # Google Sheets status
    if SHEETS_AVAILABLE:
        st.markdown("### 📊 Google Sheets")
        if st.session_state.get('sheets_connected', False):
            st.success("✅ Connected")
        else:
            st.error("❌ Not Connected")
            if st.button("Retry Connection"):
                st.session_state.sheets_connected = st.session_state.sheets_history.initialize_connection()
                st.rerun()
    
    # Teaching stats
    st.markdown("---")
    st.markdown("### 🧠 Teaching Stats")
    
    custom_count = 0
    if os.path.exists(CUSTOM_DICT_FILE):
        with open(CUSTOM_DICT_FILE, 'r', encoding='utf-8') as f:
            custom_data = json.load(f)
        custom_count = len(custom_data)
    
    st.metric("Custom Pronunciations", custom_count)
    
    if custom_count > 0:
        dialects = defaultdict(int)
        for entry in custom_data:
            dialects[entry.get('dialect', 'au')] += 1
        
        st.markdown("**By Dialect:**")
        for dialect, count in dialects.items():
            st.write(f"- {dialect.upper()}: {count}")
    
    if st.button("🔄 Refresh Pronunciation Data"):
        st.session_state.reverse_transcriber = DialectAwareIPATranscriber()
        st.rerun()

# Tabs for bidirectional transcription
tab1, tab2, tab3 = st.tabs(["🇦🇺 English → IPA", "🔄 IPA → English", "🔧 Debug"])

with tab1:
    # English to IPA transcription
    text = st.text_input("Enter Australian English text:", placeholder="e.g., I can't dance at the castle")

    if text and text != st.session_state.current_text:
        st.session_state.current_text = text
        st.session_state.word_results = process_text(text)

    if st.session_state.word_results:
        st.markdown("### Word-by-Word IPA Transcription:")
        
        word_words = [wr for wr in st.session_state.word_results if wr.get("original", "").replace("'", "").isalnum()]
        
        for i, word_data in enumerate(word_words):
            word_idx = st.session_state.word_results.index(word_data)
            
            col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
            
            with col1:
                st.markdown(f"**{word_data['original']}**")
                if word_data.get('has_override', False):
                    st.success("✅ Learned")
            
            with col2:
                if len(word_data.get('ipa_options', [])) > 1:
                    selected = st.radio(
                        "IPA Options:",
                        word_data['ipa_options'],
                        key=f"select_{word_idx}_{word_data['original']}",
                        label_visibility="collapsed"
                    )
                    st.session_state.word_results[word_idx]['selected'] = selected
                    
                    if st.session_state.auto_learn_enabled:
                        current_selection = st.session_state.word_results[word_idx].get('last_selection')
                        if current_selection != selected:
                            auto_learn_from_selection(word_data, selected, "selection")
                            st.session_state.word_results[word_idx]['last_selection'] = selected
                else:
                    ipa_option = word_data.get('ipa_options', [''])[0]
                    st.code(ipa_option)
                    st.session_state.word_results[word_idx]['selected'] = ipa_option
            
            with col3:
                correction = st.text_input(
                    "Manual correction:",
                    key=f"correct_{word_idx}_{word_data['original']}",
                    placeholder="Custom IPA...",
                    label_visibility="collapsed"
                )
                st.session_state.word_results[word_idx]['correction'] = correction if correction else None
                
                if correction and st.session_state.auto_learn_enabled:
                    current_correction = st.session_state.word_results[word_idx].get('last_correction')
                    if current_correction != correction:
                        auto_learn_from_selection(word_data, correction, "manual_correction")
                        st.session_state.word_results[word_idx]['last_correction'] = correction
            
            with col4:
                final_ipa = word_data.get('correction') or word_data.get('selected', '')
                if final_ipa and st.button("💾", key=f"force_{word_idx}", help="Force save this word"):
                    force_save_to_override(word_data['clean'], final_ipa)
                    st.rerun()
        
        st.markdown("### Full Sentence IPA:")
        full_ipa = reconstruct_sentence(st.session_state.word_results)
        st.code(full_ipa, language=None)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Accept All & Learn", use_container_width=True):
                auto_promotions = 0
                learned_words = []
                
                for word_data in st.session_state.word_results:
                    if word_data.get("original", "").replace("'", "").isalnum():
                        final_choice = word_data.get('correction') or word_data.get('selected')
                        if final_choice:
                            was_promoted = auto_learn_from_selection(word_data, final_choice, "accept_all")
                            if was_promoted:
                                auto_promotions += 1
                            learned_words.append(f"{word_data['original']} → {final_choice}")
                
                sentence_log = {
                    "timestamp": datetime.now().isoformat(),
                    "text": st.session_state.current_text,
                    "full_ipa": full_ipa,
                    "word_count": len(learned_words),
                    "auto_promotions": auto_promotions
                }
                
                with open(LOG_FILE, "a", encoding='utf-8') as f:
                    f.write(json.dumps(sentence_log, ensure_ascii=False) + "\n")
                
                if auto_promotions > 0:
                    st.success(f"✅ Learned {len(learned_words)} words, auto-promoted {auto_promotions}!")
                else:
                    st.success(f"✅ Learned {len(learned_words)} words")
                
                st.session_state.reverse_transcriber = DialectAwareIPATranscriber()
        
        with col2:
            if st.button("🔄 Clear", use_container_width=True):
                st.session_state.current_text = ""
                st.session_state.word_results = []
                st.rerun()

with tab2:
    st.markdown("### 🔄 IPA to English (with Dialect Support)")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ipa_input = st.text_input(
            "Enter IPA transcription:", 
            placeholder="e.g., dɑːns kɑːsəl pɑːθ",
            key="ipa_input"
        )
    
    with col2:
        dialect_pref = st.selectbox(
            "Dialect preference:",
            ["Any", "Australian (AU)", "American (US)"],
            key="dialect_pref"
        )
    
    if ipa_input:
        dialect_map = {
            "Any": None,
            "Australian (AU)": "au",
            "American (US)": "us"
        }
        
        # Normalize IPA input (remove spaces between phonemes)
        normalized_ipa = ' '.join([p.strip() for p in ipa_input.split() if p.strip()])
        
        # Get matches for each IPA segment
        results = []
        for ipa_segment in normalized_ipa.split():
            candidates = st.session_state.reverse_transcriber.find_word_candidates(
                ipa_segment,
                dialect_preference=dialect_map[dialect_pref]
            )
            
            # Only keep candidates with high confidence
            filtered_candidates = [
                c for c in candidates 
                if c['source'] in ['cmu', 'aus_override'] or c['is_custom']
            ]
            
            results.append({
                'ipa_input': ipa_segment,
                'candidates': filtered_candidates[:10]  # Limit to top 10
            })
        
        st.markdown("#### Possible English Words:")
        
        if not any(r['candidates'] for r in results):
            st.warning("No matching words found. Try teaching the pronunciation below.")
        else:
            for result in results:
                ipa_segment = result['ipa_input']
                candidates = result['candidates']
                
                if not candidates:
                    continue
                
                with st.expander(f"IPA: `{ipa_segment}`"):
                    for candidate in candidates:
                        source_badge = {
                            "cmu": "📚 CMU (US)",
                            "aus_override": "🇦🇺 AU",
                            "user": "✨ Custom"
                        }.get(candidate['source'], candidate['source'])
                        
                        st.markdown(f"""
                        **{candidate['word']}**  
                        - Dialect: `{candidate['dialect'].upper()}`  
                        - Source: {source_badge}
                        """)
    
    # Teaching interface
    with st.expander("💡 Teach New Pronunciation", expanded=False):
        teach_col1, teach_col2 = st.columns(2)
        with teach_col1:
            teach_word = st.text_input("English word:", key="teach_word")
            teach_dialect = st.selectbox(
                "Dialect:",
                ["au", "us", "uk"],
                key="teach_dialect"
            )
        with teach_col2:
            teach_ipa = st.text_input("IPA transcription:", key="teach_ipa")
        
        if st.button("Teach Pronunciation", key="teach_button"):
            if teach_word and teach_ipa:
                success = st.session_state.reverse_transcriber.teach_pronunciation(
                    teach_word,
                    teach_ipa,
                    teach_dialect
                )
                if success:
                    st.success("Pronunciation learned! The word will now appear in future searches.")
                    st.rerun()
            else:
                st.warning("Please enter both word and IPA")
                
with tab3:
    st.markdown("### 🔧 Debug & Learning Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Override Dictionary")
        if os.path.exists("override_dict.json"):
            try:
                with open("override_dict.json", "r", encoding='utf-8') as f:
                    override_dict = json.load(f)
                if override_dict:
                    st.json(override_dict)
                else:
                    st.info("Override dictionary is empty")
            except:
                st.error("Error reading override_dict.json")
        else:
            st.info("No override_dict.json found")
        
        st.markdown("#### Test Word Processing")
        test_word = st.text_input("Test word:", placeholder="e.g., dance")
        if test_word:
            clean_test = clean_word(test_word)
            results = process_text(test_word)
            st.write(f"**Clean word:** `{clean_test}`")
            st.write("**Processing results:**")
            st.json(results)
    
    with col2:
        st.markdown("#### Recent Auto-Learning")
        if os.path.exists(AUTO_LEARN_FILE):
            try:
                with open(AUTO_LEARN_FILE, "r", encoding='utf-8') as f:
                    lines = f.readlines()[-10:]
                
                if lines:
                    for line in lines:
                        entry = json.loads(line)
                        confidence = entry.get('confidence', 0)
                        confidence_color = "🟢" if confidence >= st.session_state.confidence_threshold else "🟡"
                        st.caption(f"{confidence_color} {entry['word']} → {entry['ipa_choice']} (conf: {confidence:.2f})")
                else:
                    st.info("No auto-learning entries yet")
            except:
                st.error("Error reading auto-learning log")
        else:
            st.info("No auto_learning_log.jsonl found")
        
        st.markdown("#### Reset Learning")
        if st.button("🗑️ Clear All Learning Data", type="secondary"):
            try:
                if os.path.exists("override_dict.json"):
                    os.remove("override_dict.json")
                if os.path.exists(AUTO_LEARN_FILE):
                    os.remove(AUTO_LEARN_FILE)
                if os.path.exists(LOG_FILE):
                    os.remove(LOG_FILE)
                if os.path.exists(CUSTOM_DICT_FILE):
                    os.remove(CUSTOM_DICT_FILE)
                st.success("All learning data cleared!")
                st.session_state.reverse_transcriber = DialectAwareIPATranscriber()
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing data: {e}")

# Quick test examples
with st.expander("🧪 Quick Test Examples"):
    examples = [
        "dance", "I can't dance", "castle path", "bath chance", 
        "She laughed at the plant", "Can't you see the graph?",
        "The cat sat on the mat", "Australia has great beaches"
    ]
    
    example_cols = st.columns(4)
    for i, example in enumerate(examples):
        with example_cols[i % 4]:
            if st.button(example, key=f"example_{example}"):
                st.session_state.current_text = example
                st.session_state.word_results = process_text(example)
                st.rerun()

# Footer
st.markdown("---")
st.caption("🇦🇺 HCE Australian English IPA Transcriber with Auto-Learning & Reverse Lookup")