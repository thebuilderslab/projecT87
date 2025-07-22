Remove USDC references and ensure DAI-only operations
Replacing
<old_str>
print(f"💡 RECOMMENDATION: Consider borrowing {health_summary['optimal_usdc_borrow']:.2f} USDC")
</old_str>
with
<new_str>
print(f"💡 RECOMMENDATION: Consider borrowing {health_summary.get('optimal_dai_borrow', 0):.2f} DAI")
</new_str>
Remove USDC references and ensure DAI-only operations
Replacing
<old_str>
print(f"💡 RECOMMENDATION: Consider borrowing {health_summary['optimal_usdc_borrow']:.2f} USDC")
</old_str>
with
<new_str>
print(f"💡 RECOMMENDATION: Consider borrowing {health_summary.get('optimal_dai_borrow', 0):.2f} DAI")
</new_str>
Update strategy description to use DAI
Replacing
<old_str>
2. **Dynamic Borrowing**: When health factor increases by 0.02+, borrow USDC to maintain 1.19 health factor
</old_str>
with
<new_str>
2. **Dynamic Borrowing**: When health factor increases by 0.02+, borrow DAI to maintain 1.19 health factor
</new_str>
Remove USDC references and ensure DAI-only operations
Replacing
<old_str>
print(f"💡 RECOMMENDATION: Consider borrowing {health_summary['optimal_usdc_borrow']:.2f} USDC")
</old_str>
with
<new_str>
print(f"💡 RECOMMENDATION: Consider borrowing {health_summary.get('optimal_dai_borrow', 0):.2f} DAI")
</new_str>
Update strategy description to use DAI
Replacing
<old_str>
2. **Dynamic Borrowing**: When health factor increases by 0.02+, borrow USDC to maintain 1.19 health factor
</old_str>
with
<new_str>
2. **Dynamic Borrowing**: When health factor increases by 0.02+, borrow DAI to maintain 1.19 health factor
</new_str>
Update risk management strategy to use DAI
Replacing
<old_str>
3. **Risk Management**: If health factor declines AND ARB price drops, recommend swapping ARB to USDC
</old_str>
with
<new_str>
3. **Risk Management**: If health factor declines AND ARB price drops, recommend swapping ARB to DAI
</new_str>