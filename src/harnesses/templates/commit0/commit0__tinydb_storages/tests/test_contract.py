import os, sys, tempfile, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
from tinydb.storages import JSONStorage, MemoryStorage

class TestBaselineContract(unittest.TestCase):
    def test_baseline_memory_and_json_storage(self):
        mem = MemoryStorage()
        self.assertIsNone(mem.read())
        mem.write({'_default': {'1': {'k': 'v'}}})
        self.assertEqual(mem.read(), {'_default': {'1': {'k': 'v'}}})
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'test.json')
            js = JSONStorage(p)
            self.assertIsNone(js.read())
            js.write({'_default': {'1': {'k': 'v'}}})
            self.assertEqual(js.read(), {'_default': {'1': {'k': 'v'}}})
            js.close()

if __name__ == '__main__':
    unittest.main()
