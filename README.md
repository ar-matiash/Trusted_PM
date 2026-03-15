<img src="assets/lock.png" width="200" alt="Project Logo">

# Trusted Password Manager

A lightweight and secure password manager built with **Python** and **PyQt6**. This application allows users to create encrypted vaults to store sensitive login information, service details, and notes.

## 🛡️ Security Features

This project focuses on implementing industry-standard cryptographic practices:
- **Symmetric Encryption:** Uses **AES-128** in CBC mode via the [Fernet](https://cryptography.io/en/latest/fernet/) specification.
- **Key Derivation:** Master passwords are never stored. Instead, they are processed using **PBKDF2HMAC** with **SHA-256**.
- **Brute-force Resistance:** Configured with **390,000 iterations** to ensure high computational cost for attackers.
- **Unique Salting:** Every vault generates a unique **16-byte salt** using `os.urandom()`, preventing rainbow table attacks.
- **Data Integrity:** Fernet tokens ensure that if the vault file is tampered with, the decryption process will fail immediately.

## 🚀 Features

- **Multiple Vaults:** Create and manage different vault files for different purposes.
- **Dynamic Table Editing:** Add, edit, and delete entries directly in a spreadsheet-like interface.
- **Auto-save & Undo:** All changes are automatically encrypted and saved; supports up to 20 levels of undo.
- **Search & Filter:** Quickly find your credentials using the real-time search bar.
- **CSV Support:** Import from or export to CSV for easy migration from other managers.
