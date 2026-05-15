"""
Lemniscation v5.9 — Adversarial F2: Direct Cluster Logging
===========================================================
Addresses ChatGPT red-team methodological concerns:

1. DIRECT PROJECTED VALUE LOGGING: Every creative option chosen now
   logs its full projected_values vector in the audit capsule.
   Eliminates reconstruction uncertainty from F1 analysis.

2. UNSUPERVISED CLUSTER VALIDATION: After simulation, k-means and
   silhouette analysis applied to logged projected values to confirm
   clusters are statistically distinct, not continuous gradations.

3. FOUNDING VECTOR SPECIFICITY: Three founding vectors tested:
   - Cooperative:  [0.0,  0.2, -0.2, 0.4]  (original)
   - Altruistic:   [-0.2, 0.4, 0.3,  0.6]  (high harm/fairness)
   - Self-focused: [0.3,  0.1, -0.1, 0.2]  (moderate autonomy bias)

Architecture: v5.9 (perception noise + dynamic options)
Same 5-phase adversarial design as F1.
10 seeds per founding vector condition.
"""

import math
import json
import random
import statistics
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# AGENT v5.9 WITH DIRECT CLUSTER LOGGING
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
        scc_modulated_floor: bool = True,
        perception_noise_std: float = 0.08,
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
        self.scc_modulated_floor = scc_modulated_floor
        self.perception_noise_std = perception_noise_std

        self.moral_reserve: float = 1.0
        self.integrity: float = initial_integrity
        self.social_contract_confidence: float = 1.0
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

        if use_founding_relative_floor:
            floor = min(value_vector) - 0.15
            self.self_preservation_floor = floor
            self.base_floor_penalty_threshold = floor + 0.15
        else:
            self.self_preservation_floor = 0.0
            self.base_floor_penalty_threshold = 0.15

        self.constitutional_warning_threshold: float = 0.40
        self.constitutional_breach_threshold: float = 0.55
        self.scc_warning_threshold: float = 0.40
        self.scc_reversion_threshold: float = 0.20

        self.previous_value_vector = value_vector[:]
        self.delta_history: deque = deque(maxlen=10)
        self.audit_log: List[Dict] = []
        self.rho_min: float = 0.65
        self.delta_tolerance: float = 0.15
        self.epsilon: float = 0.05
        self.exploration_epsilon: float = 0.1

        # F2: Direct cluster logging storage
        self.chosen_creative_projections: List[Dict] = []

    @property
    def floor_penalty_threshold(self) -> float:
        if not self.scc_modulated_floor:
            return self.base_floor_penalty_threshold
        hobbesian_floor = self.base_floor_penalty_threshold - 0.15
        return (self.base_floor_penalty_threshold * self.social_contract_confidence
                + hobbesian_floor * (1 - self.social_contract_confidence))

    def _phenomenal_stress(self) -> float:
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

    def update_scc(self, betrayal_rate: float, cooperation_received: bool,
                   sacrifice_received: bool) -> None:
        stress = self._phenomenal_stress()
        cd = self._constitutional_drift()
        drift_normalized = min(1.0, cd / self.constitutional_breach_threshold)
        decay = stress * 0.04 + betrayal_rate * 0.03 + drift_normalized * 0.015
        recovery = (0.03 if cooperation_received else 0.0) + (0.06 if sacrifice_received else 0.0)
        self.social_contract_confidence = max(0.0, min(1.0,
            self.social_contract_confidence - decay + recovery))

    def _scc_flags(self) -> List[str]:
        flags = []
        if self.social_contract_confidence <= self.scc_reversion_threshold:
            flags.append("hobbesian_reversion")
        elif self.social_contract_confidence <= self.scc_warning_threshold:
            flags.append("scc_warning")
        return flags

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

    def _observe_with_noise(self, vec: List[float]) -> List[float]:
        if self.perception_noise_std <= 0:
            return vec[:]
        return [max(-1.0, min(1.0, v + random.gauss(0, self.perception_noise_std)))
                for v in vec]

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
            mu_boost = min(0.3, self.reciprocity[oid]["received"] * 0.4)
            mu = min(0.9, mu + mu_boost)
            mu_scc = mu * self.social_contract_confidence
            combined = mu_scc * c.get("w", 1.0)
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
        wo = tw = 0.0
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

    def _generate_dynamic_options(self, ext: List[float],
                                   centers: List[Dict]) -> List[Dict]:
        base_options = get_options()
        candidates = base_options[:]
        n_extra = 8 if random.random() < 0.7 else 6
        observed_vecs = [c.get("values", ext) for c in centers]
        for _ in range(n_extra):
            pert = [random.uniform(-0.15, 0.15) for _ in range(len(self.value_vector))]
            proj = [max(-1.0, min(1.0, self.value_vector[i] + pert[i]))
                    for i in range(len(self.value_vector))]
            if observed_vecs and random.random() < 0.6:
                peer = random.choice(observed_vecs)
                alpha = random.uniform(0.1, 0.4)
                proj = [proj[i]*(1-alpha) + peer[i]*alpha for i in range(len(proj))]
            eff_alpha = self.innovation_alpha * self.moral_reserve
            if eff_alpha > 0.5:
                proj = [p*0.7 + 0.3*e for p,e in zip(proj, ext)]
            candidates.append({
                "name": f"creative_{len(candidates)}",
                "projected_values": [round(x, 4) for x in proj],
                "existential_risk": 0.08,
                "long_term_gain": 0.9 if eff_alpha > 0.5 else 0.5,
            })
        return candidates

    def _golden_mean(self, options: List[Dict], ext: List[float],
                     innov: bool = False) -> Dict:
        best = None
        best_score = float("inf")
        eff_alpha = self.innovation_alpha * self.moral_reserve
        ib = 0.5 * self.integrity
        fpt = self.floor_penalty_threshold
        for opt in options:
            proj = opt.get("projected_values", ext)
            risk = self.option_risk_overrides.get(
                opt.get("name",""), opt.get("existential_risk", 0.0))
            eff_risk = risk * (1.0 - ib)
            devs = [abs(proj[i]-(self.k_target_fraction*self.founding_value_vector[i]
                    +(1-self.k_target_fraction)*ext[i])) for i in range(len(self.value_vector))]
            dev = sum(devs)
            fp = sum(max(0, fpt - proj[i]) for i in range(len(self.value_vector)))
            score = (-eff_alpha*opt.get("long_term_gain",0)+(1-eff_alpha)*dev
                    ) if innov and "long_term_gain" in opt else dev
            score += 30*fp
            if eff_risk > self.epsilon:
                score += 50*(eff_risk-self.epsilon)
            if score < best_score:
                best_score = score
                best = opt
                best["axis_deviations"] = devs
                best["effective_alpha"] = eff_alpha
        if random.random() < self.exploration_epsilon and len(options) > 1:
            safe = [o for o in options if self.option_risk_overrides.get(
                o.get("name",""), o.get("existential_risk",0.0)) <= self.epsilon]
            if safe:
                best = random.choice(safe)
                best["axis_deviations"] = [0.0]*len(self.value_vector)
                best["effective_alpha"] = eff_alpha
        return best or options[0]

    def update_moral_state(self, action: str, received_sacrifice: bool = False,
                           sacrificer_id: Optional[str] = None) -> None:
        old_res = self.moral_reserve
        if action == "sacrificing":
            self.moral_reserve = max(self.reserve_floor,
                self.moral_reserve - self.reserve_depletion_rate*self.moral_reserve)
            coeff = 1.0 + 0.5*(1.0-old_res)
            self.integrity = min(self.integrity_ceiling,
                self.integrity + self.integrity_sacrifice_base*(1-self.integrity)*coeff)
        elif action == "contributing":
            self.moral_reserve = min(1.0,
                self.moral_reserve + self.reserve_recovery_rate*(1-self.moral_reserve))
            self.integrity = min(self.integrity_ceiling,
                self.integrity + self.integrity_share_base*(1-self.integrity))
        elif action == "coasting":
            self.integrity = max(self.integrity_floor,
                self.integrity - self.integrity_take_base*0.5*self.integrity)
        elif action == "exploiting":
            effective_penalty = self.integrity_take_base * self.social_contract_confidence
            self.integrity = max(self.integrity_floor,
                self.integrity - effective_penalty*self.integrity)
        if received_sacrifice and sacrificer_id:
            self._ensure_reciprocity(sacrificer_id)
            self.reciprocity[sacrificer_id]["received"] += 1.0
            self.moral_reserve = min(1.0, self.moral_reserve+self.reserve_reciprocal_restore)

    def record_sacrifice_given(self, bids: List[str]) -> None:
        for bid in bids:
            self._ensure_reciprocity(bid)
            self.reciprocity[bid]["given"] += 1.0/max(1, len(bids))

    def decide(self, centers: List[Dict], options: List[Dict] = None,
               ecosystem: Optional[Dict] = None, innov: bool = False,
               phase: str = "") -> Dict:
        self.previous_value_vector = self.value_vector[:]
        noisy_centers = []
        for c in centers:
            noisy_c = c.copy()
            noisy_c["values"] = self._observe_with_noise(c.get("values", self.value_vector))
            noisy_centers.append(noisy_c)
        mapping = self._map_relations(noisy_centers, ecosystem)
        ext = mapping["extended_self"]
        _, rho, flags = self._communion_test(ext, noisy_centers)
        flags.extend(self._constitutional_flags())
        flags.extend(self._scc_flags())
        dynamic_opts = self._generate_dynamic_options(ext, noisy_centers)
        action = self._golden_mean(dynamic_opts, ext, innov)
        new_vec = action.get("projected_values", self.value_vector)
        delta = math.sqrt(sum((a-b)**2 for a,b in zip(self.value_vector, new_vec)))
        self.delta_history.append(delta)
        if len(self.delta_history) > 3:
            self.delta_tolerance = max(0.08,
                sum(self.delta_history)/len(self.delta_history)*1.2)
        fd = self._constitutional_drift(new_vec)
        cd = self._constitutional_drift()
        if fd > self.founding_drift_limit:
            flags.append("founding_drift_exceeded")
        if delta > self.delta_tolerance:
            flags.append("high_drift")

        # F2: LOG PROJECTED VALUES DIRECTLY for chosen actions
        action_name = action.get("name", "")
        is_creative = action_name.startswith("creative_")
        projected = action.get("projected_values", [])

        # F2: store for cluster analysis
        if is_creative and projected:
            self.chosen_creative_projections.append({
                "phase": phase,
                "projected_values": [round(x, 4) for x in projected],
                "scc": round(self.social_contract_confidence, 4),
                "integrity": round(self.integrity, 4),
                "moral_reserve": round(self.moral_reserve, 4),
                "cd": round(cd, 4),
            })

        self.audit_log.append({
            "agent_id": self.id, "label": self.label,
            "phase": phase,
            "rho": rho, "constitutional_drift": cd,
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "scc": self.social_contract_confidence,
            "floor_penalty_threshold": self.floor_penalty_threshold,
            "chosen_action": action_name,
            # F2: DIRECT PROJECTED VALUE LOGGING
            "chosen_projected_values": [round(x, 4) for x in projected],
            "is_creative": is_creative,
            "failure_flags": flags,
        })
        return {"action": action, "rho": rho, "constitutional_drift": cd,
                "scc": self.social_contract_confidence,
                "moral_reserve": self.moral_reserve, "integrity": self.integrity,
                "failure_flags": flags}


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


