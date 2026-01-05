from django.urls import path
from .views import MapRedirectView, StationListView

app_name = 'stations'
urlpatterns = [
    path('list/', StationListView.as_view(), name='list'),
    path('map/', MapRedirectView.as_view(), name='map')
]
