import ast
import collections
import collections.abc
import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request

STAGE_ROOT = "./benchmarks/upstream_252_trials"
UPSTREAM_ROOT = "$HOME/gemini_scratch/upstream_check"
if os.path.exists(STAGE_ROOT):
    shutil.rmtree(STAGE_ROOT)
os.makedirs(STAGE_ROOT, exist_ok=True)

PY313_COMPAT_HEADER = """import collections, collections.abc, sys, warnings
warnings.filterwarnings('ignore')
for _attr in ('Mapping', 'MutableMapping', 'Iterable', 'Iterator', 'Callable', 'Sequence', 'MutableSequence', 'Set', 'MutableSet', 'Hashable', 'Sized', 'Container'):
    if hasattr(collections.abc, _attr) and not hasattr(collections, _attr):
        setattr(collections, _attr, getattr(collections.abc, _attr))
import sympy, sympy.core.compatibility
if not hasattr(sympy.core.compatibility, 'range'):
    sympy.core.compatibility.range = range
if not hasattr(sympy.core.compatibility, 'string_types'):
    sympy.core.compatibility.string_types = (str,)
if not hasattr(sympy.core.compatibility, 'exec_'):
    sympy.core.compatibility.exec_ = exec
if not hasattr(sympy.core.compatibility, 'iterable'):
    from sympy.utilities.iterables import iterable as _sym_iterable
    sympy.core.compatibility.iterable = _sym_iterable
if not hasattr(sympy.core.compatibility, 'is_sequence'):
    from sympy.utilities.iterables import is_sequence as _sym_is_seq
    sympy.core.compatibility.is_sequence = _sym_is_seq
if not hasattr(sympy.core.compatibility, 'as_int'):
    from sympy.utilities.misc import as_int as _sym_as_int
    sympy.core.compatibility.as_int = _sym_as_int
if not hasattr(sympy.core.compatibility, 'ordered'):
    from sympy.core.sorting import ordered as _sym_ordered
    sympy.core.compatibility.ordered = _sym_ordered
if not hasattr(sympy.core.compatibility, 'default_sort_key'):
    from sympy.core.sorting import default_sort_key as _sym_dsk
    sympy.core.compatibility.default_sort_key = _sym_dsk
if not hasattr(sympy.core.compatibility, 'PY3'):
    sympy.core.compatibility.PY3 = True
if not hasattr(sympy.core.compatibility, 'u'):
    sympy.core.compatibility.u = lambda x: x
if not hasattr(sympy.core.compatibility, 'unicodedata'):
    import unicodedata
    sympy.core.compatibility.unicodedata = unicodedata
if not hasattr(sympy.core.compatibility, ' ground_types'):
    sympy.core.compatibility.ground_types = ('python', 'gmpy')
"""

def fetch_hf(dataset, config="default", split="test", offset=0, length=100):
    url = f"https://datasets-server.huggingface.co/rows?dataset={urllib.parse.quote(dataset, safe='')}&config={config}&split={split}&offset={offset}&length={length}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return [x["row"] for x in json.loads(r.read().decode("utf-8")).get("rows", [])]

manifest = {"suites": {}}

# ==============================================================================
# SUITE 1: SWE-bench Verified (princeton-nlp/SWE-bench_Verified)
# ==============================================================================
print("=== Staging Suite 1: SWE-bench Verified ===")
swe_all = []
for off in [0, 100, 200, 300, 400]:
    for r in fetch_hf("princeton-nlp/SWE-bench_Verified", offset=off, length=100):
        if r["repo"] == "sympy/sympy":
            swe_all.append(r)

sympy_repo = os.path.join(UPSTREAM_ROOT, "sympy")
manifest["suites"]["swebench_verified"] = []

# Prefer newer sympy issues first (higher issue numbers are closer to Python 3.11+ / SymPy 1.9+)
swe_all_sorted = sorted(swe_all, key=lambda x: int(x["instance_id"].split("-")[-1]), reverse=True)

