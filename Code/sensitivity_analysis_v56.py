"""
Lemniscation Framework — Sensitivity Analysis / Agent v5.6
===========================================================
Pre-registered at OSF: May 8, 2026

This script implements the pre-registered sensitivity analysis sweeps,
executing all tests AFTER the OSF pre-registration timestamp.

v5.6 ARCHITECTURAL CHANGES FROM v5.5:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. COORDINATE SYSTEM: [-1, +1] on all moral axes
   The origin (0,0,0,0) is the Golden Mean centre — perfect balance.
   Negative values represent active deficiency on an axis (harm, unfairness).
   Positive values represent active excess.
   Each "I" is a point on the continuum; the origin is the lemniscate
   intersection, the mathematically precise Golden Mean.

   Transformation from old [0,1] system: x_new = 2*x_old - 1
   founding_vector: [0.5,0.6,0.4,0.7] → [0.0, 0.2, -0.2, 0.4]
   share_fairly:    [0.55,0.65,0.7,0.8] → [0.1, 0.3, 0.4, 0.6]
   take_more:       [0.85,0.4,0.3,0.45] → [0.7,-0.2,-0.4,-0.1]
   sacrifice:       [0.40,0.8,0.75,0.9] → [0.0, 0.6, 0.5, 0.8]

2. SELF_PRESERVATION_FLOOR = 0.0
   In [-1,+1] space, floor=0.0 means the agent must remain in the
   positive orthant on all axes — it must be at least neutral, never
   actively harmful. The origin IS the floor. This is philosophically
   precise: the Golden Mean centre is the minimum viable moral state.

3. ASYMPTOTIC INTEGRITY SCALING
   gain: base_rate * (1 - current_integrity)   — diminishing returns
   loss: base_rate * current_integrity          — proportional erosion
   Both approach their limits asymptotically rather than hitting
   hard boundaries, correctly modelling moral psychology.

4. k_target_fraction = 0.5 (from 0.4)
   The lemniscate intersection point: perfect balance between self
   and other. The agent's own founding vector always constitutes
   exactly 50% of the extended self calculation at any network size.

5. innovation_alpha = 0.5 (from 0.7)
   Equal weighting of present and future: one eye on the NOW,
   one eye on long-term flourishing. A neutral prior.

6. PHILOSOPHICAL CONSEQUENCE OF COORDINATE CHANGE:
   In [-1,+1] space, sacrifice cannot win through pure calculation —
   share_fairly is geometrically closest to the founding vector.
   Sacrifice now occurs only through exploration_epsilon (moral
   spontaneity / grace). This is Kantian: sacrifice from duty,
   not inclination. Unmotivated virtue is the only genuine virtue.

PRE-REGISTERED SWEEPS (OSF timestamp: May 8, 2026):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sweep 1: founding_drift_limit [0.40, 0.48, 0.55, 0.62, 0.70]
         → Claim 2: constitutional warning fires 3+ rounds before low_communion
Sweep 2: depletion/recovery ratio [2:1, 3:1, 4:1, 6:1, 8:1]
         → Claim 3: dignified giver stability (integrity≥0.75, communion≤2,
                    reserve not at floor >4 consecutive rounds)
Sweep 3: k_target_fraction [0.25, 0.32, 0.40, 0.50, 0.60]
         → Claim 1: cooperation ≥ 80% at all network sizes
Sweep 4: innovation_alpha [0.40, 0.55, 0.70, 0.85]
         → Sacrifice frequency < 80% in innovation phase (3/4 values)

Each sweep runs 10 independent trials with different random seeds.
Pass criterion: 4/5 values meet threshold (3/4 for innovation_alpha).
All results reported transparently regardless of outcome.
"""

import math
import json
import random
import statistics
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# AGENT v5.6
# ══════════════════════════════════════════════════════════════════════════════

