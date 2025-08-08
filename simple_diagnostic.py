#!/usr/bin/env python3
"""
HCE IPA Transcriber - Simple Diagnostic Tool
Checks the most important issues that could prevent deployment
"""

import os
import json
import sys
from datetime import datetime

def check_packages_txt():
    """Check packages.txt for BOM issues"""
    print("📦 Checking packages.txt...")
    
    if not os.path.exists('packages.txt'):
        print("  ➖ packages.txt not found")
        return {'exists': False, 'issue': 'missing'}
    
    # Check for BOM
    with open('packages.txt', 'rb') as f:
        raw_content = f.read()
    
    # Check common BOM patterns
    bom_patterns = {
        b'\xff\xfe': 'UTF-16 LE BOM',
        b'\xfe\xff': 'UTF-16 BE BOM', 
        b'\xef\xbb\xbf': 'UTF-8 BOM'
    }
    
    for bom, name in bom_patterns.items():
        if raw_content.startswith(bom):
            print(f"  ❌ CRITICAL: Found {name}")
            print(f"     This WILL cause Streamlit Cloud deployment to fail!")
            print(f"     Raw bytes: {raw_content[:10].hex()}")
            return {'exists': True, 'issue': 'bom', 'bom_type': name}
    
    # Check content
    try:
        with open('packages.txt', 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        print(f"  ✅ Clean file, content: '{content}'")
        return {'exists': True, 'issue': None, 'content': content}
    
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
        return {'exists': True, 'issue': 'read_error', 'error': str(e)}

def check_required_files():
    """Check for required files"""
    print("\n📁 Checking required files...")
    
    required_files = {
        'app.py': 'Main application',
        'ipa_converter.py': 'IPA conversion logic',
        'overrides.py': 'Dictionary management', 
        'requirements.txt': 'Python dependencies',
        'hce_map.json': 'HCE phoneme mappings'
    }
    
    results = {}
    all_good = True
    
    for file, description in required_files.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✅ {file}: {size} bytes ({description})")
            results[file] = {'exists': True, 'size': size}
        else:
            print(f"  ❌ {file}: MISSING ({description})")
            results[file] = {'exists': False}
            all_good = False
    
    return results, all_good

def check_python_imports():
    """Check if required Python packages can be imported"""
    print("\n🐍 Checking Python imports...")
    
    required_imports = [
        ('streamlit', 'Streamlit framework'),
        ('json', 'JSON handling (built-in)'),
        ('os', 'OS operations (built-in)'),
        ('datetime', 'Date/time (built-in)')
    ]
    
    optional_imports = [
        ('gspread', 'Google Sheets integration'),
        ('google.oauth2.service_account', 'Google authentication'),
        ('pandas', 'Data manipulation'),
        ('plotly', 'Data visualization')
    ]
    
    results = {'required': {}, 'optional': {}}
    all_required_ok = True
    
    # Check required imports
    for module, description in required_imports:
        try:
            __import__(module)
            version = getattr(__import__(module), '__version__', 'built-in')
            print(f"  ✅ {module}: {version} ({description})")
            results['required'][module] = {'available': True, 'version': version}
        except ImportError as e:
            print(f"  ❌ {module}: MISSING ({description})")
            print(f"     Error: {e}")
            results['required'][module] = {'available': False, 'error': str(e)}
            all_required_ok = False
    
    # Check optional imports  
    for module, description in optional_imports:
        try:
            __import__(module)
            version = getattr(__import__(module), '__version__', 'unknown')
            print(f"  ℹ️  {module}: {version} ({description})")
            results['optional'][module] = {'available': True, 'version': version}
        except ImportError:
            print(f"  ➖ {module}: not available ({description})")
            results['optional'][module] = {'available': False}
    
    return results, all_required_ok

def check_json_files():
    """Check JSON configuration files"""
    print("\n⚙️  Checking JSON configuration files...")
    
    json_files = ['hce_map.json', 'override_dict.json']
    results = {}
    
    for file in json_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"  ✅ {file}: Valid JSON, {len(data)} entries")
                results[file] = {'valid': True, 'entries': len(data)}
                
            except json.JSONDecodeError as e:
                print(f"  ❌ {file}: Invalid JSON")
                print(f"     Error: {e}")
                results[file] = {'valid': False, 'error': str(e)}
            
            except Exception as e:
                print(f"  ❌ {file}: Error reading")
                print(f"     Error: {e}")
                results[file] = {'valid': False, 'error': str(e)}
        else:
            if file == 'override_dict.json':
                print(f"  ➖ {file}: Will be created automatically")
                results[file] = {'exists': False, 'auto_create': True}
            else:
                print(f"  ❌ {file}: Missing required file")
                results[file] = {'exists': False, 'required': True}
    
    return results