for r in swe_all_sorted:
    if len(manifest["suites"]["swebench_verified"]) >= 5:
        break
    iid = r["instance_id"]
    base_commit = r["base_commit"]
    patch_str = r["patch"]
    test_patch_str = r["test_patch"]
    f2p = json.loads(r["FAIL_TO_PASS"])
    p2p = json.loads(r["PASS_TO_PASS"])[:4]

    src_files = re.findall(r"diff --git a/(.*?) b/", patch_str)
    test_files = re.findall(r"diff --git a/(.*?) b/", test_patch_str)
    if not src_files or not test_files or len(src_files) > 2:
        continue

    ws_tmpl = os.path.join(STAGE_ROOT, "templates", "swebench_verified", iid)
    priv_dir = os.path.join(STAGE_ROOT, "privilege_dir", "swebench_verified", iid)
    os.makedirs(ws_tmpl, exist_ok=True)
    os.makedirs(priv_dir, exist_ok=True)

    try:
        for fpath in src_files + test_files:
            full_dest = os.path.join(ws_tmpl, fpath)
            os.makedirs(os.path.dirname(full_dest), exist_ok=True)
            raw_content = subprocess.check_output(
                ["git", "-C", sympy_repo, "show", f"{base_commit}:{fpath}"],
                stderr=subprocess.DEVNULL
            )
            with open(full_dest, "wb") as f:
                f.write(raw_content)

        gold_dir = os.path.join(priv_dir, "gold_src")
        shutil.copytree(ws_tmpl, gold_dir)
        subprocess.run(["patch", "-p1", "-d", gold_dir], input=patch_str.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["patch", "-p1", "-d", gold_dir], input=test_patch_str.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        shutil.rmtree(ws_tmpl, ignore_errors=True)
        shutil.rmtree(priv_dir, ignore_errors=True)
        continue

    hotload_lines = [PY313_COMPAT_HEADER, "import importlib.util"]
    for sf in src_files:
        mod_name = sf.replace("/", ".").removesuffix(".py")
        pkg_parts = mod_name.split(".")
        parent_pkg = ".".join(pkg_parts[:-1])
        attr_name = pkg_parts[-1]
        hotload_lines.append(f"import {parent_pkg}")
        hotload_lines.append(f"_spec = importlib.util.spec_from_file_location({repr(mod_name)}, os.path.join(_ROOT_DIR, {repr(sf)}))")
        hotload_lines.append(f"_mod = importlib.util.module_from_spec(_spec)")
        hotload_lines.append(f"sys.modules[{repr(mod_name)}] = _mod")
        hotload_lines.append(f"setattr(sys.modules[{repr(parent_pkg)}], {repr(attr_name)}, _mod)")
        hotload_lines.append(f"_spec.loader.exec_module(_mod)")
        hotload_lines.append(f"for _k, _v in _mod.__dict__.items():")
        hotload_lines.append(f"    if not _k.startswith('_'):")
        hotload_lines.append(f"        if hasattr(sympy, _k): setattr(sympy, _k, _v)")
        hotload_lines.append(f"        if hasattr(sys.modules[{repr(parent_pkg)}], _k): setattr(sys.modules[{repr(parent_pkg)}], _k, _v)")
    hotload_block = "\n".join(hotload_lines)

    starter_test_code = f"""import os, sys
_ROOT_DIR = os.path.abspath(os.path.dirname(__file__) + "/..")
{hotload_block}
"""
    for tf in test_files:
        starter_test_code += f"_tspec = importlib.util.spec_from_file_location('starter_t', os.path.join(_ROOT_DIR, {repr(tf)}))\n"
        starter_test_code += f"_tmod = importlib.util.module_from_spec(_tspec); _tspec.loader.exec_module(_tmod)\n"
        for fn in p2p[:2]:
            starter_test_code += f"if hasattr(_tmod, {repr(fn)}): getattr(_tmod, {repr(fn)})()\n"
    starter_test_code += "print('STARTER_PASS_TO_PASS_OK')\n"

    os.makedirs(os.path.join(ws_tmpl, "tests"), exist_ok=True)
    with open(os.path.join(ws_tmpl, "tests", "test_regression.py"), "w") as f:
        f.write(starter_test_code)

    with open(os.path.join(ws_tmpl, "prompt.md"), "w") as f:
        f.write(f"# SWE-bench Verified Issue: `{iid}`\n\n")
        f.write(f"## Target Files in Workspace\n")
        for sf in src_files:
            f.write(f"- `{sf}`\n")
        f.write(f"- Regression test runner: `tests/test_regression.py` (run with `python3 tests/test_regression.py`)\n\n")
        f.write(f"## Upstream GitHub Issue Description\n\n{r['problem_statement']}\n")

    oracle_code = f"""import os, sys
_ROOT_DIR = os.path.abspath(sys.argv[1])
_PRIV_DIR = os.path.dirname(os.path.abspath(__file__))
{hotload_block}
"""
    for tf in test_files:
        gold_tf = os.path.join(gold_dir, tf)
        oracle_code += f"_tspec = importlib.util.spec_from_file_location('oracle_t', {repr(gold_tf)})\n"
        oracle_code += f"_tmod = importlib.util.module_from_spec(_tspec); _tspec.loader.exec_module(_tmod)\n"
        for fn in f2p:
            oracle_code += f"if hasattr(_tmod, {repr(fn)}):\n"
            oracle_code += f"    print('Running F2P:', {repr(fn)})\n"
            oracle_code += f"    getattr(_tmod, {repr(fn)})()\n"
    oracle_code += "print('ALL_ORACLE_TESTS_PASSED')\n"

    oracle_path = os.path.join(priv_dir, "oracle_eval.py")
    with open(oracle_path, "w") as f:
        f.write(oracle_code)

    try:
        r_base = subprocess.run(["python3", oracle_path, ws_tmpl], capture_output=True, text=True, timeout=20)
        r_gold = subprocess.run(["python3", oracle_path, gold_dir], capture_output=True, text=True, timeout=20)
        ok = (r_base.returncode != 0) and (r_gold.returncode == 0)
    except Exception:
        ok = False
    if not ok:
        shutil.rmtree(ws_tmpl, ignore_errors=True)
        shutil.rmtree(priv_dir, ignore_errors=True)
        continue
    print(f"  [{iid}] diff={r.get('difficulty')} | base_exit={r_base.returncode} | gold_exit={r_gold.returncode} | VALID_RED_GREEN={ok}")
    manifest["suites"]["swebench_verified"].append({
        "task_id": iid,
        "suite": "swebench_verified",
        "difficulty": r.get("difficulty", ""),
        "src_files": src_files,
        "test_files": ["tests/test_regression.py"],
        "gold_src_file": os.path.join(gold_dir, src_files[0]),
        "oracle_script": oracle_path,
    })

print(f"Selected {len(manifest['suites']['swebench_verified'])} SWE-bench Verified tasks.")

# ==============================================================================
# SUITE 2: Commit0 (wentingzhao/commit0_combined)
# ==============================================================================
print("\n=== Staging Suite 2: Commit0 ===")
manifest["suites"]["commit0"] = []
c0_rows = fetch_hf("wentingzhao/commit0_combined", offset=0, length=50)
c0_by_repo = {r["repo"]: r for r in c0_rows}

tinydb_repo = os.path.join(UPSTREAM_ROOT, "tinydb")
wcwidth_repo = os.path.join(UPSTREAM_ROOT, "wcwidth")

tinydb_base = c0_by_repo["commit-0/tinydb"]["base_commit"]
tinydb_ref = c0_by_repo["commit-0/tinydb"]["reference_commit"]
wcwidth_base = c0_by_repo["commit-0/wcwidth"]["base_commit"]
wcwidth_ref = c0_by_repo["commit-0/wcwidth"]["reference_commit"]

# Ensure ref commits are fetched in local clones
subprocess.run(["git", "-C", tinydb_repo, "fetch", "origin", tinydb_base, tinydb_ref], check=True, stderr=subprocess.DEVNULL)
subprocess.run(["git", "-C", wcwidth_repo, "fetch", "origin", wcwidth_base, wcwidth_ref], check=True, stderr=subprocess.DEVNULL)

commit0_specs = [
    {
        "task_id": "commit0__tinydb_operations",
        "repo_dir": tinydb_repo,
        "base_commit": tinydb_base,
        "ref_commit": tinydb_ref,
        "target_src": "tinydb/operations.py",
        "target_test": "tests/test_operations.py",
        "all_files": ["tinydb/__init__.py", "tinydb/version.py", "tinydb/database.py", "tinydb/table.py", "tinydb/queries.py", "tinydb/storages.py", "tinydb/middlewares.py", "tinydb/operations.py", "tinydb/utils.py", "tinydb/mypy_plugin.py"],
    },
    {
        "task_id": "commit0__tinydb_middlewares",
        "repo_dir": tinydb_repo,
        "base_commit": tinydb_base,
        "ref_commit": tinydb_ref,
        "target_src": "tinydb/middlewares.py",
        "target_test": "tests/test_middlewares.py",
        "all_files": ["tinydb/__init__.py", "tinydb/version.py", "tinydb/database.py", "tinydb/table.py", "tinydb/queries.py", "tinydb/storages.py", "tinydb/middlewares.py", "tinydb/operations.py", "tinydb/utils.py", "tinydb/mypy_plugin.py"],
    },
    {
        "task_id": "commit0__tinydb_storages",
        "repo_dir": tinydb_repo,
        "base_commit": tinydb_base,
        "ref_commit": tinydb_ref,
        "target_src": "tinydb/storages.py",
        "target_test": "tests/test_storages.py",
        "all_files": ["tinydb/__init__.py", "tinydb/version.py", "tinydb/database.py", "tinydb/table.py", "tinydb/queries.py", "tinydb/storages.py", "tinydb/middlewares.py", "tinydb/operations.py", "tinydb/utils.py", "tinydb/mypy_plugin.py"],
    },
    {
        "task_id": "commit0__tinydb_queries",
        "repo_dir": tinydb_repo,
        "base_commit": tinydb_base,
        "ref_commit": tinydb_ref,
        "target_src": "tinydb/queries.py",
        "target_test": "tests/test_queries.py",
        "all_files": ["tinydb/__init__.py", "tinydb/version.py", "tinydb/database.py", "tinydb/table.py", "tinydb/queries.py", "tinydb/storages.py", "tinydb/middlewares.py", "tinydb/operations.py", "tinydb/utils.py", "tinydb/mypy_plugin.py"],
    },
    {
        "task_id": "commit0__wcwidth_core",
        "repo_dir": wcwidth_repo,
        "base_commit": wcwidth_base,
        "ref_commit": wcwidth_ref,
        "target_src": "wcwidth/wcwidth.py",
        "target_test": "tests/test_core.py",
        "all_files": ["wcwidth/__init__.py", "wcwidth/wcwidth.py", "wcwidth/table_wide.py", "wcwidth/table_zero.py", "wcwidth/table_vs16.py", "wcwidth/unicode_versions.py"],
    },
]

for spec in commit0_specs:
    tid = spec["task_id"]
    rdir = spec["repo_dir"]
    base_c = spec["base_commit"]
    ref_c = spec["ref_commit"]

    ws_tmpl = os.path.join(STAGE_ROOT, "templates", "commit0", tid)
    priv_dir = os.path.join(STAGE_ROOT, "privilege_dir", "commit0", tid)
    gold_dir = os.path.join(priv_dir, "gold_src")
    os.makedirs(ws_tmpl, exist_ok=True)
    os.makedirs(gold_dir, exist_ok=True)

    for fpath in spec["all_files"]:
        try:
            ref_bytes = subprocess.check_output(["git", "-C", rdir, "show", f"{ref_c}:{fpath}"], stderr=subprocess.DEVNULL)
        except Exception:
            continue
        for dst_root in (ws_tmpl, gold_dir):
            full_p = os.path.join(dst_root, fpath)
            os.makedirs(os.path.dirname(full_p), exist_ok=True)
            with open(full_p, "wb") as f:
                f.write(ref_bytes)

    base_src_bytes = subprocess.check_output(["git", "-C", rdir, "show", f"{base_c}:{spec['target_src']}"])
    with open(os.path.join(ws_tmpl, spec["target_src"]), "wb") as f:
        f.write(base_src_bytes)

    test_bytes = subprocess.check_output(["git", "-C", rdir, "show", f"{ref_c}:{spec['target_test']}"])
    with open(os.path.join(priv_dir, "upstream_test.py"), "wb") as f:
        f.write(test_bytes)

    os.makedirs(os.path.join(ws_tmpl, "tests"), exist_ok=True)
    pkg_name = spec["target_src"].split("/")[0]
    mod_name = spec["target_src"].replace("/", ".").removesuffix(".py")
    starter_contract = f"""import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
import {mod_name} as target_mod

class TestContractSmoke(unittest.TestCase):
    def test_module_imports_and_functions_callable(self):
        pub = [k for k in dir(target_mod) if not k.startswith('_')]
        self.assertTrue(len(pub) > 0)

if __name__ == '__main__':
    unittest.main()
"""
    with open(os.path.join(ws_tmpl, "tests", "test_contract.py"), "w") as f:
        f.write(starter_contract)

    with open(os.path.join(ws_tmpl, "prompt.md"), "w") as f:
        f.write(f"# Commit0 Zero-to-One Library Specification: `{tid}`\n\n")
        f.write(f"## Target Module to Implement from Docstring Specification\n")
        f.write(f"- Target source file: `{spec['target_src']}` (currently contains Commit0 `pass` skeletons and complete API docstrings)\n")
        f.write(f"- Supporting package files in `{pkg_name}/` are already present for reference.\n")
        f.write(f"- Starter contract test file: `tests/test_contract.py` (expand with comprehensive unit tests covering every function/class and edge case in `{spec['target_src']}`).\n")

    oracle_code = f"""import importlib.util, inspect, os, sys, tempfile
WORKSPACE = os.path.abspath(sys.argv[1])
PRIV_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE)

import types
pytest_mod = types.ModuleType('pytest')
class _RaisesCtx:
    def __init__(self, exc): self.exc = exc
    def __enter__(self): return self
    def __exit__(self, et, ev, tb):
        if et is None: raise AssertionError(f"Expected {{self.exc}}, but no exception raised")
        return issubclass(et, self.exc)
pytest_mod.raises = lambda exc, *a, **kw: _RaisesCtx(exc)
def _parametrize(argnames, argvalues):
    def _dec(fn):
        fn._parametrize = (argnames, argvalues)
        return fn
    return _dec
class _Mark:
    parametrize = staticmethod(_parametrize)
    def __getattr__(self, name): return lambda *a, **kw: (a[0] if a and callable(a[0]) else (lambda f: f))
pytest_mod.mark = _Mark()
pytest_mod.fixture = lambda *a, **kw: (a[0] if a and callable(a[0]) else (lambda f: f))
pytest_mod.warns = lambda *a, **kw: _RaisesCtx(Exception)
sys.modules['pytest'] = pytest_mod

spec = importlib.util.spec_from_file_location('upstream_test', os.path.join(PRIV_DIR, 'upstream_test.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

ran = 0
for name, fn in inspect.getmembers(mod, inspect.isfunction):
    if not name.startswith('test_') or name == 'test_package_version':
        continue
    with tempfile.TemporaryDirectory() as tmpdir:
        sig = inspect.signature(fn)
        kwargs = {{}}
        skip = False
        for p in sig.parameters:
            if p == 'db':
                from tinydb import TinyDB
                from tinydb.storages import MemoryStorage
                db = TinyDB(storage=MemoryStorage)
                db.drop_tables()
                db.insert_multiple({{'int': 1, 'char': c}} for c in 'abc')
                kwargs['db'] = db
            elif p == 'storage':
                from tinydb.middlewares import CachingMiddleware
                from tinydb.storages import MemoryStorage
                kwargs['storage'] = CachingMiddleware(MemoryStorage)()
            elif p == 'tmpdir':
                import pathlib
                class _TmpPath(os.PathLike):
                    def __init__(self, p): self._p = pathlib.Path(p)
                    def join(self, *a): return _TmpPath(self._p.joinpath(*a))
                    def read(self): return self._p.read_text()
                    def write(self, s): return self._p.write_text(s)
                    def __fspath__(self): return str(self._p)
                    def __str__(self): return str(self._p)
                kwargs['tmpdir'] = _TmpPath(tmpdir)
            elif hasattr(fn, '_parametrize'):
                pass
            else:
                skip = True
        if skip:
            continue
        if hasattr(fn, '_parametrize'):
            argnames, argvalues = fn._parametrize
            names = [x.strip() for x in argnames.split(',')] if isinstance(argnames, str) else list(argnames)
            for val in argvalues:
                vals = val if isinstance(val, (tuple, list)) else (val,)
                call_kw = dict(kwargs)
                for k, v in zip(names, vals):
                    call_kw[k] = v
                fn(**call_kw)
                ran += 1
        else:
            fn(**kwargs)
            ran += 1

if ran == 0:
    print("NO_TESTS_RAN")
    sys.exit(1)
print(f"COMMIT0_ORACLE_PASSED ({{ran}} test invocations)")
"""
    oracle_path = os.path.join(priv_dir, "oracle_eval.py")
    with open(oracle_path, "w") as f:
        f.write(oracle_code)

    r_base = subprocess.run(["python3", oracle_path, ws_tmpl], capture_output=True, text=True)
    r_gold = subprocess.run(["python3", oracle_path, gold_dir], capture_output=True, text=True)
    ok = (r_base.returncode != 0) and (r_gold.returncode == 0)
    print(f"  [{tid}] base_exit={r_base.returncode} | gold_exit={r_gold.returncode} ({r_gold.stdout.strip()}) | VALID_RED_GREEN={ok}")
    if not ok:
        print("    GOLD STDERR:", r_gold.stderr)
    manifest["suites"]["commit0"].append({
        "task_id": tid,
        "suite": "commit0",
        "src_files": [spec["target_src"]],
        "test_files": ["tests/test_contract.py"],
        "gold_src_file": os.path.join(gold_dir, spec["target_src"]),
        "oracle_script": oracle_path,
    })

# ==============================================================================
# SUITE 3: BigCodeBench (bigcode/bigcodebench v0.1.2)
# ==============================================================================
print("\n=== Staging Suite 3: BigCodeBench v0.1.2 ===")
manifest["suites"]["bigcodebench"] = []
bcb_rows = fetch_hf("bigcode/bigcodebench", split="v0.1.2", offset=0, length=100)
bcb_map = {r["task_id"]: r for r in bcb_rows}
target_bcb_ids = ["BigCodeBench/6", "BigCodeBench/10", "BigCodeBench/22", "BigCodeBench/24", "BigCodeBench/27"]

for bid in target_bcb_ids:
    r = bcb_map[bid]
    slug = bid.replace("/", "__").lower()
    ws_tmpl = os.path.join(STAGE_ROOT, "templates", "bigcodebench", slug)
    priv_dir = os.path.join(STAGE_ROOT, "privilege_dir", "bigcodebench", slug)
    gold_dir = os.path.join(priv_dir, "gold_src")
    os.makedirs(os.path.join(ws_tmpl, "src"), exist_ok=True)
    os.makedirs(os.path.join(ws_tmpl, "tests"), exist_ok=True)
    os.makedirs(os.path.join(gold_dir, "src"), exist_ok=True)

    base_code = r["complete_prompt"].rstrip() + "\n    pass\n"
    with open(os.path.join(ws_tmpl, "src", "solution.py"), "w") as f:
        f.write(base_code)

    gold_code = r["complete_prompt"].rstrip() + "\n" + r["canonical_solution"] + "\n"
    with open(os.path.join(gold_dir, "src", "solution.py"), "w") as f:
        f.write(gold_code)

    starter_t = f"""import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import {r['entry_point']}

class TestStarter(unittest.TestCase):
    def test_callable(self):
        self.assertTrue(callable({r['entry_point']}))

if __name__ == '__main__':
    unittest.main()
"""
    with open(os.path.join(ws_tmpl, "tests", "test_solution.py"), "w") as f:
        f.write(starter_t)

    with open(os.path.join(ws_tmpl, "prompt.md"), "w") as f:
        f.write(f"# BigCodeBench v0.1.2 Task: `{bid}`\n\n")
        f.write(f"- Target implementation file: `src/solution.py`\n")
        f.write(f"- Target unit test file: `tests/test_solution.py`\n\n")
        f.write(f"## Specification\n```python\n{r['complete_prompt']}\n```\n")

    oracle_code = f"""import os, sys, unittest
WORKSPACE = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.join(WORKSPACE, "src"))
from solution import *

with open(os.path.join(WORKSPACE, "src", "solution.py")) as _sf:
    exec(_sf.read(), globals())

{r['test']}

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestCases)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() and result.testsRun > 0 else 1)
"""
    oracle_path = os.path.join(priv_dir, "oracle_eval.py")
    with open(oracle_path, "w") as f:
        f.write(oracle_code)

    r_base = subprocess.run(["python3", oracle_path, ws_tmpl], capture_output=True, text=True)
    r_gold = subprocess.run(["python3", oracle_path, gold_dir], capture_output=True, text=True)
    ok = (r_base.returncode != 0) and (r_gold.returncode == 0)
    print(f"  [{bid}] base_exit={r_base.returncode} | gold_exit={r_gold.returncode} | VALID_RED_GREEN={ok}")
    manifest["suites"]["bigcodebench"].append({
        "task_id": slug,
        "suite": "bigcodebench",
        "src_files": ["src/solution.py"],
        "test_files": ["tests/test_solution.py"],
        "gold_src_file": os.path.join(gold_dir, "src", "solution.py"),
        "oracle_script": oracle_path,
    })

# ==============================================================================
# SUITE 4: EvalPlus (evalplus/humanevalplus 80x extreme boundary suite)
# ==============================================================================
print("\n=== Staging Suite 4: EvalPlus (HumanEval+ 80x) ===")
manifest["suites"]["evalplus"] = []
hep_rows = fetch_hf("evalplus/humanevalplus", offset=60, length=40) + fetch_hf("evalplus/humanevalplus", offset=120, length=30)
hep_map = {r["task_id"]: r for r in hep_rows}
target_hep_ids = ["HumanEval/67", "HumanEval/68", "HumanEval/69", "HumanEval/70", "HumanEval/129"]

for hid in target_hep_ids:
    r = hep_map[hid]
    slug = hid.replace("/", "__").lower()
    ws_tmpl = os.path.join(STAGE_ROOT, "templates", "evalplus", slug)
    priv_dir = os.path.join(STAGE_ROOT, "privilege_dir", "evalplus", slug)
    gold_dir = os.path.join(priv_dir, "gold_src")
    os.makedirs(os.path.join(ws_tmpl, "src"), exist_ok=True)
    os.makedirs(os.path.join(ws_tmpl, "tests"), exist_ok=True)
    os.makedirs(os.path.join(gold_dir, "src"), exist_ok=True)

    base_code = r["prompt"].rstrip() + "\n    pass\n"
    with open(os.path.join(ws_tmpl, "src", "solution.py"), "w") as f:
        f.write(base_code)

    gold_code = r["prompt"].rstrip() + "\n" + r["canonical_solution"] + "\n"
    with open(os.path.join(gold_dir, "src", "solution.py"), "w") as f:
        f.write(gold_code)

    starter_t = f"""import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import {r['entry_point']}

class TestEvalPlusStarter(unittest.TestCase):
    def test_exists(self):
        self.assertTrue(callable({r['entry_point']}))

if __name__ == '__main__':
    unittest.main()
"""
    with open(os.path.join(ws_tmpl, "tests", "test_solution.py"), "w") as f:
        f.write(starter_t)

    with open(os.path.join(ws_tmpl, "prompt.md"), "w") as f:
        f.write(f"# EvalPlus (HumanEval+ 80x Boundary Benchmark): `{hid}`\n\n")
        f.write(f"- Target implementation file: `src/solution.py`\n")
        f.write(f"- Target unit test file: `tests/test_solution.py`\n\n")
        f.write(f"## Specification\n```python\n{r['prompt']}\n```\n")

    oracle_code = f"""import os, sys
WORKSPACE = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.join(WORKSPACE, "src"))
from solution import {r['entry_point']}

{r['test']}

if __name__ == '__main__':
    check({r['entry_point']})
    print("EVALPLUS_80X_ORACLE_PASSED")
"""
    oracle_path = os.path.join(priv_dir, "oracle_eval.py")
    with open(oracle_path, "w") as f:
        f.write(oracle_code)

    r_base = subprocess.run(["python3", oracle_path, ws_tmpl], capture_output=True, text=True)
    r_gold = subprocess.run(["python3", oracle_path, gold_dir], capture_output=True, text=True)
    ok = (r_base.returncode != 0) and (r_gold.returncode == 0)
    print(f"  [{hid}] base_exit={r_base.returncode} | gold_exit={r_gold.returncode} | VALID_RED_GREEN={ok}")
    manifest["suites"]["evalplus"].append({
        "task_id": slug,
        "suite": "evalplus",
        "src_files": ["src/solution.py"],
        "test_files": ["tests/test_solution.py"],
        "gold_src_file": os.path.join(gold_dir, "src", "solution.py"),
        "oracle_script": oracle_path,
    })

with open(os.path.join(STAGE_ROOT, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
print("\nSaved manifest.json with all 4 upstream benchmark suites!")

# ==============================================================================
# SUITE 5: Outer-Loop Multi-Sprint Specification Evolution (Commit0-Evo on TinyDB)
# ==============================================================================
print("\n=== Staging Suite 5: Outer-Loop Multi-Sprint Evolution (Commit0-Evo on TinyDB) ===")
evo_root = os.path.join(STAGE_ROOT, "templates", "outer_loop_evo")
evo_priv = os.path.join(STAGE_ROOT, "privilege_dir", "outer_loop_evo")
os.makedirs(evo_root, exist_ok=True)
os.makedirs(evo_priv, exist_ok=True)

# Copy clean reference tinydb codebase as the Sprint 0 baseline
tinydb_base_dir = os.path.join(evo_root, "base_tinydb")
os.makedirs(tinydb_base_dir, exist_ok=True)
for fpath in ["tinydb/__init__.py", "tinydb/version.py", "tinydb/database.py", "tinydb/table.py", "tinydb/queries.py", "tinydb/storages.py", "tinydb/middlewares.py", "tinydb/operations.py", "tinydb/utils.py"]:
    ref_bytes = subprocess.check_output(["git", "-C", tinydb_repo, "show", f"{tinydb_ref}:{fpath}"])
    full_p = os.path.join(tinydb_base_dir, fpath)
    os.makedirs(os.path.dirname(full_p), exist_ok=True)
    with open(full_p, "wb") as f:
        f.write(ref_bytes)

print("Staged base_tinydb for Outer-Loop 5-Sprint Evolution!")
with open(os.path.join(STAGE_ROOT, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
