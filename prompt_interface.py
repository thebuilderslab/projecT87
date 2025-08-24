
from multi_wallet_agent import MultiWalletAgent, create_multi_wallet_prompt
import json

class PromptInterface:
    def __init__(self):
        self.agent = MultiWalletAgent()
        
    def process_wallet_strategy_prompt(self, user_prompt):
        """
        Process natural language prompts for wallet strategies
        
        Example prompts:
        - "Execute health factor strategy on wallet 0x123... on Arbitrum mainnet"
        - "Monitor wallet 0xabc... for yield opportunities on Ethereum"
        - "Set up risk management for 0xdef... on Arbitrum with 1.25 health factor target"
        """
        
        # Extract wallet address from prompt
        wallet_address = self.extract_wallet_address(user_prompt)
        network = self.extract_network(user_prompt)
        strategy_type = self.extract_strategy_type(user_prompt)
        
        if not wallet_address:
            return {
                'error': 'No wallet address found in prompt',
                'help': 'Please include a wallet address like: 0x742d35Cc6676C4C8da4fDc4d0D60a6f3F8E2d6d1'
            }
        
        print(f"🎯 PROCESSING WALLET STRATEGY REQUEST")
        print(f"   Wallet: {wallet_address}")
        print(f"   Network: {network}")
        print(f"   Strategy: {strategy_type}")
        
        # Generate strategy configuration
        strategy_config = self.build_strategy_config(user_prompt, strategy_type)
        
        # Execute strategy
        try:
            result = self.agent.execute_strategy_for_wallet(wallet_address, network, strategy_config)
            
            return {
                'success': True,
                'wallet_address': wallet_address,
                'network': network,
                'strategy_type': strategy_type,
                'config': strategy_config,
                'result': result,
                'next_steps': self.generate_next_steps(strategy_type)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'wallet_address': wallet_address,
                'network': network,
                'suggestion': 'Try with monitor_only strategy first'
            }
    
    def extract_wallet_address(self, prompt):
        """Extract wallet address from prompt"""
        import re
        
        # Look for Ethereum address pattern
        pattern = r'0x[a-fA-F0-9]{40}'
        match = re.search(pattern, prompt)
        
        return match.group(0) if match else None
    
    def extract_network(self, prompt):
        """Extract network from prompt"""
        prompt_lower = prompt.lower()
        
        if 'arbitrum mainnet' in prompt_lower or 'arbitrum main' in prompt_lower:
            return 'arbitrum_mainnet'
        elif 'arbitrum sepolia' in prompt_lower or 'arbitrum test' in prompt_lower:
            return 'arbitrum_sepolia'
        elif 'ethereum mainnet' in prompt_lower or 'ethereum main' in prompt_lower:
            return 'ethereum_mainnet'
        else:
            return 'arbitrum_mainnet'  # Default
    
    def extract_strategy_type(self, prompt):
        """Extract strategy type from prompt"""
        prompt_lower = prompt.lower()
        
        if 'monitor' in prompt_lower and 'only' in prompt_lower:
            return 'monitor_only'
        elif 'health factor' in prompt_lower or 'dynamic' in prompt_lower:
            return 'dynamic_health'
        elif 'yield' in prompt_lower or 'optimization' in prompt_lower:
            return 'yield_optimization'
        else:
            return 'monitor_only'  # Safe default
    
    def build_strategy_config(self, prompt, strategy_type):
        """Build strategy configuration from prompt"""
        config = {
            'type': strategy_type,
            'health_factor_target': 1.19,
            'borrow_trigger_threshold': 0.02,
            'risk_mitigation_enabled': True
        }
        
        # Extract specific parameters from prompt
        import re
        
        # Health factor target
        hf_match = re.search(r'health factor.*?(\d+\.?\d*)', prompt.lower())
        if hf_match:
            config['health_factor_target'] = float(hf_match.group(1))
        
        # Borrow threshold
        threshold_match = re.search(r'threshold.*?(\d+\.?\d*)', prompt.lower())
        if threshold_match:
            config['borrow_trigger_threshold'] = float(threshold_match.group(1))
        
        return config
    
    def generate_next_steps(self, strategy_type):
        """Generate next steps based on strategy type"""
        if strategy_type == 'monitor_only':
            return [
                "✅ Wallet is now being monitored",
                "📊 Check health factor and risk metrics",
                "🔄 Upgrade to dynamic_health for automated actions",
                "⚠️ Review recommendations in the output"
            ]
        elif strategy_type == 'dynamic_health':
            return [
                "🎯 Dynamic health management active",
                "🔄 Auto-borrowing when health factor increases",
                "⚠️ Risk mitigation triggers enabled",
                "📱 MetaMask approval needed for transactions"
            ]
        else:
            return [
                "🚀 Strategy configuration applied",
                "📊 Monitor performance metrics",
                "🔧 Adjust parameters as needed"
            ]

# Example usage functions
def execute_wallet_strategy_from_prompt(user_prompt):
    """Execute wallet strategy from natural language prompt"""
    interface = PromptInterface()
    return interface.process_wallet_strategy_prompt(user_prompt)

def example_prompts():
    """Show example prompts"""
    examples = [
        "Execute dynamic health factor strategy on wallet 0x742d35Cc6676C4C8da4fDc4d0D60a6f3F8E2d6d1 on Arbitrum mainnet",
        "Monitor wallet 0x1234567890123456789012345678901234567890 for yield opportunities with 1.25 health factor target",
        "Set up risk management for 0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef on Arbitrum sepolia",
        "Start monitoring only for wallet 0x9876543210987654321098765432109876543210 on Ethereum mainnet"
    ]
    
    print("📝 EXAMPLE PROMPTS:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    
    return examples

if __name__ == "__main__":
    print("🎯 Wallet Strategy Prompt Interface")
    print("=" * 50)
    
    # Show examples
    example_prompts()
    
    # Interactive prompt
    print("\n💬 Enter your wallet strategy prompt:")
    user_input = input("> ")
    
    if user_input.strip():
        result = execute_wallet_strategy_from_prompt(user_input)
        print("\n📊 RESULT:")
        print(json.dumps(result, indent=2))
    else:
        print("No prompt entered.")
