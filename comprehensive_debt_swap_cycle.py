#!/usr/bin/env python3
"""
Comprehensive Debt Swap Cycle Executor
Complete implementation: DAI debt → ARB debt → wait 5 minutes → ARB debt → DAI debt
Includes detailed PNL tracking with numerical and percentage analysis
"""

import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, getcontext
from corrected_debt_swap_executor import CorrectedDebtSwapExecutor

# Set high precision for PNL calculations
getcontext().prec = 50

class DebtPosition:
    """Track debt position with detailed metrics"""
    def __init__(self, timestamp: str, dai_debt: float, arb_debt: float, 
                 dai_price: float, arb_price: float):
        self.timestamp = timestamp
        self.dai_debt = float(dai_debt)
        self.arb_debt = float(arb_debt)
        self.dai_price = float(dai_price)
        self.arb_price = float(arb_price)
        self.total_debt_usd = (self.dai_debt * self.dai_price) + (self.arb_debt * self.arb_price)

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'dai_debt': self.dai_debt,
            'arb_debt': self.arb_debt,
            'dai_price': self.dai_price,
            'arb_price': self.arb_price,
            'total_debt_usd': self.total_debt_usd
        }

class PNLTracker:
    """Comprehensive PNL tracking system for debt swap cycles"""
    
    def __init__(self, agent):
        self.agent = agent
        self.positions: List[DebtPosition] = []
        self.swap_events = []
        
        # Aave Protocol Data Provider for debt tracking
        self.aave_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        self.token_addresses = {
            'DAI': "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            'ARB': "0x912CE59144191C1204E64559FE8253a0e49E6548"
        }
        
        print(f"📊 PNL Tracker initialized")
        print(f"   Tracking DAI and ARB debt positions")
        print(f"   High precision calculations enabled")

    def get_current_prices(self) -> Dict[str, float]:
        """Get current token prices from CoinMarketCap"""
        try:
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            if not api_key:
                print("⚠️ Using fallback prices - CoinMarketCap API key not found")
                return {'DAI': 1.00, 'ARB': 0.80}  # Fallback prices
            
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            params = {
                'symbol': 'DAI,ARB',
                'convert': 'USD'
            }
            headers = {
                'X-CMC_PRO_API_KEY': api_key,
                'Accept': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                prices = {
                    'DAI': float(data['data']['DAI']['quote']['USD']['price']),
                    'ARB': float(data['data']['ARB']['quote']['USD']['price'])
                }
                print(f"💰 Current Prices: DAI ${prices['DAI']:.4f}, ARB ${prices['ARB']:.4f}")
                return prices
            else:
                print(f"⚠️ Price API error {response.status_code}, using fallback prices")
                return {'DAI': 1.00, 'ARB': 0.80}
                
        except Exception as e:
            print(f"⚠️ Error fetching prices: {e}, using fallback prices")
            return {'DAI': 1.00, 'ARB': 0.80}

    def get_debt_balances(self) -> Dict[str, float]:
        """Get current debt balances from Aave"""
        try:
            # Protocol Data Provider ABI for getting debt tokens
            data_provider_abi = [{
                "inputs": [{"name": "asset", "type": "address"}],
                "name": "getReserveTokensAddresses",
                "outputs": [
                    {"name": "aTokenAddress", "type": "address"},
                    {"name": "stableDebtTokenAddress", "type": "address"},
                    {"name": "variableDebtTokenAddress", "type": "address"}
                ],
                "stateMutability": "view",
                "type": "function"
            }]
            
            # ERC20 ABI for balance checking
            erc20_abi = [{
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }]
            
            data_provider_contract = self.agent.w3.eth.contract(
                address=self.aave_data_provider,
                abi=data_provider_abi
            )
            
            debt_balances = {}
            
            for symbol, token_address in self.token_addresses.items():
                # Get debt token addresses
                token_addresses = data_provider_contract.functions.getReserveTokensAddresses(token_address).call()
                variable_debt_token = token_addresses[2]
                
                # Get debt balance
                debt_token_contract = self.agent.w3.eth.contract(
                    address=variable_debt_token,
                    abi=erc20_abi
                )
                
                balance_wei = debt_token_contract.functions.balanceOf(self.agent.address).call()
                balance = float(balance_wei) / 1e18  # Convert from wei
                
                debt_balances[symbol] = balance
                print(f"📋 {symbol} debt: {balance:.6f}")
            
            return debt_balances
            
        except Exception as e:
            print(f"❌ Error getting debt balances: {e}")
            return {'DAI': 0.0, 'ARB': 0.0}

    def capture_position(self, event_name: str) -> DebtPosition:
        """Capture current debt position"""
        try:
            print(f"\n📸 CAPTURING POSITION: {event_name}")
            print("=" * 50)
            
            # Get current prices and debt balances
            prices = self.get_current_prices()
            debt_balances = self.get_debt_balances()
            
            # Create position snapshot
            position = DebtPosition(
                timestamp=datetime.now().isoformat(),
                dai_debt=debt_balances['DAI'],
                arb_debt=debt_balances['ARB'],
                dai_price=prices['DAI'],
                arb_price=prices['ARB']
            )
            
            # Store position
            self.positions.append(position)
            
            print(f"📊 POSITION CAPTURED:")
            print(f"   DAI Debt: {position.dai_debt:.6f} DAI")
            print(f"   ARB Debt: {position.arb_debt:.6f} ARB")
            print(f"   Total USD: ${position.total_debt_usd:.2f}")
            print("=" * 50)
            
            return position
            
        except Exception as e:
            print(f"❌ Error capturing position: {e}")
            return None

    def calculate_pnl_between_positions(self, pos1: DebtPosition, pos2: DebtPosition) -> Dict:
        """Calculate detailed PNL between two positions"""
        try:
            # DAI debt changes
            dai_debt_change = pos2.dai_debt - pos1.dai_debt
            dai_usd_change = dai_debt_change * pos2.dai_price
            
            # ARB debt changes
            arb_debt_change = pos2.arb_debt - pos1.arb_debt
            arb_usd_change = arb_debt_change * pos2.arb_price
            
            # Total debt changes
            total_debt_change_usd = pos2.total_debt_usd - pos1.total_debt_usd
            
            # Percentage changes
            dai_percentage = ((pos2.dai_debt / pos1.dai_debt) - 1) * 100 if pos1.dai_debt > 0 else 0
            arb_percentage = ((pos2.arb_debt / pos1.arb_debt) - 1) * 100 if pos1.arb_debt > 0 else 0
            total_percentage = ((pos2.total_debt_usd / pos1.total_debt_usd) - 1) * 100 if pos1.total_debt_usd > 0 else 0
            
            return {
                'dai_debt_change': dai_debt_change,
                'dai_usd_change': dai_usd_change,
                'dai_percentage': dai_percentage,
                'arb_debt_change': arb_debt_change,
                'arb_usd_change': arb_usd_change,
                'arb_percentage': arb_percentage,
                'total_debt_change_usd': total_debt_change_usd,
                'total_percentage': total_percentage,
                'timespan_minutes': self._calculate_time_diff_minutes(pos1.timestamp, pos2.timestamp)
            }
            
        except Exception as e:
            print(f"❌ Error calculating PNL: {e}")
            return {}

    def _calculate_time_diff_minutes(self, timestamp1: str, timestamp2: str) -> float:
        """Calculate time difference in minutes"""
        try:
            dt1 = datetime.fromisoformat(timestamp1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(timestamp2.replace('Z', '+00:00'))
            diff = dt2 - dt1
            return diff.total_seconds() / 60
        except:
            return 0.0

    def print_pnl_analysis(self, pnl: Dict, title: str):
        """Print detailed PNL analysis"""
        print(f"\n💹 {title}")
        print("=" * 60)
        print(f"📊 DEBT CHANGES:")
        print(f"   DAI: {pnl['dai_debt_change']:+.6f} DAI (${pnl['dai_usd_change']:+.2f}) [{pnl['dai_percentage']:+.2f}%]")
        print(f"   ARB: {pnl['arb_debt_change']:+.6f} ARB (${pnl['arb_usd_change']:+.2f}) [{pnl['arb_percentage']:+.2f}%]")
        print(f"💰 TOTAL USD CHANGE: ${pnl['total_debt_change_usd']:+.2f} [{pnl['total_percentage']:+.2f}%]")
        print(f"⏱️  TIMESPAN: {pnl['timespan_minutes']:.1f} minutes")
        print("=" * 60)

    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive PNL report for entire cycle"""
        try:
            if len(self.positions) < 2:
                return {'error': 'Insufficient position data for analysis'}
            
            report = {
                'cycle_summary': {
                    'start_time': self.positions[0].timestamp,
                    'end_time': self.positions[-1].timestamp,
                    'total_positions_captured': len(self.positions),
                    'total_cycle_time_minutes': self._calculate_time_diff_minutes(
                        self.positions[0].timestamp, 
                        self.positions[-1].timestamp
                    )
                },
                'position_snapshots': [pos.to_dict() for pos in self.positions],
                'pnl_analysis': {},
                'swap_events': self.swap_events
            }
            
            # Calculate PNL for each phase
            if len(self.positions) >= 2:
                # Overall cycle PNL
                overall_pnl = self.calculate_pnl_between_positions(self.positions[0], self.positions[-1])
                report['pnl_analysis']['overall_cycle'] = overall_pnl
                
                # Individual phase PNLs
                for i in range(len(self.positions) - 1):
                    phase_name = f"phase_{i+1}"
                    phase_pnl = self.calculate_pnl_between_positions(self.positions[i], self.positions[i+1])
                    report['pnl_analysis'][phase_name] = phase_pnl
            
            return report
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return {'error': str(e)}

class ComprehensiveDebtSwapCycle:
    """Complete debt swap cycle executor with PNL tracking"""
    
    def __init__(self, agent):
        self.agent = agent
        self.executor = CorrectedDebtSwapExecutor(agent)
        self.pnl_tracker = PNLTracker(agent)
        
        print(f"🚀 Comprehensive Debt Swap Cycle initialized")
        print(f"   Agent: {agent.address}")
        print(f"   Cycle: DAI debt → ARB debt → wait 5 min → ARB debt → DAI debt")

    def validate_initial_position(self) -> bool:
        """Validate user has suitable position for debt swap cycle"""
        try:
            print(f"\n🔍 VALIDATING INITIAL POSITION")
            print("=" * 50)
            
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
            
            print(f"📊 CURRENT AAVE POSITION:")
            print(f"   Total Collateral: ${total_collateral_usd:.2f}")
            print(f"   Total Debt: ${total_debt_usd:.2f}")
            print(f"   Health Factor: {health_factor:.6f}")
            
            # Get specific debt balances
            debt_balances = self.pnl_tracker.get_debt_balances()
            
            # Validation criteria (adjusted for realistic requirements)
            checks = {
                'sufficient_collateral': total_collateral_usd >= 100,  # At least $100 collateral
                'has_debt': total_debt_usd >= 20,  # At least $20 total debt
                'safe_health_factor': health_factor >= 1.5,  # Reasonable health factor for debt swaps
                'has_dai_debt': debt_balances['DAI'] >= 10,  # At least 10 DAI debt for swapping
                'cycle_safety': total_debt_usd <= total_collateral_usd * 0.7  # Reasonable LTV for swaps
            }
            
            all_checks_pass = all(checks.values())
            
            print(f"\n✅ VALIDATION RESULTS:")
            for check, passed in checks.items():
                print(f"   {check.replace('_', ' ').title()}: {'✅' if passed else '❌'}")
            
            if not all_checks_pass:
                print(f"\n❌ Position not suitable for debt swap cycle")
                print(f"   Recommendation: Ensure sufficient collateral and DAI debt")
                return False
            
            print(f"\n✅ POSITION VALIDATED - Ready for debt swap cycle")
            return True
            
        except Exception as e:
            print(f"❌ Error validating position: {e}")
            return False

    def execute_complete_debt_swap_cycle(self, private_key: str, 
                                       swap_amount_usd: float = 10.0,
                                       wait_minutes: int = 5) -> Dict:
        """Execute complete debt swap cycle with comprehensive tracking"""
        
        cycle_result = {
            'cycle_name': 'comprehensive_debt_swap_cycle',
            'start_time': datetime.now().isoformat(),
            'swap_amount_usd': swap_amount_usd,
            'wait_minutes': wait_minutes,
            'phases': {},
            'overall_success': False,
            'pnl_report': {}
        }
        
        try:
            print(f"\n🚀 COMPREHENSIVE DEBT SWAP CYCLE")
            print("=" * 80)
            print(f"Cycle: DAI debt → ARB debt → wait {wait_minutes} min → ARB debt → DAI debt")
            print(f"Amount: ${swap_amount_usd:.2f} per swap")
            print(f"Real execution: ENABLED")
            print("=" * 80)
            
            # Validate initial position
            if not self.validate_initial_position():
                raise Exception("Initial position validation failed")
            
            # PHASE 0: Capture initial position
            print(f"\n📸 PHASE 0: INITIAL POSITION CAPTURE")
            initial_position = self.pnl_tracker.capture_position("cycle_start")
            
            if not initial_position:
                raise Exception("Failed to capture initial position")
            
            # PHASE 1: DAI debt → ARB debt
            print(f"\n🚀 PHASE 1: DAI DEBT → ARB DEBT (${swap_amount_usd:.2f})")
            print("-" * 50)
            
            phase1_result = self.executor.execute_real_debt_swap(
                private_key, 'DAI', 'ARB', swap_amount_usd
            )
            
            cycle_result['phases']['phase_1_dai_to_arb'] = phase1_result
            
            if not phase1_result.get('success'):
                raise Exception(f"Phase 1 failed: {phase1_result.get('error', 'Unknown error')}")
            
            # Capture position after phase 1
            post_phase1_position = self.pnl_tracker.capture_position("after_dai_to_arb_swap")
            
            # Calculate and display Phase 1 PNL
            if post_phase1_position:
                phase1_pnl = self.pnl_tracker.calculate_pnl_between_positions(
                    initial_position, post_phase1_position
                )
                self.pnl_tracker.print_pnl_analysis(phase1_pnl, "PHASE 1 PNL ANALYSIS")
            
            print(f"\n✅ PHASE 1 COMPLETED")
            print(f"   Transaction: {phase1_result.get('tx_hash', 'N/A')}")
            print(f"   Block: {phase1_result.get('block_number', 'N/A')}")
            
            # WAIT PERIOD
            print(f"\n⏳ WAIT PERIOD: {wait_minutes} MINUTES")
            print("-" * 50)
            print(f"   Allowing debt positions to settle...")
            print(f"   Monitoring price movements during wait...")
            
            wait_start = datetime.now()
            for minute in range(wait_minutes):
                remaining = wait_minutes - minute
                print(f"   ⏱️  {remaining} minutes remaining...")
                
                # Capture price movements every minute
                if minute % 2 == 0:  # Every 2 minutes
                    prices = self.pnl_tracker.get_current_prices()
                    print(f"      Prices: DAI ${prices['DAI']:.4f}, ARB ${prices['ARB']:.4f}")
                
                time.sleep(60)  # Wait 1 minute
            
            wait_end = datetime.now()
            actual_wait_time = (wait_end - wait_start).total_seconds() / 60
            
            print(f"✅ WAIT PERIOD COMPLETED")
            print(f"   Actual wait time: {actual_wait_time:.1f} minutes")
            
            # Capture position after wait
            post_wait_position = self.pnl_tracker.capture_position("after_wait_period")
            
            # Calculate wait period PNL (price impact)
            if post_wait_position and post_phase1_position:
                wait_pnl = self.pnl_tracker.calculate_pnl_between_positions(
                    post_phase1_position, post_wait_position
                )
                self.pnl_tracker.print_pnl_analysis(wait_pnl, "WAIT PERIOD PNL (Price Impact)")
            
            # PHASE 2: ARB debt → DAI debt
            print(f"\n🚀 PHASE 2: ARB DEBT → DAI DEBT (${swap_amount_usd:.2f})")
            print("-" * 50)
            
            phase2_result = self.executor.execute_real_debt_swap(
                private_key, 'ARB', 'DAI', swap_amount_usd
            )
            
            cycle_result['phases']['phase_2_arb_to_dai'] = phase2_result
            
            if not phase2_result.get('success'):
                raise Exception(f"Phase 2 failed: {phase2_result.get('error', 'Unknown error')}")
            
            # Capture final position
            final_position = self.pnl_tracker.capture_position("cycle_end")
            
            # Calculate Phase 2 PNL
            if final_position and post_wait_position:
                phase2_pnl = self.pnl_tracker.calculate_pnl_between_positions(
                    post_wait_position, final_position
                )
                self.pnl_tracker.print_pnl_analysis(phase2_pnl, "PHASE 2 PNL ANALYSIS")
            
            print(f"\n✅ PHASE 2 COMPLETED")
            print(f"   Transaction: {phase2_result.get('tx_hash', 'N/A')}")
            print(f"   Block: {phase2_result.get('block_number', 'N/A')}")
            
            # OVERALL CYCLE ANALYSIS
            if final_position and initial_position:
                overall_pnl = self.pnl_tracker.calculate_pnl_between_positions(
                    initial_position, final_position
                )
                self.pnl_tracker.print_pnl_analysis(overall_pnl, "OVERALL CYCLE PNL ANALYSIS")
            
            # Generate comprehensive report
            cycle_result['pnl_report'] = self.pnl_tracker.generate_comprehensive_report()
            cycle_result['overall_success'] = True
            
            # SUCCESS SUMMARY
            print(f"\n🎉 DEBT SWAP CYCLE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"✅ Phase 1: DAI → ARB debt swap executed")
            print(f"✅ Wait Period: {actual_wait_time:.1f} minutes completed")
            print(f"✅ Phase 2: ARB → DAI debt swap executed")
            print(f"✅ Complete cycle with comprehensive PNL tracking")
            
            # Transaction links
            print(f"\n🔗 TRANSACTION LINKS:")
            if phase1_result.get('tx_hash'):
                print(f"   Phase 1: https://arbiscan.io/tx/{phase1_result['tx_hash']}")
            if phase2_result.get('tx_hash'):
                print(f"   Phase 2: https://arbiscan.io/tx/{phase2_result['tx_hash']}")
            
            return cycle_result
            
        except Exception as e:
            print(f"\n❌ DEBT SWAP CYCLE FAILED: {e}")
            cycle_result['error'] = str(e)
            
            # Still generate partial report
            cycle_result['pnl_report'] = self.pnl_tracker.generate_comprehensive_report()
            
            return cycle_result
        
        finally:
            cycle_result['end_time'] = datetime.now().isoformat()
            
            # Save comprehensive results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_debt_swap_cycle_{timestamp}.json"
            
            try:
                with open(filename, 'w') as f:
                    json.dump(cycle_result, f, indent=2, default=str)
                print(f"\n📁 Complete results saved to: {filename}")
            except Exception as save_error:
                print(f"⚠️ Error saving results: {save_error}")

def main():
    """Execute comprehensive debt swap cycle"""
    print("🚀 COMPREHENSIVE DEBT SWAP CYCLE EXECUTOR")
    print("=" * 80)
    print("Implementation: DAI debt → ARB debt → wait 5 min → ARB debt → DAI debt")
    print("Features: Real execution + comprehensive PNL tracking")
    print("=" * 80)
    
    try:
        # Initialize agent
        from arbitrum_testnet_agent import ArbitrumTestnetAgent
        
        print("🤖 Initializing agent...")
        agent = ArbitrumTestnetAgent()
        
        if not agent or not hasattr(agent, 'w3'):
            raise Exception("Agent initialization failed")
        
        print(f"✅ Agent initialized: {agent.address}")
        
        # Get private key
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise Exception("PRIVATE_KEY environment variable required")
        
        # Execute comprehensive cycle
        cycle_executor = ComprehensiveDebtSwapCycle(agent)
        cycle_result = cycle_executor.execute_complete_debt_swap_cycle(
            private_key=private_key,
            swap_amount_usd=10.0,  # $10 per swap
            wait_minutes=5  # 5 minute wait period
        )
        
        # Final summary
        if cycle_result.get('overall_success'):
            print(f"\n🎉 COMPREHENSIVE DEBT SWAP CYCLE: SUCCESS!")
            print(f"✅ Complete DAI↔ARB debt swap cycle executed with real transactions")
            print(f"✅ Comprehensive PNL tracking and analysis completed")
            print(f"✅ All requirements fulfilled with detailed logging")
        else:
            print(f"\n❌ COMPREHENSIVE DEBT SWAP CYCLE: FAILED")
            print(f"Error: {cycle_result.get('error', 'Unknown error')}")
        
        return cycle_result
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    main()