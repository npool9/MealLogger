from database_utility import DatabaseUtility
from ingredient import Ingredient


class IngredientRepository:

    def __init__(self, db_conn: DatabaseUtility):
        """
        Initialize database connection
        """
        self.db_conn = db_conn

    def insert(self, ingredient: Ingredient) -> Ingredient:
        """
        Insert an ingredient into the database
        """
        insert_statement = """
            INSERT INTO ingredients (name, calories_per_gram, protein_per_gram, carbs_per_gram, fat_per_gram, fiber_per_gram, sugar_per_gram, saturated_fat_per_gram, trans_fat_per_gram, cholesterol_per_gram, sodium_per_gram, potassium_per_gram, calcium_per_gram, iron_per_gram, vitamin_a_per_gram, vitamin_c_per_gram, vitamin_d_per_gram)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            ingredient.name,
            ingredient.calories_per_gram or 0,
            ingredient.protein_per_gram or 0,
            ingredient.carbs_per_gram or 0,
            ingredient.fat_per_gram or 0,
            ingredient.fiber_per_gram,
            ingredient.sugar_per_gram,
            ingredient.saturated_fat_per_gram,
            ingredient.trans_fat_per_gram,
            ingredient.cholesterol_per_gram,
            ingredient.sodium_per_gram,
            ingredient.potassium_per_gram,
            ingredient.calcium_per_gram,
            ingredient.iron_per_gram,
            ingredient.vitamin_a_per_gram,
            ingredient.vitamin_c_per_gram,
            ingredient.vitamin_d_per_gram
        )
        row_id = self.db_conn.execute_statement(insert_statement, params)
        ingredient.id = row_id
        return ingredient