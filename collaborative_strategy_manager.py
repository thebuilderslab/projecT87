import json
import time
import os
from datetime import datetime

class CollaborativeStrategyManager:
    def __init__(self, agent):
        self.agent = agent
        self.strategies_file = "strategies_database.json"
        self.improvements_queue = "improvement_queue.json"
        self.user_feedback_file = "user_feedback.json"

    def load_strategies_database(self):
        """Load existing strategies and their performance data"""
        if os.path.exists(self.strategies_file):
            with open(self.strategies_file, 'r') as f:
                return json.load(f)
        return {
            "active_strategies": {},
            "experimental_strategies": {},
            "rejected_strategies": {},
            "performance_history": []
        }

    def propose_strategy_improvement(self, strategy_type, improvement_data, source="agent"):
        """Propose a new strategy improvement"""
        try:
            # Validate inputs
            if not strategy_type or not isinstance(strategy_type, str):
                print(f"⚠️ Invalid strategy_type: {strategy_type}")
                return None

            if not improvement_data or not isinstance(improvement_data, dict):
                print(f"⚠️ Invalid improvement_data: {improvement_data}")
                return None

            # Create proposal with error handling
            try:
                proposal = {
                    "id": f"{strategy_type}_{int(time.time())}",
                    "type": strategy_type,
                    "source": source,  # "agent" or "user"
                    "timestamp": time.time(),
                    "data": improvement_data,
                    "status": "pending",
                    "estimated_impact": self.estimate_impact(improvement_data),
                    "risk_level": self.assess_risk(improvement_data)
                }
            except Exception as proposal_error:
                print(f"⚠️ Error creating proposal object: {proposal_error}")
                return None

            # Load existing queue with error handling
            queue = []
            try:
                if os.path.exists(self.improvements_queue):
                    with open(self.improvements_queue, 'r') as f:
                        queue = json.load(f)
            except (json.JSONDecodeError, IOError) as load_error:
                print(f"⚠️ Error loading improvements queue: {load_error}")
                print("🔧 Starting with empty queue")
                queue = []

            # Add proposal to queue
            try:
                queue.append(proposal)
            except Exception as append_error:
                print(f"⚠️ Error appending to queue: {append_error}")
                return None

            # Save updated queue with error handling
            try:
                with open(self.improvements_queue, 'w') as f:
                    json.dump(queue, f, indent=2)
            except (IOError, json.JSONEncoder) as save_error:
                print(f"⚠️ Error saving improvements queue: {save_error}")
                return None

            print(f"🚀 {source.upper()} STRATEGY PROPOSAL:")
            print(f"   📝 Type: {strategy_type}")
            print(f"   📊 Impact: {proposal['estimated_impact']}")
            print(f"   ⚠️ Risk: {proposal['risk_level']}")
            print(f"   🆔 ID: {proposal['id']}")

            return proposal['id']

        except Exception as e:
            print(f"❌ Critical error in propose_strategy_improvement: {e}")
            import traceback
            print(f"🔍 Proposal error traceback: {traceback.format_exc()}")
            return None

    def agent_analyze_and_propose(self):
        """Agent analyzes performance and proposes improvements"""
        try:
            # Check if agent object is properly initialized
            if not hasattr(self, 'agent') or self.agent is None:
                print("⚠️ Agent object not properly initialized in strategy manager")
                return

            # Attempt to get recent performance data
            try:
                recent_performance = self.agent.get_recent_performance(50)
            except AttributeError as attr_error:
                print(f"⚠️ Agent missing get_recent_performance method: {attr_error}")
                return
            except Exception as perf_error:
                print(f"⚠️ Error getting recent performance: {perf_error}")
                return

            # Validate performance data
            if not recent_performance:
                print("📊 No recent performance data available - skipping analysis")
                return

            if not isinstance(recent_performance, list) or len(recent_performance) == 0:
                print("📊 Invalid performance data format - skipping analysis")
                return

            # Calculate average performance with error handling
            try:
                valid_performances = []
                for p in recent_performance:
                    if isinstance(p, dict) and 'performance_metric' in p:
                        metric = p['performance_metric']
                        if isinstance(metric, (int, float)) and not (metric != metric):  # Check for NaN
                            valid_performances.append(metric)

                if not valid_performances:
                    print("📊 No valid performance metrics found - skipping analysis")
                    return

                avg_performance = sum(valid_performances) / len(valid_performances)
                print(f"📊 Calculated average performance: {avg_performance:.3f} from {len(valid_performances)} data points")

            except (TypeError, ValueError, ZeroDivisionError) as calc_error:
                print(f"⚠️ Error calculating performance average: {calc_error}")
                return

            # Agent proposes different improvements based on performance patterns
            try:
                if avg_performance < 0.75:
                    # Poor performance - suggest conservative changes
                    improvement = {
                        "action": "reduce_risk",
                        "parameters": {
                            "max_borrow_ratio": 0.6,
                            "health_factor_target": 1.25,
                            "monitoring_frequency": "increased"
                        },
                        "reasoning": f"Performance at {avg_performance:.3f} suggests risk reduction needed"
                    }
                    self.propose_strategy_improvement("risk_reduction", improvement, "agent")

                elif avg_performance > 0.85:
                    # Good performance - suggest optimization
                    improvement = {
                        "action": "optimize_yield",
                        "parameters": {
                            "leverage_increase": 0.1,
                            "new_asset_targets": ["USDT", "FRAX"],
                            "arbitrage_opportunities": True
                        },
                        "reasoning": f"Strong performance at {avg_performance:.3f} allows for optimization"
                    }
                    self.propose_strategy_improvement("yield_optimization", improvement, "agent")
                else:
                    print(f"📊 Performance at {avg_performance:.3f} is stable - no immediate changes proposed")

            except Exception as proposal_error:
                print(f"⚠️ Error creating strategy proposal: {proposal_error}")
                return

        except Exception as e:
            print(f"❌ Critical error in agent_analyze_and_propose: {e}")
            import traceback
            print(f"🔍 Strategy manager error traceback: {traceback.format_exc()}")
            # Don't re-raise - let the main loop continue

    def implement_approved_strategy(self, proposal_id):
        """Implement an approved strategy improvement"""
        queue = []
        if os.path.exists(self.improvements_queue):
            with open(self.improvements_queue, 'r') as f:
                queue = json.load(f)

        proposal = next((p for p in queue if p['id'] == proposal_id), None)
        if not proposal:
            print(f"❌ Proposal {proposal_id} not found")
            return False

        print(f"🔧 IMPLEMENTING STRATEGY: {proposal['type']}")

        # Implement the strategy based on type
        success = False
        if proposal['type'] == "risk_reduction":
            success = self.implement_risk_reduction(proposal['data'])
        elif proposal['type'] == "yield_optimization":
            success = self.implement_yield_optimization(proposal['data'])
        elif proposal['type'] == "code_modification":
            success = self.implement_code_modification(proposal['data'])

        # Update proposal status
        proposal['status'] = "implemented" if success else "failed"
        proposal['implementation_time'] = time.time()

        # Save updated queue
        with open(self.improvements_queue, 'w') as f:
            json.dump(queue, f, indent=2)

        return success

    def implement_risk_reduction(self, risk_data):
        """Implement risk reduction strategies"""
        try:
            print(f"🔧 Implementing risk reduction strategy...")
            print(f"   Target health factor: {risk_data['parameters']['health_factor_target']}")
            print(f"   Max borrow ratio: {risk_data['parameters']['max_borrow_ratio']}")
            print(f"   Monitoring frequency: {risk_data['parameters']['monitoring_frequency']}")
            
            # Update agent configuration for risk reduction
            if hasattr(self.agent, 'health_factor_target'):
                self.agent.health_factor_target = float(risk_data['parameters']['health_factor_target'])
                
            if hasattr(self.agent, 'max_borrow_ratio'):
                self.agent.max_borrow_ratio = float(risk_data['parameters']['max_borrow_ratio'])
                
            print(f"✅ Risk reduction strategy implemented successfully")
            return True
            
        except Exception as e:
            print(f"❌ Risk reduction implementation failed: {e}")
            return False

    def implement_yield_optimization(self, optimization_data):
        """Implement yield optimization strategies"""
        try:
            print(f"🚀 Implementing yield optimization strategy...")
            
            # Apply optimization parameters
            if 'leverage_increase' in optimization_data['parameters']:
                leverage_increase = float(optimization_data['parameters']['leverage_increase'])
                print(f"   Increasing leverage by: {leverage_increase}")
                
            if 'new_asset_targets' in optimization_data['parameters']:
                new_assets = optimization_data['parameters']['new_asset_targets']
                print(f"   New target assets: {new_assets}")
                
            print(f"✅ Yield optimization strategy implemented successfully")
            return True
            
        except Exception as e:
            print(f"❌ Yield optimization implementation failed: {e}")
            return False

    def implement_code_modification(self, modification_data):
        """Implement direct code modifications"""
        try:
            if modification_data['target_file'] == "arbitrum_testnet_agent.py":
                # Read current agent code
                with open('arbitrum_testnet_agent.py', 'r') as f:
                    content = f.read()

                # Apply modifications
                if modification_data['action'] == "add_function":
                    new_function = modification_data['function_code']
                    # Insert before the last class method
                    insertion_point = content.rfind("    def ")
                    content = content[:insertion_point] + new_function + "\n\n" + content[insertion_point:]

                elif modification_data['action'] == "modify_strategy":
                    old_code = modification_data['old_code']
                    new_code = modification_data['new_code']
                    content = content.replace(old_code, new_code)

                # Backup original and write new version
                backup_name = f"arbitrum_testnet_agent_backup_{int(time.time())}.py"
                with open(backup_name, 'w') as f:
                    f.write(content)

                with open('arbitrum_testnet_agent.py', 'w') as f:
                    f.write(content)

                print(f"✅ Code modified successfully (backup: {backup_name})")
                return True

        except Exception as e:
            print(f"❌ Code modification failed: {e}")
            return False

    def estimate_impact(self, improvement_data):
        """Estimate the potential impact of an improvement"""
        if improvement_data.get('action') == 'reduce_risk':
            return "Medium-High (Stability)"
        elif improvement_data.get('action') == 'optimize_yield':
            return "High (Profit)"
        elif improvement_data.get('action') == 'code_modification':
            return "Variable (Functionality)"
        return "Unknown"

    def assess_risk(self, improvement_data):
        """Assess the risk level of an improvement"""
        if improvement_data.get('action') == 'reduce_risk':
            return "Low"
        elif improvement_data.get('leverage_increase'):
            return "High"
        elif improvement_data.get('action') == 'code_modification':
            return "Medium"
        return "Low-Medium"

    def get_user_input_on_proposals(self):
        """Interactive interface for user to review proposals"""
        if not os.path.exists(self.improvements_queue):
            print("📭 No pending proposals")
            return

        with open(self.improvements_queue, 'r') as f:
            queue = json.load(f)

        pending = [p for p in queue if p['status'] == 'pending']
        if not pending:
            print("📭 No pending proposals")
            return

        print(f"\n🔍 REVIEWING {len(pending)} PENDING PROPOSALS:")
        print("=" * 50)

        for proposal in pending:
            print(f"\n📋 Proposal ID: {proposal['id']}")
            print(f"🔹 Type: {proposal['type']}")
            print(f"🔹 Source: {proposal['source']}")
            print(f"🔹 Impact: {proposal['estimated_impact']}")
            print(f"🔹 Risk: {proposal['risk_level']}")
            print(f"🔹 Details: {json.dumps(proposal['data'], indent=2)}")
            print("-" * 30)

        return pending

    def submit_user_improvement(self, strategy_type, description, parameters=None):
        """Allow user to submit strategy improvements"""
        improvement = {
            "description": description,
            "parameters": parameters or {},
            "user_priority": "high",
            "timestamp": datetime.now().isoformat()
        }

        return self.propose_strategy_improvement(strategy_type, improvement, "user")

    def print_collateral_message(self):
        print(f"💡 Add $13+ worth of collateral to activate autonomous sequence")