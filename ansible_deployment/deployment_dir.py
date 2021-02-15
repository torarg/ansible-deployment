"""
This module contains the DeploymentDirectory class.

It may also be used for DeploymentDirectory related helper functions
or classes in the future.
"""

import shutil
from pathlib import Path
import yaml
from ansible_deployment.class_skeleton import AnsibleDeployment
from ansible_deployment.role import Role
from ansible_deployment.deployment_vault import DeploymentVault
from ansible_deployment.deployment_repo import DeploymentRepo


class DeploymentDirectory(AnsibleDeployment):
    """
    Represents an ansible deployment directory.

    Args:
        path (path): Path to deployment directory.
        roles_src (RepoConfig): Namedtuple containing roles repo config.
        config_file (path): Path to deployment config file.
        vault_files (sequence): Sequence of files to put in vault.

    Attributes:
        path (Path): Path to deployment directory.
        roles_path (Path): Path to deployment roles directory.
        roles_repo (DeploymentRepo): Roles src repository.
        deployment_repo (DeploymentRepo): Deployment git repository.
        config_file (Path): Path to deployment config file.
        vault (DeploymentVault): Vault object for file encryption.
    """
    ansible_cfg = [
        '[defaults]', 'inventory = hosts.yml', 'host_key_checking = False',
        'interpreter_python = auto_silent'
    ]
    directory_layout = ('host_vars', 'group_vars', '.git')
    deployment_files = ['playbook.yml', 'hosts.yml', 'ansible.cfg']
    vault_files = deployment_files + list(directory_layout)

    def __init__(self, path, roles_src):
        self._roles_src = roles_src

        self.path = Path(path)
        self.config_file = self.path / 'deployment.json'

        self.filtered_representation = {
            "path": str(self.path),
            "roles_src": str(roles_src)
        }

        self.roles_path = self.path / 'roles'
        self.roles_repo = DeploymentRepo(self.roles_path,
                                         remote_config=roles_src)

        git_repo_content = [] + self.deployment_files
        git_repo_content += self.directory_layout[:-1]
        git_repo_content += [str(self.config_file)]
        self.deployment_repo = DeploymentRepo(self.path,
                                              files=git_repo_content)

        self.vault = DeploymentVault(self.vault_files, self.path)

        if not self.vault.locked and self.deployment_repo.repo:
            self.deployment_repo.update_changed_files()
            self.vault.files = self.deployment_repo.repo.git.ls_files().split(
                '\n') + ['.git']
            if 'deployment.json' in self.vault.files:
                self.vault.files.remove('deployment.json')

    def _create_deployment_directories(self):
        """
        Create deployment directories.
        """
        for directory_name in self.directory_layout:
            directory_path = self.path / directory_name
            if not directory_path.exists():
                directory_path.mkdir()

    def _write_role_defaults_to_group_vars(self, roles):
        """
        Writes role defaults from a list of roles to group_vars.

        Args:
            roles (sequence): A sequence of Role objects.
        """
        group_vars_path = self.path / 'group_vars'
        for role in roles:
            role = Role(role.path)
            group_vars_file_path = group_vars_path / role.name
            is_new = True
            if (group_vars_file_path).exists():
                is_new = False
                group_vars_file_path.unlink()

            for defaults_file in role.defaults.values():
                with open(group_vars_file_path, 'a') as group_vars_file_stream:
                    yaml.dump(defaults_file['data'], group_vars_file_stream)
            if is_new:
                commit_message = 'Add new group_vars file from role {}'.format(
                    role.name)
                self.deployment_repo.update(commit_message,
                                            files=[str(group_vars_file_path)])

    def _write_ansible_cfg(self):
        """
        Write ansible config file to deployment directory.
        """
        ansible_cfg_path = self.path / 'ansible.cfg'
        with open(ansible_cfg_path, 'w') as ansible_cfg_stream:
            ansible_cfg_stream.writelines('\n'.join(self.ansible_cfg))

    def create(self):
        """
        Create deployment directory.
        """
        self._create_deployment_directories()
        self.deployment_repo.init()
        self.deployment_repo.update('initial commit', force_commit=True)
        self.roles_repo.clone()
        self._write_ansible_cfg()

    def delete(self):
        """
        Delete deployment directory.
        """
        shadow_git = self.path / '.git.shadow'
        if shadow_git.exists():
            shutil.rmtree(shadow_git)
        for directory_name in self.directory_layout:
            directory_path = self.path / directory_name
            if directory_path.exists():
                shutil.rmtree(directory_path)

        for file_name in self.deployment_files:
            file_path = self.path / file_name
            if file_path.exists():
                file_path.unlink()

        if self.roles_path.exists():
            shutil.rmtree(self.roles_path)

    def update(self, deployment, scope='all'):
        """
        Update deployment directory.

        Args:
            deployment (Deployment): Initialized deployment object.
            scope (str): Scope of update. May be:

                        `all`
                        `roles`
                        `playbook`
                        `inventory`
                        `group_vars`
                        `ansible_cfg`

        The update will pull changes from the roles src repo and
        will update all deployment files.

        The update will NOT commit any deployment specific changes.
        """
        if not self.roles_path.exists():
            scope = None
        if scope in ('all', 'roles'):
            self.roles_repo.pull()
        if scope in ('all', 'playbook'):
            deployment.playbook.write()
        if scope in ('all', 'inventory'):
            deployment.inventory.write()
        if scope in ('all', 'group_vars'):
            self._write_role_defaults_to_group_vars(deployment.roles)
        if scope in ('all', 'ansible_cfg'):
            self._write_ansible_cfg()
        self.deployment_repo.update_changed_files()
