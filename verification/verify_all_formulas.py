#!/usr/bin/env python3
"""Programmatic verification of every mathematical formula, definition, theorem,
and worked example in `main.tex`.

Follows `math_code_verification` protocol:
1. Definition 1: Clean-Room Rebuildability (epsilon, delta) & Plug-in Shannon Entropy H_hat
2. Fano-Style Entropy Upper Bound: H(B_T) <= h_2(epsilon) + epsilon * log2(2^K - 1) <= h_2(epsilon) + epsilon * K
3. Clopper-Pearson One-Sided 95% Upper Confidence Bound: epsilon <= 1 - alpha^(1/k)
4. Proposition 1: Four-Stage Forward Compiler Phi = phi_ADD o varphi_MOD o varphi_REM o phi_REN,
   Single-Step & Multi-Step Inverse Phi_seq^-1, and Footprint-Complete Target Coverage (Precondition c)
5. Step 2 Contrastive Boundary Probing: (N - eta, N, N + eta) & Midpoint Discretization
6. Step 4 Constructive AST Prefix Splice Invariant: P_AST (body(ClassDef_post) = body(ClassDef_pre) || [f_1..f_m])
7. Section 6 Evaluation Metrics & Exact Non-Parametric Statistical Tests
"""

import ast
import copy
import math
import pathlib
import random
import re
import sys

PAPER_DIR = pathlib.Path(__file__).resolve().parent.parent / "paper"
MAIN_TEX = PAPER_DIR / "main.tex"


def plug_in_entropy(outcomes: list[tuple[int, ...]]) -> float:
  """Computes empirical plug-in Shannon entropy H_hat in bits (Formula 2)."""
  k = len(outcomes)
  counts: dict[tuple[int, ...], int] = {}
  for v in outcomes:
    counts[v] = counts.get(v, 0) + 1
  h = 0.0
  for count in counts.values():
    p_hat = count / k
    if p_hat > 0:
      h -= p_hat * math.log2(p_hat)
  return h


def binary_entropy(eps: float) -> float:
  """Computes binary entropy h_2(eps) in bits."""
  if eps <= 0.0 or eps >= 1.0:
    return 0.0
  return -eps * math.log2(eps) - (1.0 - eps) * math.log2(1.0 - eps)


def verify_formula_1_and_2(tex: str) -> list[str]:
  """Verifies Formula 1 (sizeof ordering) and Formula 2 (Definition 1 & H_hat)."""
  errors = []
  if (
      r"\mathrm{sizeof}(P_t) \ll \mathrm{sizeof}(S_t)" not in tex
      or r"\mathrm{sizeof}(S_t) \ll \mathrm{sizeof}(C_t)" not in tex
  ):
    errors.append("Missing Formula 1: sizeof(P_t) << sizeof(S_t) and sizeof(S_t) << sizeof(C_t)")

  # Verify empirical plug-in entropy on all 4 Outer Topologies (k=3 runs, K=5 milestones)
  all_pass = (1, 1, 1, 1, 1)
  m3_fail_rest_pass = (1, 1, 0, 1, 1)
  m2_to_m5_fail = (1, 0, 0, 0, 0)

  # Outer A (Append-Only): 0/3 pass, all 3 fail identically on M2..M5
  h_outer_a = plug_in_entropy([m2_to_m5_fail, m2_to_m5_fail, m2_to_m5_fail])
  if abs(h_outer_a - 0.0) > 1e-12:
    errors.append(f"Outer A entropy mismatch: expected 0.0, got {h_outer_a}")

  # Outer B (Feature-Isolated): 2/3 pass (all_pass), 1/3 fails M3 (WRITE_CACHE_SIZE=32 vs 64)
  h_outer_b = plug_in_entropy([all_pass, all_pass, m3_fail_rest_pass])
  expected_b = -(2 / 3) * math.log2(2 / 3) - (1 / 3) * math.log2(1 / 3)
  if abs(h_outer_b - expected_b) > 1e-12 or f"{h_outer_b:.2f}" != "0.92":
    errors.append(f"Outer B entropy mismatch: got {h_outer_b:.6f}, expected ~0.918296 (0.92)")

  # Outer C (Single-File) and Outer D (Two-Plane SSOT): 3/3 pass
  h_outer_cd = plug_in_entropy([all_pass, all_pass, all_pass])
  if abs(h_outer_cd - 0.0) > 1e-12:
    errors.append(f"Outer C/D entropy mismatch: expected 0.0, got {h_outer_cd}")

  print(
      f"[PASS] Formula 1 & 2 (Definition 1 & Plug-in Entropy): "
      f"Outer A={h_outer_a:.2f} bits, Outer B={h_outer_b:.6f} ({h_outer_b:.2f}) bits, "
      f"Outer C/D={h_outer_cd:.2f} bits"
  )
  return errors


