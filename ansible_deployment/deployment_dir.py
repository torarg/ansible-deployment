"""
This module contains the DeploymentDirectory class.

It may also be used for DeploymentDirectory related helper functions
or classes in the future.
"""

import shutil
import yaml
import subprocess
from pathlib import Path
from ansible_deployment.class_skeleton import AnsibleDeployment
from ansible_deployment.role import Role
from ansible_deployment.deployment_vault import DeploymentVault
from ansible_deployment.deployment_repo import DeploymentRepo
from ansible_deployment.config import load_config_file


class DeploymentDirectory(AnsibleDeployment):
    """
    Represents an ansible deployment directory.

    Args:
        path (path): Path to deployment directory.
        roles_repo (RepoConfig): Namedtuple containing roles repo config.
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
        "[defaults]",
        "inventory = hosts.yml",
        "host_key_checking = False",
        "interpreter_python = auto_silent",
        "stdout_callback = yaml"
    ]
    directory_layout = ("host_vars", "group_vars", "roles", ".ssh", ".roles.git", ".git")
    deployment_files = ["playbook.yml", "hosts.yml", "ansible.cfg"]

    def __init__(self, path, roles_repo_config, deployment_key_file="deployment.key", deployment_key=None):
        self._roles_repo_config = roles_repo_config

        self.path = Path(path)
        self.config_file = self.path / "deployment.json"
        self.ssh_private_key = self.path / ".ssh" / "id_rsa"
        self.ssh_public_key = self.path / ".ssh" / "id_rsa.pub"
        self.additional_files = []

        self.filtered_representation = {
            "path": str(self.path),
            "roles_repo": str(roles_repo_config),
        }

        self.roles_path = self.path / "roles"
        self.roles_repo_path = self.path / ".roles.git"
        self.roles_repo = DeploymentRepo(self.roles_repo_path, remote_config=roles_repo_config)

        git_repo_content = [] + self.deployment_files
        git_repo_content += self.directory_layout[:-2]
        git_repo_content += [str(self.config_file)]
        git_repo_content += [deployment_key_file]
        self.deployment_repo = DeploymentRepo(self.path, files=git_repo_content)

        self.vault_files = self.deployment_files + list(self.directory_layout)
        self.vault_files.remove('.roles.git')
        self.vault = DeploymentVault(self.vault_files, self.path, deployment_key)

        if not self.vault.locked and self.deployment_repo.repo:
            self.deployment_repo.update_changed_files()
            if "deployment.json" in self.vault.files:
                self.vault.files.remove("deployment.json")

    def _create_deployment_directories(self):
        """
        Create deployment directories.
        """
        for directory_name in self.directory_layout:
            directory_path = self.path / directory_name
            if not directory_path.exists():
                directory_path.mkdir()

    def _copy_roles_to_deployment(self):
        """
        Copy roles to deployment directory.
        """
        roles = load_config_file(self.config_file).roles
        shutil.rmtree(self.roles_path)
        self.roles_path.mkdir()
        for role_name in roles:
            role = Role(name=role_name, path=self.roles_repo_path / role_name)
            role.copy_to(self.roles_path)

    def write_role_defaults_to_group_vars(self, roles):
        """
        Writes role defaults from a list of roles to group_vars.

        Args:
            roles (sequence): A sequence of Role objects.
        """
        group_vars_path = self.path / "group_vars"
        for role in roles:
            group_vars_file_path = group_vars_path / role.group_name
            if (group_vars_file_path).exists():
                group_vars_file_path.unlink()

            for defaults_file in role.defaults.values():
                with open(group_vars_file_path, "a") as group_vars_file_stream:
                    yaml.dump(defaults_file["data"], group_vars_file_stream)

    def _write_ansible_cfg(self):
        """
        Write ansible config file to deployment directory.
        """
        ansible_cfg_path = self.path / "ansible.cfg"
        with open(ansible_cfg_path, "w") as ansible_cfg_stream:
            ansible_cfg_stream.writelines("\n".join(self.ansible_cfg))

    def _generate_ssh_key(self):
        """
        Generates ssh key pair inside deployment directory.
        """
        if not self.ssh_private_key.exists():
            subprocess.run(["ssh-keygen", "-f", str(self.ssh_private_key), "-q", "-N", ""])


    def create(self):
        """
        Create deployment directory.
        """
        self._create_deployment_directories()
        self._generate_ssh_key()
        self.deployment_repo.init()
        self.roles_repo.clone()
        self._copy_roles_to_deployment()
        self._write_ansible_cfg()

    def delete(self, keep=[], additional_paths=[], full_delete=False):
        """
        Delete deployment directory.

        Args:
            keep (list): List of file system paths to exclude from deletion.
            additional_paths (list): List of file system paths for additional deletion.
        """
        if full_delete:
            self.vault.delete(delete_shadowgit=True)
        for directory_name in self.directory_layout:
            directory_path = self.path / directory_name
            if directory_path.exists() and directory_path.name not in keep:
                shutil.rmtree(directory_path)

        for file_name in self.deployment_files:
            file_path = self.path / file_name
            if file_path.exists() and file_path.name not in keep:
                file_path.unlink()

        if self.roles_path.exists():
            shutil.rmtree(self.roles_path)

        for path_name in additional_paths:
            p = Path(path_name)
            if not p.exists() or p.name in keep:
                continue
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()


    def update(self, deployment, scope="all"):
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
        if scope in ("all", "roles"):
            self.roles_repo.pull()
            self._copy_roles_to_deployment()
        if scope in ("all", "playbook"):
            deployment.playbook.write()
        if scope in ("all", "inventory"):
            deployment.update_inventory()
            deployment.inventory.write()
        if scope in ("all", "ansible_cfg"):
            self._write_ansible_cfg()
        self.deployment_repo.update_changed_files()
