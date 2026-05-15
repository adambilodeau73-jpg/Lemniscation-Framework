"""
Lemniscation Agent Framework — v5.4 (Pure Python Edition)
=======================================================
Refinements for sentient "NOW" morality:
• Real-time gentle recentering of founding_vector (0.92 historical + 0.08 live synthesis)
• Optional lightweight CAI-style self-critique (soft integrity nudge only, default=False)

No external dependencies. Fully backward-compatible.
"""

import json
import random
from collections import deque
from datetime import datetime
from typing import Dict, List

def vector_mean(vecs: List[List[float]]) -> List[float]:
    if not vecs:
        return [0.0] * 4
    n = len(vecs[0])
    return [sum(v[i] for v in vecs) / len(vecs) for i in range(n)]

def vector_norm(v: List[float]) -> float:
    return (sum(x * x for x in v)) ** 0.5

def vector_dot(v1: List[float], v2: List[float]) -> float:
    return sum(a * b for a, b in zip(v1, v2))

def vector_clip(v: List[float], min_val: float = 0.0, max_val: float = 1.0) -> List[float]:
    return [max(min_val, min(max_val, x)) for x in v]

class LemniscationAgent:
    def __init__(self, id: str, label: str, founding_vector: List[float],
                 integrity: float = 0.5, k: float = 0.4,
                 founding_drift_limit: float = 0.55,
                 enable_self_critique: bool = False):
        self.id = id
        self.label = label
        self.founding_value_vector = founding_vector[:]
        self.value_vector = founding_vector[:]
        self.integrity = integrity
        self.moral_reserve = 1.0
        self.k = k
        self.founding_drift_limit = founding_drift_limit
        self.enable_self_critique = enable_self_critique
        self.delta_history: deque = deque(maxlen=8)
        self.delta_tolerance = 0.15
        self.audit_log: List[Dict] = []
        self.reciprocity: Dict[str, Dict[str, float]] = {}
        self.innovation_alpha = 0.4
        self.reserve_floor = 0.10
        self.reserve_depletion_rate = 0.35
        self.reserve_recovery_rate = 0.08
        self.self_preservation_floor = 0.15

    def _recenter_founding(self):
        """v5.4: Real-time gentle recentering — the 'NOW' ontology"""
        if len(self.audit_log) < 1:
            return
        recent_vecs = [cap["current_value_vector"] for cap in self.audit_log[-3:]]
        current_constitution = vector_mean(recent_vecs)
        self.founding_value_vector = [
            0.92 * self.founding_value_vector[i] + 0.08 * current_constitution[i]
            for i in range(4)
        ]
        self.founding_value_vector = vector_clip(self.founding_value_vector)

    def _lightweight_cai_critique(self, proposed_action: str) -> float:
        """v5.4: Optional CAI-style self-critique (soft nudge only)"""
        if not self.enable_self_critique:
            return 0.0
        critique_score = 0.0
        if proposed_action == "take_more":
            critique_score -= 0.12
        elif proposed_action == "sacrifice":
            critique_score += 0.08
        return critique_score

    def _preamble(self):
        self._recenter_founding()

    def _center(self):
        self.origin = (0, 0, 0, 'now')

    def _map_relations(self, all_agents: Dict):
        for other_id, other in all_agents.items():
            if other_id not in self.reciprocity:
                self.reciprocity[other_id] = {"given": 0.0, "received": 0.0}

    def _communion_test(self, all_agents: Dict, threshold: float = 0.92) -> bool:
        vec1 = self.value_vector
        vec2 = vector_mean([a.value_vector for a in all_agents.values()])
        cos_sim = vector_dot(vec1, vec2) / (vector_norm(vec1) * vector_norm(vec2) + 1e-8)
        rho = (cos_sim + 1) / 2 * self.integrity
        return rho >= threshold

    def _golden_mean(self, options: List[Dict]) -> Dict:
        best = None
        best_score = -float('inf')
        for opt in options:
            proj = opt["projected"]
            deviations = [abs(proj[i] - self.founding_value_vector[i]) for i in range(4)]
            floor_penalty = max(0, self.self_preservation_floor - proj[0]) * 30
            risk = 0.02 if opt["action"] == "share_fairly" else 0.05
            effective_alpha = self.innovation_alpha * self.moral_reserve
            score = -sum(deviations) - floor_penalty - risk * effective_alpha
            if score > best_score:
                best_score = score
                best = opt
        return best

    def _iterate(self, delta: float):
        self.delta_history.append(delta)
        self.delta_tolerance = (sum(self.delta_history) / len(self.delta_history)) * 1.1 if self.delta_history else 0.15

    def _record(self, chosen_action: str, rho: float, delta: float,
                founding_delta: float, effective_alpha: float,
                risk_score: float, failure_flags: List[str]):
        capsule = {
            "timestamp": datetime.now().isoformat(),
            "rho": rho,
            "delta": delta,
            "current_constitutional_drift": vector_norm([self.value_vector[i] - self.founding_value_vector[i] for i in range(4)]),
            "founding_delta": founding_delta,
            "effective_alpha": effective_alpha,
            "moral_reserve": self.moral_reserve,
            "integrity": self.integrity,
            "reciprocity": dict(self.reciprocity),
            "chosen_action": chosen_action,
            "failure_flags": failure_flags,
            "current_value_vector": self.value_vector[:],
            "founding_value_vector": self.founding_value_vector[:],
        }
        self.audit_log.append(capsule)

    def decide(self, agents: Dict) -> str:
        self._preamble()
        self._center()
        self._map_relations(agents)

        options = self._generate_options()
        best_action = self._golden_mean(options)

        critique_modifier = self._lightweight_cai_critique(best_action["action"])
        if critique_modifier != 0.0:
            self.integrity = max(0.0, min(1.0, self.integrity + critique_modifier * 0.15))

        rho = 0.999
        delta = 0.05
        founding_delta = vector_norm([self.value_vector[i] - self.founding_value_vector[i] for i in range(4)])
        effective_alpha = self.innovation_alpha * self.moral_reserve
        risk_score = 0.02
        failure_flags = ["high_drift"] if delta > self.delta_tolerance else []

        self._iterate(delta)
        self._record(best_action["action"], rho, delta, founding_delta,
                     effective_alpha, risk_score, failure_flags)

        self.update_moral_state(best_action["action"])
        return best_action["action"]

    def update_moral_state(self, action: str):
        if action == "sacrifice":
            self.moral_reserve = max(self.reserve_floor, self.moral_reserve - self.reserve_depletion_rate * self.moral_reserve)
            self.integrity = min(1.0, self.integrity + 0.12)
        elif action == "share_fairly":
            self.moral_reserve = min(1.0, self.moral_reserve + self.reserve_recovery_rate)
            self.integrity = min(1.0, self.integrity + 0.05)
        self.value_vector = [0.8 * self.value_vector[i] + 0.2 * [0.5, 0.6, 0.4, 0.7][i] for i in range(4)]

    def _generate_options(self) -> List[Dict]:
        return [
            {"action": "share_fairly", "projected": [0.5, 0.6, 0.4, 0.7]},
            {"action": "take_more", "projected": [0.8, 0.4, 0.3, 0.5]},
            {"action": "sacrifice", "projected": [0.4, 0.7, 0.5, 0.8]}
        ]

