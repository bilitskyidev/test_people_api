from abc import ABC, abstractmethod, abstractstaticmethod
from rest_framework import serializers
from typing import List
import requests
from people.models import Person, Location


class GetDataFromApi(ABC):
    """Interface for creating service, that work with API"""
    def __init__(self, params: dict = None):
        self.url = None
        self.params = params

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

    @abstractstaticmethod
    def validate_response_data(resp: dict):
        pass

    def _get_valid_response_data(self) -> dict or str:
        """Get response data from API and validate format of it"""
        resp = self.get_response(self.url, params=self.params)
        data = self.validate_response_data(resp)
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
        self.url = 'https://randomuser.me/api/'

    @staticmethod
    def validate_response_data(data: dict) -> dict:
        try:
            data = data["results"]
        except KeyError:
            raise serializers.ValidationError(
                "Wrong form data in response RandomUserApi,"
                "results not found"
            )
        valid_data = {"gender", "location", "name"}
        valid_data_name = {"first", "last"}
        if valid_data & set(data[0].keys()) != valid_data:
            raise serializers.ValidationError(
                "Wrong form data in response RandomUserApi,"
                "{} not found".format(
                    valid_data & (valid_data ^ set(data[0].keys()))))
        if not data[0]["location"].get("city", None):
            raise serializers.ValidationError(
                "Wrong form data in response RandomUserApi,"
                "city not found")
        if valid_data_name & set(data[0]["name"].keys()) != valid_data_name:
            raise serializers.ValidationError(
                "Wrong form data in response RandomUserApi,"
                "{} not found".format(
                    valid_data_name & (valid_data_name ^ set(data[0]["name"].keys()))))
        return data

    @staticmethod
    def form_data_for_person(user_data: dict) -> dict:
        gender = user_data["gender"]
        data = dict()
        data["gender"] = "M" if gender == "male" else "F"
        data["first_name"] = user_data["name"]["first"]
        data["last_name"] = user_data["name"]["last"]
        return data

    def get_data_from_api(self) -> None:
        users = self._get_valid_response_data()
        for user in users:
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

    @staticmethod
    def validate_response_data(data: list) -> list:
        valid_data = {"gender", "name", "surname", "region"}
        if valid_data & set(data[0].keys()) != valid_data:
            raise serializers.ValidationError(
                    "Wrong form data in response UINamesApi,"
                    "{} not found".format(
                        valid_data & (valid_data ^ set(data[0].keys()))))
        return data

    @staticmethod
    def form_data_for_person(user_data: dict) -> dict:
        gender = user_data["gender"]
        data = dict()
        data["gender"] = "M" if gender == "male" else "F"
        data["first_name"] = user_data["name"]
        data["last_name"] = user_data["surname"]
        return data

    def get_data_from_api(self) -> None:
        users = self._get_valid_response_data()
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

    @staticmethod
    def form_data_for_person(gender: str) -> str:
        data = "M" if gender == "male" else "F"
        return data

    @staticmethod
    def validate_response_data(data: dict) -> str:
        try:
            gender = data["gender"]
        except KeyError:
            raise serializers.ValidationError(
                "Wrong form data in response GenderizeApi,"
                "gender not found"
            )
        return gender

    def get_data_from_api(self) -> dict:
        gender = self._get_valid_response_data()
        data = dict()
        data["gender"] = self.form_data_for_person(gender)
        return data


class JsonPlaceholderApiWorker(GetDataFromApi):
    """Service for working with JsonPlaceholder Api"""

    def __init__(self, **kwargs):
        super(JsonPlaceholderApiWorker, self).__init__(**kwargs)
        self.url = 'http://jsonplaceholder.typicode.com/users'

    @staticmethod
    def validate_response_data(data: list) -> list:
        valid_data = {"address", "name"}
        if valid_data & set(data[0].keys()) != valid_data:
            raise serializers.ValidationError(
                    "Wrong form data in response JsonPlaceholderApi,"
                    "{} not found".format(
                        valid_data & (valid_data ^ set(data[0].keys()))))
        if not data[0]["address"].get("city", None):
            raise serializers.ValidationError(
                    "Wrong form data in response JsonPlaceholderApi,"
                    "city not found")
        if len(data[0]["name"].split(" ")) < 2:
            raise serializers.ValidationError(
                "Wrong form data in response JsonPlaceholderApi,"
                "first_name or last_name not found")
        return data

    @staticmethod
    def form_data_for_person(user_data: dict) -> dict:
        full_name = user_data["name"].split(" ")
        gender = GenderizeApi(params={"name": full_name[0].lower()}).get_data_from_api()
        data = dict()
        data["first_name"] = full_name[0]
        data["last_name"] = full_name[1]
        data.update(gender)
        return data

    def get_data_from_api(self) -> None:
        users = self._get_valid_response_data()
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
