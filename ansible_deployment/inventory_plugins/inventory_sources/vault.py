"""
Vault inventory reader plugin.
"""
import base64
import ansible_deployment.inventory_plugins.helpers.vault as vault_helpers
import os
from pathlib import Path
from ansible_deployment.inventory_plugins.inventory_plugin import InventoryPlugin
from hvac import exceptions as vault_exceptions


class VaultReader(InventoryPlugin):
    """
    VaultReader InventoryPlugin class.
    """

    name = "vault"

    def read_secret(self, secret, fallback_value=None, template=None):
        """
        Reads a secret from vault.

        Arguments:
            secret (str): Vault secret path.
            fallback_value (any): Fallback value if no secret is stored.
            template (str): Vault template path.

        Returns:
            any: Stored secret.
        """
        vault_client, error = vault_helpers.init_vault_client()

        if error is not None:
            raise Exception(error)

        vault_path = f"ansible-deployment/{self.deployment_name}/{secret}"
        vault_template_path = f"ansible-deployment/{template}/{secret}"
        deployment_secret = None
        template_secret = None

        if template is not None:
            try:
                if secret == 'deployment_key':
                    template_secret = vault_client.secrets.kv.read_secret_version(path=vault_template_path)[
                        "data"
                    ]["data"]["data"]["data"]
                else:
                    template_secret = vault_client.secrets.kv.read_secret_version(path=vault_template_path)[
                        "data"
                    ]["data"]["data"]
            except vault_exceptions.InvalidPath:
                template_secret = None
                
        try:
            if secret == 'deployment_key':
                deployment_secret = vault_client.secrets.kv.read_secret_version(path=vault_path)[
                    "data"
                ]["data"]["data"]["data"]
            else:
                deployment_secret = vault_client.secrets.kv.read_secret_version(path=vault_path)[
                    "data"
                ]["data"]["data"]
        except vault_exceptions.InvalidPath:
            deployment_secret = None

        if template_secret is not None and deployment_secret is None:
            deployment_secret = template_secret
        elif template_secret is None and deployment_secret is None:
            deployment_secret = fallback_value
        return deployment_secret
        
    def update_inventory(self):
        template = os.getenv('VAULT_TEMPLATE')
        self.hosts = self.read_secret("hosts", fallback_value=dict(), template=template)
        self.deployment_key = self.read_secret("deployment_key", template=template)
        if self.deployment_key is not None:
            self.deployment_key = base64.decodebytes(self.deployment_key.encode("ascii"))
        self.ssh_keypair.private_key = self.read_secret("ssh_private_key", template=template)
        self.ssh_keypair.public_key = self.read_secret("ssh_public_key", template=template)
        self.ssh_keypair.private_key_path = Path(".ssh/id_rsa", template=template)
        self.ssh_keypair.public_key_path = Path(".ssh/id_rsa.pub", template=template)

        for group in self.groups + ["all"]:
            secret_name = f"group_vars/{group}"
            self.group_vars[group] = self.read_secret(secret=secret_name,
                                                      fallback_value=dict(),
                                                      template=template)

        if "all" in self.hosts and "hosts" in self.hosts["all"]:
            for host in [*self.hosts["all"]["hosts"]]:
                secret_name = f"host_vars/{host}"
                host_vars = self.read_secret(secret=secret_name,
                                             fallback_value=dict(),
                                             template=template)
                self.host_vars[host] = host_vars
                self.all_hosts[host] = host_vars
