"""
Module containing the DeploymentVault class.
"""

import hashlib
import shutil
import tarfile
from pathlib import Path
from cryptography.fernet import Fernet
from ansible_deployment.class_skeleton import AnsibleDeployment
from ansible_deployment.deployment_repo import DeploymentRepo


class DeploymentVaultError(Exception):
    pass


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
    key_file_name = "deployment.key"
    tar_file_name = "deployment.tar.gz"
    lock_file_name = ".LOCKED"

    def __init__(self, vault_files, path, key=None):
        self.new_key = False
        self.locked = False
        self.path = Path(path)
        self.lock_file_path = self.path / self.lock_file_name
        self.tar_path = self.path / self.tar_file_name
        self.encrypted_tar_path = Path(str(self.tar_path) + self.encryption_suffix)
        self.encrypted_tar_sha256sum_path = Path(str(self.encrypted_tar_path) + ".SHA256")
        self.encrypted_tar_sha256sum = None
        self.key_file = self.path / self.key_file_name
        self._load_key(key)
        self.files = vault_files
        self.locked_files = list(
            self.path.glob("**/*{}".format(self.encryption_suffix))
        )
        if len(self.locked_files) > 0 or self.lock_file_path.exists():
            self.locked = True
            self.files = self.locked_files

    def _load_key(self, key=None):
        """
        Read or create `self.key_file` and update `self.key`.

        Note:
            Key will be generated and written to `self.key_file` if
            `self.key_file` does not exist.
        """
        if key is not None:
            self.key = key
            self._save_key()
        elif self.key_file.exists():
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

    def _sha256sum(self, file_path):
        """
        Create sha256 sum of file and write it to ``file_path.SHA256``.
        """
        h  = hashlib.sha256()
        b  = bytearray(128*1024)
        mv = memoryview(b)
        with open(file_path, 'rb', buffering=0) as f:
            for n in iter(lambda : f.readinto(mv), 0):
                h.update(mv[:n])
        return h.hexdigest()

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
        self.encrypted_tar_sha256sum = self._sha256sum(self.encrypted_tar_path)

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
        shadow_git_path = self.path / '.git.shadow'
        exclude_files = ('deployment.key', '.terraform', 'deployment.tar.gz.enc', '.ssh')
        include_files = ('.LOCKED', '.drone.yml', '.gitlab-ci', '.gitignore')

        with open(self.encrypted_tar_sha256sum_path, 'w') as f:
            f.write(self.encrypted_tar_sha256sum)

        shutil.rmtree(git_path)
        if shadow_git_path.exists():
            shutil.move(shadow_git_path, git_path)

        deployment_files = list(
            self.path.glob("[!.]*")
        )
        for file_name in include_files:
            deployment_files.append(self.path / file_name)

        shadow_repo_files = []
        for file in deployment_files:
            if file.name not in exclude_files and file.exists():
                shadow_repo_files.append(file)
        shadow_repo = DeploymentRepo(self.path, files=shadow_repo_files)
        shadow_repo.blobs['deployment_data'] = self.encrypted_tar_path
        shadow_repo.init()

        shadow_repo.update(
            message="Shadow repository activated.",
            force_commit=False,
            files=shadow_repo_files
        )

    def _restore_deployment_dir(self):
        """
        Restores deployment dir from tar archive.
        """
        git_path = self.path / '.git'
        shadow_git_path = self.path / '.git.shadow'

        if git_path.exists():
            shutil.move(git_path, shadow_git_path)

        with tarfile.open(self.tar_path) as tar:
            tar.extractall(self.path)

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
            self.lock_file_path.touch()
        else:
            raise DeploymentVaultError("Deployment already locked")

    def _verify_hash(self, file_path, expected_sha256sum):
        """Verify sha256 sum of file against an expected value."""
        sha256sum = self._sha256sum(file_path)
        return expected_sha256sum == sha256sum

    def unlock(self, force_unlock=False):
        """
        Decrypts all vault files and restores the deployment repository.

        The shadow repository's configuration file willl be saved
        to ``self.path / '.git.shadow/config``.
        """
        if self.locked:
            with open(self.encrypted_tar_sha256sum_path) as f:
                expected_hash = f.read()
            valid_hash = self._verify_hash(self.encrypted_tar_path, expected_hash)
            if not valid_hash and not force_unlock:
                raise DeploymentVaultError("Verification of encrypted deployment failed")
            self._decrypt_file(self.encrypted_tar_path)
            self._restore_deployment_dir()
            self.locked = False
            self.lock_file_path.unlink()
            self.encrypted_tar_sha256sum_path.unlink()
        else:
            raise DeploymentVaultError("Deployment already unlocked")
