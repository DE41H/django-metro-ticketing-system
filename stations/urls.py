from django.urls import path
from .views import MapTemplateView, StationListView

app_name = 'stations'
urlpatterns = [
    path('list/', StationListView.as_view(), name='list'),
    path('map/', MapTemplateView.as_view(), name='map')
]
