from ingredient_editor import IngredientEditor
from meal_log_viewer import MealLogViewer
from meals_browser import MealsBrowser
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

    def _get_app(self):
        """
        Get existing QApplication instance or create a new one.
        Prevents crash when launching multiple dialogs in one session.
        Also activates the app on macOS so dialogs come to the front.
        """
        app = QApplication.instance() or QApplication(sys.argv)
        return app

    def ask_for_action(self):
        """
        Ask the user what they want to do.
        :return: the chosen action string
        """
        print("\nWhat would you like to do?")
        print("  1. Log a meal (search)")
        print("  2. Log a meal (from URL)")
        print("  3. Create custom recipe")
        print("  4. View meal log")
        print("  5. Browse saved meals")
        print("  6. Exit")
        while True:
            choice = input("Choose an option (number): ").strip()
            actions = {"1": "log", "2": "log_url", "3": "create_custom",
                       "4": "view_log", "5": "browse_meals", "6": "exit"}
            if choice in actions:
                return actions[choice]
            print("Invalid choice. Please try again.")

    def ask_for_recipe_details(self):
        """
        Ask the user for custom recipe name and servings.
        :return: tuple of (recipe_name, servings)
        """
        name = input("Recipe name: ").strip()
        while True:
            servings = input("Number of servings: ").strip()
            try:
                int(servings)
                return name, servings
            except ValueError:
                print("Please enter a valid number.")

    def ask_for_url(self):
        """
        Ask the user for a recipe URL
        :return: the URL (str)
        """
        return input("Paste the recipe URL: ").strip()

    def ask_for_meal(self):
        """
        Ask the user about their meal
        :return: the name of the meal (provided by the user)
        """
        return input("What meal did you eat?: ").strip()

    def ask_for_website(self, supported_websites):
        """
        Ask the user which website to search for the recipe
        :param supported_websites: list of supported website names
        :return: the chosen website name (str)
        """
        print("Supported websites:")
        for i, site in enumerate(supported_websites, 1):
            print(f"  {i}. {site}")
        while True:
            choice = input("Choose a website (number): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(supported_websites):
                    return supported_websites[idx]
            except ValueError:
                pass
            print("Invalid choice. Please try again.")

    def finalize_ingredients(self, ingredients_list: list):
        """
        Ask the user to finalize the ingredients list found by the parser and make any necessary edits
        :param ingredients_list: list of ingredients found by the web scraper
        :return: the edited list of ingredients
        """
        app = self._get_app()
        window = IngredientEditor(ingredients_list)
        window.bring_to_front()
        window.exec()
        return window.ingredients

    def show_meal_log_viewer(self, meal_logs):
        """
        Launch the Meal Log Viewer dialog.
        :param meal_logs: list of tuples from model.get_all_meal_logs()
        """
        app = self._get_app()
        window = MealLogViewer(meal_logs)
        window.bring_to_front()
        window.exec()

    def show_meals_browser(self, meals, get_ingredients_callback):
        """
        Launch the Meals Browser dialog.
        :param meals: list of tuples from model.get_all_meals()
        :param get_ingredients_callback: callable(meal_id) -> list of Ingredient
        """
        app = self._get_app()
        window = MealsBrowser(meals, get_ingredients_callback)
        window.bring_to_front()
        window.exec()