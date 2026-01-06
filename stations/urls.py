from django.urls import path
from .views import (
    StationListView,
    MapRedirectView,
    StationCreateView,
    StationDeleteView,
    LineCreateView,
    LineDeleteView,
    LineToggleRunningView,
    LineToggleTicketPurchaseView,
    LineUpdateView,
    StationUpdateView
)

app_name = 'stations'
urlpatterns = [
    path('list/', StationListView.as_view(), name='list'),
    path('map/', MapRedirectView.as_view(), name='map'),
    path('create/', StationCreateView.as_view(), name='create'),
    path('update/<str:pk>/', StationUpdateView.as_view(), name='update'),
    path('delete/<str:pk>/', StationDeleteView.as_view(), name='delete'),
    path('lines/delete/<str:pk>/', LineDeleteView.as_view(), name='line_delete'),
    path('lines/update/<str:pk>/', LineUpdateView.as_view(), name='line_update'),
    path('lines/create/', LineCreateView.as_view(), name='line_create'),
    path('lines/toggle/running/<str:pk>/', LineToggleRunningView.as_view(), name='line_running'),
    path('lines/toggle/allow_running/<str:pk>/', LineToggleTicketPurchaseView.as_view(), name='line_allow_ticket_purchase')
]
