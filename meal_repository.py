from database_utility import DatabaseUtility
from meal import Meal
import datetime
import time


class MealRepository:

    def __init__(self, db_conn: DatabaseUtility):
        """
        Initialize database connection
        """
        self.db_conn = db_conn

    def insert(self, meal: Meal) -> Meal:
        """
        Insert a meal into the database
        """
        created_at = datetime.datetime.now()
        insert_statement = """
            INSERT INTO meals (name, description, servings, serving_size, serving_unit, recipe_url, created_at)
            VALUES (\'{}\', \'{}\', \'{}\', {}, \'{}\', \'{}\', \'{}\')
            RETURNING id
            """.format(meal.name, meal.description, meal.servings, meal.serving_size, meal.serving_unit,
                       meal.recipe_url, created_at)
        row_id = self.db_conn.execute_statement(insert_statement)
        meal.id = row_id
        meal.created_at = created_at
        return meal