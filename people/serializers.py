from rest_framework import serializers
from people.models import Person, Location


class GenderCountByLocationSerializer(serializers.Serializer):
    male = serializers.IntegerField()
    female = serializers.IntegerField()
    total = serializers.IntegerField()


class LocationCount(serializers.Serializer):
    location = serializers.SerializerMethodField()
    gender_count = serializers.IntegerField()

    class Meta:
        model = Location
        fields = ("gender_count", "location")

    @staticmethod
    def get_location(obj):
        if obj["city"]:
            return obj["city"]
        elif obj["region"]:
            return obj["region"]
        return None


class LocationGenderSerializer(LocationCount):
    gender_count = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_gender_count(obj):
        serializer = GenderCountByLocationSerializer(data=obj)
        serializer.is_valid(raise_exception=True)
        return serializer.data


class GenderLocationSerializer(serializers.Serializer):
    data = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_data(obj):
        total = obj.pop("Total", None)
        gender = "Male" if list(obj.keys())[0] == "M" else "Female"
        return {
            gender: LocationCount(obj[list(obj.keys())[0]], many=True).data,
            "Total": total
        }
