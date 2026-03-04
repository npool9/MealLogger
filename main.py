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

    def save_recipe(self, scraped_meal, ingredient_list):
        """
        Save a scraped recipe to the database if it doesn't already exist.
        Does NOT log consumption.
        :return: tuple of (meal, ingredients) or None if already exists
        """
        existing_meal, exists = self._model.check_for_meal(scraped_meal.recipe_url)
        if exists:
            print(f"Meal already in database: {existing_meal.name}")
            return None
        print("New meal — saving to database...")
        ingredient_list = self._view.finalize_ingredients(ingredient_list)
        meal, ingredients = self._model.save_meal(scraped_meal, ingredient_list, view=self._view)
        print(f"Saved '{meal.name}' with {len(ingredients)} ingredients.")
        return meal, ingredients

    def save_and_log(self, scraped_meal, ingredient_list, servings):
        """
        Save a scraped recipe if new, then log consumption.
        :param scraped_meal: Meal object from scraper
        :param ingredient_list: parsed ingredient dicts
        :param servings: number of servings consumed
        """
        existing_meal, exists = self._model.check_for_meal(scraped_meal.recipe_url)
        if exists:
            print(f"Meal already in database: {existing_meal.name}")
            ingredients = self._model.get_ingredients_for_meal(existing_meal)
            print(f"Found {len(ingredients)} ingredients in database")
            self._model.log_macros(existing_meal, ingredients, servings_consumed=servings)
        else:
            print("New meal — saving to database...")
            ingredient_list = self._view.finalize_ingredients(ingredient_list)
            meal, ingredients = self._model.save_meal(scraped_meal, ingredient_list, view=self._view)
            self._model.log_macros(meal, ingredients, servings_consumed=servings)
        print("Meal logged.")


def run():
    """
    The runner function to kick off the application and control it
    """
    meal_logger = MealLogger()

    while True:
        action = meal_logger._view.ask_for_action()

        if action == "exit":
            break

        elif action == "add_recipe":
            meal_name = meal_logger._view.ask_for_meal()
            website = meal_logger._view.ask_for_website(meal_logger._model.supported_websites)
            print(f"Searching {website} for meal info...")
            scraped_meal, ingredient_list = meal_logger._model.scrape_meal(meal_name, website)
            meal_logger.save_recipe(scraped_meal, ingredient_list)

        elif action == "add_recipe_url":
            url = meal_logger._view.ask_for_url()
            print("Fetching recipe from URL...")
            scraped_meal, ingredient_list = meal_logger._model.scrape_meal_from_url(url)
            meal_logger.save_recipe(scraped_meal, ingredient_list)

        elif action == "create_custom":
            recipe_name, servings = meal_logger._view.ask_for_recipe_details()
            ingredient_list = meal_logger._view.finalize_ingredients([])
            if not ingredient_list:
                print("No ingredients added. Skipping.")
                continue
            meal = Meal(name=recipe_name)
            meal.servings = servings
            meal.website_name = "custom"
            meal_logger._model.save_meal(meal, ingredient_list, view=meal_logger._view)
            print(f"Saved custom recipe '{recipe_name}'.")

        elif action == "log_meal":
            source = meal_logger._view.ask_for_meal_source()

            if source == "existing":
                meals = meal_logger._model.get_all_meals()
                selected = meal_logger._view.choose_existing_meal(meals)
                if selected is None:
                    continue
                meal_id, name, servings_str, recipe_url, ingredient_count = selected
                existing_meal = Meal(id=meal_id, name=name, servings=servings_str)
                ingredients = meal_logger._model.get_ingredients_for_meal(existing_meal)
                servings = meal_logger._view.ask_for_servings()
                meal_logger._model.log_macros(existing_meal, ingredients, servings_consumed=servings)
                print("Meal logged.")

            elif source == "search":
                meal_name = meal_logger._view.ask_for_meal()
                website = meal_logger._view.ask_for_website(meal_logger._model.supported_websites)
                print(f"Searching {website} for meal info...")
                scraped_meal, ingredient_list = meal_logger._model.scrape_meal(meal_name, website)
                servings = meal_logger._view.ask_for_servings()
                meal_logger.save_and_log(scraped_meal, ingredient_list, servings)

            elif source == "url":
                url = meal_logger._view.ask_for_url()
                print("Fetching recipe from URL...")
                scraped_meal, ingredient_list = meal_logger._model.scrape_meal_from_url(url)
                servings = meal_logger._view.ask_for_servings()
                meal_logger.save_and_log(scraped_meal, ingredient_list, servings)

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
