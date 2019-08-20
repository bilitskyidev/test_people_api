from rest_framework import serializers
import requests
from people.models import Person, Location


class GetUsersDataFromApi:
    def __init__(self, first_name=None):
        self.first_name = first_name
        self.data = {}

    @staticmethod
    def get_response(url, params=None):
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise serializers.ValidationError(
                response.json()['error']['message']
            )

    def form_data_for_person_from_random_user(self, user_data):
        gender = user_data["gender"]
        self.data.clear()
        self.data["gender"] = "M" if gender == "male" else "F"
        self.data["first_name"] = user_data["name"]["first"]
        self.data["last_name"] = user_data["name"]["last"]
        return self.data

    def get_random_user_data(self):
        url = "https://randomuser.me/api/"
        resp = self.get_response(url, params={"results": 5})['results']
        for user in resp:
            try:
                city = user["location"]["city"]
                location = Location.objects.get_or_create(city=city)[0]
                self.form_data_for_person_from_random_user(user)
            except KeyError:
                raise serializers.ValidationError(
                    'Got wrong data from random user api'
                )

            self.data["location"] = location
            Person.objects.create(**self.data)

    def form_data_for_person_from_uinames(self, user_data):
        gender = user_data["gender"]
        self.data.clear()
        self.data["gender"] = "M" if gender == "male" else "F"
        self.data["first_name"] = user_data["name"]
        self.data["last_name"] = user_data["surname"]
        return self.data

    def get_uinames_user_data(self):
        url = "https://uinames.com/api/"
        resp = self.get_response(url, params={"amount": 10})
        for user in resp:
            try:
                region = user["region"]
                location = Location.objects.get_or_create(region=region)[0]
                self.form_data_for_person_from_uinames(user)
            except KeyError:
                raise serializers.ValidationError(
                    'Got wrong data from uinames api'
                )
            self.data["location"] = location
            Person.objects.create(**self.data)

    def form_data_for_person_from_jsonplaceholder(self, user_data):
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

    def get_jsonplaceholder_user_data(self):
        url = "http://jsonplaceholder.typicode.com/users"
        resp = self.get_response(url)
        for user in resp:
            try:
                city = user["address"]["city"]
                location = Location.objects.get_or_create(city=city)[0]
                self.form_data_for_person_from_jsonplaceholder(user)
            except KeyError:
                raise serializers.ValidationError(
                    'Got wrong data from jsonplaceholder api'
                )
            self.data["location"] = location
            Person.objects.create(**self.data)

    def get_persons_data_from_apies(self):
        self.get_random_user_data()
        self.get_uinames_user_data()
        self.get_jsonplaceholder_user_data()
