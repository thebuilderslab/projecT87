# REAA Wallet Delegation Audit

## Approval Matrix (Triple Approval Model)

Users must grant TWO distinct approvals at wallet connection time via the frontend, plus the BOT handles a third programmatically:

| Approval Target | Type | Purpose | Granted By |
|---|---|---|---|
| DelegationManager contract | Aave credit delegation (`approveDelegation`) | Allows DM to call `supply`, `borrow`, `repay`, `withdraw` on Aave on behalf of user | Frontend at wallet connect |
| BOT wallet address | ERC20 `approve(BOT, MAX)` for DAI, WETH, WBTC, USDT | Allows BOT to `transferFrom(user, bot, amount)` during distribution steps | Frontend at wallet connect |
| DEX Router (Uniswap) | ERC20 `approve(router, amount)` from BOT wallet | Allows DEX router to pull tokens from BOT for swaps | Bot code via `ensure_bot_dex_approval()` |

### Why Three Approvals?

- **DM approval**: Aave V3 credit delegation requires the borrower (user) to approve the DM contract as a delegate. This lets the DM execute `borrow(asset, amount, rateMode, 0, user)` which assigns debt to user but sends tokens to DM.
- **BOT ERC20 approval**: After borrow, tokens land in user wallet (via DM atomic transfer). Distribution steps need to pull tokens from user wallet to BOT wallet for swaps. This requires standard ERC20 `transferFrom` which needs user's approval of BOT address.
- **BOT→DEX approval**: Before each swap, BOT must approve the DEX Router to pull the swap input token. Handled programmatically via `ensure_bot_dex_approval(token, amount)` before every swap call.

## Token Flow Per Strategy

### Growth / Capacity (DAI Borrow)

```
Step 1: BORROW (atomic)
  DM.executeBorrowAndTransfer(user, DAI, amount, 2) -> DAI lands in USER wallet atomically

Step 2: DAI SUPPLY
  BOT.transferFrom(user, bot, daiSupplyAmt) -> DAI in BOT
  DM.executeSupply(user, DAI, amt) -> DAI supplied to Aave onBehalfOf user

Step 3: WBTC SWAP+SUPPLY (with DEX approval + rollback)
  BOT.transferFrom(user, bot, daiForWbtc) -> DAI in BOT
  ensure_bot_dex_approval(DAI, amount)
  try: UniswapRouter.swap(DAI -> WBTC) -> WBTC in BOT
  on success: DM.executeSupply(user, WBTC, amt) -> WBTC supplied to Aave onBehalfOf user
  on failure: _forward_tokens_to_user(DAI, amount, user) -> DAI returned to USER

Step 4: WETH SWAP+SUPPLY (with DEX approval + rollback)
  BOT.transferFrom(user, bot, daiForWeth) -> DAI in BOT
  ensure_bot_dex_approval(DAI, amount)
  try: UniswapRouter.swap(DAI -> WETH) -> WETH in BOT
  on success: DM.executeSupply(user, WETH, amt) -> WETH supplied to Aave onBehalfOf user
  on failure: _forward_tokens_to_user(DAI, amount, user) -> DAI returned to USER

Step 5: GAS RESERVE
  DAI stays in USER wallet (no action needed)

Step 6: WALLET_S TRANSFER
  BOT.transferFrom(user, bot, daiForWalletS) -> DAI in BOT
  BOT.transfer(DAI, Wallet_S) -> DAI in Wallet_S

Step 7: USDC TAX (with DEX approval + rollback)
  BOT.transferFrom(user, bot, daiForUsdc) -> DAI in BOT
  ensure_bot_dex_approval(DAI, amount)
  try: UniswapRouter.swap(DAI -> USDC) -> USDC in BOT
  on success: BOT.transfer(USDC, user) -> USDC in USER wallet
  on failure: _forward_tokens_to_user(DAI, amount, user) -> DAI returned to USER
```

### Liability Short Entry (WETH Borrow)

