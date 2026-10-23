import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import pluck

class TestBaselineContract(unittest.TestCase):
    def test_baseline_docstring_examples(self):
        self.assertEqual(pluck([4, 2, 3]), [2, 1])
        self.assertEqual(pluck([1, 2, 3]), [2, 1])
        self.assertEqual(pluck([]), [])
        self.assertEqual(pluck([5, 0, 3, 0, 4, 2]), [0, 1])

if __name__ == '__main__':
    unittest.main()