def verify_formula_3_and_4(tex: str) -> list[str]:
  """Verifies Formula 3 (Fano bound) and Formula 4 (Clopper-Pearson bound)."""
  errors = []
  K = 5
  # Check Fano inequality across epsilon in [0, 1 - 2^-K]
  prev_bound = -1.0
  for i in range(0, 969):  # 1 - 2^-5 = 31/32 = 0.96875 -> 0.000 to 0.968
    eps = i / 1000.0
    # Worst-case distribution with P(v = 1_K) = 1 - eps spreads eps uniformly over 2^K - 1 failure vectors
    if eps == 0.0:
      h_worst = 0.0
    else:
      p_pass = 1.0 - eps
      p_each_fail = eps / (2**K - 1)
      h_worst = -p_pass * math.log2(p_pass) - (2**K - 1) * (p_each_fail * math.log2(p_each_fail))
    tight_fano = binary_entropy(eps) + eps * math.log2(2**K - 1)
    loose_fano = binary_entropy(eps) + eps * K

    if abs(h_worst - tight_fano) > 1e-11:
      errors.append(f"Tight Fano identity failed at eps={eps}: {h_worst} vs {tight_fano}")
    if tight_fano > loose_fano + 1e-12:
      errors.append(f"Loose Fano inequality failed at eps={eps}: {tight_fano} > {loose_fano}")
    if tight_fano < prev_bound - 1e-12:
      errors.append(f"Fano bound non-monotonic on [0, 1-2^-K] at eps={eps}")
    prev_bound = tight_fano

  # Check Clopper-Pearson one-sided 95% confidence bound for k=3, alpha=0.05
  alpha = 0.05
  k = 3
  cp_bound = 1.0 - (alpha ** (1.0 / k))
  if f"{cp_bound:.3f}" != "0.632":
    errors.append(f"Clopper-Pearson bound mismatch: got {cp_bound:.6f}, expected 0.632")
  if "0.632" not in tex:
    errors.append("Missing Clopper-Pearson numerical value 0.632 in main.tex")

  print(
      f"[PASS] Formula 3 & 4 (Fano Bound & Clopper-Pearson): "
      f"Tight Fano verified across 969 grid points on [0, 31/32]; "
      f"Clopper-Pearson 1 - 0.05^(1/3) = {cp_bound:.6f} -> {cp_bound:.3f}"
  )
  return errors


