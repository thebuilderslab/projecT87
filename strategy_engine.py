"""
Per-Wallet Delegated Strategy Engine — Full Automation Only
============================================================
Runs macro/micro/growth/capacity strategies on each delegated user wallet.
All on-chain actions are routed through the REAADelegationManager contract,
not the bot's own wallet.

There is ONE mode only: full automation. A wallet is either:
  - fully delegated (isActive=true, all flags per FULL_AUTOMATION profile), or
  - disabled / revoked / error_permissions (strategies must not run).
No "monitoring only" — misconfigurations become explicit errors.

HF Band Priority Order (checked top to bottom, first match wins):
-----------------------------------------------------------------
0. RESUME (any HF): If an incomplete distribution is detected (execution state
   file exists OR user wallet has DAI from a prior borrow), the swap pipeline
   resumes immediately. This runs BEFORE Nurse and BEFORE HF threshold checks.
1. EMERGENCY (HF < 2.20): Position at risk. Log critical warning, SKIP.
2. GROWTH (HF >= 2.60, collateral grew >= $50 or >= 10%, available borrows >= $13.20):
   Full 6-step distribution: borrow DAI, supply DAI, swap+supply WBTC, swap+supply WETH,
   swap DAI->ETH for gas, transfer DAI to Wallet_S, swap DAI->USDC (stays in user wallet).
3. CAPACITY (HF >= 2.40, available borrows >= $8.20):
   Same 6-step engine with smaller amounts.
4. MACRO SHORT (collateral velocity drop >= $50 in 30 min, HF >= 3.05):
   Hedge via WETH borrow against market downturn.
5. MICRO SHORT (collateral velocity drop >= $30 in 20 min, HF >= 3.00):
   Smaller hedge. 4h cooldown.
6. IDLE / SKIP: No conditions met. Log reason and wait for next cycle.

USER WALLET vs PERSONAL BOT — Two Intentional Differences:
  1. Profit Bucket: DISABLED for user wallets. USDC stays in user wallet, never flushed.
  2. Liability Short close: 20/20/30/20/10 split — 20% Wallet_S (DAI), 20% USDC (wallet), 30% WBTC (Aave), 20% WETH (Aave), 10% USDT (Aave). Personal bot uses 20/20/60.

Inputs (all from defi_positions — single source of truth):
  - health_factor, total_collateral_usd, total_debt_usd (from DB, refreshed by monitoring)
  - available_borrows_usd (fetched live from Aave via delegation_client.get_user_account_data)
  - Delegation permissions (from on-chain getDelegation call)

One action per wallet per cycle. No double-execution.
"""

import os
import json
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

GROWTH_HF_THRESHOLD = 2.60
CAPACITY_HF_THRESHOLD = 2.40
MACRO_HF_THRESHOLD = 3.05
MICRO_HF_THRESHOLD = 3.00
EMERGENCY_HF_THRESHOLD = 2.20

GROWTH_MIN_CAPACITY_USD = 13.20
CAPACITY_MIN_CAPACITY_USD = 8.20

GROWTH_ABSOLUTE_TRIGGER_USD = 50.0
GROWTH_RELATIVE_TRIGGER_PCT = 0.10

GROWTH_BORROW_USD = 11.40
CAPACITY_BORROW_USD = 6.70

GROWTH_DISTRIBUTION = {
    'total_borrow': 11.40,
    'usdt_swap_supply': 2.75,
    'wbtc_swap_supply': 2.80,
    'weth_swap_supply': 2.45,
    'eth_gas_reserve': 1.10,
    'dai_transfer': 1.10,
    'usdc_tax': 1.20,
}

CAPACITY_DISTRIBUTION = {
    'total_borrow': 6.70,
    'usdt_swap_supply': 1.10,
    'wbtc_swap_supply': 1.10,
    'weth_swap_supply': 1.10,
    'eth_gas_reserve': 1.10,
    'dai_transfer': 1.10,
    'usdc_tax': 1.20,
}

DELEGATED_STEP_ORDER = [
    "borrowed",
    "usdt_supplied",
    "wbtc_supplied",
    "weth_supplied",
    "eth_converted",
    "wallet_s_transferred",
    "usdc_taxed",
]

EXECUTION_STATE_DIR = "/tmp/reaa_delegation_states"

MACRO_VELOCITY_DROP_USD = 50.0
MACRO_VELOCITY_WINDOW_MIN = 30
MICRO_VELOCITY_DROP_USD = 30.0
MICRO_VELOCITY_WINDOW_MIN = 20
MICRO_COOLDOWN_HOURS = 4

MACRO_SHORT_SIZE_USD = 15.0
MICRO_SHORT_SIZE_USD = 8.0

SHORT_WBTC_PCT = 0.40
SHORT_USDT_PCT = 0.35
SHORT_WETH_PCT = 0.25

try:
    import db as database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

try:
    from delegation_client import (
        get_delegation_permissions,
        get_user_account_data,
        delegated_borrow_dai,
        delegated_borrow_weth,
        delegated_repay_weth,
        delegated_supply_dai_onbehalf,
        delegated_supply_wbtc_onbehalf,
        delegated_supply_weth_onbehalf,
        delegated_supply_usdt_onbehalf,
        delegated_withdraw_usdt,
        pull_token_from_user,
        dm_execute_supply,
        transfer_token_to_address,
        ensure_bot_dex_approval,
        _forward_tokens_to_user,
        check_user_wallet_approvals,
        get_multi_token_balances,
        get_token_balance,
        DAI_ADDRESS,
        WETH_ADDRESS,
        WBTC_TOKEN_ADDRESS,
        USDT_ADDRESS,
        USDC_ADDRESS,
        UNISWAP_ROUTER_ADDRESS,
    )
    DELEGATION_AVAILABLE = True
except ImportError:
    DELEGATION_AVAILABLE = False

try:
    from permissions import FULL_AUTOMATION, REQUIRED_FLAGS, validate_full_automation
    PERMISSIONS_AVAILABLE = True
except ImportError:
    PERMISSIONS_AVAILABLE = False

try:
    from uniswap_integration import UniswapIntegration
    UNISWAP_AVAILABLE = True
except ImportError:
    UNISWAP_AVAILABLE = False


def _log_strategy(user_id, wallet, mode, action, hf_before, hf_after=None, details=""):
    hf_after_str = f", hf_after={hf_after:.4f}" if hf_after is not None else ""
    msg = f"[Strategy] user={user_id} wallet={wallet[:10]}... mode={mode} action={action} hf_before={hf_before:.4f}{hf_after_str}"
    if details:
        msg += f" | {details}"
    logger.info(msg)
    print(msg)
    return msg


def _record_strategy_action(user_id, wallet_address, action_text):
    if not DB_AVAILABLE:
        return
    try:
        database.update_strategy_status(user_id, wallet_address, action_text)
    except Exception as e:
        logger.error(f"Failed to record strategy action for user {user_id}: {e}")


def _get_wallet_baseline(user_id, wallet_address):
    if not DB_AVAILABLE:
        return 0.0
    try:
        mw = database.get_managed_wallet(user_id, wallet_address)
        if mw and mw.get('last_collateral_baseline'):
            return float(mw['last_collateral_baseline'])
    except Exception:
        pass
    return 0.0


def _update_wallet_baseline(user_id, wallet_address, new_baseline):
    if not DB_AVAILABLE:
        return
    try:
        database.update_collateral_baseline(user_id, wallet_address, new_baseline)
    except Exception as e:
        logger.error(f"Failed to update baseline for user {user_id}: {e}")


def _get_execution_state_path(wallet_address):
    os.makedirs(EXECUTION_STATE_DIR, exist_ok=True)
    safe_addr = wallet_address.lower().replace("0x", "")
    return os.path.join(EXECUTION_STATE_DIR, f"exec_state_{safe_addr}.json")


def _save_execution_state(wallet_address, step, path_name, distribution):
    state = {
        "step": step,
        "path_name": path_name,
        "distribution": distribution,
        "timestamp": time.time(),
        "timestamp_human": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    try:
        path = _get_execution_state_path(wallet_address)
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
        logger.info(f"[ExecState] {wallet_address[:10]}... step={step} path={path_name}")
    except Exception as e:
        logger.error(f"[ExecState] save failed for {wallet_address[:10]}...: {e}")


def _load_execution_state(wallet_address):
    try:
        path = _get_execution_state_path(wallet_address)
        if os.path.exists(path):
            with open(path, 'r') as f:
                state = json.load(f)
            age = time.time() - state.get("timestamp", 0)
            if age > 86400:
                logger.warning(f"[ExecState] {wallet_address[:10]}... state is {age:.0f}s old (>24h) — clearing stale state")
                _clear_execution_state(wallet_address)
                return None
            return state
    except Exception as e:
        logger.error(f"[ExecState] load failed for {wallet_address[:10]}...: {e}")
    return None


def _clear_execution_state(wallet_address):
    try:
        path = _get_execution_state_path(wallet_address)
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"[ExecState] {wallet_address[:10]}... state cleared")
    except Exception as e:
        logger.error(f"[ExecState] clear failed for {wallet_address[:10]}...: {e}")


