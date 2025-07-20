"""
Enhanced System Validator
Comprehensive validation of all system components with proper error handling
"""

import os
import time
from typing import Dict, List, Optional
from web3 import Web3

class EnhancedSystemValidator:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        self.validation_results = {}

    def run_comprehensive_validation(self) -> bool:
        """Run comprehensive validation of all system components"""
        try:
            print("🔧 ENHANCED SYSTEM VALIDATOR")
            print("=" * 40)

            # Test 1: Network connectivity
            network_result = self._validate_network_connectivity()
            self.validation_results['network'] = network_result

            # Test 2: Contract addresses
            contract_result = self._validate_contract_addresses()
            self.validation_results['contracts'] = contract_result

            # Test 3: Account setup
            account_result = self._validate_account_setup()
            self.validation_results['account'] = account_result

            # Test 4: Integration readiness
            integration_result = self._validate_integrations()
            self.validation_results['integrations'] = integration_result

            # Overall assessment
            all_passed = all(self.validation_results.values())

            print(f"\n📊 VALIDATION SUMMARY:")
            for test_name, result in self.validation_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {test_name.title()}: {status}")

            print(f"\n🎯 OVERALL: {'✅ SYSTEM READY' if all_passed else '⚠️ ISSUES DETECTED'}")

            return all_passed

        except Exception as e:
            print(f"❌ Enhanced validation failed: {e}")
            return False

    def _validate_network_connectivity(self) -> bool:
        """Validate network connectivity and RPC functionality"""
        try:
            print("🌐 Testing network connectivity...")

            # Test basic connectivity
            if not self.w3.is_connected():
                print("   ❌ Web3 not connected")
                return False

            # Test chain ID
            chain_id = self.w3.eth.chain_id
            expected_chain = 42161 if self.agent.network_mode == 'mainnet' else 421614

            if chain_id != expected_chain:
                print(f"   ❌ Wrong chain ID: {chain_id} (expected {expected_chain})")
                return False

            # Test latest block
            latest_block = self.w3.eth.block_number
            if latest_block < 1000000:
                print(f"   ❌ Invalid block number: {latest_block}")
                return False

            print(f"   ✅ Network OK - Chain {chain_id}, Block {latest_block}")
            return True

        except Exception as e:
            print(f"   ❌ Network validation failed: {e}")
            return False

    def _validate_contract_addresses(self) -> bool:
        """Validate contract addresses are properly formatted"""
        try:
            print("📋 Testing contract addresses...")

            addresses_to_test = [
                ("USDC", self.agent.usdc_address),
                ("WBTC", self.agent.wbtc_address),
                ("WETH", self.agent.weth_address),
                ("DAI", self.agent.dai_address),
                ("Aave Pool", self.agent.aave_pool_address)
            ]

            all_valid = True
            for name, address in addresses_to_test:
                try:
                    # Validate format
                    if not address or len(address) != 42 or not address.startswith('0x'):
                        print(f"   ❌ {name} invalid format: {address}")
                        all_valid = False
                        continue

                    # Test checksum (don't fail if checksum is wrong, just warn)
                    try:
                        Web3.to_checksum_address(address)
                        print(f"   ✅ {name}: {address}")
                    except Exception:
                        print(f"   ⚠️ {name}: {address} (checksum warning)")
                        # Don't fail validation for checksum issues

                except Exception as addr_error:
                    print(f"   ❌ {name} validation error: {addr_error}")
                    all_valid = False

            return all_valid

        except Exception as e:
            print(f"   ❌ Contract address validation failed: {e}")
            return False

    def _validate_account_setup(self) -> bool:
        """Validate account and wallet setup"""
        try:
            print("🔑 Testing account setup...")

            # Check account exists
            if not hasattr(self.agent, 'account') or not self.agent.account:
                print("   ❌ No account configured")
                return False

            # Check address format
            if not hasattr(self.agent, 'address') or len(self.agent.address) != 42:
                print("   ❌ Invalid wallet address")
                return False

            # Test ETH balance access
            try:
                eth_balance = self.agent.get_eth_balance()
                print(f"   ✅ ETH balance: {eth_balance:.6f} ETH")

                if eth_balance < 0.001:
                    print("   ⚠️ Low ETH balance for gas fees")

            except Exception as balance_error:
                print(f"   ⚠️ ETH balance check failed: {balance_error}")

            print(f"   ✅ Account setup OK - {self.agent.address}")
            return True

        except Exception as e:
            print(f"   ❌ Account validation failed: {e}")
            return False

    def _validate_integrations(self) -> bool:
        """Validate DeFi integration readiness"""
        try:
            print("🔧 Testing integration readiness...")

            # Check if integrations are initialized
            integrations_ready = True

            required_integrations = [
                ('aave', 'Aave'),
                ('uniswap', 'Uniswap'),
                ('health_monitor', 'Health Monitor'),
                ('gas_calculator', 'Gas Calculator')
            ]

            for attr_name, display_name in required_integrations:
                if not hasattr(self.agent, attr_name) or getattr(self.agent, attr_name) is None:
                    print(f"   ❌ {display_name} not initialized")
                    integrations_ready = False
                else:
                    print(f"   ✅ {display_name} ready")

            return integrations_ready

        except Exception as e:
            print(f"   ❌ Integration validation failed: {e}")
            return False

def validate_system_enhanced(agent) -> bool:
    """Enhanced system validation function"""
    validator = EnhancedSystemValidator(agent)
    return validator.run_comprehensive_validation()