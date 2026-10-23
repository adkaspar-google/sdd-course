import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))
from solution import task_func

class TestBaselineContract(unittest.TestCase):
    def test_baseline_pbkdf2_salt_and_hash(self):
        salt, hashed = task_func("secret_password", SALT_LENGTH=16)
        self.assertIsInstance(salt, bytes)
        self.assertIsInstance(hashed, bytes)
        self.assertGreater(len(salt), 0)
        self.assertGreater(len(hashed), 0)

if __name__ == '__main__':
    unittest.main()
