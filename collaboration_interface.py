
#!/usr/bin/env python3

from collaborative_strategy_manager import CollaborativeStrategyManager
from arbitrum_testnet_agent import ArbitrumTestnetAgent
import json

class CollaborationInterface:
    def __init__(self):
        try:
            self.agent = ArbitrumTestnetAgent()
            self.strategy_manager = CollaborativeStrategyManager(self.agent)
            print("🤝 Collaboration Interface Ready!")
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            
    def show_menu(self):
        """Show collaboration menu options"""
        print("\n🤝 COLLABORATION MENU:")
        print("1. 📋 Review Pending Proposals")
        print("2. ✅ Approve/Reject Proposals") 
        print("3. 💡 Submit Your Strategy Idea")
        print("4. 🔧 Propose Code Modification")
        print("5. 📊 View Strategy Performance")
        print("6. 🤖 Trigger Agent Analysis")
        print("0. Exit")
        
    def review_proposals(self):
        """Review all pending proposals"""
        proposals = self.strategy_manager.get_user_input_on_proposals()
        if proposals:
            print(f"\n📝 Found {len(proposals)} proposals requiring your attention.")
        
    def approve_reject_proposals(self):
        """Interactive approval/rejection of proposals"""
        proposals = self.strategy_manager.get_user_input_on_proposals()
        if not proposals:
            return
            
        for proposal in proposals:
            print(f"\n🔍 Reviewing: {proposal['id']}")
            print(f"Risk: {proposal['risk_level']} | Impact: {proposal['estimated_impact']}")
            
            choice = input("Approve (y), Reject (n), or Skip (s)? ").lower()
            
            if choice == 'y':
                success = self.strategy_manager.implement_approved_strategy(proposal['id'])
                print(f"{'✅ Implemented' if success else '❌ Failed'}")
            elif choice == 'n':
                # Mark as rejected
                print("❌ Proposal rejected")
                
    def submit_strategy_idea(self):
        """Allow user to submit strategy improvements"""
        print("\n💡 SUBMIT YOUR STRATEGY IDEA:")
        
        strategy_types = [
            "risk_reduction", "yield_optimization", "asset_diversification",
            "timing_optimization", "code_modification", "monitoring_enhancement"
        ]
        
        print("Available strategy types:")
        for i, stype in enumerate(strategy_types, 1):
            print(f"{i}. {stype}")
            
        try:
            choice = int(input("Select type (1-6): ")) - 1
            strategy_type = strategy_types[choice]
        except (ValueError, IndexError):
            print("❌ Invalid choice")
            return
            
        description = input("Describe your strategy idea: ")
        
        # Collect specific parameters based on type
        parameters = {}
        if strategy_type == "yield_optimization":
            parameters["target_apy"] = input("Target APY (%): ")
            parameters["max_leverage"] = input("Max leverage ratio: ")
        elif strategy_type == "risk_reduction":
            parameters["max_health_factor"] = input("Max health factor: ")
            parameters["emergency_threshold"] = input("Emergency threshold: ")
            
        proposal_id = self.strategy_manager.submit_user_improvement(
            strategy_type, description, parameters
        )
        
        print(f"✅ Strategy submitted with ID: {proposal_id}")
        
    def propose_code_modification(self):
        """Propose direct code changes"""
        print("\n🔧 PROPOSE CODE MODIFICATION:")
        
        modifications = {
            "1": "Add new DeFi protocol integration",
            "2": "Modify risk management logic", 
            "3": "Enhance monitoring capabilities",
            "4": "Add new trading strategy",
            "5": "Custom code change"
        }
        
        for key, desc in modifications.items():
            print(f"{key}. {desc}")
            
        choice = input("Select modification type: ")
        
        if choice == "5":
            # Custom code change
            target_file = input("Target file (e.g., arbitrum_testnet_agent.py): ")
            old_code = input("Code to replace (or 'NEW' for new function): ")
            new_code = input("New code: ")
            
            modification_data = {
                "target_file": target_file,
                "action": "add_function" if old_code == "NEW" else "modify_strategy",
                "old_code": old_code if old_code != "NEW" else None,
                "new_code": new_code,
                "description": "User-proposed code modification"
            }
            
            proposal_id = self.strategy_manager.propose_strategy_improvement(
                "code_modification", modification_data, "user"
            )
            
            print(f"✅ Code modification proposed with ID: {proposal_id}")
    
    def run_interactive_session(self):
        """Run interactive collaboration session"""
        while True:
            self.show_menu()
            choice = input("\nSelect option: ")
            
            if choice == "1":
                self.review_proposals()
            elif choice == "2":
                self.approve_reject_proposals()
            elif choice == "3":
                self.submit_strategy_idea()
            elif choice == "4":
                self.propose_code_modification()
            elif choice == "5":
                print("📊 Strategy performance analysis coming soon...")
            elif choice == "6":
                print("🤖 Triggering agent analysis...")
                self.strategy_manager.agent_analyze_and_propose()
            elif choice == "0":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")

if __name__ == "__main__":
    interface = CollaborationInterface()
    interface.run_interactive_session()
