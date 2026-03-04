from ingredient_editor import IngredientEditor
from meal_log_viewer import MealLogViewer
from meals_browser import MealsBrowser
from usda_food_chooser import USDAFoodChooser
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
        print("  1. Add a recipe (search)")
        print("  2. Add a recipe (from URL)")
        print("  3. Create custom recipe")
        print("  4. Log a meal")
        print("  5. View meal log")
        print("  6. Browse saved meals")
        print("  7. Exit")
        while True:
            choice = input("Choose an option (number): ").strip()
            actions = {"1": "add_recipe", "2": "add_recipe_url", "3": "create_custom",
                       "4": "log_meal", "5": "view_log", "6": "browse_meals", "7": "exit"}
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

    def ask_for_meal_source(self):
        """
        Ask the user how they want to find the meal to log.
        :return: 'existing', 'search', or 'url'
        """
        print("\nHow would you like to find the meal?")
        print("  1. Choose from saved meals")
        print("  2. Search for a new recipe")
        print("  3. Add from URL")
        while True:
            choice = input("Choose an option (number): ").strip()
            actions = {"1": "existing", "2": "search", "3": "url"}
            if choice in actions:
                return actions[choice]
            print("Invalid choice. Please try again.")

    def choose_existing_meal(self, meals):
        """
        Display saved meals and let the user pick one.
        :param meals: list of tuples (id, name, servings, recipe_url, ingredient_count)
        :return: selected meal tuple or None
        """
        if not meals:
            print("No saved meals found.")
            return None
        print("\nSaved meals:")
        for i, meal in enumerate(meals, 1):
            print(f"  {i}. {meal[1]} ({meal[4]} ingredients, {meal[2]} servings)")
        while True:
            choice = input("Choose a meal (number, or 'q' to cancel): ").strip()
            if choice.lower() == 'q':
                return None
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(meals):
                    return meals[idx]
            except ValueError:
                pass
            print("Invalid choice. Please try again.")

    def ask_for_servings(self):
        """
        Ask the user how many servings they consumed.
        :return: number of servings (float)
        """
        while True:
            s = input("How many servings did you consume? [1]: ").strip()
            if not s:
                return 1.0
            try:
                val = float(s)
                if val > 0:
                    return val
                print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid number.")

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

    def show_food_chooser(self, ingredient_name, foods, pagination, search_callback):
        """
        Launch USDAFoodChooser dialog. Returns selected food dict or None.
        :param ingredient_name: ingredient name for window title context
        :param foods: list of food dicts from first page
        :param pagination: dict with totalHits, currentPage, totalPages
        :param search_callback: callable(page) -> paginated result dict
        :return: selected food dict or None if cancelled
        """
        app = self._get_app()
        window = USDAFoodChooser(ingredient_name, foods, pagination, search_callback)
        window.bring_to_front()
        result = window.exec()
        if result == USDAFoodChooser.DialogCode.Accepted and window.selected_food:
            return window.selected_food
        return None

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