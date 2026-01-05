from typing import Any
from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest
from .models import Station, Line

# Register your models here.

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', )}),
        ('Relationships', {'fields': ('lines', 'neighbours')})
    )
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('lines', 'neighbours')

    def save_model(self, request: HttpRequest, obj: Any, form: ModelForm, change: bool) -> None:
        obj.updated = True
        return super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.updated = True
        form.instance.save(update_fields=['updated'])

class StationInline(admin.TabularInline):
    model = Station.lines.through
    extra = 1
    verbose_name_plural = 'Stations on this Line'
    fields = ('station',)


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name',)}),
        ('Details', {'fields': ('color',), 'classes': ('collapse',)}),
        ('Services', {'fields': ('allow_ticket_purchase', 'is_running'), 'classes': ('collapse',)})
    )
    list_display = ('name', 'color', 'allow_ticket_purchase', 'is_running')
    inlines = (StationInline,)
    search_fields = ('name', 'color')

    def save_model(self, request: HttpRequest, obj: Any, form: ModelForm, change: bool) -> None:
        obj.updated = True
        return super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        stations = set(form.instance.stations.all())
        super().save_related(request, form, formsets, change)
        form.instance.updated = True
        form.instance.save(update_fields=['updated'])
        new_stations = set(form.instance.stations.all())
        affected_stations = [s.pk for s in stations | new_stations]
        Station.objects.filter(pk__in=affected_stations).update(updated=True)
