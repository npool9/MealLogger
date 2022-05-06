from meal import Meal
from configparser import ConfigParser
import psycopg2


class Model:
    """
    The model of the Model View Controller (MVC) paradigm
    """
    def __init__(self):
        """
        Initialize
        """
        self._config_section = "credentials"
        self._database_ini = "database.ini"
        creds = self.get_credentials()
        self._connection, self._cursor = self.connect(creds)
        self._meal_list = []

    def get_credentials(self):
        """
        Parse the database ini file (supplied in self._datbase_ini class
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
        conn = None
        try:
            print('Connecting to the PostgreSQL database...')
            conn = psycopg2.connect(**credentials)
            cur = conn.cursor()
            print('PostgreSQL database version:')
            cur.execute('SELECT version()')
            db_version = cur.fetchone()
            print(db_version)
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        return conn, cur

    def check_for_meal(self, meal_name):
        """
        Check the database for existence of a meal with the given name
        :param meal_name; the name of the meal (str)
        """
        query = ""
        print("Checking for meal...")
