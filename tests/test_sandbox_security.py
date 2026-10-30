import tempfile
import threading
import unittest
from unittest.mock import MagicMock
from pathlib import Path

from daming_os.growth.sandbox import SandboxGate, SafetyVisitor
from daming_os.growth.deployment import WorkspaceProposalValidator
from daming_os.growth.workflow import EvolutionWorkflow
from daming_os.growth.proposals import ProposalStore


class TestSandboxSecurity(unittest.TestCase):
    def test_ast_blocklist_enforcement(self):
        sandbox = SandboxGate()

        unsafe_codes = [
            "import shutil",
            "import importlib",
            "from importlib import import_module",
            "import os",
            "import subprocess",
            "x = __import__('os')",
            "getattr(object, 'attr')",
            "eval('1 + 1')",
            "exec('a = 1')",
            "open('/tmp/test', 'w')",
        ]

        for code in unsafe_codes:
            is_safe, msg = sandbox.validate_ast(code)
            self.assertFalse(is_safe, f"Expected unsafe code to be blocked: {code}")

        safe_code = "a = 1 + 1\ndef foo():\n    return 42"
        is_safe, msg = sandbox.validate_ast(safe_code)
        self.assertTrue(is_safe, f"Expected safe code to pass AST check: {msg}")

    def test_no_unapproved_code_execution_in_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProposalStore(str(Path(tmp) / "growth.db"))
            proposal_id = store.create({
                "kind": "code-update",
                "target_file": "sample.py",
                "proposed_code": "x = 10\n"
            })

            mock_sandbox = MagicMock(spec=SandboxGate)
            mock_sandbox.validate_ast.return_value = (True, "AST Validation Passed")
            mock_sandbox.run_smoke_test.return_value = (True, "Smoke test passed")

            validator = WorkspaceProposalValidator(workspace=tmp, sandbox=mock_sandbox)

            approved_flag = {"approved": False}

            class MockApprovals:
                def is_approved(self, proposal):
                    return approved_flag["approved"]

            class MockDeployer:
                def deploy(self, proposal): pass
                def rollback(self, proposal): pass

            class MockVerifier:
                def verify(self, proposal): return True

            workflow = EvolutionWorkflow(
                proposals=store,
                validator=validator,
                approvals=MockApprovals(),
                deployer=MockDeployer(),
                verifier=MockVerifier()
            )

            # 1. Advance from proposed -> validated
            outcome1 = workflow.advance(proposal_id)
            self.assertEqual(outcome1, "validated")
            # Smoke test must NOT have been called yet because proposal is not approved!
            mock_sandbox.run_smoke_test.assert_not_called()

            # 2. Advance while unapproved
            outcome2 = workflow.advance(proposal_id)
            self.assertEqual(outcome2, "awaiting_approval")
            mock_sandbox.run_smoke_test.assert_not_called()

            # 3. Grant approval
            approved_flag["approved"] = True

            # 4. Advance when approved -> should run smoke test now
            outcome3 = workflow.advance(proposal_id)
            self.assertEqual(outcome3, "approved")
            mock_sandbox.run_smoke_test.assert_called_once()

    def test_sandbox_gate_does_not_leak_gc_threads(self):
        threads_before = threading.active_count()
        sandbox = SandboxGate()
        threads_after = threading.active_count()

        self.assertEqual(
            threads_before,
            threads_after,
            "Instantiating SandboxGate should not start background threads"
        )


if __name__ == "__main__":
    unittest.main()
