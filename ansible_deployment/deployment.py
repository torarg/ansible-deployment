from pathlib import Path
from ansible_deployment.role import Role
from ansible_deployment.playbook import Playbook
import yaml

class Deployment:
    directory_layout = ['host_vars', 'group_vars', 'roles']

    def __init__(self, deployment_path, roles_path, roles):
        self.path = Path(deployment_path)
        self.roles_path = Path(roles_path)
        self.name = self.path.name
        self.roles = self._create_role_objects(roles)
        self.playbook = Playbook(self.path / 'playbook.yml', 'all', self.roles)

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
        if group_vars_path.exists:
            group_vars_path.unlink()

        for role in self.roles:
            for defaults_file in role.defaults.values():
                with open(group_vars_path, 'a') as group_vars_file:
                    yaml.dump(defaults_file['data'], group_vars_file)


    def initialize_deployment_directory(self):
        self._create_deployment_directories()
        self._copy_roles_to_deployment_directory()
        self.playbook.write()
        self._write_role_defaults_to_group_vars()
