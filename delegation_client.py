import os
import logging
from decimal import Decimal
from web3 import Web3

logger = logging.getLogger(__name__)

DELEGATION_MANAGER_ADDRESS = os.environ.get("DELEGATION_MANAGER_ADDRESS", "")

WBTC_TOKEN_ADDRESS = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
AAVE_POOL_ADDRESS = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"

WBTC_DECIMALS = 8
WBTC_UNIT = Decimal(10) ** WBTC_DECIMALS
MIN_SUPPLY_RAW = int(Decimal("0.01") * WBTC_UNIT)
MAX_SUPPLY_RATIO_NUM = 4
MAX_SUPPLY_RATIO_DEN = 5

ARBITRUM_RPCS = [
    "https://arbitrum-one.public.blastapi.io",
    "https://arb1.arbitrum.io/rpc",
    "https://arbitrum-one.publicnode.com",
]

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "success", "type": "bool"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"},
]

DELEGATION_MANAGER_ABI = [
    {"inputs": [{"name": "maxAmount", "type": "uint256"}], "name": "approveWBTCDelegation", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "revokeWBTCDelegation", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "user", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "autoSupplyWBTC", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "user", "type": "address"}], "name": "getDelegation", "outputs": [
        {"name": "isActive", "type": "bool"}, {"name": "approvedAt", "type": "uint256"}, {"name": "revokedAt", "type": "uint256"},
        {"name": "maxSupplyPerTx", "type": "uint256"}, {"name": "dailySupplyLimit", "type": "uint256"}, {"name": "dailySupplyUsed", "type": "uint256"},
        {"name": "allowSupply", "type": "bool"}, {"name": "allowBorrow", "type": "bool"}, {"name": "allowRepay", "type": "bool"}, {"name": "allowWithdraw", "type": "bool"},
    ], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "user", "type": "address"}], "name": "getDailyUsage", "outputs": [
        {"name": "used", "type": "uint256"}, {"name": "limit", "type": "uint256"}, {"name": "resetsAt", "type": "uint256"},
    ], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "paused", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "botOperator", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "owner", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
]

AAVE_POOL_SUPPLY_ABI = [
    {"inputs": [{"name": "asset", "type": "address"}, {"name": "amount", "type": "uint256"}, {"name": "onBehalfOf", "type": "address"}, {"name": "referralCode", "type": "uint16"}], "name": "supply", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
]

_w3_instance = None
_bot_account = None


def _get_web3():
    global _w3_instance
    if _w3_instance and _w3_instance.is_connected():
        return _w3_instance
    alchemy = os.getenv("ALCHEMY_RPC_URL") or os.getenv("ARBITRUM_RPC_URL")
    rpcs = ([alchemy] if alchemy else []) + ARBITRUM_RPCS
    for url in rpcs:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 10}))
            if w3.is_connected() and w3.eth.chain_id == 42161:
                _w3_instance = w3
                logger.info(f"delegation_client: connected via {url}")
                return w3
        except Exception:
            continue
    logger.error("delegation_client: all Arbitrum RPCs failed")
    return None


def _get_bot_account():
    global _bot_account
    if _bot_account:
        return _bot_account
    pk = os.getenv("BOT_PRIVATE_KEY") or os.getenv("PRIVATE_KEY") or os.getenv("Wallet_PRIVATE_KEY")
    if not pk:
        logger.error("delegation_client: no BOT_PRIVATE_KEY / PRIVATE_KEY found")
        return None
    w3 = _get_web3()
    if not w3:
        return None
    try:
        _bot_account = w3.eth.account.from_key(pk)
        logger.info(f"delegation_client: bot wallet {_bot_account.address}")
        return _bot_account
    except Exception as e:
        logger.error(f"delegation_client: invalid private key: {e}")
        return None


def is_contract_deployed() -> bool:
    if not DELEGATION_MANAGER_ADDRESS or not DELEGATION_MANAGER_ADDRESS.startswith("0x") or len(DELEGATION_MANAGER_ADDRESS) != 42:
        return False
    w3 = _get_web3()
    if not w3:
        return False
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(DELEGATION_MANAGER_ADDRESS))
        deployed = code not in (b"", b"0x", "0x")
        if not deployed:
            logger.info(f"DELEGATION_MANAGER_ADDRESS {DELEGATION_MANAGER_ADDRESS} has no bytecode on-chain")
        return deployed
    except Exception as e:
        logger.error(f"is_contract_deployed check failed: {e}")
        return False


def get_wbtc_balance_raw(wallet_address: str) -> int:
    w3 = _get_web3()
    if not w3:
        logger.warning("No Web3 — returning 0 balance")
        return 0
    try:
        wbtc = w3.eth.contract(address=Web3.to_checksum_address(WBTC_TOKEN_ADDRESS), abi=ERC20_ABI)
        balance = wbtc.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
        logger.info(f"WBTC balanceOf({wallet_address}): {balance} raw ({raw_to_wbtc(balance)} WBTC)")
        return balance
    except Exception as e:
        logger.error(f"get_wbtc_balance_raw failed for {wallet_address}: {e}")
        return 0


