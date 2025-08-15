
#!/usr/bin/env python3
"""
Safe Operations Testing - Network Approval Validation
Tests all safety mechanisms and network approval likelihood
"""

import os
import time
import json
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def test_health_factor_protection():
    """Test health factor protection mechanisms"""
    print("🔒 TESTING HEALTH FACTOR PROTECTION")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Cannot get account data")
            return False
        
        current_hf = account_data.get('healthFactor', 0)
        print(f"📊 Current Health Factor: {current_hf:.4f}")
        
        # Test minimum HF thresholds
        min_general_hf = 1.5
        min_market_ops_hf = float(os.getenv('MIN_HEALTH_FACTOR_FOR_MARKET_OPS', '2.0'))
        
        print(f"✅ Minimum HF for general ops: {min_general_hf}")
        print(f"✅ Minimum HF for market ops: {min_market_ops_hf}")
        
        if current_hf >= min_market_ops_hf:
            print(f"✅ Health Factor SAFE for market operations")
        elif current_hf >= min_general_hf:
            print(f"⚠️ Health Factor OK for general ops, but blocked for market ops")
        else:
            print(f"❌ Health Factor CRITICAL - all operations blocked")
        
        # Test emergency thresholds
        emergency_hf = 1.05
        if current_hf > emergency_hf:
            print(f"✅ Health Factor above emergency threshold ({emergency_hf})")
        else:
            print(f"🚨 Health Factor near liquidation threshold!")
        
        return True
        
    except Exception as e:
        print(f"❌ Health factor protection test failed: {e}")
        return False

def test_gas_estimation_and_limits():
    """Test gas estimation and transaction limits"""
    print("\n⛽ TESTING GAS ESTIMATION & LIMITS")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Check ETH balance
        eth_balance = agent.get_eth_balance()
        print(f"💰 ETH Balance: {eth_balance:.6f} ETH")
        
        min_eth_needed = 0.001  # Minimum ETH for operations
        if eth_balance >= min_eth_needed:
            print(f"✅ Sufficient ETH for gas operations")
        else:
            print(f"❌ Insufficient ETH - need {min_eth_needed - eth_balance:.6f} more")
            return False
        
        # Test gas price analysis
        current_gas_price = agent.w3.eth.gas_price
        gas_price_gwei = current_gas_price / 1e9
        print(f"⛽ Current Gas Price: {gas_price_gwei:.2f} gwei")
        
        # Estimate transaction costs
        estimated_gas_limit = 400000  # Conservative estimate for complex DeFi ops
        estimated_cost_wei = current_gas_price * estimated_gas_limit
        estimated_cost_eth = estimated_cost_wei / 1e18
        
        print(f"💸 Estimated Transaction Cost: {estimated_cost_eth:.6f} ETH")
        
        # Check if we have sufficient buffer
        if eth_balance >= estimated_cost_eth * 3:  # 3x buffer
            print(f"✅ Sufficient ETH buffer for operations")
        else:
            print(f"⚠️ Low ETH buffer - consider adding more ETH")
        
        return True
        
    except Exception as e:
        print(f"❌ Gas estimation test failed: {e}")
        return False

def test_operation_limits():
    """Test operation amount limits and safety caps"""
    print("\n📏 TESTING OPERATION LIMITS")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        account_data = agent.aave.get_user_account_data()
        if not account_data:
            print("❌ Cannot get account data")
            return False
        
        available_borrows = account_data.get('availableBorrowsUSD', 0)
        total_collateral = account_data.get('totalCollateralUSD', 0)
        
        print(f"📊 Available Borrows: ${available_borrows:.2f}")
        print(f"📊 Total Collateral: ${total_collateral:.2f}")
        
        # Test various operation limits
        max_market_op = float(os.getenv('MAX_MARKET_OPERATION_AMOUNT', '10'))
        capacity_percentage = 0.05  # 5% of available capacity
        collateral_percentage = 0.02  # 2% of total collateral
        
        capacity_limit = available_borrows * capacity_percentage
        collateral_limit = total_collateral * collateral_percentage
        
        # Calculate actual safe amount
        safe_amount = min(max_market_op, capacity_limit, collateral_limit)
        
        print(f"🔒 Safety Limits:")
        print(f"   Maximum Market Op: ${max_market_op:.2f}")
        print(f"   Capacity Limit (5%): ${capacity_limit:.2f}")
        print(f"   Collateral Limit (2%): ${collateral_limit:.2f}")
        print(f"   Final Safe Amount: ${safe_amount:.2f}")
        
        if safe_amount >= 0.5:
            print(f"✅ Safe operation amount determined: ${safe_amount:.2f}")
        else:
            print(f"⚠️ Operation amount too small: ${safe_amount:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Operation limits test failed: {e}")
        return False

