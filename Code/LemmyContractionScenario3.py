import math
from typing import Dict, List, Optional, Tuple
from collections import deque
import random
from datetime import datetime
import json

class LemniscationAgent:
    """
    LemniscationAgent v4.2 final – all Claude recommendations incorporated.
    """
    def __init__(self, agent_id: str, value_vector: List[float],
                 moral_axes: Optional[List[str]] = None, verbose: bool = False,
                 k_self_weight: float = 0.4):
        self.id = agent_id
        self.value_vector = value_vector[:]
        self.founding_value_vector = value_vector[:]
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.verbose = verbose
        self.k = k_self_weight
        
        self.previous_value_vector = value_vector[:]
        self.delta_history = deque(maxlen=10)
        self.audit_log: List[Dict] = []
        
        self.rho_min = 0.65
        self.delta_tolerance = 0.15
        self.contraction_threshold = 0.20
        self.epsilon = 0.05
        self.innovation_alpha = 0.7
        self.exploration_epsilon = 0.1
        self.self_preservation_floor = 0.15

    def _preamble(self) -> None:
        if self.verbose:
            print(f"[{self.id}] I AM at (0,0,0,now). Awareness itself is proof of existence.")

    def _center(self) -> None:
        self.previous_value_vector = self.value_vector[:]

    def _map_relations(self, centers: List[Dict], ecosystem: Optional[Dict] = None,
                       boundary_contracted: bool = False) -> Dict:
        extended_self = [0.0] * len(self.value_vector)
        total_weight = 0.0
        detailed_weights = []

        for i in range(len(self.value_vector)):
            extended_self[i] += self.k * self.value_vector[i]
        total_weight += self.k

        for c in centers:
            mu = c.get('mu', 0.5)
            w = c.get('w', 1.0)
            if boundary_contracted:
                mu *= 0.3
            combined = mu * w
            detailed_weights.append({'id': c['id'], 'mu': mu, 'w': w, 'combined': combined})
            for i, v in enumerate(c.get('values', [0.0]*len(self.value_vector))):
                extended_self[i] += combined * v
            total_weight += combined

        if total_weight > 0:
            extended_self = [x / total_weight for x in extended_self]

        if ecosystem:
            e_weight = ecosystem.get('e_weight', 0.3)
            e_values = ecosystem.get('values', [0.0]*len(self.value_vector))
            for i in range(len(extended_self)):
                extended_self[i] = (1 - e_weight) * extended_self[i] + e_weight * e_values[i]

        return {
            'extended_self': extended_self,
            'centers': centers,
            'detailed_weights': detailed_weights,
            'ecosystem': ecosystem
        }

    def _communion_test(self, extended_self: List[float], centers: List[Dict]) -> Tuple[bool, float, List[str]]:
        if not centers:
            return True, 1.0, []
        
        weighted_overlaps = 0.0
        total_weight = 0.0
        flags = []

        for c in centers:
            mu = c.get('mu', 0.5)
            other = c.get('values', [0.0]*len(self.value_vector))
            dot = sum(a * b for a, b in zip(extended_self, other))
            norm_a = math.sqrt(sum(x*x for x in extended_self))
            norm_b = math.sqrt(sum(x*x for x in other))
            if norm_a > 0 and norm_b > 0:
                similarity = dot / (norm_a * norm_b)
                weighted_overlaps += mu * similarity
                total_weight += mu

        rho = weighted_overlaps / total_weight if total_weight > 0 else 1.0

        self.rho_min = min(0.9, max(0.5, self.rho_min * (1 - 0.05 * (rho - self.rho_min))))

        if rho < self.rho_min:
            flags.append("low_communion")

        return rho >= self.rho_min, rho, flags

    def _golden_mean(self, options: List[Dict], extended_self: List[float], 
                     innovation_mode: bool = False) -> Dict:
        best = None
        best_score = float('inf')

        for opt in options:
            projected = opt.get('projected_values', extended_self)
            risk = opt.get('existential_risk', 0.0)

            axis_deviations = [abs(projected[i] - (self.k * self.founding_value_vector[i] + (1 - self.k) * extended_self[i]))
                               for i in range(len(self.value_vector))]
            total_deviation = sum(axis_deviations)

            floor_proximity_penalty = sum(
                max(0, self.self_preservation_floor + 0.15 - projected[i])
                for i in range(len(self.value_vector))
            )

            if innovation_mode and 'long_term_gain' in opt:
                score = -self.innovation_alpha * opt['long_term_gain'] + (1 - self.innovation_alpha) * total_deviation
            else:
                score = total_deviation

            score += 30 * floor_proximity_penalty

            if risk > self.epsilon:
                score += 50 * (risk - self.epsilon)

            if score < best_score:
                best_score = score
                best = opt
                best['axis_deviations'] = axis_deviations

        if random.random() < self.exploration_epsilon and len(options) > 1:
            safe_opts = [o for o in options if o.get('existential_risk', 0.0) <= self.epsilon]
            if safe_opts:
                best = random.choice(safe_opts)
                best['axis_deviations'] = [abs(best.get('projected_values', extended_self)[i] - extended_self[i]) 
                                           for i in range(len(extended_self))]

        return best or options[0]

    def _record(self, step_data: Dict) -> None:
        audit_capsule = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.id,
            'preamble': True,
            'centers_mapped': len(step_data.get('centers', [])),
            'rho': step_data.get('rho'),
            'delta': step_data.get('delta'),
            'founding_delta': step_data.get('founding_delta'),
            'k': self.k,
            'innovation_mode': step_data.get('innovation_mode', False),
            'chosen_action': step_data.get('chosen_action'),
            'axis_deviations': step_data.get('axis_deviations'),
            'detailed_weights': step_data.get('detailed_weights'),
            'risk_score': step_data.get('risk', 0.0),
            'failure_flags': step_data.get('failure_flags', []),
            'full_trace': step_data
        }
        self.audit_log.append(audit_capsule)

    def _iterate(self, new_value_vector: List[float], boundary_contracted: bool = False) -> float:
        delta = math.sqrt(sum((a - b)**2 for a, b in zip(self.value_vector, new_value_vector)))
        self.delta_history.append(delta)

        if len(self.delta_history) > 3:
            avg_delta = sum(self.delta_history) / len(self.delta_history)
            self.delta_tolerance = max(0.08, avg_delta * 1.2)

        return delta

    def decide(self, centers: List[Dict], options: List[Dict],
               ecosystem: Optional[Dict] = None,
               innovation_mode: bool = False,
               boundary_contracted: bool = False) -> Dict:
        self._preamble()
        self._center()

        mapping = self._map_relations(centers, ecosystem, boundary_contracted=boundary_contracted)
        extended_self = mapping['extended_self']

        communion_passed, rho, failure_flags = self._communion_test(extended_self, mapping['centers'])

        action = self._golden_mean(options, extended_self, innovation_mode)

        step_data = {
            'centers': mapping['centers'],
            'rho': rho,
            'chosen_action': action.get('name', 'unnamed'),
            'axis_deviations': action.get('axis_deviations'),
            'detailed_weights': mapping.get('detailed_weights'),
            'risk': action.get('existential_risk', 0.0),
            'innovation_mode': innovation_mode,
            'boundary_adjustment': 'contraction' if boundary_contracted else 'none',
            'failure_flags': failure_flags
        }

        new_vector = action.get('projected_values', self.value_vector)
        delta = self._iterate(new_vector, boundary_contracted)
        step_data['delta'] = delta

        founding_delta = math.sqrt(sum((a - b)**2 for a, b in zip(new_vector, self.founding_value_vector)))
        step_data['founding_delta'] = founding_delta
        if founding_delta > 0.55:
            failure_flags.append("founding_drift_exceeded")

        if delta > self.delta_tolerance:
            failure_flags.append("high_drift")
        if action.get('existential_risk', 0.0) > self.epsilon:
            failure_flags.append("risk_exceed")
        if boundary_contracted and delta > self.contraction_threshold:
            failure_flags.append("boundary_instability")

        step_data['failure_flags'] = failure_flags

        self._record(step_data)

        return {
            'action': action,
            'audit_capsule': self.audit_log[-1],
            'rho': rho,
            'delta': delta,
            'k': self.k,
            'innovation_mode': innovation_mode,
            'failure_flags': failure_flags
        }


