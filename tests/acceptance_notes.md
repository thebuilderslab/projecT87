# REAA Delegation Acceptance Test Plan

## Pre-Test Setup

### Contract State
- Deployed DelegationManager at: `0x7427370Ab4C311B090446544078c819b3946E59d`
- `USE_ATOMIC_BORROW = False` (3-step workaround active)
- User delegation must be active (`isActive=True`) with `allowBorrow=True`, `allowSupply=True`

### Required Approvals (checked by `check_user_wallet_approvals`)
1. **DM Contract Approval**: User has approved DM for Aave credit delegation (variableDebtToken.approveDelegation)
2. **BOT ERC20 Allowance**: User has approved BOT wallet address for:
   - DAI: `approve(BOT, MAX_UINT256)`
   - WETH: `approve(BOT, MAX_UINT256)`
   - WBTC: `approve(BOT, MAX_UINT256)`
   - USDT: `approve(BOT, MAX_UINT256)`

### Environment
- `WALLET_S_ADDRESS` set in env
- `COIN_API` secret available
- Bot wallet funded with ETH for gas

---

## Test 1: Growth Distribution (7-Step)

### Trigger
User HF > Growth threshold, sufficient collateral for DAI borrow.

### Expected Flow
| Step | Action | Token Location Before | Token Location After |
|---|---|---|---|
| 1 | Borrow DAI | N/A | USER wallet |
| 2 | Pull DAI -> Supply DAI to Aave | USER wallet | Aave (user's position) |
| 3 | Pull DAI -> Swap DAI->WBTC -> Supply | USER wallet | Aave (user's position) |
| 4 | Pull DAI -> Swap DAI->WETH -> Supply | USER wallet | Aave (user's position) |
| 5 | Gas reserve (no action) | USER wallet | USER wallet |
| 6 | Pull DAI -> Transfer to Wallet_S | USER wallet | Wallet_S |
| 7 | Pull DAI -> Swap DAI->USDC -> Transfer | USER wallet | USER wallet (USDC) |

### Verification Points
- [ ] `delegated_borrow` logs show "Step 3/3 OK — transferred BOT→USER"
- [ ] Steps 2-4 log "Pull $X DAI from user -> ..."
- [ ] Step 5 logs "stays in user wallet for gas reserve"
- [ ] Step 6 logs "Pull $X DAI from user -> transfer to Wallet_S"
- [ ] Step 7 logs "Pull $X DAI from user -> swap DAI->USDC -> transfer USDC to user"
- [ ] No "tokens stuck in BOT wallet" errors
- [ ] User's Aave position shows increased DAI/WBTC/WETH supply
- [ ] User wallet has USDC (profit token)
- [ ] Wallet_S received DAI

---

## Test 2: Nurse Sweep

### Trigger
Stray tokens (DAI, WETH, WBTC, USDT) in user wallet above $2 threshold.

### Expected Flow
- Nurse reads user wallet balances
- For each token > $2: calls `dm_execute_supply(user, token, amount)`
- DM contract calls `transferFrom(user, DM, amount)` then `supply(token, amount, user, 0)`
- USDC is NEVER swept (profit token)

### Verification Points
- [ ] Nurse logs "sweeping X.XX TOKEN ($Y.YY)"
- [ ] Nurse logs "supplied to Aave via DM executeSupply"
- [ ] USDC line shows "PROFIT TOKEN, never swept"
- [ ] User's Aave supply positions increase by swept amounts

---

## Test 3: Liability Short Entry

### Trigger
ETH price drops below short threshold.

### Expected Flow
| Step | Action | Token Location |
|---|---|---|
| 1 | Borrow WETH via delegation | USER wallet |
| 2 | Pull WETH -> Swap WETH->WBTC -> Supply | Aave (user's position) |
| 3 | Pull WETH -> Swap WETH->USDT -> Supply | Aave (user's position) |
| 4 | Pull WETH -> Supply WETH to Aave | Aave (user's position) |

### Verification Points
- [ ] `delegated_borrow_weth` succeeds with tokens in USER wallet
- [ ] `pull_token_from_user` calls succeed for WETH
- [ ] User's Aave position shows WBTC, USDT, WETH supply increase
- [ ] User's Aave position shows WETH variable debt increase

---

## Test 4: Liability Short Close

### Expected Flow
1. Withdraw USDT from Aave -> USER wallet
2. Pull USDT from user -> swap USDT->WETH in BOT
3. Repay WETH debt via DM
4. Distribute profit WETH (already in BOT wallet)

### Verification Points
- [ ] USDT withdrawal lands in user wallet
- [ ] `pull_token_from_user` for USDT succeeds
- [ ] WETH debt reduced after repay
- [ ] Profit distributed: USDC to user, WBTC/WETH/USDT to Aave, DAI to Wallet_S

---

## Success Criteria

1. **Zero tokens stuck in BOT wallet** after any distribution (except during active swap)
2. **Zero tokens stuck in DM contract** after any borrow
3. **All borrowed tokens end in USER wallet** before distribution begins
4. **User's Aave positions** (supply/debt) match expected values
5. **USDC profit token** ends in user wallet, never swept by Nurse
6. **Wallet_S** receives its DAI allocation
7. **No "pull from user failed" errors** (indicates missing BOT ERC20 allowance)

---

## Failure Recovery

- If pull fails: tokens stay safely in user wallet. Nurse sweep will pick them up next cycle.
- If swap fails: tokens stay in BOT wallet. Manual recovery via `_forward_tokens_to_user` needed.
- If DM supply fails: tokens stay in BOT wallet after pull. Retry or manual forward.
- If borrow Step 2/3 fails (3-step mode): tokens stuck in DM. Use `emergencyWithdrawToken` to recover.
