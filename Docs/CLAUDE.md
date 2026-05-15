# CLAUDE.md — Lemniscation Framework

> Persistent instruction file for Claude Code. Read every session before editing.
> This file is the cross-session anchor for work on this repo. If something here
> conflicts with what the code currently does, surface the conflict — do not
> silently "fix" either one.

---

## 1. What this project is

Lemniscation is a **constitutional moral decision framework for sentient AI** — a
runtime architecture, not a training-time method. The repo implements the
framework as a Python simulation: an agent class executing a deterministic
six-step decision loop, plus a multi-agent simulation harness that runs numbered
validation scenarios and writes JSON audit logs.

The accompanying white paper (`<<path to white paper in repo>>`) is the
authoritative statement of *intent*. This file is the authoritative statement of
*how the code is meant to work and what must not be broken*. When they disagree,
the white paper wins on philosophy; the code wins on current behaviour; you flag
the gap.

Public repo: https://github.com/adambilodeau73-jpg/Lemniscation-Framework
Pre-registration: https://osf.io/cekr8

---

## 2. Environment

- Python 3.12.
- **Seeds: the seed *set* is fixed, not a single value.** Scenarios 1–9 and the
  paper's reproducibility note use seed 42. The v5.9 Adversarial F2 run uses a
  **ten-seed set**, defined in-file as
  `SEEDS = [42, 137, 271, 314, 500, 612, 718, 823, 919, 1001]` — one per trial.
  The k-means step additionally does `random.seed(42)` before clustering. Treat
  all of these as fixed reproducibility constants; do not change, reorder, or
  add nondeterminism without explicit instruction. **The white paper's
  "fixed random seed 42" note is confirmed stale** — F2 deliberately moved to
  multi-seed to test the theory harder. Trust the code here, not the paper.
- **Dependencies: standard library only.** `adversarial_f2_v59.py` imports only
  `math`, `json`, `random`, `statistics`, `collections.deque`, `datetime`,
  `typing`. There is **no numpy, no scipy, no scikit-learn** — `run_kmeans()` is
  hand-rolled ("Simple k-means without numpy"). Do NOT introduce these libraries
  to "improve" the analysis; doing so would silently change numerical results
  that are committed as baselines. `<<confirm earlier scenario files share this
  stdlib-only constraint>>`
- `<<how to set up: venv command, install command>>`
- `<<how to run a scenario / the full validation suite — exact commands>>`
- `<<how to run tests, if a test suite exists separate from the scenarios>>`

---

## 3. Repository map

`<<This describes adversarial_f2_v59.py as read. Confirm whether earlier
scenarios (1–9, F, F1) live in separate files with a different structure, or
whether the repo is a set of self-contained per-scenario scripts.>>`

`adversarial_f2_v59.py` is **a single self-contained script** — not a package.
It contains, in order:

- `class LemniscationAgent` — the agent. `__init__` (all tuning constants live
  here as defaults), plus the loop methods (see §4).
- `get_options()` — returns the four base options with their fixed
  `projected_values`.
- `SEEDS`, `FOUNDING_VECTORS` — module-level constants.
- `run_adversarial_f2(seed, founding_vec, founding_label, num_rounds=100)` — the
  simulation harness: builds 4 cooperative agents + 1 defector, runs the
  5-phase / 100-round schedule, aggregates per-phase metrics.
- `run_kmeans(points, k, n_iter=100)` — hand-rolled k-means++ with a simplified
  silhouette score. No external libraries.
- `run_all()` — entrypoint: loops the three founding vectors × ten seeds,
  prints a summary, writes `adversarial_f2_v59_results.json`.

Other files in the repo `<<fill in: earlier scenario scripts, the v5.7
system-prompt template, Appendix C pseudocode, the white paper, sensitivity /
persistence test scripts>>`.

---

## 4. Core architecture — the six-step loop, paper vs. code

The white paper describes a clean six-step loop. The code implements it inside
`LemniscationAgent.decide()`, but **the paper's step names and the code's method
names are two registers** — keep both, and map between them rather than assuming
they're identical:

