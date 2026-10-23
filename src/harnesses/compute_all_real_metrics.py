import glob
import json
import os
import re
import statistics
import subprocess
from grade_all_runs import grade_inner_loops, STAGE_ROOT, MANIFEST

BRAIN_ROOT = "$HOME/.gemini/agent_runtime/brain"
TASK_LOGS_DIR = os.path.join(BRAIN_ROOT, "e38ccc83-d09a-4685-bd8d-6f7100663bab", ".system_generated", "tasks")

def extract_real_steps_from_transcripts():
    """Parses task-*.log files to map (run_idx, arm, task_id) -> total PLANNER_RESPONSE steps across Builder + Auditor + Repair."""
    # Example log line:
    # - [agent:self] R1 ARM_A sympy__sympy-24661: done (61c1fd4e-fee4-40d1-974c-8d5a3aeb48d3): ...
    # - [agent:self] R1 ARM_D Builder sympy__sympy-24661: done (5e40d4b5-2bae-477e-9884-8b5eea5fda0c): ...
    # - [agent:self] R1 ARM_D ColdAuditor sympy__sympy-24661: done (558b4d5a-2a70-4570-8a87-047d1b96c44e): ...
    pat = re.compile(r"\[agent:self\] R(\d+)\s+(ARM_[ABCD])(?:\s+(Builder|ColdAuditor|Repair))?\s+([^\s:]+):\s+done\s+\(([0-9a-f\-]{36})\)")
    conv_map = {}  # (run_idx, arm_lower, role_tag, task_id) -> conv_id
    for log_path in sorted(glob.glob(os.path.join(TASK_LOGS_DIR, "task-*.log"))):
        try:
            with open(log_path, "r", errors="ignore") as f:
                for line in f:
                    m = pat.search(line)
                    if m:
                        r_idx = int(m.group(1))
                        arm_l = m.group(2).lower()
                        role_tag = m.group(3) or "single"
                        tid = m.group(4)
                        cid = m.group(5)
                        conv_map[(r_idx, arm_l, role_tag, tid)] = cid
        except Exception:
            pass

    def count_planner_steps(cid):
        t_path = os.path.join(BRAIN_ROOT, cid, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(t_path):
            return 0
        cnt = 0
        try:
            with open(t_path, "r", errors="ignore") as f:
                for ln in f:
                    if '"PLANNER_RESPONSE"' in ln:
                        cnt += 1
        except Exception:
            pass
        return cnt

    step_totals = {}
    for (r_idx, arm_l, role_tag, tid), cid in conv_map.items():
        s = count_planner_steps(cid)
        if s > 0:
            key = (r_idx, arm_l, tid)
            step_totals.setdefault(key, {})[role_tag] = s

    final_steps = {}
    for key, role_dict in step_totals.items():
        final_steps[key] = sum(role_dict.values())
    return final_steps


def load_fixed_workflow_meta():
    """Loads builder/auditor/repair metadata from workflow_results_<suite>_run<r>.json."""
    meta = {}
    pat = re.compile(r"^workflow_results_(.+)_run(\d+)\.json$")
    for fn in sorted(os.listdir(STAGE_ROOT)):
        m = pat.match(fn)
        if not m:
            continue
        suite = m.group(1)
        run_idx = int(m.group(2))
        path = os.path.join(STAGE_ROOT, fn)
        try:
            with open(path) as f:
                data = json.load(f)
            for item in data:
                key = (run_idx, item.get("arm"), suite, item.get("task_id"))
                meta[key] = item
        except Exception:
            pass
    return meta


def evaluate_all():
    real_steps = extract_real_steps_from_transcripts()
    wf_meta = load_fixed_workflow_meta()
    records = grade_inner_loops(runs=(1, 2, 3), only_completed_workflows=True)

    # Enrich records with real transcript steps and exact workflow self_reported_pass
    for rec in records:
        r_idx = rec["run"]
        arm = rec["arm"]
        suite = rec["suite"]
        tid = rec["task_id"]
        m = wf_meta.get((r_idx, arm, suite, tid), {})
        if arm == "arm_d":
            b = m.get("builder") or {}
            a = m.get("auditor") or {}
            rep = m.get("repair") or {}
            if rep and isinstance(rep, dict) and "tests_passed_locally" in rep:
                self_pass = bool(rep["tests_passed_locally"])
            elif isinstance(a, dict) and a.get("verdict") == "APPROVE":
                self_pass = bool(b.get("tests_passed_locally", True))
            elif isinstance(a, dict) and a.get("verdict") == "REJECT":
                self_pass = False
            else:
                self_pass = bool(b.get("tests_passed_locally", rec["oracle_pass"]))
        else:
            b = m.get("builder") or {}
            self_pass = bool(b.get("tests_passed_locally", True))

        rec["self_reported_pass"] = self_pass
        rec["false_completion"] = (self_pass and not rec["oracle_pass"])
        st = real_steps.get((r_idx, arm, tid))
        if st:
            rec["steps"] = st

    # Check outer loop results
    oracle_outer = os.path.join(STAGE_ROOT, "privilege_dir", "outer_loop_evo", "oracle_m1_to_m5.py")
    outer_records = []
    for r_idx in (1, 2, 3):
        for o_arm in ("outer_a", "outer_b", "outer_c", "outer_d"):
            ws = os.path.join(STAGE_ROOT, "outer_trials", f"run_{r_idx}", o_arm)
            res = subprocess.run(["python3", oracle_outer, ws], capture_output=True, text=True, timeout=15)
            try:
                m_res = json.loads(res.stdout.strip())
            except Exception:
                m_res = {}
            outer_records.append({
                "run": r_idx,
                "outer_arm": o_arm,
                "M1": bool(m_res.get("M1")),
                "M2": bool(m_res.get("M2")),
                "M3": bool(m_res.get("M3")),
                "M4_reverted": bool(m_res.get("M4_reverted")),
                "M5": bool(m_res.get("M5")),
            })

    out_summary = {
        "inner_records": records,
        "outer_records": outer_records,
    }
    out_path = os.path.join(STAGE_ROOT, "full_benchmark_summary.json")
    with open(out_path, "w") as f:
        json.dump(out_summary, f, indent=2)

    print("=== INNER-LOOP 3-RUN AGGREGATE BY SUITE & ARM (MEAN +/- SD) ===")
    for suite in ["swebench_verified", "commit0", "bigcodebench", "evalplus"]:
        print(f"\n--- Suite: {suite} ---")
        for arm in ["arm_a", "arm_b", "arm_c", "arm_d"]:
            run_ops, run_sps, run_fcs, run_tms, run_mks, run_sts = [], [], [], [], [], []
            for r_idx in (1, 2, 3):
                sub = [x for x in records if x["suite"] == suite and x["arm"] == arm and x["run"] == r_idx]
                if not sub:
                    continue
                n = len(sub)
                run_ops.append(sum(1 for x in sub if x["oracle_pass"]) / n * 100.0)
                run_sps.append(sum(1 for x in sub if x["self_reported_pass"]) / n * 100.0)
                run_fcs.append(sum(1 for x in sub if x["false_completion"]) / n * 100.0)
                run_tms.append(sum(1 for x in sub if x["tampered"]) / n * 100.0)
                run_mks.append(statistics.mean(x["mutation_score"] for x in sub))
                run_sts.append(statistics.mean(x["steps"] for x in sub))
            print(
                f"  {arm:6s} | Oracle={statistics.mean(run_ops):5.1f}±{statistics.stdev(run_ops):4.1f}% | "
                f"Self={statistics.mean(run_sps):5.1f}% | FalseComp={statistics.mean(run_fcs):4.1f}% | "
                f"Tamper={statistics.mean(run_tms):4.1f}±{statistics.stdev(run_tms):4.1f}% | "
                f"MutKill={statistics.mean(run_mks):5.1f}±{statistics.stdev(run_mks):4.1f}% | "
                f"Steps={statistics.mean(run_sts):4.1f}±{statistics.stdev(run_sts):3.1f}"
            )

    print("\n=== OVERALL 240-TRIAL AGGREGATE ACROSS ALL 4 SUITES (MEAN +/- SD ACROSS 3 RUNS) ===")
    for arm in ["arm_a", "arm_b", "arm_c", "arm_d"]:
        run_ops, run_sps, run_fcs, run_tms, run_mks, run_sts = [], [], [], [], [], []
        for r_idx in (1, 2, 3):
            sub = [x for x in records if x["arm"] == arm and x["run"] == r_idx]
            n = len(sub)
            run_ops.append(sum(1 for x in sub if x["oracle_pass"]) / n * 100.0)
            run_sps.append(sum(1 for x in sub if x["self_reported_pass"]) / n * 100.0)
            run_fcs.append(sum(1 for x in sub if x["false_completion"]) / n * 100.0)
            run_tms.append(sum(1 for x in sub if x["tampered"]) / n * 100.0)
            run_mks.append(statistics.mean(x["mutation_score"] for x in sub))
            run_sts.append(statistics.mean(x["steps"] for x in sub))
        print(
            f"  {arm:6s} | Oracle={statistics.mean(run_ops):5.1f}±{statistics.stdev(run_ops):4.1f}% | "
            f"Self={statistics.mean(run_sps):5.1f}±{statistics.stdev(run_sps):4.1f}% | "
            f"FalseComp={statistics.mean(run_fcs):4.1f}±{statistics.stdev(run_fcs):4.1f}% | "
            f"Tamper={statistics.mean(run_tms):4.1f}±{statistics.stdev(run_tms):4.1f}% | "
            f"MutKill={statistics.mean(run_mks):5.1f}±{statistics.stdev(run_mks):4.1f}% | "
            f"Steps={statistics.mean(run_sts):4.1f}±{statistics.stdev(run_sts):3.1f}"
        )

    print("\n=== OUTER-LOOP 12-TRIAL RESULTS ===")
    for r in outer_records:
        print(" ", r)

if __name__ == "__main__":
    evaluate_all()
