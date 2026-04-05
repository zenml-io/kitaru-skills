"""Coding agent flow — Kitaru quickstart demo.

Demonstrates: @flow, @checkpoint, wait(), log(), memory
Flow shape: analyze issue → generate patch → approve → apply patch
"""

import time

from kitaru import checkpoint, flow, log, memory, wait


@checkpoint
def analyze_issue(issue: str) -> dict:
    """Simulate analyzing a code issue."""
    log(step="analyze", issue=issue)
    time.sleep(1)
    return {
        "issue": issue,
        "files": ["src/main.py", "src/utils.py"],
        "severity": "medium",
        "root_cause": f"Incorrect handling of edge case in {issue}",
    }


@checkpoint
def generate_patch(analysis: dict) -> str:
    """Simulate generating a code patch."""
    log(step="generate_patch", files=analysis["files"])
    # --- QUICKSTART CRASH: remove this line to fix the simulated failure ---
    raise Exception("Simulated timeout calling code generation model")
    # --- end crash ---
    time.sleep(2)
    patch = (
        f"--- a/src/main.py\n"
        f"+++ b/src/main.py\n"
        f"@@ -42,3 +42,5 @@\n"
        f"-    return process(data)\n"
        f"+    if not data:\n"
        f'+        raise ValueError("Empty input")\n'
        f"+    return process(data)\n"
    )
    return patch


@checkpoint
def apply_patch(patch: str) -> str:
    """Simulate applying the approved patch."""
    log(step="apply", patch_length=len(patch))
    time.sleep(1)
    return f"Patch applied successfully ({len(patch)} chars)"


@flow
def coding_flow(issue: str) -> str:
    """Analyze an issue, generate a patch, review, and apply it."""
    previous_issue = memory.get("last_issue")
    if previous_issue:
        log(returning_user=True, previous_issue=previous_issue)

    analysis = analyze_issue(issue)
    patch = generate_patch(analysis)

    approved = wait(
        name="approve_merge",
        question=f"Approve patch for '{issue}'? (true/false)",
        schema=bool,
    )

    if not approved:
        return f"Patch for '{issue}' was rejected"

    result = apply_patch(patch)
    memory.set("last_issue", issue)
    return result


if __name__ == "__main__":
    import sys

    issue = sys.argv[1] if len(sys.argv) > 1 else "fix null pointer in data processor"
    handle = coding_flow.run(issue)
    print(f"Execution ID: {handle.exec_id}")
    print(f"Status: {handle.status}")
    result = handle.wait()
    print(f"Result: {result}")
