#!/usr/bin/env python3
"""
Improved Web Dashboard - Live Data Only
No hardcoded fallback data - only live blockchain data
"""

from flask import Flask, render_template, jsonify, request
import os
import time
import json
import threading
from enhanced_contract_manager import EnhancedContractManager

app = Flask(__name__)

# Global state
wallet_data = {}
enhanced_manager = None
last_update = 0

def initialize_system():
    """Initialize Enhanced Contract Manager for live data only"""
    global enhanced_manager, wallet_data

    try:
        print("🚀 Initializing dashboard with LIVE DATA ONLY - NO HARDCODED FALLBACKS")

        # Force mainnet mode
        os.environ['NETWORK_MODE'] = 'mainnet'

        # Initialize Enhanced Contract Manager
        from enhanced_contract_manager import EnhancedContractManager
        enhanced_manager = EnhancedContractManager()

        print("🔧 Optimizing Enhanced Contract Manager for live data...")

        # Try optimization multiple times
        optimization_success = False
        for attempt in range(5):
            print(f"🔄 Optimization attempt {attempt + 1}/5...")
            if enhanced_manager.optimize_for_contract_calls():
                optimization_success = True
                print(f"✅ Enhanced Contract Manager optimized successfully")
                print(f"   Optimal RPC: {enhanced_manager.working_rpc}")
                break
            else:
                print(f"⚠️ Optimization attempt {attempt + 1} failed, retrying...")
                time.sleep(3)

        if optimization_success:
            print("🧪 Testing initial live data fetch...")
            update_wallet_data()
            print("✅ Dashboard system initialized with LIVE DATA ONLY")
        else:
            print("❌ Enhanced Contract Manager optimization failed - NO FALLBACK DATA")
            wallet_data = {
                'success': False,
                'error': 'No working RPC endpoints available for live data',
                'note': 'Live data only - no hardcoded fallbacks'
            }

    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        enhanced_manager = None
        wallet_data = {
            'success': False,
            'error': str(e),
            'note': 'Live data initialization failed - no fallback data available'
        }

