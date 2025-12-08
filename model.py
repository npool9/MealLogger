from meal import Meal
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
        print(f"Creating database {self.creds["meal_db"]}...")
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
        print("Suported Websites:", self.supported_websites)
        search = FitMenCook(meal)
        ingredient_list = search.get_ingredients(meal)
        # post process ingredient list
        # ingredient_list = self.post_process(ingredient_list)
        return ingredient_list

    def build_meal(self, meal, ingredients):
        """
        Build the full meal object from the list of ingredients provided and
        the meal object template. Query the Nutritionix API for nutrition
        information
        :param meal: the empty Meal object (except for meal_name)
        :param ingredients: list of ingredients (list of str) that needs parsed
            for ingredient name and measurements
        :return: complete Meal object
        """
        for full_ingredient in ingredients:
            # self._ingredient_parser.parse(full_ingredient)
            print(full_ingredient)
        meal.describe()

    def post_process(self, ingredient_list):
        """
        Post process the ingredient list
        :param ingredient_list: a list of str, ingredients
        :return: post-processed list of ingredients
        """
        new_ingredient_list = []
        for ingredient in ingredient_list:
            if "mixed with" in ingredient:
                ing1, ing2 = ingredient.split("mixed with")
                new_ingredient_list.append(ing1.strip())
                new_ingredient_list.append(ing2.strip())
            else:
                new_ingredient_list.append(ingredient.strip())
        return new_ingredient_list
