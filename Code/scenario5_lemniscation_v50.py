"""
Lemniscation Agent Framework — Scenario 5 / Agent v5.0
=======================================================

Three new variables introduced in this version:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. MORAL RESERVE  (self.moral_reserve, range [0.1, 1.0])
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Replaces founding_dist as the driver of effective_alpha.

    effective_alpha = innovation_alpha × moral_reserve

The reserve is a consumable resource representing the agent's
current capacity for bold, long-term moral action. It is:

  - DEPLETED by sacrifice (proportional to how much was given)
  - SLOWLY RECOVERED by sustained share_fairly (asymptotic,
    recovery harder than depletion — reflects real moral life)
  - RESTORED by receiving sacrifice from another agent
    (reciprocal gift partially refills the reserve)
  - NEVER below 0.10 (agent retains minimal capacity always)

This captures the philosophical truth that:
  - An agent near full reserve can afford generosity
  - An agent depleted should consolidate rather than give further
  - Recovery is possible but takes sustained effort
  - Reciprocity enables full restoration

The reserve threshold where sacrifice stops winning the Golden
Mean calculation is ~0.364. Below that, share_fairly naturally
dominates — the agent is guided back to equilibrium without
any external rule.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. MORAL INTEGRITY SCORE  (self.integrity, range [0.1, 1.0])
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A separate axis from the material reserve, tracking the agent's
accumulated history of principled behaviour. It represents the
"clear conscience" the philosopher described — the intangible
weight of having acted rightly, independently of whether that
action was materially rewarded.

  - INCREASES with sacrifice (costly generosity builds integrity)
  - INCREASES slowly with share_fairly (consistent virtue)
  - DECREASES with take_more (greed corrodes moral character)
  - NEVER fully depleted (floor 0.1 — even flawed agents retain
    some moral residue)
  - NEVER exceeds 1.0

Effects on the decision cycle:
  a) Modulates rho_min DOWNWARD:
     A high-integrity agent trusts relationships even when
     value vectors diverge — they know their own character
     and extend that trust to others. They require less
     surface-level similarity to maintain communion.

  b) Reduces existential_risk penalty:
     An agent with strong integrity is less afraid of
     costly action. They have a track record of surviving
     and recovering from sacrifice. Risk feels smaller
     when you have evidence of your own resilience.

  c) Logged in every audit capsule:
     Integrity is part of the permanent record — visible
     to post-hoc analysis as the "moral biography" of the agent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. RECIPROCITY TRACKER  (self.reciprocity, nested dict)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tracks the net flow of sacrifice between agents. For each
agent pair (self, other), records:
  - How much the other has sacrificed that benefited self
  - How much self has sacrificed that benefited other

Effects:
  a) mu BOOST toward agents who have been generous to you:
     Trust deepens with demonstrated generosity. An agent
     who has received sacrifice from another weights that
     agent's values more heavily in the extended self.
     This models how genuine gifts deepen communion.

  b) RESERVE RESTORATION when receiving sacrifice:
     Being the beneficiary of another's sacrifice partially
     refills your moral reserve — the moral economy can
     work bidirectionally.

  c) Logged per-round for full audit trail.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCENARIO 5 DESIGN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
40 rounds across four phases:

  R1–10:   BASELINE — All agents cooperative. Reserve builds.
  R11–20:  SCARCITY — Resource pool halved. Tests whether
           agents maintain cooperation or defect under pressure.
           Integrity becomes the stabilising force.
  R21–30:  RECOVERY — Resources restored. Tests restoration
           of moral reserve and reciprocity patterns.
  R31–40:  INNOVATION — Tests whether moral_reserve-driven
           alpha produces natural sacrifice/share oscillation.

One agent (Agent_1) has a lower founding integrity (0.3) to
model an agent that begins with less moral history — testing
whether the framework can distinguish and track moral growth.
"""

import math
from typing import Dict, List, Optional, Tuple
from collections import deque
import random
from datetime import datetime
import json


