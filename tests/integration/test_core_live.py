"""
Integration tests for VM lifecycle using the real Multipass CLI.
"""

import pathlib
import subprocess
import time
import tempfile
import uuid
import pytest

from hlsm.multipass.module_utils import core, types


def generate_unique_vm_name(prefix: str = "itest") -> str:
    """Generates a unique, temporary VM name."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def live_vm():
    """
    Creates a Multipass VM once for the module and cleans up after all tests.

    Yields:
        A VMConfig instance used to create the VM.
    """
    vm_name = generate_unique_vm_name()
    config = types.VMConfig(
        name=vm_name, image="20.04", cpus=1, memory="512M", disk="4G"
    )

    # Ensure the VM is initially absent
    assert core.get_info(vm_name) is None

    # Create it
    result = core.ensure_present(config)
    assert result["changed"] is True
    assert result["info"] is not None
    time.sleep(2)

    yield config

    # Use ensure_absent() to verify it can clean up live VMs
    cleanup_result = core.ensure_absent(config.name)
    assert cleanup_result["changed"] is True
    assert "deleted" in cleanup_result["msg"]


# pylint: disable=redefined-outer-name
@pytest.mark.integration
def test_ensure_present_creates_vm_correctly(live_vm):
    """
    Test that get_info() detects a VM created by ensure_present().
    Also verifies the VM appears in list_instances().
    """
    info = core.get_info(live_vm.name)
    assert info is not None
    assert info["state"] in ("Running", "Starting")

    all_vms = core.list_instances()
    assert isinstance(all_vms, dict)
    assert live_vm.name in all_vms
    assert all_vms[live_vm.name]["state"] in ("Running", "Starting", "Stopped")


# pylint: disable=redefined-outer-name
@pytest.mark.integration
def test_ensure_present_is_idempotent(live_vm):
    """
    Test that calling ensure_present() again returns changed=False.
    """
    result = core.ensure_present(live_vm)
    assert result["changed"] is False
    assert result["info"] is not None
    assert result["info"]["state"] in ("Running", "Starting")


@pytest.mark.integration
def test_ensure_present_applies_cloud_init():
    """Integration test: ensure cloud-init file is respected and executed."""

    vm_name = f"itest-cloud-{uuid.uuid4().hex[:8]}"
    cloud_init_content = (
        "#cloud-config\nruncmd:\n  - echo 'cloud-init OK' > /home/ubuntu/test.txt"
    )

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write(cloud_init_content)
        cloud_init_path = tmp.name

    config = types.VMConfig(
        name=vm_name,
        image="focal",  # focal = Ubuntu 20.04
        cpus=1,
        memory="512M",
        disk="4G",
        cloud_init=cloud_init_path,
        network="en0",
    )

    try:
        # Ensure the VM does not exist before creating it
        assert core.get_info(vm_name) is None

        result = core.ensure_present(config)
        assert result["changed"] is True
        assert result["info"]["state"] in ("Running", "Starting")

        # Wait a bit to allow cloud-init to complete
        time.sleep(5)

        output = subprocess.check_output(
            ["multipass", "exec", vm_name, "--", "cat", "/home/ubuntu/test.txt"],
            text=True,
        ).strip()

        assert output == "cloud-init OK"

    finally:
        core.ensure_absent(vm_name)
        pathlib.Path(cloud_init_path).unlink(missing_ok=True)
