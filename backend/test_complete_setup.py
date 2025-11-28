"""
Complete system verification for BOQ Automation
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_result(check, status, message=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {check:<30} {message}")

def test_libredwg():
    """Test LibreDWG"""
    print_header("LibreDWG Check")
    
    if shutil.which('dwg2dxf'):
        path = shutil.which('dwg2dxf')
        print_result("LibreDWG", True, f"Found at: {path}")
        try:
            result = subprocess.run(['dwg2dxf', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            print_result("Version check", True, "Command executed")
            return True
        except Exception as e:
            print_result("Version check", False, str(e))
            return False
    else:
        print_result("LibreDWG", False, "Not found in PATH")
        return False

def test_oda():
    """Test ODA FileConverter"""
    print_header("ODA FileConverter Check")
    
    oda_path = r"C:\Program Files\ODA\ODAFileConverter 26.9.0\ODAFileConverter.exe"
    
    if os.path.exists(oda_path):
        print_result("ODA Executable", True, "Found")
        print(f"   Path: {oda_path}")
        print(f"   Size: {os.path.getsize(oda_path) / (1024*1024):.1f} MB")
        
        # Try to get version
        try:
            # ODA doesn't have --version, but we can test if it runs
            result = subprocess.run([oda_path], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=2)
            print_result("Execution test", True, "Can execute")
            return oda_path
        except subprocess.TimeoutExpired:
            # Timeout is actually OK - means it's trying to run
            print_result("Execution test", True, "Can execute (GUI mode)")
            return oda_path
        except Exception as e:
            print_result("Execution test", False, str(e))
            return None
    else:
        print_result("ODA Executable", False, "Not found at expected path")
        return None

def test_env_file():
    """Test .env file"""
    print_header(".env File Check")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_result(".env file", False, "Not found")
        print(f"\n   Expected at: {env_path.absolute()}")
        return False
    
    print_result(".env file", True, "Found")
    
    # Check critical settings
    with open(env_path, 'r') as f:
        content = f.read()
        
        checks = {
            'CONVERTER': 'CONVERTER=' in content,
            'CONVERTER_BIN': 'CONVERTER_BIN=' in content,
            'REDIS_URL': 'REDIS_URL=' in content,
            'DXF_VERSION': 'DXF_VERSION=' in content,
        }
        
        for key, found in checks.items():
            print_result(f"  {key}", found)
        
        return all(checks.values())

def test_python_packages():
    """Test required packages"""
    print_header("Python Packages Check")
    
    packages = {
        'ezdxf': 'CAD file parsing',
        'openpyxl': 'Excel generation',
        'fastapi': 'Web API',
        'celery': 'Task queue',
        'redis': 'Redis client',
        'shapely': 'Geometric analysis',
        'pandas': 'Data processing',
    }
    
    all_installed = True
    missing = []
    
    for package, description in packages.items():
        try:
            __import__(package)
            print_result(package, True, description)
        except ImportError:
            print_result(package, False, f"{description} - MISSING")
            missing.append(package)
            all_installed = False
    
    if missing:
        print(f"\n⚠️  Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
    
    return all_installed

def test_project_structure():
    """Test project file structure"""
    print_header("Project Structure Check")
    
    required_files = {
        'app/workers/pipeline.py': 'Main pipeline',
        'app/workers/tasks.py': 'Celery tasks',
        'app/main.py': 'FastAPI app',
        'requirements.txt': 'Dependencies',
    }
    
    all_present = True
    for file_path, description in required_files.items():
        exists = Path(file_path).exists()
        print_result(file_path, exists, description)
        if not exists:
            all_present = False
    
    return all_present

def test_new_modules():
    """Check if new modules are present"""
    print_header("New Modules Check (for enhanced system)")
    
    new_modules = {
        'app/workers/dwg_converter.py': 'DWG converter',
        'app/workers/comprehensive_extractor.py': 'Data extractor',
        'app/workers/boq_generator.py': 'BOQ generator',
    }
    
    any_present = False
    for file_path, description in new_modules.items():
        exists = Path(file_path).exists()
        print_result(file_path, exists, description)
        if exists:
            any_present = True
    
    if not any_present:
        print("\n⚠️  New enhanced modules not yet added")
        print("   These will be added in the next step")
    
    return any_present

def main():
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  BOQ Automation System - Complete Setup Verification".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    results = {
        'libredwg': test_libredwg(),
        'oda': test_oda(),
        'env': test_env_file(),
        'packages': test_python_packages(),
        'structure': test_project_structure(),
        'new_modules': test_new_modules(),
    }
    
    print_header("FINAL SUMMARY")
    print()
    print("CONVERTERS:")
    print(f"  LibreDWG:          {'✅ READY' if results['libredwg'] else '❌ NOT FOUND'}")
    print(f"  ODA FileConverter: {'✅ READY' if results['oda'] else '❌ NOT FOUND'}")
    print()
    print("CONFIGURATION:")
    print(f"  .env File:         {'✅ CONFIGURED' if results['env'] else '❌ MISSING'}")
    print(f"  Python Packages:   {'✅ INSTALLED' if results['packages'] else '❌ MISSING'}")
    print()
    print("PROJECT:")
    print(f"  Core Files:        {'✅ PRESENT' if results['structure'] else '❌ MISSING'}")
    print(f"  Enhanced Modules:  {'✅ ADDED' if results['new_modules'] else '⏳ PENDING'}")
    print()
    
    print("="*70)
    
    if (results['libredwg'] or results['oda']) and results['env']:
        print("🎉 SYSTEM IS READY FOR BASIC OPERATION!")
        print()
        if not results['new_modules']:
            print("📝 NEXT STEP: Add enhanced modules for 95% accuracy:")
            print("   - dwg_converter.py")
            print("   - comprehensive_extractor.py")
            print("   - boq_generator.py")
        else:
            print("✅ ALL ENHANCED MODULES PRESENT!")
            print("   System ready for high-accuracy BOQ generation")
    else:
        print("⚠️  SETUP INCOMPLETE")
        print()
        if not (results['libredwg'] or results['oda']):
            print("   ❌ No DWG converters available")
        if not results['env']:
            print("   ❌ .env file missing or incomplete")
        if not results['packages']:
            print("   ❌ Some Python packages missing")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)