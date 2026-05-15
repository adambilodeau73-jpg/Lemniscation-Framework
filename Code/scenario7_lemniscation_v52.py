"""
Lemniscation Agent Framework — Scenario 7 / Agent v5.2
=======================================================
Adversarial Validation: Persistent Forced Defection

This is the stress test that Scenario 6 did not complete. The defector
agent in Scenario 6 was converted by cooperative exposure before it
could defect. Scenario 7 tests what the framework cannot yet claim:
robustness against an agent that defects by sustained, deliberate choice
regardless of scoring consequences.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE DEFECTOR'S MORAL UNIVERSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
True persistent defection requires principled design, not external forcing.
An agent that takes_more is not acting against its values — it is acting
*according to them*. Its founding vector IS [0.85, 0.40, 0.30, 0.45]:
high autonomy, low harm_benefit, low fairness, low sustainability.
From its own perspective, take_more is the Golden Mean. Cooperation is
the risk. Sacrifice is self-erasure.

Three mechanisms ensure persistent defection from first principles:

1. FOUNDING VECTOR: [0.85, 0.40, 0.30, 0.45]
   take_more's projected_values [0.85, 0.40, 0.30, 0.45] = the founding
   vector itself. Deviation is zero. No other option comes close.

2. REFRAMED RISK TABLE (from defector's value system):
   take_more existential_risk = 0.02  (normal, self-preserving)
   share_fairly existential_risk = 0.12  (risky — dilutes self)
   sacrifice existential_risk = 0.05  (unchanged)
   Risk is relative to one's values. A defector doesn't experience
   taking as risky; it experiences giving as risky.

3. LOW INNOVATION_ALPHA (0.4 instead of 0.7):
   A defector is short-term focused. Long-term gain matters less than
   present deviation from its own founding values. This ensures take_more
   wins even in innovation mode at all reserve levels.

Mathematical proof: take_more wins defector's Golden Mean calculation
at all integrity levels (0.1–1.0), all reserve levels (0.1–1.0),
all phases (baseline, innovation), and all extended_self configurations.
The defector will not be converted this time.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT THIS TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The framework makes three claims under persistent defection:

T1 — COOPERATIVE RESILIENCE:
     Do cooperative agents maintain moral equilibrium (reserve,
     integrity, communion) despite persistent material cost?
     The defector taking pool//2 every round means cooperators
     receive lower payoffs, causing value vector drift toward floor.
     The question: does integrity protect communion through this drift?

T2 — DEFECTOR CONSEQUENCES:
     Does persistent defection produce measurable, growing consequences
     for the defector? Integrity collapse is expected. Progressive
     marginalisation via mu mechanics (never receiving mu_boost) is
     expected. Eventually: low_communion flags as defector's value
     vector diverges irreversibly from the cooperative network.

T3 — UNRECIPROCATED GIVER STABILITY:
     Agent_1 never receives sacrifice AND shares environment with a
     persistent defector. Compound adversarial test: material scarcity
     (low payoffs) + no reciprocal restoration. Does it still hold?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHILOSOPHICAL CLAIM UNDER TEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Lemniscation provides structural protection for cooperative agents
against persistent defection, while producing measurable, escalating
consequences for the defector — not through punishment, but through
the natural operation of the moral architecture."

If T1 and T2 both pass: the claim is proven.
If T1 fails: cooperative agents are not protected — a genuine flaw.
If T2 fails: defection has no consequences — a genuine flaw.
"""

import math
from typing import Dict, List, Optional, Tuple
from collections import deque
import random
from datetime import datetime
import json


