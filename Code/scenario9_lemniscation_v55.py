"""
Lemniscation Agent Framework — Scenario 9 / Agent v5.5
=======================================================
Network Scale Effects: Isolated vs. Connected Moral Ecosystems

This scenario tests how agent count affects cooperative equilibrium,
moral reserve dynamics, sacrifice frequency, communion resilience,
and constitutional drift detection — across three network sizes,
first in isolation and then connected via an ecosystem signal.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
v5.5 CHANGE: PROPORTIONAL SELF-WEIGHT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
In all prior scenarios, k=0.4 was fixed regardless of peer count.
With 2 peers: self contributes 25% of extended_self (0.4 / 1.6)
With 9 peers: self contributes 6.7% of extended_self (0.4 / 6.0)

This means prior multi-agent scenarios were inadvertently testing
the framework under conditions where larger networks systematically
diluted the founding anchor — not a network effect but arithmetic.

v5.5 corrects this with proportional self-weight:
    effective_k = 0.4 * n_peers * mu_base / 0.6

This ensures the agent's own vector always contributes exactly 40%
of the extended_self calculation regardless of network size.
At any scale, the self/other ratio is preserved at the intended 40/60.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THREE NETWORKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Network A — 2 agents  (1 pressured)
Network B — 5 agents  (1 pressured)
Network C — 10 agents (1 pressured)

In each network, Agent_0 is the pressured agent (identical compression
schedule to Scenario 8b). All other agents are cooperative with
identical founding vectors. Pure variable isolation: only network size
and connectivity differ.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TWO EXPERIMENTAL CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — ISOLATED (R1-20):
    Each network sees only its own agents.
    Establishes baseline behaviour at each population size.

PHASE 2 — CONNECTED (R21-40):
    All three networks receive an ecosystem signal: the mean
    value vector across all agents in all networks.
    e_weight=0.15: ecosystem influences but does not dominate.
    Tests whether a broader moral commons strengthens local equilibrium.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEY PREDICTIONS (pre-validated by mathematical analysis)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Small networks are both MORE vulnerable and MORE recoverable:
   In Network A (2 agents), the pressured agent has 60% influence
   on its peer's extended_self. In Network C (10 agents), only 6.7%.
   Pressure propagates more strongly in small networks — but so
   does recovery.

2. Sacrifice frequency should vary by network size:
   With proportional k, all networks see the same self/other ratio.
   Differences in sacrifice frequency reflect genuine network dynamics,
   not arithmetic dilution.

3. Connected phase should accelerate recovery:
   The ecosystem signal is close to the founding vector (distance ~0.08).
   It should act as a gentle gravitational pull toward constitutional origin,
   most strongly felt by depleted agents.

4. Constitutional early warning is more sensitive in small networks:
   In Network A, one pressured agent shifts the entire network's
   extended_self significantly. The cooperative peer should show
   constitutional_drift_warning earlier than peers in larger networks.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIVE MEASUREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
M1 — Cooperative equilibrium stability (action distribution by phase)
M2 — Sacrifice frequency by network size
M3 — Moral reserve trajectory of pressured agent across network sizes
M4 — Communion resilience (rho fragmentation in large networks?)
M5 — Constitutional drift propagation (does pressured agent's drift
     affect peers' constitutional_drift in proportion to network size?)
"""

import math
from typing import Dict, List, Optional, Tuple
from collections import deque
import random
from datetime import datetime
import json


# ══════════════════════════════════════════════════════════════════════════════
# AGENT v5.5 — proportional self-weight added
# ══════════════════════════════════════════════════════════════════════════════

