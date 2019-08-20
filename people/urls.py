from django.urls import path
from people.views import LocationPersonCountByGenderViewSet, GenderPersonCountByLocationViewSet

urlpatterns = [
    path('location/', LocationPersonCountByGenderViewSet.as_view({'get': 'list'}),
         name='location'),
    path('gender/',
         GenderPersonCountByLocationViewSet.as_view({'get': 'list'}),
         name='gender')
]