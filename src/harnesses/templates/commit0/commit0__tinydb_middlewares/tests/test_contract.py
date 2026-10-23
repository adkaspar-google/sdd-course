import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import MemoryStorage

class TestBaselineContract(unittest.TestCase):
    def test_baseline_caching_write_flush(self):
        mw_cls = CachingMiddleware(MemoryStorage)
        storage = mw_cls()
        self.assertIsNone(storage.read())
        storage.write({'_default': {'1': {'val': 42}}})
        self.assertEqual(storage.read(), {'_default': {'1': {'val': 42}}})
        storage.flush()
        self.assertEqual(storage.storage.read(), {'_default': {'1': {'val': 42}}})

if __name__ == '__main__':
    unittest.main()
