from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel
)
from PyQt6.QtCore import Qt


class MealsBrowser(QDialog):
    """
    Dialog for browsing saved meals and viewing their ingredients
    """

    def __init__(self, meals, get_ingredients_callback):
        """
        Initialize the meals browser
        :param meals: list of tuples (meal_id, name, servings, recipe_url, ingredient_count)
        :param get_ingredients_callback: callable(meal_id) -> list of Ingredient objects
        """
        super().__init__()
        self.setWindowTitle("Meals Browser")
        self.resize(1000, 600)

        self.meals = meals
        self.get_ingredients = get_ingredients_callback

        # -------- Layout --------
        layout = QVBoxLayout()
        self.setLayout(layout)

        # -------- Meals Table --------
        layout.addWidget(QLabel("Saved Meals:"))

        self.meals_table = QTableWidget()
        self.meals_table.setColumnCount(4)
        self.meals_table.setHorizontalHeaderLabels([
            "Meal Name", "Servings", "Recipe URL", "Ingredients"
        ])
        self.meals_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.meals_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.meals_table.selectionModel().selectionChanged.connect(self.on_meal_selected)
        layout.addWidget(self.meals_table)

        self.refresh_meals_table()

        # -------- Ingredients Label --------
        self.ingredients_label = QLabel("Ingredients for selected meal:")
        layout.addWidget(self.ingredients_label)

        # -------- Ingredients Table --------
        self.ingredients_table = QTableWidget()
        self.ingredients_table.setColumnCount(3)
        self.ingredients_table.setHorizontalHeaderLabels(["Ingredient", "Amount", "Unit"])
        self.ingredients_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ingredients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.ingredients_table)

        # -------- Buttons --------
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        btn_layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

    def refresh_meals_table(self):
        """Populate the meals table"""
        self.meals_table.setRowCount(len(self.meals))

        for row, meal in enumerate(self.meals):
            # meal: (id, name, servings, recipe_url, ingredient_count)
            items = [
                QTableWidgetItem(str(meal[1] or "")),
                QTableWidgetItem(str(meal[2] or "")),
                QTableWidgetItem(str(meal[3] or "")),
                QTableWidgetItem(str(meal[4] or 0)),
            ]
            for col, item in enumerate(items):
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.meals_table.setItem(row, col, item)

        self.meals_table.resizeColumnsToContents()

    def on_meal_selected(self):
        """Handle meal row selection — load and display its ingredients"""
        row = self.meals_table.currentRow()
        if row < 0 or row >= len(self.meals):
            return

        meal_id = self.meals[row][0]
        meal_name = self.meals[row][1]
        self.ingredients_label.setText(f"Ingredients for: {meal_name}")

        ingredients = self.get_ingredients(meal_id)
        self.refresh_ingredients_table(ingredients)

    def refresh_ingredients_table(self, ingredients):
        """Populate the ingredients table for the selected meal"""
        self.ingredients_table.setRowCount(len(ingredients))

        for row, ing in enumerate(ingredients):
            amount = ing.amount
            if isinstance(amount, dict):
                amount = f"{amount.get('min')}–{amount.get('max')}"
            elif amount is not None:
                # Format cleanly: show as int if whole number, else up to 2 decimals
                val = float(amount)
                amount = str(int(val)) if val == int(val) else f"{val:.2f}".rstrip('0').rstrip('.')
            else:
                amount = ""

            items = [
                QTableWidgetItem(str(ing.name or "")),
                QTableWidgetItem(amount),
                QTableWidgetItem(str(ing.unit or "")),
            ]
            for col, item in enumerate(items):
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.ingredients_table.setItem(row, col, item)

        self.ingredients_table.resizeColumnsToContents()

    def bring_to_front(self):
        """Bring the window to the front"""
        self.raise_()
        self.activateWindow()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.show()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()