#!/usr/bin/env python3
"""
Contract Validator Module
Validates contract addresses and functionality for DeFi operations
"""

from web3 import Web3
import time

class ContractValidator:
    def __init__(self, w3):
        self.w3 = w3

    def validate_token_contract(self, token_address, token_name):
        """Validate token contract exists and is functional"""
        try:
            # Basic address validation
            if not Web3.is_address(token_address):
                print(f"❌ Invalid address format for {token_name}: {token_address}")
                return False

            # Check if contract exists
            code = self.w3.eth.get_code(Web3.to_checksum_address(token_address))
            if code == b'':
                print(f"❌ No contract deployed at {token_name} address: {token_address}")
                return False

            print(f"✅ {token_name} contract validated at {token_address}")
            return True

        except Exception as e:
            print(f"❌ Contract validation failed for {token_name}: {e}")
            return False

    def validate_aave_pool(self, pool_address):
        """Validate Aave pool contract"""
        try:
            pool_abi = [{
                "inputs": [],
                "name": "POOL_REVISION",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }]

            pool_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(pool_address),
                abi=pool_abi
            )

            revision = pool_contract.functions.POOL_REVISION().call()
            print(f"✅ Aave Pool validated - Revision: {revision}")
            return True

        except Exception as e:
            print(f"❌ Aave pool validation failed: {e}")
            return False

    def validate_all_tokens(self, token_addresses):
        """Validate multiple token contracts"""
        try:
            print("🔍 Validating all token contracts...")
            
            all_valid = True
            for token_name, address in token_addresses.items():
                if not self.validate_token_contract(address, token_name):
                    all_valid = False
                time.sleep(0.1)  # Brief pause between validations
            
            if all_valid:
                print("✅ All token contracts validated successfully")
            else:
                print("❌ Some token contract validations failed")
                
            return all_valid
            
        except Exception as e:
            print(f"❌ Bulk token validation failed: {e}")
            return False

def test_contract_validator():
    """Test the contract validator with known addresses"""
    from arbitrum_testnet_agent import ArbitrumTestnetAgent
    
    try:
        agent = ArbitrumTestnetAgent()
        validator = ContractValidator(agent.w3)
        
        # Test known contracts
        test_addresses = {
            'USDC': agent.usdc_address,
            'WETH': agent.weth_address,
            'WBTC': agent.wbtc_address
        }
        
        result = validator.validate_all_tokens(test_addresses)
        pool_result = validator.validate_aave_pool(agent.aave_pool_address)
        
        return result and pool_result
        
    except Exception as e:
        print(f"❌ Contract validator test failed: {e}")
        return False


if __name__ == "__main__":
    test_contract_validator()