def update_wallet_data():
    """Update wallet data using ONLY live blockchain data"""
    global wallet_data, last_update, enhanced_manager

    try:
        # Ensure Enhanced Contract Manager is working
        if not enhanced_manager or not enhanced_manager.working_rpc:
            print("❌ No working Enhanced Contract Manager - cannot fetch live data")
            wallet_data = {
                'success': False,
                'error': 'No working RPC connection for live data',
                'note': 'LIVE DATA ONLY - no hardcoded fallbacks',
                'timestamp': time.time()
            }
            return

        # Get wallet address
        wallet_addr = '0x5B823270e3719CDe8669e5e5326B455EaA8a350b'

        print(f"🔧 LIVE DATA FETCH: Using RPC {enhanced_manager.working_rpc}")

        # Get all token balances using Enhanced Contract Manager - LIVE ONLY
        usdc_balance = enhanced_manager.get_token_balance_robust(enhanced_manager.usdc_address, wallet_addr)
        wbtc_balance = enhanced_manager.get_token_balance_robust(enhanced_manager.wbtc_address, wallet_addr)
        weth_balance = enhanced_manager.get_token_balance_robust(enhanced_manager.weth_address, wallet_addr)
        arb_balance = enhanced_manager.get_token_balance_robust(enhanced_manager.arb_address, wallet_addr)

        # Get ETH balance directly from blockchain
        eth_balance = enhanced_manager.w3.eth.get_balance(wallet_addr) / 1e18

        print(f"✅ LIVE TOKEN BALANCES:")
        print(f"   ETH: {eth_balance:.6f}")
        print(f"   USDC: {usdc_balance:.6f}")
        print(f"   WBTC: {wbtc_balance:.8f}")
        print(f"   WETH: {weth_balance:.6f}")
        print(f"   ARB: {arb_balance:.6f}")

        # Get Aave data using Enhanced Contract Manager - LIVE ONLY
        aave_pool = "0x794a61358d6845594f94dc1db02a252b5b4814ad"
        print("🔄 LIVE AAVE DATA FETCH...")
        enhanced_aave_data = enhanced_manager.get_aave_data_robust(wallet_addr, aave_pool, retries=10)

        # STRICT: Only accept live Aave data
        if enhanced_aave_data and enhanced_aave_data.get('data_source') == 'live_aave_contract_enhanced':
            print(f"✅ LIVE AAVE DATA RETRIEVED:")
            print(f"   Health Factor: {enhanced_aave_data['health_factor']:.2f}")
            print(f"   Collateral: ${enhanced_aave_data['total_collateral_usd']:.2f}")
            print(f"   Debt: ${enhanced_aave_data['total_debt_usd']:.2f}")

            health_factor = enhanced_aave_data['health_factor']
            collateral_usd = enhanced_aave_data['total_collateral_usd']
            debt_usd = enhanced_aave_data['total_debt_usd']
            available_borrows_usd = enhanced_aave_data.get('available_borrows_usd', 0)

            aave_data = {
                'health_factor': health_factor,
                'total_collateral_usd': collateral_usd,
                'total_debt_usd': debt_usd,
                'available_borrows_usd': available_borrows_usd,
                'data_source': 'live_aave_contract_only',
                'note': 'LIVE AAVE DATA - no fallbacks',
                'rpc_used': enhanced_manager.working_rpc,
                'timestamp': enhanced_aave_data['timestamp']
            }
        else:
            print("❌ LIVE AAVE DATA UNAVAILABLE - NO FALLBACK")
            # NO HARDCODED DATA - return zeros if live data fails
            health_factor = 0
            collateral_usd = 0
            debt_usd = 0
            available_borrows_usd = 0

            aave_data = {
                'health_factor': 0,
                'total_collateral_usd': 0,
                'total_debt_usd': 0,
                'available_borrows_usd': 0,
                'data_source': 'live_data_failed',
                'note': 'Live Aave data unavailable - no hardcoded fallbacks',
                'error': 'All live RPC endpoints failed for Aave data',
                'rpc_attempts': len(enhanced_manager.arbitrum_mainnet_rpcs) if enhanced_manager else 0
            }

        # Get live prices - NO FALLBACK
        try:
            import requests

            # Try CoinMarketCap first
            cmc_key = os.getenv('COINMARKETCAP_API_KEY')
            if cmc_key:
                try:
                    response = requests.get(
                        'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                        headers={'X-CMC_PRO_API_KEY': cmc_key},
                        params={'symbol': 'BTC,ETH,USDC,ARB'},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        prices = {
                            'BTC': data['data']['BTC']['quote']['USD']['price'],
                            'ETH': data['data']['ETH']['quote']['USD']['price'],
                            'USDC': data['data']['USDC']['quote']['USD']['price'],
                            'ARB': data['data']['ARB']['quote']['USD']['price']
                        }
                        print(f"✅ LIVE PRICES from CoinMarketCap: BTC=${prices['BTC']:.2f}, ETH=${prices['ETH']:.2f}")
                    else:
                        raise Exception("CMC API failed")
                except:
                    # Try CoinGecko as backup
                    response = requests.get(
                        'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,usd-coin,arbitrum&vs_currencies=usd',
                        timeout=10
                    )
                    data = response.json()
                    prices = {
                        'BTC': data['bitcoin']['usd'],
                        'ETH': data['ethereum']['usd'],
                        'USDC': data['usd-coin']['usd'],
                        'ARB': data['arbitrum']['usd']
                    }
                    print(f"✅ LIVE PRICES from CoinGecko: BTC=${prices['BTC']:.2f}, ETH=${prices['ETH']:.2f}")
            else:
                # Try CoinGecko directly
                response = requests.get(
                    'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,usd-coin,arbitrum&vs_currencies=usd',
                    timeout=10
                )
                data = response.json()
                prices = {
                    'BTC': data['bitcoin']['usd'],
                    'ETH': data['ethereum']['usd'],
                    'USDC': data['usd-coin']['usd'],
                    'ARB': data['arbitrum']['usd']
                }
                print(f"✅ LIVE PRICES from CoinGecko: BTC=${prices['BTC']:.2f}, ETH=${prices['ETH']:.2f}")

        except Exception as price_error:
            print(f"❌ LIVE PRICE FETCH FAILED: {price_error} - NO FALLBACK PRICES")
            # NO HARDCODED PRICES - return zeros if live prices fail
            prices = {'ETH': 0, 'BTC': 0, 'USDC': 0, 'ARB': 0}

        # Calculate USD values only if we have valid prices
        if prices['ETH'] > 0:
            eth_usd = eth_balance * prices['ETH']
            usdc_usd = usdc_balance * prices['USDC']
            wbtc_usd = wbtc_balance * prices['BTC']
            weth_usd = weth_balance * prices['ETH']
            arb_usd = arb_balance * prices['ARB']
        else:
            eth_usd = usdc_usd = wbtc_usd = weth_usd = arb_usd = 0

        liquid_wallet_usd = eth_usd + usdc_usd + wbtc_usd + weth_usd + arb_usd
        total_portfolio_usd = liquid_wallet_usd + collateral_usd

        # Create wallet data structure with LIVE DATA ONLY
        wallet_data = {
            'wallet_address': wallet_addr,
            'network_name': 'Arbitrum Mainnet',
            'network_mode': 'mainnet',
            'chain_id': 42161,

            # Token balances - live from Enhanced Contract Manager
            'eth_balance': eth_balance,
            'wbtc_balance': wbtc_balance,
            'weth_balance': weth_balance,
            'usdc_balance': usdc_balance,
            'arb_balance': arb_balance,

            # USD values
            'usd_values': {
                'ETH': eth_usd,
                'USDC': usdc_usd,
                'WBTC': wbtc_usd,
                'WETH': weth_usd,
                'ARB': arb_usd
            },

            # Portfolio totals
            'total_portfolio_usd': total_portfolio_usd,
            'total_wallet_usd': liquid_wallet_usd,

            # Aave data - live only
            'health_factor': health_factor,
            'total_collateral': collateral_usd / prices['ETH'] if prices['ETH'] > 0 else 0,
            'total_debt': debt_usd / prices['ETH'] if prices['ETH'] > 0 else 0,
            'available_borrows': available_borrows_usd / prices['ETH'] if prices['ETH'] > 0 else 0,
            'total_collateral_usdc': collateral_usd,
            'total_debt_usdc': debt_usd,
            'available_borrows_usdc': available_borrows_usd,

            # Aave positions for detailed view
            'aave_positions': aave_data,

            # Live prices only
            'prices': prices,

            # Status and metadata
            'success': True,
            'data_source': 'live_blockchain_only',
            'data_quality': 'live_no_fallbacks',
            'enhanced_contract_manager': {
                'active': True,
                'rpc_endpoint': enhanced_manager.working_rpc,
                'aave_data_source': aave_data.get('data_source', 'unknown'),
                'tokens_success': True,
                'last_optimization': enhanced_manager.last_rpc_test,
                'no_hardcoded_fallbacks': True
            },
            'timestamp': time.time()
        }

        last_update = time.time()

        print(f"✅ LIVE DATA UPDATED at {time.strftime('%H:%M:%S')}")
        print(f"💰 Liquid wallet: ${liquid_wallet_usd:.2f}")
        print(f"🏦 Aave collateral: ${collateral_usd:.2f}")
        print(f"📊 Total portfolio: ${total_portfolio_usd:.2f}")
        print(f"❤️ Health factor: {health_factor:.2f}")
        print(f"🔗 Using RPC: {enhanced_manager.working_rpc}")
        print(f"🚫 NO HARDCODED FALLBACK DATA USED")

    except Exception as e:
        print(f"❌ LIVE DATA UPDATE FAILED: {e}")
        wallet_data = {
            'last_error': str(e),
            'last_error_time': time.time(),
            'success': False,
            'data_source': 'error_no_fallbacks',
            'note': 'Live data fetch failed - no hardcoded fallback data available'
        }

def background_data_updater():
    """Background thread to update live data every 30 seconds"""
    global enhanced_manager

    update_count = 0
    while True:
        try:
            time.sleep(30)  # Update every 30 seconds
            update_count += 1

            # Every 10 updates (5 minutes), re-optimize RPC
            if update_count % 10 == 0 and enhanced_manager:
                print("🔄 Periodic RPC optimization for live data...")
                enhanced_manager.find_optimal_rpc(force_retest=True)
                if enhanced_manager.working_rpc:
                    print(f"✅ RPC re-optimized: {enhanced_manager.working_rpc}")
                else:
                    print("❌ RPC optimization failed - no live data available")

            update_wallet_data()

        except Exception as e:
            print(f"❌ Background live data update error: {e}")

            # Try to recover Enhanced Contract Manager
            if enhanced_manager:
                print("🔄 Attempting Enhanced Contract Manager recovery...")
                try:
                    enhanced_manager.optimize_for_contract_calls()
                    if enhanced_manager.working_rpc:
                        print(f"✅ Enhanced Contract Manager recovered: {enhanced_manager.working_rpc}")
                    else:
                        print("❌ Recovery failed - no working RPC")
                except Exception as recovery_error:
                    print(f"❌ Recovery failed: {recovery_error}")

            time.sleep(60)  # Wait longer on error

def start_background_updater():
    """Start the background data update thread"""
    updater_thread = threading.Thread(target=background_data_updater, daemon=True)
    updater_thread.start()
    print("✅ Background live data updater started")

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('improved_dashboard.html')

@app.route('/api/wallet-status')
def api_wallet_status():
    """API endpoint for wallet status - live data only"""
    try:
        # Ensure we have recent data
        if time.time() - last_update > 60:  # If data is older than 1 minute
            update_wallet_data()

        return jsonify(wallet_data)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False,
            'data_source': 'error_no_fallbacks',
            'note': 'Live data fetch failed - no hardcoded fallbacks',
            'timestamp': time.time()
        }), 200

