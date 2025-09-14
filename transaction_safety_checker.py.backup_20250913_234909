
#!/usr/bin/env python3
"""
Transaction Safety Checker - Validate transaction parameters before execution
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent

class TransactionSafetyChecker:
    def __init__(self, agent):
        self.agent = agent
        self.w3 = agent.w3
        
    def validate_borrow_transaction(self, amount_usd, token_address):
        """Comprehensive borrow transaction validation"""
        print(f"🔒 TRANSACTION SAFETY CHECK: Borrow ${amount_usd:.2f}")
        print("=" * 50)
        
        safety_report = {
            'safe_to_proceed': False,
            'warnings': [],
            'critical_issues': [],
            'recommendations': []
        }
        
        try:
            # Check 1: Validate amount
            if amount_usd <= 0:
                safety_report['critical_issues'].append(f"Invalid amount: ${amount_usd:.2f}")
                return safety_report
                
            # Check 2: Get current Aave position
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
            
            pool_contract = self.w3.eth.contract(address=self.agent.aave_pool_address, abi=pool_abi)
            account_data = pool_contract.functions.getUserAccountData(self.agent.address).call()
            
            total_collateral_usd = account_data[0] / 1e8
            total_debt_usd = account_data[1] / 1e8
            available_borrows_usd = account_data[2] / 1e8
            health_factor = account_data[5] / 1e18 if account_data[5] > 0 else float('inf')
            
            print(f"📊 Current Position:")
            print(f"   Collateral: ${total_collateral_usd:.2f}")
            print(f"   Debt: ${total_debt_usd:.2f}")
            print(f"   Available: ${available_borrows_usd:.2f}")
            print(f"   Health Factor: {health_factor:.4f}")
            
            # Check 3: Health factor validation
            if health_factor < 1.5:
                safety_report['critical_issues'].append(f"Health factor too low: {health_factor:.4f} < 1.5")
            elif health_factor < 2.0:
                safety_report['warnings'].append(f"Health factor marginal: {health_factor:.4f}")
                
            # Check 4: Borrowing capacity
            if available_borrows_usd < amount_usd:
                safety_report['critical_issues'].append(f"Insufficient capacity: ${available_borrows_usd:.2f} < ${amount_usd:.2f}")
            elif available_borrows_usd < amount_usd * 1.2:
                safety_report['warnings'].append(f"Low safety margin for borrow amount")
                
            # Check 5: ETH balance for gas
            eth_balance = self.agent.get_eth_balance()
            min_eth_for_ops = 0.001
            
            if eth_balance < min_eth_for_ops:
                safety_report['critical_issues'].append(f"Insufficient ETH for gas: {eth_balance:.6f} < {min_eth_for_ops:.3f}")
            elif eth_balance < min_eth_for_ops * 2:
                safety_report['warnings'].append(f"Low ETH balance: {eth_balance:.6f}")
                
            # Check 6: Calculate post-borrow health factor
            if total_collateral_usd > 0:
                estimated_new_debt = total_debt_usd + amount_usd
                estimated_new_hf = (total_collateral_usd * 0.8) / estimated_new_debt if estimated_new_debt > 0 else float('inf')
                
                if estimated_new_hf < 1.25:
                    safety_report['critical_issues'].append(f"Post-borrow HF too low: {estimated_new_hf:.4f}")
                    
            # Final safety determination
            if len(safety_report['critical_issues']) == 0:
                safety_report['safe_to_proceed'] = True
                safety_report['recommendations'].append(f"Transaction appears safe to execute")
            else:
                safety_report['recommendations'].append(f"Address critical issues before proceeding")
                
            return safety_report
            
        except Exception as e:
            safety_report['critical_issues'].append(f"Safety check failed: {e}")
            return safety_report

def test_transaction_safety():
    """Test the transaction safety checker"""
    try:
        agent = ArbitrumTestnetAgent()
        checker = TransactionSafetyChecker(agent)
        
        # Test with a small amount
        safety_report = checker.validate_borrow_transaction(1.0, agent.usdc_address)
        
        print(f"\n🔍 SAFETY REPORT:")
        print(f"Safe to proceed: {safety_report['safe_to_proceed']}")
        
        if safety_report['warnings']:
            print(f"⚠️ Warnings:")
            for warning in safety_report['warnings']:
                print(f"   - {warning}")
                
        if safety_report['critical_issues']:
            print(f"❌ Critical Issues:")
            for issue in safety_report['critical_issues']:
                print(f"   - {issue}")
                
        if safety_report['recommendations']:
            print(f"💡 Recommendations:")
            for rec in safety_report['recommendations']:
                print(f"   - {rec}")
                
        return safety_report['safe_to_proceed']
        
    except Exception as e:
        print(f"❌ Safety test failed: {e}")
        return False

if __name__ == "__main__":
    test_transaction_safety()
