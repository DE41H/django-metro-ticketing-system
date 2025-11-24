from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.views import generic
from .models import Station
from .utils import get_map

# Create your views here.


class StationListView(generic.ListView):
    model = Station
    template_name = 'stations/station_list.html'
    context_object_name = 'stations'
    ordering = ['footfall']

    def get_queryset(self) -> QuerySet[Any]:
        return Station.objects.prefetch_related('lines', 'neighbours')
    

class MapTemplateView(generic.TemplateView):
    template_name = get_map()