import os
import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from gui.welcome_window import WelcomeWindow


def main():
    """
    Initializes the application, sets the global configuration,
    and launches the primary UI window.
    """
    app = QApplication(sys.argv)

    # Set the application taskbar and window icon
    app.setWindowIcon(QIcon(resource_path("assets/lock.png")))

    window = WelcomeWindow()
    window.show()

    sys.exit(app.exec())


def resource_path(relative_path):
    """
    Adjusts the file path to account for the PyInstaller runtime environment.

    :param relative_path (str): The relative path to the resource file.
    :return: str: The absolute path to the resource.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller creates a temporary folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Standard development environment
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    main()
