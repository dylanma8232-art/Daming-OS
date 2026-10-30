import unittest
from daming_os.growth.sandbox import SandboxGate


class TestSandboxSecurity(unittest.TestCase):
    def setUp(self):
        self.sandbox = SandboxGate()

    def test_open_function_is_blocked_by_ast(self):
        code = "open('/tmp/host-data', 'w').write('replacement')"
        is_safe, msg = self.sandbox.validate_ast(code)
        self.assertFalse(is_safe)
        self.assertIn("Blocked function call: open", msg)

    def test_eval_exec_compile_are_blocked(self):
        for fn in ["eval", "exec", "compile", "__import__"]:
            code = f"{fn}('1 + 1')"
            is_safe, msg = self.sandbox.validate_ast(code)
            self.assertFalse(is_safe, f"Expected {fn} to be blocked")
            self.assertIn(f"Blocked function call: {fn}", msg)

    def test_safe_code_passes_ast(self):
        code = "a = 1 + 2\nprint(a)"
        is_safe, msg = self.sandbox.validate_ast(code)
        self.assertTrue(is_safe)
        self.assertIn("AST Validation Passed", msg)


if __name__ == "__main__":
    unittest.main()
