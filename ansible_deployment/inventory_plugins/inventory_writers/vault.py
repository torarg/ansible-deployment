"""
Vault inventory writer plugin.
"""
import ansible_deployment.inventory_plugins.helpers.vault as vault_helpers
from ansible_deployment.inventory_plugins.inventory_plugin import InventoryPlugin


class VaultWriter(InventoryPlugin):
    """
    VaultWriter InventoryPlugin class.
    """

    name = "vault"
    plugin_type = "writer"

    def update_inventory(self, hosts, host_vars, group_vars):
        vault_base_path = f"ansible-deployment/{self.deployment_name}"
        vault_client, error = vault_helpers.init_vault_client()

        if error is not None:
            raise Exception(error)

        response = vault_client.secrets.kv.v2.create_or_update_secret(
            path=f"{vault_base_path}/hosts", secret=hosts
        )

        for group in group_vars:
            response = vault_client.secrets.kv.v2.create_or_update_secret(
                path=f"{vault_base_path}/group_vars/{group}", secret=group_vars[group]
            )

        for host in host_vars:
            response = vault_client.secrets.kv.v2.create_or_update_secret(
                path=f"{vault_base_path}/host_vars/{host}", secret=host_vars[host]
            )
