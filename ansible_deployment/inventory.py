from pathlib import Path
from pprint import pformat
import json
import yaml


class Inventory:
    inventory_types = ['terraform']

    def __init__(self, inventory_type, inventory_path, ansible_user='ansible',
                 groups=[]):
        self.hosts = self._generate_hosts_skeleton(groups)
        self.host_vars = {}
        self.group_vars = {}
        self.inventory_path = Path(inventory_path)
        self.host_vars_path = self.inventory_path.parent / 'host_vars'
        self.group_vars_path = self.inventory_path.parent / 'group_vars'
        self.vars = {
            'group_vars': {
                'vars': self.group_vars,
                'path': self.group_vars_path
            },
            'host_vars': {
                'vars': self.host_vars,
                'path': self.host_vars_path
            },
        }
        self.ansible_user = ansible_user
        self.inventory_type = inventory_type
        if self.inventory_type == 'terraform':
            self._parse_tfstate_file()

        self._load_vars('host_vars')
        self._load_vars('group_vars')

    def __repr__(self):
        filtered_attributes = ('vars',)
        representation = {}
        for attribute in self.__dict__:
            if attribute in filtered_attributes:
                continue
            representation[attribute] = self.__dict__[attribute]
        return pformat(representation)

    def __contains__(self, attribute):
        return attribute in self.__dict__

    def __getitem__(self, attribute):
        return self.__dict__[attribute]

    def _generate_hosts_skeleton(self, groups):
        hosts = {
            'all': {
                'hosts': {},
                'children': {
                    'ansible_deployment': {'hosts': {}}
                }
            }
        }
        for group in groups:
            hosts['all']['children'][group] = {
                'children': {'ansible_deployment': None}}
        return hosts

    def _load_vars(self, vars_type):
        ignore_patterns = ('.swp',)
        vars_files = list(self.vars[vars_type]['path'].glob('*'))
        for vars_file in vars_files:
            if any(map(vars_file.name.__contains__, ignore_patterns)):
                continue
            vars_name = vars_file.stem
            with open(vars_file) as vars_file_stream:
                self.vars[vars_type]['vars'][vars_name] = yaml.safe_load(
                    vars_file_stream)

    def _parse_tfstate_file(self, tfstate_file_name='terraform.tfstate'):
        tfstate_file_path = Path.cwd() / tfstate_file_name
        with open(tfstate_file_path) as tfstate_file_stream:
            tfstate_data = json.load(tfstate_file_stream)
        for resource in tfstate_data['resources']:
            for instance in resource['instances']:
                host = instance['attributes']
                if resource['type'] == 'hcloud_server':
                    host['ansible_host'] = host['ipv4_address']
                    host['ansible_user'] = self.ansible_user
                    host['bootstrap_user'] = 'root'
                    self.hosts['all']['hosts'][host['name']] = None
                    self.hosts['all']['children']['ansible_deployment']['hosts'][host['name']] = None
                    self.host_vars[host['name']] = host

    def write(self):
        for host in self.host_vars.values():
            with open(self.host_vars_path / host['name'], 'w') as hostvars_file_stream:
                yaml.dump(host, hostvars_file_stream)

        with open(self.inventory_path, 'w') as inventory_file_stream:
            yaml.dump(self.hosts, inventory_file_stream)
