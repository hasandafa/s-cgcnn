# Dependencies Installation Guide

Complete guide for setting up the AlGaAs research environment with Crystal-Toolkit and related libraries.

## Prerequisites

- **Python 3.11** (Python 3.13 is NOT compatible with crystal-toolkit)
- **Windows OS** (adjust commands for Linux/Mac)
- **pip** (latest version)

## Table of Contents

1. [Quick Start - Using Existing Environment](#quick-start---using-existing-environment)
2. [Complete Setup - From Scratch](#complete-setup---from-scratch)
3. [Troubleshooting](#troubleshooting)
4. [Verification](#verification)

---

## Quick Start - Using Existing Environment

If you already have the `venv` folder in your project root:

### Activate Virtual Environment

```powershell
# On Windows PowerShell
.\venv\Scripts\Activate.ps1

# On Windows CMD
.\venv\Scripts\activate.bat

# On Linux/Mac
source venv/bin/activate
```

### Verify Installation

```powershell
python -c "import crystal_toolkit; import pymatgen; import ase; import torch; import jarvis; print('✅ All libraries imported successfully!')"
```

If you get errors, proceed to [Complete Setup](#complete-setup---from-scratch).

---

## Complete Setup - From Scratch

### Step 1: Install Python 3.11

1. Download Python 3.11 from: https://www.python.org/downloads/release/python-31111/
2. **IMPORTANT during installation:**
   - ✅ Check "Add python.exe to PATH"
   - ✅ Choose "Customize installation"
   - ✅ In Advanced Options, check "Add Python to environment variables"

3. Verify installation:
```powershell
py --list
# Should show:
# -V:3.11          Python 3.11 (64-bit)
```

### Step 2: Create Virtual Environment

```powershell
# Navigate to your project directory
cd C:\path\to\your\project

# Create virtual environment with Python 3.11
py -3.11 -m venv venv

# Activate the environment
.\venv\Scripts\Activate.ps1

# Verify Python version
python --version
# Output: Python 3.11.x
```

### Step 3: Upgrade pip

```powershell
pip install --upgrade pip
```

### Step 4: Install Dependencies (Staged Approach)

**⚠️ CRITICAL: Follow these steps in order to avoid conflicts!**

#### Stage 1: Install Crystal-Toolkit First

```powershell
pip install crystal-toolkit
```

**Expected output:** Crystal-toolkit will install with its strict dependencies including:
- dash
- plotly
- pymatgen
- mp-api
- jupyterlab 3.x
- And many others

#### Stage 2: Install ASE

```powershell
pip install ase
```

#### Stage 3: Install PyTorch

**For CPU-only (no NVIDIA GPU):**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**For CUDA 12.1 (NVIDIA GPU):**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**For CUDA 11.8 (older NVIDIA GPU):**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

*To check if you have NVIDIA GPU: run `nvidia-smi` in terminal*

#### Stage 4: Install PyTorch Geometric

```powershell
pip install torch-geometric
```

#### Stage 5: Install Additional Libraries

```powershell
pip install kaleido optuna h5py tqdm loguru
```

**Note:** We skip `nglview` as crystal-toolkit already provides excellent visualization capabilities.

#### Stage 6: Install JARVIS-tools (Optional)

```powershell
pip install jarvis-tools
```

### Step 5: Apply Compatibility Patch

Due to a known incompatibility between `pymatgen` and `emmet-core`, we need to apply a patch:

#### Create sitecustomize.py

```powershell
# Create the patch file
$content = @'
import sys
try:
    import pymatgen.symmetry.analyzer as sa
    if not hasattr(sa, 'SymmetryUndeterminedError'):
        sa.SymmetryUndeterminedError = type('SymmetryUndeterminedError', (Exception,), {})
except ImportError:
    pass
'@

$content | Out-File -FilePath "venv\Lib\site-packages\sitecustomize.py" -Encoding utf8
```

#### Downgrade mp-api for Compatibility

```powershell
pip install mp-api==0.41.2
```

### Step 6: Lock Dependencies

Save your working configuration:

```powershell
pip freeze > requirements-locked.txt
```

---

## Troubleshooting

### Issue 1: Python 3.13 Incompatibility

**Error:** `ModuleNotFoundError: No module named 'pipes'`

**Solution:** Python 3.13 removed the `pipes` module. You must use Python 3.11 or 3.10.

### Issue 2: JupyterLab Version Conflict

**Error:** `crystaltoolkit-extension requires jupyterlab==3.*`

**Solution:** Crystal-toolkit requires JupyterLab 3.x, not 4.x:
```powershell
pip install jupyterlab==3.6.8 notebook==6.5.7
```

### Issue 3: Import Error with crystal_toolkit

**Error:** `ImportError: cannot import name 'SymmetryUndeterminedError'`

**Solution:** Apply the sitecustomize.py patch (see Step 5) and downgrade mp-api:
```powershell
pip install mp-api==0.41.2
```

### Issue 4: Long Paths in OneDrive

If you encounter issues with long paths in OneDrive:

1. Move project to a shorter path (e.g., `C:\Research\algaas`)
2. Or enable long paths in Windows:
   - Run as Administrator: `New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force`

---

## Verification

### Check for Conflicts

```powershell
pip check
```

**Expected output:** `No broken requirements found.`

### Test All Imports

```powershell
python -c "import crystal_toolkit; import pymatgen; import ase; import torch; import jarvis; print('✅ All libraries imported successfully!')"
```

### Detailed Component Test

```powershell
python -c "from pymatgen.core import Structure, Lattice; print('Pymatgen OK ✅'); import torch; print(f'PyTorch {torch.__version__} OK ✅'); from ase import Atoms; print('ASE OK ✅')"
```

---

## Final Installed Versions

After successful installation, you should have:

- **crystal-toolkit**: 2023.11.3
- **pymatgen**: 2024.8.9
- **mp-api**: 0.41.2 (downgraded for compatibility)
- **ase**: 3.26.0
- **torch**: 2.8.0+cpu (or +cu121/cu118)
- **torch-geometric**: 2.6.1
- **jarvis-tools**: 2025.5.30
- **dash**: 3.2.0
- **plotly**: 6.3.1
- **jupyterlab**: 3.6.8

---

## Important Files

### requirements-locked.txt
Contains exact versions of all installed packages. Use this for reproducibility:
```powershell
pip install -r requirements-locked.txt
```

### sitecustomize.py
Located at `venv\Lib\site-packages\sitecustomize.py`

**⚠️ DO NOT DELETE THIS FILE!** It contains the compatibility patch that runs automatically on Python startup.

---

## Alternative: Using requirements.txt

If you have a `requirements-locked.txt` from a working setup:

```powershell
# Create new environment
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1

# Install from locked requirements
pip install -r requirements-locked.txt

# Apply the patch (if needed)
# ... (follow Step 5 above)
```

---

## Notes

1. **Virtual Environment Isolation**: Always activate the virtual environment before working on the project
2. **Python Version**: Stick with Python 3.11 for maximum compatibility
3. **Updates**: Be cautious when updating packages, as version conflicts are common in this ecosystem
4. **GPU Support**: If you have NVIDIA GPU, use CUDA-enabled PyTorch for better performance

---

## Quick Reference Commands

```powershell
# Activate environment
.\venv\Scripts\Activate.ps1

# Deactivate environment
deactivate

# Check installed packages
pip list

# Check for conflicts
pip check

# Update a specific package
pip install --upgrade package_name

# Export current environment
pip freeze > requirements.txt

# Remove virtual environment
deactivate
Remove-Item -Recurse -Force venv
```

---

**Last Updated:** October 9, 2025  
**Python Version:** 3.11.x  
**Platform:** Windows (PowerShell)