import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import strange_sort_list

class TestBaselineContract(unittest.TestCase):
    def test_baseline_docstring_examples(self):
        self.assertEqual(strange_sort_list([1, 2, 3, 4]), [1, 4, 2, 3])
        self.assertEqual(strange_sort_list([5, 5, 5, 5]), [5, 5, 5, 5])
        self.assertEqual(strange_sort_list([]), [])

if __name__ == '__main__':
    unittest.main()
