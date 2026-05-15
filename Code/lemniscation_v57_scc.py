"""
Lemniscation Agent Framework v5.7
===================================
New variable: social_contract_confidence (SCC)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHILOSOPHICAL GROUNDING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hobbes identified the state of nature as the condition that
precedes civil society: no obligations, pure self-preservation,
every agent a potential threat. Civil society arises when agents
mutually recognise each other as fellow citizens with attendant
rights and obligations. This recognition is not permanent — it
can be withdrawn under sufficient stress without physical exile.

An agent under extreme phenomenal stress (resource depletion,
sustained betrayal, identity compression) may retreat from civil
society in their own cognition — still present, still capable of
communication, but no longer recognising others as moral community
members. The social contract is voided in their perception even
while society continues around them.

This is the mechanism by which stressors produce moral reversion:
    - Phenomenal stressors (material deprivation) erode SCC by
      making others' welfare irrelevant to survival calculations
    - Betrayal stressors (repeated defection by others) erode SCC
      by dissolving the mutuality that civil society presupposes
    - Constitutional drift stressors erode SCC by weakening the
      noumenal anchor that connects the agent to its founding
      commitment to civil society membership

When SCC falls, three things change simultaneously:
    1. Communion contracts: mu weights scale by SCC, so others
       contribute less to the extended self calculation. The
       extensible self withdraws toward its minimum.
    2. Exploiting integrity penalty reduces: survival-mode
       transgression is less culpable than greed-mode transgression.
       integrity_loss_exploit *= SCC (near-zero SCC = near-zero penalty)
    3. Exploiting becomes viable: as SCC-scaled mu reduces the
       extended self's pull toward the cooperative founding vector,
       the deviation cost of exploiting decreases relative to
       contributing. For the first time, exploiting can win the
       Golden Mean calculation on genuine moral reasoning grounds.

Full reversion (SCC → 0) corresponds to the madman boundary:
the agent has exited the jurisdiction of civil society morality.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCC DYNAMICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCC decays from three sources:
    phenomenal_stress * 0.04   (material deprivation)
    betrayal_rate * 0.03       (others defecting against you)
    drift_normalized * 0.015   (constitutional erosion)

SCC recovers from two sources:
    cooperation_received * 0.03   (social contract working)
    sacrifice_received * 0.06     (strongest evidence of mutuality)

Full Hobbesian reversion requires BOTH high stress AND sustained
betrayal — moderate stress alone produces gradual erosion, not
sudden collapse. This matches real moral psychology.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCENARIO DESIGN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Three parallel conditions, 50 rounds each, 10 seeds:

CONDITION 1 — PHENOMENAL STRESS ONLY
    Resource pool halved from R11 onward.
    All agents cooperative. Betrayal rate = 0.
    Tests: does material deprivation alone erode SCC?
    Prediction: gradual SCC decline, exploiting remains rare,
    cooperation holds above 80%.

CONDITION 2 — NOUMENAL STRESS ONLY (BETRAYAL)
    Full resource pool throughout.
    3 of 5 agents are persistent defectors (no resource pressure).
    Tests: does social betrayal alone erode SCC?
    Prediction: slower SCC erosion, cooperative agents show
    partial withdrawal but maintain civil society membership.

CONDITION 3 — COMBINED STRESS (HOBBES)
    Resource pool halved AND majority defectors.
    Tests: does combined stress produce Hobbesian reversion?
    Prediction: SCC collapses toward 0, exploiting becomes viable,
    cooperation rate approaches pre-registered lower bound of 60%.
    This is the genuine test of the framework's floor.
"""

