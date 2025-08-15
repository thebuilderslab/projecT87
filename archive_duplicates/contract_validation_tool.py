
#!/usr/bin/env python3
"""
Contract Validation Tool - Ensure all contracts are accessible and valid
"""

import os
from web3 import Web3
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def validate_all_contracts():
    """Validate all contract interactions before execution"""
    print("🔍 COMPREHENSIVE CONTRACT VALIDATION")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        
        # Test 1: Validate all contract addresses
        contracts_to_test = {
            'USDC': agent.usdc_address,
            'WBTC': agent.wbtc_address, 
            'WETH': agent.weth_address,
            'DAI': agent.dai_address,
            'Aave Pool': agent.aave_pool_address
        }
        
        print("📋 Testing Contract Addresses:")
        for name, address in contracts_to_test.items():
            if Web3.is_address(address):
                # Test contract accessibility
                try:
                    code = agent.w3.eth.get_code(address)
                    if len(code) > 2:  # Has contract code
                        print(f"   ✅ {name}: {address} - Contract found")
                    else:
                        print(f"   ❌ {name}: {address} - No contract code")
                except Exception as e:
                    print(f"   ❌ {name}: {address} - Access error: {e}")
            else:
                print(f"   ❌ {name}: Invalid address format")
        
        # Test 2: Validate Aave getUserAccountData function
        print("\n🏦 Testing Aave Pool Contract:")
        try:
            pool_abi = [{
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
            
            pool_contract = agent.w3.eth.contract(
                address=agent.aave_pool_address,
                abi=pool_abi
            )
            
            # Test call
            account_data = pool_contract.functions.getUserAccountData(agent.address).call()
            print(f"   ✅ Aave contract accessible")
            print(f"   📊 Current position: ${account_data[0] / 1e8:.2f} collateral")
            
        except Exception as e:
            print(f"   ❌ Aave contract test failed: {e}")
            
        # Test 3: Validate gas estimation
        print("\n⛽ Testing Gas Estimation:")
        try:
            gas_params = agent.get_optimized_gas_params('aave_borrow', 'market')
            if 'gas' in gas_params and 'gasPrice' in gas_params:
                print(f"   ✅ Gas estimation working")
                print(f"   📊 Gas limit: {gas_params['gas']:,}, Price: {gas_params['gasPrice'] / 1e9:.2f} gwei")
            else:
                print(f"   ❌ Gas estimation missing parameters")
        except Exception as e:
            print(f"   ❌ Gas estimation failed: {e}")
            
        # Test 4: Check ETH balance for gas
        print("\n💰 Testing Wallet Readiness:")
        eth_balance = agent.get_eth_balance()
        min_eth_required = 0.001
        
        if eth_balance >= min_eth_required:
            print(f"   ✅ Sufficient ETH: {eth_balance:.6f} ETH")
        else:
            print(f"   ❌ Insufficient ETH: {eth_balance:.6f} ETH (need {min_eth_required:.3f})")
            
        return True
        
    except Exception as e:
        print(f"❌ Contract validation failed: {e}")
        return False

if __name__ == "__main__":
    validate_all_contracts()
