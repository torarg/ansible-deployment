"""
This module contains the Deployment class and related data structures.
"""

from contextlib import contextmanager
from pathlib import Path
from collections import namedtuple
import json
import subprocess
from ansible_deployment import (
    AnsibleDeployment,
    Role,
    Inventory,
    Playbook,
    DeploymentDirectory,
)
from ansible_deployment.config import load_config_file


@contextmanager
def unlock_deployment(deployment, mode='w'):
    was_locked = deployment.deployment_dir.vault.locked
    unlocked_deployment = deployment
    if was_locked:
        deployment.deployment_dir.vault.unlock()
        unlocked_deployment = Deployment(deployment.deployment_dir.path, deployment.config)
    try:
        yield unlocked_deployment
    finally:
        if was_locked:
            if mode == 'w':
                unlocked_deployment.deployment_dir.vault.lock()
                unlocked_deployment.deployment_dir.delete(keep=['.git'])
                unlocked_deployment.inventory.plugin.delete_added_files()
            else:
                unlocked_deployment.deployment_dir.vault.lock_file_path.touch()
                unlocked_deployment.deployment_dir.delete(keep=['.git', 'deployment.tar.gz.enc'])
                unlocked_deployment.inventory.plugin.delete_added_files()
            unlocked_deployment.deployment_dir.vault.setup_shadow_repo()

@contextmanager
def lock_deployment(deployment):
    was_locked = deployment.deployment_dir.vault.locked
    if was_locked:
        locked_deployment = deployment
    else:
        deployment.deployment_dir.vault.lock()
        deployment.deployment_dir.delete(keep=['.git'])
        deployment.deployment_dir.vault.setup_shadow_repo()
        locked_deployment = Deployment(deployment.deployment_dir.path, deployment.config)
    try:
        yield locked_deployment
    finally:
        if not was_locked:
            locked_deployment.deployment_dir.vault.unlock()


class Deployment(AnsibleDeployment):
    """
    Represents an ansible deployment.

    Args:
        path (str): Path to deployment directory.
        config (DeploymentConfig): Namedtuple containing deployment config.

    Attributes:
        deployment_dir (DeploymentDirectory): Deployment directory object.
        name (str): Deployment name.
        config (DeploymentConfig): Namedtuple containing deployment config.
        roles (list): List of Role objects associated with deployment.
        inventory (Inventory): Inventory object.
        playbook (Playbook): Playbook object representing deployment playbook.
    """

    @staticmethod
    def load(config_file, read_sources=False):
        """
        Initializes deployment object from config file.

        Args:
            config_file (path): Path to config file.

        Returns:
            Deployment: initialized deployment object.
        """
        deployment = None
        config_file_path = Path(config_file)
        deployment_path = config_file_path.parent
        config = load_config_file(config_file_path)
        deployment = Deployment(deployment_path, config, read_sources=read_sources)
        return deployment

    def __init__(self, path, config, read_sources=False):
        self.inventory = Inventory(
            path, config, deployment_key=None, read_sources=read_sources
        )
        self.deployment_dir = DeploymentDirectory(path, config.roles_repo, config.deployment_repo, deployment_key=self.inventory.deployment_key)
        self.inventory.deployment_key = self.deployment_dir.vault.key
        self.name = config.name
        self.config = config
        self.roles = self._create_role_objects(config.roles)
        if not self.deployment_dir.vault.locked:
            added_files = self.inventory.plugin.added_files
            self.deployment_dir.vault.files = list(set(self.deployment_dir.vault.files + added_files))
            self.deployment_dir.deployment_repo.content = list(set(self.deployment_dir.deployment_repo.content + added_files))
            self.playbook = Playbook(
                self.deployment_dir.path / "playbook.yml", "all", self.roles
            )


    def _create_role_objects(self, role_names):
        """
        Create a list of role objects.

        Args:
            role_names (sequence): A sequence of role names.

        Returns:
            list: A list of initialized role objects.
        """
        parsed_roles = []
        for role_name in role_names:
            role_path = self.deployment_dir.path / '.roles.git' / role_name
            parsed_roles.append(Role(name=role_name, path=role_path))
        return parsed_roles

    def initialize_deployment_directory(self):
        """
        Initializes the deployment directory.

        Note:
            Initialization consists of
            `deployment_dir` object initialization,
            `roles` object initialization,
            `deployment_dir` update of roles, playbook and inventory,
            `deployment_dir` git update with new files.
        """
        role_names = (role.name for role in self.roles)
        self.deployment_dir.create()
        self.roles = self._create_role_objects(role_names)
        self.playbook.write()
        self.deployment_dir.write_role_defaults_to_group_vars(self.roles)
        self.inventory = Inventory(
            self.deployment_dir.path, self.config, self.deployment_dir.vault.key
        )
        self.inventory.write()
        self.deployment_dir.deployment_repo.update(message="add deployment files", force_commit=True)

    def save(self):
        """
        Write config as json to `self.deployment_dir.config_file`.
        """
        json_dump = self.config._asdict()
        json_dump["roles_repo"] = self.config.roles_repo._asdict()
        with open(self.deployment_dir.config_file, "w") as config_file_stream:
            json.dump(json_dump, config_file_stream, indent=4)

    def run(self, tags=None, limit=None, extra_vars=None):
        """
        Run deployment with ansible-playbook.

        Args:
            tags (sequence): an optional sequence of playbook tags.
            extra_vars (sequence): an optional sequence of extra vars.
        """
        command = ["ansible-playbook", "playbook.yml"]
        if tags:
            command += ["--tags", ",".join(tags)]
        if limit:
            command += ["-l", limit ]
        if extra_vars:
            for extra_var in extra_vars:
                command += ["-e", extra_var]
        subprocess.run(command, check=True)

    def update_inventory(self):
        """
        Updates inventory.
        """
        self.inventory = Inventory(
            self.deployment_dir.path, self.config, self.deployment_dir.vault.key,
            self.roles
        )


    def ssh(self, host):
        """
        Run ssh to connect to a given deployment host as `ansible_user`.

        Args:
            host (str): Target host.
        """
        if host in self.inventory.hosts["all"]["hosts"]:
            if host in self.inventory.host_vars and "ansible_host" in self.inventory.host_vars[host]:
                host_info = self.inventory.host_vars[host]
            else:
                host_info = { "ansible_host": host }

            ansible_user = self.inventory.group_vars["all"]["ansible_user"]
            ssh_key = self.deployment_dir.ssh_private_key
            subprocess.run(
                ["ssh", "-i", ssh_key, "-l", ansible_user, host_info["ansible_host"]],
                check=True,
            )
