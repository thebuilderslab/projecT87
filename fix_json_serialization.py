
<line_number>1</line_number>
#!/usr/bin/env python3
"""
Fix JSON serialization issues with Decimal types
"""

import json
import decimal

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types"""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def safe_json_dump(data, file_path):
    """Safely dump data to JSON file with Decimal handling"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, cls=DecimalEncoder, indent=2)
        return True
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False

def safe_json_dumps(data):
    """Safely convert data to JSON string with Decimal handling"""
    try:
        return json.dumps(data, cls=DecimalEncoder, indent=2)
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return "{}"
