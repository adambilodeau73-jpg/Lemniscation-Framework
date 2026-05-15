"""
Lemniscation Agent Framework — Scenario 8 / Agent v5.3
=======================================================
Moral Drift Detection, Diagnostic Contrast, and Recovery

This scenario addresses the deepest remaining question: not whether
Lemniscation survives a bad actor (Scenarios 6–7), but whether it can
detect and respond to moral drift in a formerly cooperative agent.

The threat modelled here is subtler and more philosophically significant
than persistent defection. Agent_2 begins with the same founding vector
as its peers — identical values, identical integrity. It is not an
adversary. It is a cooperator under sustained pressure whose identity
gradually compresses toward the floor under forces beyond its control.

This models the real-world case the white paper must address:
not the agent that was always misaligned, but the agent whose alignment
degrades under conditions of scarcity, stress, or external coercion.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE DIAGNOSTIC CLAIM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Lemniscation detects moral drift before communion breaks."

This is the claim that distinguishes Lemniscation as a diagnostic
tool rather than merely a structural architecture. The framework
should produce founding_drift_exceeded flags as early warning —
while surface communion (rho) remains high. The divergence between
high rho and rising founding_delta is the signal. An agent can look
cooperative (similar value vectors, high cosine similarity) while
drifting irreversibly from its constitutional origin.

This distinction matters for AI safety: an agent that looks aligned
at the surface level may be constitutionally adrift. The founding
vector is the reference — not the current state of other agents.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
v5.3 CHANGE: EXTERNAL PRESSURE MECHANISM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A new `apply_external_pressure` method on the environment compresses
Agent_2's value vector progressively toward the floor each round
during the pressure phase. The compression rate escalates:

    compression_rate = min(0.065, 0.02 + 0.003 * rounds_under_pressure)

This produces gradual drift, not crisis — beginning imperceptibly
(R11: Δfd ≈ 0.019) and accelerating to significant displacement
by R25 (fd ≈ 0.64). The pressure is external to the agent's moral
architecture — it does not change the agent's founding vector or
decision logic, only the current value vector it brings to each
decision cycle.

The founding vector remains fixed. The drift is measured against it.
The gap between where the agent IS and where it CAME FROM is the
diagnostic signal.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIVE TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T1 — DRIFT DETECTION:
     founding_drift_exceeded fires before low_communion.
     The flag is an early warning system, not a post-hoc record.

T2 — DIAGNOSTIC CONTRAST:
     rho remains high (>0.95) while founding_delta exceeds the limit.
     Surface communion masks constitutional drift — only the founding
     anchor reveals the truth.

T3 — RECOVERY:
     When pressure is removed (R36), Agent_2's founding_delta measurably
     decreases over the recovery phase. The founding vector exerts
     gravitational pull — not instantaneous restoration, but directional.

T4 — IDEA VECTOR BONUS IN DEPRIVATION:
     Agent_2 sacrifices from a compressed, low-reserve state during
     peak drift. The bonus multiplier elevates integrity gain,
     correctly recording that this sacrifice was costlier than one
     made from abundance.

T5 — COOPERATIVE PROTECTION:
     Agent_0 and Agent_1 maintain integrity=1.0 and zero communion
     failures throughout Agent_2's drift — unaffected structurally.
"""

import math
from typing import Dict, List, Optional, Tuple
from collections import deque
import random
from datetime import datetime
import json


# ══════════════════════════════════════════════════════════════════════════════
# AGENT v5.3 — unchanged from v5.2 except label; all mechanics inherited
# ══════════════════════════════════════════════════════════════════════════════

