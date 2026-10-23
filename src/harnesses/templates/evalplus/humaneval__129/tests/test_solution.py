import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import minPath

class TestBaselineContract(unittest.TestCase):
    def test_baseline_docstring_examples(self):
        self.assertEqual(minPath([[1, 2, 3], [4, 5, 6], [7, 8, 9]], 3), [1, 2, 1])
        self.assertEqual(minPath([[5, 9, 3], [4, 1, 6], [7, 8, 2]], 1), [1])

if __name__ == '__main__':
    unittest.main()
