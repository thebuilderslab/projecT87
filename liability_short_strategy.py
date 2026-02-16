#!/usr/bin/env python3
"""
Liability Short Strategy — Phase 2: Target Profit Engine

PROFIT-FIRST SYSTEM: Works backwards from a target profit to determine
the exact ETH price drop needed before entering a short position.

FLOW (Round Trip — USDT Collateral):
  Step A (Setup):  Trigger fires → Borrow WETH → Swap to USDT → Supply USDT to Aave
  Step B (Hunt):   Poll every 15s → Wait for target_price OR stop-loss
  Step C (Close):  Withdraw USDT → Swap to WETH (cheaper) → Repay loan → Distribute profit

REVERSE CALCULATOR:
  Goal: "I need $10.00 profit"
  Calculate: fees (0.3% entry + 0.3% exit + $0.50 gas) + profit target
  Result: "Market must drop -2.4% to $X price"
  Safety: Abort if required drop > 4% for Micro

DUAL TRIGGERS:
  Macro: Collateral drop >5% + HF >3.05 → Full short
  Micro: Collateral drop >2% + HF >3.00 → Partial short

PROFIT DISTRIBUTION:
  Target_Wallet_S: $2.00
  Target_Wallet_B: $2.00
  Target_Collateral: $6.00
  Total_Target: $10.00

DYNAMIC POLLING:
  IDLE → 90s (Sentry Mode)
  SHORT_ACTIVE → 15s (Hunter Mode)
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

PROFIT_TARGETS = {
    'wallet_s': 2.00,
    'wallet_b': 2.00,
    'collateral': 6.00,
    'total': 10.00,
}

COST_ESTIMATES = {
    'swap_entry_fee_pct': 0.003,
    'swap_exit_fee_pct': 0.003,
    'gas_buffer_usd': 0.50,
}

MACRO_SHORT_SIZE_USD = 10.90
MICRO_SHORT_SIZE_USD = 7.20

MACRO_TRIGGER = {
    'collateral_drop_pct': 5.0,
    'min_health_factor': 3.05,
}

MICRO_TRIGGER = {
    'collateral_drop_pct': 2.0,
    'min_health_factor': 3.00,
}

SAFETY_GATES = {
    'micro_max_required_drop_pct': 4.0,
    'macro_max_required_drop_pct': 8.0,
    'stop_loss_pct': 1.5,
}

POLLING_INTERVALS = {
    'IDLE': 90,
    'SHORT_ACTIVE': 15,
}

PHASE2_STEP_ORDER = [
    "weth_borrowed",
    "usdt_swapped",
    "usdt_supplied_as_collateral",
    "short_active",
    "usdt_withdrawn",
    "eth_repurchased",
    "loan_repaid",
    "profit_distributed",
]

SHORT_COOLDOWN_SECONDS = 600


class LiabilityShortStrategy:
    def __init__(self, agent):
        self.agent = agent
        self.positions = self._load_positions()
        self.last_collateral_snapshot = None
        self.last_collateral_snapshot_time = 0
        self.collateral_history = []
        self.max_history = 60
        logger.info("Liability Short Strategy Phase 2 (Target Profit Engine) initialized")

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

    def get_position_status(self) -> str:
        active = self.get_active_position()
        if not active:
            return "IDLE"
        return active.get("status", "IDLE").upper()

    def get_polling_interval(self) -> int:
        status = self.get_position_status()
        if status == "SHORT_ACTIVE":
            return POLLING_INTERVALS['SHORT_ACTIVE']
        return POLLING_INTERVALS['IDLE']

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

    def _calculate_required_drop(self, short_size_usd: float, target_profit_usd: float) -> Dict:
        swap_entry_fee = short_size_usd * COST_ESTIMATES['swap_entry_fee_pct']
        swap_exit_fee = short_size_usd * COST_ESTIMATES['swap_exit_fee_pct']
        gas_buffer = COST_ESTIMATES['gas_buffer_usd']

        total_costs = swap_entry_fee + swap_exit_fee + gas_buffer
        gross_revenue_needed = target_profit_usd + total_costs
        required_drop_pct = (gross_revenue_needed / short_size_usd) * 100.0

        eth_price = self.get_eth_price()
        target_price = None
        if eth_price and eth_price > 0:
            target_price = eth_price * (1.0 - required_drop_pct / 100.0)

        stop_loss_price = None
        if eth_price and eth_price > 0:
            stop_loss_price = eth_price * (1.0 + SAFETY_GATES['stop_loss_pct'] / 100.0)

        return {
            'short_size_usd': short_size_usd,
            'target_profit_usd': target_profit_usd,
            'swap_entry_fee': round(swap_entry_fee, 4),
            'swap_exit_fee': round(swap_exit_fee, 4),
            'gas_buffer': gas_buffer,
            'total_costs': round(total_costs, 4),
            'gross_revenue_needed': round(gross_revenue_needed, 4),
            'required_drop_pct': round(required_drop_pct, 4),
            'entry_price': eth_price,
            'target_price': round(target_price, 2) if target_price else None,
            'stop_loss_price': round(stop_loss_price, 2) if stop_loss_price else None,
        }

    def validate_short_entry(self, tier: str, short_size_usd: float) -> Tuple[bool, str, Dict]:
        calc = self._calculate_required_drop(short_size_usd, PROFIT_TARGETS['total'])

        if calc['entry_price'] is None:
            return False, "Cannot determine ETH price — aborting", calc

        max_drop = SAFETY_GATES['micro_max_required_drop_pct'] if tier == "micro" else SAFETY_GATES['macro_max_required_drop_pct']
        if calc['required_drop_pct'] > max_drop:
            return False, f"SAFETY GATE: Required drop {calc['required_drop_pct']:.2f}% > {max_drop:.1f}% max for {tier} — unrealistic target, ABORT", calc

        print(f"\n📉 SHORT TRIGGERED: Target Net Profit ${PROFIT_TARGETS['total']:.2f}")
        print(f"🧮 CALCULATION: Market must drop -{calc['required_drop_pct']:.2f}% (${calc['entry_price']:.2f} → ${calc['target_price']:.2f}) to cover fees + profit")
        print(f"   Entry Fee:    ${calc['swap_entry_fee']:.4f} (0.3%)")
        print(f"   Exit Fee:     ${calc['swap_exit_fee']:.4f} (0.3%)")
        print(f"   Gas Buffer:   ${calc['gas_buffer']:.2f}")
        print(f"   Total Costs:  ${calc['total_costs']:.4f}")
        print(f"   Gross Needed: ${calc['gross_revenue_needed']:.4f}")
        print(f"   Stop Loss:    ${calc['stop_loss_price']:.2f} (+{SAFETY_GATES['stop_loss_pct']:.1f}%)")

        return True, f"Short validated: need -{calc['required_drop_pct']:.2f}% drop to ${calc['target_price']:.2f}", calc

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
            return False, "Short on cooldown"

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
        return True, f"MACRO ENTRY: Collateral ${current_collateral:.2f} < ${macro_target:.2f} target (drop {drop_pct:.1f}%), HF {health_factor:.3f}"

    def check_micro_entry(self, current_collateral: float, health_factor: float) -> Tuple[bool, str]:
        if self.has_active_position():
            return False, "Position already active — cannot open new entry"

        if self._is_on_cooldown():
            return False, "Short on cooldown"

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
        return True, f"MICRO ENTRY: Collateral ${current_collateral:.2f} < ${micro_target:.2f} target (drop {drop_pct:.1f}%), HF {health_factor:.3f}"

    def check_hunt_conditions(self) -> Tuple[str, str]:
        active = self.get_active_position()
        if not active or active.get("status") != "SHORT_ACTIVE":
            return "NONE", "No active short to hunt"

        target_price = active.get("target_price", 0)
        stop_loss_price = active.get("stop_loss_price", 0)
        entry_price = active.get("entry_eth_price", 0)

        current_eth = self.get_eth_price()
        if not current_eth:
            return "WAIT", "Cannot fetch ETH price — holding position"

        if current_eth <= target_price:
            drop_pct = ((entry_price - current_eth) / entry_price) * 100 if entry_price > 0 else 0
            return "WIN", f"TARGET HIT: ETH ${current_eth:.2f} <= ${target_price:.2f} (dropped {drop_pct:.1f}%)"

        if current_eth >= stop_loss_price:
            loss_pct = ((current_eth - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            return "STOP_LOSS", f"STOP LOSS: ETH ${current_eth:.2f} >= ${stop_loss_price:.2f} (rose {loss_pct:.1f}%)"

        distance_to_target = ((current_eth - target_price) / current_eth) * 100 if current_eth > 0 else 0
        return "HUNTING", f"⏳ HUNTING: ETH ${current_eth:.2f} — target ${target_price:.2f} ({distance_to_target:.2f}% away) | stop-loss ${stop_loss_price:.2f}"

    def open_position(self, tier: str, entry_eth_price: float, short_size_usd: float, calc: Dict):
        position = {
            "id": f"ls_{int(time.time())}",
            "tier": tier,
            "status": "SHORT_ACTIVE",
            "entry_eth_price": entry_eth_price,
            "short_size_usd": short_size_usd,
            "target_price": calc.get('target_price'),
            "stop_loss_price": calc.get('stop_loss_price'),
            "target_profit_usd": calc.get('target_profit_usd'),
            "required_drop_pct": calc.get('required_drop_pct'),
            "total_costs": calc.get('total_costs'),
            "dai_collateral_amount": 0,  # Legacy field name — stores USDT collateral amount
            "weth_borrowed_amount": 0,
            "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "opened_timestamp": time.time(),
            "closed_at": None,
            "exit_eth_price": None,
            "pnl_usd": None,
            "close_reason": None,
        }
        self.positions["active_position"] = position
        self.positions["positions"].append(position)
        self._save_positions()
        print(f"✅ Position opened: {tier.upper()} short at ETH ${entry_eth_price:.2f}")
        print(f"   Target: ${calc.get('target_price', 0):.2f} | Stop-Loss: ${calc.get('stop_loss_price', 0):.2f}")
        print(f"⏳ HUNTER MODE: Polling every {POLLING_INTERVALS['SHORT_ACTIVE']}s...")
        logger.info(f"Opened {tier} Phase 2 short at ETH ${entry_eth_price:.2f}, target ${calc.get('target_price', 0):.2f}")

    def update_position_amounts(self, dai_amount: float, weth_amount: float):
        active = self.positions.get("active_position")
        if active:
            active["dai_collateral_amount"] = dai_amount
            active["weth_borrowed_amount"] = weth_amount
            self._save_positions()

    def close_position(self, exit_eth_price: float, realized_profit: float, close_reason: str):
        active = self.positions.get("active_position")
        if not active:
            return

        active["status"] = "closed"
        active["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        active["exit_eth_price"] = exit_eth_price
        active["pnl_usd"] = round(realized_profit, 4)
        active["close_reason"] = close_reason

        for p in self.positions["positions"]:
            if p.get("id") == active.get("id"):
                p.update(active)
                break

        self.positions["active_position"] = None
        self._save_positions()
        logger.info(f"Closed position: entry ${active.get('entry_eth_price', 0):.2f} → exit ${exit_eth_price:.2f}, P&L ${realized_profit:.4f}, reason: {close_reason}")

    def _is_on_cooldown(self) -> bool:
        last_op_time = getattr(self.agent, 'last_successful_operation_time', 0)
        elapsed = time.time() - last_op_time
        return elapsed < SHORT_COOLDOWN_SECONDS

    def get_status_summary(self) -> Dict:
        active = self.get_active_position()
        current_eth = self.get_eth_price()
        baseline = getattr(self.agent, 'last_collateral_value_usd', 0)

        levels = self.get_trigger_levels()
        summary = {
            "strategy_active": True,
            "phase": 2,
            "has_position": self.has_active_position(),
            "position_status": active.get("status") if active else "IDLE",
            "position_tier": active.get("tier") if active else None,
            "entry_eth_price": active.get("entry_eth_price") if active else None,
            "target_price": active.get("target_price") if active else None,
            "stop_loss_price": active.get("stop_loss_price") if active else None,
            "current_eth_price": current_eth,
            "collateral_baseline": baseline,
            "micro_trigger_usd": levels["micro_trigger_usd"],
            "macro_trigger_usd": levels["macro_trigger_usd"],
            "on_cooldown": self._is_on_cooldown(),
            "polling_interval": self.get_polling_interval(),
            "polling_mode": "HUNTER" if self.get_position_status() == "SHORT_ACTIVE" else "SENTRY",
            "total_positions_history": len(self.positions.get("positions", [])),
            "profit_targets": PROFIT_TARGETS,
        }

        if active and active.get("entry_eth_price") and current_eth:
            entry = active["entry_eth_price"]
            change_pct = ((current_eth - entry) / entry) * 100
            summary["eth_change_pct"] = round(change_pct, 2)
            target_p = active.get("target_price", 0)
            if target_p and current_eth > 0:
                distance = ((current_eth - target_p) / current_eth) * 100
                summary["distance_to_target_pct"] = round(distance, 2)

        return summary