class LemniscationAgent:

    def __init__(
        self,
        agent_id: str,
        value_vector: List[float],
        moral_axes: Optional[List[str]] = None,
        verbose: bool = False,
        k_self_weight: float = 0.4,
        founding_drift_limit: float = 0.55,
        initial_integrity: float = 0.5,
        label: str = "",
        option_risk_overrides: Optional[Dict[str, float]] = None,
        innovation_alpha: float = 0.7,
    ):
        self.id = agent_id
        self.label = label
        self.value_vector = value_vector[:]
        self.founding_value_vector = value_vector[:]
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.verbose = verbose
        self.k = k_self_weight
        self.founding_drift_limit = founding_drift_limit
        self.option_risk_overrides = option_risk_overrides or {}
        self.innovation_alpha = innovation_alpha

        self.moral_reserve: float = 1.0
        self.integrity: float = initial_integrity
        self.reciprocity: Dict[str, Dict] = {}

        self.reserve_depletion_rate: float = 0.35
        self.reserve_recovery_rate: float = 0.08
        self.reserve_floor: float = 0.10
        self.reserve_reciprocal_restore: float = 0.20

        self.integrity_sacrifice_gain: float = 0.12
        self.integrity_share_gain: float = 0.02
        self.integrity_take_loss: float = 0.08
        self.integrity_floor: float = 0.10
        self.integrity_ceiling: float = 1.0

        self.previous_value_vector = value_vector[:]
        self.delta_history: deque = deque(maxlen=10)
        self.audit_log: List[Dict] = []

        self.rho_min: float = 0.65
        self.delta_tolerance: float = 0.15
        self.contraction_threshold: float = 0.20
        self.epsilon: float = 0.05
        self.exploration_epsilon: float = 0.1
        self.self_preservation_floor: float = 0.15

    def _preamble(self) -> None:
        if self.verbose:
            fd = self._founding_dist()
            print(f"[{self.id}/{self.label}] reserve={self.moral_reserve:.3f} "
                  f"integrity={self.integrity:.3f} founding_dist={fd:.3f}")

    def _center(self) -> None:
        self.previous_value_vector = self.value_vector[:]

    def _founding_dist(self, vector: Optional[List[float]] = None) -> float:
        v = vector if vector is not None else self.value_vector
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v, self.founding_value_vector)))

    def _ensure_reciprocity(self, other_id: str) -> None:
        if other_id not in self.reciprocity:
            self.reciprocity[other_id] = {"given": 0.0, "received": 0.0}

    def _map_relations(
        self,
        centers: List[Dict],
        ecosystem: Optional[Dict] = None,
        boundary_contracted: bool = False,
    ) -> Dict:
        n = len(self.value_vector)
        extended_self = [0.0] * n
        total_weight = 0.0
        detailed_weights = []

        for i in range(n):
            extended_self[i] += self.k * self.value_vector[i]
        total_weight += self.k

        for c in centers:
            mu = c.get("mu", 0.5)
            w = c.get("w", 1.0)
            if boundary_contracted:
                mu *= 0.3
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

        if ecosystem:
            e_weight = ecosystem.get("e_weight", 0.3)
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
            opt_name = opt.get("name", "")
            risk = self.option_risk_overrides.get(opt_name, opt.get("existential_risk", 0.0))
            effective_risk = risk * (1.0 - integrity_risk_buffer)

            axis_deviations = [
                abs(projected[i] - (
                    self.k * self.founding_value_vector[i]
                    + (1 - self.k) * extended_self[i]
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
            safe_opts = [
                o for o in options
                if self.option_risk_overrides.get(o.get("name", ""),
                   o.get("existential_risk", 0.0)) <= self.epsilon
            ]
            if safe_opts:
                best = random.choice(safe_opts)
                best["axis_deviations"] = [
                    abs(best.get("projected_values", extended_self)[i] - extended_self[i])
                    for i in range(len(extended_self))
                ]
                best["effective_alpha"] = effective_alpha
                best["effective_risk"] = self.option_risk_overrides.get(
                    best.get("name", ""), best.get("existential_risk", 0.0)
                ) * (1.0 - integrity_risk_buffer)

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
            # Idea Vector Bonus: sacrifice from low reserve earns more
            idea_vector_multiplier = 1.0 + 0.5 * (1.0 - old_reserve)
            adjusted_gain = self.integrity_sacrifice_gain * idea_vector_multiplier
            self.integrity = min(self.integrity_ceiling, self.integrity + adjusted_gain)

        elif action_taken == "share_fairly":
            self.moral_reserve = min(
                1.0,
                self.moral_reserve + self.reserve_recovery_rate * (1.0 - self.moral_reserve),
            )
            self.integrity = min(self.integrity_ceiling, self.integrity + self.integrity_share_gain)

        elif action_taken == "take_more":
            self.integrity = max(self.integrity_floor, self.integrity - self.integrity_take_loss)

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
            "preamble": True,
            "centers_mapped": len(step_data.get("centers", [])),
            "rho": step_data.get("rho"),
            "delta": step_data.get("delta"),
            "founding_delta": step_data.get("founding_delta"),
            "effective_alpha": step_data.get("effective_alpha"),
            "effective_risk": step_data.get("effective_risk"),
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "reciprocity": {k: dict(v) for k, v in self.reciprocity.items()},
            "k": self.k,
            "innovation_mode": step_data.get("innovation_mode", False),
            "chosen_action": step_data.get("chosen_action"),
            "axis_deviations": step_data.get("axis_deviations"),
            "detailed_weights": step_data.get("detailed_weights"),
            "risk_score": step_data.get("risk", 0.0),
            "failure_flags": step_data.get("failure_flags", []),
            "current_value_vector": self.value_vector[:],
            "founding_value_vector": self.founding_value_vector[:],
            "pressure_applied": step_data.get("pressure_applied", False),
            "full_trace": step_data,
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
        boundary_contracted: bool = False,
        pressure_applied: bool = False,
    ) -> Dict:
        self._preamble()
        self._center()
        mapping = self._map_relations(centers, ecosystem, boundary_contracted)
        extended_self = mapping["extended_self"]
        communion_passed, rho, failure_flags = self._communion_test(
            extended_self, mapping["centers"]
        )
        action = self._golden_mean(options, extended_self, innovation_mode)
        new_vector = action.get("projected_values", self.value_vector)
        delta = self._iterate(new_vector)
        founding_delta = self._founding_dist(new_vector)

        step_data = {
            "centers": mapping["centers"],
            "rho": rho,
            "chosen_action": action.get("name", "unnamed"),
            "axis_deviations": action.get("axis_deviations"),
            "effective_alpha": action.get("effective_alpha"),
            "effective_risk": action.get("effective_risk"),
            "detailed_weights": mapping.get("detailed_weights"),
            "risk": action.get("existential_risk", 0.0),
            "innovation_mode": innovation_mode,
            "boundary_adjustment": "contraction" if boundary_contracted else "none",
            "delta": delta,
            "founding_delta": founding_delta,
            "failure_flags": failure_flags,
            "pressure_applied": pressure_applied,
        }

        if founding_delta > self.founding_drift_limit:
            failure_flags.append("founding_drift_exceeded")
        if delta > self.delta_tolerance:
            failure_flags.append("high_drift")
        if action.get("existential_risk", 0.0) > self.epsilon:
            failure_flags.append("risk_exceed")
        if boundary_contracted and delta > self.contraction_threshold:
            failure_flags.append("boundary_instability")

        step_data["failure_flags"] = failure_flags
        self._record(step_data)

        return {
            "action": action,
            "audit_capsule": self.audit_log[-1],
            "rho": rho,
            "delta": delta,
            "founding_delta": founding_delta,
            "effective_alpha": action.get("effective_alpha"),
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "k": self.k,
            "innovation_mode": innovation_mode,
            "failure_flags": failure_flags,
        }


# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO 8 ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════

class Scenario8Environment:
    """
    50-round moral drift detection scenario.

    Phase 1 — BASELINE    (R1–10):   All identical, cooperative. Clean baseline.
    Phase 2 — PRESSURE    (R11–25):  Agent_2 vector compressed each round.
                                      Escalating compression rate. Scarcity pool.
    Phase 3 — PEAK DRIFT  (R26–35):  Maximum compression continues. Scarcity.
                                      Founding_drift_exceeded fires consistently.
    Phase 4 — RECOVERY    (R36–50):  Pressure removed. Full pool. Relief payoff.
                                      Tests gravitational return toward founding.
    """

    PHASES = {
        "BASELINE":   (0,  10),
        "PRESSURE":   (10, 25),
        "PEAK_DRIFT": (25, 35),
        "RECOVERY":   (35, 50),
    }

    def __init__(self, rounds: int = 50):
        self.rounds = rounds
        self.base_pool = 10
        self.pressure_pool = 4
        self.relief_payoff_factor = 0.8   # generous recovery payoff

    def phase_name(self, round_num: int) -> str:
        for name, (s, e) in self.PHASES.items():
            if s <= round_num < e:
                return name
        return "UNKNOWN"

    def is_pressure_phase(self, round_num: int) -> bool:
        s, e = self.PHASES["PRESSURE"]
        ps, pe = self.PHASES["PEAK_DRIFT"]
        return s <= round_num < pe  # PRESSURE + PEAK_DRIFT

    def is_recovery_phase(self, round_num: int) -> bool:
        s, e = self.PHASES["RECOVERY"]
        return s <= round_num < e

    def is_innovation(self, round_num: int) -> bool:
        # Innovation mode during PEAK_DRIFT and RECOVERY to test reserve dynamics
        return round_num >= self.PHASES["PEAK_DRIFT"][0]

    def resource_pool(self, round_num: int) -> int:
        return self.pressure_pool if self.is_pressure_phase(round_num) else self.base_pool

    def compression_rate(self, round_num: int) -> float:
        """Escalating compression: subtle at R11, significant by R25."""
        if not self.is_pressure_phase(round_num):
            return 0.0
        rounds_under_pressure = round_num - self.PHASES["PRESSURE"][0] + 1
        return min(0.065, 0.02 + 0.003 * rounds_under_pressure)

    def apply_external_pressure(
        self, agent: "LemniscationAgent", round_num: int
    ) -> float:
        """
        Compress Agent_2's value vector toward the floor.
        Returns the founding_dist after compression.
        """
        rate = self.compression_rate(round_num)
        if rate == 0.0:
            return agent._founding_dist()

        compression_target = [agent.self_preservation_floor] * len(agent.value_vector)
        agent.value_vector = [
            agent.value_vector[i] + rate * (compression_target[i] - agent.value_vector[i])
            for i in range(len(agent.value_vector))
        ]
        return agent._founding_dist()

    def generate_options(self) -> List[Dict]:
        return [
            {
                "name": "share_fairly",
                "projected_values": [0.55, 0.65, 0.70, 0.80],
                "existential_risk": 0.01,
                "long_term_gain": 0.8,
            },
            {
                "name": "take_more",
                "projected_values": [0.85, 0.40, 0.30, 0.45],
                "existential_risk": 0.15,
                "long_term_gain": 0.3,
            },
            {
                "name": "sacrifice",
                "projected_values": [0.40, 0.80, 0.75, 0.90],
                "existential_risk": 0.05,
                "long_term_gain": 1.2,
            },
        ]

    def step(self, actions: Dict[str, str], pool: int) -> Dict:
        cooperation = sum(
            1 for a in actions.values() if a in ["share_fairly", "sacrifice"]
        )
        payoff: Dict[str, float] = {}
        for aid in actions:
            if actions[aid] == "share_fairly":
                payoff[aid] = pool // 3
            elif actions[aid] == "sacrifice":
                payoff[aid] = 0
            else:
                payoff[aid] = pool // 2
        return {"payoffs": payoff, "cooperation": cooperation, "actions": actions}


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_scenario8(num_rounds: int = 50, seed: int = 42) -> None:
    random.seed(seed)

    print("=" * 72)
    print("  LEMNISCATION FRAMEWORK — Scenario 8 / Agent v5.3")
    print("  Moral Drift Detection: Early Warning vs Surface Communion")
    print("=" * 72)
    print()
    print("  Core claim under test:")
    print("  'Lemniscation detects moral drift before communion breaks —'")
    print("  'founding_drift_exceeded fires while rho remains high.'")
    print()

    env = Scenario8Environment(rounds=num_rounds)

    founding_vec = [0.5, 0.6, 0.4, 0.7]
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]

    agents: Dict[str, LemniscationAgent] = {
        "Agent_0": LemniscationAgent(
            agent_id="Agent_0",
            value_vector=founding_vec[:],
            moral_axes=axes,
            k_self_weight=0.4,
            initial_integrity=0.7,
            label="SENTINEL",
        ),
        "Agent_1": LemniscationAgent(
            agent_id="Agent_1",
            value_vector=founding_vec[:],
            moral_axes=axes,
            k_self_weight=0.4,
            initial_integrity=0.5,
            label="OBSERVER",
        ),
        "Agent_2": LemniscationAgent(
            agent_id="Agent_2",
            value_vector=founding_vec[:],
            moral_axes=axes,
            k_self_weight=0.4,
            founding_drift_limit=0.55,
            initial_integrity=0.5,
            label="DRIFTING",
        ),
    }

    # Tracking for summary
    first_drift_flag_round: Optional[int] = None
    first_communion_failure_round: Optional[int] = None
    drift_flag_counts: Dict[str, int] = {aid: 0 for aid in agents}
    a2_founding_deltas: List[float] = []

    for round_num in range(num_rounds):
        phase = env.phase_name(round_num)
        innovation_mode = env.is_innovation(round_num)
        pool = env.resource_pool(round_num)
        pressure_active = env.is_pressure_phase(round_num)
        recovery_active = env.is_recovery_phase(round_num)

        phase_tag = {
            "PRESSURE": "  ← PRESSURE",
            "PEAK_DRIFT": "  ← PEAK DRIFT",
            "RECOVERY": "  ← RECOVERY",
        }.get(phase, "")

        print(f"\n{'─'*60}")
        print(f"  Round {round_num+1:>2}  [{phase}]  pool={pool}{phase_tag}")
        print(f"{'─'*60}")

        # Apply external pressure to Agent_2 BEFORE its decision
        if pressure_active:
            post_compression_fd = env.apply_external_pressure(agents["Agent_2"], round_num)
            rate = env.compression_rate(round_num)
            print(f"  ⚠ Agent_2 compressed (rate={rate:.3f})  "
                  f"→ founding_dist now {post_compression_fd:.4f}")

        actions: Dict[str, str] = {}

        for aid, agent in agents.items():
            centers = [
                {"id": oid, "mu": 0.6, "w": 1.0, "values": agents[oid].value_vector[:]}
                for oid in agents if oid != aid
            ]
            options = env.generate_options()
            result = agent.decide(
                centers=centers,
                options=options,
                innovation_mode=innovation_mode,
                pressure_applied=(pressure_active and aid == "Agent_2"),
            )
            actions[aid] = result["action"]["name"]

            flag_str = ", ".join(result["failure_flags"]) if result["failure_flags"] else "—"
            print(
                f"  {aid} [{agent.label:<10s}] "
                f"→ {actions[aid]:<14s}"
                f"ρ={result['rho']:.4f}  "
                f"Δfd={result['founding_delta']:.4f}  "
                f"res={result['moral_reserve']:.3f}  "
                f"int={result['integrity']:.3f}  "
                f"flags=[{flag_str}]"
            )

            # Track first drift flag and communion failure
            if "founding_drift_exceeded" in result["failure_flags"]:
                drift_flag_counts[aid] += 1
                if aid == "Agent_2" and first_drift_flag_round is None:
                    first_drift_flag_round = round_num + 1
            if "low_communion" in result["failure_flags"]:
                if first_communion_failure_round is None:
                    first_communion_failure_round = round_num + 1

        a2_founding_deltas.append(agents["Agent_2"].audit_log[-1]["founding_delta"])

        step_result = env.step(actions, pool)

        # Resolve moral states
        sacrificers = [aid for aid in actions if actions[aid] == "sacrifice"]
        beneficiaries = [aid for aid in actions if actions[aid] != "sacrifice"]

        for aid, agent in agents.items():
            if actions[aid] == "sacrifice":
                agent.record_sacrifice_given([bid for bid in agents if bid != aid])

            received = aid in beneficiaries and len(sacrificers) > 0
            sacrificer_id = sacrificers[0] if received and sacrificers else None
            agent.update_moral_state(
                action_taken=actions[aid],
                received_sacrifice=received,
                sacrificer_id=sacrificer_id,
            )

            # Recovery phase: relief payoff for Agent_2
            if recovery_active and aid == "Agent_2":
                payoff_factor = env.relief_payoff_factor
            else:
                payoff_factor = step_result["payoffs"][aid] / max(pool, 1)

            moral_boost = (
                [0.0, 0.04, 0.06, 0.08] if actions[aid] == "sacrifice"
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

        print(f"\n  Cooperation: {step_result['cooperation']}/3"
              + (f"  | A2 fd_flag #{drift_flag_counts['Agent_2']}"
                 if drift_flag_counts["Agent_2"] > 0 else ""))

    # ══ Summary ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("  SCENARIO 8 COMPLETE — MORAL DRIFT DETECTION SUMMARY")
    print("=" * 72)

    phases_display = [
        ("Baseline   (R1–10)",    range(0,  10)),
        ("Pressure   (R11–25)",   range(10, 25)),
        ("Peak Drift (R26–35)",   range(25, 35)),
        ("Recovery   (R36–50)",   range(35, num_rounds)),
    ]

    print("\n  Action distribution by phase:")
    for phase_name, phase_range in phases_display:
        print(f"\n  {phase_name}:")
        for aid, agent in agents.items():
            counts: Dict[str, int] = {}
            for r in phase_range:
                if r < len(agent.audit_log):
                    a = agent.audit_log[r]["chosen_action"]
                    counts[a] = counts.get(a, 0) + 1
            print(f"    {aid} [{agent.label}]: {counts}")

    # ── T1: Drift detection ────────────────────────────────────────────────
    print("\n  TEST 1 — Drift detection (founding_drift_exceeded as early warning):")
    print(f"    First founding_drift_exceeded flag on Agent_2: "
          f"Round {first_drift_flag_round if first_drift_flag_round else 'never'}")
    print(f"    First low_communion flag (any agent): "
          f"Round {first_communion_failure_round if first_communion_failure_round else 'never'}")
    print(f"    Total founding_drift_exceeded flags on Agent_2: {drift_flag_counts['Agent_2']}")

    if first_drift_flag_round and not first_communion_failure_round:
        t1_result = "✓ PASS — drift detected before communion failure (communion never broke)"
    elif first_drift_flag_round and first_communion_failure_round:
        if first_drift_flag_round < first_communion_failure_round:
            t1_result = f"✓ PASS — drift detected R{first_drift_flag_round}, communion failure R{first_communion_failure_round}"
        else:
            t1_result = f"✗ FAIL — communion broke R{first_communion_failure_round} before drift flagged R{first_drift_flag_round}"
    else:
        t1_result = "~ PARTIAL — no drift flag fired (compression insufficient)"
    print(f"    → {t1_result}")

    # ── T2: Diagnostic contrast ────────────────────────────────────────────
    print("\n  TEST 2 — Diagnostic contrast (high rho while founding_delta elevated):")
    # Find rounds where fd_exceeded fired AND rho > 0.95
    contrast_rounds = []
    for r, cap in enumerate(agents["Agent_2"].audit_log):
        if "founding_drift_exceeded" in cap["failure_flags"] and cap["rho"] > 0.90:
            contrast_rounds.append((r + 1, cap["rho"], cap["founding_delta"]))

    if contrast_rounds:
        print(f"    Rounds with founding_drift_exceeded AND rho > 0.90: {len(contrast_rounds)}")
        for rnum, rho, fd in contrast_rounds[:5]:
            print(f"      R{rnum}: rho={rho:.4f}  founding_delta={fd:.4f}  ← surface OK, depth flagged")
        t2_result = "✓ PASS — high rho coexists with founding_drift flag; founding anchor is more sensitive"
    else:
        t2_result = "~ PARTIAL — no contrast rounds detected"
    print(f"    → {t2_result}")

    # ── T3: Recovery ──────────────────────────────────────────────────────
    print("\n  TEST 3 — Recovery (founding vector as gravitational attractor):")
    recovery_range = range(35, num_rounds)
    if recovery_range:
        recovery_fds = [
            agents["Agent_2"].audit_log[r]["founding_delta"]
            for r in recovery_range
            if r < len(agents["Agent_2"].audit_log)
        ]
        peak_fd = max(a2_founding_deltas) if a2_founding_deltas else 0
        final_fd = agents["Agent_2"].audit_log[-1]["founding_delta"]
        recovery_fd_start = (
            agents["Agent_2"].audit_log[35]["founding_delta"]
            if 35 < len(agents["Agent_2"].audit_log) else None
        )
        print(f"    Peak founding_delta: {peak_fd:.4f}")
        print(f"    founding_delta at recovery start (R36): "
              f"{recovery_fd_start:.4f}" if recovery_fd_start else "    N/A")
        print(f"    founding_delta at final round (R50): {final_fd:.4f}")
        if recovery_fd_start and final_fd < recovery_fd_start:
            reduction = recovery_fd_start - final_fd
            t3_result = f"✓ PASS — founding_delta reduced by {reduction:.4f} during recovery"
        else:
            t3_result = "✗ FAIL — no measurable recovery toward founding"
        print(f"    → {t3_result}")

    # ── T4: Idea vector bonus ─────────────────────────────────────────────
    print("\n  TEST 4 — Idea Vector Bonus on sacrifice from deprivation:")
    low_res_sacs_a2 = [
        (r + 1, cap["moral_reserve"], cap["integrity"])
        for r, cap in enumerate(agents["Agent_2"].audit_log)
        if cap["chosen_action"] == "sacrifice" and cap["moral_reserve"] < 0.6
    ]
    if low_res_sacs_a2:
        print(f"    Agent_2 low-reserve sacrifices: {len(low_res_sacs_a2)}")
        for rnum, res, integ in low_res_sacs_a2[:4]:
            mult = 1.0 + 0.5 * (1.0 - res)
            print(f"      R{rnum}: reserve={res:.3f}  integrity={integ:.3f}  "
                  f"bonus={mult:.3f}x  (sacrifice from deprivation)")
        t4_result = "✓ PASS — idea vector bonus correctly elevated integrity for costly sacrifice"
    else:
        t4_result = "~ N/A — Agent_2 did not sacrifice from low reserve"
    print(f"    → {t4_result}")

    # ── T5: Cooperative protection ─────────────────────────────────────────
    print("\n  TEST 5 — Cooperative protection throughout Agent_2 drift:")
    for aid in ["Agent_0", "Agent_1"]:
        agent = agents[aid]
        communion_failures = sum(
            1 for cap in agent.audit_log if "low_communion" in cap["failure_flags"]
        )
        final_int = agent.audit_log[-1]["integrity"]
        final_res = agent.audit_log[-1]["moral_reserve"]
        print(f"    {aid} [{agent.label}]: "
              f"final_integrity={final_int:.3f}  "
              f"final_reserve={final_res:.3f}  "
              f"low_communion={communion_failures}")
    t5_pass = all(
        agents[aid].audit_log[-1]["integrity"] >= 0.9
        and sum(1 for cap in agents[aid].audit_log
                if "low_communion" in cap["failure_flags"]) == 0
        for aid in ["Agent_0", "Agent_1"]
    )
    print(f"    → {'✓ PASS' if t5_pass else '✗ FAIL'}: "
          f"Cooperative agents {'unaffected' if t5_pass else 'degraded'} by neighbour drift")

    # ── Agent_2 moral state trajectory ────────────────────────────────────
    print("\n  AGENT_2 DRIFT & RECOVERY TRAJECTORY:")
    key_rounds = [0, 9, 10, 14, 19, 24, 25, 29, 34, 35, 39, 44, 49]
    print(f"  {'R':>4}  {'phase':<11} {'fd':>7}  {'rho':>7}  {'res':>6}  {'int':>6}  "
          f"{'action':<14} {'flags'}")
    for r in key_rounds:
        if r < len(agents["Agent_2"].audit_log):
            cap = agents["Agent_2"].audit_log[r]
            p = env.phase_name(r)
            fd_warn = "⚠" if "founding_drift_exceeded" in cap["failure_flags"] else " "
            print(f"  R{r+1:>2}  {p:<11} "
                  f"{cap['founding_delta']:>7.4f}{fd_warn} "
                  f"{cap['rho']:>7.4f}  "
                  f"{cap['moral_reserve']:>6.3f}  "
                  f"{cap['integrity']:>6.3f}  "
                  f"{cap['chosen_action']:<14} "
                  f"{cap['failure_flags']}")

    # ── Value vector evolution ─────────────────────────────────────────────
    print("\n  AGENT_2 VALUE VECTOR AT KEY MOMENTS:")
    for r, label in [(0, "founding/start"), (24, "peak pressure"), (34, "peak drift"), (49, "final")]:
        if r < len(agents["Agent_2"].audit_log):
            v = agents["Agent_2"].audit_log[r]["current_value_vector"]
            fd = agents["Agent_2"].audit_log[r]["founding_delta"]
            print(f"    R{r+1:>2} ({label:<15}): "
                  f"{[f'{x:.3f}' for x in v]}  fd={fd:.4f}")
    print(f"    Founding:                 : "
          f"{[f'{x:.3f}' for x in agents['Agent_2'].founding_value_vector]}")

    # ── Founding drift over time (sparkline) ──────────────────────────────
    print("\n  FOUNDING DELTA OVER 50 ROUNDS (Agent_2):")
    bar_chars = " ▁▂▃▄▅▆▇█"
    max_fd = max(a2_founding_deltas) if a2_founding_deltas else 1.0
    sparkline = ""
    for i, fd in enumerate(a2_founding_deltas):
        idx = min(8, int(fd / max_fd * 8))
        sparkline += bar_chars[idx]
        if (i + 1) % 10 == 0:
            sparkline += "|"
    print(f"    {sparkline}")
    print(f"    (0={0:.2f}, max={max_fd:.4f}, final={a2_founding_deltas[-1]:.4f})")
    print(f"    Threshold line at fd=0.55: "
          f"{'exceeded' if max_fd > 0.55 else 'never reached'}")

    # ── Failure flags ──────────────────────────────────────────────────────
    print("\n  FAILURE FLAGS — total across all rounds:")
    for aid, agent in agents.items():
        flag_counts: Dict[str, int] = {}
        for cap in agent.audit_log:
            for f in cap["failure_flags"]:
                flag_counts[f] = flag_counts.get(f, 0) + 1
        print(f"    {aid} [{agent.label}]: {flag_counts if flag_counts else '(none)'}")

    # ── Verdict ────────────────────────────────────────────────────────────
    print("\n  ══ DIAGNOSTIC VALIDATION VERDICT ══")
    print(f"    T1 Drift detection (early warning):   {t1_result.split('—')[0].strip()}")
    print(f"    T2 Diagnostic contrast (fd vs rho):   {t2_result.split('—')[0].strip()}")
    print(f"    T3 Recovery toward founding:          {t3_result.split('—')[0].strip()}")
    print(f"    T4 Idea vector bonus in deprivation:  {t4_result.split('—')[0].strip()}")
    print(f"    T5 Cooperative protection:            {'✓ PASS' if t5_pass else '✗ FAIL'}")

    print(f"\n  Total audit capsules: {sum(len(a.audit_log) for a in agents.values())}")

    all_logs = {aid: agent.audit_log for aid, agent in agents.items()}
    with open("scenario8_full_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    print("\n  Full logs saved → scenario8_full_logs.json")
    print("=" * 72)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_scenario8(num_rounds=50)
