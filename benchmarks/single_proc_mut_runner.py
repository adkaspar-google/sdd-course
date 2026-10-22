import importlib
import json
import os
import signal
import sys

def handler(signum, frame):
    raise TimeoutError("mutant timeout")

signal.signal(signal.SIGALRM, handler)

cfg = json.loads(sys.argv[1])
ws_dir = cfg["ws_dir"]
target_rel = cfg["target_rel"]
test_files = cfg["test_files"]
mutants = cfg["mutants"]
orig_code = cfg["orig_code"]

sys.path.insert(0, ws_dir)
target_abs = os.path.join(ws_dir, target_rel)
mod_name = target_rel[:-3].replace("/", ".")

# Collect callable test functions or unittest.TestCase classes from test_files
def run_test_file(tf):
    with open(tf, "r", errors="ignore") as f:
        code = f.read()
    # Strip any sys.path.insert pointing elsewhere and strip if __name__ == '__main__' sys.exit
    ns = {"__name__": "__test_runner__", "__file__": tf}
    exec(compile(code, tf, "exec"), ns)
    import unittest
    for k, v in list(ns.items()):
        if isinstance(v, type) and issubclass(v, unittest.TestCase) and v is not unittest.TestCase:
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(v)
            res = unittest.TextTestRunner(stream=open(os.devnull, "w")).run(suite)
            if not res.wasSuccessful():
                raise AssertionError("unittest failed")
        elif callable(v) and k.startswith("test_"):
            v()
    if "_tmod" in ns:
        tmod_funcs = [
            (tk, tv) for tk, tv in ns["_tmod"].__dict__.items()
            if callable(tv) and tk.startswith("test_")
        ]
        for tk, tv in tmod_funcs[-5:]:
            tv()

# First verify which test files pass against current workspace implementation
valid_tfs = []
for tf in test_files:
    try:
        signal.alarm(3)
        run_test_file(tf)
        signal.alarm(0)
        valid_tfs.append(tf)
    except Exception:
        signal.alarm(0)

if not valid_tfs:
    print(json.dumps({"killed": 0, "total": len(mutants)}))
    sys.exit(0)

killed = 0
try:
    for desc, mut_code in mutants:
        with open(target_abs, "w") as f:
            f.write(mut_code)
        # Evict any cached workspace modules so re-importing loads the mutated file from disk
        ws_norm = os.path.abspath(ws_dir)
        for mname, mobj in list(sys.modules.items()):
            mfile = getattr(mobj, "__file__", None) or ""
            if mname in (mod_name, "solution", "src.solution") or (mfile and os.path.abspath(mfile).startswith(ws_norm)):
                if mname.startswith("sympy"):
                    try:
                        if mname == mod_name:
                            importlib.reload(mobj)
                    except Exception:
                        pass
                else:
                    sys.modules.pop(mname, None)
        m_killed = False
        for tf in valid_tfs:
            try:
                signal.alarm(2)
                run_test_file(tf)
                signal.alarm(0)
            except Exception:
                signal.alarm(0)
                m_killed = True
                break
        if m_killed:
            killed += 1
finally:
    with open(target_abs, "w") as f:
        f.write(orig_code)

print(json.dumps({"killed": killed, "total": len(mutants)}))
