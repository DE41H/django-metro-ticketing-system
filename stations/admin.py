from typing import Any
from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone
from .models import Station, Line

# Register your models here.

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'footfall', 'updated_at')}),
        ('Relationships', {'fields': ('lines', 'neighbours')})
    )
    list_display = ('name', 'footfall')
    search_fields = ('name',)
    filter_horizontal = ('lines', 'neighbours')
    readonly_fields = ('updated_at',)
    ordering = ('-updated_at',)

    def save_model(self, request: HttpRequest, obj: Any, form: ModelForm, change: bool) -> None:
        if change:
            obj.updated_at = timezone.now()
        return super().save_model(request, obj, form, change)

class StationInline(admin.TabularInline):
    model = Station.lines.through
    extra = 1
    verbose_name_plural = 'Stations on this Line'
    fields = ('station',)


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name',)}),
        ('Details', {'fields': ('color', 'updated_at'), 'classes': ('collapse',)}),
        ('Services', {'fields': ('allow_ticket_purchase', 'is_running'), 'classes': ('collapse',)})
    )
    list_display = ('name', 'color', 'allow_ticket_purchase', 'is_running')
    list_editable = ('allow_ticket_purchase', 'is_running')
    inlines = (StationInline,)
    search_fields = ('name', 'color')
    readonly_fields = ('updated_at',)
    ordering = ('-updated_at',)

    def save_model(self, request: HttpRequest, obj: Any, form: ModelForm, change: bool) -> None:
        if change:
            obj.updated_at = timezone.now()
        return super().save_model(request, obj, form, change)
