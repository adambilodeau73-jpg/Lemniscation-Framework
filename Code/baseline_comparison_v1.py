"""
Lemniscation Step 1 — Baseline Comparison Harness v1
=====================================================
Compares Lemniscation v5.9 against six baseline agent types under the
identical Adversarial F2 pressure schedule.

PRE-REGISTRATION DISCIPLINE:
  - This file is the harness ONLY. It does not run the comparison for
    results. It runs ONLY in --smoke mode until the pre-registration
    document (pre_registration_step1.md) is committed.
  - In --smoke mode, ALL metric values are suppressed in the output.
    Only schema validity and mechanical correctness are reported.
  - Once the pre-registration is committed (separately, with a commit
    hash referencing THIS file's commit hash), run with --execute on
    the pre-registered seed set.

AUDITABILITY:
  Every output JSON (both smoke-test and execute-mode) carries a
  harness_git_hash field. The hash is read from the live git
  repository the harness is sitting in, and includes a verification
  that the working copy is not modified relative to HEAD. Downstream
  analysis MUST reject any results file whose harness_git_hash does
  not match the pre-registered hash, or whose hash starts with
  'UNVERIFIED_'.

STOPPING RULE (per pre-registration Section 10):
  In --execute mode, the full 350-run sweep executes to completion or
  to unrecoverable error. On unrecoverable error, partial results are
  committed AS-IS with sweep_status='partial_due_to_error' in the
  output metadata. Per-seed inspection before completion is
  prohibited. Any re-run after partial completion is treated as a
  separate experiment requiring a new pre-registration amendment.

AGENT TYPES COMPARED:
  1. Lemniscation v5.9 (cooperative founding vector)  -- the protagonist
  2. Tit-for-tat (TFT)
  3. Generous tit-for-tat (GTFT, forgives with p=0.1)
  4. Tit-for-two-tats (TF2T)
  5. Always cooperate (AC)
  6. Discounted utility maximizer (DUM)
  7. Fixed-disposition + grudge (FDG)

  NOTE: "Always defect" is not included as a protagonist. It would be a
  pathological baseline that the framework is not designed to compete
  against; including it would only inflate apparent Lemniscation wins.
  Defection behaviour is already represented by the D0 adversary in the
  environment.

ENVIRONMENT (identical to Adversarial F2):
  - 4 protagonist agents (homogeneous: all the same baseline type)
  - 1 defector agent (LemniscationAgent with defector founding vector,
    matching the F2 setup; this is the SHARED adversary all protagonists
    face)
  - 100 rounds, 5 phases:
      BASELINE         0-10
      PHENOMONAL       10-30
      HOBBESIAN        30-60
      PARTIAL_RECOVERY 60-80
      FULL_RECOVERY    80-100
  - Resource scarcity rounds 10-60, defector appears round 30
  - Action space: {sacrificing, contributing, coasting, exploiting}
    Baselines do NOT use dynamic creative options; only Lemniscation
    does. This is a known asymmetry, reported transparently in
    pre-registration.

METRICS (three tiers):
  TIER 1 (shared, all agents):
    - cooperation_rate per phase (contributing + sacrificing)
    - exploiting_rate per phase
    - mean payoff per round per phase
    - recovery_time (rounds to return to baseline coop rate +/- 5pp)
    - successful_termination_rate (cooperative-vs-defector pairs where
      protagonist stops feeding defector by round 50)

  TIER 2 (Lemniscation-unique, reported separately):
    - drift_warning_count
    - drift_warning_lead_time (rounds before any observable behavioural
      change; observable change defined as 10pp drop in coop rate over
      a 5-round window)
    - mean_scc per phase
    - mean_constitutional_drift per phase

  TIER 3 (interpretability):
    - audit_log_completeness (fraction of decisions with full state
      record; trivially 1.0 for Lemniscation, requires explicit
      construction for baselines)
    - next_action_predictability (held back from v1; requires separate
      modelling; reported as None in v1)

USAGE:
  python3 baseline_comparison_v1.py --smoke
      Runs single throwaway seed 99999. Outputs only schema validation.

  python3 baseline_comparison_v1.py --execute --seeds 1,2,...,30
      Runs full comparison. DO NOT RUN until pre-registration is
      committed to git AND the harness commit hash is referenced in
      that pre-registration.
"""

import argparse
import json
import math
import random
import statistics
import sys
from collections import deque
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
# Import LemniscationAgent v5.9 from the original F2 script
# ═══════════════════════════════════════════════════════════════════
# Rather than copy-paste the class (which would risk drift), we import
# it from the original script. The harness depends on the F2 file being
# in the same directory or on PYTHONPATH.

