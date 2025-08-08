import streamlit as st
import json
import os
from datetime import datetime
from ipa_converter import process_text, reconstruct_sentence, clean_word
from overrides import update_override_dict
import gspread
from google.oauth2.service_account import Credentials

# --- FIXED Google Sheets Setup ---
def initialize_google_sheets():
    """Initialize Google Sheets connection with proper fallbacks"""
    try:
        # First try Streamlit secrets (for cloud deployment)
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            credentials_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(
                credentials_dict,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            gc = gspread.authorize(creds)
            st.success("✅ Connected to Google Sheets via Streamlit secrets")
            return gc
        
        # Then try local credentials file (for local development)
        elif os.path.exists("google_credentials.json"):
            creds = Credentials.from_service_account_file(
                "google_credentials.json",
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            gc = gspread.authorize(creds)
            st.success("✅ Connected to Google Sheets via local credentials")
            return gc
        
        # Legacy path (remove this problematic code)
        # elif os.path.exists(os.path.join("secrets", "service_account.json")):
        #     # This will fail in Streamlit Cloud
        
        else:
            st.warning("⚠️ Google Sheets credentials not found. Using local storage only.")
            return None
            
    except Exception as e:
        st.error(f"❌ Google Sheets connection failed: {str(e)}")
        return None

# Initialize Google Sheets
gc = initialize_google_sheets()

# Only try to access sheets if connection successful
if gc:
    SHEET_NAME = "HCE IPA Training Data"
    try:
        worksheet = gc.open(SHEET_NAME).sheet1
        first_row = worksheet.row_values(1)
        st.write("✅ Successfully read the first row from the Google Sheet:")
        st.write(first_row)
    except Exception as e:
        st.error(f"❌ Error accessing Google Sheet: {e}")
else:
    st.info("ℹ️ Running in local storage mode - Google Sheets features disabled")

SHEET_NAME = "HCE IPA Training Data"
try:
    worksheet = gc.open(SHEET_NAME).sheet1
    first_row = worksheet.row_values(1)
    st.write("✅ Successfully read the first row from the Google Sheet:")
    st.write(first_row)
except Exception as e:
    st.error(f"❌ Error accessing Google Sheet: {e}")

# --- Config ---
LOG_FILE = "corrections_log.jsonl"
AUTO_LEARN_FILE = "auto_learning_log.jsonl"

# --- Helper function for safe logging ---
def log_training_data(log_entry, filename=AUTO_LEARN_FILE):
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except PermissionError:
        st.warning(f"Permission denied: cannot write to {filename}")

# --- Auto-learn function ---
def auto_learn_from_selection(word_data, selected_option, interaction_type="selection"):
    clean_word = word_data.get('clean', word_data.get('original', '').lower())
    
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
                        auto_data[word][ipa] = {'count': 0, 'confidence': 0.0}
                    auto_data[word][ipa]['count'] += 1
        except:
            pass
    
    # Initialize if new
    if clean_word not in auto_data:
        auto_data[clean_word] = {}
    if selected_option not in auto_data[clean_word]:
        auto_data[clean_word][selected_option] = {'count': 0, 'confidence': 0.0}
    
    auto_data[clean_word][selected_option]['count'] += 1
    
    total_selections = sum(data['count'] for data in auto_data[clean_word].values())
    base_confidence = auto_data[clean_word][selected_option]['count'] / total_selections
    
    confidence_multiplier = 1.5 if interaction_type == "manual_correction" else 1.0
    if interaction_type == "accept_all":
        confidence_multiplier = 1.2
    
    auto_data[clean_word][selected_option]['confidence'] = min(1.0, base_confidence * confidence_multiplier)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "word": clean_word,
        "original_word": word_data.get('original'),
        "ipa_choice": selected_option,
        "interaction_type": interaction_type,
        "confidence": auto_data[clean_word][selected_option]['confidence'],
        "selection_count": auto_data[clean_word][selected_option]['count'],
        "total_word_selections": total_selections
    }
    
    log_training_data(log_entry, AUTO_LEARN_FILE)
    
    # Auto-promote
    if (auto_data[clean_word][selected_option]['confidence'] >= st.session_state.confidence_threshold 
        and auto_data[clean_word][selected_option]['count'] >= 2):
        
        override_dict = {}
        if os.path.exists("override_dict.json"):
            try:
                with open("override_dict.json", "r", encoding='utf-8') as f:
                    override_dict = json.load(f)
            except:
                pass
        
        override_dict[clean_word] = selected_option
        
        try:
            with open("override_dict.json", "w", encoding='utf-8') as f:
                json.dump(override_dict, f, ensure_ascii=False, indent=2)
        except PermissionError:
            st.warning("Permission denied: cannot update override_dict.json")
        
        return True
    
    return False

# --- Learning stats ---
def get_learning_stats():
    stats = {
        "total_interactions": 0,
        "unique_words": 0,
        "auto_promotions": 0,
        "manual_corrections": 0,
        "high_confidence_words": 0
    }
    
    if os.path.exists(AUTO_LEARN_FILE):
        try:
            with open(AUTO_LEARN_FILE, "r", encoding='utf-8') as f:
                lines = f.readlines()
                stats["total_interactions"] = len(lines)
                words_seen = set()
                for line in lines:
                    entry = json.loads(line)
                    words_seen.add(entry.get('word'))
                    if entry.get('interaction_type') == 'manual_correction':
                        stats["manual_corrections"] += 1
                    if entry.get('confidence', 0) >= st.session_state.confidence_threshold:
                        stats["high_confidence_words"] += 1
                stats["unique_words"] = len(words_seen)
        except:
            pass
    
    if os.path.exists("override_dict.json"):
        try:
            with open("override_dict.json", "r", encoding='utf-8') as f:
                override_dict = json.load(f)
                stats["auto_promotions"] = len(override_dict)
        except:
            pass
    
    return stats

# --- Streamlit UI Setup ---
st.set_page_config(
    page_title="HCE IPA Transcriber", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "word_results" not in st.session_state:
    st.session_state.word_results = []
if "current_text" not in st.session_state:
    st.session_state.current_text = ""
if "auto_learn_enabled" not in st.session_state:
    st.session_state.auto_learn_enabled = True
if "confidence_threshold" not in st.session_state:
    st.session_state.confidence_threshold = 0.7

# Title and settings UI
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🇦🇺 Enhanced Auto-Learning HCE IPA Transcriber")
    st.markdown("*Learns from every interaction - builds robust personal dictionary*")

with col2:
    with st.expander("⚙️ Learning Settings"):
        st.session_state.auto_learn_enabled = st.checkbox(
            "Auto-Learning Enabled", 
            value=st.session_state.auto_learn_enabled,
            help="Automatically learn from selections and build confidence scores"
        )
        
        st.session_state.confidence_threshold = st.slider(
            "Auto-Promote Threshold",
            min_value=0.5,
            max_value=1.0,
            value=st.session_state.confidence_threshold,
            step=0.1,
            help="Confidence score needed to auto-promote to permanent dictionary"
        )

# Text input
text = st.text_input("Enter Australian English text:", placeholder="e.g., I can't dance at the castle")

if text and text != st.session_state.current_text:
    st.session_state.current_text = text
    st.session_state.word_results = process_text(text)

if st.session_state.word_results:
    st.markdown("### Word-by-Word IPA Transcription:")
    
    # Filter to words with valid original text
    word_words = [wr for wr in st.session_state.word_results if wr.get("original", "").replace("'", "").isalnum()]
    
    # Show words in columns or rows based on count
    if len(word_words) <= 3:
        cols = st.columns(len(word_words))
        for i, word_data in enumerate(word_words):
            with cols[i]:
                word_idx = st.session_state.word_results.index(word_data)
                st.markdown(f"**{word_data['original']}**")
                if word_data.get('has_override', False):
                    st.success("✅ Learned")
                
                if len(word_data.get('ipa_options', [])) > 1:
                    selected = st.radio(
                        "Options:",
                        word_data['ipa_options'],
                        key=f"select_col_{word_idx}_{word_data['original']}",
                        label_visibility="collapsed",
                        on_change=lambda wd=word_data: auto_learn_from_selection(wd, st.session_state.get(f"select_col_{word_idx}_{wd['original']}", ""), "selection") if st.session_state.auto_learn_enabled else None
                    )
                    st.session_state.word_results[word_idx]['selected'] = selected
                else:
                    ipa_option = word_data.get('ipa_options', [''])[0]
                    st.code(ipa_option)
                    st.session_state.word_results[word_idx]['selected'] = ipa_option
                
                correction = st.text_input(
                    "Manual:",
                    key=f"correct_col_{word_idx}_{word_data['original']}",
                    placeholder="Custom IPA...",
                    label_visibility="collapsed",
                    on_change=lambda wd=word_data: auto_learn_from_selection(wd, st.session_state.get(f"correct_col_{word_idx}_{wd['original']}", ""), "manual_correction") if st.session_state.auto_learn_enabled and st.session_state.get(f"correct_col_{word_idx}_{wd['original']}", "") else None
                )
                st.session_state.word_results[word_idx]['correction'] = correction if correction else None
    
    elif len(word_words) <= 6:
        rows = (len(word_words) + 2) // 3
        for row in range(rows):
            start_idx = row * 3
            end_idx = min(start_idx + 3, len(word_words))
            row_words = word_words[start_idx:end_idx]
            cols = st.columns(len(row_words))
            
            for i, word_data in enumerate(row_words):
                with cols[i]:
                    word_idx = st.session_state.word_results.index(word_data)
                    st.markdown(f"**{word_data['original']}**")
                    if word_data.get('has_override', False):
                        st.success("✅ Learned")
                    
                    if len(word_data.get('ipa_options', [])) > 1:
                        selected = st.radio(
                            "Options:",
                            word_data['ipa_options'],
                            key=f"select_row_{row}_{i}_{word_data['original']}",
                            label_visibility="collapsed",
                            on_change=lambda wd=word_data: auto_learn_from_selection(wd, st.session_state.get(f"select_row_{row}_{i}_{wd['original']}", ""), "selection") if st.session_state.auto_learn_enabled else None
                        )
                        st.session_state.word_results[word_idx]['selected'] = selected
                    else:
                        ipa_option = word_data.get('ipa_options', [''])[0]
                        st.code(ipa_option)
                        st.session_state.word_results[word_idx]['selected'] = ipa_option
                    
                    correction = st.text_input(
                        "Manual:",
                        key=f"correct_row_{row}_{i}_{word_data['original']}",
                        placeholder="Custom IPA...",
                        label_visibility="collapsed",
                        on_change=lambda wd=word_data: auto_learn_from_selection(wd, st.session_state.get(f"correct_row_{row}_{i}_{wd['original']}", ""), "manual_correction") if st.session_state.auto_learn_enabled and st.session_state.get(f"correct_row_{row}_{i}_{wd['original']}", "") else None
                    )
                    st.session_state.word_results[word_idx]['correction'] = correction if correction else None
    else:
        for word_idx, word_data in enumerate(word_words):
            if word_data.get("original", "").replace("'", "").isalnum():
                actual_idx = st.session_state.word_results.index(word_data)
                st.markdown(f"**{word_data['original']}**")
                if word_data.get('has_override', False):
                    st.success("✅ Learned")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    if len(word_data.get('ipa_options', [])) > 1:
                        selected = st.radio(
                            "Options:",
                            word_data['ipa_options'],
                            key=f"select_list_{actual_idx}_{word_data['original']}",
                            horizontal=True,
                            on_change=lambda wd=word_data: auto_learn_from_selection(wd, st.session_state.get(f"select_list_{actual_idx}_{wd['original']}", ""), "selection") if st.session_state.auto_learn_enabled else None
                        )
                        st.session_state.word_results[actual_idx]['selected'] = selected
                    else:
                        ipa_option = word_data.get('ipa_options', [''])[0]
                        st.code(ipa_option)
                        st.session_state.word_results[actual_idx]['selected'] = ipa_option
                
                with col2:
                    correction = st.text_input(
                        "Custom:",
                        key=f"correct_list_{actual_idx}_{word_data['original']}",
                        placeholder="IPA...",
                        on_change=lambda wd=word_data: auto_learn_from_selection(wd, st.session_state.get(f"correct_list_{actual_idx}_{wd['original']}", ""), "manual_correction") if st.session_state.auto_learn_enabled and st.session_state.get(f"correct_list_{actual_idx}_{wd['original']}", "") else None
                    )
                    st.session_state.word_results[actual_idx]['correction'] = correction if correction else None
                
                st.divider()
    
    st.markdown("### Full Sentence IPA:")
    full_ipa = reconstruct_sentence(st.session_state.word_results)
    st.code(full_ipa, language=None)
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
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
                "auto_promotions": auto_promotions,
                "type": "sentence_accept_all"
            }
            
            with open(LOG_FILE, "a", encoding='utf-8') as f:
                f.write(json.dumps(sentence_log, ensure_ascii=False) + "\n")
            
            if auto_promotions > 0:
                st.success(f"✅ Learned {len(learned_words)} words, auto-promoted {auto_promotions} to permanent dictionary!")
            else:
                st.success(f"✅ Learned {len(learned_words)} words with confidence tracking")
    
    with col2:
        if st.button("💾 Manual Save", use_container_width=True):
            corrections_made = []
            
            for word_data in st.session_state.word_results:
                if word_data.get("original", "").replace("'", "").isalnum():
                    final_choice = word_data.get('correction') or word_data.get('selected')
                    if final_choice and final_choice != word_data.get('ipa_options', [''])[0]:
                        corrections_made.append(f"{word_data['original']} → {final_choice}")
                        
                        log_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "text": word_data['original'],
                            "word_clean": word_data['clean'],
                            "ipa_options": word_data['ipa_options'],
                            "selected": word_data.get('selected'),
                            "manual_correction": word_data.get('correction'),
                            "final_choice": final_choice,
                            "type": "manual_save"
                        }
                        
                        with open(LOG_FILE, "a", encoding='utf-8') as f:
                            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            update_override_dict()
            
            if corrections_made:
                st.success(f"✅ Manually saved {len(corrections_made)} corrections")
            else:
                st.info("ℹ️ No corrections to save")
    
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.word_results = []
            st.session_state.current_text = ""
            st.experimental_rerun()
    
    with col4:
        if st.button("🗑️ Clear All Data", use_container_width=True):
            files_to_remove = [LOG_FILE, AUTO_LEARN_FILE, "override_dict.json"]
            removed_count = 0
            for file in files_to_remove:
                if os.path.exists(file):
                    os.remove(file)
                    removed_count += 1
            st.success(f"Cleared {removed_count} data files!")
            st.experimental_rerun()

