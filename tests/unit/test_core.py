"""Unit tests for multipass core logic."""

import pytest
from hlsm.multipass.module_utils import core, cli, types


class DummyModule:
    """Mock AnsibleModule for capturing logs during CLI calls."""

    def __init__(self):
        self.logs = []

    def log(self, msg):
        """Capture log message into internal log list."""
        self.logs.append(msg)


def test_get_info_returns_vm_details(monkeypatch):
    """get_info() should return the VM info dict when instance exists."""

    def mock_run(*_args, **_kwargs):
        return {
            "json": {"info": {"myvm": {"state": "Running", "ipv4": ["192.168.64.2"]}}}
        }

    monkeypatch.setattr(cli, "run_multipass_command", mock_run)
    result = core.get_info("myvm")
    assert result["state"] == "Running"


def test_get_info_returns_none_for_missing_instance(monkeypatch):
    """get_info() should return None if instance is not found."""

    def mock_run(*_args, **_kwargs):
        raise types.MultipassCLIError("Instance does not exist")

    monkeypatch.setattr(cli, "run_multipass_command", mock_run)
    assert core.get_info("ghost") is None


def raise_cli_error(*_args, **_kwargs):
    """Raise MultipassCLIError to simulate CLI failure."""
    raise types.MultipassCLIError("fail")


def test_get_info_raises_on_other_error(monkeypatch):
    """get_info() should raise on unexpected CLI error."""

    monkeypatch.setattr(cli, "run_multipass_command", raise_cli_error)
    with pytest.raises(types.MultipassCLIError):
        core.get_info("boom")


def test_ensure_present_creates_minimal(monkeypatch):
    """ensure_present() launches a VM when it doesn't exist."""
    dummy = DummyModule()
    call_count = {"count": 0}

    def mock_get_info(_args, **_kwargs):
        if call_count["count"] == 0:
            call_count["count"] += 1
            return None
        return {"state": "Running"}

    monkeypatch.setattr(core, "get_info", mock_get_info)
    monkeypatch.setattr(cli, "run_multipass_command", lambda *_a, **_kw: {"rc": 0})

    config = types.VMConfig(name="vm1", image="20.04")
    result = core.ensure_present(config, module=dummy)
    assert result["changed"] is True
    assert "created" in result["msg"]
    assert result["info"]["state"] == "Running"


def test_ensure_present_returns_if_already_exists(monkeypatch):
    """ensure_present() should not recreate existing VM."""
    monkeypatch.setattr(core, "get_info", lambda *_a, **_kw: {"state": "Running"})

    config = types.VMConfig(name="vm1", image="20.04")
    result = core.ensure_present(config)
    assert result["changed"] is False
    assert "already exists" in result["msg"]


def test_ensure_absent_when_vm_is_missing(monkeypatch):
    """ensure_absent() should return changed=False if VM is not present."""
    monkeypatch.setattr(core, "get_info", lambda *_a, **_kw: None)
    result = core.ensure_absent("ghost")
    assert result["changed"] is False


def test_ensure_absent_deletes_existing_vm(monkeypatch):
    """ensure_absent() should delete VM and return changed=True."""
    dummy = DummyModule()
    deleted = []

    monkeypatch.setattr(core, "get_info", lambda *_a, **_kw: {"state": "Running"})

    def mock_run(args, **_kwargs):
        if args[0] == "delete":
            deleted.append(True)
        return {"rc": 0}

    monkeypatch.setattr(cli, "run_multipass_command", mock_run)
    result = core.ensure_absent("existing", module=dummy)
    assert result["changed"] is True
    assert "deleted" in result["msg"]
    assert deleted


def test_list_instances_happy(monkeypatch):
    """list_instances returns a list of VMs on success."""

    def mock_run_multipass_command(*_args, **_kwargs):
        return {
            "json": {
                "info": {
                    "vm1": {"state": "Running"},
                    "vm2": {"state": "Stopped"},
                }
            }
        }

    monkeypatch.setattr(cli, "run_multipass_command", mock_run_multipass_command)

    result = core.list_instances()
    assert isinstance(result, dict)
    assert "vm1" in result
    assert "vm2" in result
    assert result["vm1"]["state"] == "Running"
    assert result["vm2"]["state"] == "Stopped"
    assert len(result) == 2


def test_list_instances_no_info_key(monkeypatch):
    """list_instances returns empty dict if 'info' key is missing."""

    def mock_run_multipass_command(*_args, **_kwargs):
        return {"json": {}}

    monkeypatch.setattr(cli, "run_multipass_command", mock_run_multipass_command)

    assert core.list_instances() == {}


def test_list_instances_command_fails(monkeypatch):
    """list_instances raises MultipassCLIError on failure."""

    monkeypatch.setattr(cli, "run_multipass_command", raise_cli_error)

    with pytest.raises(types.MultipassCLIError):
        core.list_instances()
