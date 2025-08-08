#!/usr/bin/env python3
"""
Quick fix for packages.txt BOM issue that causes Streamlit Cloud deployment failures
"""

import os

def fix_packages_txt():
    """Create a clean packages.txt file without BOM"""
    
    print("🔧 Fixing packages.txt BOM issue...")
    
    # Check if packages.txt exists
    if os.path.exists('packages.txt'):
        # Check if it has BOM
        with open('packages.txt', 'rb') as f:
            raw_content = f.read()
        
        bom_types = {
            b'\xef\xbb\xbf': 'UTF-8 BOM',
            b'\xff\xfe': 'UTF-16 LE BOM', 
            b'\xfe\xff': 'UTF-16 BE BOM'
        }
        
        has_bom = False
        for bom, name in bom_types.items():
            if raw_content.startswith(bom):
                print(f"❌ Found {name} in packages.txt")
                has_bom = True
                break
        
        if has_bom:
            # Backup original
            backup_name = 'packages.txt.backup'
            with open(backup_name, 'wb') as f:
                f.write(raw_content)
            print(f"💾 Backed up original to: {backup_name}")
        else:
            print("✅ No BOM found in existing packages.txt")
            return
    else:
        print("📝 packages.txt not found, creating new one")
    
    # Create clean packages.txt
    clean_content = "espeak-ng\n"
    
    # Write with explicit UTF-8 encoding, no BOM
    with open('packages.txt', 'w', encoding='utf-8') as f:
        f.write(clean_content)
    
    print("✅ Created clean packages.txt with content:")
    print("   espeak-ng")
    
    # Verify it's clean
    with open('packages.txt', 'rb') as f:
        new_content = f.read()
    
    if new_content == b'espeak-ng\n':
        print("✅ Verification passed - packages.txt is clean")
        return True
    else:
        print("❌ Verification failed - something went wrong")
        return False

if __name__ == "__main__":
    success = fix_packages_txt()
    if success:
        print("\n🎉 packages.txt fixed! Your Streamlit Cloud deployment should now work.")
    else:
        print("\n❌ Fix failed. Try manually creating packages.txt with just: espeak-ng")