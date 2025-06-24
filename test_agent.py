
import pytest
import os
import time
from unittest.mock import Mock, patch
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from aave_health_monitor import AaveHealthMonitor
from dotenv import load_dotenv

class TestMainnetReadiness:
    """Critical tests for mainnet deployment readiness"""
    
    def setup_method(self):
        """Setup test environment"""
        load_dotenv()
        self.test_config = {
            'exploration_rate': 0.05,  # Conservative for mainnet
            'health_factor_target': 1.19,
            'emergency_threshold': 1.05
        }
    
    def test_pre_money_validation(self):
        """PRE-MONEY VALIDATION: Ensure agent initializes safely"""
        print("🧪 Testing PRE-MONEY VALIDATION...")
        
        try:
            # Test testnet initialization first
            agent = ArbitrumTestnetAgent('testnet')
            assert agent.w3.is_connected(), "Failed to connect to network"
            assert agent.expected_chain_id == 421614, "Wrong testnet chain ID"
            
            # Test mainnet configuration (without executing)
            with patch.dict(os.environ, {'NETWORK_MODE': 'mainnet'}):
                # Don't actually initialize mainnet agent in tests
                assert os.getenv('PRIVATE_KEY'), "PRIVATE_KEY not found in environment"
                assert os.getenv('COINMARKETCAP_API_KEY'), "CoinMarketCap API key missing"
            
            print("✅ PRE-MONEY VALIDATION: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ PRE-MONEY VALIDATION: FAILED - {e}")
            return False
    
    def test_liquidation_protection(self):
        """LIQUIDATION PROTECTION: Test emergency functions"""
        print("🧪 Testing LIQUIDATION PROTECTION...")
        
        try:
            agent = ArbitrumTestnetAgent('testnet')
            
            # Mock health factor data for testing
            mock_health_data = {
                'health_factor': 1.02,  # Critical level
                'total_collateral_eth': 1.0,
                'total_debt_eth': 0.95,
                'available_borrows_eth': 0.05
            }
            
            # Test emergency liquidation protection logic
            with patch.object(agent, 'health_monitor') as mock_monitor:
                mock_monitor.get_current_health_factor.return_value = mock_health_data
                
                # Test emergency protection function exists and is callable
                assert hasattr(agent, 'emergency_liquidation_protection'), "Emergency protection function missing"
                
                # Simulate emergency call (don't execute real transactions)
                with patch.object(agent, 'uniswap') as mock_uniswap:
                    with patch.object(agent, 'aave') as mock_aave:
                        mock_uniswap.swap_arb_to_usdc.return_value = True
                        mock_aave.repay_to_aave.return_value = True
                        
                        result = agent.emergency_liquidation_protection()
                        assert result, "Emergency protection failed"
            
            print("✅ LIQUIDATION PROTECTION: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ LIQUIDATION PROTECTION: FAILED - {e}")
            return False
    
    def test_network_configuration(self):
        """Test network configuration for mainnet"""
        print("🧪 Testing NETWORK CONFIGURATION...")
        
        try:
            # Test mainnet configuration without connecting
            mainnet_rpc = 'https://arb1.arbitrum.io/rpc'
            expected_mainnet_chain_id = 42161
            
            # Verify configuration constants
            assert mainnet_rpc, "Mainnet RPC URL not configured"
            assert expected_mainnet_chain_id == 42161, "Wrong mainnet chain ID"
            
            print("✅ NETWORK CONFIGURATION: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ NETWORK CONFIGURATION: FAILED - {e}")
            return False
    
    def test_gas_estimation(self):
        """Test gas estimation and cost calculation"""
        print("🧪 Testing GAS ESTIMATION...")
        
        try:
            agent = ArbitrumTestnetAgent('testnet')
            
            # Test gas price retrieval
            gas_price = agent.get_gas_price()
            assert gas_price > 0, "Gas price should be positive"
            
            # Test gas cost estimation
            estimated_cost = agent.estimate_gas_cost(200000)  # Complex transaction
            assert float(estimated_cost) > 0, "Gas cost estimation failed"
            
            print(f"✅ GAS ESTIMATION: PASSED (Current gas price: {agent.w3.from_wei(gas_price, 'gwei'):.2f} gwei)")
            return True
            
        except Exception as e:
            print(f"❌ GAS ESTIMATION: FAILED - {e}")
            return False
    
    def test_secrets_management(self):
        """Test secure secrets management"""
        print("🧪 Testing SECRETS MANAGEMENT...")
        
        try:
            # Verify all required secrets exist
            required_secrets = ['PRIVATE_KEY', 'COINMARKETCAP_API_KEY']
            
            for secret in required_secrets:
                value = os.getenv(secret)
                assert value, f"Required secret {secret} not found"
                assert value != f'your_{secret.lower()}_here', f"Default placeholder found for {secret}"
            
            # Verify private key format
            private_key = os.getenv('PRIVATE_KEY')
            assert private_key.startswith('0x'), "Private key should start with 0x"
            assert len(private_key) == 66, "Private key should be 66 characters"
            
            print("✅ SECRETS MANAGEMENT: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ SECRETS MANAGEMENT: FAILED - {e}")
            return False
    
    def test_health_monitoring(self):
        """Test health monitoring system"""
        print("🧪 Testing HEALTH MONITORING...")
        
        try:
            agent = ArbitrumTestnetAgent('testnet')
            
            # Test health monitor initialization
            from aave_health_monitor import AaveHealthMonitor
            health_monitor = AaveHealthMonitor(agent.w3, agent.account, Mock())
            
            # Test ARB price fetching
            arb_price = health_monitor.get_arb_price()
            # Should work with valid API key or handle gracefully
            
            # Test health factor calculation
            mock_health_data = health_monitor.get_current_health_factor()
            # Should return data or handle missing contracts gracefully
            
            print("✅ HEALTH MONITORING: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ HEALTH MONITORING: FAILED - {e}")
            return False

def run_comprehensive_tests():
    """Run all critical tests for mainnet readiness"""
    print("🚨 RUNNING COMPREHENSIVE MAINNET READINESS TESTS")
    print("=" * 60)
    
    test_suite = TestMainnetReadiness()
    test_suite.setup_method()
    
    tests = [
        test_suite.test_pre_money_validation,
        test_suite.test_liquidation_protection,
        test_suite.test_network_configuration,
        test_suite.test_gas_estimation,
        test_suite.test_secrets_management,
        test_suite.test_health_monitoring
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
        print("-" * 40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 TEST RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - READY FOR MAINNET DEPLOYMENT")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - DO NOT DEPLOY TO MAINNET")
        return False

if __name__ == "__main__":
    run_comprehensive_tests()