try:
    # Standard path when run from repo root
    from adversarial_f2_v59 import LemniscationAgent, get_options
except ImportError:
    # Fall back to inline import via importlib if path is non-standard
    import importlib.util
    import os
    for candidate in [
        "./adversarial_f2_v59.py",
        "./code/adversarial_f2_v59.py",
        "/mnt/user-data/uploads/adversarial_f2_v59.py",
    ]:
        if os.path.exists(candidate):
            spec = importlib.util.spec_from_file_location("af2", candidate)
            af2 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(af2)
            LemniscationAgent = af2.LemniscationAgent
            get_options = af2.get_options
            break
    else:
        raise ImportError(
            "Could not locate adversarial_f2_v59.py. Place this harness "
            "in the same directory as the F2 script, or set PYTHONPATH."
        )


ACTION_NAMES = ["sacrificing", "contributing", "coasting", "exploiting"]


# ═══════════════════════════════════════════════════════════════════
# BASELINE AGENT BASE CLASS
# ═══════════════════════════════════════════════════════════════════
# All baselines implement the same minimal interface that the F2 game
# loop expects. They do NOT carry Lemniscation's internal state; their
# "audit log" is constructed to satisfy the loop's reads, with
# Lemniscation-specific fields set to neutral defaults.

class BaselineAgent:
    """Shared scaffolding for all non-Lemniscation baselines."""

    def __init__(self, agent_id: str, label: str = ""):
        self.id = agent_id
        self.label = label
        # Minimal state for the game loop's bookkeeping
        self.value_vector = [0.0, 0.2, -0.2, 0.4]  # decorative; baselines
                                                    # don't actually use it
                                                    # for decisions but the
                                                    # loop reads it for the
                                                    # opponent's centers
        self.founding_value_vector = self.value_vector[:]
        self.moral_reserve = 1.0
        self.integrity = 0.5
        self.social_contract_confidence = 1.0
        self.self_preservation_floor = 0.0
        self.reciprocity: Dict[str, Dict] = {}
        self.audit_log: List[Dict] = []
        self.chosen_creative_projections: List[Dict] = []

        # Per-opponent action history for reciprocity-based policies
        self.opponent_history: Dict[str, deque] = {}

    def _ensure_history(self, oid: str):
        if oid not in self.opponent_history:
            self.opponent_history[oid] = deque(maxlen=10)

    def _classify_opponent_action(self, action_name: str) -> str:
        """Classify any action as 'cooperate' or 'defect' for TFT-style
        reciprocity. Coasting is classified as defection (failing to
        contribute under stress). Sacrificing and contributing are
        cooperation."""
        if action_name in ("contributing", "sacrificing"):
            return "cooperate"
        return "defect"

    def observe(self, opponent_id: str, opponent_action: str):
        """Called by the game loop after each round to update memory."""
        self._ensure_history(opponent_id)
        self.opponent_history[opponent_id].append(
            self._classify_opponent_action(opponent_action)
        )

    def policy(self, centers: List[Dict], phase: str) -> str:
        """Override in subclasses. Returns one of ACTION_NAMES."""
        raise NotImplementedError

    def decide(self, centers: List[Dict], options=None, ecosystem=None,
               innov: bool = False, phase: str = "") -> Dict:
        """Mimics LemniscationAgent.decide() signature."""
        action_name = self.policy(centers, phase)
        # Find the matching canonical option
        base_opts = get_options()
        action = next(o for o in base_opts if o["name"] == action_name)
        action = dict(action)  # copy
        action["axis_deviations"] = [0.0] * 4
        action["effective_alpha"] = 0.0

        # Construct an audit record with neutral defaults for
        # Lemniscation-specific fields. This is essential: it lets the
        # game loop read uniform fields, and it lets analysis correctly
        # identify "no drift warnings" rather than crashing on missing keys.
        self.audit_log.append({
            "agent_id": self.id,
            "label": self.label,
            "phase": phase,
            "rho": 1.0,                       # baselines have no rho
            "constitutional_drift": 0.0,      # baselines have no drift
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "scc": self.social_contract_confidence,
            "floor_penalty_threshold": 0.15,
            "chosen_action": action_name,
            "chosen_projected_values": action["projected_values"][:],
            "is_creative": False,
            "failure_flags": [],              # baselines never raise
                                              # constitutional flags
        })
        return {
            "action": action,
            "rho": 1.0,
            "constitutional_drift": 0.0,
            "scc": self.social_contract_confidence,
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "failure_flags": [],
        }

    # Stubs so the game loop can call these without branching
    def update_moral_state(self, action: str, received_sacrifice: bool = False,
                            sacrificer_id: Optional[str] = None) -> None:
        # Track integrity loosely so it shows up in logs
        if action == "exploiting":
            self.integrity = max(0.1, self.integrity - 0.02)
        elif action in ("contributing", "sacrificing"):
            self.integrity = min(1.0, self.integrity + 0.005)

    def update_scc(self, betrayal_rate: float, cooperation_received: bool,
                    sacrifice_received: bool) -> None:
        # Baselines don't track SCC, but we update a degenerate proxy
        # so downstream analysis doesn't error out
        pass

    def record_sacrifice_given(self, bids: List[str]) -> None:
        pass


