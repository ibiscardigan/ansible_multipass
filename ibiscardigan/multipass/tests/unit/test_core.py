"""Unit tests for core VM lifecycle logic."""

import pytest
from tests.helpers import helpers
from plugins.module_utils import cli, core, types


def raise_not_found_error(*_args, **_kwargs):
    """Returns a cli error for host not found"""
    raise types.MultipassCLIError("Instance does not exist")


def test_get_info_returns_vm_details(monkeypatch):
    """get_info() should return the VM info dict when instance exists."""

    def mock_run(*_args, **_kwargs):
        return {"json": {"info": {"myvm": {"state": "Running", "ipv4": ["192.168.64.2"]}}}}

    monkeypatch.setattr(cli, "run_multipass_command", mock_run)
    result = core.get_info("myvm")
    assert result["state"] == "Running"


def test_get_info_returns_none_for_missing_instance(monkeypatch):
    """get_info() should return None if instance is not found."""
    monkeypatch.setattr(cli, "run_multipass_command", raise_not_found_error)
    assert core.get_info("ghost") is None


def test_get_info_raises_on_other_error(monkeypatch):
    """get_info() should raise on unexpected CLI error."""
    monkeypatch.setattr(cli, "run_multipass_command", helpers.raise_cli_error)
    with pytest.raises(types.MultipassCLIError):
        core.get_info("boom")


def test_ensure_present_creates_minimal(monkeypatch):
    """ensure_present() launches a VM when it doesn't exist."""
    dummy = helpers.DummyModule()
    monkeypatch.setattr(core, "get_info", helpers.generate_toggle_mock_get_info())
    monkeypatch.setattr(cli, "run_multipass_command", helpers.mock_success_command)

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
    dummy = helpers.DummyModule()
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
    """list_instances returns a dict of VMs on success."""

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
    monkeypatch.setattr(cli, "run_multipass_command", lambda *_a, **_kw: {"json": {}})
    assert core.list_instances() == {}


def test_list_instances_command_fails(monkeypatch):
    """list_instances raises MultipassCLIError on failure."""
    monkeypatch.setattr(cli, "run_multipass_command", helpers.raise_cli_error)
    with pytest.raises(types.MultipassCLIError):
        core.list_instances()
