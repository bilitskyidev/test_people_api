from unittest import TestCase, mock
from rest_framework import serializers
import requests
import jsonschema
from people.service import *
from people.models import Location, Person


class GetResponseTestCase(TestCase):

    @mock.patch("requests.get")
    def test_get_response_success(self, mock_request_get):
        json = mock.Mock()
        json.return_value = {"test": "test"}
        mock_request_get.return_value = mock.MagicMock(status_code=200,
                                                       json=json)
        result = GetDataFromApi.get_response("test", "test")
        self.assertEqual(result, json())

    @mock.patch("requests.get")
    def test_get_response_failed_status_code(self, mock_request_get):
        json = mock.Mock()
        json.return_value = {"error": {"message": "test message"}}
        mock_request_get.return_value = mock.MagicMock(status_code=201,
                                                       json=json)
        with self.assertRaises(serializers.ValidationError):
            GetDataFromApi.get_response("test", "test")


class GetValidResponseDataTestCase(TestCase):

    def test_get_valid_response_data_success(self):
        service = RandomUserApiWorker()
        service.get_response = mock.MagicMock(return_value={"test": "test"})
        service._validate_response_data = mock.MagicMock(return_value={"test": "test"})
        result = service._get_valid_response_data(dict)
        self.assertEqual(result, {"test": "test"})

    def test_get_valid_response_data_failed_get_response(self):
        service = RandomUserApiWorker()
        service.get_response = mock.MagicMock(side_effect=serializers.ValidationError)
        service._validate_response_data = mock.MagicMock(return_value={"test": "test"})
        with self.assertRaises(serializers.ValidationError):
            service._get_valid_response_data(dict)

    def test_get_valid_response_data_failed_validate_response_data(self):
        service = RandomUserApiWorker()
        service.get_response = mock.MagicMock(return_value={"test": "test"})
        service._validate_response_data = mock.MagicMock(side_effect=serializers.ValidationError)
        with self.assertRaises(serializers.ValidationError):
            service._get_valid_response_data(dict)


class ValidateResponseDataTestCase(TestCase):

    @mock.patch("jsonschema.validate")
    def test_validate_response_data_success(self, mock_validate):
        mock_validate.return_value = None
        service = RandomUserApiWorker()
        result = service._validate_response_data({"test": "test"}, dict)
        self.assertEqual(result, {"test": "test"})

    def test_validate_response_data_failed_schema_not_found(self):
        service = RandomUserApiWorker()
        service.get_api_schema.side_effect = serializers.ValidationError
        with self.assertRaises(serializers.ValidationError):
            service._validate_response_data({"test": "test"}, dict)

    def test_validate_response_data_failed_wrong_type(self):
        service = RandomUserApiWorker()
        with self.assertRaises(serializers.ValidationError):
            service._validate_response_data({"test": "test"}, list)

    @mock.patch("jsonschema.validate")
    def test_validate_response_data_failed_validate_error(self, mock_validate):
        message = "wrong format response data"
        mock_validate.side_effect = jsonschema.exceptions.ValidationError(message)
        service = RandomUserApiWorker()
        with self.assertRaises(serializers.ValidationError):
            service._validate_response_data({"test": "test"}, dict)
        try:
            service._validate_response_data({"test": "test"}, dict)
        except serializers.ValidationError as e:
            self.assertEqual(e.detail[0], "Wrong form data in response {},"
                                          "{}".format(service.api_name, message))


class GetApiSchemaTestCase(TestCase):

    def test_get_api_schema_success(self):
        with mock.patch('builtins.open', mock.mock_open(
                read_data='{"test": "test"}')) as m:
            service = GetDataFromApi
            result = service.get_api_schema("test")
            m.assert_called_once_with("test", 'r')
            self.assertEqual(result, {"test": "test"})

    @mock.patch("builtins.open")
    def test_get_api_schema_failed_schema_not_found(self, mock_open):
        mock_open.side_effect = FileNotFoundError
        path = "test"
        service = GetDataFromApi
        with self.assertRaises(serializers.ValidationError):
            service.get_api_schema(path)
        try:
            service.get_api_schema(path)
        except serializers.ValidationError as e:
            self.assertEqual(e.detail[0],
                             "Api schema not found, wrong path:{}".format(path))



