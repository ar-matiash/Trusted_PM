import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class CryptoManager:
    """
    Handles key derivation and provides symmetric encryption/decryption
    utilities using the Fernet (AES-128 in CBC mode) standard.
    """

    def __init__(self, password: str, salt: bytes):
        """
        Initializes the manager by deriving a cryptographic key from a password.

        :param password: The plain-text master password.
        :param salt: A 16-byte random salt used for key derivation.
        """
        self.password = password.encode()
        self.salt = salt
        self.key = self._derive_key()

        # Fernet handles encryption, signing (HMAC), and integrity verification.
        self.fernet = Fernet(self.key)

    def _derive_key(self):
        """
        Derives a URL-safe base64-encoded key using PBKDF2 with SHA-256.

        :return: bytes: The derived encryption key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=390000,  # High iteration count to resist brute-force
        )

        return base64.urlsafe_b64encode(kdf.derive(self.password))

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypts a byte string.

        :param data: The raw data to be encrypted.
        :return: bytes: The encrypted ciphertext.
        """
        return self.fernet.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypts a byte string.

        :param data: The ciphertext to be decrypted.
        :return: bytes: The original decrypted data.
        :raises cryptography.fernet.InvalidToken: If the key is wrong or data is corrupted.
        """
        return self.fernet.decrypt(data)

    @staticmethod
    def generate_salt():
        """
        Generates a secure, cryptographically strong random 16-byte salt.

        :return: bytes: A random salt.
        """
        return os.urandom(16)