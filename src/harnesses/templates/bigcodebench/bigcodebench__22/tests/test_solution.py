import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import task_func

class TestBaselineContract(unittest.TestCase):
    def test_baseline_counter_sample(self):
        cnt = task_func([1, 2], [3, 4], K=5)
        self.assertEqual(sum(cnt.values()), 5)

if __name__ == '__main__':
    unittest.main()
