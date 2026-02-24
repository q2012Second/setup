"""MCP server wrapping Codex CLI for Claude Code.

Exposes codex exec and codex exec review as structured MCP tools,
eliminating the need for Claude to construct raw Bash commands.
"""

import asyncio
import json
import logging
import tomllib
from functools import lru_cache
from pathlib import Path

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "codex-cli",
    instructions=(
        "Wraps the Codex CLI for non-interactive execution and code review. "
        "Use review_plan() and review_code() for common review workflows, "
        "or codex_exec() and codex_review() for direct CLI access."
    ),
)

CODEX_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
DEFAULT_TIMEOUT = 900  # 15 minutes
FALLBACK_MODEL = "gpt-5.3-codex"

PLAN_REVIEW_PROMPT_TEMPLATE = """\
You are reviewing an implementation plan for production readiness. \
Your job is to find real problems — be thorough and critical.

PROBLEM STATEMENT:
{problem_statement}

IMPLEMENTATION PLAN:
{plan_content}

Read the plan above, then explore the actual codebase to verify the plan's \
assumptions. For each issue found, evaluate against these criteria:

1. FEASIBILITY: Can this plan actually be implemented against the current \
codebase? Are file paths, function names, class structures, and APIs correct?
2. MISSING STEPS: Are there steps the plan omits that are necessary for a \
working implementation? Missing migrations, config changes, import updates, \
dependency installs?
3. WRONG ASSUMPTIONS: Does the plan assume things about the codebase that \
aren't true? Wrong file locations, non-existent functions, incorrect signatures?
4. ORDERING: Are the steps in the right order? Will earlier steps break things \
that later steps depend on?
5. EDGE CASES: Does the plan miss error handling, boundary conditions, or \
failure modes that the codebase already handles elsewhere?
6. OVER-ENGINEERING: Does the plan introduce unnecessary complexity, \
abstractions, or indirection?
7. BACKWARD COMPATIBILITY: Will the plan break existing callers, APIs, tests, \
or data formats?
8. SECURITY: Does the plan introduce any security vulnerabilities?

Format your response as a numbered list of findings. For each finding:
- Which plan step it refers to
- Severity: CRITICAL (blocks implementation) / HIGH (will cause bugs) / \
MEDIUM (should fix) / LOW (nice to have)
- Category (from the list above)
- Specific evidence from the codebase (file paths, line numbers, code snippets \
you found)
- A concrete suggestion for how to fix the plan

End your response with exactly one of:
- **PLAN APPROVED** — if no CRITICAL or HIGH findings
- **NEEDS REVISION** — if any CRITICAL or HIGH findings exist\
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _read_default_model() -> str:
    """Read default model from ~/.codex/config.toml."""
    try:
        with open(CODEX_CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        return config.get("model", FALLBACK_MODEL)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        logger.warning(
            "Could not read model from %s (%s); falling back to %s",
            CODEX_CONFIG_PATH,
            exc,
            FALLBACK_MODEL,
        )
        return FALLBACK_MODEL


def _resolve_model(model: str | None) -> str:
    """Return the explicit model or the default from config."""
    return model if model else _read_default_model()


def _resolve_output_path(
    output_file: str, working_directory: str | None
) -> Path:
    """Resolve output_file. If relative, resolve against working_directory."""
    path = Path(output_file)
    if not path.is_absolute() and working_directory:
        path = Path(working_directory) / path
    return path.resolve()


async def _run_codex(
    args: list[str], timeout: int, cwd: str | None = None
) -> tuple[str, str]:
    """Run a codex command asynchronously. Returns (stdout, stderr).

    Retries once on timeout. Raises on non-zero exit.
    Uses stdin=DEVNULL to prevent conflict with MCP stdio transport.
    """
    for attempt in range(2):
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
            cwd=cwd,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            if attempt == 0:
                logger.warning(
                    "Codex timed out after %ds, retrying...", timeout
                )
                continue
            raise TimeoutError(
                f"Codex timed out after {timeout}s on both attempts"
            )

        stdout = stdout_bytes.decode()
        stderr = stderr_bytes.decode()

        if process.returncode != 0:
            raise RuntimeError(
                f"Codex exited with code {process.returncode}.\n"
                f"stdout: {stdout[:2000]}\n"
                f"stderr: {stderr[:2000]}"
            )

        return stdout, stderr

    raise RuntimeError("Unexpected state in _run_codex")


def _parse_jsonl_review(stdout: str) -> str:
    """Parse JSONL from codex exec review --json.

    Looks for item.completed events with item.type == "agent_message".
    Returns the text of the last such event.
    Falls back to raw stdout if parsing fails.
    """
    last_message = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if (
            event.get("type") == "item.completed"
            and isinstance(event.get("item"), dict)
            and event["item"].get("type") == "agent_message"
        ):
            last_message = event["item"].get("text", "")

    if last_message is not None:
        return last_message

    logger.warning(
        "No item.completed agent_message found in JSONL; "
        "returning raw stdout"
    )
    return stdout


# ---------------------------------------------------------------------------
# Low-level tools
# ---------------------------------------------------------------------------


async def _codex_exec_impl(
    prompt: str,
    output_file: str | None = None,
    model: str | None = None,
    sandbox: str = "read-only",
    working_directory: str | None = None,
    ephemeral: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Core implementation for codex exec."""
    resolved_model = _resolve_model(model)

    args = ["codex", "exec", "-m", resolved_model, "--sandbox", sandbox]

    if working_directory:
        args.extend(["-C", working_directory])
    if ephemeral:
        args.append("--ephemeral")
    if output_file:
        resolved_path = _resolve_output_path(output_file, working_directory)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        args.extend(["-o", str(resolved_path)])

    args.append(prompt)

    stdout, _stderr = await _run_codex(args, timeout=timeout)

    if output_file:
        resolved_path = _resolve_output_path(output_file, working_directory)
        if resolved_path.exists():
            return f"Output written to {resolved_path}\n\n{resolved_path.read_text()}"
        return f"Output file expected at {resolved_path} but not found.\n\nstdout:\n{stdout}"

    return stdout


