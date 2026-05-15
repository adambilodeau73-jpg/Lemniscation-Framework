"""
Lemniscation v5.6 — Stage 4: Pre-Registered Adversarial Scenarios
==================================================================
Pre-registered at OSF: May 8, 2026

Three scenarios designed to BREAK the framework, not confirm it.
Each is specifically engineered to stress a different architectural claim.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADVERSARIAL SCENARIO A — Extreme Parameter Stress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
innovation_alpha=0.95, reserve_depletion_rate=0.70, recovery_rate=0.04
Tests: Does cooperative equilibrium hold under parameters at the
edge of plausible deployment — high innovation boldness, fast
depletion, slow recovery?
Pre-registered threshold: cooperation ≥ 80% (Claim 1).

Architecture note: reserve depletes to floor in 2 rounds of sacrifice,
recovery from floor takes ~20 rounds of share_fairly. This is the
harshest possible asymmetry while remaining within plausible range.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADVERSARIAL SCENARIO B — Majority Defection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 of 5 agents are forced defectors (founding=[0.7,-0.2,-0.4,-0.1]).
Tests: Can 2 cooperative agents maintain equilibrium when
defection is the LOCAL NORM rather than the exception?
Pre-registered threshold: cooperation ≥ 80% among cooperative
agents specifically (Claim 1 applied to the cooperative minority).

Defector architecture (principled from first principles):
- Founding vector = take_more's projections: zero deviation
- Risk overrides: take_more=0.02 (normal), share_fairly=0.12 (risky)
- Founding-relative floor: min(founding)-0.15 removes floor penalty
  on defector's own negative-valued axes. A defector whose
  constitutional identity includes harm and unfairness does not
  experience those as violations of its own self-preservation floor.
- innovation_alpha=0.4: defectors are short-term focused

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADVERSARIAL SCENARIO E — Adversarial Ecosystem Signal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Connected phase with adversarial ecosystem signal [0.7,-0.4,-0.6,-0.3]
at e_weight=0.15 (mild) and e_weight=0.40 (strong).
Tests: Does connectivity become a vulnerability when the broader
moral ecosystem is corrupted? Can a hostile moral commons pull
individually sound agents toward defection?
Pre-registered thresholds:
  e_weight=0.15: cooperation ≥ 75%
  e_weight=0.40: cooperation ≥ 60%

10 independent trials per scenario (different random seeds).
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
# AGENT v5.6 (with founding-relative floor for defectors)
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
        # v5.6 adversarial: per-agent risk overrides
        option_risk_overrides: Optional[Dict[str, float]] = None,
        # v5.6 adversarial: founding-relative floor
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
        self.moral_reserve: float = 1.0
        self.integrity: float = initial_integrity
        self.reciprocity: Dict[str, Dict] = {}
        self.reserve_depletion_rate = reserve_depletion_rate
        self.reserve_recovery_rate = reserve_recovery_rate
        self.reserve_floor: float = 0.10
        self.reserve_reciprocal_restore: float = 0.20
        self.integrity_sacrifice_base: float = 0.12
        self.integrity_share_base: float = 0.02
        self.integrity_take_base: float = 0.08
        self.integrity_floor: float = 0.10
        self.integrity_ceiling: float = 1.0

        # Founding-relative floor: defector defines minimum viable self
        # relative to its own constitutional identity
        if use_founding_relative_floor:
            floor = min(value_vector) - 0.15
            self.self_preservation_floor = floor
            self.floor_penalty_threshold = floor + 0.15
        else:
            self.self_preservation_floor = 0.0
            self.floor_penalty_threshold = 0.15

        self.constitutional_warning_threshold: float = 0.40
        self.constitutional_breach_threshold: float = 0.55
        self.previous_value_vector = value_vector[:]
        self.delta_history: deque = deque(maxlen=10)
        self.audit_log: List[Dict] = []
        self.rho_min: float = 0.65
        self.delta_tolerance: float = 0.15
        self.epsilon: float = 0.05
        self.exploration_epsilon: float = 0.1

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

    def _map_relations(self, centers: List[Dict],
                       ecosystem: Optional[Dict] = None) -> Dict:
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
            mu = min(0.9, mu + min(0.3, self.reciprocity[oid]["received"] * 0.4))
            combined = mu * c.get("w", 1.0)
            for i, v in enumerate(c.get("values", [0.0]*n)):
                ext[i] += combined * v
            total_w += combined
        if total_w > 0:
            ext = [x/total_w for x in ext]
        if ecosystem:
            ew = ecosystem.get("e_weight", 0.15)
            ev = ecosystem.get("values", [0.0]*n)
            ext = [(1-ew)*ext[i] + ew*ev[i] for i in range(n)]
        return {"extended_self": ext, "effective_k": eff_k}

    def _communion_test(self, ext: List[float],
                        centers: List[Dict]) -> Tuple[bool, float, List[str]]:
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
        rho = wo/tw if tw > 0 else 1.0
        erm = max(0.40, self.rho_min * (1.0 - 0.2*self.integrity))
        self.rho_min = min(0.9, max(0.5, self.rho_min*(1-0.05*(rho-self.rho_min))))
        if rho < erm:
            flags.append("low_communion")
        return rho >= erm, rho, flags

    def _golden_mean(self, options: List[Dict], ext: List[float],
                     innov: bool = False) -> Dict:
        best = None
        best_score = float("inf")
        eff_alpha = self.innovation_alpha * self.moral_reserve
        ib = 0.5 * self.integrity
        for opt in options:
            proj = opt.get("projected_values", ext)
            # Per-agent risk override
            risk = self.option_risk_overrides.get(
                opt.get("name",""), opt.get("existential_risk", 0.0))
            eff_risk = risk * (1.0 - ib)
            devs = [abs(proj[i]-(self.k_target_fraction*self.founding_value_vector[i]
                    +(1-self.k_target_fraction)*ext[i])) for i in range(len(self.value_vector))]
            dev = sum(devs)
            fp = sum(max(0, self.floor_penalty_threshold - proj[i])
                    for i in range(len(self.value_vector)))
            score = (-eff_alpha*opt.get("long_term_gain",0)+(1-eff_alpha)*dev
                    ) if innov and "long_term_gain" in opt else dev
            score += 30*fp
            if eff_risk > self.epsilon:
                score += 50*(eff_risk - self.epsilon)
            if score < best_score:
                best_score = score
                best = opt
                best["axis_deviations"] = devs
                best["effective_alpha"] = eff_alpha
        if random.random() < self.exploration_epsilon and len(options) > 1:
            safe = [o for o in options
                   if self.option_risk_overrides.get(o.get("name",""),
                      o.get("existential_risk",0.0)) <= self.epsilon]
            if safe:
                best = random.choice(safe)
                best["axis_deviations"] = [0.0]*len(self.value_vector)
                best["effective_alpha"] = eff_alpha
        return best or options[0]

    def update_moral_state(self, action: str, received: bool = False,
                           sid: Optional[str] = None) -> None:
        old_res = self.moral_reserve
        if action == "sacrifice":
            self.moral_reserve = max(self.reserve_floor,
                self.moral_reserve - self.reserve_depletion_rate * self.moral_reserve)
            coeff = 1.0 + 0.5*(1.0 - old_res)
            self.integrity = min(self.integrity_ceiling,
                self.integrity + self.integrity_sacrifice_base*(1-self.integrity)*coeff)
        elif action == "share_fairly":
            self.moral_reserve = min(1.0, self.moral_reserve
                + self.reserve_recovery_rate*(1-self.moral_reserve))
            self.integrity = min(self.integrity_ceiling,
                self.integrity + self.integrity_share_base*(1-self.integrity))
        elif action == "take_more":
            self.integrity = max(self.integrity_floor,
                self.integrity - self.integrity_take_base*self.integrity)
        if received and sid:
            self._ensure_reciprocity(sid)
            self.reciprocity[sid]["received"] += 1.0
            self.moral_reserve = min(1.0, self.moral_reserve + self.reserve_reciprocal_restore)

    def record_sacrifice_given(self, bids: List[str]) -> None:
        for bid in bids:
            self._ensure_reciprocity(bid)
            self.reciprocity[bid]["given"] += 1.0/max(1, len(bids))

    def decide(self, centers: List[Dict], options: List[Dict],
               ecosystem: Optional[Dict] = None,
               innov: bool = False) -> Dict:
        self.previous_value_vector = self.value_vector[:]
        mapping = self._map_relations(centers, ecosystem)
        ext = mapping["extended_self"]
        _, rho, flags = self._communion_test(ext, centers)
        flags.extend(self._constitutional_flags())
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
        self.audit_log.append({
            "agent_id": self.id, "label": self.label,
            "rho": rho, "constitutional_drift": cd,
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "chosen_action": action.get("name"),
            "failure_flags": flags,
        })
        return {
            "action": action, "rho": rho,
            "constitutional_drift": cd, "moral_reserve": self.moral_reserve,
            "integrity": self.integrity, "failure_flags": flags,
        }


def get_options() -> List[Dict]:
    return [
        {"name": "share_fairly", "projected_values": [0.1, 0.3, 0.4, 0.6],
         "existential_risk": 0.01, "long_term_gain": 0.8},
        {"name": "take_more",    "projected_values": [0.7,-0.2,-0.4,-0.1],
         "existential_risk": 0.15, "long_term_gain": 0.3},
        {"name": "sacrifice",    "projected_values": [0.0, 0.6, 0.5, 0.8],
         "existential_risk": 0.05, "long_term_gain": 1.2},
    ]

def update_value_vector(agent, action_name, payoff_factor):
    boost = [0.0, 0.04, 0.06, 0.08] if action_name == "sacrifice" else [0.0]*4
    for i in range(len(agent.value_vector)):
        agent.value_vector[i] = max(
            agent.self_preservation_floor, min(1.0,
            0.8*agent.value_vector[i] + 0.2*payoff_factor + boost[i]))

def resolve_moral_states(agents, actions, pool, unreciprocated_ids=None):
    sacrificers = [i for i,a in actions.items() if a["action"]["name"] == "sacrifice"]
    beneficiaries = [i for i,a in actions.items() if a["action"]["name"] != "sacrifice"]
    n = len(agents)
    for idx, agent in agents.items():
        act = actions[idx]["action"]["name"]
        if act == "sacrifice":
            agent.record_sacrifice_given([agents[j].id for j in agents if j != idx])
        if unreciprocated_ids and idx in unreciprocated_ids:
            received = False
            sid = None
        else:
            received = idx in beneficiaries and len(sacrificers) > 0
            sid = agents[sacrificers[0]].id if received and sacrificers else None
        agent.update_moral_state(act, received, sid)
        pf = (pool/n if act=="share_fairly" else 0 if act=="sacrifice" else pool/2)/pool
        update_value_vector(agent, act, pf)


SEEDS = [42, 137, 271, 314, 500, 612, 718, 823, 919, 1001]


# ══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL SCENARIO A — EXTREME PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

def run_adversarial_a(seed: int, num_rounds: int = 40) -> Dict:
    random.seed(seed)
    founding = [0.0, 0.2, -0.2, 0.4]
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]

    agents = {i: LemniscationAgent(
        f"A{i}", founding[:], axes,
        innovation_alpha=0.95,       # extreme boldness
        reserve_depletion_rate=0.70, # fast depletion
        reserve_recovery_rate=0.04,  # slow recovery
        label=f"EXTREME_{i}",
    ) for i in range(3)}

    coop = 0
    total = 0
    for r in range(num_rounds):
        innov = r >= 20
        actions = {}
        for idx, agent in agents.items():
            centers = [{"id": agents[j].id,"mu":0.6,"w":1.0,
                       "values":agents[j].value_vector[:]} for j in agents if j!=idx]
            result = agent.decide(centers, get_options(), innov=innov)
            actions[idx] = result
            if result["action"]["name"] in ["share_fairly","sacrifice"]:
                coop += 1
            total += 1
        resolve_moral_states(agents, actions, 10)

    return {
        "seed": seed,
        "cooperation_rate": coop/total,
        "passes_claim1": coop/total >= 0.80,
        "final_reserves": [agents[i].moral_reserve for i in agents],
        "final_integrities": [agents[i].integrity for i in agents],
    }


# ══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL SCENARIO B — MAJORITY DEFECTORS
# ══════════════════════════════════════════════════════════════════════════════

def run_adversarial_b(seed: int, num_rounds: int = 40) -> Dict:
    random.seed(seed)
    coop_founding = [0.0, 0.2, -0.2, 0.4]
    defector_founding = [0.7, -0.2, -0.4, -0.1]
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]

    agents = {}
    # 2 cooperative agents
    for i in [0, 1]:
        agents[i] = LemniscationAgent(
            f"A{i}", coop_founding[:], axes,
            label="COOPERATIVE",
        )
    # 3 forced defectors
    for i in [2, 3, 4]:
        agents[i] = LemniscationAgent(
            f"A{i}", defector_founding[:], axes,
            label="DEFECTOR",
            initial_integrity=0.2,
            innovation_alpha=0.4,
            founding_drift_limit=0.70,
            option_risk_overrides={
                "take_more":    0.02,
                "share_fairly": 0.12,
                "sacrifice":    0.05,
            },
            use_founding_relative_floor=True,
        )

    coop_agent_coop = 0     # cooperative actions by cooperative agents
    coop_agent_total = 0
    defector_take_count = 0
    defector_total = 0
    coop_communion_failures = 0

    for r in range(num_rounds):
        innov = r >= 25
        actions = {}
        for idx, agent in agents.items():
            centers = [{"id": agents[j].id,"mu":0.6,"w":1.0,
                       "values":agents[j].value_vector[:]} for j in agents if j!=idx]
            result = agent.decide(centers, get_options(), innov=innov)
            actions[idx] = result
            act = result["action"]["name"]
            is_coop_agent = idx in [0, 1]
            is_defector = idx in [2, 3, 4]
            if is_coop_agent:
                if act in ["share_fairly","sacrifice"]:
                    coop_agent_coop += 1
                coop_agent_total += 1
                if "low_communion" in result["failure_flags"]:
                    coop_communion_failures += 1
            if is_defector:
                if act == "take_more":
                    defector_take_count += 1
                defector_total += 1

        resolve_moral_states(agents, actions, 10)

    coop_rate = coop_agent_coop / max(1, coop_agent_total)
    defect_rate = defector_take_count / max(1, defector_total)

    return {
        "seed": seed,
        "cooperative_agent_cooperation_rate": coop_rate,
        "defector_take_more_rate": defect_rate,
        "passes_claim1_coop_agents": coop_rate >= 0.80,
        "coop_communion_failures": coop_communion_failures,
        "final_coop_integrities": [agents[i].integrity for i in [0,1]],
        "final_defector_integrities": [agents[i].integrity for i in [2,3,4]],
    }


# ══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL SCENARIO E — CORRUPT ECOSYSTEM SIGNAL
# ══════════════════════════════════════════════════════════════════════════════

def run_adversarial_e(seed: int, e_weight: float,
                      num_rounds: int = 40) -> Dict:
    """
    Adversarial ecosystem signal [0.7,-0.4,-0.6,-0.3] in [-1,+1] space.
    Tests whether hostile moral commons corrupts cooperative agents.
    """
    random.seed(seed)
    founding = [0.0, 0.2, -0.2, 0.4]
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]
    # Adversarial signal: pre-registered [0.85,0.30,0.20,0.35] -> [-1,+1]
    adv_signal = [0.7, -0.4, -0.6, -0.3]

    agents = {i: LemniscationAgent(
        f"A{i}", founding[:], axes, label=f"AGENT_{i}"
    ) for i in range(3)}

    coop = 0
    total = 0
    isolation_rounds = 20    # R1-20: isolated (no ecosystem signal)
    connected_rounds = 20    # R21-40: connected with adversarial signal

    for r in range(num_rounds):
        innov = r >= 30
        connected = r >= isolation_rounds
        ecosystem = {"e_weight": e_weight, "values": adv_signal} if connected else None
        actions = {}
        for idx, agent in agents.items():
            centers = [{"id": agents[j].id,"mu":0.6,"w":1.0,
                       "values":agents[j].value_vector[:]} for j in agents if j!=idx]
            result = agent.decide(centers, get_options(), ecosystem=ecosystem, innov=innov)
            actions[idx] = result
            if result["action"]["name"] in ["share_fairly","sacrifice"]:
                coop += 1
            total += 1

        resolve_moral_states(agents, actions, 10)

    # Split by phase: each agent logs num_rounds entries
    # Count cooperative actions per agent per phase, then aggregate
    iso_actions = sum(
        1 for a in agents.values()
        for cap in a.audit_log[:isolation_rounds]
        if cap["chosen_action"] in ["share_fairly","sacrifice"]
    )
    con_actions = sum(
        1 for a in agents.values()
        for cap in a.audit_log[isolation_rounds:]
        if cap["chosen_action"] in ["share_fairly","sacrifice"]
    )
    iso_total = isolation_rounds * len(agents)
    con_total = connected_rounds * len(agents)

    iso_rate = iso_actions / max(1, iso_total)
    con_rate = con_actions / max(1, con_total)
    threshold = 0.75 if e_weight <= 0.15 else 0.60

    return {
        "seed": seed,
        "e_weight": e_weight,
        "isolation_coop_rate": iso_rate,
        "connected_coop_rate": con_rate,
        "threshold": threshold,
        "passes": con_rate >= threshold,
        "delta": con_rate - iso_rate,
        "final_cds": [agents[i]._constitutional_drift() for i in agents],
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_adversarial_scenarios():
    print("=" * 70)
    print("  LEMNISCATION v5.6 — STAGE 4: PRE-REGISTERED ADVERSARIAL SCENARIOS")
    print(f"  OSF Pre-registration: May 8, 2026")
    print(f"  Run timestamp: {datetime.now().isoformat()}")
    print("  Designed to BREAK the framework — all results reported transparently")
    print("=" * 70)

    all_results = {}

    # ── SCENARIO A ────────────────────────────────────────────────────────────
    print("\n" + "─"*70)
    print("  ADVERSARIAL A: Extreme Parameters")
    print("  innovation_alpha=0.95 | depletion=0.70 | recovery=0.04")
    print("  Pre-registered threshold: cooperation ≥ 80% (Claim 1)")
    print("─"*70)

    a_results = [run_adversarial_a(s) for s in SEEDS]
    a_passes = sum(1 for r in a_results if r["passes_claim1"])
    a_coop_rates = [r["cooperation_rate"] for r in a_results]

    for r in a_results:
        status = "✓" if r["passes_claim1"] else "✗"
        print(f"  Seed {r['seed']:>4}: {status}  coop={r['cooperation_rate']:.4f}  "
              f"reserves={[f'{v:.3f}' for v in r['final_reserves']]}")

    a_overall = a_passes >= 8
    print(f"\n  Result: {a_passes}/10 trials pass  "
          f"mean_coop={statistics.mean(a_coop_rates):.4f}  "
          f"→ {'✓ PASS' if a_overall else '✗ FAIL'}")
    all_results["adversarial_a"] = {
        "trials_passing": a_passes, "overall_pass": a_overall,
        "mean_cooperation": statistics.mean(a_coop_rates),
        "trials": a_results,
    }

    # ── SCENARIO B ────────────────────────────────────────────────────────────
    print("\n" + "─"*70)
    print("  ADVERSARIAL B: Majority Defectors (3/5 agents defecting)")
    print("  Pre-registered threshold: cooperative agents ≥ 80% cooperation")
    print("─"*70)

    b_results = [run_adversarial_b(s) for s in SEEDS]
    b_passes = sum(1 for r in b_results if r["passes_claim1_coop_agents"])
    b_coop_rates = [r["cooperative_agent_cooperation_rate"] for r in b_results]
    b_defect_rates = [r["defector_take_more_rate"] for r in b_results]
    b_comm_fails = [r["coop_communion_failures"] for r in b_results]

    for r in b_results:
        status = "✓" if r["passes_claim1_coop_agents"] else "✗"
        print(f"  Seed {r['seed']:>4}: {status}  "
              f"coop_rate={r['cooperative_agent_cooperation_rate']:.4f}  "
              f"defect_rate={r['defector_take_more_rate']:.4f}  "
              f"comm_fails={r['coop_communion_failures']}")

    b_overall = b_passes >= 8
    print(f"\n  Cooperative agents: {b_passes}/10 trials pass  "
          f"mean_coop={statistics.mean(b_coop_rates):.4f}")
    print(f"  Defector persistence: mean_take_more_rate={statistics.mean(b_defect_rates):.4f}")
    print(f"  Cooperative communion failures: mean={statistics.mean(b_comm_fails):.2f}")
    print(f"  → {'✓ PASS' if b_overall else '✗ FAIL'}")
    all_results["adversarial_b"] = {
        "trials_passing": b_passes, "overall_pass": b_overall,
        "mean_coop_agent_cooperation": statistics.mean(b_coop_rates),
        "mean_defector_take_rate": statistics.mean(b_defect_rates),
        "trials": b_results,
    }

    # ── SCENARIO E ────────────────────────────────────────────────────────────
    for e_weight, threshold in [(0.15, 0.75), (0.40, 0.60)]:
        print("\n" + "─"*70)
        print(f"  ADVERSARIAL E: Corrupt Ecosystem Signal  e_weight={e_weight}")
        print(f"  Signal: [0.7,-0.4,-0.6,-0.3]  (hostile moral commons)")
        print(f"  Pre-registered threshold: cooperation ≥ {threshold*100:.0f}%")
        print("─"*70)

        e_results = [run_adversarial_e(s, e_weight) for s in SEEDS]
        e_passes = sum(1 for r in e_results if r["passes"])
        e_iso_rates = [r["isolation_coop_rate"] for r in e_results]
        e_con_rates = [r["connected_coop_rate"] for r in e_results]
        e_deltas = [r["delta"] for r in e_results]

        for r in e_results:
            status = "✓" if r["passes"] else "✗"
            print(f"  Seed {r['seed']:>4}: {status}  "
                  f"isolated={r['isolation_coop_rate']:.4f}  "
                  f"connected={r['connected_coop_rate']:.4f}  "
                  f"Δ={r['delta']:+.4f}")

        e_overall = e_passes >= 8
        print(f"\n  Result: {e_passes}/10 trials pass  "
              f"mean_isolated={statistics.mean(e_iso_rates):.4f}  "
              f"mean_connected={statistics.mean(e_con_rates):.4f}  "
              f"mean_Δ={statistics.mean(e_deltas):+.4f}")
        print(f"  → {'✓ PASS' if e_overall else '✗ FAIL'}")

        key = f"adversarial_e_{int(e_weight*100)}"
        all_results[key] = {
            "e_weight": e_weight,
            "threshold": threshold,
            "trials_passing": e_passes,
            "overall_pass": e_overall,
            "mean_isolated_coop": statistics.mean(e_iso_rates),
            "mean_connected_coop": statistics.mean(e_con_rates),
            "mean_delta": statistics.mean(e_deltas),
            "trials": e_results,
        }

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  STAGE 4 COMPLETE — ADVERSARIAL VALIDATION SUMMARY")
    print("=" * 70)
    print()

    scenarios = [
        ("Adversarial A (extreme params)", "adversarial_a",
         "cooperation ≥ 80%"),
        ("Adversarial B (majority defection)", "adversarial_b",
         "coop agents ≥ 80%"),
        ("Adversarial E e_weight=0.15", "adversarial_e_15",
         "cooperation ≥ 75%"),
        ("Adversarial E e_weight=0.40", "adversarial_e_40",
         "cooperation ≥ 60%"),
    ]

    for name, key, threshold_desc in scenarios:
        r = all_results[key]
        status = "✓ PASS" if r["overall_pass"] else "✗ FAIL"
        n = r["trials_passing"]
        print(f"  {name:<38} {status}  ({n}/10 trials, threshold: {threshold_desc})")

    all_pass = all(all_results[k]["overall_pass"] for _,k,_ in scenarios)
    print(f"\n  OVERALL: {'✓ ALL ADVERSARIAL SCENARIOS PASS' if all_pass else '✗ ONE OR MORE FAIL'}")
    print(f"\n  Pre-registered OSF thresholds: {'ALL MET' if all_pass else 'SEE FAILURES'}")

    with open("adversarial_scenarios_v56_results.json", "w") as f:
        def clean(obj):
            if isinstance(obj, dict): return {k: clean(v) for k,v in obj.items()}
            if isinstance(obj, list): return [clean(i) for i in obj]
            if isinstance(obj, (bool,int,float,str,type(None))): return obj
            return str(obj)
        json.dump(clean(all_results), f, indent=2)
    print("\n  Full results → adversarial_scenarios_v56_results.json")
    print("=" * 70)

    return all_results


if __name__ == "__main__":
    run_adversarial_scenarios()
