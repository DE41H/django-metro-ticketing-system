import uuid
from decimal import Decimal
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib import admin
from django.db.models import F

# Create your models here.


class Ticket(models.Model):
    id = models.UUIDField(verbose_name='id', unique=True, primary_key=True, default=uuid.uuid4, editable=False)
    start = models.ForeignKey(to='stations.Station', on_delete=models.PROTECT, related_name='departing_tickets', verbose_name='start')
    stop = models.ForeignKey(to='stations.Station', on_delete=models.PROTECT, related_name='arriving_tickets', verbose_name='stop')
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets', null=True)
    created_at = models.DateTimeField(verbose_name='created at', default=timezone.now)

    class State(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        IN_USE = 'IN_USE', 'In Use'
        USED = 'USED', 'Used'
        EXPIRED = 'EXPIRED', 'Expired'

    raw_status = models.CharField(verbose_name='status', max_length=10, choices=State.choices, default=State.ACTIVE)

    @property
    @admin.display(
        ordering='-created_at',
        description='Current Status'
    )
    def status(self):
        if self.raw_status == self.State.ACTIVE and self.expired():
            return self.State.EXPIRED
        return self.raw_status # type: ignore

    def expired(self) -> bool:
        if self.raw_status in (Ticket.State.USED, Ticket.State.IN_USE):
            return False
        else:
            expiry = self.created_at + timedelta(days=2)
            return timezone.now() > expiry

    def __str__(self) -> str:
        return str(self.id)
    

class Wallet(models.Model):
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=19, decimal_places=2, default=Decimal(0))

    def deduct(self, amount: Decimal) -> bool:
        return bool(Wallet.objects.filter(pk=self.pk, balance__gte=amount).update(balance = F('balance') - amount))

    def add(self, amount: Decimal) -> bool:
        return bool(Wallet.objects.filter(pk=self.pk).update(balance = F('balance') + amount))

    def __str__(self) -> str:
        return str(self.user)
