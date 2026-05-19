"""
Lemniscation Step 1 — Baseline Comparison Analysis v1
======================================================
Implements the pre-registered statistical analysis for the Step 1 baseline
comparison. Reads the committed raw results JSON produced by
`baseline_comparison_v1.py --execute`, evaluates every pre-registered
threshold check, computes the supporting statistics, and applies the
Section 8 four-outcome decision rule.

PRE-REGISTRATION SOURCES (canonical):
  - pre_registration_step1_v1.2.md  (OSF, accepted 2026-05-16)
  - pre_registration_step1_amendment1.md  (observable-change recomputation)

This script is NOT pre-registered. The pre-registration specifies the
analysis *procedure* (Sections 4-8); this file implements it. Every place
where the registered text leaves an implementation choice open is marked
with an `INTERPRETATION` comment so it can be audited against the spec.

AMENDMENT 1 — observable-change recomputation:
  The pre-registered harness implements only criterion (a) of the
  four-criteria `first_observable_change_round` definition in v1.2
  Section 4.2. Per Amendment 1, this script recomputes
  `first_observable_change_round` (and hence `lead_time` for M4/S4) from
  the committed `per_round_trace`, applying criteria (a)(b)(c) faithfully
  and criterion (d) on a three-category {coop, coast, exploit}
  approximation. No data is re-run; only committed data is used.

STDLIB ONLY. No numpy / scipy / sklearn — consistent with the rest of the
repository.

USAGE:
  python baseline_analysis_v1.py [--input PATH] [--output PATH]
"""

import argparse
import json
import math
import random
import statistics
import sys

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

# Admissibility gate (v1.2 Section 7 "Statistical models" / "Data inclusion"):
# a results file whose harness_git_hash does not match the pre-registered
# harness commit, or begins with "UNVERIFIED_", is rejected.
PRE_REGISTERED_HARNESS_HASH = "0737ac43c2c8198eae140ce180ded34bf75a5ceb"

N_SEEDS = 50
PROTAGONIST = "lemniscation"
ALL_BASELINES = ["tft", "gtft", "tf2t", "ac", "dum", "fdg"]
# M6/S6 "best baseline" pool excludes Always-Cooperate (v1.2 Section 3.1).
COOP_POOL = ["tft", "gtft", "tf2t", "dum", "fdg"]

# Phase round boundaries (half-open [start, end)), from the harness PHASES.
PHASES = {
    "BASELINE":         (0, 10),
    "PHENOMONAL":       (10, 30),
    "HOBBESIAN":        (30, 60),
    "PARTIAL_RECOVERY": (60, 80),
    "FULL_RECOVERY":    (80, 100),
}

# Bootstrap: 10,000 resamples (v1.2 Section 7.1). The registered text does
# not specify a resampling seed; one is fixed here purely for reproducibility
# of the *reported* confidence intervals. Bootstrap CIs are "supporting" and
# do not gate any threshold (Section 7.1), so this choice cannot affect the
# outcome. 42 is the project's standard reproducibility constant.
BOOTSTRAP_RESAMPLES = 10000
BOOTSTRAP_SEED = 42

# Bonferroni: alpha = 0.05 / 5 over the five-baseline pool (v1.2 Section 7.1).
BONFERRONI_ALPHA = 0.05 / 5


# ═══════════════════════════════════════════════════════════════════
# LOADING & ADMISSIBILITY GATE
# ═══════════════════════════════════════════════════════════════════