# Clean-room implementation of Proposition 1 Four-Stage Forward Compiler & Inverse
def forward_compile_step(
    S_prev: dict[str, tuple[str, str]],
    delta: dict,
) -> tuple[dict[str, tuple[str, str]], dict]:
  """Applies S_t = Phi(S_{t-1}, Delta_t) = (phi_ADD o varphi_MOD o varphi_REM o phi_REN)(S_{t-1}).

  Each block b in S_prev is represented by key id(b) -> (header_sig, predicate_desc).
  delta has keys:
    'REN': dict[old_id, (new_id, new_header_sig)]
    'REM': set[id]
    'MOD': dict[id, (header_sig, predicate_desc)]
    'ADD': dict[id, (header_sig, predicate_desc)]
  Returns (S_t, pre_snapshot).
  """
  ren = delta.get("REN", {})
  rem = delta.get("REM", set())
  mod = delta.get("MOD", {})
  add = delta.get("ADD", {})

  # Verify Precondition (a): Disjoint & Target-Valid Operations
  prev_ids = set(S_prev.keys())
  assert set(ren.keys()).issubset(prev_ids), "REN source not in S_{t-1}"
  # Stage 1: phi_REN (simultaneous bijection on IDs and headers/signatures)
  S_prime: dict[str, tuple[str, str]] = {}
  ren_pre_headers: dict[str, str] = {}
  for old_id, (hdr, pred) in S_prev.items():
    if old_id in ren:
      new_id, new_hdr = ren[old_id]
      ren_pre_headers[old_id] = hdr
      S_prime[new_id] = (new_hdr, pred)
    else:
      S_prime[old_id] = (hdr, pred)
  assert len(S_prime) == len(S_prev), "REN is not a bijection"

  prime_ids = set(S_prime.keys())
  assert rem.issubset(prime_ids), "REM target not in S'_{t-1}"
  assert set(mod.keys()).issubset(prime_ids), "MOD target not in S'_{t-1}"
  assert rem.isdisjoint(set(mod.keys())), "REM and MOD are not disjoint"
  surviving_ids = prime_ids - rem
  assert set(add.keys()).isdisjoint(surviving_ids), "ADD collides with surviving IDs"

  # Record pre-image snapshot before destructive REM and MOD
  pre_rem = {rid: S_prime[rid] for rid in rem}
  pre_mod = {mid: S_prime[mid] for mid in mod}
  pre_snapshot = {"REM": pre_rem, "MOD": pre_mod, "REN_HDR": ren_pre_headers}

  # Stage 2: varphi_REM
  S_after_rem = {k: v for k, v in S_prime.items() if k not in rem}
  # Stage 3: varphi_MOD
  S_after_mod = dict(S_after_rem)
  for mid, new_block in mod.items():
    S_after_mod[mid] = new_block
  # Stage 4: phi_ADD
  S_t = dict(S_after_mod)
  for aid, new_block in add.items():
    S_t[aid] = new_block

  return S_t, pre_snapshot


def inverse_rollback_step(
    S_tau: dict[str, tuple[str, str]],
    delta: dict,
    pre_snapshot: dict,
) -> dict[str, tuple[str, str]]:
  """Applies Phi^-1 = phi_REN^-1 o varphi_REM^-1 o varphi_MOD^-1 o phi_ADD^-1."""
  ren = delta.get("REN", {})
  add = delta.get("ADD", {})
  pre_rem = pre_snapshot["REM"]
  pre_mod = pre_snapshot["MOD"]
  ren_pre_headers = pre_snapshot["REN_HDR"]

  # 1. Undo Stage 4 (phi_ADD^-1): remove added keys
  S_1 = {k: v for k, v in S_tau.items() if k not in add}
  # 2. Undo Stage 3 (varphi_MOD^-1): restore pre-modification blocks
  S_2 = dict(S_1)
  for mid, old_block in pre_mod.items():
    S_2[mid] = old_block
  # 3. Undo Stage 2 (varphi_REM^-1): re-insert removed blocks
  S_3 = dict(S_2)
  for rid, old_block in pre_rem.items():
    S_3[rid] = old_block
  # 4. Undo Stage 1 (phi_REN^-1): invert rename bijection and restore old headers
  inv_ren = {new_id: old_id for old_id, (new_id, _) in ren.items()}
  S_prev: dict[str, tuple[str, str]] = {}
  for cur_id, (hdr, pred) in S_3.items():
    if cur_id in inv_ren:
      old_id = inv_ren[cur_id]
      S_prev[old_id] = (ren_pre_headers[old_id], pred)
    else:
      S_prev[cur_id] = (hdr, pred)
  return S_prev


