import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QHBoxLayout,
    QMessageBox,
)

from core.vault_manager import VaultManager
from gui.main_window import MainWindow


class WelcomeWindow(QWidget):
    """
    Entry point window providing options to either unlock an existing vault
    or create a new encrypted storage file.
    """

    def __init__(self):
        """
        Initializes the WelcomeWindow, sets up the UI layouts, and loads existing vaults.
        """
        super().__init__()

        # Window Configuration
        self.setWindowTitle("Trusted Password Manager")
        self.setMinimumWidth(350)
        self.remaining_attempts = 3
        self.vault_manager = None

        # --- UI Components ---

        # Left Panel: Login/Open Vault
        self.title_left = QLabel("Open Vault")
        self.vault_selector = QComboBox()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Vault password")
        self.open_button = QPushButton("Unlock Vault")
        self.delete_button = QPushButton("Delete Vault")

        # Right Panel: Creation
        self.title_right = QLabel("Create Vault")
        self.new_vault_input = QLineEdit()
        self.new_vault_input.setPlaceholderText("New vault name")
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("New vault password")
        self.create_button = QPushButton("Create Vault")

        # --- Layout Setup ---

        main_layout = QHBoxLayout()

        # Left Column Layout
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_layout.addWidget(self.title_left)
        left_layout.addWidget(self.vault_selector)
        left_layout.addWidget(self.password_input)
        left_layout.addWidget(self.open_button)
        left_layout.addWidget(self.delete_button)

        # Right Column Layout
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_layout.addWidget(self.title_right)
        right_layout.addWidget(self.new_vault_input)
        right_layout.addWidget(self.new_password_input)
        right_layout.addWidget(self.create_button)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

        # --- Signal Connections ---

        self.open_button.clicked.connect(self.open_vault)
        self.delete_button.clicked.connect(self.delete_vault)
        self.create_button.clicked.connect(self.create_vault)

        # Initialize data
        self.load_vaults()

    def load_vaults(self):
        """
        Scans the storage directory for .vault files and populates the selector.
        """
        self.vault_selector.clear()

        # Ensure the storage directory exists
        if not os.path.exists("storage"):
            os.makedirs("storage")

        files = os.listdir("storage")
        for f in files:
            if f.endswith(".vault"):
                name = f.replace(".vault", "")
                self.vault_selector.addItem(name)

        # Disable buttons if no vaults are found
        has_vaults = self.vault_selector.count() > 0
        self.open_button.setEnabled(has_vaults)
        self.delete_button.setEnabled(has_vaults)

    def create_vault(self):
        """
        Creates a new vault file with the provided name and password.
        """
        name = self.new_vault_input.text().strip()
        password = self.new_password_input.text()

        if not name or not password:
            QMessageBox.warning(self, "Error", "Name and password are required.")
            return

        path = f"storage/{name}.vault"

        if os.path.exists(path):
            QMessageBox.warning(self, "Error", "Vault already exists.")
            return

        # Initialize and create the vault via VaultManager
        self.vault_manager = VaultManager(path)
        self.vault_manager.create_vault(password)

        self.open_main_window()

    def open_vault(self):
        """
        Authenticates the user and opens the selected vault.
        """
        name = self.vault_selector.currentText()
        password = self.password_input.text()

        if not name or not password:
            return

        path = f"storage/{name}.vault"
        self.vault_manager = VaultManager(path)

        try:
            self.vault_manager.unlock_vault(password)
            self.remaining_attempts = 3
            self.open_main_window()
        except Exception:
            self.remaining_attempts -= 1
            QMessageBox.critical(self, "Error", f"Incorrect password. Attempts left: {self.remaining_attempts}")

            if self.remaining_attempts <= 0:
                sys.exit()

    def open_main_window(self):
        """
        Transitions the UI from the Welcome screen to the Main application window.
        """
        self.main_window = MainWindow(self.vault_manager)
        self.main_window.show()
        self.close()

    def delete_vault(self):
        """
        Verifies credentials and deletes the selected vault file after confirmation.
        """
        name = self.vault_selector.currentText()
        password = self.password_input.text()

        if not name or not password:
            QMessageBox.warning(self, "Error", "Name and password required for deletion.")
            return

        path = f"storage/{name}.vault"

        try:
            # Verify password before allowing deletion
            temp_manager = VaultManager(path)
            temp_manager.unlock_vault(password)
        except Exception:
            QMessageBox.warning(self, "Error", "Incorrect password.")
            return

        # Double-check with the user
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to permanently delete vault '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            os.remove(path)
            QMessageBox.information(self, "Deleted", "Vault successfully deleted.")
            self.load_vaults()

        self.password_input.clear()