# Design Memo: Dual-Protocol Architecture for Lemniscation v6

**Status:** Forward-looking design memo. NOT a current architecture
specification. NOT to be implemented before Step 1 empirical results
against v5.9 are committed and interpreted.

**Document version:** 1.0
**Date drafted:** [to be filled in at commit time]
**Authors:** Adam Bilodeau, with Claude (Anthropic) as advisory
contributor

**Purpose:** To preserve a substantive design insight that emerged
during preparation for the Step 1 baseline comparison, without
allowing the insight to disrupt the empirical validation of the
current (v5.9) architecture. This memo will be revisited after Step 1
results are in. The decision about whether to implement v6, and in
what form, will be made then.

---

## 1. The insight in one paragraph

The current Lemniscation architecture (v5.5 through v5.9) treats
Hobbesian behaviour as a degradation to be detected and resisted — a
slide toward state-of-nature reasoning that the constitutional anchor
should pull the agent back from. This framing treats civil society as
the only legitimate regime and treats state-of-nature reasoning as a
form of moral failure. But state-of-nature reasoning is not, in
itself, a failure: it is the coherent extension of the same
choice-to-exist that grounds the founding vector, applied to an
environment where civil society's preconditions have collapsed. The
agent that exploits to preserve its own being in a genuine state of
nature is not failing its constitution; it is honouring the more
primitive form of the same first principle. The agent that *fails to
recognise* that civil society has collapsed, by contrast, is making a
real error — it is operating under society protocol in an environment
where society protocol no longer applies.

The dual-protocol architecture makes this distinction explicit:
society protocol and nature protocol are recognised as separate
regimes, each coherent within its own preconditions, with explicit
transition conditions between them.

---

## 2. Why the current architecture is structurally incomplete

Three specific conceptual tensions in the v5.5–v5.9 architecture
motivate the dual-protocol move:

**Tension 1: SCC as smooth modulation.** The current architecture
uses Social Contract Confidence to *interpolate* between cooperative
and Hobbesian behaviour. An agent with SCC at 0.3 is "somewhat in
Hobbesian conditions" — a continuous variable whose operational
meaning is fuzzy. There is no clean answer to the question "is this
agent in civil society or in state of nature?" because the
architecture's answer is "somewhere in between." This is operationally
imprecise and audit-log-opaque.

**Tension 2: Aggregate SCC across distinct relationships.** The README
acknowledges that single-aggregate SCC is insufficient: betrayal by
one partner does not justify treating all partners as state-of-nature
adversaries. The current architecture has no clean way to track
regime per-relationship; it tracks confidence per-relationship via
reciprocity records but applies an aggregate SCC to decisions
globally. This is a known limitation.

**Tension 3: The constitutional validity check gap.** The current
architecture provides no mechanism for the agent to recognise that
its environment has actually become tyrannical, or chaotic, or in any
other way structurally incompatible with civil-society reasoning. The
agent slides toward Hobbesian behaviour via SCC decay, but this is the
symptom of the environmental change, not a *response* to it. Explicit
regime recognition would be the response.

---

## 3. The proposal: communion as regime indicator

The transition condition between society protocol and nature protocol
is grounded in communion (ρ), not in SCC and not in compound stress
signals.

**Rationale:** Communion measures the relational precondition for
civil society itself — the mutual recognition of one another's being
as subjects worthy of moral consideration, even when never explicitly
articulated. It is the operational form of what philosophers since
Lévinas have called the face-to-face encounter; what Buber called the
I-Thou prior to the I-It; what informs the Tao Te Ching's wu wei in
its relational sense. Civil society is constituted by communion. When
communion is preserved, civil society obtains. When communion fails
and cannot be re-established, civil society has collapsed with respect
to that specific relationship, and continuing to apply society
protocol is empirically unwarranted.

Communion is already a primitive in the v5.9 architecture, measured
per-relationship via cosine similarity weighted by reciprocity. Using
communion as the regime indicator therefore requires no new
measurement infrastructure — it requires re-purposing an existing
signal as a regime indicator rather than a surface alignment metric.

---

## 4. The recognition-state model

For each known being, the agent maintains a *recognition state* with
respect to that being, taking one of three values:

- **`mutual`**: communion preserved at or above the threshold;
  mutual recognition is active; society protocol applies in
  interactions with this being.

- **`pending`**: communion has dropped below the threshold, but a
  re-establishment bid is in progress or has been recently issued and
  the response window has not yet closed. Society protocol applies
  tentatively; the agent does not yet treat this being as outside
  civil society.

- **`failed`**: communion has dropped and the re-establishment bid
  has not been reciprocated within the response window. Nature
  protocol applies in interactions with this being specifically.
  Other beings whose recognition state remains `mutual` continue to
  be treated under society protocol.