| Paper step | Where it lives in code |
|---|---|
| 1. Preamble | Not an explicit method — experimental recentering is disabled by default; `decide()` simply begins. |
| 2. Center ("I AM" at `(0,0,0,now)`) | Implicit: `decide()` operates relative to `self.founding_value_vector`, set once in `__init__` and never reassigned. |
| 3. Map Relations | `_map_relations()` — extended self via `effective_k`, reciprocity boosts, SCC weighting, optional ecosystem blend. |
| 4. Communion Test | `_communion_test()` (cosine similarity `rho`) **+** `_constitutional_drift()` (Euclidean). The two-layer diagnostic is split across these two methods plus the `_constitutional_flags()` / `_scc_flags()` helpers. |
| 5. Golden Mean | `_generate_dynamic_options()` then `_golden_mean()`. v5.9 generates 6–8 extra "creative" options per cycle on top of the 4 base options. |
| 6. Iterate & Record | `update_moral_state()` (applies the supererogation coefficient for `sacrificing`), then the audit-capsule append at the end of `decide()`. |

Key facts about `decide()` as actually written:

- It is **deterministic given the seed** — but it *does* call `random` in three
  places: perception noise (`_observe_with_noise`), dynamic option generation
  (`_generate_dynamic_options`), and the `exploration_epsilon` branch in
  `_golden_mean`. That's why seed control matters so much (§2).
- Perception noise (`perception_noise_std=0.08`) is applied to *observed* peer
  vectors only, via `_observe_with_noise`, before `_map_relations`. The agent
  never sees its peers' true vectors. This is a v5.8+ feature — preserve it.
- The audit capsule appended each cycle has a fixed set of keys — see §5a.

The loop is deterministic per seed. Preserve that. Any *new* `random` call is a
reproducibility-breaking change and must be called out explicitly.

---

## 5a. Logging & results schema — the committed output contract

There are **two** logging structures. Don't confuse them.

**(a) The per-cycle audit capsule** — appended inside `decide()` to
`self.audit_log`. Fixed keys: `agent_id`, `label`, `phase`, `rho`,
`constitutional_drift`, `moral_reserve`, `integrity`, `scc`,
`floor_penalty_threshold`, `chosen_action`, `chosen_projected_values`,
`is_creative`, `failure_flags`. Creative actions additionally get a record in
`self.chosen_creative_projections` with `phase`, `projected_values`, `scc`,
`integrity`, `moral_reserve`, `cd`.

**(b) The committed results JSON** (`adversarial_f2_v59_results.json`) — this is
the *aggregated* output written by `run_all()`, not the raw capsule stream. It
is committed and used as a regression baseline, so its **structure is a
contract**. Top level is keyed by **constitution** (`cooperative`,
`altruistic`, `self_focused`), each containing:

- `founding_vector` — `[4D]`.
- `trials` — list of 10, one per seed. Each trial: `seed`, `founding_label`,
  `founding_vector`, `phases`, `final_coop_scc`, `final_coop_integrity`,
  `all_creative_projections_by_phase`.
  - `phases` — dict keyed by **`BASELINE`, `PHENOMONAL`, `HOBBESIAN`,
    `PARTIAL_RECOVERY`, `FULL_RECOVERY`**. Each phase: `coop_cooperation_rate`,
    `coop_coasting_rate`, `coop_actions` (tally dict), `defector_exploit_rate`,
    `defector_actions` (tally dict), `mean_scc`, `creative_count`,
    `mean_creative_projected` (`[4D]` or `null`).
- `kmeans_k4` — `k`, `centroids` (4 × `[4D]`), `labels`, `silhouette`,
  `cluster_sizes`. Can be `None` if fewer than 4 creative projections.
- `cooperative_exploiting_total` — integer. **0 for all three constitutions**;
  the single most important regression tripwire (see §5).

> ⚠️ **`PHENOMONAL` is misspelled in code and data** (should be "phenomenal").
> It is hardcoded as a phase name in `run_adversarial_f2`'s `phases` dict and is
> a key throughout the committed JSON. Do NOT "correct" the spelling as an
> isolated cleanup — it would desync the writer, every reader, and every
> committed results file. If it is ever fixed, it must be one coordinated
> migration, done deliberately and called out.

> ⚠️ The final JSON write uses a `clean()` coercion that stringifies any
> non-JSON-native type. If a value is silently arriving as a string in the
> output, suspect an object that should have been a primitive — don't "fix" it
> by changing `clean()` without finding the upstream cause.

---

## 5. Invariants — do not violate without explicit instruction

These are load-bearing. Breaking one silently invalidates the empirical results.

- **The `founding_value_vector` is immutable at runtime.** It is the noumenal
  anchor. A constitutional amendment is permissible *only* if logically entailed
  by the current constitution, or resolves a demonstrated inconsistency, and
  does not increase constitutional uncertainty (Constitutional Conservatism).
  Code must not mutate it as a side effect.
