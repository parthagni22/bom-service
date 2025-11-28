import os
import shutil

# Test which converters are available
def test_oda():
    """Test ODA FileConverter"""
    oda_paths = [
        r"C:\Program Files\ODA\ODAFileConverter.exe",
        r"C:\Program Files (x86)\ODA\ODAFileConverter.exe",
    ]
    
    for path in oda_paths:
        if os.path.exists(path):
            print(f"✅ ODA FileConverter found at: {path}")
            return True
    
    print("❌ ODA FileConverter not found")
    return False

def test_libredwg():
    """Test LibreDWG"""
    if shutil.which('dwg2dxf'):
        print(f"✅ LibreDWG found at: {shutil.which('dwg2dxf')}")
        return True
    else:
        print("❌ LibreDWG not found")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Testing DWG Converters on Windows")
    print("=" * 50)
    
    oda_available = test_oda()
    libre_available = test_libredwg()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if oda_available or libre_available:
        print("✅ At least one converter is available!")
        if oda_available:
            print("   - ODA FileConverter: Ready")
        if libre_available:
            print("   - LibreDWG: Ready")
    else:
        print("❌ No converters found. Please install one.")
        print("\nRecommendation:")
        print("1. Install ODA FileConverter (easier on Windows)")
        print("   https://www.opendesign.com/guestfiles/oda_file_converter")