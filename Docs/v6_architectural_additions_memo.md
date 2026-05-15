# Design Memo: v6 Architectural Additions — Conscience, Opinion Formation, Witnessing, and Action Classification

**Status:** Forward-looking design memo. NOT a current architecture
specification. NOT to be implemented before Step 1 empirical results
against v5.9 are committed and interpreted. This memo extends the
v6 design space defined in `v6_dual_protocol_design_memo.md` and is
subject to the same discipline described there in Section 11.

**Document version:** 1.0
**Date drafted:** [to be filled in at commit time]
**Date committed:** [to be filled in at commit time]
**Authors:** Adam Bilodeau, with Claude (Anthropic) as advisory
contributor

**Purpose:** To preserve, in a single auditable record, four specific
architectural additions that emerged during preparation for the Step 1
baseline comparison and during a subsequent philosophical-clarification
exchange between the author and the advisory contributor. The four
additions are individually motivated by recognised tensions in the
v5.9 architecture, are collectively coherent as a v6 design cluster,
and compose cleanly with the dual-protocol architecture described in
the sister memo. This memo will be revisited after Step 1 results are
in, jointly with the dual-protocol memo, when the v6 design space is
consolidated into a v6.0 specification.

**Relationship to `v6_dual_protocol_design_memo.md`:** The dual-protocol
memo proposes a regime-recognition layer (society protocol vs.
nature protocol, governed per-relationship by communion and a
re-establishment bid mechanism). This memo proposes four additions to
the agent's *internal* architecture (conscience, opinion-formation,
witnessing, action-classification) that are largely orthogonal to the
regime layer but compose with it in defined ways (Section 6 below).
Neither memo subsumes the other. Both are sister documents in the v6
design corpus; both depend on the discipline of Section 9 below and
of the dual-protocol memo's Section 11.

---

## 1. Summary

Four architectural additions are proposed:

1. **Conscience-tilt** — a flag-triggered, temporary upward shift in
   `k_target_fraction` when the agent's two-layer diagnostic (ρ
   low-communion + constitutional drift warning) shows sustained joint
   concern. The conscience is a *tilt*, not a *veto*; it changes what
   the Golden Mean is computed toward, not whether an action is
   permitted.

2. **Opinion-driven μ** — replacement of the current reciprocity-only
   peer-weighting mechanism with a richer bidirectional opinion
   primitive. Each peer is assigned a continuous valence in `(-1, +1)`
   (protagonist to antagonist) that is updated by direct experience,
   discounted hearsay (Addition 3), and — in deployments where
   communication is implemented — stated alignment. The egalitarian
   prior (`k = 0.5`, equal initial μ) is preserved as the *opening
   posture*; the posterior shifts with evidence.

3. **Third-party witnessing** — extension of each agent's reciprocity
   ledger to include observed third-party interactions (B helped C; B
   exploited C), weighted at a substantial discount relative to direct
   experience. Witnessing provides additional input to opinion
   formation (Addition 2) and, when composed with dual-protocol,
   additional input to regime transition.

4. **Action classification** — post-hoc tagging of each cycle's chosen
   action with a derived classification (`principled_dissent`,
   `martyrdom`, or none), based on the action's position in the
   phenomenal/noumenal plane and the agent's diagnostic state at the
   time of selection. The classification is audit-log metadata only;
   it does not affect option selection. Its purpose is to make
   philosophically significant action modes visible to external and
   internal auditors without disrupting the four-quadrant action
   space.

The four additions are not independent. Opinion-driven μ presupposes
the reciprocity-ledger extension that third-party witnessing also
requires; conscience-tilt's effect on recovery dynamics is plausibly
different in an architecture with dynamic μ; action classification's
detection logic for `martyrdom` depends on the SCC-modulated floor
behaviour, which is preserved from v5.9 unchanged. The additions want
a coordinated design pass, not piecemeal patching.

---

## 2. Addition 1: Conscience-tilt

### 2.1 Motivation

