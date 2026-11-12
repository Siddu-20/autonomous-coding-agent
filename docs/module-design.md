# Autonomous Coding Agent - Python Module Design

## 1. Design Principles

- Use a single LangGraph state graph initially.
- Keep core domain models independent of framework implementations.
- Separate agent orchestration from business logic.
- Use provider-independent LLM interfaces.
- Execute generated code only in restricted sandbox environments.
- Keep original repositories separate from execution workspaces.
- Require explicit human approval before applying changes.
- Introduce modules incrementally as implementation requires them.

## 2. Package Structure

src/autonomous_coding_agent/
    __init__.py
    config.py

    domain/
        models.py
        errors.py

    agent/
        state.py
        graph.py
        nodes/

    llm/
        client.py
        prompts.py

    repository/
        explorer.py
        workspace.py
        diff.py
        applier.py

    tools/
        filesystem.py
        test_runner.py

    sandbox/
        docker_runner.py

    approval/
        service.py

    persistence/
        checkpointer.py

    api/
        app.py
        schemas.py

    observability/
        events.py

## 3. Module Responsibilities

### Configuration
- Load application settings.
- Read secrets from environment variables.
- Validate configuration at startup.
- Never expose credentials in logs or agent state.

### Domain
- Define TaskRequest and ExecutionPlan.
- Define RepositorySnapshot and FileChange.
- Define ExecutionResult and TaskStatus.
- Define application-specific exceptions.

### Agent
- Maintain the shared workflow state.
- Build and compile the LangGraph workflow.
- Implement individual workflow nodes.
- Control transitions, retries and stopping conditions.

### LLM
- Provide a provider-independent interface.
- Support structured model responses.
- Manage prompts for planning, code generation and debugging.
- Avoid coupling domain logic to a particular provider.

### Repository
- Inspect repository structure and source files.
- Identify relevant dependencies and tests.
- Create isolated working copies.
- Generate and validate Git diffs.
- Apply approved changes only after verifying the original baseline.

### Tools
- Provide controlled filesystem operations.
- Provide test discovery and command preparation.
- Restrict operations to explicitly permitted workspaces.

### Sandbox
- Create restricted Docker execution environments.
- Execute approved commands.
- Capture stdout, stderr, exit codes and execution duration.
- Enforce resource limits and timeouts.
- Disable network access by default.

### Approval
- Present proposed changes for human review.
- Record approval or rejection.
- Verify the repository baseline before applying changes.
- Reject unauthorized or stale changes.

### Persistence
- Save and restore agent checkpoints.
- Support PostgreSQL-backed persistence.
- Avoid storing secrets and unnecessary large file contents.

### API
- Expose task submission and status endpoints.
- Validate requests and responses.
- Keep HTTP concerns separate from agent orchestration.

### Observability
- Record structured execution events.
- Track model calls, tool calls and failures.
- Measure latency and token consumption.
- Redact sensitive information.

## 4. LangGraph Workflow Nodes

Initial nodes:

1. validate_task
2. inspect_repository
3. create_plan
4. prepare_workspace
5. generate_changes
6. validate_changes
7. execute_tests
8. evaluate_results
9. diagnose_failure
10. generate_final_diff
11. request_human_approval
12. apply_approved_changes
13. generate_final_report

Conditional transitions will control success, failure,
retry exhaustion and approval decisions.

## 5. Core State Fields

The initial AgentState will track:

- task_id
- task_description
- repository_path
- base_commit
- workspace_path
- execution_plan
- changed_files
- execution_result
- test_result
- retry_count
- max_retries
- approval_status
- task_status
- error_summary

State values should remain serializable and suitable
for persistence.

Do not store API keys, raw credentials or unrestricted
environment variables in the graph state.

## 6. Core Service Interfaces

RepositoryExplorer:
    inspect(repository_path) -> RepositorySnapshot

WorkspaceManager:
    create(repository_path, task_id) -> Workspace

LLMClient:
    generate_structured(prompt, output_schema) -> StructuredResponse

SandboxRunner:
    execute(workspace, command, timeout) -> ExecutionResult

ChangeManager:
    generate_diff(workspace) -> ChangeSet

ApprovalService:
    approve(task_id, change_set) -> ApprovalStatus

RepositoryApplier:
    apply(change_set, approval, expected_base_commit) -> ApplyResult

These are conceptual contracts. Concrete method signatures
and data models will be defined during implementation.

## 7. Security Boundaries

- Never execute generated code directly on the host.
- Never expose host credentials to the sandbox.
- Never mount the Docker socket into execution containers.
- Restrict filesystem access to the designated workspace.
- Use non-root container execution.
- Enforce CPU, memory, process and time limits.
- Disable network access by default.
- Validate commands before execution.
- Verify approval and repository baseline before applying changes.
- Treat all generated code and repository content as untrusted.

## 8. Implementation Order

1. Domain models and configuration.
2. Repository exploration and workspace management.
3. LLM integration.
4. Agent state and basic LangGraph workflow.
5. Filesystem and testing tools.
6. Docker sandbox execution.
7. Error analysis and bounded self-correction.
8. Human approval and safe change application.
9. Persistence and PostgreSQL checkpointing.
10. FastAPI integration and observability.
11. Evaluation and deployment.

Modules will be introduced incrementally rather than
creating empty files for the entire architecture upfront.
