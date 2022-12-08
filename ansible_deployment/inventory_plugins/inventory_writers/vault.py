"""
Vault inventory writer plugin.
"""
import base64
import ansible_deployment.inventory_plugins.helpers.vault as vault_helpers
from pathlib import Path
from ansible_deployment.inventory_plugins.inventory_plugin import InventoryPlugin


class VaultWriter(InventoryPlugin):
    """
    VaultWriter InventoryPlugin class.
    """

    name = "vault"
    plugin_type = "writer"

    def update_inventory(self, hosts, host_vars, group_vars, deployment_key,
                         template_mode=False):
        self.ssh_keypair.private_key_path = Path(".ssh/id_rsa")
        self.ssh_keypair.public_key_path = Path(".ssh/id_rsa.pub")
        self.ssh_keypair.read()

        self.write_secret("hosts", hosts)

        if not template_mode:
            deployment_key = {"data": base64.encodebytes(deployment_key).decode("ascii")}
            self.write_secret("deployment_key", deployment_key)
            self.write_secret("ssh_private_key", self.ssh_keypair.private_key)
            self.write_secret("ssh_public_key", self.ssh_keypair.public_key)

        for group in group_vars:
            self.write_secret(f"group_vars/{group}", group_vars[group])
        for host in host_vars:
            self.write_secret(f"host_vars/{host}", host_vars[host])


    def write_secret(self, secret_name, secret_value):
        """
        Write secret to vault.

        Arguments:
            secret_name (str): Secret name.
            secret_value (any): Secret value.
        """
        vault_path = f"ansible-deployment/{self.deployment_name}/{secret_name}"
        vault_client, error = vault_helpers.init_vault_client()

        if error is not None:
            raise Exception(error)

        return vault_client.secrets.kv.v2.create_or_update_secret(
            path=vault_path, secret=secret_value
        )
