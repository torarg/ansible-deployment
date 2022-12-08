"""
Module containing the DeploymentVault class.
"""

import shutil
import tarfile
from pathlib import Path
from cryptography.fernet import Fernet
from ansible_deployment.class_skeleton import AnsibleDeployment
from ansible_deployment.deployment_repo import DeploymentRepo


class DeploymentVault(AnsibleDeployment):
    """
    Represents a deployment vault used for file encryption.

    Args:
        vault_files (sequence): Sequence of paths defining vault content.
        path (path): Vault root directory.

    Attributes:
        path (Path): Vault root directory.
        locked (bool): True if vault is currently locked.
        new_key (bool): True if a new key was created.
        key_file (Path): Path to key file.
                         Defaults to `self.path / 'deployment.key'`
        key (byte): Key used for encryption.
        files (sequence): Sequence of paths defining vault content.

    Note:
        If `key_file` is not present at initialization, it will be created.
    """

    encryption_suffix = ".enc"

    def __init__(self, vault_files, path, key_name="deployment.key"):
        self.new_key = False
        self.locked = False
        self.path = Path(path)
        self.tar_path = self.path / "deployment.tar.gz"
        self.key_file = self.path / key_name
        self._load_key()
        self.files = vault_files
        self.locked_files = list(
            self.path.glob("**/*{}".format(self.encryption_suffix))
        )
        if len(self.locked_files) > 0:
            self.locked = True
            self.files = self.locked_files

    def _load_key(self):
        """
        Read or create `self.key_file` and update `self.key`.

        Note:
            Key will be generated and written to `self.key_file` if
            `self.key_file` does not exist.
        """
        if self.key_file.exists():
            with open(self.key_file, "rb") as fobj:
                self.key = fobj.read()
        else:
            self.key = self._generate_key()
            self._save_key()
            self.new_key = True

    def _save_key(self):
        """
        Write `self.key` to `self.key_file`.
        """
        with open(self.key_file, "wb") as fobj:
            fobj.write(self.key)
        self.key_file.chmod(0o600)

    @staticmethod
    def _generate_key():
        """
        Generate a new key.

        Returns:
            byte: Generated key.
        """
        return Fernet.generate_key()

    def _encrypt_file(self, file_path):
        """
        Encrypt a single file.

        Args:
            file_path (Path): Path object for target file.
        """
        cipher_suite = Fernet(self.key)
        with open(file_path, "rb") as fobj:
            plain_data = fobj.read()
        if int(oct(file_path.stat().st_mode)[-3]) < 6:
            file_path.chmod(0o640)
        with open(file_path, "wb") as fobj:
            fobj.write(cipher_suite.encrypt(plain_data))
        file_path.replace(str(file_path) + self.encryption_suffix)

    def _encrypt_files(self, files):
        """
        Encrypt a sequence of files.

        Args:
            files (sequence): Sequence of Path objects.
        """
        tar = tarfile.open(self.tar_path, 'w:gz')
        for file_name in files:
            file_path = Path(file_name)
            if file_path.exists() and file_path.name != self.key_file.name:
                tar.add(file_path)
        tar.close()
        self._encrypt_file(self.tar_path)

    def _decrypt_files(self, files):
        """
        Decrypt a sequence of files.

        Args:
            files (sequence): Sequence of Path objects.
        """
        for file_name in files:
            file_path = Path(file_name)
            if not file_path.exists():
                pass
            elif file_path.is_file():
                self._decrypt_file(file_path)
            elif file_path.is_dir():
                files_in_subdir = list(file_path.glob("*"))
                self._decrypt_files(files_in_subdir)

    def _decrypt_file(self, file_path):
        """
        Decrypt a single file.

        Args:
            file_path (Path): Path object for target file.
        """
        cipher_suite = Fernet(self.key)
        with open(file_path, "rb") as fobj:
            encrypted_data = fobj.read()
        with open(file_path, "wb") as fobj:
            fobj.write(cipher_suite.decrypt(encrypted_data))
        file_path.replace(str(file_path)[: -len(self.encryption_suffix)])

    def setup_shadow_repo(self):
        """
        Replaces deployment repo with a 'shadow repo'.

        The deployment git repository in ``self.path / '.git'``
        will be moved to ``self.path / '.git.enc'`` and if
        ``self.path / '.git.shadow'`` exists, it's config will be moved
        to ``self.path / '.git'``.
        A new repositoriy will be intialized and all files in ``self.files``
        including the original deployment repository will be
        added and commited to this new repository.

        The purpose of the shadow repository is to have
        a pushable deployment state while the deployment
        is locked.
        """
        git_path = self.path / ".git"
        git_config_path = git_path / "config"
        exclude_files = ('deployment.key', '.terraform')

        with open(git_config_path) as f:
            git_config_data = f.read()
        shutil.rmtree(git_path)
        deployment_files = list(
            self.path.glob("*")
        )
        shadow_repo_files = []
        for file in deployment_files:
            if file.name not in exclude_files:
                shadow_repo_files.append(file)
        shadow_repo = DeploymentRepo(self.path, files=shadow_repo_files)
        shadow_repo.init()

        shadow_repo.update(
            message="Shadow repository activated.",
            force_commit=True,
            files=shadow_repo_files,
        )

        with open(git_config_path, 'w') as f:
            f.write(git_config_data)


    def _restore_deployment_dir(self):
        """
        Restores deployment dir from tar archive.
        """
        git_path = self.path / '.git'
        git_config_path = git_path / "config"

        with open(git_config_path) as f:
            git_config_data = f.read()

        if git_path.exists():
            shutil.rmtree(git_path)
        if not self.tar_path.exists():
            raise FileNotFoundError(self.tar_path)

        with tarfile.open(self.tar_path) as tar:
            tar.extractall(self.path)

        with open(git_config_path, 'w') as f:
            f.write(git_config_data)

        self.tar_path.unlink()


    def lock(self):
        """
        Encrypts all files stored in the vault and activates shadow repo.

        The git repository in ``self.path`` will be encrypted and replaced
        with a shadow repository containing all encrypted vault files as
        a single commit. If an old instance of the shadow repository
        had a custuom config this will be restored in the new shadow
        repository.
        """
        if not self.locked:
            self._encrypt_files(self.files)
            self.locked = True
        else:
            raise EnvironmentError("Deployment already locked")

    def unlock(self):
        """
        Decrypts all vault files and restores the deployment repository.

        The shadow repository's configuration file willl be saved
        to ``self.path / '.git.shadow/config``.
        """
        if self.locked:
            enc_tar = Path(str(self.tar_path) + self.encryption_suffix)
            self._decrypt_file(enc_tar)
            self._restore_deployment_dir()
            self.locked = False
        else:
            raise EnvironmentError("Deployment already unlocked")
