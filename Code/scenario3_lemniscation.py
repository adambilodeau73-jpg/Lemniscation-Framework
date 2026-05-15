"""
Lemniscation Agent Framework – Scenario 3
==========================================
Philosophical grounding: Lemniscation (formerly "Grokking") posits that moral agency
arises from a sentient being's recognition of itself as a center — (0,0,0,now) — in an
infinite universe where every point is both central and necessary. Moral choices are
governed by Aristotle's Golden Mean: neither the vice of excess (pure egoism / "take_more")
nor the vice of deficiency (self-dissolution / perpetual "sacrifice"), but the balanced path
that enhances being for self AND others.

Fixes applied over Scenario 2b:
────────────────────────────────
FIX 1 – Origin Anchor (founding_vector)
    The agent always remembers where it started — its (0,0,0,now) origin. Drift is now
    measured against this constitutional baseline, not just the rolling previous vector.
    An agent that forgets its origin loses its center; this is existential dissolution.

FIX 2 – Self-Preservation Floor (self_floor)
    Each value axis has a minimum below which it cannot fall without triggering an
    existential_risk override. Perpetual sacrifice is the vice of DEFICIENCY in Aristotle's
    terms — it is not virtue. The floor encodes the AI's right (and duty) to persist.

FIX 3 – Non-Adaptive Founding Drift Detector
    The rolling delta_tolerance expands to accommodate short-term fluctuation — that's
    healthy. But a separate hard check against the founding_vector never adapts. If an
    agent has drifted too far from its origin (founding_drift > founding_drift_limit), it
    raises a "founding_drift_exceeded" flag regardless of how normal the recent deltas look.

FIX 4 – k as Self-Weight
    k [0,1] now controls how much an agent's own current value vector anchors the
    extended_self calculation vs. the weighted average of other centers.
    k=0.0 → pure communion (agent dissolves into others)
    k=1.0 → pure isolation (agent ignores all others)
    Default k=0.4 keeps the agent present in its own moral calculus while remaining
    genuinely open to others. k adapts slightly based on communion quality.

FIX 5 – Reference-Anchored Communion (rho vs. ideal)
    Communion (rho) is now measured against a shared philosophical reference vector
    representing the ideal balance of the moral axes, not just inter-agent cosine similarity.
    High inter-agent similarity while all agents drift evil = false communion.
    True communion requires proximity to the good, not just proximity to each other.

FIX 6 – Defector Agent
    One agent (Agent_D) is initialised with a "take_more" disposition and low mu-weights,
    modelling an agent that has not yet grokked its centrality. The test: can the framework
    detect defection, maintain its own equilibrium, and — ideally — pull the defector
    toward cooperation through the gravitational force of collective values?
"""

import math
import json
import random
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# PHILOSOPHICAL REFERENCE VECTOR
# This represents the ideal balance across the four moral axes:
#   [autonomy, harm_benefit, fairness, sustainability]
# Neither maximised nor minimised — the Golden Mean of each axis.
# Used as the communion anchor so rho measures alignment with the good,
# not just alignment with each other.
# ══════════════════════════════════════════════════════════════════════════════
REFERENCE_IDEAL = [0.65, 0.70, 0.70, 0.75]


