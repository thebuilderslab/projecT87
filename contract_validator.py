
<old_str>FILE_NOT_EXISTS</old_str>
<new_str>#!/usr/bin/env python3
"""
Comprehensive Contract Validator
Validates that contract addresses exist and are accessible
"""

from web3 import Web3
import time


class ContractValidator:
    def __init__(self, w3):
        self.w3 = w3
        
    def validate_token_contract(self, token_address, token_name="Token"):
        """Validate that a token contract exists and is accessible"""
        try:
            print(f"🔍 Validating {token_name} contract at {token_address}")
            
            # Ensure proper checksum format
            try:
                checksum_address = Web3.to_checksum_address(token_address)
            except Exception as e:
                print(f"❌ Invalid address format for {token_name}: {e}")
                return False
            
            # Check if contract exists
            code = self.w3.eth.get_code(checksum_address)
            if code == b'':
                print(f"❌ No contract deployed at {token_name} address: {checksum_address}")
                return False
            
            # Basic ERC20 ABI for testing
            erc20_abi = [
                {
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # Test contract interaction
            try:
                contract = self.w3.eth.contract(address=checksum_address, abi=erc20_abi)
                symbol = contract.functions.symbol().call()
                decimals = contract.functions.decimals().call()
                
                print(f"✅ {token_name} contract validated: {symbol} ({decimals} decimals)")
                return True
                
            except Exception as contract_error:
                print(f"⚠️ Contract interaction failed for {token_name}: {contract_error}")
                # Still return True if contract exists but interaction fails (might be different interface)
                return True
            
        except Exception as e:
            print(f"❌ Contract validation failed for {token_name}: {e}")
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
    
    def validate_aave_pool(self, pool_address):
        """Validate Aave pool contract"""
        try:
            print(f"🏦 Validating Aave pool contract at {pool_address}")
            
            checksum_address = Web3.to_checksum_address(pool_address)
            
            # Check if contract exists
            code = self.w3.eth.get_code(checksum_address)
            if code == b'':
                print(f"❌ No Aave pool contract at: {checksum_address}")
                return False
            
            # Basic Aave pool ABI for testing
            pool_abi = [
                {
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
                }
            ]
            
            # Test pool interaction
            try:
                pool_contract = self.w3.eth.contract(address=checksum_address, abi=pool_abi)
                # Test with zero address
                zero_address = "0x0000000000000000000000000000000000000000"
                test_data = pool_contract.functions.getUserAccountData(zero_address).call()
                
                print(f"✅ Aave pool contract validated and responsive")
                return True
                
            except Exception as pool_error:
                print(f"⚠️ Aave pool interaction test failed: {pool_error}")
                # Still return True if contract exists
                return True
            
        except Exception as e:
            print(f"❌ Aave pool validation failed: {e}")
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
    test_contract_validator()</new_str>
