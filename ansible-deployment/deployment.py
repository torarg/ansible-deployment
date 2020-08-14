from role import Role
from playbook import Playbook

class Deployment:
    directory_layout = ['host_vars', 'group_vars', 'roles']

    def __init__(self, deployment_path, roles_path, roles):
        self.path = Path(deployment_path)
        self.roles_path = Path(roles_path)
        self.name = self.path.name
        self.roles = _create_role_objects(roles)
        self.playbook = Playbook(self.path / 'playbook.yml', 'all', roles)

    def _create_deployment_directories(self):
        for directory_name in directory_layout:
            directory_path = self.path / directory_name
            if not directory_path.exists():
                directory_path.mkdir()

    def _copy_roles_to_deployment_directory(self):
        for role in self.roles:
            role.copy_to(self.path / role.name)

    def initialize_deployment_directory(self):
        self._create_deployment_directories(self)
        self._copy_roles_to_deployment_directory(self)
        self.playbook.write()
