import os, sys
_ROOT_DIR = os.path.abspath(os.path.dirname(__file__) + "/..")
import collections, collections.abc, sys, warnings
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

import importlib.util
import sympy.physics.hep
_spec = importlib.util.spec_from_file_location('sympy.physics.hep.gamma_matrices', os.path.join(_ROOT_DIR, 'sympy/physics/hep/gamma_matrices.py'))
_mod = importlib.util.module_from_spec(_spec)
sys.modules['sympy.physics.hep.gamma_matrices'] = _mod
setattr(sys.modules['sympy.physics.hep'], 'gamma_matrices', _mod)
_spec.loader.exec_module(_mod)
for _k, _v in _mod.__dict__.items():
    if not _k.startswith('_'):
        if hasattr(sympy, _k): setattr(sympy, _k, _v)
        if hasattr(sys.modules['sympy.physics.hep'], _k): setattr(sys.modules['sympy.physics.hep'], _k, _v)
_tspec = importlib.util.spec_from_file_location('starter_t', os.path.join(_ROOT_DIR, 'sympy/physics/hep/tests/test_gamma_matrices.py'))
_tmod = importlib.util.module_from_spec(_tspec); _tspec.loader.exec_module(_tmod)
if hasattr(_tmod, 'test_kahane_algorithm'): getattr(_tmod, 'test_kahane_algorithm')()
if hasattr(_tmod, 'test_gamma_matrix_class'): getattr(_tmod, 'test_gamma_matrix_class')()
print('STARTER_PASS_TO_PASS_OK')
