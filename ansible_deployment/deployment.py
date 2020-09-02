from pathlib import Path
from pprint import pformat
from collections import namedtuple
from ansible_deployment import (
    AnsibleDeployment,
    Role,
    Inventory,
    Playbook,
    DeploymentDirectory)
import json
import subprocess


DeploymentConfig = namedtuple('DeploymentConfig', 'roles roles_src inventory_plugin')
class Deployment(AnsibleDeployment):
    filtered_values = ['playbook', 'inventory']
    def load(deployment_config_file):
        deployment = None
        deployment_config_file_path = Path(deployment_config_file)
        deployment_path = deployment_config_file_path.parent
        deployment_config = Deployment._load_config_file(deployment_config_file_path)
        deployment = Deployment(deployment_path, deployment_config)
        return deployment

    def _load_config_file(config_file_path):
        with open(config_file_path) as config_file_stream:
            deployment_config = json.load(config_file_stream)
        deployment_path = config_file_path.parent

        return DeploymentConfig(**deployment_config)

    def __init__(self, path, config):
        self.deployment_dir = DeploymentDirectory(path, config.roles_src)
        self.name = self.deployment_dir.path.name
        self.config = config
        self.roles = self._create_role_objects(config.roles)
        self.inventory = Inventory(self.deployment_dir.path, config.inventory_plugin)
        self.playbook = Playbook(self.deployment_dir.path / 'playbook.yml',
                                 'all', self.roles)

    def _create_role_objects(self, role_names):
        parsed_roles = []
        for role_name in role_names:
            parsed_roles.append(
                Role(self.deployment_dir.roles_path / role_name))
        return parsed_roles


    def initialize_deployment_directory(self):
        role_names = (role.name for role in self.roles)
        self.deployment_dir.create(self.roles)
        self.roles = self._create_role_objects(role_names)
        self.deployment_dir.update(self.roles, self.playbook, self.inventory)
        self.playbook.write()
        self.inventory.write()
        self.deployment_dir.update_git(message="add deployment files")

    def save(self):
        with open(self.deployment_dir.config_file, 'w') as config_file_stream:
            json.dump(self.config._asdict(), config_file_stream, indent=4)

    def run(self, tags=None):
        command = ['ansible-playbook', 'playbook.yml']
        if tags:
            command += ['--tags', ','.join(tags)]
        self.deployment_dir.update_git('Deployment run: {}'.format(command),
                                       files=[],
                                       force_commit=True)
        subprocess.run(command)

    def ssh(self, host):
        if host in self.inventory.hosts['all']['hosts']:
            host_info = self.inventory.host_vars[host]
            subprocess.run([
                'ssh', '-l', host_info['ansible_user'],
                host_info['ansible_host']
            ])

    def update(self):
        self.deployment_dir.update(self.roles, self.playbook, self.inventory)


