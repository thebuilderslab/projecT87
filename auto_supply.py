import logging
from datetime import datetime, timezone, timedelta
import db as database
from delegation_client import (
    is_contract_deployed,
    get_wbtc_balance_raw,
    get_wbtc_allowance_raw,
    compute_supply_amount_raw,
    execute_auto_supply_wbtc,
    raw_to_wbtc,
    MIN_SUPPLY_RAW,
)

logger = logging.getLogger(__name__)

ONE_DAY = timedelta(days=1)


def auto_supply_wbtc_for_wallet(managed_wallet):
    user_id = managed_wallet['user_id']
    wallet = managed_wallet['wallet_address']

    if not managed_wallet.get('bot_enabled', False):
        logger.debug(f"Bot disabled for user {user_id} — skipping auto-supply")
        return False

    if managed_wallet['delegation_status'] != 'active':
        logger.debug(f"Delegation not active for {wallet} — skipping")
        return False
    if not managed_wallet.get('auto_supply_wbtc', False):
        logger.debug(f"auto_supply_wbtc=false for {wallet} — skipping")
        return False

    last_supply = managed_wallet.get('last_auto_supply_at')
    if last_supply:
        if isinstance(last_supply, str):
            last_supply = datetime.fromisoformat(last_supply)
        if last_supply.tzinfo is None:
            last_supply = last_supply.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - last_supply < ONE_DAY:
            logger.info(f"Already supplied within 24h for {wallet} (last: {last_supply}) — skipping")
            return False

    if not is_contract_deployed():
        logger.info(f"Delegation Manager contract not deployed — skipping auto-supply for {wallet}")
        return False

    balance_raw = get_wbtc_balance_raw(wallet)
    allowance_raw = get_wbtc_allowance_raw(wallet)

    amount_raw = compute_supply_amount_raw(balance_raw, allowance_raw)
    if amount_raw <= 0:
        logger.info(f"No viable supply amount for {wallet} (balance_raw={balance_raw}, allowance_raw={allowance_raw})")
        return False

    amount_wbtc = raw_to_wbtc(amount_raw)
    logger.info(f"Executing auto-supply of {amount_wbtc} WBTC ({amount_raw} raw) for {wallet}")

    tx_hash = execute_auto_supply_wbtc(wallet, amount_raw)

    if tx_hash is None:
        database.record_wallet_action(
            user_id=user_id,
            wallet_address=wallet,
            action_type='auto_supply_failed',
            details={
                "amount_wbtc": str(amount_wbtc),
                "amount_raw": str(amount_raw),
                "balance_raw": str(balance_raw),
                "allowance_raw": str(allowance_raw),
                "reason": "tx_not_submitted",
            },
            tx_hash=None,
        )
        logger.warning(f"Auto-supply tx not submitted for {wallet} — no DB update")
        return False

    database.record_wallet_action(
        user_id=user_id,
        wallet_address=wallet,
        action_type='auto_supply',
        details={
            "amount_wbtc": str(amount_wbtc),
            "amount_raw": str(amount_raw),
            "balance_raw": str(balance_raw),
            "allowance_raw": str(allowance_raw),
        },
        tx_hash=tx_hash,
    )

    database.update_managed_wallet_supplied(user_id, wallet, float(amount_wbtc))

    logger.info(f"Auto-supply complete for {wallet}: {amount_wbtc} WBTC, tx={tx_hash}")
    return True


def run_auto_supply_cycle():
    if not is_contract_deployed():
        logger.debug("Delegation Manager not deployed — skipping auto-supply cycle")
        return 0

    wallets = database.get_active_managed_wallets()
    if not wallets:
        logger.debug("No active managed wallets for auto-supply")
        return 0

    supplied_count = 0
    for mw in wallets:
        try:
            if auto_supply_wbtc_for_wallet(mw):
                supplied_count += 1
        except Exception as e:
            logger.error(f"Auto-supply error for wallet {mw.get('wallet_address', '?')}: {e}", exc_info=True)

    if supplied_count > 0:
        logger.info(f"Auto-supply cycle complete: {supplied_count}/{len(wallets)} wallets supplied")
    return supplied_count