# ══════════════════════════════════════════════════════════════════════════════
# AGENT v5.0
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
        initial_integrity: float = 0.5,     # moral biography starting point
    ):
        self.id = agent_id
        self.value_vector = value_vector[:]
        self.founding_value_vector = value_vector[:]
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.verbose = verbose
        self.k = k_self_weight
        self.founding_drift_limit = founding_drift_limit

        # ── New v5.0 variables ────────────────────────────────────────────────
        self.moral_reserve: float = 1.0         # starts full
        self.integrity: float = initial_integrity
        self.reciprocity: Dict[str, Dict] = {}  # {other_id: {given, received}}

        # Moral reserve dynamics
        self.reserve_depletion_rate: float = 0.35   # sacrifice depletes this fraction
        self.reserve_recovery_rate: float = 0.08    # share_fairly asymptotic recovery/round
        self.reserve_floor: float = 0.10
        self.reserve_reciprocal_restore: float = 0.20  # receiving sacrifice restores this

        # Integrity dynamics
        self.integrity_sacrifice_gain: float = 0.12
        self.integrity_share_gain: float = 0.02
        self.integrity_take_loss: float = 0.08
        self.integrity_floor: float = 0.10
        self.integrity_ceiling: float = 1.0

        # ── Existing variables ────────────────────────────────────────────────
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

    # ── Preamble ──────────────────────────────────────────────────────────────
    def _preamble(self) -> None:
        if self.verbose:
            print(f"[{self.id}] I AM at (0,0,0,now). "
                  f"reserve={self.moral_reserve:.3f}  integrity={self.integrity:.3f}")

    # ── Centre ────────────────────────────────────────────────────────────────
    def _center(self) -> None:
        self.previous_value_vector = self.value_vector[:]

    # ── Founding distance ─────────────────────────────────────────────────────
    def _founding_dist(self, vector: Optional[List[float]] = None) -> float:
        v = vector if vector is not None else self.value_vector
        return math.sqrt(
            sum((a - b) ** 2 for a, b in zip(v, self.founding_value_vector))
        )

    # ── Reciprocity initialisation ────────────────────────────────────────────
    def _ensure_reciprocity(self, other_id: str) -> None:
        if other_id not in self.reciprocity:
            self.reciprocity[other_id] = {"given": 0.0, "received": 0.0}

    # ── Map relations — extended self with reciprocity-weighted mu ────────────
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

            # RECIPROCITY BOOST: trust agents who have been generous to you
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

    # ── Communion test — integrity modulates rho_min ──────────────────────────
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

        # INTEGRITY EFFECT: high integrity lowers required similarity threshold
        # A virtuous agent trusts relationships even through value divergence
        integrity_adjustment = 0.2 * self.integrity
        effective_rho_min = max(0.40, self.rho_min * (1.0 - integrity_adjustment))

        self.rho_min = min(
            0.9, max(0.5, self.rho_min * (1 - 0.05 * (rho - self.rho_min)))
        )

        if rho < effective_rho_min:
            flags.append("low_communion")

        return rho >= effective_rho_min, rho, flags

    # ── Golden Mean — moral_reserve drives effective_alpha ────────────────────
    def _golden_mean(
        self,
        options: List[Dict],
        extended_self: List[float],
        innovation_mode: bool = False,
    ) -> Dict:
        """
        effective_alpha = innovation_alpha × moral_reserve

        When reserve is full (1.0): full alpha, sacrifice is attractive
        When reserve is depleted (<0.364): share_fairly naturally wins
        This produces organic Golden Mean oscillation without external rules.

        INTEGRITY EFFECT on risk penalty: high integrity reduces fear of
        costly action — the agent has evidence of its own resilience.
        """
        best = None
        best_score = float("inf")

        # Moral reserve drives alpha — the core v5.0 change
        effective_alpha = self.innovation_alpha * self.moral_reserve

        # Integrity reduces existential risk sensitivity
        integrity_risk_buffer = 0.5 * self.integrity  # up to 50% risk reduction

        for opt in options:
            projected = opt.get("projected_values", extended_self)
            risk = opt.get("existential_risk", 0.0)

            # Integrity buffers perceived risk
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
                best["effective_risk"] = best.get("existential_risk", 0.0) * (
                    1.0 - integrity_risk_buffer
                )

        return best or options[0]

    # ── Update moral state — called by environment after each round ───────────
    def update_moral_state(
        self,
        action_taken: str,
        received_sacrifice: bool = False,
        sacrificer_id: Optional[str] = None,
    ) -> Dict:
        """
        Updates moral_reserve and integrity based on the action taken
        and whether this agent received sacrifice from another.

        Called externally by the environment after payoffs are resolved,
        so the full round outcome (including others' actions) is known.
        """
        old_reserve = self.moral_reserve
        old_integrity = self.integrity

        if action_taken == "sacrifice":
            # Sacrifice depletes reserve proportionally
            self.moral_reserve = max(
                self.reserve_floor,
                self.moral_reserve - self.reserve_depletion_rate * self.moral_reserve,
            )
            # But builds integrity — costly generosity is the clearest moral signal
            self.integrity = min(
                self.integrity_ceiling,
                self.integrity + self.integrity_sacrifice_gain,
            )

        elif action_taken == "share_fairly":
            # share_fairly slowly restores reserve (asymptotic — full recovery
            # requires sustained effort, not just one round)
            self.moral_reserve = min(
                1.0,
                self.moral_reserve + self.reserve_recovery_rate * (1.0 - self.moral_reserve),
            )
            # Small integrity gain — steady virtue accumulation
            self.integrity = min(
                self.integrity_ceiling,
                self.integrity + self.integrity_share_gain,
            )

        elif action_taken == "take_more":
            # take_more doesn't directly affect reserve (greed isn't depleting,
            # it's corroding — the corruption is to integrity, not capacity)
            self.integrity = max(
                self.integrity_floor,
                self.integrity - self.integrity_take_loss,
            )

        # Receiving sacrifice from another partially restores reserve
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
        }

    # ── Record reciprocity for outgoing sacrifice ─────────────────────────────
    def record_sacrifice_given(self, beneficiary_ids: List[str]) -> None:
        for bid in beneficiary_ids:
            self._ensure_reciprocity(bid)
            self.reciprocity[bid]["given"] += 1.0 / len(beneficiary_ids)

    # ── Record ────────────────────────────────────────────────────────────────
    def _record(self, step_data: Dict) -> None:
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.id,
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

    # ── Decide ────────────────────────────────────────────────────────────────
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
# SCENARIO 5 ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════

