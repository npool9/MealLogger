from view import View
from model import Model
from meal import Meal


class MealLogger:
    """
    The controller of the meal logger
    """

    def __init__(self):
        """
        Initialize the Meal Logger controller
        """
        self._view = View()
        self._model = Model()

    def save_and_log(self, scraped_meal, ingredient_list):
        """
        Check if a scraped meal already exists in the database.
        If it does, log macros from existing data.
        If not, finalize ingredients, save everything, and log macros.
        """
        existing_meal, exists = self._model.check_for_meal(scraped_meal.recipe_url)
        if exists:
            print(f"Meal already in database: {existing_meal.name}")
            ingredient_list = self._model.get_ingredients_for_meal(existing_meal)
            print(f"Found {len(ingredient_list)} ingredients in database")
            print("Calculating macros and inserting into meal_log...")
            self._model.log_macros(existing_meal, ingredient_list, servings_consumed=1)
        else:
            print("New meal — saving to database...")
            ingredient_list = self._view.finalize_ingredients(ingredient_list)
            print("Inserting meal object into database")
            self._model.insert_meal(scraped_meal)
            print("Fetching ingredients for meal...")
            ingredient_list = self._model.fetch_ingredients(ingredient_list)
            print("Inserting ingredients into database...")
            for ingredient in ingredient_list:
                self._model.insert_ingredient(ingredient)
            print("Inserting into meal-ingredient bridge...")
            for ingredient in ingredient_list:
                self._model.insert_meal_ingredient_bridge(scraped_meal, ingredient)
            print("Calculating macros and inserting into meal_log...")
            self._model.log_macros(scraped_meal, ingredient_list, servings_consumed=1)


def run():
    """
    The runner function to kick off the application and control it
    """
    meal_logger = MealLogger()

    while True:
        action = meal_logger._view.ask_for_action()

        if action == "exit":
            break

        elif action == "log":
            meal_name = meal_logger._view.ask_for_meal()
            website = meal_logger._view.ask_for_website(meal_logger._model.supported_websites)
            print(f"Searching {website} for meal info...")
            scraped_meal, ingredient_list = meal_logger._model.scrape_meal(meal_name, website)
            meal_logger.save_and_log(scraped_meal, ingredient_list)

        elif action == "log_url":
            url = meal_logger._view.ask_for_url()
            print("Fetching recipe from URL...")
            scraped_meal, ingredient_list = meal_logger._model.scrape_meal_from_url(url)
            meal_logger.save_and_log(scraped_meal, ingredient_list)

        elif action == "view_log":
            meal_logs = meal_logger._model.get_all_meal_logs()
            meal_logger._view.show_meal_log_viewer(meal_logs)

        elif action == "browse_meals":
            meals = meal_logger._model.get_all_meals()

            def get_ingredients_cb(meal_id):
                m = Meal(id=meal_id)
                return meal_logger._model.get_ingredients_for_meal(m)

            meal_logger._view.show_meals_browser(meals, get_ingredients_cb)


if __name__ == "__main__":
    run()