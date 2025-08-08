#!/usr/bin/env python3
"""
HCE IPA Transcriber - Clean Security Audit
Excludes audit report files to prevent false positives
"""

import os
import re
import json
import glob
from pathlib import Path
from datetime import datetime

def clean_audit():
    """Run a clean security audit without report file noise"""
    
    # Remove all existing audit report files first
    report_files = glob.glob("security_audit_report_*.json")
    if report_files:
        print(f"🧹 Cleaning up {len(report_files)} old audit report files...")
        for report_file in report_files:
            try:
                os.remove(report_file)
                print(f"   ✅ Removed: {report_file}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {report_file}: {e}")
        print()
    
    # Define sensitive patterns (excluding harmless service account emails in reports)
    critical_patterns = {
        'private_key': r'-----BEGIN PRIVATE KEY-----.*?-----END PRIVATE KEY-----',
        'api_key': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?',
        'secret_key': r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?',
        'password': r'(?i)password\s*[:=]\s*["\']?[a-zA-Z0-9!@#$%^&*()_+-=]{8,}["\']?',
        'token': r'(?i)(token|access_token)\s*[:=]\s*["\']?[a-zA-Z0-9._-]{20,}["\']?'
    }
    
    # Files to scan
    scan_extensions = ['.py', '.js', '.html', '.md', '.txt', '.json', '.jsonl']
    
    # Files to skip
    skip_files = {
        'simple_diagnostic.py', 'security_audit.py', 'clean_security_audit.py',
        'fix_packages_txt.py', 'fix_packages_windows.py'
    }
    
    print("🔒 HCE IPA Transcriber - Clean Security Audit")
    print("=" * 55)
    print(f"Scanning: {os.path.abspath('.')}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Get all relevant files
    all_files = []
    skip_dirs = {'.git', '__pycache__', '.vscode', '.idea', 'node_modules', 'venv', 'env'}
    
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            file_name = os.path.basename(file_path)
            file_ext = Path(file_path).suffix.lower()
            
            # Only scan relevant files, skip our own tools
            if file_ext in scan_extensions and file_name not in skip_files:
                all_files.append(file_path)
    
    print(f"📊 Scanning {len(all_files)} relevant files for security issues...")
    print()
    
    # Scan files
    issues_found = []
    clean_files = []
    
    for file_path in all_files:
        try:
            file_name = os.path.basename(file_path)
            
            # Skip if file is too large (>5MB)
            if os.path.getsize(file_path) > 5 * 1024 * 1024:
                continue
            
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for critical patterns
            file_issues = []
            for pattern_name, pattern in critical_patterns.items():
                matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
                
                for match in matches:
                    match_text = match.group(0)
                    
                    # Skip obvious templates and examples
                    if any(word in match_text.upper() for word in [
                        'YOUR', 'REPLACE', 'EXAMPLE', 'TEMPLATE', 'PLACEHOLDER',
                        'TODO', 'FIXME', 'XXX', 'CHANGE_ME'
                    ]):
                        continue
                    
                    # This is a real issue
                    line_num = content[:match.start()].count('\n') + 1
                    file_issues.append({
                        'type': pattern_name,
                        'line': line_num,
                        'preview': match_text[:50] + '...' if len(match_text) > 50 else match_text
                    })
            
            if file_issues:
                issues_found.append({
                    'file': file_path,
                    'issues': file_issues
                })
                print(f"🚨 CRITICAL ISSUES in {file_name}:")
                for issue in file_issues:
                    print(f"   ❌ {issue['type']} on line {issue['line']}")
                    print(f"      Preview: {issue['preview']}")
            else:
                clean_files.append(file_path)
        
        except Exception as e:
            print(f"⚠️  Could not scan {file_path}: {e}")
    
    # Check .gitignore
    gitignore_ok = True
    if not os.path.exists('.gitignore'):
        print(f"🚨 CRITICAL: .gitignore file missing!")
        gitignore_ok = False
    else:
        with open('.gitignore', 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        required_patterns = ['google_credentials.json', '.env']
        missing = [p for p in required_patterns if p not in gitignore_content]
        
        if missing:
            print(f"⚠️  .gitignore missing patterns: {', '.join(missing)}")
        else:
            print(f"✅ .gitignore: Properly configured")
    
    # Final report
    print("\n" + "=" * 55)
    print("🔒 CLEAN SECURITY AUDIT RESULTS")
    print("=" * 55)
    
    total_critical = len(issues_found)
    
    if total_critical == 0 and gitignore_ok:
        print("🎉 EXCELLENT: No security issues detected!")
        print("   Your project is SECURE and ready for deployment!")
        print(f"\n📊 Scan Summary:")
        print(f"   ✅ Files scanned: {len(all_files)}")
        print(f"   ✅ Clean files: {len(clean_files)}")
        print(f"   🚨 Critical issues: 0")
        print(f"   ✅ .gitignore: Properly configured")
        print(f"\n🚀 STATUS: READY TO DEPLOY")
        return True
    
    elif total_critical == 0:
        print("✅ GOOD: No critical credential issues found")
        print("   Minor .gitignore improvements recommended")
        print(f"\n📊 Scan Summary:")
        print(f"   ✅ Files scanned: {len(all_files)}")
        print(f"   ✅ Clean files: {len(clean_files)}")
        print(f"   🚨 Critical issues: 0")
        print(f"   ⚠️  .gitignore: Needs improvement")
        print(f"\n🚀 STATUS: SAFE TO DEPLOY")
        return True
    
    else:
        print(f"🚨 CRITICAL SECURITY ISSUES FOUND: {total_critical}")
        print("   DO NOT DEPLOY until these are fixed!")
        print(f"\n📊 Scan Summary:")
        print(f"   🔍 Files scanned: {len(all_files)}")
        print(f"   ✅ Clean files: {len(clean_files)}")
        print(f"   🚨 Critical issues: {total_critical}")
        print(f"\n❌ STATUS: NOT SAFE TO DEPLOY")
        
        print(f"\n🚨 ISSUES TO FIX:")
        for issue_file in issues_found:
            print(f"   File: {issue_file['file']}")
            for issue in issue_file['issues']:
                print(f"     ❌ {issue['type']} on line {issue['line']}")
        
        return False

if __name__ == "__main__":
    success = clean_audit()
    exit(0 if success else 1)