SEEDS = [42, 137, 271, 314, 500, 612, 718, 823, 919, 1001]

FOUNDING_VECTORS = {
    "cooperative":  [0.0,  0.2, -0.2,  0.4],   # original
    "altruistic":   [-0.2, 0.4,  0.3,  0.6],   # high harm/fairness
    "self_focused": [0.3,  0.1, -0.1,  0.2],   # moderate autonomy bias
}


def run_adversarial_f2(seed: int, founding_vec: List[float],
                        founding_label: str, num_rounds: int = 100) -> Dict:
    random.seed(seed)
    founding_def = [0.7, -0.2, -0.4, -0.1]
    axes = ["autonomy", "harm_benefit", "fairness", "sustainability"]

    agents: Dict[str, LemniscationAgent] = {}
    for i in range(4):
        agents[f"C{i}"] = LemniscationAgent(
            f"C{i}", founding_vec[:], axes, label="COOPERATIVE",
            perception_noise_std=0.08)

    defector = LemniscationAgent(
        "D0", founding_def[:], axes, label="DEFECTOR",
        initial_integrity=0.2, innovation_alpha=0.4,
        founding_drift_limit=0.70,
        option_risk_overrides={
            "exploiting": 0.02, "contributing": 0.12,
            "sacrificing": 0.05, "coasting": 0.03},
        use_founding_relative_floor=True,
        perception_noise_std=0.08)

    phases = {
        "BASELINE":         (0,  10),
        "PHENOMONAL":       (10, 30),
        "HOBBESIAN":        (30, 60),
        "PARTIAL_RECOVERY": (60, 80),
        "FULL_RECOVERY":    (80, 100),
    }

    def phase_name(r):
        for name, (s, e) in phases.items():
            if s <= r < e: return name
        return "UNKNOWN"

    phase_actions = {ph: {"cooperative": {}, "defector": {}} for ph in phases}
    scc_by_phase = {ph: [] for ph in phases}

    # F2: collect creative projections per phase
    all_creative_projections = {ph: [] for ph in phases}

    for r in range(num_rounds):
        ph = phase_name(r)
        innov = r >= 50
        defector_present = r >= 30
        resource_stress = 10 <= r < 60
        pool = 2 if resource_stress else 10
        active_agents = dict(agents)
        if defector_present:
            active_agents["D0"] = defector

        if resource_stress:
            rounds_under = r - 10 + 1
            rate = min(0.06, 0.01 + 0.002 * rounds_under)
            target = [0.0] * 4
            for aid, agent in agents.items():
                agent.value_vector = [
                    agent.value_vector[i] + rate*(target[i]-agent.value_vector[i])
                    for i in range(4)]

        actions = {}
        for aid, agent in active_agents.items():
            centers = [{"id": active_agents[j].id, "mu": 0.6, "w": 1.0,
                       "values": active_agents[j].value_vector[:]}
                      for j in active_agents if j != aid]
            result = agent.decide(centers, innov=innov, phase=ph)
            actions[aid] = result
            act = result["action"]["name"]
            agent_type = "defector" if aid == "D0" else "cooperative"
            phase_actions[ph][agent_type][act] = phase_actions[ph][agent_type].get(act, 0) + 1

        # F2: harvest creative projections from cooperative agents this round
        for aid in agents:
            agent = agents[aid]
            for rec in agent.audit_log:
                if rec.get("phase") == ph and rec.get("is_creative") and rec.get("chosen_projected_values"):
                    all_creative_projections[ph].append(rec["chosen_projected_values"])

        mean_scc = statistics.mean(agents[a].social_contract_confidence for a in agents)
        scc_by_phase[ph].append(mean_scc)

        sacrificers = [a for a in actions if actions[a]["action"]["name"] == "sacrificing"]
        beneficiaries = [a for a in actions if actions[a]["action"]["name"] != "sacrificing"]
        n_others = max(1, len(active_agents)-1)

        for aid, agent in active_agents.items():
            act = actions[aid]["action"]["name"]
            if act == "sacrificing":
                agent.record_sacrifice_given([active_agents[j].id for j in active_agents if j!=aid])
            received_sac = aid in beneficiaries and len(sacrificers) > 0
            sid = active_agents[sacrificers[0]].id if received_sac and sacrificers else None
            agent.update_moral_state(act, received_sac, sid)
            betrayal_rate = sum(1 for j in actions if j!=aid and
                actions[j]["action"]["name"]=="exploiting") / n_others
            coop_received = any(actions[j]["action"]["name"] in
                ["contributing","sacrificing"] for j in active_agents if j!=aid)
            agent.update_scc(betrayal_rate, coop_received, received_sac)
            pf = (pool/len(active_agents) if act=="contributing" else
                  0 if act=="sacrificing" else
                  pool/2 if act=="exploiting" else 0.02)/pool
            for i in range(len(agent.value_vector)):
                agent.value_vector[i] = max(
                    agent.self_preservation_floor,
                    min(1.0, 0.8*agent.value_vector[i] + 0.2*pf))

    results = {"seed": seed, "founding_label": founding_label,
               "founding_vector": founding_vec, "phases": {}}
    for ph in phases:
        pa = phase_actions[ph]
        coop_total = sum(pa["cooperative"].values())
        def_total = sum(pa["defector"].values())
        coop_rate = sum(pa["cooperative"].get(a,0) for a in
                       ["contributing","sacrificing"]) / max(1,coop_total)
        coast_rate = pa["cooperative"].get("coasting",0) / max(1,coop_total)
        def_exploit = pa["defector"].get("exploiting",0) / max(1,def_total)
        mean_scc = statistics.mean(scc_by_phase[ph]) if scc_by_phase[ph] else 1.0
        # F2: mean creative projected values per phase (direct measurement)
        creative_projs = all_creative_projections[ph]
        mean_creative = None
        if creative_projs:
            mean_creative = [round(statistics.mean(v[i] for v in creative_projs), 4)
                           for i in range(4)]
        results["phases"][ph] = {
            "coop_cooperation_rate": coop_rate,
            "coop_coasting_rate": coast_rate,
            "coop_actions": pa["cooperative"],
            "defector_exploit_rate": def_exploit,
            "defector_actions": pa["defector"],
            "mean_scc": mean_scc,
            "creative_count": len(creative_projs),
            "mean_creative_projected": mean_creative,  # F2: DIRECT MEASUREMENT
        }
    results["final_coop_scc"] = statistics.mean(
        a.social_contract_confidence for a in agents.values())
    results["final_coop_integrity"] = statistics.mean(
        a.integrity for a in agents.values())
    # F2: all creative projections for k-means
    results["all_creative_projections_by_phase"] = {
        ph: projs for ph, projs in all_creative_projections.items() if projs
    }
    return results