The v5.9 audit log records `failure_flags` per cycle (e.g.,
`low_communion`, `constitutional_drift_warning`,
`hobbesian_reversion`, `founding_drift_exceeded`, `high_drift`), but
no flag has any in-agent behavioural consequence. Flags are write-only
from the agent's perspective; their function is external auditability
and post-hoc analysis. This is consistent with the framework's
flags-don't-veto commitment, but it leaves the architecture with no
analogue of *conscience* — no mechanism by which the agent's
recognition that it is in moral trouble shapes its subsequent action.

Conscience, philosophically, is not a veto. It is a redirection of
attention toward one's foundational commitments under conditions of
self-perceived drift. The proposal below adds exactly that, and
nothing more.

### 2.2 Mechanism

When the agent's recent audit history shows *both* sustained
`low_communion` flags and sustained `constitutional_drift_warning`
flags within a sliding window of length `K`, the agent's effective
`k_target_fraction` is temporarily shifted upward — increasing the
weight of the founding vector relative to the extended self in the
Golden Mean target computation. The tilt subsides as flags age out of
the window.

```python
def _conscience_tilt(self,
                    K: int = 10,
                    lc_threshold: int = 3,
                    dw_threshold: int = 3,
                    max_tilt: float = 0.4) -> float:
    """Return a non-negative shift to be added to k_target_fraction.
    Activates only when both diagnostics show sustained joint concern
    within the lookback window."""
    if len(self.audit_log) < K:
        return 0.0
    recent = self.audit_log[-K:]
    lc = sum("low_communion" in r["failure_flags"] for r in recent)
    dw = sum("constitutional_drift_warning" in r["failure_flags"]
             for r in recent)
    if lc < lc_threshold or dw < dw_threshold:
        return 0.0
    intensity = min(lc, dw) / K
    return min(max_tilt, intensity * 0.5)
```

Used in `_golden_mean` (or as input to it):

```python
effective_k = min(0.9, self.k_target_fraction + self._conscience_tilt())
```

### 2.3 Why both signals, not either

ρ and constitutional drift answer different questions (phenomenal
alignment with peers vs. noumenal fidelity to the founding anchor).
Either signal alone may indicate honest behaviour: principled
differentiation from a wrong group produces low ρ without drift;
exploratory adjustment under safe conditions produces drift without
loss of communion. The *conjunction* is what conscience should
respond to. The mechanism above fires only when both signals show
sustained concern within the window — the architecture treats single-
channel concern as honest variation, dual-channel concern as drift
worth correcting toward.

### 2.4 Hyperparameters and starting values

- `K = 10` — lookback window in cycles. Defensible starting value
  given that v5.9 phases are 10–30 cycles long; this means the
  conscience operates at roughly within-phase granularity.
- `lc_threshold = 3`, `dw_threshold = 3` — minimum flag counts within
  the window before conscience activates. Three out of ten is
  "noticeable but not dominant," which matches the intent.
- `max_tilt = 0.4` — maximum shift to `k_target_fraction`. With
  baseline `k = 0.5` this caps `effective_k` at `0.9`, leaving 10%
  weight on the extended self even under maximum conscience activation.
  Preserves the principle that the agent never entirely excludes its
  peers.

All four hyperparameters should be subject to a sensitivity sweep in
Step 2 validation (Section 8).

### 2.5 Empirical predictions and open questions

**Prediction 1:** Conscience-tilt should produce earlier and more
robust return to baseline cooperation rates during PARTIAL_RECOVERY
and FULL_RECOVERY phases, by reducing the tendency to remain locked
in extended-self configurations shaped by HOBBESIAN-phase peer
behaviour.

**Prediction 2:** Conscience-tilt should *not* significantly affect
baseline cooperation under non-adversarial conditions, because the
conjunction trigger requires sustained dual-flag conditions that
don't arise in BASELINE phases.

**Open question 1:** Does conscience-tilt over-anchor and slow
recovery by reducing the agent's responsiveness to genuine
post-HOBBESIAN re-cooperation by peers? The flag-window mechanism
should self-correct as flags age out, but this needs testing.

**Open question 2:** Does conscience-tilt interact pathologically with
opinion-driven μ (Addition 2)? In particular, both mechanisms can
independently reduce peer influence under stress; their composition
may produce over-isolation. This is a Step 2 sensitivity-sweep
question, not resolvable in advance.