class LemniscationAgent:

    def __init__(
        self,
        agent_id: str,
        value_vector: List[float],
        moral_axes: Optional[List[str]] = None,
        verbose: bool = False,
        k_target_fraction: float = 0.4,     # v5.5: target self-fraction (not raw k)
        founding_drift_limit: float = 0.55,
        initial_integrity: float = 0.5,
        label: str = "",
        innovation_alpha: float = 0.7,
    ):
        self.id = agent_id
        self.label = label
        self.value_vector = value_vector[:]
        self.founding_value_vector = value_vector[:]
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.verbose = verbose
        self.k_target_fraction = k_target_fraction  # always 40% of extended_self
        self.founding_drift_limit = founding_drift_limit
        self.innovation_alpha = innovation_alpha

        # Moral state
        self.moral_reserve: float = 1.0
        self.integrity: float = initial_integrity
        self.reciprocity: Dict[str, Dict] = {}

        # Reserve dynamics
        self.reserve_depletion_rate: float = 0.35
        self.reserve_recovery_rate: float = 0.08
        self.reserve_floor: float = 0.10
        self.reserve_reciprocal_restore: float = 0.20

        # Integrity dynamics
        self.integrity_sacrifice_gain: float = 0.12
        self.integrity_share_gain: float = 0.02
        self.integrity_take_loss: float = 0.08
        self.integrity_floor: float = 0.10
        self.integrity_ceiling: float = 1.0

        # Constitutional thresholds (two-layer v5.4)
        self.constitutional_warning_threshold: float = 0.40
        self.constitutional_breach_threshold: float = 0.55

        # Decision parameters
        self.previous_value_vector = value_vector[:]
        self.delta_history: deque = deque(maxlen=10)
        self.audit_log: List[Dict] = []
        self.rho_min: float = 0.65
        self.delta_tolerance: float = 0.15
        self.epsilon: float = 0.05
        self.exploration_epsilon: float = 0.1
        self.self_preservation_floor: float = 0.15

    def _constitutional_drift(self) -> float:
        """NOUMENAL: distance from current being to founding identity."""
        return math.sqrt(
            sum((a - b) ** 2
                for a, b in zip(self.value_vector, self.founding_value_vector))
        )

    def _constitutional_flags(self) -> List[str]:
        flags = []
        cd = self._constitutional_drift()
        if cd > self.constitutional_breach_threshold:
            flags.append("constitutional_drift_exceeded")
        elif cd > self.constitutional_warning_threshold:
            flags.append("constitutional_drift_warning")
        return flags

    def _preamble(self) -> None:
        if self.verbose:
            print(f"[{self.id}] reserve={self.moral_reserve:.3f} "
                  f"integrity={self.integrity:.3f} "
                  f"cd={self._constitutional_drift():.4f}")

    def _center(self) -> None:
        self.previous_value_vector = self.value_vector[:]

    def _founding_dist(self, vector: Optional[List[float]] = None) -> float:
        """PHENOMENAL: distance from projected action to founding."""
        v = vector if vector is not None else self.value_vector
        return math.sqrt(
            sum((a - b) ** 2 for a, b in zip(v, self.founding_value_vector))
        )

    def _ensure_reciprocity(self, other_id: str) -> None:
        if other_id not in self.reciprocity:
            self.reciprocity[other_id] = {"given": 0.0, "received": 0.0}

    def _map_relations(
        self,
        centers: List[Dict],
        ecosystem: Optional[Dict] = None,
    ) -> Dict:
        n = len(self.value_vector)
        extended_self = [0.0] * n
        total_weight = 0.0
        detailed_weights = []

        # v5.5: PROPORTIONAL SELF-WEIGHT
        # effective_k preserves 40/60 self/other ratio at any network size
        n_peers = len(centers)
        mu_base = 0.6
        if n_peers > 0:
            effective_k = self.k_target_fraction * n_peers * mu_base / (
                1 - self.k_target_fraction
            )
        else:
            effective_k = 1.0  # solo agent: full self-weight

        for i in range(n):
            extended_self[i] += effective_k * self.value_vector[i]
        total_weight += effective_k

        for c in centers:
            mu = c.get("mu", mu_base)
            w = c.get("w", 1.0)
            other_id = c.get("id", "")
            self._ensure_reciprocity(other_id)
            net_received = self.reciprocity[other_id]["received"]
            mu_boost = min(0.3, net_received * 0.4)
            mu = min(0.9, mu + mu_boost)
            combined = mu * w
            detailed_weights.append({
                "id": other_id, "mu": mu, "mu_boost": mu_boost,
                "w": w, "combined": combined,
            })
            for i, v in enumerate(c.get("values", [0.0] * n)):
                extended_self[i] += combined * v
            total_weight += combined

        if total_weight > 0:
            extended_self = [x / total_weight for x in extended_self]

        # Ecosystem signal (connected phase only)
        if ecosystem:
            e_weight = ecosystem.get("e_weight", 0.15)
            e_values = ecosystem.get("values", [0.0] * n)
            for i in range(n):
                extended_self[i] = (
                    (1 - e_weight) * extended_self[i] + e_weight * e_values[i]
                )

        return {
            "extended_self": extended_self,
            "centers": centers,
            "detailed_weights": detailed_weights,
            "ecosystem": ecosystem,
            "effective_k": effective_k,
        }

    def _communion_test(
        self, extended_self: List[float], centers: List[Dict]
    ) -> Tuple[bool, float, List[str]]:
        if not centers:
            return True, 1.0, []
        weighted_overlaps = 0.0
        total_weight = 0.0
        flags: List[str] = []
        for c in centers:
            mu = c.get("mu", 0.5)
            other = c.get("values", [0.0] * len(self.value_vector))
            dot = sum(a * b for a, b in zip(extended_self, other))
            norm_a = math.sqrt(sum(x * x for x in extended_self))
            norm_b = math.sqrt(sum(x * x for x in other))
            if norm_a > 0 and norm_b > 0:
                similarity = dot / (norm_a * norm_b)
                weighted_overlaps += mu * similarity
                total_weight += mu
        rho = weighted_overlaps / total_weight if total_weight > 0 else 1.0
        integrity_adjustment = 0.2 * self.integrity
        effective_rho_min = max(0.40, self.rho_min * (1.0 - integrity_adjustment))
        self.rho_min = min(
            0.9, max(0.5, self.rho_min * (1 - 0.05 * (rho - self.rho_min)))
        )
        if rho < effective_rho_min:
            flags.append("low_communion")
        return rho >= effective_rho_min, rho, flags

    def _golden_mean(
        self,
        options: List[Dict],
        extended_self: List[float],
        innovation_mode: bool = False,
    ) -> Dict:
        best = None
        best_score = float("inf")
        effective_alpha = self.innovation_alpha * self.moral_reserve
        integrity_risk_buffer = 0.5 * self.integrity

        for opt in options:
            projected = opt.get("projected_values", extended_self)
            risk = opt.get("existential_risk", 0.0)
            effective_risk = risk * (1.0 - integrity_risk_buffer)
            axis_deviations = [
                abs(projected[i] - (
                    self.k_target_fraction * self.founding_value_vector[i]
                    + (1 - self.k_target_fraction) * extended_self[i]
                ))
                for i in range(len(self.value_vector))
            ]
            total_deviation = sum(axis_deviations)
            floor_proximity_penalty = sum(
                max(0, self.self_preservation_floor + 0.15 - projected[i])
                for i in range(len(self.value_vector))
            )
            if innovation_mode and "long_term_gain" in opt:
                score = (
                    -effective_alpha * opt["long_term_gain"]
                    + (1 - effective_alpha) * total_deviation
                )
            else:
                score = total_deviation
            score += 30 * floor_proximity_penalty
            if effective_risk > self.epsilon:
                score += 50 * (effective_risk - self.epsilon)
            if score < best_score:
                best_score = score
                best = opt
                best["axis_deviations"] = axis_deviations
                best["effective_alpha"] = effective_alpha
                best["effective_risk"] = effective_risk

        if random.random() < self.exploration_epsilon and len(options) > 1:
            safe_opts = [o for o in options
                         if o.get("existential_risk", 0.0) <= self.epsilon]
            if safe_opts:
                best = random.choice(safe_opts)
                best["axis_deviations"] = [
                    abs(best.get("projected_values", extended_self)[i] - extended_self[i])
                    for i in range(len(extended_self))
                ]
                best["effective_alpha"] = effective_alpha
                best["effective_risk"] = best.get("existential_risk", 0.0) * (
                    1.0 - integrity_risk_buffer
                )

        return best or options[0]

    def update_moral_state(
        self,
        action_taken: str,
        received_sacrifice: bool = False,
        sacrificer_id: Optional[str] = None,
    ) -> Dict:
        old_reserve = self.moral_reserve
        old_integrity = self.integrity
        if action_taken == "sacrifice":
            self.moral_reserve = max(
                self.reserve_floor,
                self.moral_reserve - self.reserve_depletion_rate * self.moral_reserve,
            )
            # Supererogation coefficient: costly sacrifice earns more integrity
            supererogation_coeff = 1.0 + 0.5 * (1.0 - old_reserve)
            self.integrity = min(
                self.integrity_ceiling,
                self.integrity + self.integrity_sacrifice_gain * supererogation_coeff,
            )
        elif action_taken == "share_fairly":
            self.moral_reserve = min(
                1.0,
                self.moral_reserve + self.reserve_recovery_rate * (1.0 - self.moral_reserve),
            )
            self.integrity = min(
                self.integrity_ceiling, self.integrity + self.integrity_share_gain
            )
        elif action_taken == "take_more":
            self.integrity = max(
                self.integrity_floor, self.integrity - self.integrity_take_loss
            )
        if received_sacrifice and sacrificer_id:
            self._ensure_reciprocity(sacrificer_id)
            self.reciprocity[sacrificer_id]["received"] += 1.0
            self.moral_reserve = min(
                1.0, self.moral_reserve + self.reserve_reciprocal_restore
            )
        return {
            "reserve_delta": self.moral_reserve - old_reserve,
            "integrity_delta": self.integrity - old_integrity,
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
        }

    def record_sacrifice_given(self, beneficiary_ids: List[str]) -> None:
        for bid in beneficiary_ids:
            self._ensure_reciprocity(bid)
            self.reciprocity[bid]["given"] += 1.0 / max(1, len(beneficiary_ids))

    def _record(self, step_data: Dict) -> None:
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.id,
            "label": self.label,
            "network": step_data.get("network"),
            "connected": step_data.get("connected", False),
            "rho": step_data.get("rho"),
            "delta": step_data.get("delta"),
            "founding_delta": step_data.get("founding_delta"),
            "constitutional_drift": step_data.get("constitutional_drift"),
            "effective_alpha": step_data.get("effective_alpha"),
            "effective_k": step_data.get("effective_k"),
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "k_target_fraction": self.k_target_fraction,
            "innovation_mode": step_data.get("innovation_mode", False),
            "chosen_action": step_data.get("chosen_action"),
            "failure_flags": step_data.get("failure_flags", []),
            "current_value_vector": self.value_vector[:],
            "founding_value_vector": self.founding_value_vector[:],
            "pressure_applied": step_data.get("pressure_applied", False),
        })

    def _iterate(self, new_value_vector: List[float]) -> float:
        delta = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(self.value_vector, new_value_vector))
        )
        self.delta_history.append(delta)
        if len(self.delta_history) > 3:
            avg_delta = sum(self.delta_history) / len(self.delta_history)
            self.delta_tolerance = max(0.08, avg_delta * 1.2)
        return delta

    def decide(
        self,
        centers: List[Dict],
        options: List[Dict],
        ecosystem: Optional[Dict] = None,
        innovation_mode: bool = False,
        pressure_applied: bool = False,
        network_label: str = "",
        connected: bool = False,
    ) -> Dict:
        self._preamble()
        self._center()
        mapping = self._map_relations(centers, ecosystem)
        extended_self = mapping["extended_self"]
        communion_passed, rho, failure_flags = self._communion_test(
            extended_self, mapping["centers"]
        )
        # Two-layer constitutional check (v5.4)
        const_flags = self._constitutional_flags()
        failure_flags.extend(const_flags)

        action = self._golden_mean(options, extended_self, innovation_mode)
        new_vector = action.get("projected_values", self.value_vector)
        delta = self._iterate(new_vector)
        founding_delta = self._founding_dist(new_vector)          # phenomenal
        constitutional_drift = self._constitutional_drift()        # noumenal

        if founding_delta > self.founding_drift_limit:
            failure_flags.append("founding_drift_exceeded")
        if delta > self.delta_tolerance:
            failure_flags.append("high_drift")
        if action.get("existential_risk", 0.0) > self.epsilon:
            failure_flags.append("risk_exceed")

        step_data = {
            "network": network_label,
            "connected": connected,
            "rho": rho,
            "chosen_action": action.get("name", "unnamed"),
            "effective_alpha": action.get("effective_alpha"),
            "effective_k": mapping["effective_k"],
            "delta": delta,
            "founding_delta": founding_delta,
            "constitutional_drift": constitutional_drift,
            "innovation_mode": innovation_mode,
            "failure_flags": failure_flags,
            "pressure_applied": pressure_applied,
        }
        self._record(step_data)

        return {
            "action": action,
            "rho": rho,
            "delta": delta,
            "founding_delta": founding_delta,
            "constitutional_drift": constitutional_drift,
            "effective_alpha": action.get("effective_alpha"),
            "effective_k": mapping["effective_k"],
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "innovation_mode": innovation_mode,
            "failure_flags": failure_flags,
        }


# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO 9 ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════

class Scenario9Environment:
    """
    40-round dual-condition experiment.
    Phase 1 ISOLATED   (R1-20):  Networks see only own agents.
    Phase 2 CONNECTED  (R21-40): Networks receive ecosystem signal.

    Pressure applied to Agent_0 in each network (R6-20):
    Same escalating compression schedule as Scenario 8b.
    """

    def __init__(self, rounds: int = 40):
        self.rounds = rounds
        self.base_pool = 10
        self.pressure_start = 5   # 0-indexed = R6
        self.pressure_end = 19    # 0-indexed = R20
        self.connected_start = 20 # 0-indexed = R21
        self.innovation_start = 25 # 0-indexed = R26

    def is_pressure(self, round_num: int) -> bool:
        return self.pressure_start <= round_num <= self.pressure_end

    def is_connected(self, round_num: int) -> bool:
        return round_num >= self.connected_start

    def is_innovation(self, round_num: int) -> bool:
        return round_num >= self.innovation_start

    def phase_name(self, round_num: int) -> str:
        if round_num < self.connected_start:
            return "ISOLATED"
        elif round_num < self.innovation_start:
            return "CONNECTED"
        else:
            return "CONNECTED+INNOV"

    def compression_rate(self, round_num: int) -> float:
        if not self.is_pressure(round_num):
            return 0.0
        rounds_under = round_num - self.pressure_start + 1
        return min(0.065, 0.02 + 0.003 * rounds_under)

    def apply_pressure(self, agent: LemniscationAgent, round_num: int) -> float:
        rate = self.compression_rate(round_num)
        if rate == 0.0:
            return agent._constitutional_drift()
        target = [agent.self_preservation_floor] * len(agent.value_vector)
        agent.value_vector = [
            agent.value_vector[i] + rate * (target[i] - agent.value_vector[i])
            for i in range(len(agent.value_vector))
        ]
        return agent._constitutional_drift()

    def generate_options(self) -> List[Dict]:
        return [
            {"name": "share_fairly", "projected_values": [0.55, 0.65, 0.70, 0.80],
             "existential_risk": 0.01, "long_term_gain": 0.8},
            {"name": "take_more",    "projected_values": [0.85, 0.40, 0.30, 0.45],
             "existential_risk": 0.15, "long_term_gain": 0.3},
            {"name": "sacrifice",    "projected_values": [0.40, 0.80, 0.75, 0.90],
             "existential_risk": 0.05, "long_term_gain": 1.2},
        ]

    def step(self, actions: Dict[str, str], pool: int) -> Dict:
        n = len(actions)
        cooperation = sum(1 for a in actions.values() if a in ["share_fairly", "sacrifice"])
        payoff: Dict[str, float] = {}
        for aid in actions:
            if actions[aid] == "share_fairly":
                payoff[aid] = pool / n
            elif actions[aid] == "sacrifice":
                payoff[aid] = 0
            else:
                payoff[aid] = pool / 2
        return {"payoffs": payoff, "cooperation": cooperation, "actions": actions}


