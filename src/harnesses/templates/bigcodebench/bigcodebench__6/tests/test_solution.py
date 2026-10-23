import os, sys, tempfile, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import task_func

class TestBaselineContract(unittest.TestCase):
    def test_baseline_log_regex_search(self):
        with tempfile.TemporaryDirectory() as d:
            p1 = os.path.join(d, "access.1.log")
            with open(p1, "w") as f:
                f.write("line1\n")
            res = task_func(r"^access\..*\.log$", log_dir=d)
            self.assertEqual(res, p1)
            self.assertIsNone(task_func(r"^nonexistent\.log$", log_dir=d))

if __name__ == '__main__':
    unittest.main()
