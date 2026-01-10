from configparser import ConfigParser
import psycopg2
import os


class DatabaseUtility:
    """
    A class for database connection functionality
    """

    def __init__(self):
        """
        Initialize database connection based on .ini file
        """
        self._config_section = "credentials"
        self._database_ini = os.path.join(os.path.dirname(__file__), "database", "database.ini")
        self.conn, self.cur = None, None

    def get_credentials(self):
        """
        Parse the database ini file (supplied in self._database_ini class
            variable) for database credentials
        :return: dictionary of credentials based on ini file
        """
        parser = ConfigParser()
        parser.read(self._database_ini)
        credentials = {}
        if parser.has_section(self._config_section):
            params = parser.items(self._config_section)
            for param in params:
                credentials[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(self._config_section, self._database_ini))
        return credentials

    def connect(self, credentials):
        """
        Connect to the database supplied in the credentials dictionary
        :param credentials: a dictionary of connection parameters to the db
        :return: the (open) database connection and cursor objects
        """
        try:
            print('Connecting to the PostgreSQL database...')
            password = input(f"Please enter your database password for {credentials['user']}:")
            self.conn = psycopg2.connect(
                host=credentials["host"],
                user=credentials["user"],
                password=password,
                dbname=credentials["app_db"],
                port=credentials["port"]  # Connect to a default database to create others
            )
            self.cur = self.conn.cursor()
            self.cur.execute('SELECT version()')
            db_version = self.cur.fetchone()
            print("Successfully connected to database")
        except (Exception, psycopg2.DatabaseError) as error:
            raise Exception(error)
        return self.conn, self.cur

    def disconnect(self):
        """
        Take an existing, open database connection and close it
        """
        self.cur.close()
        self.conn.close()
        print("Connection to database has been closed.")

    def execute_statement(self, statement: str):
        """
        Execute an update, insert, or delete statement
        :param statement: the statement to execute
        """
        self.cur.execute(statement)
        row_id = self.cur.fetchone()[0]
        self.conn.commit()
        return row_id


    def get_row_id(self, table_name: str, column_name: str, value: str, id_col="id"):
        """
        Get the row id that follows the condition specified by column name and value
        :param table_name: the table to query
        :param column_name: the column name to use in the where clause
        :param value: the value of the column name for the where clause
        :param id_col: the name of the id column
        """
        query = f"select * from {table_name} where {column_name} = \'{value}\';"
        print(query)
        self.cur.execute(query)
        self.conn.commit()
        res = self.cur.fetchone()
        return res[id_col]