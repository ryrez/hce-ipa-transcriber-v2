#!/usr/bin/env python3
"""
Windows-specific fix for packages.txt BOM issue
Creates a clean UTF-8 file without BOM
"""

import os

def fix_packages_txt_windows():
    """Create clean packages.txt for Windows"""
    
    print("🔧 Fixing packages.txt for Windows...")
    
    # Delete existing file if it exists
    if os.path.exists('packages.txt'):
        os.remove('packages.txt')
        print("🗑️  Removed existing packages.txt")
    
    # Create new file with explicit UTF-8 encoding, no BOM
    content = "espeak-ng"
    
    with open('packages.txt', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    
    print("✅ Created clean packages.txt")
    
    # Verify the file
    with open('packages.txt', 'rb') as f:
        raw_bytes = f.read()
    
    print(f"📝 Content: '{content}'")
    print(f"📊 Raw bytes: {raw_bytes.hex()}")
    print(f"📏 Size: {len(raw_bytes)} bytes")
    
    # Check for BOM
    bom_patterns = {
        b'\xff\xfe': 'UTF-16 LE BOM',
        b'\xfe\xff': 'UTF-16 BE BOM', 
        b'\xef\xbb\xbf': 'UTF-8 BOM'
    }
    
    has_bom = False
    for bom, name in bom_patterns.items():
        if raw_bytes.startswith(bom):
            print(f"❌ Still has {name}")
            has_bom = True
            break
    
    if not has_bom:
        print("✅ No BOM detected - file is clean!")
        
        # Expected bytes for "espeak-ng" in UTF-8
        expected = b'espeak-ng'
        if raw_bytes == expected:
            print("✅ File content is exactly correct!")
            return True
        else:
            print(f"⚠️  Content mismatch. Expected: {expected.hex()}, Got: {raw_bytes.hex()}")
            return False
    else:
        print("❌ File still has BOM - manual intervention needed")
        return False

def manual_instructions():
    """Provide manual instructions if automated fix fails"""
    print("\n📋 Manual Fix Instructions:")
    print("=" * 40)
    print("If the automated fix didn't work, try this:")
    print()
    print("1. Delete packages.txt if it exists")
    print("2. Open Notepad (not PowerShell)")
    print("3. Type exactly: espeak-ng")
    print("4. Save As -> packages.txt")
    print("5. Make sure 'Encoding' is set to 'UTF-8' (NOT 'UTF-8 with BOM')")
    print()
    print("Alternative using PowerShell:")
    print('   [System.IO.File]::WriteAllText("packages.txt", "espeak-ng", [System.Text.UTF8Encoding]($false))')
    print()
    print("Or using Command Prompt (cmd):")
    print("   echo espeak-ng > packages.txt")

if __name__ == "__main__":
    success = fix_packages_txt_windows()
    
    if success:
        print("\n🎉 SUCCESS! packages.txt is now clean and ready for Streamlit Cloud!")
        print("💡 Run your diagnostic again to verify:")
        print("   python simple_diagnostic.py")
    else:
        print("\n❌ Automated fix failed.")
        manual_instructions()