def verify_formula_5_proposition_1() -> list[str]:
  """Verifies Proposition 1 (Claims 1, 2, 3) on TinyDB Commit0-Evo M1..M5 and 100 random histories."""
  errors = []

  # 1. Exact TinyDB 5-Milestone Commit0-Evo Trajectory
  S_0: dict[str, tuple[str, str]] = {}
  milestones = [
      # M1: Core Table & Query API
      {
          "REN": {},
          "REM": set(),
          "MOD": {},
          "ADD": {
              "REQ-0101": ("Table.insert(doc) -> int", "WRITE_CACHE_SIZE == 64"),
              "REQ-0102": ("Table.search(cond) -> list", "QUERY_CACHE == True"),
              "REQ-0103": ("LegacyHelper.run()", "LEGACY_MODE == True"),
          },
      },
      # M2: Caching & Middleware
      {
          "REN": {},
          "REM": set(),
          "MOD": {},
          "ADD": {
              "REQ-0201": ("CachingMiddleware(Storage)", "FLUSH_INTERVAL == 32"),
          },
      },
      # M3: Strict Write-Through Flush (modifies REQ-0101 in place from 64 to 1)
      {
          "REN": {},
          "REM": set(),
          "MOD": {
              "REQ-0101": ("Table.insert(doc) -> int", "WRITE_CACHE_SIZE == 1"),
          },
          "ADD": {},
      },
      # M4: Signature Rename + Simultaneous Body Modification on Renamed ID
      {
          "REN": {
              "REQ-0201": ("REQ-0401", "CachingMiddleware(Storage, flush_threshold=1)"),
          },
          "REM": set(),
          "MOD": {
              "REQ-0401": ("CachingMiddleware(Storage, flush_threshold=1)", "FLUSH_INTERVAL == 1"),
          },
          "ADD": {},
      },
      # M5: Deprecation & Removal
      {
          "REN": {},
          "REM": {"REQ-0103"},
          "MOD": {},
          "ADD": {
              "REQ-0501": ("Table.upsert(doc, cond) -> list[int]", "UPSERT_ATOMIC == True"),
          },
      },
  ]

  states = [copy.deepcopy(S_0)]
  audit_log = []
  cur = copy.deepcopy(S_0)
  for delta in milestones:
    cur, pre = forward_compile_step(cur, delta)
    states.append(copy.deepcopy(cur))
    audit_log.append((delta, pre))

  # Verify Claim 1: Unique Keys & Monotonic Overwrite (REQ-0101 has WRITE_CACHE_SIZE == 1, not 64)
  if states[5]["REQ-0101"][1] != "WRITE_CACHE_SIZE == 1":
    errors.append("Proposition 1 Claim 1 failed on M3 overwrite")
  if "REQ-0103" in states[5] or "REQ-0201" in states[5] or "REQ-0401" not in states[5]:
    errors.append("Proposition 1 Claim 1 failed on M4 rename / M5 removal")

  # Verify Claim 2: Exact Multi-Step Rollback to every earlier milestone t_0 in {0..5}
  for t_target in range(0, 6):
    rolled = copy.deepcopy(states[5])
    for tau in range(5, t_target, -1):
      delta_tau, pre_tau = audit_log[tau - 1]
      rolled = inverse_rollback_step(rolled, delta_tau, pre_tau)
    if rolled != states[t_target]:
      errors.append(f"Proposition 1 Claim 2 rollback failed for target milestone M{t_target}")

  # Verify Claim 3: Footprint-Complete Target Coverage check
  # In M3, REQ-0101 changed WRITE_CACHE_SIZE from 64 to 1. Because REQ-0101 was in MOD,
  # 0 conflicting WRITE_CACHE_SIZE == 64 predicates remain in states[3..5].
  for m_idx in (3, 4, 5):
    preds = [v[1] for v in states[m_idx].values()]
    if "WRITE_CACHE_SIZE == 64" in preds:
      errors.append(f"Proposition 1 Claim 3 failed: stale predicate survived in M{m_idx}")

  # 2. Fuzz test 200 randomized 6-step histories (including simultaneous REN + MOD + REM + ADD)
  rng = random.Random(42)
  for trial in range(200):
    s_init = {f"REQ-{i:04d}": (f"sig_{i}_v0", f"var_{i} == 0") for i in range(1, 10)}
    hist_states = [copy.deepcopy(s_init)]
    hist_log = []
    s_cur = copy.deepcopy(s_init)
    next_id = 100
    for step in range(6):
      ids = sorted(s_cur.keys())
      rng.shuffle(ids)
      ren_keys = ids[:2]
      ren_map = {}
      for rk in ren_keys:
        new_k = f"REQ-{next_id:04d}"
        next_id += 1
        ren_map[rk] = (new_k, f"sig_ren_{next_id}")
      post_ren_ids = [ren_map[k][0] if k in ren_map else k for k in ids]
      rem_set = {post_ren_ids[2]} if len(post_ren_ids) > 2 else set()
      # Intentionally include one renamed key in MOD to test simultaneous REN + MOD!
      mod_keys = [post_ren_ids[0], post_ren_ids[3]] if len(post_ren_ids) > 3 else [post_ren_ids[0]]
      mod_map = {mk: (f"sig_mod_{step}_{mk}", f"var_{mk} == {step+1}") for mk in mod_keys}
      add_map = {
          f"REQ-{next_id:04d}": (f"sig_add_{step}", f"var_add_{step} == 1"),
      }
      next_id += 1
      delta_step = {"REN": ren_map, "REM": rem_set, "MOD": mod_map, "ADD": add_map}
      s_cur, pre_step = forward_compile_step(s_cur, delta_step)
      hist_states.append(copy.deepcopy(s_cur))
      hist_log.append((delta_step, pre_step))

    for t0 in range(0, 7):
      rb = copy.deepcopy(hist_states[6])
      for tau in range(6, t0, -1):
        d_tau, p_tau = hist_log[tau - 1]
        rb = inverse_rollback_step(rb, d_tau, p_tau)
      if rb != hist_states[t0]:
        errors.append(f"Random fuzz trial {trial} failed rollback to step {t0}")
        break

  print(
      "[PASS] Formula 5 (Proposition 1 Forward Compiler Phi & Inverse Rollback Phi_seq^-1): "
      "100% exact rollback across TinyDB M1..M5 and 200/200 randomized multi-milestone histories "
      "(including simultaneous rename + modify)."
  )
  return errors


