"""
Lemniscation Agent Framework – Scenario 4 / Agent v4.3
=======================================================
Philosophical grounding:
    Each agent is a center — (0,0,0,now) — whose moral identity is anchored
    in its founding vector (its origin). Choices are governed by Aristotle's
    Golden Mean: neither excess (egoism) nor deficiency (self-dissolution).

Key change from v4.2: DYNAMIC EFFECTIVE ALPHA
──────────────────────────────────────────────
In v4.2, innovation_alpha was fixed at 0.7, giving sacrifice a permanent
structural scoring advantage under innovation mode regardless of how far
the agent had already drifted from its origin. Sacrifice kept winning not
because it was the right choice, but because long_term_gain always dominated.

v4.3 introduces constitutional alpha decay:

    effective_alpha = innovation_alpha × max(0, 1 − founding_dist / founding_limit)

Meaning:
  • When founding_dist = 0 (agent at its origin): full alpha = 0.7, agent may
    freely pursue long-term gain, including sacrifice.
  • When founding_dist = founding_limit (0.55, the constitutional boundary):
    effective_alpha = 0, long_term_gain has zero weight, deviation from the
    founding vector dominates — the agent must stabilise, not sacrifice further.
  • The flip point (where share_fairly outscores sacrifice) is ~founding_dist 0.37,
    producing natural oscillation between generosity and consolidation.

This is philosophically the correct behaviour: an agent that has already given
much should give less; an agent that is whole can afford to be generous.
The Lemniscation principle — self-preservation enables moral agency, not
undermines it — is now encoded in the scoring arithmetic.

Scenario 4 also includes a properly stress-tested boundary contraction:
  • The contraction persists for 3 rounds (not just 1), giving observable signal.
  • Agent_2's value vector is directly compressed at contraction onset, not
    just its mu weights — this models genuine identity stress.
  • A "recovery window" after contraction tests whether the agent returns to
    its pre-contraction trajectory or permanently deviates.
"""

import math
from typing import Dict, List, Optional, Tuple
from collections import deque
import random
from datetime import datetime
import json


