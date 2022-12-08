import hvac
import os
from ansible_deployment.inventory_plugins.inventory_plugin import (
    InventoryPlugin)

class Vault(InventoryPlugin):
    """
    Vault InventoryPlugin class.
    """

    def _init_vault_client(self):
        """
        Initializes vault client.

        Returns:
            (hvac.v1.Client, String): Vault client instance and error message
        """
        client = None
        error = None
        vault_address = os.environ.get('VAULT_ADDR')
        if vault_address == None:
            error = 'VAULT_ADDR not set'

        client = hvac.Client(url=vault_address)

        try:
            if not client.is_authenticated():
                error = 'Authentication error'
        except ConnectionError:
            error = "Connection error"

        return (client, error)


    def update_inventory(self):
        vault_base_path = f"ansible-deployment/{self.deployment_name}"
        vault_client, error = self._init_vault_client()
        self.hosts = {}
        self.host_vars = {}
        
        if error != None:
            raise Exception(error)


        for group in self.groups + ['all']:
            vault_path = f"{vault_base_path}/{group}"
            try:
                query_result = vault_client.secrets.kv.read_secret_version(path=vault_path)['data']['data']
            except hvac.exceptions.InvalidPath:
                query_result = dict()
            self.group_vars[group] = query_result


    def update_vault(self, group_vars):
        vault_base_path = f"ansible-deployment/{self.deployment_name}"
        vault_client, error = self._init_vault_client()
        
        if error != None:
            raise Exception(error)
        
        for group in group_vars:
            response = vault_client.secrets.kv.v2.create_or_update_secret(
                path=f"{vault_base_path}/{group}",
                secret=group_vars[group])
