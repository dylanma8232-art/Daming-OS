import ast
import os
import shutil
import logging
import subprocess
import threading
import time
import uuid
from typing import Tuple, Optional
from ..config import config

logger = logging.getLogger("daming_os.growth.sandbox")

class SafetyVisitor(ast.NodeVisitor):
    """AST NodeVisitor to explicitly block unsafe imports and functions."""
    def __init__(self):
        self.is_safe = True
        self.errors = []
        self.blocked_imports = {"subprocess", "os", "pty"}
        self.blocked_functions = {"getattr"}

    def visit_Import(self, node):
        for alias in node.names:
            base_module = alias.name.split('.')[0]
            if base_module in self.blocked_imports:
                self.is_safe = False
                self.errors.append(f"Blocked import: {alias.name} at line {node.lineno}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            base_module = node.module.split('.')[0]
            if base_module in self.blocked_imports:
                self.is_safe = False
                self.errors.append(f"Blocked import from: {node.module} at line {node.lineno}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.blocked_functions:
                self.is_safe = False
                self.errors.append(f"Blocked function call: {node.func.id} at line {node.lineno}")
        self.generic_visit(node)

class SandboxGate:
    """
    Physical Sandbox and AST Validation Gate for Evolution Proposals.
    Ensures safe modification of Agent code before atomic deployment.
    """
    def __init__(self):
        self.sandbox_dir = getattr(config, "SANDBOX_BASE_DIR", "/tmp/sandbox")
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self._start_gc_thread()

    def _start_gc_thread(self):
        """Implement a background GC cleanup mechanism for the /tmp/sandbox/evo-<id> folders."""
        def gc_worker():
            while True:
                time.sleep(3600)  # Run GC every hour
                now = time.time()
                try:
                    for entry in os.listdir(self.sandbox_dir):
                        if entry.startswith("evo-"):
                            entry_path = os.path.join(self.sandbox_dir, entry)
                            if os.path.isdir(entry_path):
                                # Clean up if older than 24 hours
                                stat = os.stat(entry_path)
                                if now - stat.st_mtime > 86400:
                                    shutil.rmtree(entry_path, ignore_errors=True)
                                    logger.info(f"GC cleaned up sandbox: {entry_path}")
                except Exception as e:
                    logger.error(f"GC Error: {e}")

        gc_thread = threading.Thread(target=gc_worker, daemon=True)
        gc_thread.start()

    def validate_ast(self, source_code: str) -> Tuple[bool, str]:
        """Validate if the proposed code is syntactically sound and safe using AST."""
        try:
            tree = ast.parse(source_code)
            visitor = SafetyVisitor()
            visitor.visit(tree)
            if not visitor.is_safe:
                return False, "\n".join(visitor.errors)
            return True, "AST Validation Passed"
        except SyntaxError as e:
            return False, f"Syntax Error: {e.msg} at line {e.lineno}"
        except Exception as e:
            return False, f"AST Parsing Error: {str(e)}"

    def run_smoke_test(self, file_name: str, source_code: str, timeout: int = 30, evo_id: Optional[str] = None) -> Tuple[bool, str]:
        """Run the proposed code in an isolated sandbox directory."""
        if evo_id is None:
            evo_id = str(uuid.uuid4())
            
        test_dir = os.path.join(self.sandbox_dir, f"evo-{evo_id}")
        os.makedirs(test_dir, exist_ok=True)
        
        target_path = os.path.join(test_dir, file_name)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(source_code)
            
        logger.info(f"Running smoke test on {target_path}...")
        
        try:
            # Physically execute the file using subprocess
            result = subprocess.run(
                ["python3", target_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=test_dir
            )
            
            if result.returncode == 0:
                output = f"Smoke test passed.\nSTDOUT:\n{result.stdout}"
                return True, output
            else:
                error_msg = f"Smoke test failed (exit code {result.returncode}).\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                # Return the error immediately so the caller can retry up to 2 times
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            return False, f"Smoke test timed out after {timeout} seconds."
        except Exception as e:
            return False, f"Error executing smoke test: {str(e)}"
        # Note: No finally block with rmtree here anymore, letting GC or caller handle cleanup
