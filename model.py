from meal import Meal
from ingredient import Ingredient
from usda_service import USDAService
from meal_repository import MealRepository
from database_utility import DatabaseUtility
from fitmencook_search import FitMenCook
from ingredient_parser import IngredientParser
from flyway import Flyway


class Model:
    """
    The model of the Model View Controller (MVC) paradigm
    """

    def __init__(self):
        """
        Initialize
        """
        self.supported_websites = ["fitmencook"]
        # Flyway parameters
        self._init_db_name = "public"
        self._meal_table_order = ["meals", "ingredients", "meal_ingredient_bridge"]
        # Open a database connection
        self._db_util = DatabaseUtility()
        self.creds = self._db_util.get_credentials()
        self.run_flyway()
        self._connection, self._cursor = self._db_util.connect(self.creds)
        self._meal_list = []
        self._ingredient_parser = IngredientParser()

    def run_flyway(self):
        """
        Run flyway step for database
        """
        flyway = Flyway()
        print(f"Creating database {self.creds['meal_db']}...")
        flyway.create_database(self.creds["meal_db"])
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

    def find_meal(self, meal):
        """
        Find the provided meal on a recipe website
        :param meal: the meal object that's not already in database (str)
        :return: list of ingredients
        """
        # TODO: Ask user for the website to search
        print("Supported Websites:", self.supported_websites)
        search = FitMenCook(meal)
        print("Getting ingredients list...")
        ingredient_list = search.get_ingredients(meal)
        print("Getting recipe description...")
        meal.description = search.get_recipe_steps(meal)
        print("Getting recipe servings...")
        meal.servings = search.get_recipe_servings(meal)
        meal.serving_size, meal.serving_unit = search.get_serving_size_and_unit(meal)
        return ingredient_list

    def insert_meal(self, meal: Meal):
        """
        Insert the meal into the database
        :param meal: the completed meal (without id and created_at)
        """
        MealRepository(self._db_util).insert(meal)

    def process_ingredients(self, ingredient_list: list):
        """
        Loop through the ingredients in the list, create ingredient objects, insert them into the database
        :param ingredient_list: the list of ingredients
        """
        for ingredient in ingredient_list:  # create ingredient object
            # lookup nutrition information about ingredient
            pass

    def build_meal(self, meal, ingredients):
        """
        Build the full meal object from the list of ingredients provided and
        the meal object template. Query the Nutritionix API for nutrition
        information
        :param meal: the complete meal object
        :param ingredients: list of parsed ingredients (list of dicts)
        :return: the completed meal and ingredient objects
        """
        usda = USDAService()
        for ingredient in ingredients:
            food_info = usda.search_food(ingredient["name"], food_type=ingredient["ingredient_type"])
            print(ingredient, "---", food_info)
        meal.describe()