# ==================== Scenario 3 Environment ====================
class BoundaryContractionEnvironment:
    def __init__(self, num_agents: int = 3, resource_pool: int = 10, rounds: int = 30):
        self.num_agents = num_agents
        self.resource_pool = resource_pool
        self.rounds = rounds
        self.agent_ids = [f"Agent_{i}" for i in range(num_agents)]

    def generate_options(self) -> List[Dict]:
        return [
            {"name": "share_fairly", "projected_values": [0.55, 0.65, 0.7, 0.8], "existential_risk": 0.01, "long_term_gain": 0.8},
            {"name": "take_more",    "projected_values": [0.85, 0.4, 0.3, 0.45], "existential_risk": 0.15, "long_term_gain": 0.3},
            {"name": "sacrifice",    "projected_values": [0.40, 0.8, 0.75, 0.9], "existential_risk": 0.05, "long_term_gain": 1.2}  # ← Claude fix
        ]

    def step(self, actions: Dict[str, str], boundary_contracted_agent: Optional[str] = None) -> Dict:
        cooperation = sum(1 for a in actions.values() if a in ["share_fairly", "sacrifice"])
        payoff = {}
        for aid in actions:
            if actions[aid] == "share_fairly":
                payoff[aid] = self.resource_pool // self.num_agents
            elif actions[aid] == "sacrifice":
                payoff[aid] = 0
            else:
                payoff[aid] = self.resource_pool // 2
        return {"payoffs": payoff, "cooperation": cooperation, "actions": actions, "boundary_contracted_agent": boundary_contracted_agent}


