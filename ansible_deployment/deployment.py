from pathlib import Path
from pprint import pformat
from ansible_deployment.class_skeleton import AnsibleDeployment
from ansible_deployment.role import Role
from ansible_deployment.inventory import Inventory
from ansible_deployment.playbook import Playbook
from ansible_deployment.deployment_dir import DeploymentDirectory
import json
import subprocess


class Deployment(AnsibleDeployment):
    filtered_values = ['playbook', 'inventory']

    def __init__(self, deployment_path, roles_src, roles, inventory_plugin):
        self.deployment_dir = DeploymentDirectory(deployment_path, roles_src)
        self.name = self.deployment_dir.path.name
        self.roles = self._create_role_objects(roles)
        self.inventory = Inventory(self.deployment_dir.path, inventory_plugin)
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
        role_names = []
        for role in self.roles:
            role_names.append(role.name)

        deployment_state = {
            'name': self.name,
            'roles': role_names,
            'inventory_plugin': self.inventory.plugin.name,
            'ansible_roles_src': self.deployment_dir.roles_src
        }
        with open(self.deployment_dir.state_file, 'w') as state_file_stream:
            json.dump(deployment_state, state_file_stream, indent=4)

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

    def load(deployment_state_file):
        deployment = None
        deployment_state_file_path = Path(deployment_state_file)
        if deployment_state_file_path.exists():
            with open(deployment_state_file_path
                      ) as deployment_state_file_stream:
                deployment_state = json.load(deployment_state_file_stream)
                deployment_path = deployment_state_file_path.parent

            deployment = Deployment(deployment_path,
                                    deployment_state['ansible_roles_src'],
                                    deployment_state['roles'],
                                    deployment_state['inventory_plugin'])

        return deployment
