#!/usr/bin/env python3
"""
Enhanced Debt Swap with Automatic Token Approval Management
"""

from production_debt_swap_executor import ProductionDebtSwapExecutor
from web3 import Web3

class AutoApprovalDebtSwapExecutor(ProductionDebtSwapExecutor):
    """Enhanced debt swap executor with automatic approval management"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paraswap_router = "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57"
        
    def check_and_approve_token_if_needed(self, token_address, required_amount_tokens):
        """
        Check token allowance and automatically approve if insufficient
        Returns: (bool) True if sufficient allowance exists or approval successful
        """
        print(f"🔍 Checking {token_address} allowance...")
        
        erc20_abi = [
            {
                'inputs': [
                    {'name': 'owner', 'type': 'address'},
                    {'name': 'spender', 'type': 'address'}
                ],
                'name': 'allowance',
                'outputs': [{'name': '', 'type': 'uint256'}],
                'stateMutability': 'view',
                'type': 'function'
            },
            {
                'inputs': [
                    {'name': 'spender', 'type': 'address'},
                    {'name': 'amount', 'type': 'uint256'}
                ],
                'name': 'approve',
                'outputs': [{'name': '', 'type': 'bool'}],
                'stateMutability': 'nonpayable',
                'type': 'function'
            }
        ]
        
        try:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            
            # Check current allowance
            current_allowance = token_contract.functions.allowance(
                self.user_address,
                self.paraswap_router
            ).call()
            
            allowance_tokens = current_allowance / 1e18
            
            print(f"   Current allowance: {allowance_tokens:.6f}")
            print(f"   Required: {required_amount_tokens:.6f}")
            
            # If sufficient allowance exists
            if allowance_tokens >= required_amount_tokens:
                print("   ✅ Sufficient allowance - no approval needed")
                return True
            
            # Need to approve more tokens
            print("   ⚠️ Insufficient allowance - auto-approving...")
            
            # Approve 2x the required amount to reduce future approvals
            approval_amount = int(required_amount_tokens * 2 * 1e18)
            
            # Build approval transaction
            approval_tx = token_contract.functions.approve(
                self.paraswap_router,
                approval_amount
            ).build_transaction({
                'from': self.user_address,
                'gas': 60000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.user_address)
            })
            
            # Sign and send approval
            signed_tx = self.w3.eth.account.sign_transaction(approval_tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print(f"   ✅ Auto-approval successful: {approval_amount/1e18:.2f} tokens")
                return True
            else:
                print("   ❌ Auto-approval failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Approval check/execution failed: {e}")
            return False
    
    def execute_debt_swap_with_auto_approval(self, from_token, to_token, amount_usd):
        """
        Execute debt swap with automatic token approval handling
        """
        print(f"🚀 EXECUTING DEBT SWAP WITH AUTO-APPROVAL")
        print(f"   From: {from_token} debt → {to_token} debt")
        print(f"   Amount: ${amount_usd}")
        
        # Calculate required token amounts
        if to_token == 'ARB':
            # For DAI→ARB swap, we need ARB tokens
            arb_price = 0.55  # Current ARB price
            required_arb = amount_usd / arb_price
            
            # Step 1: Auto-check and approve ARB tokens
            if not self.check_and_approve_token_if_needed(
                self.tokens['ARB'], 
                required_arb
            ):
                return {
                    'success': False,
                    'error': 'Failed to ensure ARB token approval'
                }
        
        # Step 2: Execute the debt swap (existing logic)
        return self.execute_debt_swap(from_token, to_token, amount_usd)

# Usage example:
def demo_auto_approval():
    """Demonstrate automatic approval + debt swap"""
    
    print("🤖 AUTOMATED DEBT SWAP WITH AUTO-APPROVAL")
    print("=" * 50)
    
    # This would automatically:
    # 1. Check ARB token allowance to ParaSwap
    # 2. Auto-approve ARB tokens if needed (once)  
    # 3. Execute debt swap
    # 4. Future swaps won't need approval (until tokens used up)
    
    executor = AutoApprovalDebtSwapExecutor()
    
    result = executor.execute_debt_swap_with_auto_approval(
        from_token='DAI',
        to_token='ARB', 
        amount_usd=30.0
    )
    
    print(f"Result: {result}")

if __name__ == "__main__":
    demo_auto_approval()