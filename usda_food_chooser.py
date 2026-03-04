from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel
)
from PyQt6.QtCore import Qt


class USDAFoodChooser(QDialog):
    """
    Dialog for browsing and selecting USDA food search results with pagination.
    """

    def __init__(self, ingredient_name, foods, pagination, search_callback, parent=None):
        """
        :param ingredient_name: name of the ingredient (for window title)
        :param foods: list of food dicts from the first page of results
        :param pagination: dict with 'totalHits', 'currentPage', 'totalPages'
        :param search_callback: callable(page) -> dict with 'foods' and pagination keys
        """
        super().__init__(parent)
        self.setWindowTitle(f"Select USDA match for: {ingredient_name}")
        self.resize(750, 450)

        self.foods = foods
        self.pagination = pagination
        self.search_callback = search_callback
        self.selected_food = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Brand", "Data Type"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 350)
        self.table.setColumnWidth(1, 200)
        self.table.doubleClicked.connect(self._on_select)
        layout.addWidget(self.table)

        # Pagination bar
        page_layout = QHBoxLayout()
        layout.addLayout(page_layout)

        self.btn_prev = QPushButton("Previous")
        self.btn_prev.clicked.connect(self._prev_page)
        page_layout.addWidget(self.btn_prev)

        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(self.page_label)

        self.btn_next = QPushButton("Next")
        self.btn_next.clicked.connect(self._next_page)
        page_layout.addWidget(self.btn_next)

        # Select button
        btn_select = QPushButton("Select")
        btn_select.clicked.connect(self._on_select)
        layout.addWidget(btn_select)

        self._refresh()

    def _refresh(self):
        """Refresh table and pagination controls from current state."""
        self.table.setRowCount(len(self.foods))
        for row, food in enumerate(self.foods):
            self.table.setItem(row, 0, QTableWidgetItem(food.get("description", "")))
            self.table.setItem(row, 1, QTableWidgetItem(food.get("brandOwner", "")))
            self.table.setItem(row, 2, QTableWidgetItem(food.get("dataType", "")))

        # Select first row
        if self.foods:
            self.table.selectRow(0)

        cur = self.pagination["currentPage"]
        total = self.pagination["totalPages"]
        hits = self.pagination["totalHits"]
        self.page_label.setText(f"Page {cur} of {total} ({hits} total results)")
        self.btn_prev.setEnabled(cur > 1)
        self.btn_next.setEnabled(cur < total)

    def _prev_page(self):
        page = self.pagination["currentPage"] - 1
        if page < 1:
            return
        result = self.search_callback(page)
        self.foods = result["foods"]
        self.pagination = {
            "totalHits": result["totalHits"],
            "currentPage": result["currentPage"],
            "totalPages": result["totalPages"],
        }
        self._refresh()

    def _next_page(self):
        page = self.pagination["currentPage"] + 1
        if page > self.pagination["totalPages"]:
            return
        result = self.search_callback(page)
        self.foods = result["foods"]
        self.pagination = {
            "totalHits": result["totalHits"],
            "currentPage": result["currentPage"],
            "totalPages": result["totalPages"],
        }
        self._refresh()

    def _on_select(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            self.selected_food = self.foods[row]
        self.accept()

    def bring_to_front(self):
        self.raise_()
        self.activateWindow()
