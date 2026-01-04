import psycopg2
import os
from database_utility import DatabaseUtility


class Flyway:
    """
    Scripts for executing flyway on a database
    """

    def  __init__(self, db_type="postgresql"):
        """
        Initialize
        """
        self.flyway_path = os.path.join(os.path.dirname(__file__), "database", "flyway", db_type)
        self.db_utility = DatabaseUtility()
        self.credentials = self.db_utility.get_credentials()
        self.credentials["password"] = input(f"Please enter your database password for {self.credentials['user']}:")
        try:
            # Connect to the default 'postgres' database to create a new one
            self.conn = psycopg2.connect(
                host=self.credentials["host"],
                user=self.credentials["user"],
                password=self.credentials["password"],
                dbname=self.credentials["init_db"],
                port=self.credentials["port"]  # Connect to a default database to create others
            )
            self.cur = self.conn.cursor()
        except psycopg2.Error as e:
            raise Exception(f"Error creating database: {e}")

    def create_database(self, db_name: str):
        """
        Create a database if it doesn't exist
        :param db_name: name of new database
        """
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{}'".format(db_name))
        try:
            exists = self.cur.fetchone()
        except psycopg2.ProgrammingError:
            try:
                self.cur.execute("CREATE DATABASE \"{}\"".format(db_name))
                self.conn.commit()
            except psycopg2.errors.DuplicateDatabase:
                print(f"{db_name} already exists.")
        self.conn = psycopg2.connect(
            host=self.credentials["host"],
            user=self.credentials["user"],
            password=self.credentials["password"],
            dbname=self.credentials["meal_db"],
            port=self.credentials["port"]  # Connect to a default database to create others
        )
        self.conn.commit()

    def create_table(self, table_name: str):
        """
        Create a postgres table from create table script saved in a file
        :param table_name: name of the table
        """
        flyway_script_name = f"create_table_{table_name}.sql"
        create_table_statement = open(os.path.join(self.flyway_path, flyway_script_name), 'r').read()
        try:
            self.cur.execute(create_table_statement)
            self.conn.commit()
        except psycopg2.errors.DuplicateTable:
            print(f"Relation \"{table_name}\" was already created")
            self.conn.commit()


if __name__ == "__main__":
    flyway = Flyway()
