import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import task_func

class TestBaselineContract(unittest.TestCase):
    def test_baseline_tuple_stats(self):
        res = task_func([("1", "2", "3"), ("4", "5", "6")], RANGE=50)
        self.assertEqual(len(res), 3)
        self.assertIsInstance(res[0], float)
        self.assertIsInstance(res[1], float)
        self.assertIsInstance(res[2], int)

if __name__ == '__main__':
    unittest.main()
