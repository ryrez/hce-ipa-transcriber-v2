import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go

class SheetsLearningHistory:
    """Enhanced learning history with Google Sheets integration"""
    
    def __init__(self, credentials_path: str = None, spreadsheet_name: str = "HCE_IPA_Learning_History"):
        self.spreadsheet_name = spreadsheet_name
        self.credentials_path = credentials_path
        self.gc = None
        self.spreadsheet = None
        self.worksheets = {}
        
        # Define worksheet structure
        self.sheet_configs = {
            'word_learning': {
                'headers': ['timestamp', 'word', 'original_word', 'ipa_choice', 'interaction_type', 
                           'confidence', 'selection_count', 'total_word_selections', 'session_id']
            },
            'sentence_history': {
                'headers': ['timestamp', 'text', 'full_ipa', 'word_count', 'auto_promotions', 
                           'session_id', 'completion_time_ms']
            },
            'learning_analytics': {
                'headers': ['date', 'total_interactions', 'unique_words_learned', 'auto_promotions',
                           'avg_confidence', 'learning_velocity', 'session_count']
            },
            'error_patterns': {
                'headers': ['timestamp', 'word', 'original_choice', 'corrected_choice', 
                           'error_type', 'frequency', 'last_seen']
            }
        }
        
    # Replace the initialize_connection method in your sheets_integration.py

    def initialize_connection(self) -> bool:
        """Initialize Google Sheets connection"""
        try:
            # First try local credentials file
            if os.path.exists("google_credentials.json"):
                scope = [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds = Credentials.from_service_account_file("google_credentials.json", scopes=scope)
                self.gc = gspread.authorize(creds)
                print("✅ Using local google_credentials.json")
            
            # Fallback to Streamlit secrets
            elif hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
                scope = [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"
                ]
                credentials_dict = dict(st.secrets["gcp_service_account"])
                creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
                self.gc = gspread.authorize(creds)
                print("✅ Using Streamlit secrets")
            
            else:
                print("❌ No Google credentials found")
                st.warning("Google Sheets credentials not found. Using local storage only.")
                return False
            
            # Open or create spreadsheet
            try:
                self.spreadsheet = self.gc.open(self.spreadsheet_name)
                print(f"✅ Opened existing spreadsheet: {self.spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                self.spreadsheet = self.gc.create(self.spreadsheet_name)
                print(f"✅ Created new spreadsheet: {self.spreadsheet_name}")
                # Make it accessible
                self.spreadsheet.share('', perm_type='anyone', role='reader')
            
            # Initialize worksheets
            self._setup_worksheets()
            print("✅ Worksheets initialized")
            return True
            
        except Exception as e:
            print(f"❌ Google Sheets connection failed: {str(e)}")
            st.error(f"Failed to connect to Google Sheets: {str(e)}")
            return False
        
    def _setup_worksheets(self):
        """Setup required worksheets with proper headers"""
        for sheet_name, config in self.sheet_configs.items():
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                self.worksheets[sheet_name] = worksheet
            except gspread.WorksheetNotFound:
                # Create new worksheet
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name, 
                    rows=1000, 
                    cols=len(config['headers'])
                )
                # Add headers
                worksheet.update('1:1', [config['headers']])
                self.worksheets[sheet_name] = worksheet
    
    def log_word_learning(self, word_data: Dict, selected_option: str, 
                         interaction_type: str, confidence: float, 
                         selection_count: int, session_id: str):
        """Log individual word learning event"""
        if not self.gc:
            return
            
        try:
            worksheet = self.worksheets['word_learning']
            row_data = [
                datetime.now().isoformat(),
                word_data.get('clean', ''),
                word_data.get('original', ''),
                selected_option,
                interaction_type,
                confidence,
                selection_count,
                word_data.get('total_selections', 1),
                session_id
            ]
            worksheet.append_row(row_data)
            
        except Exception as e:
            st.error(f"Failed to log to Google Sheets: {str(e)}")
    
    def log_sentence_completion(self, text: str, full_ipa: str, 
                               word_count: int, auto_promotions: int,
                               session_id: str, completion_time: float):
        """Log sentence completion event"""
        if not self.gc:
            return
            
        try:
            worksheet = self.worksheets['sentence_history']
            row_data = [
                datetime.now().isoformat(),
                text,
                full_ipa,
                word_count,
                auto_promotions,
                session_id,
                int(completion_time * 1000)  # Convert to milliseconds
            ]
            worksheet.append_row(row_data)
            
        except Exception as e:
            st.error(f"Failed to log sentence to Google Sheets: {str(e)}")
    
    def update_daily_analytics(self):
        """Update daily learning analytics"""
        if not self.gc:
            return
            
        try:
            # Get today's data from word_learning sheet
            worksheet = self.worksheets['word_learning']
            records = worksheet.get_all_records()
            
            today = datetime.now().date()
            today_records = [r for r in records if datetime.fromisoformat(r['timestamp']).date() == today]
            
            if not today_records:
                return
            
            # Calculate analytics
            analytics = {
                'date': today.isoformat(),
                'total_interactions': len(today_records),
                'unique_words_learned': len(set(r['word'] for r in today_records)),
                'auto_promotions': len([r for r in today_records if r['confidence'] >= 0.7]),
                'avg_confidence': sum(r['confidence'] for r in today_records) / len(today_records),
                'learning_velocity': len(today_records) / max(1, len(set(r['session_id'] for r in today_records))),
                'session_count': len(set(r['session_id'] for r in today_records))
            }
            
            # Update analytics sheet
            analytics_sheet = self.worksheets['learning_analytics']
            
            # Check if today's record exists
            existing_records = analytics_sheet.get_all_records()
            today_exists = any(r['date'] == today.isoformat() for r in existing_records)
            
            if today_exists:
                # Update existing record
                for i, record in enumerate(existing_records, 2):  # Start from row 2 (after headers)
                    if record['date'] == today.isoformat():
                        analytics_sheet.update(f'A{i}:G{i}', [list(analytics.values())])
                        break
            else:
                # Add new record
                analytics_sheet.append_row(list(analytics.values()))
                
        except Exception as e:
            st.error(f"Failed to update analytics: {str(e)}")
    
    def get_learning_dashboard_data(self, days: int = 30) -> Dict:
        """Get comprehensive learning data for dashboard"""
        if not self.gc:
            return {}
        
        try:
            # Get word learning data
            word_records = self.worksheets['word_learning'].get_all_records()
            analytics_records = self.worksheets['learning_analytics'].get_all_records()
            sentence_records = self.worksheets['sentence_history'].get_all_records()
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_words = [r for r in word_records 
                           if datetime.fromisoformat(r['timestamp']) >= cutoff_date]
            recent_analytics = [r for r in analytics_records 
                              if datetime.fromisoformat(r['date']) >= cutoff_date.date()]
            recent_sentences = [r for r in sentence_records 
                              if datetime.fromisoformat(r['timestamp']) >= cutoff_date]
            
            return {
                'word_learning': recent_words,
                'daily_analytics': recent_analytics,
                'sentence_history': recent_sentences,
                'summary': self._calculate_summary_stats(recent_words, recent_analytics)
            }
            
        except Exception as e:
            st.error(f"Failed to get dashboard data: {str(e)}")
            return {}
    
    def _calculate_summary_stats(self, word_data: List, analytics_data: List) -> Dict:
        """Calculate summary statistics"""
        if not word_data:
            return {}
        
        total_interactions = len(word_data)
        unique_words = len(set(r['word'] for r in word_data))
        high_confidence = len([r for r in word_data if r['confidence'] >= 0.7])
        
        # Learning progression
        word_confidence_over_time = {}
        for record in word_data:
            word = record['word']
            if word not in word_confidence_over_time:
                word_confidence_over_time[word] = []
            word_confidence_over_time[word].append({
                'timestamp': record['timestamp'],
                'confidence': record['confidence']
            })
        
        # Calculate learning velocity (words learned per day)
        if analytics_data:
            avg_daily_velocity = sum(r['learning_velocity'] for r in analytics_data) / len(analytics_data)
        else:
            avg_daily_velocity = 0
        
        return {
            'total_interactions': total_interactions,
            'unique_words': unique_words,
            'high_confidence_rate': high_confidence / total_interactions if total_interactions else 0,
            'avg_daily_velocity': avg_daily_velocity,
            'word_progression': word_confidence_over_time
        }
    
    def export_learning_report(self, format_type: str = 'json') -> str:
        """Export comprehensive learning report"""
        if not self.gc:
            return ""
        
        try:
            dashboard_data = self.get_learning_dashboard_data(days=90)  # 3 months
            
            if format_type == 'json':
                return json.dumps(dashboard_data, indent=2, ensure_ascii=False)
            elif format_type == 'csv':
                # Convert to CSV format
                df = pd.DataFrame(dashboard_data['word_learning'])
                return df.to_csv(index=False)
            else:
                return str(dashboard_data)
                
        except Exception as e:
            return f"Export failed: {str(e)}"

def create_learning_visualizations(dashboard_data: Dict):
    """Create interactive visualizations for learning progress"""
    if not dashboard_data:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily learning progress
        if dashboard_data.get('daily_analytics'):
            df_analytics = pd.DataFrame(dashboard_data['daily_analytics'])
            df_analytics['date'] = pd.to_datetime(df_analytics['date'])
            
            fig = px.line(df_analytics, x='date', y='total_interactions',
                         title='Daily Learning Interactions',
                         labels={'total_interactions': 'Interactions', 'date': 'Date'})
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Confidence distribution
        if dashboard_data.get('word_learning'):
            df_words = pd.DataFrame(dashboard_data['word_learning'])
            
            fig = px.histogram(df_words, x='confidence', bins=20,
                             title='Confidence Score Distribution',
                             labels={'confidence': 'Confidence Score', 'count': 'Word Count'})
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # Word learning progression heatmap
    if dashboard_data.get('summary', {}).get('word_progression'):
        progression = dashboard_data['summary']['word_progression']
        
        # Create heatmap data
        heatmap_data = []
        for word, history in progression.items():
            for entry in history:
                heatmap_data.append({
                    'word': word,
                    'date': datetime.fromisoformat(entry['timestamp']).date(),
                    'confidence': entry['confidence']
                })
        
        if heatmap_data:
            df_heatmap = pd.DataFrame(heatmap_data)
            
            # Top 20 most practiced words
            word_counts = df_heatmap['word'].value_counts().head(20)
            df_filtered = df_heatmap[df_heatmap['word'].isin(word_counts.index)]
            
            fig = px.scatter(df_filtered, x='date', y='word', 
                           size='confidence', color='confidence',
                           title='Word Learning Progression Over Time',
                           color_continuous_scale='Viridis')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

# Integration function for your existing app
def integrate_sheets_learning(existing_auto_learn_function):
    """Wrapper to integrate Google Sheets with existing auto-learning"""
    
    # Initialize sheets integration
    if 'sheets_history' not in st.session_state:
        st.session_state.sheets_history = SheetsLearningHistory()
        st.session_state.sheets_connected = st.session_state.sheets_history.initialize_connection()
    
    # Session ID for tracking
    if 'session_id' not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def enhanced_auto_learn(word_data, selected_option, interaction_type="selection"):
        """Enhanced auto-learning with Google Sheets logging"""
        
        # Call original function
        result = existing_auto_learn_function(word_data, selected_option, interaction_type)
        
        # Additional Google Sheets logging
        if st.session_state.sheets_connected:
            # Calculate confidence and selection count (simplified)
            confidence = 0.8 if interaction_type == "manual_correction" else 0.6
            selection_count = 1
            
            st.session_state.sheets_history.log_word_learning(
                word_data, selected_option, interaction_type, 
                confidence, selection_count, st.session_state.session_id
            )
        
        return result
    
    return enhanced_auto_learn

# Requirements for Google Sheets integration
ADDITIONAL_REQUIREMENTS = """
# Add these to your requirements.txt:
gspread>=5.7.0
google-auth>=2.16.0
google-auth-oauthlib>=0.8.0
google-auth-httplib2>=0.1.0
pandas>=1.5.0
plotly>=5.10.0
"""