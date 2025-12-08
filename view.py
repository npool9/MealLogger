from ingredient_editor import IngredientEditor
from PyQt6.QtWidgets import QApplication
import sys


class View:
    """
    The "view" of the Model View Controller (MVC) paradigm
    """

    def __init__(self):
        """
        Initialize the view
        """
        pass

    def ask_for_meal(self):
        """
        Ask the user about their meal
        :return: the name of the meal (provided by the user)
        """
        return input("What meal did you eat?: ").strip()

    def finalize_ingredients(self, ingredients_list: list):
        """
        Ask the user to finalize the ingredients list found by the parser and make any necessary edits
        :param ingredients_list: list of ingredients found by the web scraper
        :return: the edited list of ingredients
        """
        app = QApplication(sys.argv)
        window = IngredientEditor(ingredients_list)
        window.bring_to_front()
        window.exec()
        return window.ingredients