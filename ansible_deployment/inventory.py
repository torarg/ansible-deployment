"""
This module contains the Inventory class.
"""

from pathlib import Path
import yaml
from ansible_deployment import AnsibleDeployment
from ansible_deployment.inventory_plugins import Terraform, Vault, Local, InventoryPlugin


class Inventory(AnsibleDeployment):
    """
    Represents an ansible inventory.

    Args:
        inventory_path (str): Path to inventory.
        config (DeploymentConfig): Deployment configuration.

    Attributes:
        plugins (dict): Available inventory plugins,
        hosts (dict): Hosts dictionary representing hosts.yml
        host_vars (dict): Host variables.
        group_vars (dict): Group variables.
        vars (dict): Variable lookup table.
    """
    plugins = {
        'terraform': Terraform,
        'vault': Vault,
        'local': Local
    }
    filtered_attributes = ['vars']

    def __init__(self, inventory_path, config):
        self.path = Path(inventory_path)
        self.hosts = {}
        self.groups = []
        self.host_vars = {}
        self.group_vars = {}
        self.plugin = InventoryPlugin(config)
        self.loaded_plugins = []
        for plugin_name in config.inventory_plugin:
            if plugin_name in self.plugins:
                plugin = self.plugins[plugin_name](config)
                self._update_plugin_inventory(plugin)
                self.loaded_plugins.append(plugin)

            
        self.vars = {
            'host_vars': self.host_vars,
            'group_vars': self.group_vars
        }
        self._load_vars('host_vars')
        self._load_vars('group_vars')
        for plugin in self.loaded_plugins:
            plugin.update_inventory()
            self._update_plugin_inventory(plugin)

        self.filtered_representation = {}

        for host in self.host_vars:
            self.filtered_representation[host] = {}
            self.filtered_representation[host]['ansible_host'] = self.host_vars[host]['ansible_host']
            self.filtered_representation[host]['ansible_user'] = self.host_vars[host]['ansible_user']
            self.filtered_representation[host]['ansible_host'] = self.host_vars[host]['ansible_host']

    def _update_plugin_inventory(self, plugin):
        self.plugin.groups = self.groups + list(set(plugin.groups) - set(self.groups))

        if 'all' in plugin.hosts:
            self.plugin.hosts['all']['hosts'] = self.plugin.hosts['all']['hosts'] | plugin.hosts['all']['hosts']
            self.plugin.hosts['all']['children'] = self.plugin.hosts['all']['children'] | plugin.hosts['all']['children']

        for host in plugin.host_vars:
            if host in self.plugin.host_vars:
                self.plugin.host_vars[host] = self.plugin.host_vars[host] | plugin.host_vars[host]
            elif plugin.host_vars[host]:
                self.plugin.host_vars[host] = plugin.host_vars[host]

        for group in plugin.group_vars:
            if group in self.plugin.group_vars:
                self.plugin.group_vars[group] = self.plugin.group_vars[group] | plugin.group_vars[group]
            elif plugin.group_vars[group]:
                self.plugin.group_vars[group] = plugin.group_vars[group]

        self.hosts = self.plugin.hosts
        self.groups = self.plugin.groups
        self.host_vars = self.plugin.host_vars
        self.group_vars = self.plugin.group_vars

    def _load_vars(self, vars_type):
        """
        Loads inventory variables from inventory path.

        Args:
            vars_type (str): Variable type. May be 'host_vars' or 'group_vars'.
        """
        ignore_patterns = ('.swp', )
        vars_files = list((self.path / vars_type).glob('*'))
        for vars_file in vars_files:
            if any(map(vars_file.name.__contains__, ignore_patterns)):
                continue
            vars_name = vars_file.stem
            with open(vars_file) as vars_file_stream:
                self.vars[vars_type][vars_name] = yaml.safe_load(
                    vars_file_stream)


    def write(self):
        """
        Writes inventory files to inventory_path.
        """
        for host in self.host_vars.values():
            with open(self.path / 'host_vars' / host['name'],
                      'w') as hostvars_file_stream:
                yaml.dump(host, hostvars_file_stream)

        for group in self.group_vars:
            with open(self.path / 'group_vars' / group,
                      'w') as groupvars_file_stream:
                yaml.dump(self.group_vars[group], groupvars_file_stream)

        for plugin in self.loaded_plugins:
            if isinstance(plugin, Vault):
                plugin.update_vault(self.hosts, self.host_vars, self.group_vars)

        with open(self.path / 'hosts.yml', 'w') as inventory_file_stream:
            yaml.dump(self.hosts, inventory_file_stream)
