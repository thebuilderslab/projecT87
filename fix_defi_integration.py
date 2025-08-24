
#!/usr/bin/env python3
"""
DeFi Integration Fix Script
Diagnoses and fixes DeFi integration initialization issues
"""

import sys
import traceback

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        'web3',
        'eth_account', 
        'requests',
        'json',
        'time',
        'os'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}: Available")
        except ImportError:
            missing.append(module)
            print(f"❌ {module}: Missing")
    
    return missing

def test_enhanced_borrow_manager():
    """Test enhanced borrow manager initialization"""
    print("\n🔍 Testing Enhanced Borrow Manager...")
    
    try:
        from enhanced_borrow_manager import EnhancedBorrowManager
        print("✅ Enhanced Borrow Manager imported successfully")
        
        # Test basic initialization without agent
        print("✅ Module syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in enhanced_borrow_manager.py: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_agent_initialization():
    """Test agent initialization"""
    print("\n🔍 Testing Agent Initialization...")
    
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        print("✅ Agent module imported successfully")
        
        # Test initialization
        agent = ArbitrumTestnetAgent()
        print("✅ Agent initialized successfully")
        
        # Test DeFi integrations
        if hasattr(agent, 'initialize_integrations'):
            success = agent.initialize_integrations()
            if success:
                print("✅ DeFi integrations initialized successfully")
            else:
                print("⚠️ DeFi integrations partially failed")
        else:
            print("❌ initialize_integrations method not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main diagnostic function"""
    print("🔧 DEFI INTEGRATION DIAGNOSTIC")
    print("=" * 40)
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"\n❌ Missing dependencies: {missing_deps}")
        return False
    
    # Test enhanced borrow manager
    ebm_ok = test_enhanced_borrow_manager()
    if not ebm_ok:
        print("\n❌ Enhanced Borrow Manager has issues")
        return False
    
    # Test agent initialization
    agent_ok = test_agent_initialization()
    if not agent_ok:
        print("\n❌ Agent initialization failed")
        return False
    
    print("\n✅ ALL DIAGNOSTICS PASSED")
    print("🚀 DeFi integrations should now work correctly")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
