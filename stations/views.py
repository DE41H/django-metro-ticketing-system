from typing import Any
from django.db.models.query import QuerySet
from django.views import generic
from .models import Station
from .utils import get_map_url

# Create your views here.


class StationListView(generic.ListView):
    model = Station
    template_name = 'stations/station_list.html'
    context_object_name = 'stations'
    ordering = ['name']

    def get_queryset(self) -> QuerySet[Any]:
        return Station.objects.prefetch_related('lines', 'neighbours')
    

class MapRedirectView(generic.RedirectView):
    permanent = False

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str | None:
        return get_map_url()
    