"""
Reusable test utilities for mocking Ansible behavior and common CLI responses.
"""

import uuid
from typing import Any


class DummyModule:
    """Mock AnsibleModule for capturing logs and simulating fail_json()."""

    def __init__(self):
        self.logs = []
        self.failed = False
        self.fail_msg = ""

    def log(self, msg: str) -> None:
        """Simulate module.log() and capture logs."""
        self.logs.append(msg)

    def fail_json(self, msg: str) -> None:
        """Simulate module.fail_json() and raise Exception."""
        self.failed = True
        self.fail_msg = msg
        raise RuntimeError(f"fail_json called: {msg}")


def raise_cli_error(*_args: Any, **_kwargs: Any) -> None:
    """
    Raise a simulated CLI error to test exception handling.
    """
    # pylint: disable=import-outside-toplevel
    from plugins.module_utils import (
        types,
    )  # Local import to avoid test-time circular import

    raise types.MultipassCLIError("Simulated CLI failure")


def generate_unique_vm_name(prefix: str = "test") -> str:
    """
    Generate a short, unique VM name for testing.
    """
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def mock_vm_info(state: str = "Running", ip: str = "192.168.64.2") -> dict[str, Any]:
    """
    Return a fake Multipass VM info dictionary.
    """
    return {
        "state": state,
        "ipv4": [ip],
        "release": "20.04",
        "image_hash": "fake123",
        "load": [0.01, 0.02, 0.03],
    }


def generate_toggle_mock_get_info(vm_info: dict[str, object] = None):
    """
    Returns a mock get_info function that returns None on first call, then `vm_info` afterwards.

    Args:
        vm_info: The VM info to return after the first call.

    Returns:
        A callable suitable for monkeypatching `get_info`.
    """
    call_state = {"called": False}
    vm_info = vm_info or {"state": "Running"}

    def mock_get_info(*_args, **_kwargs):
        if not call_state["called"]:
            call_state["called"] = True
            return None
        return vm_info

    return mock_get_info


def mock_success_command(*_args, **_kwargs):
    """
    Mock successful run_multipass_command result.

    Returns:
        A dict simulating CLI output.
    """
    return {"rc": 0}
