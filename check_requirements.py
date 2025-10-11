"""
s-CGCNN v0.1.1 - Dependency Checker

Verifies that all required packages are installed with correct versions.

Usage:
    python check_requirements.py

Author: Abdullah Hasan Dafa
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================================
# VERSION REQUIREMENTS
# ============================================================================

# Critical dependencies (MUST have exact or compatible versions)
CRITICAL_DEPS = {
    "mp-api": "0.41.2",  # Fixed version
    "pymatgen": ">=2023.5.10,<2024.0.0",
    "numpy": ">=1.24.0,<2.0.0",
    "pyyaml": ">=6.0",
}

# Important dependencies (for core functionality)
IMPORTANT_DEPS = {
    "scipy": ">=1.10.0",
    "pandas": ">=2.0.0",
    "torch": ">=2.0.0",
    "matplotlib": ">=3.7.0",
}

# Optional dependencies (for enhanced features)
OPTIONAL_DEPS = {
    "plotly": ">=5.14.0",
    "crystal-toolkit": ">=2023.11.3",
    "dash": ">=2.11.0",
    "jupyter": ">=1.0.0",
    "torch-geometric": ">=2.3.0",
}

# Python version requirement
REQUIRED_PYTHON = (3, 10)
MAX_PYTHON = (3, 12)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible"""
    current = sys.version_info[:2]
    
    if current < REQUIRED_PYTHON:
        return False, (
            f"Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required, "
            f"but you have {current[0]}.{current[1]}"
        )
    
    if current > MAX_PYTHON:
        return False, (
            f"Python {current[0]}.{current[1]} is not yet tested. "
            f"Maximum supported version: {MAX_PYTHON[0]}.{MAX_PYTHON[1]}"
        )
    
    return True, f"Python {current[0]}.{current[1]} ✓"


def get_installed_version(package: str) -> str:
    """Get installed version of a package"""
    try:
        import importlib.metadata
        version = importlib.metadata.version(package)
        return version
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def parse_version_requirement(requirement: str) -> Tuple[str, str]:
    """
    Parse version requirement string.
    
    Examples:
        ">=1.0.0" -> (">=", "1.0.0")
        "==1.0.0" -> ("==", "1.0.0")
        ">=1.0.0,<2.0.0" -> Returns first constraint
    """
    requirement = requirement.strip()
    
    # Handle multiple constraints (take first one)
    if "," in requirement:
        requirement = requirement.split(",")[0].strip()
    
    # Parse operator and version
    for op in [">=", "<=", "==", ">", "<", "~="]:
        if requirement.startswith(op):
            return op, requirement[len(op):].strip()
    
    return "==", requirement


def compare_versions(installed: str, required: str) -> Tuple[bool, str]:
    """
    Compare installed version with requirement.
    
    Returns:
        (is_compatible, message)
    """
    operator, req_version = parse_version_requirement(required)
    
    try:
        from packaging import version
        
        installed_v = version.parse(installed)
        required_v = version.parse(req_version)
        
        if operator == ">=":
            compatible = installed_v >= required_v
        elif operator == "<=":
            compatible = installed_v <= required_v
        elif operator == "==":
            compatible = installed_v == required_v
        elif operator == ">":
            compatible = installed_v > required_v
        elif operator == "<":
            compatible = installed_v < required_v
        elif operator == "~=":
            # Compatible release (same major.minor)
            compatible = (
                installed_v.major == required_v.major and
                installed_v.minor == required_v.minor and
                installed_v >= required_v
            )
        else:
            return False, f"Unknown operator: {operator}"
        
        if compatible:
            return True, f"v{installed} ✓"
        else:
            return False, f"v{installed} (need {required})"
    
    except ImportError:
        # packaging not available, do basic string comparison
        if installed == req_version or operator == ">=":
            return True, f"v{installed} (not verified)"
        return False, f"v{installed} (need {required})"


def check_package(package: str, requirement: str) -> Tuple[bool, str, str]:
    """
    Check if a package is installed with correct version.
    
    Returns:
        (is_installed, status, message)
    """
    installed_version = get_installed_version(package)
    
    if installed_version is None:
        return False, "MISSING", f"Not installed"
    
    is_compatible, msg = compare_versions(installed_version, requirement)
    
    if is_compatible:
        return True, "OK", msg
    else:
        return False, "VERSION", msg


def check_mp_api_key() -> Tuple[bool, str]:
    """Check if Materials Project API key exists"""
    key_file = Path("config/mp_api_key.txt")
    
    if not key_file.exists():
        return False, "config/mp_api_key.txt not found"
    
    try:
        with open(key_file, 'r') as f:
            key = f.read().strip()
        
        if not key:
            return False, "API key file is empty"
        
        if len(key) < 10:
            return False, "API key seems invalid (too short)"
        
        return True, "API key found ✓"
    
    except Exception as e:
        return False, f"Could not read API key: {e}"