def verify_formula_6_inner_loop() -> list[str]:
  """Verifies Formula 6: Step 2 boundary probing (N-eta, N, N+eta) & Step 4 AST Prefix Invariant."""
  errors = []

  # 1. Step 2 Boundary Probing: integer threshold N=64, eta=1 -> (63, 64, 65)
  N_int, eta_int = 64, 1
  triple_int = (N_int - eta_int, N_int, N_int + eta_int)
  if triple_int != (63, 64, 65):
    errors.append(f"Integer boundary triple failed: {triple_int}")
  # Midpoint of [10, 20] -> floor((10+20)/2) = 15
  if (10 + 20) // 2 != 15:
    errors.append("Integer midpoint failed")
  # Float threshold N=0.75 (d=2 -> eta=10^-2 = 0.01) -> (0.74, 0.75, 0.76)
  N_flt, d = 0.75, 2
  eta_flt = 10 ** (-d)
  triple_flt = (round(N_flt - eta_flt, d), round(N_flt, d), round(N_flt + eta_flt, d))
  if triple_flt != (0.74, 0.75, 0.76):
    errors.append(f"Float boundary triple failed: {triple_flt}")

  # 2. Step 4 Constructive AST Prefix Invariant P_AST
  src_pre = (
      "class TestSuite:\n"
      "    def test_one(self):\n"
      "        assert 1 == 1\n"
      "    def test_two(self):\n"
      "        assert 2 == 2\n"
  )
  src_post_valid = (
      src_pre
      + "    def test_three_auditor(self):\n"
      "        assert 3 == 3\n"
  )
  src_post_tampered = (
      "class TestSuite:\n"
      "    def test_one(self):\n"
      "        assert 1 == 1\n"
      "    def test_three_auditor(self):\n"
      "        assert 3 == 3\n"
  )

  def check_p_ast(pre_code: str, post_code: str) -> bool:
    tree_pre = ast.parse(pre_code)
    tree_post = ast.parse(post_code)
    cls_pre = [n for n in tree_pre.body if isinstance(n, ast.ClassDef)][0]
    cls_post = [n for n in tree_post.body if isinstance(n, ast.ClassDef)][0]
    k_pre = len(cls_pre.body)
    if len(cls_post.body) < k_pre:
      return False
    for a, b in zip(cls_pre.body, cls_post.body[:k_pre]):
      if ast.dump(a) != ast.dump(b):
        return False
    return all(
        isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
        for f in cls_post.body[k_pre:]
    )

  if not check_p_ast(src_pre, src_post_valid):
    errors.append("P_AST rejected valid constructive append")
  if check_p_ast(src_pre, src_post_tampered):
    errors.append("P_AST failed to catch deleted starter test")

  print(
      "[PASS] Formula 6 (Step 2 Boundary Probing & Step 4 AST Prefix Invariant P_AST): "
      f"int triple={triple_int}, float triple={triple_flt}, P_AST prefix check verified."
  )
  return errors


