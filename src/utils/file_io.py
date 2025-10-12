"""
File I/O Utilities for s-CGCNN v0.2

Helper functions for reading/writing files safely.

Author: Abdullah Hasan Dafa
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Union, Optional
import shutil


# ============================================================================
# JSON OPERATIONS
# ============================================================================

def read_json(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Read JSON file safely.
    
    Args:
        filepath: Path to JSON file
    
    Returns:
        Dictionary from JSON
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def write_json(
    data: Dict[str, Any],
    filepath: Union[str, Path],
    pretty: bool = True,
    create_dirs: bool = True
):
    """
    Write dictionary to JSON file.
    
    Args:
        data: Dictionary to write
        filepath: Output file path
        pretty: Use indentation for readability
        create_dirs: Create parent directories if needed
    """
    filepath = Path(filepath)
    
    if create_dirs:
        filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)


def append_to_json_list(
    item: Any,
    filepath: Union[str, Path],
    create_if_missing: bool = True
):
    """
    Append item to JSON file containing a list.
    
    Args:
        item: Item to append
        filepath: Path to JSON file
        create_if_missing: Create file if doesn't exist
    """
    filepath = Path(filepath)
    
    if filepath.exists():
        data = read_json(filepath)
        if not isinstance(data, list):
            raise ValueError(f"JSON file must contain a list, got {type(data)}")
    elif create_if_missing:
        data = []
    else:
        raise FileNotFoundError(f"File not found: {filepath}")
    
    data.append(item)
    write_json(data, filepath)


# ============================================================================
# YAML OPERATIONS
# ============================================================================

def read_yaml(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Read YAML file safely.
    
    Args:
        filepath: Path to YAML file
    
    Returns:
        Dictionary from YAML
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"YAML file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    return data


def write_yaml(
    data: Dict[str, Any],
    filepath: Union[str, Path],
    create_dirs: bool = True
):
    """
    Write dictionary to YAML file.
    
    Args:
        data: Dictionary to write
        filepath: Output file path
        create_dirs: Create parent directories if needed
    """
    filepath = Path(filepath)
    
    if create_dirs:
        filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# ============================================================================
# TEXT FILE OPERATIONS
# ============================================================================

def read_text(filepath: Union[str, Path]) -> str:
    """Read text file safely."""
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Text file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content


def write_text(
    content: str,
    filepath: Union[str, Path],
    create_dirs: bool = True
):
    """Write text to file."""
    filepath = Path(filepath)
    
    if create_dirs:
        filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def read_lines(filepath: Union[str, Path]) -> List[str]:
    """Read text file as list of lines."""
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Text file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Strip newline characters
    return [line.rstrip('\n') for line in lines]


def write_lines(
    lines: List[str],
    filepath: Union[str, Path],
    create_dirs: bool = True
):
    """Write list of lines to file."""
    filepath = Path(filepath)
    
    if create_dirs:
        filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')


# ============================================================================
# DIRECTORY OPERATIONS
# ============================================================================

def ensure_dir(dirpath: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if needed.
    
    Args:
        dirpath: Directory path
    
    Returns:
        Path object for the directory
    """
    dirpath = Path(dirpath)
    dirpath.mkdir(parents=True, exist_ok=True)
    return dirpath


