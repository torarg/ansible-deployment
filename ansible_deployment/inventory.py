from pathlib import Path
from pprint import pformat
from ansible_deployment.class_skeleton import AnsibleDeployment
from ansible_deployment.inventory_plugins.terraform import Terraform
import json
import yaml

class Inventory(AnsibleDeployment):
    plugins = {
        'terraform': Terraform
    }
    filtered_attributes = ['vars']

    def __init__(self, inventory_path, inventory_plugin, ansible_user='ansible'):
        self.plugins = {
            'terraform': Terraform
        }
        self.path = Path(inventory_path)
        self.plugin = self.plugins[inventory_plugin]()
        self.hosts = self.plugin.hosts
        self.host_vars = self.plugin.host_vars
        self.group_vars = self.plugin.group_vars
        self.vars = {'host_vars': self.host_vars, 'group_vars': self.group_vars}
        self._load_vars('host_vars')
        self._load_vars('group_vars')
        self.plugin.update_inventory()


    def _load_vars(self, vars_type):
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
        for host in self.host_vars.values():
            with open(self.path / 'host_vars' / host['name'],
                      'w') as hostvars_file_stream:
                yaml.dump(host, hostvars_file_stream)

        with open(self.path / 'hosts.yml', 'w') as inventory_file_stream:
            yaml.dump(self.hosts, inventory_file_stream)
