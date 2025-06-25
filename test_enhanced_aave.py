
#!/usr/bin/env python3
"""
Test Enhanced Aave Integration
Comprehensive testing of direct Aave V3 contract calls
"""

import os
from dotenv import load_dotenv
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3

def test_enhanced_aave_integration():
    """Test enhanced Aave V3 integration with detailed logging"""
    load_dotenv()
    
    print("🧪 TESTING ENHANCED AAVE V3 INTEGRATION")
    print("=" * 60)
    
    try:
        # Initialize agent
        print("🤖 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        print(f"✅ Agent initialized for wallet: {agent.address}")
        print(f"🌐 Connected to network: {agent.w3.eth.chain_id}")
        print(f"💰 ETH Balance: {agent.get_eth_balance():.6f} ETH")
        
        # Test network connectivity
        print(f"\n🔗 Network connectivity test:")
        latest_block = agent.w3.eth.get_block('latest')
        print(f"   Latest block: {latest_block.number}")
        print(f"   Block timestamp: {latest_block.timestamp}")
        
        # Test enhanced Aave data retrieval
        print(f"\n📊 Testing enhanced Aave data retrieval...")
        
        # Aave V3 Pool address on Arbitrum Mainnet
        aave_pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        
        # Enhanced ABI
        aave_pool_abi = [
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                "name": "getUserAccountData",
                "outputs": [
                    {"internalType": "uint256", "name": "totalCollateralBase", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalDebtBase", "type": "uint256"},
                    {"internalType": "uint256", "name": "availableBorrowsBase", "type": "uint256"},
                    {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
                    {"internalType": "uint256", "name": "ltv", "type": "uint256"},
                    {"internalType": "uint256", "name": "healthFactor", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        print(f"🔍 Contract address: {aave_pool_address}")
        print(f"👤 User address: {agent.address}")
        
        # Test contract creation
        try:
            pool_contract = agent.w3.eth.contract(
                address=Web3.to_checksum_address(aave_pool_address),
                abi=aave_pool_abi
            )
            print("✅ Contract instance created successfully")
        except Exception as e:
            print(f"❌ Contract creation failed: {e}")
            return False
        
        # Test contract call
        print("\n📞 Testing getUserAccountData call...")
        try:
            user_data = pool_contract.functions.getUserAccountData(
                Web3.to_checksum_address(agent.address)
            ).call()
            
            print("✅ Contract call successful!")
            print(f"📊 Raw data: {user_data}")
            
            # Parse the data
            total_collateral_base = user_data[0]
            total_debt_base = user_data[1] 
            available_borrows_base = user_data[2]
            current_liquidation_threshold = user_data[3]
            ltv = user_data[4]
            health_factor_raw = user_data[5]
            
            # Convert from base units
            total_collateral_usd = total_collateral_base / (10**8)  # Aave uses 8 decimals for USD
            total_debt_usd = total_debt_base / (10**8)
            available_borrows_usd = available_borrows_base / (10**8)
            
            # Health factor conversion
            if health_factor_raw == 2**256 - 1:  # Max uint256 means no debt
                health_factor = float('inf')
                health_factor_display = "∞ (No Debt)"
            else:
                health_factor = health_factor_raw / (10**18)
                health_factor_display = f"{health_factor:.4f}"
            
            print(f"\n🎯 PARSED AAVE DATA:")
            print(f"   💰 Total Collateral: ${total_collateral_usd:,.2f} USD")
            print(f"   🔴 Total Debt: ${total_debt_usd:,.2f} USD")
            print(f"   💚 Available Borrows: ${available_borrows_usd:,.2f} USD")
            print(f"   ⚡ Health Factor: {health_factor_display}")
            print(f"   📈 Liquidation Threshold: {current_liquidation_threshold / 100:.2f}%")
            print(f"   📊 LTV: {ltv / 100:.2f}%")
            
            # Check if we have meaningful data
            has_position = total_collateral_usd > 0 or total_debt_usd > 0
            print(f"\n✅ Position Status: {'Active Position Found' if has_position else 'No Position Found'}")
            
            if has_position:
                print("🎉 SUCCESS: Enhanced Aave integration is working!")
                print("🚀 Your dashboard should now display correct Aave data!")
            else:
                print("ℹ️ No Aave position found for this wallet")
                print("💡 This is normal if you haven't deposited collateral to Aave")
            
            return True
            
        except Exception as call_error:
            print(f"❌ Contract call failed: {call_error}")
            print(f"❌ Error type: {type(call_error)}")
            
            # Try with explicit gas and block
            print("\n🔄 Trying alternative call method...")
            try:
                user_data_alt = pool_contract.functions.getUserAccountData(
                    Web3.to_checksum_address(agent.address)
                ).call(block_identifier='latest')
                
                print("✅ Alternative call successful!")
                print(f"📊 Alt data: {user_data_alt}")
                return True
                
            except Exception as alt_error:
                print(f"❌ Alternative call also failed: {alt_error}")
                return False
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_web_dashboard_integration():
    """Test if web dashboard can use the enhanced function"""
    print(f"\n🌐 Testing web dashboard integration...")
    
    try:
        from web_dashboard import get_enhanced_aave_data
        agent = ArbitrumTestnetAgent()
        
        result = get_enhanced_aave_data(agent)
        if result:
            print("✅ Web dashboard integration working!")
            print(f"📊 Dashboard data: {result}")
            return True
        else:
            print("❌ Web dashboard integration returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Web dashboard integration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ENHANCED AAVE V3 INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Direct Aave integration
    test1_success = test_enhanced_aave_integration()
    
    # Test 2: Web dashboard integration  
    test2_success = test_web_dashboard_integration()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    print(f"   Direct Aave Integration: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Web Dashboard Integration: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Your dashboard should now show correct Aave data!")
        print("🔄 Restart your web dashboard to see the changes")
    else:
        print("\n⚠️ Some tests failed - check logs above")
    
    print("=" * 60)