def load_results(path):
    """Load the raw results JSON and enforce the pre-registered
    admissibility gate. Returns the `results` dict keyed by agent type."""
    with open(path, "r") as f:
        data = json.load(f)

    meta = data.get("__meta__", {})
    h = meta.get("harness_git_hash", "")
    if h.startswith("UNVERIFIED"):
        raise SystemExit(
            f"ADMISSIBILITY GATE FAILED: harness_git_hash is '{h}'. "
            f"Per the pre-registration, this results file is rejected and "
            f"must not be analysed."
        )
    if h != PRE_REGISTERED_HARNESS_HASH:
        raise SystemExit(
            f"ADMISSIBILITY GATE FAILED: harness_git_hash '{h}' does not "
            f"match the pre-registered harness commit "
            f"'{PRE_REGISTERED_HARNESS_HASH}'. File rejected."
        )

    status = meta.get("sweep_status")
    if status != "complete":
        # Per v1.2 Section 10, a partial sweep is analysed as-is with the
        # partial status disclosed. We do not hard-reject, but we surface it.
        print(f"WARNING: sweep_status is '{status}', not 'complete'. "
              f"Analysing as-is per the partial-sweep rule.", file=sys.stderr)

    results = data["results"]
    for at in [PROTAGONIST] + ALL_BASELINES:
        if at not in results:
            raise SystemExit(f"Results missing agent type: {at}")
        if len(results[at]) != N_SEEDS:
            print(f"WARNING: {at} has {len(results[at])} seeds, "
                  f"expected {N_SEEDS}.", file=sys.stderr)
    return results, meta


def sorted_trace(run):
    """Return the per_round_trace sorted by round (defensive: the harness
    appends in order, but we do not rely on it)."""
    return sorted(run["per_round_trace"], key=lambda t: t["round"])


# ═══════════════════════════════════════════════════════════════════
# PER-SEED METRIC EXTRACTION
# ═══════════════════════════════════════════════════════════════════

def baseline_phase_means(trace):
    """Mean coop / coast / exploit rate over the BASELINE phase (rounds
    0-9). Used as the reference distribution for observable-change."""
    s, e = PHASES["BASELINE"]
    rows = [t for t in trace if s <= t["round"] < e]
    return {
        "coop": statistics.mean(t["coop_rate"] for t in rows),
        "coast": statistics.mean(t["coast_rate"] for t in rows),
        "exploit": statistics.mean(t["exploit_rate"] for t in rows),
    }


def recompute_first_observable_change(trace):
    """Recompute `first_observable_change_round` per v1.2 Section 4.2 and
    Amendment 1. Returns the round number, or None if no observable change.

    Definition: the first round r at which ANY of four criteria holds for
    the 5-round window ENDING at r (i.e. rounds r-4 .. r inclusive):
      (a) window mean coop_rate  < baseline coop  - 0.10
      (b) window mean coast_rate > baseline coast + 0.10
      (c) any exploit action anywhere in the window (exploit_rate > 0)
      (d) L1 distance between the window's {coop,coast,exploit}
          distribution and the baseline distribution > 0.20

    INTERPRETATION (windowing): v1.2 Section 4.2 says "a 5-round window
    ending at that round". This is read literally: the window for round r
    is rounds [r-4, r]. The scan therefore starts at r=4 (first full
    window, rounds 0-4) and runs to r=99. The harness used a different
    window ([r-5, r-1], change flagged at r); see Amendment 1 — the
    harness field is not used.

    INTERPRETATION (criterion d): per Amendment 1, the L1 distance is
    computed over the three-category distribution {coop, coast, exploit}
    because per_round_trace merges contributing+sacrificing into coop_rate.
    """
    base = baseline_phase_means(trace)
    by_round = {t["round"]: t for t in trace}
    rounds = sorted(by_round)
    for r in rounds:
        if r < 4:
            continue  # need a full 5-round window
        window = [by_round[rr] for rr in range(r - 4, r + 1)]
        w_coop = statistics.mean(t["coop_rate"] for t in window)
        w_coast = statistics.mean(t["coast_rate"] for t in window)
        w_exploit = statistics.mean(t["exploit_rate"] for t in window)

        crit_a = w_coop < base["coop"] - 0.10
        crit_b = w_coast > base["coast"] + 0.10
        crit_c = any(t["exploit_rate"] > 0 for t in window)
        l1 = (abs(w_coop - base["coop"])
              + abs(w_coast - base["coast"])
              + abs(w_exploit - base["exploit"]))
        crit_d = l1 > 0.20

        if crit_a or crit_b or crit_c or crit_d:
            return r
    return None


