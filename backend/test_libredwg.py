import os
import subprocess
import shutil

def test_libredwg():
    # Method 1: Check if in PATH
    if shutil.which('dwg2dxf'):
        print(f"✅ LibreDWG found in PATH: {shutil.which('dwg2dxf')}")
        try:
            result = subprocess.run(['dwg2dxf', '--version'], 
                                  capture_output=True, text=True)
            print(f"Version: {result.stdout}")
            return True
        except Exception as e:
            print(f"Error running dwg2dxf: {e}")
    
    # Method 2: Check full path
    full_path = r"C:\LibreDWG\bin\dwg2dxf.exe"
    if os.path.exists(full_path):
        print(f"✅ LibreDWG found at: {full_path}")
        try:
            result = subprocess.run([full_path, '--version'], 
                                  capture_output=True, text=True)
            print(f"Version: {result.stdout}")
            return True
        except Exception as e:
            print(f"Error running dwg2dxf: {e}")
    
    print("❌ LibreDWG not found")
    return False

if __name__ == "__main__":
    test_libredwg()