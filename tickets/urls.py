from django.urls import path
from .views import (
    TicketListView, 
    TicketPurchaseView, 
    WalletBalanceUpdateView, 
    TicketScanUpdateView, 
    TicketPurchaseOfflineView,
    ScannerTemplateView,
    DashboardTemplateView
)

urlpatterns = [
    path('my/', TicketListView.as_view(), name='TicketListView'),
    path('buy/', TicketPurchaseView.as_view(), name='TicketPurchaseView'),
    path('dashboard/add-funds/', WalletBalanceUpdateView.as_view(), name='WalletBalanceUpdateView'),
    path('scanner/scan/', TicketScanUpdateView.as_view(), name='TicketScanUpdateView'),
    path('scanner/buy/', TicketPurchaseOfflineView.as_view(), name='TicketPurchaseOfflineView'),
    path('scanner/', ScannerTemplateView.as_view(), name='ScannerTemplateView'),
    path('dashboard/', DashboardTemplateView.as_view(), name='DashboardTemplateView')
]
