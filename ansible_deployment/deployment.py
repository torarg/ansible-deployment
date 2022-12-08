"""
This module contains the Deployment class and related data structures.
"""

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

RepoConfig = namedtuple("RepoConfig", "repo branch")
"""
Represents a remote git repository configuration.

Args:
    repo (str): A clonable git repository path or url.
    branch (str): Git branch to checkout.
"""

DeploymentConfig = namedtuple(
    "DeploymentConfig",
    "name roles roles_src inventory_sources inventory_writers ansible_user",
)
"""
Represents the deployment configuration.

Inventory sources are queried in the order specified and produce a
merged inventory in which the last specified inventory source may
overwrite earlier queried values.

Inventory writers persist the current inventory at another location.

Args:
    name (String): Deployment name
    roles (sequence): A sequence of role names.
    roles_src (RepoConfig): Namedtuple containing roles repo information.
    inventory_sources (sequence): Sequence of inventory plugin names.
    inventory_writers (sequence): Sequence of inventory plugin names.
    ansible_user (str): Name of the default ansible user.
"""


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
    def _load_config_file(config_file_path):
        """
        Loads deployment configuration from json file.

        Args:
            config_file_path (path): Path to config file.

        Returns:
            DeploymentConfig: Namedtuple containing deployment config.
        """
        with open(config_file_path) as config_file_stream:
            config = json.load(config_file_stream)
        roles_src = RepoConfig(
            config["roles_src"]["repo"], config["roles_src"]["branch"]
        )
        config["roles_src"] = roles_src

        return DeploymentConfig(**config)

    @staticmethod
    def load(config_file):
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
        config = Deployment._load_config_file(config_file_path)
        deployment = Deployment(deployment_path, config)
        return deployment

    def __init__(self, path, config):
        self.deployment_dir = DeploymentDirectory(path, config.roles_src)
        self.name = config.name
        self.config = config
        self.roles = self._create_role_objects(config.roles)
        if not self.deployment_dir.vault.locked:
            self.inventory = Inventory(
                self.deployment_dir.path, self.config, self.deployment_dir.vault.key
            )
            if self.inventory.deployment_key is not None:
                self.deployment_dir.vault.key = self.inventory.deployment_key
                self.deployment_dir.vault._save_key()
            added_files = self.inventory.plugin.added_files
            self.deployment_dir.vault.files += added_files
            self.deployment_dir.deployment_repo.content += added_files
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
            role_path = self.deployment_dir.roles_path / role_name
            parsed_roles.append(Role(role_path))
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
        self.deployment_dir.update(self)
        self.inventory = Inventory(
            self.deployment_dir.path, self.config, self.deployment_dir.vault.key
        )
        # self.playbook.write()
        self.inventory.write()
        self.deployment_dir.deployment_repo.update(message="add deployment files")

    def save(self):
        """
        Write config as json to `self.deployment_dir.config_file`.
        """
        json_dump = self.config._asdict()
        json_dump["roles_src"] = self.config.roles_src._asdict()
        with open(self.deployment_dir.config_file, "w") as config_file_stream:
            json.dump(json_dump, config_file_stream, indent=4)

    def run(self, tags=None):
        """
        Run deployment with ansible-playbook.

        Args:
            tags (sequence): an optional sequence of playbook tags.

        Every deployment run triggers a new git commit in
        `self.deployment_dir.repo` containing the executed command.
        """
        command = ["ansible-playbook", "playbook.yml"]
        if tags:
            command += ["--tags", ",".join(tags)]
        self.deployment_dir.deployment_repo.update(
            "Deployment run: {}".format(command), files=[], force_commit=True
        )
        subprocess.run(command, check=True)

    def ssh(self, host):
        """
        Run ssh to connect to a given deployment host as `ansible_user`.

        Args:
            host (str): Target host.
        """
        if host in self.inventory.hosts["all"]["hosts"]:
            host_info = self.inventory.host_vars[host]
            subprocess.run(
                ["ssh", "-l", host_info["ansible_user"], host_info["ansible_host"]],
                check=True,
            )
