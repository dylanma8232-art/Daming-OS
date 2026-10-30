import os
import subprocess
import unittest
from pathlib import Path


class TestWorkflowSecurity(unittest.TestCase):
    def setUp(self):
        self.workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "auto-merge-jules.yml"
        self.assertTrue(self.workflow_path.exists(), "auto-merge-jules.yml exists")

    def _extract_identify_script(self):
        content = self.workflow_path.read_text()
        # Locate the run script block in 'Identify Jules PR' step
        lines = content.splitlines()
        script_lines = []
        capturing = False
        for line in lines:
            if "name: Identify Jules PR" in line:
                capturing = False
            elif capturing:
                if line.startswith("      - name:") or line.startswith("  "):
                    if not line.startswith("        ") and script_lines:
                        break
                if line.startswith("        "):
                    script_lines.append(line[8:])
            elif "run: |" in line and not capturing:
                # check if this run block belongs to identify step
                capturing = True

        return "\n".join(script_lines)

    def _run_identify_script(self, body, branch, head_repo, base_repo, pr_author, repo_owner="owner_user"):
        script = self._extract_identify_script()
        env = {
            "PATH": os.environ.get("PATH", ""),
            "BODY": body,
            "BRANCH": branch,
            "HEAD_REPO": head_repo,
            "BASE_REPO": base_repo,
            "PR_AUTHOR": pr_author,
            "REPO_OWNER": repo_owner,
        }
        # Create temp output file for GITHUB_OUTPUT
        output_file = Path(__file__).parent / "_temp_github_output.txt"
        if output_file.exists():
            output_file.unlink()

        env["GITHUB_OUTPUT"] = str(output_file)

        res = subprocess.run(
            ["bash", "-c", script],
            env=env,
            capture_output=True,
            text=True
        )

        outputs = {}
        if output_file.exists():
            for line in output_file.read_text().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    outputs[k] = v
            output_file.unlink()

        return res.returncode, outputs, res.stdout

    def test_fork_pr_with_jules_text_is_rejected(self):
        # A fork PR trying to spoof Jules body text
        code, outputs, stdout = self._run_identify_script(
            body="PR created automatically by Jules",
            branch="feature-branch",
            head_repo="attacker/daming-os",
            base_repo="daming-os/daming-os",
            pr_author="attacker",
        )
        self.assertEqual(code, 0)
        self.assertEqual(outputs.get("is_jules"), "false")
        self.assertIn("PR is from a fork", stdout)

    def test_fork_pr_with_jules_branch_is_rejected(self):
        # A fork PR trying to spoof Jules 15-digit branch name
        code, outputs, stdout = self._run_identify_script(
            body="Fix something",
            branch="jules-123456789012345",
            head_repo="attacker/daming-os",
            base_repo="daming-os/daming-os",
            pr_author="attacker",
        )
        self.assertEqual(code, 0)
        self.assertEqual(outputs.get("is_jules"), "false")
        self.assertIn("PR is from a fork", stdout)

    def test_same_repo_unauthorized_author_is_rejected(self):
        # A same-repo PR by an unauthorized user with spoofed text
        code, outputs, stdout = self._run_identify_script(
            body="PR created automatically by Jules",
            branch="patch-1",
            head_repo="daming-os/daming-os",
            base_repo="daming-os/daming-os",
            pr_author="untrusted_contributor",
        )
        self.assertEqual(code, 0)
        self.assertEqual(outputs.get("is_jules"), "false")
        self.assertIn("PR author (untrusted_contributor) is not authorized", stdout)

    def test_valid_jules_bot_pr_accepted(self):
        # Same repo, google-labs-jules[bot], matching body phrase
        code, outputs, stdout = self._run_identify_script(
            body="PR created automatically by Jules",
            branch="jules-fix",
            head_repo="daming-os/daming-os",
            base_repo="daming-os/daming-os",
            pr_author="google-labs-jules[bot]",
        )
        self.assertEqual(code, 0)
        self.assertEqual(outputs.get("is_jules"), "true")

    def test_valid_jules_branch_pr_accepted(self):
        # Same repo, google-labs-jules, matching 15 digit branch
        code, outputs, stdout = self._run_identify_script(
            body="Automated update",
            branch="jules-123456789012345",
            head_repo="daming-os/daming-os",
            base_repo="daming-os/daming-os",
            pr_author="google-labs-jules",
        )
        self.assertEqual(code, 0)
        self.assertEqual(outputs.get("is_jules"), "true")


if __name__ == "__main__":
    unittest.main()