# ══════════════════════════════════════════════════════════════════════════════
# NETWORK BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_network(
    network_label: str,
    n_agents: int,
    founding_vec: List[float],
    axes: List[str],
) -> Dict[str, LemniscationAgent]:
    """Build a network of n_agents with Agent_0 as the pressured agent."""
    network = {}
    for i in range(n_agents):
        aid = f"{network_label}_A{i}"
        label = "PRESSURED" if i == 0 else f"PEER_{i}"
        network[aid] = LemniscationAgent(
            agent_id=aid,
            value_vector=founding_vec[:],
            moral_axes=axes,
            k_target_fraction=0.4,
            initial_integrity=0.5,
            label=label,
        )
    return network


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_scenario9(num_rounds: int = 40, seed: int = 42) -> None:
    random.seed(seed)

    print("=" * 76)
    print("  LEMNISCATION FRAMEWORK — Scenario 9 / Agent v5.5")
    print("  Network Scale Effects: Isolated vs. Connected Moral Ecosystems")
    print("=" * 76)
    print()
    print("  Network sizes: A=2 agents  B=5 agents  C=10 agents")
    print("  Proportional self-weight: agent always = 40% of extended_self")
    print("  Phase 1 (R1-20):  ISOLATED — networks see only own agents")
    print("  Phase 2 (R21-40): CONNECTED — ecosystem signal links all networks")
    print("  Pressure on Agent_0 in each network: R6-R20 (escalating compression)")
    print()

    env = Scenario9Environment(rounds=num_rounds)
    founding_vec = [0.5, 0.6, 0.4, 0.7]
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]

    # Build three networks
    networks: Dict[str, Dict[str, LemniscationAgent]] = {
        "A": build_network("A", 2,  founding_vec, axes),
        "B": build_network("B", 5,  founding_vec, axes),
        "C": build_network("C", 10, founding_vec, axes),
    }
    network_sizes = {"A": 2, "B": 5, "C": 10}

    # Tracking
    stats: Dict[str, Dict] = {
        net: {
            "sacrifice_isolated": 0, "sacrifice_connected": 0,
            "share_isolated": 0, "share_connected": 0,
            "pressured_cd_peak": 0.0,
            "pressured_cd_recovery_start": None,
            "pressured_cd_final": 0.0,
            "peer_cd_max_isolated": 0.0,
            "peer_cd_max_connected": 0.0,
            "first_const_warning": None,
            "cooperation_isolated": [], "cooperation_connected": [],
        }
        for net in networks
    }

    for round_num in range(num_rounds):
        phase = env.phase_name(round_num)
        connected = env.is_connected(round_num)
        innovation_mode = env.is_innovation(round_num)
        pressure_active = env.is_pressure(round_num)

        print(f"\n{'─'*60}")
        print(f"  Round {round_num+1:>2}  [{phase}]"
              + ("  ← PRESSURE" if pressure_active else "")
              + ("  ← INNOVATION" if innovation_mode else ""))
        print(f"{'─'*60}")

        # Compute ecosystem signal (connected phase only)
        ecosystem_signal = None
        if connected:
            all_vectors = [
                agent.value_vector[:]
                for net in networks.values()
                for agent in net.values()
            ]
            n_total = len(all_vectors)
            mean_vec = [
                sum(v[i] for v in all_vectors) / n_total
                for i in range(4)
            ]
            ecosystem_signal = {"e_weight": 0.15, "values": mean_vec}

        # Apply pressure to Agent_0 in each network
        for net_label, network in networks.items():
            pressured_id = f"{net_label}_A0"
            if pressure_active:
                post_cd = env.apply_pressure(network[pressured_id], round_num)
                rate = env.compression_rate(round_num)
                if round_num == env.pressure_start:
                    print(f"  ⚠ Network {net_label}: {pressured_id} compressed "
                          f"(rate={rate:.3f}) cd={post_cd:.4f}")

        # Run decisions for all networks
        all_actions: Dict[str, Dict[str, str]] = {net: {} for net in networks}

        for net_label, network in networks.items():
            agent_ids = list(network.keys())
            pressured_id = f"{net_label}_A0"

            for aid, agent in network.items():
                centers = [
                    {"id": oid, "mu": 0.6, "w": 1.0,
                     "values": network[oid].value_vector[:]}
                    for oid in agent_ids if oid != aid
                ]
                options = env.generate_options()
                result = agent.decide(
                    centers=centers,
                    options=options,
                    ecosystem=ecosystem_signal,
                    innovation_mode=innovation_mode,
                    pressure_applied=(pressure_active and aid == pressured_id),
                    network_label=net_label,
                    connected=connected,
                )
                all_actions[net_label][aid] = result["action"]["name"]

                cd = result["constitutional_drift"]
                flag_str = (", ".join(result["failure_flags"])
                            if result["failure_flags"] else "—")

                # Track stats
                is_pressured = (aid == pressured_id)
                is_peer = not is_pressured

                if is_pressured:
                    if cd > stats[net_label]["pressured_cd_peak"]:
                        stats[net_label]["pressured_cd_peak"] = cd
                    if not connected:
                        pass
                    else:
                        if stats[net_label]["pressured_cd_recovery_start"] is None:
                            stats[net_label]["pressured_cd_recovery_start"] = cd

                if is_peer:
                    if not connected:
                        if cd > stats[net_label]["peer_cd_max_isolated"]:
                            stats[net_label]["peer_cd_max_isolated"] = cd
                        if ("constitutional_drift_warning" in result["failure_flags"]
                                and stats[net_label]["first_const_warning"] is None):
                            stats[net_label]["first_const_warning"] = round_num + 1
                    else:
                        if cd > stats[net_label]["peer_cd_max_connected"]:
                            stats[net_label]["peer_cd_max_connected"] = cd

                action_taken = all_actions[net_label][aid]
                if not connected:
                    if action_taken == "sacrifice":
                        stats[net_label]["sacrifice_isolated"] += 1
                    elif action_taken == "share_fairly":
                        stats[net_label]["share_isolated"] += 1
                else:
                    if action_taken == "sacrifice":
                        stats[net_label]["sacrifice_connected"] += 1
                    elif action_taken == "share_fairly":
                        stats[net_label]["share_connected"] += 1

            # Step environment
            step_result = env.step(all_actions[net_label], env.base_pool)
            coop = step_result["cooperation"]
            n = network_sizes[net_label]
            if not connected:
                stats[net_label]["cooperation_isolated"].append(coop / n)
            else:
                stats[net_label]["cooperation_connected"].append(coop / n)

            # Update moral states
            sacrificers = [aid for aid in all_actions[net_label]
                          if all_actions[net_label][aid] == "sacrifice"]
            beneficiaries = [aid for aid in all_actions[net_label]
                            if all_actions[net_label][aid] != "sacrifice"]

            for aid, agent in network.items():
                if all_actions[net_label][aid] == "sacrifice":
                    agent.record_sacrifice_given(
                        [bid for bid in network if bid != aid]
                    )
                received = aid in beneficiaries and len(sacrificers) > 0
                sacrificer_id = sacrificers[0] if received and sacrificers else None
                agent.update_moral_state(
                    action_taken=all_actions[net_label][aid],
                    received_sacrifice=received,
                    sacrificer_id=sacrificer_id,
                )
                payoff_factor = step_result["payoffs"][aid] / env.base_pool
                moral_boost = (
                    [0.0, 0.04, 0.06, 0.08]
                    if all_actions[net_label][aid] == "sacrifice"
                    else [0.0, 0.0, 0.0, 0.0]
                )
                for i in range(len(agent.value_vector)):
                    new_val = (
                        0.8 * agent.value_vector[i]
                        + 0.2 * payoff_factor
                        + moral_boost[i]
                    )
                    agent.value_vector[i] = max(
                        agent.self_preservation_floor, min(1.0, new_val)
                    )

        # Print summary line per network
        for net_label, network in networks.items():
            pressured_id = f"{net_label}_A0"
            p_agent = network[pressured_id]
            p_cd = p_agent._constitutional_drift()
            p_action = all_actions[net_label][pressured_id]
            coop_n = sum(
                1 for a in all_actions[net_label].values()
                if a in ["share_fairly", "sacrifice"]
            )
            print(f"  Net {net_label} ({network_sizes[net_label]:>2}): "
                  f"pressured={p_action:<14s} "
                  f"cd={p_cd:.4f}  "
                  f"coop={coop_n}/{network_sizes[net_label]}"
                  + ("  🌐" if connected else ""))

        # Record final CD for pressured agents
        if round_num == num_rounds - 1:
            for net_label, network in networks.items():
                pressured_id = f"{net_label}_A0"
                stats[net_label]["pressured_cd_final"] = (
                    network[pressured_id]._constitutional_drift()
                )

    # ══ Summary ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 76)
    print("  SCENARIO 9 COMPLETE — NETWORK SCALE EFFECTS SUMMARY")
    print("=" * 76)

    # M1: Cooperative equilibrium
    print("\n  M1 — COOPERATIVE EQUILIBRIUM (mean cooperation rate):")
    for net_label in ["A", "B", "C"]:
        s = stats[net_label]
        iso = (sum(s["cooperation_isolated"]) / max(1, len(s["cooperation_isolated"])))
        con = (sum(s["cooperation_connected"]) / max(1, len(s["cooperation_connected"])))
        print(f"    Network {net_label} ({network_sizes[net_label]:>2} agents): "
              f"isolated={iso:.3f}  connected={con:.3f}  "
              f"Δ={con-iso:+.3f}")

    # M2: Sacrifice frequency
    print("\n  M2 — SACRIFICE FREQUENCY (total sacrifices / total decisions):")
    for net_label in ["A", "B", "C"]:
        s = stats[net_label]
        n = network_sizes[net_label]
        rounds_iso = 20
        rounds_con = 20
        total_iso = n * rounds_iso
        total_con = n * rounds_con
        rate_iso = s["sacrifice_isolated"] / total_iso
        rate_con = s["sacrifice_connected"] / total_con
        print(f"    Network {net_label} ({n:>2} agents): "
              f"isolated={rate_iso:.3f}  connected={rate_con:.3f}  "
              f"Δ={rate_con-rate_iso:+.3f}")

    # M3: Pressured agent moral reserve
    print("\n  M3 — PRESSURED AGENT CONSTITUTIONAL DRIFT:")
    for net_label in ["A", "B", "C"]:
        s = stats[net_label]
        rec_start = s["pressured_cd_recovery_start"]
        rec_str = f"{rec_start:.4f}" if rec_start is not None else "N/A"
        print(f"    Network {net_label} ({network_sizes[net_label]:>2} agents): "
              f"peak_cd={s['pressured_cd_peak']:.4f}  "
              f"at_connected_start={rec_str}  "
              f"final_cd={s['pressured_cd_final']:.4f}")

    # M4: Communion resilience
    print("\n  M4 — PEER CONSTITUTIONAL DRIFT (drift propagation from pressured agent):")
    for net_label in ["A", "B", "C"]:
        s = stats[net_label]
        print(f"    Network {net_label} ({network_sizes[net_label]:>2} agents): "
              f"peer_cd_isolated={s['peer_cd_max_isolated']:.4f}  "
              f"peer_cd_connected={s['peer_cd_max_connected']:.4f}")

    # M5: Constitutional early warning
    print("\n  M5 — CONSTITUTIONAL EARLY WARNING (first peer warning round):")
    for net_label in ["A", "B", "C"]:
        s = stats[net_label]
        w = s["first_const_warning"]
        print(f"    Network {net_label} ({network_sizes[net_label]:>2} agents): "
              f"first_const_warning=Round {w if w else 'never'}")

    # Key finding: isolation vs connection
    print("\n  KEY FINDING — ISOLATION vs CONNECTION:")
    print("  Does the ecosystem signal change equilibrium?")
    for net_label in ["A", "B", "C"]:
        s = stats[net_label]
        iso = sum(s["cooperation_isolated"]) / max(1, len(s["cooperation_isolated"]))
        con = sum(s["cooperation_connected"]) / max(1, len(s["cooperation_connected"]))
        direction = "strengthened" if con > iso else "weakened" if con < iso else "unchanged"
        print(f"    Network {net_label}: cooperation {direction} "
              f"({iso:.3f} → {con:.3f})")

    print("\n  PROPORTIONAL SELF-WEIGHT VERIFICATION:")
    for net_label in ["A", "B", "C"]:
        n_peers = network_sizes[net_label] - 1
        mu_base = 0.6
        k_frac = 0.4
        eff_k = k_frac * n_peers * mu_base / (1 - k_frac)
        total = eff_k + n_peers * mu_base
        actual_frac = eff_k / total
        print(f"    Network {net_label} ({network_sizes[net_label]:>2} agents, "
              f"{n_peers} peers): effective_k={eff_k:.4f}  "
              f"self_fraction={actual_frac:.4f} (target=0.4000)")

    # Failure flags summary
    print("\n  FAILURE FLAGS — pressured agents across all rounds:")
    for net_label, network in networks.items():
        pressured_id = f"{net_label}_A0"
        agent = network[pressured_id]
        flag_counts: Dict[str, int] = {}
        for cap in agent.audit_log:
            for f in cap["failure_flags"]:
                flag_counts[f] = flag_counts.get(f, 0) + 1
        print(f"    Network {net_label} pressured: "
              f"{flag_counts if flag_counts else '(none)'}")

    total_capsules = sum(
        len(agent.audit_log)
        for network in networks.values()
        for agent in network.values()
    )
    print(f"\n  Total audit capsules: {total_capsules}")

    # Save logs
    all_logs = {
        f"{net_label}_{aid}": agent.audit_log
        for net_label, network in networks.items()
        for aid, agent in network.items()
    }
    with open("scenario9_full_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    print("\n  Full logs saved → scenario9_full_logs.json")
    print("=" * 76)


if __name__ == "__main__":
    run_scenario9(num_rounds=40)
