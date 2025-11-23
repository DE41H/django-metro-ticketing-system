from django.contrib import admin
from .models import Station, Line

# Register your models here.

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'footfall')}),
        ('Relationships', {'fields': ('lines', 'neighbours')})
    )
    list_display = ('name', 'footfall')
    search_fields = ('name',)
    filter_horizontal = ('lines', 'neighbours')


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
    list_editable = ('allow_ticket_purchase', 'is_running')
    inlines = (StationInline,)
    search_fields = ('name', 'color')

