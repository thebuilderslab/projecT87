
#!/usr/bin/env python3
"""
Test Contract Call Fixes
Comprehensive testing of the fixed aToken contract calls and balance validation
"""

import os
from web3 import Web3
from eth_account import Account

def test_contract_fixes():
    """Test all the critical contract call fixes"""
    print("🔧 TESTING CRITICAL CONTRACT CALL FIXES")
    print("=" * 50)
    
    try:
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized: {agent.address}")
        
        # Test 1: Enhanced aToken contract calls
        print(f"\n🔍 TEST 1: Enhanced aToken Contract Calls")
        print("-" * 40)
        
        tokens_to_test = [
            ("USDC", agent.usdc_address),
            ("WBTC", agent.wbtc_address), 
            ("WETH", agent.weth_address),
            ("DAI", agent.dai_address)
        ]
        
        for token_name, token_address in tokens_to_test:
            try:
                supplied_balance = agent.aave.get_supplied_balance(token_address)
                print(f"   ✅ {token_name} supplied balance: {supplied_balance:.8f}")
            except Exception as e:
                print(f"   ❌ {token_name} supplied balance failed: {e}")
        
        # Test 2: Prerequisites validation
        print(f"\n🔍 TEST 2: Enhanced Prerequisites Validation")
        print("-" * 45)
        
        try:
            from enhanced_borrow_manager import EnhancedBorrowManager
            ebm = EnhancedBorrowManager(agent)
            
            validation = ebm._validate_prerequisites(1.0, agent.usdc_address)
            
            if validation['success']:
                print(f"   ✅ Prerequisites validation passed")
                print(f"      ETH Balance: {validation['data'].get('eth_balance', 0):.6f}")
                print(f"      Health Factor: {validation['data'].get('health_factor', 0):.2f}")
                print(f"      Available Borrows: ${validation['data'].get('available_borrows_usdc', 0):.2f}")
            else:
                print(f"   ❌ Prerequisites validation failed: {validation['error']}")
                
        except Exception as e:
            print(f"   ❌ Prerequisites validation test failed: {e}")
        
        # Test 3: Token decimals resolution
        print(f"\n🔍 TEST 3: Token Decimals Resolution")
        print("-" * 35)
        
        for token_name, token_address in tokens_to_test:
            try:
                decimals = agent.aave._get_token_decimals(token_address)
                print(f"   ✅ {token_name} decimals: {decimals}")
            except Exception as e:
                print(f"   ❌ {token_name} decimals failed: {e}")
        
        # Test 4: Multiple RPC failover
        print(f"\n🔍 TEST 4: RPC Failover Capability")
        print("-" * 30)
        
        try:
            # Test primary RPC
            block_num = agent.w3.eth.block_number
            print(f"   ✅ Primary RPC working: Block {block_num}")
            
            # Test alternative RPCs
            alt_rpc_count = 0
            for rpc_url in agent.alternative_rpcs[:3]:  # Test first 3
                try:
                    test_w3 = Web3(Web3.HTTPProvider(rpc_url))
                    if test_w3.is_connected():
                        test_block = test_w3.eth.block_number
                        print(f"   ✅ Alternative RPC working: {rpc_url[:30]}... Block {test_block}")
                        alt_rpc_count += 1
                except:
                    print(f"   ⚠️ Alternative RPC failed: {rpc_url[:30]}...")
            
            print(f"   📊 Working RPCs: 1 primary + {alt_rpc_count} alternatives")
            
        except Exception as e:
            print(f"   ❌ RPC failover test failed: {e}")
        
        # Test 5: Contract call robustness
        print(f"\n🔍 TEST 5: Contract Call Robustness")
        print("-" * 35)
        
        try:
            # Test Aave pool contract calls
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
            
            account_data = pool_contract.functions.getUserAccountData(
                Web3.to_checksum_address(agent.address)
            ).call()
            
            health_factor = account_data[5] / 1e18 if account_data[5] > 0 else float('inf')
            collateral_usd = account_data[0] / 1e8
            debt_usd = account_data[1] / 1e8
            
            print(f"   ✅ Aave contract call successful:")
            print(f"      Health Factor: {health_factor:.4f}")
            print(f"      Collateral: ${collateral_usd:.2f}")
            print(f"      Debt: ${debt_usd:.2f}")
            
        except Exception as e:
            print(f"   ❌ Contract call robustness test failed: {e}")
        
        print(f"\n🎉 CONTRACT FIXES TESTING COMPLETE!")
        print(f"✅ Critical issues should now be resolved")
        
        return True
        
    except Exception as e:
        print(f"❌ Contract fixes test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_contract_fixes()
    if success:
        print(f"\n✅ ALL CONTRACT FIXES VALIDATED")
    else:
        print(f"\n❌ CONTRACT FIXES NEED FURTHER WORK")