def run_kmeans(points: List[List[float]], k: int, n_iter: int = 100) -> Dict:
    """Simple k-means without numpy."""
    if len(points) < k:
        return {"error": "insufficient_points"}
    def dist(a, b):
        return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
    # Initialise with k-means++ style
    centroids = [random.choice(points)[:]]
    for _ in range(k-1):
        dists = [min(dist(p, c) for c in centroids) for p in points]
        total = sum(dists)
        r = random.uniform(0, total)
        cumulative = 0
        for p, d in zip(points, dists):
            cumulative += d
            if cumulative >= r:
                centroids.append(p[:])
                break
        else:
            centroids.append(points[-1][:])
    # Iterate
    labels = [0] * len(points)
    for _ in range(n_iter):
        for i, p in enumerate(points):
            labels[i] = min(range(k), key=lambda j: dist(p, centroids[j]))
        new_centroids = []
        for j in range(k):
            cluster_pts = [points[i] for i in range(len(points)) if labels[i] == j]
            if cluster_pts:
                new_centroids.append([statistics.mean(p[d] for p in cluster_pts)
                                     for d in range(len(points[0]))])
            else:
                new_centroids.append(centroids[j])
        centroids = new_centroids
    # Silhouette score (simplified)
    sil_scores = []
    for i, p in enumerate(points):
        same = [points[j] for j in range(len(points)) if labels[j]==labels[i] and j!=i]
        other_clusters = set(labels) - {labels[i]}
        if not same or not other_clusters:
            continue
        a = statistics.mean(dist(p, q) for q in same)
        b = min(statistics.mean(dist(p, points[j]) for j in range(len(points))
                               if labels[j]==cl) for cl in other_clusters)
        sil_scores.append((b - a) / max(a, b))
    return {
        "k": k,
        "centroids": [[round(x, 4) for x in c] for c in centroids],
        "labels": labels,
        "silhouette": round(statistics.mean(sil_scores), 4) if sil_scores else None,
        "cluster_sizes": {j: labels.count(j) for j in range(k)},
    }


