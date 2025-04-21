"""Ansible module for listing Multipass instances."""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import core, types  # pylint: disable=import-error


def main():
    """Entrypoint for Ansible list module."""
    module = AnsibleModule(
        argument_spec={},  # No args needed for listing
        supports_check_mode=True,
    )

    try:
        instances = core.list_instances(module=module)
        module.exit_json(changed=False, instances=instances)
    except types.MultipassCLIError as exc:
        module.fail_json(msg=f"Failed to list multipass instances: {exc}")


if __name__ == "__main__":
    main()
