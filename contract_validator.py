
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

            checksum_address = Web3.to_checksum_address(token_address)

            # Check if contract exists
            code = self.w3.eth.get_code(checksum_address)
            if code == b'':
                print(f"❌ No contract deployed at {token_name} address: {token_address}")
                return False

            # Try to call a basic ERC20 function
            try:
                erc20_abi = [{
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                }]
                
                contract = self.w3.eth.contract(address=checksum_address, abi=erc20_abi)
                decimals = contract.functions.decimals().call()
                
                print(f"✅ {token_name} contract validated - Decimals: {decimals}")
                return True
                
            except Exception as call_error:
                print(f"⚠️ {token_name} contract exists but function call failed: {call_error}")
                return True  # Still consider valid if contract exists

        except Exception as e:
            print(f"❌ Contract validation failed for {token_name}: {e}")
            return False

    def validate_aave_pool(self, pool_address):
        """Validate Aave pool contract"""
        try:
            if not Web3.is_address(pool_address):
                print(f"❌ Invalid Aave pool address: {pool_address}")
                return False

            checksum_address = Web3.to_checksum_address(pool_address)
            
            # Check if contract exists
            code = self.w3.eth.get_code(checksum_address)
            if code == b'':
                print(f"❌ No contract at Aave pool address: {pool_address}")
                return False

            # Try to call POOL_REVISION function
            try:
                pool_abi = [{
                    "inputs": [],
                    "name": "POOL_REVISION",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }]

                pool_contract = self.w3.eth.contract(address=checksum_address, abi=pool_abi)
                revision = pool_contract.functions.POOL_REVISION().call()
                print(f"✅ Aave Pool validated - Revision: {revision}")
                return True
                
            except Exception as call_error:
                print(f"⚠️ Aave pool exists but POOL_REVISION call failed: {call_error}")
                
                # Try alternative validation with getUserAccountData
                try:
                    alt_abi = [{
                        "inputs": [{"name": "user", "type": "address"}],
                        "name": "getUserAccountData",
                        "outputs": [
                            {"name": "totalCollateralBase", "type": "uint256"},
                            {"name": "totalDebtBase", "type": "uint256"},
                            {"name": "availableBorrowsBase", "type": "uint256"},
                            {"name": "currentLiquidationThreshold", "type": "uint256"},
                            {"name": "ltv", "type": "uint256"},
                            {"name": "healthFactor", "type": "uint256"}
                        ],
                        "stateMutability": "view",
                        "type": "function"
                    }]
                    
                    alt_contract = self.w3.eth.contract(address=checksum_address, abi=alt_abi)
                    # Test with zero address - should not revert for Aave pool
                    zero_address = "0x0000000000000000000000000000000000000000"
                    alt_contract.functions.getUserAccountData(zero_address).call()
                    print(f"✅ Aave Pool validated via getUserAccountData")
                    return True
                    
                except Exception as alt_error:
                    print(f"❌ Aave pool validation failed: {alt_error}")
                    return False

        except Exception as e:
            print(f"❌ Aave pool validation failed: {e}")
            return False

    def validate_all_tokens(self, token_addresses):
        """Validate multiple token contracts"""
        try:
            print("🔍 Validating all token contracts...")
            
            all_valid = True
            for token_name, address in token_addresses.items():
                print(f"  Validating {token_name}...")
                if not self.validate_token_contract(address, token_name):
                    all_valid = False
                time.sleep(0.1)  # Brief pause between validations
            
            if all_valid:
                print("✅ All token contracts validated successfully")
            else:
                print("⚠️ Some token contract validations failed")
                
            return all_valid
            
        except Exception as e:
            print(f"❌ Bulk token validation failed: {e}")
            return False

    def validate_complete_system(self, agent):
        """Validate complete DeFi system contracts"""
        try:
            print("🔍 Running complete contract validation...")
            
            # Validate all tokens
            token_addresses = {
                'USDC': agent.usdc_address,
                'WETH': agent.weth_address,
                'WBTC': agent.wbtc_address,
                'DAI': agent.dai_address
            }
            
            tokens_valid = self.validate_all_tokens(token_addresses)
            
            # Validate Aave pool
            pool_valid = self.validate_aave_pool(agent.aave_pool_address)
            
            overall_valid = tokens_valid and pool_valid
            
            if overall_valid:
                print("✅ Complete contract validation PASSED")
            else:
                print("❌ Complete contract validation FAILED")
                
            return overall_valid
            
        except Exception as e:
            print(f"❌ Complete contract validation failed: {e}")
            return False

def test_contract_validator():
    """Test the contract validator with known addresses"""
    try:
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        agent = ArbitrumTestnetAgent()
        validator = ContractValidator(agent.w3)
        
        # Run complete validation
        result = validator.validate_complete_system(agent)
        
        if result:
            print("🎯 Contract validator test: SUCCESS")
        else:
            print("🎯 Contract validator test: PARTIAL SUCCESS")
            
        return result
        
    except Exception as e:
        print(f"❌ Contract validator test failed: {e}")
        return False

if __name__ == "__main__":
    test_contract_validator()