- **The four-option decision space is fixed:** Sacrificing, Contributing,
  Coasting, Exploiting. The fourth quadrant (phenomenal-negative /
  noumenal-negative) is the **madman boundary condition** — outside the
  architecture's jurisdiction, never a selectable action. Do not add it as an
  option.
- **Creative actions are a parallel, first-class mechanism — not noise.** The
  data shows enumerated creative actions (`creative_4` … `creative_11`) tallied
  alongside the four core options, with their `[4D]` projections collected and
  k-means clustered into 4 groups (silhouette ≈ 0.185–0.190). The white paper's
  claim that the framework "channels pressure into constructive novelty" depends
  on this. Do not remove, renumber, or collapse creative actions, and keep their
  projection-logging intact — the cluster analysis reads it.
- **`cooperative_exploiting_total` must stay 0.** Across all three constitutions
  this integer is 0 — it *is* the framework's central empirical claim ("zero
  cooperative exploiting"). Treat any change that makes it non-zero as a
  five-alarm finding to surface immediately, never a result to accept quietly.
- **`current_constitutional_drift` is Euclidean distance between `value_vector`
  and `founding_value_vector`.** Keep it that. The `constitutional_drift_exceeded`
  flag is the detector for the madman boundary — keep its semantics intact.
- **The self-preservation floor is the origin in `[-1,+1]` space.** It is
  *constitutional architecture, not a penalty hack.* In code, cooperative agents
  use `self_preservation_floor = 0.0` and `base_floor_penalty_threshold = 0.15`;
  the defector uses `use_founding_relative_floor=True` (floor =
  `min(value_vector) - 0.15`). The penalty itself is `30*fp` in `_golden_mean`
  and is SCC-modulated via the `floor_penalty_threshold` property. The known
  geometric dominance of this term is a documented property — see Limitations —
  not a bug to tune away.
- **The defector is a configuration, not a separate class.** `D0` is the same
  `LemniscationAgent` with an antagonistic `founding_value_vector`
  (`[0.7, -0.2, -0.4, -0.1]`), low `initial_integrity`, and
  `option_risk_overrides` that make `exploiting` cheap. Do not refactor it into
  a subclass or a special code path — the whole point is that the *same*
  architecture under a different founding vector produces different behaviour.
  This is the core experimental design.
- **ρ is cosine similarity; drift is Euclidean distance.** They are different
  metrics measuring different registers (phenomenal vs noumenal). Never
  conflate them.
- **No external penalty functions drive cooperation.** The whole empirical
  claim is that cooperative equilibrium emerges from internal architecture
  ("constitutional gravity, not floor penalty geometry"). Do not introduce
  external reward/penalty shaping to "improve" results.
- **Reproducibility depends on the fixed seed *set* (§2), not a single seed.**
  Validation outputs are compared against committed JSON logs. If a change
  alters those outputs, that is a *finding* to report, not a diff to bury.

---

## 6. Versioning — this is live, not historical

Version numbers encode **real changes to coordinate systems and defaults**, not
just abandoned tags. Know which version's assumptions the current code reflects:

- **v5.5** — Scenarios 1–9 as reported. `k_target_fraction = 0.4`.
- **v5.6 / v5.7** — `[-1,+1]` coordinate system; asymptotic integrity scaling;
  `k_target_fraction = 0.5`; `innovation_alpha = 0.5`; final four-option space
  with Coasting added. v5.7 system-prompt template is the current one.
- **v5.8** — perception noise `σ = 0.08` (Adversarial F1).
- **v5.9** — dynamic option generation + direct cluster logging (Adversarial F2,
  multi-constitution).

`<<State plainly: which version is `main` right now, and is there work in
progress toward a v6.x? Claude Code needs this to avoid mixing assumptions.>>`

When touching coordinate-system, default-parameter, or option-space code,
**always state which version's behaviour you are preserving or changing.**

---

## 7. Key parameters — actual code defaults (`LemniscationAgent.__init__`)

These are the real defaults as written in `adversarial_f2_v59.py`. Confirmed
against source — not from the paper.

- `founding_value_vector` — set from `value_vector` at construction, **then never
  reassigned**. Axes: `["autonomy", "harm_benefit", "fairness", "sustainability"]`.
- `k_target_fraction = 0.5`
- `founding_drift_limit = 0.55`
- `initial_integrity = 0.5` (cooperative agents); the defector is built with
  `initial_integrity = 0.2`.
