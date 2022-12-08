from pathlib import Path
from ansible_deployment.class_skeleton import AnsibleDeployment
from cryptography.fernet import Fernet


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
    encryption_suffix = '.enc'

    def __init__(self, vault_files, path):
        self.new_key = False
        self.locked = False
        self.path = Path(path)
        self.key_file = self.path / 'deployment.key'
        self._load_key()
        self.files = vault_files
        self.locked_files = list(
            self.path.glob('**/*{}'.format(self.encryption_suffix)))
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
            with open(self.key_file, 'rb') as fobj:
                self.key = fobj.read()
        else:
            self.key = self._generate_key()
            self._save_key()
            self.new_key = True

    def _save_key(self):
        """
        Write `self.key` to `self.key_file`.
        """
        with open(self.key_file, 'wb') as fobj:
            fobj.write(self.key)
        self.key_file.chmod(0o400)

    def _generate_key(self):
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
        with open(file_path, 'rb') as fobj:
            plain_data = fobj.read()
        if int(oct(file_path.stat().st_mode)[-3]) < 6:
            file_path.chmod(0o640)
        with open(file_path, 'wb') as fobj:
            fobj.write(cipher_suite.encrypt(plain_data))
        file_path.replace(str(file_path) + self.encryption_suffix)

    def _encrypt_files(self, files):
        """
        Encrypt a sequence of files.

        Args:
            files (sequence): Sequence of Path objects.
        """
        for file_name in files:
            file_path = Path(file_name)
            if not file_path.exists():
                pass
            elif file_path.is_file():
                self._encrypt_file(file_path)
            elif file_path.is_dir():
                files_in_subdir = list(file_path.glob('*'))
                self._encrypt_files(files_in_subdir)

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
                files_in_subdir = list(file_path.glob('*'))
                self._decrypt_files(files_in_subdir)

    def _decrypt_file(self, file_path):
        """
        Decrypt a single file.

        Args:
            file_path (Path): Path object for target file.
        """
        cipher_suite = Fernet(self.key)
        with open(file_path, 'rb') as fobj:
            encrypted_data = fobj.read()
        with open(file_path, 'wb') as fobj:
            fobj.write(cipher_suite.decrypt(encrypted_data))
        file_path.replace(str(file_path)[:-len(self.encryption_suffix)])

    def lock(self):
        """
        Lock vault and encrypt all files.
        """
        if not self.locked:
            self._encrypt_files(self.files)
            self.locked = True

    def unlock(self):
        """
        Unlock vault and decrypt all files.
        """
        if self.locked:
            self._decrypt_files(self.files)
            self.locked = False
