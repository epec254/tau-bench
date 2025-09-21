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

## Output Format

VERDICT: [PASS/FAIL]

REASONING: Specific evidence with trace locations showing what went wrong/right to help developers improve the system.