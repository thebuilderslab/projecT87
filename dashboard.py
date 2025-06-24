
import time
import json
import os
from datetime import datetime

class AgentDashboard:
    def __init__(self, agent):
        self.agent = agent
        
    def display_wallet_status(self):
        """Display current wallet status with emojis"""
        try:
            # Get balances
            eth_balance = self.agent.get_eth_balance()
            
            if hasattr(self.agent, 'aave'):
                usdc_balance = self.agent.aave.get_token_balance(self.agent.aave.usdc_address)
                health_data = self.agent.health_monitor.get_current_health_factor()
            else:
                usdc_balance = 0
                health_data = None
            
            print("\n" + "="*60)
            print("🏦 **AAVE PROTOCOL WALLET DASHBOARD** 🏦")
            print("="*60)
            
            # Wallet Balances
            print(f"💰 **WALLET BALANCES**")
            print(f"   🔷 ETH Balance: {eth_balance:.6f} ETH")
            print(f"   💵 USDC Balance: {usdc_balance:.2f} USDC")
            
            if health_data:
                # Aave Protocol Status
                print(f"\n🏥 **AAVE PROTOCOL STATUS**")
                print(f"   ❤️ Health Factor: {health_data['health_factor']:.4f}")
                print(f"   🔒 Total Collateral: {health_data['total_collateral_eth']:.6f} ETH")
                print(f"   💸 Total Debt: {health_data['total_debt_eth']:.6f} ETH")
                print(f"   📈 Available Borrow: {health_data['available_borrows_eth']:.6f} ETH")
                
                # Borrow Power Used
                if health_data['total_collateral_eth'] > 0:
                    borrow_power_used = (health_data['total_debt_eth'] / health_data['total_collateral_eth']) * 100
                    print(f"   ⚡ Borrow Power Used: {borrow_power_used:.2f}%")
                
                # Risk Status
                hf = health_data['health_factor']
                if hf > 2.0:
                    risk_status = "🟢 SAFE"
                elif hf > 1.5:
                    risk_status = "🟡 MODERATE"
                elif hf > 1.2:
                    risk_status = "🟠 CAUTION"
                else:
                    risk_status = "🔴 HIGH RISK"
                print(f"   🛡️ Risk Level: {risk_status}")
            
            print("="*60)
            
        except Exception as e:
            print(f"❌ Dashboard error: {e}")
    
    def display_24h_performance(self):
        """Display 24h performance metrics"""
        try:
            print("\n📊 **24-HOUR PERFORMANCE METRICS**")
            print("-"*40)
            
            # Load recent performance data
            performance_data = []
            if os.path.exists('performance_log.json'):
                with open('performance_log.json', 'r') as f:
                    for line in f:
                        performance_data.append(json.loads(line))
            
            if len(performance_data) >= 2:
                recent_performance = performance_data[-50:]  # Last 50 entries
                avg_performance = sum(p['performance_metric'] for p in recent_performance) / len(recent_performance)
                
                # P/L Calculation (simplified)
                if len(recent_performance) > 1:
                    start_performance = recent_performance[0]['performance_metric']
                    end_performance = recent_performance[-1]['performance_metric']
                    pnl_pct = ((end_performance - start_performance) / start_performance) * 100
                else:
                    pnl_pct = 0
                
                # Speed metrics
                total_iterations = len(recent_performance)
                time_span = recent_performance[-1]['timestamp'] - recent_performance[0]['timestamp']
                speed = total_iterations / (time_span / 3600) if time_span > 0 else 0  # iterations per hour
                
                # Error detection (simplified)
                error_count = sum(1 for p in recent_performance if p['performance_metric'] < 0.5)
                error_rate = (error_count / len(recent_performance)) * 100
                
                print(f"💹 P/L (24h): {pnl_pct:+.2f}%")
                print(f"⚡ Processing Speed: {speed:.1f} ops/hour")
                print(f"🛡️ Error Detection Rate: {error_rate:.1f}%")
                print(f"📈 Avg Performance: {avg_performance:.3f}")
                
                # Performance trend
                if pnl_pct > 0:
                    trend = "📈 TRENDING UP"
                elif pnl_pct < -1:
                    trend = "📉 TRENDING DOWN"
                else:
                    trend = "➡️ STABLE"
                print(f"🎯 Trend: {trend}")
                
                # Vulnerability detection
                if error_rate < 5:
                    vuln_status = "🟢 LOW RISK"
                elif error_rate < 15:
                    vuln_status = "🟡 MEDIUM RISK"
                else:
                    vuln_status = "🔴 HIGH RISK"
                print(f"🔍 Vulnerability Status: {vuln_status}")
            else:
                print("📊 Insufficient data for 24h metrics")
                
        except Exception as e:
            print(f"❌ Performance display error: {e}")
    
    def run_live_dashboard(self):
        """Run live updating dashboard"""
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            self.display_wallet_status()
            self.display_24h_performance()
            
            print(f"\n🔄 Refreshing in 30 seconds... (Ctrl+C to stop)")
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n👋 Dashboard stopped.")
                break

if __name__ == "__main__":
    from arbitrum_testnet_agent import ArbitrumTestnetAgent
    
    try:
        agent = ArbitrumTestnetAgent()
        dashboard = AgentDashboard(agent)
        dashboard.run_live_dashboard()
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
