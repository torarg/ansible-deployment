"""
Vault inventory reader plugin.
"""
import base64
import ansible_deployment.inventory_plugins.helpers.vault as vault_helpers
from ansible_deployment.inventory_plugins.inventory_plugin import InventoryPlugin
from hvac import exceptions as vault_exceptions


class VaultReader(InventoryPlugin):
    """
    VaultReader InventoryPlugin class.
    """

    name = "vault"

    def read_secret(self, secret, fallback_value=None):
        """
        Reads a secret from vault.

        secret (str): Vault secret path.
        """
        vault_client, error = vault_helpers.init_vault_client()

        if error is not None:
            raise Exception(error)

        vault_path = f"ansible-deployment/{self.deployment_name}/{secret}"
        try:
            if secret == 'deployment_key':
                query_result = vault_client.secrets.kv.read_secret_version(path=vault_path)[
                    "data"
                ]["data"]["data"]
            else:
                query_result = vault_client.secrets.kv.read_secret_version(path=vault_path)[
                    "data"
                ]["data"]
        except vault_exceptions.InvalidPath:
            query_result = fallback_value
        return query_result
        
    def update_inventory(self):
        self.hosts = self.read_secret("hosts", fallback_value=dict())
        self.deployment_key = self.read_secret("deployment_key")
        if self.deployment_key is not None:
            self.deployment_key = base64.decodebytes(self.deployment_key.encode("ascii")
        
        self.ssh_keypair.private_key = self.read_secret("ssh_private_key")
        self.ssh_keypair.public_key = self.read_secret("ssh_public_key")
        self.ssh_keypair.private_key = self.read_secret("ssh_private_key_file")
        self.ssh_keypair.public_key = self.read_secret("ssh_public_key_file")

        for group in self.groups + ["all"]:
            secret_name = f"group_vars/{group}"
            self.group_vars[group] = self.read_secret(secret=secret_name,
                                                      fallback_value=dict())

        if "all" in self.hosts and "hosts" in self.hosts["all"]:
            for host in [*self.hosts["all"]["hosts"]]:
                secret_name = f"host_vars/{host}"
                host_vars = self.read_secret(secret=secret_name,
                                             fallback_value=dict())
                self.host_vars[host] = host_vars
                self.all_hosts[host] = host_vars
