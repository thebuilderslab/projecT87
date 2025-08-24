
#!/usr/bin/env python3
"""
Test the API functions directly without HTTP layer
"""

import sys
import os
import json
import time

# Add current directory to path to import web_dashboard
sys.path.append('.')

def test_api_functions_directly():
    """Test the actual API functions directly"""
    print("🔍 TESTING API FUNCTIONS DIRECTLY")
    print("="*50)
    
    try:
        # Import the web dashboard module
        import web_dashboard
        
        print("✅ web_dashboard module imported successfully")
        
        # Test get_parameters function directly
        print("\n📊 Testing get_parameters() function:")
        try:
            with web_dashboard.app.app_context():
                params_response = web_dashboard.get_parameters()
                print(f"✅ get_parameters() returned: {type(params_response)}")
                
                # Extract JSON data from Flask response
                if hasattr(params_response, 'get_json'):
                    params_data = params_response.get_json()
                elif hasattr(params_response, 'data'):
                    params_data = json.loads(params_response.data.decode())
                else:
                    params_data = params_response
                    
                print(f"📄 Parameters data: {json.dumps(params_data, indent=2)}")
                
        except Exception as e:
            print(f"❌ get_parameters() failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test get_emergency_status function directly
        print("\n🚨 Testing get_emergency_status() function:")
        try:
            with web_dashboard.app.app_context():
                emergency_response = web_dashboard.get_emergency_status()
                print(f"✅ get_emergency_status() returned: {type(emergency_response)}")
                
                # Extract JSON data from Flask response
                if hasattr(emergency_response, 'get_json'):
                    emergency_data = emergency_response.get_json()
                elif hasattr(emergency_response, 'data'):
                    emergency_data = json.loads(emergency_response.data.decode())
                else:
                    emergency_data = emergency_response
                    
                print(f"🚨 Emergency data: {json.dumps(emergency_data, indent=2)}")
                
        except Exception as e:
            print(f"❌ get_emergency_status() failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test agent initialization
        print(f"\n🤖 Testing agent initialization:")
        print(f"   Agent object exists: {web_dashboard.agent is not None}")
        print(f"   Dashboard object exists: {web_dashboard.dashboard is not None}")
        
        if web_dashboard.agent:
            try:
                print(f"   Agent address: {web_dashboard.agent.address}")
                print(f"   Agent network: {web_dashboard.agent.w3.eth.chain_id}")
            except Exception as e:
                print(f"   Agent details error: {e}")
        
        # Test environment variables
        print(f"\n🌍 Environment variables:")
        env_vars = ['NETWORK_MODE', 'PRIVATE_KEY', 'COINMARKETCAP_API_KEY']
        for var in env_vars:
            value = os.getenv(var)
            if value:
                if var == 'PRIVATE_KEY':
                    print(f"   {var}: {'*' * 10}...{value[-4:] if len(value) > 14 else '****'}")
                elif var == 'COINMARKETCAP_API_KEY':
                    print(f"   {var}: {'*' * 8}...{value[-4:] if len(value) > 12 else '****'}")
                else:
                    print(f"   {var}: {value}")
            else:
                print(f"   {var}: NOT SET")
                
    except ImportError as e:
        print(f"❌ Could not import web_dashboard: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_functions_directly()
