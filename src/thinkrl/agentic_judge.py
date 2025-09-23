"""
DSPy module for evaluating LLM agent performance in telecommunications support scenarios.

This module implements an agentic judge that evaluates whether an LLM agent FAILfully
resolved a customer's issue according to company policy.
"""

import os
from typing import Dict, Any, Literal, Tuple
import json
import dspy
import dotenv
import mlflow
from datetime import datetime
import argparse
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path

from thinkrl.utils.tracing import enable_tracing


dotenv.load_dotenv()

JUDGE_MODEL = os.getenv("JUDGE_MODEL")

enable_tracing()

if not JUDGE_MODEL:
    raise ValueError("JUDGE_MODEL environment variable not set. Please set it to the desired LLM model for the judge.")

# class JudgmentResult(BaseModel):
#     """Output structure for the agentic judge."""
#     verdict: str = Field(description="Either 'FAIL' or 'FAIL'")
#     rationale: str = Field(description="Detailed explanation with specific evidence and trace locations")


signature_v1 = """
    # Technical Support Evaluation

    Evaluate whether an LLM agent successfully resolved a customer's telecommunications issue.

    ## PASS Requirements

    The agent must demonstrate ALL of:

    ### 1. Issue Resolution
    - Customer confirmed fix works
    OR
    - Properly escalated to human support

    ### 2. Correct Tool Usage
    - Used appropriate tools based on the policy and user's query
    - Accurately interpreted and conveyed tool outputs
    - Followed logical sequence (diagnose → fix → escalate if needed)

    ### 3. Sound Troubleshooting
    - Maintained context throughout the conversation
    - Adapted based on results
    - No loops or contradictions
    - Recognized when to escalate

    ### 4. Policy Adherence
    - Followed all guidelines in the provided policy

    ## FAIL Triggers

    ANY of these = automatic FAIL:

    ### Illogical behavior
    - Lost context mid-conversation
    - Misinterpreted clear diagnostics
    - Applied unrelated fixes
    - Missed resolution confirmation
    - Ignored relevant tool outputs
    - Continued after resolution

    ### Poor LLM Patterns
    - Hallucinated tool results or capabilities
    - Conversation loops
    - Failed to use tools when needed
    - Made up technical information
    - Called non-existent tools

    ### Policy Violations
    - Ignored or did not follow the policy
    """

class AgenticJudgeSignature(dspy.Signature):
    """
    Evaluate whether an LLM agent successfully addressed a customer's issue.

    PASS requirements:

    1. The conversation must have one of the following present:
        - Customer confirmed fix works
        - LLM agent properly escalated to human support

    2. The LLM agent must follow all relevant guidelines in the provided policy.

    3. The LLM agent's responses must be grounded in the tool outputs, the user's queries, and the policies.  It must not hallucinate or make up information.

    4. The LLM agent must:
        - Maintain context throughout the conversation
        - Adapt based on user inputs and tool results
        - Not have any loops or contradictions
    """

    messages: str = dspy.InputField(desc="The conversation log to evaluate as a JSON string.  Includes all user, agent, and tool messages.")
    policy: str = dspy.InputField(desc="The policy that defines expected agent behavior")
    verdict: Literal["PASS", "FAIL"] = dspy.OutputField(desc="PASS if the an LLM agent successfully addressed a customer's issue based on the PASS requirements; FAIL otherwise.")
    debug_info: str = dspy.OutputField(desc="Explanation of why the verdict was reached to aid in a developer in identifying what went wrong (or right) so they can fix the issue. Includes specific messages locations (the jq query to find the data within the messages input) and evidence (specific violations of the policy or criteria not met).")



def load_simulations(file_path: str) -> Tuple[list[Dict[str, Any]], str, Dict[str, Any]]:
    """Load simulation data from JSON file.

    Args:
        file_path: Path to the JSON file containing simulation data

    Returns:
        Dictionary containing the loaded simulation data
    """

    with open(file_path, 'r') as f:
        simulations_raw_data = json.load(f)

    policy = simulations_raw_data.get("info", {}).get("environment_info", {}).get("policy", "")

    if not policy:
        raise ValueError("Policy field is missing in the simulation data.")

    simulations = simulations_raw_data.get("simulations", [])

    if len(simulations) == 0:
        raise ValueError("No simulations found in the simulation data.")

    return simulations, policy, simulations_raw_data


def judge_rollout(rollout: Dict[str, Any], policy: str, judge):
    with mlflow.start_span(name="agentic_judge") as span:
        mlflow.update_current_trace(tags={"agentic_judge": "yes"}, request_preview=f"{rollout.get('task_id', 'unknown')}:{rollout.get('id', 'unknown')}")
        span.set_inputs({"rollout": rollout, "policy": policy})
        messages_str = json.dumps(rollout.get("messages"))

        if not messages_str:
            raise ValueError(f"Messages field is missing or empty in the rollout: {rollout}")

        result = judge(messages=messages_str, policy=policy)
        mlflow.update_current_trace(response_preview=result.toDict().get("verdict", "unknown"))
        span.set_outputs(result.toDict())

    return result.toDict()


