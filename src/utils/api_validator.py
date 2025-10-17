"""
API validation utilities for Materials Project API.

This module provides functionality to validate API keys and test
connectivity to the Materials Project API using the official mp-api package.
"""

from typing import Optional, Tuple
from pathlib import Path
from mp_api.client import MPRester


class APIValidator:
    """Handles validation of Materials Project API credentials."""

    def __init__(self, api_key: Optional[str] = None, key_file: str = "key.env"):
        """
        Initialize the API validator.

        Args:
            api_key: Direct API key (optional, will load from file if not provided)
            key_file: Path to file containing API key
        """
        self.api_key = api_key or self._load_api_key(key_file)

    def _load_api_key(self, key_file: str) -> str:
        """
        Load API key from environment file.

        Args:
            key_file: Path to the key file

        Returns:
            API key string

        Raises:
            FileNotFoundError: If key file doesn't exist
            ValueError: If mp_api key not found in file
        """
        key_path = Path(key_file)

        if not key_path.exists():
            raise FileNotFoundError(f"API key file not found: {key_path}")

        # Read the key.env file
        with open(key_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # Parse the key (format: mp_api = <key>)
        if '=' not in content:
            raise ValueError(f"Invalid key file format. Expected 'mp_api = <key>', got: {content}")

        key_name, key_value = content.split('=', 1)
        key_name = key_name.strip()
        key_value = key_value.strip()

        if key_name != 'mp_api':
            raise ValueError(f"Expected key name 'mp_api', got '{key_name}'")

        if not key_value:
            raise ValueError("API key value is empty")

        return key_value

    def validate_api_key(self) -> Tuple[bool, str]:
        """
        Validate the API key by making a test request using mp-api.

        Returns:
            Tuple of (is_valid, message)
        """
        if not self.api_key:
            return False, "No API key provided"

        try:
            # Use MPRester to validate the API key
            with MPRester(self.api_key) as mpr:
                # Try to fetch a simple material (Silicon)
                material = mpr.materials.summary.search(
                    material_ids=["mp-149"],
                    fields=["material_id", "formula_pretty"]
                )
                
                if material and len(material) > 0:
                    formula = material[0].formula_pretty
                    mat_id = material[0].material_id
                    return True, f"API key valid. Successfully connected to Materials Project (tested with {formula}, {mat_id})"
                else:
                    return False, "API key accepted but no data returned"

        except ValueError as e:
            # MPRester raises ValueError for invalid API keys
            if "API key" in str(e).lower() or "invalid" in str(e).lower():
                return False, f"Invalid API key: {str(e)}"
            return False, f"Validation error: {str(e)}"
        except ConnectionError as e:
            return False, f"Connection error: {str(e)}"
        except TimeoutError as e:
            return False, f"Request timed out: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error during API validation: {str(e)}"

    def test_connectivity(self) -> Tuple[bool, str]:
        """
        Test basic connectivity to Materials Project API.

        Returns:
            Tuple of (is_connected, message)
        """
        try:
            # Test connectivity by attempting to create an MPRester instance
            # and making a simple query
            with MPRester(self.api_key) as mpr:
                # Try to get available fields to test connectivity
                # This is a lightweight operation
                material = mpr.materials.summary.search(
                    material_ids=["mp-149"],
                    fields=["material_id"]
                )
                if material:
                    return True, "Successfully connected to Materials Project API"
                else:
                    return False, "Connected but unable to retrieve data"
                    
        except ConnectionError:
            return False, "Connection failed - check internet connection"
        except TimeoutError:
            return False, "Connection timed out"
        except Exception as e:
            return False, f"Connectivity test failed: {str(e)}"


def validate_mp_api(api_key: Optional[str] = None, key_file: str = "key.env") -> Tuple[bool, str]:
    """
    Convenience function to validate Materials Project API key.

    Args:
        api_key: Direct API key (optional)
        key_file: Path to key file

    Returns:
        Tuple of (is_valid, message)
    """
    validator = APIValidator(api_key, key_file)
    return validator.validate_api_key()


def test_mp_connectivity(api_key: Optional[str] = None, key_file: str = "key.env") -> Tuple[bool, str]:
    """
    Convenience function to test Materials Project API connectivity.

    Args:
        api_key: Direct API key (optional)
        key_file: Path to key file

    Returns:
        Tuple of (is_connected, message)
    """
    validator = APIValidator(api_key, key_file)
    return validator.test_connectivity()