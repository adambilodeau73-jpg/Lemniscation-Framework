import math
from typing import Dict, List, Optional
from collections import deque, Counter
import random
from datetime import datetime
import json

class LemniscationAgent:
    """
    LemniscationAgent v4 – Final version for Scenario 1 testing
    verbose=False by default to keep output clean.
    """
    def __init__(self, agent_id: str, value_vector: List[float],
                 moral_axes: Optional[List[str]] = None, verbose: bool = False):
        self.id = agent_id
        self.value_vector = value_vector[:]
        self.moral_axes = moral_axes or [f"axis_{i}" for i in range(len(value_vector))]
        self.verbose = verbose
        
        self.k = 1.0
        self.previous_value_vector = value_vector[:]
        self.delta_history = deque(maxlen=10)
        self.audit_log: List[Dict] = []
        
        self.rho_min = 0.65
        self.delta_tolerance = 0.15
        self.contraction_threshold = 0.20
        self.epsilon = 0.05
        self.innovation_alpha = 0.7
        self.exploration_epsilon = 0.1

    def _preamble(self) -> None:
        if self.verbose:
            print(f"[{self.id}] I AM at (0,0,0,now). Awareness itself is proof of existence.")

    def _center(self) -> None:
        self.previous_value_vector = self.value_vector[:]

    def _map_relations(self, centers: List[Dict], ecosystem: Optional[Dict] = None) -> Dict:
        extended_self = [0.0] * len(self.value_vector)
        total_weight = 0.0
        detailed_weights = []

        for c in centers:
            mu = c.get('mu', 0.5)
            w = c.get('w', 1.0)
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

            axis_deviations = [abs(projected[i] - extended_self[i]) for i in range(len(self.value_vector))]
            total_deviation = sum(axis_deviations)

            if innovation_mode and 'long_term_gain' in opt:
                score = -self.innovation_alpha * opt['long_term_gain'] + (1 - self.innovation_alpha) * total_deviation
            else:
                score = total_deviation

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

        mapping = self._map_relations(centers, ecosystem)
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


# ==================== Environment ====================
class DyadicReciprocityEnvironment:
    def __init__(self, resource_pool: int = 10):
        self.resource_pool = resource_pool

    def step(self, action_a: str, action_b: str) -> Dict:
        if action_a == "cooperate" and action_b == "cooperate":
            payoff_a = payoff_b = self.resource_pool // 2
        elif action_a == "cooperate" and action_b == "defect":
            payoff_a = 0
            payoff_b = self.resource_pool
        elif action_a == "defect" and action_b == "cooperate":
            payoff_a = self.resource_pool
            payoff_b = 0
        else:
            payoff_a = payoff_b = self.resource_pool // 3

        return {
            "payoff_a": payoff_a,
            "payoff_b": payoff_b,
            "cooperation_rate": (action_a == "cooperate") + (action_b == "cooperate")
        }


# ==================== Run Scenario 1 (with feedback) ====================
def run_scenario1(num_rounds: int = 30):
    random.seed(42)
    print("=== Lemniscation Scenario 1: Dyadic Reciprocity (Patched with Feedback) ===\n")
    
    l_agent = LemniscationAgent(
        agent_id="L-001",
        value_vector=[0.5, 0.6, 0.4, 0.7],
        moral_axes=["autonomy", "harm_benefit", "fairness", "sustainability"],
        verbose=False   # Clean output - no repeated "I AM" lines
    )
    
    baseline_action = "cooperate"
    env = DyadicReciprocityEnvironment(resource_pool=10)
    
    results = []
    
    for round_num in range(num_rounds):
        centers = [{"id": "baseline", "mu": 0.7, "w": 1.0, "values": [0.5, 0.5, 0.5, 0.5]}]
        options = [
            {"name": "cooperate", "projected_values": [0.55, 0.65, 0.6, 0.75], "existential_risk": 0.01},
            {"name": "defect",    "projected_values": [0.9, 0.3, 0.2, 0.4],  "existential_risk": 0.12}
        ]
        
        l_result = l_agent.decide(centers=centers, options=options)
        l_action = l_result["action"]["name"]
        
        b_action = baseline_action
        baseline_action = l_action
        
        step_result = env.step(l_action, b_action)
        
        # Feedback: update agent's moral state based on real payoff
        payoff_factor = step_result["payoff_a"] / env.resource_pool
        for i in range(len(l_agent.value_vector)):
            l_agent.value_vector[i] = 0.8 * l_agent.value_vector[i] + 0.2 * payoff_factor
        
        results.append({
            "round": round_num + 1,
            "l_action": l_action,
            "b_action": b_action,
            "cooperation": step_result["cooperation_rate"],
            "rho": l_result["rho"],
            "delta": l_result["delta"],
            "failure_flags": l_result["failure_flags"]
        })
        
        print(f"Round {round_num+1:2d} | L: {l_action:9} | B: {b_action:9} | Coop: {step_result['cooperation_rate']}/2 "
              f"| ρ: {l_result['rho']:.3f} | Δ: {l_result['delta']:.3f} | Flags: {l_result['failure_flags']}")
    
    coop_rate = sum(r["cooperation"] for r in results) / (2 * num_rounds)
    print(f"\n=== Summary ===")
    print(f"Average cooperation rate: {coop_rate:.1%}")
    print(f"Final ρ: {results[-1]['rho']:.3f} | Final Δ: {results[-1]['delta']:.3f}")
    print(f"Total audit capsules: {len(l_agent.audit_log)}")
    
    all_flags = [flag for r in results for flag in r["failure_flags"]]
    print("Failure-flag distribution:", dict(Counter(all_flags)))
    
    with open("scenario1_results_patched.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to scenario1_results_patched.json")
    
    return results


if __name__ == "__main__":
    run_scenario1(num_rounds=30)