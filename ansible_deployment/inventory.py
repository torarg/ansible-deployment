"""
This module contains the Inventory class.
"""

from pathlib import Path
import yaml
from ansible_deployment import AnsibleDeployment
from ansible_deployment.inventory_plugins import (
    Terraform,
    VaultReader,
    VaultWriter,
    Local,
    InventoryPlugin,
)


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

    inventory_sources = {"terraform": Terraform, "vault": VaultReader, "local": Local}

    inventory_writers = {"vault": VaultWriter}

    filtered_attributes = ["vars"]

    def __init__(self, inventory_path, config):
        self.path = Path(inventory_path)
        self.hosts = {}
        self.groups = []
        self.host_vars = {}
        self.group_vars = {}
        self.plugin = InventoryPlugin(config)
        self.config = config

        self.local_inventory = Local(config)
        self.loaded_sources = [self.local_inventory]

        self.loaded_writers = []

        self._load_plugins(config)
        self.run_reader_plugins()

        self.filtered_representation = {}

        for host in self.host_vars:
            self.filtered_representation[host] = {}
            self.filtered_representation[host]["ansible_host"] = self.host_vars[host][
                "ansible_host"
            ]
            self.filtered_representation[host]["ansible_user"] = self.host_vars[host][
                "ansible_user"
            ]
            self.filtered_representation[host]["ansible_host"] = self.host_vars[host][
                "ansible_host"
            ]

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
                self.plugin.host_vars[host] = (
                    self.plugin.host_vars[host] | plugin.host_vars[host]
                )
            elif plugin.host_vars[host]:
                self.plugin.host_vars[host] = plugin.host_vars[host]

        for group in plugin.group_vars:
            if group in self.plugin.group_vars:
                self.plugin.group_vars[group] = (
                    self.plugin.group_vars[group] | plugin.group_vars[group]
                )
            elif plugin.group_vars[group]:
                self.plugin.group_vars[group] = plugin.group_vars[group]

        self.hosts = self.plugin.hosts
        self.groups = self.plugin.groups
        self.host_vars = self.plugin.host_vars
        self.group_vars = self.plugin.group_vars

    def run_reader_plugins(self):
        """
        Run loaded inventory sources.
        """
        for plugin in self.loaded_sources:
            plugin.update_inventory()
            self._update_plugin_inventory(plugin)

    def run_writer_plugins(self):
        """
        Run loaded inventory writers.
        """
        for plugin in self.loaded_writers:
            self.local_inventory.update_inventory()
            plugin.update_inventory(
                self.local_inventory.hosts,
                self.local_inventory.host_vars,
                self.local_inventory.group_vars,
            )

    def write(self):
        """
        Writes inventory files to inventory_path.
        """
        for host in self.host_vars.values():
            with open(
                self.path / "host_vars" / host["name"], "w"
            ) as hostvars_file_stream:
                yaml.dump(host, hostvars_file_stream)

        for group in self.group_vars:
            with open(self.path / "group_vars" / group, "w") as groupvars_file_stream:
                yaml.dump(self.group_vars[group], groupvars_file_stream)

        with open(self.path / "hosts.yml", "w") as inventory_file_stream:
            yaml.dump(self.hosts, inventory_file_stream)
