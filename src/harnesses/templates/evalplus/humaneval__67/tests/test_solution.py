import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import fruit_distribution

class TestBaselineContract(unittest.TestCase):
    def test_baseline_docstring_examples(self):
        self.assertEqual(fruit_distribution("5 apples and 6 oranges", 19), 8)
        self.assertEqual(fruit_distribution("0 apples and 1 oranges", 3), 2)
        self.assertEqual(fruit_distribution("2 apples and 3 oranges", 100), 95)

if __name__ == '__main__':
    unittest.main()