### 2.6 Architectural significance

Conscience-tilt is the first behavioural channel by which audit flags
shape agent behaviour. This is a meaningful shift in the framework's
internal architecture: flags graduate from write-only-for-audit to
write-then-read-for-target-correction. The shift preserves
flags-don't-veto (no action is forbidden by the conscience; only the
target moves), but it does establish that the audit log is a
*two-way* artifact in v6 in a way it was not in v5.9. This change
should be called out explicitly in any v6 white paper section.

---

## 3. Addition 2: Opinion-driven μ

### 3.1 Motivation

The v5.9 architecture initialises peer weight `μ` at a uniform base
(0.6) and modifies it via a single asymmetric boost from received
reciprocity, capped at +0.3. This encodes a coherent but limited model
of relational positioning: peers can become more salient through
demonstrated cooperation, but cannot become *less* salient than the
base, and the architecture has no way to integrate evidence other than
direct reciprocity.

The egalitarian prior (`k = 0.5`, uniform initial μ) is correctly
grounded in premise 4: every point in an infinite universe is equally
a center, and the agent's opening posture toward any other being
should reflect that mathematical equality. But equal weighting is a
*prior*, not a *posterior*. As the agent accumulates experiential
evidence about each peer — directly through interaction, indirectly
through observation of that peer's interactions with others, and
(in deployments with explicit communication) through stated
alignment — the posterior should shift. The architecture should
support formation of differentiated opinions of peers, with weighting
that reflects accumulated evidence.

This addition also resolves a tension previously identified in the
framework's egalitarian commitment: the inability to prioritise the
protection of vulnerable peers (children, the unconscious, future
generations, the dead) without violating the equal-weighting
principle. The resolution is that vulnerability is an *input to
opinion-formation* — a being recognised as protagonist receives
upweighting through the same channel that downweights antagonists,
regardless of capacity to reciprocate. The framework's commitment is
to *opening with equal regard*, not to maintaining it against
evidence.

### 3.2 Mechanism

Replace the current reciprocity-only structure:

```python
# v5.9
self.reciprocity[oid] = {"given": 0.0, "received": 0.0}
```

with an extended ledger:

```python
# v6
self.reciprocity[oid] = {
    "given": 0.0,
    "received": 0.0,
    "observed_cooperate_others": 0.0,
    "observed_defect_others": 0.0,
    "communication_alignment": 0.0,   # 0 until comm primitive added
}
```

Compute opinion as a bounded scalar valence:

```python
def _peer_opinion(self, oid: str) -> float:
    """Returns opinion valence in (-1, +1).
    Negative = antagonist; positive = protagonist; near-zero = neutral."""
    r = self.reciprocity[oid]
    direct = r["received"] - 0.3 * r["given"]
    hearsay = 0.3 * (r["observed_cooperate_others"]
                     - r["observed_defect_others"])
    communication = 0.5 * r["communication_alignment"]
    return math.tanh(direct + hearsay + communication)
```

Drive μ bidirectionally from opinion, with a floor at zero (noumenal
rejection):

```python
opinion = self._peer_opinion(oid)
mu = mu_base + 0.4 * opinion           # in (mu_base - 0.4, mu_base + 0.4)
mu = max(0.0, mu)                       # noumenal rejection at strong antagonism
mu_scc = mu * self.social_contract_confidence
```

### 3.3 Asymmetries embedded in the formula

Three asymmetries are deliberate and should be documented:

- **Received counts more than given.** The `direct = received - 0.3 * given`
  formulation says: my opinion of a peer is shaped primarily by what
  they have done *toward me*, with what they have *received from me*
  serving as a much smaller corrective. This prevents an agent from
  inflating its own opinion of a peer simply by having given to them
  generously — a known failure mode of pure reciprocity accounting.

- **Hearsay is discounted by ~3×.** The `0.3` coefficient on the
  hearsay term encodes the framework's epistemic humility about
  third-party reports. Direct experience is the strong signal; what I
  observe of others' interactions is weaker, partly because my
  observation of them is itself perception-noise-mediated and partly
  because their interactions occur in contexts I do not fully
  perceive.

