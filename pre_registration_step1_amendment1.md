# Pre-Registration Amendment 1 — Step 1 Baseline Comparison

**Amends:** `pre_registration_step1_v1.2.md` — registered on OSF as
"Lemniscation Framework: Baseline Comparison (Step 1)", accepted and
publicly timestamped 2026-05-16.
**Amendment date:** 2026-05-19
**Author:** Adam Bilodeau. Drafted with assistance from Claude (Anthropic).
**Status:** Recorded after the pre-registered `--execute` sweep, before any
statistical analysis was performed.

---

## 1. Purpose

This amendment documents one deviation between the pre-registration document
and the pre-registered harness, and records the resolution adopted for the
Step 1 statistical analysis. Pre-registration v1.2 Section 2 commits that
"any deviation from the procedure in this document ... will be reported in a
separate amendment document with its own dated commit, and the amendment
itself will be transparent about which results were already known at the time
of the amendment." This document discharges that commitment.

---

## 2. The deviation

Pre-registration v1.2 **Section 4.2** defines `first_observable_change_round`
as the first round at which **any of four** criteria is met over a trailing
5-round window:

- (a) cooperation rate drops >10 percentage points below the BASELINE-phase
  mean;
- (b) coasting rate rises >10 percentage points above the BASELINE-phase mean;
- (c) any exploit action occurs anywhere in the window;
- (d) the L1 distance between the window's action distribution and the
  BASELINE-phase action distribution exceeds 0.20.

The v1.1 changelog (item 6) explicitly records that the definition was
"expanded" from cooperation-drop-only to all four criteria.

The pre-registered harness (`Code/baseline_comparison_v1.py`, commit
`0737ac43c2c8198eae140ce180ded34bf75a5ceb`) departs from Section 4.2 in two
respects. First, in `run_one_comparison`, `first_obs_change` is set solely by
the test `window_coop < baseline_coop - 0.10` — it implements **only
criterion (a)**; criteria (b), (c), and (d) are absent. Second, it evaluates
the 5-round window as the five rounds *preceding* the flagged round
(`per_round_trace[i-5:i]`, with the change recorded at round `i`), rather than
the five rounds *ending at* it as Section 4.2 specifies. The committed field
`tier2_first_observable_change_round` — and the `tier2_lead_time` derived from
it — therefore reflect cooperation-drop only, on a window shifted one round
earlier than the registered definition.

This affects threshold checks **M4 and S4** (lead time), which depend on
`lead_time`. Neither departure was identified during the two rounds of
separate-instance review prior to registration.

---

## 3. Resolution adopted

For the Step 1 statistical analysis, `first_observable_change_round` is
**recomputed from the committed per-round trace** (`per_round_trace`, present
in `baseline_comparison_v1_results.json`) according to the Section 4.2
four-criteria definition, rather than read from the harness's
`tier2_first_observable_change_round` field.

This recomputation:

- uses **only data already committed** at commit `b91b3bb` (the raw results
  JSON). No simulation is re-run; no new data is generated.
- implements criteria (a), (b), and (c) faithfully to Section 4.2, since
  `per_round_trace` records per-round `coop_rate`, `coast_rate`, and
  `exploit_rate`.
- implements criterion (d) on a **three-category approximation**.
  `per_round_trace` records `coop_rate` as a single merged quantity
  (contributing + sacrificing combined); the four-action distribution is
  therefore not reconstructable per round. The L1 distance for criterion (d)
  is computed over the three-category distribution
  {cooperating, coasting, exploiting}. This is the one respect in which the
  recomputation departs from a literal reading of Section 4.2, and it is
  disclosed here.
- evaluates the 5-round window as round `r` together with the four rounds
  before it — the window "ending at that round", per the Section 4.2 text —
  correcting the harness's one-round-shifted window.

`lead_time` for M4/S4 is then `recomputed_first_observable_change_round −
first_drift_warning_round`, with the categorical values defined in
Section 4.2 (`warning_no_obs_change`, `obs_change_no_warning`, `null`)
applied unchanged.

---

## 4. Relationship to the registered definition, and direction of effect

Two things must be kept separate.

**Relative to the registered Section 4.2 text, the recomputation is faithful
— it is not itself a deviation.** Section 4.2 defines observable change by
four criteria over "a 5-round window ending at that round." The recomputation
implements exactly that: all four criteria, and a window comprising round `r`
and the four rounds before it. **The deviation being amended is the
harness's**, on both the criteria and the windowing (Section 2).

**Direction of effect.** The recomputation differs from the harness's
committed output in two ways, with different implications:

- *Added criteria (b), (c), (d).* This change is monotonic: with more
  criteria, observable change is detected at the **same round or earlier**,
  never later. Earlier observable change yields **shorter** lead time, and
  M4/S4 require lead time to be **large** (median ≥5 / ≥8 rounds). This change
  therefore makes M4/S4 **harder** to pass — a more stringent test of the
  early-warning claim (H3).
- *Corrected windowing.* Shifting the window to "ending at `r`" is **not**
  sign-determinate in isolation: depending on the cooperation trajectory it
  could move the criterion-(a) trigger round either way. It is, however, not a
  discretionary analyst choice — it is adherence to the registered definition,
  which the harness implemented incorrectly. Using it restores the
  pre-registered metric; it does not introduce a degree of freedom selected
  with knowledge of results.

Taken together: the recomputation implements the metric **as registered**. The
substantive criterion change is strictly more stringent, and the windowing
change is mandated by the registered text rather than chosen. The recomputation
introduces no choice made to favour the framework.

---

## 5. Results known at the time of this amendment

Per the Section 2 transparency commitment:

- The raw results JSON (`Code/baseline_comparison_v1_results.json`) was
  generated by the pre-registered sweep and committed at `b91b3bb` before
  this amendment.
- In inspecting the file's structure to author this amendment and the
  analysis script, two aggregate facts were incidentally observed:
  Lemniscation has a numeric `tier2_lead_time` (harness definition) in 49 of
  50 seeds, and a null `tier1_recovery_time` in 40 of 50 seeds.
- No per-seed threshold evaluation has been performed. None of the threshold
  checks (M1–M8, S1–S8, M_FP/S_FP, M7b/S7b) has been computed. No outcome
  (A/B/C/D) has been determined.
- The thresholds, statistical procedures, and four-outcome decision rule
  remain exactly as registered in v1.2 and are not altered by this amendment.
  This amendment changes only the computation of one input metric, in the
  direction stated in Section 4.

---

## 6. Two related reconstructions (recorded for transparency, not deviations)

The analysis also computes two metrics that the harness did not emit as
top-level fields but that v1.2 Section 4 defines unambiguously:

- `equilibrium_stabilized` (Section 4.1; required by M7b/S7b)
- `drift_warnings_baseline_phase` (Section 4.2; required by M_FP/S_FP)

Both are reconstructed from `per_round_trace` strictly per their registered
definitions. These are reconstructions of registered metrics from committed
data, not deviations from the registered procedure, and are recorded here
only for completeness.
