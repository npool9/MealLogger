from meal import Meal
from database_utility import DatabaseUtility
from fitmencook_search import FitMenCook


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
        creds = self._db_util.get_credentials()
        self._connection, self._cursor = self._db_util.connect(creds)
        self._meal_list = []

    def check_for_meal(self, meal_name):
        """
        Check the database for existence of a meal with the given name
        :param meal_name; the name of the meal (str)
        :return: the meal object, exist flag
        """
        query = "SELECT * FROM meal_data WHERE UPPER(meal_name) = \'" + meal_name.upper() + "\';"
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
        print(self.supported_websites)
        search = FitMenCook(meal)
        return search.get_ingredients()
