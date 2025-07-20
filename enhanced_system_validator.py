
#!/usr/bin/env python3
"""
Enhanced System Validator
Comprehensive validation of all system components
"""

import os
import time
from web3 import Web3

class EnhancedSystemValidator:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3

    def run_comprehensive_validation(self):
        """Run comprehensive system validation"""
        print("🔧 Running Enhanced System Validation...")

        validation_results = {
            'network_connectivity': False,
            'contract_addresses': False,
            'integrations': False,
            'wallet_readiness': False,
            'borrow_system': False
        }

        try:
            # Test 1: Network connectivity
            if self._validate_network():
                validation_results['network_connectivity'] = True
                print("✅ Network connectivity: PASSED")
            else:
                print("❌ Network connectivity: FAILED")

            # Test 2: Contract addresses
            if self._validate_contracts():
                validation_results['contract_addresses'] = True
                print("✅ Contract addresses: PASSED")
            else:
                print("❌ Contract addresses: FAILED")

            # Test 3: DeFi integrations
            if self._validate_integrations():
                validation_results['integrations'] = True
                print("✅ DeFi integrations: PASSED")
            else:
                print("❌ DeFi integrations: FAILED")

            # Test 4: Wallet readiness
            if self._validate_wallet():
                validation_results['wallet_readiness'] = True
                print("✅ Wallet readiness: PASSED")
            else:
                print("❌ Wallet readiness: FAILED")

            # Test 5: Borrow system
            if self._validate_borrow_system():
                validation_results['borrow_system'] = True
                print("✅ Borrow system: PASSED")
            else:
                print("❌ Borrow system: FAILED")

            # Overall result
            passed_tests = sum(validation_results.values())
            total_tests = len(validation_results)

            print(f"📊 Validation Results: {passed_tests}/{total_tests} passed")

            if passed_tests >= 4:  # Allow for 1 failure
                print("✅ Enhanced system validation PASSED (sufficient)")
                return True
            else:
                print("❌ Enhanced system validation FAILED")
                self._provide_fix_recommendations(validation_results)
                return False

        except Exception as e:
            print(f"❌ Enhanced validation error: {e}")
            return False

    def _validate_network(self):
        """Validate network connectivity"""
        try:
            if not self.w3.is_connected():
                print("  ❌ Web3 not connected")
                return False

            chain_id = self.w3.eth.chain_id
            block_number = self.w3.eth.block_number

            if chain_id not in [42161, 421614]:  # Mainnet or Sepolia
                print(f"  ❌ Wrong chain ID: {chain_id}")
                return False

            print(f"  ✅ Network: Chain {chain_id}, Block {block_number}")
            return True

        except Exception as e:
            print(f"  ❌ Network validation failed: {e}")
            return False

    def _validate_contracts(self):
        """Validate contract addresses"""
        try:
            contracts = [
                ("USDC", self.agent.usdc_address),
                ("WBTC", self.agent.wbtc_address),
                ("WETH", self.agent.weth_address),
                ("Aave Pool", self.agent.aave_pool_address)
            ]

            for name, address in contracts:
                if not Web3.is_address(address):
                    print(f"  ❌ Invalid {name} address: {address}")
                    return False

                try:
                    code = self.w3.eth.get_code(Web3.to_checksum_address(address))
                    if code == b'':
                        print(f"  ❌ No contract at {name} address: {address}")
                        return False
                except Exception as e:
                    print(f"  ❌ Failed to check {name} contract: {e}")
                    return False

            print("  ✅ All contract addresses validated")
            return True

        except Exception as e:
            print(f"  ❌ Contract validation failed: {e}")
            return False

    def _validate_integrations(self):
        """Validate DeFi integrations"""
        try:
            # Initialize integrations if not already done
            if not hasattr(self.agent, 'aave') or not self.agent.aave:
                print("  🔄 Initializing missing integrations...")
                success = self.agent.initialize_integrations()
                if not success:
                    print("  ❌ Failed to initialize integrations")
                    return False

            required_integrations = [
                ('aave', 'Aave'),
                ('uniswap', 'Uniswap'),
                ('health_monitor', 'Health Monitor'),
                ('gas_calculator', 'Gas Calculator')
            ]

            missing = []
            for attr, name in required_integrations:
                if not hasattr(self.agent, attr) or getattr(self.agent, attr) is None:
                    missing.append(name)

            if missing:
                print(f"  ❌ Missing integrations: {', '.join(missing)}")
                return False

            print("  ✅ All integrations present and initialized")
            return True

        except Exception as e:
            print(f"  ❌ Integration validation failed: {e}")
            return False

    def _validate_wallet(self):
        """Validate wallet readiness"""
        try:
            eth_balance = self.agent.get_eth_balance()

            if eth_balance < 0.001:  # Minimum ETH for gas
                print(f"  ❌ Insufficient ETH: {eth_balance:.6f}")
                return False

            # Check if wallet has valid address
            if not Web3.is_address(self.agent.address):
                print(f"  ❌ Invalid wallet address: {self.agent.address}")
                return False

            print(f"  ✅ Wallet ready - ETH: {eth_balance:.6f}")
            return True

        except Exception as e:
            print(f"  ❌ Wallet validation failed: {e}")
            return False

    def _validate_borrow_system(self):
        """Validate enhanced borrow system"""
        try:
            # Check if enhanced borrow manager exists
            if not hasattr(self.agent, 'enhanced_borrow_manager'):
                print("  ❌ Enhanced borrow manager not initialized")
                return False

            ebm = self.agent.enhanced_borrow_manager
            if not ebm:
                print("  ❌ Enhanced borrow manager is None")
                return False

            # Test borrow validation method
            if not hasattr(ebm, '_validate_borrow_conditions'):
                print("  ❌ Borrow validation method missing")
                return False

            print("  ✅ Enhanced borrow system available")
            return True

        except Exception as e:
            print(f"  ❌ Borrow system validation failed: {e}")
            return False

    def _provide_fix_recommendations(self, results):
        """Provide specific fix recommendations"""
        print("\n🔧 FIX RECOMMENDATIONS:")
        
        if not results['network_connectivity']:
            print("  • Check RPC endpoints and network connectivity")
        
        if not results['contract_addresses']:
            print("  • Verify contract addresses for current network")
        
        if not results['integrations']:
            print("  • Run agent.initialize_integrations() manually")
        
        if not results['wallet_readiness']:
            print("  • Add ETH to wallet for gas fees")
        
        if not results['borrow_system']:
            print("  • Initialize enhanced borrow manager")

def validate_arbitrum_testnet_agent():
    """Validate the main agent module"""
    try:
        # First check for syntax errors
        import py_compile
        py_compile.compile('arbitrum_testnet_agent.py', doraise=True)
        print("✅ Syntax validation passed")

        # Then test import
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        print("✅ Import validation passed")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in arbitrum_testnet_agent.py: {e}")
        return False
    except Exception as e:
        print(f"❌ ArbitrumTestnetAgent validation failed: {e}")
        return False

if __name__ == "__main__":
    # Test the validator
    try:
        if validate_arbitrum_testnet_agent():
            from arbitrum_testnet_agent import ArbitrumTestnetAgent
            agent = ArbitrumTestnetAgent()
            validator = EnhancedSystemValidator(agent)
            result = validator.run_comprehensive_validation()
            print(f"\n🎯 Final Result: {'SUCCESS' if result else 'NEEDS FIXES'}")
        else:
            print("❌ Cannot run validator due to agent issues")
    except Exception as e:
        print(f"❌ Validator test failed: {e}")
