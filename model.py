from meal import Meal
from ingredient import Ingredient
from usda_service import USDAService
from meal_repository import MealRepository
from ingredient_repository import IngredientRepository
from database_utility import DatabaseUtility
from fitmencook_search import FitMenCook
from flyway import Flyway
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
        self.supported_websites = ["fitmencook"]
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
        flyway = Flyway()
        print(f"Creating database {self.creds['app_db']}...")
        flyway.create_database(self.creds["app_db"])
        for table in self._meal_table_order:
            print(f"Creating table {table}...")
            flyway.create_table(table)

    def check_for_meal(self, meal_name):
        """
        Check the database for existence of a meal with the given name
        :param meal_name; the name of the meal (str)
        :return: the meal object, exist flag
        """
        query = "SELECT * FROM meals WHERE UPPER(name) = \'" + meal_name.upper() + "\';"
        self._cursor.execute(query)
        row = self._cursor.fetchone()
        exists = True
        if not row:  # meal does not exist
            row = []
            exists = False
        meal = Meal(*row)
        return meal, exists

    def scrape_meal(self, meal_name: str) -> tuple[Meal, list]:
        """
        Scrape a recipe website for meal details and ingredients.

        :param meal_name: the name of the meal to search for
        :return: tuple of (populated Meal object, list of parsed ingredients)
        """
        # TODO: Ask user for the website to search
        print("Supported Websites:", self.supported_websites)
        meal = Meal(name=meal_name)
        search = FitMenCook(meal)
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
            - name: ingredient name to search for
            - ingredient_type: 'foundation' or 'branded'
        :return: List of Ingredient objects with nutrient fields populated
        """
        usda = USDAService()
        ingredients_list = []
        for ingredient in ingredients:
            food_info = usda.search_food(ingredient["name"], food_type=ingredient["ingredient_type"])
            name = list(food_info.keys())[0]
            ing = Ingredient(name=name.title())
            # print(ingredient)
            # Get default unit of ingredient
            nutrient_fields = usda.parse_nutrients_to_ingredient_fields(food_info[name])
            # print(nutrient_fields)
            for nutrient_name in nutrient_fields:
                if nutrient_name.endswith("_unit"):
                    continue
                val = nutrient_fields[nutrient_name] / 100  # convert from "per 100g" to "per 1g" of food/ingredient
                setattr(ing, nutrient_name, val)
            # ing.describe()
            ingredients_list.append(ing)
        return ingredients_list
