"""
Delegation Permissions Audit & Full-Automation Profile
======================================================
Derived from a full audit of the strategy engine, delegation client,
and auto-supply modules. Any new strategy or token MUST update these
tables.

On-chain contract: REAADelegationManager (Arbitrum mainnet)
  Address: 0x7427370Ab4C311B090446544078c819b3946E59d
  Flags are WALLET-LEVEL (single set per wallet, not per-token).

Audit date: 2026-02-19
"""

WBTC_ADDRESS = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
DAI_ADDRESS  = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
WETH_ADDRESS = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
USDC_ADDRESS = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

TOKEN_PERMISSIONS = {
    "WBTC": {
        "address": WBTC_ADDRESS,
        "decimals": 8,
        "can_monitor": True,
        "can_supply": True,
        "can_borrow": False,
        "can_repay": False,
        "can_withdraw": False,
        "used_by": ["auto_supply"],
        "notes": "Primary collateral. Auto-supplied on delegation activation.",
    },
    "DAI": {
        "address": DAI_ADDRESS,
        "decimals": 18,
        "can_monitor": True,
        "can_supply": False,
        "can_borrow": True,
        "can_repay": True,
        "can_withdraw": False,
        "used_by": ["growth", "capacity", "nurse_repay"],
        "notes": "Borrowed by Growth and Capacity strategies. Repaid by Nurse mode.",
    },
    "WETH": {
        "address": WETH_ADDRESS,
        "decimals": 18,
        "can_monitor": True,
        "can_supply": False,
        "can_borrow": True,
        "can_repay": True,
        "can_withdraw": False,
        "used_by": ["macro_short", "micro_short"],
        "notes": "Borrowed by Macro/Micro short hedge strategies.",
    },
    "USDC": {
        "address": USDC_ADDRESS,
        "decimals": 6,
        "can_monitor": True,
        "can_supply": False,
        "can_borrow": False,
        "can_repay": False,
        "can_withdraw": False,
        "used_by": [],
        "notes": "Profit token. User claims via Dashboard. NEVER swept by bot.",
    },
}

FULL_AUTOMATION = {
    "isActive": True,
    "allowSupply": True,
    "allowBorrow": True,
    "allowRepay": True,
    "allowWithdraw": True,
}

REQUIRED_FLAGS = ["allowSupply", "allowBorrow", "allowRepay", "allowWithdraw"]

STRATEGY_MAP = {
    "growth": {
        "description": "Borrow DAI when collateral appreciates significantly",
        "hf_threshold": 3.10,
        "tokens": ["DAI"],
        "actions": ["borrow"],
        "required_flags": ["allowBorrow"],
    },
    "capacity": {
        "description": "Smaller DAI borrow to utilize idle borrowing capacity",
        "hf_threshold": 2.90,
        "tokens": ["DAI"],
        "actions": ["borrow"],
        "required_flags": ["allowBorrow"],
    },
    "macro_short": {
        "description": "Hedge via WETH borrow against major market downturn",
        "hf_threshold": 3.05,
        "tokens": ["WETH"],
        "actions": ["borrow"],
        "required_flags": ["allowBorrow"],
    },
    "micro_short": {
        "description": "Smaller WETH hedge against minor market dip",
        "hf_threshold": 3.00,
        "tokens": ["WETH"],
        "actions": ["borrow"],
        "required_flags": ["allowBorrow"],
    },
    "auto_supply": {
        "description": "Auto-supply WBTC to Aave on delegation activation",
        "hf_threshold": None,
        "tokens": ["WBTC"],
        "actions": ["supply"],
        "required_flags": ["allowSupply"],
    },
    "emergency": {
        "description": "Alert when HF drops below emergency threshold",
        "hf_threshold": 2.50,
        "tokens": [],
        "actions": ["alert"],
        "required_flags": [],
    },
}


def validate_full_automation(on_chain_perms: dict) -> dict:
    """
    Compare on-chain permissions against the FULL_AUTOMATION profile.
    Returns {"valid": True/False, "missing_flags": [...], "details": str}
    """
    if not on_chain_perms.get("isActive"):
        return {
            "valid": False,
            "missing_flags": ["isActive"],
            "details": "Delegation not active on-chain",
        }

    missing = []
    for flag in REQUIRED_FLAGS:
        if not on_chain_perms.get(flag, False):
            missing.append(flag)

    if missing:
        return {
            "valid": False,
            "missing_flags": missing,
            "details": f"Missing permissions: {', '.join(missing)}",
        }

    return {"valid": True, "missing_flags": [], "details": "Full automation verified"}