def list_files(
    dirpath: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    List files in directory matching pattern.
    
    Args:
        dirpath: Directory path
        pattern: Glob pattern (e.g., "*.json")
        recursive: Search subdirectories
    
    Returns:
        List of Path objects
    """
    dirpath = Path(dirpath)
    
    if not dirpath.exists():
        return []
    
    if recursive:
        return list(dirpath.rglob(pattern))
    else:
        return list(dirpath.glob(pattern))


def count_files(
    dirpath: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> int:
    """Count files matching pattern in directory."""
    return len(list_files(dirpath, pattern, recursive))


def clear_directory(
    dirpath: Union[str, Path],
    pattern: str = "*",
    confirm: bool = True
):
    """
    Delete all files matching pattern in directory.
    
    Args:
        dirpath: Directory path
        pattern: Glob pattern
        confirm: Require confirmation (safety check)
    """
    dirpath = Path(dirpath)
    
    if not dirpath.exists():
        return
    
    files = list_files(dirpath, pattern, recursive=False)
    
    if confirm and len(files) > 0:
        print(f"About to delete {len(files)} files from {dirpath}")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    for file in files:
        file.unlink()


# ============================================================================
# SAFE FILE OPERATIONS
# ============================================================================

def safe_copy(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = False
) -> bool:
    """
    Copy file safely.
    
    Args:
        src: Source file
        dst: Destination file
        overwrite: Overwrite if exists
    
    Returns:
        True if copied, False if skipped
    """
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    
    if dst.exists() and not overwrite:
        return False
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def safe_move(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = False
) -> bool:
    """
    Move file safely.
    
    Args:
        src: Source file
        dst: Destination file
        overwrite: Overwrite if exists
    
    Returns:
        True if moved, False if skipped
    """
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    
    if dst.exists() and not overwrite:
        return False
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return True


def backup_file(filepath: Union[str, Path], suffix: str = ".bak") -> Path:
    """
    Create backup copy of file.
    
    Args:
        filepath: File to backup
        suffix: Backup file suffix
    
    Returns:
        Path to backup file
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    backup_path = filepath.with_suffix(filepath.suffix + suffix)
    shutil.copy2(filepath, backup_path)
    
    return backup_path


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

def batch_rename(
    dirpath: Union[str, Path],
    old_pattern: str,
    new_pattern: str,
    dry_run: bool = True
) -> List[tuple]:
    """
    Batch rename files in directory.
    
    Args:
        dirpath: Directory path
        old_pattern: Pattern to match
        new_pattern: Replacement pattern
        dry_run: If True, only show what would be renamed
    
    Returns:
        List of (old_path, new_path) tuples
    """
    dirpath = Path(dirpath)
    files = list_files(dirpath, old_pattern)
    
    renames = []
    
    for old_file in files:
        new_name = old_file.name.replace(old_pattern.replace("*", ""), new_pattern)
        new_file = old_file.parent / new_name
        renames.append((old_file, new_file))
        
        if not dry_run:
            old_file.rename(new_file)
    
    return renames


# ============================================================================
# FILE VALIDATION
# ============================================================================

def validate_file_exists(filepath: Union[str, Path], file_type: str = "File"):
    """Validate file exists, raise error if not."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"{file_type} not found: {filepath}")


def validate_dir_exists(dirpath: Union[str, Path], dir_type: str = "Directory"):
    """Validate directory exists, raise error if not."""
    dirpath = Path(dirpath)
    if not dirpath.exists():
        raise FileNotFoundError(f"{dir_type} not found: {dirpath}")
    if not dirpath.is_dir():
        raise NotADirectoryError(f"Not a directory: {dirpath}")


def get_file_size(filepath: Union[str, Path]) -> int:
    """Get file size in bytes."""
    filepath = Path(filepath)
    return filepath.stat().st_size


def get_file_size_mb(filepath: Union[str, Path]) -> float:
    """Get file size in MB."""
    return get_file_size(filepath) / (1024 * 1024)

"""
Add these functions to your src/utils/file_io.py file
"""

from pymatgen.core import Structure
from pathlib import Path
from typing import Union


def load_structure_from_cif(cif_path: Union[str, Path]) -> Structure:
    """
    Load crystal structure from CIF file.
    
    Args:
        cif_path: Path to CIF file
        
    Returns:
        Structure: Pymatgen Structure object
        
    Raises:
        FileNotFoundError: If CIF file doesn't exist
        ValueError: If CIF file is invalid
        
    Example:
        >>> structure = load_structure_from_cif('data/structures/cif/AlGaAs_x0.500.cif')
        >>> print(structure.formula)
        Al0.5Ga0.5As
    """
    cif_path = Path(cif_path)
    
    if not cif_path.exists():
        raise FileNotFoundError(f"CIF file not found: {cif_path}")
    
    try:
        structure = Structure.from_file(str(cif_path))
        return structure
    except Exception as e:
        raise ValueError(f"Failed to load CIF file {cif_path}: {e}")


def save_structure_to_cif(structure: Structure, output_path: Union[str, Path]):
    """
    Save crystal structure to CIF file.
    
    Args:
        structure: Pymatgen Structure object
        output_path: Output CIF file path
        
    Example:
        >>> save_structure_to_cif(structure, 'output/my_structure.cif')
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    structure.to(filename=str(output_path), fmt='cif')

# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "0.1.1"
__author__ = "Abdullah Hasan Dafa"

__all__ = [
    # JSON
    "read_json",
    "write_json",
    "append_to_json_list",
    # YAML
    "read_yaml",
    "write_yaml",
    # Text
    "read_text",
    "write_text",
    "read_lines",
    "write_lines",
    # Directory
    "ensure_dir",
    "list_files",
    "count_files",
    "clear_directory",
    # Safe operations
    "safe_copy",
    "safe_move",
    "backup_file",
    # Batch
    "batch_rename",
    # Validation
    "validate_file_exists",
    "validate_dir_exists",
    "get_file_size",
    "get_file_size_mb",
]