"""
Inventory class skeleton.
"""

from pathlib import Path

class SSHKeypair:
    """
    Represents a ssh key pair.

    Contains paths and values for a ssh public and private keys.

    Attributes:
        public_key (str): Public key
        private_key (str): Private key
        public_key_path (Path): Public key path
        private_key_path (Path): Private key path
    """

    def __init__(self, public_key=None, public_key_path=None,
                 private_key=None, private_key_path=None):
        self.public_key = public_key
        self.public_key_path = Path(public_key_path)
        self.private_key = private_key
        self.private_key_path = Path(private_key_path)

    def read(self):
        if self.public_key_path is not None and self.public_key_path.exists():
            self.public_key = public_key_path.read_text()
        else:
            raise ValueError("Invalid public key file")

        if self.private_key_path is not None and self.private_key_path.exists():
            self.private_key = private_key_path.read_text()
        else:
            raise ValueError("Invalid private key file")

    def write(self):
        if self.public_key_path is not None:
            self.public_key_path.write_text(self.public_key)
        else:
            raise ValueError("Invalid public key file")

        if self.private_key_path is not None:
            self.private_key_path.write_text(self.private_key)
        else:
            raise ValueError("Invalid private key file")


class InventoryPlugin:
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

    def __init__(self, config, roles=None):
        self.deployment_name = config.name
        self.deployment_key = None
        self.all_hosts = {}
        self.deployment_group = {}
        self.groups = [ role.replace('-', '_') for role in config.roles ]
        self.ansible_user = "ansible"
        self.hosts = {
            "all": {
                "hosts": self.all_hosts,
                "children": {"ansible_deployment": {"hosts": self.deployment_group}},
            }
        }
        self.host_vars = {}
        self.group_vars = {}
        self.ssh_keypair = SSHKeypair(private_key_path='./.ssh/id_rsa',
                                      public_key_path='./.ssh/id_rsa.pub')
        self.ssh_keypair.read()
        self.group_vars["all"] = {"ansible_user": "ansible",
                                  "ansible_ssh_private_key_file": "./.ssh/id_rsa",
                                  "ansible_ssh_public_key_file": "./.ssh/id_rsa.pub"}
        self._set_groups()
        if roles is not None:
            self._load_role_defaults(roles)
        self.added_files = []
        self.vars = {"host_vars": self.host_vars, "group_vars": self.group_vars}

    def _load_role_defaults(self, roles):
        """
        Loads role defaults into inventory.

        Args:
            roles (list): List of role objects.
        """
        for role in roles:
            for vars_file in role.defaults:
                self.group_vars[role.name] = self.group_vars.get(role.name, {}) | role.defaults[vars_file]['data']

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