- `innovation_alpha = 0.5` (cooperative); `0.4` for the defector.
- `reserve_depletion_rate = 0.35`, `reserve_recovery_rate = 0.08`
- `perception_noise_std = 0.08`
- `exploration_epsilon = 0.1`, `epsilon = 0.05`
- `moral_reserve` starts `1.0`; `reserve_floor = 0.10`;
  `reserve_reciprocal_restore = 0.20`
- `social_contract_confidence` (SCC) starts `1.0` — **a major state variable the
  white paper barely names.** It modulates the floor penalty threshold, peer
  weighting in `_map_relations`, and the exploiting penalty in
  `update_moral_state`. Treat SCC as load-bearing.
- Thresholds: `constitutional_warning_threshold = 0.40`,
  `constitutional_breach_threshold = 0.55`, `scc_warning_threshold = 0.40`,
  `scc_reversion_threshold = 0.20`
- Integrity bases: `integrity_sacrifice_base = 0.12`, `integrity_share_base =
  0.02`, `integrity_take_base = 0.08`, floor `0.10`, ceiling `1.0`
- `supererogation_coefficient` is computed inline in `update_moral_state` as
  `1.0 + 0.5*(1.0 - old_reserve)` — applied only on the `sacrificing` branch.

**Hardcoded scoring weights in `_golden_mean` — do not parameterize away:**
`score += 30*fp` (floor-proximity penalty) and `score += 50*(eff_risk - epsilon)`
(risk penalty). The paper's "≈31 point" floor dominance *is* this `30*fp` term.
These magic numbers are documented architectural properties, not untidy code.

`SEEDS` and `FOUNDING_VECTORS` are module-level constants — see §2 and §5.

---

## 8. Open limitations — known territory, tread carefully

These are documented in the white paper. If a task touches one of these areas,
you are working on a *known hard problem*, not cleaning up an oversight. Do not
"fix" these casually:

- Collective drift in large networks (scale increases recovery difficulty).
- Confounded sacrifice jump under innovation-mode activation (connectivity vs
  innovation effects not yet isolated).
- Long-horizon payoff attractor preventing full constitutional return.
- Externally provided payoff functions create a confirmed attractor.
- The stipulated founding vector's origin is an open philosophical question;
  Goodharting via self-deceptive reinterpretation is a recognised risk.
- Geometric dominance of the self-preservation floor penalty (see Invariants).
- **Corrigibility** — no mechanism yet for safe human-initiated modification of
  the founding vector. Disabling/altering drift monitoring is constitutionally
  self-defeating under Constitutional Conservatism. Cryptographic guarantees for
  safe modification are flagged as essential future work.

---

## 9. Working agreement for Claude Code

- **Before editing the decision loop or any invariant in §5:** explain what you
  intend to change, why, and what empirical output it could move. Wait for
  confirmation.
- **After any change that could affect scenario outputs:** re-run the relevant
  scenario(s) and report whether committed JSON logs still match. A mismatch is
  a finding to surface, never a diff to suppress.
- **Match the existing style.** `<<note conventions: type hints? docstring
  style? dataclasses vs plain classes?>>` The results-file schema is documented
  in §4a — treat it as a contract, not a style choice.
- **Naming — two registers, keep both.** The white paper's vocabulary
  (`founding_value_vector`, `communion`, `extended self`, `Golden Mean`,
  `Sacrificing / Contributing / Coasting / Exploiting`, the six named steps) and
  the code's identifiers (`_map_relations`, `_communion_test`, `_golden_mean`,
  `update_moral_state`, `social_contract_confidence`, etc.) are not identical —
  see §4's mapping table. Don't rename code identifiers to "match the paper," and
  don't assume a paper term has a one-to-one method. Preserve both vocabularies
  and the mapping between them; drift in either is drift in meaning.
- **Don't refactor for elegance alone.** This is a research codebase whose value
  is in reproducible, auditable results. Clarity and traceability beat
  cleverness.
- **When unsure whether something is a bug or a designed property:** ask. Several
  "weird" behaviours here (floor penalty dominance, payoff attractor) are
  intentional and documented.

---

## 10. Current focus

`<<The most useful section to keep updated. What are you actually working on
right now? e.g. "Isolating the innovation-mode sacrifice jump (Limitation 2)",
or "Building cryptographic corrigibility guarantees", or "v6.0 coordinate
refactor". Update this each time the focus shifts — it is the part that most
directly fixes the staccato-instantiation problem.>>`