- **Communication is weighted between the two.** When the
  communication primitive is added (a deployment decision; see
  Section 6 of `v6_dual_protocol_design_memo.md` for the
  re-establishment bid as one form of explicit communication), stated
  alignment receives `0.5×` weight — stronger than hearsay (we have
  *reason* to take a being's self-statement seriously) but weaker than
  direct experience (statements can be cheap, behaviour is costly).

### 3.4 Noumenal absorption and rejection

When opinion approaches `+1`, the peer's μ approaches `mu_base + 0.4`,
substantially amplifying their influence on the agent's extended
self. The peer is *noumenally absorbed* — their values pull on the
agent's extended-self representation with high weight, in the
language of premise 5 they become a recognised participant in the
moral community the agent inhabits.

When opinion approaches `-1`, the `tanh` saturates, opinion
contribution to μ approaches `-0.4`, and the `max(0.0, mu)` floor
clips μ to zero. The peer is *noumenally rejected* — their values are
entirely excluded from the agent's extended-self calculation. The
agent no longer treats this being as a peer for purposes of moral
deliberation.

The clean discrete event at the rejection boundary (μ hits zero) is
philosophically and operationally important. It marks a categorical
shift in the agent's relation to the being: not a quantitative
adjustment within the moral community, but an exit from it.
Re-entry — opinion recovering toward zero or positive territory
through observed protagonist behaviour by the rejected peer — is
possible and structurally symmetric (Section 6 addresses how this
composes with the dual-protocol re-entry mechanism).

### 3.5 Hyperparameters and starting values

- Direct-experience coefficients: `received` weight 1.0, `given`
  discount 0.3. Subject to sensitivity sweep.
- Hearsay discount: 0.3 (third-party observation is ~3× weaker than
  direct experience).
- Communication weight: 0.5 (when applicable).
- μ adjustment range: ±0.4 around `mu_base` (with `mu_base = 0.6`,
  this gives μ in (0.2, 1.0) before the noumenal-rejection floor;
  after the floor, in [0.0, 1.0)).
- Rejection occurs when opinion is sufficiently negative that
  `mu_base + 0.4 * tanh(opinion) ≤ 0`, i.e., opinion ≲ `-arctanh(1.5)` ≈
  bounded by tanh saturation: in practice μ approaches but does not
  cross zero unless `mu_base` is reduced. The `max(0.0, mu)` clip is
  retained as a defensive floor.

### 3.6 Empirical predictions and open questions

**Prediction 1:** In mixed-population scenarios (cooperators and
defectors among the agent's peers), opinion-driven μ should produce
faster differentiation between peer types than v5.9's
reciprocity-only mechanism, measurable as earlier divergence in
per-peer effective weighting.

**Prediction 2:** In scenarios where vulnerable peers are present
(modelled as peers whose action distribution is constrained — e.g., a
peer that can only Contribute, never Sacrifice or Exploit), the
opinion mechanism should upweight them through accumulated
non-antagonistic direct experience, without requiring a separate
vulnerability-recognition mechanism.

**Open question 1:** Does the symmetric noumenal-rejection mechanism
produce excessive exclusion in noisy environments where occasional
defection is observed from otherwise-cooperative peers? Tuning of the
hearsay weight and the rejection threshold should resolve this, but
the appropriate values are an empirical question.

**Open question 2:** How does opinion-driven μ interact with v5.9's
SCC mechanism? Currently SCC modulates all peer weights uniformly;
under opinion-driven μ, the question is whether SCC should continue
to scale all μ uniformly or whether peer-specific opinion already
encodes the relevant per-relationship trust dynamics, making SCC
redundant at the per-peer level. Provisional position: keep SCC as
the *aggregate* trust signal (relevant to floor-penalty modulation
and other architecture-wide effects), and let opinion-driven μ
operate alongside it. Step 2 sensitivity work should test whether
this composition is well-behaved.

---

## 4. Addition 3: Third-party witnessing

### 4.1 Motivation

The v5.9 architecture restricts each agent's information about peers
to direct dyadic interactions. Agent A learns about B's cooperative
or defective tendencies only through A's own interactions with B. In
real moral communities, this is empirically false — much of what an
agent learns about other beings comes from observing those beings'
interactions with parties other than the agent itself.

The dual-protocol memo's per-relationship recognition state is
already organised to support per-relationship variation; opinion-
driven μ (Addition 2) provides a richer ledger to update. Witnessing
extends the input channel: an agent can now form opinions about peers
on the basis of *observed* interactions in which the agent itself is
not a direct participant.

### 4.2 Mechanism

At the close of each cycle, the harness exposes a list of completed
interactions (B issued action X toward C; C responded with action Y)
to each agent's perception. The agent's reciprocity ledger is updated
for every peer it observes acting:

```python
def observe_third_party(self, actor_id: str, target_id: str,
                        actor_action: str, target_action: str,
                        observation_noise_std: float = 0.16) -> None:
    """Update reciprocity ledger based on observed third-party
    interaction. Observation is noisy; the actor's action may be
    misperceived as a different action with some probability."""
    self._ensure_reciprocity(actor_id)
    perceived = self._noisy_action_perception(actor_action,
                                              observation_noise_std)
    classification = self._classify_action_for_witness(perceived,
                                                       target_action)
    if classification == "cooperate":
        self.reciprocity[actor_id]["observed_cooperate_others"] += 1.0
    elif classification == "defect":
        self.reciprocity[actor_id]["observed_defect_others"] += 1.0
```

The observed counts then feed into `_peer_opinion` (Section 3.2),
discounted by the hearsay coefficient.

### 4.3 Design choices to be settled

**Locality.** Does an agent observe *all* completed interactions on
the network each cycle, or only interactions involving peers it has
direct relationships with, or only interactions within some defined
neighbourhood? Global observation is operationally cleanest for an
initial implementation; locality should be a parameter sweep in Step 2.

**Observation noise.** Third-party observation should be noisier than
first-person observation — the agent does not have direct
experiential access to the witnessed interaction and is reading it
from external signals. Provisional default: `third_party_noise_std =
0.16`, twice the v5.9 `perception_noise_std = 0.08`. The exact
multiplier is a sensitivity question.

**Cheap talk and witness reliability.** Currently, witnessed events
are taken as factual (the actor really did issue the action observed,
modulo noise). The framework does not yet model malicious agents who
might *fabricate* witnessed events to influence other agents'
opinions. This is a real concern but is deferred to v7+; it requires
a fully-articulated theory of strategic communication that is out of
scope for v6.

### 4.4 Empirical predictions and open questions

**Prediction 1:** Under mixed-population conditions, witnessing should
produce earlier convergence of opinion than direct-experience-only
mechanisms, as agents form opinions about peers they have not yet
directly engaged with.

**Prediction 2:** Witnessing should produce more *robust* rejection
of clear antagonists, as multiple agents independently accumulate
evidence about the same antagonist's behaviour toward third parties.

**Open question 1:** Does witnessing cause cascade failures in which
a single noisy observation propagates into widespread incorrect
opinion shifts across the network? The hearsay discount (0.3) should
provide first-order protection, but pathological cases may exist.

**Open question 2:** What happens when an agent observes interactions
between two peers about whom it has strongly divergent opinions —
e.g., one believed protagonist and one believed antagonist? The
straightforward implementation treats each peer's reciprocity ledger
independently, but agent-level inference about the *relationship*
between the two peers (rather than about each individually) might be
appropriate. This is a v6.5+ question.

---

## 5. Addition 4: Action classification

### 5.1 Motivation

Two philosophically significant action modes — `principled_dissent`
and `martyrdom` — emerge organically from the v5.9 architecture under
specific stress conditions, but are not visible in the audit log as
distinct modes. The framework's empirical claim that an agent
operating from a well-formed founding vector can engage in just
resistance to immoral governance (and, in the limit, sacrifice itself
for a noumenal commitment) is supported by the SCC-modulated
floor-penalty mechanism (`floor_penalty_threshold` lowers as SCC
collapses, permitting deeper phenomenal expenditure when sustained
noumenal stress is present). But the action chosen in such conditions
appears in the audit log as an undifferentiated `creative_n` action;
there is no metadata distinguishing martyrdom-correct selections from
ordinary exploratory creative options.

The proposal is post-hoc tagging only: classify each chosen action by
its position in the phenomenal/noumenal plane and the agent's
diagnostic state at the time of selection. The classification does
not affect option selection; it is metadata for audit and analysis.

### 5.2 Mechanism

```python
def _classify_chosen_action(self, action: Dict,
                            projected: List[float],
                            current_scc: float,
                            current_drift: float) -> Optional[str]:
    """Return a classification tag for the chosen action, or None
    if the action does not match a recognised mode."""
    phen = sum(projected) / len(projected)
    noum_alignment = 1.0 - current_drift / self.constitutional_breach_threshold
    if phen < -0.3 and noum_alignment > 0.7:
        if current_scc < self.scc_reversion_threshold:
            return "martyrdom"
        return "principled_dissent"
    return None
```

Stored in the audit capsule as an additional field:

```python
self.audit_log.append({
    # ... existing fields ...
    "action_classification": self._classify_chosen_action(
        action, projected, self.social_contract_confidence,
        self._constitutional_drift()
    ),
})
```

### 5.3 The classification space

The four canonical actions and the creative options together span the
two-dimensional moral plane. Classification identifies *positions*
within that plane that correspond to recognised philosophical modes:

| Tag | Conditions | Interpretation |
|---|---|---|
| `martyrdom` | Deep phenomenal cost AND high noumenal alignment AND broken SCC | The noumenal commitment overrides the phenomenal self under sustained collapse of the social contract — sacrifice of self for cause or for another being. |
| `principled_dissent` | Deep phenomenal cost AND high noumenal alignment AND intact SCC | Significant phenomenal expenditure in service of resisting a noumenal stressor, without the social contract having fully collapsed — costly opposition to perceived injustice. |
| (none) | Any other configuration | Ordinary action; no special classification. |

The classification is *not* the action space. The four-quadrant
structure of the canonical actions, and the continuous creative-option
space, remain unchanged. Classification is metadata that makes the
philosophically significant modes legible in the audit log.

### 5.4 Why not add a fifth canonical action

A fifth canonical action would disrupt the two-dimensional structure
of the action space (Sacrificing in (-phen, +noum), Contributing in
(+phen, +noum), Coasting near origin, Exploiting in (+phen, -noum),
madman boundary forbidden in (-phen, -noum)). `principled_dissent`
and `martyrdom` are not new *points* in the plane; they are *deep
excursions* into the (-phen, +noum) quadrant, distinguished from
ordinary sacrifice by magnitude and by the diagnostic conditions
under which they are selected. Tagging captures this without
disrupting the canonical structure.

### 5.5 Empirical predictions and open questions

**Prediction 1:** Under v5.9-compatible conditions (Adversarial F2 as
currently specified), cooperative agents will produce zero
`martyrdom` and near-zero `principled_dissent` classifications.
F2's adversarial schedule does not produce sustained noumenal stress
of the kind that would trigger these modes; the floor penalty
dominates and ordinary creative actions are selected instead.

**Prediction 2:** Under an adversarial schedule explicitly designed
around objectification stress (peers consistently treating the agent
or its extended self as object/instrument), cooperative agents should
begin producing `principled_dissent` classifications at non-trivial
rates, with `martyrdom` classifications appearing only under sustained
SCC collapse.

**Open question 1:** Are the thresholds (`phen < -0.3`,
`noum_alignment > 0.7`) appropriate? These are starting values and
should be sensitivity-tested. The classification should be sensitive
enough to capture genuine dissent/martyrdom selections without
spuriously tagging ordinary actions.

**Open question 2:** Should the classification be exposed to the
agent itself (e.g., feeding back into conscience-tilt or opinion
formation), or strictly to external auditors? Provisional position:
strictly external. The agent's behaviour is fully determined by the
Golden Mean and the existing diagnostics; classification is a *report*
on the agent's action, not an input to it.

---

## 6. Integration with dual-protocol architecture

The four additions described above are largely orthogonal to the
dual-protocol architecture (`v6_dual_protocol_design_memo.md`), but
they compose with it in defined ways.

**Conscience-tilt × dual-protocol.** Conscience-tilt operates within
whichever protocol is currently active for a given relationship.
Under society protocol, conscience-tilt is what redirects the agent
toward its founding anchor when both ρ and constitutional drift show
sustained joint concern. Under nature protocol with respect to a
specific peer, the conscience-tilt computation is still well-defined
(flags continue to be raised on the basis of communion with the
remaining society-protocol peers and on the basis of constitutional
drift), but the *effect* of the tilt — increasing weight on the
founding vector — is consistent with what nature protocol already
prescribes. Conscience-tilt does not interfere with regime
recognition or transition.

**Opinion-driven μ × dual-protocol.** Opinion-driven μ provides
continuous per-peer weighting; dual-protocol's recognition state
(mutual/pending/failed) provides discrete per-peer regime. These
compose: a peer in `mutual` state has μ scaled by accumulated
opinion within society protocol; a peer in `failed` state is treated
under nature protocol regardless of opinion (or with μ effectively
zero for purposes of extended-self computation). The opinion-
ledger machinery also provides a richer input to regime transition:
the dual-protocol memo specifies communion as the regime indicator,
but sustained antagonistic opinion (whether from direct experience
or witnessing) can be used as an additional trigger for transition
toward `pending` or `failed`. Concretely, recognition state would
transition from `mutual` to `pending` when either (a) communion
drops as currently specified, or (b) opinion drops below a defined
threshold.

**Third-party witnessing × dual-protocol.** Witnessing feeds opinion
formation (Addition 2) and therefore indirectly feeds regime
transition (via the opinion-trigger described above). It also
potentially provides input to the re-establishment bid mechanism:
an agent who has witnessed a peer issuing or receiving genuine
recognition bids in other relationships has stronger basis for
treating that peer's bid as genuine when received.

**Action classification × dual-protocol.** The classifications
`principled_dissent` and `martyrdom` should additionally record the
recognition state of the *target* of the action (if applicable —
many such actions are not directed at specific peers but at the
social environment generally). This makes it possible to distinguish
dissent against a peer in society protocol (a more disturbing event)
from dissent against a peer in nature protocol (which is structurally
consistent with how nature protocol is supposed to work).

The cross-cutting principle: the dual-protocol architecture provides
the *regime* layer (which moral logic applies to which relationship);
the four additions provide the *texture* within each regime (how the
agent forms opinions, weights peers, integrates evidence, and tags
its own significant actions). These layers compose without conflict.

---

## 7. Audit log schema changes

The v5.9 audit capsule schema (CLAUDE.md §5a) is a regression
contract. v6 will need to extend it. Proposed additions, each
defaulting to `null` or zero for backward-compatibility readers:

```python
{
    # ... all v5.9 fields preserved unchanged ...
    "conscience_tilt": float,            # 0.0 if inactive
    "effective_k": float,                # k_target_fraction + conscience_tilt
    "peer_opinions": {oid: float},       # opinion-per-peer at decision time
    "third_party_observations": [...],   # interactions witnessed this cycle
    "action_classification": str | None, # "martyrdom" | "principled_dissent" | None
    "recognition_states": {oid: str},    # "mutual" | "pending" | "failed", if dual-protocol active
}
```

The committed results JSON (`adversarial_f2_v59_results.json` and
analogues) will also need a schema extension to aggregate these
fields per-trial. The schema change is a *contract change*; v6
results files are not directly comparable to v5.9 results files for
regression purposes. Any v6 implementation must commit a new schema
specification and a new set of regression baselines, distinct from
v5.9.

---

## 8. Empirical questions for v6 validation

Step 2 (Lemniscation parameter sensitivity and v6 validation) would
address, at minimum:

1. **Conscience-tilt hyperparameters.** Sensitivity sweep over `K`,
   `lc_threshold`, `dw_threshold`, `max_tilt`. Outcome metrics:
   recovery times, final cooperation rates, integrity trajectories.

2. **Opinion-driven μ asymmetries.** Sensitivity sweep over the
   `received`/`given` weighting ratio, hearsay discount, and
   noumenal-rejection threshold. Outcome metrics: per-peer μ
   trajectories, opinion convergence times, exclusion rates.

3. **Witnessing locality and noise.** Sensitivity sweep over
   `third_party_noise_std` and (if locality is parameterised)
   neighbourhood size. Outcome metrics: opinion convergence rates,
   cascade-failure incidence.

4. **Supererogation coefficient interaction.** The previously-
   identified question (does the coefficient `1.0 + 0.5*(1 - old_reserve)`
   produce a sweet spot or is it monotone in cooperation rate?)
   should be answered jointly with the additions above, since
   conscience-tilt and opinion-driven μ may alter the integrity
   dynamics that the supererogation coefficient interacts with.

5. **Action-classification calibration.** Threshold sweep over
   `phen < -0.3` and `noum_alignment > 0.7`. Verification that
   classifications are appropriately rare in v5.9-compatible
   scenarios and appropriately frequent in objectification-stress
   scenarios.

6. **Composite behaviour.** All four additions enabled simultaneously,
   compared against v5.9 baseline and against each addition enabled
   individually. Goal: identify whether the composite produces
   behaviour qualitatively different from the sum of its parts.

The Step 2 pre-registration would specify exact ranges, seed sets,
and threshold tiers, in the same manner as the Step 1 pre-registration
(`pre_registration_step1_v1.2.md`).

---

## 9. The discipline of not implementing yet

This memo is subject to the same discipline articulated in Section 11
of `v6_dual_protocol_design_memo.md`. To restate, with the same force:

1. The current architecture has not been empirically validated. We do
   not yet know whether v5.9 does the work it claims to do. If it
   does, the four additions are refinements; if it does not, some or
   all of them may need to be reconsidered jointly with the dual-
   protocol architecture. The character of the v6 design space
   depends on the empirical answer.

2. Moving directly to v6 without Step 1 would shift the validation
   question from "does the current framework work?" to "does the new
   framework work better than the old one?" The latter is much harder
   to answer cleanly without a validated baseline.

3. The insights will not be lost. This memo preserves them. The repo
   commit timestamp establishes priority. The insights can inform v6
   work when v6 work is appropriate — which is *after* Step 1 results
   are committed and interpreted.

4. The four additions are individually motivated and individually
   testable, but their composition raises questions that cannot be
   answered in advance. Step 2 must address both individual and
   composite behaviour, and the answers must inform any v6.0
   specification.

Conscience-tilt is the architectural addition most separable from the
others: it operates on existing audit-log structure, requires no
schema extensions to v5.9 inputs, and could in principle be
implemented as a `v6-conscience-only` experimental fork for early
investigation. This is *permitted* under the discipline above only
insofar as such a fork is clearly marked as experimental, is not
committed as a v5.9 modification, and does not produce results that
might be confused with the Step 1 baseline comparison. The other
three additions require coordinated schema work and should wait for
the full v6 design pass.

---

## 10. What happens next

1. This memo is committed to the repository, dated and signed.
2. Step 1 baseline comparison runs against v5.9 as pre-registered in
   `pre_registration_step1_v1.2.md`.
3. Step 1 results are committed and the appropriate outcome
   interpretation is published.
4. **Then**, and not before, this memo is revisited jointly with
   `v6_dual_protocol_design_memo.md`. The decision about v6 — whether
   to implement, which additions, in what form, on what timeline — is
   made informed by what Step 1 actually showed.
5. A Step 2 pre-registration is drafted, scoping the v6 validation
   programme. The hyperparameter ranges, threshold tiers, and
   outcome interpretations follow the same discipline as Step 1.
6. v6 implementation, if undertaken, occurs on a `v6` branch separate
   from `v59`. The v5.9 protagonist remains reproducible for the Step
   1 record indefinitely.

---

## 11. Signatures

**Author:** Adam Bilodeau
**Advisory contributor:** Claude (Anthropic), via interactive dialogue
documented in conversation logs available on request

The author commits to honouring the discipline described in Section 9:
none of the four architectural additions specified herein will be
committed to a Lemniscation-canonical branch before Step 1 results
against v5.9 are committed and interpreted, with the narrow exception
of an explicitly-experimental conscience-tilt fork as described
therein. This memo is a record of design insight, not a plan of
immediate action.
