from pathlib import Path
from git import Repo
from pprint import pformat
import yaml
import shutil


class DeploymentDirectory:
    ansible_cfg = [
        '[defaults]', 'inventory = hosts.yml', 'host_key_checking = False'
    ]
    directory_layout = ('host_vars', 'group_vars', 'roles', '.git')
    temporary_directories = ('.roles', )
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
        self.unstaged_changes = []
        self._git_update_unstaged_changes()

    def __getitem__(self, attribute):
        return self.__dict__[attribute]

    def __contains__(self, attribute):
        return attribute in self.__dict__

    def __repr__(self):
        representation = {
            'path': self.path,
            'repo': self.repo,
            'state_file': self.state_file,
            'roles_src': self.roles_src,
            'roles_path': self.roles_path
        }
        return pformat(representation)

    def _git_update_unstaged_changes(self):
        self.unstaged_changes = [
            diff.a_path for diff in self.repo.index.diff(None)
        ]

    def _git_add(self, files):
        for git_file in files:
            self.repo.index.add(git_file)

    def _git_commit(self, message):
        self.repo.index.commit(message)

    def _clone_ansible_roles_repo(self):
        if not self.roles_path.exists():
            Repo.clone_from(self.roles_src['repo'],
                            self.roles_path,
                            branch=self.roles_src['branch'])

    def _update_ansible_roles_repo(self):
        if self.roles_path.exists():
            roles_repo = Repo(self.roles_path)
            roles_repo.remotes.origin.pull()

    def _create_deployment_directories(self):
        for directory_name in self.directory_layout:
            directory_path = self.path / directory_name
            if not directory_path.exists():
                directory_path.mkdir()

    def _symlink_roles_in_deployment_directory(self, roles):
        for role in roles:
            role.symlink_to(self.path / 'roles')

    def _unlink_roles_in_deployment_directory(self):
        for role_dir in self.path.glob('roles/*'):
            role_dir.unlink()

    def _write_role_defaults_to_group_vars(self, roles):
        group_vars_path = self.path / 'group_vars'

        for role in roles:
            for defaults_file in role.defaults.values():
                with open(group_vars_path / role.name, 'w') as group_vars_file:
                    group_vars_file.write('# role: {}\n'.format(role.name))
                    yaml.dump(defaults_file['data'], group_vars_file)
                    group_vars_file.write('\n')

    def _write_ansible_cfg(self):
        ansible_cfg_path = self.path / 'ansible.cfg'
        with open(ansible_cfg_path, 'w') as ansible_cfg_stream:
            ansible_cfg_stream.writelines('\n'.join(self.ansible_cfg))

    def _delete_temporary_directories(self):
        for directory in self.temporary_directories:
            directory_path = self.path / directory
            if directory_path.exists():
                shutil.rmtree(directory_path)

    def create(self, roles):
        self._create_deployment_directories()
        self._clone_ansible_roles_repo()
        self._unlink_roles_in_deployment_directory()
        self._symlink_roles_in_deployment_directory(roles)
        self._write_ansible_cfg()

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

    def update(self, roles):
        self._update_ansible_roles_repo()
        self._unlink_roles_in_deployment_directory()
        self._symlink_roles_in_deployment_directory(roles)
        self._write_role_defaults_to_group_vars(roles)
        self._git_update_unstaged_changes()

    def update_git(self,
                   message="Automatic ansible-deployment update.",
                   files=git_repo_content):
        self._git_add(files)
        self._git_commit(message)
        self._git_update_unstaged_changes()
