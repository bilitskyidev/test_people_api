from rest_framework import serializers
import requests
from people.models import Person, Location
from abc import ABC, abstractmethod, abstractstaticmethod


class GetDataFromApi(ABC):
    def __init__(self, params=None):
        self.url = None
        self.data = {}
        self.params = params

    @staticmethod
    def get_response(url, params):
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise serializers.ValidationError(
                response.json()['error']['message']
            )

    @abstractstaticmethod
    def validate_response_data(resp):
        pass

    def _get_valid_response_data(self):
        resp = self.get_response(self.url, params=self.params)
        data = self.validate_response_data(resp)
        return data

    @abstractmethod
    def form_data_for_person(self, user_data):
        raise Exception("You must change this method")

    @abstractmethod
    def get_data_from_api(self):
        raise Exception("You must change this method")


class RandomUserApiWorker(GetDataFromApi):

    def __init__(self, **kwargs):
        super(RandomUserApiWorker, self).__init__(**kwargs)
        self.url = 'https://randomuser.me/api/'

    @staticmethod
    def validate_response_data(data):
        try:
            data = data["results"]
        except KeyError:
            raise serializers.ValidationError(
                "Wrong form data in response,"
                "'results' not found"
            )
        valid_data = {"gender", "location", "name"}
        if len(valid_data & set(data[0].keys())) == 3:
            if len({"city"} & set(data[0]["location"].keys())) != 1:
                raise serializers.ValidationError("Wrong form data in response,"
                                                  "'city' not found")
            elif len({"first", "last"} & set(data[0]["name"].keys())) != 2:
                raise serializers.ValidationError(
                    "Wrong form data in response,"
                    "{} not found".format(
                        {"first", "last"} & ({"first", "last"} ^ set(data[0]["name"].keys()))))
        else:
            raise serializers.ValidationError(
                    "Wrong form data in response,"
                    "{} not found".format(
                        valid_data & (valid_data ^ set(data[0].keys()))))
        return data

    def form_data_for_person(self, user_data):
        gender = user_data["gender"]
        self.data.clear()
        self.data["gender"] = "M" if gender == "male" else "F"
        self.data["first_name"] = user_data["name"]["first"]
        self.data["last_name"] = user_data["name"]["last"]
        return self.data

    def get_data_from_api(self):
        users = self._get_valid_response_data()
        for user in users:
            city = user["location"]["city"]
            location = Location.objects.get_or_create(city=city)[0]
            self.form_data_for_person(user)
            self.data["location"] = location
            Person.objects.create(**self.data)


class UINamesApiWorker(GetDataFromApi):
    def __init__(self, **kwargs):
        super(UINamesApiWorker, self).__init__(**kwargs)
        self.url = 'https://uinames.com/api/'

    @staticmethod
    def validate_response_data(data):
        valid_data = {"gender", "name", "surname", "region"}
        if len(valid_data & set(data[0].keys())) == 4:
            return data
        else:
            raise serializers.ValidationError(
                    "Wrong form data in response,"
                    "{} not found".format(
                        valid_data & (valid_data ^ set(data[0].keys()))))

    def form_data_for_person(self, user_data):
        gender = user_data["gender"]
        self.data.clear()
        self.data["gender"] = "M" if gender == "male" else "F"
        self.data["first_name"] = user_data["name"]
        self.data["last_name"] = user_data["surname"]
        return self.data

    def get_data_from_api(self):
        users = self._get_valid_response_data()
        for user in users:
            region = user["region"]
            location = Location.objects.get_or_create(region=region)[0]
            self.form_data_for_person(user)
            self.data["location"] = location
            Person.objects.create(**self.data)


class GenderizeApi(GetDataFromApi):

    def __init__(self, **kwargs):
        super(GenderizeApi, self).__init__(**kwargs)
        self.url = "https://api.genderize.io/"

    def form_data_for_person(self, gender):
        self.data["gender"] = "M" if gender == "male" else "F"
        return self.data

    @staticmethod
    def validate_response_data(data):
        try:
            gender = data["gender"]
        except KeyError:
            raise serializers.ValidationError(
                'Got wrong data from genderize api'
            )
        return gender

    def get_data_from_api(self):
        gender = self._get_valid_response_data()
        self.form_data_for_person(gender)
        return self.data


class JsonPlaceholderApiWorker(GetDataFromApi):

    def __init__(self, **kwargs):
        super(JsonPlaceholderApiWorker, self).__init__(**kwargs)
        self.url = 'http://jsonplaceholder.typicode.com/users'

    @staticmethod
    def validate_response_data(data):
        valid_data = {"address", "name"}
        if len(valid_data & set(data[0].keys())) == 2:
            if len({"city"} & set(data[0]["address"].keys())) == 1:
                return data
            else:
                raise serializers.ValidationError(
                    "Wrong form data in response,"
                    "'city' not found")
        else:
            raise serializers.ValidationError(
                    "Wrong form data in response,"
                    "{} not found".format(
                        valid_data & (valid_data ^ set(data[0].keys()))))

    def form_data_for_person(self, user_data):
        full_name = user_data["name"].split(" ")
        gender = GenderizeApi(params={"name": full_name[0].lower()}).get_data_from_api()
        self.data.clear()
        self.data["first_name"] = full_name[0]
        self.data["last_name"] = full_name[1]
        self.data.update(gender)
        return self.data

    def get_data_from_api(self):
        users = self._get_valid_response_data()
        for user in users:
            city = user["address"]["city"]
            location = Location.objects.get_or_create(city=city)[0]
            self.form_data_for_person(user)
            self.data["location"] = location
            Person.objects.create(**self.data)


class ApiWorker:
    def __init__(self, api_worker, many=False):
        self.api_worker = api_worker
        self.many = many

    def get_data(self):
        if self.many:
            for worker in self.api_worker:
                worker.get_data_from_api()
        else:
            self.api_worker.get_data_from_api()


def get_users_data_from_apis():
    api_workers = [
        RandomUserApiWorker(params={'results': 5}),
        UINamesApiWorker(params={'amount': 10}),
        JsonPlaceholderApiWorker()
    ]
    ApiWorker(api_workers, many=True).get_data()
