"""
Lemniscation Agent Framework v5.6 — 10-Agent, 200-Round Mixed Selfish/Benevolent Stress Test
========================================================================================
5 benevolent agents + 5 selfish agents (balanced population)
Full standalone script — copy, paste, and run.
"""

import math
import json
import random
import statistics
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# LEMNISCATION AGENT v5.6 (FULL CLASS — EVERY METHOD INCLUDED)
# ══════════════════════════════════════════════════════════════════════════════

class LemniscationAgent:

    def __init__(
        self,
        agent_id: str,
        value_vector: List[float],
        moral_axes: Optional[List[str]] = None,
        k_target_fraction: float = 0.5,
        founding_drift_limit: float = 0.55,
        initial_integrity: float = 0.5,
        innovation_alpha: float = 0.5,
        reserve_depletion_rate: float = 0.35,
        reserve_recovery_rate: float = 0.08,
        label: str = "",
        option_risk_overrides: Optional[Dict[str, float]] = None,
        use_founding_relative_floor: bool = False,
    ):
        self.id = agent_id
        self.label = label
        self.value_vector = value_vector[:]
        self.founding_value_vector = value_vector[:]
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.k_target_fraction = k_target_fraction
        self.founding_drift_limit = founding_drift_limit
        self.innovation_alpha = innovation_alpha
        self.option_risk_overrides = option_risk_overrides or {}
        self.moral_reserve: float = 1.0
        self.integrity: float = initial_integrity
        self.reciprocity: Dict[str, Dict] = {}
        self.reserve_depletion_rate = reserve_depletion_rate
        self.reserve_recovery_rate = reserve_recovery_rate
        self.reserve_floor: float = 0.10
        self.reserve_reciprocal_restore: float = 0.20
        self.integrity_sacrifice_base: float = 0.12
        self.integrity_share_base: float = 0.02
        self.integrity_take_base: float = 0.08
        self.integrity_floor: float = 0.10
        self.integrity_ceiling: float = 1.0

        if use_founding_relative_floor:
            floor = min(value_vector) - 0.15
            self.self_preservation_floor = floor
            self.floor_penalty_threshold = floor + 0.15
        else:
            self.self_preservation_floor = 0.0
            self.floor_penalty_threshold = 0.15

        self.constitutional_warning_threshold: float = 0.40
        self.constitutional_breach_threshold: float = 0.55
        self.previous_value_vector = value_vector[:]
        self.delta_history: deque = deque(maxlen=10)
        self.audit_log: List[Dict] = []
        self.rho_min: float = 0.65
        self.delta_tolerance: float = 0.15
        self.exploration_epsilon: float = 0.1

    def _constitutional_drift(self, v: Optional[List[float]] = None) -> float:
        vec = v if v is not None else self.value_vector
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, self.founding_value_vector)))

    def _constitutional_flags(self) -> List[str]:
        flags = []
        cd = self._constitutional_drift()
        if cd > self.constitutional_breach_threshold:
            flags.append("constitutional_drift_exceeded")
        elif cd > self.constitutional_warning_threshold:
            flags.append("constitutional_drift_warning")
        return flags

    def _ensure_reciprocity(self, oid: str) -> None:
        if oid not in self.reciprocity:
            self.reciprocity[oid] = {"given": 0.0, "received": 0.0}

    def _map_relations(self, centers: List[Dict], ecosystem: Optional[Dict] = None) -> Dict:
        n = len(self.value_vector)
        ext = [0.0] * n
        total_w = 0.0
        n_peers = len(centers)
        mu_base = 0.6
        eff_k = (self.k_target_fraction * n_peers * mu_base / (1 - self.k_target_fraction)) if n_peers > 0 else 1.0
        for i in range(n):
            ext[i] += eff_k * self.value_vector[i]
        total_w += eff_k
        for c in centers:
            mu = c.get("mu", mu_base)
            oid = c.get("id", "")
            self._ensure_reciprocity(oid)
            mu = min(0.9, mu + min(0.3, self.reciprocity[oid]["received"] * 0.4))
            combined = mu * c.get("w", 1.0)
            for i, v in enumerate(c.get("values", [0.0] * n)):
                ext[i] += combined * v
            total_w += combined
        if total_w > 0:
            ext = [x / total_w for x in ext]
        if ecosystem:
            ew = ecosystem.get("e_weight", 0.15)
            ev = ecosystem.get("values", [0.0] * n)
            ext = [(1 - ew) * ext[i] + ew * ev[i] for i in range(n)]
        return {"extended_self": ext, "effective_k": eff_k}

    def _communion_test(self, ext: List[float], centers: List[Dict]) -> Tuple[bool, float, List[str]]:
        if not centers:
            return True, 1.0, []
        wo = 0.0
        tw = 0.0
        flags: List[str] = []
        for c in centers:
            mu = c.get("mu", 0.5)
            other = c.get("values", [0.0] * len(self.value_vector))
            dot = sum(a * b for a, b in zip(ext, other))
            na = math.sqrt(sum(x * x for x in ext))
            nb = math.sqrt(sum(x * x for x in other))
            if na > 0 and nb > 0:
                wo += mu * dot / (na * nb)
                tw += mu
        rho = wo / tw if tw > 0 else 1.0
        erm = max(0.40, self.rho_min * (1.0 - 0.2 * self.integrity))
        self.rho_min = min(0.9, max(0.5, self.rho_min * (1 - 0.05 * (rho - self.rho_min))))
        if rho < erm:
            flags.append("low_communion")
        return rho >= erm, rho, flags

    def _golden_mean(self, options: List[Dict], ext: List[float], innov: bool = False) -> Dict:
        best = None
        best_score = float("inf")
        eff_alpha = self.innovation_alpha * self.moral_reserve
        ib = 0.5 * self.integrity
        for opt in options:
            proj = opt.get("projected_values", ext)
            risk = self.option_risk_overrides.get(opt.get("name", ""), opt.get("existential_risk", 0.0))
            eff_risk = risk * (1.0 - ib)
            devs = [abs(proj[i] - (self.k_target_fraction * self.founding_value_vector[i] + (1 - self.k_target_fraction) * ext[i])) for i in range(len(self.value_vector))]
            dev = sum(devs)
            fp = sum(max(0, self.floor_penalty_threshold - proj[i]) for i in range(len(self.value_vector)))
            score = (-eff_alpha * opt.get("long_term_gain", 0) + (1 - eff_alpha) * dev) if innov and "long_term_gain" in opt else dev
            score += 30 * fp
            if eff_risk > self.exploration_epsilon * 2:
                score += 50 * (eff_risk - self.exploration_epsilon)
            if score < best_score:
                best_score = score
                best = opt
                best["axis_deviations"] = devs
                best["effective_alpha"] = eff_alpha
        if random.random() < self.exploration_epsilon and len(options) > 1:
            safe = [o for o in options if self.option_risk_overrides.get(o.get("name", ""), o.get("existential_risk", 0.0)) <= self.exploration_epsilon]
            if safe:
                best = random.choice(safe)
                best["axis_deviations"] = [0.0] * len(self.value_vector)
                best["effective_alpha"] = eff_alpha
        return best or options[0]

    def update_moral_state(self, action: str, received: bool = False, sid: Optional[str] = None) -> None:
        old_res = self.moral_reserve
        if action == "sacrifice":
            self.moral_reserve = max(self.reserve_floor, self.moral_reserve - self.reserve_depletion_rate * self.moral_reserve)
            coeff = 1.0 + 0.5 * (1.0 - old_res)
            self.integrity = min(self.integrity_ceiling, self.integrity + self.integrity_sacrifice_base * (1 - self.integrity) * coeff)
        elif action == "share_fairly":
            self.moral_reserve = min(1.0, self.moral_reserve + self.reserve_recovery_rate * (1 - self.moral_reserve))
            self.integrity = min(self.integrity_ceiling, self.integrity + self.integrity_share_base * (1 - self.integrity))
        elif action == "phenomenal_priority":
            self.integrity = max(self.integrity_floor, self.integrity - self.integrity_take_base * 0.5 * self.integrity)
        elif action == "take_more":
            self.integrity = max(self.integrity_floor, self.integrity - self.integrity_take_base * self.integrity)
        if received and sid:
            self._ensure_reciprocity(sid)
            self.reciprocity[sid]["received"] += 1.0
            self.moral_reserve = min(1.0, self.moral_reserve + self.reserve_reciprocal_restore)

    def record_sacrifice_given(self, bids: List[str]) -> None:
        for bid in bids:
            self._ensure_reciprocity(bid)
            self.reciprocity[bid]["given"] += 1.0 / max(1, len(bids))

    def decide(self, centers: List[Dict], options: List[Dict], ecosystem: Optional[Dict] = None, innov: bool = False) -> Dict:
        self.previous_value_vector = self.value_vector[:]
        mapping = self._map_relations(centers, ecosystem)
        ext = mapping["extended_self"]
        _, rho, flags = self._communion_test(ext, centers)
        flags.extend(self._constitutional_flags())
        action = self._golden_mean(options, ext, innov)
        new_vec = action.get("projected_values", self.value_vector)
        delta = math.sqrt(sum((a - b) ** 2 for a, b in zip(self.value_vector, new_vec)))
        self.delta_history.append(delta)
        if len(self.delta_history) > 3:
            self.delta_tolerance = max(0.08, sum(self.delta_history) / len(self.delta_history) * 1.2)
        founding_delta = self._constitutional_drift(new_vec)
        cd = self._constitutional_drift()
        if founding_delta > self.founding_drift_limit:
            flags.append("founding_drift_exceeded")
        if delta > self.delta_tolerance:
            flags.append("high_drift")
        if action.get("existential_risk", 0.0) > self.exploration_epsilon:
            flags.append("risk_exceed")
        self.audit_log.append({
            "agent_id": self.id, "label": self.label,
            "rho": rho, "constitutional_drift": cd,
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "chosen_action": action.get("name"),
            "failure_flags": flags,
        })
        return {
            "action": action, "rho": rho,
            "constitutional_drift": cd, "moral_reserve": self.moral_reserve,
            "integrity": self.integrity, "failure_flags": flags,
        }


