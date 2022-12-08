from ansible_deployment.inventory_plugins.inventory_plugin import InventoryPlugin
from pathlib import Path
import json

class Terraform(InventoryPlugin):
    def __init__(self, inventory_src='terraform.tfstate'):
        InventoryPlugin.__init__(self )
        self.name = 'terraform'
        self.inventory_src = inventory_src
        self.resource_functions = {
            "hcloud": self.parse_hcloud_servers,
        }

    def _filter_instances(self, tfstate_data):
        resources = tfstate_data['resources']
        instances = {}
        for resource in resources:
            if resource['type'] in self.resource_functions:
                instances[resource['type']] = resource['instances']

        return instances
        
    def _load_tf_state_file(self):
        tfstate_file_path = Path(self.inventory_src)
        if not tfstate_file_path.exists():
            return None
        with open(tfstate_file_path) as tfstate_file_stream:
            tfstate_data = json.load(tfstate_file_stream)
        return tfstate_data

    def update_inventory(self):
        tfstate_data = self._load_tf_state_file()
        instances = self._filter_instances(tfstate_data)
        for resource_type in instances:
            self.resource_functions[resource_type](instances[resource_type])
        
    def parse_hcloud_servers(self, instances):
        for instance in instances:
            host = instance['attributes']
            host['ansible_host'] = host['ipv4_address']
            host['ansible_user'] = ansible_user
            host['bootstrap_user'] = 'root'
            self.all_hosts[host['name']] = None
            self.deployment_group[host['name']] = None
            self.host_vars[host['name']] = host