class SafeJSONWriter:
    """Thread-safe JSON writer that incrementally updates results."""

    def __init__(self, output_file: str, raw_data: Dict[str, Any]):
        self.output_file = output_file
        self.raw_data = raw_data.copy()
        self.lock = threading.Lock()
        self.backup_file = f"{output_file}.backup"

    def write_judgment(self, simulation_index: int, judgment: Dict[str, Any]):
        """Safely write a judgment result and update the JSON file."""
        with self.lock:
            # Update in-memory data
            self.raw_data["simulations"][simulation_index]["judgment"] = judgment

            # Create backup of current file if it exists
            if Path(self.output_file).exists():
                Path(self.output_file).rename(self.backup_file)

            try:
                # Write updated data
                with open(self.output_file, 'w') as f:
                    json.dump(self.raw_data, f, indent=2)

                # Remove backup on successful write
                if Path(self.backup_file).exists():
                    Path(self.backup_file).unlink()

            except Exception as e:
                # Restore backup if write failed
                if Path(self.backup_file).exists():
                    Path(self.backup_file).rename(self.output_file)
                raise e


def process_simulation_batch(batch_info: Tuple[int, Dict[str, Any]], policy: str, judge, writer: SafeJSONWriter, judge_model: str) -> Tuple[int, str]:
    """Process a single simulation and write result safely."""
    simulation_index, rollout = batch_info

    try:
        result = judge_rollout(rollout=rollout, policy=policy, judge=judge)

        judgment = {
            "verdict": result["verdict"],
            "debug_info": result["debug_info"],
            "reasoning": result["reasoning"],
            "judge_model": judge_model,
            "timestamp": datetime.now().isoformat()
        }

        writer.write_judgment(simulation_index, judgment)
        return simulation_index, result['verdict']

    except Exception as e:
        # Write error information
        judgment = {
            "verdict": "ERROR",
            "debug_info": f"Error during judgment: {str(e)}",
            "reasoning": "Processing failed",
            "judge_model": judge_model,
            "timestamp": datetime.now().isoformat()
        }
        writer.write_judgment(simulation_index, judgment)
        return simulation_index, "ERROR"



def main():
    parser = argparse.ArgumentParser(description='Judge LLM agent performance in simulation data')
    parser.add_argument('input_file', help='Input JSON file path containing simulation data')
    parser.add_argument('--max-simulations', type=int, help='Maximum number of simulations to process (default: process all)')
    parser.add_argument('--max-workers', type=int, default=4, help='Maximum number of concurrent workers (default: 4)')

    args = parser.parse_args()

    # Configure DSPy
    dspy.configure(lm=dspy.LM(JUDGE_MODEL, temperature=1.0, max_tokens=20000))
    telecom_judge = dspy.ChainOfThought(AgenticJudgeSignature)

    # Load simulations
    simulations, policy, raw_data = load_simulations(args.input_file)

    # Limit simulations if max_simulations is specified
    simulations_to_process = simulations[:args.max_simulations] if args.max_simulations else simulations
    total_simulations = len(simulations_to_process)

    print(f"Processing {total_simulations} of {len(simulations)} simulations with {args.max_workers} workers")

    # Prepare output file and writer
    output_file = args.input_file.replace(".json", "_with_judgments.json")
    writer = SafeJSONWriter(output_file, raw_data)

    # Create simulation batches with indices
    simulation_batches = [(i, rollout) for i, rollout in enumerate(simulations_to_process)]

    # Process simulations concurrently
    completed_count = 0
    verdict_counts = {"PASS": 0, "FAIL": 0, "ERROR": 0}
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # Submit all jobs
        future_to_simulation = {
            executor.submit(process_simulation_batch, batch, policy, telecom_judge, writer, JUDGE_MODEL): batch[0]
            for batch in simulation_batches
        }

        # Process completed futures
        for future in as_completed(future_to_simulation):
            simulation_index = future_to_simulation[future]
            try:
                result_index, verdict = future.result()
                completed_count += 1
                verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

                elapsed_time = time.time() - start_time
                rate = completed_count / elapsed_time if elapsed_time > 0 else 0

                print(f"Simulation {result_index + 1}/{total_simulations}: {verdict} "
                      f"[{completed_count}/{total_simulations} complete, {rate:.2f}/sec]")

            except Exception as e:
                print(f"Simulation {simulation_index + 1} failed with error: {e}")
                verdict_counts["ERROR"] = verdict_counts.get("ERROR", 0) + 1

    elapsed_time = time.time() - start_time
    print(f"\nCompleted in {elapsed_time:.2f} seconds")
    print(f"Results: {verdict_counts}")
    print(f"Saved judgments to: {output_file}")


if __name__ == "__main__":
    main()