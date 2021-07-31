from pathlib import Path

class SSHKeypair:
    """
    Represents a ssh key pair.

    Contains paths and values for a ssh public and private keys.

    Attributes:
        public_key (str): Public key
        private_key (str): Private key
        public_key_path (Path): Public key path
        private_key_path (Path): Private key path
    """

    def __init__(self, public_key=None, public_key_path=None,
                 private_key=None, private_key_path=None):
        self.public_key = public_key
        self.private_key = private_key

        try:
            self.public_key_path = Path(public_key_path)
        except TypeError:
            self.public_key_path = None

        try:
            self.private_key_path = Path(private_key_path)
        except TypeError:
            self.private_key_path = None

    def read(self):
        if self.public_key_path is not None and self.public_key_path.exists():
            self.public_key = self.public_key_path.read_text()
        else:
            self.public_key = None

        if self.private_key_path is not None and self.private_key_path.exists():
            self.private_key = self.private_key_path.read_text()
        else:
            self.private_key = None

    def write(self):
        if self.public_key is not None and self.public_key_path is not None:
            self.public_key_path.write_text(self.public_key)
        else:
            print("could not write public key")
            print(self.public_key)
            print(self.public_key_path)
        if self.private_key is not None and self.private_key_path is not None:
            self.private_key_path.write_text(self.private_key)
        else:
            print("could not write private key")
            print(self.private_key)
            print(self.private_key_path)
            

    def update_with(self, update_keypair):
        """
        Updates keypair with the attributes of another keypair.
        """
        if update_keypair.public_key is not None:
            self.public_key = update_keypair.public_key
        if update_keypair.private_key is not None:
            self.private_key = update_keypair.private_key
        if update_keypair.public_key_path is not None:
            self.public_key_path = update_keypair.public_key_path
        if update_keypair.private_key_path is not None:
            self.private_key_path = update_keypair.private_key_path
