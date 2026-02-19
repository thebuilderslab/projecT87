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
1. EMERGENCY (HF < 2.50): Position at risk. Log critical warning, SKIP.
2. GROWTH (HF >= 3.10, collateral grew >= $50 or >= 10%, available borrows >= $13.20):
   Borrow DAI via delegation to expand position.
3. CAPACITY (HF >= 2.90, available borrows >= $8.20):
   Smaller DAI borrow to utilize idle capacity. Fires only if Growth did not.
4. MACRO SHORT (collateral velocity drop >= $50 in 30 min, HF >= 3.05):
   Hedge via WETH borrow against market downturn.
5. MICRO SHORT (collateral velocity drop >= $30 in 20 min, HF >= 3.00):
   Smaller hedge. 4h cooldown.
6. IDLE / SKIP: No conditions met. Log reason and wait for next cycle.

Inputs (all from defi_positions — single source of truth):
  - health_factor, total_collateral_usd, total_debt_usd (from DB, refreshed by monitoring)
  - available_borrows_usd (fetched live from Aave via delegation_client.get_user_account_data)
  - Delegation permissions (from on-chain getDelegation call)

One action per wallet per cycle. No double-execution.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

GROWTH_HF_THRESHOLD = 3.10
CAPACITY_HF_THRESHOLD = 2.90
MACRO_HF_THRESHOLD = 3.05
MICRO_HF_THRESHOLD = 3.00
EMERGENCY_HF_THRESHOLD = 2.50

GROWTH_MIN_CAPACITY_USD = 13.20
CAPACITY_MIN_CAPACITY_USD = 8.20

GROWTH_ABSOLUTE_TRIGGER_USD = 50.0
GROWTH_RELATIVE_TRIGGER_PCT = 0.10

GROWTH_BORROW_USD = 11.40
CAPACITY_BORROW_USD = 6.70

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
    )
    DELEGATION_AVAILABLE = True
except ImportError:
    DELEGATION_AVAILABLE = False

try:
    from permissions import FULL_AUTOMATION, REQUIRED_FLAGS, validate_full_automation
    PERMISSIONS_AVAILABLE = True
except ImportError:
    PERMISSIONS_AVAILABLE = False


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


def run_delegated_strategy(user_id, wallet_address, agent, run_id, iteration, config):
    """
    Run the strategy engine for a single delegated wallet.
    Returns a dict: {"mode": str, "action": str, "executed": bool, "details": str}

    Priority order: Emergency > Growth > Capacity > Idle/Skip
    One action per call. Never multiple conflicting actions.
    """
    result = {"mode": "idle", "action": "SKIP", "executed": False, "details": ""}

    if not DB_AVAILABLE:
        result["details"] = "database_unavailable"
        return result

    if not DELEGATION_AVAILABLE:
        result["details"] = "delegation_client_unavailable"
        return result

    position = database.get_defi_position(user_id)
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

        _log_strategy(user_id, wallet_address, "growth", "BORROW_DAI", live_hf,
                      details=f"borrowing ${borrow_amount:.2f} DAI via delegation (collateral grew ${absolute_growth:+.2f} / {relative_growth*100:.1f}%)")

        tx_hash = delegated_borrow_dai(wallet_address, borrow_amount)
        if tx_hash:
            post_data = get_user_account_data(wallet_address)
            post_hf = post_data.get("healthFactor", 0) if post_data else 0
            _log_strategy(user_id, wallet_address, "growth", "BORROW_DAI_OK", live_hf, hf_after=post_hf,
                          details=f"tx={tx_hash[:16]}..., amount=${borrow_amount:.2f}")
            _update_wallet_baseline(user_id, wallet_address, collateral_usd)
            _record_strategy_action(user_id, wallet_address, f"GROWTH: Borrowed ${borrow_amount:.2f} DAI, HF {live_hf:.2f} -> {post_hf:.2f}")
            result.update({"mode": "growth", "action": "BORROW_DAI", "executed": True,
                          "details": f"Borrowed ${borrow_amount:.2f} DAI, HF {live_hf:.2f} -> {post_hf:.2f}"})

            if DB_AVAILABLE:
                database.record_wallet_action(
                    user_id=user_id, wallet_address=wallet_address,
                    action_type='strategy_growth_borrow',
                    details={"amount_dai": borrow_amount, "hf_before": live_hf, "hf_after": post_hf,
                             "collateral_usd": collateral_usd, "growth_abs": absolute_growth, "growth_rel": relative_growth},
                    tx_hash=tx_hash)
        else:
            _log_strategy(user_id, wallet_address, "growth", "BORROW_DAI_FAILED", live_hf,
                          details=f"tx failed for ${borrow_amount:.2f} DAI")
            _record_strategy_action(user_id, wallet_address, f"FAILED: Growth borrow ${borrow_amount:.2f} DAI failed")
            result.update({"mode": "growth", "action": "BORROW_DAI_FAILED", "executed": False,
                          "details": f"Tx failed for ${borrow_amount:.2f} DAI"})
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

        _log_strategy(user_id, wallet_address, "capacity", "BORROW_DAI", live_hf,
                      details=f"borrowing ${borrow_amount:.2f} DAI via delegation (capacity=${available_borrows:.2f})")

        tx_hash = delegated_borrow_dai(wallet_address, borrow_amount)
        if tx_hash:
            post_data = get_user_account_data(wallet_address)
            post_hf = post_data.get("healthFactor", 0) if post_data else 0
            _log_strategy(user_id, wallet_address, "capacity", "BORROW_DAI_OK", live_hf, hf_after=post_hf,
                          details=f"tx={tx_hash[:16]}..., amount=${borrow_amount:.2f}")
            _record_strategy_action(user_id, wallet_address, f"CAPACITY: Borrowed ${borrow_amount:.2f} DAI, HF {live_hf:.2f} -> {post_hf:.2f}")
            result.update({"mode": "capacity", "action": "BORROW_DAI", "executed": True,
                          "details": f"Borrowed ${borrow_amount:.2f} DAI, HF {live_hf:.2f} -> {post_hf:.2f}"})

            if DB_AVAILABLE:
                database.record_wallet_action(
                    user_id=user_id, wallet_address=wallet_address,
                    action_type='strategy_capacity_borrow',
                    details={"amount_dai": borrow_amount, "hf_before": live_hf, "hf_after": post_hf,
                             "collateral_usd": collateral_usd, "available_borrows": available_borrows},
                    tx_hash=tx_hash)
        else:
            _log_strategy(user_id, wallet_address, "capacity", "BORROW_DAI_FAILED", live_hf,
                          details=f"tx failed for ${borrow_amount:.2f} DAI")
            _record_strategy_action(user_id, wallet_address, f"FAILED: Capacity borrow ${borrow_amount:.2f} DAI failed")
            result.update({"mode": "capacity", "action": "BORROW_DAI_FAILED", "executed": False,
                          "details": f"Tx failed for ${borrow_amount:.2f} DAI"})
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

    position = database.get_defi_position(user_id)
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
