#!/usr/bin/env python3
"""
AAVE ADAPTER ABI VALIDATION SCRIPT
Validates the correct ABI and function signatures for debt swap adapters on Arbitrum mainnet.
Resolves discrepancies between different adapter addresses and ABI structures.
"""

import os
from web3 import Web3
import json

def validate_adapter_abi():
    """Validate both adapter addresses and their supported functions"""
    
    print("🔍 AAVE ADAPTER ABI VALIDATION")
    print("=" * 60)
    
    # Initialize Web3 connection
    rpc_url = os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        raise Exception(f"Failed to connect to Arbitrum RPC: {rpc_url}")
    
    print(f"✅ Connected to Arbitrum mainnet")
    
    # Test both adapter addresses found in codebase
    adapters = {
        'current_production': '0xCf85FF1c37c594a10195F7A9Ab85CBb0a03f69dE',
        'other_files': '0xAE9f94BD98eC2831a1330e0418bE0fDb5C95C2B9'
    }
    
    results = {}
    
    for name, address in adapters.items():
        print(f"\n📋 VALIDATING ADAPTER: {name}")
        print(f"   Address: {address}")
        
        # Check if contract exists
        code = w3.eth.get_code(address)
        if code == b'':
            print(f"❌ No contract found at {address}")
            results[address] = {'exists': False}
            continue
        
        print(f"✅ Contract found (code length: {len(code)} bytes)")
        results[address] = {'exists': True, 'code_length': len(code)}
        
        # Test known function signatures
        function_signatures = {
            '0xb8bd1c6b': 'swapDebt (current production)',
            '0x18cbafe5': 'swapAllDebt',
            '0x5d9dd1e6': 'swapDebt (alternative)',
            '0xa415bcad': 'swapDebt (5-param version)'
        }
        
        supported_functions = []
        
        for sig, description in function_signatures.items():
            try:
                # Try calling with minimal data to see if function exists
                call_data = sig + '0' * 64  # Function selector + minimal padding
                
                try:
                    w3.eth.call({'to': address, 'data': call_data})
                    # If it doesn't revert with "function not found", function likely exists
                    supported_functions.append(f"{sig} - {description}")
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'function not found' in error_msg or 'invalid opcode' in error_msg:
                        continue
                    else:
                        # Other errors suggest the function exists but needs proper parameters
                        supported_functions.append(f"{sig} - {description} (needs proper params)")
                        
            except Exception as e:
                continue
        
        results[address]['supported_functions'] = supported_functions
        
        print(f"📋 FUNCTION SUPPORT ANALYSIS:")
        if supported_functions:
            for func in supported_functions:
                print(f"   ✅ {func}")
        else:
            print(f"   ⚠️ No recognized functions found (may need different selectors)")
    
    print(f"\n🔬 DETAILED CONTRACT ANALYSIS")
    print("=" * 60)
    
    # Check for EIP-165 support (standard interface detection)
    eip165_selector = '0x01ffc9a7'  # supportsInterface(bytes4)
    
    for address, data in results.items():
        if not data.get('exists'):
            continue
            
        print(f"\n📊 CONTRACT: {address}")
        
        # Check if it's a proxy contract
        try:
            implementation_slot = w3.eth.get_storage_at(
                address, 
                '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'  # EIP-1967 implementation slot
            )
            if implementation_slot != b'\x00' * 32:
                impl_address = '0x' + implementation_slot[-20:].hex()
                print(f"🔗 PROXY DETECTED - Implementation: {impl_address}")
                results[address]['is_proxy'] = True
                results[address]['implementation'] = impl_address
        except:
            results[address]['is_proxy'] = False
    
    # Generate recommendation
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 60)
    
    active_adapters = [addr for addr, data in results.items() if data.get('exists')]
    
    if len(active_adapters) == 0:
        print("❌ No valid adapters found - need to investigate further")
    elif len(active_adapters) == 1:
        recommended = active_adapters[0]
        print(f"✅ USE ADAPTER: {recommended}")
        print(f"   - Only valid adapter found")
        print(f"   - Functions: {results[recommended].get('supported_functions', [])}")
    else:
        print("🤔 MULTIPLE VALID ADAPTERS FOUND")
        for addr in active_adapters:
            print(f"   {addr}: {len(results[addr].get('supported_functions', []))} functions")
        
        # Recommend the one with most supported functions
        best_adapter = max(active_adapters, key=lambda x: len(results[x].get('supported_functions', [])))
        print(f"✅ RECOMMENDED: {best_adapter} (most function support)")
    
    # Save results
    with open('adapter_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: adapter_validation_results.json")
    
    return results

if __name__ == "__main__":
    try:
        results = validate_adapter_abi()
        
        # Print final summary
        print(f"\n✅ VALIDATION COMPLETE")
        active_count = len([r for r in results.values() if r.get('exists')])
        print(f"   Active contracts: {active_count}")
        print(f"   Check adapter_validation_results.json for detailed results")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        print(f"🔍 Full error: {traceback.format_exc()}")