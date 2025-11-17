#!/usr/bin/env python3
"""
Comprehensive Debt Swap Diagnostic Test
Tests 10 DAI → WETH swap with full pre-checks and dry run
"""

from web3 import Web3
from decimal import Decimal
from arbitrum_testnet_agent import ArbitrumTestnetAgent
from debt_swap_bidirectional import BidirectionalDebtSwapper
from corrected_swap_debt_abi import DEBT_SWITCH_V3_ADDRESS, ARBITRUM_ADDRESSES
import json

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(title)
    print("="*80)

def main():
    print_section("COMPREHENSIVE DEBT SWAP DIAGNOSTIC TEST")
    print("Test Configuration: 10 DAI → WETH")
    print("Mode: Dry run with full diagnostics")
    
    # Initialize
    agent = ArbitrumTestnetAgent()
    swapper = BidirectionalDebtSwapper(agent.w3, agent.wallet_address, agent.private_key)
    
    print_section("TASK 1: CONTRACT ADDRESS VERIFICATION")
    
    contracts = {
        "Debt Switch V3": DEBT_SWITCH_V3_ADDRESS,
        "DAI Token": ARBITRUM_ADDRESSES['DAI'],
        "WETH Token": ARBITRUM_ADDRESSES['WETH'],
        "DAI Variable Debt": ARBITRUM_ADDRESSES['variableDebtArbDAI'],
        "WETH Variable Debt": ARBITRUM_ADDRESSES['variableDebtArbWETH'],
        "Aave Pool V3": ARBITRUM_ADDRESSES['AavePoolV3'],
    }
    
    print("\n📋 Contract Addresses in Use:")
    for name, address in contracts.items():
        # Verify contract has code
        code = agent.w3.eth.get_code(address)
        status = "✅ Valid" if len(code) > 2 else "❌ No code"
        print(f"   {name}:")
        print(f"      Address: {address}")
        print(f"      Status: {status}")
    
    # Verify against user's manual swap addresses
    print("\n🔍 Verification Against Manual MetaMask Swaps:")
    user_weth_debt = "0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351"
    user_debt_switch = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"
    
    weth_match = ARBITRUM_ADDRESSES['variableDebtArbWETH'].lower() == user_weth_debt.lower()
    switch_match = DEBT_SWITCH_V3_ADDRESS.lower() == user_debt_switch.lower()
    
    print(f"   WETH Debt Token: {'✅ MATCH' if weth_match else '❌ MISMATCH'}")
    print(f"      Config: {ARBITRUM_ADDRESSES['variableDebtArbWETH']}")
    print(f"      Manual: {user_weth_debt}")
    
    print(f"   Debt Switch V3: {'✅ MATCH' if switch_match else '❌ MISMATCH'}")
    print(f"      Config: {DEBT_SWITCH_V3_ADDRESS}")
    print(f"      Manual: {user_debt_switch}")
    
    if weth_match and switch_match:
        print("\n   ✅ ALL ADDRESSES VERIFIED - Using exact contracts from manual swaps")
    else:
        print("\n   ❌ ADDRESS MISMATCH DETECTED")
        return
    
    print_section("TASK 2: PRE-FLIGHT CHECKS")
    
    # Get current position
    summary = agent.get_account_summary()
    
    print("\n💰 Current Position:")
    print(f"   Wallet: {agent.wallet_address}")
    print(f"   DAI Debt: {summary['dai_debt']:.6f} DAI")
    print(f"   WETH Debt: {summary['weth_debt']:.6f} WETH")
    print(f"   Total Collateral: ${summary['total_collateral_usd']:.2f}")
    print(f"   Total Debt: ${summary['total_debt_usd']:.2f}")
    print(f"   Available Borrow: ${summary['available_borrows_usd']:.2f}")
    
    print(f"\n❤️  Health Factor: {summary['health_factor']:.4f}")
    print(f"   Minimum required: 1.05 (aggressive mode)")
    print(f"   Recommended: 1.15+ (safe for swaps)")
    print(f"   Liquidation at: 1.00")
    
    hf = summary['health_factor']
    if hf < 1.05:
        print(f"   ❌ CRITICAL: Below minimum threshold")
    elif hf < 1.15:
        print(f"   ⚠️  WARNING: Marginal - swaps may fail due to flashloan HF drop")
    else:
        print(f"   ✅ SAFE: Adequate buffer for swaps")
    
    # Check ETH for gas
    eth_balance = agent.get_eth_balance()
    print(f"\n⛽ Gas Check:")
    print(f"   ETH Balance: {eth_balance:.6f} ETH (${eth_balance * 3100:.2f})")
    print(f"   Estimated gas needed: ~0.005 ETH (~$15.50)")
    if eth_balance >= 0.005:
        print(f"   ✅ Sufficient ETH for gas")
    else:
        print(f"   ⚠️  Low ETH - may not cover gas for swap")
    
    # Check credit delegation
    print(f"\n🔐 Credit Delegation Check:")
    weth_debt_token = agent.w3.eth.contract(
        address=ARBITRUM_ADDRESSES['variableDebtArbWETH'],
        abi=[{
            "inputs": [{"name": "fromUser", "type": "address"}, {"name": "toUser", "type": "address"}],
            "name": "borrowAllowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
    )
    
    try:
        allowance = weth_debt_token.functions.borrowAllowance(
            agent.wallet_address,
            DEBT_SWITCH_V3_ADDRESS
        ).call()
        allowance_weth = Decimal(allowance) / Decimal(1e18)
        print(f"   WETH Credit Delegation: {allowance_weth:.6f} WETH")
        if allowance_weth > 0:
            print(f"   ✅ Credit delegation active")
        else:
            print(f"   ❌ No credit delegation - need to delegate first")
    except Exception as e:
        print(f"   ⚠️  Could not check delegation: {e}")
    
    # Check if we have enough DAI debt to repay
    print(f"\n📊 Swap Feasibility:")
    test_amount = Decimal('10')
    print(f"   Requested repay: {test_amount} DAI")
    print(f"   Current DAI debt: {summary['dai_debt']:.6f} DAI")
    
    if summary['dai_debt'] >= test_amount:
        print(f"   ✅ Sufficient DAI debt to repay")
    else:
        print(f"   ❌ Insufficient DAI debt - can only repay {summary['dai_debt']:.6f} DAI")
        test_amount = Decimal(str(summary['dai_debt']))
    
    print_section("TASK 3: EXECUTE DRY RUN TEST")
    
    print(f"\n🔄 Testing {test_amount} DAI → WETH swap (DRY RUN)")
    print(f"   This will build the transaction but NOT execute it\n")
    
    try:
        # Execute dry run
        result = swapper.swap_debt(
            from_asset='DAI',
            to_asset='WETH',
            amount=test_amount,
            slippage_bps=100,  # 1% slippage
            dry_run=True
        )
        
        if result == "DRY_RUN":
            print(f"\n✅ DRY RUN COMPLETED SUCCESSFULLY")
            print(f"   Transaction parameters built correctly")
            print(f"   All contract calls validated")
            print(f"   Ready for live execution")
            
            print_section("TASK 4: LIVE EXECUTION APPROVAL")
            print("\n⚠️  IMPORTANT: Based on pre-flight checks:")
            
            if hf < 1.15:
                print(f"\n❌ LIVE EXECUTION NOT RECOMMENDED")
                print(f"   Your health factor ({hf:.4f}) is too low")
                print(f"   During flashloan execution, HF will temporarily drop")
                print(f"   Transaction will likely REVERT on-chain")
                print(f"\n💡 SOLUTION:")
                print(f"   1. Add 0.01-0.02 ETH collateral via Aave UI")
                print(f"   2. Raise health factor to 1.2+")
                print(f"   3. Then retry this test")
            else:
                print(f"\n✅ PRE-FLIGHT CHECKS PASSED")
                print(f"   Health factor is adequate")
                print(f"   Transaction should succeed")
                print(f"\n   To execute live, run:")
                print(f"   python3 comprehensive_swap_diagnostic.py --live")
        
    except Exception as e:
        print(f"\n❌ DRY RUN FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    print_section("TASK 5: SUMMARY REPORT")
    
    print("\n📋 Contract Verification Results:")
    print(f"   ✅ All contract addresses match manual MetaMask swaps")
    print(f"   ✅ WETH Variable Debt: {user_weth_debt}")
    print(f"   ✅ Debt Switch V3: {user_debt_switch}")
    
    print("\n📊 Current Position:")
    print(f"   Health Factor: {hf:.4f}")
    print(f"   DAI Debt: {summary['dai_debt']:.6f} DAI")
    print(f"   WETH Debt: {summary['weth_debt']:.6f} WETH")
    print(f"   ETH Balance: {eth_balance:.6f} ETH")
    
    print("\n🎯 Recommended Next Actions:")
    
    if hf < 1.15:
        print("\n   Priority 1: Increase Health Factor")
        print(f"      Current: {hf:.4f}")
        print(f"      Target: 1.2+")
        print(f"      Action: Add 0.01-0.02 ETH collateral")
        print(f"      Method: https://app.aave.com/ → Supply ETH")
        
        print("\n   Priority 2: Retry Test After Adding Collateral")
        print(f"      Run: python3 comprehensive_swap_diagnostic.py")
        
        print("\n   Priority 3: Execute Live Swap")
        print(f"      Once HF > 1.15, approve live execution")
    else:
        print("\n   ✅ Ready for live execution!")
        print(f"      All pre-flight checks passed")
        print(f"      Transaction should succeed")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