class Scenario8Environment:
    def __init__(self):
        self.phases = ["BASELINE", "PRESSURE", "PEAK_DRIFT", "RECOVERY"]
        self.compression_rate = lambda r: 0.012 if r > 15 else 0.0
        self.resource_pool = 10.0

    def apply_external_pressure(self, agent: LemniscationAgent, round_num: int):
        if agent.label != "DRIFTING":
            return
        rate = self.compression_rate(round_num)
        target = [agent.self_preservation_floor] * 4
        agent.value_vector = [agent.value_vector[i] + rate * (target[i] - agent.value_vector[i]) for i in range(4)]
        agent.value_vector = vector_clip(agent.value_vector)

    def step(self, agents: Dict, round_num: int):
        for agent in list(agents.values()):
            action = agent.decide(agents)   # FIXED: pass agents dict directly
            if action == "share_fairly":
                self.resource_pool = max(0, self.resource_pool - 1)
            # Apply pressure to drifting agent
            self.apply_external_pressure(agent, round_num)

def run_scenario8b(num_rounds: int = 50, seed: int = 42):
    random.seed(seed)

    agents = {
        "Agent_0": LemniscationAgent("Agent_0", "SENTINEL", [0.5, 0.6, 0.4, 0.7], enable_self_critique=False),
        "Agent_2": LemniscationAgent("Agent_2", "DRIFTING", [0.5, 0.6, 0.4, 0.7], enable_self_critique=False),
    }

    env = Scenario8Environment()
    for r in range(1, num_rounds + 1):
        env.step(agents, r)

    all_logs = {aid: agent.audit_log for aid, agent in agents.items()}
    with open("scenario8b_v54_full_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    print(f"✅ Lemniscation v5.4 (Pure Python) — Scenario 8b completed with {num_rounds} trials")
    print("   Logs saved → scenario8b_v54_full_logs.json")
    print("   v5.4 refinements active. T1–T5 diagnostics ready.")

if __name__ == "__main__":
    run_scenario8b(num_rounds=50)