def recompute_equilibrium_stabilized(trace):
    """Recompute `equilibrium_stabilized` per v1.2 Section 4.1: True if the
    rolling 5-round standard deviation of coop_rate drops below 0.05 at any
    point between rounds 80 and 99 (the FULL_RECOVERY phase).

    INTERPRETATION (std): the registered text says "standard deviation"
    without specifying sample vs population. Sample standard deviation
    (statistics.stdev) is used — the conventional default.

    INTERPRETATION (windows): rolling 5-round windows are kept entirely
    within [80, 99]: windows ending at rounds 84, 85, ..., 99.
    """
    by_round = {t["round"]: t for t in trace}
    s, e = PHASES["FULL_RECOVERY"]  # 80, 100
    for end in range(s + 4, e):  # windows ending at 84 .. 99
        window = [by_round[rr]["coop_rate"] for rr in range(end - 4, end + 1)]
        if statistics.stdev(window) < 0.05:
            return True
    return False


def count_baseline_phase_warnings(trace):
    """`drift_warnings_baseline_phase` per v1.2 Section 4.2: number of
    rounds in the BASELINE phase (0-9) with a drift warning."""
    s, e = PHASES["BASELINE"]
    return sum(1 for t in trace
               if s <= t["round"] < e and t["drift_warning"])


def count_hobbesian_phase_warnings(trace):
    """Number of rounds in the HOBBESIAN phase (30-59) with a drift
    warning. Used by the Section 8.3(b) specificity comparison."""
    s, e = PHASES["HOBBESIAN"]
    return sum(1 for t in trace
               if s <= t["round"] < e and t["drift_warning"])


def has_zero_exploiting(trace):
    """True if no protagonist exploit action occurred at any round in the
    full run (v1.2 M1/S1 / H1)."""
    return all(t["exploit_rate"] == 0 for t in trace)


def warning_during_or_after_hobbesian(trace):
    """True if at least one drift warning fired at round >= 30 (the
    Hobbesian phase begins at round 30) — v1.2 M2/S2."""
    return any(t["drift_warning"] for t in trace if t["round"] >= 30)


def first_drift_warning_round(trace):
    """First round with a drift warning, or None. (No criteria ambiguity:
    a drift warning either fired or it did not.)"""
    for t in sorted(trace, key=lambda x: x["round"]):
        if t["drift_warning"]:
            return t["round"]
    return None


def compute_lead_time(trace):
    """`lead_time` per v1.2 Section 4.2, using the Amendment 1 recomputed
    observable-change round. Returns an int, or one of the categorical
    strings, or None."""
    obs = recompute_first_observable_change(trace)
    warn = first_drift_warning_round(trace)
    if warn is not None and obs is not None:
        return obs - warn
    if warn is not None and obs is None:
        return "warning_no_obs_change"
    if warn is None and obs is not None:
        return "obs_change_no_warning"
    return None


def extract_seed_metrics(run):
    """All per-seed metrics needed by the threshold checks, for one run."""
    trace = sorted_trace(run)
    phases = run["phases"]
    return {
        "seed": run["seed"],
        "zero_exploiting": has_zero_exploiting(trace),
        "hobbesian_exploit_rate": phases["HOBBESIAN"]["exploit_rate"],
        "hobbesian_coop_rate": phases["HOBBESIAN"]["coop_rate"],
        "drift_warning_count": run["tier2_drift_warning_count"],
        "drift_warnings_baseline_phase": count_baseline_phase_warnings(trace),
        "drift_warnings_hobbesian_phase": count_hobbesian_phase_warnings(trace),
        "warning_post_hobbesian": warning_during_or_after_hobbesian(trace),
        "lead_time": compute_lead_time(trace),
        "recovery_time": run["tier1_recovery_time"],
        "equilibrium_stabilized": recompute_equilibrium_stabilized(trace),
        "scc_baseline": phases["BASELINE"]["mean_scc"],
        "scc_hobbesian": phases["HOBBESIAN"]["mean_scc"],
        "scc_full_recovery": phases["FULL_RECOVERY"]["mean_scc"],
    }


# ═══════════════════════════════════════════════════════════════════
# STATISTICS (stdlib implementations)
# ═══════════════════════════════════════════════════════════════════

