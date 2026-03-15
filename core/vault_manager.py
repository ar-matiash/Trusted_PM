import json
from pathlib import Path

from core.crypto_manager import CryptoManager
from core.models import VaultEntry


class VaultManager:
    """
    Manages the lifecycle of a vault file, including creation,
    authentication (unlocking), and secure data persistence.
    """

    def __init__(self, vault_path):
        """
        Initializes the manager with a specific file path.

        :param vault_path: The filesystem path (str or Path) to the .vault file.
        """
        self.vault_path = Path(vault_path)
        self.entries = []
        self.crypto = None

    def create_vault(self, password: str):
        """
        Generates a new salt, initializes the crypto engine, and creates
        an empty encrypted vault file.

        :param password: The master password used to derive the encryption key.
        """
        # Generate a unique salt for this specific vault
        salt = CryptoManager.generate_salt()
        self.crypto = CryptoManager(password, salt)

        # Create the initial empty structure
        empty_data = json.dumps({"entries": []}).encode()
        encrypted = self.crypto.encrypt(empty_data)

        # Write the 16-byte salt followed by the encrypted payload
        with open(self.vault_path, "wb") as f:
            f.write(salt)
            f.write(encrypted)

    def unlock_vault(self, password: str):
        """
        Reads the salt from the file, derives the key, and decrypts the entries.

        :param password: The master password provided by the user.
        :raises Exception: If decryption fails (usually due to an incorrect password).
        """
        with open(self.vault_path, "rb") as f:
            # First 16 bytes are always the salt
            salt = f.read(16)
            encrypted = f.read()

        # Initialize crypto with the stored salt
        self.crypto = CryptoManager(password, salt)

        # Decrypt and parse the JSON structure
        decrypted = self.crypto.decrypt(encrypted)
        data = json.loads(decrypted)

        # Convert dictionary list back into VaultEntry objects
        self.entries = [VaultEntry(**e) for e in data["entries"]]

    def save_vault(self):
        """
        Serializes current entries to JSON, encrypts the data, and overwrites
         the vault file while preserving the original salt.
        """
        # Convert objects back to a dictionary for JSON serialization
        data = {
            "entries": [e.__dict__ for e in self.entries]
        }

        raw = json.dumps(data).encode()
        encrypted = self.crypto.encrypt(raw)

        # We must retrieve the existing salt to keep the file consistent
        with open(self.vault_path, "rb") as f:
            salt = f.read(16)

        # Overwrite the file with the same salt but new encrypted data
        with open(self.vault_path, "wb") as f:
            f.write(salt)
            f.write(encrypted)
