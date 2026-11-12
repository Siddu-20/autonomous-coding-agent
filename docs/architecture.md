# Autonomous Coding Agent - Architecture

## 1. Objective

Build a production-style autonomous coding agent that can
understand software development tasks, inspect codebases,
generate code changes, execute tests, diagnose failures,
and deliver validated changes with human oversight.

## 2. High-Level Workflow

User Task
    -> Task Understanding
    -> Planning
    -> Codebase Exploration
    -> Code Generation
    -> Sandboxed Execution
    -> Result Inspection
    -> Self-Correction
    -> Final Diff Generation
    -> Human Approval
    -> Apply Changes
    -> Final Report

## 3. Core Components

### Task Understanding and Planning
- Interpret user requirements.
- Identify relevant files and dependencies.
- Generate an execution plan.
- Define task completion criteria.

### Codebase Explorer
- Inspect repository structure.
- Read and search source files.
- Identify dependencies and existing tests.
- Exclude sensitive files and unnecessary directories.

### Code Generation Agent
- Generate code modifications.
- Work inside an isolated workspace.
- Validate proposed patches.
- Avoid unrestricted filesystem access.

### Sandboxed Executor
- Execute code inside Docker containers.
- Run configured tests.
- Apply execution timeouts and resource limits.
- Run without network access by default.

### Inspector and Self-Correction
- Analyse execution output.
- Diagnose errors.
- Generate corrective changes.
- Limit retries and prevent infinite loops.

### Human Approval
- Present the final changes and execution results.
- Require explicit approval before modifying the original repository.
- Reject changes if the original repository has changed unexpectedly.

### Final Delivery
- Apply approved changes.
- Produce a summary of modifications.
- Report test results and remaining issues.

## 4. Agent Orchestration

LangGraph will manage the workflow using a stateful graph.

Initial execution flow:

START
  -> validate_task
  -> inspect_repository
  -> create_plan
  -> prepare_workspace
  -> generate_changes
  -> validate_changes
  -> execute_tests
  -> evaluate_results

If tests fail and retry limits remain:
  -> diagnose_failure
  -> generate_changes

If tests pass:
  -> generate_final_diff
  -> human_approval
  -> apply_changes_if_approved
  -> final_report
  -> END

If the retry limit is reached or execution cannot be validated:
  -> generate_final_diff
  -> generate_failure_report
  -> preserve_original_repository
  -> END

## 5. State Management

The agent state will track:
- Task identifier and user request
- Target repository information
- Repository baseline commit
- Execution plan
- Current workflow stage
- Files inspected and modified
- Proposed changes
- Tool execution results
- Test results
- Retry count
- Approval status
- Final task status

## 6. Security Requirements

- Never execute generated code directly on the host.
- Execute generated code in restricted containers.
- Run containers as non-root.
- Disable network access by default.
- Apply CPU, memory, process and execution-time limits.
- Do not expose API keys or host credentials to the sandbox.
- Never mount the Docker socket into execution containers.
- Require approval before modifying the original repository.

Docker is a baseline isolation mechanism, not a guarantee
against all container escapes or hostile-code attacks.

## 7. Initial Scope

Version 1 will support:
- Python repositories.
- Codebase inspection.
- Python code generation and modification.
- Automated test execution.
- Bounded self-correction.
- Human-approved changes.

Out of scope initially:
- Automatic Git commits and pushes.
- Automatic deployment.
- Unrestricted network access.
- Multi-language code execution.
- Unattended modifications to the original repository.

## 8. Technology Stack

- Python 3.12
- LangGraph
- Gemini / Claude API
- FastAPI
- Docker
- PostgreSQL
- Langfuse
- Pytest

## 9. Evaluation Metrics

- Task completion rate
- Test pass rate
- Code execution success rate
- Self-correction success rate
- Number of repair attempts
- Execution latency
- Token consumption
- Security policy violations
