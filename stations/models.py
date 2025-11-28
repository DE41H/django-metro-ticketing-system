from django.db import models
from django.db.models import F
from django.core.validators import RegexValidator

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


    class Meta:
        verbose_name = 'Line'
        verbose_name_plural = 'Lines'


    def __str__(self) -> str:
        return str(self.name)
    
    def __hash__(self) -> int:
        return hash(self.name)


class Station(models.Model):
    name = models.CharField(verbose_name='name', max_length=200, unique=True, primary_key=True)
    lines = models.ManyToManyField(to="stations.Line", related_name='stations', blank=True)
    neighbours = models.ManyToManyField(to='self', symmetrical=False, blank=True)
    footfall = models.PositiveIntegerField(verbose_name='footfall', default=0)


    class Meta:
        verbose_name = 'Station'
        verbose_name_plural = 'Stations'
    

    def increase_footfall(self):
        Station.objects.filter(pk=self.pk).update(footfall=F('footfall') + 1)

    def __str__(self) -> str:
        return str(self.name)
    
    def __hash__(self) -> int:
        return hash(self.name)
