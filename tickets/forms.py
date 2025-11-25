from decimal import Decimal
from typing import Any
from django import forms
from .models import Wallet, Ticket


class WalletBalanceUpdateForm(forms.ModelForm):
    amount = forms.DecimalField(
        label='Amount to Add',
        max_digits=19,
        decimal_places=2,
        min_value=Decimal(0.01),
        widget = forms.NumberInput(attrs={'step': '0.01'}),
        required=True
    )
    

    class Meta:
        model = Wallet
        fields = []


class TicketScanUpdateForm(forms.ModelForm):
    ticket_id = forms.UUIDField(required=True)
    
    
    class Meta:
        model = Ticket
        fields = []

    
    def clean(self) -> dict[str, Any]:
        try:
            ticket = Ticket.objects.get(id=self.cleaned_data.get('ticket_id'))
        except Ticket.DoesNotExist:
            raise forms.ValidationError('Ticket Does Not Exist!')
        match ticket.status:
            case Ticket.State.EXPIRED:
                raise forms.ValidationError('Ticket is Expired!')
            case Ticket.State.USED:
                raise forms.ValidationError('Ticket has already been Used!')
        return super().clean()


class OTPConfirmationForm(forms.ModelForm):
    code = forms.CharField(min_length=6, max_length=6)
