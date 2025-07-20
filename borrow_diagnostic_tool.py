#!/usr/bin/env python3
"""
Comprehensive Borrowing Diagnostic Tool with Enhanced Validation
"""

import os
import json
import time
from datetime import datetime
from web3 import Web3
from enhanced_system_validator import EnhancedSystemValidator
from fix_json_serialization import safe_json_dump
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from config_constants import MIN_ETH_FOR_OPERATIONS


class BorrowDiagnosticTool:
    def __init__(self):
        self.agent = None
        self.issues = []
        self.fixes_applied = []
        self.validator = None

    def initialize_agent(self):
        """Initialize agent with error handling"""
        try:
            print("🤖 Initializing Arbitrum Agent...")
            self.agent = ArbitrumTestnetAgent()

            # Force integration initialization
            if not self.agent.initialize_integrations():
                self.issues.append("DeFi integrations failed to initialize")
                return False

            # Initialize the system validator
            self.validator = EnhancedSystemValidator(self.agent)

            print("✅ Agent initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Agent initialization failed: {e}")
            self.issues.append(f"Agent initialization: {e}")
            return False

    def diagnose_health_factor_validation(self):
        """Diagnose health factor validation issues"""
        print("\n🏥 DIAGNOSING HEALTH FACTOR VALIDATION...")

        try:
            # Get current health data
            health_data = self.agent.health_monitor.get_current_health_factor()

            if not health_data:
                self.issues.append("Cannot retrieve health factor data")
                return False

            hf = health_data['health_factor']
            collateral = health_data.get('total_collateral_usdc', 0)
            debt = health_data.get('total_debt_usdc', 0)
            available = health_data.get('available_borrows_usdc', 0)

            print(f"   Current Health Factor: {hf:.4f}")
            print(f"   Total Collateral: ${collateral:.2f}")
            print(f"   Total Debt: ${debt:.2f}")
            print(f"   Available Borrows: ${available:.2f}")

            # Validation checks
            if hf < 1.1:
                self.issues.append(f"Health factor too low: {hf:.4f} (minimum: 1.1)")
                return False

            if collateral == 0:
                self.issues.append("No collateral supplied to Aave")
                return False

            if available < 1.0:
                self.issues.append(f"Insufficient borrowing capacity: ${available:.2f}")
                return False

            print("✅ Health Factor validation passed")
            return True

        except Exception as e:
            print(f"❌ Health factor diagnosis failed: {e}")
            self.issues.append(f"Health factor validation: {e}")
            return False

    def diagnose_gas_optimization(self):
        """Diagnose gas price optimization issues"""
        print("\n⛽ DIAGNOSING GAS OPTIMIZATION...")

        try:
            # Test gas parameter calculation
            gas_params = self.agent.get_optimized_gas_params('aave_borrow', 'normal')

            print(f"   Gas Limit: {gas_params['gas']:,}")
            print(f"   Gas Price: {gas_params['gasPrice']:,} wei ({gas_params['gasPrice']/1e9:.3f} gwei)")

            # Validate gas parameters
            if gas_params['gas'] < 300000:
                self.issues.append(f"Gas limit too low: {gas_params['gas']} (minimum: 300,000)")

            if gas_params['gasPrice'] < 100000000:  # 0.1 gwei
                self.issues.append(f"Gas price too low: {gas_params['gasPrice']} wei")

            # Test network gas price
            network_gas = self.agent.w3.eth.gas_price
            print(f"   Network Gas Price: {network_gas:,} wei ({network_gas/1e9:.3f} gwei)")

            if gas_params['gasPrice'] < network_gas * 1.1:
                print("⚠️ Gas price may be insufficient for fast confirmation")

            print("✅ Gas optimization diagnosis completed")
            return True

        except Exception as e:
            print(f"❌ Gas optimization diagnosis failed: {e}")
            self.issues.append(f"Gas optimization: {e}")
            return False

    def diagnose_token_balances(self):
        """Diagnose token balance verification"""
        print("\n💰 DIAGNOSING TOKEN BALANCES...")

        import logging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

        try:
            # Check ETH balance for gas
            logging.debug(f"DEBUG: Checking ETH balance for wallet {self.agent.address}")
            eth_balance = self.agent.get_eth_balance()
            logging.debug(f"DEBUG: Raw ETH balance: {eth_balance:.10f} ETH")
            print(f"   ETH Balance: {eth_balance:.6f} ETH")

            if eth_balance < MIN_ETH_FOR_OPERATIONS:
                self.issues.append(f"Insufficient ETH for gas: {eth_balance:.6f} (minimum: {MIN_ETH_FOR_OPERATIONS:.8f})")

            # Check supplied balances on Aave
            tokens_to_check = [
                ("WBTC", self.agent.wbtc_address),
                ("WETH", self.agent.weth_address),
                ("USDC", self.agent.usdc_address)
            ]

            # Debug aToken addresses for verification
            atoken_addresses = {
                "WBTC": "0x6533afac2E7BCCB20dca161449A13A2D2d5B739A",  # aWBTC
                "WETH": "0xe50fA9b4c56454E2edF6BFf7c81b50c5F05aBE61",  # aWETH
                "USDC": "0x724dc807b04555b71ed48a6896b6F41593b8C637"   # aUSDC
            }

            logging.debug(f"DEBUG: Expected aToken addresses: {atoken_addresses}")

            total_supplied_value = 0

            for token_name, token_address in tokens_to_check:
                try:
                    logging.debug(f"DEBUG: ===== Checking {token_name} Supplied Balance =====")
                    logging.debug(f"DEBUG: Token name: {token_name}")
                    logging.debug(f"DEBUG: Underlying token address passed: {token_address}")
                    logging.debug(f"DEBUG: Expected aToken address: {atoken_addresses.get(token_name, 'UNKNOWN')}")
                    logging.debug(f"DEBUG: Wallet address: {self.agent.address}")

                    # Call the supplied balance function with detailed logging
                    logging.debug(f"DEBUG: Calling self.agent.aave.get_supplied_balance({token_address})")
                    supplied_balance = self.agent.aave.get_supplied_balance(token_address)
                    logging.debug(f"DEBUG: Raw supplied balance returned: {supplied_balance}")
                    logging.debug(f"DEBUG: Type of returned balance: {type(supplied_balance)}")

                    print(f"   {token_name} Supplied: {supplied_balance:.6f}")

                    # Rough USD value estimation
                    if token_name == "WBTC" and supplied_balance > 0:
                        usd_value = supplied_balance * 100000  # ~$100k per WBTC
                        total_supplied_value += usd_value
                        logging.debug(f"DEBUG: {token_name} USD value: ${usd_value:.2f}")
                    elif token_name == "WETH" and supplied_balance > 0:
                        usd_value = supplied_balance * 3000   # ~$3k per ETH
                        total_supplied_value += usd_value
                        logging.debug(f"DEBUG: {token_name} USD value: ${usd_value:.2f}")
                    elif token_name == "USDC" and supplied_balance > 0:
                        usd_value = supplied_balance  # 1:1 USD
                        total_supplied_value += usd_value
                        logging.debug(f"DEBUG: {token_name} USD value: ${usd_value:.2f}")
                    else:
                        logging.debug(f"DEBUG: {token_name} has zero balance, no USD value added")

                except Exception as balance_error:
                    print(f"   {token_name}: Error getting balance - {balance_error}")

            print(f"   Estimated Total Supplied Value: ${total_supplied_value:.2f}")

            if total_supplied_value < 50:
                self.issues.append(f"Insufficient collateral value: ${total_supplied_value:.2f} (minimum: $50)")

            print("✅ Token balance diagnosis completed")
            return True

        except Exception as e:
            print(f"❌ Token balance diagnosis failed: {e}")
            self.issues.append(f"Token balance verification: {e}")
            return False

    def diagnose_protocol_state(self):
        """Diagnose Aave protocol state"""
        print("\n🏦 DIAGNOSING AAVE PROTOCOL STATE...")

        try:
            # Test Aave pool contract connectivity
            pool_contract = self.agent.aave.pool_contract

            # Get pool revision to test connectivity
            try:
                # Test with getUserAccountData call
                user_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
                print("   Aave Pool Contract: ✅ Responsive")

                # Check if borrowing is enabled for USDC
                usdc_reserve_data = None
                try:
                    # This would require the data provider contract
                    print("   USDC Borrowing: ✅ Likely enabled (pool responsive)")
                except:
                    print("   USDC Borrowing: ⚠️ Unable to verify")

            except Exception as pool_error:
                print(f"   Aave Pool Contract: ❌ Error - {pool_error}")
                self.issues.append("Aave pool contract not responsive")
                return False

            # Test token approvals
            usdc_contract = self.agent.w3.eth.contract(
                address=self.agent.usdc_address,
                abi=self.agent.aave.erc20_abi
            )

            try:
                allowance = usdc_contract.functions.allowance(
                    self.agent.address, 
                    self.agent.aave_pool_address
                ).call()

                print(f"   USDC Allowance: {allowance:,}")

                if allowance == 0:
                    print("   ⚠️ USDC not approved for Aave")

            except Exception as approval_error:
                print(f"   USDC Approval Check: ❌ Error - {approval_error}")

            print("✅ Protocol state diagnosis completed")
            return True

        except Exception as e:
            print(f"❌ Protocol state diagnosis failed: {e}")
            self.issues.append(f"Protocol state check: {e}")
            return False

    def test_small_borrow(self):
        """Test a small borrow operation"""
        print("\n🧪 TESTING SMALL BORROW OPERATION...")

        try:
            # Get current health data
            health_data = self.agent.health_monitor.get_current_health_factor()
            available_borrows = health_data.get('available_borrows_usdc', 0)

            if available_borrows < 1.0:
                print(f"❌ Cannot test borrow: insufficient capacity (${available_borrows:.2f})")
                return False

            # Calculate safe test amount
            test_amount = min(1.0, available_borrows * 0.1)  # 10% of available or $1

            print(f"   Testing borrow of ${test_amount:.2f} USDC...")

            # Simulate the borrow without executing
            try:
                # This would use the enhanced borrow manager
                if hasattr(self.agent, 'enhanced_borrow_manager'):
                    print("   Enhanced Borrow Manager: ✅ Available")

                    # Test gas estimation for borrow
                    pool_contract = self.agent.aave.pool_contract
                    decimals = 6  # USDC decimals
                    amount_wei = int(test_amount * (10 ** decimals))

                    gas_estimate = pool_contract.functions.borrow(
                        Web3.to_checksum_address(self.agent.usdc_address),
                        amount_wei,
                        2,  # Variable rate
                        0,  # Referral code
                        Web3.to_checksum_address(self.agent.address)
                    ).estimate_gas({'from': self.agent.address})

                    print(f"   Gas Estimate: {gas_estimate:,}")

                    if gas_estimate > 1000000:
                        print("⚠️ Gas estimate very high")
                    else:
                        print("✅ Gas estimate reasonable")

                else:
                    print("❌ Enhanced Borrow Manager not available")
                    self.issues.append("Enhanced Borrow Manager not initialized")
                    return False

            except Exception as sim_error:
                print(f"❌ Borrow simulation failed: {sim_error}")
                self.issues.append(f"Borrow simulation: {sim_error}")
                return False

            print("✅ Small borrow test completed successfully")
            return True

        except Exception as e:
            print(f"❌ Small borrow test failed: {e}")
            self.issues.append(f"Small borrow test: {e}")
            return False

    def generate_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n📊 COMPREHENSIVE DIAGNOSTIC REPORT")
        print("=" * 60)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        report = {
            'timestamp': timestamp,
            'wallet_address': self.agent.address if self.agent else None,
            'network_mode': self.agent.network_mode if self.agent else None,
            'chain_id': self.agent.w3.eth.chain_id if self.agent and self.agent.w3 else None,
            'issues_found': self.issues,
            'fixes_applied': self.fixes_applied,
            'status': 'READY' if len(self.issues) == 0 else 'NEEDS_FIXES'
        }

        # Save report
        report_filename = f"borrow_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_filename, 'w') as f:
            safe_json_dump(report, f, indent=2)

        print(f"📄 Report saved: {report_filename}")

        if len(self.issues) == 0:
            print("🎉 ALL DIAGNOSTICS PASSED - SYSTEM READY FOR BORROWING!")
        else:
            print("❌ ISSUES FOUND - SYSTEM NEEDS FIXES:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")

        return report

    def run_full_diagnostic(self):
        """Run complete diagnostic suite"""
        print("🔍 COMPREHENSIVE BORROWING DIAGNOSTIC")
        print("=" * 60)

        # Step 1: Initialize agent
        if not self.initialize_agent():
            return self.generate_report()

        # Step 2: Health factor validation
        self.diagnose_health_factor_validation()

        # Step 3: Gas optimization
        self.diagnose_gas_optimization()

        # Step 4: Token balances
        self.diagnose_token_balances()

        # Step 5: Protocol state
        self.diagnose_protocol_state()

        # Step 6: Test small borrow
        self.test_small_borrow()

        # Step 7: Enhanced System Validation
        validation_results = self.validator.run_all_checks()  # Execute all validation checks

        if validation_results:
            print("\n🛠️  Validation Issues Found:")
            for issue in validation_results:
                print(f"   - {issue}")
                self.issues.append(issue)

        # Step 8: Generate report
        return self.generate_report()

def main():
    """Main diagnostic function"""
    diagnostic = BorrowDiagnosticTool()
    report = diagnostic.run_full_diagnostic()

    if report['status'] == 'READY':
        print("\n🚀 SYSTEM IS READY FOR AUTONOMOUS OPERATION!")
        return True
    else:
        print("\n🔧 PLEASE FIX THE IDENTIFIED ISSUES BEFORE PROCEEDING")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)