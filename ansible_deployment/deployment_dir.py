from pathlib import Path
from git import Repo
from pprint import pformat
from ansible_deployment.class_skeleton import AnsibleDeployment
import yaml
import shutil


class DeploymentDirectory(AnsibleDeployment):
    ansible_cfg = [
        '[defaults]', 'inventory = hosts.yml', 'host_key_checking = False'
    ]
    directory_layout = ('host_vars', 'group_vars', 'roles', '.git', '.roles')
    deployment_files = ['playbook.yml', 'hosts.yml', 'ansible.cfg']
    git_repo_content = deployment_files + [
        'host_vars', 'group_vars', 'deployment.json'
    ]

    def __init__(self, path, roles_src, state_file='deployment.json'):
        self.path = Path(path)
        self.roles_src = roles_src
        self.roles_path = self.path / '.roles'
        self.state_file = self.path / 'deployment.json'
        self.repo = Repo.init(self.path)
        self.roles_repo = None
        self.unstaged_changes = []
        self._update_unstaged_changes()

    def _update_unstaged_changes(self):
        self.unstaged_changes = [
            diff.a_path for diff in self.repo.index.diff(None)
        ]

    def _create_deployment_directories(self):
        for directory_name in self.directory_layout:
            directory_path = self.path / directory_name
            if not directory_path.exists():
                directory_path.mkdir()

    def _reset_role_symlinks(self, roles):
        for role in roles:
            role.symlink_to(self.path / 'roles')
        for role_dir in self.path.glob('roles/*'):
            role_dir.unlink()

    def _write_role_defaults_to_group_vars(self, roles):
        group_vars_path = self.path / 'group_vars'
        for role in roles:
            for defaults_file in role.defaults.values():
                with open(group_vars_path / role.name, 'w') as group_vars_file:
                    yaml.dump(defaults_file['data'], group_vars_file)

    def _write_ansible_cfg(self):
        ansible_cfg_path = self.path / 'ansible.cfg'
        with open(ansible_cfg_path, 'w') as ansible_cfg_stream:
            ansible_cfg_stream.writelines('\n'.join(self.ansible_cfg))

    def create(self, roles):
        self._create_deployment_directories()
        self.roles_repo = Repo.clone_from(self.roles_src['repo'],
                                          self.roles_path,
                                          branch=self.roles_src['branch'])
        self._reset_role_symlinks(roles)
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

    def update(self, roles):
        if not self.roles_path.exists():
            return None
        roles_repo = Repo(self.roles_path)
        roles_repo.remotes.origin.pull()
        self._reset_role_symlinks(roles)
        self._write_role_defaults_to_group_vars(roles)
        self._write_ansible_cfg()
        self._update_unstaged_changes()

    def update_git(self,
                   message="Automatic ansible-deployment update.",
                   files=git_repo_content):
        for git_file in files:
            self.repo.index.add(git_file)
        self.repo.index.commit(message)
        self._update_unstaged_changes()