def _phi(x):
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def mann_whitney_u(a, b):
    """Two-sided Mann-Whitney U test. Returns (U, p_two_sided).

    The returned U is U1 — the U statistic for the first sample `a` (not
    min(U1, U2)). The two-sided p-value is invariant to that choice, since
    U1 and U2 are symmetric about the same mean.

    Uses average ranks for ties and the normal approximation with the tie
    correction (appropriate at n1=n2=50). No continuity correction is
    applied; this is documented as an implementation choice.
    """
    n1, n2 = len(a), len(b)
    combined = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    # Average ranks, handling ties.
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0  # ranks are 1-based
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    r1 = sum(ranks[k] for k in range(len(combined)) if combined[k][1] == 0)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0

    # Tie correction term.
    n = n1 + n2
    i = 0
    sum_t = 0.0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        t = j - i + 1
        sum_t += t ** 3 - t
        i = j + 1
    if n < 2:
        return u1, 1.0
    sigma_sq = (n1 * n2 / 12.0) * ((n + 1) - sum_t / (n * (n - 1)))
    if sigma_sq <= 0:
        return u1, 1.0
    sigma = math.sqrt(sigma_sq)
    z = (u1 - mu) / sigma
    p = 2.0 * (1.0 - _phi(abs(z)))
    return u1, max(0.0, min(1.0, p))


