import streamlit as st
import json
import os
from datetime import datetime
from ipa_converter import process_text, reconstruct_sentence, clean_word
from overrides import update_override_dict
import pandas as pd

# Import Google Sheets integration
try:
    from sheets_integration import SheetsLearningHistory
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

# Config
LOG_FILE = "corrections_log.jsonl"
AUTO_LEARN_FILE = "auto_learning_log.jsonl"

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
    st.session_state.confidence_threshold = 0.7

# Initialize Google Sheets
if SHEETS_AVAILABLE and 'sheets_history' not in st.session_state:
    st.session_state.sheets_history = SheetsLearningHistory()
    st.session_state.sheets_connected = st.session_state.sheets_history.initialize_connection()
    if 'session_id' not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# Reverse transcription class
class IPAToEnglishTranscriber:
    def __init__(self):
        self.ipa_to_word_dict = {}
        self.load_reverse_mappings()
    
    def load_reverse_mappings(self):
        """Load reverse mappings from override dictionary and auto-learning data"""
        # Load from override dictionary
        if os.path.exists("override_dict.json"):
            try:
                with open("override_dict.json", "r", encoding='utf-8') as f:
                    override_dict = json.load(f)
                
                for word, ipa in override_dict.items():
                    if ipa not in self.ipa_to_word_dict:
                        self.ipa_to_word_dict[ipa] = []
                    if word not in self.ipa_to_word_dict[ipa]:
                        self.ipa_to_word_dict[ipa].append(word)
            except:
                pass
        
        # Load from auto-learning logs (high confidence only)
        if os.path.exists(AUTO_LEARN_FILE):
            try:
                word_confidence = {}
                with open(AUTO_LEARN_FILE, "r", encoding='utf-8') as f:
                    for line in f:
                        entry = json.loads(line)
                        word = entry.get('word', '')
                        ipa = entry.get('ipa_choice', '')
                        confidence = entry.get('confidence', 0)
                        
                        if word and ipa and confidence >= 0.6:
                            key = (ipa, word)
                            if key not in word_confidence or confidence > word_confidence[key]:
                                word_confidence[key] = confidence
                
                # Add high confidence mappings
                for (ipa, word), confidence in word_confidence.items():
                    if ipa not in self.ipa_to_word_dict:
                        self.ipa_to_word_dict[ipa] = []
                    if word not in self.ipa_to_word_dict[ipa]:
                        self.ipa_to_word_dict[ipa].append(word)
            except:
                pass
    
    def find_word_candidates(self, ipa_input):
        """Find English word candidates for given IPA"""
        ipa_input = ipa_input.strip()
        if ipa_input in self.ipa_to_word_dict:
            return self.ipa_to_word_dict[ipa_input]
        return []
    
    def transcribe_ipa_sequence(self, ipa_sequence):
        """Transcribe IPA sequence to potential English words"""
        ipa_words = [w.strip() for w in ipa_sequence.split() if w.strip()]
        results = []
        
        for ipa_word in ipa_words:
            candidates = self.find_word_candidates(ipa_word)
            results.append({
                'ipa_input': ipa_word,
                'candidates': candidates[:5]
            })
        
        return results

def auto_learn_from_selection(word_data, selected_option, interaction_type="selection"):
    """Simple auto-learning with Google Sheets integration"""
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
    
    # Boost for manual corrections
    confidence_multiplier = 1.5 if interaction_type == "manual_correction" else 1.0
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
    
    # Auto-promote to override dictionary
    if (final_confidence >= st.session_state.confidence_threshold 
        and auto_data[clean_word_val][selected_option]['count'] >= 2):
        
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

# Initialize reverse transcriber
if 'reverse_transcriber' not in st.session_state:
    st.session_state.reverse_transcriber = IPAToEnglishTranscriber()

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
        min_value=0.5,
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

# Tabs for bidirectional transcription
tab1, tab2 = st.tabs(["🇦🇺 English → IPA", "🔄 IPA → English"])

