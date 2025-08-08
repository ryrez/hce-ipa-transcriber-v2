from pathlib import Path

# Create the user_guide.md file with the full guide content
guide_md = """
# 🎯 HCE IPA Transcriber User Guide

## Welcome to the HCE IPA Transcriber! 
This tool converts text into IPA (International Phonetic Alphabet) transcription using the **HCE (Harmonized Consonant Enhancement)** system - perfect for linguistics research, language learning, and phonetic analysis.

---

## 🚀 Quick Start Guide

### Step 1: Enter Your Text
- Type or paste any text into the input box
- Works with single words, sentences, or entire paragraphs
- Supports multiple languages and mixed content

### Step 2: Choose Your Settings
- **Processing Mode**: Select how you want words processed
- **Display Options**: Choose what information to show
- **Export Format**: Pick your preferred output format

### Step 3: Get Your Results
- Click **"Transcribe"** to process your text
- View results instantly with detailed analysis
- Export or copy results as needed

---

## 📊 Understanding Your Results

### 🎯 Main Metrics Explained

#### **Accuracy Score** 
- **What it is**: How confident the system is in the transcription
- **Range**: 0-100%
- **Good**: 85%+ means high confidence
- **Fair**: 70-84% means moderate confidence  
- **Check**: <70% may need manual review

#### **Processing Time**
- **What it is**: How long it took to transcribe your text
- **Typical**: 0.1-2.0 seconds for most texts
- **Longer texts**: May take more time but usually under 5 seconds

#### **Word Count Statistics**
- **Total Words**: Number of words processed
- **Successfully Transcribed**: Words with confident IPA output
- **Needs Review**: Words that may need manual checking
- **Unknown/Skipped**: Words not in the phonetic database

---

## 🔧 Features & Tools

### **Text Processing**
- ✅ **Smart Word Detection**: Automatically identifies word boundaries
- ✅ **Punctuation Handling**: Preserves punctuation and formatting
- ✅ **Mixed Language Support**: Handles multilingual text
- ✅ **Special Characters**: Processes numbers, abbreviations, etc.

### **IPA Output Options**
- 📝 **Standard IPA**: Traditional International Phonetic Alphabet
- 🎯 **HCE Enhanced**: Harmonized Consonant Enhancement system
- 📊 **Detailed Analysis**: Word-by-word breakdown with confidence scores
- 📋 **Clean Copy**: Simple IPA output for easy copying

### **Export & Sharing**
- 💾 **Multiple Formats**: Plain text, CSV, JSON
- 📊 **Analysis Reports**: Detailed statistics and metrics
- 🔗 **Shareable Links**: Save and share your transcriptions
- 📋 **Copy to Clipboard**: One-click copying

---

## 🎓 How to Read IPA Symbols

### Common IPA Symbols
| Symbol | Sound | Example Word | 
|--------|--------|-------------|
| /θ/ | "th" in "think" | θɪŋk |
| /ð/ | "th" in "that" | ðæt |
| /ʃ/ | "sh" in "ship" | ʃɪp |
| /ʒ/ | "s" in "measure" | ˈmɛʒər |
| /tʃ/ | "ch" in "chair" | tʃɛr |
| /dʒ/ | "j" in "judge" | dʒʌdʒ |
| /ŋ/ | "ng" in "sing" | sɪŋ |

### Stress Marks
- **ˈ** = Primary stress (main emphasis)
- **ˌ** = Secondary stress (lighter emphasis)
- No mark = Unstressed syllable

---

## 💡 Tips for Best Results

### **Input Tips**
- ✅ Use clear, standard spelling
- ✅ One sentence per line for better processing
- ✅ Avoid excessive punctuation or special formatting
- ⚠️ Very technical terms may need manual review

### **Understanding Confidence**
- **High (85%+)**: Trust the transcription
- **Medium (70-84%)**: Generally reliable, double-check if critical
- **Low (<70%)**: Manual review recommended

### **When to Review Results**
- Proper names and foreign words
- Technical or specialized terminology  
- Very short function words (a, the, to)
- Words with multiple possible pronunciations

---

## 🛠️ Advanced Features

### **Override Dictionary**
- Add your own pronunciation rules
- Perfect for specialized vocabulary
- Saves time on repeated technical terms

### **Batch Processing**
- Upload text files for bulk processing
- Great for research projects
- Maintains formatting and structure

### **Analysis Tools**
- Phoneme frequency analysis
- Syllable structure breakdown
- Stress pattern identification
- Sound change tracking

---

## 📚 Use Cases

### **For Linguists**
- Phonetic research and analysis
- Dialect comparison studies
- Sound change documentation
- Academic paper preparation

### **For Language Learners**
- Pronunciation practice
- Understanding accent differences  
- Learning phonetic transcription
- Comparing languages

### **For Educators**
- Creating pronunciation guides
- Teaching phonetics courses
- Student assessment tools
- Curriculum development

### **For Researchers**
- Speech therapy applications
- Accent analysis studies
- Language acquisition research
- Computational linguistics

---

## 🔍 Troubleshooting

### **Common Issues**
❓ **"Word not transcribed"**
- Check spelling
- Try adding to override dictionary
- Some proper names may not be in database

❓ **"Low confidence score"**
- Word may have multiple pronunciations
- Consider context when using
- Manual verification recommended

❓ **"Processing taking too long"**
- Large texts may take time
- Try breaking into smaller chunks
- Check internet connection

### **Getting Help**
- 📧 Use the feedback form for questions
- 🐛 Report bugs or issues
- 💡 Suggest new features
- 📖 Check the FAQ section

---

## 🎯 Quick Reference Card

| Task | Steps | Result |
|------|-------|--------|
| **Basic Transcription** | Enter text → Click Transcribe | IPA output |
| **High Accuracy** | Use clear text → Check confidence | Reliable IPA |
| **Batch Process** | Upload file → Select options | Bulk results |
| **Export Results** | Choose format → Download | Saved file |
| **Add Custom Word** | Go to Override → Add entry | Personal dictionary |

---

## 🚀 Ready to Start?

1. **Enter your text** in the main input area  
2. **Select your preferences** from the sidebar  
3. **Click "Transcribe"** and watch the magic happen!  
4. **Review your results** and export as needed

---

## 📋 System Information

**Version**: 2.0  
**Last Updated**: August 2025  
**Supported Languages**: English (primary), with multilingual support  
**Technology**: Streamlit + Python + HCE Algorithm  
**Status**: ✅ Fully Operational
"""

# Write to user_guide.md
guide_path = Path("user_guide.md")
guide_path.write_text(guide_md.strip(), encoding="utf-8")

guide_path.exists()

