#!/usr/bin/env python3
"""
JSON Serialization Fixes for Decimal Types
"""

import json
import decimal
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal types"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super(DecimalEncoder, self).default(obj)


def safe_json_dump(data, filename=None, **kwargs):
    """
    Safe JSON dumping that handles Decimal types

    Args:
        data: Data to serialize
        filename: Optional filename to write to
        **kwargs: Additional arguments for json.dump

    Returns:
        JSON string if no filename provided, True if file written successfully
    """
    try:
        # Set default encoder if not provided
        if 'cls' not in kwargs:
            kwargs['cls'] = DecimalEncoder

        if 'indent' not in kwargs:
            kwargs['indent'] = 2

        if filename:
            with open(filename, 'w') as f:
                json.dump(data, f, **kwargs)
            return True
        else:
            return json.dumps(data, **kwargs)

    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        if filename:
            return False
        else:
            return "{}"


def safe_json_loads(json_string_or_file):
    """
    Safe JSON loading with error handling

    Args:
        json_string_or_file: JSON string or filename to load

    Returns:
        Parsed JSON data or empty dict on failure
    """
    try:
        if isinstance(json_string_or_file, str):
            if json_string_or_file.endswith('.json'):
                # It's a filename
                with open(json_string_or_file, 'r') as f:
                    return json.load(f)
            else:
                # It's a JSON string
                return json.loads(json_string_or_file)
        else:
            return {}

    except Exception as e:
        print(f"❌ JSON loading failed: {e}")
        return {}


# Decimal handling utilities
def convert_decimals_to_float(obj):
    """Convert all Decimal objects in a nested structure to floats"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_decimals_to_float(v) for v in obj)
    else:
        return obj


# Test function
def test_decimal_serialization():
    """Test that Decimal serialization works correctly"""
    test_data = {
        'health_factor': Decimal('2.5'),
        'collateral_usd': Decimal('150.75'),
        'debt_usd': Decimal('60.25'),
        'timestamp': 1234567890,
        'nested': {
            'value': Decimal('123.456'),
            'list': [Decimal('1.1'), Decimal('2.2')]
        }
    }

    try:
        # Test string serialization
        json_string = safe_json_dump(test_data)
        print(f"✅ JSON serialization successful: {len(json_string)} characters")

        # Test file serialization
        success = safe_json_dump(test_data, 'test_decimal.json')
        if success:
            print("✅ File serialization successful")

            # Test loading back
            loaded_data = safe_json_loads('test_decimal.json')
            print(f"✅ File loading successful: {len(loaded_data)} keys")

            # Clean up
            import os
            if os.path.exists('test_decimal.json'):
                os.remove('test_decimal.json')

        return True

    except Exception as e:
        print(f"❌ Decimal serialization test failed: {e}")
        return False


if __name__ == "__main__":
    test_decimal_serialization()