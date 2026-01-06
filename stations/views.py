from typing import Any
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.views import generic
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Station, Line
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


class StationCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Station
    fields = ['name', 'lines', 'neighbours']
    template_name_field = 'stations/station_create.html'
    success_url = reverse_lazy('stations:list')

    def test_func(self) -> bool | None:
        return self.request.user.is_staff


class StationDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Station
    template_name = 'stations/station_delete.html'
    success_url = reverse_lazy('stations:list')

    def test_func(self) -> bool | None:
        return self.request.user.is_staff


class LineCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Line
    fields = ['name', 'color']
    template_name = 'stations/station_create.html'
    
    def get_success_url(self) -> str:
        return reverse_lazy('stations:create')

    def test_func(self) -> bool | None:
        return self.request.user.is_staff


class LineDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Line
    template_name = 'stations/station_delete.html'

    def get_success_url(self) -> str:
        return reverse_lazy('stations:create')
    
    def test_func(self) -> bool | None:
        return self.request.user.is_staff


class LineToggleRunningView(LoginRequiredMixin, UserPassesTestMixin, generic.RedirectView):
    permanent = False

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str | None:
        return reverse_lazy('stations:create')

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        pk = self.kwargs.get('pk')
        line = get_object_or_404(Line, pk=pk)
        line.toggle_running()
        return super().post(request, *args, **kwargs)
    
    def test_func(self) -> bool | None:
        return self.request.user.is_staff


class LineToggleTicketPurchaseView(LoginRequiredMixin, UserPassesTestMixin, generic.RedirectView):
    permanent = False

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str | None:
        return reverse_lazy('stations:create')

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        pk = self.kwargs.get('pk')
        line = get_object_or_404(Line, pk=pk)
        line.toggle_ticket_purchase()
        return super().post(request, *args, **kwargs)
    
    def test_func(self) -> bool | None:
        return self.request.user.is_staff