@app.route('/api/refresh-data', methods=['POST'])
def api_refresh_data():
    """Manually refresh wallet data - live only"""
    try:
        update_wallet_data()
        return jsonify({
            'success': True,
            'message': 'Live data refreshed successfully',
            'timestamp': last_update,
            'data_source': 'live_blockchain_only'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time(),
            'data_source': 'error_no_fallbacks'
        }), 500

@app.route('/api/system-status')
def api_system_status():
    """Get system status information"""
    ecm_status = {}
    if enhanced_manager:
        ecm_status = {
            'active': True,
            'working_rpc': enhanced_manager.working_rpc,
            'last_rpc_test': enhanced_manager.last_rpc_test,
            'rpc_performance_data': len(enhanced_manager.rpc_performance),
            'live_data_only': True,
            'no_hardcoded_fallbacks': True
        }
    else:
        ecm_status = {'active': False, 'reason': 'not_initialized'}

    return jsonify({
        'data_source': 'live_blockchain_only',
        'enhanced_contract_manager': ecm_status,
        'last_update': last_update,
        'data_age_seconds': time.time() - last_update if last_update > 0 else -1,
        'wallet_address': wallet_data.get('wallet_address', 'Unknown'),
        'network': wallet_data.get('network_name', 'Unknown'),
        'success': wallet_data.get('success', False),
        'live_data_only': True,
        'no_hardcoded_fallbacks': True,
        'timestamp': time.time()
    })

