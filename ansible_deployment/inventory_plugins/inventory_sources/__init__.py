"""
Inventory sources.
"""
from ansible_deployment.inventory_plugins.inventory_sources.local import Local
from ansible_deployment.inventory_plugins.inventory_sources.terraform import Terraform
from ansible_deployment.inventory_plugins.inventory_sources.vault import (
    VaultReader as Vault,
)
