from meal import Meal
from meal_log import MealLog
from ingredient import Ingredient
from meal_ingredient_repository import MealIngredientRepository
from meal_log_repository import MealLogRepository
from usda_service import USDAService
from meal_repository import MealRepository
from ingredient_repository import IngredientRepository
from database_utility import DatabaseUtility
from fitmencook_search import FitMenCook
from allrecipes_search import AllRecipes
from flyway import Flyway
from datetime import date
import json
import os


class Model:
    """
    The model of the Model View Controller (MVC) paradigm
    """

    def __init__(self):
        """
        Initialize
        """
        self.supported_websites = ["fitmencook", "allrecipes"]
        # Open a database connection
        self._db_util = DatabaseUtility()
        self.creds = self._db_util.get_credentials()
        self._meal_table_order = self.creds["table_order"].split(',')
        self.run_flyway()
        self._connection, self._cursor = self._db_util.connect(self.creds)
        self._meal_list = []
        self.NUTRIENT_MAP = json.load(open(os.path.join(os.path.dirname(__file__), "nutrient_map.json"), 'r'))

    def run_flyway(self):
        """
        Run flyway step for database
        """
        flyway = Flyway(credentials=self.creds)
        print(f"Creating database {self.creds['app_db']}...")
        flyway.create_database(self.creds["app_db"])
        for table in self._meal_table_order:
            print(f"Creating table {table}...")
            flyway.create_table(table)

    def check_for_meal(self, recipe_url):
        """
        Check the database for existence of a meal with the given recipe URL
        :param recipe_url: the recipe URL to check (str)
        :return: the meal object, exist flag
        """
        query = "SELECT * FROM meals WHERE recipe_url = %s"
        self._cursor.execute(query, (recipe_url,))
        row = self._cursor.fetchone()
        exists = True
        if not row:  # meal does not exist
            row = []
            exists = False
        meal = Meal(*row)
        return meal, exists

    def get_ingredients_for_meal(self, meal):
        """
        Fetch all ingredients for an existing meal from the database,
        including their per-gram nutrient values and amounts from the bridge table.
        :param meal: Meal object with id set
        :return: list of Ingredient objects with amount_grams populated
        """
        query = """
            SELECT i.*, mib.quantity, mib.unit, mib.quantity_grams
            FROM ingredients i
            JOIN meal_ingredient_bridge mib ON i.id = mib.ingredient_id
            WHERE mib.meal_id = %s
        """
        self._cursor.execute(query, (meal.id,))
        rows = self._cursor.fetchall()
        ingredients = []
        for row in rows:
            # ingredients table columns: id, name, calories_per_gram, ..., vitamin_d_per_gram (17 cols)
            # then bridge columns: quantity, unit, quantity_grams
            ing = Ingredient(*row[:17])
            ing.amount = row[17]
            ing.unit = row[18]
            ing.amount_grams = row[19]
            ingredients.append(ing)
        return ingredients

    def scrape_meal(self, meal_name: str, website: str) -> tuple[Meal, list]:
        """
        Scrape a recipe website for meal details and ingredients.

        :param meal_name: the name of the meal to search for
        :param website: the website to search (e.g. 'fitmencook', 'allrecipes')
        :return: tuple of (populated Meal object, list of parsed ingredients)
        """
        meal = Meal(name=meal_name)
        scrapers = {
            "fitmencook": FitMenCook,
            "allrecipes": AllRecipes,
        }
        scraper_class = scrapers.get(website)
        if not scraper_class:
            raise ValueError(f"Unsupported website: {website}")
        search = scraper_class(meal)
        print("Getting ingredients list...")
        ingredient_list = search.get_ingredients(meal)
        print("Getting recipe description...")
        meal.description = search.get_recipe_steps(meal)
        print("Getting recipe servings...")
        meal.servings = search.get_recipe_servings(meal)
        meal.serving_size, meal.serving_unit = search.get_serving_size_and_unit(meal)
        return meal, ingredient_list

    def insert_meal(self, meal: Meal):
        """
        Insert the meal into the database
        :param meal: the completed meal (without id and created_at)
        """
        MealRepository(self._db_util).insert(meal)

    def insert_ingredient(self, ingredient):
        """
        Insert the ingredient into the database
        :param ingredient: the ingredient (without id)
        """
        IngredientRepository(self._db_util).insert(ingredient)

    def insert_meal_ingredient_bridge(self, meal, ingredient):
        """
        Insert the meal ingredient bridge into the database
        :param meal: the meal object
        :param ingredient: the ingredient object
        """
        MealIngredientRepository(self._db_util).insert(meal, ingredient)

    def process_ingredients(self, ingredient_list: list):
        """
        Loop through the ingredients in the list, create ingredient objects, insert them into the database
        :param ingredient_list: the list of ingredients
        """
        for ingredient in ingredient_list:  # create ingredient object
            # lookup nutrition information about ingredient
            pass

    def fetch_ingredients(self, ingredients: list[dict]) -> list[Ingredient]:
        """
        Query the USDA API for nutritional data and build Ingredient objects.
        For each parsed ingredient, search the USDA FoodData Central database,
        retrieve nutrient values, convert them to per-gram amounts, and
        populate an Ingredient object.
        :param ingredients: Parsed ingredient dicts, each containing:
            - original
            - amount
            - unit
            - name: ingredient name to search for
            - notes
            - ingredient_type: 'foundation' or 'branded'
        :return: List of Ingredient objects with nutrient fields populated
        """
        usda = USDAService()
        ingredients_list = []
        for ingredient in ingredients:
            food_info = usda.search_food(ingredient["name"], food_type=ingredient["ingredient_type"], target_unit=ingredient.get("unit"))
            print(food_info["portions"])
            ing = Ingredient(name=food_info["name"].title())
            # Parse nutrient fields and convert to per-gram values
            nutrient_fields = usda.parse_nutrients_to_ingredient_fields(food_info["nutrients"])
            for nutrient_name in nutrient_fields:
                if nutrient_name.endswith("_unit"):
                    continue
                val = nutrient_fields[nutrient_name] / 100  # convert from "per 100g" to "per 1g"
                setattr(ing, nutrient_name, val)
            # Handle range amounts (take max)
            amount = ingredient["amount"]
            if isinstance(amount, dict):
                amount = amount["max"]
            # Store original amount/unit for recipe readability
            unit = ingredient["unit"]
            # If unit is None, infer from portions data
            if unit is None and amount and food_info["portions"]:
                available_units = list(food_info["portions"].keys())
                if available_units:
                    unit = available_units[0]
            ing.amount = amount
            ing.unit = unit
            ing.notes = ingredient["notes"]
            # Convert amount to grams for nutrient calculations
            try:
                if unit:
                    ing.amount_grams = usda.convert_amount_to_grams(
                        amount, unit, food_info["portions"], ingredient_name=food_info["name"]
                    )
            except ValueError as e:
                print(f"Warning: {e}. Gram conversion not available.")
                ing.amount_grams = None
            ingredients_list.append(ing)
            print("Amount Grams:", ing.amount_grams)
            print("Amount:", ing.amount)
            print("Unit:", ing.unit)
        return ingredients_list

    def log_macros(self, meal, ingredients, servings_consumed=1, date_eaten=None):
        """
        Log a meal's macros to the meal_log table.
        Calculates total macros from ingredients and stores them.

        :param meal: Meal object (must have id set)
        :param ingredients: list of Ingredient objects with amount_grams set
        :param servings_consumed: number of servings eaten (default 1)
        :param date_eaten: date the meal was eaten (default today)
        :return: MealLog object with id set
        """
        if date_eaten is None:
            date_eaten = date.today()
        # Calculate totals from ingredients
        nutrients = [
            "calories", "protein", "carbs", "fat", "fiber", "sugar",
            "saturated_fat", "trans_fat", "cholesterol", "sodium",
            "potassium", "calcium", "iron", "vitamin_a", "vitamin_c", "vitamin_d"
        ]
        totals = {n: 0 for n in nutrients}
        for ing in ingredients:
            if ing.amount_grams is None:
                continue
            grams = ing.amount_grams
            for nutrient in nutrients:
                per_gram = getattr(ing, f"{nutrient}_per_gram", None)
                if per_gram:
                    totals[nutrient] += per_gram * grams
        # Scale to per-serving, then multiply by servings consumed
        recipe_servings = float(meal.servings) if meal.servings else 1
        for key in totals:
            totals[key] = round((totals[key] / recipe_servings) * servings_consumed, 2)
        # Create and insert meal log
        meal_log = MealLog(
            meal_id=meal.id,
            date_eaten=date_eaten,
            servings_consumed=servings_consumed,
            **totals
        )
        meal_log_repo = MealLogRepository(self._db_util)
        meal_log_repo.insert(meal_log)
        return meal_log
