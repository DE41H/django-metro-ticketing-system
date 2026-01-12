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
    created_at = models.DateTimeField(verbose_name='created at', auto_now_add=True)
    price = models.DecimalField(verbose_name='price', max_digits=11, decimal_places=2)


    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        indexes = [
            models.Index(fields=['raw_status', 'created_at']),
            models.Index(fields=['user', 'raw_status', '-created_at'])
        ]


    class State(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        IN_USE = 'IN_USE', 'In Use'
        USED = 'USED', 'Used'
        EXPIRED = 'EXPIRED', 'Expired'


    raw_status = models.CharField(verbose_name='status', max_length=11, choices=State.choices, default=State.ACTIVE, db_index=True)

    @property
    @admin.display(
        ordering='-created_at',
        description='Current Status'
    )
    def status(self):
        if self.raw_status == self.State.ACTIVE and self._expired():
            return self.State.EXPIRED
        return self.raw_status # type: ignore

    def _expired(self) -> bool:
        if self.raw_status in (Ticket.State.USED, Ticket.State.IN_USE):
            return False
        else:
            expiry = self.created_at + timedelta(days=2)
            return timezone.now() > expiry

    def __str__(self) -> str:
        return str(self.id)
    
    @classmethod
    def bulk_update_ticket_expiry(cls) -> None:
        cls.objects.filter(
            raw_status=cls.State.ACTIVE,
            created_at__lt=timezone.now() - timedelta(days=2)
        ).update(raw_status=cls.State.EXPIRED)
    

class Wallet(models.Model):
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet', primary_key=True)
    balance = models.DecimalField(max_digits=19, decimal_places=2, default=Decimal(0))


    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'


    def deduct(self, amount: Decimal):
        success = bool(Wallet.objects.filter(pk=self.pk, balance__gte=amount).update(balance = F('balance') - amount))
        self.refresh_from_db()
        return success

    def add(self, amount: Decimal) -> bool:
        success = bool(Wallet.objects.filter(pk=self.pk).update(balance = F('balance') + amount))
        self.refresh_from_db()
        return success

    def __str__(self) -> str:
        return str(self.user)
    

class OTP(models.Model):
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otp', primary_key=True)
    code = models.CharField(max_length=6, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'


    def expired(self) -> bool:
        expiry = self.created_at + timedelta(minutes=5)
        return timezone.now() > expiry
    
    def __str__(self) -> str:
        return self.code
