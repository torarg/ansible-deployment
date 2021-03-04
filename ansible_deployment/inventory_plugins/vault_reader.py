import hvac
import os
from ansible_deployment.inventory_plugins.inventory_plugin import (
    InventoryPlugin)
from ansible_deployment.inventory_plugins.vault import Vault

class VaultReader(Vault):
    """
    VaultReader InventoryPlugin class.
    """

    def update_inventory(self):
        vault_base_path = f"ansible-deployment/{self.deployment_name}"
        vault_client, error = self.init_vault_client()
        self.hosts = {}
        self.host_vars = {}
        
        if error != None:
            raise Exception(error)


        vault_path = f"{vault_base_path}/hosts"
        try:
            query_result = vault_client.secrets.kv.read_secret_version(path=vault_path)['data']['data']
        except hvac.exceptions.InvalidPath:
            query_result = dict()
        self.hosts = query_result

        for group in self.groups + ['all']:
            vault_path = f"{vault_base_path}/group_vars/{group}"
            try:
                query_result = vault_client.secrets.kv.read_secret_version(path=vault_path)['data']['data']
            except hvac.exceptions.InvalidPath:
                query_result = dict()
            self.group_vars[group] = query_result

        if 'all' in self.hosts and 'hosts' in self.hosts['all']:
            for host in [*self.hosts['all']['hosts']]:
                vault_path = f"{vault_base_path}/host_vars/{host}"
                try:
                    query_result = vault_client.secrets.kv.read_secret_version(path=vault_path)['data']['data']
                except hvac.exceptions.InvalidPath:
                    query_result = dict()
                self.host_vars[host] = query_result
                self.all_hosts[host] = query_result
