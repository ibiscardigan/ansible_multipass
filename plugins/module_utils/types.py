"""
Shared types and exception classes used in the Multipass Ansible module.

This module defines data structures and error types that are reused across
the CLI wrapper, orchestration logic, and the Ansible integration layer.

Classes:
    - MultipassCLIError: Exception raised when a Multipass CLI command fails.
    - VMConfig: Dataclass describing the configuration of a Multipass instance.

This module is intentionally free of any execution logic and exists to
improve structure, clarity, and testability of the overall codebase.
"""

from dataclasses import dataclass
from typing import Optional


class MultipassCLIError(Exception):
    """Raised when the multipass command fails."""


@dataclass
class VMConfig:
    """Configuration for a Multipass instance."""

    name: str
    image: str
    cpus: Optional[int] = None
    memory: Optional[str] = None
    disk: Optional[str] = None
    cloud_init: Optional[str] = None
    network: Optional[str] = None
