from meal import Meal
from database_utility import DatabaseUtility


class Model:
    """
    The model of the Model View Controller (MVC) paradigm
    """

    def __init__(self):
        """
        Initialize
        """
        self._db_util = DatabaseUtility()
        creds = self._db_util.get_credentials()
        # Open a database connection
        self._connection, self._cursor = self._db_util.connect(creds)
        self._meal_list = []

    def check_for_meal(self, meal_name):
        """
        Check the database for existence of a meal with the given name
        :param meal_name; the name of the meal (str)
        :return: the meal object
        """
        query = "SELECT * FROM meal_data WHERE UPPER(meal_name) = \'" + meal_name.upper() + "\';"
        self._cursor.execute(query)
        row = self._cursor.fetchone()
        if not row:  # meal does not exist
            row = []
        meal = Meal(*row)
        return meal
