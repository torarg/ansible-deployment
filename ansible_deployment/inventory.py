from pathlib import Path
import json
import yaml

class Inventory:
    inventory_types = [ 'terraform' ]
    def __init__(self, inventory_type, inventory_path):
        self.hosts = {}
        self.hosts['all'] = {}
        self.hosts['all']['hosts'] = {}
        self.inventory_type = inventory_type
        self.inventory_path = Path(inventory_path)
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
                    host['ansible_user'] = 'root'
                    self.hosts['all']['hosts'][host['name']] = host

    def write(self):
        with open(self.inventory_path, 'w') as inventory_file_stream:
            yaml.dump(self.hosts, inventory_file_stream)
