#!/usr/bin/env python3
"""Test delegation approval flow"""

from automated_swap_executor import AutomatedSwapExecutor
from decimal import Decimal

# Initialize executor
executor = AutomatedSwapExecutor()

# Check delegation need
direction = 'DAI_TO_WETH'
needs_delegation = executor._needs_delegation(direction)
print(f"Direction {direction} needs delegation: {needs_delegation}")

# Check current delegation
current_delegation = executor.delegation_mgr.get_current_delegation()
print(f"Current delegation: {current_delegation:.6f} WETH")

# Estimate WETH needed for 5 DAI swap
amount = Decimal('5.0')
eth_price = executor.eth_price_usd
estimated_weth = amount / eth_price
print(f"Estimated WETH needed: {estimated_weth:.6f} @ ${eth_price:.2f}/ETH")
print(f"With 1.2x buffer: {estimated_weth * Decimal('1.2'):.6f} WETH")

# Check if delegation is sufficient
if current_delegation < estimated_weth * Decimal('1.2'):
    print(f"\n❌ Insufficient delegation - would approve {estimated_weth:.6f} WETH")
else:
    print(f"\n✅ Sufficient delegation already exists")

# Approve delegation test
print(f"\n🔐 Testing delegation approval...")
approval_tx = executor.delegation_mgr.approve_exact_delegation(estimated_weth)

if approval_tx:
    print(f"✅ Delegation approved: {approval_tx}")
    print(f"   Arbiscan: https://arbiscan.io/tx/{approval_tx}")
    
    # Check new delegation
    new_delegation = executor.delegation_mgr.get_current_delegation()
    print(f"New delegation: {new_delegation:.6f} WETH")
else:
    print(f"❌ Delegation approval failed")
