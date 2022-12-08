"""
Local inventory source plugin.
"""
import yaml
from pathlib import Path
from ansible_deployment.inventory_plugins.inventory_plugin import InventoryPlugin


class Local(InventoryPlugin):
    """
    Local InventoryPlugin class.
    """

    name = "local"

    def _load_vars(self, vars_type):
        """
        Loads inventory variables from inventory path.

        Args:
            vars_type (str): Variable type. May be 'host_vars' or 'group_vars'.
        """
        vars_dir_path = Path(f"./{vars_type}")
        ignore_patterns = (".swp",)
        vars_files = list(vars_dir_path.glob("*"))
        for vars_file in vars_files:
            if any(map(vars_file.name.__contains__, ignore_patterns)):
                continue
            vars_name = vars_file.stem
            with open(vars_file) as vars_file_stream:
                self.vars[vars_type][vars_name] = yaml.safe_load(vars_file_stream)

    def _load_hosts(self):
        hosts_file_path = Path("./hosts.yml")
        if hosts_file_path.exists():
            with open(hosts_file_path) as f:
                self.hosts = yaml.safe_load(f)

    def update_inventory(self):
        self.ssh_keypair.private_key_path = Path('./.ssh/id_rsa')
        self.ssh_keypair.public_key_path = Path('./.ssh/id_rsa.pub')
        self.ssh_keypair.read()
        self._load_hosts()
        self._load_vars("host_vars")
        self._load_vars("group_vars")
