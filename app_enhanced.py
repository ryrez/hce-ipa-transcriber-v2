import streamlit as st
import json
import os
from datetime import datetime, timedelta
from ipa_converter import process_text, reconstruct_sentence, clean_word
from overrides import update_override_dict
import time
import pandas as pd

# App Title
st.title("🧪 Markdown Display Debug")

# Show current working directory
st.write("**Current Working Directory:**", os.getcwd())

# Check if the file exists
if os.path.exists("user_guide.md"):
    st.success("✅ `user_guide.md` found!")

    with open("user_guide.md", "r", encoding="utf-8") as f:
        markdown_text = f.read()

    with st.expander("📘 How to Use This App", expanded=False):
        st.markdown(markdown_text, unsafe_allow_html=True)

else:
    st.error("❌ `user_guide.md` not found.")
    st.info("Make sure the file is in the same folder as this app (`app.py`).")
    
# Import the enhanced Google Sheets integration
try:
    from sheets_integration import SheetsLearningHistory, create_learning_visualizations, integrate_sheets_learning
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    st.sidebar.warning("Google Sheets integration not available. Install required packages.")

# Config
LOG_FILE = "corrections_log.jsonl"
AUTO_LEARN_FILE = "auto_learning_log.jsonl"

# Page setup
st.set_page_config(
    page_title="Enhanced HCE IPA Transcriber with Sheets Integration", 
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
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()

# Initialize Google Sheets integration
if SHEETS_AVAILABLE and 'sheets_history' not in st.session_state:
    st.session_state.sheets_history = SheetsLearningHistory()
    st.session_state.sheets_connected = st.session_state.sheets_history.initialize_connection()
    if 'session_id' not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

def enhanced_auto_learn_from_selection(word_data, selected_option, interaction_type="selection"):
    """Enhanced auto-learning with Google Sheets integration"""
    clean_word = word_data.get('clean', word_data.get('original', '').lower())
    
    # Original auto-learning logic
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
    
    # Initialize word data if new
    if clean_word not in auto_data:
        auto_data[clean_word] = {}
    
    if selected_option not in auto_data[clean_word]:
        auto_data[clean_word][selected_option] = {'count': 0, 'confidence': 0.0}
    
    # Update selection count
    auto_data[clean_word][selected_option]['count'] += 1
    
    # Calculate confidence score
    total_selections = sum(data['count'] for data in auto_data[clean_word].values())
    base_confidence = auto_data[clean_word][selected_option]['count'] / total_selections
    
    # Boost confidence for manual corrections
    confidence_multiplier = 1.5 if interaction_type == "manual_correction" else 1.0
    if interaction_type == "accept_all":
        confidence_multiplier = 1.2
    
    final_confidence = min(1.0, base_confidence * confidence_multiplier)
    auto_data[clean_word][selected_option]['confidence'] = final_confidence
    
    # Log the learning event locally
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "word": clean_word,
        "original_word": word_data.get('original'),
        "ipa_choice": selected_option,
        "interaction_type": interaction_type,
        "confidence": final_confidence,
        "selection_count": auto_data[clean_word][selected_option]['count'],
        "total_word_selections": total_selections
    }
    
    with open(AUTO_LEARN_FILE, "a", encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # Google Sheets logging
    if SHEETS_AVAILABLE and st.session_state.get('sheets_connected', False):
        try:
            st.session_state.sheets_history.log_word_learning(
                word_data, selected_option, interaction_type, 
                final_confidence, auto_data[clean_word][selected_option]['count'],
                st.session_state.session_id
            )
        except Exception as e:
            st.sidebar.error(f"Sheets logging failed: {str(e)}")
    
    # Auto-promote logic
    if (final_confidence >= st.session_state.confidence_threshold 
        and auto_data[clean_word][selected_option]['count'] >= 2):
        
        override_dict = {}
        if os.path.exists("override_dict.json"):
            try:
                with open("override_dict.json", "r", encoding='utf-8') as f:
                    override_dict = json.load(f)
            except:
                pass
        
        override_dict[clean_word] = selected_option
        
        with open("override_dict.json", "w", encoding='utf-8') as f:
            json.dump(override_dict, f, ensure_ascii=False, indent=2)
        
        return True
    
    return False

def get_enhanced_learning_stats():
    """Get enhanced learning statistics"""
    stats = {
        "total_interactions": 0,
        "unique_words": 0,
        "auto_promotions": 0,
        "manual_corrections": 0,
        "high_confidence_words": 0,
        "session_duration": 0,
        "learning_velocity": 0
    }
    
    # Local stats
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
    
    # Session stats
    session_duration = time.time() - st.session_state.session_start_time
    stats["session_duration"] = session_duration / 60  # Convert to minutes
    
    if session_duration > 0:
        stats["learning_velocity"] = stats["total_interactions"] / (session_duration / 60)
    
    # Override dictionary
    if os.path.exists("override_dict.json"):
        try:
            with open("override_dict.json", "r", encoding='utf-8') as f:
                override_dict = json.load(f)
                stats["auto_promotions"] = len(override_dict)
        except:
            pass
    
    return stats

# Main UI
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🇦🇺 Enhanced HCE IPA Transcriber")
    st.markdown("*Advanced Auto-Learning with Google Sheets Integration*")

with col2:
    with st.popover("⚙️ Settings"):
        st.session_state.auto_learn_enabled = st.toggle(
            "Auto-Learning Enabled", 
            value=st.session_state.auto_learn_enabled
        )
        
        st.session_state.confidence_threshold = st.slider(
            "Auto-Promote Threshold",
            min_value=0.5,
            max_value=1.0,
            value=st.session_state.confidence_threshold,
            step=0.1
        )
        
        # Google Sheets settings
        if SHEETS_AVAILABLE:
            st.markdown("**Google Sheets:**")
            if st.session_state.get('sheets_connected', False):
                st.success("✅ Connected")
                if st.button("Update Analytics", use_container_width=True):
                    st.session_state.sheets_history.update_daily_analytics()
                    st.success("Analytics updated!")
            else:
                st.error("❌ Not Connected")
                if st.button("Retry Connection", use_container_width=True):
                    st.session_state.sheets_connected = st.session_state.sheets_history.initialize_connection()
                    st.rerun()

# Input section
text = st.text_input("Enter Australian English text:", placeholder="e.g., I can't dance at the castle")

if text and text != st.session_state.current_text:
    st.session_state.current_text = text
    st.session_state.word_results = process_text(text)

# Word processing (same logic as original but with enhanced auto-learning)
if st.session_state.word_results:
    st.markdown("### Word-by-Word IPA Transcription:")
    
    word_words = [wr for wr in st.session_state.word_results if wr.get("original", "").replace("'", "").isalnum()]
    
    # Display logic (keeping your original layout logic)
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
                        label_visibility="collapsed"
                    )
                    st.session_state.word_results[word_idx]['selected'] = selected
                    
                    # Enhanced auto-learning on change
                    if st.session_state.auto_learn_enabled:
                        enhanced_auto_learn_from_selection(word_data, selected, "selection")
                else:
                    ipa_option = word_data.get('ipa_options', [''])[0]
                    st.code(ipa_option)
                    st.session_state.word_results[word_idx]['selected'] = ipa_option
                
                correction = st.text_input(
                    "Manual:",
                    key=f"correct_col_{word_idx}_{word_data['original']}",
                    placeholder="Custom IPA...",
                    label_visibility="collapsed"
                )
                st.session_state.word_results[word_idx]['correction'] = correction if correction else None
                
                # Enhanced auto-learning for corrections
                if correction and st.session_state.auto_learn_enabled:
                    enhanced_auto_learn_from_selection(word_data, correction, "manual_correction")
    
    # Similar logic for other layout cases...
    # [Include the rest of your layout logic here with enhanced_auto_learn_from_selection calls]
    
    # Show reconstructed sentence
    st.markdown("### Full Sentence IPA:")
    full_ipa = reconstruct_sentence(st.session_state.word_results)
    st.code(full_ipa, language=None)
    
    # Enhanced action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("✅ Accept All & Learn", use_container_width=True):
            start_time = time.time()
            auto_promotions = 0
            learned_words = []
            
            for word_data in st.session_state.word_results:
                if word_data.get("original", "").replace("'", "").isalnum():
                    final_choice = word_data.get('correction') or word_data.get('selected')
                    if final_choice:
                        was_promoted = enhanced_auto_learn_from_selection(word_data, final_choice, "accept_all")
                        if was_promoted:
                            auto_promotions += 1
                        learned_words.append(f"{word_data['original']} → {final_choice}")
            
            completion_time = time.time() - start_time
            
            # Local logging
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
            
            # Google Sheets logging
            if SHEETS_AVAILABLE and st.session_state.get('sheets_connected', False):
                try:
                    st.session_state.sheets_history.log_sentence_completion(
                        st.session_state.current_text, full_ipa, 
                        len(learned_words), auto_promotions,
                        st.session_state.session_id, completion_time
                    )
                except Exception as e:
                    st.sidebar.error(f"Sheets sentence logging failed: {str(e)}")
            
            if auto_promotions > 0:
                st.success(f"✅ Learned {len(learned_words)} words, auto-promoted {auto_promotions}!")
            else:
                st.success(f"✅ Learned {len(learned_words)} words")
    
    # [Include other buttons with similar enhancements]