def test_basic_functionality():
    """Test basic app functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Try to import main modules
        sys.path.insert(0, '.')
        
        print("  📝 Testing IPA converter import...")
        from ipa_converter import process_text, clean_word
        print("     ✅ IPA converter imported successfully")
        
        print("  📝 Testing simple word processing...")
        result = process_text("hello")
        if result and len(result) > 0:
            print(f"     ✅ Processed 'hello' -> {result[0].get('ipa_options', ['no options'])}")
        else:
            print("     ⚠️  Processing returned no results")
        
        print("  📝 Testing overrides import...")
        from overrides import update_override_dict
        print("     ✅ Overrides module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Functionality test failed: {e}")
        return False

def generate_fix_recommendations(packages_result, files_result, imports_result):
    """Generate specific fix recommendations"""
    print("\n💡 Fix Recommendations:")
    print("=" * 40)
    
    fixes = []
    
    # Critical: packages.txt BOM
    if packages_result.get('issue') == 'bom':
        fixes.append({
            'priority': 'CRITICAL', 
            'issue': 'packages.txt has BOM',
            'fix': 'Run: echo "espeak-ng" > packages.txt',
            'reason': 'BOM causes Streamlit Cloud deployment to fail'
        })
    
    # Critical: missing required files
    files_data, files_ok = files_result
    missing_files = [f for f, data in files_data.items() if not data.get('exists')]
    if missing_files:
        fixes.append({
            'priority': 'CRITICAL',
            'issue': f'Missing required files: {", ".join(missing_files)}',
            'fix': 'Download missing files from the repository',
            'reason': 'App cannot run without these files'
        })
    
    # High: missing Python packages
    imports_data, imports_ok = imports_result
    missing_packages = [pkg for pkg, data in imports_data['required'].items() 
                       if not data.get('available')]
    if missing_packages:
        fixes.append({
            'priority': 'HIGH',
            'issue': f'Missing Python packages: {", ".join(missing_packages)}',
            'fix': f'Run: pip install {" ".join(missing_packages)}',
            'reason': 'Required for basic app functionality'
        })
    
    # Display fixes
    if not fixes:
        print("🎉 No critical issues found!")
        return
    
    for i, fix in enumerate(fixes, 1):
        priority_emoji = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '💡'}
        emoji = priority_emoji.get(fix['priority'], '•')
        
        print(f"{emoji} {fix['priority']} #{i}:")
        print(f"   Issue: {fix['issue']}")
        print(f"   Fix: {fix['fix']}")
        print(f"   Why: {fix['reason']}")
        print()

def main():
    """Main diagnostic function"""
    print("🔍 HCE IPA Transcriber - Simple Diagnostic")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Working Directory: {os.getcwd()}")
    print()
    
    # Run checks
    packages_result = check_packages_txt()
    files_result = check_required_files()
    imports_result = check_python_imports() 
    json_result = check_json_files()
    functionality_ok = test_basic_functionality()
    
    # Summary
    print("\n🎯 SUMMARY")
    print("=" * 20)
    
    issues = []
    
    if packages_result.get('issue') == 'bom':
        issues.append("CRITICAL: packages.txt has BOM")
    
    files_data, files_ok = files_result
    if not files_ok:
        issues.append("CRITICAL: Missing required files")
    
    imports_data, imports_ok = imports_result
    if not imports_ok:
        issues.append("HIGH: Missing Python packages")
    
    if not functionality_ok:
        issues.append("HIGH: Basic functionality test failed")
    
    if not issues:
        print("✅ All checks passed!")
        print("🚀 Your setup looks ready for deployment!")
    else:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   - {issue}")
    
    # Generate recommendations
    generate_fix_recommendations(packages_result, files_result, imports_result)
    
    return len(issues) == 0

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Diagnostic completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Issues found - fix them before deploying")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Diagnostic cancelled")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Diagnostic failed: {e}")
        sys.exit(1)