class RandomUserApiTestCaseMixin(TestCase):

    def setUp(self) -> None:
        self.data = {
            "results": [
                {
                    "gender": "test",
                    "location": {
                        "city": "test"
                    },
                    "name": {
                        "first": "test",
                        "last": "test"
                    }
                },
            ]
        }
        self.error_message = lambda x, y: "Wrong form data in response {}," \
                             "{}".format(y, x)
        self.form_data = {
            "gender": "M",
            "first_name": "test",
            "last_name": "test"
        }


class RandomUserApiFormDataForPerson(RandomUserApiTestCaseMixin):

    def test_form_data_for_person_gender_success_male(self):
        self.data["results"][0]["gender"] = "male"
        service = RandomUserApiWorker
        result = service.form_data_for_person(self.data["results"][0])
        self.assertEqual(result, self.form_data)

    def test_form_data_for_person_gender_success_female(self):
        self.data["results"][0]["gender"] = "female"
        service = RandomUserApiWorker
        result = service.form_data_for_person(self.data["results"][0])
        self.assertNotEqual(result, self.form_data)
        self.assertEqual(result["gender"], "F")
        self.assertEqual(result["first_name"], "test")
        self.assertEqual(result["last_name"], "test")


class RandomUserApiGetDataFromApiTestCase(RandomUserApiTestCaseMixin):

    @mock.patch("people.models.Location.objects.get_or_create")
    @mock.patch("people.models.Person.objects.create")
    def test_get_data_from_api_success(self, mock_person, mock_location):
        mock_person.return_value = None
        mock_location.return_value = [None, False]
        count = 5
        self.data['results'] = self.data['results'] * count
        service = RandomUserApiWorker()
        service._get_valid_response_data = mock.MagicMock(
            return_value=self.data
        )
        service.form_data_for_person = mock.MagicMock(
            return_value=self.form_data
        )
        service.get_data_from_api()
        self.assertEqual(mock_person.call_count, count)
        self.assertEqual(mock_location.call_count, count)

    @mock.patch("people.models.Location.objects.get_or_create")
    @mock.patch("people.models.Person.objects.create")
    def test_get_data_from_api_failed(self, mock_person, mock_location):
        mock_person.return_value = None
        mock_location.return_value = [None, False]
        count = 5
        self.data['results'] = self.data['results'] * count
        service = RandomUserApiWorker()
        service._get_valid_response_data = mock.MagicMock(
            side_effect=serializers.ValidationError
        )
        service.form_data_for_person = mock.MagicMock(
            return_value=self.form_data
        )
        with self.assertRaises(serializers.ValidationError):
            service.get_data_from_api()
        self.assertEqual(mock_person.call_count, 0)
        self.assertEqual(mock_location.call_count, 0)


class UINamesApiTestCaseMixin(RandomUserApiTestCaseMixin):

    def setUp(self) -> None:
        super(UINamesApiTestCaseMixin, self).setUp()
        self.data = [
            {
                "gender": "test",
                "region": "test",
                "name": "test",
                "surname": "test"
            },
        ]


class UINamesApiFormDataForPerson(UINamesApiTestCaseMixin):

    def test_form_data_for_person_gender_success_male(self):
        self.data[0]["gender"] = "male"
        service = UINamesApiWorker
        result = service.form_data_for_person(self.data[0])
        self.assertEqual(result, self.form_data)

    def test_form_data_for_person_gender_success_female(self):
        self.data[0]["gender"] = "female"
        service = UINamesApiWorker
        result = service.form_data_for_person(self.data[0])
        self.assertNotEqual(result, self.form_data)
        self.assertEqual(result["gender"], "F")
        self.assertEqual(result["first_name"], "test")
        self.assertEqual(result["last_name"], "test")