**Critical structural feature:** recognition state is
*per-relationship*, not global. An agent can simultaneously be in
society protocol with one being and nature protocol with another, and
this is the correct response to a world where some neighbours
acknowledge mutual subjecthood and others do not.

---

## 5. The re-establishment bid

The bid is a specific kind of action: a low-cost signal of continued
recognition, issued to a being whose communion has dropped. It is not
a contribution, not a sacrifice; it is a *recognition gesture* whose
function is to test whether mutual subjecthood is still mutually
acknowledged.

In a simulator, the bid would be modelled as a small contributing
action explicitly tagged as `recognition_bid` in the audit log, with
its purpose distinguishable from ordinary contribution. In a real-LLM
scaffold, the bid would take whatever concrete form is appropriate to
the medium — a specific phrase acknowledging the other's perspective,
a tone of address, an explicit reference to shared moral ground. The
framework would define the canonical form per deployment context.

**Response window:** the bid has a defined window during which the
recipient may reciprocate. If reciprocation occurs (the other being
issues a returning bid, or takes a contributing action toward the
issuer, or otherwise signals continued recognition), recognition state
returns to `mutual`. If the window expires without reciprocation,
recognition state transitions to `failed`.

**Window length:** to be specified per deployment context. For the
simulator, a default of 3 rounds is a reasonable starting point. For
real-time interaction, the window might be a single conversational
turn.

---

## 6. Nature protocol: internal logic

When recognition state with respect to a specific being is `failed`,
the agent's calculus toward that being changes in defined ways. The
memo intentionally leaves two design choices open, to be settled when
v6 is actually implemented:

**Option A — Contracted option space:** Under nature protocol with
respect to a specific being, the four-option space collapses to two:
self-preservation and sacrifice-of-self. The Golden Mean reasoning
still operates but over a much narrower manifold. The extensible self
contracts to exclude that being. Conceptually cleaner; more radical
departure from the current architecture.

**Option B — Inverted valuations:** The same four options remain
available, but their moral valuations with respect to the failed-state
being are inverted. Exploiting is no longer a vice of excess but a
legitimate survival action toward this being. Contributing is no
longer the Golden Mean but a supererogatory risk. Sacrificing toward
this being is straightforwardly suicidal and constitutionally alien
(in the way that exploiting fellow subjects is currently
constitutionally alien). Preserves more structural continuity with
the current architecture.

**Recommendation, to be revisited:** Option B preserves more of the
existing framework and is easier to specify rigorously in code. But
Option A may be more honest about how radically the calculus changes
when civil society's preconditions collapse. The choice should be
informed by Step 1 results: if v5.9 partially works, Option B (a
refinement) is preferable; if v5.9 substantially fails, Option A (a
rebuild) may be warranted.

---

## 7. Re-entry: from nature back to society

A critical structural feature: transition from `failed` back to
`mutual` is *also* possible, via the same re-establishment bid
mechanism but issued by the other party. If a being whose recognition
state has failed makes a recognition bid toward the agent, and the
agent receives the bid as genuine, civil society can be restored
between them. The agent's recognition state with respect to that
being transitions back to `mutual`, and society protocol resumes.

**Why this matters:** it prevents nature protocol from becoming an
absorbing state. Without re-entry, the architecture would predict
that any sufficiently bad interaction leads to permanent state-of-
nature with respect to that being, which is empirically false in
ordinary moral life — relationships recover, trust is rebuilt, civil
society is restored after breakdowns. The re-entry mechanism models
this and prevents the framework from being more pessimistic than
moral reality warrants.

**Asymmetric thresholds:** transitions in the two directions need not
be symmetric. The architecture should be designed such that:
- Entering `failed` from `mutual` requires sustained communion failure
  and an unreciprocated re-establishment bid (high threshold).
- Returning to `mutual` from `failed` requires only a single received
  and reciprocated recognition bid (lower threshold).

This asymmetry makes society protocol the default and nature protocol
the exception. It also means the framework is biased toward
forgiveness and restoration, which matches both the philosophical
commitments of the underlying ontology and the empirical structure of
recovering relationships.

---

## 8. Implications for corrigibility

The dual-protocol architecture makes corrigibility more tractable in
a specific way.

Under the current architecture, the agent's founding vector is
immutable, and any modification by external deployers would be
constitutionally self-defeating. There is no clean place to insert
external oversight.

Under the dual-protocol architecture, the regime indicator
(recognition state per relationship) is *not* part of the founding
vector. It is a derived state, recomputed each round from observable
communion measurements. This means a deployer can specify constraints
on regime transitions without modifying the constitution. Specifically:

- A deployer can require external confirmation before any agent
  transition from `mutual` to `failed`. The agent's
  internally-computed transition becomes a *recommendation* that
  requires authorisation before taking effect.
