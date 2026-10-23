import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
from wcwidth.wcwidth import wcwidth, wcswidth

class TestBaselineContract(unittest.TestCase):
    def test_baseline_ascii_and_cjk_widths(self):
        self.assertEqual(wcwidth('A'), 1)
        self.assertEqual(wcwidth('\x00'), 0)
        self.assertEqual(wcwidth('\n'), -1)
        self.assertEqual(wcswidth('hello'), 5)
        self.assertEqual(wcswidth('hello\nworld'), -1)

if __name__ == '__main__':
    unittest.main()