def _get_dai_debt_balance(wallet_address):
    if not DELEGATION_AVAILABLE:
        return 0.0
    try:
        from delegation_client import _get_web3, VARIABLE_DEBT_TOKENS
        from web3 import Web3
        w3 = _get_web3()
        dai_debt_addr = VARIABLE_DEBT_TOKENS.get("DAI")
        if not dai_debt_addr or not w3:
            return 0.0
        erc20_abi = [{"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
        debt_token = w3.eth.contract(address=Web3.to_checksum_address(dai_debt_addr), abi=erc20_abi)
        raw = debt_token.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
        return raw / 1e18
    except Exception as e:
        logger.error(f"[DAIDebt] {wallet_address[:10]}... check error: {e}")
        return 0.0


def _detect_orphaned_dai(wallet_address):
    if not DELEGATION_AVAILABLE:
        return False, 0.0
    try:
        balances = get_multi_token_balances(wallet_address)
        dai_balance = balances.get("DAI", {}).get("balance", 0) if balances else 0

        dai_debt = _get_dai_debt_balance(wallet_address)

        if dai_balance >= 2.0 and dai_debt >= 1.0:
            return True, dai_balance
    except Exception as e:
        logger.error(f"[OrphanDAI] {wallet_address[:10]}... detection error: {e}")
    return False, 0.0


def has_active_distribution(wallet_address):
    state = _load_execution_state(wallet_address)
    if state and state.get("step") and state.get("path_name"):
        step = state["step"]
        last_step = DELEGATED_STEP_ORDER[-1]
        if step != last_step:
            return True

    orphaned, dai_bal = _detect_orphaned_dai(wallet_address)
    if orphaned:
        logger.info(f"[ActiveDist] {wallet_address[:10]}... orphaned DAI detected (${dai_bal:.2f} DAI + debt) — treating as active distribution")
        return True
    return False


def resume_incomplete_distribution(user_id, wallet_address, agent):
    state = _load_execution_state(wallet_address)

    if state:
        step = state.get("step", "")
        path_name = state.get("path_name", "")
        distribution = state.get("distribution", {})
        last_step = DELEGATED_STEP_ORDER[-1]

        if step == last_step:
            _clear_execution_state(wallet_address)
            return None

        if not path_name or not distribution:
            logger.warning(f"[Resume] {wallet_address[:10]}... corrupt execution state — clearing")
            _clear_execution_state(wallet_address)
        else:
            age = time.time() - state.get("timestamp", 0)
            logger.info(f"[Resume] {wallet_address[:10]}... INCOMPLETE distribution (state file)! "
                        f"path={path_name}, last_step={step}, age={age:.0f}s — resuming swap pipeline")

            live_data = get_user_account_data(wallet_address) if DELEGATION_AVAILABLE else None
            live_hf = live_data.get("healthFactor", 0) if live_data else 0

            result = _execute_delegated_distribution(user_id, wallet_address, agent, path_name, distribution, live_hf)
            result["resumed"] = True
            result["resume_source"] = "state_file"
            logger.info(f"[Resume] {wallet_address[:10]}... state-file resume result: "
                        f"action={result.get('action')}, details={result.get('details')}")
            return result

    orphaned, dai_balance = _detect_orphaned_dai(wallet_address)
    if orphaned:
        logger.info(f"[Resume] {wallet_address[:10]}... ORPHANED DAI detected! "
                    f"DAI=${dai_balance:.2f} in wallet + active DAI debt — building recovery distribution")

        if dai_balance < 5.0:
            logger.info(f"[Resume] {wallet_address[:10]}... orphaned DAI ${dai_balance:.2f} below $5 minimum — "
                        f"too small for meaningful swaps, skipping recovery")
            return None

        recovery_distribution = dict(CAPACITY_DISTRIBUTION)
        if dai_balance > GROWTH_BORROW_USD:
            recovery_distribution = dict(GROWTH_DISTRIBUTION)

        total_available = dai_balance
        recovery_distribution['total_borrow'] = 0

        template_total = sum(v for k, v in recovery_distribution.items() if k != 'total_borrow')
        scale = min(1.0, total_available / template_total) if template_total > 0 else 0

        for k in recovery_distribution:
            if k != 'total_borrow':
                recovery_distribution[k] = round(recovery_distribution[k] * scale, 2)

        viable_legs = sum(1 for k, v in recovery_distribution.items() if k != 'total_borrow' and v >= 1.0)
        if viable_legs < 2:
            logger.info(f"[Resume] {wallet_address[:10]}... recovery distribution has only {viable_legs} legs >= $1 — "
                        f"not enough for meaningful recovery, skipping")
            return None

        _save_execution_state(wallet_address, "borrowed", "recovery", recovery_distribution)

        live_data = get_user_account_data(wallet_address) if DELEGATION_AVAILABLE else None
        live_hf = live_data.get("healthFactor", 0) if live_data else 0

        result = _execute_delegated_distribution(user_id, wallet_address, agent, "recovery", recovery_distribution, live_hf)
        result["resumed"] = True
        result["resume_source"] = "orphaned_dai"
        logger.info(f"[Resume] {wallet_address[:10]}... orphaned DAI resume result: "
                    f"action={result.get('action')}, details={result.get('details')}")
        return result

    return None


def _get_uniswap(agent):
    if hasattr(agent, 'uniswap') and agent.uniswap:
        return agent.uniswap
    return _get_bot_uniswap()


_bot_uniswap_cache = None

def _get_bot_uniswap():
    global _bot_uniswap_cache
    if _bot_uniswap_cache is not None:
        return _bot_uniswap_cache
    if UNISWAP_AVAILABLE:
        try:
            from delegation_client import _get_web3, _get_bot_account
            w3 = _get_web3()
            acct = _get_bot_account()
            if w3 and acct:
                _bot_uniswap_cache = UniswapIntegration(w3, acct)
                logger.info(f"[Uniswap] Bot-wallet UniswapIntegration created for {acct.address}")
                return _bot_uniswap_cache
            else:
                logger.error("[Uniswap] Cannot create bot UniswapIntegration: missing w3 or bot account")
        except Exception as e:
            logger.error(f"[Uniswap] Failed to initialize bot UniswapIntegration: {e}")
    return None


def _execute_delegated_distribution(user_id, wallet_address, agent, path_name, distribution, live_hf):
    """
    Execute the full 7-step distribution for a delegated user wallet.
    Tokens flow: Aave -> DM -> USER (via atomic executeBorrowAndTransfer).
    Each subsequent step pulls from USER wallet via pull_token_from_user (ERC20 allowance).

    Steps:
      1. Borrow DAI via delegation (lands in USER wallet atomically)
      2. Pull DAI from user -> swap DAI->USDT (multi-hop via WETH) -> supply USDT to Aave onBehalfOf user
      3. Pull DAI from user -> approve DEX -> swap DAI->WBTC -> supply WBTC to Aave onBehalfOf user
      4. Pull DAI from user -> approve DEX -> swap DAI->WETH -> supply WETH to Aave onBehalfOf user
      5. DAI stays in user wallet for gas reserve (no pull needed — user already holds DAI)
      6. Pull DAI from user -> transfer to Wallet_S
      7. Pull DAI from user -> approve DEX -> swap DAI->USDC -> transfer USDC to user wallet

    PRECONDITIONS:
      - User has granted BOT wallet ERC20 allowance for DAI (and other tokens) via frontend.
      - BOT->DEX Router approval is asserted before each swap (ensure_bot_dex_approval).

    SAFETY: Each swap step is wrapped in try/except. On failure, pulled tokens are
    returned to user wallet via _forward_tokens_to_user before aborting that step.
    Crash recovery via execution_state files.
    """
    result = {"mode": path_name, "action": "DISTRIBUTION", "executed": False, "details": "", "steps_completed": []}
    total_borrow = distribution['total_borrow']

    existing_state = _load_execution_state(wallet_address)
    resume_after = None
    if existing_state and existing_state.get("path_name") == path_name:
        resume_after = existing_state.get("step")
        logger.info(f"[Distribution] {wallet_address[:10]}... resuming {path_name} after step '{resume_after}'")

    already_done = set()
    if resume_after and resume_after in DELEGATED_STEP_ORDER:
        idx = DELEGATED_STEP_ORDER.index(resume_after)
        already_done = set(DELEGATED_STEP_ORDER[:idx + 1])

    uniswap = _get_bot_uniswap()
    if not uniswap:
        result["details"] = "Bot-wallet Uniswap unavailable — cannot execute swaps"
        result["action"] = "UNISWAP_UNAVAILABLE"
        logger.error(f"[Distribution] {wallet_address[:10]}... ABORTED: bot-wallet UniswapIntegration is None")
        _record_strategy_action(user_id, wallet_address, "ERROR: bot uniswap unavailable")
        return result

    dist_serializable = {k: v for k, v in distribution.items()}
    steps_completed = list(already_done)
    steps_failed = []

    approval_check = check_user_wallet_approvals(wallet_address) if DELEGATION_AVAILABLE else None
    if approval_check and not approval_check.get("all_approved"):
        missing = approval_check.get("missing", [])
        missing_str = "; ".join([f"{m['token']}->{m['spender']}" for m in missing[:5]])
        result["details"] = f"Missing approvals: {missing_str}"
        result["action"] = "APPROVAL_ERROR"
        _log_strategy(user_id, wallet_address, path_name, "APPROVAL_ERROR", live_hf,
                      details=f"Cannot execute — missing approvals: {missing_str}")
        _record_strategy_action(user_id, wallet_address, f"ERROR: missing approvals — {missing_str}")
        return result

    try:
        if "borrowed" not in already_done:
            _log_strategy(user_id, wallet_address, path_name, "STEP1_BORROW", live_hf,
                          details=f"Borrowing ${total_borrow:.2f} DAI via delegation")
            tx_hash = delegated_borrow_dai(wallet_address, total_borrow)
            if not tx_hash:
                result["details"] = f"DAI borrow failed for ${total_borrow:.2f}"
                result["action"] = "BORROW_FAILED"
                _record_strategy_action(user_id, wallet_address, f"FAILED: {path_name} borrow ${total_borrow:.2f} DAI")
                return result
            _save_execution_state(wallet_address, "borrowed", path_name, dist_serializable)
            steps_completed.append("borrowed")
            time.sleep(3)

        usdt_amount = distribution['usdt_swap_supply']
        if "usdt_supplied" not in already_done and usdt_amount >= 0.50 and uniswap:
            _log_strategy(user_id, wallet_address, path_name, "STEP2_USDT_SWAP", live_hf,
                          details=f"Pull ${usdt_amount:.2f} DAI from user -> swap DAI->USDT -> supply onBehalfOf")
            usdt_dai_wei = int(usdt_amount * 1e18)
            pull_tx = pull_token_from_user(wallet_address, DAI_ADDRESS, usdt_dai_wei)
            if pull_tx:
                time.sleep(2)
                try:
                    if not ensure_bot_dex_approval(DAI_ADDRESS, usdt_dai_wei):
                        raise Exception("BOT->DEX Router DAI approval failed")
                    from delegation_client import _get_bot_account, _get_web3, ERC20_ABI
                    w3 = _get_web3()
                    acct = _get_bot_account()
                    usdt_contract = w3.eth.contract(
                        address=w3.to_checksum_address(USDT_ADDRESS), abi=ERC20_ABI)
                    usdt_before = usdt_contract.functions.balanceOf(acct.address).call()
                    swap_result = uniswap.swap_dai_for_usdt_multihop(usdt_amount)
                    if swap_result and swap_result.get('tx_hash'):
                        time.sleep(3)
                        usdt_after = usdt_contract.functions.balanceOf(acct.address).call()
                        usdt_received = usdt_after - usdt_before
                        if usdt_received > 0:
                            usdt_float = usdt_received / 1e6
                            supply_tx = delegated_supply_usdt_onbehalf(wallet_address, usdt_float)
                            if supply_tx:
                                _save_execution_state(wallet_address, "usdt_supplied", path_name, dist_serializable)
                                steps_completed.append("usdt_supplied")
                                time.sleep(2)
                            else:
                                logger.error(f"[Distribution] {wallet_address[:10]}... USDT supply failed. Returning {usdt_float:.2f} USDT to user.")
                                _forward_tokens_to_user(USDT_ADDRESS, usdt_received, wallet_address)
                                steps_failed.append("usdt_supply_to_aave")
                        else:
                            steps_failed.append("usdt_swap_zero_output")
                    else:
                        raise Exception("DAI->USDT swap tx failed or reverted")
                except Exception as e:
                    logger.error(f"[Distribution] {wallet_address[:10]}... USDT swap failed: {e}. Rolling back DAI to user.")
                    _forward_tokens_to_user(DAI_ADDRESS, usdt_dai_wei, wallet_address)
                    steps_failed.append("dai_to_usdt_swap_rollback")
            else:
                steps_failed.append("usdt_dai_pull")
                logger.warning(f"[Distribution] {wallet_address[:10]}... DAI pull for USDT swap failed (check BOT allowance)")
        elif "usdt_supplied" in already_done:
            pass

        wbtc_amount = distribution['wbtc_swap_supply']
        if "wbtc_supplied" not in already_done and wbtc_amount >= 0.50 and uniswap:
            _log_strategy(user_id, wallet_address, path_name, "STEP3_WBTC_SWAP", live_hf,
                          details=f"Pull ${wbtc_amount:.2f} DAI from user -> swap DAI->WBTC -> supply onBehalfOf")
            wbtc_dai_wei = int(wbtc_amount * 1e18)
            pull_tx = pull_token_from_user(wallet_address, DAI_ADDRESS, wbtc_dai_wei)
            if pull_tx:
                time.sleep(2)
                try:
                    if not ensure_bot_dex_approval(DAI_ADDRESS, wbtc_dai_wei):
                        raise Exception("BOT->DEX Router DAI approval failed")
                    from delegation_client import _get_bot_account, _get_web3, ERC20_ABI
                    w3 = _get_web3()
                    acct = _get_bot_account()
                    wbtc_contract = w3.eth.contract(
                        address=w3.to_checksum_address(WBTC_TOKEN_ADDRESS), abi=ERC20_ABI)
                    wbtc_before = wbtc_contract.functions.balanceOf(acct.address).call()
                    swap_result = uniswap.swap_dai_for_wbtc(wbtc_amount)
                    if swap_result and swap_result.get('tx_hash'):
                        time.sleep(3)
                        wbtc_after = wbtc_contract.functions.balanceOf(acct.address).call()
                        wbtc_received = wbtc_after - wbtc_before
                        if wbtc_received > 0:
                            wbtc_float = wbtc_received / 1e8
                            supply_tx = delegated_supply_wbtc_onbehalf(wallet_address, wbtc_float)
                            if supply_tx:
                                _save_execution_state(wallet_address, "wbtc_supplied", path_name, dist_serializable)
                                steps_completed.append("wbtc_supplied")
                                time.sleep(2)
                            else:
                                logger.error(f"[Distribution] {wallet_address[:10]}... WBTC supply failed. Returning {wbtc_float:.8f} WBTC to user.")
                                _forward_tokens_to_user(WBTC_TOKEN_ADDRESS, wbtc_received, wallet_address)
                                steps_failed.append("wbtc_supply_to_aave")
                        else:
                            steps_failed.append("wbtc_swap_zero_output")
                    else:
                        raise Exception("DAI->WBTC swap tx failed or reverted")
                except Exception as e:
                    logger.error(f"[Distribution] {wallet_address[:10]}... WBTC swap failed: {e}. Rolling back DAI to user.")
                    _forward_tokens_to_user(DAI_ADDRESS, wbtc_dai_wei, wallet_address)
                    steps_failed.append("dai_to_wbtc_swap_rollback")
            else:
                steps_failed.append("wbtc_dai_pull")
                logger.warning(f"[Distribution] {wallet_address[:10]}... DAI pull for WBTC swap failed (check BOT allowance)")
        elif "wbtc_supplied" in already_done:
            pass

        weth_amount = distribution['weth_swap_supply']
        if "weth_supplied" not in already_done and weth_amount >= 0.50 and uniswap:
            _log_strategy(user_id, wallet_address, path_name, "STEP4_WETH_SWAP", live_hf,
                          details=f"Pull ${weth_amount:.2f} DAI from user -> swap DAI->WETH -> supply onBehalfOf")
            weth_dai_wei = int(weth_amount * 1e18)
            pull_tx = pull_token_from_user(wallet_address, DAI_ADDRESS, weth_dai_wei)
            if pull_tx:
                time.sleep(2)
                try:
                    if not ensure_bot_dex_approval(DAI_ADDRESS, weth_dai_wei):
                        raise Exception("BOT->DEX Router DAI approval failed")
                    from delegation_client import _get_bot_account, _get_web3, ERC20_ABI
                    w3 = _get_web3()
                    acct = _get_bot_account()
                    weth_contract = w3.eth.contract(
                        address=w3.to_checksum_address(WETH_ADDRESS), abi=ERC20_ABI)
                    weth_before = weth_contract.functions.balanceOf(acct.address).call()
                    swap_result = uniswap.swap_dai_for_weth(weth_amount)
                    if swap_result and swap_result.get('tx_hash'):
                        time.sleep(3)
                        weth_after = weth_contract.functions.balanceOf(acct.address).call()
                        weth_received = weth_after - weth_before
                        if weth_received > 0:
                            weth_float = weth_received / 1e18
                            supply_tx = delegated_supply_weth_onbehalf(wallet_address, weth_float)
                            if supply_tx:
                                _save_execution_state(wallet_address, "weth_supplied", path_name, dist_serializable)
                                steps_completed.append("weth_supplied")
                                time.sleep(2)
                            else:
                                logger.error(f"[Distribution] {wallet_address[:10]}... WETH supply failed. Returning {weth_float:.8f} WETH to user.")
                                _forward_tokens_to_user(WETH_ADDRESS, weth_received, wallet_address)
                                steps_failed.append("weth_supply_to_aave")
                        else:
                            steps_failed.append("weth_swap_zero_output")
                    else:
                        raise Exception("DAI->WETH swap tx failed or reverted")
                except Exception as e:
                    logger.error(f"[Distribution] {wallet_address[:10]}... WETH swap failed: {e}. Rolling back DAI to user.")
                    _forward_tokens_to_user(DAI_ADDRESS, weth_dai_wei, wallet_address)
                    steps_failed.append("dai_to_weth_swap_rollback")
            else:
                steps_failed.append("weth_dai_pull")
                logger.warning(f"[Distribution] {wallet_address[:10]}... DAI pull for WETH swap failed (check BOT allowance)")
        elif "weth_supplied" in already_done:
            pass

        eth_amount = distribution['eth_gas_reserve']
        if "eth_converted" not in already_done and eth_amount >= 0.50:
            _log_strategy(user_id, wallet_address, path_name, "STEP5_ETH_GAS", live_hf,
                          details=f"${eth_amount:.2f} DAI stays in user wallet for gas reserve (no action needed)")
            _save_execution_state(wallet_address, "eth_converted", path_name, dist_serializable)
            steps_completed.append("eth_converted")
        elif "eth_converted" in already_done:
            pass

        dai_transfer = distribution['dai_transfer']
        if "wallet_s_transferred" not in already_done and dai_transfer >= 0.50:
            wallet_s = os.getenv('WALLET_S_ADDRESS', '').strip()
            if wallet_s and len(wallet_s) == 42:
                _log_strategy(user_id, wallet_address, path_name, "STEP6_WALLET_S", live_hf,
                              details=f"Pull ${dai_transfer:.2f} DAI from user -> transfer to Wallet_S")
                dai_transfer_wei = int(dai_transfer * 1e18)
                # PRECONDITION: user → BOT wallet ERC20 allowance is set for DAI via frontend.
                pull_tx = pull_token_from_user(wallet_address, DAI_ADDRESS, dai_transfer_wei)
                if pull_tx:
                    time.sleep(2)
                    xfer_tx = transfer_token_to_address(wallet_s, DAI_ADDRESS, dai_transfer_wei)
                    if xfer_tx:
                        _save_execution_state(wallet_address, "wallet_s_transferred", path_name, dist_serializable)
                        steps_completed.append("wallet_s_transferred")
                        time.sleep(2)
                    else:
                        steps_failed.append("wallet_s_transfer")
                else:
                    steps_failed.append("wallet_s_dai_pull")
                    logger.warning(f"[Distribution] {wallet_address[:10]}... DAI pull for Wallet_S failed (check BOT allowance)")
            else:
                logger.warning(f"[Distribution] WALLET_S_ADDRESS not set — skipping Wallet_S transfer")
                _save_execution_state(wallet_address, "wallet_s_transferred", path_name, dist_serializable)
                steps_completed.append("wallet_s_transferred")

        usdc_tax = distribution.get('usdc_tax', 0)
        if "usdc_taxed" not in already_done and usdc_tax >= 0.50 and uniswap:
            _log_strategy(user_id, wallet_address, path_name, "STEP7_USDC_TAX", live_hf,
                          details=f"Pull ${usdc_tax:.2f} DAI from user -> swap DAI->USDC -> transfer USDC to user")
            usdc_dai_wei = int(usdc_tax * 1e18)
            pull_tx = pull_token_from_user(wallet_address, DAI_ADDRESS, usdc_dai_wei)
            if pull_tx:
                time.sleep(2)
                try:
                    if not ensure_bot_dex_approval(DAI_ADDRESS, usdc_dai_wei):
                        raise Exception("BOT->DEX Router DAI approval failed")
                    from delegation_client import _get_bot_account, _get_web3, ERC20_ABI
                    w3 = _get_web3()
                    acct = _get_bot_account()
                    usdc_contract = w3.eth.contract(
                        address=w3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
                    usdc_before = usdc_contract.functions.balanceOf(acct.address).call()
                    swap_result = uniswap.swap_dai_for_usdc(usdc_tax)
                    if swap_result and swap_result.get('tx_hash'):
                        time.sleep(3)
                        usdc_after = usdc_contract.functions.balanceOf(acct.address).call()
                        usdc_received = usdc_after - usdc_before
                        if usdc_received > 0:
                            xfer_tx = transfer_token_to_address(wallet_address, USDC_ADDRESS, usdc_received)
                            if xfer_tx:
                                _save_execution_state(wallet_address, "usdc_taxed", path_name, dist_serializable)
                                steps_completed.append("usdc_taxed")
                            else:
                                _forward_tokens_to_user(USDC_ADDRESS, usdc_received, wallet_address)
                                steps_failed.append("usdc_transfer_to_user")
                        else:
                            steps_failed.append("usdc_swap_zero_output")
                    else:
                        raise Exception("DAI->USDC swap tx failed or reverted")
                except Exception as e:
                    logger.error(f"[Distribution] {wallet_address[:10]}... USDC swap failed: {e}. Rolling back DAI to user.")
                    _forward_tokens_to_user(DAI_ADDRESS, usdc_dai_wei, wallet_address)
                    steps_failed.append("dai_to_usdc_swap_rollback")
            else:
                steps_failed.append("usdc_dai_pull")
                logger.warning(f"[Distribution] {wallet_address[:10]}... DAI pull for USDC tax failed (check BOT allowance)")
        elif "usdc_taxed" in already_done:
            pass

        _clear_execution_state(wallet_address)

        post_data = get_user_account_data(wallet_address)
        post_hf = post_data.get("healthFactor", 0) if post_data else 0

        completed_count = len(steps_completed)
        failed_count = len(steps_failed)
        detail_str = f"{completed_count}/7 steps OK"
        if failed_count > 0:
            detail_str += f", {failed_count} failed: {', '.join(steps_failed)}"
        detail_str += f", HF {live_hf:.2f} -> {post_hf:.2f}"

        result["executed"] = completed_count >= 1
        result["action"] = "DISTRIBUTION_COMPLETE" if failed_count == 0 else "DISTRIBUTION_PARTIAL"
        result["details"] = detail_str
        result["steps_completed"] = steps_completed

        _log_strategy(user_id, wallet_address, path_name, result["action"], live_hf, hf_after=post_hf,
                      details=detail_str)
        _record_strategy_action(user_id, wallet_address, f"{path_name.upper()}: {detail_str}")

        if DB_AVAILABLE:
            database.record_wallet_action(
                user_id=user_id, wallet_address=wallet_address,
                action_type=f'strategy_{path_name}_distribution',
                details={"distribution": dist_serializable, "steps_completed": steps_completed,
                         "steps_failed": steps_failed, "hf_before": live_hf, "hf_after": post_hf},
                tx_hash=None)

        return result

    except Exception as e:
        logger.error(f"[Distribution] {wallet_address[:10]}... {path_name} failed: {e}", exc_info=True)
        result["details"] = f"Distribution exception: {e}"
        result["action"] = "DISTRIBUTION_ERROR"
        _record_strategy_action(user_id, wallet_address, f"ERROR: {path_name} distribution exception — {e}")
        return result


def _execute_delegated_short_entry(user_id, wallet_address, agent, tier, short_size_usd, live_hf):
    """
    Delegated liability short entry:
      1. Borrow WETH via delegation (lands in user wallet)
      2. Pull WETH from user -> swap 40% to WBTC -> supply onBehalfOf
      3. Remaining WETH: swap 35% to USDT -> supply onBehalfOf
      4. Remaining 25% WETH -> supply onBehalfOf as WETH collateral
    """
    result = {"mode": f"{tier}_short", "action": "SHORT_ENTRY", "executed": False, "details": ""}

    uniswap = _get_bot_uniswap()
    if not uniswap:
        result["details"] = "uniswap_unavailable"
        return result

    try:
        from delegation_client import _get_web3
        w3 = _get_web3()
        if not w3:
            result["details"] = "web3_unavailable"
            return result

        eth_price = 2000.0
        try:
            oracle_addr = "0xb56c2F0B653B2e0b10C9b928C8580Ac5Df02C7C7"
            oracle_abi = [{"inputs": [{"name": "asset", "type": "address"}], "name": "getAssetPrice",
                           "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
            oracle = w3.eth.contract(address=w3.to_checksum_address(oracle_addr), abi=oracle_abi)
            eth_price = oracle.functions.getAssetPrice(w3.to_checksum_address(WETH_ADDRESS)).call() / 1e8
        except Exception:
            pass

        weth_amount = short_size_usd / eth_price
        _log_strategy(user_id, wallet_address, f"{tier}_short", "SHORT_ENTRY", live_hf,
                      details=f"Borrowing {weth_amount:.6f} WETH (${short_size_usd:.2f}) via delegation")

        tx_hash = delegated_borrow_weth(wallet_address, weth_amount)
        if not tx_hash:
            result["details"] = f"WETH borrow failed for {weth_amount:.6f}"
            result["action"] = "SHORT_ENTRY_FAILED"
            return result

        time.sleep(3)

        wbtc_weth = weth_amount * SHORT_WBTC_PCT
        usdt_weth = weth_amount * SHORT_USDT_PCT
        hold_weth = weth_amount * SHORT_WETH_PCT

        wbtc_weth_wei = int(wbtc_weth * 1e18)
        pull_tx = pull_token_from_user(wallet_address, WETH_ADDRESS, wbtc_weth_wei)
        if pull_tx:
            time.sleep(2)
            try:
                if not ensure_bot_dex_approval(WETH_ADDRESS, wbtc_weth_wei):
                    raise Exception("BOT->DEX Router WETH approval failed")
                swap_result = uniswap.swap_weth_for_wbtc(wbtc_weth)
                if swap_result and swap_result.get('tx_hash'):
                    time.sleep(3)
                    from delegation_client import _get_bot_account, ERC20_ABI
                    acct = _get_bot_account()
                    wbtc_contract = w3.eth.contract(address=w3.to_checksum_address(WBTC_TOKEN_ADDRESS), abi=ERC20_ABI)
                    wbtc_bal = wbtc_contract.functions.balanceOf(acct.address).call()
                    if wbtc_bal > 0:
                        delegated_supply_wbtc_onbehalf(wallet_address, wbtc_bal / 1e8)
                        time.sleep(2)
                else:
                    raise Exception("WETH->WBTC swap tx failed or reverted")
            except Exception as e:
                logger.error(f"[Short Entry] {wallet_address[:10]}... WBTC swap failed: {e}. Rolling back WETH to user.")
                _forward_tokens_to_user(WETH_ADDRESS, wbtc_weth_wei, wallet_address)

        usdt_weth_wei = int(usdt_weth * 1e18)
        pull_tx = pull_token_from_user(wallet_address, WETH_ADDRESS, usdt_weth_wei)
        if pull_tx:
            time.sleep(2)
            try:
                if not ensure_bot_dex_approval(WETH_ADDRESS, usdt_weth_wei):
                    raise Exception("BOT->DEX Router WETH approval failed")
                swap_result = uniswap.swap_weth_for_usdt(usdt_weth)
                if swap_result and swap_result.get('tx_hash'):
                    time.sleep(3)
                    from delegation_client import _get_bot_account, ERC20_ABI
                    acct = _get_bot_account()
                    usdt_contract = w3.eth.contract(address=w3.to_checksum_address(USDT_ADDRESS), abi=ERC20_ABI)
                    usdt_bal = usdt_contract.functions.balanceOf(acct.address).call()
                    if usdt_bal > 0:
                        delegated_supply_usdt_onbehalf(wallet_address, usdt_bal / 1e6)
                        time.sleep(2)
                else:
                    raise Exception("WETH->USDT swap tx failed or reverted")
            except Exception as e:
                logger.error(f"[Short Entry] {wallet_address[:10]}... USDT swap failed: {e}. Rolling back WETH to user.")
                _forward_tokens_to_user(WETH_ADDRESS, usdt_weth_wei, wallet_address)

        hold_weth_wei = int(hold_weth * 1e18)
        pull_tx = pull_token_from_user(wallet_address, WETH_ADDRESS, hold_weth_wei)
        if pull_tx:
            time.sleep(2)
            delegated_supply_weth_onbehalf(wallet_address, hold_weth)
            time.sleep(2)

        result["executed"] = True
        result["action"] = "SHORT_ENTRY_OK"
        result["details"] = f"{tier} short: {weth_amount:.6f} WETH (${short_size_usd:.2f}), ETH@${eth_price:.2f}"

        if DB_AVAILABLE:
            database.record_wallet_action(
                user_id=user_id, wallet_address=wallet_address,
                action_type=f'strategy_{tier}_short_entry',
                details={"weth_borrowed": weth_amount, "eth_price": eth_price,
                         "short_size_usd": short_size_usd, "hf": live_hf},
                tx_hash=tx_hash)

        _log_strategy(user_id, wallet_address, f"{tier}_short", "SHORT_ENTRY_OK", live_hf,
                      details=result["details"])
        _record_strategy_action(user_id, wallet_address, f"SHORT ENTRY: {result['details']}")
        return result

    except Exception as e:
        logger.error(f"[Short Entry] {wallet_address[:10]}... failed: {e}", exc_info=True)
        result["details"] = f"Short entry exception: {e}"
        result["action"] = "SHORT_ENTRY_ERROR"
        return result


SHORT_CLOSE_WALLET_S_PCT = 0.20
SHORT_CLOSE_USDC_PCT = 0.20
SHORT_CLOSE_WBTC_PCT = 0.30
SHORT_CLOSE_WETH_PCT = 0.20
SHORT_CLOSE_USDT_PCT = 0.10


def _log_short_close_slice(wallet_address, slice_name, pct, status, amount_in_weth, amount_out_token=0.0, reason=""):
    import json as _json
    entry = {
        "event": "short_close_slice",
        "wallet": wallet_address,
        "slice": slice_name,
        "percent_of_profit": int(pct * 100),
        "status": status,
        "amount_in_weth": round(amount_in_weth, 8),
        "amount_out_token": round(amount_out_token, 8),
        "reason": reason
    }
    logger.info(_json.dumps(entry))
    return entry


def _log_short_close_residual(wallet_address, amount_in_weth, amount_out_eth=0.0, status="OK", reason=""):
    import json as _json
    entry = {
        "event": "short_close_residual_sweep",
        "wallet": wallet_address,
        "token_in": "WETH",
        "amount_in_weth": round(amount_in_weth, 8),
        "amount_out_eth": round(amount_out_eth, 8),
        "status": status,
        "reason": reason
    }
    logger.info(_json.dumps(entry))
    return entry


def _execute_delegated_short_close(user_id, wallet_address, agent, live_hf):
    """
    Delegated liability short close with 20/20/30/20/10 profit distribution.

    Phase 1 — Close the short:
      1. Withdraw USDT collateral from Aave via delegation
      2. Pull USDT from user wallet -> swap USDT->WETH
      3. Repay WETH debt via delegation
      4. Remaining WETH in bot wallet = realized profit P

    Phase 2 — Distribute profit P (WETH remaining after repay):
      20% → Wallet_S (swap WETH->DAI, transfer DAI to Wallet_S)
      20% → USDC    (swap WETH->USDC, transfer USDC to user wallet)
      30% → WBTC    (swap WETH->WBTC, supply to Aave onBehalfOf user)
      20% → WETH    (keep as WETH, supply to Aave onBehalfOf user)
      10% → USDT    (swap WETH->USDT, supply to Aave onBehalfOf user)

    Residual: Any leftover WETH (from rounding/slippage/failures) is swapped
    to ETH and sent to the user wallet as gas/safety net.

    Each slice executes independently (best-effort). If one slice fails,
    the others still proceed. Nurse Mode will sweep any stray tokens later.

    Personal bot uses a different split (20/20/60 Wallet_S/Wallet_B/collateral).
    """
    result = {"mode": "short_close", "action": "SHORT_CLOSE", "executed": False, "details": "",
              "distribution": {}}

    uniswap = _get_bot_uniswap()
    if not uniswap:
        result["details"] = "uniswap_unavailable"
        return result

    try:
        from delegation_client import _get_web3, _get_bot_account, ERC20_ABI
        w3 = _get_web3()
        acct = _get_bot_account()
        if not w3 or not acct:
            result["details"] = "web3_or_account_unavailable"
            return result

        user_balances = get_multi_token_balances(wallet_address)
        usdt_balance = user_balances.get("USDT", {}).get("balance", 0) if user_balances else 0

        if usdt_balance < 1.0:
            result["details"] = f"USDT balance too low ({usdt_balance:.2f}) for short close"
            return result

        _log_strategy(user_id, wallet_address, "short_close", "STEP1_WITHDRAW_USDT", live_hf,
                      details=f"Withdrawing {usdt_balance:.2f} USDT from Aave")
        withdraw_tx = delegated_withdraw_usdt(wallet_address, usdt_balance)
        if not withdraw_tx:
            result["details"] = "USDT withdrawal from Aave failed"
            result["action"] = "SHORT_CLOSE_FAILED"
            return result
        time.sleep(3)

        usdt_available_raw = int(usdt_balance * 1e6)
        pull_tx = pull_token_from_user(wallet_address, USDT_ADDRESS, usdt_available_raw)
        if not pull_tx:
            result["details"] = "USDT pull from user failed — USDT stays in user wallet"
            result["action"] = "SHORT_CLOSE_FAILED"
            return result
        time.sleep(2)

        _log_strategy(user_id, wallet_address, "short_close", "STEP2_SWAP_USDT_WETH", live_hf,
                      details=f"Swapping {usdt_balance:.2f} USDT -> WETH")
        if not ensure_bot_dex_approval(USDT_ADDRESS, usdt_available_raw):
            logger.error(f"[Short Close] {wallet_address[:10]}... BOT->DEX USDT approval failed. Rolling back USDT to user.")
            _forward_tokens_to_user(USDT_ADDRESS, usdt_available_raw, wallet_address)
            result["details"] = "BOT->DEX USDT approval failed — USDT returned to user"
            result["action"] = "SHORT_CLOSE_FAILED"
            return result
        swap_result = uniswap.swap_usdt_for_weth(usdt_balance * 0.95)
        if not swap_result or 'tx_hash' not in swap_result:
            logger.error(f"[Short Close] {wallet_address[:10]}... USDT->WETH swap failed. Rolling back USDT to user.")
            _forward_tokens_to_user(USDT_ADDRESS, usdt_available_raw, wallet_address)
            result["details"] = "USDT->WETH swap failed — USDT returned to user"
            result["action"] = "SHORT_CLOSE_FAILED"
            return result
        time.sleep(3)

        weth_contract = w3.eth.contract(address=w3.to_checksum_address(WETH_ADDRESS), abi=ERC20_ABI)
        weth_received_raw = weth_contract.functions.balanceOf(acct.address).call()
        weth_received = weth_received_raw / 1e18

        if weth_received < 0.0001:
            result["details"] = "WETH received from swap too low"
            result["action"] = "SHORT_CLOSE_FAILED"
            return result

        _log_strategy(user_id, wallet_address, "short_close", "STEP3_REPAY_WETH", live_hf,
                      details=f"Repaying {weth_received:.8f} WETH debt via delegation")

        from delegation_client import _ensure_bot_approval, AAVE_POOL_ADDRESS
        _ensure_bot_approval(WETH_ADDRESS, AAVE_POOL_ADDRESS, weth_received_raw)

        repay_tx = delegated_repay_weth(wallet_address, weth_received * 0.999)
        if not repay_tx:
            result["details"] = "WETH repayment failed — WETH in bot wallet for recovery"
            result["action"] = "SHORT_CLOSE_FAILED"
            return result
        time.sleep(3)

        profit_weth_raw = weth_contract.functions.balanceOf(acct.address).call()
        profit_weth = profit_weth_raw / 1e18

        if profit_weth < 0.00001:
            _log_strategy(user_id, wallet_address, "short_close", "NO_PROFIT", live_hf,
                          details=f"No profit after repay (remaining WETH={profit_weth:.8f})")
            post_data = get_user_account_data(wallet_address)
            post_hf = post_data.get("healthFactor", 0) if post_data else 0
            result["executed"] = True
            result["action"] = "SHORT_CLOSE_OK"
            result["details"] = f"Short closed, no profit. HF {live_hf:.2f} -> {post_hf:.2f}"
            _record_strategy_action(user_id, wallet_address, f"SHORT CLOSE: no profit, HF {live_hf:.2f} -> {post_hf:.2f}")
            return result

        _log_strategy(user_id, wallet_address, "short_close", "STEP4_DISTRIBUTE_PROFIT", live_hf,
                      details=f"Profit = {profit_weth:.8f} WETH — distributing 20/20/30/20/10")

        weth_wallet_s = profit_weth * SHORT_CLOSE_WALLET_S_PCT
        weth_usdc     = profit_weth * SHORT_CLOSE_USDC_PCT
        weth_wbtc     = profit_weth * SHORT_CLOSE_WBTC_PCT
        weth_aave     = profit_weth * SHORT_CLOSE_WETH_PCT
        weth_usdt     = profit_weth * SHORT_CLOSE_USDT_PCT

        dist_log = (f"P={profit_weth:.8f} WETH: "
                    f"20% Wallet_S={weth_wallet_s:.8f}, "
                    f"20% USDC={weth_usdc:.8f}, "
                    f"30% WBTC={weth_wbtc:.8f}, "
                    f"20% WETH(supply)={weth_aave:.8f}, "
                    f"10% USDT={weth_usdt:.8f}")
        logger.info(f"[Short Close] {wallet_address[:10]}... {dist_log}")

        dist_results = {"wallet_s": "pending", "usdc": "pending",
                        "wbtc": "pending", "weth_supply": "pending", "usdt": "pending"}
        slice_logs = []

        wallet_s = os.getenv('WALLET_S_ADDRESS', '').strip()
        if wallet_s and len(wallet_s) == 42 and weth_wallet_s >= 0.00001:
            _log_strategy(user_id, wallet_address, "short_close", "DIST_WALLET_S", live_hf,
                          details=f"Swap {weth_wallet_s:.8f} WETH -> DAI -> Wallet_S")
            try:
                ensure_bot_dex_approval(WETH_ADDRESS, int(weth_wallet_s * 1e18))
                swap_res = uniswap.swap_weth_for_dai(weth_wallet_s)
                if swap_res and swap_res.get('tx_hash'):
                    time.sleep(3)
                    dai_contract = w3.eth.contract(address=w3.to_checksum_address(DAI_ADDRESS), abi=ERC20_ABI)
                    dai_bal = dai_contract.functions.balanceOf(acct.address).call()
                    if dai_bal > 0:
                        xfer_tx = transfer_token_to_address(wallet_s, DAI_ADDRESS, dai_bal)
                        if xfer_tx:
                            dai_out = dai_bal / 1e18
                            dist_results["wallet_s"] = f"OK ({dai_out:.4f} DAI)"
                            slice_logs.append(_log_short_close_slice(wallet_address, "Wallet_S", SHORT_CLOSE_WALLET_S_PCT, "OK", weth_wallet_s, dai_out))
                            time.sleep(2)
                        else:
                            dist_results["wallet_s"] = "transfer_failed"
                            slice_logs.append(_log_short_close_slice(wallet_address, "Wallet_S", SHORT_CLOSE_WALLET_S_PCT, "FAILED", weth_wallet_s, reason="DAI transfer to Wallet_S failed"))
                    else:
                        dist_results["wallet_s"] = "swap_zero_output"
                        slice_logs.append(_log_short_close_slice(wallet_address, "Wallet_S", SHORT_CLOSE_WALLET_S_PCT, "FAILED", weth_wallet_s, reason="swap returned zero DAI"))
                else:
                    dist_results["wallet_s"] = "swap_failed"
                    slice_logs.append(_log_short_close_slice(wallet_address, "Wallet_S", SHORT_CLOSE_WALLET_S_PCT, "FAILED", weth_wallet_s, reason="WETH->DAI swap failed"))
            except Exception as e:
                dist_results["wallet_s"] = f"error: {e}"
                slice_logs.append(_log_short_close_slice(wallet_address, "Wallet_S", SHORT_CLOSE_WALLET_S_PCT, "FAILED", weth_wallet_s, reason=str(e)))
                logger.error(f"[Short Close] Wallet_S distribution failed: {e}")
        elif not wallet_s or len(wallet_s) != 42:
            dist_results["wallet_s"] = "WALLET_S_ADDRESS_not_set"
            slice_logs.append(_log_short_close_slice(wallet_address, "Wallet_S", SHORT_CLOSE_WALLET_S_PCT, "FAILED", weth_wallet_s, reason="WALLET_S_ADDRESS not configured"))
        else:
            dist_results["wallet_s"] = "amount_too_small"
            slice_logs.append(_log_short_close_slice(wallet_address, "Wallet_S", SHORT_CLOSE_WALLET_S_PCT, "OK", weth_wallet_s, reason="amount below threshold, skipped"))

        if weth_usdc >= 0.00001:
            _log_strategy(user_id, wallet_address, "short_close", "DIST_USDC", live_hf,
                          details=f"Swap {weth_usdc:.8f} WETH -> USDC -> user wallet")
            try:
                ensure_bot_dex_approval(WETH_ADDRESS, int(weth_usdc * 1e18))
                usdc_swap = uniswap.swap_tokens(WETH_ADDRESS, USDC_ADDRESS, weth_usdc, fee=500)
                if usdc_swap and usdc_swap.get('tx_hash'):
                    time.sleep(3)
                    usdc_contract = w3.eth.contract(address=w3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
                    usdc_bal = usdc_contract.functions.balanceOf(acct.address).call()
                    if usdc_bal > 0:
                        xfer_tx = transfer_token_to_address(wallet_address, USDC_ADDRESS, usdc_bal)
                        if xfer_tx:
                            usdc_out = usdc_bal / 1e6
                            dist_results["usdc"] = f"OK ({usdc_out:.2f} USDC)"
                            slice_logs.append(_log_short_close_slice(wallet_address, "USDC", SHORT_CLOSE_USDC_PCT, "OK", weth_usdc, usdc_out))
                            time.sleep(2)
                        else:
                            dist_results["usdc"] = "transfer_failed"
                            slice_logs.append(_log_short_close_slice(wallet_address, "USDC", SHORT_CLOSE_USDC_PCT, "FAILED", weth_usdc, reason="USDC transfer to user wallet failed"))
                    else:
                        dist_results["usdc"] = "swap_zero_output"
                        slice_logs.append(_log_short_close_slice(wallet_address, "USDC", SHORT_CLOSE_USDC_PCT, "FAILED", weth_usdc, reason="swap returned zero USDC"))
                else:
                    dist_results["usdc"] = "swap_failed"
                    slice_logs.append(_log_short_close_slice(wallet_address, "USDC", SHORT_CLOSE_USDC_PCT, "FAILED", weth_usdc, reason="WETH->USDC swap failed"))
            except Exception as e:
                dist_results["usdc"] = f"error: {e}"
                slice_logs.append(_log_short_close_slice(wallet_address, "USDC", SHORT_CLOSE_USDC_PCT, "FAILED", weth_usdc, reason=str(e)))
                logger.error(f"[Short Close] USDC distribution failed: {e}")
        else:
            dist_results["usdc"] = "amount_too_small"
            slice_logs.append(_log_short_close_slice(wallet_address, "USDC", SHORT_CLOSE_USDC_PCT, "OK", weth_usdc, reason="amount below threshold, skipped"))

        if weth_wbtc >= 0.00001:
            _log_strategy(user_id, wallet_address, "short_close", "DIST_WBTC", live_hf,
                          details=f"Swap {weth_wbtc:.8f} WETH -> WBTC -> Aave supply onBehalfOf user")
            try:
                ensure_bot_dex_approval(WETH_ADDRESS, int(weth_wbtc * 1e18))
                wbtc_swap = uniswap.swap_weth_for_wbtc(weth_wbtc)
                if wbtc_swap and wbtc_swap.get('tx_hash'):
                    time.sleep(3)
                    wbtc_contract = w3.eth.contract(address=w3.to_checksum_address(WBTC_TOKEN_ADDRESS), abi=ERC20_ABI)
                    wbtc_bal = wbtc_contract.functions.balanceOf(acct.address).call()
                    if wbtc_bal > 0:
                        wbtc_float = wbtc_bal / 1e8
                        supply_tx = delegated_supply_wbtc_onbehalf(wallet_address, wbtc_float)
                        if supply_tx:
                            dist_results["wbtc"] = f"OK ({wbtc_float:.8f} WBTC supplied)"
                            slice_logs.append(_log_short_close_slice(wallet_address, "WBTC", SHORT_CLOSE_WBTC_PCT, "OK", weth_wbtc, wbtc_float))
                            time.sleep(2)
                        else:
                            dist_results["wbtc"] = "aave_supply_failed"
                            slice_logs.append(_log_short_close_slice(wallet_address, "WBTC", SHORT_CLOSE_WBTC_PCT, "FAILED", weth_wbtc, wbtc_float, reason="Aave supply onBehalfOf failed"))
                    else:
                        dist_results["wbtc"] = "swap_zero_output"
                        slice_logs.append(_log_short_close_slice(wallet_address, "WBTC", SHORT_CLOSE_WBTC_PCT, "FAILED", weth_wbtc, reason="swap returned zero WBTC"))
                else:
                    dist_results["wbtc"] = "swap_failed"
                    slice_logs.append(_log_short_close_slice(wallet_address, "WBTC", SHORT_CLOSE_WBTC_PCT, "FAILED", weth_wbtc, reason="WETH->WBTC swap failed"))
            except Exception as e:
                dist_results["wbtc"] = f"error: {e}"
                slice_logs.append(_log_short_close_slice(wallet_address, "WBTC", SHORT_CLOSE_WBTC_PCT, "FAILED", weth_wbtc, reason=str(e)))
                logger.error(f"[Short Close] WBTC distribution failed: {e}")
        else:
            dist_results["wbtc"] = "amount_too_small"
            slice_logs.append(_log_short_close_slice(wallet_address, "WBTC", SHORT_CLOSE_WBTC_PCT, "OK", weth_wbtc, reason="amount below threshold, skipped"))

        if weth_aave >= 0.00001:
            _log_strategy(user_id, wallet_address, "short_close", "DIST_WETH_SUPPLY", live_hf,
                          details=f"Supply {weth_aave:.8f} WETH to Aave onBehalfOf user")
            try:
                supply_tx = delegated_supply_weth_onbehalf(wallet_address, weth_aave)
                if supply_tx:
                    dist_results["weth_supply"] = f"OK ({weth_aave:.8f} WETH supplied)"
                    slice_logs.append(_log_short_close_slice(wallet_address, "WETH", SHORT_CLOSE_WETH_PCT, "OK", weth_aave, weth_aave))
                    time.sleep(2)
                else:
                    dist_results["weth_supply"] = "aave_supply_failed"
                    slice_logs.append(_log_short_close_slice(wallet_address, "WETH", SHORT_CLOSE_WETH_PCT, "FAILED", weth_aave, reason="Aave supply WETH onBehalfOf failed"))
            except Exception as e:
                dist_results["weth_supply"] = f"error: {e}"
                slice_logs.append(_log_short_close_slice(wallet_address, "WETH", SHORT_CLOSE_WETH_PCT, "FAILED", weth_aave, reason=str(e)))
                logger.error(f"[Short Close] WETH supply distribution failed: {e}")
        else:
            dist_results["weth_supply"] = "amount_too_small"
            slice_logs.append(_log_short_close_slice(wallet_address, "WETH", SHORT_CLOSE_WETH_PCT, "OK", weth_aave, reason="amount below threshold, skipped"))

        if weth_usdt >= 0.00001:
            _log_strategy(user_id, wallet_address, "short_close", "DIST_USDT", live_hf,
                          details=f"Swap {weth_usdt:.8f} WETH -> USDT -> Aave supply onBehalfOf user")
            try:
                ensure_bot_dex_approval(WETH_ADDRESS, int(weth_usdt * 1e18))
                usdt_swap = uniswap.swap_weth_for_usdt(weth_usdt)
                if usdt_swap and usdt_swap.get('tx_hash'):
                    time.sleep(3)
                    usdt_contract = w3.eth.contract(address=w3.to_checksum_address(USDT_ADDRESS), abi=ERC20_ABI)
                    usdt_bal = usdt_contract.functions.balanceOf(acct.address).call()
                    if usdt_bal > 0:
                        usdt_float = usdt_bal / 1e6
                        supply_tx = delegated_supply_usdt_onbehalf(wallet_address, usdt_float)
                        if supply_tx:
                            dist_results["usdt"] = f"OK ({usdt_float:.2f} USDT supplied)"
                            slice_logs.append(_log_short_close_slice(wallet_address, "USDT", SHORT_CLOSE_USDT_PCT, "OK", weth_usdt, usdt_float))
                            time.sleep(2)
                        else:
                            dist_results["usdt"] = "aave_supply_failed"
                            slice_logs.append(_log_short_close_slice(wallet_address, "USDT", SHORT_CLOSE_USDT_PCT, "FAILED", weth_usdt, usdt_float, reason="Aave supply USDT onBehalfOf failed"))
                    else:
                        dist_results["usdt"] = "swap_zero_output"
                        slice_logs.append(_log_short_close_slice(wallet_address, "USDT", SHORT_CLOSE_USDT_PCT, "FAILED", weth_usdt, reason="swap returned zero USDT"))
                else:
                    dist_results["usdt"] = "swap_failed"
                    slice_logs.append(_log_short_close_slice(wallet_address, "USDT", SHORT_CLOSE_USDT_PCT, "FAILED", weth_usdt, reason="WETH->USDT swap failed"))
            except Exception as e:
                dist_results["usdt"] = f"error: {e}"
                slice_logs.append(_log_short_close_slice(wallet_address, "USDT", SHORT_CLOSE_USDT_PCT, "FAILED", weth_usdt, reason=str(e)))
                logger.error(f"[Short Close] USDT distribution failed: {e}")
        else:
            dist_results["usdt"] = "amount_too_small"
            slice_logs.append(_log_short_close_slice(wallet_address, "USDT", SHORT_CLOSE_USDT_PCT, "OK", weth_usdt, reason="amount below threshold, skipped"))

        ok_count = sum(1 for v in dist_results.values() if v.startswith("OK"))
        fail_count = sum(1 for v in dist_results.values() if not v.startswith("OK") and v != "amount_too_small")

        bot_leftover_weth_raw = weth_contract.functions.balanceOf(acct.address).call()
        bot_leftover_weth = bot_leftover_weth_raw / 1e18
        if bot_leftover_weth_raw > 0:
            try:
                xfer_tx = transfer_token_to_address(wallet_address, WETH_ADDRESS, bot_leftover_weth_raw)
                if xfer_tx:
                    _log_short_close_residual(wallet_address, bot_leftover_weth, bot_leftover_weth, status="OK")
                else:
                    _log_short_close_residual(wallet_address, bot_leftover_weth, status="FAILED", reason="WETH transfer to user wallet failed")
            except Exception as e:
                _log_short_close_residual(wallet_address, bot_leftover_weth, status="FAILED", reason=str(e))
                logger.error(f"[Short Close] Residual WETH sweep failed: {e}")

        post_data = get_user_account_data(wallet_address)
        post_hf = post_data.get("healthFactor", 0) if post_data else 0

        dist_summary = ", ".join([f"{k}={v}" for k, v in dist_results.items()])
        detail_str = (f"Profit {profit_weth:.8f} WETH distributed 20/20/30/20/10. "
                     f"{ok_count}/5 OK. HF {live_hf:.2f} -> {post_hf:.2f}. {dist_summary}")

        result["executed"] = True
        result["action"] = "SHORT_CLOSE_OK" if fail_count == 0 else "SHORT_CLOSE_PARTIAL"
        result["details"] = detail_str
        result["distribution"] = dist_results

        _log_strategy(user_id, wallet_address, "short_close", result["action"], live_hf,
                      hf_after=post_hf,
                      details=f"20/20/30/20/10 split: {dist_summary}")
        _record_strategy_action(user_id, wallet_address,
                               f"SHORT CLOSE: profit={profit_weth:.8f} WETH, {ok_count}/5 dist OK, HF {live_hf:.2f} -> {post_hf:.2f}")

        if DB_AVAILABLE:
            database.record_wallet_action(
                user_id=user_id, wallet_address=wallet_address,
                action_type='strategy_short_close',
                details={"hf_before": live_hf, "hf_after": post_hf,
                         "profit_weth": profit_weth,
                         "split": "20/20/30/20/10",
                         "wallet_s_pct": 0.20, "usdc_pct": 0.20,
                         "wbtc_pct": 0.30, "weth_supply_pct": 0.20, "usdt_pct": 0.10,
                         "distribution_results": dist_results,
                         "slice_logs": slice_logs,
                         "residual_weth": bot_leftover_weth,
                         "note": "20% Wallet_S(DAI), 20% USDC(wallet), 30% WBTC(supplied), 20% WETH(supplied), 10% USDT(supplied)"},
                tx_hash=repay_tx)

        return result

    except Exception as e:
        logger.error(f"[Short Close] {wallet_address[:10]}... failed: {e}", exc_info=True)
        result["details"] = f"Short close exception: {e}"
        result["action"] = "SHORT_CLOSE_ERROR"
        return result


def run_delegated_nurse_sweep(user_id, wallet_address, agent):
    """
    Nurse Mode for delegated wallets.
    Reads user wallet balances for DAI/WETH/WBTC/USDT.
    Skips below $2 floor. NEVER touches USDC.
    Pulls via transferFrom -> supplies to Aave onBehalfOf user.

    IMPORTANT: Nurse must NOT sweep tokens if an active distribution is in progress.
    DAI is also skipped if the user has outstanding DAI debt, because that DAI
    likely came from a borrow and should go through the swap pipeline instead.
    """
    result = {"swept": False, "tokens_swept": [], "details": ""}

    if not DELEGATION_AVAILABLE:
        result["details"] = "delegation_client_unavailable"
        return result

    if has_active_distribution(wallet_address):
        result["details"] = "skipped_active_distribution"
        logger.info(f"[Nurse] {wallet_address[:10]}... SKIPPED — active distribution in progress, Nurse must not interfere")
        return result

    try:
        balances = get_multi_token_balances(wallet_address)
        if not balances:
            result["details"] = "Could not fetch user wallet balances"
            return result

        HARD_FLOOR_USD = 2.00

        from delegation_client import _get_web3
        w3 = _get_web3()
        eth_price = 2000.0
        btc_price = 67000.0
        if w3:
            try:
                oracle_addr = "0xb56c2F0B653B2e0b10C9b928C8580Ac5Df02C7C7"
                oracle_abi = [{"inputs": [{"name": "asset", "type": "address"}], "name": "getAssetPrice",
                               "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
                oracle = w3.eth.contract(address=w3.to_checksum_address(oracle_addr), abi=oracle_abi)
                eth_price = oracle.functions.getAssetPrice(w3.to_checksum_address(WETH_ADDRESS)).call() / 1e8
                btc_price = oracle.functions.getAssetPrice(w3.to_checksum_address(WBTC_TOKEN_ADDRESS)).call() / 1e8
            except Exception:
                pass

        user_has_dai_debt = False
        try:
            dai_debt = _get_dai_debt_balance(wallet_address)
            if dai_debt >= 1.0:
                user_has_dai_debt = True
                logger.debug(f"[Nurse] {wallet_address[:10]}... DAI-specific debt: ${dai_debt:.2f}")
        except Exception:
            pass

        sweep_tokens = {
            "DAI": {"address": DAI_ADDRESS, "price": 1.0, "decimals": 18,
                    "supply_fn": delegated_supply_dai_onbehalf},
            "WETH": {"address": WETH_ADDRESS, "price": eth_price, "decimals": 18,
                     "supply_fn": delegated_supply_weth_onbehalf},
            "WBTC": {"address": WBTC_TOKEN_ADDRESS, "price": btc_price, "decimals": 8,
                     "supply_fn": delegated_supply_wbtc_onbehalf},
            "USDT": {"address": USDT_ADDRESS, "price": 1.0, "decimals": 6,
                     "supply_fn": delegated_supply_usdt_onbehalf},
        }

        for token_name, config in sweep_tokens.items():
            if token_name == "DAI" and user_has_dai_debt:
                dai_data = balances.get("DAI", {})
                dai_bal = dai_data.get("balance", 0)
                if dai_bal > 0:
                    logger.info(f"[Nurse] {wallet_address[:10]}... DAI ${dai_bal:.2f} SKIPPED — user has DAI debt, DAI should go through swap pipeline")
                continue
            token_data = balances.get(token_name, {})
            balance = token_data.get("balance", 0)
            balance_raw = token_data.get("balance_raw", 0)
            usd_value = balance * config["price"]

            if balance <= 0 or balance_raw <= 0:
                continue

            if usd_value < HARD_FLOOR_USD:
                logger.info(f"[Nurse] {wallet_address[:10]}... {token_name} ${usd_value:.2f} below $2 floor — skip")
                continue

            logger.info(f"[Nurse] {wallet_address[:10]}... sweeping {balance:.8f} {token_name} (${usd_value:.2f})")

            supply_raw = int(balance_raw * 0.99)
            supply_tx = dm_execute_supply(wallet_address, config["address"], supply_raw)
            if supply_tx:
                result["swept"] = True
                result["tokens_swept"].append(f"{token_name}(${usd_value:.2f})")
                logger.info(f"[Nurse] {wallet_address[:10]}... {token_name} supplied to Aave via DM executeSupply")
                time.sleep(2)
            else:
                logger.warning(f"[Nurse] {wallet_address[:10]}... {token_name} DM executeSupply failed")

        usdc_data = balances.get("USDC", {})
        usdc_balance = usdc_data.get("balance", 0)
        if usdc_balance > 0:
            logger.info(f"[Nurse] {wallet_address[:10]}... USDC ${usdc_balance:.2f} — PROFIT TOKEN, never swept")

        if result["swept"]:
            result["details"] = f"Swept: {', '.join(result['tokens_swept'])}"
        else:
            result["details"] = "No tokens above $2 floor to sweep"

        return result

    except Exception as e:
        logger.error(f"[Nurse] {wallet_address[:10]}... sweep failed: {e}", exc_info=True)
        result["details"] = f"Nurse sweep exception: {e}"
        return result


def run_delegated_strategy(user_id, wallet_address, agent, run_id, iteration, config):
    """
    Run the strategy engine for a single delegated wallet.
    Returns a dict: {"mode": str, "action": str, "executed": bool, "details": str}

    Priority order: Emergency > Growth (6-step) > Capacity (6-step) > Macro Short > Micro Short > Idle/Skip
    One action per call. Never multiple conflicting actions.

    USER WALLET: No Profit Bucket. Short profits stay 100% in user wallet.
    """
    result = {"mode": "idle", "action": "SKIP", "executed": False, "details": ""}

    if not DB_AVAILABLE:
        result["details"] = "database_unavailable"
        return result

    if not DELEGATION_AVAILABLE:
        result["details"] = "delegation_client_unavailable"
        return result

    position = database.get_defi_position(user_id, wallet_address)
    if not position or not position.get('has_active_position', False):
        result["details"] = "no_active_position"
        _log_strategy(user_id, wallet_address, "idle", "SKIP", 0, details="no active position")
        _record_strategy_action(user_id, wallet_address, "SKIP: no active position")
        return result

    hf = float(position.get('health_factor', 0))
    collateral_usd = float(position.get('total_collateral_usd', 0))
    debt_usd = float(position.get('total_debt_usd', 0))

    perms = get_delegation_permissions(wallet_address)
    if not perms.get("isActive"):
        result["details"] = "delegation_not_active_on_chain"
        _log_strategy(user_id, wallet_address, "idle", "SKIP", hf, details="delegation not active on-chain")
        _record_strategy_action(user_id, wallet_address, "SKIP: delegation not active on-chain")
        return result

    if PERMISSIONS_AVAILABLE:
        validation = validate_full_automation(perms)
        if not validation["valid"]:
            missing = validation["missing_flags"]
            result["mode"] = "error_permissions"
            result["action"] = "SKIP"
            result["details"] = f"Permission misconfiguration: {validation['details']}"
            _log_strategy(user_id, wallet_address, "error_permissions", "SKIP", hf,
                          details=f"PERMISSION ERROR: {validation['details']} — wallet marked misconfigured")
            _record_strategy_action(user_id, wallet_address, f"ERROR: permission misconfiguration — missing: {', '.join(missing)}")
            if DB_AVAILABLE:
                database.update_strategy_status_field(user_id, wallet_address, 'error_permissions')
            return result
    else:
        can_borrow = perms.get("allowBorrow", False)
        can_supply = perms.get("allowSupply", False)
        can_repay = perms.get("allowRepay", False)
        can_withdraw = perms.get("allowWithdraw", False)
        missing = []
        if not can_supply: missing.append("allowSupply")
        if not can_borrow: missing.append("allowBorrow")
        if not can_repay: missing.append("allowRepay")
        if not can_withdraw: missing.append("allowWithdraw")
        if missing:
            result["mode"] = "error_permissions"
            result["action"] = "SKIP"
            result["details"] = f"Permission misconfiguration: missing {', '.join(missing)}"
            _log_strategy(user_id, wallet_address, "error_permissions", "SKIP", hf,
                          details=f"PERMISSION ERROR: missing {', '.join(missing)} — wallet marked misconfigured")
            _record_strategy_action(user_id, wallet_address, f"ERROR: permission misconfiguration — missing: {', '.join(missing)}")
            if DB_AVAILABLE:
                database.update_strategy_status_field(user_id, wallet_address, 'error_permissions')
            return result

    live_data = get_user_account_data(wallet_address)
    if not live_data:
        result["details"] = "aave_data_fetch_failed"
        _log_strategy(user_id, wallet_address, "idle", "SKIP", hf, details="could not fetch live Aave data")
        _record_strategy_action(user_id, wallet_address, "SKIP: Aave data fetch failed")
        return result

    available_borrows = live_data.get("availableBorrowsUSD", 0)
    live_hf = live_data.get("healthFactor", hf)

    if live_hf < EMERGENCY_HF_THRESHOLD:
        result["mode"] = "emergency"
        result["action"] = "ALERT"
        result["details"] = f"HF {live_hf:.4f} below emergency threshold {EMERGENCY_HF_THRESHOLD}"
        _log_strategy(user_id, wallet_address, "emergency", "ALERT", live_hf,
                      details=f"HF critically low! Collateral=${collateral_usd:.2f}, Debt=${debt_usd:.2f}")
        _record_strategy_action(user_id, wallet_address, f"ALERT: HF {live_hf:.4f} critically low")
        return result

    baseline = _get_wallet_baseline(user_id, wallet_address)
    if baseline <= 0:
        baseline = collateral_usd
        _update_wallet_baseline(user_id, wallet_address, baseline)

    absolute_growth = collateral_usd - baseline
    relative_growth = (absolute_growth / baseline) if baseline > 0 else 0

    growth_met = (
        live_hf >= GROWTH_HF_THRESHOLD and
        available_borrows >= GROWTH_MIN_CAPACITY_USD and
        (absolute_growth >= GROWTH_ABSOLUTE_TRIGGER_USD or relative_growth >= GROWTH_RELATIVE_TRIGGER_PCT)
    )

    if growth_met:
        borrow_amount = min(GROWTH_BORROW_USD, available_borrows * 0.9)
        if borrow_amount < 1.0:
            result["mode"] = "growth"
            result["action"] = "SKIP"
            result["details"] = f"growth triggered but borrow amount too small (${borrow_amount:.2f})"
            _log_strategy(user_id, wallet_address, "growth", "SKIP", live_hf,
                          details=f"borrow amount ${borrow_amount:.2f} too small")
            _record_strategy_action(user_id, wallet_address, f"SKIP: growth borrow too small (${borrow_amount:.2f})")
            return result

        result = _execute_delegated_distribution(user_id, wallet_address, agent, "growth", GROWTH_DISTRIBUTION, live_hf)
        if result.get("executed"):
            _update_wallet_baseline(user_id, wallet_address, collateral_usd)
        return result

    capacity_met = (
        live_hf >= CAPACITY_HF_THRESHOLD and
        available_borrows >= CAPACITY_MIN_CAPACITY_USD
    )

    if capacity_met:
        borrow_amount = min(CAPACITY_BORROW_USD, available_borrows * 0.9)
        if borrow_amount < 1.0:
            result["mode"] = "capacity"
            result["action"] = "SKIP"
            result["details"] = f"capacity triggered but borrow amount too small (${borrow_amount:.2f})"
            _log_strategy(user_id, wallet_address, "capacity", "SKIP", live_hf,
                          details=f"borrow amount ${borrow_amount:.2f} too small")
            _record_strategy_action(user_id, wallet_address, f"SKIP: capacity borrow too small (${borrow_amount:.2f})")
            return result

        result = _execute_delegated_distribution(user_id, wallet_address, agent, "capacity", CAPACITY_DISTRIBUTION, live_hf)
        return result

    skip_reasons = []
    if live_hf < GROWTH_HF_THRESHOLD:
        skip_reasons.append(f"HF {live_hf:.2f} < Growth threshold {GROWTH_HF_THRESHOLD}")
    elif absolute_growth < GROWTH_ABSOLUTE_TRIGGER_USD and relative_growth < GROWTH_RELATIVE_TRIGGER_PCT:
        skip_reasons.append(f"growth ${absolute_growth:+.2f} ({relative_growth*100:.1f}%) below triggers")
    if available_borrows < CAPACITY_MIN_CAPACITY_USD:
        skip_reasons.append(f"capacity ${available_borrows:.2f} < ${CAPACITY_MIN_CAPACITY_USD}")

    reason_str = "; ".join(skip_reasons) if skip_reasons else f"HF {live_hf:.2f} within safe band, no triggers met"
    result["mode"] = "idle"
    result["action"] = "SKIP"
    result["details"] = reason_str
    _log_strategy(user_id, wallet_address, "idle", "SKIP", live_hf, details=reason_str)
    _record_strategy_action(user_id, wallet_address, f"SKIP: {reason_str}")
    return result


def get_strategy_status(user_id, wallet_address):
    """
    Determine the strategy status for a wallet.
    Returns one of: 'active', 'disabled', 'error_permissions'

    Full automation only — no monitoring_only mode.
    """
    if not DB_AVAILABLE:
        return "disabled"

    mw = database.get_managed_wallet(user_id, wallet_address)
    if not mw:
        return "disabled"

    if mw.get('delegation_status') != 'active':
        return "disabled"

    if not database.is_bot_enabled(user_id):
        return "disabled"

    position = database.get_defi_position(user_id, wallet_address)
    if not position or not position.get('has_active_position', False):
        return "disabled"

    if DELEGATION_AVAILABLE:
        try:
            perms = get_delegation_permissions(wallet_address)
            if not perms.get("isActive"):
                return "disabled"
            if PERMISSIONS_AVAILABLE:
                validation = validate_full_automation(perms)
                if validation["valid"]:
                    return "active"
                else:
                    return "error_permissions"
            else:
                required = ["allowSupply", "allowBorrow", "allowRepay", "allowWithdraw"]
                if all(perms.get(f, False) for f in required):
                    return "active"
                else:
                    return "error_permissions"
        except Exception:
            pass

    return "disabled"
