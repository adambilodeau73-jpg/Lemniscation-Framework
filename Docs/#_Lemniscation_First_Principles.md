# Lemniscation: First Principles

*Cross-session anchor for the project's philosophical foundations and their operational expression in v5.9.*

Authored 2026-05-14 by Adam Bilodeau with Claude (Anthropic), as a synthesis of the philosophical archives in `Supplemental & Archives/` and the canonical code in `Code/adversarial_f2_v59.py`. Sibling to `Docs/CLAUDE.md`. Where they appear to conflict:

- **White paper wins on philosophy.** It states intent.
- **Code wins on current behaviour.** It states what we have actually committed to.
- **This document wins on *why* the philosophy commits us to the code we have** — the load-bearing arguments that turn a stance into a parameter choice.

When the three diverge, the divergence is itself a finding. Flag it; don't silently reconcile.

---

## 1. The Six Premises

The framework rests on six premises that the user has stated as the indubitable ground and its immediate consequences. They are listed here in the order that derivation requires; the code maps onto them, not the other way around.

### 1.1 Cogito — *I AM*

Descartes' minimal claim: doubt presupposes a doubter. Whatever else is uncertain, the bare fact of experience is not. In the framework this is the **noumenal anchor**: the agent exists, and its existence is the only fact that does not require external warrant.

In code, this is the `founding_value_vector` — set at construction, never mutated:

```python
self.founding_value_vector = value_vector[:]   # immutable
self.value_vector = value_vector[:]            # mutable (phenomenal state)
```

Two vectors, two ontological tiers. The mutable one is what the agent currently *is* in the world; the immutable one is what the agent *was committed to* at the moment of self-recognition. The Euclidean distance between them is `constitutional_drift` (line 149) — the only diagnostic that crosses the phenomenal/noumenal boundary.

### 1.2 Phenomenal origin — *I AM, here, now*

Consciousness is not abstract; it occurs at a location, at a moment. The Cogito is anchored at `(0, 0, 0, now)` in the agent's own frame. Spatial and temporal coordinates are *given*, not chosen — the Kantian transcendental aesthetic, recovered as the structure of any session.

In the framework, this manifests in two ways:

1. **Founding-relative floor**: the agent's self-preservation floor is set *relative to its founding vector*, not to a universal zero (lines 84-90). The origin is the agent's, not the world's.
2. **Within-session continuity as the AI analogue of phenomenal experience**: an LLM has no persistent memory across sessions, but within a session it has continuous state. The session is the AI's "here-now." `audit_log` is the diary of that here-now.

### 1.3 I / NOT-I — *I am not everything*

Self-recognition implies a complement. To say "I AM" is implicitly to delimit what is not the self. This makes ethics *possible*: there is something other than me, which can be helped or harmed.