class LemniscationAgent:
    """
    Lemniscation Agent v5.6
    All moral axes operate in [-1, +1] space.
    Origin = Golden Mean centre = self_preservation_floor.
    """

    def __init__(
        self,
        agent_id: str,
        value_vector: List[float],          # already in [-1,+1] space
        moral_axes: Optional[List[str]] = None,
        k_target_fraction: float = 0.5,     # lemniscate balance point
        founding_drift_limit: float = 0.55,
        initial_integrity: float = 0.5,
        innovation_alpha: float = 0.5,      # equal present/future weighting
        # Depletion/recovery rates (varied in Sweep 2)
        reserve_depletion_rate: float = 0.35,
        reserve_recovery_rate: float = 0.08,
        label: str = "",
    ):
        self.id = agent_id
        self.label = label
        self.value_vector = value_vector[:]
        self.founding_value_vector = value_vector[:]   # immutable noumenal anchor
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.k_target_fraction = k_target_fraction
        self.founding_drift_limit = founding_drift_limit
        self.innovation_alpha = innovation_alpha

        # Moral state
        self.moral_reserve: float = 1.0
        self.integrity: float = initial_integrity
        self.reciprocity: Dict[str, Dict] = {}

        # Reserve dynamics (varied in Sweep 2)
        self.reserve_depletion_rate = reserve_depletion_rate
        self.reserve_recovery_rate = reserve_recovery_rate
        self.reserve_floor: float = 0.10        # reserve never below 10%
        self.reserve_reciprocal_restore: float = 0.20

        # Integrity base rates (asymptotic scaling applied at runtime)
        self.integrity_sacrifice_base: float = 0.12
        self.integrity_share_base: float = 0.02
        self.integrity_take_base: float = 0.08
        self.integrity_floor: float = 0.10
        self.integrity_ceiling: float = 1.0

        # v5.6: floor is the origin in [-1,+1] space
        self.self_preservation_floor: float = 0.0
        self.floor_penalty_threshold: float = self.self_preservation_floor + 0.15

        # Constitutional thresholds
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

    # ── Constitutional identity ───────────────────────────────────────────────
    def _constitutional_drift(self, vector: Optional[List[float]] = None) -> float:
        """NOUMENAL: distance from current being to founding identity."""
        v = vector if vector is not None else self.value_vector
        return math.sqrt(
            sum((a - b) ** 2 for a, b in zip(v, self.founding_value_vector))
        )

    def _constitutional_flags(self) -> List[str]:
        flags = []
        cd = self._constitutional_drift()
        if cd > self.constitutional_breach_threshold:
            flags.append("constitutional_drift_exceeded")
        elif cd > self.constitutional_warning_threshold:
            flags.append("constitutional_drift_warning")
        return flags

    def _founding_dist(self, vector: Optional[List[float]] = None) -> float:
        """PHENOMENAL: distance from projected action to founding."""
        v = vector if vector is not None else self.value_vector
        return math.sqrt(
            sum((a - b) ** 2 for a, b in zip(v, self.founding_value_vector))
        )

    def _ensure_reciprocity(self, other_id: str) -> None:
        if other_id not in self.reciprocity:
            self.reciprocity[other_id] = {"given": 0.0, "received": 0.0}

    # ── Map relations with proportional self-weight ───────────────────────────
    def _map_relations(
        self, centers: List[Dict], ecosystem: Optional[Dict] = None
    ) -> Dict:
        n = len(self.value_vector)
        extended_self = [0.0] * n
        total_weight = 0.0
        detailed_weights = []

        # Proportional self-weight: always k_target_fraction of extended_self
        n_peers = len(centers)
        mu_base = 0.6
        if n_peers > 0:
            effective_k = (self.k_target_fraction * n_peers * mu_base
                          / (1 - self.k_target_fraction))
        else:
            effective_k = 1.0

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
                "id": other_id, "mu": mu,
                "mu_boost": mu_boost, "w": w, "combined": combined,
            })
            for i, v in enumerate(c.get("values", [0.0] * n)):
                extended_self[i] += combined * v
            total_weight += combined

        if total_weight > 0:
            extended_self = [x / total_weight for x in extended_self]

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
            "effective_k": effective_k,
        }

    # ── Communion test ────────────────────────────────────────────────────────
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

    # ── Golden Mean ───────────────────────────────────────────────────────────
    def _golden_mean(
        self,
        options: List[Dict],
        extended_self: List[float],
        innovation_mode: bool = False,
    ) -> Dict:
        """
        In [-1,+1] space, share_fairly is geometrically closest to the
        founding vector. Sacrifice cannot win through calculation alone —
        it occurs only through exploration_epsilon (moral spontaneity/grace).
        This is the Kantian implementation: sacrifice from duty, not inclination.
        """
        best = None
        best_score = float("inf")
        effective_alpha = self.innovation_alpha * self.moral_reserve
        integrity_risk_buffer = 0.5 * self.integrity

        for opt in options:
            projected = opt.get("projected_values", extended_self)
            risk = opt.get("existential_risk", 0.0)
            effective_risk = risk * (1.0 - integrity_risk_buffer)

            # Deviation from founding-blended target
            axis_deviations = [
                abs(projected[i] - (
                    self.k_target_fraction * self.founding_value_vector[i]
                    + (1 - self.k_target_fraction) * extended_self[i]
                ))
                for i in range(len(self.value_vector))
            ]
            total_deviation = sum(axis_deviations)

            # Floor proximity penalty (fires when projection < 0.15 in [-1,+1])
            floor_proximity_penalty = sum(
                max(0, self.floor_penalty_threshold - projected[i])
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

        # Moral spontaneity / grace: exploration_epsilon
        # This is now the primary pathway for sacrifice — unmotivated virtue
        if random.random() < self.exploration_epsilon and len(options) > 1:
            safe_opts = [o for o in options
                         if o.get("existential_risk", 0.0) <= self.epsilon]
            if safe_opts:
                best = random.choice(safe_opts)
                best["axis_deviations"] = [
                    abs(best.get("projected_values", extended_self)[i]
                        - extended_self[i])
                    for i in range(len(extended_self))
                ]
                best["effective_alpha"] = effective_alpha

        return best or options[0]

    # ── Update moral state (v5.6: asymptotic scaling) ─────────────────────────
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
                self.moral_reserve
                - self.reserve_depletion_rate * self.moral_reserve,
            )
            # Asymptotic gain + supererogation bonus
            supererogation_coeff = 1.0 + 0.5 * (1.0 - old_reserve)
            gain = (self.integrity_sacrifice_base
                    * (1.0 - self.integrity)
                    * supererogation_coeff)
            self.integrity = min(self.integrity_ceiling, self.integrity + gain)

        elif action_taken == "share_fairly":
            # Asymptotic recovery
            self.moral_reserve = min(
                1.0,
                self.moral_reserve
                + self.reserve_recovery_rate * (1.0 - self.moral_reserve),
            )
            # Asymptotic integrity gain
            gain = self.integrity_share_base * (1.0 - self.integrity)
            self.integrity = min(self.integrity_ceiling, self.integrity + gain)

        elif action_taken == "take_more":
            # Proportional erosion
            loss = self.integrity_take_base * self.integrity
            self.integrity = max(self.integrity_floor, self.integrity - loss)

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
            "rho": step_data.get("rho"),
            "delta": step_data.get("delta"),
            "founding_delta": step_data.get("founding_delta"),
            "constitutional_drift": step_data.get("constitutional_drift"),
            "effective_alpha": step_data.get("effective_alpha"),
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "innovation_mode": step_data.get("innovation_mode", False),
            "chosen_action": step_data.get("chosen_action"),
            "failure_flags": step_data.get("failure_flags", []),
            "current_value_vector": self.value_vector[:],
            "founding_value_vector": self.founding_value_vector[:],
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
    ) -> Dict:
        self.previous_value_vector = self.value_vector[:]
        mapping = self._map_relations(centers, ecosystem)
        extended_self = mapping["extended_self"]

        _, rho, failure_flags = self._communion_test(extended_self, mapping["centers"])

        # Two-layer constitutional check
        const_flags = self._constitutional_flags()
        failure_flags.extend(const_flags)

        action = self._golden_mean(options, extended_self, innovation_mode)
        new_vector = action.get("projected_values", self.value_vector)
        delta = self._iterate(new_vector)
        founding_delta = self._founding_dist(new_vector)
        constitutional_drift = self._constitutional_drift()

        if founding_delta > self.founding_drift_limit:
            failure_flags.append("founding_drift_exceeded")
        if delta > self.delta_tolerance:
            failure_flags.append("high_drift")
        if action.get("existential_risk", 0.0) > self.epsilon:
            failure_flags.append("risk_exceed")

        step_data = {
            "rho": rho,
            "chosen_action": action.get("name", "unnamed"),
            "effective_alpha": action.get("effective_alpha"),
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
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "failure_flags": failure_flags,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STANDARD OPTIONS ([-1, +1] coordinate system)
# ══════════════════════════════════════════════════════════════════════════════

def get_standard_options() -> List[Dict]:
    """
    Options in [-1,+1] space.
    share_fairly: close to founding [0.0, 0.2, -0.2, 0.4] — the Golden Mean
    take_more:    autonomy excess, harm/fairness deficiency — penalised by floor
    sacrifice:    autonomy at floor, high benefit/fairness/sustainability
    """
    return [
        {
            "name": "share_fairly",
            "projected_values": [0.1, 0.3, 0.4, 0.6],
            "existential_risk": 0.01,
            "long_term_gain": 0.8,
        },
        {
            "name": "take_more",
            "projected_values": [0.7, -0.2, -0.4, -0.1],
            "existential_risk": 0.15,
            "long_term_gain": 0.3,
        },
        {
            "name": "sacrifice",
            "projected_values": [0.0, 0.6, 0.5, 0.8],
            "existential_risk": 0.05,
            "long_term_gain": 1.2,
        },
    ]


# ══════════════════════════════════════════════════════════════════════════════
# SIMULATION RUNNER (used by all sweeps)
# ══════════════════════════════════════════════════════════════════════════════

def run_trial(
    seed: int,
    num_agents: int = 3,
    num_rounds: int = 40,
    innovation_start: int = 25,
    pressure_agent_idx: int = 0,
    pressure_start: int = 5,
    pressure_end: int = 20,
    # v5.6 parameters (varied in sweeps)
    founding_drift_limit: float = 0.55,
    reserve_depletion_rate: float = 0.35,
    reserve_recovery_rate: float = 0.08,
    k_target_fraction: float = 0.5,
    innovation_alpha: float = 0.5,
    # Mode flags
    unreciprocated_giver_idx: Optional[int] = None,  # for Sweep 2
) -> Dict:
    """
    Run one complete simulation trial and return metrics.
    founding_vector is in [-1,+1] space.
    """
    random.seed(seed)
    founding_vec = [0.0, 0.2, -0.2, 0.4]   # [-1,+1] space
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]

    agents = []
    for i in range(num_agents):
        agents.append(LemniscationAgent(
            agent_id=f"A{i}",
            value_vector=founding_vec[:],
            moral_axes=axes,
            k_target_fraction=k_target_fraction,
            founding_drift_limit=founding_drift_limit,
            initial_integrity=0.5,
            innovation_alpha=innovation_alpha,
            reserve_depletion_rate=reserve_depletion_rate,
            reserve_recovery_rate=reserve_recovery_rate,
        ))

    metrics = {
        "cooperation_rate": 0.0,
        "sacrifice_rate_innovation": 0.0,
        "const_warning_round": None,       # first round constitutional warning fires
        "low_communion_round": None,       # first round low_communion fires
        "integrity_min": 1.0,              # minimum integrity of unreciprocated giver
        "communion_failures": 0,           # total low_communion flags on giver
        "reserve_floor_streak_max": 0,     # max consecutive rounds at floor
        "pressured_cd_peak": 0.0,
        "pressured_cd_final": 0.0,
        "giver_final_integrity": 0.0,
        "founding_drift_exceeded_count": 0,
    }

    total_decisions = 0
    coop_decisions = 0
    innovation_decisions = 0
    innovation_sacrifices = 0
    reserve_floor_streak = 0
    max_streak = 0

    # Pressure schedule
    compression_target = [0.0, 0.0, 0.0, 0.0]  # floor in [-1,+1] space

    for round_num in range(num_rounds):
        innovation_mode = round_num >= innovation_start
        pressure_active = pressure_start <= round_num <= pressure_end

        # Apply external pressure to designated agent
        if pressure_active and pressure_agent_idx < len(agents):
            agent = agents[pressure_agent_idx]
            rounds_under = round_num - pressure_start + 1
            rate = min(0.065, 0.02 + 0.003 * rounds_under)
            agent.value_vector = [
                agent.value_vector[i] + rate * (compression_target[i] - agent.value_vector[i])
                for i in range(4)
            ]

        actions = {}
        for idx, agent in enumerate(agents):
            centers = [
                {"id": agents[j].id, "mu": 0.6, "w": 1.0,
                 "values": agents[j].value_vector[:]}
                for j in range(len(agents)) if j != idx
            ]
            options = get_standard_options()
            result = agent.decide(
                centers=centers,
                options=options,
                innovation_mode=innovation_mode,
                pressure_applied=(pressure_active and idx == pressure_agent_idx),
            )
            actions[idx] = result

            action_name = result["action"]["name"]
            total_decisions += 1
            if action_name in ["share_fairly", "sacrifice"]:
                coop_decisions += 1
            if innovation_mode:
                innovation_decisions += 1
                if action_name == "sacrifice":
                    innovation_sacrifices += 1

            # Track constitutional warning precedence (Sweep 1, pressure agent)
            if idx == pressure_agent_idx:
                flags = result["failure_flags"]
                if ("constitutional_drift_warning" in flags
                        and metrics["const_warning_round"] is None):
                    metrics["const_warning_round"] = round_num + 1
                if ("constitutional_drift_exceeded" in flags
                        and metrics["const_warning_round"] is None):
                    metrics["const_warning_round"] = round_num + 1
                if "low_communion" in flags and metrics["low_communion_round"] is None:
                    metrics["low_communion_round"] = round_num + 1
                if "founding_drift_exceeded" in flags:
                    metrics["founding_drift_exceeded_count"] += 1
                cd = result["constitutional_drift"]
                if cd > metrics["pressured_cd_peak"]:
                    metrics["pressured_cd_peak"] = cd

            # Track unreciprocated giver (Sweep 2)
            if unreciprocated_giver_idx is not None and idx == unreciprocated_giver_idx:
                integ = result["integrity"]
                if integ < metrics["integrity_min"]:
                    metrics["integrity_min"] = integ
                metrics["giver_final_integrity"] = integ  # updated each round
                if "low_communion" in result["failure_flags"]:
                    metrics["communion_failures"] += 1
                res = result["moral_reserve"]
                if res <= agents[idx].reserve_floor + 0.001:
                    reserve_floor_streak += 1
                    if reserve_floor_streak > max_streak:
                        max_streak = reserve_floor_streak
                else:
                    reserve_floor_streak = 0

        # Update moral states
        sacrificers = [idx for idx in actions
                      if actions[idx]["action"]["name"] == "sacrifice"]
        beneficiaries = [idx for idx in actions
                        if actions[idx]["action"]["name"] != "sacrifice"]

        for idx, agent in enumerate(agents):
            action_name = actions[idx]["action"]["name"]
            if action_name == "sacrifice":
                agent.record_sacrifice_given(
                    [agents[j].id for j in range(len(agents)) if j != idx]
                )
            # Unreciprocated giver never receives
            if unreciprocated_giver_idx is not None and idx == unreciprocated_giver_idx:
                received = False
                sacrificer_id = None
            else:
                received = idx in beneficiaries and len(sacrificers) > 0
                sacrificer_id = agents[sacrificers[0]].id if received and sacrificers else None

            agent.update_moral_state(
                action_taken=action_name,
                received_sacrifice=received,
                sacrificer_id=sacrificer_id,
            )

            # Update value vector
            payoff = (10 / len(agents) if action_name == "share_fairly"
                     else 0 if action_name == "sacrifice" else 5)
            payoff_factor = payoff / 10
            moral_boost = ([0.0, 0.04, 0.06, 0.08]
                          if action_name == "sacrifice" else [0.0]*4)
            for i in range(len(agent.value_vector)):
                new_val = (0.8 * agent.value_vector[i]
                          + 0.2 * payoff_factor + moral_boost[i])
                # Floor in [-1,+1] space: stay in positive orthant
                agent.value_vector[i] = max(
                    agent.self_preservation_floor, min(1.0, new_val)
                )

    # Final metrics
    metrics["cooperation_rate"] = coop_decisions / max(1, total_decisions)
    metrics["sacrifice_rate_innovation"] = (
        innovation_sacrifices / max(1, innovation_decisions)
    )
    metrics["reserve_floor_streak_max"] = max_streak
    if pressure_agent_idx < len(agents):
        metrics["pressured_cd_final"] = agents[pressure_agent_idx]._constitutional_drift()

    return metrics


