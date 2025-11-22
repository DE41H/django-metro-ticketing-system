from django.db import models

# Create your models here.


class Line(models.Model):
    name = models.CharField(verbose_name='name', max_length=200, unique=True, primary_key=True)
    color = models.CharField(verbose_name='color', max_length=7, unique=True)
    enabled = models.BooleanField(verbose_name='enabled', default=False)

    def __str__(self) -> str:
        return str(self.name)


class Station(models.Model):
    name = models.CharField(verbose_name='name', max_length=200, unique=True, primary_key=True)
    line = models.ForeignKey(to="stations.Line", related_name='stations', on_delete=models.CASCADE)
    neighbours = models.ManyToManyField(to='self', symmetrical=False, blank=True)
    footfall = models.PositiveBigIntegerField(verbose_name='footfall', default=0)

    def __str__(self) -> str:
        return str(self.name)