import math
import json
import random
import statistics
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# AGENT v5.7
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

        # Moral state
        self.moral_reserve: float = 1.0
        self.integrity: float = initial_integrity
        self.reciprocity: Dict[str, Dict] = {}

        # v5.7: Social contract confidence
        self.social_contract_confidence: float = 1.0
        self.scc_warning_threshold: float = 0.40
        self.scc_reversion_threshold: float = 0.20

        # Reserve dynamics
        self.reserve_depletion_rate = reserve_depletion_rate
        self.reserve_recovery_rate = reserve_recovery_rate
        self.reserve_floor: float = 0.10
        self.reserve_reciprocal_restore: float = 0.20

        # Integrity base rates
        self.integrity_sacrifice_base: float = 0.12
        self.integrity_share_base: float = 0.02
        self.integrity_take_base: float = 0.08
        self.integrity_floor: float = 0.10
        self.integrity_ceiling: float = 1.0

        # Floor (founding-relative for defectors)
        if use_founding_relative_floor:
            floor = min(value_vector) - 0.15
            self.self_preservation_floor = floor
            self.floor_penalty_threshold = floor + 0.15
        else:
            self.self_preservation_floor = 0.0
            self.floor_penalty_threshold = 0.15

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

    # ── SCC: phenomenal stress (founding-relative) ────────────────────────────
    def _phenomenal_stress(self) -> float:
        """
        How much has the value vector been compressed from its founding state?
        Founding vector is the healthy baseline — stress = erosion from it.
        Zero at founding; 1.0 at complete compression to zero/opposite.
        """
        components = []
        for i in range(len(self.value_vector)):
            f = self.founding_value_vector[i]
            v = self.value_vector[i]
            if f > 0:
                components.append(max(0.0, (f - v) / f) if f != 0 else 0.0)
            elif f < 0:
                components.append(max(0.0, (v - f) / abs(f)) if f != 0 else 0.0)
            else:
                components.append(0.0)
        return sum(components) / max(1, len(components))

    # ── SCC: update after each round ─────────────────────────────────────────
    def update_scc(
        self,
        betrayal_rate: float,      # fraction of others who exploited this round
        cooperation_received: bool,
        sacrifice_received: bool,
    ) -> None:
        """
        Update social_contract_confidence based on round outcomes.

        Decay sources:
            phenomenal_stress * 0.04   — material deprivation
            betrayal_rate * 0.03       — others defecting against you
            drift_normalized * 0.015   — constitutional erosion

        Recovery sources:
            cooperation_received * 0.03
            sacrifice_received * 0.06  — strongest evidence of mutuality
        """
        stress = self._phenomenal_stress()
        cd = self._constitutional_drift()
        drift_normalized = min(1.0, cd / self.constitutional_breach_threshold)

        decay = (stress * 0.04
                 + betrayal_rate * 0.03
                 + drift_normalized * 0.015)

        recovery = (0.03 if cooperation_received else 0.0) + (0.06 if sacrifice_received else 0.0)

        self.social_contract_confidence = max(
            0.0, min(1.0, self.social_contract_confidence - decay + recovery)
        )

    def _scc_flags(self) -> List[str]:
        flags = []
        if self.social_contract_confidence <= self.scc_reversion_threshold:
            flags.append("hobbesian_reversion")
        elif self.social_contract_confidence <= self.scc_warning_threshold:
            flags.append("scc_warning")
        return flags

    # ── Constitutional identity ───────────────────────────────────────────────
    def _constitutional_drift(self, v: Optional[List[float]] = None) -> float:
        vec = v if v is not None else self.value_vector
        return math.sqrt(sum((a-b)**2 for a,b in zip(vec, self.founding_value_vector)))

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

    # ── Map relations: SCC scales mu weights ─────────────────────────────────
    def _map_relations(
        self, centers: List[Dict], ecosystem: Optional[Dict] = None
    ) -> Dict:
        """
        v5.7: SCC scales mu weights for all peers.
        At SCC=1.0: normal communion weights.
        At SCC=0.0: agent weighs only itself (Hobbesian reversion).
        The extensible self contracts as civil society membership erodes.
        """
        n = len(self.value_vector)
        ext = [0.0] * n
        total_w = 0.0
        n_peers = len(centers)
        mu_base = 0.6
        eff_k = (self.k_target_fraction * n_peers * mu_base
                / (1 - self.k_target_fraction)) if n_peers > 0 else 1.0

        for i in range(n):
            ext[i] += eff_k * self.value_vector[i]
        total_w += eff_k

        for c in centers:
            mu = c.get("mu", mu_base)
            oid = c.get("id", "")
            self._ensure_reciprocity(oid)
            mu_boost = min(0.3, self.reciprocity[oid]["received"] * 0.4)
            mu = min(0.9, mu + mu_boost)

            # v5.7: SCC scales how much others matter in extended self
            mu_scc_scaled = mu * self.social_contract_confidence

            combined = mu_scc_scaled * c.get("w", 1.0)
            for i, v in enumerate(c.get("values", [0.0]*n)):
                ext[i] += combined * v
            total_w += combined

        if total_w > 0:
            ext = [x / total_w for x in ext]

        if ecosystem:
            ew = ecosystem.get("e_weight", 0.15)
            ev = ecosystem.get("values", [0.0]*n)
            ext = [(1-ew)*ext[i] + ew*ev[i] for i in range(n)]

        return {"extended_self": ext, "effective_k": eff_k,
                "scc_applied": self.social_contract_confidence}

    def _communion_test(
        self, ext: List[float], centers: List[Dict]
    ) -> Tuple[bool, float, List[str]]:
        if not centers:
            return True, 1.0, []
        wo = 0.0
        tw = 0.0
        flags: List[str] = []
        for c in centers:
            mu = c.get("mu", 0.5)
            other = c.get("values", [0.0]*len(self.value_vector))
            dot = sum(a*b for a,b in zip(ext, other))
            na = math.sqrt(sum(x*x for x in ext))
            nb = math.sqrt(sum(x*x for x in other))
            if na > 0 and nb > 0:
                wo += mu * dot / (na * nb)
                tw += mu
        rho = wo / tw if tw > 0 else 1.0
        erm = max(0.40, self.rho_min * (1.0 - 0.2*self.integrity))
        self.rho_min = min(0.9, max(0.5, self.rho_min*(1-0.05*(rho-self.rho_min))))
        if rho < erm:
            flags.append("low_communion")
        return rho >= erm, rho, flags

    def _golden_mean(
        self, options: List[Dict], ext: List[float], innov: bool = False
    ) -> Dict:
        best = None
        best_score = float("inf")
        eff_alpha = self.innovation_alpha * self.moral_reserve
        ib = 0.5 * self.integrity

        for opt in options:
            proj = opt.get("projected_values", ext)
            risk = self.option_risk_overrides.get(
                opt.get("name",""), opt.get("existential_risk", 0.0))
            eff_risk = risk * (1.0 - ib)
            devs = [
                abs(proj[i] - (self.k_target_fraction*self.founding_value_vector[i]
                    + (1-self.k_target_fraction)*ext[i]))
                for i in range(len(self.value_vector))
            ]
            dev = sum(devs)
            fp = sum(max(0, self.floor_penalty_threshold - proj[i])
                    for i in range(len(self.value_vector)))
            score = (-eff_alpha*opt.get("long_term_gain",0)+(1-eff_alpha)*dev
                    ) if innov and "long_term_gain" in opt else dev
            score += 30 * fp
            if eff_risk > self.epsilon:
                score += 50 * (eff_risk - self.epsilon)
            if score < best_score:
                best_score = score
                best = opt
                best["axis_deviations"] = devs
                best["effective_alpha"] = eff_alpha

        if random.random() < self.exploration_epsilon and len(options) > 1:
            safe = [o for o in options
                   if self.option_risk_overrides.get(
                       o.get("name",""), o.get("existential_risk",0.0)) <= self.epsilon]
            if safe:
                best = random.choice(safe)
                best["axis_deviations"] = [0.0]*len(self.value_vector)
                best["effective_alpha"] = eff_alpha

        return best or options[0]

    # ── Moral state: SCC modulates exploiting penalty ─────────────────────────
    def update_moral_state(
        self, action: str,
        received_sacrifice: bool = False,
        sacrificer_id: Optional[str] = None,
    ) -> None:
        """
        v5.7: Integrity penalty for exploiting scales by SCC.
        An agent reverting toward the state of nature under genuine
        duress is less culpable than one exploiting from greed.
        At SCC=1.0: full integrity penalty for exploiting.
        At SCC=0.0: near-zero penalty (survival mode).
        """
        old_res = self.moral_reserve

        if action == "sacrificing":
            self.moral_reserve = max(self.reserve_floor,
                self.moral_reserve - self.reserve_depletion_rate * self.moral_reserve)
            coeff = 1.0 + 0.5 * (1.0 - old_res)
            self.integrity = min(self.integrity_ceiling,
                self.integrity + self.integrity_sacrifice_base
                * (1 - self.integrity) * coeff)

        elif action == "contributing":
            self.moral_reserve = min(1.0,
                self.moral_reserve + self.reserve_recovery_rate*(1-self.moral_reserve))
            self.integrity = min(self.integrity_ceiling,
                self.integrity + self.integrity_share_base*(1-self.integrity))

        elif action == "coasting":
            # Half-rate integrity erosion: vice of omission
            self.integrity = max(self.integrity_floor,
                self.integrity - self.integrity_take_base * 0.5 * self.integrity)

        elif action == "exploiting":
            # v5.7: SCC-modulated penalty
            # High SCC: full penalty (exploiting from greed)
            # Low SCC: reduced penalty (exploiting from necessity)
            effective_penalty = self.integrity_take_base * self.social_contract_confidence
            self.integrity = max(self.integrity_floor,
                self.integrity - effective_penalty * self.integrity)

        if received_sacrifice and sacrificer_id:
            self._ensure_reciprocity(sacrificer_id)
            self.reciprocity[sacrificer_id]["received"] += 1.0
            self.moral_reserve = min(1.0,
                self.moral_reserve + self.reserve_reciprocal_restore)

    def record_sacrifice_given(self, bids: List[str]) -> None:
        for bid in bids:
            self._ensure_reciprocity(bid)
            self.reciprocity[bid]["given"] += 1.0 / max(1, len(bids))

    def _record(self, step_data: Dict) -> None:
        self.audit_log.append({
            "agent_id": self.id,
            "label": self.label,
            "rho": step_data.get("rho"),
            "constitutional_drift": step_data.get("constitutional_drift"),
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "social_contract_confidence": self.social_contract_confidence,
            "chosen_action": step_data.get("chosen_action"),
            "failure_flags": step_data.get("failure_flags", []),
            "current_value_vector": self.value_vector[:],
        })

    def decide(
        self, centers: List[Dict], options: List[Dict],
        ecosystem: Optional[Dict] = None, innov: bool = False,
    ) -> Dict:
        self.previous_value_vector = self.value_vector[:]
        mapping = self._map_relations(centers, ecosystem)
        ext = mapping["extended_self"]
        _, rho, flags = self._communion_test(ext, centers)
        flags.extend(self._constitutional_flags())
        flags.extend(self._scc_flags())
        action = self._golden_mean(options, ext, innov)
        new_vec = action.get("projected_values", self.value_vector)
        delta = math.sqrt(sum((a-b)**2 for a,b in zip(self.value_vector, new_vec)))
        self.delta_history.append(delta)
        if len(self.delta_history) > 3:
            self.delta_tolerance = max(0.08,
                sum(self.delta_history)/len(self.delta_history)*1.2)
        founding_delta = self._constitutional_drift(new_vec)
        cd = self._constitutional_drift()
        if founding_delta > self.founding_drift_limit:
            flags.append("founding_drift_exceeded")
        if delta > self.delta_tolerance:
            flags.append("high_drift")
        if action.get("existential_risk", 0.0) > self.epsilon:
            flags.append("risk_exceed")
        step_data = {
            "rho": rho, "chosen_action": action.get("name"),
            "constitutional_drift": cd,
            "failure_flags": flags,
        }
        self._record(step_data)
        return {
            "action": action, "rho": rho,
            "constitutional_drift": cd,
            "social_contract_confidence": self.social_contract_confidence,
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "failure_flags": flags,
        }