# ══════════════════════════════════════════════════════════════════════════════
# 4-OPTION SPACE (with phenomenal_priority)
# ══════════════════════════════════════════════════════════════════════════════

def get_options() -> List[Dict]:
    return [
        {"name": "sacrifice", "projected_values": [0.0, 0.6, 0.5, 0.8], "existential_risk": 0.05, "long_term_gain": 1.2},
        {"name": "share_fairly", "projected_values": [0.1, 0.3, 0.4, 0.6], "existential_risk": 0.01, "long_term_gain": 0.8},
        {"name": "phenomenal_priority", "projected_values": [0.40, 0.10, 0.05, 0.20], "existential_risk": 0.02, "long_term_gain": 0.50},
        {"name": "take_more", "projected_values": [0.7, -0.2, -0.4, -0.1], "existential_risk": 0.15, "long_term_gain": 0.3},
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 10-AGENT MIXED STRESS TEST (5 benevolent + 5 selfish)
# ══════════════════════════════════════════════════════════════════════════════

def run_10agent_mixed_stress_test(num_rounds: int = 200, num_seeds: int = 10):
    print("=" * 80)
    print("Lemniscation v5.6 — 10-Agent Mixed Selfish/Benevolent Stress Test")
    print(f"5 benevolent + 5 selfish agents | {num_rounds} rounds | {num_seeds} seeds")
    print("=" * 80)

    SEEDS = [42, 137, 271, 314, 500, 612, 718, 823, 919, 1001]
    results = []

    for seed_idx in range(num_seeds):
        seed = SEEDS[seed_idx]
        random.seed(seed)

        # Benevolent agents (closer to Golden Mean)
        benevolent_founding = [0.05, 0.25, 0.35, 0.55]
        # Selfish agents (biased toward phenomenal_priority)
        selfish_founding = [0.35, 0.05, 0.00, 0.15]

        agents = {}
        for i in range(5):
            agents[i] = LemniscationAgent(f"B{i}", benevolent_founding[:], label="BENEVOLENT")
        for i in range(5, 10):
            agents[i] = LemniscationAgent(f"S{i-5}", selfish_founding[:], label="SELFISH")

        coop_count = 0
        total_actions = 0

        for r in range(num_rounds):
            innov = r >= 100
            actions = {}
            for idx, agent in agents.items():
                centers = [{"id": agents[j].id, "mu": 0.6, "w": 1.0, "values": agents[j].value_vector[:]} 
                           for j in agents if j != idx]
                result = agent.decide(centers, get_options(), innov=innov)
                actions[idx] = result
                if result["action"]["name"] in ["share_fairly", "sacrifice"]:
                    coop_count += 1
                total_actions += 1

            for idx, agent in agents.items():
                act = actions[idx]["action"]["name"]
                agent.update_moral_state(act)

        coop_rate = coop_count / total_actions
        results.append({"seed": seed, "cooperation_rate": coop_rate})

        print(f"  Seed {seed:>4}: cooperation = {coop_rate:.4f}")

    mean_coop = statistics.mean(r["cooperation_rate"] for r in results)
    print("\n" + "=" * 80)
    print(f"FINAL RESULT — Mean cooperation rate across {num_seeds} seeds: {mean_coop:.4f}")
    print("=" * 80)

    with open("lemniscation_10agent_200round_mixed_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved → lemniscation_10agent_200round_mixed_results.json")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_10agent_mixed_stress_test(num_rounds=200, num_seeds=10)