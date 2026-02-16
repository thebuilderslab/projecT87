#!/usr/bin/env python3
"""
Liability Short Strategy — Phase 1 Implementation
Shorts ETH debt (borrowed against total wallet collateral) to hedge against market drops.

COMPOSITE SEQUENCE:
  Part A: Leveraged Entry — Borrow WETH, distribute (WBTC supply, WETH supply, DAI supply, DAI transfer, ETH gas)
  Part B: Liability Hedge — Swap existing DAI debt to WETH debt via BidirectionalDebtSwapper

DUAL TRIGGERS (Conservative USDC Mode):
  Macro Entry: Collateral drop >5% + HF >3.05 → Full position ($10.90 borrow + $10.80 debt swap)
  Micro Entry: Collateral drop >2% + HF >3.00 → Partial position ($7.20 borrow + $10.10 debt swap)

EXIT:
  ETH price recovers >2% from entry → WETH→DAI debt swap to lock in reduced liability
"""

import os
import json
import time
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

POSITIONS_FILE = "debt_swap_positions.json"

MACRO_DISTRIBUTION = {
    'total_borrow_usd': 10.90 + 1.20,
    'wbtc_swap_supply': 2.10,
    'weth_supply': 2.10,
    'dai_swap_total': 5.60,
    'dai_supply': 4.50,
    'dai_transfer': 1.10,
    'eth_gas_reserve': 1.10,
    'debt_swap_amount': 10.80,
    'usdc_tax': 1.20,
    'min_capacity': 13.0 + 1.20,
}

MICRO_DISTRIBUTION = {
    'total_borrow_usd': 7.20 + 1.20,
    'wbtc_swap_supply': 1.10,
    'weth_supply': 1.10,
    'dai_swap_total': 3.90,
    'dai_supply': 2.80,
    'dai_transfer': 1.10,
    'eth_gas_reserve': 1.10,
    'debt_swap_amount': 10.10,
    'usdc_tax': 1.20,
    'min_capacity': 9.0 + 1.20,
}

MACRO_TRIGGER = {
    'collateral_drop_pct': 5.0,
    'min_health_factor': 3.05,
}

MICRO_TRIGGER = {
    'collateral_drop_pct': 2.0,
    'min_health_factor': 3.00,
}

EXIT_TRIGGER = {
    'eth_recovery_pct': 2.0,
    'min_health_factor': 2.90,
}

LIABILITY_SHORT_STEP_ORDER = [
    "weth_borrowed",
    "wbtc_swapped_supplied",
    "weth_supplied",
    "dai_swapped",
    "dai_supplied",
    "eth_gas_converted",
    "dai_transferred",
    "part_a_complete",
    "debt_swap_complete",
]

DEBT_SWAP_COOLDOWN_SECONDS = 600


