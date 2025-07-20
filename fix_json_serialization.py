#!/usr/bin/env python3
"""
JSON Serialization Fix Module
Handles serialization of Decimal types and other complex objects
"""

import json
import os
from decimal import Decimal
from datetime import datetime

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal types"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Handle custom objects by converting to dict
            return obj.__dict__
        return super(DecimalEncoder, self).default(obj)

def safe_json_dump(data, filename):
    """Safely dump data to JSON file with proper error handling"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

        # Write with custom encoder
        with open(filename, 'w') as f:
            json.dump(data, f, cls=DecimalEncoder, indent=2)

        return True

    except Exception as e:
        print(f"❌ JSON serialization failed for {filename}: {e}")
        return False

def safe_json_load(filename):
    """Safely load data from JSON file"""
    try:
        if not os.path.exists(filename):
            return None

        with open(filename, 'r') as f:
            return json.load(f)

    except Exception as e:
        print(f"❌ JSON deserialization failed for {filename}: {e}")
        return None

def test_serialization():
    """Test the serialization functionality"""
    try:
        test_data = {
            'decimal_value': Decimal('123.456'),
            'timestamp': datetime.now(),
            'regular_float': 789.123,
            'string_value': 'test'
        }

        # Test serialization
        success = safe_json_dump(test_data, 'test_serialization.json')

        if success:
            # Test deserialization
            loaded_data = safe_json_load('test_serialization.json')

            if loaded_data:
                print("✅ JSON serialization test passed")
                # Cleanup
                os.remove('test_serialization.json')
                return True

        print("❌ JSON serialization test failed")
        return False

    except Exception as e:
        print(f"❌ Serialization test error: {e}")
        return False

if __name__ == "__main__":
    test_serialization()
"""
JSON Serialization Fix
Handles Decimal and other non-serializable types for JSON output
"""

import json
import decimal
from typing import Any, Dict

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types"""
    
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def safe_json_dump(data: Dict[str, Any], filename: str) -> bool:
    """Safely dump data to JSON file with Decimal handling"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, cls=DecimalEncoder, indent=2)
        return True
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False

def safe_json_loads(filename: str) -> Dict[str, Any]:
    """Safely load JSON data from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ JSON deserialization failed: {e}")
        return {}

print("✅ JSON serialization fix loaded")