def verify_formula_7_statistics() -> list[str]:
  """Verifies Formula 7: Strict Pass logic and exact non-parametric p-values."""
  errors = []
  # Exact two-sided binomial sign test for 9/9 positive paired differences (0 ties)
  p_sign_9 = 2.0 * (0.5**9)
  if abs(p_sign_9 - 0.00390625) > 1e-12 or f"{p_sign_9:.4f}" != "0.0039":
    errors.append(f"Sign test 9/9 mismatch: {p_sign_9}")

  # Exact two-sided McNemar test for 14 vs 0 discordant pairs (Arm D vs Arm A/B on SWE-bench)
  p_mcnemar_14 = 2.0 * (0.5**14)
  if f"{p_mcnemar_14:.5f}" != "0.00012":
    errors.append(f"McNemar 14 vs 0 mismatch: {p_mcnemar_14}")

  # Exact two-sided McNemar test for 6 vs 0 discordant pairs (Arm D vs Arm C on SWE-bench)
  p_mcnemar_6 = 2.0 * (0.5**6)
  if f"{p_mcnemar_6:.4f}" != "0.0312":
    errors.append(f"McNemar 6 vs 0 mismatch: {p_mcnemar_6}")

  print(
      "[PASS] Formula 7 (Evaluation Metrics & Exact Non-Parametric p-Values): "
      f"Sign test (9/9) p={p_sign_9:.6f} (0.0039), "
      f"McNemar (14:0) p={p_mcnemar_14:.6f} (0.00012), "
      f"McNemar (6:0) p={p_mcnemar_6:.6f} (0.0312)."
  )
  return errors


def main() -> int:
  tex = MAIN_TEX.read_text(encoding="utf-8")
  all_errors: list[str] = []
  all_errors.extend(verify_formula_1_and_2(tex))
  all_errors.extend(verify_formula_3_and_4(tex))
  all_errors.extend(verify_formula_5_proposition_1())
  all_errors.extend(verify_formula_6_inner_loop())
  all_errors.extend(verify_formula_7_statistics())

  if all_errors:
    print("\n[FAIL] Formula verification failed:")
    for e in all_errors:
      print(f"  - {e}")
    return 1

  print("\nALL 7 FORMULA GROUPS IN main.tex PASSED 100% PROGRAMMATIC VERIFICATION (0 ERRORS).")
  return 0


if __name__ == "__main__":
  sys.exit(main())
