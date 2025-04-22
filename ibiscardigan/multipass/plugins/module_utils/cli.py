"""CLI wrapper for calling the multipass command safely."""

import os
import subprocess
import json
from typing import TYPE_CHECKING

from . import types

if TYPE_CHECKING:
    from ansible.module_utils.basic import AnsibleModule


def run_multipass_command(
    args: list[str],
    check: bool = True,
    capture_output: bool = True,
    json_output: bool = False,
    module: "AnsibleModule" = None,
) -> dict[str, object]:
    """
    Runs a multipass CLI command and returns structured output.

    Args:
        args: The CLI arguments after `multipass`.
        check: Raise an error if the command fails.
        capture_output: Whether to capture stdout/stderr.
        json_output: If true, parse and include 'json' key in the result.
        module: Optional AnsibleModule for safe logging.

    Returns:
        A dictionary with keys: rc, stdout, stderr, and optionally json.

    Raises:
        MultipassCLIError: If the command fails or output can't be parsed.
    """
    base_cmd = ["multipass"] + args
    _log_debug(module, f"Executing: {' '.join(base_cmd)}")

    try:
        env = os.environ.copy()
        env["PATH"] = env.get("PATH", "") + ":/opt/homebrew/bin:/usr/local/bin"
        result = subprocess.run(
            base_cmd,
            capture_output=capture_output,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        _log_and_raise(module, "multipass binary not found in PATH")
    except (subprocess.SubprocessError, OSError) as exc:
        _log_and_raise(module, f"Unexpected error running multipass: {exc}")

    return _process_result(result, base_cmd, check, json_output, module)


def _process_result(
    result: subprocess.CompletedProcess,
    base_cmd: list[str],
    check: bool,
    json_output: bool,
    module: "AnsibleModule",
) -> dict[str, object]:
    stdout = result.stdout.strip() if result.stdout else ""
    stderr = result.stderr.strip() if result.stderr else ""

    _log_debug(module, f"Command returned code {result.returncode}")
    if stdout:
        _log_debug(module, f"stdout: {stdout}")
    if stderr:
        _log_debug(module, f"stderr: {stderr}")

    if check and result.returncode != 0:
        msg = (
            f"multipass command failed: {' '.join(base_cmd)}\n"
            f"Exit code: {result.returncode}\n"
            f"Stdout: {stdout}\nStderr: {stderr}"
        )
        _log_and_raise(module, msg)

    output: dict[str, object] = {
        "rc": result.returncode,
        "stdout": stdout,
        "stderr": stderr,
    }

    if json_output:
        try:
            output["json"] = json.loads(stdout)
            _log_debug(module, "Successfully parsed JSON output")
        except json.JSONDecodeError:
            _log_and_raise(module, f"Failed to parse JSON output: {stdout}")

    return output


def _log_debug(module: "AnsibleModule", msg: str) -> None:
    """Log a debug message to the provided AnsibleModule, if set."""
    if module:
        module.log(f"[cli] {msg}")


def _log_and_raise(module: "AnsibleModule", msg: str) -> None:
    """Log an error and raise a MultipassCLIError."""
    if module:
        module.log(f"[cli] {msg}")
    raise types.MultipassCLIError(msg)
