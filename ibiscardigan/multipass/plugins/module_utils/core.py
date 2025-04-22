"""Core multipass VM state logic."""

import os
from typing import TYPE_CHECKING, Any
from . import cli, types

if TYPE_CHECKING:  # pragma: no cover
    from ansible.module_utils.basic import AnsibleModule


def get_info(name: str, module: "AnsibleModule" = None) -> dict[str, Any] | None:
    """
    Returns parsed info for a multipass instance, or None if it doesn't exist.

    Args:
        name: The name of the instance.
        module: Optional AnsibleModule for logging.

    Returns:
        A dictionary with VM details, or None if not found.
    """
    try:
        result = cli.run_multipass_command(
            ["info", name, "--format", "json"],
            json_output=True,
            module=module,
        )
        json_data = result.get("json", {})
        vm_info = json_data.get("info", {}).get(name)
        return vm_info
    except types.MultipassCLIError as exc:
        if "instance not found" in str(exc).lower() or "does not exist" in str(exc).lower():
            if module:
                module.log(f"VM '{name}' not found.")
            return None
        raise


def ensure_present(
    config: types.VMConfig,
    module: "AnsibleModule" = None,
) -> dict[str, Any]:
    """
    Ensures the specified multipass instance is present.

    If the instance does not exist, it will be created using the given parameters.

    Args:
        config: A VMConfig object describing the instance.
        module: Optional AnsibleModule for safe logging.

    Returns:
        A dictionary with:
            - changed (bool)
            - msg (str)
            - info (dict) if available
    """
    existing = get_info(config.name, module=module)
    if existing:
        if module:
            module.log(f"[core] VM '{config.name}' already exists.")
        return {
            "changed": False,
            "msg": f"VM '{config.name}' already exists",
            "info": existing,
        }

    cmd = ["launch", config.image, "--name", config.name]

    if config.cpus:
        cmd += ["--cpus", str(config.cpus)]
    if config.memory:
        cmd += ["--memory", config.memory]
    if config.disk:
        cmd += ["--disk", config.disk]

    if config.network:
        cmd += ["--network", config.network]
        if module:
            module.log(f"[core] Attaching VM to network interface: {config.network}")

    if config.cloud_init:
        if not os.path.exists(config.cloud_init):
            msg = f"[core] Cloud-init file not found: {config.cloud_init}"
            if module:
                module.fail_json(msg=msg)
            raise FileNotFoundError(msg)
        cmd += ["--cloud-init", config.cloud_init]
        if module:
            module.log(f"[core] Using cloud-init config: {config.cloud_init}")

    if module:
        module.log(f"[core] Creating VM '{config.name}' with command: multipass {' '.join(cmd)}")

    cli.run_multipass_command(cmd, check=True, capture_output=True, module=module)

    info = get_info(config.name, module=module)

    return {
        "changed": True,
        "msg": f"VM '{config.name}' created",
        "info": info,
    }


def ensure_absent(name: str, module: "AnsibleModule" = None) -> dict[str, Any]:
    """
    Ensures the given VM does not exist. Deletes it if present.

    Args:
        name: The name of the VM to delete.
        module: Optional AnsibleModule for logging.

    Returns:
        A dictionary with:
            - changed (bool)
            - msg (str)
    """
    info = get_info(name, module=module)
    if info is None:
        if module:
            module.log(f"[core] VM '{name}' does not exist. No action needed.")
        return {"changed": False, "msg": f"VM '{name}' is already absent"}

    if module:
        module.log(f"[core] Deleting VM '{name}'")

    cli.run_multipass_command(["delete", name], check=True, module=module)
    cli.run_multipass_command(["purge"], check=True, module=module)

    return {"changed": True, "msg": f"VM '{name}' was deleted"}


def list_instances(module: "AnsibleModule" = None) -> dict[str, Any]:
    """
    Lists all Multipass instances and their information.

    Args:
        module: Optional AnsibleModule for logging.

    Returns:
        A dictionary where keys are instance names and values are their info dicts.
    """
    if module:
        module.log("[core] Listing all Multipass instances")

    try:
        result = cli.run_multipass_command(
            ["info", "--format", "json"],
            json_output=True,
            module=module,
        )
        return result.get("json", {}).get("info", {})
    except types.MultipassCLIError as exc:
        if module:
            module.fail_json(msg=f"Failed to list instances: {exc}")
        raise
