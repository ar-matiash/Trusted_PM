import csv
from PyQt6.QtCore import QDate, QTimer, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QDateEdit,
    QAbstractItemView, QLineEdit, QFileDialog,
)
from core.models import VaultEntry


class MainWindow(QWidget):
    """
    The main interface for viewing and managing decrypted vault entries.
    Provides table-based editing, CSV import/export, and undo functionality.
    """

    def __init__(self, vault_manager):
        """
        Initializes the MainWindow and sets up the table and control buttons.

        :param vault_manager: The manager handling encryption and data storage.
        """
        super().__init__()

        self.vault_manager = vault_manager
        self.undo_stack = []

        # Window Configuration
        self.setWindowTitle("Decrypted Vault")
        self.setMinimumWidth(1070)
        self.resize(1070, 600)

        self._setup_ui()
        self.load_entries()

    def _setup_ui(self):
        """
        Internal helper to initialize layouts and widgets.
        """
        layout = QVBoxLayout()

        # Table Configuration
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.table.verticalHeader().setSectionResizeMode(self.table.verticalHeader().ResizeMode.Fixed)

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Service", "Site", "Login", "Password", "Status", "Updated", "Note"]
        )

        column_widths = [100, 200, 150, 150, 130, 120, 170]
        for i, w in enumerate(column_widths):
            self.table.setColumnWidth(i, w)

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)

        # Search and Control Buttons
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search...")

        self.import_button = QPushButton("Import CSV")
        self.export_button = QPushButton("Export CSV")
        self.delete_button = QPushButton("Delete")
        self.undo_button = QPushButton("Undo")
        self.exit_button = QPushButton("Exit Vault")

        button_layout = QHBoxLayout()
        for widget in [self.search_field, self.import_button, self.export_button,
                       self.delete_button, self.undo_button, self.exit_button]:
            button_layout.addWidget(widget)

        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Signal Connections
        self.table.itemChanged.connect(self.table_item_changed)
        self.table.cellClicked.connect(self.save_undo_state)
        self.search_field.textChanged.connect(self.filter_rows)
        self.import_button.clicked.connect(self.import_csv)
        self.export_button.clicked.connect(self.export_csv)
        self.delete_button.clicked.connect(self.delete_entry)
        self.undo_button.clicked.connect(self.undo)
        self.exit_button.clicked.connect(self.exit_vault)

    def _create_status_box(self, current_text="active"):
        """
        Helper to create a pre-configured QComboBox for the Status column.

        :param current_text: The status string to select by default.
        :return: QComboBox: A configured dropdown menu.
        """
        box = QComboBox()
        box.addItems(["active", "updated", "terminated", "term.process", "to delete"])
        box.setCurrentText(current_text)
        box.currentIndexChanged.connect(self.autosave)
        return box

    def _create_date_edit(self, date_str=None):
        """
        Helper to create a pre-configured QDateEdit for the Updated column.

        :param date_str: Date string in 'dd-MM-yyyy' format.
        :return: QDateEdit: A configured date picker.
        """
        date_edit = QDateEdit()
        date_edit.setDisplayFormat("dd-MM-yyyy")
        date_edit.setCalendarPopup(True)

        if date_str:
            date_edit.setDate(QDate.fromString(date_str, "dd-MM-yyyy"))
        else:
            date_edit.setDate(QDate.currentDate())

        date_edit.dateChanged.connect(self.autosave)
        return date_edit

    def load_entries(self, sort_after_load=True):
        """
        Fills the table with entries from the vault manager.

        :param sort_after_load: Whether to apply alphabetical sorting after loading.
        """
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.vault_manager.entries))

        for row, entry in enumerate(self.vault_manager.entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.service))
            self.table.setItem(row, 1, QTableWidgetItem(entry.site))
            self.table.setItem(row, 2, QTableWidgetItem(entry.login))
            self.table.setItem(row, 3, QTableWidgetItem(entry.password))
            self.table.setCellWidget(row, 4, self._create_status_box(entry.status))
            self.table.setCellWidget(row, 5, self._create_date_edit(entry.updated))
            self.table.setItem(row, 6, QTableWidgetItem(entry.note))

        # Add the placeholder empty row for new data entry
        self.table.insertRow(self.table.rowCount())
        new_row = self.table.rowCount() - 1
        self.table.setCellWidget(new_row, 4, self._create_status_box())
        self.table.setCellWidget(new_row, 5, self._create_date_edit())

        self.table.blockSignals(False)

        if sort_after_load:
            self.sort_entries()

    def delete_entry(self):
        """
        Removes the currently selected row from the table.
        """
        self.save_undo_state()
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.autosave()

    def exit_vault(self):
        """
        Closes the main window and returns to the Welcome Screen.
        """
        from gui.welcome_window import WelcomeWindow
        self.welcome_window = WelcomeWindow()
        self.welcome_window.show()
        self.close()

    def table_item_changed(self):
        """
        Handles data changes in table items, triggering the creation of new rows if needed.
        """
        if self.table.signalsBlocked():
            return
        # Use singleShot to let the current event finish before modifying structure
        QTimer.singleShot(0, self.ensure_empty_row)

    def autosave(self):
        """
        Collects all data from the table and saves it to the encrypted vault file.
        """
        if self.table.state() == self.table.State.EditingState:
            QTimer.singleShot(100, self.autosave)
            return

        if self.table.signalsBlocked():
            return

        self.table.blockSignals(True)
        self.vault_manager.entries.clear()

        for row in range(self.table.rowCount()):
            # Extract widgets and items
            service = self.table.item(row, 0)
            site = self.table.item(row, 1)
            login = self.table.item(row, 2)
            password_item = self.table.item(row, 3)
            status_widget = self.table.cellWidget(row, 4)
            updated_widget = self.table.cellWidget(row, 5)
            note = self.table.item(row, 6)

            # Skip empty rows (where text fields are blank)
            text_values = [
                service.text() if service else "",
                site.text() if site else "",
                login.text() if login else "",
                password_item.text() if password_item else "",
                note.text() if note else ""
            ]
            if not any(v.strip() for v in text_values):
                continue

            entry = VaultEntry(
                service=text_values[0],
                site=text_values[1],
                login=text_values[2],
                password=text_values[3],
                status=status_widget.currentText() if status_widget else "active",
                updated=updated_widget.date().toString("dd-MM-yyyy") if updated_widget else "",
                note=text_values[4]
            )
            self.vault_manager.entries.append(entry)

        self.vault_manager.save_vault()
        self.table.blockSignals(False)

    def save_undo_state(self):
        """
        Takes a snapshot of the current table data and pushes it to the undo stack.
        """
        snapshot = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                if col == 4:  # Status
                    widget = self.table.cellWidget(row, col)
                    row_data.append(widget.currentText() if widget else "")
                elif col == 5:  # Date
                    widget = self.table.cellWidget(row, col)
                    row_data.append(widget.date().toString("dd-MM-yyyy") if widget else "")
                else:
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
            snapshot.append(row_data)

        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def undo(self):
        """
        Restores the table to the last saved state from the undo stack.
        """
        if not self.undo_stack:
            return

        snapshot = self.undo_stack.pop()
        self.table.blockSignals(True)
        self.table.setRowCount(len(snapshot))

        for r, row_data in enumerate(snapshot):
            for c, value in enumerate(row_data):
                if c == 4:
                    self.table.setCellWidget(r, c, self._create_status_box(value))
                elif c == 5:
                    self.table.setCellWidget(r, c, self._create_date_edit(value))
                else:
                    self.table.setItem(r, c, QTableWidgetItem(value))

        self.table.blockSignals(False)
        self.autosave()

    def ensure_empty_row(self):
        """
        Checks if the last row is filled; if so, appends a new empty row for future entries.
        """
        rows = self.table.rowCount()
        if rows == 0:
            return

        last_row = rows - 1
        for c in range(self.table.columnCount()):
            item = self.table.item(last_row, c)
            if item and item.text().strip():
                # Last row has content, create a new one
                self.table.blockSignals(True)
                self.table.insertRow(rows)
                self.table.setCellWidget(rows, 4, self._create_status_box())
                self.table.setCellWidget(rows, 5, self._create_date_edit())
                self.table.blockSignals(False)
                QTimer.singleShot(0, self.autosave)
                break

    def filter_rows(self):
        """
        Filters table rows based on the text entered in the search field.
        """
        text = self.search_field.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def export_csv(self):
        """
        Exports the current vault entries to a CSV file.
        """
        default_name = f"{self.vault_manager.vault_path.stem}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export vault", default_name, "CSV files (*.csv)")

        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Service", "Site", "Login", "Password", "Status", "Updated", "Note"])
            for e in self.vault_manager.entries:
                writer.writerow([e.service, e.site, e.login, e.password, e.status, e.updated, e.note])

    def import_csv(self):
        """
        Imports passwords from a CSV file and appends them to the current vault.
        """
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV files (*.csv)")
        if not path:
            return

        self.save_undo_state()
        with open(path, newline="", encoding="utf-8") as f:
            sample = f.read(2048)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.reader(f, dialect)
            next(reader, None)  # Skip header

            for row in reader:
                if not row: continue
                entry = VaultEntry(
                    service=row[0] if len(row) > 0 else "",
                    site=row[1] if len(row) > 1 else "",
                    login=row[2] if len(row) > 2 else "",
                    password=row[3] if len(row) > 3 else "",
                    status="active",
                    updated=QDate.currentDate().toString("dd-MM-yyyy"),
                    note=" ".join(row[4:]) if len(row) > 4 else ""
                )
                self.vault_manager.entries.append(entry)

        self.vault_manager.save_vault()
        self.load_entries(sort_after_load=False)

    def sort_entries(self):
        """
        Sorts the underlying data entries alphabetically by service, site, and login.
        """
        self.vault_manager.entries.sort(
            key=lambda e: (
                (e.service or "").lower(),
                (e.site or "").lower(),
                (e.login or "").lower()
            )
        )
        self.load_entries(sort_after_load=False)