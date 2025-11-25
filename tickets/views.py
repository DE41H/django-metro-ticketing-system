from typing import Any
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import generic
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Ticket, Wallet, OTP
from .utils import calculate_ticket_price, send_email, generate_otp
from .forms import WalletBalanceUpdateForm, TicketScanUpdateForm, OTPConfirmationForm
from stations.models import Station


# Create your views here.


class TicketPurchaseView(LoginRequiredMixin, generic.CreateView):
    model = Ticket
    fields = ['start', 'stop']
    template_name = 'tickets/ticket_purchase_form.html'
    success_url = '/tickets/confirm/'

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        start = form.instance.start
        stop = form.instance.stop
        if not start.lines.filter(allow_ticket_purchase=True).exists() or not stop.lines.filter(allow_ticket_purchase=True).exists():
            messages.error(self.request, 'Ticket Purchase is Disabled for a Chosen Station!')
            return self.form_invalid(form)
        elif start == stop:
            messages.error(self.request, 'Start and Destination cannot be the same!')
            return self.form_invalid(form)
        price = calculate_ticket_price(start, stop)
        self.request.session['pending_data'] = {
            'start': start.pk,
            'stop': stop.pk,
            'price': price
        }
        otp = OTP.objects.update_or_create(
            user=self.request.user,
            code = generate_otp()
            )[0]
        send_email(
            user_email=self.request.user.email, # type: ignore
            subject='OTP for Metro Ticket Purchase',
            message=f'Your OTP Code is {otp.code}'
        )
        return redirect('/tickets/confirm/')


class ConfirmTicketPurchase(LoginRequiredMixin, generic.FormView):
    model = OTP
    form_class = OTPConfirmationForm
    template_name = 'tickets/confirm_otp_code_form.html'
    success_url = '/tickets/my/'

    def get(self, request, *args, **kwargs):
        if 'pending_ticket_data' not in request.session:
            messages.error(request, 'No pending ticket purchase found.')
            return redirect('tickets:ticket_purchase')
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form: Any) -> HttpResponse:
        user = self.request.user
        otp_entered = form.cleaned_data['code']
        pending_data = self.request.session.get('pending_data')
        if pending_data is None:
            messages.error(self.request, 'No valid confirmation request found!')
            return self.form_invalid(form)
        price = pending_data['price']
        latest_otp = OTP.objects.filter(user=user, code=otp_entered)
        if not latest_otp.exists():
            messages.error(self.request, 'Invalid OTP Code')
            return self.form_invalid(form)
        elif latest_otp.expired(): # type: ignore
            messages.error(self.request, 'OTP Expired!')
            return self.form_invalid(form)
        latest_otp.delete()
        start = Station.objects.get(pk=pending_data['start'])
        stop = Station.objects.get(pk=pending_data['stop'])
        wallet = Wallet.objects.get_or_create(user=self.request.user)[0]
        try:
            with transaction.atomic():
                if not wallet.deduct(Decimal(price)):
                    raise Exception('Insufficient Funds')
                ticket = Ticket.objects.create(
                    user=user,
                    start=start,
                    stop=stop
                )
                send_email(
                    user_email=self.request.user.email, # type: ignore
                    subject='Ticket Details',
                    message=f'Ticket ID: {ticket.id}\nStart Station: {ticket.start.name}\nDestination Station: {ticket.stop.name}\nCreated At: {ticket.created_at}'
                )
                del self.request.session['pending_data']
                return redirect('tickets:ticket_list')
        except Exception:
            messages.error(self.request, 'Purchase Failed! Insufficient Wallet Funds')
            return redirect('tickets:wallet_balance_update')


class TicketListView(LoginRequiredMixin, generic.ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    ordering = ['-created_at']

    def get_queryset(self) -> QuerySet[Any]:
        return Ticket.objects.select_related('start', 'stop').filter(user=self.request.user) # type: ignore
    

class WalletBalanceUpdateView(LoginRequiredMixin, generic.FormView):
    model = Wallet
    form_class = WalletBalanceUpdateForm
    context_object_name = 'wallet'
    template_name = 'user/wallet_balance_update_form.html'
    success_url = '/tickets/dashboard/'

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model: # type: ignore
        return Wallet.objects.get_or_create(user=self.request.user)[0]
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        wallet = Wallet.objects.get_or_create(user=self.request.user)[0]
        amount = form.cleaned_data.get('amount')
        wallet.add(amount) #type: ignore
        return redirect(self.get_success_url())
    

class TicketScanUpdateView(UserPassesTestMixin, generic.UpdateView):
    model = Ticket
    form_class = TicketScanUpdateForm
    template_name = 'scanner/ticket_scan_update_form.html'
    success_url = '/tickets/scanner/'

    def test_func(self) -> bool | None:
        return self.request.user.is_staff
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        ticket_id = form.cleaned_data.get('ticket_id')
        
        with transaction.atomic():
            ticket = Ticket.objects.select_for_update().get(id=ticket_id)
            match ticket.status:
                case Ticket.State.ACTIVE:
                    ticket.start.increase_footfall()
                    status = ticket.State.IN_USE
                case Ticket.State.IN_USE:
                    ticket.stop.increase_footfall()
                    status = ticket.State.USED
                case _:
                    messages.error(self.request, 'Ticket is already used or expired.')
                    return redirect(self.request.path)
            Ticket.objects.filter(pk=ticket.pk).update(raw_status=status)
        return redirect(self.get_success_url())
    

class TicketPurchaseOfflineView(UserPassesTestMixin, generic.CreateView):
    model = Ticket
    fields = ['start', 'stop']
    template_name = 'scanner/ticket_purchase_offline_form.html'
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
    template_name = 'user/dashboard_page.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class ScannerTemplateView(UserPassesTestMixin, generic.TemplateView):
    template_name = 'scanner/scanner_page.html'

    def test_func(self) -> bool | None:
        return self.request.user.is_staff
