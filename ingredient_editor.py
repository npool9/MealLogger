from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QApplication,
    QInputDialog, QMessageBox, QRadioButton, QButtonGroup,
    QWidget
)
from PyQt6.QtCore import Qt
import sys


class IngredientEditor(QDialog):
    """
    The ingredient editor user interface
    """

    def __init__(self, ingredients):
        """
        Initialize the layout of the ingredient editor window
        """
        super().__init__()
        self.setWindowTitle("Ingredient Editor")
        self.resize(800, 550)

        self.ingredients = ingredients  # list of dicts from your parser

        # -------- Layout --------
        layout = QVBoxLayout()
        self.setLayout(layout)

        # -------- Table --------
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Amount", "Unit", "Name", "Section", "Notes", "Type"])
        self.table.setColumnWidth(5, 200)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.refresh_table()

        # -------- Buttons --------
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        btn_add = QPushButton("Add Ingredient")
        btn_add.clicked.connect(self.add_ingredient)
        btn_layout.addWidget(btn_add)

        btn_edit = QPushButton("Edit Selected")
        btn_edit.clicked.connect(self.edit_ingredient)
        btn_layout.addWidget(btn_edit)

        btn_remove = QPushButton("Remove Selected")
        btn_remove.clicked.connect(self.remove_ingredient)
        btn_layout.addWidget(btn_remove)

        btn_done = QPushButton("Save and Close")
        btn_done.clicked.connect(self.accept)
        btn_layout.addWidget(btn_done)

    def refresh_table(self):
        """
        Refresh the table with most up-to-date ingredient list
        """
        self.table.setRowCount(len(self.ingredients))

        for row, ing in enumerate(self.ingredients):
            amt = ing.get("amount")
            if isinstance(amt, dict):
                amt = f"{amt.get('min')}–{amt.get('max')}"
            elif amt is None:
                amt = ""

            items = [
                QTableWidgetItem(str(amt)),
                QTableWidgetItem(ing.get("unit") or ""),
                QTableWidgetItem(ing.get("name") or ""),
                QTableWidgetItem(ing.get("subsection") or ""),
                QTableWidgetItem(ing.get("notes") or "")
            ]

            for col, item in enumerate(items):
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, col, item)

            type_widget = self.create_type_widget(ing)
            self.table.setCellWidget(row, 5, type_widget)

    def add_ingredient(self):
        """
        Add an ingredient to the list
        """
        name, ok = QInputDialog.getText(self, "Add Ingredient", "Name:")
        if not ok or not name.strip():
            return

        amount, _ = QInputDialog.getText(self, "Add Ingredient", "Amount (optional):")
        unit, _ = QInputDialog.getText(self, "Add Ingredient", "Unit (optional):")
        section, _ = QInputDialog.getText(self, "Add Ingredient", "Section (optional):")
        notes, _ = QInputDialog.getMultiLineText(self, "Add Ingredient", "Notes (optional):")

        if isinstance(amount, dict):
            amount = f"{amount.get('min')}–{amount.get('max')}"
        elif amount is None:
            amount = ""

        self.ingredients.append({
            "amount": amount,
            "unit": unit or None,
            "name": name,
            "notes": notes or None,
            "subsection": section or None,
            "ingredient_type": "foundation",
            "original": None,
        })

        self.refresh_table()

    def edit_ingredient(self):
        """
        Edit an ingredient on the list
        """
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Edit", "Please select an ingredient first.")
            return

        ing = self.ingredients[row]

        name, ok = QInputDialog.getText(self, "Edit Ingredient", "Name:", text=ing.get("name") or "")
        if not ok:
            return

        amount, ok = QInputDialog.getText(self, "Edit Ingredient", "Amount:", text=str(ing.get("amount") or ""))
        if not ok:
            return

        unit, ok = QInputDialog.getText(self, "Edit Ingredient", "Unit:", text=ing.get("unit") or "")
        if not ok:
            return

        section, ok = QInputDialog.getText(self, "Edit Ingredient", "Section:", text=ing.get("subsection") or "")
        if not ok:
            return

        notes, ok = QInputDialog.getMultiLineText(self, "Edit Ingredient", "Notes:", text=ing.get("notes") or "")
        if not ok:
            return

        if isinstance(amount, dict):
            amount = f"{amount.get('min')}–{amount.get('max')}"
        elif amount is None:
            amount = ""

        ing.update({
            "amount": amount,
            "unit": unit or None,
            "name": name,
            "subsection": section or None,
            "notes": notes or None,
        })

        self.refresh_table()

    def remove_ingredient(self):
        """
        Remove an ingredient from the list
        """
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Remove", "Please select an ingredient first.")
            return

        ing = self.ingredients.pop(row)
        # QMessageBox.information(self, "Removed", f"Removed: {ing.get('name')}")
        self.refresh_table()

    def bring_to_front(self):
        """
        Bring the window to the front
        """
        self.raise_()
        self.activateWindow()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.show()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()

    def create_type_widget(self, ing):
        """
        Create Foundation / Branded radio buttons for a table row
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rb_foundation = QRadioButton("Foundation")
        rb_branded = QRadioButton("Branded")

        group = QButtonGroup(container)
        group.setExclusive(True)
        group.addButton(rb_foundation)
        group.addButton(rb_branded)

        # ---- ENSURE VALUE EXISTS IMMEDIATELY ----
        if ing.get("ingredient_type") not in ("foundation", "branded"):
            ing["ingredient_type"] = "foundation"

        if ing["ingredient_type"] == "branded":
            rb_branded.setChecked(True)
        else:
            rb_foundation.setChecked(True)

        def on_change():
            ing["ingredient_type"] = (
                "branded" if rb_branded.isChecked() else "foundation"
            )

        rb_foundation.toggled.connect(on_change)
        rb_branded.toggled.connect(on_change)

        layout.addWidget(rb_foundation)
        layout.addWidget(rb_branded)

        return container


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ingredients = [
        {"amount": 2, "unit": "tbsp", "name": "olive oil", "notes": "Use extra virgin", "subsection": None},
        {"amount": 1, "unit": "cup", "name": "coconut milk", "notes": None, "subsection": "Sauce"}
    ]
    window = IngredientEditor(ingredients)
    window.exec()
    print("FINAL INGREDIENTS:")
    for i in window.ingredients:
        print(i)