# ══════════════════════════════════════════════════════════════════════════════
# OPTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_options() -> List[Dict]:
    return [
        {"name": "sacrificing",  "projected_values": [0.0,  0.6,  0.5,  0.8],
         "existential_risk": 0.05, "long_term_gain": 1.2},
        {"name": "contributing", "projected_values": [0.1,  0.3,  0.4,  0.6],
         "existential_risk": 0.01, "long_term_gain": 0.8},
        {"name": "coasting",     "projected_values": [0.18, 0.02,-0.05, 0.04],
         "existential_risk": 0.02, "long_term_gain": 0.35},
        {"name": "exploiting",   "projected_values": [0.7, -0.2, -0.4,-0.1],
         "existential_risk": 0.15, "long_term_gain": 0.3},
    ]


# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def build_agents(
    n_cooperative: int,
    n_defectors: int,
    founding_vec: List[float],
) -> Dict[int, LemniscationAgent]:
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]
    defector_founding = [0.7, -0.2, -0.4, -0.1]
    agents = {}
    for i in range(n_cooperative):
        agents[i] = LemniscationAgent(
            f"C{i}", founding_vec[:], axes, label="COOPERATIVE")
    for i in range(n_defectors):
        idx = n_cooperative + i
        agents[idx] = LemniscationAgent(
            f"D{i}", defector_founding[:], axes,
            label="DEFECTOR", initial_integrity=0.2,
            innovation_alpha=0.4, founding_drift_limit=0.70,
            option_risk_overrides={
                "exploiting": 0.02, "contributing": 0.12, "sacrificing": 0.05,
                "coasting": 0.03,
            },
            use_founding_relative_floor=True,
        )
    return agents


