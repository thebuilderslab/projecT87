from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/6ZvYzOV1E80R-bM9XgIIU'))

WALLET = "0x5B823270e3719CDe8669e5e5326B455EaA8a350b"
DAI_VDEBT = "0x8619d80FB0141ba7F184CbF22fd724116D9f7ffC"
ARB_VDEBT = "0x44705f578135cC5d703b4c9c122528C73Eb87145"

erc20_abi = [{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]

dai_debt_contract = w3.eth.contract(address=DAI_VDEBT, abi=erc20_abi)
arb_debt_contract = w3.eth.contract(address=ARB_VDEBT, abi=erc20_abi)

dai_debt = dai_debt_contract.functions.balanceOf(WALLET).call()
arb_debt = arb_debt_contract.functions.balanceOf(WALLET).call()

print("Current Debt Position:")
print("=" * 60)
print(f"DAI Variable Debt: {dai_debt / 1e18:.6f} DAI")
print(f"ARB Variable Debt: {arb_debt / 1e18:.6f} ARB")
print("=" * 60)
print()

if dai_debt < 20 * 1e18:
    print(f"⚠️  PROBLEM FOUND!")
    print(f"   We only have {dai_debt/1e18:.6f} DAI debt")
    print(f"   But trying to repay 20 DAI!")
    print(f"   This would cause the transaction to fail")
else:
    print(f"✅ Sufficient DAI debt to repay 20 DAI")

