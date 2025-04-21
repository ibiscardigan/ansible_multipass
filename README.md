# ansible-multipass

An Ansible collection for managing [Multipass](https://multipass.run/) virtual machines. This module provides a clean, testable interface to create, destroy, and list Multipass VMs, including support for common configuration options such as CPU, memory, disk, networking, and cloud-init.

---

## Features

- Create Multipass instances with configurable:
  - Name
  - Image
  - CPU, memory, disk
  - cloud-init
  - Network interface
- Ensure VMs are present or absent
- List all existing Multipass instances
- Clean, modular implementation with full test coverage
- Supports both unit and integration testing

---

## Requirements

- Python 3.9+
- Ansible 2.14+
- Multipass installed and available in your `$PATH`
- macOS or Linux host (Multipass support may vary on Windows)

---

## Project Structure

```
ansible_multipass/
├── plugins/
│   ├── modules/
│   │   ├── hosts.py        # Module to create/delete VMs
│   │   ├── list.py         # Module to list VMs
│   ├── module_utils/
│   │   ├── core.py         # Core logic for VM lifecycle
│   │   ├── cli.py          # CLI command wrapper for multipass
│   │   ├── types.py        # Supporting dataclasses and exceptions
├── tests/
│   ├── unit/               # Unit tests for internal functions
│   ├── integration/        # Live tests using real Multipass
├── pyproject.toml          # Project and tooling config
├── .pre-commit-config.yaml # Pre-commit hooks
├── README.md               # This file
```

---

## Installation

This module is designed for local development and testing. To use it in Ansible, configure the environment variables:

```bash
export ANSIBLE_LIBRARY=plugins/modules
export ANSIBLE_MODULE_UTILS=plugins/module_utils
```

---

## Usage

### Create a VM

```bash
ansible -m hosts -a "name=myvm image=20.04 cpus=2 memory=1G disk=10G state=present" localhost
```

### Remove a VM

```bash
ansible -m hosts -a "name=myvm state=absent" localhost
```

### List All VMs

```bash
ansible -m list -a "" localhost
```

---

## Development

This project uses `pre-commit`, `pytest`, `pylint`, and `black` for code linting, formatting, and testing.

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

### Run Pre-commit Hooks

```bash
pre-commit run --all-files
```

### Run Unit Tests

```bash
PYTHONPATH=. pytest tests/unit
```

### Run Integration Tests (requires real Multipass)

```bash
PYTHONPATH=. pytest tests/integration
```

---

## Configuration Notes

You may customize linter behavior using `.pylintrc` or `pyproject.toml`. For example, the `plugins/modules/` directory has a dedicated `.pylintrc` to ignore import errors related to Ansible.

---

## Roadmap

- Add VM update support (e.g., changing CPU/memory after creation)
- Static IP and mount support
- Dynamic inventory integration
- Publishing as a Galaxy collection

---

## License

This project is licensed under the MIT License.