with tab1:
    # English to IPA transcription
    text = st.text_input("Enter Australian English text:", placeholder="e.g., I can't dance at the castle")

    if text and text != st.session_state.current_text:
        st.session_state.current_text = text
        st.session_state.word_results = process_text(text)

    if st.session_state.word_results:
        st.markdown("### Word-by-Word IPA Transcription:")
        
        word_words = [wr for wr in st.session_state.word_results if wr.get("original", "").replace("'", "").isalnum()]
        
        # Simple layout for word selection
        for i, word_data in enumerate(word_words):
            word_idx = st.session_state.word_results.index(word_data)
            
            col1, col2, col3 = st.columns([2, 3, 2])
            
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
                    
                    # Auto-learning on selection
                    if st.session_state.auto_learn_enabled:
                        auto_learn_from_selection(word_data, selected, "selection")
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
                
                # Auto-learning for corrections
                if correction and st.session_state.auto_learn_enabled:
                    auto_learn_from_selection(word_data, correction, "manual_correction")
        
        # Full sentence result
        st.markdown("### Full Sentence IPA:")
        full_ipa = reconstruct_sentence(st.session_state.word_results)
        st.code(full_ipa, language=None)
        
        # Action buttons
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
                
                # Log sentence completion
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
                
                # Refresh reverse transcriber
                st.session_state.reverse_transcriber = IPAToEnglishTranscriber()
        
        with col2:
            if st.button("🔄 Clear", use_container_width=True):
                st.session_state.current_text = ""
                st.session_state.word_results = []
                st.rerun()

with tab2:
    # IPA to English transcription
    st.markdown("### 🔄 IPA to English Reverse Transcription")
    st.markdown("*Convert IPA back to English using your learned pronunciations*")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ipa_input = st.text_input(
            "Enter IPA transcription:", 
            placeholder="e.g., dɑːns kɑːsəl pɑːθ",
            help="Enter IPA symbols separated by spaces for multiple words"
        )
    
    with col2:
        if st.button("🔄 Refresh Mappings"):
            st.session_state.reverse_transcriber = IPAToEnglishTranscriber()
            st.success("Refreshed!")
    
    if ipa_input:
        results = st.session_state.reverse_transcriber.transcribe_ipa_sequence(ipa_input)
        
        if results:
            st.markdown("#### Possible English Words:")
            
            for result in results:
                ipa_segment = result['ipa_input']
                candidates = result['candidates']
                
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**`{ipa_segment}`**")
                
                with col2:
                    if candidates:
                        candidate_text = " | ".join(candidates)
                        st.markdown(f"→ **{candidate_text}**")
                    else:
                        st.info("No learned words found")
        
        # Quick stats about reverse transcription
        with st.expander("📊 Reverse Transcription Stats"):
            total_patterns = len(st.session_state.reverse_transcriber.ipa_to_word_dict)
            total_words = sum(len(words) for words in st.session_state.reverse_transcriber.ipa_to_word_dict.values())
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("IPA Patterns Learned", total_patterns)
            with col2:
                st.metric("Total Word Mappings", total_words)

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

# Basic learning statistics in sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📈 Learning Stats")
    
    # Count learned words
    override_count = 0
    if os.path.exists("override_dict.json"):
        try:
            with open("override_dict.json", "r", encoding='utf-8') as f:
                override_dict = json.load(f)
                override_count = len(override_dict)
        except:
            pass
    
    # Count total interactions
    total_interactions = 0
    if os.path.exists(AUTO_LEARN_FILE):
        try:
            with open(AUTO_LEARN_FILE, "r", encoding='utf-8') as f:
                total_interactions = len(f.readlines())
        except:
            pass
    
    st.metric("Words Learned", override_count)
    st.metric("Total Interactions", total_interactions)
    
    # Show recent activity
    if os.path.exists(AUTO_LEARN_FILE):
        try:
            with open(AUTO_LEARN_FILE, "r", encoding='utf-8') as f:
                lines = f.readlines()
            
            if lines:
                st.markdown("**Recent Activity:**")
                for line in lines[-3:]:
                    entry = json.loads(line)
                    confidence = entry.get('confidence', 0)
                    confidence_color = "🟢" if confidence >= st.session_state.confidence_threshold else "🟡"
                    st.caption(f"{confidence_color} {entry['word']} → {entry['ipa_choice']}")
        except:
            pass

# Google Sheets setup instructions
if SHEETS_AVAILABLE:
    with st.expander("⚙️ Google Sheets Setup"):
        st.markdown("""
        ### Setting up Google Sheets Integration:
        
        1. Create a Google Cloud Project and enable Google Sheets API
        2. Create a Service Account and download JSON credentials
        3. Add credentials to `.streamlit/secrets.toml`:
        
        ```toml
        [gcp_service_account]
        type = "service_account"
        project_id = "your-project-id"
        private_key = "-----BEGIN PRIVATE KEY-----\\nYOUR-KEY\\n-----END PRIVATE KEY-----\\n"
        client_email = "your-service-account@your-project.iam.gserviceaccount.com"
        # ... other fields
        ```
        
        4. Share your Google Sheet with the service account email
        5. Install required packages: `pip install gspread google-auth pandas`
        """)
else:
    st.sidebar.warning("Install Google Sheets packages for cloud sync: `pip install gspread google-auth pandas`")

# Footer
st.markdown("---")
st.caption("🇦🇺 HCE Australian English IPA Transcriber with Auto-Learning & Reverse Lookup")