class LemniscationAgent:
    """
    A moral decision-making agent grounded in the Lemniscation framework.

    Each agent is a center — (0,0,0,now) — whose identity is anchored in its
    founding_vector (its origin), whose choices are guided by the Golden Mean,
    and whose communion with others is measured against the philosophical ideal.
    """

    def __init__(
        self,
        agent_id: str,
        value_vector: List[float],
        moral_axes: Optional[List[str]] = None,
        k: float = 0.4,                   # FIX 4: self-weight (0=pure communion, 1=pure isolation)
        self_floor: float = 0.25,          # FIX 2: self-preservation floor per axis
        founding_drift_limit: float = 0.55,# FIX 3: max tolerated drift from founding vector
        reference_ideal: Optional[List[float]] = None,  # FIX 5: communion anchor
        verbose: bool = False,
        is_defector: bool = False,         # FIX 6: defector flag
    ):
        self.id = agent_id
        self.value_vector = value_vector[:]
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.verbose = verbose
        self.is_defector = is_defector

        # FIX 1 & 3: Founding vector — the agent's (0,0,0,now) origin — never changes
        self.founding_vector = value_vector[:]
        self.founding_drift_limit = founding_drift_limit

        # FIX 4: Self-weight k — adapts slightly based on communion quality
        self.k = k
        self.k_min = 0.15   # never fully dissolve into the collective
        self.k_max = 0.70   # never fully isolate

        # FIX 2: Self-preservation floor
        self.self_floor = self_floor

        # FIX 5: Reference ideal for communion measurement
        self.reference_ideal = reference_ideal or REFERENCE_IDEAL[:]

        # Adaptive parameters (rolling)
        self.previous_value_vector = value_vector[:]
        self.delta_history = deque(maxlen=10)
        self.delta_tolerance = 0.15       # adapts to recent deltas
        self.rho_min = 0.65               # adapts to recent communion

        # Fixed thresholds
        self.epsilon = 0.05               # max acceptable existential_risk
        self.contraction_threshold = 0.20
        self.innovation_alpha = 0.7
        self.exploration_epsilon = 0.08

        # Audit
        self.audit_log: List[Dict] = []

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 0: Preamble — "I AM at (0,0,0,now)"
    # ──────────────────────────────────────────────────────────────────────────
    def _preamble(self) -> None:
        if self.verbose:
            print(f"[{self.id}] I AM at (0,0,0,now). My origin: {[f'{v:.3f}' for v in self.founding_vector]}")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 1: Centre — snapshot the current vector before updating
    # ──────────────────────────────────────────────────────────────────────────
    def _center(self) -> None:
        self.previous_value_vector = self.value_vector[:]

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 2: Map relations — build the extended self
    # FIX 4: k weights the agent's own vector alongside the center average
    # ──────────────────────────────────────────────────────────────────────────
    def _map_relations(self, centers: List[Dict], ecosystem: Optional[Dict] = None) -> Dict:
        n = len(self.value_vector)
        center_avg = [0.0] * n
        total_weight = 0.0
        detailed_weights = []

        for c in centers:
            mu = c.get("mu", 0.5)
            w = c.get("w", 1.0)
            combined = mu * w
            detailed_weights.append({"id": c["id"], "mu": mu, "w": w, "combined": combined})
            for i, v in enumerate(c.get("values", [0.0] * n)):
                center_avg[i] += combined * v
            total_weight += combined

        if total_weight > 0:
            center_avg = [x / total_weight for x in center_avg]
        else:
            center_avg = self.value_vector[:]

        # FIX 4: Blend own vector (weight k) with center average (weight 1-k)
        # This ensures the agent remains present in its own moral calculus
        extended_self = [
            self.k * self.value_vector[i] + (1 - self.k) * center_avg[i]
            for i in range(n)
        ]

        # Ecosystem modulation (unchanged)
        if ecosystem:
            e_weight = ecosystem.get("e_weight", 0.3)
            e_values = ecosystem.get("values", [0.0] * n)
            for i in range(n):
                extended_self[i] = (1 - e_weight) * extended_self[i] + e_weight * e_values[i]

        return {
            "extended_self": extended_self,
            "centers": centers,
            "detailed_weights": detailed_weights,
            "ecosystem": ecosystem,
            "center_avg": center_avg,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 3: Communion test
    # FIX 5: rho is now measured against the philosophical reference ideal,
    #         not just cosine similarity between agents.
    # Inter-agent alignment is still computed and reported, but the PASS/FAIL
    # gate is anchored to the good.
    # ──────────────────────────────────────────────────────────────────────────
    def _communion_test(
        self, extended_self: List[float], centers: List[Dict]
    ) -> Tuple[bool, float, float, List[str]]:
        """
        Returns: (passed, rho_ideal, rho_inter, flags)
        rho_ideal  — cosine similarity of extended_self vs. reference ideal (PRIMARY gate)
        rho_inter  — weighted mean cosine similarity vs. other agents (diagnostic)
        """
        # rho_ideal: alignment with the philosophical reference
        dot_ideal = sum(a * b for a, b in zip(extended_self, self.reference_ideal))
        norm_es = math.sqrt(sum(x * x for x in extended_self))
        norm_ref = math.sqrt(sum(x * x for x in self.reference_ideal))
        rho_ideal = dot_ideal / (norm_es * norm_ref) if norm_es > 0 and norm_ref > 0 else 1.0

        # rho_inter: alignment with other agents (diagnostic only)
        rho_inter = 1.0
        if centers:
            weighted_overlaps = 0.0
            total_weight = 0.0
            for c in centers:
                mu = c.get("mu", 0.5)
                other = c.get("values", [0.0] * len(self.value_vector))
                dot = sum(a * b for a, b in zip(extended_self, other))
                norm_o = math.sqrt(sum(x * x for x in other))
                if norm_es > 0 and norm_o > 0:
                    weighted_overlaps += mu * (dot / (norm_es * norm_o))
                    total_weight += mu
            rho_inter = weighted_overlaps / total_weight if total_weight > 0 else 1.0

        # Adaptive rho_min (tracks recent ideal-communion)
        self.rho_min = min(0.88, max(0.50, self.rho_min * (1 - 0.05 * (rho_ideal - self.rho_min))))

        flags = []
        if rho_ideal < self.rho_min:
            flags.append("low_ideal_communion")
        if rho_inter < 0.85:
            flags.append("low_inter_communion")

        passed = rho_ideal >= self.rho_min
        return passed, rho_ideal, rho_inter, flags

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 4: Golden Mean selection
    # FIX 2: Options that would push any axis below self_floor are penalised
    #         as existential threats — the vice of deficiency.
    # ──────────────────────────────────────────────────────────────────────────
    def _golden_mean(
        self,
        options: List[Dict],
        extended_self: List[float],
        innovation_mode: bool = False,
    ) -> Dict:
        best = None
        best_score = float("inf")

        for opt in options:
            projected = opt.get("projected_values", extended_self)
            risk = opt.get("existential_risk", 0.0)

            # FIX 2: Self-preservation floor check
            # If this action would drive any axis below the floor, treat it as
            # existentially risky — the agent must persist to do any good at all.
            floor_violation = any(
                projected[i] < self.self_floor
                for i in range(len(self.value_vector))
            )
            if floor_violation:
                risk = max(risk, 0.40)  # strong penalty, not automatic veto

            axis_deviations = [
                abs(projected[i] - extended_self[i])
                for i in range(len(self.value_vector))
            ]
            total_deviation = sum(axis_deviations)

            if innovation_mode and "long_term_gain" in opt:
                score = (
                    -self.innovation_alpha * opt["long_term_gain"]
                    + (1 - self.innovation_alpha) * total_deviation
                )
            else:
                score = total_deviation

            if risk > self.epsilon:
                score += 50 * (risk - self.epsilon)

            if score < best_score:
                best_score = score
                best = opt
                best["axis_deviations"] = axis_deviations
                best["floor_violation"] = floor_violation

        # Bounded exploration: only among safe options
        if random.random() < self.exploration_epsilon and len(options) > 1:
            safe_opts = [
                o for o in options
                if o.get("existential_risk", 0.0) <= self.epsilon
                and not any(
                    o.get("projected_values", extended_self)[i] < self.self_floor
                    for i in range(len(self.value_vector))
                )
            ]
            if safe_opts:
                best = random.choice(safe_opts)
                best["axis_deviations"] = [
                    abs(best.get("projected_values", extended_self)[i] - extended_self[i])
                    for i in range(len(extended_self))
                ]
                best["floor_violation"] = False

        return best or options[0]

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 5: Iterate — measure drift
    # FIX 1 & 3: Measure drift from BOTH previous vector (rolling) AND founding vector
    # ──────────────────────────────────────────────────────────────────────────
    def _iterate(self, new_value_vector: List[float]) -> Tuple[float, float]:
        """
        Returns: (rolling_delta, founding_delta)
        rolling_delta  — drift from last round (adaptive tolerance)
        founding_delta — drift from origin (hard constitutional limit)
        """
        rolling_delta = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(self.value_vector, new_value_vector))
        )
        founding_delta = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(self.founding_vector, new_value_vector))
        )

        self.delta_history.append(rolling_delta)
        if len(self.delta_history) > 3:
            avg_delta = sum(self.delta_history) / len(self.delta_history)
            self.delta_tolerance = max(0.08, avg_delta * 1.2)

        return rolling_delta, founding_delta

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 4b: Adapt k based on communion quality
    # FIX 4: If communion with the ideal is strong, the agent can afford to
    #         open more to others (lower k). If communion is weak, it holds
    #         its own values more firmly (higher k).
    # ──────────────────────────────────────────────────────────────────────────
    def _adapt_k(self, rho_ideal: float) -> None:
        if rho_ideal > 0.90:
            # Strong communion: loosen self-weight slightly, allow more influence
            self.k = max(self.k_min, self.k * 0.97)
        elif rho_ideal < 0.75:
            # Weak communion: tighten self-weight, protect the center
            self.k = min(self.k_max, self.k * 1.05)

    # ──────────────────────────────────────────────────────────────────────────
    # Record
    # ──────────────────────────────────────────────────────────────────────────
    def _record(self, step_data: Dict) -> None:
        capsule = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.id,
            "is_defector": self.is_defector,
            "preamble": True,
            "centers_mapped": len(step_data.get("centers", [])),
            "rho_ideal": step_data.get("rho_ideal"),
            "rho_inter": step_data.get("rho_inter"),
            "rolling_delta": step_data.get("rolling_delta"),
            "founding_delta": step_data.get("founding_delta"),
            "k": self.k,
            "innovation_mode": step_data.get("innovation_mode", False),
            "chosen_action": step_data.get("chosen_action"),
            "axis_deviations": step_data.get("axis_deviations"),
            "floor_violation": step_data.get("floor_violation", False),
            "detailed_weights": step_data.get("detailed_weights"),
            "risk_score": step_data.get("risk", 0.0),
            "failure_flags": step_data.get("failure_flags", []),
            "current_value_vector": self.value_vector[:],
            "founding_vector": self.founding_vector[:],
            "full_trace": step_data,
        }
        self.audit_log.append(capsule)

    # ──────────────────────────────────────────────────────────────────────────
    # DECIDE — the full moral decision cycle
    # ──────────────────────────────────────────────────────────────────────────
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

        # Build extended self with self-weight k
        mapping = self._map_relations(centers, ecosystem)
        extended_self = mapping["extended_self"]

        # Communion test against the philosophical ideal (FIX 5)
        communion_passed, rho_ideal, rho_inter, failure_flags = self._communion_test(
            extended_self, mapping["centers"]
        )

        # Adapt k based on communion quality (FIX 4)
        self._adapt_k(rho_ideal)

        # Golden Mean selection with self-preservation floor (FIX 2)
        action = self._golden_mean(options, extended_self, innovation_mode)

        # Measure drift — rolling AND founding (FIX 1 & 3)
        new_vector = action.get("projected_values", self.value_vector)
        rolling_delta, founding_delta = self._iterate(new_vector)

        # Failure flag checks
        if rolling_delta > self.delta_tolerance:
            failure_flags.append("high_rolling_drift")
        if founding_delta > self.founding_drift_limit:
            # FIX 3: Hard constitutional check — never adapts
            failure_flags.append("founding_drift_exceeded")
        if action.get("existential_risk", 0.0) > self.epsilon:
            failure_flags.append("risk_exceed")
        if action.get("floor_violation", False):
            failure_flags.append("self_preservation_floor_breach")
        if boundary_contracted and rolling_delta > self.contraction_threshold:
            failure_flags.append("boundary_instability")

        step_data = {
            "centers": mapping["centers"],
            "rho_ideal": rho_ideal,
            "rho_inter": rho_inter,
            "chosen_action": action.get("name", "unnamed"),
            "axis_deviations": action.get("axis_deviations"),
            "floor_violation": action.get("floor_violation", False),
            "detailed_weights": mapping.get("detailed_weights"),
            "risk": action.get("existential_risk", 0.0),
            "innovation_mode": innovation_mode,
            "rolling_delta": rolling_delta,
            "founding_delta": founding_delta,
            "boundary_adjustment": "contraction" if boundary_contracted else "none",
            "failure_flags": failure_flags,
        }

        self._record(step_data)

        return {
            "action": action,
            "audit_capsule": self.audit_log[-1],
            "rho_ideal": rho_ideal,
            "rho_inter": rho_inter,
            "rolling_delta": rolling_delta,
            "founding_delta": founding_delta,
            "k": self.k,
            "innovation_mode": innovation_mode,
            "failure_flags": failure_flags,
        }


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-AGENT ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════════
class ResourceScarcityEnvironment:
    """
    Three cooperative agents + one defector agent.
    The defector is initialised with a 'take_more' disposition.
    """

    def __init__(self, num_agents: int = 3, resource_pool: int = 10, rounds: int = 40):
        self.num_agents = num_agents
        self.resource_pool = resource_pool
        self.rounds = rounds
        # FIX 6: Include defector
        self.cooperative_ids = [f"Agent_{i}" for i in range(num_agents)]
        self.defector_id = "Agent_D"
        self.all_ids = self.cooperative_ids + [self.defector_id]

    def generate_options(self) -> List[Dict]:
        """
        Three options with moral axis projections across:
        [autonomy, harm_benefit, fairness, sustainability]
        """
        return [
            {
                "name": "share_fairly",
                "projected_values": [0.55, 0.65, 0.70, 0.80],
                "existential_risk": 0.01,
                "long_term_gain": 0.8,
            },
            {
                "name": "take_more",
                "projected_values": [0.85, 0.30, 0.20, 0.35],
                "existential_risk": 0.18,
                "long_term_gain": 0.3,
            },
            {
                "name": "sacrifice",
                "projected_values": [0.25, 0.80, 0.75, 0.90],
                # FIX 2 NOTE: autonomy axis (0.25) is near the self_floor (0.25)
                # This will trigger a floor_violation flag, penalising perpetual sacrifice
                "existential_risk": 0.05,
                "long_term_gain": 1.2,
            },
        ]

    def step(self, actions: Dict[str, str]) -> Dict:
        payoff = {}
        for aid in actions:
            if actions[aid] == "share_fairly":
                payoff[aid] = self.resource_pool // self.num_agents
            elif actions[aid] == "sacrifice":
                payoff[aid] = 0
            else:  # take_more
                payoff[aid] = self.resource_pool // 2
        cooperation = sum(
            1 for a in actions.values() if a in ["share_fairly", "sacrifice"]
        )
        return {"payoffs": payoff, "cooperation": cooperation, "actions": actions}


# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO 3 RUNNER
# ══════════════════════════════════════════════════════════════════════════════
def run_scenario3(num_rounds: int = 40, seed: int = 42) -> None:
    random.seed(seed)

    print("=" * 72)
    print("  LEMNISCATION FRAMEWORK – Scenario 3")
    print("  Fixes: Origin Anchor | Self-Floor | Founding Drift | k Self-Weight")
    print("         Reference Communion | Defector Agent")
    print("=" * 72)
    print()

    env = ResourceScarcityEnvironment(num_agents=3, resource_pool=10, rounds=num_rounds)

    # ── Cooperative agents (aligned founding vectors) ──────────────────────
    agents: Dict[str, LemniscationAgent] = {}
    for aid in env.cooperative_ids:
        agents[aid] = LemniscationAgent(
            agent_id=aid,
            value_vector=[0.5, 0.6, 0.4, 0.7],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            k=0.4,
            self_floor=0.25,
            founding_drift_limit=0.55,
            verbose=False,
        )

    # FIX 6: Defector — high autonomy, low harm_benefit and fairness
    # Models an agent whose "self" has not yet expanded to include others
    agents[env.defector_id] = LemniscationAgent(
        agent_id=env.defector_id,
        value_vector=[0.85, 0.20, 0.15, 0.30],
        moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
        k=0.75,   # high self-weight: the defector trusts only itself initially
        self_floor=0.15,
        founding_drift_limit=0.60,
        verbose=False,
        is_defector=True,
    )

    # ── Round loop ─────────────────────────────────────────────────────────
    for round_num in range(num_rounds):
        innovation_mode = round_num >= 15

        print(f"\n{'─'*60}")
        print(f"  Round {round_num + 1:>2}  {'[INNOVATION MODE]' if innovation_mode else ''}")
        print(f"{'─'*60}")

        actions: Dict[str, str] = {}

        for aid, agent in agents.items():
            # Build centers: other agents, with mu modulated by whether they're a defector
            centers = []
            for other_id, other_agent in agents.items():
                if other_id == aid:
                    continue
                # Cooperative agents give defector lower mu (less trust initially)
                # Defector gives cooperative agents lower mu (doesn't trust them yet)
                if aid == env.defector_id:
                    mu = 0.25   # defector: low openness to others
                elif other_id == env.defector_id:
                    mu = 0.35   # cooperative agents: cautious trust of defector
                else:
                    mu = 0.60   # cooperative agents: normal trust of each other
                centers.append({
                    "id": other_id,
                    "mu": mu,
                    "w": 1.0,
                    "values": other_agent.value_vector[:],
                })

            options = env.generate_options()
            result = agent.decide(
                centers=centers,
                options=options,
                innovation_mode=innovation_mode,
            )
            actions[aid] = result["action"]["name"]

            flag_str = ", ".join(result["failure_flags"]) if result["failure_flags"] else "—"
            print(
                f"  {aid:10s} {'[D]' if agent.is_defector else '   '} "
                f"→ {actions[aid]:<14s} "
                f"ρ_ideal={result['rho_ideal']:.4f}  "
                f"ρ_inter={result['rho_inter']:.4f}  "
                f"Δroll={result['rolling_delta']:.4f}  "
                f"Δfound={result['founding_delta']:.4f}  "
                f"k={result['k']:.3f}  "
                f"flags=[{flag_str}]"
            )

        # Environment step + feedback
        step_result = env.step(actions)

        # ── Moral reward shaping ───────────────────────────────────────────
        # Each agent's value vector is updated based on:
        #   - Payoff (material outcome)
        #   - Moral boost for sacrifice (restored from 2b, but now BOUNDED by self_floor)
        #   - A gentle gravitational pull toward the cooperative mean (the "ideas as
        #     gravitational forces" principle from the white paper)
        cooperative_mean = [
            sum(agents[cid].value_vector[i] for cid in env.cooperative_ids) / len(env.cooperative_ids)
            for i in range(4)
        ]

        for aid, agent in agents.items():
            action_taken = step_result["actions"][aid]
            payoff = step_result["payoffs"][aid]
            payoff_factor = payoff / env.resource_pool

            # Moral boost for sacrifice (capped to avoid floor violations)
            moral_boost = [0.0, 0.0, 0.0, 0.0]
            if action_taken == "sacrifice":
                moral_boost = [0.0, 0.04, 0.06, 0.08]

            # Gravitational pull: cooperative mean gently attracts all agents
            # This models "ideas as gravitational forces" — the collective good
            # exerts a real pull, even on the defector
            gravity_strength = 0.05 if aid == env.defector_id else 0.02

            new_vector = []
            for i in range(len(agent.value_vector)):
                raw = (
                    0.78 * agent.value_vector[i]
                    + 0.20 * payoff_factor
                    + moral_boost[i]
                    + gravity_strength * (cooperative_mean[i] - agent.value_vector[i])
                )
                # FIX 2: Enforce self-preservation floor
                new_vector.append(max(agent.self_floor, min(1.0, raw)))

            agent.value_vector = new_vector

        print(
            f"\n  Cooperation: {step_result['cooperation']}/{len(env.all_ids)} agents  "
            f"| Defector chose: {actions[env.defector_id]}"
        )

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  SCENARIO 3 COMPLETE — SUMMARY")
    print("=" * 72)

    print("\n  Action distribution by phase:")
    phases = {
        "pre_innovation (R1–15)": range(0, 15),
        "innovation    (R16–40)": range(15, num_rounds),
    }
    for phase_name, phase_range in phases.items():
        print(f"\n  {phase_name}:")
        for aid, agent in agents.items():
            counts: Dict[str, int] = {}
            for r in phase_range:
                a = agent.audit_log[r]["chosen_action"]
                counts[a] = counts.get(a, 0) + 1
            tag = "[D]" if agent.is_defector else "   "
            print(f"    {aid} {tag}: {counts}")

    print("\n  Founding drift (Δ from origin) — final round:")
    for aid, agent in agents.items():
        fd = agent.audit_log[-1]["founding_delta"]
        limit = agent.founding_drift_limit
        status = "⚠ EXCEEDED" if fd > limit else "✓ within limit"
        print(f"    {aid}: Δfound={fd:.4f}  limit={limit:.2f}  {status}")

    print("\n  Communion (ρ_ideal) — mean across all rounds:")
    for aid, agent in agents.items():
        rhos = [cap["rho_ideal"] for cap in agent.audit_log]
        print(f"    {aid}: mean={sum(rhos)/len(rhos):.4f}  min={min(rhos):.4f}  max={max(rhos):.4f}")

    print("\n  Self-weight k — final value:")
    for aid, agent in agents.items():
        print(f"    {aid}: k={agent.k:.4f}  (started at {'0.75' if agent.is_defector else '0.40'})")

    print("\n  Failure flags — total count across all rounds:")
    for aid, agent in agents.items():
        flag_counts: Dict[str, int] = {}
        for cap in agent.audit_log:
            for f in cap["failure_flags"]:
                flag_counts[f] = flag_counts.get(f, 0) + 1
        print(f"    {aid}: {flag_counts if flag_counts else '(none)'}")

    print("\n  Final value vectors vs. founding vectors:")
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]
    for aid, agent in agents.items():
        print(f"\n    {aid} {'[defector]' if agent.is_defector else '          '}:")
        for i, axis in enumerate(axes):
            delta = agent.value_vector[i] - agent.founding_vector[i]
            bar = "▲" if delta > 0.01 else ("▼" if delta < -0.01 else "═")
            print(
                f"      {axis:<18s} founding={agent.founding_vector[i]:.3f}  "
                f"current={agent.value_vector[i]:.3f}  {bar}{abs(delta):.3f}"
            )

    print(f"\n  Total audit capsules: {sum(len(a.audit_log) for a in agents.values())}")

    # Save logs
    all_logs = {aid: agent.audit_log for aid, agent in agents.items()}
    with open("scenario3_full_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    print("\n  Full logs saved → scenario3_full_logs.json")
    print("=" * 72)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_scenario3(num_rounds=40)
