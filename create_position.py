import os
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

class PositionCreator:
    def __init__(self):
        load_dotenv()

        # Use mainnet for real position
        self.w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))

        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise ValueError("PRIVATE_KEY not found in environment")

        self.account = Account.from_key(private_key)
        self.address = self.w3.to_checksum_address(self.account.address)

        # Arbitrum mainnet addresses
        self.aave_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.weth_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
        self.usdc_address = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

        print(f"🤖 Position Creator initialized")
        print(f"Wallet: {self.address}")
        print(f"Network: Arbitrum Mainnet")

    def get_eth_balance(self):
        """Get ETH balance"""
        balance_wei = self.w3.eth.get_balance(self.address)
        return float(self.w3.from_wei(balance_wei, 'ether'))

    def get_aave_position(self):
        """Get current Aave position"""
        aave_abi = [
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
            }
        ]

        pool_contract = self.w3.eth.contract(
            address=self.aave_pool,
            abi=aave_abi
        )

        try:
            user_data = pool_contract.functions.getUserAccountData(self.address).call()

            total_collateral_usd = user_data[0] / (10 ** 8)
            total_debt_usd = user_data[1] / (10 ** 8)
            available_borrows_usd = user_data[2] / (10 ** 8)

            if user_data[5] == 2 ** 256 - 1:
                health_factor = float('inf')
            else:
                health_factor = user_data[5] / (10 ** 18)

            return {
                'collateral': total_collateral_usd,
                'debt': total_debt_usd,
                'available_borrows': available_borrows_usd,
                'health_factor': health_factor
            }
        except Exception as e:
            print(f"❌ Error getting Aave position: {e}")
            return None

    def supply_eth_collateral(self, amount_eth):
        """Supply ETH as collateral to Aave"""
        try:
            # WETH ABI for deposit
            weth_abi = [
                {
                    "inputs": [],
                    "name": "deposit",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"internalType": "address", "name": "spender", "type": "address"},
                        {"internalType": "uint256", "name": "amount", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]

            # Aave Pool ABI for supply
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
                }
            ]

            weth_contract = self.w3.eth.contract(address=self.weth_address, abi=weth_abi)
            pool_contract = self.w3.eth.contract(address=self.aave_pool, abi=pool_abi)

            amount_wei = self.w3.to_wei(amount_eth, 'ether')

            # Step 1: Convert ETH to WETH
            print(f"🔄 Converting {amount_eth:.6f} ETH to WETH...")

            # Estimate gas costs
            current_gas_price = self.w3.eth.gas_price
            gas_limit = 100000
            estimated_fee = self.w3.from_wei(current_gas_price * gas_limit, 'ether')
            print(f"⛽ Estimated gas fee: {estimated_fee:.8f} ETH (${float(estimated_fee) * 2500:.4f})")

            nonce = self.w3.eth.get_transaction_count(self.address)

            deposit_tx = weth_contract.functions.deposit().build_transaction({
                'from': self.address,
                'value': amount_wei,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce
            })

            signed_tx = self.w3.eth.account.sign_transaction(deposit_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status != 1:
                print("❌ WETH deposit failed")
                return False

            print("✅ ETH converted to WETH")

            # Step 2: Approve WETH to Aave Pool
            print("🔄 Approving WETH to Aave Pool...")
            nonce = self.w3.eth.get_transaction_count(self.address)

            approve_tx = weth_contract.functions.approve(self.aave_pool, amount_wei).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce
            })

            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status != 1:
                print("❌ WETH approval failed")
                return False

            print("✅ WETH approved")

            # Step 3: Supply WETH to Aave
            print("🔄 Supplying WETH to Aave...")
            nonce = self.w3.eth.get_transaction_count(self.address)

            supply_tx = pool_contract.functions.supply(
                self.weth_address,
                amount_wei,
                self.address,
                0
            ).build_transaction({
                'from': self.address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce
            })

            signed_tx = self.w3.eth.account.sign_transaction(supply_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                print(f"✅ Successfully supplied {amount_eth:.6f} ETH to Aave")
                return True
            else:
                print("❌ Aave supply failed")
                return False

        except Exception as e:
            print(f"❌ Supply ETH error: {e}")
            return False

    def borrow_usdc(self, amount_usdc):
        """Borrow USDC from Aave"""
        try:
            pool_abi = [
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
                }
            ]

            pool_contract = self.w3.eth.contract(address=self.aave_pool, abi=pool_abi)

            # USDC has 6 decimals
            amount_wei = int(amount_usdc * (10 ** 6))

            print(f"🔄 Borrowing {amount_usdc:.2f} USDC...")
            nonce = self.w3.eth.get_transaction_count(self.address)

            borrow_tx = pool_contract.functions.borrow(
                self.usdc_address,
                amount_wei,
                2,  # Variable interest rate
                0,  # Referral code
                self.address
            ).build_transaction({
                'from': self.address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce
            })

            signed_tx = self.w3.eth.account.sign_transaction(borrow_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                print(f"✅ Successfully borrowed {amount_usdc:.2f} USDC")
                return True
            else:
                print("❌ USDC borrow failed")
                return False

        except Exception as e:
            print(f"❌ Borrow USDC error: {e}")
            return False

    def create_position_and_maintain_health(self):
        """Create position with 20 USDC borrow and maintain health factor > 3.5"""
        print("🚀 CREATING AAVE POSITION WITH HEALTH FACTOR > 3.5")
        print("=" * 60)

        # Check current position
        position = self.get_aave_position()
        if position and position['debt'] > 0:
            print(f"⚠️ Existing position detected:")
            print(f"   Collateral: ${position['collateral']:.2f}")
            print(f"   Debt: ${position['debt']:.2f}")
            print(f"   Health Factor: {position['health_factor']:.2f}")

            if position['health_factor'] < 3.5:
                print("🚨 Health factor below target 3.5!")
                return False
            else:
                print("✅ Health factor already above 3.5")
                return True

        # Check ETH balance
        eth_balance = self.get_eth_balance()
        print(f"💰 Current ETH Balance: {eth_balance:.6f} ETH")

        # Arbitrum has very low gas fees - 0.0001 ETH is sufficient for gas
        required_gas = 0.0001  # ~$0.25 for gas on Arbitrum
        
        if eth_balance < required_gas:
            print(f"❌ Insufficient ETH balance. Need {required_gas:.6f} ETH for gas, have {eth_balance:.6f} ETH")
            return False

        # Get existing collateral value (includes WBTC + any existing WETH)
        existing_position = self.get_aave_position()
        existing_collateral_usd = existing_position['collateral'] if existing_position else 0
        
        print(f"💰 Existing Aave Collateral: ${existing_collateral_usd:.2f}")
        
        # Calculate additional ETH collateral we'll add
        collateral_eth = eth_balance - required_gas  # Use almost all ETH, keep minimal for gas
        eth_price = 2500  # Assuming ETH = $2500
        additional_collateral_usd = collateral_eth * eth_price
        
        # Total collateral = existing + new ETH collateral
        total_collateral_usd = existing_collateral_usd + additional_collateral_usd
        ltv = 0.8  # Average LTV for WBTC/WETH
        max_safe_borrow = total_collateral_usd * ltv

        borrow_amount = 20.0  # $20 USDC target
        estimated_hf = (total_collateral_usd * ltv) / borrow_amount

        print(f"📊 Complete Position Analysis:")
        print(f"   Existing Collateral: ${existing_collateral_usd:.2f}")
        print(f"   Adding ETH Collateral: {collateral_eth:.6f} ETH (${additional_collateral_usd:.2f})")
        print(f"   Total Collateral: ${total_collateral_usd:.2f}")
        print(f"   Max Safe Borrow (80% LTV): ${max_safe_borrow:.2f}")
        print(f"   Requested Borrow: ${borrow_amount:.2f} USDC")
        print(f"   Estimated Health Factor: {estimated_hf:.2f}")

        if estimated_hf < 3.5:
            print("❌ Estimated health factor too low with total collateral!")
            # Calculate safe borrow amount using total collateral
            safe_borrow = (total_collateral_usd * ltv) / 3.5
            print(f"💡 Safe borrow amount with total collateral: ${safe_borrow:.2f}")
            borrow_amount = min(safe_borrow, 20.0)  # Don't exceed our target

        print(f"🎯 Proceeding with ${borrow_amount:.2f} USDC borrow")

        # Step 1: Supply ETH as collateral
        if not self.supply_eth_collateral(collateral_eth):
            return False

        time.sleep(5)  # Wait for confirmation

        # Step 2: Borrow USDC
        if not self.borrow_usdc(borrow_amount):
            return False

        time.sleep(5)  # Wait for confirmation

        # Step 3: Verify final position
        final_position = self.get_aave_position()
        if final_position:
            print(f"\n✅ POSITION CREATED SUCCESSFULLY!")
            print(f"   Collateral: ${final_position['collateral']:.2f}")
            print(f"   Debt: ${final_position['debt']:.2f}")
            print(f"   Health Factor: {final_position['health_factor']:.2f}")

            if final_position['health_factor'] > 3.5:
                print(f"🎉 Health factor {final_position['health_factor']:.2f} > 3.5 ✅")
                return True
            else:
                print(f"⚠️ Health factor {final_position['health_factor']:.2f} < 3.5")
                return False
        else:
            print("❌ Could not verify final position")
            return False

if __name__ == "__main__":
    try:
        creator = PositionCreator()
        success = creator.create_position_and_maintain_health()

        if success:
            print("\n🎉 SUCCESS: Position created with health factor > 3.5")
            print("🤖 Bot will now maintain this position automatically")
        else:
            print("\n❌ FAILED: Could not create safe position")

    except Exception as e:
        print(f"❌ Error: {e}")