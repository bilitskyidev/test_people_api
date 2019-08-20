from django.db.models import Count, Q
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from people.serializers import LocationGenderSerializer, GenderLocationSerializer
from people.models import Location
from people.service import GetUsersDataFromApi


class LocationPersonCountByGenderViewSet(ListModelMixin, GenericViewSet):
    serializer_class = LocationGenderSerializer
    queryset = Location.objects.all()

    def get_queryset(self):
        queryset = self.queryset.annotate(
            female=Count("person__gender", filter=Q(person__gender='F')),
            male=Count("person__gender", filter=Q(person__gender='M')),
            total=Count("person")).values("id", "city", "region", "female",
                                          "male", "total")
        return queryset

    def list(self, request, *args, **kwargs):
        GetUsersDataFromApi().get_persons_data_from_apies()
        return super(LocationPersonCountByGenderViewSet, self).list(request, *args, **kwargs)


class GenderPersonCountByLocationViewSet(ListModelMixin, GenericViewSet):
    serializer_class = GenderLocationSerializer

    def get_queryset(self):
        return Location.get_location_data()
