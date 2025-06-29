
#!/usr/bin/env python3
"""
Fix Private Key Issue
Diagnostic script to identify and fix private key problems
"""

import os
from dotenv import load_dotenv

def check_private_key():
    """Check and validate private key format"""
    print("🔍 PRIVATE KEY DIAGNOSTIC")
    print("=" * 40)
    
    # Load environment
    load_dotenv()
    
    # Check both possible private key environment variables
    private_key = os.getenv('PRIVATE_KEY2') or os.getenv('PRIVATE_KEY')
    
    if not private_key:
        print("❌ No private key found in environment variables")
        print("💡 Please set PRIVATE_KEY in Replit Secrets")
        print("💡 Go to Secrets tab and add:")
        print("   Key: PRIVATE_KEY")
        print("   Value: your 64-character hex private key")
        return False
    
    print(f"✅ Private key found: {len(private_key)} characters")
    
    # Clean the private key
    original_key = private_key
    private_key = private_key.strip()
    
    if private_key != original_key:
        print(f"⚠️ Removed whitespace from private key")
    
    # Check for 0x prefix
    has_prefix = private_key.startswith('0x')
    if has_prefix:
        hex_part = private_key[2:]
        print(f"✅ Private key has 0x prefix")
    else:
        hex_part = private_key
        print(f"ℹ️ Private key has no 0x prefix (this is fine)")
    
    # Check length
    if len(hex_part) != 64:
        print(f"❌ Invalid hex length: {len(hex_part)} (expected 64)")
        print(f"💡 Your private key should be exactly 64 hexadecimal characters")
        if len(hex_part) < 64:
            print(f"💡 Your key is too short by {64 - len(hex_part)} characters")
        else:
            print(f"💡 Your key is too long by {len(hex_part) - 64} characters")
        return False
    
    # Check if it's valid hex
    try:
        int(hex_part, 16)
        print(f"✅ Private key is valid hexadecimal")
    except ValueError as e:
        print(f"❌ Private key contains invalid characters: {e}")
        print(f"💡 Private key should only contain: 0-9, a-f, A-F")
        
        # Find invalid characters
        valid_chars = set('0123456789abcdefABCDEF')
        invalid_chars = set(hex_part) - valid_chars
        if invalid_chars:
            print(f"💡 Invalid characters found: {', '.join(sorted(invalid_chars))}")
        return False
    
    print(f"✅ Private key format is valid!")
    print(f"🔐 Key preview: {hex_part[:8]}...{hex_part[-8:]}")
    
    return True

def main():
    """Main diagnostic function"""
    if check_private_key():
        print("\n🎉 Private key validation passed!")
        print("💡 Try running the dashboard again")
    else:
        print("\n❌ Private key validation failed")
        print("💡 Please fix the private key in Replit Secrets")
        print("💡 After fixing, run this script again to verify")

if __name__ == "__main__":
    main()
