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
            'wallet_readiness': False
        }

        try:
            # Test 1: Network connectivity
            if self._validate_network():
                validation_results['network_connectivity'] = True

            # Test 2: Contract addresses
            if self._validate_contracts():
                validation_results['contract_addresses'] = True

            # Test 3: DeFi integrations
            if self._validate_integrations():
                validation_results['integrations'] = True

            # Test 4: Wallet readiness
            if self._validate_wallet():
                validation_results['wallet_readiness'] = True

            # Overall result
            passed_tests = sum(validation_results.values())
            total_tests = len(validation_results)

            print(f"📊 Validation Results: {passed_tests}/{total_tests} passed")

            if passed_tests == total_tests:
                print("✅ Enhanced system validation PASSED")
                return True
            else:
                print("❌ Enhanced system validation FAILED")
                return False

        except Exception as e:
            print(f"❌ Enhanced validation error: {e}")
            return False

    def _validate_network(self):
        """Validate network connectivity"""
        try:
            if not self.w3.is_connected():
                return False

            chain_id = self.w3.eth.chain_id
            block_number = self.w3.eth.block_number

            print(f"✅ Network: Chain {chain_id}, Block {block_number}")
            return True

        except Exception as e:
            print(f"❌ Network validation failed: {e}")
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
                    print(f"❌ Invalid {name} address")
                    return False

                code = self.w3.eth.get_code(Web3.to_checksum_address(address))
                if code == b'':
                    print(f"❌ No contract at {name} address")
                    return False

            print("✅ All contract addresses validated")
            return True

        except Exception as e:
            print(f"❌ Contract validation failed: {e}")
            return False

    def _validate_integrations(self):
        """Validate DeFi integrations"""
        try:
            if not hasattr(self.agent, 'aave') or not self.agent.aave:
                print("❌ Aave integration missing")
                return False

            if not hasattr(self.agent, 'uniswap') or not self.agent.uniswap:
                print("❌ Uniswap integration missing")
                return False

            if not hasattr(self.agent, 'health_monitor') or not self.agent.health_monitor:
                print("❌ Health monitor missing")
                return False

            print("✅ All integrations present")
            return True

        except Exception as e:
            print(f"❌ Integration validation failed: {e}")
            return False

    def _validate_wallet(self):
        """Validate wallet readiness"""
        try:
            eth_balance = self.agent.get_eth_balance()

            if eth_balance < 0.001:  # Minimum ETH for gas
                print(f"❌ Insufficient ETH: {eth_balance:.6f}")
                return False

            print(f"✅ Wallet ready - ETH: {eth_balance:.6f}")
            return True

        except Exception as e:
            print(f"❌ Wallet validation failed: {e}")
            return False

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
    # This would be called from the main diagnostic workflow
    print("Enhanced System Validator - Run from main diagnostic workflow")