def check_directory_structure() -> Tuple[bool, List[str]]:
    """Check if required directories exist"""
    required_dirs = [
        "config",
        "src",
        "src/data_acquisition",
        "src/utils",
        "tests",
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        return False, missing
    return True, []


def install_package(package: str) -> bool:
    """Attempt to install a package"""
    try:
        print(f"  → Installing {package}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


# ============================================================================
# MAIN CHECK FUNCTION
# ============================================================================

def run_checks():
    """Run all dependency checks and print report"""
    
    print("=" * 80)
    print("  s-CGCNN v0.1.1 - Dependency Checker")
    print("=" * 80)
    print()
    
    all_ok = True
    
    # ========================================================================
    # 1. Python Version
    # ========================================================================
    print("1. PYTHON VERSION")
    print("-" * 80)
    
    py_ok, py_msg = check_python_version()
    
    if py_ok:
        print(f"  ✓ {py_msg}")
    else:
        print(f"  ✗ {py_msg}")
        all_ok = False
    
    print()
    
    # ========================================================================
    # 2. Critical Dependencies
    # ========================================================================
    print("2. CRITICAL DEPENDENCIES (Must have)")
    print("-" * 80)
    
    critical_ok = True
    for package, requirement in CRITICAL_DEPS.items():
        is_ok, status, msg = check_package(package, requirement)
        
        if is_ok:
            print(f"  ✓ {package:<20} {msg}")
        else:
            print(f"  ✗ {package:<20} {msg}")
            critical_ok = False
            all_ok = False
    
    print()
    
    # ========================================================================
    # 3. Important Dependencies
    # ========================================================================
    print("3. IMPORTANT DEPENDENCIES (Core functionality)")
    print("-" * 80)
    
    important_ok = True
    for package, requirement in IMPORTANT_DEPS.items():
        is_ok, status, msg = check_package(package, requirement)
        
        if is_ok:
            print(f"  ✓ {package:<20} {msg}")
        else:
            print(f"  ⚠ {package:<20} {msg}")
            important_ok = False
    
    print()
    
    # ========================================================================
    # 4. Optional Dependencies
    # ========================================================================
    print("4. OPTIONAL DEPENDENCIES (Enhanced features)")
    print("-" * 80)
    
    optional_installed = []
    optional_missing = []
    
    for package, requirement in OPTIONAL_DEPS.items():
        is_ok, status, msg = check_package(package, requirement)
        
        if is_ok:
            print(f"  ✓ {package:<20} {msg}")
            optional_installed.append(package)
        else:
            print(f"  - {package:<20} {msg}")
            optional_missing.append(package)
    
    print()
    
    # ========================================================================
    # 5. Materials Project API Key
    # ========================================================================
    print("5. MATERIALS PROJECT API KEY")
    print("-" * 80)
    
    key_ok, key_msg = check_mp_api_key()
    
    if key_ok:
        print(f"  ✓ {key_msg}")
    else:
        print(f"  ✗ {key_msg}")
        print(f"     Get your free API key from: https://materialsproject.org")
        print(f"     Save it to: config/mp_api_key.txt")
        all_ok = False
    
    print()
    
    # ========================================================================
    # 6. Directory Structure
    # ========================================================================
    print("6. DIRECTORY STRUCTURE")
    print("-" * 80)
    
    dirs_ok, missing_dirs = check_directory_structure()
    
    if dirs_ok:
        print(f"  ✓ All required directories exist")
    else:
        print(f"  ✗ Missing directories:")
        for dir_path in missing_dirs:
            print(f"     - {dir_path}")
        all_ok = False
    
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    
    if all_ok and critical_ok and important_ok:
        print("  ✓ ALL CHECKS PASSED - Ready to use s-CGCNN!")
        print()
        print("  Next steps:")
        print("    1. python run_version_0.1.1.py --mode literature")
        print("    2. python tests/test_v0.1.1_complete.py")
        print()
        return 0
    
    elif critical_ok and important_ok:
        print("  ⚠ CORE DEPENDENCIES OK - Basic functionality available")
        print()
        if optional_missing:
            print(f"  Missing optional packages ({len(optional_missing)}):")
            for pkg in optional_missing:
                print(f"    - {pkg}")
        print()
        print("  You can proceed, but some features may be unavailable.")
        print()
        return 0
    
    else:
        print("  ✗ CRITICAL ISSUES FOUND - Cannot run s-CGCNN")
        print()
        print("  Required actions:")
        
        if not critical_ok:
            print("    1. Install critical dependencies:")
            print("       pip install -r requirements.txt")
        
        if not important_ok:
            print("    2. Install important dependencies:")
            for package, requirement in IMPORTANT_DEPS.items():
                is_ok, _, _ = check_package(package, requirement)
                if not is_ok:
                    print(f"       pip install '{package}{requirement}'")
        
        if not key_ok:
            print("    3. Setup Materials Project API key:")
            print("       - Get key from: https://materialsproject.org")
            print("       - Save to: config/mp_api_key.txt")
        
        print()
        return 1
    
    print("=" * 80)
    print()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    exit_code = run_checks()
    sys.exit(exit_code)