import os
import logging
from decimal import Decimal, ROUND_DOWN

logger = logging.getLogger(__name__)

DELEGATION_MANAGER_ADDRESS = os.environ.get("DELEGATION_MANAGER_ADDRESS", "")
WBTC_TOKEN_ADDRESS = os.environ.get("WBTC_TOKEN_ADDRESS", "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")

WBTC_DECIMALS = 8
WBTC_UNIT = Decimal(10) ** WBTC_DECIMALS

MIN_SUPPLY_RAW = int(Decimal("0.01") * WBTC_UNIT)
MAX_SUPPLY_RATIO_NUM = 4
MAX_SUPPLY_RATIO_DEN = 5


def is_contract_deployed():
    return bool(DELEGATION_MANAGER_ADDRESS and DELEGATION_MANAGER_ADDRESS.startswith("0x") and len(DELEGATION_MANAGER_ADDRESS) == 42)


def get_wbtc_balance_raw(wallet_address):
    if not is_contract_deployed():
        logger.info("Delegation Manager not deployed — returning 0 balance")
        return 0
    try:
        logger.info(f"[STUB] Would read WBTC balance for {wallet_address} — contract not yet live")
        return 0
    except Exception as e:
        logger.error(f"Failed to read WBTC balance for {wallet_address}: {e}")
        return 0


def get_wbtc_allowance_raw(wallet_address):
    if not is_contract_deployed():
        logger.info("Delegation Manager not deployed — returning 0 allowance")
        return 0
    try:
        logger.info(f"[STUB] Would read WBTC allowance for {wallet_address} -> DelegationManager — contract not yet live")
        return 0
    except Exception as e:
        logger.error(f"Failed to read WBTC allowance for {wallet_address}: {e}")
        return 0


def compute_supply_amount_raw(balance_raw, allowance_raw):
    if balance_raw <= 0 or allowance_raw <= 0:
        return 0

    eighty_pct_raw = (balance_raw * MAX_SUPPLY_RATIO_NUM) // MAX_SUPPLY_RATIO_DEN

    amount_raw = min(eighty_pct_raw, allowance_raw)

    if amount_raw < MIN_SUPPLY_RAW:
        logger.info(f"Computed supply {amount_raw} raw below minimum {MIN_SUPPLY_RAW} raw — skipping")
        return 0

    return amount_raw


def raw_to_wbtc(raw_amount):
    return Decimal(raw_amount) / WBTC_UNIT


def wbtc_to_raw(wbtc_amount):
    return int(Decimal(str(wbtc_amount)) * WBTC_UNIT)


def execute_auto_supply_wbtc(wallet_address, amount_raw):
    if not is_contract_deployed():
        logger.warning("Delegation Manager not deployed — cannot execute auto-supply")
        return None

    amount_wbtc = raw_to_wbtc(amount_raw)
    try:
        logger.info(f"[STUB] Would call autoSupplyWBTC({wallet_address}, {amount_wbtc} WBTC / {amount_raw} raw) on DelegationManager at {DELEGATION_MANAGER_ADDRESS}")
        return None
    except Exception as e:
        logger.error(f"Auto-supply WBTC failed for {wallet_address}: {e}")
        return None


def approve_delegation(wallet_address):
    if not is_contract_deployed():
        logger.warning("Delegation Manager not deployed — cannot approve delegation on-chain")
        return None

    try:
        logger.info(f"[STUB] Would call approveDelegation({wallet_address}) on DelegationManager — contract not yet live")
        return None
    except Exception as e:
        logger.error(f"Approve delegation failed for {wallet_address}: {e}")
        return None


def revoke_delegation(wallet_address):
    if not is_contract_deployed():
        logger.warning("Delegation Manager not deployed — cannot revoke delegation on-chain")
        return None

    try:
        logger.info(f"[STUB] Would call revokeDelegation({wallet_address}) on DelegationManager — contract not yet live")
        return None
    except Exception as e:
        logger.error(f"Revoke delegation failed for {wallet_address}: {e}")
        return None
