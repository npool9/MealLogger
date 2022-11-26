import requests
import json
from configparser import ConfigParser


class Nutritionix:
    """
    Utilities for communicating with the Nutritionix API
    """

    def __init__(self):
        """
        Define base urls, endpoints, etc.
        """
        # Get API credentials
        self._config_section = "nutritionix"
        self._api_ini = "api_credentials.ini"
        self.creds = self.get_credentials()
        # JSON variables
        self.json_dir = "json/"
        self.headers_template_file = self.json_dir + "nutritionix_headers_template.json"
        self.body_template_file = self.json_dir + "natural_language_body_template.json"
        # self.headers = json.load(open(self.headers_template_file, 'r').read())
        with open(self.headers_template_file, 'r') as f:
            self.headers = json.load(f)
        self.headers["x-app-id"] = self.creds["x-app-id"]
        self.headers["x-app-key"] = self.creds["x-app-key"]
        # API endpoints
        self.base_url = "https://trackapi.nutritionix.com/"
        self.instant_search_endpoint = self.base_url + "v2/search/instant"
        self.natural_language_endpoint = self.base_url + "v2/natural/nutrients"

    def get_credentials(self):
        """
        Parse the api ini file (supplied in self._api_credentials class
            variable) for api credentials
        :return: dictionary of credentials based on ini file
        """
        parser = ConfigParser()
        parser.read(self._api_ini)
        credentials = {}
        if parser.has_section(self._config_section):
            params = parser.items(self._config_section)
            for param in params:
                credentials[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(self._config_section, self._database_ini))
        return credentials

    def query_natural_language(self, query):
        """
        Request response from the natural language API endpoint
        :param query: the str to query the API with for nutrition data
        :return: the JSON response (dict)
        """
        with open(self.body_template_file, 'r') as f:
            body = json.load(f)
        body["query"] = query
        # Make POST request
        return requests.post(url=self.natural_language_endpoint, headers=self.headers, json=body)

    def query_instant_search(self, query):
        """
        Request response from the instant search API endpoint
        :param query: the str to query the API for nutrition  data
        :return: the JSON response (dict)
        """
        url = self.instant_search_endpoint + "?query=" + query
        # Make GET request
        return requests.get(url=url, headers=self.headers)


if __name__ == "__main__":
    nutritionix = Nutritionix()
    response = nutritionix.query_natural_language("egg").text
