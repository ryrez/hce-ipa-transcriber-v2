#!/usr/bin/env python3
"""
HCE IPA Transcriber - Data Migration Script
Migrates existing local learning data to Google Sheets format
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

def migrate_local_to_sheets_format(
    auto_learn_file: str = "auto_learning_log.jsonl",
    corrections_file: str = "corrections_log.jsonl",
    output_dir: str = "migration_output"
) -> Dict[str, str]:
    """
    Migrate existing local JSONL files to Google Sheets compatible format
    
    Returns paths to generated CSV files for manual upload if needed
    """
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    migration_results = {}
    word_learning_data = []
    
    # 1. Migrate auto_learning_log.jsonl to word_learning format
    if os.path.exists(auto_learn_file):
        try:
            with open(auto_learn_file, "r", encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        
                        # Convert to new format
                        migrated_entry = {
                            'timestamp': entry.get('timestamp', datetime.now().isoformat()),
                            'word': entry.get('word', ''),
                            'original_word': entry.get('original_word', entry.get('word', '')),
                            'ipa_choice': entry.get('ipa_choice', ''),
                            'interaction_type': entry.get('interaction_type', 'selection'),
                            'confidence': entry.get('confidence', 0.5),
                            'selection_count': entry.get('selection_count', 1),
                            'total_word_selections': entry.get('total_word_selections', 1),
                            'session_id': entry.get('session_id', f"migrated_{datetime.fromisoformat(entry.get('timestamp', datetime.now().isoformat())).strftime('%Y%m%d')}")
                        }
                        word_learning_data.append(migrated_entry)
            
            # Save as CSV
            if word_learning_data:
                df = pd.DataFrame(word_learning_data)
                word_learning_path = os.path.join(output_dir, "word_learning_migrated.csv")
                df.to_csv(word_learning_path, index=False)
                migration_results['word_learning'] = word_learning_path
                print(f"✅ Migrated {len(word_learning_data)} word learning entries")
        
        except Exception as e:
            print(f"❌ Error migrating auto_learning_log.jsonl: {str(e)}")
    
    # 2. Migrate corrections_log.jsonl to sentence_history format
    if os.path.exists(corrections_file):
        sentence_history_data = []
        
        try:
            with open(corrections_file, "r", encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        
                        # Only migrate sentence-level entries
                        if entry.get('type') in ['sentence', 'sentence_accept_all']:
                            migrated_entry = {
                                'timestamp': entry.get('timestamp', datetime.now().isoformat()),
                                'text': entry.get('text', ''),
                                'full_ipa': entry.get('full_ipa', ''),
                                'word_count': entry.get('word_count', 0),
                                'auto_promotions': entry.get('auto_promotions', entry.get('corrections_count', 0)),
                                'session_id': f"migrated_{datetime.fromisoformat(entry.get('timestamp', datetime.now().isoformat())).strftime('%Y%m%d')}",
                                'completion_time_ms': 1000  # Default 1 second for migrated data
                            }
                            sentence_history_data.append(migrated_entry)
            
            # Save as CSV
            if sentence_history_data:
                df = pd.DataFrame(sentence_history_data)
                sentence_history_path = os.path.join(output_dir, "sentence_history_migrated.csv")
                df.to_csv(sentence_history_path, index=False)
                migration_results['sentence_history'] = sentence_history_path
                print(f"✅ Migrated {len(sentence_history_data)} sentence history entries")
        
        except Exception as e:
            print(f"❌ Error migrating corrections_log.jsonl: {str(e)}")
    
    # 3. Generate analytics summary from migrated data
    if word_learning_data:
        analytics_data = generate_analytics_from_migrated_data(word_learning_data)
        if analytics_data:
            df = pd.DataFrame(analytics_data)
            analytics_path = os.path.join(output_dir, "learning_analytics_migrated.csv")
            df.to_csv(analytics_path, index=False)
            migration_results['learning_analytics'] = analytics_path
            print(f"✅ Generated analytics for {len(analytics_data)} days")
    
    return migration_results

def generate_analytics_from_migrated_data(word_learning_data: List[Dict]) -> List[Dict]:
    """Generate daily analytics from word learning data"""
    
    # Group by date
    daily_data = {}
    
    for entry in word_learning_data:
        try:
            date = datetime.fromisoformat(entry['timestamp']).date()
            date_str = date.isoformat()
            
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'interactions': [],
                    'words': set(),
                    'sessions': set(),
                    'confidences': []
                }
            
            daily_data[date_str]['interactions'].append(entry)
            daily_data[date_str]['words'].add(entry['word'])
            daily_data[date_str]['sessions'].add(entry['session_id'])
            daily_data[date_str]['confidences'].append(entry['confidence'])
        
        except Exception as e:
            print(f"Warning: Could not process entry for analytics: {str(e)}")
            continue
    
    # Calculate analytics
    analytics = []
    for date_str, data in daily_data.items():
        avg_confidence = sum(data['confidences']) / len(data['confidences']) if data['confidences'] else 0
        session_count = len(data['sessions'])
        learning_velocity = len(data['interactions']) / session_count if session_count > 0 else 0
        
        analytics.append({
            'date': date_str,
            'total_interactions': len(data['interactions']),
            'unique_words_learned': len(data['words']),
            'auto_promotions': len([i for i in data['interactions'] if i['confidence'] >= 0.7]),
            'avg_confidence': round(avg_confidence, 3),
            'learning_velocity': round(learning_velocity, 2),
            'session_count': session_count
        })
    
    # Sort by date
    analytics.sort(key=lambda x: x['date'])
    return analytics

def create_migration_summary(migration_results: Dict[str, str]) -> str:
    """Create a summary report of the migration process"""
    
    summary = {
        "migration_timestamp": datetime.now().isoformat(),
        "files_processed": list(migration_results.keys()),
        "output_files": migration_results,
        "status": "completed" if migration_results else "no_data_found"
    }
    
    # Count records in each migrated file
    record_counts = {}
    for sheet_type, file_path in migration_results.items():
        try:
            df = pd.read_csv(file_path)
            record_counts[sheet_type] = len(df)
        except Exception as e:
            record_counts[sheet_type] = f"Error reading: {str(e)}"
    
    summary["record_counts"] = record_counts
    
    # Generate human-readable summary
    summary_text = f"""