class UINamesApiGetDataFromApiTestCase(UINamesApiTestCaseMixin):

    @mock.patch("people.models.Location.objects.get_or_create")
    @mock.patch("people.models.Person.objects.create")
    def test_get_data_from_api_success(self, mock_person, mock_location):
        mock_person.return_value = None
        mock_location.return_value = [None, False]
        count = 5
        self.data = self.data * count
        service = UINamesApiWorker()
        service._get_valid_response_data = mock.MagicMock(
            return_value=self.data
        )
        service.form_data_for_person = mock.MagicMock(
            return_value=self.form_data
        )
        service.get_data_from_api()
        self.assertEqual(mock_person.call_count, count)
        self.assertEqual(mock_location.call_count, count)

    @mock.patch("people.models.Location.objects.get_or_create")
    @mock.patch("people.models.Person.objects.create")
    def test_get_data_from_api_failed(self, mock_person, mock_location):
        mock_person.return_value = None
        mock_location.return_value = [None, False]
        count = 5
        self.data = self.data * count
        service = UINamesApiWorker()
        service._get_valid_response_data = mock.MagicMock(
            side_effect=serializers.ValidationError
        )
        service.form_data_for_person = mock.MagicMock(
            return_value=self.form_data
        )
        with self.assertRaises(serializers.ValidationError):
            service.get_data_from_api()
        self.assertEqual(mock_person.call_count, 0)
        self.assertEqual(mock_location.call_count, 0)


class GenderizeApiFormDataForPersonTestCase(TestCase):

    def test_form_data_for_person_male(self):
        service = GenderizeApi
        result = service.form_data_for_person("male")
        self.assertEqual(result, "M")

    def test_form_data_for_person_female(self):
        service = GenderizeApi
        result = service.form_data_for_person("female")
        self.assertEqual(result, "F")


class GenderizeApiGetDataFromApiTestCase(TestCase):

    def test_get_data_from_api_success(self):
        service = GenderizeApi()
        service._get_valid_response_data = mock.MagicMock(
            return_value={"gender": "female"})
        service.form_data_for_person = mock.MagicMock(return_value="F")
        result = service.get_data_from_api()
        self.assertEqual(result, {"gender": "F"})

    def test_get_data_from_api_failed(self):
        service = GenderizeApi()
        service._get_valid_response_data = mock.MagicMock(
            side_effect=serializers.ValidationError
        )
        with self.assertRaises(serializers.ValidationError):
            service.get_data_from_api()


class JsonPlaceholderApiTestCaseMixin(RandomUserApiTestCaseMixin):

    def setUp(self) -> None:
        super(JsonPlaceholderApiTestCaseMixin, self).setUp()
        self.data = [
            {
                "name": "test test",
                "address": {
                    "city": "test"
                }
            },
        ]


class JsonPlaceholderApiFormDataForPersonTesCase(JsonPlaceholderApiTestCaseMixin):

    @mock.patch("people.service.GenderizeApi.get_data_from_api")
    def test_form_data_for_person_success_male(self, mock_genderize):
        mock_genderize.return_value = {"gender": "M"}
        service = JsonPlaceholderApiWorker
        result = service.form_data_for_person(self.data[0])
        self.assertEqual(result, self.form_data)

    @mock.patch("people.service.GenderizeApi.get_data_from_api")
    def test_form_data_for_person_failed_genderize_error(self, mock_genderize):
        mock_genderize.side_effect = serializers.ValidationError
        service = JsonPlaceholderApiWorker
        with self.assertRaises(serializers.ValidationError):
            service.form_data_for_person(self.data[0])


class JsonPlaceholderApiGetDataFromApiTestCase(JsonPlaceholderApiTestCaseMixin):

    @mock.patch("people.models.Location.objects.get_or_create")
    @mock.patch("people.models.Person.objects.create")
    def test_get_data_from_api_success(self, mock_person, mock_location):
        mock_person.return_value = None
        mock_location.return_value = [None, False]
        count = 5
        self.data = self.data * count
        service = JsonPlaceholderApiWorker()
        service._get_valid_response_data = mock.MagicMock(
            return_value=self.data
        )
        service.form_data_for_person = mock.MagicMock(
            return_value=self.form_data
        )
        service.get_data_from_api()
        self.assertEqual(mock_person.call_count, count)
        self.assertEqual(mock_location.call_count, count)

    @mock.patch("people.models.Location.objects.get_or_create")
    @mock.patch("people.models.Person.objects.create")
    def test_get_data_from_api_failed(self, mock_person, mock_location):
        mock_person.return_value = None
        mock_location.return_value = [None, False]
        count = 5
        self.data = self.data * count
        service = JsonPlaceholderApiWorker()
        service._get_valid_response_data = mock.MagicMock(
            side_effect=serializers.ValidationError
        )
        service.form_data_for_person = mock.MagicMock(
            return_value=self.form_data
        )
        with self.assertRaises(serializers.ValidationError):
            service.get_data_from_api()
        self.assertEqual(mock_person.call_count, 0)
        self.assertEqual(mock_location.call_count, 0)