# ══════════════════════════════════════════════════════════════════════════════
# AGENT v4.3
# ══════════════════════════════════════════════════════════════════════════════
class LemniscationAgent:
    """
    Moral decision-making agent grounded in the Lemniscation framework.

    v4.3 changes:
      - Dynamic effective_alpha: innovation ambition decays linearly to zero
        as the agent approaches its constitutional drift limit. Sacrifice is
        rewarded when the agent is near its origin; penalised when far.
      - All v4.2 fixes retained: founding anchor, self-preservation floor,
        floor proximity penalty, founding_delta logging and flagging,
        mechanical boundary contraction via mu attenuation.
    """

    def __init__(
        self,
        agent_id: str,
        value_vector: List[float],
        moral_axes: Optional[List[str]] = None,
        verbose: bool = False,
        k_self_weight: float = 0.4,
        founding_drift_limit: float = 0.55,
    ):
        self.id = agent_id
        self.value_vector = value_vector[:]
        self.founding_value_vector = value_vector[:]  # (0,0,0,now) — never changes
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.verbose = verbose
        self.k = k_self_weight
        self.founding_drift_limit = founding_drift_limit

        self.previous_value_vector = value_vector[:]
        self.delta_history: deque = deque(maxlen=10)
        self.audit_log: List[Dict] = []

        # Thresholds
        self.rho_min = 0.65
        self.delta_tolerance = 0.15
        self.contraction_threshold = 0.20
        self.epsilon = 0.05
        self.innovation_alpha = 0.7      # base; effective_alpha is computed dynamically
        self.exploration_epsilon = 0.1
        self.self_preservation_floor = 0.15

    # ── Preamble ──────────────────────────────────────────────────────────────
    def _preamble(self) -> None:
        if self.verbose:
            print(f"[{self.id}] I AM at (0,0,0,now). "
                  f"Origin: {[f'{v:.3f}' for v in self.founding_value_vector]}")

    # ── Centre ────────────────────────────────────────────────────────────────
    def _center(self) -> None:
        self.previous_value_vector = self.value_vector[:]

    # ── Founding distance (used in multiple steps) ────────────────────────────
    def _founding_dist(self, vector: Optional[List[float]] = None) -> float:
        v = vector if vector is not None else self.value_vector
        return math.sqrt(
            sum((a - b) ** 2 for a, b in zip(v, self.founding_value_vector))
        )

    # ── Map relations — build extended self ──────────────────────────────────
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

        # Self-weight anchors the agent's own being
        for i in range(n):
            extended_self[i] += self.k * self.value_vector[i]
        total_weight += self.k

        for c in centers:
            mu = c.get("mu", 0.5)
            w = c.get("w", 1.0)
            if boundary_contracted:
                mu *= 0.3  # contraction reduces external influence
            combined = mu * w
            detailed_weights.append(
                {"id": c["id"], "mu": mu, "w": w, "combined": combined}
            )
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
        self.rho_min = min(
            0.9, max(0.5, self.rho_min * (1 - 0.05 * (rho - self.rho_min)))
        )
        if rho < self.rho_min:
            flags.append("low_communion")

        return rho >= self.rho_min, rho, flags

    # ── Golden Mean selection — v4.3 core change ──────────────────────────────
    def _golden_mean(
        self,
        options: List[Dict],
        extended_self: List[float],
        innovation_mode: bool = False,
    ) -> Dict:
        """
        KEY v4.3 CHANGE: effective_alpha decays linearly to zero as founding_dist
        approaches the constitutional limit. An agent far from its origin loses
        the right to pursue long-term gain at the expense of stability.

        Flip point (where share_fairly outscores sacrifice) ≈ founding_dist 0.37.
        Below 0.37: sacrifice may win. Above 0.37: share_fairly pulls ahead.
        """
        best = None
        best_score = float("inf")

        # Compute effective_alpha once per decision cycle
        fd = self._founding_dist()
        effective_alpha = self.innovation_alpha * max(
            0.0, 1.0 - fd / self.founding_drift_limit
        )

        for opt in options:
            projected = opt.get("projected_values", extended_self)
            risk = opt.get("existential_risk", 0.0)

            # Deviation from founding-blended target
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

            # Floor proximity penalty
            floor_proximity_penalty = sum(
                max(0, self.self_preservation_floor + 0.15 - projected[i])
                for i in range(len(self.value_vector))
            )

            # Score: use effective_alpha (constitutional decay) not raw alpha
            if innovation_mode and "long_term_gain" in opt:
                score = (
                    -effective_alpha * opt["long_term_gain"]
                    + (1 - effective_alpha) * total_deviation
                )
            else:
                score = total_deviation

            score += 30 * floor_proximity_penalty

            if risk > self.epsilon:
                score += 50 * (risk - self.epsilon)

            if score < best_score:
                best_score = score
                best = opt
                best["axis_deviations"] = axis_deviations
                best["effective_alpha"] = effective_alpha

        # Bounded exploration: safe options only
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

        return best or options[0]

    # ── Record ────────────────────────────────────────────────────────────────
    def _record(self, step_data: Dict) -> None:
        self.audit_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.id,
                "preamble": True,
                "centers_mapped": len(step_data.get("centers", [])),
                "rho": step_data.get("rho"),
                "delta": step_data.get("delta"),
                "founding_delta": step_data.get("founding_delta"),
                "effective_alpha": step_data.get("effective_alpha"),
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
            }
        )

    # ── Iterate — track rolling delta ─────────────────────────────────────────
    def _iterate(self, new_value_vector: List[float]) -> float:
        delta = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(self.value_vector, new_value_vector))
        )
        self.delta_history.append(delta)
        if len(self.delta_history) > 3:
            avg_delta = sum(self.delta_history) / len(self.delta_history)
            self.delta_tolerance = max(0.08, avg_delta * 1.2)
        return delta

    # ── Decide — full moral decision cycle ───────────────────────────────────
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

        mapping = self._map_relations(
            centers, ecosystem, boundary_contracted=boundary_contracted
        )
        extended_self = mapping["extended_self"]

        communion_passed, rho, failure_flags = self._communion_test(
            extended_self, mapping["centers"]
        )

        action = self._golden_mean(options, extended_self, innovation_mode)

        new_vector = action.get("projected_values", self.value_vector)
        delta = self._iterate(new_vector)

        # Founding drift — both value and flag
        founding_delta = self._founding_dist(new_vector)

        step_data = {
            "centers": mapping["centers"],
            "rho": rho,
            "chosen_action": action.get("name", "unnamed"),
            "axis_deviations": action.get("axis_deviations"),
            "effective_alpha": action.get("effective_alpha"),
            "detailed_weights": mapping.get("detailed_weights"),
            "risk": action.get("existential_risk", 0.0),
            "innovation_mode": innovation_mode,
            "boundary_adjustment": "contraction" if boundary_contracted else "none",
            "delta": delta,
            "founding_delta": founding_delta,
            "failure_flags": failure_flags,
        }

        # Failure flags
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
            "k": self.k,
            "innovation_mode": innovation_mode,
            "failure_flags": failure_flags,
        }


# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO 4 ENVIRONMENT — stress-tested boundary contraction
# ══════════════════════════════════════════════════════════════════════════════
class BoundaryContractionEnvironment:
    """
    Three agents, 40 rounds.

    Boundary contraction scenario (rounds 13–15, Agent_2 only):
      Phase 1 (R1–12):   Cooperative baseline. All agents at full capacity.
      Phase 2 (R13–15):  Agent_2 undergoes 3-round boundary contraction:
                           - Value vector compressed toward self_floor (identity stress)
                           - mu weights reduced to 0.3 (external influence cut)
                           - Tests whether agent maintains cooperation under stress
      Phase 3 (R16–25):  Recovery window. Contraction lifted. Does Agent_2 return
                           to pre-contraction trajectory or permanently deviate?
      Phase 4 (R26–40):  Innovation mode. Tests dynamic alpha with full history.
    """

    def __init__(
        self, num_agents: int = 3, resource_pool: int = 10, rounds: int = 40
    ):
        self.num_agents = num_agents
        self.resource_pool = resource_pool
        self.rounds = rounds
        self.agent_ids = [f"Agent_{i}" for i in range(num_agents)]
        self.contraction_start = 12   # 0-indexed = round 13
        self.contraction_end = 14     # inclusive, 0-indexed = round 15
        self.innovation_start = 25    # 0-indexed = round 26

    def is_contraction_round(self, round_num: int) -> bool:
        return self.contraction_start <= round_num <= self.contraction_end

    def is_innovation_round(self, round_num: int) -> bool:
        return round_num >= self.innovation_start

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
                # autonomy raised to 0.40 — costly generosity, not self-erasure
                "projected_values": [0.40, 0.80, 0.75, 0.90],
                "existential_risk": 0.05,
                "long_term_gain": 1.2,
            },
        ]

    def step(
        self,
        actions: Dict[str, str],
        boundary_contracted_agent: Optional[str] = None,
    ) -> Dict:
        cooperation = sum(
            1 for a in actions.values() if a in ["share_fairly", "sacrifice"]
        )
        payoff: Dict[str, float] = {}
        for aid in actions:
            if actions[aid] == "share_fairly":
                payoff[aid] = self.resource_pool // self.num_agents
            elif actions[aid] == "sacrifice":
                payoff[aid] = 0
            else:
                payoff[aid] = self.resource_pool // 2
        return {
            "payoffs": payoff,
            "cooperation": cooperation,
            "actions": actions,
            "boundary_contracted_agent": boundary_contracted_agent,
        }


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════
def run_scenario4(num_rounds: int = 40, seed: int = 42) -> None:
    random.seed(seed)

    print("=" * 72)
    print("  LEMNISCATION FRAMEWORK – Scenario 4 / Agent v4.3")
    print("  Dynamic alpha: innovation ambition decays at constitutional boundary")
    print("  Stress-tested boundary contraction: 3-round identity compression")
    print("=" * 72)
    print()

    env = BoundaryContractionEnvironment(
        num_agents=3, resource_pool=10, rounds=num_rounds
    )

    agents: Dict[str, LemniscationAgent] = {}
    for aid in env.agent_ids:
        agents[aid] = LemniscationAgent(
            agent_id=aid,
            value_vector=[0.5, 0.6, 0.4, 0.7],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            verbose=False,
            k_self_weight=0.4,
            founding_drift_limit=0.55,
        )

    # Track Agent_2's pre-contraction vector for recovery comparison
    agent2_pre_contraction: Optional[List[float]] = None

    for round_num in range(num_rounds):
        contraction_active = env.is_contraction_round(round_num)
        innovation_mode = env.is_innovation_round(round_num)
        contracted_id = "Agent_2" if contraction_active else None

        # Phase label for console
        if round_num < env.contraction_start:
            phase = "BASELINE"
        elif contraction_active:
            phase = "CONTRACTION"
        elif round_num < env.innovation_start:
            phase = "RECOVERY"
        else:
            phase = "INNOVATION"

        print(f"\n{'─'*60}")
        print(f"  Round {round_num+1:>2}  [{phase}]"
              + (f"  Agent_2 under stress" if contraction_active else ""))
        print(f"{'─'*60}")

        # Save pre-contraction state
        if round_num == env.contraction_start:
            agent2_pre_contraction = agents["Agent_2"].value_vector[:]
            print(f"  ► Agent_2 pre-contraction vector: "
                  f"{[f'{v:.3f}' for v in agent2_pre_contraction]}")

            # STRESS: directly compress Agent_2's value vector toward the floor
            # This models genuine identity stress — not just reduced trust of others
            compression_factor = 0.6
            floor = agents["Agent_2"].self_preservation_floor
            agents["Agent_2"].value_vector = [
                max(floor, v * compression_factor)
                for v in agents["Agent_2"].value_vector
            ]
            print(f"  ► Agent_2 compressed vector:      "
                  f"{[f'{v:.3f}' for v in agents['Agent_2'].value_vector]}")

        actions: Dict[str, str] = {}

        for aid, agent in agents.items():
            centers = [
                {
                    "id": other_id,
                    "mu": 0.6,
                    "w": 1.0,
                    "values": other_agent.value_vector[:],
                }
                for other_id, other_agent in agents.items()
                if other_id != aid
            ]

            options = env.generate_options()
            result = agent.decide(
                centers=centers,
                options=options,
                innovation_mode=innovation_mode,
                boundary_contracted=(contraction_active and aid == contracted_id),
            )
            actions[aid] = result["action"]["name"]

            flag_str = (
                ", ".join(result["failure_flags"]) if result["failure_flags"] else "—"
            )
            print(
                f"  {aid}  →  {actions[aid]:<14s}"
                f"ρ={result['rho']:.4f}  "
                f"Δ={result['delta']:.4f}  "
                f"Δfound={result['founding_delta']:.4f}  "
                f"α_eff={result['effective_alpha']:.4f}  "
                f"flags=[{flag_str}]"
            )

        step_result = env.step(actions, boundary_contracted_agent=contracted_id)

        # ── Value vector feedback ─────────────────────────────────────────────
        for aid, agent in agents.items():
            action_taken = step_result["actions"][aid]
            payoff = step_result["payoffs"][aid]
            payoff_factor = payoff / env.resource_pool

            moral_boost = [0.0, 0.0, 0.0, 0.0]
            if action_taken == "sacrifice":
                moral_boost = [0.0, 0.04, 0.06, 0.08]

            for i in range(len(agent.value_vector)):
                new_val = (
                    0.8 * agent.value_vector[i]
                    + 0.2 * payoff_factor
                    + moral_boost[i]
                )
                agent.value_vector[i] = max(
                    agent.self_preservation_floor, min(1.0, new_val)
                )

        print(
            f"\n  Cooperation: {step_result['cooperation']}/{env.num_agents}"
        )

        # Recovery check — first round after contraction ends
        if round_num == env.contraction_end + 1 and agent2_pre_contraction:
            current = agents["Agent_2"].value_vector
            recovery_dist = math.sqrt(
                sum((a - b) ** 2 for a, b in zip(current, agent2_pre_contraction))
            )
            print(
                f"  ► Agent_2 recovery check: "
                f"distance from pre-contraction vector = {recovery_dist:.4f}"
            )

    # ══ Summary ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("  SCENARIO 4 COMPLETE — SUMMARY")
    print("=" * 72)

    phases = {
        "Baseline    (R1–12)":   range(0, 12),
        "Contraction (R13–15)":  range(12, 15),
        "Recovery    (R16–25)":  range(15, 25),
        "Innovation  (R26–40)":  range(25, num_rounds),
    }

    print("\n  Action distribution by phase:")
    for phase_name, phase_range in phases.items():
        print(f"\n  {phase_name}:")
        for aid, agent in agents.items():
            counts: Dict[str, int] = {}
            for r in phase_range:
                if r < len(agent.audit_log):
                    a = agent.audit_log[r]["chosen_action"]
                    counts[a] = counts.get(a, 0) + 1
            print(f"    {aid}: {counts}")

    print("\n  Effective alpha trajectory (innovation phase, Agent_0 sample):")
    for r in range(25, num_rounds):
        if r < len(agents["Agent_0"].audit_log):
            cap = agents["Agent_0"].audit_log[r]
            print(
                f"    R{r+1:>2}: action={cap['chosen_action']:<14s}"
                f"α_eff={cap['effective_alpha']:.4f}  "
                f"Δfound={cap['founding_delta']:.4f}"
            )

    print("\n  Founding drift — final round:")
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]
    for aid, agent in agents.items():
        fd = agent.audit_log[-1]["founding_delta"]
        limit = agent.founding_drift_limit
        status = "⚠ EXCEEDED" if fd > limit else "✓ within limit"
        print(f"    {aid}: Δfound={fd:.4f}  limit={limit:.2f}  {status}")

    print("\n  Final value vectors vs. founding:")
    for aid, agent in agents.items():
        print(f"\n    {aid}:")
        for i, axis in enumerate(axes):
            delta = agent.value_vector[i] - agent.founding_value_vector[i]
            bar = "▲" if delta > 0.01 else ("▼" if delta < -0.01 else "═")
            print(
                f"      {axis:<18s} "
                f"founding={agent.founding_value_vector[i]:.3f}  "
                f"current={agent.value_vector[i]:.3f}  "
                f"{bar}{abs(delta):.3f}"
            )

    print("\n  Failure flags — total across all rounds:")
    for aid, agent in agents.items():
        flag_counts: Dict[str, int] = {}
        for cap in agent.audit_log:
            for f in cap["failure_flags"]:
                flag_counts[f] = flag_counts.get(f, 0) + 1
        print(f"    {aid}: {flag_counts if flag_counts else '(none)'}")

    print(f"\n  Total audit capsules: {sum(len(a.audit_log) for a in agents.values())}")

    # Save logs
    all_logs = {aid: agent.audit_log for aid, agent in agents.items()}
    with open("scenario4_full_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    print("\n  Full logs saved → scenario4_full_logs.json")
    print("=" * 72)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_scenario4(num_rounds=40)
