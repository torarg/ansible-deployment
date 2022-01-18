"""
Terraform inventory plugin.
"""

from pathlib import Path
import json
from ansible_deployment.inventory_plugins.inventory_plugin import InventoryPlugin


class Terraform(InventoryPlugin):
    """
    Terraform InventoryPlugin class.

    Args:
        config (DeploymentConfig): Deployment configuration.

    Attributes:
        all_hosts (dict): Dictionary of all hosts.
        deployment_group (dict): Deployment group hosts.
        hosts (dict): Hosts dict representing a hosts.yml file.
        host_vars (dict): Host vars dict.
        group_vars (dict): Group vars dict.
        added_files (list): List of files added to deployment.
    """

    name = "terraform"

    def __init__(self, groups, inventory_src="terraform.tfstate"):
        InventoryPlugin.__init__(self, groups)
        self.name = "terraform"
        self.inventory_src = inventory_src
        self.resource_functions = {
            "hcloud_server": self.parse_hcloud_servers,
        }
        self.added_files.append(inventory_src)

    def _filter_instances(self, tfstate_data):
        """
        Filter terraform instances from tfstate file data.

        Args:
            tfstate_data (str): tfstate file file content.
        Returns:
            dict: instances by type.
        """
        resources = tfstate_data["resources"]
        instances = {}
        for resource in resources:
            if resource["type"] in self.resource_functions:
                if resource["type"] not in instances:
                    instances[resource["type"]] = resource["instances"]
                else:
                    instances[resource["type"]] += resource["instances"]

        return instances

    def _load_tf_state_file(self):
        """
        Load tfstate file content from file.

        Returns:
            str: tfstate file content.
        """
        tfstate_file_path = Path(self.inventory_src)
        if not tfstate_file_path.exists():
            raise FileNotFoundError(f"'{tfstate_file_path}' does not exist.")
        with open(tfstate_file_path) as tfstate_file_stream:
            tfstate_data = json.load(tfstate_file_stream)
        return (tfstate_data, tfstate_file_path)

    def update_inventory(self):
        """
        Update inventory attributes with tfstate file data.
        """

        tfstate_data, tfstate_file_path = self._load_tf_state_file()
        instances = self._filter_instances(tfstate_data)
        for resource_type in instances:
            self.resource_functions[resource_type](instances[resource_type])

        self.added_files = [str(tfstate_file_path)]

    def parse_hcloud_servers(self, instances):
        """
        Parse hcloud_server instances and update object attributes.

        Args:
            instances (dict): Parsed instances by instance_type.
        """

        for instance in instances:
            host = instance["attributes"]
            host["ansible_host"] = host["ipv4_address"]
            host["bootstrap_user"] = "root"
            self.all_hosts[host["name"]] = None
            self.deployment_group[host["name"]] = None
            self.host_vars[host["name"]] = host
