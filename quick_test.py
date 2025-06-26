
#!/usr/bin/env python3
"""Quick test to verify fixes"""

import os
import sys

def test_imports():
    """Test if critical modules can be imported"""
    try:
        print("🔍 Testing imports...")
        
        # Test arbitrum agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        print("✅ ArbitrumTestnetAgent import successful")
        
        # Test web dashboard
        from web_dashboard import app
        print("✅ Web dashboard import successful")
        
        return True
    except SyntaxError as e:
        print(f"❌ Syntax Error: {e}")
        return False
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def check_environment():
    """Check environment variables"""
    print("\n🌍 Checking environment...")
    required_vars = ['NETWORK_MODE', 'PRIVATE_KEY']
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing")

if __name__ == "__main__":
    print("🚀 Quick System Test")
    print("=" * 40)
    
    imports_ok = test_imports()
    check_environment()
    
    if imports_ok:
        print("\n✅ Basic tests passed!")
        print("💡 Try running: python web_dashboard.py")
    else:
        print("\n❌ Critical errors found")
        print("💡 Check syntax errors above")