# Enhanced sidebar with Google Sheets integration
with st.sidebar:
    st.markdown("### 🧠 Enhanced Learning Stats")
    
    stats = get_enhanced_learning_stats()
    
    # Basic stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Interactions", stats["total_interactions"])
        st.metric("Unique Words", stats["unique_words"])
        st.metric("Session Duration", f"{stats['session_duration']:.1f} min")
    
    with col2:
        st.metric("Auto-Promotions", stats["auto_promotions"])
        st.metric("Manual Corrections", stats["manual_corrections"])
        st.metric("Learning Velocity", f"{stats['learning_velocity']:.1f}/min")
    
    # Advanced metrics
    if stats["total_interactions"] > 0:
        efficiency = round((stats["auto_promotions"] / stats["total_interactions"]) * 100, 1)
        st.metric("Learning Efficiency", f"{efficiency}%")
        
        confidence_rate = round((stats["high_confidence_words"] / stats["total_interactions"]) * 100, 1)
        st.metric("High Confidence Rate", f"{confidence_rate}%")
    
    # Recent activity from local logs
    st.markdown("---")
    st.markdown("### 📈 Recent Local Activity")
    
    if os.path.exists(AUTO_LEARN_FILE):
        try:
            with open(AUTO_LEARN_FILE, "r", encoding='utf-8') as f:
                lines = f.readlines()
            
            recent_entries = []
            for line in lines[-5:]:
                entry = json.loads(line)
                recent_entries.append(entry)
            
            if recent_entries:
                for entry in reversed(recent_entries):
                    confidence = entry.get('confidence', 0)
                    confidence_color = "🟢" if confidence >= st.session_state.confidence_threshold else "🟡"
                    interaction_icon = "✏️" if entry.get('interaction_type') == 'manual_correction' else "👆"
                    
                    st.text(f"{confidence_color}{interaction_icon} {entry['word']} → {entry['ipa_choice']}")
                    st.caption(f"Confidence: {confidence:.2f} | {entry.get('interaction_type', 'selection')}")
        except Exception as e:
            st.error(f"Error reading recent activity: {str(e)}")

