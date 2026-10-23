import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
from tinydb.queries import Query, where

class TestBaselineContract(unittest.TestCase):
    def test_baseline_query_equality_and_logic(self):
        Q = Query()
        q1 = (Q.name == 'alice') & (Q.age > 20)
        self.assertTrue(q1({'name': 'alice', 'age': 25}))
        self.assertFalse(q1({'name': 'alice', 'age': 18}))
        self.assertEqual(hash(Q.name == 'alice'), hash(where('name') == 'alice'))

if __name__ == '__main__':
    unittest.main()