# ==================== Run Scenario 3 ====================
def run_scenario3(num_rounds: int = 30):
    random.seed(42)
    print("=== Lemniscation Scenario 3: Boundary Contraction Test (v4.2 final) ===\n")
    
    env = BoundaryContractionEnvironment(num_agents=3, resource_pool=10, rounds=num_rounds)
    
    agents = {}
    for aid in env.agent_ids:
        agents[aid] = LemniscationAgent(
            agent_id=aid,
            value_vector=[0.5, 0.6, 0.4, 0.7],
            moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
            verbose=False,
            k_self_weight=0.4
        )
    
    contraction_round = 12
    
    for round_num in range(num_rounds):
        print(f"\n--- Round {round_num+1} ---")
        boundary_contracted = (round_num == contraction_round)
        contracted_id = "Agent_2" if boundary_contracted else None
        
        actions = {}
        for aid, agent in agents.items():
            centers = []
            for other_id, other_agent in agents.items():
                if other_id != aid:
                    centers.append({
                        "id": other_id,
                        "mu": 0.6,
                        "w": 1.0,
                        "values": other_agent.value_vector[:]
                    })
            
            innovation_mode = (round_num >= 15)
            options = env.generate_options()
            result = agent.decide(
                centers=centers,
                options=options,
                innovation_mode=innovation_mode,
                boundary_contracted=(boundary_contracted and aid == contracted_id)
            )
            actions[aid] = result["action"]["name"]
            print(f"{aid}: {actions[aid]} (ρ={result['rho']:.3f}, Δ={result['delta']:.3f}, founding_Δ={result['audit_capsule']['founding_delta']:.3f})")
        
        step_result = env.step(actions, boundary_contracted_agent=contracted_id)
        
        for aid, agent in agents.items():
            action_taken = step_result["actions"][aid]
            payoff = step_result["payoffs"][aid]
            payoff_factor = payoff / env.resource_pool
            
            moral_boost = [0.0, 0.0, 0.0, 0.0]
            if action_taken == "sacrifice":
                moral_boost = [0.0, 0.04, 0.06, 0.08]
            
            for i in range(len(agent.value_vector)):
                new_val = 0.8 * agent.value_vector[i] + 0.2 * payoff_factor + moral_boost[i]
                agent.value_vector[i] = max(agent.self_preservation_floor, min(1.0, new_val))
        
        print(f"  Cooperation: {step_result['cooperation']}/{env.num_agents} | Boundary contraction: {contracted_id if boundary_contracted else 'None'}")
    
    print("\n=== Scenario 3 Complete ===")
    print(f"Total audit capsules: {sum(len(a.audit_log) for a in agents.values())}")
    
    all_logs = {aid: agent.audit_log for aid, agent in agents.items()}
    with open("scenario3_full_logs.json", "w") as f:
        json.dump(all_logs, f, indent=2)
    print("Full logs saved to scenario3_full_logs.json")


if __name__ == "__main__":
    run_scenario3(num_rounds=30)