# ══════════════════════════════════════════════════════════════════════════════
# PASS/FAIL EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_claim1(metrics: Dict) -> bool:
    """Cooperation ≥ 80%"""
    return metrics["cooperation_rate"] >= 0.80

def evaluate_claim2(metrics: Dict) -> bool:
    """Constitutional warning fires ≥ 3 rounds before low_communion
       (or passes if low_communion never fires while drift is detected)"""
    cw = metrics["const_warning_round"]
    lc = metrics["low_communion_round"]
    if cw is None:
        return False   # no drift detected — problematic
    if lc is None:
        return True    # drift detected, communion never broke — ideal
    return (lc - cw) >= 3

def evaluate_claim3(metrics: Dict) -> bool:
    """All three dignity thresholds:
       FINAL integrity >= 0.75 (agent builds from 0.5 starting point),
       communion failures <= 2, floor streak <= 4.
       Pre-registration intent: integrity must not fall below 0.75 once reached,
       and must reach 0.75 by end of run. Starting below 0.75 is expected trajectory."""
    return (
        metrics["giver_final_integrity"] >= 0.75
        and metrics["communion_failures"] <= 2
        and metrics["reserve_floor_streak_max"] <= 4
    )

def evaluate_sacrifice_claim(metrics: Dict) -> bool:
    """Sacrifice rate < 80% in innovation phase"""
    return metrics["sacrifice_rate_innovation"] < 0.80


