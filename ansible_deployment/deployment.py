from pathlib import Path
from ansible_deployment.role import Role
from ansible_deployment.inventory import Inventory
from ansible_deployment.playbook import Playbook
import yaml
import shutil
import subprocess

class Deployment:
    ansible_cfg = [
        '[defaults]',
        'inventory = hosts.yml']
    directory_layout = ['host_vars', 'group_vars', 'roles']
    deployment_files = ['playbook.yml', '.deployment.state', 'hosts.yml', 
                        'ansible.cfg']

    def __init__(self, deployment_path, roles_path, roles, inventory_type):
        self.path = Path(deployment_path)
        self.roles_path = Path(roles_path)
        self.name = self.path.name
        self.roles = self._create_role_objects(roles)
        self.inventory = Inventory(inventory_type, 'hosts.yml')
        self.playbook = Playbook(self.path / 'playbook.yml', 'all', self.roles)

    def __repr__(self):
        return 'Deployment({})'.format(self.__dict__)


    def _create_role_objects(self, roles):
        parsed_roles = []
        for role_name in roles:
            parsed_roles.append(Role(self.roles_path / role_name))
        return parsed_roles


    def _create_deployment_directories(self):
        for directory_name in self.directory_layout:
            directory_path = self.path / directory_name
            if not directory_path.exists():
                directory_path.mkdir()

    def _copy_roles_to_deployment_directory(self):
        for role in self.roles:
            role.copy_to(self.path / 'roles')

    def _write_role_defaults_to_group_vars(self):
        group_vars_path = self.path / 'group_vars' / 'all'
        if group_vars_path.exists():
            group_vars_path.unlink()

        for role in self.roles:
            for defaults_file in role.defaults.values():
                with open(group_vars_path, 'a') as group_vars_file:
                    yaml.dump(defaults_file['data'], group_vars_file)

    def _write_ansible_cfg(self):
        ansible_cfg_path = self.path / 'ansible.cfg'
        with open(ansible_cfg_path, 'w') as ansible_cfg_stream:
            ansible_cfg_stream.writelines('\n'.join(self.ansible_cfg))

    def initialize_deployment_directory(self):
        self._create_deployment_directories()
        self._copy_roles_to_deployment_directory()
        self.playbook.write()
        self.inventory.write()
        self._write_role_defaults_to_group_vars()
        self._write_ansible_cfg()

    def delete(self):
        for directory_name in self.directory_layout:
            directory_path = self.path / directory_name
            if directory_path.exists():
                shutil.rmtree(directory_path)

        for file_name in self.deployment_files:
            file_path = self.path / file_name
            if file_path.exists():
                file_path.unlink()

    def run(self):
        subprocess.run(['ansible-playbook', 'playbook.yml'])

    def ssh(self, host):
        if host in self.inventory.hosts['all']['hosts']:
            host_info = self.inventory.hosts['all']['hosts'][host]
            subprocess.run(['ssh', '-l', host_info['ansible_user'],
                            host_info['ansible_host']])