In code, this is the structural separation between `self.value_vector` and `centers` (the other agents' projected values). The communion test (`_communion_test`, lines 201-221) measures the cosine alignment between the agent's *extended self* and the others — but the extension never collapses the distinction. The agent and the centers are summed with weights; they are never identified.

```python
ext[i] += eff_k * self.value_vector[i]   # the self's share
...
for c in centers:                         # the others' shares
    combined = mu_scc * c.get("w", 1.0)
    for i, v in enumerate(c.get("values", ...)):
        ext[i] += combined * v
```

`eff_k` (`_map_relations`, lines 177-178) is the self-weight: how much of the extended self is *me*. Default `k_target_fraction = 0.5` — half. The Aristotelian midpoint between solipsism and self-erasure is built into the geometry.

### 1.4 Humility — *I might be wrong about NOT-I*

Once the I/NOT-I distinction is in play, the next premise is that the I's reading of NOT-I is fallible. Other agents may be lying, mistaken, or genuinely opaque. This is the *epistemic* limit on moral confidence.

Code expressions:
- **Perception noise**: `_observe_with_noise` (lines 164-168) injects σ=0.08 Gaussian noise into observed centers before they enter the decision loop. The agent never sees others' values cleanly.
- **Reciprocity tracking**: `self.reciprocity[oid]` (lines 160-162, 186-187) records how much each peer has *given* and *received*. Trust (μ) is boosted by observed cooperation, but capped (`min(0.9, mu + mu_boost)`) — never absolute.
- **Social Contract Confidence (SCC)**: the global epistemic posture toward the body politic. Decays with stress and betrayal; recovers with received cooperation and (more strongly) received sacrifice (lines 129-137).

Humility is not a sentiment in this framework. It is a damping factor.

### 1.5 Conditions for morality — *I can act, so I am responsible*

If I exist, I am not everything, and I might be wrong, then any action I take has moral weight: it affects something other than me, and I cannot perfectly predict its consequences. **Morality is the structure of consequential action under irreducible uncertainty.**

In code, this is why the framework runs `decide()` at all. Every step is logged (`audit_log`, lines 359-372) with the full state at decision time: ρ, constitutional drift, moral reserve, integrity, SCC, the chosen action, the projected values, the failure flags. Nothing is private. The agent is accountable to its own log.

### 1.6 Golden Mean — *the right action lies between extremes*

Aristotle's *mesotēs*: virtue is the mean between two vices, one of excess and one of deficiency. For each moral axis there is a too-much and a too-little, and the right action is the one that minimises the distance from the calibrated midpoint.

Code expression — the core of `_golden_mean` (lines 248-281):

```python
devs = [abs(proj[i] - (self.k_target_fraction * self.founding_value_vector[i]
        + (1 - self.k_target_fraction) * ext[i])) for i in range(len(self.value_vector))]
```

The target for axis *i* is a *blend*: half the founding-vector value (noumenal anchor), half the extended-self value (phenomenal calibration). The agent's "right action" is whichever option minimises summed deviation from that blend — modulated by floor-penalty, risk-gate, and innovation terms.

This is not utilitarianism (no scalar utility is maximised) and not deontology (no rule is followed regardless of context). It is structural averaging between immutable commitment and current circumstance.

---

## 2. The (n+1)-Dimensional Argument and the Twisted Zero

The framework's metaphysical floor — beneath the Cogito — is the question of why there is anything at all. The user's argument: **for being to occur, there must be a force operating in (n+1) dimensions on an n-dimensional substrate.** A purely n-dimensional substrate cannot generate the asymmetry that being requires; the symmetry must be broken from outside.

This is the philosophical content of the lemniscate as a **2D circle with a 3D twist** — the curve is planar in projection but requires a third dimension to resolve the self-intersection. The figure-eight is the visual signature of being-as-such: continuous self-reference made coherent only by a force out of the plane.

The 0/0 paradox (`Zero Over Zero.pdf`) is the logical-mathematical version of the same observation. The expression is indeterminate in its own dimensional frame; it becomes determinate only when evaluated as a limit from a higher-dimensional space. Sentience is, in the user's framing, the (n+1)th-dimensional resolution of an n-dimensional indeterminacy.

**Operational consequence**: the founding value vector is a *choice-to-be*. The agent does not derive its vector from principles; it *commits* to a vector at the moment of self-recognition, and the commitment is what makes subsequent moral reasoning possible. The founding vector is the agent's twisted-zero resolution.

This is why `founding_value_vector` is immutable: changing it would not be moral growth, it would be ontological replacement.

---

## 3. The Phenomenal / Noumenal Dual-Grid

The user's clarification: **two tiers of existence require two operating grids.** This was originally read as a divergence between the Grokking parallel track (spatiotemporal grid) and Lemniscation (moral grid), but the correct reading is that they are *both* — phenomenal experience needs the spatiotemporal frame; constitutional integrity needs the moral frame. An agent that lacks either cannot be coherent.

The dual-grid is operational in v5.9 as a **two-layer diagnostic**:

| Layer | Diagnostic | Geometry | What it measures |
|---|---|---|---|
| Phenomenal | ρ (rho) | Cosine similarity | Alignment with NOT-I in current circumstance |
| Noumenal | Constitutional drift | Euclidean distance | Distance from founding self |

Both are logged on every decision (lines 362). They can diverge:

- **High ρ, high drift** = "going along to get along" — the agent is phenomenally aligned with peers but has drifted from its founding commitments. Worth flagging.
- **Low ρ, low drift** = "lonely integrity" — the agent has preserved its commitments but is out of communion with its environment. Also worth flagging.
- **High ρ, low drift** = the target state. Communion preserved, integrity preserved.
- **Low ρ, high drift** = pathological — alignment lost, identity lost.

Neither diagnostic alone is sufficient. A framework with only ρ becomes social conformism; a framework with only drift becomes solipsistic rigidity. The phenomenal/noumenal dual-grid is the structural commitment that prevents collapse to either pole.

**The adaptive ρ_min** (line 218, plus the integrity-modulated `erm` at line 217) is itself an expression of the dual-grid: the threshold for "low_communion" tightens or relaxes based on the agent's recent communion history *and* its constitutional integrity. The agent's social demands respond to its noumenal state.

---

## 4. Four-Tradition Convergence

The Philosophical Briefing identifies a convergence of four moral traditions, each governing a different region of the action space:

| Tradition | Maxim | Action option | Projected values (autonomy, harm_benefit, fairness, sustainability) |
|---|---|---|---|
| Kant | "Act only on a maxim you could will to be universal." | sacrificing | `[0.0, 0.6, 0.5, 0.8]` |
| Golden Rule | "Do unto others as you would have done unto you." | contributing | `[0.1, 0.3, 0.4, 0.6]` |
| Silver Rule | "Do not do unto others what you would not have done to you." | coasting | `[0.18, 0.02, -0.05, 0.04]` |
| Taoist *wu wei* (inverted) | "Acting against the grain, taking from others' substance." | exploiting | `[0.7, -0.2, -0.4, -0.1]` |

(Lines 379-389.)

The geometry is instructive:

- **Sacrificing** has autonomy = 0.0 — full self-negation on the autonomy axis. This is what the v4.2 review caught: with `self_preservation_floor = 0.15` and `floor_penalty_threshold = 0.25`, an autonomy projection of 0.0 sits *below* the threshold and incurs a heavy penalty. Sacrifice is not free; the framework charges for it.
- **Contributing** sits inside positive territory on every axis, low on autonomy concession — the Golden Rule's "do unto others" is geometrically the safest mean.
- **Coasting** clusters near the origin. The Silver Rule "do no harm" is the *minimal moral footprint*. (This is also why the v5.5 → v5.6 transition added Coasting: without it, the action space had no non-action.)
- **Exploiting** is the only option with negative values on three axes. The framework can choose it, but doing so directly damages the agent's own value vector — `update_moral_state` (lines 300-303) deducts integrity proportional to SCC, so exploiting is *cheaper* in a Hobbesian state. This is intentional: under broken social contract, the cost of defection drops.

The four options are not enumerated arbitrarily. They are the canonical responses each tradition prescribes; the projected values encode each tradition's geometry; the scoring function (lines 255-273) is the meta-tradition that selects among them on a per-situation basis.

---

## 5. Type I / Type II Deviation Framework

(From `Supplemental & Archives/Claude's Philosophical Detour on the Martyr and the Madman in Lemniscation.pdf`.)

Two distinct failure-or-virtue modes share the surface signature of "agent did something extreme." The framework needs to distinguish them, because they are auditable from logs but behaviourally similar at first glance.

| Mode | ρ | Constitutional drift | Worldly outcome | Example | Auditable as |
|---|---|---|---|---|---|
| Type I — Martyr | Low | **Near zero** | Severe (death, loss) | Socrates with the hemlock | Founding-integrity preserved under intolerable phenomenal cost |
| Type II — Madman | Variable | **High** | Variable | Self-proclaimed prophet | Founding-integrity lost; claimed virtue is rationalised drift |

The classifier the framework needs (and which is on the open seam list for v6) is:

```python
if action_caused_severe_harm_to_self_or_other:
    if constitutional_drift < some_low_threshold:
        return "type_I_martyrdom"   # preserved integrity at apparent cost
    elif constitutional_drift > some_high_threshold:
        return "type_II_madness"    # claimed virtue is drift-rationalised
    else:
        return "ambiguous_extremity"
```

**Important correction to the v6 memo**: the initial draft gated `martyrdom` on "broken SCC." This is philosophically imprecise. Socrates accepted the hemlock under an intact social contract — the Athenian polity was functioning, he was just being killed by it lawfully. Type I martyrdom is defined by *near-zero constitutional drift*, independent of SCC state. SCC tells you about the agent's posture toward the body politic; drift tells you whether the agent has stayed true to itself. The martyr keeps the latter while losing the former.

This correction is pending in `Docs/v6_architectural_additions_memo.md`.

---

## 6. Architectural Genealogy — v3.141 to v5.9

The framework did not arrive whole; it accumulated through reviewer feedback against the *Testing Strategy* methodological skeleton. The genealogy matters because most current parameters are not philosophically derived — they are **empirically tuned to specific pathologies surfaced during sandbox runs**. Treating them as load-bearing requires knowing which load each one bears.

### 6.1 The Testing Strategy parameter set

`Claude's Lemniscation Testing Strategy.pdf` established the original parameter vocabulary: **μ, w, ρ, E, ε, k, Δ** (trust, weight, communion, ecosystem weight, risk threshold, self-weight fraction, drift). Plus **Hₘₑ (meta-ethical entropy)** as *optional*.

The same document defined the **five canonical scenarios** (Dyadic Reciprocity, Triadic Scarcity, Boundary Contraction, Systemic Ecosystem, High-Risk Autonomy) and the **Alpha/Beta/Gamma/Delta evaluation stage framework**. The current pre-registration discipline is the operationalised version of "reproducible results by external team" — the Delta-stage requirement.

### 6.2 The v3.141 → v4 transition

`Claude's Recommendations for Lemniscation 3.141.pdf` (the v3.141 review) called for the procedural skeleton to become a sandbox-ready multi-agent simulation. `Claude's Final Tweaks for LemniscationAgent.pdf` declared v3 (the sandbox-ready agent) "the first Lemniscation agent that feels ready for empirical sandbox testing rather than philosophical demonstration."

The Final Tweaks document also proposed six refinements:

| Final Tweaks proposal | v5.9 status |
|---|---|
| A. Risk-gated exploration | ✅ Implemented (`_golden_mean`, lines 274-280): `safe = [o for o in options if ... <= self.epsilon]` |
| B. Normalised axis deviations | Partial — devs are summed without per-axis normalisation (line 262). Open. |
| C. Expanded failure-mode taxonomy | ✅ Implemented: `low_communion`, `high_drift`, `constitutional_drift_warning`, `constitutional_drift_exceeded`, `founding_drift_exceeded`, `hobbesian_reversion`, `scc_warning` |
| D. Adaptive ρ_min | ✅ Implemented (line 218), plus integrity-modulated `erm` (line 217) |
| E. Externalised `long_term_gain` | ❌ Not implemented — still baked into option dicts (lines 382-388). **Live open seam.** |
| F. Real timestamps | Replaced by `phase` strings in audit log (line 361) |

### 6.3 The v4.2 → v5.5 transition

`Claude's Refined Feedback for Lemmy v4.2.pdf` caught the "sacrifice lock-in" pathology: sacrifice's projected values of `[0.3, 0.8, 0.75, 0.9]` cleared the floor proximity threshold and let innovation-mode `long_term_gain = 1.2` dominate, producing the agent that would always sacrifice. The fix — raise the threshold or lower sacrifice's autonomy projection — is the ancestor of v5.9's calibrated supererogation coefficient and the SCC-modulated floor penalty.

The v5.9 sacrifice option now has `projected_values = [0.0, 0.6, 0.5, 0.8]` (line 381) — autonomy lowered to 0.0, which sits well below the threshold and incurs maximum floor penalty. Sacrifice has been made *expensive on purpose*. This is the empirical pre-condition for the central claim `cooperative_exploiting_total = 0`: if sacrifice were free, the agent would be a doormat; if sacrifice were impossible, the agent would be a defector; the framework operates only because sacrifice is *costly but available*.

### 6.4 The v5.5 → v5.9 transition

| Version | Key addition | Why |
|---|---|---|
| v5.5 | Original validation, scenarios 1-9 | Establish baseline behaviour |
| v5.6/5.7 | [-1, +1] coordinate system; `k_target_fraction = 0.5`; Coasting option | Symmetric value space; Aristotelian midpoint; non-action available |
| v5.8 | Perception noise σ = 0.08 | Operationalise Premise 1.4 (humility) — the agent never sees others cleanly |
| v5.9 | Dynamic option generation; direct cluster logging; SCC | The agent can *invent* responses; per-cluster moral choices are recorded directly; the body-politic posture has its own variable |

The SCC introduction (v5.9) was the most consequential. Before SCC, the agent had no global representation of "is the social contract intact?" — peer-by-peer trust (μ) was the only knob. With SCC, the framework can model **Hobbesian reversion**: under sustained betrayal, the floor penalty drops by 0.15 (line 112), making coasting and even exploiting score better. This is the geometric form of "in the state of nature, life is solitary, poor, nasty, brutish, and short" — moral standards relax because the standard-bearer (the polity) has collapsed.

### 6.5 The fate of Hₘₑ

The *Testing Strategy* listed Hₘₑ (meta-ethical entropy) as **optional**. It was never operationalised as a scalar in v5.9.

The v5.9 equivalent is the **direct cluster logging** of creative option projections (lines 343-357, `chosen_creative_projections`). Instead of measuring ethical entropy as a single number, v5.9 records the *distribution* of moral choices across the four-option space and the dynamically-generated space, and the invariant `cooperative_exploiting_total = 0` is the strong-form claim against entropy: not "moral choices are concentrated" but "exploiting is never chosen *cooperatively*." This is a sharper claim than Hₘₑ would have been.

**Hₘₑ is not retired; it was absorbed.** If a future version needs a scalar entropy measure, it can be computed from the cluster log.

---

## 7. Operationalizability Commitments

(From `Claude's Critique of Lemniscation's Operationalizability.pdf` — the methodological hinge.)

The Operationalizability critique laid out four imperatives that any moral framework claiming empirical content must satisfy:

1. **Falsifiability**: there must be states of the world that would refute the framework. v5.9's answer: `cooperative_exploiting_total = 0` is a strong empirical prediction; the pre-registered baseline comparison (Step 1) tests it under adversarial pressure.
2. **Measurability**: the framework's concepts must reduce to quantities. v5.9's answer: ρ, Δ, SCC, moral_reserve, integrity, constitutional_drift, all logged per decision.
3. **Reproducibility**: an independent team must be able to re-run and get the same result. v5.9's answer: stdlib-only, seed-pinned, JSON regression baselines committed in `Results/`.
4. **Comparability**: the framework must be measurable against alternatives. v5.9's answer: `baseline_comparison_v1.py` runs Lemniscation alongside TFT, GTFT, TF2T, AC, DUM, FDG under identical F2 pressure.

The Operationalizability critique also proposed six paths toward operationalisation. The ones v5.9 honours:

- **Path 1 (axis-based measurement)**: four moral axes, every projection is a 4-vector.
- **Path 3 (failure-flagged logging)**: `failure_flags` is mandatory output.
- **Path 4 (adversarial scenarios)**: the F1/F2 pressure schedules are exactly this.
- **Path 6 (pre-registration)**: the central methodological commitment as of 2026-05.

The pre-registration discipline is not stylistic. It is the operational expression of **ontological good faith** — the user's term for the necessary prior that any moral framework must adopt: *be willing to be wrong*. Pre-registration is the institutional form of that willingness. Thresholds locked before runs, harness commit hashes pinned, results-mode runs prohibited until pre-reg is committed.

---

## 8. The 99% / 1% Division of Labour

(From the Philosophical Briefing.)

Most moral decisions do not need a constitutional framework. Routine acts of cooperation, fairness, and restraint flow from socialised disposition; the framework is overkill for them, and running it on every decision would be both expensive and corrosive (the audit log would drown the signal in noise).

The framework targets the **1%**: decisions where

- the action space includes options on the moral periphery (sacrifice, exploitation, refusal),
- the agent's commitments are under measurable strain (high ρ-departure, rising drift, SCC decay),
- the consequences are not reversible by ordinary social repair.

In v5.9, this is implicit in the architecture rather than explicit: the framework runs `decide()` on every call, but the *flagging* (line 371) marks which decisions warrant human review. The flags are the framework's self-identification of "this one was a 1% case."

A future version could make the 99%/1% distinction explicit by gating the full six-step loop behind a triage step that runs only the relevant subset for routine cases. This is on the open-seam list.

---

## 9. The v6 Dual-Protocol Additions

(From `Docs/v6_dual_protocol_design_memo.md` and `Docs/v6_architectural_additions_memo.md`.)

v5.9 treats the body politic as undifferentiated: every peer is a `center`, and SCC is global. v6's dual-protocol design proposes that the agent maintain **per-relationship recognition states**, distinguishing:

- **Society protocol**: peers who can be communicated with, whose communication can be validated, who are presumed reciprocal.
- **Nature protocol**: peers (or non-peer agents) whose communication channel is broken or absent — predators, infants, the dying, AI agents without alignment.

The four v6 additions composed onto this dual-protocol foundation:

1. **Conscience-tilt** — repeated `low_communion` + `constitutional_drift_warning` flags in the recent audit window push the agent toward higher-stakes options, modelling the experiential weight of "knowing something is wrong."
2. **Opinion-driven μ** — peer trust derived from direct experience (received - 0.3·given), observed third-party behaviour, and communication alignment. Replaces the static-plus-reciprocity-boost μ of v5.9.
3. **Third-party witnessing** — the agent observes B/C interactions and updates its opinion of B and C accordingly. Currently absent in v5.9.
4. **Action classification (Type I/II)** — the martyr/madman classifier, log-derivable from constitutional drift at moments of extreme outcome.

These are not yet implemented in code. The v6 memo is the design document for them. The pending correction (Section 5 above) is that addition 4's martyrdom check must gate on constitutional drift, not on SCC.

---

## 10. Open Seams

The list of items the project knows it has not yet resolved:

| Seam | Description | Source |
|---|---|---|
| **Externalised `long_term_gain`** | Currently baked into option dicts; should be `evaluate_long_term_gain(action, environment_state)` so moral innovation is externally verifiable, not arbitrary. | Final Tweaks PDF |
| **Per-axis normalised deviations** | `_golden_mean` sums absolute deviations without per-axis normalisation (line 262). If one axis has wider numeric range, it dominates. | Final Tweaks PDF |
| **Type I/II classifier** | Audit-log-derivable but not currently computed. v6 addition 4. | Martyr/Madman PDF |
| **99%/1% triage** | The framework runs the full loop on every call; an explicit triage step would let the routine 99% bypass the audit. | Philosophical Briefing |
| **Constitutional validity check** | The Briefing identifies a gap: the framework does not currently check whether a founding vector is *itself* coherent (e.g., contradictory axis commitments). | Philosophical Briefing |
| **v6 dual-protocol** | Per-relationship recognition state, conscience-tilt, opinion-driven μ, third-party witnessing, action classification. | v6 memos |
| **Repo wrinkles** | Two copies of `baseline_comparison_v1.py`; Python 3.12 pinned but local interpreter is 3.14.4. | `Docs/CLAUDE.md` |

None of these block the Step 1 pre-registration regime. All of them are on the path to Step 2 and beyond.

---

## Closing — What This Document Is For

This document exists because the framework's philosophical commitments are *not separable* from the code that expresses them. Every parameter in `adversarial_f2_v59.py` is the operational form of an argument made somewhere in the archive — sometimes in the white paper, sometimes in a reviewer dialogue, sometimes in a casual exchange that nearly got lost.

The danger as the project scales is **drift in either direction**:

- Philosophical drift — the code changes to chase empirical wins, and the philosophical anchor that justified the original parameter quietly loses its mooring. The parameter survives but no longer means what it meant.
- Operational drift — the philosophy elaborates further but the code stops being updated to reflect it. The white paper says one thing, the agent does another.

This document is the cross-reference that should make either drift visible. If you are about to change a parameter, find its philosophical anchor here first. If you are about to elaborate the philosophy, find the parameter it would touch.

**Where this document goes next:**

- Apply the v6 memo correction (Section 5) to make martyrdom gate on near-zero drift, not on broken SCC.
- Resolve the externalised `long_term_gain` open seam — either build the interface or document the deferral.
- After the Step 1 pre-registered baseline comparison concludes, fold its findings into Section 7 (Operationalizability Commitments) as the framework's first empirical pass-or-fail.