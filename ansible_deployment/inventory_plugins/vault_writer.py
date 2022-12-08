import hvac
import os
from ansible_deployment.inventory_plugins.inventory_plugin import (
    InventoryPlugin)
from ansible_deployment.inventory_plugins.vault import Vault

class VaultWriter(Vault):
    """
    VaultWriter InventoryPlugin class.
    """
    plugin_type = "writer"

    def update_inventory(self, hosts, host_vars, group_vars):
        vault_base_path = f"ansible-deployment/{self.deployment_name}"
        vault_client, error = self.init_vault_client()
        
        if error != None:
            raise Exception(error)

        response = vault_client.secrets.kv.v2.create_or_update_secret(
            path=f"{vault_base_path}/hosts",
            secret=hosts)
        
        for group in group_vars:
            response = vault_client.secrets.kv.v2.create_or_update_secret(
                path=f"{vault_base_path}/group_vars/{group}",
                secret=group_vars[group])

        for host in host_vars:
            response = vault_client.secrets.kv.v2.create_or_update_secret(
                path=f"{vault_base_path}/host_vars/{host}",
                secret=host_vars[host])
