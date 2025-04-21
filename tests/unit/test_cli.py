"""Tests for the multipass CLI wrapper."""

import subprocess
import pytest
from hlsm.multipass.module_utils import cli, types


def test_run_command_success(monkeypatch):
    """Test basic CLI command succeeds with stdout returned."""

    class Result:
        """Mock result object for subprocess.run success case."""

        returncode = 0
        stdout = "Success"
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: Result())
    result = cli.run_multipass_command(["version"])
    assert result["rc"] == 0
    assert result["stdout"] == "Success"


def test_run_command_json_output(monkeypatch):
    """Test that CLI output is parsed as JSON when requested."""

    class Result:
        """Mock result with JSON output."""

        returncode = 0
        stdout = '{"test": true}'
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: Result())
    result = cli.run_multipass_command(["info"], json_output=True)
    assert result["json"] == {"test": True}


def test_run_command_bad_json(monkeypatch):
    """Test that invalid JSON output raises a parse error."""

    class Result:
        """Mock result with bad JSON."""

        returncode = 0
        stdout = "Not JSON"
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: Result())
    with pytest.raises(types.MultipassCLIError) as excinfo:
        cli.run_multipass_command(["info"], json_output=True)
    assert "Failed to parse JSON" in str(excinfo.value)


def test_run_command_bad_json_with_logging(monkeypatch):
    """Test JSON parse failure logs a message if module is passed."""

    logs = []

    class MockModule:
        """Mock AnsibleModule-like logger for capturing logs."""

        def log(self, msg):
            """Store a log message."""
            logs.append(msg)

    class Result:
        """Mock result with bad JSON."""

        returncode = 0
        stdout = "bad json"
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: Result())
    with pytest.raises(types.MultipassCLIError):
        cli.run_multipass_command(["info"], json_output=True, module=MockModule())

    assert any("Failed to parse JSON output" in msg for msg in logs)


def test_run_command_file_not_found(monkeypatch):
    """Test that a missing multipass binary raises a CLI error."""

    def mock_run(*_args, **_kwargs):
        raise FileNotFoundError("not found")

    monkeypatch.setattr(subprocess, "run", mock_run)
    with pytest.raises(types.MultipassCLIError) as excinfo:
        cli.run_multipass_command(["info"])
    assert "multipass binary not found" in str(excinfo.value)


def test_run_command_unexpected_error(monkeypatch):
    """Test unexpected exception is caught and re-raised."""

    def mock_run(*_args, **_kwargs):
        raise subprocess.SubprocessError("kaboom")

    monkeypatch.setattr(subprocess, "run", mock_run)
    with pytest.raises(types.MultipassCLIError) as excinfo:
        cli.run_multipass_command(["boom"])
    assert "Unexpected error running multipass" in str(excinfo.value)


def test_run_command_nonzero_exit(monkeypatch):
    """Test that non-zero exit codes raise an error when check=True."""

    class Result:
        """Mock result with non-zero return code."""

        returncode = 1
        stdout = ""
        stderr = "Something went wrong"

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: Result())
    with pytest.raises(types.MultipassCLIError) as excinfo:
        cli.run_multipass_command(["fail"])
    assert "Exit code: 1" in str(excinfo.value)


def test_run_command_nonzero_with_logging(monkeypatch):
    """Test non-zero exit logs error details if module is passed."""

    logs = []

    class MockModule:
        """Mock AnsibleModule with logger."""

        def log(self, msg):
            """Log message to list."""
            logs.append(msg)

    class Result:
        """Mock result with error."""

        returncode = 2
        stdout = "partial"
        stderr = "error"

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: Result())
    with pytest.raises(types.MultipassCLIError):
        cli.run_multipass_command(["fail"], module=MockModule())

    assert any("Exit code: 2" in log for log in logs)
    assert any("stdout" in log for log in logs)
    assert any("stderr" in log for log in logs)


def test_run_command_success_with_logging(monkeypatch):
    """Test successful command logs output and return code."""

    logs = []

    class MockModule:
        """Mock AnsibleModule capturing logs."""

        def log(self, msg):
            """Append a message to the logs."""
            logs.append(msg)

    class Result:
        """Mock success result."""

        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: Result())
    result = cli.run_multipass_command(["ok"], module=MockModule())
    assert result["rc"] == 0
    assert any("Executing" in log for log in logs)
    assert any("Command returned code 0" in log for log in logs)
