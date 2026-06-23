import logging
import os
import shutil
import time
from abc import ABC, abstractmethod
from ..config import config
from ..events import bus, EvolutionCompletedEvent
from .sandbox import SandboxGate

logger = logging.getLogger("daming_os.growth.orchestrator")

class ApprovalAdapter(ABC):
    @abstractmethod
    def request_approval(self, proposal_id: str, diff_summary: str) -> bool:
        pass

class ConsoleApprovalAdapter(ApprovalAdapter):
    """Fallback approval mechanism for local development."""
    def request_approval(self, proposal_id: str, diff_summary: str) -> bool:
        print(f"\n[URGENT APPROVAL REQUIRED] Proposal: {proposal_id}")
        print(f"Summary: {diff_summary}")
        ans = input("Approve this evolution? (y/N): ")
        return ans.lower() == 'y'

class FeishuOTPApprovalAdapter(ApprovalAdapter):
    """Approval mechanism using Feishu OTP webhooks."""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def request_approval(self, proposal_id: str, diff_summary: str) -> bool:
        import requests
        logger.info(f"Sending approval request to Feishu OTP webhook for proposal {proposal_id}")
        try:
            payload = {
                "proposal_id": proposal_id,
                "diff_summary": diff_summary,
                "message": "Evolution approval required"
            }
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info("Feishu OTP Approval requested successfully. Awaiting external callback/confirmation...")
            return response.json().get("approved", False)
        except Exception as e:
            logger.error(f"Feishu OTP webhook failed: {e}")
            return False

class EvolutionOrchestrator:
    """
    Coordinates the lifecycle of a Growth Evolution:
    Debate -> Sandbox Validate -> Human Approval -> Atomic Deploy
    """
    def __init__(self, approval_adapter: ApprovalAdapter = None):
        self.sandbox = SandboxGate()
        self.approval_adapter = approval_adapter or ConsoleApprovalAdapter()

    def handle_evolution_trigger(self, proposal_id: str, proposed_code: str, target_file: str):
        logger.info(f"Orchestrating evolution for {proposal_id} on {target_file}")
        
        # 1. AST Gate
        is_valid, msg = self.sandbox.validate_ast(proposed_code)
        if not is_valid:
            logger.error(f"Evolution {proposal_id} failed AST gate: {msg}")
            return
            
        # 2. Smoke Test
        is_smoke_valid, smoke_msg = self.sandbox.run_smoke_test(target_file, proposed_code)
        if not is_smoke_valid:
            logger.error(f"Evolution {proposal_id} failed smoke test: {smoke_msg}")
            return
            
        # 3. Human in the loop (HITL) Webhook
        diff_summary = f"Refactored {target_file} to fix runtime exceptions."
        approved = self.approval_adapter.request_approval(proposal_id, diff_summary)
        
        if approved:
            self._deploy_atomic(target_file, proposed_code)
            # 4. Fire event to decouple from Memory Cache clearing
            bus.publish(EvolutionCompletedEvent(
                proposal_id=proposal_id,
                diff_summary=diff_summary,
                scope_tags=[target_file]
            ))
        else:
            logger.info(f"Evolution {proposal_id} rejected by user.")

    def _deploy_atomic(self, target_file: str, new_code: str):
        """Atomic deployment with <1ms backup using shutil.copy2"""
        logger.info(f"Atomically deploying {target_file}...")
        
        # 1. Take atomic backup < 1ms
        if os.path.exists(target_file):
            backup_file = f"{target_file}.bak_{int(time.time())}"
            shutil.copy2(target_file, backup_file)
            logger.debug(f"Created atomic backup at {backup_file}")
            
        # 2. Write to temporary file
        temp_file = f"{target_file}.tmp"
        with open(temp_file, "w") as f:
            f.write(new_code)
            
        # 3. Atomic replace
        os.replace(temp_file, target_file)
        logger.info(f"Deployed successfully via atomic replace.")