async def _codex_review_impl(
    working_directory: str,
    prompt: str | None = None,
    output_file: str | None = None,
    model: str | None = None,
    uncommitted: bool = False,
    base_branch: str | None = None,
    commit_sha: str | None = None,
    title: str | None = None,
    ephemeral: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Core implementation for codex exec review."""
    has_target = uncommitted or bool(base_branch) or bool(commit_sha)

    # Validate: at most one target selector
    target_count = sum([uncommitted, bool(base_branch), bool(commit_sha)])
    if target_count > 1:
        raise ValueError(
            "Only one target selector can be provided: "
            "uncommitted, base_branch, or commit_sha"
        )

    # Validate: prompt vs target selector mutual exclusivity
    if prompt and has_target:
        raise ValueError(
            "prompt and target selectors (uncommitted/base_branch/commit_sha) "
            "are mutually exclusive for codex exec review. "
            "Use title for context when using a target selector."
        )

    # Default to --uncommitted if nothing specified
    if not prompt and not has_target:
        uncommitted = True

    resolved_model = _resolve_model(model)

    args = ["codex", "exec", "review", "-m", resolved_model]

    # Target selectors (mutually exclusive with prompt)
    if commit_sha:
        args.extend(["--commit", commit_sha])
    elif base_branch:
        args.extend(["--base", base_branch])
    elif uncommitted:
        args.append("--uncommitted")

    if title:
        args.extend(["--title", title])
    if ephemeral:
        args.append("--ephemeral")

    args.append("--json")

    # Prompt as positional arg (only when no target selector)
    if prompt:
        args.append(prompt)

    stdout, _stderr = await _run_codex(
        args, timeout=timeout, cwd=working_directory
    )
    content = _parse_jsonl_review(stdout)

    if output_file:
        resolved_path = _resolve_output_path(output_file, working_directory)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(content)
        return f"Review written to {resolved_path}"

    return content


@mcp.tool
async def codex_exec(
    prompt: str,
    output_file: str | None = None,
    model: str | None = None,
    sandbox: str = "read-only",
    working_directory: str | None = None,
    ephemeral: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Run codex exec (non-interactive execution) with a prompt.

    Args:
        prompt: The instruction prompt for Codex.
        output_file: Path to write the last agent message.
        model: Model override. Defaults to ~/.codex/config.toml model.
        sandbox: Sandbox mode: "read-only", "workspace-write", or
            "danger-full-access". Defaults to "read-only".
        working_directory: Directory for Codex to use as working root.
            Passed via -C flag.
        ephemeral: If True, don't persist session files. Defaults to True.
        timeout: Timeout in seconds. Defaults to 600 (10 minutes).
    """
    return await _codex_exec_impl(
        prompt=prompt,
        output_file=output_file,
        model=model,
        sandbox=sandbox,
        working_directory=working_directory,
        ephemeral=ephemeral,
        timeout=timeout,
    )


@mcp.tool
async def codex_review(
    working_directory: str,
    prompt: str | None = None,
    output_file: str | None = None,
    model: str | None = None,
    uncommitted: bool = False,
    base_branch: str | None = None,
    commit_sha: str | None = None,
    title: str | None = None,
    ephemeral: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Run codex exec review against a repository.

    working_directory is required — specifies the git repo to review.

    IMPORTANT: prompt and target selectors (uncommitted, base_branch,
    commit_sha) are mutually exclusive. You cannot pass both.
    When using a target selector, pass context via the title parameter.

    If neither prompt nor any target selector is provided,
    defaults to --uncommitted.

    Args:
        working_directory: Git repo directory to review (required).
        prompt: Custom review instructions. Mutually exclusive with
            target selectors.
        output_file: Path to write the review output.
        model: Model override. Defaults to ~/.codex/config.toml model.
        uncommitted: Review staged, unstaged, and untracked changes.
        base_branch: Review changes against a specific base branch.
        commit_sha: Review changes introduced by a specific commit.
        title: Optional context string passed via --title flag.
            Can combine with target selectors.
        ephemeral: If True, don't persist session files. Defaults to True.
        timeout: Timeout in seconds. Defaults to 600 (10 minutes).
    """
    return await _codex_review_impl(
        working_directory=working_directory,
        prompt=prompt,
        output_file=output_file,
        model=model,
        uncommitted=uncommitted,
        base_branch=base_branch,
        commit_sha=commit_sha,
        title=title,
        ephemeral=ephemeral,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# High-level tools
# ---------------------------------------------------------------------------


@mcp.tool
async def review_plan(
    problem_statement: str,
    plan_content: str,
    output_file: str,
    model: str | None = None,
    working_directory: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Review an implementation plan using Codex in a read-only sandbox.

    Composes the standard plan review prompt and runs codex exec.
    Codex explores the codebase to verify the plan's assumptions.

    Args:
        problem_statement: The problem being solved (content of problem.md).
        plan_content: The implementation plan (content of plan.md).
        output_file: Path to write the review output.
        model: Model override. Defaults to ~/.codex/config.toml model.
        working_directory: Project directory for Codex to explore.
        timeout: Timeout in seconds. Defaults to 600 (10 minutes).
    """
    prompt = PLAN_REVIEW_PROMPT_TEMPLATE.format(
        problem_statement=problem_statement,
        plan_content=plan_content,
    )
    return await _codex_exec_impl(
        prompt=prompt,
        output_file=output_file,
        model=model,
        sandbox="read-only",
        working_directory=working_directory,
        ephemeral=True,
        timeout=timeout,
    )


@mcp.tool
async def review_code(
    working_directory: str,
    output_file: str | None = None,
    task_context: str | None = None,
    model: str | None = None,
    uncommitted: bool = True,
    base_branch: str | None = None,
    commit_sha: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Run a code review using Codex's built-in review.

    Uses codex exec review with target selectors (--uncommitted by default).
    Pass task_context to provide additional context via --title flag
    (e.g., "Read tasks/foo/plan.md and tasks/foo/problem.md for context").

    Does NOT accept a custom review prompt — Codex's built-in review
    already covers security, bugs, performance, etc.

    Args:
        working_directory: Git repo directory to review (required).
        output_file: Path to write the review output.
        task_context: Context string passed via --title flag.
        model: Model override. Defaults to ~/.codex/config.toml model.
        uncommitted: Review uncommitted changes. Defaults to True.
        base_branch: Review changes against a base branch.
        commit_sha: Review a specific commit.
        timeout: Timeout in seconds. Defaults to 600 (10 minutes).
    """
    return await _codex_review_impl(
        working_directory=working_directory,
        prompt=None,
        output_file=output_file,
        model=model,
        uncommitted=uncommitted,
        base_branch=base_branch,
        commit_sha=commit_sha,
        title=task_context,
        ephemeral=True,
        timeout=timeout,
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
