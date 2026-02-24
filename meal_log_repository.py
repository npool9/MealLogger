from database_utility import DatabaseUtility
from meal_log import MealLog
import datetime


class MealLogRepository:

    def __init__(self, db_conn: DatabaseUtility):
        """
        Initialize database connection
        """
        self.db_conn = db_conn

    def insert(self, meal_log: MealLog) -> MealLog:
        """
        Insert a meal log entry into the database
        """
        created_at = datetime.datetime.now()
        insert_statement = """
            INSERT INTO meal_log (
                meal_id, date_eaten, servings_consumed,
                calories, protein, carbs, fat,
                fiber, sugar, saturated_fat, trans_fat,
                cholesterol, sodium, potassium, calcium,
                iron, vitamin_a, vitamin_c, vitamin_d,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            meal_log.meal_id,
            meal_log.date_eaten,
            meal_log.servings_consumed,
            meal_log.calories,
            meal_log.protein,
            meal_log.carbs,
            meal_log.fat,
            meal_log.fiber,
            meal_log.sugar,
            meal_log.saturated_fat,
            meal_log.trans_fat,
            meal_log.cholesterol,
            meal_log.sodium,
            meal_log.potassium,
            meal_log.calcium,
            meal_log.iron,
            meal_log.vitamin_a,
            meal_log.vitamin_c,
            meal_log.vitamin_d,
            created_at
        )
        row_id = self.db_conn.execute_statement(insert_statement, params)
        meal_log.id = row_id
        meal_log.created_at = created_at
        return meal_log

    def get_by_date(self, date_eaten) -> list:
        """
        Get all meal log entries for a specific date
        :param date_eaten: the date to query
        :return: list of MealLog objects
        """
        query = """
            SELECT id, meal_id, date_eaten, servings_consumed,
                   calories, protein, carbs, fat,
                   fiber, sugar, saturated_fat, trans_fat,
                   cholesterol, sodium, potassium, calcium,
                   iron, vitamin_a, vitamin_c, vitamin_d,
                   created_at
            FROM meal_log
            WHERE date_eaten = %s
            ORDER BY created_at
        """
        rows = self.db_conn.execute_statement(query, (date_eaten,))
        return [MealLog(*row) for row in rows]

    def get_daily_totals(self, date_eaten) -> dict:
        """
        Get total macros for a specific date
        :param date_eaten: the date to query
        :return: dict with macro totals
        """
        query = """
            SELECT
                SUM(calories) as total_calories,
                SUM(protein) as total_protein,
                SUM(carbs) as total_carbs,
                SUM(fat) as total_fat,
                SUM(fiber) as total_fiber,
                SUM(sugar) as total_sugar,
                SUM(saturated_fat) as total_saturated_fat,
                SUM(cholesterol) as total_cholesterol,
                SUM(sodium) as total_sodium
            FROM meal_log
            WHERE date_eaten = %s
        """
        rows = self.db_conn.execute_statement(query, (date_eaten,))
        if rows and rows[0]:
            row = rows[0]
            return {
                "calories": row[0] or 0,
                "protein": row[1] or 0,
                "carbs": row[2] or 0,
                "fat": row[3] or 0,
                "fiber": row[4] or 0,
                "sugar": row[5] or 0,
                "saturated_fat": row[6] or 0,
                "cholesterol": row[7] or 0,
                "sodium": row[8] or 0
            }
        return {}