# Quick test examples (keeping your original)
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
                st.rerun()

# Setup instructions
with st.expander("⚙️ Google Sheets Setup Instructions"):
    st.markdown("""
    ### Setting up Google Sheets Integration:
    
    **Method 1: Using Streamlit Secrets (Recommended for deployment)**
    1. Create a Google Cloud Project and enable the Google Sheets API
    2. Create a Service Account and download the JSON credentials
    3. Add the credentials to your Streamlit secrets:
    ```toml
    # .streamlit/secrets.toml
    [gcp_service_account]
    type = "service_account"
    project_id = "your-project-id"
    private_key_id = "your-private-key-id"
    private_key = "-----BEGIN PRIVATE KEY-----\\nYOUR-PRIVATE-KEY\\n-----END PRIVATE KEY-----\\n"
    client_email = "your-service-account@your-project.iam.gserviceaccount.com"
    client_id = "your-client-id"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    ```
    
    **Method 2: Using Local Credentials File**
    1. Download your service account JSON file
    2. Place it in your project directory
    3. The app will automatically detect and use it
    
    **Required Packages:**
    ```
    pip install gspread google-auth google-auth-oauthlib google-auth-httplib2 pandas plotly
    ```
    
    **Spreadsheet Permissions:**
    - Share your Google Spreadsheet with the service account email
    - Give it "Editor" permissions
    """)

# Help section (enhanced)
with st.expander("ℹ️ Enhanced Auto-Learning Features"):
    st.markdown("""
    **🤖 Enhanced Automatic Learning:**
    
    1. **Multi-Platform Logging**: 
       - Local JSON files for immediate access
       - Google Sheets for cloud storage and analytics
       - Real-time synchronization between platforms
    
    2. **Advanced Analytics**: 
       - Learning velocity tracking
       - Confidence progression over time
       - Error pattern analysis
       - Session-based performance metrics
    
    3. **Intelligent Learning**:
       - Context-aware confidence scoring
       - Interaction type weighting (manual corrections get higher confidence)
       - Automatic pattern recognition for problematic words
    
    4. **Comprehensive Reporting**:
       - Interactive visualizations
       - Exportable learning reports
       - Progress tracking over time
       - Performance optimization insights
    
    **💡 Pro Tips:**
    - Connect Google Sheets for persistent learning across sessions
    - Use the dashboard to identify words that need more practice
    - Export reports to track long-term learning progress
    - The system learns your Australian English pronunciation preferences over time
    """)

# Footer with session info
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"Session ID: {st.session_state.get('session_id', 'Not set')}")
with col2:
    st.caption(f"Session Duration: {stats['session_duration']:.1f} minutes")
with col3:
    if SHEETS_AVAILABLE and st.session_state.get('sheets_connected', False):
        st.caption("🟢 Cloud sync enabled")
    else:
        st.caption("🔴 Local storage only")