```
Step 1: BORROW WETH (atomic)
  DM.executeBorrowAndTransfer(user, WETH, amount, 2) -> WETH lands in USER wallet atomically

Step 2: WBTC portion (with DEX approval + rollback)
  BOT.transferFrom(user, bot, wethForWbtc) -> WETH in BOT
  ensure_bot_dex_approval(WETH, amount)
  try: UniswapRouter.swap(WETH -> WBTC) -> WBTC in BOT
  on success: DM.executeSupply(user, WBTC, amt) -> WBTC supplied to Aave
  on failure: _forward_tokens_to_user(WETH, amount, user) -> WETH returned to USER

Step 3: USDT portion (with DEX approval + rollback)
  BOT.transferFrom(user, bot, wethForUsdt) -> WETH in BOT
  ensure_bot_dex_approval(WETH, amount)
  try: UniswapRouter.swap(WETH -> USDT) -> USDT in BOT
  on success: DM.executeSupply(user, USDT, amt) -> USDT supplied to Aave
  on failure: _forward_tokens_to_user(WETH, amount, user) -> WETH returned to USER

Step 4: WETH hold portion
  BOT.transferFrom(user, bot, wethHold) -> WETH in BOT
  DM.executeSupply(user, WETH, amt) -> WETH supplied to Aave
```

### Liability Short Close

```
Step 1: WITHDRAW USDT from Aave (atomic via DM contract)
  DM.executeWithdraw(user, USDT, amt) -> USDT transferred to USER atomically by DM

Step 2: PULL + SWAP (with DEX approval + rollback)
  BOT.transferFrom(user, bot, usdtAmt) -> USDT in BOT
  ensure_bot_dex_approval(USDT, amount)
  try: UniswapRouter.swap(USDT -> WETH) -> WETH in BOT
  on failure: _forward_tokens_to_user(USDT, amount, user) -> USDT returned to USER

Step 3: REPAY WETH debt
  BOT.approve(AavePool, wethAmt)
  DM.executeRepay(user, WETH, amt) -> debt reduced

Step 4: PROFIT DISTRIBUTION (from BOT wallet, profit WETH already there)
  Each swap gets ensure_bot_dex_approval(WETH, amount) before swap.
  No rollback to user needed (WETH is profit in BOT, not pulled from user).
  20% -> swap WETH->DAI -> transfer to Wallet_S
  20% -> swap WETH->USDC -> transfer to USER
  30% -> swap WETH->WBTC -> supply to Aave onBehalfOf user
  20% -> supply WETH to Aave onBehalfOf user
  10% -> swap WETH->USDT -> supply to Aave onBehalfOf user
  Residual WETH sweep -> transfer to USER
```

### Nurse Sweep

```
Reads USER wallet balances for DAI/WETH/WBTC/USDT.
Skips below $2 floor. NEVER touches USDC (profit token).

For each token above threshold:
  DM.executeSupply(user, token, amt)
  (DM calls transferFrom(user, DM, amt) internally — DM already has user approval)
  -> Token supplied to Aave onBehalfOf user
```

## Personal Bot vs Delegation Comparison

| Aspect | Personal Bot | Delegated User |
|---|---|---|
| Borrow recipient | Bot wallet (direct) | User wallet (via DM) |
| Swap source | Bot wallet | Pull from user → bot wallet → swap |
| Supply method | Direct Aave supply | DM.executeSupply onBehalfOf user |
| Debt owner | Bot wallet | User wallet |
| Collateral owner | Bot wallet | User wallet |
| ERC20 approval needed | None (bot owns tokens) | User → BOT for pulls, User → DM for Aave ops |
| Profit destination | Bot wallet | User wallet (USDC) |

## Fragile Joints & Risk Areas

1. **Missing BOT ERC20 Allowance**: If user hasn't approved BOT for DAI/WETH/WBTC/USDT, all `pull_token_from_user` calls will fail silently. Frontend MUST set these at wallet connect time.

2. **Insufficient Allowance Amount**: If user approved exactly N DAI but multiple strategies run, later strategies may exhaust the allowance. Frontend should approve `MAX_UINT256` or implement allowance refresh.

3. **Swap Slippage**: Uniswap swaps in BOT wallet may fail due to slippage. **Mitigated**: Each swap is wrapped in try/except with rollback — on failure, pulled tokens are returned to user wallet via `_forward_tokens_to_user`. No tokens stuck in BOT.

4. **Race Conditions**: If two strategies run simultaneously for the same user, both may try to pull the same tokens. Execution state files (`_load_execution_state`) provide crash recovery but not concurrency control.

5. **Contract Redeployment Required**: REAADelegationManager.sol must be redeployed with `executeBorrowAndTransfer` function. Current deployed contract at 0x7427370Ab4C311B090446544078c819b3946E59d may not have this function yet.

6. **DEX Approval Gas**: `ensure_bot_dex_approval` is called before each swap. If allowance is already sufficient, it skips the approval tx. Worst case adds ~1 extra tx per swap step.