def get_wbtc_allowance_raw(wallet_address: str) -> int:
    if not is_contract_deployed():
        logger.info("Contract not deployed — returning 0 allowance")
        return 0
    w3 = _get_web3()
    if not w3:
        return 0
    try:
        dm_addr = Web3.to_checksum_address(DELEGATION_MANAGER_ADDRESS)
        wbtc = w3.eth.contract(address=Web3.to_checksum_address(WBTC_TOKEN_ADDRESS), abi=ERC20_ABI)
        allowance = wbtc.functions.allowance(Web3.to_checksum_address(wallet_address), dm_addr).call()
        logger.info(f"WBTC allowance({wallet_address} -> {dm_addr}): {allowance} raw ({raw_to_wbtc(allowance)} WBTC)")
        return allowance
    except Exception as e:
        logger.error(f"get_wbtc_allowance_raw failed for {wallet_address}: {e}")
        return 0


def compute_supply_amount_raw(balance_raw: int, allowance_raw: int) -> int:
    if balance_raw <= 0 or allowance_raw <= 0:
        return 0
    eighty_pct_raw = (balance_raw * MAX_SUPPLY_RATIO_NUM) // MAX_SUPPLY_RATIO_DEN
    amount_raw = min(eighty_pct_raw, allowance_raw)
    if amount_raw < MIN_SUPPLY_RAW:
        logger.info(f"Computed supply {amount_raw} raw < minimum {MIN_SUPPLY_RAW} raw — skip")
        return 0
    return amount_raw


def raw_to_wbtc(raw_amount):
    return Decimal(raw_amount) / WBTC_UNIT


def wbtc_to_raw(wbtc_amount):
    return int(Decimal(str(wbtc_amount)) * WBTC_UNIT)


def build_approve_tx(user_address: str, max_amount_raw: int) -> dict:
    if not is_contract_deployed():
        return {"error": "Delegation Manager contract not deployed"}
    w3 = _get_web3()
    if not w3:
        return {"error": "No Web3 connection"}
    dm_addr = Web3.to_checksum_address(DELEGATION_MANAGER_ADDRESS)
    wbtc = w3.eth.contract(address=Web3.to_checksum_address(WBTC_TOKEN_ADDRESS), abi=ERC20_ABI)
    user_cs = Web3.to_checksum_address(user_address)
    try:
        tx_data = wbtc.functions.approve(dm_addr, max_amount_raw).build_transaction({
            "from": user_cs,
            "gas": 60000,
            "gasPrice": w3.eth.gas_price,
            "nonce": w3.eth.get_transaction_count(user_cs),
            "chainId": 42161,
        })
        return tx_data
    except Exception as e:
        logger.error(f"build_approve_tx failed: {e}")
        return {"error": str(e)}


def call_auto_supply_wbtc(user_address: str, amount_raw: int):
    if not is_contract_deployed():
        logger.error("call_auto_supply_wbtc: contract not deployed")
        return None
    w3 = _get_web3()
    acct = _get_bot_account()
    if not w3 or not acct:
        logger.error("call_auto_supply_wbtc: missing Web3 or bot account")
        return None

    dm_addr = Web3.to_checksum_address(DELEGATION_MANAGER_ADDRESS)
    user_cs = Web3.to_checksum_address(user_address)
    dm = w3.eth.contract(address=dm_addr, abi=DELEGATION_MANAGER_ABI)

    try:
        eth_bal = w3.eth.get_balance(acct.address)
        if eth_bal < w3.to_wei(0.0002, "ether"):
            logger.error(f"Bot ETH too low for gas: {w3.from_wei(eth_bal, 'ether')} ETH")
            return None

        base_gas = w3.eth.gas_price
        gas_price = int(base_gas * 2.5)
        nonce = w3.eth.get_transaction_count(acct.address)

        try:
            est = dm.functions.autoSupplyWBTC(user_cs, amount_raw).estimate_gas({"from": acct.address})
            gas_limit = int(est * 1.3)
        except Exception as ge:
            logger.warning(f"autoSupplyWBTC gas estimate failed ({ge}), using 400000")
            gas_limit = 400000

        tx = dm.functions.autoSupplyWBTC(user_cs, amount_raw).build_transaction({
            "from": acct.address,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "nonce": nonce,
            "chainId": 42161,
        })

        signed = w3.eth.account.sign_transaction(tx, acct.key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        logger.info(f"autoSupplyWBTC tx sent: {tx_hash.hex()}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            final_hash = receipt.transactionHash.hex()
            logger.info(f"autoSupplyWBTC confirmed: {final_hash}")
            return final_hash
        else:
            logger.error(f"autoSupplyWBTC reverted: {tx_hash.hex()}")
            return None

    except Exception as e:
        logger.error(f"call_auto_supply_wbtc failed for {user_address}: {e}", exc_info=True)
        return None


def approve_delegation(wallet_address: str):
    if not is_contract_deployed():
        logger.warning("Contract not deployed — cannot approve delegation on-chain")
        return None
    return Web3.to_checksum_address(DELEGATION_MANAGER_ADDRESS)


def revoke_delegation(wallet_address: str):
    if not is_contract_deployed():
        logger.warning("Contract not deployed — cannot revoke delegation on-chain")
        return None
    return Web3.to_checksum_address(DELEGATION_MANAGER_ADDRESS)