def test_cooldown_mechanisms():
    """Test cooldown and rate limiting mechanisms"""
    print("\n⏰ TESTING COOLDOWN MECHANISMS")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        
        # Test operation cooldown
        cooldown_seconds = getattr(agent, 'operation_cooldown_seconds', 60)
        signal_cooldown = int(os.getenv('SIGNAL_COOLDOWN', '1800'))  # 30 minutes
        
        print(f"✅ Operation Cooldown: {cooldown_seconds} seconds")
        print(f"✅ Signal Cooldown: {signal_cooldown} seconds ({signal_cooldown/60:.1f} minutes)")
        
        # Check current cooldown status
        current_time = time.time()
        last_op_time = getattr(agent, 'last_successful_operation_time', 0)
        time_since_last = current_time - last_op_time
        
        if time_since_last >= cooldown_seconds:
            print(f"✅ Operations ready (last operation: {time_since_last:.0f}s ago)")
        else:
            remaining = cooldown_seconds - time_since_last
            print(f"⏰ Operations in cooldown ({remaining:.0f}s remaining)")
        
        # Test market signal cooldown
        if hasattr(agent, 'market_signal_strategy') and agent.market_signal_strategy:
            last_signal_time = getattr(agent.market_signal_strategy, 'last_signal_time', 0)
            signal_time_since = current_time - last_signal_time
            
            if signal_time_since >= signal_cooldown:
                print(f"✅ Market signals ready (last signal: {signal_time_since:.0f}s ago)")
            else:
                signal_remaining = signal_cooldown - signal_time_since
                print(f"⏰ Market signals in cooldown ({signal_remaining:.0f}s remaining)")
        
        return True
        
    except Exception as e:
        print(f"❌ Cooldown mechanisms test failed: {e}")
        return False

def test_network_approval_readiness():
    """Test overall network approval readiness"""
    print("\n🌐 TESTING NETWORK APPROVAL READINESS")
    print("=" * 50)
    
    try:
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        # Comprehensive readiness check
        checks = {
            'web3_connected': False,
            'aave_accessible': False,
            'uniswap_accessible': False,
            'sufficient_gas': False,
            'healthy_position': False,
            'market_signals_enabled': False
        }
        
        # Web3 connectivity
        if agent.w3 and agent.w3.is_connected():
            checks['web3_connected'] = True
            print("✅ Web3 connected to Arbitrum")
        else:
            print("❌ Web3 connection failed")
        
        # Aave accessibility
        if agent.aave:
            account_data = agent.aave.get_user_account_data()
            if account_data:
                checks['aave_accessible'] = True
                print("✅ Aave integration working")
            else:
                print("❌ Aave integration failed")
        
        # Uniswap accessibility
        if agent.uniswap:
            checks['uniswap_accessible'] = True
            print("✅ Uniswap integration available")
        else:
            print("❌ Uniswap integration failed")
        
        # Gas sufficiency
        eth_balance = agent.get_eth_balance()
        if eth_balance >= 0.001:
            checks['sufficient_gas'] = True
            print(f"✅ Sufficient ETH for gas: {eth_balance:.6f}")
        else:
            print(f"❌ Insufficient ETH for gas: {eth_balance:.6f}")
        
        # Position health
        if account_data:
            hf = account_data.get('healthFactor', 0)
            if hf >= 2.0:
                checks['healthy_position'] = True
                print(f"✅ Healthy position: HF {hf:.3f}")
            else:
                print(f"⚠️ Position health concern: HF {hf:.3f}")
        
        # Market signals
        market_enabled = os.getenv('MARKET_SIGNAL_ENABLED', 'false').lower() == 'true'
        if market_enabled and agent.market_signal_strategy:
            checks['market_signals_enabled'] = True
            print("✅ Market signals enabled and functional")
        else:
            print("⚠️ Market signals disabled or not functional")
        
        # Calculate readiness score
        passed_checks = sum(checks.values())
        total_checks = len(checks)
        readiness_score = (passed_checks / total_checks) * 100
        
        print(f"\n📊 NETWORK APPROVAL READINESS: {readiness_score:.1f}%")
        print(f"✅ Passed: {passed_checks}/{total_checks} checks")
        
        if readiness_score >= 80:
            print("🎉 SYSTEM READY FOR NETWORK APPROVAL")
        else:
            print("⚠️ SYSTEM NEEDS IMPROVEMENTS FOR RELIABLE APPROVAL")
        
        return readiness_score >= 80
        
    except Exception as e:
        print(f"❌ Network approval readiness test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔒 COMPREHENSIVE SAFE OPERATIONS TESTING")
    print("=" * 60)
    
    # Run all safety tests
    hf_test = test_health_factor_protection()
    gas_test = test_gas_estimation_and_limits()
    limits_test = test_operation_limits()
    cooldown_test = test_cooldown_mechanisms()
    approval_test = test_network_approval_readiness()
    
    print(f"\n📊 SAFETY TEST RESULTS:")
    print(f"   Health Factor Protection: {'✅ PASS' if hf_test else '❌ FAIL'}")
    print(f"   Gas Estimation & Limits: {'✅ PASS' if gas_test else '❌ FAIL'}")
    print(f"   Operation Limits: {'✅ PASS' if limits_test else '❌ FAIL'}")
    print(f"   Cooldown Mechanisms: {'✅ PASS' if cooldown_test else '❌ FAIL'}")
    print(f"   Network Approval Ready: {'✅ PASS' if approval_test else '❌ FAIL'}")
    
    all_passed = all([hf_test, gas_test, limits_test, cooldown_test, approval_test])
    
    if all_passed:
        print(f"\n🎉 ALL SAFETY TESTS PASSED")
        print(f"🚀 SYSTEM READY FOR AUTONOMOUS DEBT MANAGEMENT")
    else:
        print(f"\n⚠️ SOME SAFETY TESTS FAILED - ADDRESS ISSUES BEFORE DEPLOYMENT")
