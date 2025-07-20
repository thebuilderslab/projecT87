
#!/usr/bin/env python3
"""
Comprehensive Contract Validation System
Validates all token contracts before operations
"""

from web3 import Web3
import json

class ContractValidator:
    def __init__(self, w3):
        self.w3 = w3
        
    def validate_token_contract(self, token_address, token_name="Unknown"):
        """Comprehensive token contract validation"""
        try:
            print(f"🔍 Validating {token_name} contract at {token_address}...")
            
            # Ensure address is checksummed
            checksum_address = Web3.to_checksum_address(token_address)
            
            # Check if contract exists
            contract_code = self.w3.eth.get_code(checksum_address)
            if len(contract_code) == 0:
                print(f"❌ No contract found at {token_name} address: {checksum_address}")
                return False
                
            # Basic ERC20 validation
            erc20_abi = [
                {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
            ]
            
            try:
                contract = self.w3.eth.contract(address=checksum_address, abi=erc20_abi)
                
                # Test basic ERC20 functions
                name = contract.functions.name().call()
                symbol = contract.functions.symbol().call()
                decimals = contract.functions.decimals().call()
                
                print(f"✅ {token_name} contract validated:")
                print(f"   Name: {name}")
                print(f"   Symbol: {symbol}")
                print(f"   Decimals: {decimals}")
                print(f"   Address: {checksum_address}")
                
                return True
                
            except Exception as call_error:
                print(f"❌ {token_name} contract call failed: {call_error}")
                return False
                
        except Exception as e:
            print(f"❌ {token_name} validation error: {e}")
            return False
    
    def validate_all_tokens(self, token_addresses):
        """Validate all required token contracts"""
        print("🔍 COMPREHENSIVE TOKEN VALIDATION")
        print("=" * 50)
        
        validation_results = {}
        
        for token_name, address in token_addresses.items():
            result = self.validate_token_contract(address, token_name)
            validation_results[token_name] = {
                'address': address,
                'valid': result
            }
            
        # Summary
        valid_count = sum(1 for r in validation_results.values() if r['valid'])
        total_count = len(validation_results)
        
        print(f"\n📊 Validation Summary: {valid_count}/{total_count} contracts valid")
        
        if valid_count == total_count:
            print("✅ All token contracts validated successfully!")
            return True
        else:
            print("❌ Some token contracts failed validation")
            for name, result in validation_results.items():
                if not result['valid']:
                    print(f"   ❌ {name}: {result['address']}")
            return False

def validate_arbitrum_mainnet_tokens(w3):
    """Validate all Arbitrum Mainnet token addresses"""
    
    # Correct Arbitrum Mainnet addresses
    token_addresses = {
        'USDC_E': '0xFF970A61A04b1cA14834A651bAb06d67307796618',  # USDC.e (bridged)
        'USDC_NATIVE': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',  # Native USDC  
        'WBTC': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f',
        'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
        'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
        'ARB': '0x912CE59144191C1204E64559FE8253a0e49E6548'
    }
    
    validator = ContractValidator(w3)
    return validator.validate_all_tokens(token_addresses)

if __name__ == "__main__":
    # Test validation
    import os
    from web3 import Web3
    
    rpc_url = "https://arb1.arbitrum.io/rpc"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if w3.is_connected():
        validate_arbitrum_mainnet_tokens(w3)
    else:
        print("❌ Failed to connect to Arbitrum")
