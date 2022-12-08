"""
Inventory class skeleton.
"""
from pathlib import Path
from ansible_deployment import SSHKeypair
from ansible_deployment.class_skeleton import AnsibleDeployment
from ansible_deployment.config import DEFAULT_OUTPUT_JSON_INDENT


class InventoryPlugin(AnsibleDeployment):
    """
    Represents the skeleton of an inventory plugin.

    Attributes:
        all_hosts (dict): Dictionary of all hosts.
        deployment_group (dict): Deployment group hosts.
        hosts (dict): Hosts dict representing a hosts.yml file.
        host_vars (dict): Host vars dict.
        group_vars (dict): Group vars dict.
        vars (dict): Combined dictionary for host and group vars.
        added_files (list): List of files added to deployment.
    """

    name = "skeleton"
    plugin_type = "reader"
    filtered_attributes = ["vars", "resource_functions"]

    def __init__(self, config, roles=None):
        self.deployment_name = config.name
        self.deployment_key = None
        self.all_hosts = {}
        self.deployment_group = {}
        self.groups = [ role.replace('-', '_').replace('/', '_') for role in config.roles ]
        self.ansible_user = "ansible"
        self.hosts = {
            "all": {
                "hosts": self.all_hosts,
                "children": {"ansible_deployment": {"hosts": self.deployment_group}},
            }
        }
        self.host_vars = {}
        self.group_vars = {}
        self.ssh_keypair = SSHKeypair()
        self.group_vars["all"] = {"ansible_user": "ansible",
                                  "ansible_ssh_private_key_file": "./.ssh/id_rsa",
                                  "ansible_ssh_public_key_file": "./.ssh/id_rsa.pub"}
        self._set_groups()
        if roles is not None:
            self._load_role_defaults(roles)
        self.added_files = []
        self.vars = {"host_vars": self.host_vars, "group_vars": self.group_vars}
        self.filtered_representation = self.name

    def _load_role_defaults(self, roles):
        """
        Loads role defaults into inventory.

        Args:
            roles (list): List of role objects.
        """
        for role in roles:
            for vars_file in role.defaults:
                self.group_vars[role.group_name] = self.group_vars.get(role.group_name, {}) | role.defaults[vars_file]['data']

    def _set_groups(self):
        """
        Set initial inventory groups in self.hosts.
        """
        for group in self.groups:
            group_data = {"children": { 'ansible_deployment': None }}
            self.hosts["all"]["children"][group] = group_data

    def update_inventory(self):
        """
        Update inventory.

        Note:
            This function is called from ansible_deployment.Inventory and
            is required to update the objects inventory attributes and
            upadate `self.added_files` with a list of plugin specific
            files to add to the deployment repository.
        """

    def delete_added_files(self):
        for path_name in self.added_files:
            p = Path(path_name)
            if not p.exists():
                continue
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
