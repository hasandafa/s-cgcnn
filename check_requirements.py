#!/usr/bin/env python
"""
Requirements Checker for s-CGCNN v0.1
Validates all dependencies and environment setup
"""

import sys
import subprocess
from pathlib import Path
from importlib import import_module


def check_python_version():
    """Check Python version compatibility."""
    print("\n" + "="*60)
    print("Checking Python Version")
    print("="*60)
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3:
        print("❌ FAILED: Python 3 required")
        return False
    
    if version.minor < 8:
        print("❌ FAILED: Python 3.8 or higher required")
        return False
    
    if version.minor >= 13:
        print("⚠️  WARNING: Python 3.13+ may have compatibility issues")
        print("   Recommended: Python 3.10 or 3.11")
        return True
    
    print("✅ PASSED: Python version compatible")
    return True


def check_module(module_name, import_name=None, required_version=None):
    """Check if a module is installed and optionally verify version."""
    if import_name is None:
        import_name = module_name
    
    try:
        module = import_module(import_name)
        
        # Check version if specified
        if required_version and hasattr(module, '__version__'):
            installed_version = module.__version__
            print(f"  ✅ {module_name:20s} {installed_version}")
        else:
            print(f"  ✅ {module_name:20s} installed")
        
        return True
    except ImportError:
        print(f"  ❌ {module_name:20s} NOT FOUND")
        return False


def check_all_dependencies():
    """Check all required dependencies."""
    print("\n" + "="*60)
    print("Checking Dependencies")
    print("="*60)
    
    core_packages = [
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("scipy", "scipy"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("pyyaml", "yaml"),
    ]
    
    materials_packages = [
        ("pymatgen", "pymatgen"),
        ("mp-api", "mp_api"),
        ("matminer", "matminer"),
    ]
    
    ml_packages = [
        ("torch", "torch"),
        ("torch-geometric", "torch_geometric"),
    ]
    
    viz_packages = [
        ("plotly", "plotly"),
        ("tqdm", "tqdm"),
    ]
    
    all_passed = True
    
    print("\nCore Scientific:")
    for pkg, imp in core_packages:
        if not check_module(pkg, imp):
            all_passed = False
    
    print("\nMaterials Science:")
    for pkg, imp in materials_packages:
        if not check_module(pkg, imp):
            all_passed = False
    
    print("\nMachine Learning:")
    for pkg, imp in ml_packages:
        if not check_module(pkg, imp):
            all_passed = False
    
    print("\nVisualization:")
    for pkg, imp in viz_packages:
        if not check_module(pkg, imp):
            all_passed = False
    
    return all_passed


def check_file_structure():
    """Check directory structure."""
    print("\n" + "="*60)
    print("Checking Directory Structure")
    print("="*60)
    
    required_dirs = [
        "src/data_acquisition",
        "src/utils",
        "config",
        "data/raw",
        "data/structures/cif",
        "data/structures/metadata",
        "logs",
        "results",
        "notebooks",
    ]
    
    all_present = True
    
    for dir_path in required_dirs:
        p = Path(dir_path)
        if p.exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - MISSING")
            all_present = False
    
    return all_present


def check_api_key():
    """Check if API key is configured."""
    print("\n" + "="*60)
    print("Checking API Key")
    print("="*60)
    
    api_key_file = Path("config/mp_api_key.txt")
    
    if not api_key_file.exists():
        print("  ❌ API key file not found")
        print("     Create: config/mp_api_key.txt")
        print("     Get key from: https://next-gen.materialsproject.org/api")
        return False
    
    with open(api_key_file, 'r') as f:
        api_key = f.read().strip()
    
    if not api_key or len(api_key) < 10:
        print("  ❌ API key appears invalid")
        print("     Check: config/mp_api_key.txt")
        return False
    
    print(f"  ✅ API key configured (length: {len(api_key)} chars)")
    return True


def check_imports():
    """Check if project modules can be imported."""
    print("\n" + "="*60)
    print("Checking Project Imports")
    print("="*60)
    
    try:
        from src.data_acquisition.mp_fetcher import MPDataFetcher
        print("  ✅ mp_fetcher")
    except ImportError as e:
        print(f"  ❌ mp_fetcher: {e}")
        return False
    
    try:
        from src.data_acquisition.structure_interpolator import StructureInterpolator
        print("  ✅ structure_interpolator")
    except ImportError as e:
        print(f"  ❌ structure_interpolator: {e}")
        return False
    
    try:
        from src.utils.constants import GaAs_PROPERTIES
        print("  ✅ constants")
    except ImportError as e:
        print(f"  ❌ constants: {e}")
        return False
    
    try:
        from src.utils.logger_config import setup_logger
        print("  ✅ logger_config")
    except ImportError as e:
        print(f"  ❌ logger_config: {e}")
        return False
    
    return True


def check_pip_conflicts():
    """Check for pip dependency conflicts."""
    print("\n" + "="*60)
    print("Checking for Dependency Conflicts")
    print("="*60)
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("  ✅ No dependency conflicts found")
            return True
        else:
            print("  ⚠️  Dependency conflicts detected:")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"  ⚠️  Could not check conflicts: {e}")
        return True  # Don't fail on this


def generate_report():
    """Run all checks and generate report."""
    print("\n" + "="*70)
    print("s-CGCNN v0.1 - Requirements Checker")
    print("="*70)
    
    results = {}
    
    results['python'] = check_python_version()
    results['dependencies'] = check_all_dependencies()
    results['structure'] = check_file_structure()
    results['api_key'] = check_api_key()
    results['imports'] = check_imports()
    results['conflicts'] = check_pip_conflicts()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, status in results.items():
        status_str = "✅ PASS" if status else "❌ FAIL"
        print(f"  {status_str}  {check.replace('_', ' ').title()}")
    
    print("\n" + "="*70)
    
    if passed == total:
        print("✅✅✅ ALL CHECKS PASSED - READY TO GO! ✅✅✅")
        print("\nNext steps:")
        print("  1. Run pipeline: python run_version_0.1.py")
        print("  2. Run tests: python '1. Data Acquisition and Structure Interpolation Testing.py'")
        print("  3. Explore notebooks: jupyter notebook")
        return 0
    else:
        print(f"⚠️  {total - passed}/{total} checks failed")
        print("\nFix the issues above, then run this script again.")
        print("\nCommon fixes:")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - Missing directories: run setup_windows.bat")
        print("  - Missing API key: create config/mp_api_key.txt")
        return 1


if __name__ == "__main__":
    exit_code = generate_report()
    sys.exit(exit_code)