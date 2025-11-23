import uuid
from typing import Any
from django import forms
from .models import Wallet, Ticket


class WalletBalanceUpdateForm(forms.ModelForm):
    amount = forms.DecimalField(
        label='Amount to Add',
        max_digits=19,
        decimal_places=2,
        min_value=0.01,
        widget = forms.NumberInput(attrs={'step': '0.01'})
    )
    

    class Meta:
        model = Wallet
        fields = []

    
    def clean(self) -> dict[str, Any]:
        amount = self.cleaned_data.get('amount')
        if amount <= 0: # type: ignore
            raise forms.ValidationError('Amount added must be greater than zero!')
        return super().clean()


class TicketScanUpdateForm(forms.ModelForm):
    sample_id = str(uuid.uuid4)
    ticket_id = forms.UUIDField(min_length=len(sample_id), max_length=len(sample_id))

    
    class Meta:
        model = Ticket
        fields = []

    
    def clean(self) -> dict[str, Any]:
        ticket_id = self.cleaned_data.get('ticket_id')
        if not Ticket.objects.filter(id=ticket_id):
            raise forms.ValidationError('Ticket Does Not Exist!')
        elif not Ticket.objects.filter(id=ticket_id, status=Ticket.State.EXPIRED):
            raise forms.ValidationError('Ticket is Expired!')
        return super().clean()
