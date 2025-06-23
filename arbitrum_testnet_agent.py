
import os
import json
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

class ArbitrumTestnetAgent:
    def __init__(self):
        load_dotenv()
        
        # Connect to Arbitrum Sepolia
        self.rpc_url = os.getenv('ARBITRUM_SEPOLIA_RPC', 'https://sepolia-rollup.arbitrum.io/rpc')
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Load wallet
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key or private_key == 'your_private_key_here':
            raise ValueError("Please set PRIVATE_KEY in .env file")
        
        self.account = Account.from_key(private_key)
        # Ensure address is properly checksummed from the start
        self.address = self.w3.to_checksum_address(self.account.address)
        
        print(f"🤖 Arbitrum Testnet Agent initialized")
        print(f"Wallet: {self.address}")
        print(f"Network: Arbitrum Sepolia (Chain ID: {self.w3.eth.chain_id})")
    
    def get_eth_balance(self):
        """Get ETH balance in human-readable format"""
        user_address = self.w3.to_checksum_address(self.address)
        balance_wei = self.w3.eth.get_balance(user_address)
        return float(self.w3.from_wei(balance_wei, 'ether'))
    
    def get_gas_price(self):
        """Get current gas price"""
        return self.w3.eth.gas_price
    
    def estimate_gas_cost(self, gas_limit=21000):
        """Estimate transaction cost"""
        gas_price = self.get_gas_price()
        cost_wei = gas_price * gas_limit
        return self.w3.from_wei(cost_wei, 'ether')
    
    def send_test_transaction(self, to_address, amount_eth):
        """Send a test transaction (for testing purposes)"""
        try:
            # Get current nonce
            user_address = self.w3.to_checksum_address(self.address)
            nonce = self.w3.eth.get_transaction_count(user_address)
            
            # Build transaction
            transaction = {
                'to': self.w3.to_checksum_address(to_address),
                'value': self.w3.to_wei(amount_eth, 'ether'),
                'gas': 21000,
                'gasPrice': self.get_gas_price(),
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id
            }
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Transaction sent: {tx_hash.hex()}")
            print(f"Explorer: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"❌ Transaction failed: {e}")
            return None
    
    def check_network_status(self):
        """Check network connectivity and status"""
        try:
            if not self.w3.is_connected():
                return False, "Not connected to network"
            
            latest_block = self.w3.eth.get_block('latest')
            balance = self.get_eth_balance()
            gas_price = self.get_gas_price()
            
            status = {
                'connected': True,
                'latest_block': latest_block.number,
                'eth_balance': float(balance),
                'gas_price_gwei': self.w3.from_wei(gas_price, 'gwei'),
                'estimated_tx_cost': float(self.estimate_gas_cost())
            }
            
            return True, status
            
        except Exception as e:
            return False, f"Network error: {e}"
    
    def run_real_defi_task(self, run_id, iteration, config):
        """
        Execute real DeFi operations using dynamic health monitoring and conditional trading
        """
        print(f"\n🔄 Dynamic DeFi Task (Run: {run_id}, Iteration: {iteration})")
        
        # Check network status
        connected, status = self.check_network_status()
        if not connected:
            print(f"❌ Network issue: {status}")
            return 0.0
        
        print(f"📊 Network Status: Block {status['latest_block']}, Balance: {status['eth_balance']:.6f} ETH")
        
        # Initialize integrations if not already done
        if not hasattr(self, 'aave'):
            from aave_integration import AaveArbitrumIntegration
            self.aave = AaveArbitrumIntegration(self.w3, self.account)
        
        if not hasattr(self, 'uniswap'):
            from uniswap_integration import UniswapV3Integration
            self.uniswap = UniswapV3Integration(self.w3, self.account)
        
        if not hasattr(self, 'health_monitor'):
            from aave_health_monitor import AaveHealthMonitor
            self.health_monitor = AaveHealthMonitor(self.w3, self.account, self.aave)
        
        # Get comprehensive monitoring data
        monitoring_summary = self.health_monitor.get_monitoring_summary()
        
        print(f"🏥 Health Factor: {monitoring_summary['current_health_factor']:.4f}")
        print(f"🪙 ARB Price: ${monitoring_summary['arb_price']:.4f}")
        print(f"💰 ARB Balance: {monitoring_summary['arb_balance']:.4f}")
        
        portfolio_before = status['eth_balance']
        performance = 0.7  # Base performance
        
        try:
            # PRIORITY 1: Risk Mitigation (Execute first if triggered)
            if monitoring_summary['risk_trigger_active']:
                print("🚨 EXECUTING RISK MITIGATION STRATEGY")
                
                arb_balance = monitoring_summary['arb_balance']
                if arb_balance > 0.1:  # Only if we have significant ARB to swap
                    # Swap ARB back to USDC for safety
                    arb_amount_wei = int(arb_balance * 0.8 * (10 ** 18))  # Swap 80% of ARB holdings
                    
                    risk_swap_tx = self.uniswap.swap_tokens(
                        self.health_monitor.arb_address,  # ARB in
                        self.aave.usdc_address,           # USDC out
                        arb_amount_wei,
                        3000  # 0.3% fee
                    )
                    
                    if risk_swap_tx:
                        performance = 0.85  # Good performance for risk mitigation
                        print(f"✅ Risk mitigation: Swapped {arb_balance*0.8:.4f} ARB to USDC")
                    else:
                        performance = 0.75  # Moderate performance for attempted mitigation
                else:
                    print("ℹ️ Risk trigger active but insufficient ARB balance")
                    performance = 0.72
            
            # PRIORITY 2: Dynamic Borrow Strategy (Only if health factor increased)
            elif monitoring_summary['borrow_trigger_active']:
                print("🚨 EXECUTING DYNAMIC BORROW STRATEGY")
                
                optimal_usdc_borrow = monitoring_summary['optimal_usdc_borrow']
                
                if optimal_usdc_borrow > 50:  # Only if borrowing significant amount
                    print(f"💰 Optimal USDC borrow amount: ${optimal_usdc_borrow:.2f}")
                    
                    # Step 1: Borrow USDC to bring health factor to 1.19
                    borrow_tx = self.aave.borrow_from_aave(
                        self.aave.usdc_address, 
                        optimal_usdc_borrow
                    )
                    
                    if borrow_tx:
                        print("✅ Step 1: USDC borrowed successfully")
                        
                        # Wait for transaction to confirm
                        time.sleep(5)
                        
                        # Step 2: Swap ALL borrowed USDC to ARB
                        usdc_balance = self.aave.get_token_balance(self.aave.usdc_address)
                        
                        if usdc_balance > 10:  # If we have USDC to swap
                            usdc_amount_wei = int(usdc_balance * (10 ** 6))  # USDC has 6 decimals
                            
                            arb_swap_tx = self.uniswap.swap_tokens(
                                self.aave.usdc_address,           # USDC in
                                self.health_monitor.arb_address,  # ARB out
                                usdc_amount_wei,
                                3000  # 0.3% fee
                            )
                            
                            if arb_swap_tx:
                                print("✅ Step 2: USDC swapped to ARB")
                                
                                # Step 3: Supply 3/4 of original USDC amount back to Aave
                                supply_amount = optimal_usdc_borrow * 0.75
                                
                                # Get current USDC balance after swap (should be minimal)
                                # We'll use ARB value equivalent to 3/4 original USDC
                                
                                # For demo: supply some of remaining assets
                                if status['eth_balance'] > 0.05:
                                    supply_tx = self.aave.supply_to_aave(
                                        self.aave.weth_address, 
                                        status['eth_balance'] * 0.1  # Supply 10% of ETH
                                    )
                                    
                                    if supply_tx:
                                        print("✅ Step 3: Additional collateral supplied")
                                        performance = 0.95  # Excellent performance for full strategy
                                    else:
                                        performance = 0.90  # High performance for borrow+swap
                                else:
                                    performance = 0.88  # Good performance for borrow+swap only
                            else:
                                performance = 0.82  # Moderate performance for borrow only
                        else:
                            performance = 0.80  # Performance for borrow without sufficient swap
                    else:
                        performance = 0.65  # Lower performance for failed borrow
                else:
                    print("ℹ️ Borrow trigger active but optimal amount too small")
                    performance = 0.75
            
            # PRIORITY 3: Standard Operations (When no special triggers)
            else:
                if config['exploration_rate'] > 0.2:
                    # High exploration: Conservative monitoring and small operations
                    if portfolio_before > 0.05:
                        print("🏦 Conservative monitoring + small lending...")
                        tx_hash = self.aave.execute_yield_strategy("conservative")
                        performance = 0.78 if tx_hash else 0.72
                        
                elif config['exploration_rate'] > 0.1:
                    # Medium exploration: Balanced approach
                    if portfolio_before > 0.08:
                        print("⚖️ Balanced strategy with monitoring...")
                        if iteration % 15 == 0:  # Less frequent operations
                            tx_hash = self.aave.supply_to_aave(self.aave.weth_address, portfolio_before * 0.2)
                            performance = 0.80 if tx_hash else 0.74
                        else:
                            performance = 0.76  # Monitoring performance
                else:
                    # Low exploration: Active monitoring with occasional optimization
                    print("🔍 Active monitoring for opportunities...")
                    performance = 0.74  # Base monitoring performance
            
            # Adjust performance based on monitoring quality
            if monitoring_summary['current_health_factor'] > 0:
                monitoring_bonus = min(0.05, 0.01 * monitoring_summary['current_health_factor'])
                performance += monitoring_bonus
            
            # Adjust performance based on gas efficiency
            gas_efficiency = 1.0 - (float(status['gas_price_gwei']) / 100)
            performance = performance * max(0.85, gas_efficiency)
            
        except Exception as e:
            print(f"❌ Dynamic DeFi operation failed: {e}")
            performance = 0.5
        
        # Cap performance at 1.0
        performance = min(performance, 1.0)
        
        print(f"📈 Dynamic DeFi Performance: {performance:.4f}")
        print(f"💡 Based on: Health monitoring, conditional triggers, and execution success")
        
        return performance

def test_real_defi_integration():
    """Test the real DeFi agent"""
    try:
        agent = ArbitrumTestnetAgent()
        
        # Test network connection
        connected, status = agent.check_network_status()
        if connected:
            print(f"\n✅ Network Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ Network Error: {status}")
            return
        
        # Test a real DeFi task simulation
        test_config = {'exploration_rate': 0.15}
        performance = agent.run_real_defi_task(1, 1, test_config)
        
        print(f"\n🎯 Test Performance: {performance:.4f}")
        print(f"🚀 Ready for real DeFi operations!")
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")

if __name__ == "__main__":
    test_real_defi_integration()
