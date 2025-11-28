from typing import Any
from django.shortcuts import redirect
from django.db.models.query import QuerySet
from django.views import generic, View
from .models import Station
from .utils import get_map_url

# Create your views here.


class StationListView(generic.ListView):
    model = Station
    template_name = 'stations/station_list.html'
    context_object_name = 'stations'
    ordering = ['-footfall', 'name']

    def get_queryset(self) -> QuerySet[Any]:
        return Station.objects.prefetch_related('lines', 'neighbours')
    

class MapTemplateView(View):
    def get(self, request, *args, **kwargs):
        return redirect(get_map_url())
    