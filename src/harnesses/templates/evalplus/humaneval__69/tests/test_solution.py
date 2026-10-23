import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import search

class TestBaselineContract(unittest.TestCase):
    def test_baseline_docstring_examples(self):
        self.assertEqual(search([4, 1, 2, 2, 3, 1]), 2)
        self.assertEqual(search([1, 2, 2, 3, 3, 3, 4, 4, 4]), 3)
        self.assertEqual(search([5, 5, 4, 4, 4]), -1)

if __name__ == '__main__':
    unittest.main()
