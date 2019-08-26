from django.db import models


class Location(models.Model):
    city = models.CharField(max_length=250, blank=True, null=True, unique=True)
    region = models.CharField(max_length=250, blank=True, null=True, unique=True)

    @staticmethod
    def form_data(queryset):
        data = [{"M": [], "Total": 0}, {"F": [], "Total": 0}]
        for location in queryset:
            gender = location.pop("person__gender", None)
            if gender == "M":
                data[0][gender].append(location)
                data[0]["Total"] += location["gender_count"]
            elif gender == "F":
                data[1][gender].append(location)
                data[1]["Total"] += location["gender_count"]
        return data

    @classmethod
    def get_location_data(cls):
        queryset = cls.objects.all()\
            .annotate()\
            .values('city', 'region')\
            .annotate(gender_count=models.Count('person__gender'))\
            .values('person__gender', 'city', 'gender_count', "region")
        return cls.form_data(queryset)


class Person(models.Model):
    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'
    GENDER_CHOICES = (
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    location = models.ForeignKey(Location, related_name="person",
                                 on_delete=models.CASCADE)

