
#!/usr/bin/env python3
"""
System Validation Script
Validates all components are working properly before deployment
"""

import sys
import os
import ast

def validate_syntax(file_path):
    """Validate Python file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file to check for syntax errors
        ast.parse(content)
        print(f"✅ {file_path}: Syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ {file_path}: Syntax Error - {e}")
        return False
    except Exception as e:
        print(f"⚠️ {file_path}: Could not validate - {e}")
        return False

def validate_imports():
    """Validate that main.py can import successfully"""
    try:
        import main
        print("✅ main.py: Import successful")
        return True
    except Exception as e:
        print(f"❌ main.py: Import failed - {e}")
        return False

def validate_secrets():
    """Validate required secrets are available"""
    required_secrets = [
        'NETWORK_MODE', 'COINMARKETCAP_API_KEY', 'PROMPT_KEY', 
        'PRIVATE_KEY', 'ARBITRUM_RPC_URL'
    ]
    
    all_valid = True
    for secret in required_secrets:
        value = os.getenv(secret)
        if value:
            print(f"✅ {secret}: Available")
        else:
            print(f"❌ {secret}: Missing")
            all_valid = False
    
    return all_valid

def validate_network_approval_requirements():
    """Validate specific network approval requirements"""
    print("\n🌐 Network Approval Requirements:")
    
    # Check for comprehensive audit capability
    try:
        from comprehensive_syntax_validator import ComprehensiveSyntaxValidator
        print("✅ Comprehensive audit system: Available")
        audit_available = True
    except ImportError:
        print("❌ Comprehensive audit system: Not available")
        audit_available = False
    
    # Check for network approval validator
    network_validator_exists = os.path.exists('network_approval_validator.py')
    if network_validator_exists:
        print("✅ Network approval validator: Available")
    else:
        print("❌ Network approval validator: Missing")
    
    # Check mainnet readiness
    network_mode = os.getenv('NETWORK_MODE', 'testnet')
    if network_mode.lower() == 'mainnet':
        print("✅ Network mode: Mainnet ready")
        mainnet_ready = True
    else:
        print(f"⚠️  Network mode: {network_mode} (not mainnet)")
        mainnet_ready = False
    
    return audit_available and network_validator_exists and mainnet_ready

def main():
    """Run complete system validation with network approval check"""
    print("🔍 ENHANCED SYSTEM VALIDATION")
    print("=" * 50)
    
    all_passed = True
    
    # 1. Syntax validation
    print("\n📝 Syntax Validation:")
    if not validate_syntax('main.py'):
        all_passed = False
    
    # 2. Import validation
    print("\n📦 Import Validation:")
    if not validate_imports():
        all_passed = False
    
    # 3. Secrets validation
    print("\n🔐 Secrets Validation:")
    if not validate_secrets():
        all_passed = False
    
    # 4. Network approval requirements
    network_ready = validate_network_approval_requirements()
    if not network_ready:
        print("\n⚠️  Network approval requirements not fully met")
    
    print("\n" + "=" * 50)
    if all_passed and network_ready:
        print("✅ SYSTEM VALIDATION PASSED")
        print("🎉 NETWORK APPROVAL READY")
        print("🚀 Ready for mainnet deployment")
        return True
    elif all_passed:
        print("✅ BASIC VALIDATION PASSED")
        print("⚠️  Network approval requirements need attention")
        print("🔧 Run network approval validator for full assessment")
        return True
    else:
        print("❌ SYSTEM VALIDATION FAILED")
        print("🛑 Fix critical issues before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
