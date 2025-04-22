"""Ansible module for managing Multipass VMs.

Supports creating and removing VMs using the multipass CLI.
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibiscardigan.multipass.plugins.module_utils import core, types  # pylint: disable=import-error


def main():
    """Ansible entry point for managing multipass hosts."""
    argument_spec = {
        "name": {"type": "str", "required": True},
        "image": {"type": "str", "required": False},
        "cpus": {"type": "int", "required": False},
        "memory": {"type": "str", "required": False},
        "disk": {"type": "str", "required": False},
        "cloud_init": {"type": "str", "required": False},
        "network": {"type": "str", "required": False},
        "state": {
            "type": "str",
            "choices": ["present", "absent"],
            "default": "present",
        },
    }

    module = AnsibleModule(argument_spec=argument_spec)

    name = module.params["name"]
    state = module.params["state"]

    if state == "present" and not module.params.get("image"):
        module.fail_json(msg="'image' is required when state=present")

    config = types.VMConfig(
        name=name,
        image=module.params.get("image"),
        cpus=module.params.get("cpus"),
        memory=module.params.get("memory"),
        disk=module.params.get("disk"),
        cloud_init=module.params.get("cloud_init"),
        network=module.params.get("network"),
    )

    try:
        if state == "present":
            result = core.ensure_present(config, module=module)
        else:
            result = core.ensure_absent(name, module=module)
        module.exit_json(**result)
    except types.MultipassCLIError as exc:
        module.fail_json(msg=f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
