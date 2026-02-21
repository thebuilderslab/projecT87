# REAA Wallet Delegation Audit

## Approval Matrix (Dual Approval Model)

Users must grant TWO distinct approvals at wallet connection time via the frontend:

| Approval Target | Type | Purpose | Granted By |
|---|---|---|---|
| DelegationManager contract | Aave credit delegation (`approveDelegation`) | Allows DM to call `supply`, `borrow`, `repay`, `withdraw` on Aave on behalf of user | Frontend at wallet connect |
| BOT wallet address | ERC20 `approve(BOT, MAX)` for DAI, WETH, WBTC, USDT | Allows BOT to `transferFrom(user, bot, amount)` during distribution steps | Frontend at wallet connect |

### Why Two Approvals?

- **DM approval**: Aave V3 credit delegation requires the borrower (user) to approve the DM contract as a delegate. This lets the DM execute `borrow(asset, amount, rateMode, 0, user)` which assigns debt to user but sends tokens to DM.
- **BOT ERC20 approval**: After borrow, tokens land in user wallet (via DM transfer). Distribution steps need to pull tokens from user wallet to BOT wallet for swaps. This requires standard ERC20 `transferFrom` which needs user's approval of BOT address.

## Token Flow Per Strategy

### Growth / Capacity (DAI Borrow)

```
Step 1: BORROW
  Aave.borrow(DAI, amount, 2, 0, user) -> DAI lands in DM contract
  DM.transfer(DAI, user) -> DAI lands in USER wallet
  (3-step: DM->BOT->USER, atomic: DM->USER)

Step 2: DAI SUPPLY
  BOT.transferFrom(user, bot, daiSupplyAmt) -> DAI in BOT
  DM.executeSupply(user, DAI, amt) -> DAI supplied to Aave onBehalfOf user

Step 3: WBTC SWAP+SUPPLY
  BOT.transferFrom(user, bot, daiForWbtc) -> DAI in BOT
  UniswapRouter.swap(DAI -> WBTC) -> WBTC in BOT
  DM.executeSupply(user, WBTC, amt) -> WBTC supplied to Aave onBehalfOf user

Step 4: WETH SWAP+SUPPLY
  BOT.transferFrom(user, bot, daiForWeth) -> DAI in BOT
  UniswapRouter.swap(DAI -> WETH) -> WETH in BOT
  DM.executeSupply(user, WETH, amt) -> WETH supplied to Aave onBehalfOf user

Step 5: GAS RESERVE
  DAI stays in USER wallet (no action needed)

Step 6: WALLET_S TRANSFER
  BOT.transferFrom(user, bot, daiForWalletS) -> DAI in BOT
  BOT.transfer(DAI, Wallet_S) -> DAI in Wallet_S

Step 7: USDC TAX
  BOT.transferFrom(user, bot, daiForUsdc) -> DAI in BOT
  UniswapRouter.swap(DAI -> USDC) -> USDC in BOT
  BOT.transfer(USDC, user) -> USDC in USER wallet
```

### Liability Short Entry (WETH Borrow)

```
Step 1: BORROW WETH
  Aave.borrow(WETH, amount, 2, 0, user) -> WETH in DM -> USER wallet

Step 2: WBTC portion
  BOT.transferFrom(user, bot, wethForWbtc) -> WETH in BOT
  UniswapRouter.swap(WETH -> WBTC) -> WBTC in BOT
  DM.executeSupply(user, WBTC, amt) -> WBTC supplied to Aave

Step 3: USDT portion
  BOT.transferFrom(user, bot, wethForUsdt) -> WETH in BOT
  UniswapRouter.swap(WETH -> USDT) -> USDT in BOT
  DM.executeSupply(user, USDT, amt) -> USDT supplied to Aave

Step 4: WETH hold portion
  BOT.transferFrom(user, bot, wethHold) -> WETH in BOT
  DM.executeSupply(user, WETH, amt) -> WETH supplied to Aave
```

### Liability Short Close

```
Step 1: WITHDRAW USDT from Aave
  DM.executeWithdraw(user, USDT, amt) -> USDT in USER wallet

Step 2: PULL + SWAP
  BOT.transferFrom(user, bot, usdtAmt) -> USDT in BOT
  UniswapRouter.swap(USDT -> WETH) -> WETH in BOT

Step 3: REPAY WETH debt
  BOT.approve(AavePool, wethAmt)
  DM.executeRepay(user, WETH, amt) -> debt reduced

Step 4: PROFIT DISTRIBUTION (from BOT wallet, profit WETH already there)
  20% -> swap WETH->DAI -> transfer to Wallet_S
  20% -> swap WETH->USDC -> transfer to USER
  30% -> swap WETH->WBTC -> supply to Aave onBehalfOf user
  20% -> supply WETH to Aave onBehalfOf user
  10% -> swap WETH->USDT -> supply to Aave onBehalfOf user
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

2. **3-Step Borrow Workaround**: Current deployed contract requires DM→BOT→USER transfer chain. If `_rescue_tokens_from_dm` or `_forward_tokens_to_user` fails, tokens get stuck in DM or BOT. Switch to `USE_ATOMIC_BORROW=True` after contract redeployment.

3. **Insufficient Allowance Amount**: If user approved exactly N DAI but multiple strategies run, later strategies may exhaust the allowance. Frontend should approve `MAX_UINT256` or implement allowance refresh.

4. **Swap Slippage**: Uniswap swaps in BOT wallet may fail due to slippage. Tokens remain in BOT wallet — Nurse sweep won't find them there (Nurse reads USER wallet only). Manual recovery needed.

5. **Race Conditions**: If two strategies run simultaneously for the same user, both may try to pull the same tokens. Execution state files (`_load_execution_state`) provide crash recovery but not concurrency control.

6. **Contract Redeployment**: After redeploying with `executeBorrowAndTransfer`, set `USE_ATOMIC_BORROW=True` in `delegation_client.py`. Old `executeBorrow` still works as fallback.

## Feature Flags

| Flag | Location | Current | Description |
|---|---|---|---|
| `USE_ATOMIC_BORROW` | `delegation_client.py` | `False` | When True, uses `executeBorrowAndTransfer` for single-tx borrow+transfer. Set True after contract redeployment. |
