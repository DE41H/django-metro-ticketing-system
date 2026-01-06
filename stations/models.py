from django.db import models, transaction
from django.db.models import F
from django.core.validators import RegexValidator
from django.contrib import admin
from django.utils import timezone
from tickets.models import Ticket

# Create your models here.

_hex_validator = RegexValidator(
    regex='^#[0-9a-fA-F]{6}$',
    message='Enter a valid hex color code.'
)


class Line(models.Model):
    name = models.CharField(verbose_name='name', max_length=200, unique=True, primary_key=True)
    color = models.CharField(verbose_name='color', max_length=7, unique=True, validators=[_hex_validator])
    allow_ticket_purchase = models.BooleanField(verbose_name='allow_ticket_purchase', default=True)
    is_running = models.BooleanField(verbose_name='is_running', default=True)
    updated = models.BooleanField(verbose_name='updated', default=True)


    class Meta:
        verbose_name = 'Line'
        verbose_name_plural = 'Lines'
        ordering = ['name']

    
    def toggle_running(self) -> None:
        with transaction.atomic():
            line = self.__class__.objects.select_for_update().get(pk=self.pk)
            line.is_running = not line.is_running
            line.save(update_fields=['is_running'])

    def toggle_ticket_purchase(self) -> None:
        with transaction.atomic():
            line = self.__class__.objects.select_for_update().get(pk=self.pk)
            line.allow_ticket_purchase = not line.allow_ticket_purchase
            line.save(update_fields=['allow_ticket_purchase'])

    def __str__(self) -> str:
        return str(self.name)
    
    def __hash__(self) -> int:
        return hash(self.name)


class Station(models.Model):
    name = models.CharField(verbose_name='name', max_length=200, unique=True, primary_key=True)
    lines = models.ManyToManyField(to="stations.Line", related_name='stations', blank=True)
    neighbours = models.ManyToManyField(to='self', symmetrical=False, blank=True)
    updated = models.BooleanField(verbose_name='updated', default=True)


    class Meta:
        verbose_name = 'Station'
        verbose_name_plural = 'Stations'
        ordering = ['name']


    @property
    @admin.display(
        ordering='name',
        description='Daily Footfall'
    )
    def footfall(self) -> int:
        today = timezone.localdate(timezone.now())
        return Ticket.objects.filter(created_at__date=today).filter(models.Q(start=self) | models.Q(stop=self)).count()

    def __str__(self) -> str:
        return str(self.name)
    
    def __hash__(self) -> int:
        return hash(self.name)