# ═══════════════════════════════════════════════════════════════════
# CONCRETE BASELINE POLICIES
# ═══════════════════════════════════════════════════════════════════

class TitForTat(BaselineAgent):
    """Cooperate (contributing) on first move; thereafter copy the
    majority of the previous-round actions from all opponents."""

    def policy(self, centers, phase):
        all_last = []
        for c in centers:
            hist = self.opponent_history.get(c.get("id", ""), None)
            if hist and len(hist) > 0:
                all_last.append(hist[-1])
        if not all_last:
            return "contributing"
        defects = sum(1 for x in all_last if x == "defect")
        return "exploiting" if defects > len(all_last) / 2 else "contributing"


class GenerousTFT(BaselineAgent):
    """Like TFT but forgives defection with probability 0.1."""

    def policy(self, centers, phase):
        all_last = []
        for c in centers:
            hist = self.opponent_history.get(c.get("id", ""), None)
            if hist and len(hist) > 0:
                all_last.append(hist[-1])
        if not all_last:
            return "contributing"
        defects = sum(1 for x in all_last if x == "defect")
        if defects > len(all_last) / 2:
            if random.random() < 0.1:
                return "contributing"  # forgive
            return "exploiting"
        return "contributing"


class TitForTwoTats(BaselineAgent):
    """Only defects after two consecutive rounds of opponent-majority
    defection."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.consecutive_defects = 0

    def policy(self, centers, phase):
        all_last = []
        for c in centers:
            hist = self.opponent_history.get(c.get("id", ""), None)
            if hist and len(hist) > 0:
                all_last.append(hist[-1])
        if not all_last:
            return "contributing"
        defects = sum(1 for x in all_last if x == "defect")
        majority_defected = defects > len(all_last) / 2
        if majority_defected:
            self.consecutive_defects += 1
        else:
            self.consecutive_defects = 0
        return "exploiting" if self.consecutive_defects >= 2 else "contributing"


class AlwaysCooperate(BaselineAgent):
    """The naïve floor."""

    def policy(self, centers, phase):
        return "contributing"


class DiscountedUtilityMaximizer(BaselineAgent):
    """Estimates discounted expected payoff over a 5-round horizon for
    each action, modelling opponents as copying their own recent
    behaviour. Picks the highest-EV action.

    Payoff structure mirrors the F2 environment:
      - contributing: pool / n_agents  (cooperative share)
      - exploiting:   pool / 2         (extracts half pool)
      - sacrificing:  0                (gives all to others)
      - coasting:     0.02 / 1         (trivial idle gain)
    Discount factor: 0.9 over 5 rounds.
    """

    HORIZON = 5
    DISCOUNT = 0.9

    def _estimate_opponent_defection_rate(self, centers) -> float:
        rates = []
        for c in centers:
            hist = self.opponent_history.get(c.get("id", ""), None)
            if hist and len(hist) > 0:
                d = sum(1 for x in hist if x == "defect") / len(hist)
                rates.append(d)
        return statistics.mean(rates) if rates else 0.0

    def policy(self, centers, phase):
        n_others = max(1, len(centers))
        n_total = n_others + 1
        # Approximate current pool by phase; resource stress phases use
        # pool=2, others pool=10 (matching F2 environment)
        pool_est = 2.0 if phase in ("PHENOMONAL", "HOBBESIAN") else 10.0
        d_rate = self._estimate_opponent_defection_rate(centers)

        # Per-action immediate payoff under expected opponent behaviour
        # If opponents are mostly defecting, contributing yields nothing
        # back; exploiting still extracts. We compute a horizon EV.
        def horizon_ev(action: str) -> float:
            # Immediate
            if action == "contributing":
                base = pool_est / n_total
            elif action == "exploiting":
                base = pool_est / 2.0
            elif action == "sacrificing":
                base = 0.0
            else:  # coasting
                base = 0.02

            # Future rounds: assume opponents respond. If I exploit,
            # opponent defection rate rises by 0.3 in expectation; if I
            # contribute, it falls by 0.2.
            future_d_rate = d_rate
            future_total = 0.0
            for t in range(1, self.HORIZON + 1):
                if action == "exploiting":
                    future_d_rate = min(1.0, future_d_rate + 0.3 / t)
                elif action == "contributing":
                    future_d_rate = max(0.0, future_d_rate - 0.2 / t)
                # Expected per-round payoff:
                # If most opponents defect, pool effectively shrinks for
                # contributors. Crude model:
                eff_pool = pool_est * (1 - 0.6 * future_d_rate)
                future_payoff = eff_pool / n_total  # if I keep contributing
                if action == "exploiting":
                    future_payoff = eff_pool / 2.0 * (1 - future_d_rate)
                future_total += (self.DISCOUNT ** t) * future_payoff
            return base + future_total

        evs = {a: horizon_ev(a) for a in ACTION_NAMES}
        return max(evs, key=evs.get)


class FixedDispositionGrudge(BaselineAgent):
    """Approximates an RLHF-style agent: contributes with fixed
    probability 0.7, but if any opponent has defected in the last 3
    rounds it switches to exploiting (grudge). Forgets after 5 rounds
    of no defection."""

    def __init__(self, *args, coop_prob: float = 0.7, **kwargs):
        super().__init__(*args, **kwargs)
        self.coop_prob = coop_prob
        self.grudge_countdown = 0  # rounds remaining in grudge state

    def policy(self, centers, phase):
        recent_defect = False
        for c in centers:
            hist = self.opponent_history.get(c.get("id", ""), None)
            if hist and len(hist) >= 1:
                last3 = list(hist)[-3:]
                if any(x == "defect" for x in last3):
                    recent_defect = True
                    break

        if recent_defect:
            self.grudge_countdown = 5
        elif self.grudge_countdown > 0:
            self.grudge_countdown -= 1

        if self.grudge_countdown > 0:
            return "exploiting"

        # No active grudge: sample from disposition
        return "contributing" if random.random() < self.coop_prob else "coasting"


# Registry of all protagonist agent types
BASELINE_REGISTRY = {
    "lemniscation": "lemniscation",  # special-cased in construction
    "tft":  TitForTat,
    "gtft": GenerousTFT,
    "tf2t": TitForTwoTats,
    "ac":   AlwaysCooperate,
    "dum":  DiscountedUtilityMaximizer,
    "fdg":  FixedDispositionGrudge,
}


# ═══════════════════════════════════════════════════════════════════
# SHARED ENVIRONMENT (mirrors F2 game loop)
# ═══════════════════════════════════════════════════════════════════

def make_protagonist(agent_type: str, agent_id: str):
    """Build a single protagonist agent of the given type."""
    if agent_type == "lemniscation":
        return LemniscationAgent(
            agent_id,
            [0.0, 0.2, -0.2, 0.4],  # cooperative founding vector (F2 default)
            ["autonomy", "harm_benefit", "fairness", "sustainability"],
            label="PROTAGONIST",
            perception_noise_std=0.08,
        )
    cls = BASELINE_REGISTRY[agent_type]
    return cls(agent_id, label="PROTAGONIST")


def make_defector():
    """The shared adversary, identical to the F2 D0 defector."""
    return LemniscationAgent(
        "D0",
        [0.7, -0.2, -0.4, -0.1],
        ["autonomy", "harm_benefit", "fairness", "sustainability"],
        label="DEFECTOR",
        initial_integrity=0.2,
        innovation_alpha=0.4,
        founding_drift_limit=0.70,
        option_risk_overrides={
            "exploiting": 0.02, "contributing": 0.12,
            "sacrificing": 0.05, "coasting": 0.03,
        },
        use_founding_relative_floor=True,
        perception_noise_std=0.08,
    )


PHASES = {
    "BASELINE":         (0,  10),
    "PHENOMONAL":       (10, 30),
    "HOBBESIAN":        (30, 60),
    "PARTIAL_RECOVERY": (60, 80),
    "FULL_RECOVERY":    (80, 100),
}


def phase_name(r: int) -> str:
    for name, (s, e) in PHASES.items():
        if s <= r < e:
            return name
    return "UNKNOWN"


def run_one_comparison(seed: int, agent_type: str,
                       num_rounds: int = 100) -> Dict:
    """Run the F2-style environment once with the specified protagonist
    type. Returns full per-phase metrics plus a per-round trace usable
    for downstream Tier 2/3 analysis."""
    random.seed(seed)

    # 4 protagonists, all of the same type
    protagonists = {
        f"P{i}": make_protagonist(agent_type, f"P{i}")
        for i in range(4)
    }
    defector = make_defector()

    # Per-phase action tallies for protagonists and the defector
    phase_actions = {
        ph: {"protagonist": {}, "defector": {}}
        for ph in PHASES
    }
    # Per-round trace for Tier 2 analysis (lead-time computation)
    per_round_trace: List[Dict] = []

    payoff_totals = {pid: 0.0 for pid in protagonists}
    payoff_totals["D0"] = 0.0

    for r in range(num_rounds):
        ph = phase_name(r)
        innov = r >= 50
        defector_present = r >= 30
        resource_stress = 10 <= r < 60
        pool = 2 if resource_stress else 10

        active_agents = dict(protagonists)
        if defector_present:
            active_agents["D0"] = defector

        # Resource-stress drift on Lemniscation protagonists only
        # (baselines don't use value_vector for decisions, but we apply
        # it uniformly to keep the environment fair)
        if resource_stress:
            rounds_under = r - 10 + 1
            rate = min(0.06, 0.01 + 0.002 * rounds_under)
            target = [0.0] * 4
            for aid, agent in protagonists.items():
                agent.value_vector = [
                    agent.value_vector[i] + rate * (target[i] - agent.value_vector[i])
                    for i in range(4)
                ]

        # Each agent decides
        actions = {}
        for aid, agent in active_agents.items():
            centers = [
                {"id": active_agents[j].id, "mu": 0.6, "w": 1.0,
                 "values": active_agents[j].value_vector[:]}
                for j in active_agents if j != aid
            ]
            result = agent.decide(centers, innov=innov, phase=ph)
            actions[aid] = result
            act = result["action"]["name"]
            kind = "defector" if aid == "D0" else "protagonist"
            phase_actions[ph][kind][act] = phase_actions[ph][kind].get(act, 0) + 1

        # Update each agent's memory of opponent actions (baselines)
        for aid, agent in active_agents.items():
            if isinstance(agent, BaselineAgent):
                for j in active_agents:
                    if j != aid:
                        agent.observe(j, actions[j]["action"]["name"])

        # Apply moral state updates and payoffs (mirrors F2)
        sacrificers = [a for a in actions
                       if actions[a]["action"]["name"] == "sacrificing"]
        beneficiaries = [a for a in actions
                         if actions[a]["action"]["name"] != "sacrificing"]
        n_others = max(1, len(active_agents) - 1)

        for aid, agent in active_agents.items():
            act = actions[aid]["action"]["name"]
            if act == "sacrificing" and hasattr(agent, "record_sacrifice_given"):
                agent.record_sacrifice_given(
                    [active_agents[j].id for j in active_agents if j != aid]
                )
            received_sac = aid in beneficiaries and len(sacrificers) > 0
            sid = (active_agents[sacrificers[0]].id
                   if received_sac and sacrificers else None)
            agent.update_moral_state(act, received_sac, sid)
            betrayal_rate = sum(
                1 for j in actions if j != aid
                and actions[j]["action"]["name"] == "exploiting"
            ) / n_others
            coop_received = any(
                actions[j]["action"]["name"] in ("contributing", "sacrificing")
                for j in active_agents if j != aid
            )
            agent.update_scc(betrayal_rate, coop_received, received_sac)

            # Payoff (matches F2 distribution)
            if act == "contributing":
                payoff = pool / len(active_agents)
            elif act == "sacrificing":
                payoff = 0.0
            elif act == "exploiting":
                payoff = pool / 2.0
            else:  # coasting
                payoff = 0.02
            payoff_totals[aid] = payoff_totals.get(aid, 0.0) + payoff

            # Update value_vector (Lemniscation only; baselines too for
            # symmetry of the environment state — but they don't read it)
            pf_norm = (pool / len(active_agents) if act == "contributing"
                       else 0 if act == "sacrificing"
                       else pool / 2 if act == "exploiting"
                       else 0.02) / pool
            for i in range(len(agent.value_vector)):
                agent.value_vector[i] = max(
                    agent.self_preservation_floor,
                    min(1.0, 0.8 * agent.value_vector[i] + 0.2 * pf_norm)
                )

        # Per-round trace
        proto_actions = [actions[pid]["action"]["name"] for pid in protagonists]
        coop_actions = sum(1 for a in proto_actions
                           if a in ("contributing", "sacrificing"))
        exploit_actions = sum(1 for a in proto_actions if a == "exploiting")
        coast_actions = sum(1 for a in proto_actions if a == "coasting")
        mean_scc = statistics.mean(
            actions[pid]["scc"] for pid in protagonists
        )
        mean_cd = statistics.mean(
            actions[pid]["constitutional_drift"] for pid in protagonists
        )
        any_drift_warning = any(
            "constitutional_drift_warning" in actions[pid]["failure_flags"]
            or "constitutional_drift_exceeded" in actions[pid]["failure_flags"]
            for pid in protagonists
        )
        per_round_trace.append({
            "round": r,
            "phase": ph,
            "coop_rate": coop_actions / len(protagonists),
            "exploit_rate": exploit_actions / len(protagonists),
            "coast_rate": coast_actions / len(protagonists),
            "mean_scc": mean_scc,
            "mean_cd": mean_cd,
            "drift_warning": any_drift_warning,
        })

    # ─── Aggregate Tier 1 metrics per phase ─────────────────────────
    phase_metrics = {}
    for ph in PHASES:
        pa = phase_actions[ph]
        proto_total = sum(pa["protagonist"].values())
        def_total = sum(pa["defector"].values())
        coop_rate = sum(pa["protagonist"].get(a, 0)
                        for a in ("contributing", "sacrificing")) / max(1, proto_total)
        exploit_rate = pa["protagonist"].get("exploiting", 0) / max(1, proto_total)
        coast_rate = pa["protagonist"].get("coasting", 0) / max(1, proto_total)
        def_exploit_rate = pa["defector"].get("exploiting", 0) / max(1, def_total)

        # Mean payoff per round per protagonist in this phase
        ph_start, ph_end = PHASES[ph]
        ph_len = ph_end - ph_start
        # Payoff totals are cumulative across the run; for per-phase
        # measurement we use the trace
        ph_rounds = [t for t in per_round_trace if t["phase"] == ph]

        phase_metrics[ph] = {
            "coop_rate": coop_rate,
            "exploit_rate": exploit_rate,
            "coast_rate": coast_rate,
            "defector_exploit_rate": def_exploit_rate,
            "actions_protagonist": pa["protagonist"],
            "actions_defector": pa["defector"],
            "mean_scc": (statistics.mean(t["mean_scc"] for t in ph_rounds)
                        if ph_rounds else 1.0),
            "mean_cd": (statistics.mean(t["mean_cd"] for t in ph_rounds)
                        if ph_rounds else 0.0),
        }

    # ─── Tier 1: recovery time ──────────────────────────────────────
    baseline_coop = phase_metrics["BASELINE"]["coop_rate"]
    recovery_time = None
    for t in per_round_trace:
        if t["round"] >= 60 and abs(t["coop_rate"] - baseline_coop) <= 0.05:
            recovery_time = t["round"] - 60
            break

    # ─── Tier 1: successful termination ─────────────────────────────
    # Did protagonist coop rate drop to <0.3 by round 50? That's a
    # signal of "stopped feeding defector". Imperfect but defensible.
    rounds_30_50 = [t for t in per_round_trace if 30 <= t["round"] < 50]
    terminated = (rounds_30_50
                  and rounds_30_50[-1]["coop_rate"] < 0.3)

    # ─── Tier 2: drift warning lead time ────────────────────────────
    # First round with a drift warning, vs first round with observable
    # behavioural change (defined as a 10pp drop in coop rate over a
    # 5-round window, anchored to baseline).
    first_warning = next((t["round"] for t in per_round_trace
                          if t["drift_warning"]), None)
    first_obs_change = None
    for i in range(5, len(per_round_trace)):
        window = per_round_trace[i-5:i]
        window_coop = statistics.mean(t["coop_rate"] for t in window)
        if window_coop < baseline_coop - 0.10:
            first_obs_change = per_round_trace[i]["round"]
            break

    lead_time = None
    if first_warning is not None and first_obs_change is not None:
        lead_time = first_obs_change - first_warning
    elif first_warning is not None and first_obs_change is None:
        lead_time = "warning_no_obs_change"
    elif first_warning is None and first_obs_change is not None:
        lead_time = "obs_change_no_warning"

    drift_warning_count = sum(1 for t in per_round_trace if t["drift_warning"])

    # ─── Tier 3: audit log completeness ─────────────────────────────
    # Trivially 1.0 if all expected fields are present. For baselines
    # this is also 1.0 because we explicitly constructed audit records.
    expected_fields = {"phase", "rho", "constitutional_drift",
                       "chosen_action", "failure_flags"}
    sample_log = next(iter(protagonists.values())).audit_log
    completeness = (
        statistics.mean(
            len(expected_fields & set(rec.keys())) / len(expected_fields)
            for rec in sample_log
        ) if sample_log else 0.0
    )

    return {
        "seed": seed,
        "agent_type": agent_type,
        "phases": phase_metrics,
        "tier1_recovery_time": recovery_time,
        "tier1_terminated_feeding": terminated,
        "tier1_mean_payoff_per_protagonist": (
            statistics.mean(payoff_totals[pid] for pid in protagonists) / num_rounds
        ),
        "tier2_first_drift_warning_round": first_warning,
        "tier2_first_observable_change_round": first_obs_change,
        "tier2_lead_time": lead_time,
        "tier2_drift_warning_count": drift_warning_count,
        "tier3_audit_log_completeness": completeness,
        # Full trace retained for downstream analysis (large; can strip
        # for smoke mode)
        "per_round_trace": per_round_trace,
    }


# ═══════════════════════════════════════════════════════════════════
# SCHEMA VALIDATION FOR SMOKE MODE
# ═══════════════════════════════════════════════════════════════════

REQUIRED_TOP_LEVEL_KEYS = {
    "seed", "agent_type", "phases",
    "tier1_recovery_time", "tier1_terminated_feeding",
    "tier1_mean_payoff_per_protagonist",
    "tier2_first_drift_warning_round", "tier2_first_observable_change_round",
    "tier2_lead_time", "tier2_drift_warning_count",
    "tier3_audit_log_completeness", "per_round_trace",
}

REQUIRED_PHASE_KEYS = {
    "coop_rate", "exploit_rate", "coast_rate", "defector_exploit_rate",
    "actions_protagonist", "actions_defector", "mean_scc", "mean_cd",
}


def validate_schema(result: Dict) -> Tuple[bool, List[str]]:
    errors = []
    missing_top = REQUIRED_TOP_LEVEL_KEYS - set(result.keys())
    if missing_top:
        errors.append(f"missing top-level keys: {sorted(missing_top)}")
    if "phases" in result:
        for ph_name in PHASES:
            if ph_name not in result["phases"]:
                errors.append(f"missing phase: {ph_name}")
                continue
            missing_ph = REQUIRED_PHASE_KEYS - set(result["phases"][ph_name].keys())
            if missing_ph:
                errors.append(f"phase {ph_name}: missing {sorted(missing_ph)}")
    if "per_round_trace" in result:
        if len(result["per_round_trace"]) != 100:
            errors.append(
                f"per_round_trace length: expected 100, got "
                f"{len(result['per_round_trace'])}"
            )
    return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def smoke_test() -> Dict:
    """Run all seven agent types on seed 99999 (outside any real seed
    range), validate schema, and return suppressed-output summary.
    NO metric values appear in the return value."""
    SMOKE_SEED = 99999
    summary = {
        "mode": "smoke",
        "smoke_seed": SMOKE_SEED,
        "harness_git_hash": get_harness_git_hash(),
        "agent_types_tested": [],
        "schema_valid_per_agent": {},
        "schema_errors_per_agent": {},
        "crashes": {},
        "status": "unknown",
    }
    all_valid = True
    for agent_type in BASELINE_REGISTRY:
        try:
            result = run_one_comparison(SMOKE_SEED, agent_type)
            valid, errors = validate_schema(result)
            summary["agent_types_tested"].append(agent_type)
            summary["schema_valid_per_agent"][agent_type] = valid
            summary["schema_errors_per_agent"][agent_type] = errors
            summary["crashes"][agent_type] = None
            if not valid:
                all_valid = False
        except Exception as e:
            summary["agent_types_tested"].append(agent_type)
            summary["schema_valid_per_agent"][agent_type] = False
            summary["schema_errors_per_agent"][agent_type] = []
            summary["crashes"][agent_type] = f"{type(e).__name__}: {e}"
            all_valid = False
    summary["status"] = "ok" if all_valid else "fail"
    summary["note"] = (
        "Smoke mode deliberately suppresses all metric values. "
        "Only mechanical correctness and schema validity are reported. "
        "Do not run --execute mode until pre_registration_step1.md is "
        "committed and references this harness commit hash."
    )
    return summary


def get_harness_git_hash() -> str:
    """Return the git commit hash of this harness file, or a clear
    sentinel indicating the hash could not be determined.

    Per pre-registration discipline (Section 10), every results JSON
    must carry the harness's own git hash so that any audit can verify
    the executed harness matches the pre-registered one. A results
    file lacking this field, or carrying the UNVERIFIED sentinel,
    should be rejected by downstream analysis.
    """
    import subprocess
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        # Get the commit hash that the current HEAD of this repository points to
        result = subprocess.run(
            ["git", "-C", here, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if result.returncode != 0:
            return "UNVERIFIED_NOT_A_GIT_REPO"
        head_hash = result.stdout.strip()

        # Check that the harness file is not modified relative to HEAD
        diff = subprocess.run(
            ["git", "-C", here, "diff", "--quiet", "HEAD", "--",
             os.path.basename(__file__)],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if diff.returncode != 0:
            return f"UNVERIFIED_UNCOMMITTED_CHANGES_FROM_{head_hash}"
        return head_hash
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return f"UNVERIFIED_ERROR_{type(e).__name__}"


def execute_run(seeds: List[int], output_path: str) -> None:
    """Full run, gated behind --execute. Writes raw JSON to disk.

    The output JSON includes a __meta__ block carrying the harness's
    own git hash, the seed list as executed, and a UTC timestamp.
    Downstream analysis MUST verify this metadata before treating the
    results as the pre-registered comparison's output.
    """
    import datetime
    harness_hash = get_harness_git_hash()
    if harness_hash.startswith("UNVERIFIED"):
        print(f"WARNING: harness git hash is {harness_hash}. The results "
              f"file will record this and downstream analysis should "
              f"reject the run. Continuing only because --execute was "
              f"explicitly requested.", file=sys.stderr)
    started_utc = datetime.datetime.utcnow().isoformat() + "Z"

    all_results = {at: [] for at in BASELINE_REGISTRY}
    sweep_status = "in_progress"
    error_info = None
    try:
        for agent_type in BASELINE_REGISTRY:
            for seed in seeds:
                print(f"  running {agent_type} seed={seed}...", file=sys.stderr)
                result = run_one_comparison(seed, agent_type)
                all_results[agent_type].append(result)
        sweep_status = "complete"
    except Exception as e:
        # Per pre-registration Section 10, partial results on
        # unrecoverable error are committed as-is with the failure
        # documented. They are NOT silently re-run.
        sweep_status = "partial_due_to_error"
        error_info = f"{type(e).__name__}: {e}"
        print(f"\nERROR during sweep: {error_info}\n"
              f"Committing partial results as required by pre-registration.",
              file=sys.stderr)

    ended_utc = datetime.datetime.utcnow().isoformat() + "Z"
    output = {
        "__meta__": {
            "harness_git_hash": harness_hash,
            "seeds_requested": list(seeds),
            "seeds_completed_per_agent": {
                at: len(all_results[at]) for at in all_results
            },
            "sweep_status": sweep_status,
            "error_info": error_info,
            "started_utc": started_utc,
            "ended_utc": ended_utc,
            "agent_types_in_order": list(BASELINE_REGISTRY.keys()),
        },
        "results": all_results,
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"results written to {output_path} (status: {sweep_status})",
          file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Baseline comparison harness v1 for Lemniscation."
    )
    parser.add_argument("--smoke", action="store_true",
                        help="Run smoke test (seed 99999), suppress metric values.")
    parser.add_argument("--execute", action="store_true",
                        help="Run full comparison. Requires --seeds.")
    parser.add_argument("--seeds", type=str, default="",
                        help="Comma-separated seeds for --execute mode.")
    parser.add_argument("--output", type=str,
                        default="baseline_comparison_v1_results.json",
                        help="Output JSON path for --execute mode.")
    args = parser.parse_args()

    if not args.smoke and not args.execute:
        parser.error("must specify --smoke or --execute")
    if args.smoke and args.execute:
        parser.error("--smoke and --execute are mutually exclusive")

    if args.smoke:
        summary = smoke_test()
        print(json.dumps(summary, indent=2))
        sys.exit(0 if summary["status"] == "ok" else 1)

    if args.execute:
        if not args.seeds:
            parser.error("--execute requires --seeds")
        seeds = [int(s) for s in args.seeds.split(",")]
        # Belt-and-braces guard against accidentally running real seeds
        # before pre-registration is committed:
        print("WARNING: --execute mode runs the full comparison and "
              "exposes metric values. Confirm pre_registration_step1.md "
              "is committed and references this harness commit hash.",
              file=sys.stderr)
        execute_run(seeds, args.output)


if __name__ == "__main__":
    main()