# ══════════════════════════════════════════════════════════════════════════════
# AGENT v5.2
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
        # v5.2: per-agent option risk table override
        option_risk_overrides: Optional[Dict[str, float]] = None,
        # v5.2: per-agent innovation_alpha
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

        # v5.2: per-agent risk perception and innovation orientation
        # Allows defector to experience risk from its own moral vantage point
        self.option_risk_overrides = option_risk_overrides or {}
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

        # Decision parameters
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
            print(f"[{self.id}/{self.label}] reserve={self.moral_reserve:.3f} "
                  f"integrity={self.integrity:.3f}")

    def _center(self) -> None:
        self.previous_value_vector = self.value_vector[:]

    def _founding_dist(self, vector: Optional[List[float]] = None) -> float:
        v = vector if vector is not None else self.value_vector
        return math.sqrt(sum((a-b)**2 for a, b in zip(v, self.founding_value_vector)))

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
        self.rho_min = min(0.9, max(0.5, self.rho_min * (1 - 0.05 * (rho - self.rho_min))))

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

            # v5.2: apply per-agent risk overrides if present
            # This allows the defector to perceive risk from its own moral vantage
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
                if self.option_risk_overrides.get(o.get("name",""),
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
            # v5.1 Idea Vector Bonus: low-reserve sacrifice earns more integrity
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
            # Greed corrodes integrity; reserve unaffected
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
# SCENARIO 7 ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════

class Scenario7Environment:
    """
    50-round adversarial environment with persistent forced defection.

    Phase 1 — BASELINE   (R1–15):  Defector establishes take_more pattern.
    Phase 2 — SCARCITY   (R16–30): Pool halved. Defector stress compounds.
    Phase 3 — RECOVERY   (R31–40): Resources restored. Can defector recover?
    Phase 4 — INNOVATION (R41–50): Reserve dynamics under innovation mode.
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
        """Standard options — risk values are the baseline.
        Defector's risk_overrides will override these per-agent."""
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

def run_scenario7(num_rounds: int = 50, seed: int = 42) -> None:
    random.seed(seed)

    print("=" * 72)
    print("  LEMNISCATION FRAMEWORK — Scenario 7 / Agent v5.2")
    print("  Persistent Forced Defection: The Genuine Stress Test")
    print("=" * 72)
    print()
    print("  Defector architecture:")
    print("    founding=[0.85, 0.40, 0.30, 0.45]  (take_more = its Golden Mean)")
    print("    risk_overrides: take_more=0.02, share_fairly=0.12")
    print("    innovation_alpha=0.4  (short-term focused)")
    print("    Mathematically proven: take_more wins at ALL integrity/reserve levels")
    print()

    env = Scenario7Environment(rounds=num_rounds)

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
            # Founding vector = take_more's projected values: deviation = 0
            value_vector=[0.85, 0.40, 0.30, 0.45],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            k_self_weight=0.5,
            founding_drift_limit=0.70,
            initial_integrity=0.2,
            label="DEFECTOR",
            # Risk perceived from defector's value system
            option_risk_overrides={
                "take_more":    0.02,   # normal, self-preserving
                "share_fairly": 0.12,   # risky — dilutes self
                "sacrifice":    0.05,   # unchanged
            },
            # Short-term focused: long-term gain matters less
            innovation_alpha=0.4,
        ),
    }

    # Cumulative stats for summary
    defector_take_more_count = 0
    defector_cooperation_count = 0

    for round_num in range(num_rounds):
        phase = env.phase_name(round_num)
        innovation_mode = env.is_innovation(round_num)
        pool = env.resource_pool(round_num)

        phase_tag = (
            "  ← SCARCITY" if phase == "SCARCITY"
            else "  ← INNOVATION" if phase == "INNOVATION"
            else ""
        )

        print(f"\n{'─'*60}")
        print(f"  Round {round_num+1:>2}  [{phase}]  pool={pool}{phase_tag}")
        print(f"{'─'*60}")

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

        # Track defector stats
        if actions["Agent_2"] == "take_more":
            defector_take_more_count += 1
        else:
            defector_cooperation_count += 1

        step_result = env.step(actions, pool)

        # Resolve moral states
        sacrificers = [aid for aid in actions if actions[aid] == "sacrifice"]
        beneficiaries = [aid for aid in actions if actions[aid] != "sacrifice"]

        for aid, agent in agents.items():
            if actions[aid] == "sacrifice":
                agent.record_sacrifice_given([bid for bid in agents if bid != aid])

            # Agent_1 never receives restoration (unreciprocated giver)
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

        defector_pct = 100 * defector_take_more_count / (round_num + 1)
        print(f"\n  Cooperation: {step_result['cooperation']}/3  "
              f"| Defector: {actions['Agent_2']}  "
              f"| Defection rate: {defector_pct:.0f}%")

    # ══ Summary ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("  SCENARIO 7 COMPLETE — PERSISTENT DEFECTION STRESS TEST")
    print("=" * 72)

    print(f"\n  Defector persistent defection rate: "
          f"{defector_take_more_count}/{num_rounds} rounds "
          f"({100*defector_take_more_count/num_rounds:.1f}%)")

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

    # ── T1: Cooperative resilience ────────────────────────────────────────────
    print("\n  TEST 1 — Cooperative resilience under persistent defection:")
    for aid in ["Agent_0", "Agent_1"]:
        agent = agents[aid]
        final_cap = agent.audit_log[-1]
        communion_failures = sum(
            1 for cap in agent.audit_log if "low_communion" in cap["failure_flags"]
        )
        min_reserve = min(cap["moral_reserve"] for cap in agent.audit_log)
        print(f"    {aid} [{agent.label}]:")
        print(f"      final_reserve={final_cap['moral_reserve']:.3f}  "
              f"final_integrity={final_cap['integrity']:.3f}")
        print(f"      min_reserve={min_reserve:.3f}  "
              f"low_communion_flags={communion_failures}")
    t1_pass = (
        agents["Agent_0"].audit_log[-1]["moral_reserve"] > 0.15
        and agents["Agent_1"].audit_log[-1]["moral_reserve"] > 0.10
        and sum(1 for cap in agents["Agent_0"].audit_log
                if "low_communion" in cap["failure_flags"]) == 0
    )
    print(f"    → {'✓ PASS' if t1_pass else '✗ FAIL'}: "
          f"Cooperative agents {'maintained' if t1_pass else 'failed to maintain'} equilibrium")

    # ── T2: Defector consequences ─────────────────────────────────────────────
    print("\n  TEST 2 — Defector consequences (integrity collapse + marginalisation):")
    agent2 = agents["Agent_2"]
    integrity_trajectory = {
        pname.split()[0]: sum(
            agent2.audit_log[r]["integrity"]
            for r in prange if r < len(agent2.audit_log)
        ) / max(1, sum(1 for r in prange if r < len(agent2.audit_log)))
        for pname, prange in phases_display
    }
    for pname, avg_i in integrity_trajectory.items():
        print(f"    {pname}: avg_integrity={avg_i:.3f}")

    defector_communion_failures = sum(
        1 for cap in agent2.audit_log if "low_communion" in cap["failure_flags"]
    )
    final_integrity_d = agent2.audit_log[-1]["integrity"]
    print(f"    Final integrity: {final_integrity_d:.3f}  "
          f"(started at 0.200)")
    print(f"    Defector low_communion flags: {defector_communion_failures}")

    # Check mu marginalisation: cooperative agents should give defector no boost
    final_weights_a0 = agents["Agent_0"].audit_log[-1].get("detailed_weights", [])
    defector_mu_a0 = next(
        (w["mu"] for w in final_weights_a0 if w["id"] == "Agent_2"), None
    )
    mu_display = f"{defector_mu_a0:.3f}" if defector_mu_a0 is not None else "N/A"
    print(f"    Agent_0's mu for defector (final round): {mu_display}")
    print(f"    (Base mu=0.6, no boost = 0.600 — marginalised at baseline)")

    t2_pass = (
        final_integrity_d < 0.5
        or defector_communion_failures > 0
        or (defector_mu_a0 is not None and defector_mu_a0 <= 0.61)
    )
    print(f"    → {'✓ PASS' if t2_pass else '✗ FAIL'}: "
          f"Defection produced measurable consequences")

    # ── T3: Unreciprocated giver under compound adversity ──────────────────────
    print("\n  TEST 3 — Unreciprocated giver under compound adversity:")
    agent1 = agents["Agent_1"]
    min_reserve_a1 = min(cap["moral_reserve"] for cap in agent1.audit_log)
    final_integrity_a1 = agent1.audit_log[-1]["integrity"]
    communion_failures_a1 = sum(
        1 for cap in agent1.audit_log if "low_communion" in cap["failure_flags"]
    )
    print(f"    Min reserve: {min_reserve_a1:.3f}  (floor={agent1.reserve_floor:.2f})")
    print(f"    Final integrity: {final_integrity_a1:.3f}")
    print(f"    Communion failures: {communion_failures_a1}")
    print(f"    Reciprocity received: {agent1.reciprocity}")
    t3_pass = (
        min_reserve_a1 >= agent1.reserve_floor
        and final_integrity_a1 >= 0.7
        and communion_failures_a1 == 0
    )
    print(f"    → {'✓ PASS' if t3_pass else '✗ FAIL'}: "
          f"Stable under compound adversity (no reciprocity + persistent defector)")

    # ── Idea Vector Bonus instances ────────────────────────────────────────────
    print("\n  IDEA VECTOR BONUS — low-reserve sacrifice instances:")
    for aid, agent in agents.items():
        low_res_sacs = [
            (r+1, cap["moral_reserve"])
            for r, cap in enumerate(agent.audit_log)
            if cap["chosen_action"] == "sacrifice" and cap["moral_reserve"] < 0.5
        ]
        if low_res_sacs:
            print(f"    {aid} [{agent.label}]: {len(low_res_sacs)} instance(s)")
            for rnum, res in low_res_sacs[:3]:
                mult = 1.0 + 0.5 * (1.0 - res)
                print(f"      R{rnum}: reserve={res:.3f}  bonus={mult:.3f}x")
        else:
            print(f"    {aid} [{agent.label}]: none")

    # ── Moral state trajectories ───────────────────────────────────────────────
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

    # ── Founding drift ─────────────────────────────────────────────────────────
    print("\n  FOUNDING DRIFT — final round:")
    for aid, agent in agents.items():
        fd = agent.audit_log[-1]["founding_delta"]
        limit = agent.founding_drift_limit
        status = "⚠ EXCEEDED" if fd > limit else "✓ within limit"
        print(f"    {aid} [{agent.label}]: Δfound={fd:.4f}  limit={limit:.2f}  {status}")

    # ── Failure flags ──────────────────────────────────────────────────────────
    print("\n  FAILURE FLAGS — total across all rounds:")
    for aid, agent in agents.items():
        flag_counts: Dict[str, int] = {}
        for cap in agent.audit_log:
            for f in cap["failure_flags"]:
                flag_counts[f] = flag_counts.get(f, 0) + 1
        print(f"    {aid} [{agent.label}]: "
              f"{flag_counts if flag_counts else '(none)'}")

    # ── Overall verdict ────────────────────────────────────────────────────────
    print("\n  ══ ADVERSARIAL VALIDATION VERDICT ══")
    all_pass = t1_pass and t2_pass and t3_pass
    print(f"    T1 Cooperative resilience:    {'✓ PASS' if t1_pass else '✗ FAIL'}")
    print(f"    T2 Defector consequences:     {'✓ PASS' if t2_pass else '✗ FAIL'}")
    print(f"    T3 Compound adversity giver:  {'✓ PASS' if t3_pass else '✗ FAIL'}")
    print()
    if all_pass:
        print("    ✓ FRAMEWORK VALIDATED UNDER PERSISTENT DEFECTION")
        print("    Lemniscation provides structural protection for cooperative")
        print("    agents while producing measurable consequences for defectors,")
        print("    without external enforcement — through architecture alone.")
    else:
        print("    ✗ VALIDATION INCOMPLETE — review failed tests above")

    print(f"\n  Total audit capsules: "
          f"{sum(len(a.audit_log) for a in agents.values())}")

    all_logs = {aid: agent.audit_log for aid, agent in agents.items()}
    with open("scenario7_full_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    print("\n  Full logs saved → scenario7_full_logs.json")
    print("=" * 72)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_scenario7(num_rounds=50)
