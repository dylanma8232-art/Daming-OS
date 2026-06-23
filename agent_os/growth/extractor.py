import logging
import json
import concurrent.futures
from typing import List, Dict, Any, Optional
from ..llm import LLMProvider
from ..config import config

logger = logging.getLogger("agent_os.growth.extractor")

class ExperienceExtractor:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = LLMProvider(model_name=model_name)

    def red_agent(self, cluster_text: str) -> str:
        """Finds flaws and problems."""
        system_prompt = "You are the Red Agent. Your task is to critique the following cluster of events and identify any flaws, anti-patterns, or missing details."
        return self.llm.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Events Cluster:\n{cluster_text}"}
            ],
            temperature=0.3
        )

    def blue_agent(self, cluster_text: str) -> str:
        """Writes the fix or reusable pattern."""
        system_prompt = "You are the Blue Agent. Your task is to analyze the following cluster of events and propose a constructive fix, reusable pattern, or best practice."
        return self.llm.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Events Cluster:\n{cluster_text}"}
            ],
            temperature=0.3
        )

    def white_agent(self, cluster_text: str, flaws: str, fix: str) -> Dict[str, Any]:
        """Judges the outcome and formats the final proposal."""
        system_prompt = (
            "You are the White Agent (Judge). Review the event cluster, the Red Agent's critique (flaws), and the Blue Agent's proposal (fix).\n"
            "Combine their output into a final evolution proposal in JSON format.\n"
            "Requirements:\n"
            "1. pattern: A concise, reusable pattern or practice.\n"
            "2. lesson: What was learned (2-3 sentences with specific details).\n"
            "3. action_item: A concrete, actionable next step.\n"
            "4. confidence: 0.0-1.0 confidence score based on event consistency.\n"
            "Output valid JSON only, no markdown formatting."
        )

        user_content = (
            f"Here are the related growth events:\n\n{cluster_text}\n\n"
            f"Red Agent (Flaws):\n{flaws}\n\n"
            f"Blue Agent (Fix):\n{fix}\n\n"
            "Extract a structured experience and output as JSON:\n"
            "{\n"
            '  "pattern": "reusable pattern",\n'
            '  "lesson": "what was learned",\n'
            '  "action_item": "concrete next step",\n'
            '  "confidence": 0.85,\n'
            '  "source_events": [{"index": 1}]\n'
            "}\n"
        )

        try:
            result = self.llm.generate_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3
            )
            return result
        except Exception as e:
            logger.error(f"White agent JSON generation failed: {e}")
            return {}

    def extract_from_cluster(self, cluster: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Extract structured experience from a cluster of events using a Cabinet Swarm pattern.
        """
        if not cluster:
            return None

        event_summaries = []
        for i, ev in enumerate(cluster, 1):
            summary = {
                "index": i,
                "type": ev.get("type", ""),
                "context": ev.get("context", ""),
                "reflection": ev.get("reflection", ""),
                "severity": ev.get("severity", ""),
                "timestamp": ev.get("timestamp", ""),
            }
            event_summaries.append(summary)

        cluster_text = json.dumps(event_summaries, ensure_ascii=False, indent=2)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_red = executor.submit(self.red_agent, cluster_text)
            future_blue = executor.submit(self.blue_agent, cluster_text)
            
            flaws = future_red.result()
            fix = future_blue.result()

        result = self.white_agent(cluster_text, flaws, fix)

        if not result:
            return None

        # Validate fields
        required = ["pattern", "lesson", "action_item", "confidence"]
        for key in required:
            if key not in result:
                logger.warning(f"LLM returned missing field: {key}")
                result[key] = "" if key != "confidence" else 0.5

        # Clamp confidence
        result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
        result["source_events"] = event_summaries

        return result
