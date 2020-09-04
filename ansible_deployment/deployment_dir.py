from pathlib import Path
from git import Repo
import gitdb.exc as git_exc
from pprint import pformat
from ansible_deployment.class_skeleton import AnsibleDeployment
from ansible_deployment.role import Role
import yaml
import shutil


class DeploymentDirectory(AnsibleDeployment):
    """
    Represents an ansible deployment directory.

    Args:
        path (path): Path to deployment directory.
        roles_src (RolesRepo): Namedtuple containing roles repo config.
        config_file (path): Path to deployment config file.

    Attributes:
        path (Path): Path to deployment directory.
        roles_src (dict): Roles repo git information.
        roles_path (Path): Path to deployment roles directory.
        config_file (Path): Path to deployment config file.
        repo (git.Repo): Deployment git repository.
        unstaged_changes (list): List of unstaged files.
        staged_changes (list): List of staged files.
        changes (list): List of all changed files.
    """
    ansible_cfg = [
        '[defaults]', 'inventory = hosts.yml', 'host_key_checking = False'
    ]
    directory_layout = ('host_vars', 'group_vars', '.git')
    deployment_files = [
        'playbook.yml', 'hosts.yml', 'ansible.cfg', '.gitmodules'
    ]
    git_repo_content = deployment_files + [
        'host_vars', 'group_vars', 'deployment.json'
    ]

    def __init__(self, path, roles_src, config_file='deployment.json'):
        self.path = Path(path)
        self.roles_src = roles_src
        self.roles_path = self.path / 'roles'
        self.config_file = self.path / 'deployment.json'
        self.repo = Repo.init(self.path)
        self.unstaged_changes = []
        self._update_changed_files()

    def _update_changed_files(self):
        """
        Set attributes representing file changes to current repository state.

        Updates the following attributes:
            `unstaged_changes`
            `staged_changes`
            `changes`
        """
        self.unstaged_changes = [
            diff.a_path for diff in self.repo.index.diff(None)
        ]
        try:
            self.staged_changes = [
                diff.a_path for diff in self.repo.index.diff('HEAD')
            ]
        except git_exc.BadName:
            self.staged_changes = []
        self.changes = self.staged_changes + self.unstaged_changes

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
                self.update_git(commit_message,
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
        self.update_git('initial commit', force_commit=True)
        self.repo.git.subtree('add', '--prefix', 'roles', '--squash',
                              self.roles_src.repo, self.roles_src.branch)
        self._write_ansible_cfg()

    def delete(self):
        """
        Delete deployment directory.
        """
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

    def update(self, roles, playbook, inventory):
        """
        Update deployment directory.

        The update will pull changes from the roles src repo and
        will update all deployment files.

        The update will NOT commit any changes to the main deployment directory.
        """
        if not self.roles_path.exists():
            return None
        self.repo.git.subtree('pull', '--prefix', 'roles', '--squash',
                              self.roles_src.repo, self.roles_src.branch)
        playbook.write()
        inventory.write()
        self._write_role_defaults_to_group_vars(roles)
        self._write_ansible_cfg()
        self._update_changed_files()

    def update_git(self,
                   message="Automatic ansible-deployment update.",
                   files=git_repo_content,
                   force_commit=False):
        """
        Updates the deployment git repository.

        Args:
            message (str): Commit message.
            files (sequence): Files to commit.
            force_commit (bool): Whether or not to force an empty commit.

        The update will add the specified files and commit them.
        """
        for git_file in files:
            if Path(git_file).exists():
                self.repo.index.add(git_file)
        self._update_changed_files()
        if len(self.staged_changes) > 0 or force_commit:
            self.repo.index.commit("ansible-deployment: {}".format(
                message.capitalize()))
