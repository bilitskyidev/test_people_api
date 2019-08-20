from rest_framework import serializers
import requests
from people.models import Person, Location
from abc import ABC, abstractmethod


class GetUsersDataFromApi(ABC):
    def __init__(self, url, params=None):
        self.data = {}
        self.url = url
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

    @abstractmethod
    def form_data_for_person(self, user_data):
        raise Exception("You must change this method")

    @abstractmethod
    def get_data_from_api(self):
        raise Exception("You must change this method")


class RandomUserApiWorker(GetUsersDataFromApi):

    def form_data_for_person(self, user_data):
        gender = user_data["gender"]
        self.data.clear()
        self.data["gender"] = "M" if gender == "male" else "F"
        self.data["first_name"] = user_data["name"]["first"]
        self.data["last_name"] = user_data["name"]["last"]
        return self.data

    def get_data_from_api(self):
        resp = self.get_response(self.url, params=self.params)['results']
        for user in resp:
            try:
                city = user["location"]["city"]
                location = Location.objects.get_or_create(city=city)[0]
                self.form_data_for_person(user)
            except KeyError:
                raise serializers.ValidationError(
                    'Got wrong data from random user api'
                )

            self.data["location"] = location
            Person.objects.create(**self.data)


class UINamesApiWorker(GetUsersDataFromApi):

    def form_data_for_person(self, user_data):
        gender = user_data["gender"]
        self.data.clear()
        self.data["gender"] = "M" if gender == "male" else "F"
        self.data["first_name"] = user_data["name"]
        self.data["last_name"] = user_data["surname"]
        return self.data

    def get_data_from_api(self):
        resp = self.get_response(self.url, params=self.params)
        for user in resp:
            try:
                region = user["region"]
                location = Location.objects.get_or_create(region=region)[0]
                self.form_data_for_person(user)
            except KeyError:
                raise serializers.ValidationError(
                    'Got wrong data from uinames api'
                )
            self.data["location"] = location
            Person.objects.create(**self.data)


class JsonPlaceholderApiWorker(GetUsersDataFromApi):

    def form_data_for_person(self, user_data):
        url = "https://api.genderize.io/"
        self.data.clear()
        full_name = user_data["name"].split(" ")
        self.data["first_name"] = full_name[0]
        self.data["last_name"] = full_name[1]
        resp = self.get_response(url, params={"name": full_name[0].lower()})
        try:
            gender = resp["gender"]
        except KeyError:
            raise serializers.ValidationError(
                'Got wrong data from genderize api'
            )
        self.data["gender"] = "M" if gender == "male" else "F"
        return self.data

    def get_data_from_api(self):
        resp = self.get_response(self.url, params=self.params)
        for user in resp:
            try:
                city = user["address"]["city"]
                location = Location.objects.get_or_create(city=city)[0]
                self.form_data_for_person(user)
            except KeyError:
                raise serializers.ValidationError(
                    'Got wrong data from jsonplaceholder api'
                )
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


def get_users_data_from_apies():
    api_workers = [
        RandomUserApiWorker('https://randomuser.me/api/', params={'results': 5}),
        UINamesApiWorker('https://uinames.com/api/', params={'amount': 10}),
        JsonPlaceholderApiWorker('http://jsonplaceholder.typicode.com/users')
    ]
    ApiWorker(api_workers, many=True).get_data()
