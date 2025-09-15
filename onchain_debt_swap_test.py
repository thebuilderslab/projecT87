#!/usr/bin/env python3
"""
On-Chain Debt Swap Test - Real Execution
Test: $10 DAI debt → ARB debt → wait 5 minutes → DAI debt
"""

import os
import time
import json
from datetime import datetime
from corrected_debt_swap_executor import CorrectedDebtSwapExecutor

class OnChainDebtSwapTest:
    """Real on-chain debt swap test execution"""
    
    def __init__(self, agent):
        self.agent = agent
        self.executor = CorrectedDebtSwapExecutor(agent)
        
        print(f"🧪 On-Chain Debt Swap Test initialized")
        print(f"   Test: $10 DAI debt → ARB debt → wait 5 min → DAI debt")
        print(f"   User: {agent.address}")

    def validate_debt_position_for_test(self) -> bool:
        """Validate user has sufficient DAI debt for test"""
        try:
            print(f"🔍 VALIDATING DEBT POSITION FOR TEST")
            
            # Get current Aave position
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
            
            pool_contract = self.agent.w3.eth.contract(
                address=self.executor.aave_pool,
                abi=pool_abi
            )
            
            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
            
            total_collateral_usd = account_data[0] / (10**8)
            total_debt_usd = account_data[1] / (10**8)
            health_factor = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
            
            print(f"📊 CURRENT POSITION:")
            print(f"   Total Collateral: ${total_collateral_usd:.2f}")
            print(f"   Total Debt: ${total_debt_usd:.2f}")
            print(f"   Health Factor: {health_factor:.6f}")
            
            # Validation checks
            checks = {
                'has_collateral': total_collateral_usd > 50,  # At least $50 collateral
                'has_debt': total_debt_usd >= 10,  # At least $10 debt
                'safe_health_factor': health_factor >= 1.5,  # Safe health factor (adjusted for test)
                'test_amount_ok': total_debt_usd >= 20  # Can handle $10 swaps
            }
            
            all_checks_pass = all(checks.values())
            
            print(f"✅ VALIDATION RESULTS:")
            for check, passed in checks.items():
                print(f"   {check.replace('_', ' ').title()}: {'✅' if passed else '❌'}")
            
            if not all_checks_pass:
                print(f"❌ Position not suitable for debt swap test")
                return False
            
            print(f"✅ Position validated - ready for debt swap test")
            return True
            
        except Exception as e:
            print(f"❌ Error validating position: {e}")
            return False

    def execute_real_debt_swap_with_execution_enabled(self, private_key: str, 
                                                     from_asset: str, to_asset: str, 
                                                     swap_amount_usd: float) -> dict:
        """Execute real debt swap with ENABLED on-chain execution"""
        
        execution_result = {
            'operation': f'{from_asset}_debt_to_{to_asset}_debt_swap',
            'start_time': datetime.now().isoformat(),
            'swap_amount_usd': swap_amount_usd,
            'success': False,
            'real_execution_enabled': True
        }
        
        try:
            print(f"\n🚀 EXECUTING REAL DEBT SWAP - ON-CHAIN ENABLED")
            print("=" * 60)
            print(f"Operation: {from_asset} debt → {to_asset} debt")
            print(f"Amount: ${swap_amount_usd:.2f}")
            print("=" * 60)
            
            # CRITICAL FIX: Use corrected executor method instead of duplicate broken logic
            print(f"🔄 DELEGATING TO CORRECTED EXECUTOR (with amount binding fix)")
            return self.executor.execute_real_debt_swap(private_key, from_asset, to_asset, swap_amount_usd)
            
            # Create credit delegation permit
            credit_permit = self.executor.create_correct_credit_delegation_permit(
                private_key, new_debt_token
            )
            
            if not credit_permit:
                raise Exception("Failed to create credit delegation permit")
            
            # Build transaction
            debt_swap_contract = self.agent.w3.eth.contract(
                address=self.executor.paraswap_debt_swap_adapter,
                abi=self.executor.debt_swap_adapter_abi
            )
            
            function_call = debt_swap_contract.functions.swapDebt(
                self.executor.tokens[from_asset.upper()],  # assetToSwapFrom
                self.executor.tokens[to_asset.upper()],    # assetToSwapTo  
                amount_to_swap,                           # amountToSwap
                bytes.fromhex(paraswap_data['calldata'][2:]),  # paraswapData
                (
                    credit_permit['token'],       # token
                    credit_permit['delegatee'],   # delegatee
                    credit_permit['value'],       # value
                    credit_permit['deadline'],    # deadline
                    credit_permit['v'],           # v
                    credit_permit['r'],           # r
                    credit_permit['s']            # s
                )
            )
            
            # Get gas estimate
            try:
                gas_estimate = function_call.estimate_gas({'from': self.agent.address})
                gas_limit = int(gas_estimate * 1.2)
            except Exception:
                gas_limit = 800000  # Conservative fallback
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.agent.address,
                'gas': gas_limit,
                'gasPrice': self.agent.w3.eth.gas_price,
                'nonce': self.agent.w3.eth.get_transaction_count(self.agent.address)
            })
            
            execution_result['transaction_prepared'] = {
                'gas_limit': gas_limit,
                'gas_price': self.agent.w3.eth.gas_price,
                'estimated_cost_eth': (gas_limit * self.agent.w3.eth.gas_price) / 1e18
            }
            
            print(f"✅ Transaction prepared")
            print(f"   Gas Limit: {gas_limit:,}")
            print(f"   Gas Price: {self.agent.w3.eth.gas_price / 1e9:.2f} gwei")
            print(f"   Est. Cost: {(gas_limit * self.agent.w3.eth.gas_price) / 1e18:.6f} ETH")
            
            # REAL EXECUTION ENABLED - Sign and send transaction
            user_account = self.agent.w3.eth.account.from_key(private_key)
            signed_tx = user_account.sign_transaction(transaction)
            
            print(f"\n🚀 SENDING TRANSACTION ON-CHAIN...")
            tx_hash = self.agent.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"✅ TRANSACTION SENT: {tx_hash_hex}")
            
            # Wait for confirmation
            print(f"⏳ Waiting for transaction confirmation...")
            receipt = self.agent.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                print(f"✅ TRANSACTION CONFIRMED!")
                print(f"   Block: {receipt['blockNumber']}")
                print(f"   Gas Used: {receipt['gasUsed']:,}")
                print(f"   Arbiscan: https://arbiscan.io/tx/{tx_hash_hex}")
                
                execution_result['success'] = True
                execution_result['tx_hash'] = tx_hash_hex
                execution_result['block_number'] = receipt['blockNumber']
                execution_result['gas_used'] = receipt['gasUsed']
            else:
                print(f"❌ TRANSACTION FAILED")
                execution_result['error'] = 'Transaction reverted'
                execution_result['tx_hash'] = tx_hash_hex
            
            return execution_result
            
        except Exception as e:
            print(f"❌ Real debt swap execution failed: {e}")
            execution_result['error'] = str(e)
            return execution_result
        
        finally:
            execution_result['end_time'] = datetime.now().isoformat()

    def execute_debt_swap_cycle_test(self, private_key: str) -> dict:
        """Execute the exact test: $10 DAI debt → ARB debt → wait 5 min → DAI debt"""
        
        test_result = {
            'test_name': 'onchain_debt_swap_cycle_test',
            'start_time': datetime.now().isoformat(),
            'test_amount_usd': 2.0,
            'wait_time_minutes': 5,
            'phases': {},
            'overall_success': False
        }
        
        try:
            print(f"\n🧪 ON-CHAIN DEBT SWAP CYCLE TEST")
            print("=" * 80)
            print(f"Test: $10 DAI debt → ARB debt → wait 5 minutes → DAI debt")
            print(f"Real on-chain execution ENABLED")
            print("=" * 80)
            
            # Validate position first
            if not self.validate_debt_position_for_test():
                raise Exception("Position validation failed - cannot proceed with test")
            
            # Phase 1: DAI debt → ARB debt
            print(f"\n🚀 PHASE 1: DAI DEBT → ARB DEBT ($10)")
            phase1_result = self.execute_real_debt_swap_with_execution_enabled(
                private_key, 'DAI', 'ARB', 2.0
            )
            
            test_result['phases']['phase_1_dai_to_arb'] = phase1_result
            
            if not phase1_result.get('success'):
                raise Exception(f"Phase 1 failed: {phase1_result.get('error', 'Unknown error')}")
            
            print(f"✅ PHASE 1 COMPLETED SUCCESSFULLY")
            print(f"   Transaction: {phase1_result['tx_hash']}")
            
            # Wait 5 minutes
            print(f"\n⏳ WAITING 5 MINUTES BEFORE REVERSE SWAP...")
            wait_time = 5 * 60  # 5 minutes
            
            for minute in range(5):
                remaining = 5 - minute
                print(f"   ⏱️  {remaining} minutes remaining...")
                time.sleep(60)  # Wait 1 minute
            
            print(f"✅ 5-minute wait completed")
            
            # Phase 2: ARB debt → DAI debt
            print(f"\n🚀 PHASE 2: ARB DEBT → DAI DEBT ($10)")
            phase2_result = self.execute_real_debt_swap_with_execution_enabled(
                private_key, 'ARB', 'DAI', 2.0
            )
            
            test_result['phases']['phase_2_arb_to_dai'] = phase2_result
            
            if not phase2_result.get('success'):
                raise Exception(f"Phase 2 failed: {phase2_result.get('error', 'Unknown error')}")
            
            print(f"✅ PHASE 2 COMPLETED SUCCESSFULLY")
            print(f"   Transaction: {phase2_result['tx_hash']}")
            
            # Test completed successfully
            test_result['overall_success'] = True
            
            print(f"\n🎉 ON-CHAIN DEBT SWAP CYCLE TEST COMPLETED!")
            print("=" * 80)
            print(f"✅ Phase 1: DAI → ARB debt swap successful")
            print(f"✅ Phase 2: ARB → DAI debt swap successful")
            print(f"✅ Full cycle completed in ~5 minutes")
            print(f"✅ Both transactions confirmed on Arbitrum")
            
            # Display transaction links
            print(f"\n🔗 TRANSACTION LINKS:")
            print(f"   Phase 1: https://arbiscan.io/tx/{phase1_result['tx_hash']}")
            print(f"   Phase 2: https://arbiscan.io/tx/{phase2_result['tx_hash']}")
            
            return test_result
            
        except Exception as e:
            print(f"❌ On-chain debt swap test failed: {e}")
            test_result['error'] = str(e)
            return test_result
        
        finally:
            test_result['end_time'] = datetime.now().isoformat()
            
            # Save test results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"onchain_debt_swap_test_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(test_result, f, indent=2, default=str)
            
            print(f"\n📁 Test results saved to: {filename}")

def main():
    """Execute on-chain debt swap test"""
    print("🧪 ON-CHAIN DEBT SWAP TEST - REAL EXECUTION")
    print("=" * 80)
    print("Test: $10 DAI debt → ARB debt → wait 5 minutes → DAI debt")
    print("=" * 80)
    
    try:
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        print("🤖 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent or not hasattr(agent, 'w3'):
            raise Exception("Agent initialization failed")
        
        print(f"✅ Agent initialized: {agent.address}")
        
        # Get private key from environment
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise Exception("PRIVATE_KEY environment variable required")
        
        # Execute test
        test_executor = OnChainDebtSwapTest(agent)
        test_result = test_executor.execute_debt_swap_cycle_test(private_key)
        
        # Summary
        if test_result.get('overall_success'):
            print(f"\n🎉 ON-CHAIN DEBT SWAP TEST: SUCCESS!")
            print(f"✅ System successfully executed DAI↔ARB debt swaps on-chain")
        else:
            print(f"\n❌ ON-CHAIN DEBT SWAP TEST: FAILED")
            print(f"Error: {test_result.get('error', 'Unknown error')}")
        
        return test_result
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    main()