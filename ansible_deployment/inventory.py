from pathlib import Path
import json
import yaml

class Inventory:
    inventory_types = [ 'terraform' ]
    def __init__(self, inventory_type, inventory_path, ansible_user='ansible'):
        self.hosts = {}
        self.hosts['all'] = {}
        self.hosts['all']['hosts'] = {}
        self.ansible_user= ansible_user
        self.inventory_type = inventory_type
        self.inventory_path = Path(inventory_path)
        self.host_vars_path = self.inventory_path.parent / 'host_vars'
        if self.inventory_type == 'terraform':
            self._parse_tfstate_file()

    def __repr__(self):
        return 'Inventory({})'.format(self.__dict__)

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
                    self.hosts['all']['hosts'][host['name']] = host

    def write(self):
        inventory_data = {}
        inventory_data['all']  = {}
        inventory_data['all']['hosts']  = {}
        for host in self.hosts['all']['hosts'].values():
            inventory_data['all']['hosts'][host['name']] = None
            with open(self.host_vars_path / host['name'], 'w') as hostvars_file_stream:
                yaml.dump(host, hostvars_file_stream)
        with open(self.inventory_path, 'w') as inventory_file_stream:
            yaml.dump(inventory_data, inventory_file_stream)
