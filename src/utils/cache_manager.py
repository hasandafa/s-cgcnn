"""
Cache management utilities for the AlGaAs pipeline.

This module provides functionality to manage cached data, check for
existing files, and handle cache invalidation based on timestamps.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached data entry."""
    key: str
    timestamp: datetime
    file_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    size_bytes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class CacheManager:
    """Manages caching of data files and metadata."""

    def __init__(self, cache_dir: str = "cache/", metadata_file: str = "cache_metadata.json"):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cached files
            metadata_file: File to store cache metadata
        """
        self.cache_dir = Path(cache_dir)
        self.metadata_file = self.cache_dir / metadata_file
        self.entries: Dict[str, CacheEntry] = {}

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load existing metadata
        self._load_metadata()

    def _load_metadata(self):
        """Load cache metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, entry_data in data.items():
                        self.entries[key] = CacheEntry.from_dict(entry_data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not load cache metadata: {e}")
                self.entries = {}

    def _save_metadata(self):
        """Save cache metadata to file."""
        data = {key: entry.to_dict() for key, entry in self.entries.items()}
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _generate_key(self, identifier: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a unique cache key.

        Args:
            identifier: Base identifier for the cache entry
            params: Additional parameters to include in key generation

        Returns:
            Unique cache key
        """
        key_parts = [identifier]

        if params:
            # Sort parameters for consistent key generation
            sorted_params = sorted(params.items())
            param_str = json.dumps(sorted_params, sort_keys=True)
            key_parts.append(param_str)

        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def is_cached(self, key: str, max_age_days: Optional[int] = None) -> bool:
        """
        Check if a cache entry exists and is still valid.

        Args:
            key: Cache key to check
            max_age_days: Maximum age in days (None for no age limit)

        Returns:
            True if cached and valid, False otherwise
        """
        if key not in self.entries:
            return False

        entry = self.entries[key]

        # Check if file still exists
        if entry.file_path and not Path(entry.file_path).exists():
            self.remove_entry(key)
            return False

        # Check age if specified
        if max_age_days is not None:
            age = datetime.now() - entry.timestamp
            if age > timedelta(days=max_age_days):
                return False

        return True

    def get_entry(self, key: str) -> Optional[CacheEntry]:
        """
        Get a cache entry by key.

        Args:
            key: Cache key

        Returns:
            CacheEntry if exists, None otherwise
        """
        return self.entries.get(key)

    def add_entry(self, key: str, file_path: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None):
        """
        Add or update a cache entry.

        Args:
            key: Cache key
            file_path: Path to cached file
            metadata: Additional metadata
        """
        size_bytes = None
        if file_path and Path(file_path).exists():
            size_bytes = Path(file_path).stat().st_size

        entry = CacheEntry(
            key=key,
            timestamp=datetime.now(),
            file_path=file_path,
            metadata=metadata,
            size_bytes=size_bytes
        )

        self.entries[key] = entry
        self._save_metadata()

    def remove_entry(self, key: str):
        """
        Remove a cache entry.

        Args:
            key: Cache key to remove
        """
        if key in self.entries:
            entry = self.entries[key]
            # Remove the file if it exists
            if entry.file_path and Path(entry.file_path).exists():
                try:
                    Path(entry.file_path).unlink()
                except OSError as e:
                    logger.warning(f"Could not remove cached file {entry.file_path}: {e}")

            del self.entries[key]
            self._save_metadata()

    def clear_cache(self, pattern: Optional[str] = None):
        """
        Clear all cache entries, optionally matching a pattern.

        Args:
            pattern: Pattern to match keys (None for all)
        """
        keys_to_remove = []

        for key in self.entries:
            if pattern is None or pattern in key:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self.remove_entry(key)

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self.entries)
        total_size = sum(entry.size_bytes or 0 for entry in self.entries.values())

        # Count entries by age
        now = datetime.now()
        age_counts = {
            '1_day': 0,
            '1_week': 0,
            '1_month': 0,
            'older': 0
        }

        for entry in self.entries.values():
            age_days = (now - entry.timestamp).days
            if age_days <= 1:
                age_counts['1_day'] += 1
            elif age_days <= 7:
                age_counts['1_week'] += 1
            elif age_days <= 30:
                age_counts['1_month'] += 1
            else:
                age_counts['older'] += 1

        return {
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'entries_by_age': age_counts
        }

    def list_entries(self, pattern: Optional[str] = None) -> List[CacheEntry]:
        """
        List cache entries, optionally filtered by pattern.

        Args:
            pattern: Pattern to filter keys

        Returns:
            List of matching cache entries
        """
        entries = []
        for key, entry in self.entries.items():
            if pattern is None or pattern in key:
                entries.append(entry)
        return entries

    def cleanup_old_entries(self, max_age_days: int):
        """
        Remove cache entries older than specified days.

        Args:
            max_age_days: Maximum age in days
        """
        cutoff = datetime.now() - timedelta(days=max_age_days)
        keys_to_remove = []

        for key, entry in self.entries.items():
            if entry.timestamp < cutoff:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self.remove_entry(key)

        if keys_to_remove:
            logger.info(f"Cleaned up {len(keys_to_remove)} old cache entries")


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def check_cache(key: str, max_age_days: Optional[int] = None) -> bool:
    """Check if data is cached and valid."""
    return get_cache_manager().is_cached(key, max_age_days)