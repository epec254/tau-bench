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


class AgenticJudgeSignature(dspy.Signature):
    """
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
    """

    messages: str = dspy.InputField(desc="The conversation log to evaluate as a JSON string.  Includes all user, agent, and tool messages.")
    policy: str = dspy.InputField(desc="The policy that defines expected agent behavior")
    verdict: Literal["PASS", "FAIL"] = dspy.OutputField(desc="Either PASS or FAIL based on evaluation criteria")
    debug_info: str = dspy.OutputField(desc="Explanation of why the verdict was reached to aid in a developer in identifying what went wrong (or right) so they can fix the issue. Includes specific messages locations (the jq query to find the data within the messages input) and evidence (specific violations of the policy or criteria not met).")



def load_simulations(file_path: str) -> Tuple[str, list[Dict[str, Any]]]:
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


def judge_rollout(rollout: Dict[str, Any], policy: str):

    with mlflow.start_span() as span:
        span.set_inputs({"rollout": rollout, "policy": policy})
        messages_str = json.dumps(rollout.get("messages"))

        if not messages_str:
            raise ValueError(f"Messages field is missing or empty in the rollout: {rollout}")

        result = telecom_judge(messages=messages_str, policy=policy)
        span.set_outputs(result.toDict())

    return result.toDict()



# Example usage
if __name__ == "__main__":
    # Example configuration

    dspy.configure(lm=dspy.LM(JUDGE_MODEL, temperature=1.0, max_tokens=20000))

    telecom_judge = dspy.ChainOfThought(AgenticJudgeSignature)

    simulations, policy, raw_data = load_simulations("data/simulations/2025-09-21T13:52:54.208346_telecom_llm_agent_gpt-5_user_simulator_gpt-5_rollouts_only.json")


    for i, rollout in enumerate(simulations):
        result = judge_rollout(rollout=rollout, policy=policy)

        # Add judgment to the simulation in raw_data
        raw_data["simulations"][i]["judgment"] = {
            "verdict": result["verdict"],
            "debug_info": result["debug_info"],
            "reasoning": result["reasoning"],
            "judge_model": JUDGE_MODEL,
            "timestamp": datetime.now().isoformat()
        }

        # print(result)

    # Save updated data to new file
    input_file = "data/simulations/2025-09-21T13:52:54.208346_telecom_llm_agent_gpt-5_user_simulator_gpt-5_rollouts_only.json"
    output_file = input_file.replace(".json", "_with_judgments.json")

    with open(output_file, 'w') as f:
        json.dump(raw_data, f, indent=2)

    print(f"Saved judgments to: {output_file}")