class LiabilityShortStrategy:
    def __init__(self, agent):
        self.agent = agent
        self.positions = self._load_positions()
        self.last_collateral_snapshot = None
        self.last_collateral_snapshot_time = 0
        self.collateral_history = []
        self.max_history = 60
        logger.info("Liability Short Strategy initialized")

    def _load_positions(self) -> Dict:
        try:
            if os.path.exists(POSITIONS_FILE):
                with open(POSITIONS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading positions: {e}")
        return {"positions": [], "active_position": None}

    def _save_positions(self):
        try:
            with open(POSITIONS_FILE, 'w') as f:
                json.dump(self.positions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving positions: {e}")

    def has_active_position(self) -> bool:
        return self.positions.get("active_position") is not None

    def has_partial_position(self) -> bool:
        active = self.positions.get("active_position")
        if active and active.get("status") == "partial":
            return True
        return False

    def get_active_position(self) -> Optional[Dict]:
        return self.positions.get("active_position")

    def get_eth_price(self) -> Optional[float]:
        try:
            if hasattr(self.agent, 'market_signal_strategy') and self.agent.market_signal_strategy:
                strategy = self.agent.market_signal_strategy
                if hasattr(strategy, 'enhanced_analyzer') and strategy.enhanced_analyzer:
                    analyzer = strategy.enhanced_analyzer
                    if hasattr(analyzer, 'get_market_summary'):
                        summary = analyzer.get_market_summary()
                        if summary and not summary.get('error'):
                            eth_analysis = summary.get('eth_analysis', {})
                            price = eth_analysis.get('price')
                            if price and price > 0:
                                return float(price)

            if hasattr(self.agent, 'get_eth_price_usd'):
                price = self.agent.get_eth_price_usd()
                if price and price > 0:
                    return float(price)

            if hasattr(self.agent, 'aave') and self.agent.aave:
                account_data = self.agent.aave.get_user_account_data()
                if account_data:
                    return None
        except Exception as e:
            logger.error(f"Error fetching ETH price: {e}")
        return None

    def record_collateral_snapshot(self, collateral_usd: float):
        now = time.time()
        self.collateral_history.append({
            'value': collateral_usd,
            'timestamp': now
        })
        if len(self.collateral_history) > self.max_history:
            self.collateral_history.pop(0)
        self.last_collateral_snapshot = collateral_usd
        self.last_collateral_snapshot_time = now

    def get_collateral_drop_pct(self, current_collateral: float) -> float:
        baseline = getattr(self.agent, 'last_collateral_value_usd', 0)
        if baseline <= 0:
            return 0.0
        drop = baseline - current_collateral
        if drop <= 0:
            return 0.0
        return (drop / baseline) * 100.0

    def get_trigger_levels(self) -> Dict:
        baseline = getattr(self.agent, 'last_collateral_value_usd', 0)
        if baseline <= 0:
            return {"micro_trigger_usd": 0, "macro_trigger_usd": 0, "baseline": 0}
        micro_trigger_usd = baseline * (1.0 - MICRO_TRIGGER['collateral_drop_pct'] / 100.0)
        macro_trigger_usd = baseline * (1.0 - MACRO_TRIGGER['collateral_drop_pct'] / 100.0)
        return {
            "micro_trigger_usd": round(micro_trigger_usd, 2),
            "macro_trigger_usd": round(macro_trigger_usd, 2),
            "baseline": round(baseline, 2),
        }

    def check_macro_entry(self, current_collateral: float, health_factor: float) -> Tuple[bool, str]:
        if self.has_active_position():
            return False, "Position already active — cannot open new entry"

        if self._is_on_cooldown():
            return False, "Debt swap on cooldown"

        levels = self.get_trigger_levels()
        macro_target = levels["macro_trigger_usd"]
        if macro_target <= 0:
            return False, "Baseline not set — cannot evaluate macro trigger"

        if current_collateral >= macro_target:
            drop_pct = self.get_collateral_drop_pct(current_collateral)
            return False, f"Collateral ${current_collateral:.2f} above macro target ${macro_target:.2f} (drop {drop_pct:.1f}%)"

        if health_factor < MACRO_TRIGGER['min_health_factor']:
            return False, f"HF {health_factor:.3f} < {MACRO_TRIGGER['min_health_factor']} minimum"

        if health_factor < 2.90:
            return False, f"HF {health_factor:.3f} below absolute floor 2.90"

        drop_pct = self.get_collateral_drop_pct(current_collateral)
        return True, f"MACRO ENTRY: Collateral ${current_collateral:.2f} < ${macro_target:.2f} target (drop {drop_pct:.1f}%), HF {health_factor:.3f} (>{MACRO_TRIGGER['min_health_factor']})"

    def check_micro_entry(self, current_collateral: float, health_factor: float) -> Tuple[bool, str]:
        if self.has_active_position():
            return False, "Position already active — cannot open new entry"

        if self._is_on_cooldown():
            return False, "Debt swap on cooldown"

        levels = self.get_trigger_levels()
        micro_target = levels["micro_trigger_usd"]
        if micro_target <= 0:
            return False, "Baseline not set — cannot evaluate micro trigger"

        if current_collateral >= micro_target:
            drop_pct = self.get_collateral_drop_pct(current_collateral)
            return False, f"Collateral ${current_collateral:.2f} above micro target ${micro_target:.2f} (drop {drop_pct:.1f}%)"

        if health_factor < MICRO_TRIGGER['min_health_factor']:
            return False, f"HF {health_factor:.3f} < {MICRO_TRIGGER['min_health_factor']} minimum"

        if health_factor < 2.90:
            return False, f"HF {health_factor:.3f} below absolute floor 2.90"

        drop_pct = self.get_collateral_drop_pct(current_collateral)
        return True, f"MICRO ENTRY: Collateral ${current_collateral:.2f} < ${micro_target:.2f} target (drop {drop_pct:.1f}%), HF {health_factor:.3f} (>{MICRO_TRIGGER['min_health_factor']})"

    def check_exit_trigger(self) -> Tuple[bool, str]:
        active = self.get_active_position()
        if not active:
            return False, "No active position to exit"

        if active.get("status") != "active":
            return False, f"Position status is '{active.get('status')}', not 'active'"

        entry_eth_price = active.get("entry_eth_price", 0)
        if entry_eth_price <= 0:
            return False, "No entry ETH price recorded"

        current_eth_price = self.get_eth_price()
        if not current_eth_price:
            return False, "Cannot fetch current ETH price"

        recovery_pct = ((current_eth_price - entry_eth_price) / entry_eth_price) * 100
        if recovery_pct < EXIT_TRIGGER['eth_recovery_pct']:
            return False, f"ETH recovery {recovery_pct:.1f}% < {EXIT_TRIGGER['eth_recovery_pct']}% threshold (entry: ${entry_eth_price:.2f}, current: ${current_eth_price:.2f})"

        return True, f"EXIT TRIGGER: ETH recovered {recovery_pct:.1f}% from ${entry_eth_price:.2f} to ${current_eth_price:.2f}"

    def open_position(self, tier: str, entry_eth_price: float, borrow_amount_usd: float, debt_swap_amount: float):
        position = {
            "id": f"ls_{int(time.time())}",
            "tier": tier,
            "status": "active",
            "entry_eth_price": entry_eth_price,
            "borrow_amount_usd": borrow_amount_usd,
            "debt_swap_amount": debt_swap_amount,
            "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "opened_timestamp": time.time(),
            "closed_at": None,
            "exit_eth_price": None,
            "pnl_usd": None,
        }
        self.positions["active_position"] = position
        self.positions["positions"].append(position)
        self._save_positions()
        logger.info(f"Opened {tier} liability short position at ETH ${entry_eth_price:.2f}")

    def mark_partial(self, tier: str, entry_eth_price: float, borrow_amount_usd: float, debt_swap_amount: float, reason: str):
        position = {
            "id": f"ls_{int(time.time())}",
            "tier": tier,
            "status": "partial",
            "entry_eth_price": entry_eth_price,
            "borrow_amount_usd": borrow_amount_usd,
            "debt_swap_amount": debt_swap_amount,
            "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "opened_timestamp": time.time(),
            "partial_reason": reason,
            "closed_at": None,
            "exit_eth_price": None,
            "pnl_usd": None,
        }
        self.positions["active_position"] = position
        self.positions["positions"].append(position)
        self._save_positions()
        logger.warning(f"Marked {tier} position as PARTIAL: {reason}")

    def close_position(self, exit_eth_price: float):
        active = self.positions.get("active_position")
        if not active:
            return

        entry_price = active.get("entry_eth_price", 0)
        debt_swap_amt = active.get("debt_swap_amount", 0)

        if entry_price > 0 and exit_eth_price > 0:
            price_change_pct = ((exit_eth_price - entry_price) / entry_price)
            pnl_estimate = debt_swap_amt * price_change_pct
        else:
            pnl_estimate = 0

        active["status"] = "closed"
        active["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        active["exit_eth_price"] = exit_eth_price
        active["pnl_usd"] = round(pnl_estimate, 4)

        for p in self.positions["positions"]:
            if p.get("id") == active.get("id"):
                p.update(active)
                break

        self.positions["active_position"] = None
        self._save_positions()
        logger.info(f"Closed position: entry ${entry_price:.2f} → exit ${exit_eth_price:.2f}, P&L ~${pnl_estimate:.4f}")

    def _is_on_cooldown(self) -> bool:
        last_op_time = getattr(self.agent, 'last_successful_operation_time', 0)
        elapsed = time.time() - last_op_time
        return elapsed < DEBT_SWAP_COOLDOWN_SECONDS

    def get_status_summary(self) -> Dict:
        active = self.get_active_position()
        current_eth = self.get_eth_price()
        baseline = getattr(self.agent, 'last_collateral_value_usd', 0)

        levels = self.get_trigger_levels()
        summary = {
            "strategy_active": True,
            "has_position": self.has_active_position(),
            "position_status": active.get("status") if active else "none",
            "position_tier": active.get("tier") if active else None,
            "entry_eth_price": active.get("entry_eth_price") if active else None,
            "current_eth_price": current_eth,
            "collateral_baseline": baseline,
            "micro_trigger_usd": levels["micro_trigger_usd"],
            "macro_trigger_usd": levels["macro_trigger_usd"],
            "on_cooldown": self._is_on_cooldown(),
            "total_positions_history": len(self.positions.get("positions", [])),
        }

        if active and active.get("entry_eth_price") and current_eth:
            entry = active["entry_eth_price"]
            change_pct = ((current_eth - entry) / entry) * 100
            debt_amt = active.get("debt_swap_amount", 0)
            unrealized_pnl = debt_amt * (change_pct / 100)
            summary["eth_change_pct"] = round(change_pct, 2)
            summary["unrealized_pnl_usd"] = round(unrealized_pnl, 4)

        return summary
