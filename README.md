# 🇦🇺 Enhanced HCE IPA Transcriber

Advanced Australian English IPA transcriber with cloud-based learning analytics and Google Sheets integration.

## ✨ Features

### Core Functionality
- **Word-by-word IPA transcription** for Australian English (HCE dialect)
- **Auto-learning system** with confidence scoring
- **Manual corrections** with learning boost
- **Session tracking** and progress analytics

### Enhanced Features
- **Google Sheets integration** for cloud storage and analytics
- **Interactive dashboards** with learning progress visualization
- **Learning velocity tracking** and performance metrics
- **Data migration tools** for existing learning data
- **Export capabilities** (JSON, CSV formats)

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/ryrez/hce-ipa-transcriber-v2.git
cd hce-ipa-transcriber-v2

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

**Basic version (local storage only):**
```bash
streamlit run app.py
```

**Enhanced version (with Google Sheets support):**
```bash
streamlit run app_enhanced.py
```

## 📊 Google Sheets Setup (Optional)

### For Local Development

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Google Sheets API
   - Create Service Account and download JSON credentials

2. **Setup Credentials**
   ```bash
   # Rename your downloaded credentials file
   mv path/to/downloaded/credentials.json google_credentials.json
   ```

3. **Create Spreadsheet**
   - Create new Google Spreadsheet named "HCE_IPA_Learning_History"
   - Share with your service account email (Editor permissions)

### For Streamlit Cloud Deployment

Add your service account credentials in Streamlit Cloud secrets:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR-KEY\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

## 🛠️ Usage

1. **Enter Australian English text** in the input field
2. **Select IPA options** for each word or use auto-suggestions
3. **Make manual corrections** for improved learning
4. **Use "Accept All & Learn"** for batch processing
5. **Monitor progress** in sidebar analytics
6. **Export learning data** for backup or analysis

## 📁 Project Structure

```
hce-ipa-transcriber-v2/
├── app.py                          # Basic app (local storage)
├── app_enhanced.py                 # Enhanced app with Google Sheets
├── sheets_integration.py           # Google Sheets functionality
├── ipa_converter.py               # IPA conversion logic
├── overrides.py                   # Dictionary management
├── migration_script.py            # Data migration utilities
├── hce_map.json                   # HCE phoneme mappings
├── requirements.txt               # Dependencies
├── google_credentials_template.json # Credentials template
└── README.md                      # This file
```

## 🔧 Development

### Testing Migration Tools
```bash
# Analyze existing learning data
python migration_script.py --analyze-only

# Full migration (if you have data from previous version)
python migration_script.py
```

### Testing Google Sheets Connection
```bash
python -c "from sheets_integration import SheetsLearningHistory; print('✅ Import successful')"
```

## 🆘 Troubleshooting

### Common Issues

**Import Errors:**
```bash
pip install --upgrade gspread google-auth pandas plotly
```

**Google Sheets 403 Error:**
- Check service account has access to spreadsheet
- Verify credentials file is valid JSON

**Streamlit Errors:**
```bash
streamlit cache clear
```

## 🔒 Security

- Credentials files are excluded from git via `.gitignore`
- Use environment variables or Streamlit secrets for deployment
- Service accounts have minimal required permissions
- Local storage fallback when cloud unavailable

## 📈 Analytics Features

- **Learning velocity** tracking (words per minute/session)
- **Confidence progression** over time
- **Error pattern analysis** for problematic words
- **Interactive visualizations** with Plotly
- **Export capabilities** for data analysis

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for Australian English (HCE dialect) pronunciation learning
- Uses eSpeak NG for base IPA generation
- Enhanced with machine learning-based confidence scoring
- Designed for linguists, language learners, and educators