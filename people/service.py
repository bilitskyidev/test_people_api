from abc import ABC, abstractmethod, abstractstaticmethod
from typing import List
import json
import jsonschema
from jsonschema import validate
import requests
from rest_framework import serializers
from people.models import Person, Location


class GetDataFromApi(ABC):
    """Interface for creating service, that work with API"""

    def __init__(self, params: dict = None):
        self.url = None
        self.params = params
        self.api_name = "GetDataFromApi"

    @staticmethod
    def get_response(url, params) -> dict or Exception:
        """Creating request to api and check response status"""
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise serializers.ValidationError(
                response.json()['error']['message']
            )

    @staticmethod
    def get_api_schema(path):
        """Open schema file and convert to json"""
        try:
            with open(path, "r") as s:
                data = s.read()
        except IOError:
            raise serializers.ValidationError(
                "Api schema not found, wrong path:{}".format(path)
            )
        return json.loads(data)

    def _validate_response_data(self, data: dict or list, type_data: type,
                                schema_path: str) -> dict or list:
        """Check response data, it format must match to the scheme"""
        schema = self.get_api_schema(schema_path)
        if type(data) != type_data:
            raise serializers.ValidationError(
                "Wrong form data in response {}".format(self.api_name)
            )
        try:
            validate(data, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise serializers.ValidationError(
                "Wrong form data in response {},"
                "{}".format(self.__str__(), e.message)
            )
        return data

    def _get_valid_response_data(self, type_data, schema_path) -> dict or str:
        """Get response data from API and validate format of it"""
        resp = self.get_response(self.url, params=self.params)
        data = self._validate_response_data(resp, type_data, schema_path)
        return data

    @abstractstaticmethod
    def form_data_for_person(user_data):
        """Format data in dict for creating Person object"""
        raise Exception("You must change this method")

    @abstractmethod
    def get_data_from_api(self):
        """Get valid response data and creating Person objects"""
        raise Exception("You must change this method")


class RandomUserApiWorker(GetDataFromApi):
    """Service for working with RandomUser Api"""

    def __init__(self, **kwargs):
        super(RandomUserApiWorker, self).__init__(**kwargs)
        self.url = "https://randomuser.me/api/"
        self.schema_path = "people/api_validator_schema/RandomUserApiSchema"
        self.api_name = "RandomUser Api"

    @staticmethod
    def form_data_for_person(user_data: dict) -> dict:
        gender = user_data["gender"]
        data = dict()
        data["gender"] = "M" if gender == "male" else "F"
        data["first_name"] = user_data["name"]["first"]
        data["last_name"] = user_data["name"]["last"]
        return data

    def get_data_from_api(self) -> None:
        users = self._get_valid_response_data(dict, self.schema_path)
        for user in users["results"]:
            city = user["location"]["city"]
            location = Location.objects.get_or_create(city=city)[0]
            data = self.form_data_for_person(user)
            data["location"] = location
            Person.objects.create(**data)


class UINamesApiWorker(GetDataFromApi):
    """Service for working with UiNames Api"""

    def __init__(self, **kwargs):
        super(UINamesApiWorker, self).__init__(**kwargs)
        self.url = 'https://uinames.com/api/'
        self.schema_path = "people/api_validator_schema/UINamesApiSchema"
        self.api_name = "UINames Api"

    @staticmethod
    def form_data_for_person(user_data: dict) -> dict:
        gender = user_data["gender"]
        data = dict()
        data["gender"] = "M" if gender == "male" else "F"
        data["first_name"] = user_data["name"]
        data["last_name"] = user_data["surname"]
        return data

    def get_data_from_api(self) -> None:
        users = self._get_valid_response_data(list, self.schema_path)
        for user in users:
            region = user["region"]
            location = Location.objects.get_or_create(region=region)[0]
            data = self.form_data_for_person(user)
            data["location"] = location
            Person.objects.create(**data)


class GenderizeApi(GetDataFromApi):
    """Service for working with Genderize Api"""

    def __init__(self, **kwargs):
        super(GenderizeApi, self).__init__(**kwargs)
        self.url = "https://api.genderize.io/"
        self.schema_path = "people/api_validator_schema/GenderizeApiSchema"
        self.api_name = "Genderize Api"

    @staticmethod
    def form_data_for_person(gender: str) -> str:
        data = "M" if gender == "male" else "F"
        return data

    def get_data_from_api(self) -> dict:
        gender_data = self._get_valid_response_data(dict, self.schema_path)
        data = dict()
        data["gender"] = self.form_data_for_person(gender_data["gender"])
        return data


class JsonPlaceholderApiWorker(GetDataFromApi):
    """Service for working with JsonPlaceholder Api"""

    def __init__(self, **kwargs):
        super(JsonPlaceholderApiWorker, self).__init__(**kwargs)
        self.url = 'http://jsonplaceholder.typicode.com/users'
        self.schema_path = "people/api_validator_schema/JsonPlaceholderApiSchema"
        self.api_name = "JsonPlaceholder Api"

    @staticmethod
    def form_data_for_person(user_data: dict) -> dict:
        full_name = user_data["name"].split(" ")
        gender = GenderizeApi(
            params={"name": full_name[-2].lower()}).get_data_from_api()
        data = dict()
        data["first_name"] = full_name[0]
        data["last_name"] = full_name[1]
        data.update(gender)
        return data

    def get_data_from_api(self) -> None:
        users = self._get_valid_response_data(list, self.schema_path)
        for user in users:
            city = user["address"]["city"]
            location = Location.objects.get_or_create(city=city)[0]
            data = self.form_data_for_person(user)
            data["location"] = location
            Person.objects.create(**data)


class ApiWorker:
    """Service for run Api Workers"""

    def __init__(self, api_worker: GetDataFromApi or List[GetDataFromApi]):
        self.api_worker = api_worker
        self.many = True if type(self.api_worker) == list else False

    def check_worker(self):
        if self.many:
            for worker in self.api_worker:
                if not isinstance(worker, GetDataFromApi):
                    raise serializers.ValidationError(
                        "Api Worker must be instance of class GetDataFromApi"
                    )
        else:
            if not isinstance(self.api_worker, GetDataFromApi):
                raise serializers.ValidationError(
                    "Api Worker must be instance of class GetDataFromApi"
                )

    def get_data(self) -> None:
        self.check_worker()
        if self.many:
            for worker in self.api_worker:
                worker.get_data_from_api()
        else:
            self.api_worker.get_data_from_api()


def get_users_data_from_api() -> None:
    api_workers = [
        RandomUserApiWorker(params={'results': 5}),
        UINamesApiWorker(params={'amount': 10}),
        JsonPlaceholderApiWorker()
    ]
    ApiWorker(api_workers).get_data()