# --- Sidebar ---
stats = get_learning_stats()
with st.sidebar:
    st.markdown("### 🧠 Auto-Learning Stats")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Interactions", stats["total_interactions"])
        st.metric("Unique Words", stats["unique_words"])
    with col2:
        st.metric("Auto-Promotions", stats["auto_promotions"])
        st.metric("Manual Corrections", stats["manual_corrections"])
    
    st.metric("High Confidence Words", stats["high_confidence_words"])
    
    if stats["total_interactions"] > 0:
        efficiency = round((stats["auto_promotions"] / stats["total_interactions"]) * 100, 1)
        st.metric("Learning Efficiency", f"{efficiency}%")
    
    if os.path.exists(AUTO_LEARN_FILE):
        try:
            with open(AUTO_LEARN_FILE, "r", encoding='utf-8') as f:
                lines = f.readlines()
            
            recent_entries = []
            for line in lines[-5:]:
                entry = json.loads(line)
                recent_entries.append(entry)
            
            if recent_entries:
                st.markdown("**Recent Auto-Learning:**")
                for entry in reversed(recent_entries):
                    confidence_color = "🟢" if entry.get('confidence', 0) >= st.session_state.confidence_threshold else "🟡"
                    st.text(f"{confidence_color} {entry['word']} → {entry['ipa_choice']}")
                    st.caption(f"Confidence: {entry.get('confidence', 0):.2f}")
        except:
            pass

# --- Quick Test Examples ---
with st.expander("🧪 Quick Test Examples - Try These to Build Learning Data"):
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
                st.experimental_rerun()

# --- Help Section ---
with st.expander("ℹ️ How Auto-Learning Works"):
    st.markdown("""
    **🤖 Automatic Learning Features:**
    
    1. **Every Selection Counts**: Choosing any IPA option automatically logs it with confidence scoring
    
    2. **Smart Confidence Building**: 
       - Manual corrections get 1.5x confidence boost
       - "Accept All" gives 1.2x boost  
       - Regular selections build base confidence
    
    3. **Auto-Promotion**: When a word reaches your confidence threshold (default 70%) and has been selected 2+ times, it automatically becomes permanent
    
    4. **Comprehensive Tracking**: 
       - Individual word learning in `auto_learning_log.jsonl`
       - Permanent dictionary in `override_dict.json`
       - Manual corrections in `corrections_log.jsonl`
    
    **💡 Pro Tips:**
    - Start with simple words to build the base dictionary
    - Use "Accept All & Learn" for fast bulk learning
    - Adjust confidence threshold in settings for stricter/looser auto-promotion
    - The sidebar shows your learning progress in real-time
    """)

