from django.urls import path
from .views import (
    TicketListView, 
    TicketPurchaseView, 
    WalletBalanceUpdateView, 
    TicketScanUpdateView, 
    TicketPurchaseOfflineView,
    ScannerTemplateView,
    DashboardTemplateView,
    ConfirmTicketPurchase
)

app_name = 'tickets'
urlpatterns = [
    path('my/', TicketListView.as_view(), name='ticket_list'),
    path('buy/', TicketPurchaseView.as_view(), name='ticket_purchase'),
    path('dashboard/add-funds/', WalletBalanceUpdateView.as_view(), name='wallet_balance_update'),
    path('scanner/scan/', TicketScanUpdateView.as_view(), name='ticket_scan'),
    path('scanner/buy/', TicketPurchaseOfflineView.as_view(), name='ticket_purchase_offline'),
    path('scanner/', ScannerTemplateView.as_view(), name='scanner'),
    path('dashboard/', DashboardTemplateView.as_view(), name='dashboard'),
    path('confirm/', ConfirmTicketPurchase.as_view(), name='confirm')
]