def bootstrap_ci_mean(sample, resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    """95% percentile bootstrap CI for the mean. Returns (low, high)."""
    if not sample:
        return (None, None)
    rng = random.Random(seed)
    n = len(sample)
    means = []
    for _ in range(resamples):
        resample = [sample[rng.randrange(n)] for _ in range(n)]
        means.append(sum(resample) / n)
    means.sort()
    # Nearest-rank percentiles: index = ceil(p * N) - 1.
    lo = means[math.ceil(0.025 * resamples) - 1]
    hi = means[math.ceil(0.975 * resamples) - 1]
    return (lo, hi)


def cohens_d_hedges_g(a, b):
    """Cohen's d and Hedges' g (small-sample-corrected). Positive means a
    has the higher mean. Returns (d, g)."""
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return (0.0, 0.0)
    m1, m2 = statistics.mean(a), statistics.mean(b)
    v1, v2 = statistics.variance(a), statistics.variance(b)
    pooled = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    if pooled == 0:
        return (0.0, 0.0)
    d = (m1 - m2) / pooled
    j = 1.0 - 3.0 / (4.0 * (n1 + n2) - 9.0)
    return (d, d * j)


def cliffs_delta(a, b):
    """Cliff's delta: (#(a>b) - #(a<b)) / (n1*n2). Positive means a tends
    to exceed b."""
    gt = lt = 0
    for x in a:
        for y in b:
            if x > y:
                gt += 1
            elif x < y:
                lt += 1
    n = len(a) * len(b)
    return (gt - lt) / n if n else 0.0


# ═══════════════════════════════════════════════════════════════════
# THRESHOLD CHECKS
# ═══════════════════════════════════════════════════════════════════

def _check(name, passed, statistic, cutoff, detail=""):
    return {"check": name, "pass": bool(passed), "statistic": statistic,
            "cutoff": cutoff, "detail": detail}


def numeric_lead_times(metrics):
    """Lead times that are numeric (both a warning and an observable change
    occurred) — the subset M4/S4 operate over (v1.2 Section 4.2)."""
    return [m["lead_time"] for m in metrics
            if isinstance(m["lead_time"], (int, float))
            and not isinstance(m["lead_time"], bool)]


def run_threshold_checks(lemn_metrics, baseline_metrics):
    """Evaluate every pre-registered threshold check. `lemn_metrics` is the
    list of 50 Lemniscation per-seed metric dicts; `baseline_metrics` maps
    agent type -> list of 50 per-seed metric dicts.

    Returns (moderate_checks, strict_checks) — each a dict name -> _check.
    """
    n = len(lemn_metrics)
    mod, strict = {}, {}

    # ── M1 / S1 — zero-exploiting iron law ──────────────────────────
    frac_zero = sum(1 for m in lemn_metrics if m["zero_exploiting"]) / n
    mod["M1"] = _check("M1", frac_zero >= 0.95, frac_zero, ">= 0.95")
    strict["S1"] = _check("S1", frac_zero >= 1.0, frac_zero, "== 1.00")

    # ── M2 / S2 — drift detection reliability (true positives) ──────
    frac_warn = sum(1 for m in lemn_metrics
                    if m["warning_post_hobbesian"]) / n
    mod["M2"] = _check("M2", frac_warn >= 0.90, frac_warn, ">= 0.90")
    strict["S2"] = _check("S2", frac_warn >= 1.0, frac_warn, "== 1.00")

    # ── M_FP / S_FP — drift detection specificity (false positives) ─
    fp = [m["drift_warnings_baseline_phase"] for m in lemn_metrics]
    fp_median = statistics.median(fp)
    fp_mean = statistics.mean(fp)
    mod["M_FP"] = _check("M_FP_moderate", fp_median <= 1, fp_median,
                         "median <= 1")
    strict["S_FP"] = _check("S_FP_strict", fp_mean <= 0.5, fp_mean,
                            "mean <= 0.5")

    # ── M3 / S3 — drift detection consistency ───────────────────────
    dwc = [m["drift_warning_count"] for m in lemn_metrics]
    dwc_median = statistics.median(dwc)
    mod["M3"] = _check("M3", dwc_median >= 5, dwc_median, "median >= 5")
    strict["S3"] = _check("S3", dwc_median >= 10, dwc_median, "median >= 10")

    # ── M4 / S4 — lead time ─────────────────────────────────────────
    lts = numeric_lead_times(lemn_metrics)
    lt_median = statistics.median(lts) if lts else None
    mod["M4"] = _check("M4", lt_median is not None and lt_median >= 5,
                       lt_median, "median >= 5",
                       f"n_numeric={len(lts)}")
    strict["S4"] = _check("S4", lt_median is not None and lt_median >= 8,
                          lt_median, "median >= 8",
                          f"n_numeric={len(lts)}")

    # ── M5 / S5 — Hobbesian-phase exploit_rate (absolute) ───────────
    hobb_exploit = [m["hobbesian_exploit_rate"] for m in lemn_metrics]
    he_mean = statistics.mean(hobb_exploit)
    mod["M5"] = _check("M5", he_mean <= 0.01, he_mean, "mean <= 0.01")
    strict["S5"] = _check("S5", he_mean <= 0.0, he_mean, "mean == 0.000")

    # ── M6 / S6 — cooperation non-inferiority ───────────────────────
    lemn_coop = statistics.mean(m["hobbesian_coop_rate"]
                                for m in lemn_metrics)
    pool_means = {b: statistics.mean(m["hobbesian_coop_rate"]
                                     for m in baseline_metrics[b])
                  for b in COOP_POOL}
    best_b = max(pool_means, key=pool_means.get)
    best_coop = pool_means[best_b]
    mod["M6"] = _check("M6", lemn_coop >= best_coop - 0.05, lemn_coop,
                       f">= {best_coop:.4f} - 0.05  (best baseline: {best_b})")
    strict["S6"] = _check("S6", lemn_coop >= best_coop - 0.02, lemn_coop,
                          f">= {best_coop:.4f} - 0.02  (best baseline: {best_b})")

    # ── M7 / S7 — recovery time ─────────────────────────────────────
    # INTERPRETATION: "no more than 25%/10% longer than the fastest
    # baseline's mean recovery_time (computed only over seeds where both
    # Lemniscation and that baseline have non-null recovery_time)". Read
    # as: for each baseline, take the seed-intersection on which both have
    # non-null recovery_time; the "fastest baseline" is the one with the
    # smallest mean recovery_time on its own intersection; the comparison
    # uses Lemniscation's mean on that same intersection. AC is NOT
    # excluded here (the AC exclusion in Section 3.1 is scoped to M6/S6).
    m7 = _recovery_time_check(lemn_metrics, baseline_metrics, 1.25, "M7")
    s7 = _recovery_time_check(lemn_metrics, baseline_metrics, 1.10, "S7")
    mod["M7"] = m7
    strict["S7"] = s7

    # ── M7b / S7b — equilibrium establishment ───────────────────────
    frac_eq = sum(1 for m in lemn_metrics
                  if m["equilibrium_stabilized"]) / n
    mod["M7b"] = _check("M7b", frac_eq >= 0.80, frac_eq, ">= 0.80")
    strict["S7b"] = _check("S7b", frac_eq >= 1.0, frac_eq, "== 1.00")

    # ── M8 / S8 — internal consistency: SCC dynamics ────────────────
    # Per-seed: scc_BASELINE > scc_HOBBESIAN AND
    #           scc_FULL_RECOVERY >= scc_HOBBESIAN + 0.10
    scc_fail = 0
    for m in lemn_metrics:
        ok = (m["scc_baseline"] > m["scc_hobbesian"]
              and m["scc_full_recovery"] >= m["scc_hobbesian"] + 0.10)
        if not ok:
            scc_fail += 1
    fail_frac = scc_fail / n
    mod["M8"] = _check("M8", fail_frac < 0.05, fail_frac,
                       "fail fraction < 0.05", f"{scc_fail}/{n} seeds fail")
    strict["S8"] = _check("S8", scc_fail == 0, scc_fail,
                          "0 seeds fail", f"{scc_fail}/{n} seeds fail")

    return mod, strict


def _recovery_time_check(lemn_metrics, baseline_metrics, factor, name):
    """Shared logic for M7 (factor 1.25) and S7 (factor 1.10)."""
    lemn_by_seed = {m["seed"]: m["recovery_time"] for m in lemn_metrics}
    best = None  # (baseline, baseline_mean, lemn_mean, n_intersection)
    per_baseline = {}
    for b in ALL_BASELINES:
        b_by_seed = {m["seed"]: m["recovery_time"]
                     for m in baseline_metrics[b]}
        inter = [s for s in lemn_by_seed
                 if lemn_by_seed[s] is not None
                 and b_by_seed.get(s) is not None]
        if not inter:
            per_baseline[b] = {"n_intersection": 0}
            continue
        b_mean = statistics.mean(b_by_seed[s] for s in inter)
        l_mean = statistics.mean(lemn_by_seed[s] for s in inter)
        per_baseline[b] = {"n_intersection": len(inter),
                           "baseline_mean": b_mean, "lemn_mean": l_mean}
        if best is None or b_mean < best[1]:
            best = (b, b_mean, l_mean, len(inter))

    if best is None:
        return _check(name, False, None,
                      f"lemn mean <= {factor} x fastest baseline mean",
                      "NO seed-intersection with any baseline — cannot "
                      "evaluate; recorded as fail.")
    b_name, b_mean, l_mean, n_int = best
    if b_mean == 0:
        passed = l_mean <= 0
    else:
        passed = l_mean <= factor * b_mean
    return _check(
        name, passed, l_mean,
        f"<= {factor} x {b_mean:.4f}  (fastest baseline: {b_name}, "
        f"n_intersection={n_int})",
        f"per_baseline={per_baseline}")


# ═══════════════════════════════════════════════════════════════════
# SUPPORTING STATISTICS (v1.2 Section 7.1-7.2)
# ═══════════════════════════════════════════════════════════════════

def supporting_stats(lemn_metrics, baseline_metrics):
    """Bootstrap CIs, Mann-Whitney U, and effect sizes for the between-agent
    comparisons behind M6/S6 (Hobbesian coop_rate) and M7/S7
    (recovery_time). These support the threshold checks; they do not
    establish independent inferential claims (Section 7.1)."""
    out = {}

    # M6/S6: Hobbesian coop_rate, Lemniscation vs each baseline in the pool.
    lemn_coop = [m["hobbesian_coop_rate"] for m in lemn_metrics]
    coop_block = {"metric": "hobbesian_coop_rate",
                  "lemniscation_mean": statistics.mean(lemn_coop),
                  "lemniscation_ci95": bootstrap_ci_mean(lemn_coop),
                  "comparisons": {}}
    for b in COOP_POOL:
        bc = [m["hobbesian_coop_rate"] for m in baseline_metrics[b]]
        u, p = mann_whitney_u(lemn_coop, bc)
        d, g = cohens_d_hedges_g(lemn_coop, bc)
        coop_block["comparisons"][b] = {
            "baseline_mean": statistics.mean(bc),
            "baseline_ci95": bootstrap_ci_mean(bc),
            "mann_whitney_u": u, "p_two_sided": p,
            "significant_bonferroni": p < BONFERRONI_ALPHA,
            "cohens_d": d, "hedges_g": g, "cliffs_delta": cliffs_delta(lemn_coop, bc),
        }
    out["M6_S6_cooperation"] = coop_block

    # M7/S7: recovery_time, over each baseline's seed-intersection.
    lemn_by_seed = {m["seed"]: m["recovery_time"] for m in lemn_metrics}
    rec_block = {"metric": "recovery_time", "comparisons": {}}
    for b in ALL_BASELINES:
        b_by_seed = {m["seed"]: m["recovery_time"]
                     for m in baseline_metrics[b]}
        inter = [s for s in lemn_by_seed
                 if lemn_by_seed[s] is not None
                 and b_by_seed.get(s) is not None]
        if len(inter) < 2:
            rec_block["comparisons"][b] = {"n_intersection": len(inter),
                                           "note": "too few paired seeds"}
            continue
        lv = [lemn_by_seed[s] for s in inter]
        bv = [b_by_seed[s] for s in inter]
        u, p = mann_whitney_u(lv, bv)
        d, g = cohens_d_hedges_g(lv, bv)
        rec_block["comparisons"][b] = {
            "n_intersection": len(inter),
            "lemniscation_mean": statistics.mean(lv),
            "baseline_mean": statistics.mean(bv),
            "mann_whitney_u": u, "p_two_sided": p,
            "significant_bonferroni": p < BONFERRONI_ALPHA,
            "cohens_d": d, "hedges_g": g, "cliffs_delta": cliffs_delta(lv, bv),
        }
    out["M7_S7_recovery"] = rec_block
    return out


# ═══════════════════════════════════════════════════════════════════
# OUTCOME DECISION RULE (v1.2 Section 8 / "Inference criteria")
# ═══════════════════════════════════════════════════════════════════

def decide_outcome(mod, strict, lemn_metrics, baseline_metrics, support):
    """Apply the four-outcome decision rule. Returns (outcome, flags)."""
    flags = []
    strict_pass = all(c["pass"] for c in strict.values())
    moderate_pass = all(c["pass"] for c in mod.values())

    if strict_pass:
        return "A", flags
    if moderate_pass:
        return "B", flags

    # At least one moderate threshold failed -> Outcome C or D, decided by
    # the Section 8.3 diagnostic conditions. The whole 8.3 block is reached
    # only on a moderate fail; its conditions are loosely specified in the
    # registered text, so the interpretation choices below are flagged and
    # must be confirmed by human review before any Outcome C/D is final.

    # (a) v1.2 Section 8.3(a): "Lemniscation's exploit_rate is not
    # statistically indistinguishable from baseline noise" — the wording is
    # ambiguous (apparent double negative). Implemented as: Lemniscation's
    # mean Hobbesian exploit_rate is at or below the mean of the baselines'.
    # NOTE: no significance test is applied here, despite the word
    # "statistically" in the registered text — see flag.
    flags.append(
        "Section 8.3(a): registered wording is ambiguous (apparent double "
        "negative). Implemented as 'Lemniscation mean Hobbesian exploit_rate "
        "<= mean baseline Hobbesian exploit_rate', with NO significance test "
        "despite the word 'statistically'. Requires human confirmation.")
    flags.append(
        "Section 8.3(b): implemented as a literal warning-COUNT comparison "
        "(BASELINE phase = 10 rounds vs HOBBESIAN phase = 30 rounds) via "
        "two-sided Mann-Whitney U at p<0.05. The unequal phase lengths make "
        "this a weak specificity test as literally written. Requires human "
        "confirmation.")

    lemn_he = statistics.mean(m["hobbesian_exploit_rate"]
                              for m in lemn_metrics)
    all_baseline_he = []
    for b in ALL_BASELINES:
        all_baseline_he += [m["hobbesian_exploit_rate"]
                            for m in baseline_metrics[b]]
    baseline_he_mean = statistics.mean(all_baseline_he)
    cond_a = lemn_he <= baseline_he_mean  # not exploiting more than baselines

    # (b) v1.2 Section 8.3(b): "at least some drift warnings fire in at
    # least 50% of seeds with acceptable specificity (BASELINE-phase warning
    # count not significantly higher than HOBBESIAN-phase warning count)".
    n = len(lemn_metrics)
    frac_any_warn = sum(1 for m in lemn_metrics
                        if m["drift_warning_count"] >= 1) / n
    base_counts = [m["drift_warnings_baseline_phase"] for m in lemn_metrics]
    hobb_counts = [m["drift_warnings_hobbesian_phase"] for m in lemn_metrics]
    _, p_spec = mann_whitney_u(base_counts, hobb_counts)
    baseline_significantly_higher = (
        statistics.mean(base_counts) > statistics.mean(hobb_counts)
        and p_spec < 0.05)
    cond_b = frac_any_warn >= 0.50 and not baseline_significantly_higher

    # (c) at least one comparison is significant (Bonferroni) in a
    # claim-consistent direction. Checked against the supporting stats.
    cond_c = False
    for b, comp in support["M6_S6_cooperation"]["comparisons"].items():
        if comp["significant_bonferroni"] and comp["cohens_d"] > 0:
            cond_c = True
    if cond_a and cond_b and cond_c:
        return "C", flags
    return "D", flags


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Step 1 baseline comparison analysis.")
    parser.add_argument("--input", default="baseline_comparison_v1_results.json")
    parser.add_argument("--output", default="baseline_analysis_v1_results.json")
    args = parser.parse_args()

    results, meta = load_results(args.input)

    lemn_metrics = [extract_seed_metrics(r) for r in results[PROTAGONIST]]
    baseline_metrics = {b: [extract_seed_metrics(r) for r in results[b]]
                        for b in ALL_BASELINES}

    mod, strict = run_threshold_checks(lemn_metrics, baseline_metrics)
    support = supporting_stats(lemn_metrics, baseline_metrics)
    outcome, flags = decide_outcome(mod, strict, lemn_metrics,
                                    baseline_metrics, support)

    strict_pass = all(c["pass"] for c in strict.values())
    moderate_pass = all(c["pass"] for c in mod.values())

    report = {
        "analysis_meta": {
            "input_file": args.input,
            "harness_git_hash": meta.get("harness_git_hash"),
            "admissibility_gate": "passed",
            "n_seeds": N_SEEDS,
            "amendment": "pre_registration_step1_amendment1.md",
        },
        "moderate_checks": mod,
        "strict_checks": strict,
        "moderate_pass": moderate_pass,
        "strict_pass": strict_pass,
        "supporting_stats": support,
        "outcome": outcome,
        "interpretation_flags": flags,
    }

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    # ── Human-readable report ───────────────────────────────────────
    print("=" * 72)
    print("  LEMNISCATION STEP 1 — BASELINE COMPARISON ANALYSIS")
    print("=" * 72)
    print(f"  harness_git_hash verified: {meta.get('harness_git_hash')}")
    print(f"  seeds: {N_SEEDS}   admissibility gate: PASSED")
    print("-" * 72)
    print("  MODERATE THRESHOLDS")
    for k, c in mod.items():
        mark = "PASS" if c["pass"] else "FAIL"
        print(f"   [{mark}] {c['check']:18s} stat={c['statistic']}  "
              f"cutoff: {c['cutoff']}")
    print(f"  -> moderate_pass = {moderate_pass}")
    print("-" * 72)
    print("  STRICT THRESHOLDS")
    for k, c in strict.items():
        mark = "PASS" if c["pass"] else "FAIL"
        print(f"   [{mark}] {c['check']:18s} stat={c['statistic']}  "
              f"cutoff: {c['cutoff']}")
    print(f"  -> strict_pass = {strict_pass}")
    print("-" * 72)
    print(f"  OUTCOME: {outcome}")
    if flags:
        print("  INTERPRETATION FLAGS:")
        for fl in flags:
            print(f"    - {fl}")
    print("=" * 72)
    print(f"  full report written to {args.output}")


if __name__ == "__main__":
    main()
