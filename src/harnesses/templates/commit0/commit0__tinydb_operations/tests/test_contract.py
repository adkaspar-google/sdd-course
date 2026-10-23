import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
import tinydb.operations as ops

class TestBaselineContract(unittest.TestCase):
    def test_baseline_increment_and_Decrement(self):
        doc = {'count': 5, 'tag': 'x'}
        ops.increment('count')(doc)
        self.assertEqual(doc['count'], 6)
        ops.decrement('count')(doc)
        self.assertEqual(doc['count'], 5)

    def test_baseline_delete_and_set(self):
        doc = {'a': 1, 'b': 2}
        ops.set('b', 99)(doc)
        self.assertEqual(doc['b'], 99)
        ops.delete('a')(doc)
        self.assertNotIn('a', doc)

if __name__ == '__main__':
    unittest.main()
