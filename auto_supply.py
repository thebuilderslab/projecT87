import logging
from datetime import datetime, timezone, timedelta
import db as database
from delegation_client import (
    is_contract_deployed,
    get_wbtc_balance_raw,
    get_wbtc_allowance_raw,
    compute_supply_amount_raw,
    call_auto_supply_wbtc,
    raw_to_wbtc,
    MIN_SUPPLY_RAW,
)

logger = logging.getLogger(__name__)

ONE_DAY = timedelta(days=1)
WBTC_DECIMALS = 8


def auto_supply_wbtc_for_wallet(managed_wallet):
    user_id = managed_wallet['user_id']
    wallet = managed_wallet['wallet_address']

    if not managed_wallet.get('bot_enabled', False):
        logger.debug(f"bot_enabled=false for user {user_id} — skip")
        return False

    if managed_wallet['delegation_status'] != 'active':
        logger.debug(f"delegation_status={managed_wallet['delegation_status']} for {wallet} — skip")
        return False
    if not managed_wallet.get('auto_supply_wbtc', False):
        logger.debug(f"auto_supply_wbtc=false for {wallet} — skip")
        return False

    last_supply = managed_wallet.get('last_auto_supply_at')
    if last_supply:
        if isinstance(last_supply, str):
            last_supply = datetime.fromisoformat(last_supply)
        if last_supply.tzinfo is None:
            last_supply = last_supply.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - last_supply < ONE_DAY:
            logger.info(f"Supplied within 24h for {wallet} (last: {last_supply}) — skip")
            return False

    if not is_contract_deployed():
        logger.info(f"Delegation Manager not deployed — skip auto-supply for {wallet}")
        database.record_wallet_action(
            user_id=user_id,
            wallet_address=wallet,
            action_type='auto_supply_skipped_contract',
            details={"reason": "delegation_manager_not_deployed"},
            tx_hash=None,
        )
        return False

    balance_raw = get_wbtc_balance_raw(wallet)
    allowance_raw = get_wbtc_allowance_raw(wallet)

    amount_raw = compute_supply_amount_raw(balance_raw, allowance_raw)
    if amount_raw <= 0:
        logger.info(f"No viable supply for {wallet} (balance_raw={balance_raw}, allowance_raw={allowance_raw})")
        database.record_wallet_action(
            user_id=user_id,
            wallet_address=wallet,
            action_type='auto_supply_skipped_amount',
            details={
                "balance_raw": str(balance_raw),
                "allowance_raw": str(allowance_raw),
                "computed_amount_raw": "0",
                "reason": "insufficient_balance_or_allowance",
            },
            tx_hash=None,
        )
        return False

    amount_wbtc = float(raw_to_wbtc(amount_raw))
    logger.info(f"Executing auto-supply: {amount_wbtc} WBTC ({amount_raw} raw) for {wallet}")

    tx_hash = call_auto_supply_wbtc(wallet, amount_raw)

    if tx_hash is None:
        database.record_wallet_action(
            user_id=user_id,
            wallet_address=wallet,
            action_type='auto_supply_failed',
            details={
                "amount_wbtc": amount_wbtc,
                "amount_raw": int(amount_raw),
                "balance_raw": str(balance_raw),
                "allowance_raw": str(allowance_raw),
                "reason": "tx_failed_or_not_submitted",
            },
            tx_hash=None,
        )
        logger.warning(f"auto-supply tx failed for {wallet} — DB not updated")
        return False

    database.record_wallet_action(
        user_id=user_id,
        wallet_address=wallet,
        action_type='auto_supply_wbtc',
        details={
            "amount_raw": int(amount_raw),
            "amount_wbtc": amount_wbtc,
        },
        tx_hash=tx_hash,
    )
    database.update_managed_wallet_supplied(user_id, wallet, amount_wbtc)

    logger.info(f"Auto-supply complete for {wallet}: {amount_wbtc} WBTC, tx={tx_hash}")
    return True


def run_auto_supply_cycle():
    if not is_contract_deployed():
        logger.debug("Delegation Manager not deployed — skip auto-supply cycle")
        return 0

    wallets = database.get_active_managed_wallets()
    if not wallets:
        logger.debug("No active managed wallets for auto-supply")
        return 0

    supplied = 0
    for mw in wallets:
        try:
            if auto_supply_wbtc_for_wallet(mw):
                supplied += 1
        except Exception as e:
            logger.error(f"Auto-supply error for {mw.get('wallet_address', '?')}: {e}", exc_info=True)

    if supplied > 0:
        logger.info(f"Auto-supply cycle: {supplied}/{len(wallets)} wallets supplied")
    return supplied
