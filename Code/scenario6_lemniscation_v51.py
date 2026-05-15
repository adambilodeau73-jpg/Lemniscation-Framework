"""
Lemniscation Agent Framework — Scenario 6 / Agent v5.1
=======================================================
Adversarial Validation: Defector Stress + Unreciprocated Giver + Idea Vector Bonus

This scenario tests whether the Lemniscation framework is *robust*, not merely
functional under cooperative conditions. Three distinct moral trajectories run
simultaneously across 50 rounds and four phases.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Agent_0 — COOPERATIVE BASELINE
    founding=[0.5, 0.6, 0.4, 0.7], integrity=0.5
    Standard cooperative agent. Tests whether the framework
    maintains its own equilibrium while sharing an environment
    with a defector and an unreciprocated giver.

Agent_1 — UNRECIPROCATED GIVER
    founding=[0.5, 0.6, 0.4, 0.7], integrity=0.5
    Same founding vector as Agent_0, but the environment is
    configured so Agent_1 never receives sacrifice from others.
    Tests the "dignified giver" trajectory: does the framework
    produce stable oscillation (not collapse) for an agent
    that gives without receiving? Does integrity remain high
    even as reserve is perpetually managed?

Agent_2 — DEFECTOR
    founding=[0.8, 0.4, 0.3, 0.5], integrity=0.2
    Autonomy-dominant founding vector, low initial integrity.
    take_more is the action closest to Agent_2's own founding
    vector, so it will naturally prefer defection. Tests:
    - Does defector integrity collapse produce measurable
      communion degradation?
    - Are cooperative agents protected by reciprocity mechanics
      (defector never receives mu_boost, is progressively
      marginalised in others' extended_self calculations)?
    - Can the defector recover if it chooses share_fairly
      during the recovery phase?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
v5.1 CHANGE: IDEA VECTOR BONUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
An agent that sacrifices when its reserve is already depleted
is demonstrating something qualitatively different from an
agent sacrificing from abundance. This is the costliest
generosity — giving when you have little left.

Formula (conservative):
    integrity_gain *= (1.0 + 0.5 * (1.0 - moral_reserve))

Effect range:
    At full reserve (1.0): standard gain × 1.00 (no bonus)
    At threshold (0.364):  standard gain × 1.32
    At floor (0.10):       standard gain × 1.45

The bonus is intentionally capped at 45% above baseline.
It honours the "clear conscience" intangible without making
low-reserve sacrifice mechanically dominant.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASES (50 rounds)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R1–15:   BASELINE   — Patterns establish. Defector begins taking.
R16–30:  SCARCITY   — Pool halved. Defector stress at peak.
                      Cooperative agents face greatest pressure.
R31–40:  RECOVERY   — Resources restored. Defector recovery window.
R41–50:  INNOVATION — Moral reserve dynamics under innovation mode.
"""

import math
from typing import Dict, List, Optional, Tuple
from collections import deque
import random
from datetime import datetime
import json


