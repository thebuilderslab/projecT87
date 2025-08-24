
#!/usr/bin/env python3
"""
Real-Time Trend Monitor
Displays minute-by-minute and 1-hour trend analysis in real-time
"""

import time
import os
import json
from datetime import datetime
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def display_trend_dashboard():
    """Display real-time trend analysis dashboard"""
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        if not hasattr(agent, 'market_signal_strategy') or not agent.market_signal_strategy:
            print("❌ Market signal strategy not available")
            return
        
        strategy = agent.market_signal_strategy
        
        # Clear screen and show header
        os.system('clear' if os.name == 'posix' else 'cls')
        print("🚀 REAL-TIME TREND ANALYSIS DASHBOARD")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
        
        # Check if advanced trend analyzer is available
        if hasattr(strategy, 'trend_analyzer') and strategy.trend_analyzer:
            print("📊 MINUTE-BY-MINUTE ANALYSIS: ✅ ENABLED")
            
            # Collect and display real-time data
            trend_point = strategy.trend_analyzer.collect_real_time_data()
            if trend_point:
                print(f"💰 CURRENT PRICES:")
                print(f"   BTC: ${trend_point.btc_price:,.2f}")
                print(f"   ARB: ${trend_point.arb_price:.4f}")
                print()
                
                print(f"📈 MULTI-TIMEFRAME CHANGES:")
                print(f"   BTC: 1m: {trend_point.btc_change_1m:+.3f}% | 5m: {trend_point.btc_change_5m:+.3f}% | 1h: {trend_point.btc_change_1h:+.2f}%")
                print(f"   ARB: 1m: {trend_point.arb_change_1m:+.3f}% | 5m: {trend_point.arb_change_5m:+.3f}% | 1h: {trend_point.arb_change_1h:+.2f}%")
                print()
            
            # Display trend analysis
            trend_analysis = strategy.trend_analyzer.analyze_minute_trends()
            if trend_analysis:
                print(f"🎯 TREND ANALYSIS:")
                
                # Direction with emoji
                direction_emoji = {
                    'bullish': '📈',
                    'bearish': '📉',
                    'sideways': '➡️'
                }
                
                print(f"   Direction: {direction_emoji.get(trend_analysis.trend_direction, '❓')} {trend_analysis.trend_direction.upper()}")
                print(f"   Strength: {trend_analysis.strength:.2f} {'🔥' if trend_analysis.strength > 0.7 else '⚡' if trend_analysis.strength > 0.4 else '💤'}")
                print(f"   Confidence: {trend_analysis.confidence:.2f} {'✅' if trend_analysis.confidence > 0.8 else '⚠️' if trend_analysis.confidence > 0.6 else '❌'}")
                print()
                
                print(f"⚡ MOMENTUM ANALYSIS:")
                print(f"   1-Minute:  {trend_analysis.momentum_1m:+.4f}%")
                print(f"   5-Minute:  {trend_analysis.momentum_5m:+.4f}%")
                print(f"   15-Minute: {trend_analysis.momentum_15m:+.4f}%")
                print(f"   1-Hour:    {trend_analysis.momentum_1h:+.4f}%")
                print()
                
                print(f"🔮 1-HOUR PREDICTION:")
                prediction = trend_analysis.prediction_1h
                pred_emoji = {
                    'bullish': '📈',
                    'bearish': '📉',
                    'sideways': '➡️'
                }
                
                print(f"   Direction: {pred_emoji.get(prediction['direction'], '❓')} {prediction['direction'].upper()}")
                print(f"   Magnitude: {prediction['magnitude']:.3f}% ({prediction['magnitude']*100:.1f} basis points)")
                print(f"   Confidence: {prediction['confidence']:.2f} {'🎯' if prediction['confidence'] > 0.8 else '🤔'}")
                print()
                
                # Display volatility
                vol_emoji = '🌪️' if trend_analysis.volatility_score > 0.05 else '🌊' if trend_analysis.volatility_score > 0.02 else '🏞️'
                print(f"📊 VOLATILITY: {vol_emoji} {trend_analysis.volatility_score:.3f}")
                
                # Display active signals
                if trend_analysis.signals:
                    print(f"🚨 ACTIVE SIGNALS:")
                    for signal in trend_analysis.signals:
                        signal_emoji = {
                            'DAI_TO_ARB_OPPORTUNITY': '💰',
                            'ARB_TO_DAI_OPPORTUNITY': '💎',
                            'STRONG_BEARISH_TREND': '📉',
                            'STRONG_BULLISH_TREND': '📈',
                            'HIGH_VOLATILITY_DETECTED': '⚡',
                            'BEARISH_MOMENTUM_BUILDING': '⬇️',
                            'BULLISH_MOMENTUM_BUILDING': '⬆️'
                        }
                        
                        emoji = signal_emoji.get(signal, '🔔')
                        print(f"   {emoji} {signal.replace('_', ' ').title()}")
                    print()
                
                # Check for trade opportunities
                should_trade, trade_type, trade_info = strategy.trend_analyzer.should_trigger_trade_based_on_trends()
                
                if should_trade:
                    print(f"🎯 TRADE OPPORTUNITY DETECTED!")
                    print(f"   Type: {trade_type.upper()}")
                    print(f"   Confidence: {trade_info.get('confidence', 0):.2f}")
                    print(f"   Strength: {trade_info.get('strength', 0):.2f}")
                    print(f"   🚀 Ready for execution!")
                else:
                    print(f"⏳ No trade opportunities detected")
                    print(f"   Reason: {trade_info.get('reason', 'Conditions not met')}")
                
                print()
        else:
            print("📊 MINUTE-BY-MINUTE ANALYSIS: ❌ NOT AVAILABLE")
            print("   Using basic market signal analysis")
            print()
        
        # Display system status
        status = strategy.get_strategy_status()
        print(f"🔧 SYSTEM STATUS:")
        print(f"   Strategy Enabled: {'✅' if status['enabled'] else '❌'}")
        print(f"   Cooldown Remaining: ⏰ {status['cooldown_remaining']:.0f}s")
        print(f"   BTC Drop Threshold: 📉 {status['btc_threshold']*100:.2f}%")
        print(f"   Signal History: 📝 {status['signal_history_count']} signals")
        
        if 'trend_analysis' in status:
            trend_data = status['trend_analysis']
            print(f"   Data Points: 📊 {trend_data.get('data_points', 0)}")
            print(f"   Analysis Count: 🔍 {trend_data.get('analysis_count', 0)}")
        
        print("\n💡 Press Ctrl+C to exit, or run again for updated data")
        
    except KeyboardInterrupt:
        print("\n👋 Trend monitoring stopped")
    except Exception as e:
        print(f"❌ Error in trend monitoring: {e}")

if __name__ == "__main__":
    display_trend_dashboard()
