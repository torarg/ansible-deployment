from pathlib import Path
from git import Repo
from ansible_deployment.role import Role
from ansible_deployment.inventory import Inventory
from ansible_deployment.playbook import Playbook
import yaml
import json
import shutil
import subprocess

class Deployment:
    ansible_cfg = [
        '[defaults]',
        'inventory = hosts.yml']
    directory_layout = ('host_vars', 'group_vars', 'roles')
    temporary_directories = ('.roles',)
    deployment_files = ['playbook.yml', 'hosts.yml', 
                        'ansible.cfg']

    def __init__(self, deployment_path, roles_path, roles, inventory_type):
        self.path = Path(deployment_path)
        self.roles_src = roles_path
        self.roles_path = self.path / '.roles'
        self.name = self.path.name
        self.role_names = roles
        self.roles = self._create_role_objects()
        self.inventory = Inventory(inventory_type, 'hosts.yml')
        self.playbook = Playbook(self.path / 'playbook.yml', 'all', self.roles)
        self.state_file = self.path / 'deployment.json'

    def __repr__(self):
        return 'Deployment({})'.format(self.__dict__)


    def _create_role_objects(self):
        parsed_roles = []
        for role_name in self.role_names:
            parsed_roles.append(Role(self.roles_path / role_name ))
        return parsed_roles

    def _clone_ansible_roles_repo(self, git_src):
        if not self.roles_path.exists():
            Repo.clone_from(git_src['repo'], self.roles_path,
                            branch=git_src['branch'])

    def _update_ansible_roles_repo(self):
        if self.roles_path.exists():
            roles_repo = Repo(self.roles_path)
            roles_repo.remotes.origin.pull()

    def _create_deployment_directories(self):
        for directory_name in self.directory_layout:
            directory_path = self.path / directory_name
            if not directory_path.exists():
                directory_path.mkdir()

    def _symlink_roles_in_deployment_directory(self):
        for role in self.roles:
            role.symlink_to(self.path / 'roles')

    def _unlink_roles_in_deployment_directory(self):
        for role_dir in self.path.glob('roles/*'):
            role_dir.unlink()

    def _write_role_defaults_to_group_vars(self):
        group_vars_path = self.path / 'group_vars' / 'all'
        group_vars_path_backup = self.path / 'group_vars' / 'all.BAK'
        if group_vars_path.exists():
            shutil.move(group_vars_path, group_vars_path_backup)

        for role in self.roles:
            for defaults_file in role.defaults.values():
                with open(group_vars_path, 'a') as group_vars_file:
                    yaml.dump(defaults_file['data'], group_vars_file)

    def _write_ansible_cfg(self):
        ansible_cfg_path = self.path / 'ansible.cfg'
        with open(ansible_cfg_path, 'w') as ansible_cfg_stream:
            ansible_cfg_stream.writelines('\n'.join(self.ansible_cfg))

    def _delete_temporary_directories(self):
        for directory in self.temporary_directories:
            directory_path = self.path / directory
            if directory_path.exists():
                shutil.rmtree(directory_path)

    def initialize_deployment_directory(self):
        self._create_deployment_directories()
        self._clone_ansible_roles_repo(self.roles_src)
        self.roles = self._create_role_objects()
        self._unlink_roles_in_deployment_directory()
        self._symlink_roles_in_deployment_directory()
        self.playbook.write()
        self.inventory.write()
        self._write_role_defaults_to_group_vars()
        self._write_ansible_cfg()

    def save(self):
        deployment_state = {
            'name': self.name,
            'roles': self.role_names,
            'inventory_type': self.inventory.inventory_type,
            'ansible_roles_src': self.roles_src
        }
        with open(self.state_file, 'w') as state_file_stream:
            json.dump(deployment_state, state_file_stream, indent=4)


    def delete(self):
        self._delete_temporary_directories()
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

    def update(self):
        self._update_ansible_roles_repo()
        self._unlink_roles_in_deployment_directory()
        self._symlink_roles_in_deployment_directory()
        self.roles = self._create_role_objects()
        self._write_role_defaults_to_group_vars()
        self.playbook.write()

    def load(deployment_state_file):
        deployment = None
        deployment_state_file_path = Path(deployment_state_file)
        if deployment_state_file_path.exists():
            with open(deployment_state_file_path) as deployment_state_file_stream:
                deployment_state = json.load(deployment_state_file_stream)
                deployment_path = deployment_state_file_path.parent
    
            deployment = Deployment(deployment_path,
                              deployment_state['ansible_roles_src'],
                              deployment_state['roles'], 
                              deployment_state['inventory_type'])

        return deployment