# HCE IPA Transcriber - Migration Summary

**Migration completed at:** {summary['migration_timestamp']}

## Files Processed
{chr(10).join(f"- {file}" for file in summary['files_processed'])}

## Generated Output Files
{chr(10).join(f"- {sheet}: {path} ({record_counts.get(sheet, 0)} records)" for sheet, path in migration_results.items())}

## Next Steps
1. Upload CSV files to your Google Sheets manually, OR
2. Run the enhanced app - it will automatically sync this data
3. Verify data integrity in Google Sheets
4. Archive original JSONL files as backup

## Migration Statistics
- Total data types migrated: {len(migration_results)}
- Total records processed: {sum(count for count in record_counts.values() if isinstance(count, int))}
- Success rate: {len([c for c in record_counts.values() if isinstance(c, int)]) / len(record_counts) * 100:.1f}%
"""
    
    return summary_text

def validate_migrated_data(migration_results: Dict[str, str]) -> Dict[str, bool]:
    """Validate the migrated data for completeness and integrity"""
    
    validation_results = {}
    
    for sheet_type, file_path in migration_results.items():
        try:
            df = pd.read_csv(file_path)
            
            # Basic validation checks
            checks = {
                'file_exists': os.path.exists(file_path),
                'has_data': len(df) > 0,
                'has_required_columns': True,
                'timestamps_valid': True,
                'no_null_critical_fields': True
            }
            
            # Check required columns based on sheet type
            required_columns = {
                'word_learning': ['timestamp', 'word', 'ipa_choice', 'confidence'],
                'sentence_history': ['timestamp', 'text', 'full_ipa'],
                'learning_analytics': ['date', 'total_interactions', 'unique_words_learned']
            }
            
            if sheet_type in required_columns:
                missing_cols = set(required_columns[sheet_type]) - set(df.columns)
                checks['has_required_columns'] = len(missing_cols) == 0
                if missing_cols:
                    print(f"⚠️  {sheet_type}: Missing columns {missing_cols}")
            
            # Validate timestamps
            try:
                if 'timestamp' in df.columns:
                    pd.to_datetime(df['timestamp'])
                elif 'date' in df.columns:
                    pd.to_datetime(df['date'])
            except Exception:
                checks['timestamps_valid'] = False
                print(f"⚠️  {sheet_type}: Invalid timestamp format")
            
            # Check for critical null values
            critical_fields = ['word', 'ipa_choice'] if sheet_type == 'word_learning' else ['text']
            for field in critical_fields:
                if field in df.columns and df[field].isnull().any():
                    checks['no_null_critical_fields'] = False
                    print(f"⚠️  {sheet_type}: Null values in {field}")
            
            validation_results[sheet_type] = all(checks.values())
            
            if validation_results[sheet_type]:
                print(f"✅ {sheet_type}: Validation passed ({len(df)} records)")
            else:
                print(f"❌ {sheet_type}: Validation failed")
                for check, result in checks.items():
                    if not result:
                        print(f"   - {check}: FAILED")
        
        except Exception as e:
            validation_results[sheet_type] = False
            print(f"❌ {sheet_type}: Validation error - {str(e)}")
    
    return validation_results

def create_backup_script() -> str:
    """Generate a backup script for regular data archiving"""
    
    backup_script = '''#!/usr/bin/env python3
"""
HCE IPA Transcriber - Automated Backup Script
Run this weekly/monthly to backup your learning data
"""

import os
import shutil
from datetime import datetime
import json

def create_backup():
    """Create timestamped backup of all learning data"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/hce_backup_{timestamp}"
    
    os.makedirs(backup_dir, exist_ok=True)
    
    # Files to backup
    files_to_backup = [
        "auto_learning_log.jsonl",
        "corrections_log.jsonl", 
        "override_dict.json",
        "hce_map.json"
    ]
    
    backed_up = []
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            backed_up.append(file)
    
    # Create backup manifest
    manifest = {
        "backup_timestamp": datetime.now().isoformat(),
        "files_backed_up": backed_up,
        "backup_directory": backup_dir
    }
    
    with open(os.path.join(backup_dir, "backup_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Backup created: {backup_dir}")
    print(f"📁 Files backed up: {len(backed_up)}")
    
    return backup_dir

if __name__ == "__main__":
    create_backup()
'''
    
    return backup_script

def run_full_migration():
    """Complete migration workflow"""
    
    print("🚀 Starting HCE IPA Transcriber Data Migration...")
    print("=" * 50)
    
    # Step 1: Check for existing data
    auto_learn_exists = os.path.exists("auto_learning_log.jsonl")
    corrections_exists = os.path.exists("corrections_log.jsonl")
    
    if not auto_learn_exists and not corrections_exists:
        print("ℹ️  No existing learning data found. Migration not needed.")
        return
    
    print(f"📋 Found existing data:")
    if auto_learn_exists:
        with open("auto_learning_log.jsonl", "r") as f:
            auto_count = len(f.readlines())
        print(f"   - auto_learning_log.jsonl: {auto_count} entries")
    
    if corrections_exists:
        with open("corrections_log.jsonl", "r") as f:
            corrections_count = len(f.readlines())
        print(f"   - corrections_log.jsonl: {corrections_count} entries")
    
    # Step 2: Run migration
    print("\n🔄 Running migration...")
    migration_results = migrate_local_to_sheets_format()
    
    # Step 3: Validate migrated data
    print("\n🔍 Validating migrated data...")
    validation_results = validate_migrated_data(migration_results)
    
    # Step 4: Generate summary
    summary = create_migration_summary(migration_results)
    
    # Save summary
    with open("migration_output/migration_summary.md", "w", encoding='utf-8') as f:
        f.write(summary)
    
    # Step 5: Generate backup script
    backup_script = create_backup_script()
    with open("create_backup.py", "w", encoding='utf-8') as f:
        f.write(backup_script)
    
    print("\n" + "=" * 50)
    print("🎉 Migration completed!")
    print(f"📁 Output directory: migration_output/")
    print(f"📄 Summary report: migration_output/migration_summary.md")
    print(f"💾 Backup script generated: create_backup.py")
    
    # Final recommendations
    print("\n📋 Next Steps:")
    print("1. Review the generated CSV files in migration_output/")
    print("2. Set up Google Sheets integration using the setup guide")
    print("3. Run the enhanced app - it will automatically use the new format")
    print("4. Use create_backup.py for regular backups")
    
    if all(validation_results.values()):
        print("✅ All validations passed - data is ready for Google Sheets!")
    else:
        print("⚠️  Some validation issues found - check the logs above")
    
    return migration_results, validation_results

# Utility functions for data analysis
def analyze_learning_patterns(auto_learn_file: str = "auto_learning_log.jsonl") -> Dict:
    """Analyze existing learning patterns for insights"""
    
    if not os.path.exists(auto_learn_file):
        return {}
    
    analysis = {
        "word_frequency": {},
        "interaction_types": {},
        "confidence_distribution": [],
        "learning_timeline": [],
        "problem_words": []
    }
    
    try:
        with open(auto_learn_file, "r", encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    
                    # Word frequency
                    word = entry.get('word', '')
                    analysis["word_frequency"][word] = analysis["word_frequency"].get(word, 0) + 1
                    
                    # Interaction types
                    interaction = entry.get('interaction_type', 'unknown')
                    analysis["interaction_types"][interaction] = analysis["interaction_types"].get(interaction, 0) + 1
                    
                    # Confidence distribution
                    confidence = entry.get('confidence', 0)
                    analysis["confidence_distribution"].append(confidence)
                    
                    # Timeline
                    analysis["learning_timeline"].append({
                        'timestamp': entry.get('timestamp'),
                        'word': word,
                        'confidence': confidence
                    })
        
        # Identify problem words (high frequency, low confidence)
        for word, frequency in analysis["word_frequency"].items():
            if frequency > 2:  # Practiced multiple times
                word_entries = [e for e in analysis["learning_timeline"] if e['word'] == word]
                avg_confidence = sum(e['confidence'] for e in word_entries) / len(word_entries)
                
                if avg_confidence < 0.6:  # Low average confidence
                    analysis["problem_words"].append({
                        'word': word,
                        'frequency': frequency,
                        'avg_confidence': avg_confidence
                    })
        
        # Sort problem words by frequency
        analysis["problem_words"].sort(key=lambda x: x['frequency'], reverse=True)
        
    except Exception as e:
        print(f"Analysis error: {str(e)}")
    
    return analysis

def generate_learning_insights_report(analysis: Dict) -> str:
    """Generate human-readable insights from learning pattern analysis"""
    
    if not analysis:
        return "No learning data available for analysis."
    
    report = f"""
# HCE IPA Learning Insights Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Learning Overview

### Vocabulary Statistics
- **Total unique words practiced:** {len(analysis.get('word_frequency', {}))}
- **Total learning interactions:** {sum(analysis.get('word_frequency', {}).values())}
- **Average confidence score:** {sum(analysis.get('confidence_distribution', [0])) / len(analysis.get('confidence_distribution', [1])):.3f}

### Interaction Breakdown
"""
    
    for interaction_type, count in analysis.get('interaction_types', {}).items():
        percentage = count / sum(analysis['interaction_types'].values()) * 100
        report += f"- **{interaction_type.replace('_', ' ').title()}:** {count} ({percentage:.1f}%)\n"
    
    # Most practiced words
    if analysis.get('word_frequency'):
        top_words = sorted(analysis['word_frequency'].items(), key=lambda x: x[1], reverse=True)[:10]
        report += f"""

### Most Practiced Words
"""
        for word, count in top_words:
            report += f"- **{word}:** {count} times\n"
    
    # Problem words analysis
    if analysis.get('problem_words'):
        report += f"""

### Words Needing Attention
These words have been practiced multiple times but still have low confidence scores:

"""
        for word_info in analysis['problem_words'][:5]:
            report += f"- **{word_info['word']}:** {word_info['frequency']} attempts, {word_info['avg_confidence']:.2f} confidence\n"
    
    # Recommendations
    report += f"""

## Recommendations

### Immediate Actions
1. **Focus practice** on the words listed in "Words Needing Attention"
2. **Use manual corrections** more frequently for problem words (gets 1.5x confidence boost)
3. **Set up Google Sheets integration** for better long-term tracking

### Learning Strategy
- Words with < 0.6 confidence need targeted practice
- Manual corrections are more effective than repeated selections
- Batch learning with "Accept All" is efficient for familiar words

### Technical Improvements
- Consider adjusting confidence threshold based on your learning speed
- Enable Google Sheets for cross-device learning continuity
- Regular backups recommended for data preservation
"""
    
    return report

# Main execution
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate HCE IPA learning data")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze existing data")
    parser.add_argument("--output-dir", default="migration_output", help="Output directory for migrated files")
    
    args = parser.parse_args()
    
    if args.analyze_only:
        # Just analyze existing learning patterns
        print("🔍 Analyzing existing learning patterns...")
        analysis = analyze_learning_patterns()
        
        if analysis:
            insights = generate_learning_insights_report(analysis)
            
            os.makedirs(args.output_dir, exist_ok=True)
            with open(f"{args.output_dir}/learning_insights.md", "w", encoding='utf-8') as f:
                f.write(insights)
            
            print(f"📊 Learning insights saved to: {args.output_dir}/learning_insights.md")
            
            # Print quick summary
            print(f"\n📈 Quick Stats:")
            print(f"   Unique words: {len(analysis.get('word_frequency', {}))}")
            print(f"   Total interactions: {sum(analysis.get('word_frequency', {}).values())}")
            print(f"   Problem words: {len(analysis.get('problem_words', []))}")
        else:
            print("ℹ️  No learning data found to analyze")
    
    else:
        # Full migration
        try:
            migration_results, validation_results = run_full_migration()
            
            # Also generate insights
            analysis = analyze_learning_patterns()
            if analysis:
                insights = generate_learning_insights_report(analysis)
                with open("migration_output/learning_insights.md", "w", encoding='utf-8') as f:
                    f.write(insights)
                print("📊 Learning insights also generated!")
            
        except KeyboardInterrupt:
            print("\n⏹️  Migration cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Migration failed: {str(e)}")
            sys.exit(1)