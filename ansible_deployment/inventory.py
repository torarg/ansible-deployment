from pathlib import Path
from ansible_deployment import AnsibleDeployment
from ansible_deployment.inventory_plugins import Terraform
import yaml


class Inventory(AnsibleDeployment):
    """
    Represents an ansible inventory.

    Args:
        inventory_path (str): Path to inventory.
        inventory_plugin (str): Name of inventory plugin.
        ansible_user (str): Ansible user.

    Attributes:
        plugins (dict): Available inventory plugins,
        plugin (InventoryPlugin): Inventory plugin object.
        hosts (dict): Hosts dictionary representing hosts.yml
        host_vars (dict): Host variables.
        group_vars (dict): Group variables.
        vars (dict): Variable lookup table.
    """
    plugins = {'terraform': Terraform}
    filtered_attributes = ['vars']

    def __init__(self, inventory_path, config):
        self.path = Path(inventory_path)
        self.plugin = self.plugins[config.inventory_plugin](config)
        self.hosts = self.plugin.hosts
        self.groups = self.plugin.groups
        self.host_vars = self.plugin.host_vars
        self.group_vars = self.plugin.group_vars
        self.vars = {
            'host_vars': self.host_vars,
            'group_vars': self.group_vars
        }
        self._load_vars('host_vars')
        self._load_vars('group_vars')
        self.plugin.update_inventory()

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

        with open(self.path / 'hosts.yml', 'w') as inventory_file_stream:
            yaml.dump(self.hosts, inventory_file_stream)
