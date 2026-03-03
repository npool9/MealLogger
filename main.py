from view import View
from model import Model


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


def run():
    """
    The runner function to kick off the application and control it
    """
    meal_logger = MealLogger()
    meal_name = meal_logger._view.ask_for_meal()
    website = meal_logger._view.ask_for_website(meal_logger._model.supported_websites)
    print(f"Searching {website} for meal info...")
    scraped_meal, ingredient_list = meal_logger._model.scrape_meal(meal_name, website)

    # Check if this recipe already exists in the database
    existing_meal, exists = meal_logger._model.check_for_meal(scraped_meal.recipe_url)
    if exists:
        print(f"Meal already in database: {existing_meal.name}")
        ingredient_list = meal_logger._model.get_ingredients_for_meal(existing_meal)
        print(f"Found {len(ingredient_list)} ingredients in database")
        print("Calculating macros and inserting into meal_log...")
        meal_logger._model.log_macros(existing_meal, ingredient_list, servings_consumed=1)
    else:
        print("New meal — saving to database...")
        # Send the parsed ingredients list to the view
        ingredient_list = meal_logger._view.finalize_ingredients(ingredient_list)
        # Insert meal into database
        print("Inserting meal object into database")
        meal_logger._model.insert_meal(scraped_meal)
        print("Fetching ingredients for meal...")
        ingredient_list = meal_logger._model.fetch_ingredients(ingredient_list)
        print("Inserting ingredients into database...")
        for ingredient in ingredient_list:
            meal_logger._model.insert_ingredient(ingredient)
        print("Inserting into meal-ingredient bridge...")
        for ingredient in ingredient_list:
            meal_logger._model.insert_meal_ingredient_bridge(scraped_meal, ingredient)
        print("Calculating macros and inserting into meal_log...")
        meal_logger._model.log_macros(scraped_meal, ingredient_list, servings_consumed=1)


if __name__ == "__main__":
    run()
