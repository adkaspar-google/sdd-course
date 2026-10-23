import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import task_func

class TestBaselineContract(unittest.TestCase):
    def test_baseline_timestamp_base64_encode(self):
        encoded = task_func({"event": "deploy", "count": 3})
        self.assertIsInstance(encoded, str)
        self.assertTrue(len(encoded) > 10)

if __name__ == '__main__':
    unittest.main()
