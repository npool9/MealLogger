from database_utility import DatabaseUtility
from meal import Meal
from ingredient import Ingredient


class MealIngredientRepository:

    def __init__(self, db_conn: DatabaseUtility):
        """
        Initialize database connection
        """
        self.db_conn = db_conn

    def insert(self, meal: Meal, ingredient: Ingredient) -> None:
        """
        Insert a meal-ingredient relationship into the bridge table.

        :param meal: Meal object (must have id set)
        :param ingredient: Ingredient object (must have id, amount, unit, and amount_grams set)
        """
        insert_statement = """
            INSERT INTO meal_ingredient_bridge (meal_id, ingredient_id, quantity, unit, quantity_grams)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING meal_id, ingredient_id
        """
        params = (
            meal.id,
            ingredient.id,
            ingredient.amount,
            ingredient.unit,
            ingredient.amount_grams
        )
        self.db_conn.execute_statement(insert_statement, params)