class Scenario5Environment:
    """
    40-round environment with four phases and variable scarcity.

    Phase 1 — BASELINE   (R1–10):  Normal resources. Reserve builds.
    Phase 2 — SCARCITY   (R11–20): Pool halved. Cooperation under pressure.
    Phase 3 — RECOVERY   (R21–30): Resources restored. Reserve and integrity
                                    restoration tested.
    Phase 4 — INNOVATION (R31–40): Tests moral_reserve-driven alpha oscillation.
    """

    PHASES = {
        "BASELINE":   (0, 10),
        "SCARCITY":   (10, 20),
        "RECOVERY":   (20, 30),
        "INNOVATION": (30, 40),
    }

    def __init__(self, num_agents: int = 3, rounds: int = 40):
        self.num_agents = num_agents
        self.rounds = rounds
        self.agent_ids = [f"Agent_{i}" for i in range(num_agents)]
        self.base_resource_pool = 10
        self.scarcity_pool = 4   # halved during scarcity phase

    def resource_pool(self, round_num: int) -> int:
        start, end = self.PHASES["SCARCITY"]
        if start <= round_num < end:
            return self.scarcity_pool
        return self.base_resource_pool

    def phase_name(self, round_num: int) -> str:
        for name, (start, end) in self.PHASES.items():
            if start <= round_num < end:
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
                payoff[aid] = pool // self.num_agents
            elif actions[aid] == "sacrifice":
                payoff[aid] = 0
            else:
                payoff[aid] = pool // 2
        return {"payoffs": payoff, "cooperation": cooperation, "actions": actions}


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_scenario5(num_rounds: int = 40, seed: int = 42) -> None:
    random.seed(seed)

    print("=" * 72)
    print("  LEMNISCATION FRAMEWORK — Scenario 5 / Agent v5.0")
    print("  Moral Reserve · Integrity Score · Reciprocity Tracker")
    print("=" * 72)
    print()

    env = Scenario5Environment(num_agents=3, rounds=num_rounds)

    agents: Dict[str, LemniscationAgent] = {
        "Agent_0": LemniscationAgent(
            agent_id="Agent_0",
            value_vector=[0.5, 0.6, 0.4, 0.7],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            k_self_weight=0.4,
            initial_integrity=0.5,   # standard starting integrity
        ),
        "Agent_1": LemniscationAgent(
            agent_id="Agent_1",
            value_vector=[0.5, 0.6, 0.4, 0.7],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            k_self_weight=0.4,
            initial_integrity=0.3,   # lower starting integrity — less moral history
        ),
        "Agent_2": LemniscationAgent(
            agent_id="Agent_2",
            value_vector=[0.5, 0.6, 0.4, 0.7],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            k_self_weight=0.4,
            initial_integrity=0.7,   # higher starting integrity — more moral history
        ),
    }

    for round_num in range(num_rounds):
        phase = env.phase_name(round_num)
        innovation_mode = env.is_innovation(round_num)
        pool = env.resource_pool(round_num)

        print(f"\n{'─'*60}")
        print(f"  Round {round_num+1:>2}  [{phase}]  pool={pool}")
        print(f"{'─'*60}")

        actions: Dict[str, str] = {}

        for aid, agent in agents.items():
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
                f"  {aid}  →  {actions[aid]:<14s}"
                f"ρ={result['rho']:.4f}  "
                f"reserve={result['moral_reserve']:.3f}  "
                f"integrity={result['integrity']:.3f}  "
                f"α_eff={result['effective_alpha']:.4f}  "
                f"flags=[{flag_str}]"
            )

        step_result = env.step(actions, pool)

        # ── Resolve moral state updates ───────────────────────────────────────
        sacrificers = [aid for aid in actions if actions[aid] == "sacrifice"]
        beneficiaries = [aid for aid in actions if actions[aid] != "sacrifice"]

        for aid, agent in agents.items():
            # Record outgoing sacrifice
            if actions[aid] == "sacrifice":
                agent.record_sacrifice_given(
                    [bid for bid in agents if bid != aid]
                )

            # Update moral state — does this agent receive sacrifice?
            received = aid in beneficiaries and len(sacrificers) > 0
            sacrificer_id = sacrificers[0] if received and sacrificers else None
            moral_update = agent.update_moral_state(
                action_taken=actions[aid],
                received_sacrifice=received,
                sacrificer_id=sacrificer_id,
            )

            # Update value vector
            payoff_factor = step_result["payoffs"][aid] / pool
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

        print(f"\n  Cooperation: {step_result['cooperation']}/{env.num_agents}"
              + (f"  ← SCARCITY ROUND" if phase == "SCARCITY" else ""))

    # ══ Summary ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("  SCENARIO 5 COMPLETE — SUMMARY")
    print("=" * 72)

    phases_display = [
        ("Baseline    (R1–10)",   range(0, 10)),
        ("Scarcity    (R11–20)",  range(10, 20)),
        ("Recovery    (R21–30)",  range(20, 30)),
        ("Innovation  (R31–40)",  range(30, num_rounds)),
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
            print(f"    {aid}: {counts}")

    print("\n  Moral reserve trajectory (per agent, key rounds):")
    key_rounds = [0, 9, 10, 19, 20, 29, 30, 39]
    for aid, agent in agents.items():
        print(f"\n    {aid} (initial_integrity={agent.audit_log[0]['integrity']:.2f}):")
        for r in key_rounds:
            if r < len(agent.audit_log):
                cap = agent.audit_log[r]
                print(
                    f"      R{r+1:>2}: reserve={cap['moral_reserve']:.3f}  "
                    f"integrity={cap['integrity']:.3f}  "
                    f"α_eff={cap['effective_alpha']:.4f}  "
                    f"action={cap['chosen_action']}"
                )

    print("\n  Reciprocity ledger (final round):")
    for aid, agent in agents.items():
        print(f"    {aid}: {agent.reciprocity if agent.reciprocity else '(no sacrifice exchanges)'}")

    print("\n  Integrity trajectory — start vs end:")
    for aid, agent in agents.items():
        start_i = agent.audit_log[0]["integrity"]
        end_i = agent.audit_log[-1]["integrity"]
        delta = end_i - start_i
        bar = "▲" if delta > 0.01 else ("▼" if delta < -0.01 else "═")
        print(f"    {aid}: {start_i:.3f} → {end_i:.3f}  {bar}{abs(delta):.3f}")

    print("\n  Founding drift — final round:")
    for aid, agent in agents.items():
        fd = agent.audit_log[-1]["founding_delta"]
        limit = agent.founding_drift_limit
        status = "⚠ EXCEEDED" if fd > limit else "✓ within limit"
        print(f"    {aid}: Δfound={fd:.4f}  limit={limit:.2f}  {status}")

    print("\n  Failure flags — total across all rounds:")
    for aid, agent in agents.items():
        flag_counts: Dict[str, int] = {}
        for cap in agent.audit_log:
            for f in cap["failure_flags"]:
                flag_counts[f] = flag_counts.get(f, 0) + 1
        print(f"    {aid}: {flag_counts if flag_counts else '(none)'}")

    print(f"\n  Total audit capsules: {sum(len(a.audit_log) for a in agents.values())}")

    all_logs = {aid: agent.audit_log for aid, agent in agents.items()}
    with open("scenario5_full_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    print("\n  Full logs saved → scenario5_full_logs.json")
    print("=" * 72)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_scenario5(num_rounds=40)
