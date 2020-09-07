from pathlib import Path
from collections import namedtuple
import json
import subprocess
from ansible_deployment import (AnsibleDeployment, Role, Inventory, Playbook,
                                DeploymentDirectory)

RepoConfig = namedtuple('RepoConfig', 'repo branch')
"""
Represents a remote git repository configuration.

Args:
    repo (str): A clonable git repository path or url.
    branch (str): Git branch to checkout.
"""

DeploymentConfig = namedtuple('DeploymentConfig',
                              'roles roles_src inventory_plugin ansible_user')
"""
Represents the deployment configuration.

Args:
    roles (sequence): A sequence of role names.
    roles_src (RepoConfig): Namedtuple containing roles repo information.
    inventory_plugin (str): Name of the inventory plugin to use.
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
        inventory (Inventory): Inventory object representing deployment inventory.
        playbook (Playbook): Playbook object representing deployment playbook.
    """

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
        roles_src = RepoConfig(config["roles_src"]['repo'],
                              config["roles_src"]['branch'])
        config['roles_src'] = roles_src

        return DeploymentConfig(**config)

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
        self.name = self.deployment_dir.path.name
        self.config = config
        self.roles = self._create_role_objects(config.roles)
        if not self.deployment_dir.vault.locked:
            self.inventory = Inventory(self.deployment_dir.path, self.config)
            self.deployment_dir.vault.files += self.inventory.plugin.added_files
            self.deployment_dir.deployment_repo.content += self.inventory.plugin.added_files
            self.playbook = Playbook(self.deployment_dir.path / 'playbook.yml',
                                     'all', self.roles)

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
        self.playbook.write()
        self.inventory.write()
        self.deployment_dir.deployment_repo.update(message="add deployment files")

    def save(self):
        """
        Write config as json to `self.deployment_dir.config_file`.
        """
        json_dump = self.config._asdict()
        json_dump['roles_src'] = self.config.roles_src._asdict()
        with open(self.deployment_dir.config_file, 'w') as config_file_stream:
            json.dump(json_dump, config_file_stream, indent=4)

    def run(self, tags=None):
        """
        Run deployment with ansible-playbook.

        Args:
            tags (sequence): an optional sequence of playbook tags.

        Every deployment run triggers a new git commit in
        `self.deployment_dir.repo` containing the executed command.
        """
        command = ['ansible-playbook', 'playbook.yml']
        if tags:
            command += ['--tags', ','.join(tags)]
        self.deployment_dir.deployment_repo.update('Deployment run: {}'.format(command),
                                       files=[],
                                       force_commit=True)
        subprocess.run(command)

    def ssh(self, host):
        """
        Run ssh to connect to a given deployment host as `ansible_user`.

        Args:
            host (str): Target host.
        """
        if host in self.inventory.hosts['all']['hosts']:
            host_info = self.inventory.host_vars[host]
            subprocess.run([
                'ssh', '-l', host_info['ansible_user'],
                host_info['ansible_host']
            ])