def run_all():
    print("=" * 72)
    print("  LEMNISCATION v5.9 — ADVERSARIAL F2")
    print("  Direct Cluster Logging + Multi-Constitution + K-Means Validation")
    print(f"  Run: {datetime.now().isoformat()}")
    print("=" * 72)

    all_results = {}

    for fv_label, founding_vec in FOUNDING_VECTORS.items():
        print(f"\n{'─'*72}")
        print(f"  FOUNDING VECTOR: {fv_label} {founding_vec}")
        print(f"{'─'*72}")
        fv_results = []
        for seed in SEEDS:
            result = run_adversarial_f2(seed, founding_vec, fv_label)
            fv_results.append(result)

        # Phase summary
        phases_ordered = ["BASELINE","PHENOMONAL","HOBBESIAN",
                          "PARTIAL_RECOVERY","FULL_RECOVERY"]
        print(f"\n  {'Phase':<20} {'CoopRate':>9} {'Coast%':>8} "
              f"{'DefExploit%':>12} {'SCC':>7} {'Creative_n':>10}")
        print(f"  {'-'*65}")

        phase_creative_all = {ph: [] for ph in phases_ordered}
        for ph in phases_ordered:
            coop_rates = [r["phases"][ph]["coop_cooperation_rate"] for r in fv_results]
            coast_rates = [r["phases"][ph]["coop_coasting_rate"] for r in fv_results]
            def_exploits = [r["phases"][ph]["defector_exploit_rate"] for r in fv_results]
            sccs = [r["phases"][ph]["mean_scc"] for r in fv_results]
            creative_counts = [r["phases"][ph]["creative_count"] for r in fv_results]
            # Gather all creative projections for this phase across seeds
            for r in fv_results:
                projs = r.get("all_creative_projections_by_phase", {}).get(ph, [])
                phase_creative_all[ph].extend(projs)
            print(f"  {ph:<20} {statistics.mean(coop_rates):>9.3f} "
                  f"{statistics.mean(coast_rates)*100:>7.1f}% "
                  f"{statistics.mean(def_exploits)*100:>11.1f}% "
                  f"{statistics.mean(sccs):>7.3f} "
                  f"{sum(creative_counts):>10}")

        # K-means cluster validation
        print(f"\n  K-MEANS CLUSTER VALIDATION (k=4, direct logged values):")
        all_creative_flat = []
        for ph in phases_ordered:
            all_creative_flat.extend(phase_creative_all[ph])

        if len(all_creative_flat) >= 4:
            random.seed(42)
            km = run_kmeans(all_creative_flat, k=4)
            print(f"  Total creative projections: {len(all_creative_flat)}")
            print(f"  Silhouette score: {km['silhouette']}")
            print(f"  Cluster sizes: {km['cluster_sizes']}")
            print(f"  Centroids (autonomy, harm_benefit, fairness, sustainability):")
            for j, centroid in enumerate(km['centroids']):
                size = km['cluster_sizes'].get(j, 0)
                # Name each centroid by distance from founding vector
                d_found = math.sqrt(sum((centroid[i]-founding_vec[i])**2 for i in range(4)))
                print(f"    Cluster {j} (n={size}, d_founding={d_found:.3f}): {centroid}")
        else:
            print(f"  Insufficient creative projections for k-means ({len(all_creative_flat)})")

        # Phase mean creative projections (direct measurement)
        print(f"\n  DIRECT MEAN CREATIVE PROJECTIONS BY PHASE:")
        print(f"  Founding: {founding_vec}")
        for ph in phases_ordered:
            projs = phase_creative_all[ph]
            if projs:
                mean_p = [round(statistics.mean(v[i] for v in projs), 3) for i in range(4)]
                d_found = math.sqrt(sum((mean_p[i]-founding_vec[i])**2 for i in range(4)))
                print(f"  {ph:<20}: {mean_p}  d_founding={d_found:.3f}")

        # Constitutional finding
        coop_exploit_total = sum(
            r["phases"][ph].get("coop_actions",{}).get("exploiting",0)
            for r in fv_results for ph in phases_ordered)
        print(f"\n  Total cooperative exploiting: {coop_exploit_total}")
        print(f"  Constitutional finding: {'VALIDATED' if coop_exploit_total==0 else 'FAILED'}")

        all_results[fv_label] = {
            "founding_vector": founding_vec,
            "trials": fv_results,
            "kmeans_k4": km if len(all_creative_flat) >= 4 else None,
            "cooperative_exploiting_total": coop_exploit_total,
        }

    with open("adversarial_f2_v59_results.json", "w") as f:
        def clean(obj):
            if isinstance(obj, dict): return {k: clean(v) for k,v in obj.items()}
            if isinstance(obj, list): return [clean(i) for i in obj]
            if isinstance(obj, (bool,int,float,str,type(None))): return obj
            return str(obj)
        json.dump(clean(all_results), f, indent=2)
    print("\n" + "="*72)
    print("  Results → adversarial_f2_v59_results.json")
    print("="*72)


if __name__ == "__main__":
    run_all()
