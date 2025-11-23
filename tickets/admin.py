from django.contrib import admin
from .models import Ticket

# Register your models here.


class TicketAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['user']}),
        ('Details', {'fields': ['start', 'stop', 'created_at', 'status', 'expired'], 'classes': ['collapse']}),
    ]
    list_display = ['user', 'start', 'stop', 'created_at', 'status', 'expired']
    search_fields = ['user']


admin.site.register(Ticket, TicketAdmin)