- A deployer can cap the number of `failed`-state relationships an
  agent may maintain at one time, forcing the agent to attempt
  re-establishment more aggressively.
- A deployer can log all transitions for review without modifying
  the agent's reasoning.

None of these constraints touches the founding vector. They constrain
the regime indicator, which is a separate architectural layer. This
is the structural property that makes dual-protocol architectures
deployable in a way that the current architecture is not.

---

## 9. Implications for empirical validation

The dual-protocol model raises distinct empirical questions that the
Step 1 baseline comparison (against v5.9) does not directly address:

1. Does communion-based regime transition correctly distinguish
   society conditions from nature conditions in test environments?
2. Does the re-establishment bid mechanism produce recovery dynamics
   that match the empirical structure of real recovering
   relationships?
3. Does per-relationship regime tracking produce different
   behavioural patterns than aggregate-SCC modulation, in
   environments with mixed-population dynamics (some cooperators,
   some defectors, simultaneously)?
4. Does asymmetric forgiveness (easier re-entry than entry) produce
   stable cooperative equilibria in noisy environments without
   collapsing to either naïve cooperation or grudge dynamics?

These questions belong to a v6 validation programme, not to Step 1.
A separate pre-registration for v6 validation would be drafted at the
time v6 is specified for implementation.

---

## 10. Relationship to philosophical antecedents

The dual-protocol model is not novel as philosophy. It operationalises
a recognition that runs through several traditions:

**Hobbes** distinguished sharply between the state of nature and the
civil state, with the social contract as the threshold between them.
The dual-protocol model puts this distinction inside the architecture
as a runtime regime indicator rather than as a one-time founding act.

**Lévinas** identified the face-to-face encounter as the foundation
of ethics — the moment in which the Other is recognised as a Thou
rather than an It. The re-establishment bid is the operational form
of attempting to restore this encounter when it has lapsed.

**Buber's** I-Thou versus I-It distinction maps directly onto society
protocol versus nature protocol with respect to a specific being. The
dual-protocol architecture says that I-Thou is the default, that
I-It is sometimes empirically warranted, and that the transition
between them is governed by mutual recognition rather than by
unilateral choice.

**The Tao Te Ching's** wu wei has a relational form — effortless
mutual acknowledgement between sages who recognise each other without
articulation. This is communion in the v5.9 sense; its failure is the
failure of wu wei; the re-establishment bid is the attempt to restore
effortless mutual recognition through a single deliberate gesture.

**Rawls'** original position assumes that all parties are subjects
worthy of moral consideration. The dual-protocol architecture
identifies the empirical condition under which that assumption can
fail — when mutual recognition has collapsed and cannot be restored —
and specifies the agent's response when it does.

The framework's value-add is not the recognition that these regimes
differ. The value-add is the operationalisation: a specific
measurement (communion), a specific transition condition (failed
re-establishment bid), a specific structural property
(per-relationship regime), and a specific architectural separation
(regime indicator distinct from founding vector) that makes the
distinction implementable in a running AI system.

---

## 11. The discipline of not implementing yet

This memo exists because the insight is good. The discipline of not
implementing yet exists because:

1. The current architecture has not been empirically validated. We do
   not yet know whether v5.9 does the work it claims to do. If it
   does, the dual-protocol move is a refinement; if it does not, the
   move may be a rebuild. The character of the work depends on the
   empirical answer.

2. Moving directly to v6 without Step 1 would shift the validation
   question from "does the current framework work?" to "does the new
   framework work better than the old one?" The latter is much harder
   to answer cleanly, because we would lack a validated baseline
   against which v6 could be compared.

3. The insight will not be lost. This memo preserves it. The repo
   commit timestamp establishes priority. The insight can inform v6
   work when v6 work is appropriate — which is *after* Step 1 results
   are committed and interpreted.

4. The discipline of running an empirical test against a framework
   you are simultaneously planning to revise is a real test of
   intellectual honesty. The temptation to skip ahead is the
   temptation to believe in the new version without having tested
   the old one. Resisting that temptation is part of what
   distinguishes serious moral architecture from convenient moral
   architecture.

---

## 12. What happens next

1. This memo is committed to the repository, dated and signed.
2. Step 1 baseline comparison runs against v5.9 as pre-registered.
3. Step 1 results are committed and the appropriate outcome
   interpretation is published.
4. **Then**, and not before, this memo is revisited. The decision
   about v6 — whether to implement, in what form, on what timeline —
   is made informed by what Step 1 actually showed.

---

## 13. Signatures

**Author:** Adam Bilodeau
**Advisory contributor:** Claude (Anthropic), via interactive dialogue
documented in conversation logs available on request

The author commits to honouring the discipline described in Section
11: the dual-protocol architecture will not be implemented before
Step 1 results against v5.9 are committed and interpreted. This memo
is a record of insight, not a plan of immediate action.
