
#!/usr/bin/env python3
"""
Compound V3 Integration as Aave Fallback
"""

import requests
from web3 import Web3

class CompoundV3Fallback:
    def __init__(self, agent):
        self.agent = agent
        # Compound V3 USDC market on Arbitrum
        self.comet_usdc_address = "0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf"
        
    def borrow_from_compound(self, amount_usd):
        """Borrow USDC from Compound V3 as fallback"""
        try:
            print("🔄 Attempting Compound V3 borrow...")
            
            # Compound V3 minimal ABI
            comet_abi = [{
                "inputs": [{"name": "amount", "type": "uint256"}],
                "name": "withdraw",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
            
            comet_contract = self.agent.w3.eth.contract(
                address=self.comet_usdc_address,
                abi=comet_abi
            )
            
            # Convert to USDC decimals (6)
            amount_usdc = int(amount_usd * 1e6)
            
            # Build transaction
            tx = comet_contract.functions.withdraw(amount_usdc).build_transaction({
                'chainId': 42161,
                'gas': 300000,
                'gasPrice': self.agent.w3.eth.gas_price,
                'nonce': self.agent.w3.eth.get_transaction_count(self.agent.address),
                'from': self.agent.address
            })
            
            # Sign and send
            signed_tx = self.agent.w3.eth.account.sign_transaction(tx, self.agent.account.key)
            tx_hash = self.agent.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"✅ Compound V3 borrow successful: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            print(f"❌ Compound V3 borrow failed: {e}")
            return None
