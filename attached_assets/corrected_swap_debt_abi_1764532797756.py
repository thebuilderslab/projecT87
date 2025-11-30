#!/usr/bin/env python3
"""
Corrected Aave Debt Switch V3 ABI for swapDebt() function
Based on successful on-chain transactions analysis
Contract: 0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4
Function Selector: 0xb8bd1c6b
"""

# CORRECT ABI for swapDebt function
# Signature: swapDebt((address,uint256,uint256,address,uint256,address,uint256,uint256,bytes),(address,uint256,uint256,uint8,bytes32,bytes32),(address,uint256,uint256,uint8,bytes32,bytes32))
DEBT_SWITCH_SWAP_DEBT_ABI = [{
    "inputs": [
        {
            "components": [
                {"internalType": "address", "name": "debtAsset", "type": "address"},
                {"internalType": "uint256", "name": "debtRepayAmount", "type": "uint256"},
                {"internalType": "uint256", "name": "debtRateMode", "type": "uint256"},
                {"internalType": "address", "name": "newDebtAsset", "type": "address"},
                {"internalType": "uint256", "name": "maxNewDebtAmount", "type": "uint256"},
                {"internalType": "address", "name": "extraCollateralAsset", "type": "address"},
                {"internalType": "uint256", "name": "extraCollateralAmount", "type": "uint256"},
                {"internalType": "uint256", "name": "offset", "type": "uint256"},
                {"internalType": "bytes", "name": "paraswapData", "type": "bytes"}
            ],
            "internalType": "struct IParaSwapDebtSwapAdapter.DebtSwapParams",
            "name": "debtSwapParams",
            "type": "tuple"
        },
        {
            "components": [
                {"internalType": "address", "name": "debtToken", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                {"internalType": "uint8", "name": "v", "type": "uint8"},
                {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                {"internalType": "bytes32", "name": "s", "type": "bytes32"}
            ],
            "internalType": "struct IParaSwapDebtSwapAdapter.CreditDelegationInput",
            "name": "creditDelegationPermit",
            "type": "tuple"
        },
        {
            "components": [
                {"internalType": "address", "name": "aToken", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                {"internalType": "uint8", "name": "v", "type": "uint8"},
                {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                {"internalType": "bytes32", "name": "s", "type": "bytes32"}
            ],
            "internalType": "struct IBaseParaSwapAdapter.PermitInput",
            "name": "collateralATokenPermit",
            "type": "tuple"
        }
    ],
    "name": "swapDebt",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

# Contract address
DEBT_SWITCH_V3_ADDRESS = "0x63dfa7c09Dc2Ff4030d6B8Dc2ce6262BF898C8A4"

# Key addresses on Arbitrum
ARBITRUM_ADDRESSES = {
    "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
    "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
    "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    
    # Aave V3 tokens
    "aArbDAI": "0x82E64f49Ed5EC1bC6e43DAD4FC8Af9bb3A2312EE",
    "aArbWETH": "0xe50fA9b3c56FfB159cB0FCA61F5c9D750e8128c8",
    
    # Debt tokens
    "variableDebtArbDAI": "0x8619d80FB0141ba7F184CbF22fd724116D9f7ffC",
    "variableDebtArbWETH": "0x0c84331e39d6658Cd6e6b9ba04736cC4c4734351",
    
    # ParaSwap
    "AUGUSTUS_V6_2": "0x6A000F20005980200259B80c5102003040001068",
}

def get_empty_permit():
    """Return empty permit structure (all zeros)"""
    return {
        "aToken": "0x0000000000000000000000000000000000000000",
        "value": 0,
        "deadline": 0,
        "v": 0,
        "r": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "s": "0x0000000000000000000000000000000000000000000000000000000000000000"
    }

def get_empty_credit_delegation_permit():
    """Return empty credit delegation permit (all zeros)"""
    return {
        "debtToken": "0x0000000000000000000000000000000000000000",
        "value": 0,
        "deadline": 0,
        "v": 0,
        "r": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "s": "0x0000000000000000000000000000000000000000000000000000000000000000"
    }

if __name__ == "__main__":
    from web3 import Web3
    
    w3 = Web3()
    
    # Verify function selector
    signature = "swapDebt((address,uint256,uint256,address,uint256,address,uint256,uint256,bytes),(address,uint256,uint256,uint8,bytes32,bytes32),(address,uint256,uint256,uint8,bytes32,bytes32))"
    selector = w3.keccak(text=signature)[:4].hex()
    
    print("=" * 80)
    print("CORRECTED DEBT SWITCH ABI VERIFICATION")
    print("=" * 80)
    print(f"Contract: {DEBT_SWITCH_V3_ADDRESS}")
    print(f"Function Signature:")
    print(f"  {signature}")
    print()
    print(f"Expected Selector: 0xb8bd1c6b")
    print(f"Computed Selector: {selector}")
    print(f"Match: {'✅ YES - CORRECT!' if selector == '0xb8bd1c6b' else '❌ NO'}")
    print()
    print("=" * 80)
    print("PARAMETER STRUCTURE:")
    print("=" * 80)
    print("1. debtSwapParams (tuple with 9 fields):")
    print("   - debtAsset: address of debt to repay (e.g., DAI)")
    print("   - debtRepayAmount: amount to repay in wei")
    print("   - debtRateMode: 2 for variable rate")
    print("   - newDebtAsset: address of new debt (e.g., WETH)")
    print("   - maxNewDebtAmount: maximum new debt amount in wei")
    print("   - extraCollateralAsset: 0x0 (not used)")
    print("   - extraCollateralAmount: 0 (not used)")
    print("   - offset: 0 (not used)")
    print("   - paraswapData: encoded swap calldata from ParaSwap API")
    print()
    print("2. creditDelegationPermit (tuple with 6 fields):")
    print("   - debtToken: variable debt token address")
    print("   - value: credit delegation amount")
    print("   - deadline: permit deadline timestamp")
    print("   - v: signature v")
    print("   - r: signature r")
    print("   - s: signature s")
    print()
    print("3. collateralATokenPermit (tuple with 6 fields):")
    print("   - All zeros (not needed for debt swaps)")
    print("=" * 80)
