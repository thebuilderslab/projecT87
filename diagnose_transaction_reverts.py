#!/usr/bin/env python3
"""
Transaction Revert Diagnostic Tool
Analyzes specific reasons why borrow transactions are reverting
"""

from arbitrum_testnet_agent import ArbitrumTestnetAgent
from web3 import Web3
from web3.exceptions import ContractLogicError
import json


def diagnose_recent_reverts():
    """Analyze recent reverted transactions"""
    print("🔍 TRANSACTION REVERT DIAGNOSTIC")
    print("=" * 50)

    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()

        print(f"📍 Wallet: {agent.address}")
        print(f"🌐 Network: {agent.network_mode}")
        print(f"⛓️ Chain ID: {agent.w3.eth.chain_id}")

        # Get recent transactions for this address
        latest_block = agent.w3.eth.block_number
        print(f"📊 Latest block: {latest_block}")

        # Analyze the failing transaction hashes from logs
        failing_txs = [
            "0x37e01d19ee4b41336a846dc1079bd75ea53730a1d35bb5f4f26363fb423e43f0",
            "0xb56e516ddf8160cc316d538802ef46247c4e61a5da5ff2b5d8fb5feda1597587",
            "0x079e4c9f9f23a7b8e85a59ff258a31d855b6336e71caab81a2ff0f935205ceee"
        ]

        for tx_hash in failing_txs:
            try:
                print(f"\n🔍 Analyzing transaction: {tx_hash}")

                # Get transaction details
                tx = agent.w3.eth.get_transaction(tx_hash)
                receipt = agent.w3.eth.get_transaction_receipt(tx_hash)

                print(
                    f"   Status: {'✅ Success' if receipt.status == 1 else '❌ Reverted'}"
                )
                print(f"   Gas used: {receipt.gasUsed:,}")
                print(f"   Gas limit: {tx.gas:,}")
                print(
                    f"   Gas price: {tx.gasPrice:,} wei ({agent.w3.from_wei(tx.gasPrice, 'gwei'):.2f} gwei)"
                )

                if receipt.status == 0:
                    # Try to get revert reason
                    try:
                        # Simulate the transaction to get revert reason
                        agent.w3.eth.call(
                            {
                                'to': tx['to'],
                                'data': tx['input'],
                                'from': tx['from'],
                                'value': tx.get('value', 0),
                                'gas': tx['gas']
                            }, receipt.blockNumber)

                    except Exception as revert_error:
                        revert_reason = str(revert_error)
                        print(f"🎯 REVERT REASON: {revert_reason}")

                        # Specific analysis
                        if "insufficient collateral" in revert_reason.lower():
                            print(
                                f"💡 ISSUE: Insufficient collateral for borrow")
                            print(
                                f"   SOLUTION: Deposit more collateral or reduce borrow amount"
                            )
                        elif "health factor" in revert_reason.lower():
                            print(f"💡 ISSUE: Health factor would be too low")
                            print(
                                f"   SOLUTION: Reduce borrow amount to maintain safe HF"
                            )
                        elif "borrowing not enabled" in revert_reason.lower():
                            print(
                                f"💡 ISSUE: Borrowing not enabled for this asset"
                            )
                            print(
                                f"   SOLUTION: Check if asset supports borrowing"
                            )
                        elif "market not active" in revert_reason.lower():
                            print(f"💡 ISSUE: Market paused or inactive")
                            print(
                                f"   SOLUTION: Wait for market to become active"
                            )
                        elif "stable borrowing not enabled" in revert_reason.lower(
                        ):
                            print(f"💡 ISSUE: Stable rate borrowing disabled")
                            print(
                                f"   SOLUTION: Use variable rate (interestRateMode=2)"
                            )
                        else:
                            print(f"💡 ISSUE: Unknown revert reason")
                            print(
                                f"   SOLUTION: Check Aave protocol documentation"
                            )

            except Exception as tx_error:
                print(f"   ❌ Could not analyze {tx_hash}: {tx_error}")

        # Check current Aave position
        print(f"\n📊 CURRENT AAVE POSITION:")
        pool_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"},
                    {"internalType": "uint16", "name": "referralCode", "type": "uint16"}
                ],
                "name": "supply",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                    {"internalType": "uint16", "name": "referralCode", "type": "uint16"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"}
                ],
                "name": "borrow",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "interestRateMode", "type": "uint256"},
                    {"internalType": "address", "name": "onBehalfOf", "type": "address"}
                ],
                "name": "repay",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "to", "type": "address"}
                ],
                "name": "withdraw",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                "name": "getUserAccountData",
                "outputs": [
                    {"internalType": "uint256", "name": "totalCollateralBase", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalDebtBase", "type": "uint256"},
                    {"internalType": "uint256", "name": "availableBorrowsBase", "type": "uint256"},
                    {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
                    {"internalType": "uint256", "name": "ltv", "type": "uint256"},
                    {"internalType": "uint256", "name": "healthFactor", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "bool", "name": "useAsCollateral", "type": "bool"}
                ],
                "name": "setUserUseReserveAsCollateral",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "uint256", "name": "categoryId", "type": "uint256"}],
                "name": "setUserEMode",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

        pool_contract = agent.w3.eth.contract(address=agent.aave_pool_address,
                                              abi=pool_abi)

        account_data = pool_contract.functions.getUserAccountData(
            agent.address).call()

        collateral_usd = account_data[0] / (10**8)
        debt_usd = account_data[1] / (10**8)
        available_borrows_usd = account_data[2] / (10**8)
        health_factor = account_data[5] / (
            10**18) if account_data[5] > 0 else float('inf')

        print(f"   Total Collateral: ${collateral_usd:.2f}")
        print(f"   Total Debt: ${debt_usd:.2f}")
        print(f"   Available Borrows: ${available_borrows_usd:.2f}")
        print(f"   Health Factor: {health_factor:.4f}")

        # Determine if position supports $10 borrow
        print(f"\n🧪 CAN BORROW $10 ANALYSIS:")
        if available_borrows_usd >= 10.0:
            print(f"✅ Available capacity supports $10 borrow")
        else:
            print(f"❌ Available capacity (${available_borrows_usd:.2f}) < $10")

        if health_factor > 2.0:
            print(
                f"✅ Health factor ({health_factor:.4f}) is safe for borrowing")
        else:
            print(f"⚠️ Health factor ({health_factor:.4f}) might be too low")

        # Test transaction simulation
        print(f"\n🧪 TRANSACTION SIMULATION TEST:")
        try:
            usdc_address = agent.usdc_address
            user_address = agent.address
            amount_wei = 10 * (10**6)  # $10 in USDC wei

            # Use .call() for simulation
            pool_contract.functions.borrow(
                Web3.to_checksum_address(usdc_address),
                amount_wei,
                2,  # Variable rate
                0,  # Referral code
                Web3.to_checksum_address(user_address)
            ).call({
                'from': Web3.to_checksum_address(user_address),
                'gas': 700000  # Increased gas limit for simulation
            })

            print(f"✅ Simulation SUCCESS - $10 borrow should work!")

        except ContractLogicError as e:
            revert_reason = str(e)
            print(f"❌ Simulation FAILED: Contract Reverted!")
            print(f"🎯 REVERT REASON: {revert_reason}")
            if "Aave/unavailable-liquidity" in revert_reason:
                print("💡 ISSUE: Insufficient liquidity in the Aave pool for the requested asset.")
                print("SOLUTION: Try borrowing a different asset or a smaller amount.")
            elif "Aave/health-factor-not-improved" in revert_reason:
                print("💡 ISSUE: Health factor would not improve or would fall below liquidation threshold.")
                print("SOLUTION: Provide more collateral or reduce the borrow amount.")
            elif "Aave/too-small-borrow" in revert_reason:
                print("💡 ISSUE: Attempted to borrow an amount smaller than the protocol's minimum.")
                print("SOLUTION: Increase the borrow amount.")
            elif "Aave/" in revert_reason: # Catch other Aave-specific reverts
                # This attempts to parse the Aave error code if present
                try:
                    aave_error_code = revert_reason.split('Aave/')[1].split(':')[0].strip()
                    print(f"💡 ISSUE: Aave Protocol specific error: {aave_error_code}")
                except IndexError:
                    print("💡 ISSUE: Generic Aave Protocol error (could not parse specific code).")
                print("SOLUTION: Consult Aave documentation for this specific error or condition.")
            else:
                print("💡 ISSUE: Generic contract execution reverted.")
                print("SOLUTION: Review contract state, Aave documentation, or debug further.")
        except Exception as e:
            print(f"❌ Simulation FAILED: {e}")
            print("💡 ISSUE: Unexpected error during simulation.")
            print("SOLUTION: Check environment or RPC connection.")

    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")


if __name__ == "__main__":
    diagnose_recent_reverts()
