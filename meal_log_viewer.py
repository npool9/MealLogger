from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QDateEdit,
    QCheckBox
)
from PyQt6.QtCore import Qt, QDate


class MealLogViewer(QDialog):
    """
    Dialog for viewing meal log entries with optional date filtering
    """

    def __init__(self, meal_logs):
        """
        Initialize the meal log viewer
        :param meal_logs: list of tuples (meal_name, date_eaten, servings, calories, protein, carbs, fat)
        """
        super().__init__()
        self.setWindowTitle("Meal Log Viewer")
        self.resize(900, 500)

        self._all_logs = meal_logs
        self.meal_logs = meal_logs

        # -------- Layout --------
        layout = QVBoxLayout()
        self.setLayout(layout)

        # -------- Filter Bar --------
        filter_layout = QHBoxLayout()
        layout.addLayout(filter_layout)

        filter_layout.addWidget(QLabel("Filter by date:"))

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        filter_layout.addWidget(self.date_edit)

        self.show_all_cb = QCheckBox("Show all dates")
        self.show_all_cb.setChecked(True)
        self.show_all_cb.toggled.connect(self._toggle_date_filter)
        filter_layout.addWidget(self.show_all_cb)

        btn_filter = QPushButton("Apply Filter")
        btn_filter.clicked.connect(self.apply_filter)
        filter_layout.addWidget(btn_filter)

        filter_layout.addStretch()

        # -------- Table --------
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Meal Name", "Date Eaten", "Servings",
            "Calories", "Protein (g)", "Carbs (g)", "Fat (g)"
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.refresh_table()

        # -------- Buttons --------
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        btn_layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

    def _toggle_date_filter(self, show_all):
        """Enable/disable the date edit based on the checkbox"""
        self.date_edit.setEnabled(not show_all)

    def apply_filter(self):
        """Filter meal logs by the selected date or show all"""
        if self.show_all_cb.isChecked():
            self.meal_logs = self._all_logs
        else:
            selected_date = self.date_edit.date().toPyDate()
            self.meal_logs = [
                row for row in self._all_logs
                if row[1] == selected_date
            ]
        self.refresh_table()

    def refresh_table(self):
        """Refresh the table with current meal log data"""
        self.table.setRowCount(len(self.meal_logs))

        for row, log in enumerate(self.meal_logs):
            # log: (meal_name, date_eaten, servings, calories, protein, carbs, fat)
            items = [
                QTableWidgetItem(str(log[0] or "")),
                QTableWidgetItem(str(log[1] or "")),
                QTableWidgetItem(str(log[2] or "")),
                QTableWidgetItem(f"{log[3]:.1f}" if log[3] is not None else ""),
                QTableWidgetItem(f"{log[4]:.1f}" if log[4] is not None else ""),
                QTableWidgetItem(f"{log[5]:.1f}" if log[5] is not None else ""),
                QTableWidgetItem(f"{log[6]:.1f}" if log[6] is not None else ""),
            ]
            for col, item in enumerate(items):
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()

    def bring_to_front(self):
        """Bring the window to the front"""
        self.raise_()
        self.activateWindow()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.show()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()