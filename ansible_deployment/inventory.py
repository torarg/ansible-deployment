"""
This module contains the Inventory class.
"""

import yaml
import collections
from pathlib import Path
from ansible_deployment import AnsibleDeployment, SSHKeypair
from ansible_deployment.inventory_plugins import (
    InventoryPlugin,
    inventory_sources,
    inventory_writers,
)

class DeploymentKeyError(Exception):
    pass


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
        plugin (InventoryPlugin): Merged plugin inventory.
        local_inventory (Local): Local inventory.
        config (DeploymentConfig): Deployment configuration.
        loaded_writers (list): Loaded inventory writers.
        loaded_sources (list): Loaded inventory sources.
    """

    inventory_sources = {
        "terraform": inventory_sources.Terraform,
        "vault": inventory_sources.Vault,
        "local": inventory_sources.Local,
    }

    inventory_writers = {"vault": inventory_writers.Vault}

    filtered_attributes = ["vars"]

    def __init__(self, inventory_path, config, deployment_key=None, roles=None, read_sources=True):
        self.path = Path(inventory_path)
        self.hosts = {}
        self.groups = []
        self.host_vars = {}
        self.group_vars = {}
        self.plugin = InventoryPlugin(config, roles)
        self.config = config
        self.ssh_keypair = SSHKeypair()

        self.local_inventory = inventory_sources.Local(config)
        self.loaded_sources = [self.local_inventory]

        self.loaded_writers = []

        self.deployment_key = deployment_key

        self._load_plugins(config)

        self.update_added_files()
        if read_sources:
            self.run_reader_plugins()
        else:
            self.local_inventory.update_inventory()
            self._update_plugin_inventory(self.local_inventory)

        self.filtered_representation = {}

        for host in self.host_vars:
            self.filtered_representation[host] = {}
            if "ansible_host" in self.host_vars[host]:
                self.filtered_representation[host]["ansible_host"] = self.host_vars[
                    host
                ]["ansible_host"]
            if "ansible_user" in self.host_vars[host]:
                self.filtered_representation[host]["ansible_user"] = self.host_vars[
                    host
                ]["ansible_user"]


    def _dict_merge(self, dct, merge_dct):
        """
        Recursive dictionary merge.

        Args:
            dct (dict): Dictionary onto which the merge is executed.
            merge_dct (dict): Dictionary merged into ``dct``.
        """
        for k, v in merge_dct.items():
            if (k in dct and isinstance(dct[k], dict)
                    and isinstance(merge_dct[k], collections.abc.Mapping)):
                self._dict_merge(dct[k], merge_dct[k])
            else:
                dct[k] = merge_dct[k]


    def _load_plugins(self, config):
        for plugin_name in config.inventory_sources:
            if plugin_name in self.inventory_sources:
                plugin = self.inventory_sources[plugin_name](config)
                self.loaded_sources.append(plugin)

        for plugin_name in config.inventory_writers:
            if plugin_name in self.inventory_writers:
                plugin = self.inventory_writers[plugin_name](config)
                self.loaded_writers.append(plugin)

    def _update_plugin_inventory(self, plugin):
        self.plugin.groups = self.groups + list(set(plugin.groups) - set(self.groups))

        if "all" in plugin.hosts:
            self.plugin.hosts["all"]["hosts"] = (
                self.plugin.hosts["all"]["hosts"] | plugin.hosts["all"]["hosts"]
            )
            self.plugin.hosts["all"]["children"] = (
                self.plugin.hosts["all"]["children"] | plugin.hosts["all"]["children"]
            )

        for host in plugin.host_vars:
            if host in self.plugin.host_vars:
                self._dict_merge(self.plugin.host_vars[host], plugin.host_vars[host])
            elif plugin.host_vars[host]:
                self.plugin.host_vars[host] = plugin.host_vars[host]

        for group in plugin.group_vars:
            if group in self.plugin.group_vars:
                self._dict_merge(self.plugin.group_vars[group], plugin.group_vars[group])
            elif plugin.group_vars[group]:
                self.plugin.group_vars[group] = plugin.group_vars[group]

        self.plugin.ssh_keypair.update_with(plugin.ssh_keypair)

        self.hosts = self.plugin.hosts
        self.groups = self.plugin.groups
        self.host_vars = self.plugin.host_vars
        self.group_vars = self.plugin.group_vars
        self.ssh_keypair = self.plugin.ssh_keypair

        if plugin.deployment_key is not None:
            self.deployment_key = plugin.deployment_key

    def run_reader_plugins(self):
        """
        Run loaded inventory sources.
        """
        for plugin in self.loaded_sources:
            plugin.update_inventory()
            self._update_plugin_inventory(plugin)

    def update_added_files(self):
        for plugin in self.loaded_sources:
            self.plugin.added_files += plugin.added_files

    def delete_from_writers(self):
        """
        Delete stored inventory from configured writer plugins.
        """
        if self.deployment_key is None:
            raise DeploymentKeyError("Deployment key is missing")
        for plugin in self.loaded_writers:
            plugin.delete(
                self.local_inventory.hosts,
                self.local_inventory.host_vars,
                self.local_inventory.group_vars
            )

    def run_writer_plugins(self, template_mode=False):
        """
        Run loaded inventory writers.
        """
        if self.deployment_key is None:
            raise DeploymentKeyError("Deployment key is missing")
        for plugin in self.loaded_writers:
            self.local_inventory.update_inventory()
            plugin.update_inventory(
                self.local_inventory.hosts,
                self.local_inventory.host_vars,
                self.local_inventory.group_vars,
                self.deployment_key,
                template_mode
            )

    def write_inventory(self):
        """
        Writes inventory file to inventory_path.
        """
        with open(self.path / "hosts.yml", "w") as inventory_file_stream:
            yaml.dump(self.hosts, inventory_file_stream)
        self.ssh_keypair.write()

    def write_vars(self):
        """
        Writes var files to inventory_path.
        """
        for hostname, host in self.host_vars.items():
            with open(self.path / "host_vars" / hostname, "w") as hostvars_file_stream:
                yaml.dump(host, hostvars_file_stream)

        for group in self.group_vars:
            with open(self.path / "group_vars" / group, "w") as groupvars_file_stream:
                yaml.dump(self.group_vars[group], groupvars_file_stream)