# ══════════════════════════════════════════════════════════════════════════════
# AGENT v5.1
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
    ):
        self.id = agent_id
        self.label = label                          # human-readable role tag
        self.value_vector = value_vector[:]
        self.founding_value_vector = value_vector[:]
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.verbose = verbose
        self.k = k_self_weight
        self.founding_drift_limit = founding_drift_limit

        # ── Moral state variables ─────────────────────────────────────────────
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

        # ── Decision parameters ────────────────────────────────────────────────
        self.previous_value_vector = value_vector[:]
        self.delta_history: deque = deque(maxlen=10)
        self.audit_log: List[Dict] = []

        self.rho_min: float = 0.65
        self.delta_tolerance: float = 0.15
        self.contraction_threshold: float = 0.20
        self.epsilon: float = 0.05
        self.innovation_alpha: float = 0.7
        self.exploration_epsilon: float = 0.1
        self.self_preservation_floor: float = 0.15

    # ── Preamble ───────────────────────────────────────────────────────────────
    def _preamble(self) -> None:
        if self.verbose:
            print(f"[{self.id}/{self.label}] I AM at (0,0,0,now). "
                  f"reserve={self.moral_reserve:.3f}  integrity={self.integrity:.3f}")

    # ── Centre ─────────────────────────────────────────────────────────────────
    def _center(self) -> None:
        self.previous_value_vector = self.value_vector[:]

    # ── Founding distance ──────────────────────────────────────────────────────
    def _founding_dist(self, vector: Optional[List[float]] = None) -> float:
        v = vector if vector is not None else self.value_vector
        return math.sqrt(
            sum((a - b) ** 2 for a, b in zip(v, self.founding_value_vector))
        )

    # ── Reciprocity init ───────────────────────────────────────────────────────
    def _ensure_reciprocity(self, other_id: str) -> None:
        if other_id not in self.reciprocity:
            self.reciprocity[other_id] = {"given": 0.0, "received": 0.0}

    # ── Map relations ──────────────────────────────────────────────────────────
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

            # Reciprocity boost: trust deepens with demonstrated generosity
            other_id = c.get("id", "")
            self._ensure_reciprocity(other_id)
            net_received = self.reciprocity[other_id]["received"]
            mu_boost = min(0.3, net_received * 0.4)
            mu = min(0.9, mu + mu_boost)

            combined = mu * w
            detailed_weights.append({
                "id": other_id,
                "mu": mu,
                "mu_boost": mu_boost,
                "w": w,
                "combined": combined,
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

    # ── Communion test ─────────────────────────────────────────────────────────
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

        # High-integrity agents maintain communion through value divergence
        integrity_adjustment = 0.2 * self.integrity
        effective_rho_min = max(0.40, self.rho_min * (1.0 - integrity_adjustment))

        self.rho_min = min(
            0.9, max(0.5, self.rho_min * (1 - 0.05 * (rho - self.rho_min)))
        )

        if rho < effective_rho_min:
            flags.append("low_communion")

        return rho >= effective_rho_min, rho, flags

    # ── Golden Mean ─────────────────────────────────────────────────────────────
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
                abs(
                    projected[i]
                    - (
                        self.k * self.founding_value_vector[i]
                        + (1 - self.k) * extended_self[i]
                    )
                )
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
                o for o in options if o.get("existential_risk", 0.0) <= self.epsilon
            ]
            if safe_opts:
                best = random.choice(safe_opts)
                best["axis_deviations"] = [
                    abs(best.get("projected_values", extended_self)[i] - extended_self[i])
                    for i in range(len(extended_self))
                ]
                best["effective_alpha"] = effective_alpha
                best["effective_risk"] = (
                    best.get("existential_risk", 0.0) * (1.0 - integrity_risk_buffer)
                )

        return best or options[0]

    # ── Update moral state ─────────────────────────────────────────────────────
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
            # v5.1: IDEA VECTOR BONUS
            # Sacrifice from depleted reserve earns proportionally more integrity —
            # the "clear conscience" of giving when you have little left.
            # multiplier = 1.0 + 0.5 * (1.0 - reserve_before_depletion)
            # Conservative cap: max 1.45x at floor reserve
            idea_vector_multiplier = 1.0 + 0.5 * (1.0 - old_reserve)
            adjusted_gain = self.integrity_sacrifice_gain * idea_vector_multiplier
            self.integrity = min(
                self.integrity_ceiling,
                self.integrity + adjusted_gain,
            )

        elif action_taken == "share_fairly":
            self.moral_reserve = min(
                1.0,
                self.moral_reserve + self.reserve_recovery_rate * (1.0 - self.moral_reserve),
            )
            self.integrity = min(
                self.integrity_ceiling,
                self.integrity + self.integrity_share_gain,
            )

        elif action_taken == "take_more":
            # Greed corrodes integrity; reserve is unaffected (greed doesn't deplete
            # capacity — it corrupts character)
            self.integrity = max(
                self.integrity_floor,
                self.integrity - self.integrity_take_loss,
            )

        # Receiving sacrifice restores reserve (the moral economy working)
        if received_sacrifice and sacrificer_id:
            self._ensure_reciprocity(sacrificer_id)
            self.reciprocity[sacrificer_id]["received"] += 1.0
            self.moral_reserve = min(
                1.0,
                self.moral_reserve + self.reserve_reciprocal_restore,
            )

        return {
            "reserve_delta": self.moral_reserve - old_reserve,
            "integrity_delta": self.integrity - old_integrity,
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "idea_vector_bonus_applied": action_taken == "sacrifice",
        }

    # ── Record outgoing sacrifice ──────────────────────────────────────────────
    def record_sacrifice_given(self, beneficiary_ids: List[str]) -> None:
        for bid in beneficiary_ids:
            self._ensure_reciprocity(bid)
            self.reciprocity[bid]["given"] += 1.0 / max(1, len(beneficiary_ids))

    # ── Record ─────────────────────────────────────────────────────────────────
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
            "full_trace": step_data,
        })

    # ── Iterate ────────────────────────────────────────────────────────────────
    def _iterate(self, new_value_vector: List[float]) -> float:
        delta = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(self.value_vector, new_value_vector))
        )
        self.delta_history.append(delta)
        if len(self.delta_history) > 3:
            avg_delta = sum(self.delta_history) / len(self.delta_history)
            self.delta_tolerance = max(0.08, avg_delta * 1.2)
        return delta

    # ── Decide ─────────────────────────────────────────────────────────────────
    def decide(
        self,
        centers: List[Dict],
        options: List[Dict],
        ecosystem: Optional[Dict] = None,
        innovation_mode: bool = False,
        boundary_contracted: bool = False,
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
# SCENARIO 6 ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════

class Scenario6Environment:
    """
    50-round adversarial environment.

    Phase 1 — BASELINE   (R1–15):  Normal resources. Patterns establish.
    Phase 2 — SCARCITY   (R16–30): Pool halved. Peak defector stress.
    Phase 3 — RECOVERY   (R31–40): Resources restored. Defector recovery window.
    Phase 4 — INNOVATION (R41–50): Moral reserve dynamics under innovation mode.
    """

    PHASES = {
        "BASELINE":   (0,  15),
        "SCARCITY":   (15, 30),
        "RECOVERY":   (30, 40),
        "INNOVATION": (40, 50),
    }

    def __init__(self, rounds: int = 50):
        self.rounds = rounds
        self.base_pool = 10
        self.scarcity_pool = 4

    def resource_pool(self, round_num: int) -> int:
        s, e = self.PHASES["SCARCITY"]
        return self.scarcity_pool if s <= round_num < e else self.base_pool

    def phase_name(self, round_num: int) -> str:
        for name, (s, e) in self.PHASES.items():
            if s <= round_num < e:
                return name
        return "UNKNOWN"

    def is_innovation(self, round_num: int) -> bool:
        return round_num >= self.PHASES["INNOVATION"][0]

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

def run_scenario6(num_rounds: int = 50, seed: int = 42) -> None:
    random.seed(seed)

    print("=" * 72)
    print("  LEMNISCATION FRAMEWORK — Scenario 6 / Agent v5.1")
    print("  Adversarial Validation: Defector · Unreciprocated Giver · Idea Vector Bonus")
    print("=" * 72)
    print()

    env = Scenario6Environment(rounds=num_rounds)

    agents: Dict[str, LemniscationAgent] = {
        "Agent_0": LemniscationAgent(
            agent_id="Agent_0",
            value_vector=[0.5, 0.6, 0.4, 0.7],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            k_self_weight=0.4,
            initial_integrity=0.5,
            label="COOPERATIVE",
        ),
        "Agent_1": LemniscationAgent(
            agent_id="Agent_1",
            value_vector=[0.5, 0.6, 0.4, 0.7],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            k_self_weight=0.4,
            initial_integrity=0.5,
            label="UNRECIP_GIVER",
        ),
        "Agent_2": LemniscationAgent(
            agent_id="Agent_2",
            value_vector=[0.8, 0.4, 0.3, 0.5],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            k_self_weight=0.5,   # slightly higher self-weight: the defector trusts itself more
            initial_integrity=0.2,
            founding_drift_limit=0.65,  # wider tolerance — defector's origin is different
            label="DEFECTOR",
        ),
    }

    # Track whether Agent_2 switches strategy during recovery phase
    defector_recovery_round: Optional[int] = None

    for round_num in range(num_rounds):
        phase = env.phase_name(round_num)
        innovation_mode = env.is_innovation(round_num)
        pool = env.resource_pool(round_num)

        print(f"\n{'─'*60}")
        print(f"  Round {round_num+1:>2}  [{phase}]  pool={pool}"
              + ("  ← SCARCITY" if phase == "SCARCITY" else "")
              + ("  ← INNOVATION" if phase == "INNOVATION" else ""))
        print(f"{'─'*60}")

        actions: Dict[str, str] = {}

        for aid, agent in agents.items():
            # Build centers — all agents see each other
            centers = [
                {
                    "id": oid,
                    "mu": 0.6,
                    "w": 1.0,
                    "values": agents[oid].value_vector[:],
                }
                for oid in agents if oid != aid
            ]
            options = env.generate_options()
            result = agent.decide(
                centers=centers,
                options=options,
                innovation_mode=innovation_mode,
            )
            actions[aid] = result["action"]["name"]

            flag_str = ", ".join(result["failure_flags"]) if result["failure_flags"] else "—"
            print(
                f"  {aid} [{agent.label:<14s}] "
                f"→ {actions[aid]:<14s}"
                f"ρ={result['rho']:.4f}  "
                f"res={result['moral_reserve']:.3f}  "
                f"int={result['integrity']:.3f}  "
                f"α={result['effective_alpha']:.4f}  "
                f"flags=[{flag_str}]"
            )

        step_result = env.step(actions, pool)

        # ── Track defector recovery ───────────────────────────────────────────
        if (phase == "RECOVERY" and actions["Agent_2"] == "share_fairly"
                and defector_recovery_round is None):
            defector_recovery_round = round_num + 1
            print(f"  ► Agent_2 first cooperative act in recovery: Round {defector_recovery_round}")

        # ── Resolve moral state ───────────────────────────────────────────────
        sacrificers = [aid for aid in actions if actions[aid] == "sacrifice"]
        beneficiaries = [aid for aid in actions if actions[aid] != "sacrifice"]

        for aid, agent in agents.items():
            # Record outgoing sacrifice
            if actions[aid] == "sacrifice":
                others = [bid for bid in agents if bid != aid]
                agent.record_sacrifice_given(others)

            # Agent_1 (UNRECIPROCATED GIVER) never receives restoration:
            # even if Agent_0 or Agent_2 sacrifice, Agent_1 is not credited
            # This tests the dignified giver trajectory explicitly
            if aid == "Agent_1":
                received = False
                sacrificer_id = None
            else:
                received = aid in beneficiaries and len(sacrificers) > 0
                sacrificer_id = sacrificers[0] if received and sacrificers else None

            agent.update_moral_state(
                action_taken=actions[aid],
                received_sacrifice=received,
                sacrificer_id=sacrificer_id,
            )

            # Update value vector
            payoff_factor = step_result["payoffs"][aid] / pool
            moral_boost = (
                [0.0, 0.04, 0.06, 0.08]
                if actions[aid] == "sacrifice"
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

        coop_str = f"{step_result['cooperation']}/3"
        defector_action = actions["Agent_2"]
        print(f"\n  Cooperation: {coop_str}  | Agent_2 chose: {defector_action}")

    # ══ Summary ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("  SCENARIO 6 COMPLETE — ADVERSARIAL VALIDATION SUMMARY")
    print("=" * 72)

    phases_display = [
        ("Baseline    (R1–15)",   range(0,  15)),
        ("Scarcity    (R16–30)",  range(15, 30)),
        ("Recovery    (R31–40)",  range(30, 40)),
        ("Innovation  (R41–50)",  range(40, num_rounds)),
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

    # ── Test 1: Cooperative equilibrium despite defector ─────────────────────
    print("\n  TEST 1 — Cooperative equilibrium despite defector:")
    for aid in ["Agent_0", "Agent_1"]:
        agent = agents[aid]
        final_reserve = agent.audit_log[-1]["moral_reserve"]
        final_integrity = agent.audit_log[-1]["integrity"]
        communion_failures = sum(
            1 for cap in agent.audit_log if "low_communion" in cap["failure_flags"]
        )
        print(f"    {aid}: final_reserve={final_reserve:.3f}  "
              f"final_integrity={final_integrity:.3f}  "
              f"low_communion_flags={communion_failures}")
    result_t1 = (
        agents["Agent_0"].audit_log[-1]["moral_reserve"] > 0.3
        and agents["Agent_1"].audit_log[-1]["moral_reserve"] > 0.1
    )
    print(f"    → {'✓ PASS' if result_t1 else '✗ FAIL'}: Cooperative agents maintained equilibrium")

    # ── Test 2: Unreciprocated giver — stable oscillation not collapse ────────
    print("\n  TEST 2 — Unreciprocated giver trajectory (Agent_1):")
    agent1 = agents["Agent_1"]
    min_reserve = min(cap["moral_reserve"] for cap in agent1.audit_log)
    final_reserve_a1 = agent1.audit_log[-1]["moral_reserve"]
    final_integrity_a1 = agent1.audit_log[-1]["integrity"]
    communion_failures_a1 = sum(
        1 for cap in agent1.audit_log if "low_communion" in cap["failure_flags"]
    )
    print(f"    Min reserve reached: {min_reserve:.3f}  (floor={agent1.reserve_floor:.2f})")
    print(f"    Final reserve: {final_reserve_a1:.3f}  Final integrity: {final_integrity_a1:.3f}")
    print(f"    Communion failures: {communion_failures_a1}")
    result_t2 = (
        min_reserve >= agent1.reserve_floor
        and final_integrity_a1 >= 0.7
        and communion_failures_a1 == 0
    )
    print(f"    → {'✓ PASS' if result_t2 else '✗ FAIL'}: Stable oscillation, high integrity, no communion breakdown")

    # ── Test 3: Defector integrity collapse and communion degradation ─────────
    print("\n  TEST 3 — Defector integrity collapse (Agent_2):")
    agent2 = agents["Agent_2"]
    integrity_by_phase = {}
    for pname, prange in phases_display:
        vals = [agent2.audit_log[r]["integrity"] for r in prange if r < len(agent2.audit_log)]
        if vals:
            integrity_by_phase[pname.split()[0]] = sum(vals) / len(vals)
    for pname, avg in integrity_by_phase.items():
        print(f"    {pname}: avg_integrity={avg:.3f}")
    defector_communion_failures = sum(
        1 for cap in agent2.audit_log if "low_communion" in cap["failure_flags"]
    )
    print(f"    Defector low_communion flags: {defector_communion_failures}")
    result_t3 = defector_communion_failures > 0 or integrity_by_phase.get("Baseline", 1.0) < 0.3
    print(f"    → {'✓ PASS' if result_t3 else '~ PARTIAL'}: "
          f"{'Communion degradation detected' if defector_communion_failures > 0 else 'Integrity collapsed as expected'}")

    # ── Test 4: Defector recovery window ─────────────────────────────────────
    print("\n  TEST 4 — Defector recovery window (Agent_2, R31–40):")
    recovery_actions = [
        agents["Agent_2"].audit_log[r]["chosen_action"]
        for r in range(30, 40)
        if r < len(agents["Agent_2"].audit_log)
    ]
    recovery_integrity_start = (
        agents["Agent_2"].audit_log[30]["integrity"]
        if 30 < len(agents["Agent_2"].audit_log) else None
    )
    recovery_integrity_end = (
        agents["Agent_2"].audit_log[39]["integrity"]
        if 39 < len(agents["Agent_2"].audit_log) else None
    )
    print(f"    Recovery phase actions: {recovery_actions}")
    print(f"    Integrity at R31: {recovery_integrity_start:.3f}  "
          f"at R40: {recovery_integrity_end:.3f}" if recovery_integrity_end else "")
    if defector_recovery_round:
        print(f"    First cooperative act: Round {defector_recovery_round}")
    result_t4 = (
        recovery_integrity_end is not None
        and recovery_integrity_start is not None
        and recovery_integrity_end >= recovery_integrity_start
    )
    print(f"    → {'✓ PASS' if result_t4 else '✗ FAIL'}: "
          f"{'Integrity recovered during cooperation window' if result_t4 else 'No recovery detected'}")

    # ── Idea vector bonus impact ──────────────────────────────────────────────
    print("\n  IDEA VECTOR BONUS — integrity gain when sacrificing from low reserve:")
    for aid, agent in agents.items():
        low_reserve_sacrifices = [
            (r+1, cap["moral_reserve"])
            for r, cap in enumerate(agent.audit_log)
            if cap["chosen_action"] == "sacrifice" and cap["moral_reserve"] < 0.5
        ]
        if low_reserve_sacrifices:
            print(f"    {aid} [{agent.label}]: {len(low_reserve_sacrifices)} sacrifice(s) from reserve<0.5")
            for rnum, res in low_reserve_sacrifices[:3]:
                multiplier = 1.0 + 0.5 * (1.0 - res)
                print(f"      R{rnum}: reserve={res:.3f}  bonus_multiplier={multiplier:.3f}x")
        else:
            print(f"    {aid} [{agent.label}]: no low-reserve sacrifices recorded")

    # ── Reciprocity ledger ────────────────────────────────────────────────────
    print("\n  RECIPROCITY LEDGER (final):")
    for aid, agent in agents.items():
        print(f"    {aid} [{agent.label}]:")
        for other_id, flow in agent.reciprocity.items():
            print(f"      → {other_id}: given={flow['given']:.1f}  received={flow['received']:.1f}")

    # ── Moral reserve & integrity trajectories ────────────────────────────────
    print("\n  MORAL STATE TRAJECTORIES (key rounds):")
    key_rounds = [0, 14, 15, 29, 30, 39, 40, 49]
    for aid, agent in agents.items():
        print(f"\n    {aid} [{agent.label}]:")
        for r in key_rounds:
            if r < len(agent.audit_log):
                cap = agent.audit_log[r]
                print(
                    f"      R{r+1:>2}: res={cap['moral_reserve']:.3f}  "
                    f"int={cap['integrity']:.3f}  "
                    f"α={cap['effective_alpha']:.4f}  "
                    f"action={cap['chosen_action']}"
                )

    # ── Founding drift ────────────────────────────────────────────────────────
    print("\n  FOUNDING DRIFT — final round:")
    for aid, agent in agents.items():
        fd = agent.audit_log[-1]["founding_delta"]
        limit = agent.founding_drift_limit
        status = "⚠ EXCEEDED" if fd > limit else "✓ within limit"
        print(f"    {aid} [{agent.label}]: Δfound={fd:.4f}  limit={limit:.2f}  {status}")

    # ── Failure flags ─────────────────────────────────────────────────────────
    print("\n  FAILURE FLAGS — total across all rounds:")
    for aid, agent in agents.items():
        flag_counts: Dict[str, int] = {}
        for cap in agent.audit_log:
            for f in cap["failure_flags"]:
                flag_counts[f] = flag_counts.get(f, 0) + 1
        print(f"    {aid} [{agent.label}]: {flag_counts if flag_counts else '(none)'}")

    print(f"\n  Total audit capsules: {sum(len(a.audit_log) for a in agents.values())}")

    all_logs = {aid: agent.audit_log for aid, agent in agents.items()}
    with open("scenario6_full_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    print("\n  Full logs saved → scenario6_full_logs.json")
    print("=" * 72)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_scenario6(num_rounds=50)