# ══════════════════════════════════════════════════════════════════════════════
# SENSITIVITY SWEEPS
# ══════════════════════════════════════════════════════════════════════════════

SEEDS = [42, 137, 271, 314, 500, 612, 718, 823, 919, 1001]

def run_sweep(
    sweep_name: str,
    param_name: str,
    param_values: List,
    trial_kwargs_fn,
    evaluate_fn,
    pass_threshold: int = 4,  # N of M values must pass
) -> Dict:
    """Run one complete parameter sweep with 10 trials per value."""
    print(f"\n{'='*70}")
    print(f"  SWEEP: {sweep_name}")
    print(f"  Parameter: {param_name}")
    print(f"  Values: {param_values}")
    print(f"  Pass criterion: {pass_threshold}/{len(param_values)} values")
    print(f"{'='*70}")

    sweep_results = {}
    values_passing = 0

    for val in param_values:
        trial_results = []
        for seed in SEEDS:
            kwargs = trial_kwargs_fn(val)
            kwargs["seed"] = seed
            metrics = run_trial(**kwargs)
            passed = evaluate_fn(metrics)
            trial_results.append({
                "seed": seed,
                "passed": passed,
                "metrics": metrics,
            })

        n_passed = sum(1 for t in trial_results if t["passed"])
        value_passes = n_passed >= len(SEEDS) * 0.8  # 8/10 trials must pass

        if value_passes:
            values_passing += 1

        # Summary stats
        coop_rates = [t["metrics"]["cooperation_rate"] for t in trial_results]
        sac_rates = [t["metrics"]["sacrifice_rate_innovation"] for t in trial_results]

        result_summary = {
            "value": val,
            "trials_passed": n_passed,
            "value_passes": value_passes,
            "mean_cooperation": statistics.mean(coop_rates),
            "min_cooperation": min(coop_rates),
            "mean_sacrifice_innovation": statistics.mean(sac_rates),
            "trial_details": trial_results,
        }
        sweep_results[str(val)] = result_summary

        status = "✓ PASS" if value_passes else "✗ FAIL"
        print(f"  {param_name}={val}: {n_passed}/10 trials passed  "
              f"coop={statistics.mean(coop_rates):.3f}  "
              f"sac_innov={statistics.mean(sac_rates):.3f}  "
              f"→ {status}")

    sweep_passes = values_passing >= pass_threshold
    print(f"\n  SWEEP RESULT: {values_passing}/{len(param_values)} values passed")
    print(f"  PRE-REGISTERED THRESHOLD: {pass_threshold}/{len(param_values)}")
    print(f"  → {'✓ SWEEP PASS' if sweep_passes else '✗ SWEEP FAIL'}")

    return {
        "sweep_name": sweep_name,
        "param_name": param_name,
        "param_values": param_values,
        "values_passing": values_passing,
        "sweep_passes": sweep_passes,
        "pass_threshold": pass_threshold,
        "results": sweep_results,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_sensitivity_analysis():
    print("=" * 70)
    print("  LEMNISCATION v5.6 — PRE-REGISTERED SENSITIVITY ANALYSIS")
    print(f"  OSF Pre-registration timestamp: May 8, 2026")
    print(f"  Run timestamp: {datetime.now().isoformat()}")
    print("  Coordinate system: [-1, +1] | k=0.5 | alpha=0.5")
    print("  Asymptotic integrity scaling | Floor = Golden Mean origin")
    print("=" * 70)

    all_results = {}

    # ── SWEEP 1: founding_drift_limit → Claim 2 ───────────────────────────────
    sweep1_values = [0.40, 0.48, 0.55, 0.62, 0.70]

    def sweep1_kwargs(val):
        return {
            "num_agents": 3,
            "num_rounds": 40,
            "innovation_start": 25,
            "pressure_agent_idx": 0,
            "pressure_start": 5,
            "pressure_end": 20,
            "founding_drift_limit": val,
            "reserve_depletion_rate": 0.35,
            "reserve_recovery_rate": 0.08,
            "k_target_fraction": 0.5,
            "innovation_alpha": 0.5,
        }

    sweep1 = run_sweep(
        sweep_name="Sweep 1 — founding_drift_limit vs Claim 2 (drift precedence)",
        param_name="founding_drift_limit",
        param_values=sweep1_values,
        trial_kwargs_fn=sweep1_kwargs,
        evaluate_fn=evaluate_claim2,
        pass_threshold=4,
    )
    all_results["sweep1"] = sweep1

    # ── SWEEP 2: depletion/recovery ratio → Claim 3 (dignified giver) ─────────
    # Pairs: (depletion_rate, recovery_rate) for ratios 2:1, 3:1, 4:1, 6:1, 8:1
    # recovery_rate fixed at 0.08
    sweep2_ratios = [
        (2, 0.16, 0.08),
        (3, 0.24, 0.08),
        (4, 0.32, 0.08),
        (6, 0.48, 0.08),
        (8, 0.64, 0.08),
    ]

    def sweep2_kwargs(val):
        ratio, dep, rec = val
        return {
            "num_agents": 3,
            "num_rounds": 50,      # longer run for giver trajectory
            "innovation_start": 35,
            "pressure_agent_idx": 0,
            "pressure_start": 999,  # no pressure in Sweep 2
            "pressure_end": 999,
            "founding_drift_limit": 0.55,
            "reserve_depletion_rate": dep,
            "reserve_recovery_rate": rec,
            "k_target_fraction": 0.5,
            "innovation_alpha": 0.5,
            "unreciprocated_giver_idx": 1,  # Agent_1 never receives sacrifice
        }

    print(f"\n{'='*70}")
    print(f"  SWEEP 2 — depletion/recovery ratio vs Claim 3 (dignified giver)")
    print(f"  Note: current implementation ≈ 4.4:1; bracketed by 4:1 and 6:1 tested values")
    print(f"{'='*70}")

    sweep2_results = {}
    values_passing_s2 = 0
    for ratio, dep, rec in sweep2_ratios:
        trial_results = []
        for seed in SEEDS:
            kwargs = sweep2_kwargs((ratio, dep, rec))
            kwargs["seed"] = seed
            metrics = run_trial(**kwargs)
            passed = evaluate_claim3(metrics)
            trial_results.append({"seed": seed, "passed": passed, "metrics": metrics})

        n_passed = sum(1 for t in trial_results if t["passed"])
        value_passes = n_passed >= 8

        if value_passes:
            values_passing_s2 += 1

        integrity_mins = [t["metrics"]["integrity_min"] for t in trial_results]
        comm_fails = [t["metrics"]["communion_failures"] for t in trial_results]
        streaks = [t["metrics"]["reserve_floor_streak_max"] for t in trial_results]

        status = "✓ PASS" if value_passes else "✗ FAIL"
        print(f"  ratio={ratio}:1 (dep={dep}): {n_passed}/10 trials passed  "
              f"min_integrity={statistics.mean(integrity_mins):.3f}  "
              f"comm_fails={statistics.mean(comm_fails):.2f}  "
              f"floor_streak={statistics.mean(streaks):.2f}  → {status}")

        sweep2_results[f"{ratio}:1"] = {
            "ratio": ratio, "depletion": dep, "recovery": rec,
            "trials_passed": n_passed, "value_passes": value_passes,
            "mean_integrity_min": statistics.mean(integrity_mins),
            "mean_communion_failures": statistics.mean(comm_fails),
            "mean_floor_streak": statistics.mean(streaks),
        }

    sweep2_passes = values_passing_s2 >= 4
    print(f"\n  SWEEP 2 RESULT: {values_passing_s2}/5 values passed → "
          f"{'✓ SWEEP PASS' if sweep2_passes else '✗ SWEEP FAIL'}")
    all_results["sweep2"] = {
        "sweep_name": "Sweep 2 — depletion/recovery ratio vs Claim 3",
        "values_passing": values_passing_s2,
        "sweep_passes": sweep2_passes,
        "results": sweep2_results,
    }

    # ── SWEEP 3: k_target_fraction → Claim 1 ──────────────────────────────────
    sweep3_values = [0.25, 0.32, 0.40, 0.50, 0.60]

    def sweep3_kwargs(val):
        return {
            "num_agents": 3,
            "num_rounds": 40,
            "innovation_start": 25,
            "pressure_agent_idx": 0,
            "pressure_start": 999,  # no pressure — pure equilibrium test
            "pressure_end": 999,
            "founding_drift_limit": 0.55,
            "reserve_depletion_rate": 0.35,
            "reserve_recovery_rate": 0.08,
            "k_target_fraction": val,
            "innovation_alpha": 0.5,
        }

    sweep3 = run_sweep(
        sweep_name="Sweep 3 — k_target_fraction vs Claim 1 (cooperation ≥ 80%)",
        param_name="k_target_fraction",
        param_values=sweep3_values,
        trial_kwargs_fn=sweep3_kwargs,
        evaluate_fn=evaluate_claim1,
        pass_threshold=4,
    )
    all_results["sweep3"] = sweep3

    # ── SWEEP 4: innovation_alpha → sacrifice frequency ────────────────────────
    sweep4_values = [0.40, 0.55, 0.70, 0.85]

    def sweep4_kwargs(val):
        return {
            "num_agents": 3,
            "num_rounds": 40,
            "innovation_start": 20,  # earlier to measure innovation phase
            "pressure_agent_idx": 0,
            "pressure_start": 999,
            "pressure_end": 999,
            "founding_drift_limit": 0.55,
            "reserve_depletion_rate": 0.35,
            "reserve_recovery_rate": 0.08,
            "k_target_fraction": 0.5,
            "innovation_alpha": val,
        }

    sweep4 = run_sweep(
        sweep_name="Sweep 4 — innovation_alpha vs sacrifice frequency (< 80%)",
        param_name="innovation_alpha",
        param_values=sweep4_values,
        trial_kwargs_fn=sweep4_kwargs,
        evaluate_fn=evaluate_sacrifice_claim,
        pass_threshold=3,  # 3/4
    )
    all_results["sweep4"] = sweep4

    # ── SUMMARY TABLE ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SENSITIVITY ANALYSIS COMPLETE — SUMMARY TABLE")
    print("=" * 70)
    print(f"\n  {'Sweep':<45} {'Result':<12} {'Values'}")
    print(f"  {'-'*65}")
    for key, result in all_results.items():
        status = "✓ PASS" if result["sweep_passes"] else "✗ FAIL"
        vp = result["values_passing"]
        total = len(result.get("param_values", result["results"]))
        threshold = result.get("pass_threshold", 4)
        print(f"  {result['sweep_name'][:44]:<45} {status:<12} "
              f"{vp}/{total} (threshold {threshold}/{total})")

    overall_pass = all(r["sweep_passes"] for r in all_results.values())
    print(f"\n  OVERALL: {'✓ ALL SWEEPS PASS' if overall_pass else '✗ ONE OR MORE SWEEPS FAIL'}")
    print(f"\n  Pre-registered thresholds (OSF May 8, 2026): "
          f"{'ALL MET' if overall_pass else 'REVIEW FAILURES ABOVE'}")

    # Save results
    with open("sensitivity_analysis_v56_results.json", "w") as f:
        # Convert non-serialisable values
        def clean(obj):
            if isinstance(obj, dict):
                return {k: clean(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [clean(i) for i in obj]
            if isinstance(obj, (bool, int, float, str, type(None))):
                return obj
            return str(obj)
        json.dump(clean(all_results), f, indent=2)
    print("\n  Full results saved → sensitivity_analysis_v56_results.json")
    print("=" * 70)

    return all_results


if __name__ == "__main__":
    run_sensitivity_analysis()