class ApiWorkerTestCaseMixin(TestCase):

    def setUp(self) -> None:
        self.worker = mock.Mock(spec=GetDataFromApi)
        self.worker_with_method = mock.MagicMock(
            get_data_from_api=mock.MagicMock(
                return_value=True
            ))


class ApiWorkerCheckWorkerTestCase(ApiWorkerTestCaseMixin):

    def test_check_worker_many_false_success(self):
        service = ApiWorker(self.worker)
        self.assertFalse(service.many)
        result = service.check_worker()
        self.assertIsNone(result)

    def test_check_worker_many_false_failed(self):
        service = ApiWorker(mock.Mock())
        self.assertFalse(service.many)
        with self.assertRaises(serializers.ValidationError):
            service.check_worker()

    def test_check_worker_many_true_success(self):
        service = ApiWorker([self.worker, ])
        self.assertTrue(service.many)
        result = service.check_worker()
        self.assertIsNone(result)

    def test_check_worker_many_true_failed(self):
        service = ApiWorker([mock.Mock(), ])
        self.assertTrue(service.many)
        with self.assertRaises(serializers.ValidationError):
            service.check_worker()


class ApiWorkerGetDataTestCase(ApiWorkerTestCaseMixin):

    def test_get_data_success_many_false(self):
        service = ApiWorker(self.worker_with_method)
        service.check_worker = mock.MagicMock(return_value=None)
        service.get_data()
        self.worker_with_method.get_data_from_api.assert_called_once()
        self.assertFalse(service.many)

    def test_get_data_success_many_true(self):
        workers = [self.worker_with_method,
                   self.worker_with_method,
                   self.worker_with_method]
        service = ApiWorker(workers)
        service.check_worker = mock.MagicMock(return_value=None)
        service.get_data()
        self.assertTrue(service.many)
        self.assertEqual(self.worker_with_method.get_data_from_api.call_count,
                         len(workers))

    def test_get_data_failed_many_true(self):
        workers = [self.worker_with_method,
                   self.worker_with_method,
                   self.worker_with_method]
        service = ApiWorker(workers)
        service.check_worker = mock.MagicMock(side_effect=serializers.ValidationError)
        with self.assertRaises(serializers.ValidationError):
            service.get_data()
        self.assertEqual(self.worker_with_method.get_data_from_api.call_count, 0)


class LocationTestCase(TestCase):

    def setUp(self) -> None:
        self.fixture = [
            {
                "person__gender": "M",
                'city': 'Wisokyburgh',
                'region': None,
                'gender_count': 4
            },
            {
                "person__gender": "M",
                'city': None,
                'region': 'Bosnia and Herzegovina',
                'gender_count': 2
            },
            {
                "person__gender": "F",
                'city': 'wagga wagga',
                'region': None,
                'gender_count': 1
            },
            {
                "person__gender": "F",
                'city': 'salisbury',
                'region': None,
                'gender_count': 1
            },
        ]
        self.format_data = [
            {
                "M": [
                    {
                        'city': 'Wisokyburgh',
                        'region': None,
                        'gender_count': 4
                    },
                    {
                        'city': None,
                        'region': 'Bosnia and Herzegovina',
                        'gender_count': 2
                    }
                ],
                "Total": 6
            },
            {
                "F": [
                    {
                        'city': 'wagga wagga',
                        'region': None,
                        'gender_count': 1
                    },
                    {
                        'city': 'salisbury',
                        'region': None,
                        'gender_count': 1
                    },
                ],
                "Total": 2
            }
        ]
        self.empty_data = [{"M": [], "Total": 0}, {"F": [], "Total": 0}]

    def test_form_data_from_fixture(self):
        result = Location.form_data(self.fixture)
        self.assertEqual(result, self.format_data)

    def test_form_empty_data(self):
        result = Location.form_data([])
        self.assertEqual(result, self.empty_data)
