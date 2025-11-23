from typing import Any
from django.db import transaction
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Ticket, Wallet
from .utils import calculate_ticket_price
from .forms import WalletBalanceUpdateForm, TicketScanUpdateForm


# Create your views here.


class TicketPurchaseView(LoginRequiredMixin, generic.CreateView):
    model = Ticket
    fields = ['start', 'stop']
    template_name = 'ticket_purchase_form.html'
    success_url = '/tickets/my/'

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.user = self.request.user
        wallet = Wallet.objects.get_or_create(user=self.request.user)[0]
        price = calculate_ticket_price(form.instance.start, form.instance.stop)
        try:
            with transaction.atomic():
                success = wallet.deduct(price)
                if not success:
                    raise Exception('Insufficient Funds')
            form.instance.user = self.request.user
            messages.success(self.request, 'Ticket Purchased Successfully!')
            return super().form_valid(form)
        except Exception:
            messages.error(self.request, 'Purchase Failed! Insufficient Wallet Funds')
            return redirect('/tickets/buy/')
            
        

class TicketListView(LoginRequiredMixin, generic.ListView):
    model = Ticket
    template_name = 'ticket_list.html'
    context_object_name = 'tickets'
    ordering = ['-created_at']

    def get_queryset(self) -> QuerySet[Any]:
        return Ticket.objects.select_related('start', 'stop') # type: ignore
    

class WalletBalanceUpdateView(LoginRequiredMixin, generic.FormView):
    model = Wallet
    form_class = WalletBalanceUpdateForm
    context_object_name = 'wallet'
    template_name = 'wallet_balance_update_form.html'
    success_url = '/tickets/dashboard/'

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model: # type: ignore
        return Wallet.objects.get_or_create(user=self.request.user)[0]
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        wallet = Wallet.objects.get_or_create(user=self.request.user)[0]
        amount = form.cleaned_data.get('amount')
        wallet.deduct(-amount) # type: ignore
        return redirect(self.get_success_url())
    

class TicketScanUpdateView(UserPassesTestMixin, generic.UpdateView):
    model = Ticket
    form_class = TicketScanUpdateForm
    template_name = 'ticket_scan_update_form.html'
    success_url = '/tickets/scanner/'

    def test_func(self) -> bool | None:
        return self.request.user.is_staff
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        try:
            ticket_id = form.cleaned_data.get('ticket_id')
        except Ticket.DoesNotExist:
            messages.error(self.request, f'Ticket Does Not Exist')
            return redirect('/tickets/scanner/scan/')
        ticket = Ticket.objects.get(id=ticket_id)
        match ticket.status:
            case Ticket.State.ACTIVE:
                ticket.status = ticket.State.IN_USE
            case Ticket.State.IN_USE:
                ticket.status = ticket.State.USED
        ticket.save()
        return redirect(self.get_success_url())
    

class TicketPurchaseOfflineView(UserPassesTestMixin, generic.CreateView):
    model = Ticket
    fields = ['start', 'stop']
    template_name = 'ticket_purchase_offline_form.html'
    success_url = '/tickets/scanner/'

    def test_func(self) -> bool | None:
        return self.request.user.is_staff
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        ticket = Ticket.objects.create(
            user=None,
            start=form.instance.start,
            stop=form.instance.stop,
        )
        messages.success(self.request, f'Purchase Successful! Ticket ID is: {ticket.id}')
        return redirect(self.get_success_url())
    

class DashboardTemplateView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'dashboard_page.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class ScannerTemplateView(UserPassesTestMixin, generic.TemplateView):
    template_name = 'scanner_page.html'

    def test_func(self) -> bool | None:
        return self.request.user.is_staff