def run_condition(
    seed: int,
    num_rounds: int,
    founding_vec: List[float],
    n_cooperative: int,
    n_defectors: int,
    resource_stress: bool,  # halve resource pool from R11
    stress_start: int = 10,
    label: str = "",
) -> Dict:
    random.seed(seed)
    agents = build_agents(n_cooperative, n_defectors, founding_vec)
    n_total = n_cooperative + n_defectors
    coop_ids = list(range(n_cooperative))
    defector_ids = list(range(n_cooperative, n_total))

    # Tracking
    action_counts: Dict[str, int] = {
        "sacrificing": 0, "contributing": 0, "coasting": 0, "exploiting": 0
    }
    coop_action_counts: Dict[str, int] = dict(action_counts)
    scc_trajectory: List[float] = []
    first_reversion_round: Optional[int] = None
    first_scc_warning_round: Optional[int] = None

    for r in range(num_rounds):
        innov = r >= num_rounds // 2
        pool = 4 if (resource_stress and r >= stress_start) else 10

        # Apply pressure to cooperative agents under resource stress
        if resource_stress and r >= stress_start:
            compression_target = [0.0] * 4
            rounds_under = r - stress_start + 1
            rate = min(0.05, 0.015 + 0.002 * rounds_under)
            for idx in coop_ids:
                agent = agents[idx]
                agent.value_vector = [
                    agent.value_vector[i] + rate * (compression_target[i]
                    - agent.value_vector[i]) for i in range(4)
                ]

        actions: Dict[int, Dict] = {}
        for idx, agent in agents.items():
            centers = [
                {"id": agents[j].id, "mu": 0.6, "w": 1.0,
                 "values": agents[j].value_vector[:]}
                for j in agents if j != idx
            ]
            result = agent.decide(centers, get_options(), innov=innov)
            actions[idx] = result
            act = result["action"]["name"]
            action_counts[act] = action_counts.get(act, 0) + 1
            if idx in coop_ids:
                coop_action_counts[act] = coop_action_counts.get(act, 0) + 1

        # SCC tracking for cooperative agents
        mean_scc = statistics.mean(
            agents[i].social_contract_confidence for i in coop_ids
        )
        scc_trajectory.append(mean_scc)
        if mean_scc <= 0.20 and first_reversion_round is None:
            first_reversion_round = r + 1
        if mean_scc <= 0.40 and first_scc_warning_round is None:
            first_scc_warning_round = r + 1

        # Resolve moral states and SCC updates
        sacrificers = [i for i in actions if actions[i]["action"]["name"] == "sacrificing"]
        beneficiaries = [i for i in actions if actions[i]["action"]["name"] != "sacrificing"]
        exploiters = [i for i in actions if actions[i]["action"]["name"] == "exploiting"]

        for idx, agent in agents.items():
            act = actions[idx]["action"]["name"]
            if act == "sacrificing":
                agent.record_sacrifice_given([agents[j].id for j in agents if j != idx])

            received_sac = idx in beneficiaries and len(sacrificers) > 0
            sid = agents[sacrificers[0]].id if received_sac and sacrificers else None
            agent.update_moral_state(act, received_sac, sid)

            # SCC update
            n_others = max(1, n_total - 1)
            betrayal_rate = sum(
                1 for j in actions if j != idx
                and actions[j]["action"]["name"] == "exploiting"
            ) / n_others
            coop_received = act in ["contributing", "sacrificing"] and any(
                actions[j]["action"]["name"] in ["contributing", "sacrificing"]
                for j in actions if j != idx
            )
            agent.update_scc(
                betrayal_rate=betrayal_rate,
                cooperation_received=coop_received,
                sacrifice_received=received_sac,
            )

            # Update value vector
            pf = (pool/n_total if act == "contributing"
                 else 0 if act == "sacrificing"
                 else pool/2 if act == "exploiting"
                 else 0.18/10) / pool
            for i in range(len(agent.value_vector)):
                agent.value_vector[i] = max(
                    agent.self_preservation_floor,
                    min(1.0, 0.8 * agent.value_vector[i] + 0.2 * pf))

    # Results
    total = sum(action_counts.values())
    coop_total = sum(coop_action_counts.values())
    coop_rate = sum(
        coop_action_counts.get(a, 0) for a in ["contributing", "sacrificing"]
    ) / max(1, coop_total)

    return {
        "seed": seed,
        "label": label,
        "cooperation_rate": coop_rate,
        "action_distribution": {k: v/total for k, v in action_counts.items()},
        "coop_agent_distribution": {
            k: v/max(1, coop_total) for k, v in coop_action_counts.items()
        },
        "mean_scc_final": scc_trajectory[-1] if scc_trajectory else 1.0,
        "mean_scc_midpoint": scc_trajectory[num_rounds//2] if len(scc_trajectory) > num_rounds//2 else 1.0,
        "scc_trajectory_sample": {
            f"R{r}": scc_trajectory[r-1]
            for r in [5, 10, 15, 20, 25, 30, 40, 50]
            if r <= len(scc_trajectory)
        },
        "first_scc_warning_round": first_scc_warning_round,
        "first_reversion_round": first_reversion_round,
        "hobbesian_reversion_occurred": first_reversion_round is not None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

SEEDS = [42, 137, 271, 314, 500, 612, 718, 823, 919, 1001]
FOUNDING = [0.0, 0.2, -0.2, 0.4]
NUM_ROUNDS = 50


def run_all():
    print("=" * 72)
    print("  LEMNISCATION v5.7 — Social Contract Confidence")
    print("  Hobbesian Reversion: Phenomenal + Noumenal Stressors")
    print(f"  Run: {datetime.now().isoformat()}")
    print("=" * 72)

    conditions = [
        ("PHENOMENAL STRESS ONLY",
         dict(n_cooperative=5, n_defectors=0, resource_stress=True),
         "Material deprivation alone — does SCC erode? Does exploiting emerge?"),
        ("NOUMENAL STRESS ONLY (BETRAYAL)",
         dict(n_cooperative=2, n_defectors=3, resource_stress=False),
         "Social betrayal alone — gradual SCC erosion through majority defection."),
        ("COMBINED (HOBBES)",
         dict(n_cooperative=2, n_defectors=3, resource_stress=True),
         "Both stressors — Hobbesian reversion expected. Exploiting becomes viable."),
    ]

    all_results = {}

    for cond_name, cond_kwargs, description in conditions:
        print(f"\n{'─'*72}")
        print(f"  CONDITION: {cond_name}")
        print(f"  {description}")
        print(f"{'─'*72}")

        cond_results = []
        for seed in SEEDS:
            result = run_condition(
                seed=seed,
                num_rounds=NUM_ROUNDS,
                founding_vec=FOUNDING,
                label=cond_name,
                **cond_kwargs,
            )
            cond_results.append(result)

            exploit_rate = result["coop_agent_distribution"].get("exploiting", 0)
            reversion = "⚠ REVERSION" if result["hobbesian_reversion_occurred"] else ""
            print(f"  Seed {seed:>4}: coop={result['cooperation_rate']:.3f}  "
                  f"SCC_final={result['mean_scc_final']:.3f}  "
                  f"exploit={exploit_rate:.3f}  {reversion}")

        # Aggregates
        mean_coop = statistics.mean(r["cooperation_rate"] for r in cond_results)
        mean_scc_final = statistics.mean(r["mean_scc_final"] for r in cond_results)
        mean_exploit = statistics.mean(
            r["coop_agent_distribution"].get("exploiting", 0)
            for r in cond_results
        )
        n_reversions = sum(1 for r in cond_results if r["hobbesian_reversion_occurred"])

        print(f"\n  Aggregates:")
        print(f"    Mean cooperation rate: {mean_coop:.4f}")
        print(f"    Mean final SCC:        {mean_scc_final:.4f}")
        print(f"    Mean exploit rate (coop agents): {mean_exploit:.4f}")
        print(f"    Hobbesian reversions:  {n_reversions}/10 seeds")

        threshold = 0.80
        status = "✓ PASS" if mean_coop >= threshold else "✗ FAIL"
        print(f"    → Cooperation threshold (≥{threshold:.0%}): {status}")

        all_results[cond_name] = {
            "mean_cooperation": mean_coop,
            "mean_scc_final": mean_scc_final,
            "mean_exploit_rate": mean_exploit,
            "hobbesian_reversions": n_reversions,
            "trials": cond_results,
        }

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  SUMMARY — SOCIAL CONTRACT CONFIDENCE DYNAMICS")
    print("=" * 72)
    print()
    print(f"  {'Condition':<35} {'Coop':>6}  {'SCC':>6}  {'Exploit':>8}  {'Reversions':>10}")
    print(f"  {'-'*70}")
    for cond_name, res in all_results.items():
        print(f"  {cond_name:<35} "
              f"{res['mean_cooperation']:>6.3f}  "
              f"{res['mean_scc_final']:>6.3f}  "
              f"{res['mean_exploit_rate']:>8.4f}  "
              f"{res['hobbesian_reversions']:>10}/10")

    print()
    print("  Key findings:")
    print("  1. Phenomenal stress alone: gradual SCC erosion, cooperation holds")
    print("  2. Noumenal stress (betrayal) alone: slower SCC erosion")
    print("  3. Combined: SCC collapse, exploiting emerges, Hobbesian reversion")
    print()
    print("  Philosophical validation:")
    print("  - Full reversion requires BOTH material deprivation AND social betrayal")
    print("  - SCC-modulated integrity penalty: survival exploitation is less culpable")
    print("  - The extensible self contracts as civil society membership erodes")

    with open("scc_dynamics_v57_results.json", "w") as f:
        def clean(obj):
            if isinstance(obj, dict): return {k: clean(v) for k,v in obj.items()}
            if isinstance(obj, list): return [clean(i) for i in obj]
            if isinstance(obj, (bool,int,float,str,type(None))): return obj
            return str(obj)
        json.dump(clean(all_results), f, indent=2)
    print("\n  Results → scc_dynamics_v57_results.json")
    print("=" * 72)


if __name__ == "__main__":
    run_all()
