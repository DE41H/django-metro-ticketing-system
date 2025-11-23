from django.contrib import admin
from .models import Station, Line

# Register your models here.


class StationInline(admin.TabularInline):
    model = Station
    extra = 1


class LineAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name']}),
        ('config', {'fields': ['color', 'allow_ticket_purchase'], 'classes': ['collapse']})
    ]
    inlines = [StationInline]
    list_display = ['name', 'color', 'allow_ticket_purchase']
    search_fields = ['name']


admin.site.register(Line, LineAdmin)