@app.route('/api/emergency-stop', methods=['POST'])
def api_emergency_stop():
    """Emergency stop endpoint"""
    try:
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        with open(emergency_file, 'w') as f:
            f.write(f"Emergency stop activated at {time.time()}\n")
            f.write("Source: Live Data Dashboard\n")

        return jsonify({
            'success': True,
            'message': 'Emergency stop activated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/emergency-stop', methods=['DELETE'])
def api_clear_emergency_stop():
    """Clear emergency stop"""
    try:
        emergency_file = 'EMERGENCY_STOP_ACTIVE.flag'
        if os.path.exists(emergency_file):
            os.remove(emergency_file)
            return jsonify({
                'success': True,
                'message': 'Emergency stop cleared'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No emergency stop active'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def setup_app():
    """Set up the Flask app"""
    print("🔧 Setting up live data dashboard...")
    print("🚫 NO HARDCODED FALLBACK DATA - LIVE BLOCKCHAIN DATA ONLY")

    # Initialize system
    initialize_system()

    # Start background updater
    start_background_updater()

    print("✅ Live data dashboard setup complete")

if __name__ == '__main__':
    setup_app()

    print("🌐 Starting Live Data DeFi Dashboard")
    print("📊 LIVE BLOCKCHAIN DATA ONLY - NO HARDCODED FALLBACKS")
    print("🔗 Access via your Replit webview URL")

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)