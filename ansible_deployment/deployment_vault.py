from pathlib import Path
from cryptography.fernet import Fernet

class DeploymentVault:
    def __init__(self, key_file, vault_files, lock_file):
        self.new_key = False
        self.key_file = Path(key_file)
        self.files = vault_files
        self.lock_file = Path(lock_file)
        self.locked = self.lock_file.exists()
        self._load_key()
        
    def _load_key(self):
        if self.key_file.exists():
            with open(self.key_file, 'rb') as fobj:
                self.key = fobj.read()
        else:
            self.key = self._generate_key()
            self._save_key()
            self.new_key = True

    def _save_key(self):
        with open(self.key_file, 'wb') as fobj:
            fobj.write(self.key)
        self.key_file.chmod(0o400)

    def _generate_key(self):
        return Fernet.generate_key()

    def _encrypt_file(self, file_path):
        cipher_suite = Fernet(self.key)
        with open(file_path, 'rb') as fobj:
            plain_data = fobj.read()
        if int(oct(file_path.stat().st_mode)[-3]) < 6:
            file_path.chmod(0o640)
        with open(file_path, 'wb') as fobj:
            fobj.write(cipher_suite.encrypt(plain_data))

    def _encrypt_files(self, files):
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
        cipher_suite = Fernet(self.key)
        with open(file_path, 'rb') as fobj:
            encrypted_data = fobj.read()
        with open(file_path, 'wb') as fobj:
            fobj.write(cipher_suite.decrypt(encrypted_data))

    def lock(self):
        if not self.locked:
            self._encrypt_files(self.files)
            self.lock_file.touch()

    def unlock(self):
        if self.locked:
            self._decrypt_files(self.files)
            self.lock_file.unlink()
